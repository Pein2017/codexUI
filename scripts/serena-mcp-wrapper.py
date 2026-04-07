#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


READY_DELAY_MS = int(os.environ.get("CODEXUI_SERENA_READY_DELAY_MS", "3000"))
READY_TIMEOUT_MS = int(os.environ.get("CODEXUI_SERENA_READY_TIMEOUT_MS", "30000"))
RETRY_DELAY_MS = int(os.environ.get("CODEXUI_SERENA_RETRY_DELAY_MS", "1500"))
MAX_RETRIES = int(os.environ.get("CODEXUI_SERENA_MAX_RETRIES", "3"))
RETRIABLE_ERROR_MARKERS = (
    "Cannot extract symbols from file",
    "No module named 'pyright._utils'",
)
SYMBOL_TOOL_NAMES = {
    "get_symbols_overview",
    "find_symbol",
    "find_referencing_symbols",
    "replace_symbol_body",
    "insert_after_symbol",
    "insert_before_symbol",
    "rename_symbol",
}
PROBE_SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".codex",
    ".serena",
    "dist",
    "build",
}


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_project_root(repo_root: Path) -> str:
    for key in ("CODEXUI_LAUNCH_SCOPE", "TELEGRAM_DEFAULT_CWD", "PWD"):
        raw = os.environ.get(key, "").strip()
        if raw:
            return str(Path(raw).resolve())
    return str(repo_root)


def build_child_command(repo_root: Path, project_root: str) -> list[str]:
    explicit_serena_root = os.environ.get("CODEXUI_SERENA_REPO_ROOT", "").strip()
    if explicit_serena_root:
        explicit_root = Path(explicit_serena_root).resolve()
        serena_bin = explicit_root / ".venv" / "bin" / "serena"
        if serena_bin.is_file():
            return [str(serena_bin), "start-mcp-server", "--project", project_root, "--context", "codex"]

    serena_bin = Path(project_root) / "mcp" / "serena" / ".venv" / "bin" / "serena"
    if serena_bin.is_file():
        return [str(serena_bin), "start-mcp-server", "--project", project_root, "--context", "codex"]

    serena_bin = repo_root.parent / "serena" / ".venv" / "bin" / "serena"
    if serena_bin.is_file():
        return [str(serena_bin), "start-mcp-server", "--project", project_root, "--context", "codex"]

    uv_bin = Path(project_root) / ".local" / "bin" / "uv"
    uv_command = str(uv_bin) if uv_bin.is_file() else shutil.which("uv")
    if not uv_command:
        raise RuntimeError("Cannot find Serena launcher: neither mcp/serena/.venv/bin/serena nor uv is available")

    return [
        uv_command,
        "run",
        "--directory",
        str(Path(explicit_serena_root).resolve() if explicit_serena_root else Path(project_root) / "mcp" / "serena"),
        "serena",
        "start-mcp-server",
        "--project",
        project_root,
        "--context",
        "codex",
    ]


def build_child_env(repo_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    compat_root = str((repo_root / "scripts" / "serena-python-bootstrap").resolve())
    existing = env.get("PYTHONPATH", "").strip()
    env["PYTHONPATH"] = compat_root if not existing else f"{compat_root}:{existing}"
    return env


def parse_json(line: str) -> dict[str, Any] | None:
    try:
        value = json.loads(line)
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def response_contains_retryable_error(payload: dict[str, Any]) -> bool:
    if payload.get("error"):
        message = payload["error"].get("message", "") if isinstance(payload["error"], dict) else ""
        return any(marker in str(message) for marker in RETRIABLE_ERROR_MARKERS)

    result = payload.get("result")
    if result is None:
        return False

    content = json.dumps(result, ensure_ascii=False)
    return any(marker in content for marker in RETRIABLE_ERROR_MARKERS)


def response_is_success(payload: dict[str, Any]) -> bool:
    return not payload.get("error") and not response_contains_retryable_error(payload)


def collect_probe_candidates(project_root: str) -> list[str]:
    root = Path(project_root)
    preferred = [
        root / "src" / "dispatcher" / "api.py",
        root / "src" / "dispatcher" / "stream_contract.py",
        root / "video_runtime" / "runtime_config.py",
    ]
    candidates: list[str] = []

    def add_candidate(path: Path) -> None:
        if not path.is_file() or path.suffix != ".py":
            return
        rel_path = path.relative_to(root).as_posix()
        if rel_path not in candidates:
            candidates.append(rel_path)

    for path in preferred:
        if path.is_file():
            add_candidate(path)

    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in PROBE_SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            add_candidate(Path(current_root) / filename)
            if len(candidates) >= 12:
                return candidates

    return candidates


class SerenaMcpProxy:
    def __init__(self) -> None:
        self.repo_root = get_repo_root()
        self.project_root = get_project_root(self.repo_root)
        child_env = build_child_env(self.repo_root)
        child_cmd = build_child_command(self.repo_root, self.project_root)
        self.child = subprocess.Popen(
            child_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=child_env,
        )
        assert self.child.stdin is not None
        assert self.child.stdout is not None
        assert self.child.stderr is not None

        self._write_lock = threading.Lock()
        self._pending_lock = threading.Lock()
        self._pending: dict[int, dict[str, Any]] = {}
        self._next_internal_id = -1
        self._ready_at: float | None = None
        self._stop_event = threading.Event()
        self._serena_ready = threading.Event()
        self._probe_candidates = collect_probe_candidates(self.project_root)

    def _new_internal_id(self) -> int:
        with self._pending_lock:
            value = self._next_internal_id
            self._next_internal_id -= 1
            return value

    def _write_child(self, message: dict[str, Any]) -> None:
        with self._write_lock:
            self.child.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            self.child.stdin.flush()

    def _write_stdout(self, message: dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    def _call_internal(self, method: str, params: dict[str, Any], timeout_s: float) -> dict[str, Any] | None:
        internal_id = self._new_internal_id()
        event = threading.Event()
        with self._pending_lock:
            self._pending[internal_id] = {
                "probe_event": event,
                "probe_response": None,
            }
        self._write_child({
            "jsonrpc": "2.0",
            "id": internal_id,
            "method": method,
            "params": params,
        })
        if not event.wait(timeout=timeout_s):
            with self._pending_lock:
                self._pending.pop(internal_id, None)
            return None
        with self._pending_lock:
            context = self._pending.pop(internal_id, None)
        if not context:
            return None
        response = context.get("probe_response")
        return response if isinstance(response, dict) else None

    def _wait_until_ready(self) -> None:
        if self._serena_ready.is_set():
            return
        ready_at = self._ready_at
        if ready_at is None:
            return
        remaining = ready_at - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)
        deadline = time.monotonic() + max(0, READY_TIMEOUT_MS) / 1000
        candidates = self._probe_candidates or []
        while not self._stop_event.is_set() and not self._serena_ready.is_set() and time.monotonic() < deadline:
            for relative_path in candidates:
                response = self._call_internal(
                    "tools/call",
                    {
                        "name": "get_symbols_overview",
                        "arguments": {
                            "relative_path": relative_path,
                        },
                    },
                    timeout_s=5.0,
                )
                if response and response_is_success(response):
                    self._serena_ready.set()
                    return
                if self._stop_event.is_set() or time.monotonic() >= deadline:
                    break
            time.sleep(max(0, RETRY_DELAY_MS) / 1000)
        self._serena_ready.set()

    def _handle_client_message(self, raw_line: str) -> None:
        message = parse_json(raw_line)
        if message is None:
            self.child.stdin.write(raw_line)
            self.child.stdin.flush()
            return

        method = message.get("method")
        if method in {"initialized", "notifications/initialized"}:
            self._ready_at = time.monotonic() + READY_DELAY_MS / 1000
            self._serena_ready.clear()
            self._write_child(message)
            return

        if method == "tools/call" and isinstance(message.get("id"), int):
            params = message.get("params")
            if isinstance(params, dict) and params.get("name") in SYMBOL_TOOL_NAMES:
                self._wait_until_ready()
            internal_id = self._new_internal_id()
            with self._pending_lock:
                self._pending[internal_id] = {
                    "client_id": message["id"],
                    "request": message,
                    "retries": 0,
                }
            forwarded = dict(message)
            forwarded["id"] = internal_id
            self._write_child(forwarded)
            return

        self._write_child(message)

    def _retry_or_forward_response(self, message: dict[str, Any]) -> bool:
        response_id = message.get("id")
        if not isinstance(response_id, int) or response_id >= 0:
            return False

        with self._pending_lock:
            context = self._pending.get(response_id)
        if context is None:
            return False

        probe_event = context.get("probe_event")
        if isinstance(probe_event, threading.Event):
            with self._pending_lock:
                context["probe_response"] = message
            probe_event.set()
            return True

        if response_contains_retryable_error(message) and context["retries"] < MAX_RETRIES:
            time.sleep(RETRY_DELAY_MS / 1000)
            next_id = self._new_internal_id()
            retried_request = dict(context["request"])
            retried_request["id"] = next_id
            with self._pending_lock:
                self._pending.pop(response_id, None)
                self._pending[next_id] = {
                    **context,
                    "retries": context["retries"] + 1,
                }
            self._write_child(retried_request)
            return True

        forwarded = dict(message)
        forwarded["id"] = context["client_id"]
        with self._pending_lock:
            self._pending.pop(response_id, None)
        self._write_stdout(forwarded)
        return True

    def _forward_child_stdout(self) -> None:
        for raw_line in self.child.stdout:
            if self._stop_event.is_set():
                break
            line = raw_line.rstrip("\n")
            if not line:
                continue
            message = parse_json(line)
            if message is not None and self._retry_or_forward_response(message):
                continue
            if message is not None:
                self._write_stdout(message)
                continue
            sys.stdout.write(raw_line)
            sys.stdout.flush()

    def _forward_child_stderr(self) -> None:
        for raw_line in self.child.stderr:
            if self._stop_event.is_set():
                break
            sys.stderr.write(raw_line)
            sys.stderr.flush()

    def _forward_stdin(self) -> None:
        for raw_line in sys.stdin:
            if self._stop_event.is_set():
                break
            self._handle_client_message(raw_line)
        try:
            self.child.stdin.close()
        except Exception:
            pass

    def _terminate_child(self) -> None:
        if self.child.poll() is not None:
            return
        try:
            self.child.terminate()
        except Exception:
            return
        try:
            self.child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                self.child.kill()
            except Exception:
                pass

    def run(self) -> int:
        def stop_handler(_signum: int, _frame: Any) -> None:
            self._stop_event.set()
            self._terminate_child()

        signal.signal(signal.SIGTERM, stop_handler)
        signal.signal(signal.SIGINT, stop_handler)

        stdin_thread = threading.Thread(target=self._forward_stdin, name="serena-mcp-proxy-stdin", daemon=True)
        stdout_thread = threading.Thread(target=self._forward_child_stdout, name="serena-mcp-proxy-stdout", daemon=True)
        stderr_thread = threading.Thread(target=self._forward_child_stderr, name="serena-mcp-proxy-stderr", daemon=True)

        stdin_thread.start()
        stdout_thread.start()
        stderr_thread.start()

        exit_code = self.child.wait()
        self._stop_event.set()
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)
        stdin_thread.join(timeout=1)
        return exit_code


def main() -> int:
    proxy = SerenaMcpProxy()
    return proxy.run()


if __name__ == "__main__":
    raise SystemExit(main())
