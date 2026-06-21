from __future__ import annotations

import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IverilogAdapterResult:
    ran: bool
    passed: bool
    stdout: str
    stderr: str
    reason: str | None = None


def _find_verif_tb(context_files: dict[str, str]) -> str | None:
    for path in sorted(context_files.keys()):
        if path.startswith("verif/") and path.endswith((".sv", ".v")):
            return path
    return None


def _tb_top_module(tb_text: str) -> str | None:
    m = re.search(r"^\s*module\s+(\w+)", tb_text, re.MULTILINE)
    return m.group(1) if m else None


def run_iverilog_adapter(
    workspace_harness_dir: Path,
    context_files: dict[str, str],
    *,
    timeout_s: int = 120,
) -> IverilogAdapterResult:
    """
    Optional fast pre-check when the problem includes a SystemVerilog ``verif/`` testbench.

    Non-agentic cid016 problems typically use cocotb-only harnesses — this returns ``ran=False``.
    """
    tb_rel = _find_verif_tb(context_files)
    if not tb_rel:
        return IverilogAdapterResult(
            ran=False,
            passed=False,
            stdout="",
            stderr="",
            reason="no verif/ testbench in context",
        )

    tb_path = workspace_harness_dir / tb_rel
    if not tb_path.is_file():
        tb_path = workspace_harness_dir.parent / "context" / tb_rel
    if not tb_path.is_file():
        return IverilogAdapterResult(
            ran=False,
            passed=False,
            stdout="",
            stderr="",
            reason=f"testbench not staged: {tb_rel}",
        )

    tb_text = tb_path.read_text(encoding="utf-8", errors="ignore")
    top = _tb_top_module(tb_text)
    if not top:
        return IverilogAdapterResult(
            ran=False,
            passed=False,
            stdout="",
            stderr="",
            reason="could not detect TB top module",
        )

    rtl_sources = sorted(
        p for p in context_files if p.startswith("rtl/") and p.endswith((".sv", ".v"))
    )
    sources: list[str] = []
    cwd = workspace_harness_dir if workspace_harness_dir.is_absolute() else workspace_harness_dir.absolute()
    for rtl_rel in rtl_sources:
        src = workspace_harness_dir / rtl_rel
        if src.is_file():
            sources.append(str(src if src.is_absolute() else src.absolute()))
    sources.append(str(tb_path if tb_path.is_absolute() else tb_path.absolute()))

    out_bin = workspace_harness_dir / "rundir" / "iverilog_adapter.out"
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    out_path = str(out_bin if out_bin.is_absolute() else out_bin.absolute())

    compile_cmd = ["iverilog", "-g2012", "-o", out_path, "-s", top, *sources]
    compile_proc = subprocess.run(
        compile_cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout_s,
    )
    run_rc = 1
    run_stdout = ""
    run_stderr = ""
    if compile_proc.returncode == 0:
        run_proc = subprocess.run(
            ["vvp", out_path],
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout_s,
        )
        run_rc = run_proc.returncode
        run_stdout = run_proc.stdout or ""
        run_stderr = run_proc.stderr or ""

    stdout = run_stdout + "\n" + (compile_proc.stdout or "")
    stderr = run_stderr + "\n" + (compile_proc.stderr or "")

    passed = compile_proc.returncode == 0 and run_rc == 0
    return IverilogAdapterResult(
        ran=True,
        passed=passed,
        stdout=(
            "$ " + " ".join(shlex.quote(arg) for arg in compile_cmd) + "\n" + stdout
        ).strip(),
        stderr=stderr.strip(),
        reason=None,
    )
