"""
Cursor LLM transport: SDK local bridge (WSL/desktop) or direct REST API (Linux servers).

On machines where ``cursor-sdk-bridge`` works, we use the SDK local runtime.
Elsewhere (e.g. headless Linux where curl to api.cursor.com works but the bridge
returns opaque 500s), we call the Cloud Agents REST API with a no-repo agent.

Set ``CURSOR_TRANSPORT`` to ``auto`` (default), ``bridge``, or ``rest``.
"""

from __future__ import annotations

import os
import json
import logging
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Literal

import httpx

TransportName = Literal["bridge", "rest"]
TransportMode = Literal["auto", "bridge", "rest"]

API_BASE = "https://api.cursor.com"
REPO_ROOT = Path(__file__).absolute().parents[1]
_TERMINAL_RUN_STATUSES = frozenset({"FINISHED", "ERROR", "CANCELLED", "EXPIRED"})

_bridge_probe_result: bool | None = None
_cloud_repo_cache: tuple[str, str] | None = None
_http_request_logging_enabled = False


def enable_http_request_logging() -> None:
    """Enable httpx request logs used by the Cursor SDK transport."""
    global _http_request_logging_enabled
    if _http_request_logging_enabled:
        return

    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.INFO)
    _http_request_logging_enabled = True


def _close_quietly(obj: object | None) -> None:
    if obj is None:
        return
    close = getattr(obj, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass
    process = getattr(obj, "process", None)
    terminate = getattr(process, "terminate", None)
    if callable(terminate):
        try:
            terminate()
        except Exception:
            pass


def _cloud_repo_ref() -> str:
    return os.environ.get("CURSOR_CLOUD_REPO_REF", "main").strip() or "main"


def _resolve_cloud_repo(client: httpx.Client, auth: tuple[str, str]) -> tuple[str, str]:
    """
    Cloud Agents on many accounts cannot use no-repo mode (environment_public_id error).
    Resolve a repo from CURSOR_CLOUD_REPO_URL or GET /v1/repositories (cached).
    """
    global _cloud_repo_cache

    explicit = os.environ.get("CURSOR_CLOUD_REPO_URL", "").strip()
    ref = _cloud_repo_ref()
    if explicit:
        return explicit, ref

    if _cloud_repo_cache is not None:
        return _cloud_repo_cache

    resp = client.get(f"{API_BASE}/v1/repositories", auth=auth, timeout=120)
    if resp.status_code >= 400:
        raise RuntimeError(
            f"Cursor REST list repositories failed: HTTP {resp.status_code}: "
            f"{resp.text[:800]}"
        )

    items = resp.json().get("items") or []
    if not items:
        raise RuntimeError(
            "Cursor REST needs a GitHub repository (no-repo cloud agents are unavailable "
            "on your account). Connect GitHub in the Cursor dashboard, or set:\n"
            "  export CURSOR_CLOUD_REPO_URL=https://github.com/YOU/AIfordebugging"
        )

    url = str(items[0].get("url", "")).strip()
    if not url:
        raise RuntimeError("Cursor REST: /v1/repositories returned no usable repo URL.")

    _cloud_repo_cache = (url, ref)
    return _cloud_repo_cache


def _write_prompt_artifact(path: Path | None, prompt: str) -> None:
    if path is not None:
        path.write_text(prompt, encoding="utf-8")


def _rest_prompt_text(prompt: str) -> str:
    return (
        "Reply in the agent message only. Do not create, edit, or commit "
        "repository files.\n\n"
        + prompt
    )


def _rest_create_payload(prompt: str, model: str, repo_url: str, starting_ref: str) -> dict:
    return {
        "prompt": {
            "text": _rest_prompt_text(prompt),
        },
        "model": {"id": model},
        "repos": [{"url": repo_url, "startingRef": starting_ref}],
        "autoCreatePR": False,
    }


def get_transport_mode() -> TransportMode:
    raw = os.environ.get("CURSOR_TRANSPORT", "auto").strip().lower()
    if raw in ("bridge", "sdk"):
        return "bridge"
    if raw == "rest":
        return "rest"
    return "auto"


def reset_bridge_probe() -> None:
    """Clear cached bridge probe (for tests)."""
    global _bridge_probe_result, _cloud_repo_cache
    _bridge_probe_result = None
    _cloud_repo_cache = None


def _probe_bridge(api_key: str, workspace: str, timeout_s: float = 30) -> bool:
    bridge = None
    client = None
    try:
        from cursor_sdk._bridge import Bridge  # type: ignore
        from cursor_sdk._client import Client  # type: ignore

        bridge = Bridge.launch(workspace=workspace, timeout=timeout_s)
        client = Client(bridge.endpoint, allow_api_key_env_fallback=True)
        client.list_models(api_key=api_key)
        return True
    except Exception:
        return False
    finally:
        _close_quietly(client)
        _close_quietly(bridge)


def bridge_available(*, api_key: str, workspace: str | None = None) -> bool:
    global _bridge_probe_result

    mode = get_transport_mode()
    if mode == "rest":
        return False

    if _bridge_probe_result is not None:
        return _bridge_probe_result

    ws = workspace or os.getcwd()
    _bridge_probe_result = _probe_bridge(api_key, ws)
    if not _bridge_probe_result:
        print(
            "[cursor] SDK bridge unavailable on this host; using REST API "
            "(https://api.cursor.com). Set CURSOR_TRANSPORT=bridge to require the bridge.",
            flush=True,
        )
    return _bridge_probe_result


class CursorPromptSession:
    """Reusable Cursor transport for batch jobs.

    REST mode keeps one cloud agent alive so follow-up prompts share the same
    conversation and workspace state. Bridge mode intentionally keeps the
    stable one-shot Agent.prompt path because explicit local Agent.create calls
    have produced opaque bridge 500s in WSL.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        workspace: str | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("CURSOR_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("CURSOR_API_KEY is not set in environment.")
        self.workspace = workspace or os.getcwd()
        self.mode = get_transport_mode()
        self._bridge: Any | None = None
        self._client: Any | None = None
        self._rest_client: httpx.Client | None = None
        self._rest_agent_id: str | None = None
        self._bridge_failed = False
        self._bridge_probed = False

    def __enter__(self) -> "CursorPromptSession":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def close(self) -> None:
        client = self._client
        bridge = self._bridge
        rest_client = self._rest_client
        rest_agent_id = self._rest_agent_id
        self._client = None
        self._bridge = None
        self._rest_client = None
        self._rest_agent_id = None

        _close_quietly(client)
        _close_quietly(bridge)
        if rest_client is not None:
            if rest_agent_id:
                _try_archive(rest_client, rest_agent_id, (self.api_key, ""))
            rest_client.close()

    def prompt(
        self,
        prompt: str,
        *,
        model: str = "composer-2.5",
        timeout_s: float = 600,
        prompt_artifact_path: Path | None = None,
    ) -> tuple[str, TransportName]:
        if self.mode == "auto":
            try:
                return self._prompt_rest_session(
                    prompt,
                    model=model,
                    timeout_s=timeout_s,
                    prompt_artifact_path=prompt_artifact_path,
                ), "rest"
            except Exception as rest_exc:
                print(
                    f"[cursor] REST session call failed ({type(rest_exc).__name__}); "
                    "trying SDK bridge.",
                    flush=True,
                )

        if self.mode == "rest":
            return self._prompt_rest_session(
                prompt,
                model=model,
                timeout_s=timeout_s,
                prompt_artifact_path=prompt_artifact_path,
            ), "rest"

        if self.mode == "bridge" or (
            self.mode == "auto" and not self._bridge_failed
        ):
            try:
                return _prompt_bridge(
                    prompt,
                    model=model,
                    api_key=self.api_key,
                    workspace=self.workspace,
                    timeout_s=timeout_s,
                    prompt_artifact_path=prompt_artifact_path,
                ), "bridge"
            except Exception as first_exc:
                # The local bridge is more reliable when each prompt gets a
                # fresh bridge process. Keep only the session-level fallback
                # state here; do not reuse a bridge/client across prompts.
                self.close()
                self._bridge_failed = True
                bridge_error_name = type(first_exc).__name__
                if self.mode == "bridge":
                    raise
                print(
                    f"[cursor] SDK bridge session failed ({bridge_error_name}); "
                    "falling back to REST API.",
                    flush=True,
                )

        return _prompt_rest(
            prompt,
            model=model,
            api_key=self.api_key,
            timeout_s=timeout_s,
            prompt_artifact_path=prompt_artifact_path,
        ), "rest"

    def _ensure_rest_client(self) -> httpx.Client:
        if self._rest_client is None:
            self._rest_client = httpx.Client(timeout=60)
        return self._rest_client

    def _prompt_rest_session(
        self,
        prompt: str,
        *,
        model: str,
        timeout_s: float,
        prompt_artifact_path: Path | None = None,
    ) -> str:
        auth = (self.api_key, "")
        headers = {"Content-Type": "application/json"}
        client = self._ensure_rest_client()
        submitted_prompt = _rest_prompt_text(prompt)
        _write_prompt_artifact(prompt_artifact_path, submitted_prompt)

        if self._rest_agent_id is None:
            repo_url, starting_ref = _resolve_cloud_repo(client, auth)
            payload = _rest_create_payload(prompt, model, repo_url, starting_ref)
            create = client.post(
                f"{API_BASE}/v1/agents",
                json=payload,
                auth=auth,
                headers=headers,
            )
            if create.status_code >= 400:
                raise RuntimeError(
                    f"Cursor REST create agent failed: HTTP {create.status_code}: "
                    f"{create.text[:800]}"
                )
            data = create.json()
            self._rest_agent_id = data["agent"]["id"]
            run_id = data["run"]["id"]
        else:
            create = client.post(
                f"{API_BASE}/v1/agents/{self._rest_agent_id}/runs",
                json={"prompt": {"text": submitted_prompt}},
                auth=auth,
                headers=headers,
            )
            if create.status_code >= 400:
                raise RuntimeError(
                    f"Cursor REST create run failed: HTTP {create.status_code}: "
                    f"{create.text[:800]}"
                )
            run_id = create.json()["run"]["id"]

        return _wait_rest_run(
            client,
            self._rest_agent_id,
            run_id,
            auth,
            timeout_s=timeout_s,
            archive_on_finish=False,
        )

    def _ensure_bridge(self, timeout_s: float) -> Any:
        if self._client is not None:
            return self._client

        from cursor_sdk._bridge import Bridge  # type: ignore
        from cursor_sdk._client import Client  # type: ignore

        if not self._bridge_probed:
            if not _probe_bridge(
                self.api_key,
                self.workspace,
                timeout_s=min(timeout_s, 30),
            ):
                raise RuntimeError("Cursor SDK bridge probe failed.")
            self._bridge_probed = True

        self._bridge = Bridge.launch(workspace=self.workspace, timeout=timeout_s)
        self._client = Client(self._bridge.endpoint, allow_api_key_env_fallback=True)
        return self._client

    def _prompt_bridge(
        self,
        prompt: str,
        *,
        model: str,
        timeout_s: float,
    ) -> str:
        from cursor_sdk import Agent, AgentOptions, LocalAgentOptions  # type: ignore

        options = AgentOptions(
            model=model,
            api_key=self.api_key,
            local=LocalAgentOptions(cwd=self.workspace),
        )
        client = self._ensure_bridge(min(timeout_s, 120))
        result = Agent.prompt(prompt, options, client=client)
        return (result.result or "") if hasattr(result, "result") else str(result)


def cursor_prompt(
    prompt: str,
    *,
    model: str = "composer-2.5",
    api_key: str | None = None,
    workspace: str | None = None,
    timeout_s: float = 600,
    prompt_artifact_path: Path | None = None,
) -> tuple[str, TransportName]:
    """
    Send a one-shot prompt to Cursor and return ``(assistant_text, transport)``.

    ``transport`` is ``"bridge"`` (local SDK) or ``"rest"`` (Cloud Agents API).
    """
    key = api_key or os.environ.get("CURSOR_API_KEY", "")
    if not key:
        raise RuntimeError("CURSOR_API_KEY is not set in environment.")

    ws = workspace or os.getcwd()
    mode = get_transport_mode()

    if mode == "auto":
        try:
            return _prompt_rest(
                prompt,
                model=model,
                api_key=key,
                timeout_s=timeout_s,
                prompt_artifact_path=prompt_artifact_path,
            ), "rest"
        except Exception as rest_exc:
            print(
                f"[cursor] REST call failed ({type(rest_exc).__name__}); "
                "trying SDK bridge.",
                flush=True,
            )
            if not bridge_available(api_key=key, workspace=ws):
                raise
            try:
                return _prompt_bridge(
                    prompt,
                    model=model,
                    api_key=key,
                    workspace=ws,
                    timeout_s=timeout_s,
                    prompt_artifact_path=prompt_artifact_path,
                ), "bridge"
            except Exception as bridge_exc:
                raise RuntimeError(
                    f"Cursor REST failed with {type(rest_exc).__name__}: {rest_exc}; "
                    f"bridge failed with {type(bridge_exc).__name__}: {bridge_exc}"
                ) from bridge_exc

    if mode == "bridge":
        if not bridge_available(api_key=key, workspace=ws):
            raise RuntimeError("Cursor SDK bridge probe failed.")
        try:
            return _prompt_bridge(
                prompt,
                model=model,
                api_key=key,
                workspace=ws,
                timeout_s=timeout_s,
                prompt_artifact_path=prompt_artifact_path,
            ), "bridge"
        except Exception:
            raise

    return _prompt_rest(
        prompt,
        model=model,
        api_key=key,
        timeout_s=timeout_s,
        prompt_artifact_path=prompt_artifact_path,
    ), "rest"


def cursor_prompt_isolated_bridge(
    prompt: str,
    *,
    model: str = "composer-2.5",
    api_key: str | None = None,
    workspace: str | None = None,
    timeout_s: float = 600,
) -> tuple[str, TransportName]:
    """Run the local bridge prompt in a fresh Python process."""
    key = api_key or os.environ.get("CURSOR_API_KEY", "")
    if not key:
        raise RuntimeError("CURSOR_API_KEY is not set in environment.")

    ws = workspace or os.getcwd()
    with tempfile.TemporaryDirectory(prefix="cursor-bridge-") as td:
        prompt_path = Path(td) / "prompt.txt"
        output_path = Path(td) / "result.json"
        prompt_path.write_text(prompt, encoding="utf-8")
        env = dict(os.environ)
        env["CURSOR_API_KEY"] = key
        env["PYTHONPATH"] = (
            str(REPO_ROOT)
            if not env.get("PYTHONPATH")
            else str(REPO_ROOT) + os.pathsep + env["PYTHONPATH"]
        )
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "react.cursor_bridge_helper",
                "--prompt-path",
                str(prompt_path),
                "--output-path",
                str(output_path),
                "--workspace",
                ws,
                "--model",
                model,
                "--timeout-s",
                str(timeout_s),
            ],
            text=True,
            capture_output=True,
            timeout=timeout_s + 30,
            env=env,
            cwd=str(REPO_ROOT),
        )
        if output_path.is_file():
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        else:
            payload = {
                "ok": False,
                "error": "isolated bridge helper did not write result",
                "traceback": "",
            }
        if proc.returncode != 0 or not payload.get("ok"):
            detail = payload.get("traceback") or payload.get("error") or proc.stderr
            raise RuntimeError(f"isolated Cursor bridge failed:\n{detail}")
        return str(payload.get("result") or ""), "bridge"


def _prompt_bridge(
    prompt: str,
    *,
    model: str,
    api_key: str,
    workspace: str,
    timeout_s: float,
    prompt_artifact_path: Path | None = None,
) -> str:
    from cursor_sdk import Agent, AgentOptions, LocalAgentOptions  # type: ignore
    from cursor_sdk._bridge import Bridge  # type: ignore
    from cursor_sdk._client import Client  # type: ignore

    options = AgentOptions(
        model=model,
        api_key=api_key,
        local=LocalAgentOptions(cwd=workspace),
    )

    first_timeout = min(timeout_s, 120)
    try:
        bridge = Bridge.launch(workspace=workspace, timeout=first_timeout)
        client = Client(bridge.endpoint, allow_api_key_env_fallback=True)
        print(
            f"[cursor] bridge prompt size: "
            f"{len(prompt)} chars / {len(prompt.encode('utf-8'))} bytes",
            flush=True,
        )
        _write_prompt_artifact(prompt_artifact_path, prompt)
        result = Agent.prompt(prompt, options, client=client)
    except Exception:
        bridge = Bridge.launch(workspace=workspace, timeout=timeout_s)
        client = Client(bridge.endpoint, allow_api_key_env_fallback=True)
        print(
            f"[cursor] bridge prompt size: "
            f"{len(prompt)} chars / {len(prompt.encode('utf-8'))} bytes",
            flush=True,
        )
        _write_prompt_artifact(prompt_artifact_path, prompt)
        result = Agent.prompt(prompt, options, client=client)

    return (result.result or "") if hasattr(result, "result") else str(result)


def _prompt_rest(
    prompt: str,
    *,
    model: str,
    api_key: str,
    timeout_s: float,
    prompt_artifact_path: Path | None = None,
) -> str:
    auth = (api_key, "")
    headers = {"Content-Type": "application/json"}

    with httpx.Client(timeout=60) as client:
        repo_url, starting_ref = _resolve_cloud_repo(client, auth)
        payload = _rest_create_payload(prompt, model, repo_url, starting_ref)
        _write_prompt_artifact(prompt_artifact_path, payload["prompt"]["text"])

        create = client.post(
            f"{API_BASE}/v1/agents",
            json=payload,
            auth=auth,
            headers=headers,
        )
        if create.status_code >= 400:
            raise RuntimeError(
                f"Cursor REST create agent failed: HTTP {create.status_code}: "
                f"{create.text[:800]}"
            )

        data = create.json()
        agent_id = data["agent"]["id"]
        run_id = data["run"]["id"]

        return _wait_rest_run(
            client,
            agent_id,
            run_id,
            auth,
            timeout_s=timeout_s,
            archive_on_finish=True,
        )


def _wait_rest_run(
    client: httpx.Client,
    agent_id: str,
    run_id: str,
    auth: tuple[str, str],
    *,
    timeout_s: float,
    archive_on_finish: bool,
) -> str:
    deadline = time.monotonic() + timeout_s
    poll_s = 20.0

    while time.monotonic() < deadline:
        run_resp = client.get(
            f"{API_BASE}/v1/agents/{agent_id}/runs/{run_id}",
            auth=auth,
        )
        if run_resp.status_code >= 400:
            if archive_on_finish:
                _try_archive(client, agent_id, auth)
            raise RuntimeError(
                f"Cursor REST get run failed: HTTP {run_resp.status_code}: "
                f"{run_resp.text[:800]}"
            )

        run = run_resp.json()
        status = str(run.get("status", "")).upper()
        if status == "FINISHED":
            if archive_on_finish:
                _try_archive(client, agent_id, auth)
            return str(run.get("result") or "")
        if status in _TERMINAL_RUN_STATUSES:
            if archive_on_finish:
                _try_archive(client, agent_id, auth)
            detail = run.get("result") or run
            raise RuntimeError(f"Cursor REST run ended with {status}: {detail}")

        time.sleep(poll_s)

    _try_cancel(client, agent_id, run_id, auth)
    if archive_on_finish:
        _try_archive(client, agent_id, auth)
    raise TimeoutError(f"Cursor REST run timed out after {timeout_s:.0f}s")


def _try_archive(client: httpx.Client, agent_id: str, auth: tuple[str, str]) -> None:
    try:
        client.post(f"{API_BASE}/v1/agents/{agent_id}/archive", auth=auth, timeout=30)
    except Exception:
        pass


def _try_cancel(
    client: httpx.Client,
    agent_id: str,
    run_id: str,
    auth: tuple[str, str],
) -> None:
    try:
        client.post(
            f"{API_BASE}/v1/agents/{agent_id}/runs/{run_id}/cancel",
            auth=auth,
            timeout=30,
        )
    except Exception:
        pass
