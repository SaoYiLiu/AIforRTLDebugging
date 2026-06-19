"""
Parse iverilog/vvp output into structured, LLM-friendly feedback.

Inspired by veridebugger/backend/parsers.py; extended for ChipBench testbench formats.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Literal

ErrorKind = Literal["syntax", "binding", "type", "port", "range", "compile", "logic", "unknown"]


@dataclass
class CompileError:
    line: int
    column: int | None
    type: str
    message: str
    hint: str | None = None


@dataclass
class CompileResult:
    success: bool
    errors: list[CompileError]
    raw_output: str


@dataclass
class ChipBenchMismatch:
    mismatches: int
    samples: int
    first_mismatch_time_ps: int | None = None
    output_signal: str | None = None
    output_mismatch_count: int | None = None


@dataclass
class SimFailure:
    cycle: int | None
    time_ns: int | None
    signal: str
    expected: str
    actual: str


@dataclass
class SimResult:
    passed: bool
    failures: list[SimFailure]
    chipbench: ChipBenchMismatch | None
    raw_output: str


@dataclass
class StructuredFeedback:
    """Combined compile + simulation feedback for one iteration."""

    error_kind: ErrorKind
    compile: CompileResult | None = None
    simulation: SimResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return feedback_to_dict(self)


def classify_error(message: str) -> str:
    message_lower = message.lower()
    if "bind" in message_lower or "undeclared" in message_lower:
        return "binding"
    if "type" in message_lower or "width" in message_lower:
        return "type"
    if "port" in message_lower:
        return "port"
    if "range" in message_lower:
        return "range"
    return "error"


def generate_hint(err_type: str, _message: str = "") -> str | None:
    hints = {
        "binding": "Check that all signals are declared as 'wire' or 'reg' before use",
        "syntax": "Check for missing semicolons, mismatched begin/end, or invalid keywords",
        "type": "Check bit widths match between assignments and declarations",
        "port": "Check module port declarations match instantiation",
        "range": "Check array/vector indices are within declared bounds",
        "error": "Review the error message and fix the referenced line",
    }
    return hints.get(err_type)


def parse_iverilog_compile(output: str, returncode: int) -> CompileResult:
    """Parse iverilog compilation output."""
    errors: list[CompileError] = []

    pattern = r"([^:\n]+):(\d+):\s*(error|warning|syntax error):\s*(.+)"
    for match in re.finditer(pattern, output, re.MULTILINE):
        _filename, line, err_type, message = match.groups()
        if "syntax" in err_type:
            normalized = "syntax"
        elif "warning" in err_type:
            normalized = "warning"
        else:
            normalized = classify_error(message)
        hint = generate_hint(normalized, message)
        errors.append(
            CompileError(
                line=int(line),
                column=None,
                type=normalized,
                message=message.strip(),
                hint=hint,
            )
        )

    simple_pattern = r"([^:\n]+):(\d+):\s*syntax error"
    for match in re.finditer(simple_pattern, output, re.MULTILINE):
        line_no = int(match.group(2))
        if not any(e.line == line_no for e in errors):
            errors.append(
                CompileError(
                    line=line_no,
                    column=None,
                    type="syntax",
                    message="Syntax error",
                    hint=generate_hint("syntax"),
                )
            )

    success = returncode == 0 and not any(e.type != "warning" for e in errors)
    return CompileResult(success=success, errors=errors, raw_output=output)


def parse_chipbench_mismatches(output: str) -> ChipBenchMismatch | None:
    m = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)\s*samples", output)
    if not m:
        return None

    mismatches = int(m.group(1))
    samples = int(m.group(2))

    first_time = None
    tm = re.search(
        r"First mismatch occurred at time\s+(\d+)",
        output,
        re.IGNORECASE,
    )
    if tm:
        first_time = int(tm.group(1))

    output_signal = None
    output_mismatch_count = None
    hm = re.search(
        r"Output\s+'([^']+)'\s+has\s+(\d+)\s+mismatches",
        output,
        re.IGNORECASE,
    )
    if hm:
        output_signal = hm.group(1)
        output_mismatch_count = int(hm.group(2))

    return ChipBenchMismatch(
        mismatches=mismatches,
        samples=samples,
        first_mismatch_time_ps=first_time,
        output_signal=output_signal,
        output_mismatch_count=output_mismatch_count,
    )


def parse_vvp_simulation(output: str, returncode: int) -> SimResult:
    """Parse vvp simulation output (VeriDebug + ChipBench patterns)."""
    failures: list[SimFailure] = []
    passed = True

    fail_pattern = (
        r"\[FAIL\]\s*(\w+)=(\S+)\s+expected=(\S+)\s+actual=(\S+)"
        r"(?:\s+cycle=(\d+))?(?:\s+time=(\d+))?"
    )
    for match in re.finditer(fail_pattern, output):
        signal, _, expected, actual, cycle, time_ns = match.groups()
        failures.append(
            SimFailure(
                cycle=int(cycle) if cycle else None,
                time_ns=int(time_ns) if time_ns else None,
                signal=signal,
                expected=expected,
                actual=actual,
            )
        )
        passed = False

    chipbench = parse_chipbench_mismatches(output)
    if chipbench is not None and chipbench.mismatches > 0:
        passed = False

    done_match = re.search(r"\[DONE\]\s*passed=(\d+)\s+failed=(\d+)", output)
    if done_match and int(done_match.group(2)) > 0:
        passed = False

    if returncode != 0:
        passed = False

    if re.search(r"\$stop|\$fatal|ERROR|TIMEOUT", output, re.IGNORECASE):
        passed = False

    if re.search(r"FAIL:", output) and not re.search(r"Mismatches:\s*0\b", output):
        passed = False

    if (
        re.search(r"PASS|All tests passed", output, re.IGNORECASE)
        and not failures
        and (chipbench is None or chipbench.mismatches == 0)
        and not re.search(r"FAIL", output, re.IGNORECASE)
    ):
        passed = True

    return SimResult(
        passed=passed,
        failures=failures,
        chipbench=chipbench,
        raw_output=output,
    )


def parse_iverilog_result(result: dict[str, Any]) -> StructuredFeedback:
    """Parse a full `run_iverilog` result dict into structured feedback."""
    compile_block = result.get("compile") or {}
    run_block = result.get("run") or {}

    compile_out = (compile_block.get("stdout") or "") + "\n" + (compile_block.get("stderr") or "")
    compile_rc = compile_block.get("returncode", 1)
    compile_result = parse_iverilog_compile(compile_out, compile_rc)

    sim_result: SimResult | None = None
    if run_block:
        run_out = (run_block.get("stdout") or "") + "\n" + (run_block.get("stderr") or "")
        sim_result = parse_vvp_simulation(run_out, run_block.get("returncode", 1))

    error_kind = infer_error_kind(compile_result, sim_result)
    return StructuredFeedback(
        error_kind=error_kind,
        compile=compile_result,
        simulation=sim_result,
    )


def infer_error_kind(
    compile_result: CompileResult | None,
    sim_result: SimResult | None,
) -> ErrorKind:
    if compile_result and not compile_result.success:
        for err in compile_result.errors:
            if err.type == "warning":
                continue
            if err.type in ("syntax", "binding", "type", "port", "range"):
                return err.type  # type: ignore[return-value]
        return "compile"

    if sim_result:
        if sim_result.chipbench and sim_result.chipbench.mismatches > 0:
            return "logic"
        if sim_result.failures:
            return "logic"
        if not sim_result.passed:
            return "logic"

    return "unknown"


def feedback_to_dict(feedback: StructuredFeedback) -> dict[str, Any]:
    def _compile(c: CompileResult) -> dict[str, Any]:
        return {
            "success": c.success,
            "errors": [asdict(e) for e in c.errors],
            "raw_output": c.raw_output,
        }

    def _sim(s: SimResult) -> dict[str, Any]:
        return {
            "passed": s.passed,
            "failures": [asdict(f) for f in s.failures],
            "chipbench": asdict(s.chipbench) if s.chipbench else None,
            "raw_output": s.raw_output,
        }

    return {
        "error_kind": feedback.error_kind,
        "compile": _compile(feedback.compile) if feedback.compile else None,
        "simulation": _sim(feedback.simulation) if feedback.simulation else None,
    }


def format_structured_feedback(feedback: StructuredFeedback) -> str:
    """Render structured feedback as compact text for LLM prompts."""
    lines: list[str] = [f"error_kind: {feedback.error_kind}"]

    if feedback.compile and not feedback.compile.success:
        lines.append("\n## Compile errors")
        for err in feedback.compile.errors:
            if err.type == "warning":
                continue
            hint = f" — hint: {err.hint}" if err.hint else ""
            lines.append(f"- L{err.line} [{err.type}]: {err.message}{hint}")

    if feedback.simulation:
        sim = feedback.simulation
        if sim.chipbench:
            cb = sim.chipbench
            lines.append("\n## ChipBench regression")
            lines.append(f"- mismatches: {cb.mismatches} / {cb.samples} samples")
            if cb.first_mismatch_time_ps is not None:
                lines.append(f"- first_mismatch_time_ps: {cb.first_mismatch_time_ps}")
            if cb.output_signal:
                lines.append(
                    f"- output '{cb.output_signal}': {cb.output_mismatch_count} mismatches"
                )
        if sim.failures:
            lines.append("\n## Simulation failures")
            for f in sim.failures[:10]:
                when = ""
                if f.time_ns is not None:
                    when = f" @ time={f.time_ns}"
                elif f.cycle is not None:
                    when = f" @ cycle={f.cycle}"
                lines.append(
                    f"- {f.signal}: expected={f.expected} actual={f.actual}{when}"
                )

    return "\n".join(lines)


def detect_mismatches(sim_stdout: str) -> int | None:
    """Return mismatch count from ChipBench output, or None if not found."""
    cb = parse_chipbench_mismatches(sim_stdout)
    return cb.mismatches if cb else None
