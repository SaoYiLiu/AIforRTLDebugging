from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


CvdpFormat = Literal["nonagentic", "agentic"]


@dataclass(frozen=True)
class CvdpProblemSpec:
    problem_id: str
    category: str
    difficulty: str
    format: CvdpFormat
    prompt: str
    context_files: dict[str, str]
    patch_targets: list[str]
    harness_files: dict[str, str]
    primary_module: str | None = None
    system_message: str | None = None

    @property
    def rtl_files(self) -> dict[str, str]:
        return {p: c for p, c in self.context_files.items() if p.startswith("rtl/")}


def _detect_module(sv_text: str) -> str | None:
    m = re.search(r"^\s*module\s+(\w+)", sv_text, re.MULTILINE)
    return m.group(1) if m else None


def _primary_rtl_path(spec_context: dict[str, str], patch_targets: list[str]) -> str | None:
    rtl_paths = [p for p in spec_context if p.startswith("rtl/") and p.endswith((".sv", ".v"))]
    if not rtl_paths:
        return None
    for target in patch_targets:
        if target in rtl_paths:
            return target
    return rtl_paths[0]


def _normalize_record(raw: dict) -> CvdpProblemSpec | None:
    categories = raw.get("categories") or []
    if not categories:
        return None
    category = categories[0]
    difficulty = categories[1] if len(categories) > 1 else "unknown"

    if "input" in raw:
        fmt: CvdpFormat = "nonagentic"
        inp = raw["input"]
        prompt = inp.get("prompt") or ""
        context_files = dict(inp.get("context") or {})
        out_ctx = (raw.get("output") or {}).get("context") or {}
        patch_targets = sorted(out_ctx.keys()) or sorted(context_files.keys())
        harness_files = dict((raw.get("harness") or {}).get("files") or {})
        system_message = None
    else:
        fmt = "agentic"
        prompt = raw.get("prompt") or ""
        context_files = dict(raw.get("context") or {})
        patch_targets = sorted((raw.get("patch") or {}).keys()) or [
            p for p in context_files if p.startswith("rtl/")
        ]
        harness_raw = raw.get("harness") or {}
        if "files" in harness_raw:
            harness_files = dict(harness_raw["files"])
        else:
            harness_files = {k: v for k, v in harness_raw.items() if isinstance(v, str)}
        system_message = raw.get("system_message")

    primary_path = _primary_rtl_path(context_files, patch_targets)
    primary_module = None
    if primary_path and primary_path in context_files:
        primary_module = _detect_module(context_files[primary_path])

    return CvdpProblemSpec(
        problem_id=raw["id"],
        category=category,
        difficulty=difficulty,
        format=fmt,
        prompt=prompt,
        context_files=context_files,
        patch_targets=patch_targets,
        harness_files=harness_files,
        primary_module=primary_module,
        system_message=system_message,
    )


def load_cvdp_problems(
    jsonl_path: str | Path,
    *,
    categories: list[str] | None = None,
    formats: tuple[CvdpFormat, ...] = ("nonagentic", "agentic"),
    problem_ids: list[str] | None = None,
) -> list[CvdpProblemSpec]:
    """
    Load CVDP problems from a JSONL file.

    Default ``categories`` is ``[\"cid016\"]`` (debugging / bug fixing).
    """
    path = Path(jsonl_path)
    if not path.is_file():
        raise FileNotFoundError(f"CVDP JSONL not found: {path}")

    wanted_cats = set(categories or ["cid016"])
    wanted_ids = {p.strip() for p in problem_ids} if problem_ids else None
    wanted_formats = set(formats)

    specs: list[CvdpProblemSpec] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc

            spec = _normalize_record(raw)
            if spec is None:
                continue
            if spec.category not in wanted_cats:
                continue
            if spec.format not in wanted_formats:
                continue
            if wanted_ids and spec.problem_id not in wanted_ids:
                continue
            specs.append(spec)

    return specs
