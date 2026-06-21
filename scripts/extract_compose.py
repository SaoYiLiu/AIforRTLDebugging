#!/usr/bin/env python3
import json
import sys

pid = sys.argv[1]
path = "third_party/cvdp/datasets/cvdp_v1.1.0_agentic_code_generation_no_commercial.jsonl"
for line in open(path, encoding="utf-8"):
    r = json.loads(line)
    if r["id"] == pid:
        h = r.get("harness") or {}
        files = h.get("files") if "files" in h else h
        print(files.get("docker-compose.yml", "(missing)"))
        break
else:
    sys.exit(f"not found: {pid}")
