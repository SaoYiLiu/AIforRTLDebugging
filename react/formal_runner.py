"""
Run SymbiYosys on auto-generated formal wrappers and collect counterexample evidence.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import mcp_server  # noqa: E402
from react.formal_generator import FormalMode, write_sby_file  # noqa: E402
from react.vcd_trace import build_vcd_debug_summary, format_causal_chain_for_llm  # noqa: E402

FormalStatus = Literal["pass", "fail", "error", "skipped"]


@dataclass
class FormalRunResult:
    status: FormalStatus
    passed: bool
    mode: str
    depth: int
    returncode: int | None
    failing_assertion: str | None
    stdout_excerpt: str
    trace_vcd: str | None
    cex_summary: dict[str, Any] | None
    sby_file: str | None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_sby_stdout(stdout: str, returncode: int) -> tuple[FormalStatus, str | None]:
    """Return (status, failing_assertion_line)."""
    text = stdout or ""

    if "DONE (PASS" in text or re.search(r"returned pass", text, re.IGNORECASE):
        return "pass", None

    if "DONE (FAIL" in text or re.search(r"Status:\s*failed", text, re.IGNORECASE):
        failing = _extract_failing_assertion(text)
        return "fail", failing

    if "DONE (ERROR" in text or returncode not in (0, None):
        failing = _extract_failing_assertion(text)
        if failing and "assert" in failing.lower():
            return "fail", failing
        return "error", failing

    if returncode == 0:
        return "pass", None

    return "error", _extract_failing_assertion(text)


def _extract_failing_assertion(stdout: str) -> str | None:
    patterns = [
        r"(Assert failed[^\n]*)",
        r"(Assertion failed[^\n]*)",
        r"(BMC failed[^\n]*)",
        r"(ERROR:[^\n]*assert[^\n]*)",
        r"(Unreached cover[^\n]*)",
    ]
    for pat in patterns:
        m = re.search(pat, stdout, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    for line in stdout.splitlines():
        low = line.lower()
        if "assert" in low and ("fail" in low or "error" in low):
            return line.strip()
    return None


def _stdout_excerpt(stdout: str, *, max_lines: int = 40) -> str:
    lines = (stdout or "").splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[-max_lines:])


def _find_cex_vcd(formal_dir: Path, job_name: str = "TopModule") -> Path | None:
    candidates = [
        formal_dir / job_name / "engine_0" / "trace.vcd",
        formal_dir / job_name / "engine_0" / "trace_induct.vcd",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def run_formal_check(
    *,
    prob_id: str,
    dut_sv: str,
    formal_dir: Path,
    project_root: Path,
    mode: FormalMode = "bmc",
    depth: int = 20,
    timeout_s: int | None = 600,
) -> FormalRunResult:
    """
    Copy current DUT into formal_dir, run sby, and summarize any counterexample VCD.
    """
    formal_dir.mkdir(parents=True, exist_ok=True)
    dut_path = formal_dir / "TopModule.sv"
    sby_path = formal_dir / "TopModule.sby"

    dut_path.write_text(dut_sv, encoding="utf-8")
    write_sby_file(sby_path, mode=mode, depth=depth)

    formal_wrapper = formal_dir / "TopModule_formal.sv"
    if not formal_wrapper.is_file():
        return FormalRunResult(
            status="skipped",
            passed=False,
            mode=mode,
            depth=depth,
            returncode=None,
            failing_assertion=None,
            stdout_excerpt="",
            trace_vcd=None,
            cex_summary=None,
            sby_file=None,
            error="TopModule_formal.sv not found; generate wrapper first.",
        )

    try:
        rel_sby = sby_path.relative_to(project_root).as_posix()
    except ValueError:
        rel_sby = str(sby_path)

    print(f"[{prob_id}] Running formal ({mode} depth={depth})...", flush=True)
    effective_timeout = timeout_s if timeout_s and timeout_s > 0 else None
    if effective_timeout:
        print(f"[{prob_id}] Formal timeout: {effective_timeout}s", flush=True)
    raw = mcp_server.run_sby(rel_sby, force=True, timeout_s=effective_timeout)
    stdout = raw.get("stdout") or ""
    rc = raw.get("returncode")

    if raw.get("timed_out"):
        print(f"[{prob_id}] Formal TIMEOUT after {effective_timeout}s — skipping CEX", flush=True)
        return FormalRunResult(
            status="error",
            passed=False,
            mode=mode,
            depth=depth,
            returncode=rc,
            failing_assertion=None,
            stdout_excerpt=_stdout_excerpt(stdout),
            trace_vcd=None,
            cex_summary=None,
            sby_file=str(sby_path),
            error=f"SymbiYosys timed out after {effective_timeout}s",
        )

    status, failing = parse_sby_stdout(stdout, rc if rc is not None else 1)

    trace_vcd: Path | None = None
    cex_summary: dict[str, Any] | None = None

    if status == "fail":
        trace_vcd = _find_cex_vcd(formal_dir)
        if trace_vcd:
            cex_dst = formal_dir / "formal_cex.vcd"
            shutil.copy2(trace_vcd, cex_dst)
            trace_vcd = cex_dst
            cex_summary = build_vcd_debug_summary(trace_vcd, stdout, connection_map=None)
            if cex_summary.get("ok") and cex_summary.get("causal_chain"):
                print(
                    f"[{prob_id}] Formal FAIL — CEX trace has "
                    f"{len(cex_summary['causal_chain'])} events",
                    flush=True,
                )
        else:
            print(f"[{prob_id}] Formal FAIL — no trace.vcd found", flush=True)
    elif status == "pass":
        print(f"[{prob_id}] Formal PASS ({mode})", flush=True)
    else:
        print(f"[{prob_id}] Formal ERROR (rc={rc})", flush=True)

    return FormalRunResult(
        status=status,
        passed=(status == "pass"),
        mode=mode,
        depth=depth,
        returncode=rc,
        failing_assertion=failing,
        stdout_excerpt=_stdout_excerpt(stdout),
        trace_vcd=str(trace_vcd) if trace_vcd else None,
        cex_summary=cex_summary if cex_summary and cex_summary.get("ok") else None,
        sby_file=str(sby_path),
        error=raw.get("error") if status == "error" else None,
    )


def format_formal_for_llm(result: FormalRunResult | dict[str, Any] | None) -> str:
    if not result:
        return ""

    if isinstance(result, FormalRunResult):
        data = result.to_dict()
    else:
        data = result

    status = data.get("status")
    if status in (None, "skipped"):
        return ""

    lines = [
        f"formal_status: {status}",
        f"mode: {data.get('mode')} depth={data.get('depth')}",
    ]
    if data.get("failing_assertion"):
        lines.append(f"failing_assertion: {data['failing_assertion']}")
    if data.get("error"):
        lines.append(f"error: {data['error']}")

    excerpt = (data.get("stdout_excerpt") or "").strip()
    if excerpt:
        lines.append("\n## sby stdout (tail)")
        lines.append(excerpt)

    cex = data.get("cex_summary") or {}
    chain = cex.get("causal_chain") or []
    if chain:
        lines.append("\n## Formal counterexample (causal trace)")
        lines.append(format_causal_chain_for_llm(chain))

    results = cex.get("results") or {}
    for sig, info in list(results.items())[:4]:
        from react.vcd_trace import is_clock_vcd_signal

        if is_clock_vcd_signal(sig):
            continue
        lines.append(f"\n## CEX waveform: {sig}")
        for line in info.get("lines", [])[:40]:
            lines.append(line)

    return "\n".join(lines).strip()
