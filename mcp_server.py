from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

# `vcdvcd` is only needed for the `vcd_to_text` tool.
# Import it lazily inside that tool so the server can start even if users
# haven't installed waveform dependencies yet.


def _import_fastmcp() -> Any:
    """
    Support both import styles:
    - official MCP Python SDK: `from mcp.server.fastmcp import FastMCP`
    - standalone fastmcp:      `from fastmcp import FastMCP`
    """

    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore

        return FastMCP
    except Exception:
        from fastmcp import FastMCP  # type: ignore

        return FastMCP


FastMCP = _import_fastmcp()
mcp = FastMCP(name="RTL Debug Helper (Icarus + VCD + SBY)")

# Repo root (directory containing mcp_server.py). Used to resolve formal paths
# regardless of the MCP server's process cwd.
PROJECT_ROOT = Path(__file__).resolve().parent


def _run(
    args: list[str],
    cwd: str | None = None,
    timeout_s: int | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout_s,
    )
    return {
        "command": " ".join(shlex.quote(a) for a in args),
        "cwd": cwd or os.getcwd(),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


@mcp.tool()
def run_iverilog(
    sources: list[str],
    output: str = "build/a.out",
    top: str | None = None,
    include_dirs: list[str] | None = None,
    defines: dict[str, str | None] | None = None,
    extra_args: list[str] | None = None,
    run: bool = True,
    vvp_args: list[str] | None = None,
    cwd: str | None = None,
    timeout_s: int | None = None,
) -> dict[str, Any]:
    """
    Compile (and optionally run) a Verilog/SystemVerilog testbench using Icarus.

    - **sources**: list of RTL/TB files.
    - **output**: output executable path for `vvp`.
    - **top**: optional top module name (`-s`).
    - **include_dirs**: `-I` include directories.
    - **defines**: macro defines (`-DKEY` or `-DKEY=VALUE`).
    - **extra_args**: extra `iverilog` arguments.
    - **run**: if true, runs `vvp <output>`.
    """

    # Ensure output directory exists (relative to `cwd` where iverilog runs).
    # Use simple joins (not resolve()) so paths with spaces behave predictably.
    if cwd and not Path(output).is_absolute():
        out_dir = Path(cwd) / Path(output).parent
        out_path = Path(cwd) / output
    else:
        out_dir = Path(output).parent
        out_path = Path(output)

    if str(out_dir) not in ("", "."):
        out_dir.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = ["iverilog", "-g2012", "-o", output]
    if top:
        cmd += ["-s", top]
    for inc in include_dirs or []:
        cmd += ["-I", inc]
    for k, v in (defines or {}).items():
        cmd.append(f"-D{k}" if v is None else f"-D{k}={v}")
    cmd += list(extra_args or [])
    cmd += list(sources)

    compile_res = _run(cmd, cwd=cwd, timeout_s=timeout_s)

    run_res: dict[str, Any] | None = None
    if run and compile_res["returncode"] == 0:
        run_cmd = ["vvp", output] + list(vvp_args or [])
        run_res = _run(run_cmd, cwd=cwd, timeout_s=timeout_s)

    return {
        "compile": compile_res,
        "run": run_res,
        "output": str(out_path),
    }


@dataclass(frozen=True)
class _VcdDumpConfig:
    start: int | None
    end: int | None
    max_transitions: int
    format: Literal["transitions", "samples"]
    sample_period: int


def _format_vcd_transitions(
    tv: list[tuple[int, Any]],
    cfg: _VcdDumpConfig,
) -> list[str]:
    start = cfg.start
    end = cfg.end
    lines: list[str] = []
    n = 0
    for t, v in tv:
        if start is not None and t < start:
            continue
        if end is not None and t > end:
            break
        lines.append(f"{t}: {v}")
        n += 1
        if n >= cfg.max_transitions:
            lines.append("... (truncated)")
            break
    return lines


def _format_vcd_samples(
    tv: list[tuple[int, Any]],
    cfg: _VcdDumpConfig,
) -> list[str]:
    if not tv:
        return []

    start = cfg.start if cfg.start is not None else tv[0][0]
    end = cfg.end if cfg.end is not None else tv[-1][0]
    if end < start:
        return []

    period = max(1, cfg.sample_period)
    # Build a cursor over transitions, sampling the last-known value at each step.
    lines: list[str] = []
    i = 0
    cur_v = tv[0][1]
    for t in range(start, end + 1, period):
        while i + 1 < len(tv) and tv[i + 1][0] <= t:
            i += 1
            cur_v = tv[i][1]
        lines.append(f"{t}: {cur_v}")
        if len(lines) >= cfg.max_transitions:
            lines.append("... (truncated)")
            break
    return lines


@mcp.tool()
def vcd_to_text(
    vcd_path: str,
    signals: list[str] | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    max_lines_per_signal: int = 200,
    mode: Literal["transitions", "samples"] = "transitions",
    sample_period: int = 10,
) -> dict[str, Any]:
    """
    Convert a VCD into compact, LLM-readable text snippets for selected signals.

    - **signals**: full hierarchical names as they appear in the VCD (or None to list available signals).
    - **mode**:
        - `transitions`: emit time/value transitions (most useful for debugging)
        - `samples`: emit a sampled timeline using last-known value at each tick
    """

    try:
        from vcdvcd import VCDVCD  # type: ignore
    except Exception as e:
        return {
            "ok": False,
            "error": "Missing Python dependency: vcdvcd. Activate your venv and run `pip install -r requirements.txt`.",
            "detail": str(e),
        }

    path = Path(vcd_path)
    if not path.exists():
        return {"ok": False, "error": f"VCD not found: {vcd_path}"}

    vcd = VCDVCD(str(path), store_tvs=True)

    available = sorted(vcd.signals)
    if not signals:
        # Return just the catalog; waves can be huge.
        return {
            "ok": True,
            "vcd_path": str(path),
            "timescale": getattr(vcd, "timescale", None),
            "signal_count": len(available),
            "signals": available[:500],
            "signals_truncated": len(available) > 500,
        }

    cfg = _VcdDumpConfig(
        start=start_time,
        end=end_time,
        max_transitions=max(1, int(max_lines_per_signal)),
        format=mode,
        sample_period=max(1, int(sample_period)),
    )

    out: dict[str, Any] = {
        "ok": True,
        "vcd_path": str(path),
        "timescale": getattr(vcd, "timescale", None),
        "requested_signals": signals,
        "results": {},
        "missing_signals": [],
    }

    for sig in signals:
        if sig not in vcd.signals:
            out["missing_signals"].append(sig)
            continue

        var = vcd[sig]
        tv = list(getattr(var, "tv", []) or [])

        if mode == "samples":
            lines = _format_vcd_samples(tv, cfg)
        else:
            lines = _format_vcd_transitions(tv, cfg)

        out["results"][sig] = {
            "lines": lines,
            "transition_count": len(tv),
        }

    return out


@mcp.tool()
def trace_vcd_failure(
    vcd_path: str,
    failure_time: int | None = None,
    sim_stdout: str | None = None,
    window: int = 100,
    max_events: int = 20,
) -> dict[str, Any]:
    """
    Trace signal transitions before a simulation failure (causal waveform chain).

    - **failure_time**: VCD time of first failure (ps). If omitted, inferred from
      ChipBench sim output (`First mismatch occurred at time ...`) or first `tb_mismatch`.
    - **sim_stdout**: optional simulation stdout for time inference.
    - **window**: look-back window in VCD time units before failure_time.
    """
    from react.vcd_trace import (  # noqa: WPS433
        build_vcd_debug_summary,
        infer_failure_time_ps,
        trace_vcd_failure as _trace,
    )

    path = Path(vcd_path)
    if not path.exists():
        return {"ok": False, "error": f"VCD not found: {vcd_path}"}

    ft = failure_time
    if ft is None and sim_stdout:
        ft = infer_failure_time_ps(sim_stdout, path)
    if ft is None:
        summary = build_vcd_debug_summary(path, sim_stdout or "", connection_map=None)
        if not summary.get("ok"):
            return summary
        ft = summary.get("failure_time")

    if ft is None:
        return {
            "ok": False,
            "error": "Could not infer failure_time; pass failure_time explicitly.",
            "vcd_path": str(path),
        }

    chain = _trace(path, failure_time=ft, window=window, max_events=max_events)
    return {
        "ok": True,
        "vcd_path": str(path),
        "failure_time": ft,
        "window": window,
        "causal_chain": chain,
        "event_count": len(chain),
    }


def _yosys_version_line() -> str:
    try:
        proc = subprocess.run(
            ["yosys", "-V"],
            text=True,
            capture_output=True,
            timeout=10,
        )
        return (proc.stdout or proc.stderr or "").strip().splitlines()[0]
    except Exception as e:
        return f"(yosys not runnable: {e})"


def _yosys_too_old_for_sby(version_line: str) -> bool:
    # SymbiYosys 0.6x always runs `hierarchy -smtcheck`, which needs a modern
    # YosysHQ Yosys. Ubuntu 22.04 apt ships Yosys 0.9, which will fail.
    if "Yosys 0.9" in version_line or "Yosys 0.1" in version_line:
        return True
    return False


@mcp.tool()
def run_sby(
    sby_file: str,
    cwd: str | None = None,
    extra_args: list[str] | None = None,
    timeout_s: int | None = None,
    force: bool = True,
) -> dict[str, Any]:
    """
    Run SymbiYosys on an `.sby` file.

    - **force**: if true, passes `-f` to overwrite old runs.
    """

    sby_path = (PROJECT_ROOT / sby_file).expanduser().resolve()
    if not sby_path.is_file():
        return {
            "ok": False,
            "error": f".sby file not found: {sby_path}",
            "project_root": str(PROJECT_ROOT),
        }

    if cwd is None:
        cwd = str(sby_path.parent)

    yosys_v = _yosys_version_line()
    if _yosys_too_old_for_sby(yosys_v):
        return {
            "ok": False,
            "error": (
                "Yosys is too old for SymbiYosys 0.6x (needs YosysHQ Yosys with "
                "`hierarchy -smtcheck`). Ubuntu apt `yosys` 0.9 will not work. "
                "See docs/SETUP.md section 'Upgrade Yosys for SymbiYosys'."
            ),
            "yosys_version": yosys_v,
            "sby_file": str(sby_path),
            "cwd": cwd,
        }

    args = ["sby"]
    if force:
        args.append("-f")
    args += list(extra_args or [])
    args.append(sby_path.name)

    result = _run(args, cwd=cwd, timeout_s=timeout_s)
    result["ok"] = result.get("returncode") == 0
    result["yosys_version"] = yosys_v
    result["sby_file"] = str(sby_path)
    return result


if __name__ == "__main__":
    try:
        mcp.run()
    except KeyboardInterrupt:
        # FastMCP/anyio may emit a verbose cancellation traceback on Ctrl+C.
        # Exiting quietly makes local dev less confusing.
        raise SystemExit(0)

