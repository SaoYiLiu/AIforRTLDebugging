#!/usr/bin/env python3
"""CVDP batch entry point (repo root). Usage: python run_cvdp_batch.py --jsonl ..."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).absolute().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from react_cvdp.cvdp_batch_runner import main

if __name__ == "__main__":
    main()
