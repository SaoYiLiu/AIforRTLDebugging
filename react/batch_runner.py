from __future__ import annotations

import argparse
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from react.react_runner import run_react_loop  # noqa: E402


@dataclass
class ProblemSpec:
    prob_id: str
    base_name: str
    prompt_path: Path
    testbench_path: Path
    ref_path: Path


def _discover_problems(dataset_dir: Path) -> list[ProblemSpec]:
    problems_file = dataset_dir / "problems.txt"
    if problems_file.exists():
        base_names = [
            line.strip()
            for line in problems_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    else:
        base_names = sorted(
            p.name[: -len("_prompt.txt")]
            for p in dataset_dir.glob("*_prompt.txt")
        )

    specs: list[ProblemSpec] = []
    for base_name in base_names:
        m = re.match(r"^(Prob\d+)", base_name)
        if not m:
            raise ValueError(f"Could not extract prob_id from problem name: {base_name}")
        prob_id = m.group(1)

        prompt_path = dataset_dir / f"{base_name}_prompt.txt"
        testbench_path = dataset_dir / f"{base_name}_test.sv"
        ref_path = dataset_dir / f"{base_name}_ref.sv"

        missing = [p for p in (prompt_path, testbench_path, ref_path) if not p.exists()]
        if missing:
            raise FileNotFoundError(
                f"Missing files for {base_name}: {', '.join(str(p) for p in missing)}"
            )

        specs.append(
            ProblemSpec(
                prob_id=prob_id,
                base_name=base_name,
                prompt_path=prompt_path,
                testbench_path=testbench_path,
                ref_path=ref_path,
            )
        )
    return specs


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
    dataset_dir: str,
    output_root: str,
    use_cursor_sdk: bool = False,
    use_veridebug_hf: bool = False,
    veridebug_hf_model: str = "LLM-EDA/VeriDebug",
    cursor_model: str = "composer-2.5",
    top: str = "tb",
    max_iters: int = 3,
    build_connection_map: bool = True,
    connection_map_llm: bool = False,
    prob_ids: list[str] | None = None,
) -> dict:
    dataset_path = Path(dataset_dir).resolve()
    if not dataset_path.is_dir():
        raise NotADirectoryError(f"Dataset directory not found: {dataset_path}")

    specs = _discover_problems(dataset_path)
    if prob_ids:
        wanted = {p.strip() for p in prob_ids}
        specs = [s for s in specs if s.prob_id in wanted]
        if not specs:
            raise ValueError(f"No problems matched prob_ids={sorted(wanted)}")

    print(f"Dataset: {dataset_path}")
    print(f"Problems to run: {len(specs)}")
    print("-" * 72)

    results: list[dict] = []
    batch_start = time.perf_counter()

    for idx, spec in enumerate(specs, 1):
        print(f"\n[{idx}/{len(specs)}] {spec.base_name} ({spec.prob_id})")
        start = time.perf_counter()
        status = "ERROR"
        ok = False
        mismatches = None
        error = None
        output_dir = None

        try:
            res = run_react_loop(
                prob_id=spec.prob_id,
                prompt_path=str(spec.prompt_path),
                testbench_path=str(spec.testbench_path),
                ref_model_path=str(spec.ref_path),
                output_root=output_root,
                fixer=None,
                top=top,
                max_iters=max_iters,
                use_cursor_sdk=use_cursor_sdk,
                use_veridebug_hf=use_veridebug_hf,
                veridebug_hf_model=veridebug_hf_model,
                cursor_model=cursor_model,
                build_connection_map=build_connection_map,
                connection_map_llm=connection_map_llm,
            )
            ok = bool(res.get("ok"))
            mismatches = res.get("mismatches")
            output_dir = res.get("output_dir")
            status = "PASS" if ok else "FAIL"
        except Exception as exc:
            error = str(exc)
            status = "ERROR"

        elapsed = time.perf_counter() - start
        results.append(
            {
                "prob_id": spec.prob_id,
                "base_name": spec.base_name,
                "ok": ok,
                "status": status,
                "elapsed_seconds": elapsed,
                "mismatches": mismatches,
                "output_dir": output_dir,
                "error": error,
            }
        )

        detail = f"mismatches={mismatches}" if mismatches is not None else "mismatches=?"
        if error:
            detail = error
        print(
            f"  => {status} | {_format_duration(elapsed)} | {detail}",
            flush=True,
        )

    batch_elapsed = time.perf_counter() - batch_start
    passed = sum(1 for r in results if r["ok"])
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errored = sum(1 for r in results if r["status"] == "ERROR")
    total = len(results)
    success_rate = (passed / total * 100.0) if total else 0.0

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"{'Problem':<42} {'Status':<8} {'Time':>10} {'Mismatches':>12}")
    print("-" * 72)
    for r in results:
        mm = r["mismatches"]
        mm_str = str(mm) if mm is not None else ("ERR" if r["error"] else "?")
        print(
            f"{r['base_name']:<42} {r['status']:<8} "
            f"{_format_duration(r['elapsed_seconds']):>10} {mm_str:>12}"
        )
    print("-" * 72)
    print(f"Passed:       {passed}/{total}")
    print(f"Failed:       {failed}/{total}")
    print(f"Errors:       {errored}/{total}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Total time:   {_format_duration(batch_elapsed)}")
    print("=" * 72)

    return {
        "dataset_dir": str(dataset_path),
        "total": total,
        "passed": passed,
        "failed": failed,
        "errored": errored,
        "success_rate": success_rate,
        "elapsed_seconds": batch_elapsed,
        "results": results,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Run react_runner over all ChipBench problems in a dataset folder."
    )
    ap.add_argument(
        "--dataset-dir",
        required=True,
        help="Path to a ChipBench dataset folder (contains problems.txt or *_prompt.txt files).",
    )
    ap.add_argument("--output-root", default=str(REPO_ROOT / "outputs"))
    ap.add_argument("--max-iters", type=int, default=3)
    ap.add_argument("--use-cursor-sdk", action="store_true")
    ap.add_argument("--use-veridebug-hf", action="store_true")
    ap.add_argument("--veridebug-hf-model", default="LLM-EDA/VeriDebug")
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
        help="Skip connection map after first sim failure.",
    )
    ap.add_argument(
        "--connection-map-llm",
        action="store_true",
        help="Enrich error-focused connection map with Cursor (slow; default is static only).",
    )
    ap.add_argument("--top", default="tb")
    ap.add_argument(
        "--prob-ids",
        nargs="+",
        help="Optional subset of problem IDs to run (e.g. Prob001 Prob002).",
    )
    args = ap.parse_args()

    if args.cursor_transport:
        os.environ["CURSOR_TRANSPORT"] = args.cursor_transport

    run_batch(
        dataset_dir=args.dataset_dir,
        output_root=args.output_root,
        use_cursor_sdk=args.use_cursor_sdk,
        use_veridebug_hf=args.use_veridebug_hf,
        veridebug_hf_model=args.veridebug_hf_model,
        cursor_model=args.cursor_model,
        top=args.top,
        max_iters=args.max_iters,
        build_connection_map=not args.no_connection_map,
        connection_map_llm=args.connection_map_llm,
        prob_ids=args.prob_ids,
    )
