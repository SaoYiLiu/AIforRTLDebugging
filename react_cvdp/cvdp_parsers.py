from __future__ import annotations

import re
from dataclasses import dataclass, field

from react.parsers import (
    CompileError,
    CompileResult,
    SimFailure,
    SimResult,
    StructuredFeedback,
    infer_error_kind,
)


@dataclass
class CocotbFailure:
    test_name: str | None = None
    case_name: str | None = None
    signal: str | None = None
    expected: str | None = None
    actual: str | None = None
    time_ns: float | None = None
    message: str = ""


@dataclass
class CvdpHarnessResult:
    passed: bool
    compile_failed: bool
    failures: list[CocotbFailure] = field(default_factory=list)
    tests_passed: int | None = None
    tests_failed: int | None = None
    raw_output: str = ""


_RE_ASSERT = re.compile(
    r"AssertionError:\s*(.+?)(?:\n|$)",
    re.MULTILINE,
)
_RE_TEST_SUMMARY = re.compile(
    r"TESTS=(\d+)\s+PASS=(\d+)\s+FAIL=(\d+)",
)
_RE_CARRY = re.compile(
    r"Expected Carry Out:\s*(\S+),\s*Actual Carry Out:\s*(\S+)",
    re.IGNORECASE,
)
_RE_SUM = re.compile(
    r"Expected Sum:\s*(\S+),\s*Actual Sum:\s*(\S+)",
    re.IGNORECASE,
)
_RE_CASE = re.compile(
    r"Running test case:\s*(.+)$",
    re.MULTILINE,
)
_RE_IVERILOG_FAIL = re.compile(
    r"CalledProcessError: Command '\['iverilog'",
)


def parse_cvdp_harness_output(stdout: str, stderr: str, returncode: int) -> CvdpHarnessResult:
    combined = (stdout or "") + "\n" + (stderr or "")
    compile_failed = bool(_RE_IVERILOG_FAIL.search(combined)) or (
        "returned non-zero exit status 1" in combined and "iverilog" in combined
    )

    failures: list[CocotbFailure] = []
    current_case: str | None = None
    for line in combined.splitlines():
        cm = _RE_CASE.search(line)
        if cm:
            current_case = cm.group(1).strip()

        sm = _RE_SUM.search(line)
        if sm:
            expected, actual = sm.group(1), sm.group(2)
            if expected != actual:
                failures.append(
                    CocotbFailure(
                        case_name=current_case,
                        signal="sum",
                        expected=expected,
                        actual=actual,
                        message=line.strip(),
                    )
                )

        cm2 = _RE_CARRY.search(line)
        if cm2:
            expected, actual = cm2.group(1), cm2.group(2)
            if expected != actual:
                failures.append(
                    CocotbFailure(
                        case_name=current_case,
                        signal="carry_out",
                        expected=expected,
                        actual=actual,
                        message=line.strip(),
                    )
                )

    for am in _RE_ASSERT.finditer(combined):
        msg = am.group(1).strip()
        if any(f.message == msg for f in failures):
            continue
        failures.append(CocotbFailure(case_name=current_case, message=msg))

    tests_passed = tests_failed = None
    tm = _RE_TEST_SUMMARY.search(combined)
    if tm:
        tests_passed = int(tm.group(2))
        tests_failed = int(tm.group(3))

    passed = returncode == 0 and not compile_failed
    if tests_failed is not None:
        passed = passed and tests_failed == 0
    elif failures:
        passed = False

    return CvdpHarnessResult(
        passed=passed,
        compile_failed=compile_failed,
        failures=failures,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        raw_output=combined.strip(),
    )


def to_structured_feedback(result: CvdpHarnessResult) -> StructuredFeedback:
    compile_result: CompileResult | None = None
    if result.compile_failed:
        compile_result = CompileResult(
            success=False,
            errors=[
                CompileError(
                    line=0,
                    column=None,
                    type="compile",
                    message="iverilog/cocotb build failed (see harness log)",
                    hint="Fix syntax/elaboration errors before debugging logic.",
                )
            ],
            raw_output=result.raw_output,
        )

    sim_failures: list[SimFailure] = []
    for f in result.failures:
        sig = f.signal or f.case_name or "cocotb"
        sim_failures.append(
            SimFailure(
                cycle=None,
                time_ns=int(f.time_ns) if f.time_ns is not None else None,
                signal=sig,
                expected=f.expected or "?",
                actual=f.actual or f.message,
            )
        )

    sim_result = SimResult(
        passed=result.passed,
        failures=sim_failures,
        chipbench=None,
        raw_output=result.raw_output,
    )

    error_kind = infer_error_kind(compile_result, sim_result)
    return StructuredFeedback(
        error_kind=error_kind,
        compile=compile_result,
        simulation=sim_result,
    )


def format_cvdp_harness_feedback(result: CvdpHarnessResult) -> str:
    lines: list[str] = []
    if result.compile_failed:
        lines.append("error_kind: compile")
        lines.append("\n## Harness compile failure")
        lines.append("- iverilog/cocotb build failed before tests ran")
    else:
        lines.append("error_kind: logic" if result.failures else "error_kind: unknown")
    if result.tests_passed is not None:
        lines.append(
            f"\n## Cocotb summary\n- pass={result.tests_passed} fail={result.tests_failed or 0}"
        )
    if result.failures:
        lines.append("\n## Cocotb failures")
        for f in result.failures[:15]:
            parts = []
            if f.case_name:
                parts.append(f.case_name)
            if f.signal:
                parts.append(f"signal={f.signal}")
            if f.expected is not None and f.actual is not None:
                parts.append(f"expected={f.expected} actual={f.actual}")
            if f.message and not parts:
                parts.append(f.message)
            lines.append("- " + " | ".join(parts))
    return "\n".join(lines)
