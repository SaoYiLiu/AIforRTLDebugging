"""
Build a testbench connection map (static extract + optional Cursor LLM enrichment).

Default: fast **error-focused** map from TB regex + sim mismatch hints (no LLM).
Optional: ``--connection-map-llm`` for a small Cursor pass on compare/mismatch nets only.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

VCD_BLOCK_MARK = "======= VCD OUTPUT BEGIN ======="

# Nets always included when building an error-focused map
_ERROR_NET_SEEDS = frozenset(
    {"tb_match", "tb_mismatch", "match_ref", "match_dut", "match"}
)


def strip_spec_from_prompt(prompt_text: str) -> str:
    """Remove embedded VCD from one-shot ChipBench prompts."""
    if VCD_BLOCK_MARK in prompt_text:
        return prompt_text.split(VCD_BLOCK_MARK, 1)[0].strip()
    return prompt_text.strip()


def strip_buggy_module_from_prompt(prompt_text: str) -> str:
    """Remove embedded buggy TopModule RTL from ChipBench one-shot prompts."""
    text = strip_spec_from_prompt(prompt_text)
    marker = "Based on the problem description above"
    if marker in text:
        return text.split(marker, 1)[0].strip()
    blocks = re.findall(r"```\s*(.*?)\s*```", text, flags=re.DOTALL)
    for block in blocks:
        if "module TopModule" in block:
            return re.sub(
                r"```\s*.*?\s*```",
                "",
                text,
                count=1,
                flags=re.DOTALL,
            ).strip()
    return text.strip()


def extract_error_context(sim_stdout: str) -> dict[str, Any]:
    """
    Parse ChipBench sim output for signals involved in the mismatch.
    """
    ctx: dict[str, Any] = {
        "mismatches": None,
        "samples": None,
        "first_mismatch_time_ps": None,
        "err_output_ports": [],
        "hint_lines": [],
    }

    m = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)\s*samples", sim_stdout)
    if m:
        ctx["mismatches"] = int(m.group(1))
        ctx["samples"] = int(m.group(2))

    tm = re.search(
        r"First mismatch occurred at time\s+(\d+)",
        sim_stdout,
        re.IGNORECASE,
    )
    if tm:
        ctx["first_mismatch_time_ps"] = int(tm.group(1))

    for hm in re.finditer(
        r"Output\s+'([^']+)'\s+has\s+(\d+)\s+mismatches",
        sim_stdout,
        re.IGNORECASE,
    ):
        ctx["err_output_ports"].append(hm.group(1))

    for line in sim_stdout.splitlines():
        if "mismatch" in line.lower() or "Hint:" in line:
            ctx["hint_lines"].append(line.strip())

    return ctx


def extract_static_tb_facts(tb_text: str) -> dict[str, Any]:
    """Deterministic facts from ChipBench-style testbenches (no LLM)."""
    facts: dict[str, Any] = {
        "instances": [],
        "port_bindings": [],
        "compare_assign": None,
        "tb_mismatch_derived": None,
        "dumpvars_signals": [],
    }

    for m in re.finditer(
        r"(RefModule|TopModule|stimulus_gen)\s+(\w+)\s*\((.*?)\)\s*;",
        tb_text,
        flags=re.DOTALL,
    ):
        mod, inst, ports_blob = m.group(1), m.group(2), m.group(3)
        facts["instances"].append({"module": mod, "instance": inst})

        for pm in re.finditer(r"\.(\w+)\s*\(\s*([^.)]+)\s*\)", ports_blob):
            port, net = pm.group(1), pm.group(2).strip()
            facts["port_bindings"].append(
                {"instance": inst, "module": mod, "port": port, "net": net}
            )

    cm = re.search(r"assign\s+tb_match\s*=(.*?);", tb_text, flags=re.DOTALL)
    if cm:
        facts["compare_assign"] = "assign tb_match =" + cm.group(1).strip() + ";"

    if re.search(r"tb_mismatch\s*=\s*~?\s*tb_match", tb_text):
        facts["tb_mismatch_derived"] = "tb_mismatch = ~tb_match (or equivalent)"

    dv = re.search(r"\$dumpvars\s*\((.*?)\)\s*;", tb_text, flags=re.DOTALL)
    if dv:
        raw = dv.group(1)
        tokens = re.findall(r"[\w.]+", raw)
        facts["dumpvars_signals"] = [t for t in tokens if t not in ("1", "0")]

    return facts


_COMPARE_EXPR_STOP = frozenset(
    {
        "assign",
        "and",
        "or",
        "not",
        "xor",
        "xnor",
        "if",
        "else",
        "begin",
        "end",
    }
)


def _nets_from_compare_expr(compare_assign: str | None) -> set[str]:
    if not compare_assign:
        return set()
    rhs = compare_assign
    if "=" in rhs:
        rhs = rhs.split("=", 1)[1]
    words = set(re.findall(r"\b([A-Za-z_][\w]*)\b", rhs))
    return {w for w in words if w not in _COMPARE_EXPR_STOP}


def _error_focus_net_names(
    static: dict[str, Any],
    error_ctx: dict[str, Any],
) -> set[str]:
    """Nets to keep in a minimal error-focused map."""
    focus: set[str] = set(_ERROR_NET_SEEDS)

    focus |= _nets_from_compare_expr(static.get("compare_assign"))

    for port in error_ctx.get("err_output_ports", []):
        focus.add(port)
        focus.add(f"{port}_ref")
        focus.add(f"{port}_dut")

    for b in static.get("port_bindings", []):
        net = b.get("net", "")
        mod = b.get("module", "")
        port = b.get("port", "")
        if not net:
            continue
        if mod == "TopModule" and port == "match":
            focus.add(net)
            focus.add("match_dut")
        elif mod == "RefModule" and port == "match":
            focus.add(net)
            focus.add("match_ref")
        elif mod == "stimulus_gen" and port in (
            "clk",
            "rst_n",
            "a",
            "data",
            "data_valid",
        ):
            focus.add(net)

    for d in static.get("dumpvars_signals", []):
        tail = d.split(".")[-1]
        if tail in focus or any(k in d for k in ("mismatch", "match")):
            focus.add(tail)
            focus.add(d)

    return {n for n in focus if n and not n.isdigit()}


def _role_for_net(net: str, binding: dict[str, Any] | None) -> str:
    if net in ("tb_mismatch",):
        return "compare_fail"
    if net in ("tb_match",):
        return "compare_ok"
    if binding:
        mod = binding.get("module", "")
        port = binding.get("port", "")
        if mod == "TopModule" and port == "match":
            return "dut_output"
        if mod == "RefModule" and port == "match":
            return "ref_output"
        if mod == "stimulus_gen":
            return "stimulus"
    if "match" in net and "dut" in net:
        return "dut_output"
    if "match" in net and "ref" in net:
        return "ref_output"
    if net in ("clk",):
        return "clock"
    if net in ("rst_n",):
        return "reset"
    return "signal"


def build_focused_connection_map(
    static: dict[str, Any],
    error_ctx: dict[str, Any],
) -> dict[str, Any]:
    """
    Fast map: compare/mismatch cone + related DUT/ref ports and dumped signals only.
    """
    focus_nets = _error_focus_net_names(static, error_ctx)
    bindings_by_net: dict[str, dict[str, Any]] = {}
    for b in static.get("port_bindings", []):
        net = b.get("net", "")
        if net in focus_nets:
            bindings_by_net[net] = b

    nets: list[dict[str, Any]] = []
    compare_signals: list[str] = []

    for net in sorted(focus_nets):
        b = bindings_by_net.get(net)
        role = _role_for_net(net, b)
        source = f"{b['instance']}.{b['port']}" if b else "tb"
        vcd_hier = f"tb.{net}" if net and not str(net).startswith("tb.") else net
        nets.append(
            {
                "net": net,
                "role": role,
                "source": source,
                "vcd_hier": vcd_hier,
            }
        )
        if role in (
            "compare_fail",
            "compare_ok",
            "dut_output",
            "ref_output",
        ):
            compare_signals.append(net)

    instances: list[dict[str, Any]] = []
    seen_inst: set[str] = set()
    for b in bindings_by_net.values():
        inst = b.get("instance", "")
        mod = b.get("module", "")
        if inst in seen_inst:
            continue
        seen_inst.add(inst)
        role = (
            "dut"
            if mod == "TopModule"
            else "ref"
            if mod == "RefModule"
            else "stimulus"
        )
        instances.append({"instance": inst, "module": mod, "role": role})

    vcd_trace: list[str] = []
    priority_order = (
        "tb_mismatch",
        "tb.tb_mismatch",
        "match_dut",
        "match_ref",
        "tb.match_dut",
        "tb.match_ref",
    )
    for p in priority_order:
        if p not in vcd_trace:
            vcd_trace.append(p)
    for d in static.get("dumpvars_signals", []):
        tail = d.split(".")[-1]
        if tail in focus_nets:
            hier = d if "." in d else f"tb.{d}"
            if hier not in vcd_trace:
                vcd_trace.append(hier)
    for n in nets:
        if n["role"] in ("dut_output", "ref_output", "compare_fail"):
            h = n["vcd_hier"]
            if h and h not in vcd_trace:
                vcd_trace.append(h)

    return {
        "instances": instances,
        "nets": nets,
        "compare": {
            "expr": static.get("compare_assign"),
            "signals": sorted(set(compare_signals + ["tb_match", "tb_mismatch"])),
        },
        "vcd_trace_signals": vcd_trace[:12],
        "error_context": error_ctx,
        "focus_net_count": len(focus_nets),
        "source": "static_error_focused",
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if fence:
        text = fence.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    return json.loads(text)


def format_connection_map_for_llm(connection_map: dict[str, Any] | None) -> str:
    if not connection_map:
        return ""
    lines = ["## Connection map (error-focused)"]
    ec = connection_map.get("error_context") or {}
    if ec.get("mismatches") is not None:
        lines.append(
            f"- mismatches: {ec.get('mismatches')} / {ec.get('samples')} samples, "
            f"first_fail_ps={ec.get('first_mismatch_time_ps')}"
        )
    for net in connection_map.get("nets", [])[:16]:
        lines.append(
            f"- `{net.get('net')}` role={net.get('role')} vcd={net.get('vcd_hier', '')}"
        )
    if connection_map.get("compare"):
        c = connection_map["compare"]
        lines.append(f"- compare signals: {c.get('signals', [])}")
    vcd_focus = connection_map.get("vcd_trace_signals", [])
    if vcd_focus:
        lines.append(f"- VCD focus: {vcd_focus}")
    return "\n".join(lines)


def resolve_vcd_priority_signals(
    connection_map: dict[str, Any] | None,
    available_signals: list[str],
    *,
    max_signals: int = 12,
) -> list[str]:
    from react.vcd_trace import without_clock_vcd_signals

    if not connection_map:
        return []

    role_priority = (
        "compare_fail",
        "compare_ok",
        "dut_output",
        "ref_output",
        "compare",
        "stimulus",
        "clock",
        "reset",
    )

    candidates: list[str] = []
    for sig in connection_map.get("vcd_trace_signals", []):
        if isinstance(sig, str):
            candidates.append(sig)

    nets = connection_map.get("nets", [])
    nets_sorted = sorted(
        nets,
        key=lambda n: (
            role_priority.index(n["role"])
            if n.get("role") in role_priority
            else len(role_priority)
        ),
    )
    for n in nets_sorted:
        for key in ("vcd_hier", "net"):
            v = n.get(key)
            if v and isinstance(v, str):
                candidates.append(v)

    for s in connection_map.get("compare", {}).get("signals", []):
        if isinstance(s, str):
            candidates.append(s)

    resolved: list[str] = []
    for name in candidates:
        name = name.strip()
        if not name:
            continue
        if name in available_signals:
            if name not in resolved:
                resolved.append(name)
            continue
        tail = name.split(".")[-1]
        for avail in available_signals:
            if (
                avail.endswith("." + name)
                or avail.endswith("." + tail)
                or tail in avail
                or name in avail
            ):
                if avail not in resolved:
                    resolved.append(avail)
        if len(resolved) >= max_signals:
            break

    return without_clock_vcd_signals(resolved[:max_signals])


def _extract_tb_compare_snippet(tb_text: str, max_lines: int = 120) -> str:
    """Small TB excerpt: compare assign + three instance hooks + dumpvars."""
    lines = tb_text.splitlines()
    keep: list[str] = []
    for i, line in enumerate(lines):
        if any(
            k in line
            for k in (
                "assign tb_match",
                "tb_mismatch",
                "RefModule",
                "TopModule",
                "stimulus_gen",
                "$dumpvars",
                "module tb",
            )
        ):
            keep.append(line)
    if len(keep) > max_lines:
        keep = keep[:max_lines]
    return "\n".join(keep)


def build_connection_map_with_cursor(
    *,
    prob_id: str,
    tb_text: str,
    static_facts: dict[str, Any],
    error_ctx: dict[str, Any],
    focus_nets: set[str],
    model: str = "composer-2.5",
) -> dict[str, Any]:
    """
    Small Cursor call: label roles / vcd_hier for error-related nets only.
    """
    from react.cursor_transport import cursor_prompt  # noqa: E402

    if "CURSOR_API_KEY" not in os.environ:
        raise RuntimeError("CURSOR_API_KEY is not set in environment.")

    tb_snip = _extract_tb_compare_snippet(tb_text)
    seed_list = sorted(focus_nets)

    prompt = f"""You are labeling **error-related** testbench signals for RTL debug (ChipBench).

## Problem
{prob_id}

## Simulation error context
```json
{json.dumps(error_ctx, indent=2)}
```

## Nets to map (ONLY these — do not add others)
{seed_list}

## Testbench excerpt
```verilog
{tb_snip}
```

## Static hints
```json
{json.dumps({k: static_facts[k] for k in ("compare_assign", "tb_mismatch_derived", "dumpvars_signals", "port_bindings") if k in static_facts}, indent=2)[:4000]}
```

## Task
Return JSON only:
```json
{{
  "nets": [
    {{"net": "match_dut", "role": "dut_output", "source": "top_module1.match", "vcd_hier": "tb.match_dut"}}
  ],
  "compare": {{"expr": "...", "signals": ["match_ref", "match_dut", "tb_match", "tb_mismatch"]}},
  "vcd_trace_signals": ["tb.tb_mismatch", "tb.match_dut", "tb.match_ref"]
}}
```
Max 12 entries in vcd_trace_signals. Roles: compare_fail, compare_ok, dut_output, ref_output, stimulus, clock, reset.
"""

    raw, transport = cursor_prompt(
        prompt,
        model=model,
        api_key=os.environ["CURSOR_API_KEY"],
        workspace=os.getcwd(),
        timeout_s=180,
    )
    try:
        parsed = _extract_json_object(raw)
        # Merge with static focused scaffold
        base = build_focused_connection_map(static_facts, error_ctx)
        base["nets"] = parsed.get("nets") or base["nets"]
        base["compare"] = parsed.get("compare") or base["compare"]
        base["vcd_trace_signals"] = (
            parsed.get("vcd_trace_signals") or base["vcd_trace_signals"]
        )[:12]
        base["source"] = (
            "cursor_sdk_error_focused"
            if transport == "bridge"
            else "cursor_rest_error_focused"
        )
        return base
    except (json.JSONDecodeError, ValueError):
        fallback = build_focused_connection_map(static_facts, error_ctx)
        fallback["cursor_raw"] = raw[:2000]
        fallback["source"] = "static_error_focused_cursor_parse_failed"
        return fallback


def _is_focused_map_cached(data: dict[str, Any]) -> bool:
    """True if cache is the new compact error-focused format."""
    src = data.get("source", "")
    if src.startswith(("static_error", "cursor_sdk_error", "cursor_rest_error")):
        return True
    # Old full-LLM maps had a large ``connections`` list or embedded static_facts.
    if data.get("connections") or data.get("static_facts"):
        return False
    return bool(data.get("nets") and data.get("vcd_trace_signals"))


def load_connection_map(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not _is_focused_map_cached(data):
        return None
    return data


def save_connection_map(path: Path, connection_map: dict[str, Any]) -> None:
    slim = {k: v for k, v in connection_map.items() if k != "static_facts"}
    path.write_text(json.dumps(slim, indent=2), encoding="utf-8")


def ensure_connection_map(
    *,
    prob_id: str,
    prompt_path: Path,
    tb_path: Path,
    ref_path: Path,
    out_dir: Path,
    sim_stdout: str,
    use_llm: bool = False,
    cursor_model: str = "composer-2.5",
    force_rebuild: bool = False,
) -> dict[str, Any]:
    """
    Load cached connection_map.json or build after first sim failure.

    Default (``use_llm=False``): instant static error-focused map.
    ``use_llm=True`` (``--connection-map-llm``): small Cursor pass on same net list.
    """
    cache = out_dir / "connection_map.json"
    if not force_rebuild:
        loaded = load_connection_map(cache)
        if loaded:
            return loaded

    tb_text = tb_path.read_text(encoding="utf-8", errors="ignore")
    static = extract_static_tb_facts(tb_text)
    error_ctx = extract_error_context(sim_stdout)
    focus_nets = _error_focus_net_names(static, error_ctx)

    if use_llm and "CURSOR_API_KEY" in os.environ:
        print(
            f"[{prob_id}] Connection map (error-focused LLM, {len(focus_nets)} nets)...",
            flush=True,
        )
        connection_map = build_connection_map_with_cursor(
            prob_id=prob_id,
            tb_text=tb_text,
            static_facts=static,
            error_ctx=error_ctx,
            focus_nets=focus_nets,
            model=cursor_model,
        )
    else:
        print(
            f"[{prob_id}] Connection map (static error-focused, {len(focus_nets)} nets)...",
            flush=True,
        )
        connection_map = build_focused_connection_map(static, error_ctx)

    save_connection_map(cache, connection_map)
    (out_dir / "connection_map_prompt_notes.txt").write_text(
        f"source={connection_map.get('source')}\n"
        f"focus_net_count={connection_map.get('focus_net_count', len(focus_nets))}\n"
        f"vcd_trace_signals={connection_map.get('vcd_trace_signals')}\n",
        encoding="utf-8",
    )
    return connection_map
