"""
Auto-generate SymbiYosys formal wrappers (TopModule_formal.sv) from ChipBench spec.

Uses lightweight port-level asserts (no golden shadow models) so BMC stays fast.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from react.connection_map import strip_spec_from_prompt  # noqa: E402
from react.cursor_transport import CursorPromptSession, cursor_prompt  # noqa: E402

REPO_ROOT = Path(__file__).absolute().parents[1]

FormalMode = Literal["bmc", "prove"]

# Default BMC depth kept low for fast debug iterations.
DEFAULT_FORMAL_DEPTH = 10

SBY_TEMPLATE = """[options]
mode {mode}
depth {depth}

[engines]
smtbmc z3

[script]
read -formal -sv TopModule.sv TopModule_formal.sv
hierarchy -check -top TopModule_formal
proc; opt
memory; opt

[files]
TopModule.sv
TopModule_formal.sv
"""

# Lightweight pattern: assert directly on DUT ports, no internal reference state.
FORMAL_EXAMPLE = """
module TopModule_formal;
    localparam integer W = 4;
    (* gclk *) reg clk;
    (* anyseq *) reg rst_n;
    (* anyseq *) reg en;
    wire [W-1:0] q;

    TopModule #(.W(W)) dut (
        .clk(clk), .rst_n(rst_n), .en(en), .q(q)
    );

    always @(posedge clk) begin
        if ($initstate) begin
            assume(!rst_n);
        end else if (!$past(rst_n)) begin
            assert(q == {W{1'b0}});
        end else if ($past(en)) begin
            assert(q == ($past(q) + 1'b1));
        end else begin
            assert(q == $past(q));
        end
    end
endmodule
""".strip()

# Patterns that indicate a heavy shadow/reference model (reject for BMC speed).
_SHADOW_PATTERNS = [
    r"\bgold_\w+",
    r"\bref_\w+",
    r"\bshadow_\w+",
    r"\bmodel_\w+",
    r"\bexpected_\w+",
    r"\bn_state\b",
    r"\bc_state\b",
    r"\bnstate\b",
    r"\bRefModule\b",
]

_MAX_WRAPPER_LINES = 80
_MAX_INTERNAL_REGS = 0  # only (* gclk *) clk and (* anyseq *) inputs allowed as regs


@dataclass(frozen=True)
class FormalWrapperResult:
    formal_sv: str
    rationale: str
    raw_text: str
    transport: str
    sby_path: Path
    formal_sv_path: Path


def _extract_module_header(rtl: str) -> str | None:
    m = re.search(r"module\s+TopModule\s*(\([\s\S]*?\));", rtl)
    return m.group(0) if m else None


def _extract_formal_module(text: str) -> str | None:
    patterns = [
        r"```(?:verilog|systemverilog|sv)?\s*(module\s+TopModule_formal[\s\S]*?endmodule)\s*```",
        r"(module\s+TopModule_formal[\s\S]*?endmodule)",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip() + "\n"
    return None


def _internal_reg_count(formal_sv: str) -> int:
    """Count internal reg declarations (excluding gclk/anyseq input regs)."""
    count = 0
    for m in re.finditer(r"^\s*reg\b", formal_sv, re.MULTILINE):
        start = m.start()
        line_end = formal_sv.find("\n", start)
        line = formal_sv[start:line_end if line_end != -1 else None]
        if "gclk" in line or "anyseq" in line:
            continue
        count += 1
    return count


def validate_formal_wrapper(formal_sv: str, *, require_assert: bool = True) -> list[str]:
    """Return validation errors (empty if OK). Rejects heavy shadow-model wrappers."""
    errors: list[str] = []
    if "module TopModule_formal" not in formal_sv:
        errors.append("missing module TopModule_formal")
    if "TopModule" not in formal_sv or "dut" not in formal_sv.lower():
        errors.append("missing TopModule dut instantiation")
    if require_assert and "assert" not in formal_sv:
        errors.append("missing assert statements")
    if "(* gclk *)" not in formal_sv:
        errors.append("missing (* gclk *) clock")
    for pat in _SHADOW_PATTERNS:
        if re.search(pat, formal_sv, re.IGNORECASE):
            errors.append(
                f"contains shadow/reference pattern ({pat}) — use port-level asserts only"
            )
            break
    line_count = len(formal_sv.splitlines())
    if line_count > _MAX_WRAPPER_LINES:
        errors.append(f"wrapper too large ({line_count} lines > {_MAX_WRAPPER_LINES})")
    internal_regs = _internal_reg_count(formal_sv)
    if internal_regs > _MAX_INTERNAL_REGS:
        errors.append(
            f"wrapper has {internal_regs} internal reg(s) — "
            "no shadow state allowed; assert on DUT ports only"
        )
    return errors


def _parse_ports(header: str) -> list[dict[str, str]]:
    """Parse simple port list from module header."""
    ports: list[dict[str, str]] = []
    inner = re.search(r"\(([\s\S]*)\)", header)
    if not inner:
        return ports
    for chunk in inner.group(1).split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(
            r"(?:(input|output|inout)\s+)?(?:(?:wire|reg)\s+)?(?:\[([^\]]+)\]\s+)?(\w+)",
            chunk,
        )
        if m:
            direction = m.group(1) or "input"
            width = m.group(2)
            name = m.group(3)
            ports.append({"dir": direction, "width": width or "", "name": name})
    return ports


def build_minimal_formal_wrapper(dut_sv: str) -> str:
    """
    Deterministic fast wrapper: reset assumptions + outputs zero after reset.

    No shadow model — only port-level checks derived from the DUT header.
    """
    header = _extract_module_header(dut_sv) or "module TopModule(input clk, input rst_n);"
    ports = _parse_ports(header)
    has_rst_n = any(p["name"] == "rst_n" and p["dir"] == "input" for p in ports)

    lines = [
        "module TopModule_formal;",
        "    (* gclk *) reg clk;",
    ]

    dut_ports: list[str] = []
    output_asserts: list[str] = []

    for p in ports:
        name = p["name"]
        if name == "clk":
            dut_ports.append(".clk(clk)")
            continue
        width = p["width"]
        width_decl = f"[{width}] " if width else ""
        zero = f"{{{width}{{1'b0}}}}" if width else "1'b0"

        if p["dir"] == "input":
            lines.append(f"    (* anyseq *) reg {width_decl}{name};")
            dut_ports.append(f".{name}({name})")
        elif p["dir"] == "output":
            lines.append(f"    wire {width_decl}{name};")
            dut_ports.append(f".{name}({name})")
            if has_rst_n:
                output_asserts.append(f"            assert({name} == {zero});")

    lines.append("")
    lines.append(f"    TopModule dut ({', '.join(dut_ports)});")
    lines.append("")
    lines.append("    always @(posedge clk) begin")
    lines.append("        if ($initstate) begin")
    if has_rst_n:
        lines.append("            assume(!rst_n);")
        lines.append("        end else if (!$past(rst_n)) begin")
        if output_asserts:
            lines.extend(output_asserts)
        else:
            lines.append("            ;")
        lines.append("        end")
    else:
        lines.append("            ;")
        lines.append("        end")
    lines.append("    end")
    lines.append("endmodule")
    lines.append("")

    return "\n".join(lines)


def write_sby_file(
    path: Path,
    *,
    mode: FormalMode = "bmc",
    depth: int = DEFAULT_FORMAL_DEPTH,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        SBY_TEMPLATE.format(mode=mode, depth=depth),
        encoding="utf-8",
    )
    return path


def _build_prompt(
    *,
    prob_id: str,
    spec: str,
    header: str,
    dut_sv: str,
    strict: bool,
) -> str:
    strict_block = ""
    if strict:
        strict_block = """
## STRICT (previous attempt was rejected)
- ZERO internal `reg` state in TopModule_formal except `(* gclk *) reg clk` and `(* anyseq *)` inputs.
- NO reference/shadow/gold/ref/model FSM. NO second always block updating internal state.
- ONLY assert on DUT output wires and `$past()` of inputs/outputs.
- Maximum 60 lines.
"""

    return f"""You are writing a **fast SymbiYosys BMC** wrapper for Verilog `TopModule`.

## Problem
{prob_id}

## Functional spec (from prompt — use THIS, not a duplicated reference design)
{spec.strip()}

## DUT interface (must match exactly)
```verilog
{header}
```

## Port names / widths (for instantiation only)
```verilog
{dut_sv.strip()[:1200]}
```

## REQUIRED style — lightweight port-level asserts ONLY
```verilog
{FORMAL_EXAMPLE}
```

{strict_block}

## Rules (must follow)
1. Module name: **TopModule_formal**.
2. `(* gclk *) reg clk;` — no clock generators.
3. DUT inputs: `(* anyseq *) reg ...` — no other internal regs.
4. Instantiate `TopModule dut (...)` once.
5. One `always @(posedge clk)` block with `$past()` asserts on **DUT ports only**.
6. `$initstate`: assume reset active (e.g. `assume(!rst_n)`).
7. After reset deassert: check spec rules (reset values, handshake, output relations).
8. **2–4 assert properties max** — simple enough for BMC depth 10 in under 2 minutes.
9. **FORBIDDEN**: golden/ref/shadow models, internal FSM copies, `gold_*`/`ref_*` regs,
   duplicate reference always blocks, RefModule instantiation, `$fatal`, UVM.
10. Target **≤ 60 lines**. No refmodel Verilog is provided — derive properties from the spec text.

## Output format
## Rationale
Brief bullets: which port-level properties you chose.

## TopModule_formal
Single ```verilog block with the complete module.
"""


def generate_formal_wrapper_with_cursor(
    *,
    prob_id: str,
    spec_text: str,
    dut_sv: str,
    model: str = "composer-2.5",
    strict: bool = False,
    cursor_session: CursorPromptSession | None = None,
    prompt_artifact_path: Path | None = None,
) -> tuple[str, str, str, str]:
    """
    Ask Cursor to emit a lightweight TopModule_formal.sv from the English spec.

    Returns (formal_sv, rationale, raw_response, transport).
    """
    if "CURSOR_API_KEY" not in os.environ:
        raise RuntimeError("CURSOR_API_KEY is not set in environment.")

    spec = strip_spec_from_prompt(spec_text)
    header = _extract_module_header(dut_sv) or "module TopModule(...);"
    prompt = _build_prompt(
        prob_id=prob_id,
        spec=spec,
        header=header,
        dut_sv=dut_sv,
        strict=strict,
    )

    if cursor_session is not None:
        raw, transport = cursor_session.prompt(
            prompt,
            model=model,
            timeout_s=600,
            prompt_artifact_path=prompt_artifact_path,
        )
    else:
        raw, transport = cursor_prompt(
            prompt,
            model=model,
            api_key=os.environ["CURSOR_API_KEY"],
            workspace=str(REPO_ROOT),
            timeout_s=600,
            prompt_artifact_path=prompt_artifact_path,
        )

    formal_sv = _extract_formal_module(raw)
    if not formal_sv:
        raise RuntimeError("Cursor response did not contain a parsable TopModule_formal module.")

    validation_errors = validate_formal_wrapper(formal_sv)
    if validation_errors:
        raise RuntimeError(
            "Generated formal wrapper failed validation: " + "; ".join(validation_errors)
        )

    rationale = ""
    m = re.search(
        r"##\s*Rationale\s*(.*?)(?:\n##\s*TopModule_formal|\Z)",
        raw,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if m:
        rationale = m.group(1).strip()

    return formal_sv, rationale, raw, transport


def ensure_formal_wrapper(
    *,
    prob_id: str,
    spec_text: str,
    dut_sv: str,
    formal_dir: Path,
    model: str = "composer-2.5",
    mode: FormalMode = "bmc",
    depth: int = DEFAULT_FORMAL_DEPTH,
    force_regenerate: bool = False,
    cursor_session: CursorPromptSession | None = None,
) -> FormalWrapperResult:
    """
    Load cached TopModule_formal.sv or generate a lightweight wrapper, then write .sby.
    """
    formal_dir.mkdir(parents=True, exist_ok=True)
    formal_sv_path = formal_dir / "TopModule_formal.sv"
    sby_path = formal_dir / "TopModule.sby"
    meta_path = formal_dir / "formal_wrapper_meta.json"

    if formal_sv_path.exists() and sby_path.exists() and not force_regenerate:
        formal_sv = formal_sv_path.read_text(encoding="utf-8")
        cache_errors = validate_formal_wrapper(formal_sv)
        if not cache_errors:
            print(f"[{prob_id}] Using cached formal wrapper ({formal_sv_path.name})", flush=True)
            return FormalWrapperResult(
                formal_sv=formal_sv,
                rationale="(loaded from cache)",
                raw_text="",
                transport="cache",
                sby_path=sby_path,
                formal_sv_path=formal_sv_path,
            )
        print(
            f"[{prob_id}] Cached formal wrapper invalid ({'; '.join(cache_errors)}); regenerating...",
            flush=True,
        )

    transport = "template"
    rationale = ""
    raw = ""
    formal_sv: str | None = None

    if "CURSOR_API_KEY" in os.environ:
        for attempt, strict in enumerate((False, True)):
            try:
                print(
                    f"[{prob_id}] Generating lightweight formal wrapper via Cursor"
                    f"{'' if attempt == 0 else ' (strict retry)'}...",
                    flush=True,
                )
                formal_sv, rationale, raw, transport = generate_formal_wrapper_with_cursor(
                    prob_id=prob_id,
                    spec_text=spec_text,
                    dut_sv=dut_sv,
                    model=model,
                    strict=strict,
                    cursor_session=cursor_session,
                    prompt_artifact_path=formal_dir / "formal_wrapper_prompt.md",
                )
                break
            except RuntimeError as exc:
                print(f"[{prob_id}] Formal wrapper generation failed: {exc}", flush=True)
                if attempt == 1:
                    formal_sv = None

    if formal_sv is None:
        print(
            f"[{prob_id}] Using minimal template wrapper (reset + output-zero checks only)...",
            flush=True,
        )
        formal_sv = build_minimal_formal_wrapper(dut_sv)
        rationale = "Deterministic minimal wrapper: reset assume + outputs zero after reset."
        transport = "template"
        errors = validate_formal_wrapper(formal_sv)
        if errors:
            raise RuntimeError(
                "Minimal template wrapper failed validation: " + "; ".join(errors)
            )

    formal_sv_path.write_text(formal_sv, encoding="utf-8")
    write_sby_file(sby_path, mode=mode, depth=depth)

    (formal_dir / "formal_wrapper_generation.txt").write_text(
        f"transport={transport}\n\n## Rationale\n{rationale}\n\n## Raw\n{raw}\n\n## Wrapper\n```verilog\n{formal_sv}\n```\n",
        encoding="utf-8",
    )

    meta_path.write_text(
        json.dumps(
            {
                "prob_id": prob_id,
                "transport": transport,
                "mode": mode,
                "depth": depth,
                "style": "lightweight_port_asserts",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return FormalWrapperResult(
        formal_sv=formal_sv,
        rationale=rationale,
        raw_text=raw,
        transport=transport,
        sby_path=sby_path,
        formal_sv_path=formal_sv_path,
    )
