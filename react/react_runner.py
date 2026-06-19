from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

# Import the same functions the MCP server exposes.
# When this script is run as `python react/react_runner.py`, the repo root isn't
# automatically on sys.path, so add it.
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import mcp_server  # noqa: E402
from react.cursor_sdk_fixer import fix_with_cursor_sdk  # noqa: E402
from react.veridebug_hf_fixer import fix_with_veridebug_hf  # noqa: E402
from react.parsers import (  # noqa: E402
    detect_mismatches,
    format_structured_feedback,
    parse_iverilog_result,
)
from react.connection_map import (  # noqa: E402
    ensure_connection_map,
    format_connection_map_for_llm,
)
from react.vcd_trace import (  # noqa: E402
    build_vcd_debug_summary,
    format_causal_chain_for_llm,
)


@dataclass
class Step:
    thought: str
    action: str
    observation: str | None = None


def _extract_buggy_module(prompt_text: str) -> str:
    """
    ChipBench prompt format typically includes a fenced code block containing the buggy RTL.
    We'll grab the first ```...``` block that contains 'module TopModule'.
    """
    blocks = re.findall(r"```\s*(.*?)\s*```", prompt_text, flags=re.DOTALL)
    for b in blocks:
        if "module TopModule" in b:
            return b.strip() + "\n"
    raise ValueError("Could not find a TopModule code block in prompt.")

def _write_llm_fix_request(
    *,
    out_dir: Path,
    prob_id: str,
    prompt_text: str,
    buggy_sv: str,
    current_sv: str,
    sim_stdout: str,
    sim_stderr: str,
    vcd_summary: dict[str, Any] | None,
    structured_feedback_text: str | None = None,
    connection_map_text: str | None = None,
) -> Path:
    """
    Writes a compact “next ReAct iteration” brief that you can paste into Cursor chat.
    """
    p = out_dir / "llm_fix_request.md"
    with p.open("w", encoding="utf-8") as f:
        f.write(f"# LLM fix request: {prob_id}\n\n")
        f.write("## Goal\nFix `TopModule` so the DUT matches the reference model under the provided testbench.\n\n")

        if structured_feedback_text:
            f.write("## Structured feedback\n")
            f.write("```text\n")
            f.write(structured_feedback_text.strip() + "\n")
            f.write("```\n\n")

        if connection_map_text:
            f.write("## Connection map\n")
            f.write("```text\n")
            f.write(connection_map_text.strip() + "\n")
            f.write("```\n\n")

        f.write("## Testbench result (raw)\n")
        f.write("```text\n")
        f.write((sim_stdout or "").strip() + "\n")
        if sim_stderr:
            f.write("\n[stderr]\n")
            f.write(sim_stderr.strip() + "\n")
        f.write("```\n\n")

        if vcd_summary is not None:
            f.write("## Waveform summary (from VCD)\n")
            f.write("```text\n")
            # Keep it short; this is for the LLM.
            if "signals" in vcd_summary:
                f.write("signals (first chunk):\n")
                for s in vcd_summary.get("signals", [])[:80]:
                    f.write(f"- {s}\n")
            if vcd_summary.get("failure_time") is not None:
                f.write(f"\nfailure_time (ps): {vcd_summary['failure_time']}\n")
            if vcd_summary.get("causal_chain"):
                f.write("\ncausal trace:\n")
                f.write(format_causal_chain_for_llm(vcd_summary["causal_chain"]) + "\n")
            if "results" in vcd_summary:
                f.write("\nselected signals:\n")
                for sig, info in vcd_summary["results"].items():
                    f.write(f"\n[{sig}]\n")
                    for line in info.get("lines", [])[:200]:
                        f.write(line + "\n")
            f.write("```\n\n")

        f.write("## Buggy RTL extracted from prompt\n")
        f.write("```verilog\n")
        f.write(buggy_sv.strip() + "\n")
        f.write("```\n\n")

        f.write("## Current candidate RTL\n")
        f.write("```verilog\n")
        f.write(current_sv.strip() + "\n")
        f.write("```\n\n")

        f.write("## What to do\n")
        f.write("- Identify the logic bug relative to the spec.\n")
        f.write("- Output a corrected full `TopModule` implementation.\n")
    return p


def run_react_loop(
    *,
    prob_id: str,
    prompt_path: str,
    testbench_path: str,
    ref_model_path: str,
    output_root: str = "outputs",
    fixer: Callable[[str, dict[str, Any]], str] | None = None,
    use_cursor_sdk: bool = False,
    use_veridebug_hf: bool = False,
    veridebug_hf_model: str = "LLM-EDA/VeriDebug",
    cursor_model: str = "composer-2.5",
    top: str = "tb",
    max_iters: int = 3,
    build_connection_map: bool = True,
    connection_map_llm: bool = False,
) -> dict[str, Any]:
    """
    ReAct-style automation:
    - Read prompt (spec + buggy RTL)
    - Iteratively propose fixes (via provided fixer callback)
    - Run Icarus regression (testbench compares DUT vs ref)
    - If mismatches, summarize VCD and emit an “LLM fix request” artifact
    - Keep outputs in a per-problem output directory

    Fixers (iteration 2+): ``fixer`` callback, ``--use-veridebug-hf``, or ``--use-cursor-sdk``.
    """
    if use_cursor_sdk and use_veridebug_hf:
        raise ValueError("Use only one of use_cursor_sdk or use_veridebug_hf.")

    prompt_p = Path(prompt_path)
    tb_p = Path(testbench_path)
    ref_p = Path(ref_model_path)

    out_dir = Path(output_root) / f"{prob_id}_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    steps: list[Step] = []

    # Step 1: read prompt / extract buggy code
    prompt_text = prompt_p.read_text(encoding="utf-8", errors="ignore")
    buggy_sv = _extract_buggy_module(prompt_text)
    steps.append(
        Step(
            thought="I need the buggy RTL and spec first.",
            action=f"Read prompt file and extract TopModule.",
            observation=f"Extracted {len(buggy_sv.splitlines())} lines of TopModule RTL.",
        )
    )

    buggy_path = out_dir / f"{prob_id}_buggy.sv"
    buggy_path.write_text(buggy_sv, encoding="utf-8")

    current_sv = buggy_sv
    fixed_path = out_dir / f"{prob_id}_fixed.sv"
    last_result: dict[str, Any] | None = None
    last_feedback: Any = None
    last_vcd_summary: dict[str, Any] | None = None
    last_llm_request: Path | None = None
    prior_rationales: list[str] = []
    connection_map: dict[str, Any] | None = None
    connection_map_built = False

    cwd = str(tb_p.parent)
    tb_src = str(tb_p)
    ref_src = str(ref_p)

    for it in range(1, max_iters + 1):
        print(f"[{prob_id}] Iteration {it}/{max_iters} starting...", flush=True)
        # Step: propose a candidate
        if it == 1:
            steps.append(
                Step(
                    thought="Start from the buggy RTL extracted from the prompt.",
                    action="Use extracted TopModule as initial candidate.",
                    observation="Candidate = buggy RTL.",
                )
            )
        else:
            if fixer is None and not use_cursor_sdk and not use_veridebug_hf:
                break
            steps.append(
                Step(
                    thought="There are mismatches; use simulation evidence (and waveform summary) to propose a patch.",
                    action=f"Call fixer() for iteration {it}.",
                )
            )
            last_run = (last_result.get("run") or {}) if last_result else {}
            if use_veridebug_hf:
                print(f"[{prob_id}] Iteration {it}: VeriDebug HF (embed + guided fix)...", flush=True)
                fr = fix_with_veridebug_hf(
                    prob_id=prob_id,
                    spec_text=prompt_text,
                    current_sv=current_sv,
                    sim_stdout=last_run.get("stdout", ""),
                    sim_stderr=last_run.get("stderr", ""),
                    structured_feedback=last_feedback,
                    model_id=veridebug_hf_model,
                )
                (out_dir / f"veridebug_hf_iter_{it}.txt").write_text(
                    "## Rationale\n"
                    + fr.rationale.strip()
                    + "\n\n## Raw generation\n```\n"
                    + fr.raw_text.strip()
                    + "\n```\n\n## Patched TopModule\n```verilog\n"
                    + fr.fixed_sv.strip()
                    + "\n```\n",
                    encoding="utf-8",
                )
                prior_rationales.append(fr.rationale)
                current_sv = fr.fixed_sv
                steps[-1].observation = "VeriDebug HF applied guided line fix."
            elif use_cursor_sdk:
                print(f"[{prob_id}] Iteration {it}: requesting patch from Cursor...", flush=True)
                fr = fix_with_cursor_sdk(
                    prob_id=prob_id,
                    spec_text=prompt_text,
                    buggy_sv=buggy_sv,
                    current_sv=current_sv,
                    sim_stdout=last_run.get("stdout", ""),
                    sim_stderr=last_run.get("stderr", ""),
                    vcd_summary=last_vcd_summary,
                    connection_map=connection_map,
                    structured_feedback=last_feedback,
                    prior_rationales=prior_rationales,
                    model=cursor_model,
                )
                (out_dir / f"cursor_sdk_iter_{it}.txt").write_text(
                    f"## Transport\n{fr.transport}\n\n"
                    "## Rationale\n"
                    + (fr.rationale.strip() + "\n" if fr.rationale.strip() else "(empty)\n")
                    + "\n## FixedTopModule\n```verilog\n"
                    + fr.fixed_sv.strip()
                    + "\n```\n",
                    encoding="utf-8",
                )
                prior_rationales.append(fr.rationale)
                current_sv = fr.fixed_sv
                steps[-1].observation = (
                    f"Cursor ({fr.transport}) produced candidate (len={len(current_sv)} chars)."
                )
            else:
                current_sv = fixer(current_sv, {"iteration": it, "vcd_summary": last_vcd_summary})
                steps[-1].observation = f"Candidate updated (len={len(current_sv)} chars)."

        fixed_path.write_text(current_sv, encoding="utf-8")

        # Step: run sim
        sim_out = out_dir / f"{prob_id}.out"
        print(f"[{prob_id}] Iteration {it}: running simulation (iverilog/vvp)...", flush=True)
        steps.append(
            Step(
                thought="Run simulation to compare DUT vs reference.",
                action=f"run_iverilog(tb, ref, fixed) [iteration {it}]",
            )
        )

        # For sources in the ChipBench folder, pass basenames; for our candidate, pass absolute.
        result = mcp_server.run_iverilog(
            sources=[Path(tb_src).name, Path(ref_src).name, str(fixed_path)],
            top=top,
            output=str(sim_out),
            run=True,
            cwd=cwd,
        )
        last_result = result
        steps[-1].observation = (
            f"compile.rc={result['compile']['returncode']}, "
            f"run.rc={(result['run'] or {}).get('returncode', None)}"
        )

        run_stdout = (result.get("run") or {}).get("stdout", "") or ""
        run_stderr = (result.get("run") or {}).get("stderr", "") or ""

        (out_dir / "sim_stdout.txt").write_text(run_stdout, encoding="utf-8")
        (out_dir / "sim_stderr.txt").write_text(run_stderr, encoding="utf-8")

        last_feedback = parse_iverilog_result(result)

        (out_dir / f"structured_feedback_iter_{it}.json").write_text(
            json.dumps(last_feedback.to_dict(), indent=2),
            encoding="utf-8",
        )

        # Collect wave if present
        wave_src = Path(cwd) / "wave.vcd"
        wave_dst = out_dir / "wave.vcd"
        if wave_src.exists():
            shutil.copy2(wave_src, wave_dst)

        mismatches = detect_mismatches(run_stdout)
        error_kind = last_feedback.error_kind
        if mismatches is not None:
            print(
                f"[{prob_id}] Iteration {it}: mismatches={mismatches} error_kind={error_kind}",
                flush=True,
            )
        else:
            rc = (result.get("run") or {}).get("returncode", None)
            print(
                f"[{prob_id}] Iteration {it}: no mismatch summary (run rc={rc}, error_kind={error_kind})",
                flush=True,
            )

        compile_ok = last_feedback.compile is None or last_feedback.compile.success
        ok = compile_ok and (result.get("run") or {}).get("returncode", 1) == 0 and (
            mismatches in (None, 0)
        )
        if ok:
            print(f"[{prob_id}] Iteration {it}: PASS (0 mismatches).", flush=True)
            break

        # After first failing sim: build connection map (LLM reads TB + ref + spec).
        want_map = build_connection_map and (not connection_map_built)
        if want_map and (mismatches is None or mismatches > 0):
            try:
                connection_map = ensure_connection_map(
                    prob_id=prob_id,
                    prompt_path=prompt_p,
                    tb_path=tb_p,
                    ref_path=ref_p,
                    out_dir=out_dir,
                    sim_stdout=run_stdout,
                    use_llm=connection_map_llm,
                    cursor_model=cursor_model,
                )
                connection_map_built = True
                n_focus = len(connection_map.get("vcd_trace_signals", []))
                print(
                    f"[{prob_id}] Connection map ready (source={connection_map.get('source')}, "
                    f"vcd_focus={n_focus} signals)",
                    flush=True,
                )
            except Exception as exc:
                print(f"[{prob_id}] Connection map failed: {exc}", flush=True)
                connection_map_built = True

        # Summarize wave + causal trace for next fix iteration.
        if wave_dst.exists():
            print(f"[{prob_id}] Iteration {it}: tracing wave.vcd for causal evidence...", flush=True)
            vcd_debug = build_vcd_debug_summary(
                wave_dst, run_stdout, connection_map=connection_map
            )
            last_vcd_summary = vcd_debug if vcd_debug.get("ok") else None

            if last_vcd_summary and last_vcd_summary.get("priority_signals"):
                failure_t = last_vcd_summary.get("failure_time")
                end_t = (failure_t + 5000) if failure_t is not None else 5000
                start_t = max(0, (failure_t - 200) if failure_t is not None else 0)
                waves = mcp_server.vcd_to_text(
                    str(wave_dst),
                    signals=last_vcd_summary["priority_signals"][:8],
                    start_time=start_t,
                    end_time=end_t,
                )
                if waves.get("ok"):
                    last_vcd_summary["results"] = waves.get("results", {})
        else:
            last_vcd_summary = None

        feedback_text = format_structured_feedback(last_feedback)
        map_text = format_connection_map_for_llm(connection_map)
        last_llm_request = _write_llm_fix_request(
            out_dir=out_dir,
            prob_id=prob_id,
            prompt_text=prompt_text,
            buggy_sv=buggy_sv,
            current_sv=current_sv,
            sim_stdout=run_stdout,
            sim_stderr=run_stderr,
            vcd_summary=last_vcd_summary,
            structured_feedback_text=feedback_text,
            connection_map_text=map_text,
        )
        print(f"[{prob_id}] Iteration {it}: wrote llm_fix_request.md", flush=True)

    # Write a human-readable ReAct trace
    trace_md = out_dir / "react_trace.md"
    with trace_md.open("w", encoding="utf-8") as f:
        f.write(f"# ReAct trace: {prob_id}\n\n")
        for i, s in enumerate(steps, 1):
            f.write(f"## Step {i}\n")
            f.write(f"**Thought**: {s.thought}\n\n")
            f.write(f"**Action**: {s.action}\n\n")
            if s.observation is not None:
                f.write(f"**Observation**: {s.observation}\n\n")

    run_stdout = (result.get("run") or {}).get("stdout", "") or ""
    mismatches = detect_mismatches(run_stdout)
    final_feedback = parse_iverilog_result(result)
    compile_ok = final_feedback.compile is None or final_feedback.compile.success
    ok = compile_ok and (result.get("run") or {}).get("returncode", 1) == 0 and (
        mismatches in (None, 0)
    )

    return {
        "ok": ok,
        "mismatches": mismatches,
        "error_kind": final_feedback.error_kind,
        "output_dir": str(out_dir),
        "iverilog": result,
        "react_trace": str(trace_md),
        "llm_fix_request": str(last_llm_request) if last_llm_request else None,
    }


def _demo_prob001_fixer(current_sv: str, _ctx: dict[str, Any]) -> str:
    # Demo-only deterministic fix for Prob001: swap shift direction.
    return current_sv.replace("{a, a_tem[6:0]}", "{a_tem[6:0], a}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prob-id", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--testbench", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--top", default="tb")
    ap.add_argument("--output-root", default=str(REPO_ROOT / "outputs"))
    ap.add_argument("--max-iters", type=int, default=3)
    ap.add_argument("--use-cursor-sdk", action="store_true")
    ap.add_argument(
        "--use-veridebug-hf",
        action="store_true",
        help="Use Hugging Face LLM-EDA/VeriDebug (contrastive embedding + guided line fix).",
    )
    ap.add_argument(
        "--veridebug-hf-model",
        default="LLM-EDA/VeriDebug",
        help="Hugging Face model id or local path (env: VERIDEBUG_HF_MODEL).",
    )
    ap.add_argument("--cursor-model", default="composer-2.5")
    ap.add_argument(
        "--cursor-transport",
        choices=["auto", "bridge", "rest"],
        default=None,
        help="Cursor LLM transport: auto (bridge if available, else REST), bridge, or rest.",
    )
    ap.add_argument(
        "--no-connection-map",
        action="store_true",
        help="Skip connection map after first sim failure (use name heuristics only).",
    )
    ap.add_argument(
        "--connection-map-llm",
        action="store_true",
        help="Enrich error-focused connection map with a small Cursor call (slow; default is static only).",
    )
    ap.add_argument(
        "--demo-prob001-fixer",
        action="store_true",
        help="Use a deterministic fixer for Prob001 (for demo only).",
    )
    args = ap.parse_args()

    if args.cursor_transport:
        os.environ["CURSOR_TRANSPORT"] = args.cursor_transport

    res = run_react_loop(
        prob_id=args.prob_id,
        prompt_path=args.prompt,
        testbench_path=args.testbench,
        ref_model_path=args.ref,
        output_root=args.output_root,
        fixer=_demo_prob001_fixer if args.demo_prob001_fixer else None,
        top=args.top,
        max_iters=args.max_iters,
        use_cursor_sdk=args.use_cursor_sdk,
        use_veridebug_hf=args.use_veridebug_hf,
        veridebug_hf_model=args.veridebug_hf_model,
        cursor_model=args.cursor_model,
        build_connection_map=not args.no_connection_map,
        connection_map_llm=args.connection_map_llm,
    )
    print(res)

