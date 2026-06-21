#!/usr/bin/env python3
import json
from pathlib import Path

p = Path("third_party/cvdp/datasets/cvdp_v1.1.0_agentic_code_generation_no_commercial.jsonl")
for line in p.open(encoding="utf-8"):
    r = json.loads(line)
    if (r.get("categories") or [None])[0] != "cid016":
        continue
    ctx = r.get("context") or {}
    patch = list((r.get("patch") or {}).keys())
    h = r.get("harness") or {}
    hfiles = h.get("files") if "files" in h else {k: v for k, v in h.items() if isinstance(v, str)}
    rtl = [k for k in ctx if k.startswith("rtl/")]
    verif = [k for k in ctx if k.startswith("verif/")]
    print(r["id"])
    print(f"  patch: {patch[:5]}{'...' if len(patch)>5 else ''}")
    print(f"  context rtl: {len(rtl)}, verif: {len(verif)}, harness files: {len(hfiles)}")
    print()
