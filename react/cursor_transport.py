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
_rest_models_cache: list[dict[str, Any]] | None = None
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


def _normalize_repo_url(url: str) -> str:
    cleaned = url.strip().rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    return cleaned


def _fetch_rest_models(client: httpx.Client, auth: tuple[str, str]) -> list[dict[str, Any]]:
    global _rest_models_cache

    if _rest_models_cache is not None:
        return _rest_models_cache

    resp = client.get(f"{API_BASE}/v1/models", auth=auth, timeout=120)
    if resp.status_code >= 400:
        raise RuntimeError(
            f"Cursor REST list models failed: HTTP {resp.status_code}: "
            f"{resp.text[:800]}"
        )

    _rest_models_cache = list(resp.json().get("items") or [])
    return _rest_models_cache


def _resolve_rest_model_id(
    client: httpx.Client,
    auth: tuple[str, str],
    requested: str,
) -> str | None:
    """
    Map an SDK/CLI model slug to a REST ``model.id``.

    The local bridge accepts names like ``composer-2.5``, but ``POST /v1/agents``
    only accepts IDs (or aliases) returned by ``GET /v1/models``. Passing an
    unknown ID yields HTTP 400.
    """
    requested = requested.strip()
    if not requested:
        return None

    items = _fetch_rest_models(client, auth)

    # SDK/CLI slugs like composer-2.5 are not accepted by POST /v1/agents even when
    # they appear in marketing docs; map to the canonical composer REST id.
    if "2.5" in requested or requested.endswith(".5"):
        for item in items:
            model_id = str(item.get("id", "")).strip()
            if model_id == "composer-2" or model_id.startswith("composer-"):
                print(
                    f"[cursor] REST model mapped: {requested!r} -> {model_id!r}",
                    flush=True,
                )
                return model_id

    for item in items:
        model_id = str(item.get("id", "")).strip()
        if not model_id:
            continue
        aliases = [str(alias).strip() for alias in (item.get("aliases") or []) if str(alias).strip()]
        if requested == model_id or requested in aliases:
            if requested != model_id:
                print(
                    f"[cursor] REST model alias: {requested!r} -> {model_id!r}",
                    flush=True,
                )
            return model_id

    lower = requested.lower()
    if lower.startswith("composer"):
        for item in items:
            model_id = str(item.get("id", "")).strip()
            if model_id.lower().startswith("composer"):
                print(
                    f"[cursor] REST model mapped: {requested!r} -> {model_id!r}",
                    flush=True,
                )
                return model_id

    for item in items:
        model_id = str(item.get("id", "")).strip()
        aliases = [str(alias).strip().lower() for alias in (item.get("aliases") or [])]
        if lower == model_id.lower() or lower in aliases:
            print(
                f"[cursor] REST model mapped: {requested!r} -> {model_id!r}",
                flush=True,
            )
            return model_id

    print(
        f"[cursor] REST model {requested!r} not listed by GET /v1/models; "
        "omitting model field so Cursor uses the account default.",
        flush=True,
    )
    return None


def _resolve_cloud_repo(client: httpx.Client, auth: tuple[str, str]) -> tuple[str, str]:
    """
    Cloud Agents on many accounts cannot use no-repo mode (environment_public_id error).
    Resolve a repo from CURSOR_CLOUD_REPO_URL or GET /v1/repositories (cached).
    """
    global _cloud_repo_cache

    explicit = os.environ.get("CURSOR_CLOUD_REPO_URL", "").strip()
    ref = _cloud_repo_ref()
    if explicit:
        return _normalize_repo_url(explicit), ref

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

    preferred_name = os.environ.get("CURSOR_CLOUD_REPO_URL", "").strip().lower()
    chosen = items[0]
    if preferred_name:
        for item in items:
            url = str(item.get("url", "")).strip().lower()
            if preferred_name.rstrip("/").removesuffix(".git") in url:
                chosen = item
                break
    else:
        for item in items:
            url = str(item.get("url", "")).strip().lower()
            if "aifordebugging" in url:
                chosen = item
                break

    url = _normalize_repo_url(str(chosen.get("url", "")).strip())
    if not url:
        raise RuntimeError("Cursor REST: /v1/repositories returned no usable repo URL.")

    ref = (
        str(chosen.get("defaultBranch") or chosen.get("defaultRef") or chosen.get("ref") or "")
        .strip()
        or _cloud_repo_ref()
    )

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


def _rest_create_payload(
    prompt: str,
    model_id: str | None,
    repo_url: str,
    starting_ref: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "prompt": {
            "text": _rest_prompt_text(prompt),
        },
        "repos": [{"url": repo_url, "startingRef": starting_ref}],
        "autoCreatePR": False,
    }
    if model_id:
        payload["model"] = {"id": model_id}
    return payload


def _rest_create_payload_no_repo(prompt: str, model_id: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "prompt": {
            "text": _rest_prompt_text(prompt),
        },
        "autoCreatePR": False,
    }
    if model_id:
        payload["model"] = {"id": model_id}
    return payload


def _create_rest_agent(
    client: httpx.Client,
    auth: tuple[str, str],
    headers: dict[str, str],
    *,
    prompt: str,
    model: str,
    repo_url: str,
    starting_ref: str,
) -> httpx.Response:
    rest_model_id = _resolve_rest_model_id(client, auth, model)
    print(
        f"[cursor] REST create agent: model={rest_model_id or '(account default)'} "
        f"repo={repo_url} ref={starting_ref}",
        flush=True,
    )
    variants: list[tuple[str, dict[str, Any]]] = [
        ("repos", _rest_create_payload(prompt, rest_model_id, repo_url, starting_ref)),
        ("repos,no-model", _rest_create_payload(prompt, None, repo_url, starting_ref)),
        ("no-repo", _rest_create_payload_no_repo(prompt, rest_model_id)),
        ("no-repo,no-model", _rest_create_payload_no_repo(prompt, None)),
    ]
    last_err = "Cursor REST create agent failed with no attempts."
    for label, payload in variants:
        create = client.post(
            f"{API_BASE}/v1/agents",
            json=payload,
            auth=auth,
            headers=headers,
        )
        if create.status_code >= 400:
            _raise_if_cursor_billing_error(create, action=f"create agent ({label})")
        if create.status_code < 400:
            if label != "repos":
                print(f"[cursor] REST create agent succeeded with fallback: {label}", flush=True)
            return create
        last_err = _rest_create_error_message(create, action=f"create agent ({label})")
        print(f"[cursor] {last_err}", flush=True)
    raise RuntimeError(last_err)


def _rest_create_error_message(resp: httpx.Response, *, action: str) -> str:
    body = resp.text[:1200]
    try:
        parsed = resp.json()
        if isinstance(parsed, dict):
            err = parsed.get("error")
            if isinstance(err, dict):
                body = json.dumps(err, ensure_ascii=False)
            elif isinstance(err, str):
                body = err
    except Exception:
        pass
    return f"Cursor REST {action} failed: HTTP {resp.status_code}: {body}"


def _is_cursor_billing_error(text: str) -> bool:
    return "usage_limit_exceeded" in text or "Usage-based pricing required" in text


def _raise_if_cursor_billing_error(resp: httpx.Response, *, action: str) -> None:
    if resp.status_code < 400:
        return
    if _is_cursor_billing_error(resp.text):
        detail = _rest_create_error_message(resp, action=action)
        raise RuntimeError(
            "Cursor Cloud Agents (REST API) are unavailable on this account: "
            "usage-based pricing with a spend limit is required "
            "(Background Agent needs at least $2 headroom).\n"
            "Enable it at https://www.cursor.com/dashboard?tab=settings\n"
            "Or use the local bridge instead: export CURSOR_TRANSPORT=bridge\n"
            f"Details: {detail}"
        )


def get_transport_mode() -> TransportMode:
    raw = os.environ.get("CURSOR_TRANSPORT", "auto").strip().lower()
    if raw in ("bridge", "sdk"):
        return "bridge"
    if raw == "rest":
        return "rest"
    return "auto"


def reset_bridge_probe() -> None:
    """Clear cached bridge probe (for tests)."""
    global _bridge_probe_result, _cloud_repo_cache, _rest_models_cache
    _bridge_probe_result = None
    _cloud_repo_cache = None
    _rest_models_cache = None


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
        rest_exc: Exception | None = None
        bridge_exc: Exception | None = None

        if self.mode == "auto":
            try:
                return self._prompt_rest_session(
                    prompt,
                    model=model,
                    timeout_s=timeout_s,
                    prompt_artifact_path=prompt_artifact_path,
                ), "rest"
            except Exception as exc:
                rest_exc = exc
                print(f"[cursor] REST session call failed: {rest_exc}", flush=True)
                print(
                    "[cursor] Trying SDK bridge.",
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
            except Exception as exc:
                bridge_exc = exc
                # The local bridge is more reliable when each prompt gets a
                # fresh bridge process. Keep only the session-level fallback
                # state here; do not reuse a bridge/client across prompts.
                self.close()
                self._bridge_failed = True
                bridge_error_name = type(bridge_exc).__name__
                if self.mode == "bridge":
                    raise
                print(
                    f"[cursor] SDK bridge session failed ({bridge_error_name}); "
                    "falling back to REST API.",
                    flush=True,
                )

        if (
            self.mode == "auto"
            and rest_exc is not None
            and _is_cursor_billing_error(str(rest_exc))
        ):
            if bridge_exc is not None:
                raise RuntimeError(
                    "Cursor REST is blocked by account billing limits and the SDK "
                    "bridge also failed. Enable usage-based pricing for REST at "
                    "https://www.cursor.com/dashboard?tab=settings — or fix the "
                    "bridge (export CURSOR_TRANSPORT=bridge)."
                ) from bridge_exc
            raise RuntimeError(
                "Cursor REST is blocked by account billing limits. Enable "
                "usage-based pricing at https://www.cursor.com/dashboard?tab=settings "
                "— or use the local bridge (export CURSOR_TRANSPORT=bridge)."
            ) from rest_exc

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
            create = _create_rest_agent(
                client,
                auth,
                headers,
                prompt=prompt,
                model=model,
                repo_url=repo_url,
                starting_ref=starting_ref,
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
                raise RuntimeError(_rest_create_error_message(create, action="create run"))
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

    text = (result.result or "") if hasattr(result, "result") else str(result)
    status = getattr(result, "status", None)
    if not str(text).strip():
        raise RuntimeError(
            "Cursor bridge returned an empty response"
            + (f" (status={status!r})" if status is not None else "")
            + ". Try CURSOR_TRANSPORT=rest or shorten the fix prompt."
        )
    return str(text)


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
        create = _create_rest_agent(
            client,
            auth,
            headers,
            prompt=prompt,
            model=model,
            repo_url=repo_url,
            starting_ref=starting_ref,
        )
        _write_prompt_artifact(
            prompt_artifact_path,
            _rest_prompt_text(prompt),
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
