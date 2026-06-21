from __future__ import annotations

import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


def _absolute_path(path: Path) -> str:
    """Use absolute paths without resolving symlinks on WSL-mounted drives."""
    if not path.is_absolute():
        raise ValueError(f"Expected absolute harness path, got: {path}")
    return str(path)


@dataclass(frozen=True)
class HarnessRunResult:
    passed: bool
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    command: str


def _project_name(problem_id: str, iteration: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", problem_id.lower()).strip("_")
    return f"cvdp_react_{slug[:40]}_{iteration}"


def detect_compose_service(compose_file: Path) -> str:
    """
    Return the Docker Compose service to run for a CVDP harness.

    CVDP embeds different service names (`direct`, `01-new-tb`, etc.). Prefer
    ``direct`` when present; otherwise use the first service under ``services:``.
    """
    text = compose_file.read_text(encoding="utf-8")
    in_services = False
    names: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if re.match(r"^services:\s*$", line):
            in_services = True
            continue
        if not in_services:
            continue
        if not line.startswith(" "):
            break
        m = re.match(r"^  ([A-Za-z0-9_.-]+):\s*(?:#.*)?$", line)
        if m:
            names.append(m.group(1))
    if "direct" in names:
        return "direct"
    if names:
        return names[0]
    raise RuntimeError(
        f"No Docker Compose services found in {compose_file}. "
        "Expected a top-level `services:` block with at least one service."
    )


def run_cvdp_harness(
    harness_dir: Path,
    *,
    problem_id: str,
    docker_image: str,
    iteration: int = 1,
    timeout_s: int = 600,
) -> HarnessRunResult:
    """
    Run the CVDP cocotb/pytest harness via Docker Compose.

    Expects ``harness_dir/docker-compose.yml`` produced by ``cvdp_staging.stage_problem``.
    """
    compose_file = harness_dir / "docker-compose.yml"
    if not compose_file.is_file():
        raise FileNotFoundError(f"Missing docker-compose.yml in {harness_dir}")

    service = detect_compose_service(compose_file)
    uid = os.getuid() if hasattr(os, "getuid") else 1000
    gid = os.getgid() if hasattr(os, "getgid") else 1000
    project = _project_name(problem_id, iteration)

    cmd = [
        "docker",
        "compose",
        "-f",
        _absolute_path(compose_file),
        "-p",
        project,
        "run",
        "--rm",
        "--user",
        f"{uid}:{gid}",
        "-e",
        "HOME=/code/rundir",
        "-e",
        "XDG_CACHE_HOME=/code/rundir/.cache",
        service,
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=_absolute_path(harness_dir),
            text=True,
            capture_output=True,
            timeout=timeout_s,
            env={**os.environ, "OSS_SIM_IMAGE": docker_image},
        )
        return HarnessRunResult(
            passed=proc.returncode == 0,
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            timed_out=False,
            command=" ".join(shlex.quote(c) for c in cmd),
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")
        return HarnessRunResult(
            passed=False,
            returncode=-1,
            stdout=stdout,
            stderr=stderr + f"\n[harness timed out after {timeout_s}s]",
            timed_out=True,
            command=" ".join(shlex.quote(c) for c in cmd),
        )


def cleanup_harness_project(harness_dir: Path, problem_id: str, iteration: int) -> None:
    """Best-effort remove compose project containers/images."""
    compose_file = harness_dir / "docker-compose.yml"
    if not compose_file.is_file():
        return
    project = _project_name(problem_id, iteration)
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            _absolute_path(compose_file),
            "-p",
            project,
            "down",
            "--remove-orphans",
        ],
        cwd=_absolute_path(harness_dir),
        capture_output=True,
        text=True,
    )
