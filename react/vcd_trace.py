"""
VCD causal tracing: find transitions before a simulation failure.

Inspired by veridebugger/backend/vcd_parser.py::trace_failure.
Uses vcdvcd (same as mcp_server.vcd_to_text) for consistency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CausalTransition:
    signal: str
    time: int
    value: str
    delta: int


def _load_vcd(vcd_path: str | Path) -> Any:
    from vcdvcd import VCDVCD  # type: ignore

    return VCDVCD(str(vcd_path), store_tvs=True)


def find_mismatch_signal_names(available: list[str]) -> list[str]:
    """Prefer ChipBench tb_mismatch signals for failure tracing."""
    names: list[str] = []
    for s in available:
        if "tb_mismatch" in s or s.endswith(".tb_mismatch"):
            names.append(s)
    return names


def find_first_mismatch_time(
    vcd_path: str | Path,
    signal_names: list[str] | None = None,
) -> int | None:
    """
    Return the first simulation time where tb_mismatch becomes active (non-zero).
    """
    vcd = _load_vcd(vcd_path)
    available = sorted(vcd.signals)

    candidates = signal_names or find_mismatch_signal_names(available)
    if not candidates:
        for pat in ("tb_mismatch", "tb.tb_mismatch"):
            for s in available:
                if pat in s:
                    candidates.append(s)
                    break

    first_time: int | None = None
    for sig in candidates:
        if sig not in vcd.signals:
            continue
        tv = list(getattr(vcd[sig], "tv", []) or [])
        for t, v in tv:
            if str(v) not in ("0", "b0", "x", "z", ""):
                if first_time is None or t < first_time:
                    first_time = int(t)
                break

    return first_time


def infer_failure_time_ps(sim_stdout: str, vcd_path: str | Path | None = None) -> int | None:
    """Parse ChipBench hint line, else fall back to first tb_mismatch transition."""
    m = re.search(
        r"First mismatch occurred at time\s+(\d+)",
        sim_stdout,
        re.IGNORECASE,
    )
    if m:
        return int(m.group(1))

    if vcd_path and Path(vcd_path).exists():
        return find_first_mismatch_time(vcd_path)

    return None


def trace_vcd_failure(
    vcd_path: str | Path,
    failure_time: int,
    window: int = 100,
    max_events: int = 20,
    priority_signals: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Collect signal transitions in [failure_time - window, failure_time].
    Returns most recent transitions first (smallest delta to failure).
    """
    vcd = _load_vcd(vcd_path)
    start_time = max(0, failure_time - window)
    causal: list[CausalTransition] = []

    priority_set = set(priority_signals or [])

    for sig in sorted(vcd.signals):
        tv = list(getattr(vcd[sig], "tv", []) or [])
        for t, v in tv:
            t_int = int(t)
            if start_time <= t_int <= failure_time:
                causal.append(
                    CausalTransition(
                        signal=sig,
                        time=t_int,
                        value=str(v),
                        delta=failure_time - t_int,
                    )
                )

    # Prefer priority signals, then sort by recency (smallest delta).
    causal.sort(
        key=lambda x: (0 if x.signal in priority_set else 1, x.delta, x.signal),
    )

    return [
        {
            "signal": c.signal,
            "time": c.time,
            "value": c.value,
            "delta_to_failure": c.delta,
        }
        for c in causal[:max_events]
    ]


def build_vcd_debug_summary(
    vcd_path: str | Path,
    sim_stdout: str,
    *,
    connection_map: dict[str, Any] | None = None,
    window: int = 100,
    max_trace_events: int = 20,
) -> dict[str, Any]:
    """
    Build an LLM-friendly VCD summary: signal catalog, selected waves, causal trace.
    """
    path = Path(vcd_path)
    if not path.exists():
        return {"ok": False, "error": f"VCD not found: {path}"}

    try:
        vcd = _load_vcd(path)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    available = sorted(vcd.signals)
    failure_time = infer_failure_time_ps(sim_stdout, path)

    priority: list[str] = []
    if connection_map:
        from react.connection_map import resolve_vcd_priority_signals

        priority = resolve_vcd_priority_signals(
            connection_map, available, max_signals=12
        )

    if not priority:
        for s in available:
            if any(
                k in s
                for k in (
                    "tb_mismatch",
                    "tb.tb_mismatch",
                    "match_ref",
                    "match_dut",
                    "tb.match",
                )
            ):
                priority.append(s)
        priority = priority[:12]

    causal_chain: list[dict[str, Any]] = []
    if failure_time is not None:
        causal_chain = trace_vcd_failure(
            path,
            failure_time=failure_time,
            window=window,
            max_events=max_trace_events,
            priority_signals=priority,
        )

    return {
        "ok": True,
        "vcd_path": str(path),
        "failure_time": failure_time,
        "signals": available[:500],
        "signals_truncated": len(available) > 500,
        "priority_signals": priority,
        "priority_from_connection_map": bool(connection_map and priority),
        "causal_chain": causal_chain,
    }


def format_causal_chain_for_llm(causal_chain: list[dict[str, Any]]) -> str:
    if not causal_chain:
        return "(no causal transitions in trace window)"
    lines = []
    for ev in causal_chain:
        lines.append(
            f"- {ev['signal']} @ t={ev['time']}: {ev['value']} "
            f"(Δ={ev['delta_to_failure']} before failure)"
        )
    return "\n".join(lines)
