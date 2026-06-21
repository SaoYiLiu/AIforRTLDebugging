#!/usr/bin/env python3
"""ChipBench batch entry point (repo root). Usage: python run_chipbench_batch.py --dataset-dir ..."""

from __future__ import annotations

from repo_paths import ensure_repo_on_path

ensure_repo_on_path()

from react.batch_runner import main  # noqa: E402

if __name__ == "__main__":
    main()
