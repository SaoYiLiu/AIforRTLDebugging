from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).absolute().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from react_cvdp.cvdp_dataset import load_cvdp_problems
from react_cvdp.cvdp_react_runner import run_cvdp_react_loop


def _display_path(path: str | Path) -> str:
    """Return an absolute path without consulting process cwd."""
    p = Path(path)
    return str(p if p.is_absolute() else REPO_ROOT / p)


def _repo_relative_path(path: str | Path | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    return str(p if p.is_absolute() else REPO_ROOT / p)


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {secs:.1f}s"
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes)}m {secs:.1f}s"


def run_batch(
    *,
    jsonl_path: str,
    output_root: str = "outputs",
    categories: list[str] | None = None,
    formats: tuple[str, ...] = ("nonagentic",),
    problem_ids: list[str] | None = None,
    use_cursor_sdk: bool = False,
    cursor_model: str = "composer-2.5",
    max_iters: int = 5,
    harness_timeout_s: int = 600,
    cvdp_env_path: str | None = None,
    force_restage: bool = False,
    use_iverilog_precheck: bool = False,
    harness_every_n_iters: int = 1,
    reuse_cursor_session: bool = True,
    skip_first: int = 0,
    use_debug_tb: bool = True,
    debug_tb_min_iter: int = 3,
) -> dict:
    jsonl_path = _repo_relative_path(jsonl_path) or jsonl_path
    output_root = _repo_relative_path(output_root) or output_root
    cvdp_env_path = _repo_relative_path(cvdp_env_path)

    specs = load_cvdp_problems(
        jsonl_path,
        categories=categories,
        formats=formats,  # type: ignore[arg-type]
        problem_ids=problem_ids,
    )
    if not specs:
        raise ValueError("No CVDP problems matched filters.")
    if skip_first < 0:
        raise ValueError("--skip-first must be non-negative.")
    if skip_first:
        specs = specs[skip_first:]
        if not specs:
            raise ValueError("No CVDP problems remain after applying --skip-first.")

    print(f"JSONL: {_display_path(jsonl_path)}")
    if skip_first:
        print(f"Skipped first: {skip_first}")
    print(f"Problems to run: {len(specs)}")
    print("-" * 72)

    results: list[dict] = []
    batch_start = time.perf_counter()
    cursor_session = None

    try:
        for idx, spec in enumerate(specs, 1):
            print(f"\n[{idx}/{len(specs)}] {spec.problem_id} ({spec.category}/{spec.difficulty})")
            start = time.perf_counter()
            status = "ERROR"
            ok = False
            error = None
            output_dir = None

            try:
                if not spec.harness_files:
                    raise ValueError(
                        "No harness embedded in JSONL (common for agentic cid016 on public HF release)."
                    )
                res = run_cvdp_react_loop(
                    spec,
                    output_root=output_root,
                    max_iters=max_iters,
                    use_cursor_sdk=use_cursor_sdk,
                    cursor_model=cursor_model,
                    harness_timeout_s=harness_timeout_s,
                    cvdp_env_path=cvdp_env_path,
                    force_restage=force_restage,
                    use_iverilog_precheck=use_iverilog_precheck,
                    harness_every_n_iters=harness_every_n_iters,
                    cursor_session=cursor_session,
                    reuse_cursor_session=reuse_cursor_session,
                    use_debug_tb=use_debug_tb,
                    debug_tb_min_iter=debug_tb_min_iter,
                )
                ok = bool(res.get("ok"))
                output_dir = res.get("output_dir")
                status = "PASS" if ok else "FAIL"
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                tb = traceback.format_exc()
                if output_dir:
                    try:
                        Path(output_dir).joinpath("batch_error.txt").write_text(
                            error + "\n\n" + tb, encoding="utf-8"
                        )
                    except OSError:
                        pass
                elif spec.problem_id:
                    try:
                        err_dir = Path(output_root) / spec.problem_id
                        err_dir.mkdir(parents=True, exist_ok=True)
                        err_dir.joinpath("batch_error.txt").write_text(
                            error + "\n\n" + tb, encoding="utf-8"
                        )
                    except OSError:
                        pass
                status = "ERROR"

            elapsed = time.perf_counter() - start
            results.append(
                {
                    "problem_id": spec.problem_id,
                    "category": spec.category,
                    "format": spec.format,
                    "ok": ok,
                    "status": status,
                    "elapsed_seconds": elapsed,
                    "output_dir": output_dir,
                    "error": error,
                }
            )
            print(f"  => {status} | {_format_duration(elapsed)}")
            if error:
                print(f"     error: {error}")
    finally:
        if cursor_session is not None:
            cursor_session.close()

    total = time.perf_counter() - batch_start
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"{'Problem ID':<50} {'Status':<8} {'Time'}")
    print("-" * 72)
    for r in results:
        line = f"{r['problem_id'][:49]:<50} {r['status']:<8} {_format_duration(r['elapsed_seconds'])}"
        print(line)
        if r.get("error"):
            print(f"  {'':49}  {r['error'][:120]}")
    print("-" * 72)
    print(f"Passed:       {passed}/{len(results)}")
    print(f"Failed:       {failed}/{len(results)}")
    print(f"Errors:       {errors}/{len(results)}")
    if results:
        print(f"Success rate: {100.0 * passed / len(results):.1f}%")
    print(f"Total time:   {_format_duration(total)}")
    print("=" * 72)

    return {"results": results, "passed": passed, "failed": failed, "errors": errors}


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Run CVDP cid016 ReAct debugging loop (Docker harness + optional Cursor SDK)."
    )
    ap.add_argument(
        "--jsonl",
        required=True,
        help="Path to CVDP JSONL (e.g. cvdp_v1.1.0_nonagentic_code_generation_no_commercial.jsonl).",
    )
    ap.add_argument(
        "--categories",
        nargs="+",
        default=["cid016"],
        help="CVDP category IDs to include (default: cid016).",
    )
    ap.add_argument(
        "--format",
        dest="formats",
        choices=["nonagentic", "agentic", "both"],
        default="nonagentic",
        help="Dataset record format (default: nonagentic). Use agentic with the agentic JSONL file.",
    )
    ap.add_argument("--output-root", default="outputs")
    ap.add_argument("--max-iters", type=int, default=5)
    ap.add_argument("--use-cursor-sdk", action="store_true")
    ap.add_argument("--cursor-model", default="composer-2.5")
    ap.add_argument("--harness-timeout-s", type=int, default=600)
    ap.add_argument(
        "--cvdp-env",
        default=None,
        help="Path to cvdp_benchmark/.env (OSS_SIM_IMAGE).",
    )
    ap.add_argument("--force-restage", action="store_true")
    ap.add_argument(
        "--iverilog-precheck",
        action="store_true",
        help="Run optional iverilog when verif/ TB exists in context.",
    )
    ap.add_argument(
        "--harness-every-n-iters",
        type=int,
        default=1,
        help="Run Docker harness every N iterations (default: every iteration).",
    )
    ap.add_argument(
        "--problem-ids",
        nargs="+",
        help="Optional subset of CVDP problem IDs.",
    )
    ap.add_argument(
        "--skip-first",
        type=int,
        default=0,
        help="Skip the first N matched problems after applying filters.",
    )
    ap.add_argument(
        "--cursor-transport",
        default=None,
        help="Set CURSOR_TRANSPORT (auto|bridge|rest).",
    )
    ap.add_argument(
        "--no-reuse-cursor-session",
        action="store_true",
        help="Use one-shot Cursor SDK calls instead of a batch-scoped bridge session.",
    )
    ap.add_argument(
        "--no-debug-tb",
        action="store_true",
        help="Do not offer Cursor an optional iverilog debug-sim decision after harness failures.",
    )
    ap.add_argument(
        "--debug-tb-min-iter",
        type=int,
        default=3,
        help="First iteration after which a separate debug-TB Cursor call runs on harness FAIL (default: 3).",
    )
    args = ap.parse_args()

    if args.cursor_transport:
        os.environ["CURSOR_TRANSPORT"] = args.cursor_transport

    fmt: tuple[str, ...]
    if args.formats == "both":
        fmt = ("nonagentic", "agentic")
    else:
        fmt = (args.formats,)

    run_batch(
        jsonl_path=args.jsonl,
        output_root=args.output_root,
        categories=args.categories,
        formats=fmt,  # type: ignore[arg-type]
        problem_ids=args.problem_ids,
        use_cursor_sdk=args.use_cursor_sdk,
        cursor_model=args.cursor_model,
        max_iters=args.max_iters,
        harness_timeout_s=args.harness_timeout_s,
        cvdp_env_path=args.cvdp_env,
        force_restage=args.force_restage,
        use_iverilog_precheck=args.iverilog_precheck,
        harness_every_n_iters=args.harness_every_n_iters,
        reuse_cursor_session=not args.no_reuse_cursor_session,
        skip_first=args.skip_first,
        use_debug_tb=not args.no_debug_tb,
        debug_tb_min_iter=args.debug_tb_min_iter,
    )


if __name__ == "__main__":
    main()
