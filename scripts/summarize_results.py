#!/usr/bin/env python3
import json
from pathlib import Path

root = Path("outputs")
rows = []
for d in sorted(root.iterdir()):
    p = d / "result.json"
    if not p.is_file():
        continue
    r = json.loads(p.read_text())
    rows.append(
        (
            r.get("problem_id", d.name),
            r.get("ok"),
            r.get("harness_passed", r.get("ok")),
            r.get("iterations", "-"),
            r.get("format", "chipbench"),
        )
    )
for row in rows:
    print("\t".join(str(x) for x in row))
print(f"total={len(rows)} pass={sum(1 for r in rows if r[1])}")
