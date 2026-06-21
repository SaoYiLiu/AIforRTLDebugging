#!/usr/bin/env python3
"""CVDP batch entry point (repo root). Usage: python run_cvdp_batch.py --jsonl ..."""

from __future__ import annotations

from repo_paths import ensure_repo_on_path

ensure_repo_on_path()

from react_cvdp.cvdp_batch_runner import main  # noqa: E402

if __name__ == "__main__":
    main()
