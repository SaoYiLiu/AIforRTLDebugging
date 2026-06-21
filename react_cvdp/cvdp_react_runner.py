from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import sys

REPO_ROOT = Path(__file__).absolute().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from react.parsers import StructuredFeedback
from react.cursor_transport import CursorPromptSession
from react.vcd_trace import build_vcd_debug_summary

from react_cvdp.cvdp_cursor_fixer import fix_with_cursor_sdk_cvdp
from react_cvdp.cvdp_dataset import CvdpProblemSpec
from react_cvdp.cvdp_debug_tb import (
    format_debug_sim_for_llm,
    format_debug_sim_skipped_for_llm,
    request_debug_testbench_cvdp,
)
from react_cvdp.cvdp_harness_runner import (
    HarnessRunResult,
    cleanup_harness_project,
    run_cvdp_harness,
)
from react_cvdp.cvdp_iverilog_adapter import run_iverilog_adapter
from react_cvdp.cvdp_iverilog_runner import CvdpIverilogResult, run_cvdp_debug_sim
from react_cvdp.cvdp_parsers import (
    parse_cvdp_harness_output,
    to_structured_feedback,
)
from react_cvdp.cvdp_staging import (
    read_current_rtl,
    resolve_docker_image,
    stage_problem,
    write_patched_rtl,
)


@dataclass
class Step:
    thought: str
    action: str
    observation: str | None = None


def run_cvdp_react_loop(
    spec: CvdpProblemSpec,
    *,
    output_root: str = "outputs",
    max_iters: int = 5,
    use_cursor_sdk: bool = False,
    cursor_model: str = "composer-2.5",
    harness_timeout_s: int = 600,
    cvdp_env_path: str | None = None,
    force_restage: bool = False,
    use_iverilog_precheck: bool = False,
    harness_every_n_iters: int = 1,
    cursor_session: CursorPromptSession | None = None,
    reuse_cursor_session: bool = True,
    use_debug_tb: bool = True,
    debug_tb_min_iter: int = 3,
) -> dict[str, Any]:
    """
    ReAct loop for CVDP cid016: harness grade → parse → Cursor patch → repeat.

    Pass = CVDP Docker harness exit 0 with cocotb PASS.
    """
    docker_image = resolve_docker_image(
        Path(cvdp_env_path) if cvdp_env_path else None
    )
    workspace = stage_problem(
        spec,
        output_root=output_root,
        docker_image=docker_image,
        force=force_restage,
    )
    out_dir = workspace.out_dir
    steps: list[Step] = []
    prior_rationales: list[str] = []
    last_feedback: StructuredFeedback | None = None
    last_harness: HarnessRunResult | None = None
    last_parsed = None
    debug_sim_section = ""
    last_iv_result: CvdpIverilogResult | None = None

    buggy_files = dict(spec.context_files)
    owned_cursor_session: CursorPromptSession | None = None
    if use_cursor_sdk and reuse_cursor_session and cursor_session is None:
        owned_cursor_session = CursorPromptSession(workspace=str(REPO_ROOT))
        cursor_session = owned_cursor_session

    steps.append(
        Step(
            thought="Load CVDP problem and stage harness workspace.",
            action=f"stage_problem({spec.problem_id})",
            observation=f"Workspace at {out_dir}",
        )
    )

    ok = False
    iterations_run = 0
    try:
        for it in range(1, max_iters + 1):
            iterations_run = it
            print(f"[{spec.problem_id}] Iteration {it}/{max_iters} starting...", flush=True)

            if it > 1:
                if not use_cursor_sdk:
                    print(f"[{spec.problem_id}] No fixer configured; stopping.", flush=True)
                    break
                print(f"[{spec.problem_id}] Iteration {it}: requesting patch from Cursor...", flush=True)
                current_files = read_current_rtl(workspace)
                try:
                    fr = fix_with_cursor_sdk_cvdp(
                        problem_id=spec.problem_id,
                        spec_text=spec.prompt,
                        buggy_files=buggy_files,
                        current_files=current_files,
                        patch_targets=workspace.patch_targets,
                        harness_stdout=last_harness.stdout if last_harness else "",
                        harness_stderr=last_harness.stderr if last_harness else "",
                        structured_feedback=last_feedback,
                        prior_rationales=prior_rationales,
                        harness_dir=workspace.harness_dir,
                        primary_module=spec.primary_module,
                        model=cursor_model,
                        cursor_session=cursor_session,
                        prompt_artifact_path=out_dir / f"llm_fix_request_iter_{it}.md",
                        include_test_excerpt=(it == 2),
                        debug_sim_section=debug_sim_section,
                    )
                except Exception as exc:
                    err_path = out_dir / f"cursor_sdk_error_iter_{it}.txt"
                    err_path.write_text(
                        f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}",
                        encoding="utf-8",
                    )
                    hint = (
                        "Cursor SDK bridge could not start (common on WSL if `cursor` CLI is missing). "
                        "Try: export CURSOR_TRANSPORT=rest and set CURSOR_CLOUD_REPO_URL, "
                        "or run from a shell where ChipBench Cursor fixes work."
                    )
                    if isinstance(exc, FileNotFoundError) or "No such file or directory" in str(exc):
                        raise RuntimeError(f"{exc}\n{hint}") from exc
                    raise
                write_patched_rtl(workspace, fr.patched_files)
                (out_dir / f"cursor_sdk_iter_{it}.txt").write_text(
                    f"## Transport\n{fr.transport}\n\n## Rationale\n{fr.rationale}\n\n"
                    + "## PatchedFiles\n"
                    + "\n".join(
                        f"### {p}\n```verilog\n{c.strip()}\n```"
                        for p, c in fr.patched_files.items()
                    ),
                    encoding="utf-8",
                )
                prompt_path = out_dir / f"llm_fix_request_iter_{it}.md"
                if prompt_path.is_file():
                    (out_dir / "llm_fix_request.md").write_text(
                        prompt_path.read_text(encoding="utf-8"),
                        encoding="utf-8",
                    )
                prior_rationales.append(fr.rationale)
                steps.append(
                    Step(
                        thought="Apply Cursor patch to harness/rtl.",
                        action=f"fix_with_cursor_sdk_cvdp(iter={it})",
                        observation=f"Patched {list(fr.patched_files.keys())}",
                    )
                )

            iverilog_note = None
            if use_iverilog_precheck:
                iv = run_iverilog_adapter(workspace.harness_dir, spec.context_files)
                if iv.ran:
                    iverilog_note = (
                        f"iverilog pre-check passed={iv.passed}\n{iv.stdout[:2000]}"
                    )
                    (out_dir / f"iverilog_precheck_iter_{it}.txt").write_text(
                        iv.stdout + "\n" + iv.stderr,
                        encoding="utf-8",
                    )

            run_harness_now = (it == 1) or (it % harness_every_n_iters == 0) or (it == max_iters)
            if not run_harness_now:
                print(f"[{spec.problem_id}] Iteration {it}: skipping harness (every {harness_every_n_iters} iters)", flush=True)
                continue

            print(f"[{spec.problem_id}] Iteration {it}: running CVDP harness (Docker)...", flush=True)
            harness_result = run_cvdp_harness(
                workspace.harness_dir,
                problem_id=spec.problem_id,
                docker_image=workspace.docker_image,
                iteration=it,
                timeout_s=harness_timeout_s,
            )
            cleanup_harness_project(workspace.harness_dir, spec.problem_id, it)
            last_harness = harness_result
            (out_dir / f"harness_stdout_iter_{it}.txt").write_text(
                harness_result.stdout, encoding="utf-8"
            )
            (out_dir / f"harness_stderr_iter_{it}.txt").write_text(
                harness_result.stderr, encoding="utf-8"
            )

            parsed = parse_cvdp_harness_output(
                harness_result.stdout,
                harness_result.stderr,
                harness_result.returncode,
            )
            last_parsed = parsed
            last_feedback = to_structured_feedback(parsed)

            steps.append(
                Step(
                    thought="Grade candidate RTL with CVDP harness.",
                    action=f"run_cvdp_harness(iter={it})",
                    observation=(
                        f"passed={parsed.passed} rc={harness_result.returncode} "
                        f"failures={len(parsed.failures)}"
                    ),
                )
            )

            if parsed.passed:
                print(f"[{spec.problem_id}] Iteration {it}: PASS (CVDP harness).", flush=True)
                ok = True
                break

            if parsed.failures:
                f0 = parsed.failures[0]
                detail = f0.message or f"{f0.signal} expected={f0.expected} actual={f0.actual}"
                print(
                    f"[{spec.problem_id}] Iteration {it}: harness FAIL — {detail[:120]}",
                    flush=True,
                )
            else:
                print(
                    f"[{spec.problem_id}] Iteration {it}: harness FAIL (rc={harness_result.returncode})",
                    flush=True,
                )

            if (
                use_cursor_sdk
                and use_debug_tb
                and not parsed.passed
                and it >= debug_tb_min_iter
            ):
                print(
                    f"[{spec.problem_id}] Iteration {it}: asking Cursor if debug sim is useful...",
                    flush=True,
                )
                current_files = read_current_rtl(workspace)
                try:
                    tb_result = request_debug_testbench_cvdp(
                        problem_id=spec.problem_id,
                        spec_text=spec.prompt,
                        current_files=current_files,
                        harness_stdout=harness_result.stdout,
                        harness_stderr=harness_result.stderr,
                        structured_feedback=last_feedback,
                        harness_dir=workspace.harness_dir,
                        primary_module=spec.primary_module,
                        model=cursor_model,
                        cursor_session=cursor_session,
                        prompt_artifact_path=out_dir / f"debug_tb_request_iter_{it}.md",
                    )
                    (out_dir / f"debug_tb_cursor_iter_{it}.txt").write_text(
                        f"## Transport\n{tb_result.transport}\n\n"
                        f"## Requested\n{tb_result.requested}\n\n"
                        f"## Rationale\n{tb_result.rationale}\n\n"
                        f"## Raw\n{tb_result.raw_text}",
                        encoding="utf-8",
                    )

                    if not tb_result.requested:
                        (out_dir / f"debug_tb_skipped_iter_{it}.txt").write_text(
                            tb_result.decision_rationale or tb_result.rationale or "(no reason)",
                            encoding="utf-8",
                        )
                        debug_sim_section = format_debug_sim_skipped_for_llm(tb_result=tb_result)
                        steps.append(
                            Step(
                                thought="Cursor declined optional iverilog debug sim.",
                                action=f"request_debug_testbench_cvdp(iter={it})",
                                observation="debug sim skipped (Cursor use: no)",
                            )
                        )
                        continue

                    (out_dir / f"debug_tb_iter_{it}.sv").write_text(
                        tb_result.tb_sv, encoding="utf-8"
                    )

                    iv = run_cvdp_debug_sim(
                        harness_dir=workspace.harness_dir,
                        out_dir=out_dir,
                        patch_targets=workspace.patch_targets,
                        tb_sv=tb_result.tb_sv,
                        iteration=it,
                    )
                    last_iv_result = iv
                    sim_log = (iv.stdout + "\n" + iv.stderr).strip()
                    (out_dir / f"iverilog_debug_iter_{it}.txt").write_text(
                        sim_log or "(empty)", encoding="utf-8"
                    )

                    vcd_summary = None
                    if iv.vcd_path and iv.vcd_path.is_file():
                        vcd_summary = build_vcd_debug_summary(
                            iv.vcd_path,
                            iv.stdout,
                            connection_map=None,
                        )
                        (out_dir / f"vcd_summary_iter_{it}.json").write_text(
                            json.dumps(vcd_summary, indent=2),
                            encoding="utf-8",
                        )

                    debug_sim_section = format_debug_sim_for_llm(
                        iv_result=iv,
                        vcd_summary=vcd_summary,
                    )
                    steps.append(
                        Step(
                            thought="Generate focused iverilog TB and trace VCD after iter 3+ harness fail.",
                            action=f"request_debug_testbench_cvdp(iter={it})",
                            observation=(
                                f"iverilog compile_rc={iv.compile_rc} run_rc={iv.run_rc} "
                                f"vcd={'yes' if iv.vcd_path else 'no'}"
                            ),
                        )
                    )
                    print(
                        f"[{spec.problem_id}] Iteration {it}: iverilog debug "
                        f"compile_rc={iv.compile_rc} run_rc={iv.run_rc}",
                        flush=True,
                    )
                except Exception as exc:
                    warn = f"{type(exc).__name__}: {exc}"
                    (out_dir / f"debug_tb_error_iter_{it}.txt").write_text(
                        warn + "\n\n" + traceback.format_exc(),
                        encoding="utf-8",
                    )
                    print(
                        f"[{spec.problem_id}] Iteration {it}: debug TB/iverilog skipped — {warn}",
                        flush=True,
                    )
                    debug_sim_section = ""
    finally:
        if owned_cursor_session is not None:
            owned_cursor_session.close()
    trace_md = out_dir / "react_trace.md"
    with trace_md.open("w", encoding="utf-8") as f:
        f.write(f"# CVDP ReAct trace: {spec.problem_id}\n\n")
        f.write(f"- category: {spec.category}\n")
        f.write(f"- format: {spec.format}\n")
        f.write(f"- patch_targets: {workspace.patch_targets}\n\n")
        for i, s in enumerate(steps, 1):
            f.write(f"## Step {i}\n")
            f.write(f"**Thought**: {s.thought}\n\n")
            f.write(f"**Action**: {s.action}\n\n")
            if s.observation:
                f.write(f"**Observation**: {s.observation}\n\n")

    summary = {
        "ok": ok,
        "problem_id": spec.problem_id,
        "category": spec.category,
        "format": spec.format,
        "output_dir": str(out_dir),
        "harness_passed": ok,
        "iterations": iterations_run,
        "patch_targets": workspace.patch_targets,
        "debug_iverilog_ran": last_iv_result.ran if last_iv_result else False,
    }
    (out_dir / "result.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
