"""Locate the AIfordebugging repo root without requiring a valid process cwd (WSL /mnt/c)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_MARKER = "mcp_server.py"


def _root_from_file(path: Path) -> Path | None:
    p = path if path.is_dir() else path.parent
    if (p / _MARKER).is_file():
        return p
    if p.name == "react" and (p.parent / _MARKER).is_file():
        return p.parent
    return None


def repo_root() -> Path:
    """Return repository root; raise SystemExit with recovery hints if unknown."""
    env = os.environ.get("AIFORDEBUGGING_ROOT")
    if env:
        root = Path(env).expanduser()
        if (root / _MARKER).is_file():
            return root
        raise SystemExit(f"AIFORDEBUGGING_ROOT is set but invalid: {root}")

    for raw in (globals().get("__file__"), sys.argv[0] if sys.argv else None):
        if not raw:
            continue
        p = Path(raw)
        if p.is_absolute():
            found = _root_from_file(p)
            if found is not None:
                return found

    # Relative script path — needs cwd unless AIFORDEBUGGING_ROOT was set above.
    try:
        cwd = Path(os.getcwd())
    except OSError:
        cwd = None

    if cwd is not None:
        for raw in (globals().get("__file__"), sys.argv[0] if sys.argv else None):
            if not raw:
                continue
            found = _root_from_file(cwd / raw)
            if found is not None:
                return found

    raise SystemExit(
        "Cannot determine repository root: the shell working directory is invalid "
        "(common on WSL /mnt/c).\n\n"
        "Fix one of:\n"
        "  cd /mnt/c/Users/user/Desktop/AIfordebugging\n"
        "  python run_chipbench_batch.py ...\n\n"
        "  export AIFORDEBUGGING_ROOT=/mnt/c/Users/user/Desktop/AIfordebugging\n"
        "  python run_chipbench_batch.py ...\n\n"
        "  python /mnt/c/Users/user/Desktop/AIfordebugging/run_chipbench_batch.py ..."
    )


def ensure_repo_on_path() -> Path:
    """Insert repo root on sys.path and chdir there if the process cwd is broken."""
    root = repo_root()
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    try:
        os.getcwd()
    except OSError:
        os.chdir(root_s)
    return root
