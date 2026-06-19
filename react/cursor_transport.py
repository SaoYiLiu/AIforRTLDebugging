"""
Cursor LLM transport: SDK local bridge (WSL/desktop) or direct REST API (Linux servers).

On machines where ``cursor-sdk-bridge`` works, we use the SDK local runtime.
Elsewhere (e.g. headless Linux where curl to api.cursor.com works but the bridge
returns opaque 500s), we call the Cloud Agents REST API with a no-repo agent.

Set ``CURSOR_TRANSPORT`` to ``auto`` (default), ``bridge``, or ``rest``.
"""

from __future__ import annotations

import os
import time
from typing import Literal

import httpx

TransportName = Literal["bridge", "rest"]
TransportMode = Literal["auto", "bridge", "rest"]

API_BASE = "https://api.cursor.com"
_TERMINAL_RUN_STATUSES = frozenset({"FINISHED", "ERROR", "CANCELLED", "EXPIRED"})

_bridge_probe_result: bool | None = None
_cloud_repo_cache: tuple[str, str] | None = None


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


def _rest_create_payload(prompt: str, model: str, repo_url: str, starting_ref: str) -> dict:
    return {
        "prompt": {
            "text": (
                "Reply in the agent message only. Do not create, edit, or commit "
                "repository files.\n\n"
                + prompt
            ),
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
    try:
        from cursor_sdk._bridge import Bridge  # type: ignore
        from cursor_sdk._client import Client  # type: ignore

        bridge = Bridge.launch(workspace=workspace, timeout=timeout_s)
        client = Client(bridge.endpoint, allow_api_key_env_fallback=True)
        client.list_models(api_key=api_key)
        return True
    except Exception:
        return False


def bridge_available(*, api_key: str, workspace: str | None = None) -> bool:
    global _bridge_probe_result

    mode = get_transport_mode()
    if mode == "rest":
        return False
    if mode == "bridge":
        return True

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


def cursor_prompt(
    prompt: str,
    *,
    model: str = "composer-2.5",
    api_key: str | None = None,
    workspace: str | None = None,
    timeout_s: float = 600,
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

    if mode == "bridge" or (mode == "auto" and bridge_available(api_key=key, workspace=ws)):
        try:
            return _prompt_bridge(
                prompt,
                model=model,
                api_key=key,
                workspace=ws,
                timeout_s=timeout_s,
            ), "bridge"
        except Exception as exc:
            if mode == "bridge":
                raise
            print(
                f"[cursor] SDK bridge call failed ({type(exc).__name__}); "
                "falling back to REST API.",
                flush=True,
            )
            global _bridge_probe_result
            _bridge_probe_result = False

    return _prompt_rest(prompt, model=model, api_key=key, timeout_s=timeout_s), "rest"


def _prompt_bridge(
    prompt: str,
    *,
    model: str,
    api_key: str,
    workspace: str,
    timeout_s: float,
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
        result = Agent.prompt(prompt, options, client=client)
    except Exception:
        bridge = Bridge.launch(workspace=workspace, timeout=timeout_s)
        client = Client(bridge.endpoint, allow_api_key_env_fallback=True)
        result = Agent.prompt(prompt, options, client=client)

    return (result.result or "") if hasattr(result, "result") else str(result)


def _prompt_rest(
    prompt: str,
    *,
    model: str,
    api_key: str,
    timeout_s: float,
) -> str:
    auth = (api_key, "")
    headers = {"Content-Type": "application/json"}

    with httpx.Client(timeout=60) as client:
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
        agent_id = data["agent"]["id"]
        run_id = data["run"]["id"]

        deadline = time.monotonic() + timeout_s
        poll_s = 3.0

        while time.monotonic() < deadline:
            run_resp = client.get(
                f"{API_BASE}/v1/agents/{agent_id}/runs/{run_id}",
                auth=auth,
            )
            if run_resp.status_code >= 400:
                raise RuntimeError(
                    f"Cursor REST get run failed: HTTP {run_resp.status_code}: "
                    f"{run_resp.text[:800]}"
                )

            run = run_resp.json()
            status = str(run.get("status", "")).upper()
            if status == "FINISHED":
                _try_archive(client, agent_id, auth)
                return str(run.get("result") or "")
            if status in _TERMINAL_RUN_STATUSES:
                _try_archive(client, agent_id, auth)
                detail = run.get("result") or run
                raise RuntimeError(f"Cursor REST run ended with {status}: {detail}")

            time.sleep(poll_s)

        _try_cancel(client, agent_id, run_id, auth)
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
