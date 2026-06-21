from __future__ import annotations

import argparse
import json
import os
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).absolute().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description="Run one Cursor SDK bridge prompt.")
    ap.add_argument("--prompt-path", required=True)
    ap.add_argument("--output-path", required=True)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--model", default="composer-2.5")
    ap.add_argument("--timeout-s", type=float, default=600)
    args = ap.parse_args()

    try:
        from cursor_sdk import Agent, AgentOptions, LocalAgentOptions  # type: ignore
        from cursor_sdk._bridge import Bridge  # type: ignore
        from cursor_sdk._client import Client  # type: ignore

        api_key = os.environ["CURSOR_API_KEY"]
        prompt = Path(args.prompt_path).read_text(encoding="utf-8")
        workspace = str(REPO_ROOT)
        os.chdir(workspace)
        bridge = Bridge.launch(
            workspace=workspace,
            timeout=min(args.timeout_s, 120),
        )
        client = Client(bridge.endpoint, allow_api_key_env_fallback=True)
        options = AgentOptions(
            model=args.model,
            api_key=api_key,
            local=LocalAgentOptions(cwd=workspace),
        )
        print(
            f"[cursor-helper] prompt size: "
            f"{len(prompt)} chars / {len(prompt.encode('utf-8'))} bytes",
            flush=True,
        )
        result = Agent.prompt(prompt, options, client=client)
        text = (result.result or "") if hasattr(result, "result") else str(result)
        payload = {"ok": True, "result": text}
    except Exception as exc:
        payload = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }

    Path(args.output_path).write_text(json.dumps(payload), encoding="utf-8")
    if not payload["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
