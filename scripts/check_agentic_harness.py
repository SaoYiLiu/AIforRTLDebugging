#!/usr/bin/env python3
import json
from pathlib import Path

DATA = Path("third_party/cvdp/datasets")
for name in [
    "cvdp_v1.1.0_nonagentic_code_generation_no_commercial.jsonl",
    "cvdp_v1.1.0_agentic_code_generation_no_commercial.jsonl",
]:
    p = DATA / name
    if not p.exists():
        print(f"{name}: MISSING")
        continue
    cid016 = with_h = 0
    ids_no_h = []
    for line in p.open(encoding="utf-8"):
        r = json.loads(line)
        cats = r.get("categories") or []
        if not cats or cats[0] != "cid016":
            continue
        cid016 += 1
        h = r.get("harness") or {}
        if "files" in h:
            files = h["files"]
        else:
            files = {k: v for k, v in h.items() if isinstance(v, str)}
        if files:
            with_h += 1
        else:
            ids_no_h.append(r["id"])
    print(f"\n{name}")
    print(f"  cid016 total: {cid016}, with harness: {with_h}")
    if ids_no_h:
        print(f"  no harness ({len(ids_no_h)}):")
        for pid in ids_no_h[:15]:
            print(f"    - {pid}")
        if len(ids_no_h) > 15:
            print(f"    ... +{len(ids_no_h)-15} more")
