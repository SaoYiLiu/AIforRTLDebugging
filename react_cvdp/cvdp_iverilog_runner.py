from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import mcp_server


@dataclass(frozen=True)
class CvdpIverilogResult:
    ran: bool
    passed: bool
    compile_rc: int
    run_rc: int | None
    stdout: str
    stderr: str
    vcd_path: Path | None = None
    tb_path: Path | None = None
    reason: str | None = None


def detect_tb_top_module(tb_text: str) -> str | None:
    m = re.search(r"^\s*module\s+(\w+)", tb_text, re.MULTILINE)
    return m.group(1) if m else None


def collect_rtl_sources(harness_dir: Path, patch_targets: list[str]) -> list[Path]:
    seen: set[Path] = set()
    sources: list[Path] = []
    for rel in sorted(patch_targets):
        src = harness_dir / rel
        if src.is_file():
            resolved = src.resolve()
            if resolved not in seen:
                seen.add(resolved)
                sources.append(src)
    rtl_dir = harness_dir / "rtl"
    if rtl_dir.is_dir():
        for src in sorted(rtl_dir.glob("*.sv")) + sorted(rtl_dir.glob("*.v")):
            resolved = src.resolve()
            if resolved not in seen:
                seen.add(resolved)
                sources.append(src)
    return sources


def run_cvdp_debug_sim(
    *,
    harness_dir: Path,
    out_dir: Path,
    patch_targets: list[str],
    tb_sv: str,
    iteration: int,
    timeout_s: int = 120,
) -> CvdpIverilogResult:
    """
    Compile patched RTL + generated debug testbench with iverilog and run vvp.

    Expects ``tb_sv`` to dump ``wave.vcd`` in the simulation cwd (``debug/``).
    """
    debug_dir = out_dir / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    tb_path = debug_dir / f"tb_debug_iter_{iteration}.sv"
    tb_path.write_text(tb_sv, encoding="utf-8")

    top = detect_tb_top_module(tb_sv)
    if not top:
        return CvdpIverilogResult(
            ran=False,
            passed=False,
            compile_rc=1,
            run_rc=None,
            stdout="",
            stderr="",
            tb_path=tb_path,
            reason="could not detect testbench top module",
        )

    rtl_sources = collect_rtl_sources(harness_dir, patch_targets)
    if not rtl_sources:
        return CvdpIverilogResult(
            ran=False,
            passed=False,
            compile_rc=1,
            run_rc=None,
            stdout="",
            stderr="",
            tb_path=tb_path,
            reason="no RTL sources found under harness/rtl",
        )

    out_bin = debug_dir / f"iverilog_iter_{iteration}.out"
    cwd = str(debug_dir.resolve())
    source_paths = [str(p.resolve()) for p in rtl_sources] + [str(tb_path.resolve())]

    result = mcp_server.run_iverilog(
        sources=source_paths,
        top=top,
        output=str(out_bin.resolve()),
        run=True,
        cwd=cwd,
        timeout_s=timeout_s,
    )

    compile_rc = int(result["compile"]["returncode"])
    run_block = result.get("run") or {}
    run_rc = run_block.get("returncode")
    stdout = ((run_block.get("stdout") or "") + "\n" + (result["compile"].get("stdout") or "")).strip()
    stderr = ((run_block.get("stderr") or "") + "\n" + (result["compile"].get("stderr") or "")).strip()

    vcd_path = debug_dir / "wave.vcd"
    if not vcd_path.is_file():
        alt = Path(cwd) / "wave.vcd"
        if alt.is_file():
            vcd_path = alt

    wave_copy = out_dir / f"wave_iter_{iteration}.vcd"
    if vcd_path.is_file():
        shutil.copy2(vcd_path, wave_copy)
        vcd_path = wave_copy

    passed = compile_rc == 0 and run_rc == 0
    return CvdpIverilogResult(
        ran=True,
        passed=passed,
        compile_rc=compile_rc,
        run_rc=run_rc,
        stdout=stdout,
        stderr=stderr,
        vcd_path=vcd_path if vcd_path.is_file() else None,
        tb_path=tb_path,
    )
