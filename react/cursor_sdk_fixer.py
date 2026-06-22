from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react.connection_map import (  # noqa: E402
    format_connection_map_for_llm,
    strip_buggy_module_from_prompt,
)
from react.cursor_transport import CursorPromptSession, cursor_prompt  # noqa: E402
from react.formal_runner import format_formal_for_llm  # noqa: E402
from react.parsers import (  # noqa: E402
    ErrorKind,
    StructuredFeedback,
    format_structured_feedback,
)

REPO_ROOT = Path(__file__).absolute().parents[1]
CHIPBENCH_MAX_PROMPT_CHARS = int(os.environ.get("CHIPBENCH_MAX_PROMPT_CHARS", "12000"))


@dataclass(frozen=True)
class FixResult:
    fixed_sv: str
    rationale: str
    raw_text: str
    transport: str = "bridge"


ERROR_PROMPTS: dict[ErrorKind, str] = {
    "syntax": (
        "Focus on syntax only: semicolons, begin/end pairing, keywords, and valid Verilog-2001 constructs. "
        "Do not change functional logic unless required to fix a syntax error."
    ),
    "binding": (
        "Focus on undeclared identifiers, port connections, and wire/reg declarations. "
        "Ensure every signal used in the module is declared before use."
    ),
    "type": (
        "Focus on bit-width mismatches, signed/unsigned issues, and assignment width rules."
    ),
    "port": (
        "Focus on module port lists matching instantiation and reference connections."
    ),
    "range": (
        "Focus on index bounds, array sizes, and part-select ranges."
    ),
    "compile": (
        "Fix all compilation errors before attempting logic changes. "
        "Address each listed error at the indicated line."
    ),
    "logic": (
        "The design compiles but fails simulation against the reference model. "
        "Use structured mismatch data and the causal waveform trace to find where DUT diverges from ref. "
        "Make minimal targeted logic fixes; preserve correct behavior elsewhere."
    ),
    "formal": (
        "SymbiYosys found an assertion violation under unconstrained inputs. "
        "Use the failing assertion name and formal counterexample (CEX) trace to locate the bug. "
        "Fix TopModule so all spec properties hold; the CEX shows a minimal input sequence that breaks an invariant."
    ),
    "unknown": (
        "Review structured feedback and simulation evidence to identify whether the issue is "
        "compile-time or a logic mismatch, then apply the smallest correct fix."
    ),
}


def _extract_topmodule_sv(text: str) -> str | None:
    m = re.search(
        r"##\s*FixedTopModule\s*(?:```(?:verilog|systemverilog|sv)?\s*)?"
        r"(module\s+TopModule[\s\S]*?endmodule)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return m.group(1).strip() + "\n"

    m = re.search(
        r"```(?:verilog|systemverilog|sv)?\s*(module\s+TopModule[\s\S]*?endmodule)\s*```",
        text,
    )
    if m:
        return m.group(1).strip() + "\n"

    m2 = re.search(r"(module\s+TopModule[\s\S]*?endmodule)", text)
    if m2:
        return m2.group(1).strip() + "\n"

    return None


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


def _extract_rationale(text: str) -> str:
    m = re.search(
        r"##\s*Rationale\s*(.*?)(?:\n##\s*FixedTopModule|\Z)",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()

    parts = re.split(
        r"```(?:verilog|systemverilog|sv)?\s*module\s+TopModule[\s\S]*?endmodule\s*```",
        text,
        maxsplit=1,
    )
    if len(parts) >= 1:
        return parts[0].strip()

    return ""


def _add_line_numbers(code: str) -> str:
    lines = code.splitlines()
    width = max(3, len(str(len(lines))))
    return "\n".join(f"L{i + 1:0{width}d}: {line}" for i, line in enumerate(lines))


def _format_vcd_summary(vcd_summary: dict[str, Any] | None) -> str:
    if not vcd_summary:
        return ""

    from react.vcd_trace import filter_vcd_summary_for_llm, is_clock_vcd_signal

    vcd_summary = filter_vcd_summary_for_llm(vcd_summary) or {}

    parts: list[str] = []

    if vcd_summary.get("failure_time") is not None:
        parts.append(f"failure_time (ps): {vcd_summary['failure_time']}")

    causal = vcd_summary.get("causal_chain") or []
    if causal:
        parts.append("\n## Causal trace (transitions before failure)")
        for ev in causal[:20]:
            sig = str(ev.get("signal", ""))
            if is_clock_vcd_signal(sig):
                continue
            parts.append(
                f"- {sig} @ t={ev['time']}: {ev['value']} "
                f"(Δ={ev['delta_to_failure']} ps before failure)"
            )

    sigs = vcd_summary.get("signals", [])[:40]
    if sigs:
        parts.append("\n## Available signals (partial)")
        parts.extend(f"- {s}" for s in sigs)

    results = vcd_summary.get("results", {})
    for sig, info in list(results.items())[:6]:
        if is_clock_vcd_signal(sig):
            continue
        parts.append(f"\n## Waveform: {sig}")
        parts.extend(info.get("lines", [])[:80])

    return "\n".join(parts).strip()


def _format_prior_rationale(prior_rationales: list[str] | None) -> str:
    if not prior_rationales:
        return ""
    latest = [r.strip() for r in prior_rationales if r.strip()][-1:]
    if not latest:
        return ""
    return "## Previous iteration rationale (prioritize this)\n" + latest[0]


def build_chipbench_fix_prompt(
    *,
    prob_id: str,
    spec_text: str,
    current_sv: str,
    sim_stdout: str,
    sim_stderr: str,
    vcd_summary: dict[str, Any] | None,
    connection_map: dict[str, Any] | None = None,
    structured_feedback: StructuredFeedback | dict[str, Any] | None = None,
    error_kind: ErrorKind | None = None,
    prior_rationales: list[str] | None = None,
    formal_summary: dict[str, Any] | None = None,
) -> tuple[str, ErrorKind]:
    if isinstance(structured_feedback, dict):
        kind = error_kind or structured_feedback.get("error_kind", "unknown")
        feedback_text = _format_feedback_from_dict(structured_feedback)
    elif structured_feedback is not None:
        kind = error_kind or structured_feedback.error_kind
        feedback_text = format_structured_feedback(structured_feedback)
    else:
        kind = error_kind or "unknown"
        feedback_text = ""

    kind = kind or "unknown"
    error_guidance = ERROR_PROMPTS.get(kind, ERROR_PROMPTS["unknown"])
    spec_brief = _truncate_middle(
        strip_buggy_module_from_prompt(spec_text), 4000, label="spec"
    )
    vcd_text = _truncate_middle(_format_vcd_summary(vcd_summary), 3000, label="waveform evidence")
    map_text = _truncate_middle(
        format_connection_map_for_llm(connection_map) or "",
        2000,
        label="connection map",
    )
    formal_text = _truncate_middle(
        format_formal_for_llm(formal_summary) or "",
        1500,
        label="formal evidence",
    )
    prior_memory = _truncate_middle(
        _format_prior_rationale(prior_rationales),
        1500,
        label="previous rationale",
    )
    numbered_current = _add_line_numbers(current_sv)

    raw_sim = _truncate_middle(
        (sim_stdout or "").strip()
        + (("\n[stderr]\n" + sim_stderr.strip()) if (sim_stderr or "").strip() else ""),
        1500,
        label="simulation output",
    )

    prompt = f"""You are debugging a Verilog RTL module called TopModule.

## Problem
{prob_id}

## Error type
{kind}

## Fix strategy
{error_guidance}

{prior_memory}

## Spec (from prompt file)
{spec_brief}

## Current candidate RTL (line-numbered — fix this module)
```verilog
{numbered_current}
```

## Structured tool feedback
```text
{feedback_text.strip() if feedback_text else "(none — see raw simulation output below)"}
```

## Connection map (testbench wiring — use for waveform interpretation)
```text
{map_text if map_text else "(not available)"}
```

## Raw simulation output
```text
{raw_sim}
```

## Waveform evidence
```text
{vcd_text if vcd_text else "(no VCD summary available)"}
```

## Formal verification evidence (SymbiYosys)
```text
{formal_text if formal_text else "(formal not run or passed)"}
```

## Task
- Output in TWO sections:

## Rationale
3-8 bullet points describing:
- the suspected bug (cite line numbers from the numbered RTL)
- evidence from structured feedback and waveform causal trace
- what change you made

## FixedTopModule
A FULL corrected `TopModule` implementation (verilog). Put it in a single fenced ```verilog block.
"""
    if len(prompt) > CHIPBENCH_MAX_PROMPT_CHARS:
        prompt = _truncate_middle(prompt, CHIPBENCH_MAX_PROMPT_CHARS, label="fix prompt")
    return prompt, kind  # type: ignore[return-value]


def fix_with_cursor_sdk(
    *,
    prob_id: str,
    spec_text: str,
    current_sv: str,
    sim_stdout: str,
    sim_stderr: str,
    vcd_summary: dict[str, Any] | None,
    connection_map: dict[str, Any] | None = None,
    structured_feedback: StructuredFeedback | dict[str, Any] | None = None,
    error_kind: ErrorKind | None = None,
    prior_rationales: list[str] | None = None,
    model: str = "composer-2.5",
    formal_summary: dict[str, Any] | None = None,
    cursor_session: CursorPromptSession | None = None,
    prompt_artifact_path: Path | None = None,
) -> FixResult:
    """
    Use Cursor (SDK bridge or REST API) to propose a corrected `TopModule`.

    Requires ``CURSOR_API_KEY``. Pass ``cursor_session`` to reuse one REST cloud
    agent per problem (see ``CursorPromptSession``).
    """
    if "CURSOR_API_KEY" not in os.environ:
        raise RuntimeError("CURSOR_API_KEY is not set in environment.")

    prompt, _kind = build_chipbench_fix_prompt(
        prob_id=prob_id,
        spec_text=spec_text,
        current_sv=current_sv,
        sim_stdout=sim_stdout,
        sim_stderr=sim_stderr,
        vcd_summary=vcd_summary,
        connection_map=connection_map,
        structured_feedback=structured_feedback,
        error_kind=error_kind,
        prior_rationales=prior_rationales,
        formal_summary=formal_summary,
    )
    print(
        f"[{prob_id}] Cursor fix prompt size: {len(prompt)} chars "
        f"(limit {CHIPBENCH_MAX_PROMPT_CHARS})",
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
        raw, transport = cursor_prompt(
            prompt,
            model=model,
            api_key=os.environ["CURSOR_API_KEY"],
            workspace=str(REPO_ROOT),
            timeout_s=600,
            prompt_artifact_path=prompt_artifact_path,
        )
    fixed = _extract_topmodule_sv(raw)
    if not fixed:
        raw_path: Path | None = None
        if prompt_artifact_path is not None:
            raw_path = prompt_artifact_path.with_name(
                prompt_artifact_path.stem + "_raw_response.txt"
            )
            raw_path.write_text(raw or "(empty response)", encoding="utf-8")
        excerpt = (raw or "").strip()[:800]
        raise RuntimeError(
            "Cursor response did not contain a parsable TopModule."
            + (f" Raw excerpt saved to {raw_path.name}." if raw_path else "")
            + (f" Excerpt: {excerpt!r}" if excerpt else " Response was empty.")
        )

    rationale = _extract_rationale(raw)
    return FixResult(
        fixed_sv=fixed,
        rationale=rationale,
        raw_text=raw,
        transport=transport,
    )


def _format_feedback_from_dict(data: dict[str, Any]) -> str:
    """Reconstruct formatted feedback from a serialized StructuredFeedback dict."""
    lines: list[str] = [f"error_kind: {data.get('error_kind', 'unknown')}"]

    compile_block = data.get("compile")
    if compile_block and not compile_block.get("success", True):
        lines.append("\n## Compile errors")
        for err in compile_block.get("errors", []):
            if err.get("type") == "warning":
                continue
            hint = err.get("hint")
            hint_s = f" — hint: {hint}" if hint else ""
            lines.append(
                f"- L{err.get('line')} [{err.get('type')}]: {err.get('message')}{hint_s}"
            )

    sim_block = data.get("simulation")
    if sim_block:
        cb = sim_block.get("chipbench")
        if cb:
            lines.append("\n## ChipBench regression")
            lines.append(f"- mismatches: {cb.get('mismatches')} / {cb.get('samples')} samples")
            if cb.get("first_mismatch_time_ps") is not None:
                lines.append(f"- first_mismatch_time_ps: {cb['first_mismatch_time_ps']}")
        for f in sim_block.get("failures", [])[:10]:
            lines.append(
                f"- {f.get('signal')}: expected={f.get('expected')} actual={f.get('actual')}"
            )

    formal_block = data.get("formal")
    if formal_block and formal_block.get("status") not in (None, "skipped", "pass"):
        lines.append("\n## Formal verification")
        lines.append(f"- status: {formal_block.get('status')}")
        if formal_block.get("failing_assertion"):
            lines.append(f"- failing_assertion: {formal_block['failing_assertion']}")

    return "\n".join(lines)
