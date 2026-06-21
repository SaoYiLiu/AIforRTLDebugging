from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from react_cvdp.cvdp_dataset import CvdpProblemSpec

REPO_ROOT = Path(__file__).absolute().parents[1]


@dataclass(frozen=True)
class CvdpWorkspace:
    problem_id: str
    out_dir: Path
    harness_dir: Path
    rtl_dir: Path
    rundir: Path
    prompt_path: Path
    context_dir: Path
    patch_targets: list[str]
    docker_image: str


def _load_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.is_file():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        values[key.strip()] = val.strip()
    return values


def resolve_docker_image(cvdp_env_path: Path | None = None) -> str:
    if cvdp_env_path is None:
        cvdp_env_path = REPO_ROOT / "third_party" / "cvdp" / "cvdp_benchmark" / ".env"
    env = _load_env_file(cvdp_env_path)
    return env.get("OSS_SIM_IMAGE", "nvidia/cvdp-sim:v1.0.0")


def _sanitize_compose(content: str, docker_image: str) -> str:
    text = content.replace("__OSS_SIM_IMAGE__", docker_image)
    # Drop external network requirements — react_cvdp uses the default bridge.
    text = re.sub(
        r"networks:\s*\n(?:  .*\n)*",
        "",
        text,
        flags=re.MULTILINE,
    )
    return text


def _sanitize_harness_files(files: dict[str, str], docker_image: str) -> dict[str, str]:
    """Replace CVDP image placeholders wherever the embedded harness uses them."""
    return {
        path: content.replace("__OSS_SIM_IMAGE__", docker_image)
        for path, content in files.items()
    }


def _volume_host_path(line: str) -> str | None:
    """Extract host path from a compose volume list item, e.g. ``./rtl:/code/rtl``."""
    m = re.match(r"^\s*-\s+(\./[^\s:]+)", line.strip())
    return m.group(1) if m else None


def _ensure_compose_volumes(compose_text: str) -> str:
    """Ensure rtl/rundir/docs/verif mounts exist under a single ``volumes:`` block."""
    required = {
        "./src": "./src/:/src/:ro",
        "./rtl": "./rtl:/code/rtl",
        "./rundir": "./rundir:/code/rundir",
        "./docs": "./docs:/code/docs:ro",
        "./verif": "./verif:/code/verif:ro",
    }

    present: set[str] = set()
    for line in compose_text.splitlines():
        host = _volume_host_path(line)
        if host:
            present.add(host.rstrip("/"))
            if host.endswith("/"):
                present.add(host)

    missing = [f"- {spec}" for key, spec in required.items() if key not in present and f"{key}/" not in present]
    if not missing and "working_dir" in compose_text:
        return compose_text

    lines = compose_text.splitlines()
    out: list[str] = []
    in_volumes = False
    volumes_indent = ""
    merged = False

    for line in lines:
        stripped = line.strip()
        if re.match(r"^volumes:\s*(?:#.*)?$", stripped):
            in_volumes = True
            volumes_indent = re.match(r"^(\s*)", line).group(1)
            out.append(line)
            continue

        if in_volumes:
            # Still inside volumes list (``- ./foo:...`` entries).
            if stripped.startswith("- "):
                out.append(line)
                continue
            # Next service key — inject missing mounts before leaving volumes.
            if not merged and missing:
                for vol in missing:
                    out.append(f"{volumes_indent}  {vol}")
                merged = True
            in_volumes = False

        out.append(line)

    if not merged and missing:
        # No volumes block found — append one under the first service.
        inserted_block = False
        final: list[str] = []
        for line in out:
            final.append(line)
            if not inserted_block and re.match(r"^  \w[\w.-]*:\s*$", line):
                final.append("    volumes:")
                for vol in missing:
                    final.append(f"      {vol}")
                if "working_dir" not in compose_text:
                    final.append("    working_dir: /code/rundir")
                inserted_block = True
        out = final

    if "working_dir" not in compose_text:
        out.append("    working_dir: /code/rundir")

    return "\n".join(out).rstrip() + "\n"


def _write_tree(base: Path, files: dict[str, str]) -> None:
    for rel_path, content in files.items():
        dest = base / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")


def stage_problem(
    spec: CvdpProblemSpec,
    *,
    output_root: str | Path = "outputs",
    docker_image: str | None = None,
    force: bool = False,
) -> CvdpWorkspace:
    """
    Materialize a CVDP workspace under ``outputs/cvdp_<problem_id>/``.

    Seeds ``harness/rtl/`` from ``input.context`` (buggy starter), never from golden output.
    """
    if not spec.harness_files:
        raise ValueError(
            f"{spec.problem_id}: no harness files in JSONL "
            f"(agentic cid016 on the public HF release often lacks embedded harnesses)."
        )

    image = docker_image or resolve_docker_image()
    output_root_path = Path(output_root)
    if not output_root_path.is_absolute():
        output_root_path = REPO_ROOT / output_root_path
    out_dir = output_root_path / spec.problem_id
    harness_dir = out_dir / "harness"
    context_dir = out_dir / "context"
    rtl_dir = harness_dir / "rtl"
    rundir = harness_dir / "rundir"
    prompt_path = out_dir / "prompt.md"

    if force and out_dir.exists():
        shutil.rmtree(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    context_dir.mkdir(parents=True, exist_ok=True)
    rtl_dir.mkdir(parents=True, exist_ok=True)
    rundir.mkdir(parents=True, exist_ok=True)
    (harness_dir / "docs").mkdir(parents=True, exist_ok=True)
    (harness_dir / "verif").mkdir(parents=True, exist_ok=True)

    prompt_path.write_text(spec.prompt.strip() + "\n", encoding="utf-8")

    # Frozen buggy snapshot for the fixer (reference).
    _write_tree(context_dir, spec.context_files)

    # Copy non-harness context into harness tree (docs/, verif/, extra rtl stubs).
    for rel_path, content in spec.context_files.items():
        if rel_path.startswith("rtl/"):
            continue
        dest = harness_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

    harness_only = dict(spec.harness_files)
    compose_raw = harness_only.pop("docker-compose.yml", "")
    compose_text = _sanitize_compose(compose_raw, image)
    compose_text = _ensure_compose_volumes(compose_text)
    harness_only = _sanitize_harness_files(harness_only, image)
    _write_tree(harness_dir, harness_only)
    (harness_dir / "docker-compose.yml").write_text(compose_text, encoding="utf-8")

    # Seed all RTL from context (agentic problems often have non-patch support files).
    # patch_targets lists files Cursor may edit; others stay fixed golden copies.
    all_rtl = sorted(p for p in spec.context_files if p.startswith("rtl/"))
    rtl_targets = [p for p in spec.patch_targets if p.startswith("rtl/")]
    if not rtl_targets:
        rtl_targets = all_rtl
    for rtl_path in all_rtl:
        content = spec.context_files.get(rtl_path, "")
        dest = harness_dir / rtl_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

    return CvdpWorkspace(
        problem_id=spec.problem_id,
        out_dir=out_dir,
        harness_dir=harness_dir,
        rtl_dir=rtl_dir,
        rundir=rundir,
        prompt_path=prompt_path,
        context_dir=context_dir,
        patch_targets=rtl_targets or sorted(spec.rtl_files.keys()),
        docker_image=image,
    )


def write_patched_rtl(workspace: CvdpWorkspace, patched_files: dict[str, str]) -> None:
    for rel_path, content in patched_files.items():
        if not rel_path.startswith("rtl/"):
            rel_path = f"rtl/{Path(rel_path).name}"
        dest = workspace.harness_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

        mirror = workspace.out_dir / "patched" / rel_path
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_text(content, encoding="utf-8")


def read_current_rtl(workspace: CvdpWorkspace) -> dict[str, str]:
    files: dict[str, str] = {}
    for rel_path in workspace.patch_targets:
        src = workspace.harness_dir / rel_path
        if src.is_file():
            files[rel_path] = src.read_text(encoding="utf-8")
    return files
