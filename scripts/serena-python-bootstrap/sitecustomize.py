from __future__ import annotations

import sys
import types
from pathlib import Path


def install_pyright(*_args, **_kwargs) -> Path:
    for entry in sys.path:
        candidate = Path(entry).resolve() / "pyright" / "dist"
        if candidate.exists():
            return candidate
    raise ModuleNotFoundError("Cannot locate pyright/dist for bootstrap shim")


if "pyright._utils" not in sys.modules:
    module = types.ModuleType("pyright._utils")
    module.install_pyright = install_pyright
    sys.modules["pyright._utils"] = module
