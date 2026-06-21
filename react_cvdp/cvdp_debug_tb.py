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
)
from react.parsers import StructuredFeedback, format_structured_feedback

from react_cvdp.cvdp_cursor_fixer import (
    _cocotb_test_excerpt,
    _format_raw_harness,
    _max_cursor_prompt_chars,
    _prompt_size,
    _truncate_middle,
)

REPO_ROOT = Path(__file__).absolute().parents[1]


@dataclass(frozen=True)
class DebugTbResult:
    """Result of the optional debug-sim Cursor call."""

    requested: bool
    tb_sv: str
    tb_top: str
    rationale: str
    decision_rationale: str
    raw_text: str
    transport: str = "bridge"


def _extract_section(text: str, heading: str) -> str:
    m = re.search(
        rf"##\s*{re.escape(heading)}\s*(.*?)(?=##\s|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    return m.group(1).strip() if m else ""


def _extract_debug_sim_decision(text: str) -> bool | None:
    body = _extract_section(text, "DebugSimDecision").lower()
    if not body:
        return None
    if re.search(r"\buse\s*:\s*yes\b", body) or re.fullmatch(r"yes", body.strip()):
        return True
    if re.search(r"\buse\s*:\s*no\b", body) or re.fullmatch(r"no", body.strip()):
        return False
    return None


def _extract_rationale(text: str) -> str:
    return _extract_section(text, "Rationale")


def _extract_debug_testbench(text: str) -> str:
    body = _extract_section(text, "DebugTestbench") or text
    blocks = re.findall(
        r"```(?:verilog|systemverilog|sv)?\s*(.*?)```",
        body,
        flags=re.DOTALL | re.IGNORECASE,
    )
    for block in blocks:
        if re.search(r"\bmodule\b", block, re.I):
            return block.strip() + "\n"
    blocks = re.findall(
        r"```(?:verilog|systemverilog|sv)?\s*(module[\s\S]*?endmodule)\s*```",
        text,
        flags=re.IGNORECASE,
    )
    if blocks:
        return blocks[0].strip() + "\n"
    return ""


def _format_rtl_ports(current_files: dict[str, str], primary_module: str | None) -> str:
    if not current_files:
        return "(no RTL files)"
    if primary_module:
        for path, content in current_files.items():
            if primary_module in content:
                return f"### {path}\n```verilog\n{content[:3500].strip()}\n```"
    path = sorted(current_files.keys())[0]
    return f"### {path}\n```verilog\n{current_files[path][:3500].strip()}\n```"


def request_debug_testbench_cvdp(
    *,
    problem_id: str,
    spec_text: str,
    current_files: dict[str, str],
    harness_stdout: str,
    harness_stderr: str,
    structured_feedback: StructuredFeedback | None = None,
    harness_dir: Path | None = None,
    primary_module: str | None = None,
    model: str = "composer-2.5",
    cursor_session: CursorPromptSession | None = None,
    prompt_artifact_path: Path | None = None,
) -> DebugTbResult:
    """
    Separate Cursor call (offered from iter 3+ after harness failure).

    Cursor decides whether a local iverilog/VCD debug sim would help. Only when
    it answers ``use: yes`` does it also author ``## DebugTestbench``.
    """
    if "CURSOR_API_KEY" not in os.environ:
        raise RuntimeError("CURSOR_API_KEY is required for debug testbench generation.")

    enable_http_request_logging()

    feedback_text = (
        format_structured_feedback(structured_feedback)
        if structured_feedback
        else ""
    )
    feedback_text = _truncate_middle(feedback_text.strip(), 2200, label="structured feedback")
    spec_brief = _truncate_middle(spec_text.strip(), 6000, label="task prompt")
    raw_harness = _format_raw_harness(harness_stdout, harness_stderr, limit=6000)
    rtl_excerpt = _format_rtl_ports(current_files, primary_module)
    test_excerpt = ""
    if harness_dir:
        test_excerpt = _truncate_middle(
            _cocotb_test_excerpt(harness_dir),
            4000,
            label="cocotb test excerpt",
        )

    module_hint = primary_module or "the DUT top-level module"
    error_kind = structured_feedback.error_kind if structured_feedback else "unknown"

    prompt = f"""You are helping debug RTL for a CVDP hardware verification benchmark.

**First decide** whether a local **iverilog + VCD** debug simulation would materially help
the next RTL-fix iteration. Only if yes, write a focused SystemVerilog testbench.
Do NOT modify RTL.

## Problem
{problem_id}

## Harness error kind
{error_kind}

## Task description excerpt
{spec_brief}

## DUT RTL (for port/module names — do not edit)
{rtl_excerpt}

Primary module to instantiate: `{module_hint}`

## Structured harness feedback
```text
{feedback_text if feedback_text else "(see harness log below)"}
```

## Raw CVDP harness failure excerpt
```text
{raw_harness}
```

## Cocotb harness source
{test_excerpt if test_excerpt else "(not available)"}

## When to answer **use: no** (skip debug sim)
- Elaboration/synthesis/parameter errors (e.g. `$clog2(0)`); harness log already pinpoints the bug.
- Docker/cocotb compile or import failures that iverilog will not reproduce better.
- Failure is already a single clear expected-vs-actual on outputs; no benefit from waves.
- Design is too complex for a faithful mini-TB (wide buses, AXI, many files, DPI/UVM).
- Prior iterations already show the fix direction without waveform evidence.

## When to answer **use: yes** (write DebugTestbench)
- Functional logic bug with reproducible vectors but unclear **internal** root cause.
- Multi-cycle/FSM behavior where cocotb only reports final output mismatch.
- You can mirror the **specific failing cocotb case** in iverilog-friendly SV.

## Output format

## DebugSimDecision
use: yes | no

## Rationale
3-6 bullets explaining your decision (required for both yes and no).

## DebugTestbench
(Include ONLY when use: yes — otherwise omit this section entirely.)
```verilog
module tb_debug;
  // $dumpfile("wave.vcd"); $dumpvars(0, tb_debug);
  // wire tb_mismatch; $display("First mismatch occurred at time %0t", $time);
  // one failing scenario from harness log
endmodule
```

Requirements when use: yes:
1. Top module name: `tb_debug`
2. Drive the **specific failing test case** (exact inputs/expected outputs).
3. `$dumpfile("wave.vcd");` and `$dumpvars(0, tb_debug);`
4. `tb_mismatch` wire + mismatch time `$display` as above.
5. iverilog-friendly Verilog only (no UVM/DPI/classes).
"""

    max_prompt_chars = _max_cursor_prompt_chars()
    if len(prompt) > max_prompt_chars:
        prompt = _truncate_middle(prompt, max_prompt_chars, label="debug TB prompt")

    print(
        f"[{problem_id}] Debug sim decision prompt: {_prompt_size(prompt)} "
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

    decision = _extract_debug_sim_decision(raw)
    tb_sv = _extract_debug_testbench(raw)
    rationale = _extract_rationale(raw)

    if decision is False or (decision is None and not tb_sv):
        print(
            f"[{problem_id}] Cursor declined debug sim "
            f"(decision={'no' if decision is False else 'no TB'})",
            flush=True,
        )
        return DebugTbResult(
            requested=False,
            tb_sv="",
            tb_top="",
            rationale=rationale,
            decision_rationale=rationale or _extract_section(raw, "DebugSimDecision"),
            raw_text=raw,
            transport=transport,
        )

    if decision is True and not tb_sv:
        print(
            f"[{problem_id}] Cursor chose debug sim but omitted testbench — skipping",
            flush=True,
        )
        return DebugTbResult(
            requested=False,
            tb_sv="",
            tb_top="",
            rationale=rationale,
            decision_rationale="use: yes but no DebugTestbench block was provided",
            raw_text=raw,
            transport=transport,
        )

    tb_top = "tb_debug"
    m = re.search(r"^\s*module\s+(\w+)", tb_sv, re.MULTILINE)
    if m:
        tb_top = m.group(1)

    print(f"[{problem_id}] Cursor requested debug sim (top={tb_top})", flush=True)
    return DebugTbResult(
        requested=True,
        tb_sv=tb_sv,
        tb_top=tb_top,
        rationale=rationale,
        decision_rationale=rationale,
        raw_text=raw,
        transport=transport,
    )


def format_debug_sim_for_llm(
    *,
    iv_result: Any,
    vcd_summary: dict[str, Any] | None,
) -> str:
    """Compact block for the next RTL-fix Cursor prompt."""
    from react.cursor_sdk_fixer import _format_vcd_summary

    parts: list[str] = ["## Local iverilog debug (generated testbench)"]
    if getattr(iv_result, "ran", False):
        parts.append(
            f"compile_rc={iv_result.compile_rc} run_rc={iv_result.run_rc} "
            f"passed={iv_result.passed}"
        )
        if iv_result.stdout.strip():
            parts.append("### iverilog/vvp stdout\n```text\n" + iv_result.stdout[:4000].strip() + "\n```")
        if iv_result.stderr.strip():
            parts.append("### iverilog/vvp stderr\n```text\n" + iv_result.stderr[:2000].strip() + "\n```")
    else:
        parts.append(f"(not run: {getattr(iv_result, 'reason', 'unknown')})")

    vcd_text = _format_vcd_summary(vcd_summary)
    if vcd_text:
        parts.append("### Waveform causal trace\n```text\n" + vcd_text + "\n```")
    return "\n\n".join(parts)


def format_debug_sim_skipped_for_llm(*, tb_result: DebugTbResult) -> str:
    """Note for next RTL-fix prompt when Cursor chose not to run debug sim."""
    reason = tb_result.decision_rationale or tb_result.rationale or "(no rationale)"
    return (
        "## Local iverilog debug\n"
        "Skipped — Cursor judged a local iverilog/VCD sim would not help this failure.\n\n"
        f"```text\n{reason.strip()[:2000]}\n```"
    )
