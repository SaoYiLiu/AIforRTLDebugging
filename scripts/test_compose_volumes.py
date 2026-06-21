#!/usr/bin/env python3
"""Quick check for docker-compose volume merging."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from react_cvdp.cvdp_staging import _ensure_compose_volumes, _sanitize_compose

RAW = """services:
  sanity:
    image: __OSS_SIM_IMAGE__
    volumes:
      - ./src:/src/      
    working_dir : /code/rundir
    env_file    : ./src/.env
    command     : pytest /src/test_runner.py -s -v -o cache_dir=/rundir/harness/.cache
"""

out = _ensure_compose_volumes(_sanitize_compose(RAW, "nvidia/cvdp-sim:v1.0.0"))
print(out)
assert out.count("volumes:") == 1, "duplicate volumes: key"
assert "./rtl:/code/rtl" in out
print("OK")
