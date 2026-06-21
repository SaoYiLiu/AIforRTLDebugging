from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react.cursor_transport import (
    CursorPromptSession,
    cursor_prompt,
    enable_http_request_logging,
    get_transport_mode,
)
from react.parsers import ErrorKind, StructuredFeedback, format_structured_feedback

REPO_ROOT = Path(__file__).absolute().parents[1]
BRIDGE_CURSOR_PROMPT_CHARS = int(os.environ.get("CVDP_BRIDGE_MAX_PROMPT_CHARS", "15000"))
REST_CURSOR_PROMPT_TOKENS = int(os.environ.get("CVDP_REST_MAX_PROMPT_TOKENS", "128000"))
CHARS_PER_TOKEN_ESTIMATE = int(os.environ.get("CVDP_CHARS_PER_TOKEN_ESTIMATE", "4"))
RAW_HARNESS_MAX_CHARS = int(os.environ.get("CVDP_RAW_HARNESS_MAX_CHARS", "9000"))

_HARNESS_FAILURE_ANCHOR = re.compile(
    r"(AssertionError|assert\s+.*==|Test failed|failed for|"
    r"ERROR:\s*Failed|\*\*\s+.*\s+FAIL\s+\*\*|"
    r"FAILED\s+|short test summary info|"
    r"Memory Mismatch|Expected Carry Out|Expected Sum|"
    r"Actual Carry Out|Actual Sum|E\s+SystemExit:)",
    re.IGNORECASE,
)

_RUNNING_TEST_LINE = re.compile(r"running\s+test_", re.IGNORECASE)


def _failure_block_bounds(lines: list[str], anchor: int) -> tuple[int, int]:
    """Return [start, end) line indices for one failure, including stimulus."""
    start = anchor
    for j in range(anchor, max(-1, anchor - 40), -1):
        if _RUNNING_TEST_LINE.search(lines[j]):
            start = j
            break
        if re.search(r"^=+\s*FAILURES\s*=+$", lines[j]):
            start = j
            break
        start = j

    end = min(len(lines), anchor + 15)
    for j in range(anchor + 1, min(len(lines), anchor + 20)):
        if _RUNNING_TEST_LINE.search(lines[j]):
            end = j
            break
        end = j + 1
    return start, end


def _merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    ranges = sorted(ranges)
    merged = [ranges[0]]
    for start, end in ranges[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def _extract_harness_failure_excerpt(combined: str) -> str:
    """Pull assertion / expected-vs-actual blocks to the front of the harness section."""
    lines = combined.splitlines()
    if not lines:
        return ""

    anchors = [
        i
        for i, line in enumerate(lines)
        if _HARNESS_FAILURE_ANCHOR.search(line)
    ]
    if not anchors:
        for i, line in enumerate(lines):
            if re.search(r"(error:|SyntaxError|undefined|cannot find)", line, re.I):
                anchors.append(i)
        if not anchors:
            return ""

    ranges = [_failure_block_bounds(lines, i) for i in anchors]
    parts = [
        "\n".join(lines[start:end]).strip()
        for start, end in _merge_ranges(ranges)
        if start < end
    ]
    return "\n\n".join(p for p in parts if p).strip()


@dataclass(frozen=True)
class CvdpFixResult:
    patched_files: dict[str, str]
    rationale: str
    raw_text: str
    transport: str = "bridge"


ERROR_PROMPTS: dict[ErrorKind, str] = {
    "syntax": (
        "Focus on syntax and elaboration errors reported by iverilog/cocotb. "
        "Do not change functional logic unless required to compile."
    ),
    "binding": (
        "Focus on undeclared identifiers, port connections, and missing wire/reg declarations."
    ),
    "type": "Focus on bit-width mismatches and signed/unsigned issues.",
    "port": "Focus on module port lists matching instantiation sites.",
    "range": "Focus on index bounds and part-select ranges.",
    "compile": (
        "Fix all compile/build errors before attempting logic changes. "
        "Address each harness log error."
    ),
    "logic": (
        "The design builds but fails cocotb/pytest checks in the CVDP harness. "
        "Use failing test cases and expected vs actual values from the harness log. "
        "Make minimal targeted fixes."
    ),
    "formal": "Formal evidence is not primary for CVDP; prioritize harness failures.",
    "unknown": (
        "Review harness output to determine compile vs functional failure, then apply "
        "the smallest correct fix."
    ),
}


def _add_line_numbers(text: str) -> str:
    return "\n".join(f"{i + 1:4d}| {line}" for i, line in enumerate(text.splitlines()))


def _extract_rationale(text: str) -> str:
    m = re.search(r"##\s*Rationale\s*(.*?)(?=##\s*PatchedFiles|\Z)", text, re.DOTALL | re.I)
    if m:
        return m.group(1).strip()
    return ""


def _extract_patched_files(text: str, expected_paths: list[str]) -> dict[str, str]:
    found: dict[str, str] = {}

    # ### rtl/foo.sv followed by fenced block
    section_pat = re.compile(
        r"###\s+(\S+)\s*\n+```(?:verilog|systemverilog|sv)?\s*(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    for m in section_pat.finditer(text):
        path = m.group(1).strip()
        body = m.group(2).strip()
        if body:
            found[path] = body + "\n"

    if found:
        return found

    # Fallback: any ```verilog block containing module
    blocks = re.findall(
        r"```(?:verilog|systemverilog|sv)?\s*(module[\s\S]*?endmodule)\s*```",
        text,
        flags=re.IGNORECASE,
    )
    if len(blocks) == 1 and len(expected_paths) == 1:
        found[expected_paths[0]] = blocks[0].strip() + "\n"
    elif blocks and expected_paths:
        for i, block in enumerate(blocks):
            if i < len(expected_paths):
                found[expected_paths[i]] = block.strip() + "\n"

    return found


def _format_context_files(files: dict[str, str], *, numbered_paths: set[str] | None = None) -> str:
    parts: list[str] = []
    for path in sorted(files.keys()):
        content = files[path]
        if numbered_paths and path in numbered_paths:
            content = _add_line_numbers(content)
        parts.append(f"### {path}\n```verilog\n{content.strip()}\n```")
    return "\n\n".join(parts)


def _cocotb_test_excerpt(harness_dir: Path) -> str:
    src = harness_dir / "src"
    if not src.is_dir():
        return ""
    chunks: list[str] = []
    for test_py in sorted(src.glob("test_*.py")):
        if test_py.name == "test_runner.py":
            continue
        text = test_py.read_text(encoding="utf-8", errors="ignore")
        if "test_vectors" in text or "assert" in text:
            chunks.append(f"### {test_py.name}\n```python\n{text[:4000].strip()}\n```")
    return "\n\n".join(chunks)


def _truncate_middle(text: str, limit: int, *, label: str) -> str:
    if len(text) <= limit:
        return text
    head = limit // 2
    tail = limit - head
    omitted = len(text) - limit
    return (
        text[:head]
        + f"\n\n[... truncated {omitted} chars from {label} ...]\n\n"
        + text[-tail:]
    )


def _truncate_end(text: str, limit: int, *, label: str) -> str:
    if len(text) <= limit:
        return text
    keep = limit
    while keep > 0:
        omitted = len(text) - keep
        suffix = f"\n\n[... truncated {omitted} chars from end of {label} ...]"
        if keep + len(suffix) <= limit:
            return text[:keep] + suffix
        keep -= 1
    return text[:limit]


def _format_raw_harness(
    stdout: str,
    stderr: str,
    *,
    limit: int | None = None,
) -> str:
    parts: list[str] = []
    if (stdout or "").strip():
        parts.append(stdout.strip())
    if (stderr or "").strip():
        parts.append("[stderr]\n" + stderr.strip())
    combined = "\n\n".join(parts)
    if not combined:
        return ""

    max_chars = limit if limit is not None else RAW_HARNESS_MAX_CHARS
    highlights = _extract_harness_failure_excerpt(combined)
    if highlights:
        body = (
            "## Key failure excerpts\n"
            + highlights
            + "\n\n--- full harness log ---\n\n"
            + combined
        )
    else:
        body = combined
    return _truncate_end(body, max_chars, label="harness output")


def _prompt_size(text: str) -> str:
    return f"{len(text)} chars / {len(text.encode('utf-8'))} bytes"


def _max_cursor_prompt_chars() -> int:
    if get_transport_mode() == "bridge":
        return BRIDGE_CURSOR_PROMPT_CHARS
    return REST_CURSOR_PROMPT_TOKENS * CHARS_PER_TOKEN_ESTIMATE


def fix_with_cursor_sdk_cvdp(
    *,
    problem_id: str,
    spec_text: str,
    buggy_files: dict[str, str],
    current_files: dict[str, str],
    patch_targets: list[str],
    harness_stdout: str,
    harness_stderr: str,
    structured_feedback: StructuredFeedback | None = None,
    prior_rationales: list[str] | None = None,
    harness_dir: Path | None = None,
    primary_module: str | None = None,
    model: str = "composer-2.5",
    cursor_session: CursorPromptSession | None = None,
    prompt_artifact_path: Path | None = None,
    include_test_excerpt: bool = True,
    debug_sim_section: str = "",
) -> CvdpFixResult:
    if "CURSOR_API_KEY" not in os.environ:
        raise RuntimeError("CURSOR_API_KEY is required for Cursor SDK fixes.")
    enable_http_request_logging()

    kind: ErrorKind = structured_feedback.error_kind if structured_feedback else "unknown"
    error_guidance = ERROR_PROMPTS.get(kind, ERROR_PROMPTS["unknown"])
    feedback_text = (
        format_structured_feedback(structured_feedback)
        if structured_feedback
        else ""
    )
    feedback_text = _truncate_middle(
        feedback_text.strip(),
        2200,
        label="structured feedback",
    )
    spec_brief = _truncate_middle(spec_text.strip(), 10000, label="task prompt")

    raw_harness = _format_raw_harness(harness_stdout, harness_stderr)

    memory = ""
    if prior_rationales:
        latest = [r.strip() for r in prior_rationales if r.strip()][-1:]
        if latest:
            memory = "## Previous iteration rationale (prioritize this)\n" + latest[0]
            memory = _truncate_middle(memory, 2500, label="previous rationale")

    test_excerpt_raw = ""
    test_excerpt = ""
    if include_test_excerpt and harness_dir:
        test_excerpt_raw = _cocotb_test_excerpt(harness_dir)
        test_excerpt = _truncate_middle(
            test_excerpt_raw,
            1200,
            label="cocotb test excerpt",
        )
    module_hint = primary_module or "the top-level RTL module"

    def build_prompt(
        *,
        spec: str,
        feedback: str,
        harness: str,
        test: str,
        prior_memory: str,
        with_test_excerpt: bool = include_test_excerpt,
        debug_sim: str = "",
    ) -> str:
        test_section = ""
        if with_test_excerpt:
            test_section = f"""
## Cocotb test excerpt
{test if test else "(not available)"}
"""
        debug_section = ""
        if debug_sim.strip():
            debug_section = f"""
{debug_sim.strip()}
"""
        return f"""You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
{problem_id}

## Error type
{kind}

## Fix strategy
{error_guidance}

## Task description excerpt
{spec}

## Current candidate files (line-numbered on patch targets)
{_format_context_files(current_files, numbered_paths=set(patch_targets))}

## Files you must patch
{", ".join(patch_targets)}

Primary module: `{module_hint}`

## Structured harness feedback
```text
{feedback if feedback else "(see raw harness output below)"}
```

{prior_memory}

## Raw CVDP harness output excerpt
```text
{harness}
```
{test_section}{debug_section}
## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in {patch_targets}, use:

### rtl/your_file.sv
```verilog
<full file contents>
```
"""

    debug_sim_trimmed = _truncate_middle(
        debug_sim_section.strip(),
        5000,
        label="iverilog debug evidence",
    )

    prompt = build_prompt(
        spec=spec_brief,
        feedback=feedback_text,
        harness=raw_harness,
        test=test_excerpt,
        prior_memory=memory,
        debug_sim=debug_sim_trimmed,
    )
    max_prompt_chars = _max_cursor_prompt_chars()
    if len(prompt) > max_prompt_chars:
        prompt = build_prompt(
            spec=_truncate_middle(spec_brief, 1000, label="task prompt"),
            feedback=_truncate_middle(feedback_text, 1000, label="structured feedback"),
            harness=_format_raw_harness(harness_stdout, harness_stderr, limit=800),
            test=_truncate_middle(
                test_excerpt_raw,
                2000,
                label="cocotb test excerpt",
            ),
            prior_memory=_truncate_middle(memory, 2000, label="previous rationale"),
            debug_sim=_truncate_middle(debug_sim_trimmed, 2500, label="iverilog debug evidence"),
        )
    if len(prompt) > max_prompt_chars:
        raise RuntimeError(
            f"CVDP Cursor prompt is still too large after compaction: "
            f"{_prompt_size(prompt)} > {max_prompt_chars} chars. "
            "Increase CVDP_BRIDGE_MAX_PROMPT_CHARS or CVDP_REST_MAX_PROMPT_TOKENS, "
            "or reduce RTL context."
        )

    print(
        f"[{problem_id}] Cursor prompt size: {_prompt_size(prompt)} "
        f"(limit {max_prompt_chars} chars)",
        flush=True,
    )

    if cursor_session is not None:
        raw, transport = cursor_session.prompt(
            prompt,
            model=model,
            timeout_s=600,
            prompt_artifact_path=prompt_artifact_path,
        )
    else:
        os.chdir(REPO_ROOT)
        raw, transport = cursor_prompt(
            prompt,
            model=model,
            api_key=os.environ["CURSOR_API_KEY"],
            workspace=str(REPO_ROOT),
            timeout_s=600,
            prompt_artifact_path=prompt_artifact_path,
        )

    patched = _extract_patched_files(raw, patch_targets)
    if not patched:
        raise RuntimeError(
            f"Cursor response did not contain parsable PatchedFiles for {patch_targets}."
        )

    # Ensure every patch target has content (allow single-block fallback for primary file).
    for target in patch_targets:
        if target not in patched and len(patched) == 1:
            patched[target] = next(iter(patched.values()))

    missing = [t for t in patch_targets if t not in patched]
    if missing:
        raise RuntimeError(f"Cursor patch missing files: {missing}")

    return CvdpFixResult(
        patched_files=patched,
        rationale=_extract_rationale(raw),
        raw_text=raw,
        transport=transport,
    )
