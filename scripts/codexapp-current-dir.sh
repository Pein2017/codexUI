#!/usr/bin/env bash

set -euo pipefail

log() {
  printf '[codexapp-current-dir] %s\n' "$*" >&2
}

fail() {
  log "$*"
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/.." && pwd -P)"
launch_dir="$(pwd -P)"
codex_home="${CODEX_HOME:-${launch_dir}/.codex}"
local_entry="${repo_root}/dist-cli/index.js"
frontend_entry="${repo_root}/dist/index.html"

need_cmd node
need_cmd npm

export CODEX_HOME="${codex_home}"
export TELEGRAM_DEFAULT_CWD="${TELEGRAM_DEFAULT_CWD:-${launch_dir}}"
export CODEXUI_LAUNCH_SCOPE="${CODEXUI_LAUNCH_SCOPE:-${launch_dir}}"
export CODEXUI_REPO_ROOT="${CODEXUI_REPO_ROOT:-${repo_root}}"
export CODEXUI_SERENA_READY_DELAY_MS="${CODEXUI_SERENA_READY_DELAY_MS:-3000}"
export CODEXUI_SERENA_READY_TIMEOUT_MS="${CODEXUI_SERENA_READY_TIMEOUT_MS:-30000}"
export CODEXUI_SERENA_RETRY_DELAY_MS="${CODEXUI_SERENA_RETRY_DELAY_MS:-1500}"
export CODEXUI_SERENA_MAX_RETRIES="${CODEXUI_SERENA_MAX_RETRIES:-3}"
export http_proxy=http://127.0.0.1:9090

if [[ -z "${CODEXUI_SERENA_REPO_ROOT:-}" ]]; then
  if [[ -d "${launch_dir}/mcp/serena" ]]; then
    export CODEXUI_SERENA_REPO_ROOT="${launch_dir}/mcp/serena"
  elif [[ -d "${repo_root}/../serena" ]]; then
    export CODEXUI_SERENA_REPO_ROOT="$(cd "${repo_root}/../serena" && pwd -P)"
  fi
fi

proxy_url="${CODEXUI_PROXY_URL:-${http_proxy:-${HTTP_PROXY:-}}}"
if [[ -n "${proxy_url}" ]]; then
  export http_proxy="${proxy_url}"
  export https_proxy="${https_proxy:-${proxy_url}}"
  export HTTP_PROXY="${HTTP_PROXY:-${http_proxy}}"
  export HTTPS_PROXY="${HTTPS_PROXY:-${https_proxy}}"
fi

mkdir -p "${CODEX_HOME}"

deps_ready() {
  [[ -x "${repo_root}/node_modules/.bin/vue-tsc" ]] &&
    [[ -x "${repo_root}/node_modules/.bin/vite" ]] &&
    [[ -x "${repo_root}/node_modules/.bin/tsup" ]] &&
    [[ -f "${repo_root}/node_modules/vite/dist/client/client.mjs" ]] &&
    [[ -f "${repo_root}/node_modules/rollup/dist/shared/parseAst.js" ]]
}

install_deps() {
  local install_cmd=()

  if [[ -f "${repo_root}/package-lock.json" ]]; then
    install_cmd=(npm --prefix "${repo_root}" ci --include=dev)
  else
    install_cmd=(npm --prefix "${repo_root}" install --include=dev)
  fi

  log "Installing local codexUI dependencies"
  "${install_cmd[@]}"
}

build_local_app() {
  log "Building local codexUI frontend and CLI"
  (
    cd "${repo_root}"
    ./node_modules/.bin/vue-tsc --noEmit
    ./node_modules/.bin/vite build
    ./node_modules/.bin/tsup
  )
}

if ! deps_ready; then
  install_deps
fi

deps_ready || fail "Local dependencies are incomplete after install; inspect ${repo_root}/node_modules"

if [[ ! -f "${local_entry}" || ! -f "${frontend_entry}" ]]; then
  build_local_app
fi

[[ -f "${local_entry}" ]] || fail "Missing CLI build artifact: ${local_entry}"
[[ -f "${frontend_entry}" ]] || fail "Missing frontend build artifact: ${frontend_entry}"

exec node "${local_entry}" "${launch_dir}" --no-login --no-open --no-tunnel
