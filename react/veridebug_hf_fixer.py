"""
Hugging Face LLM-EDA/VeriDebug integration (arXiv:2504.19099).

Two-phase pipeline from the paper:
  1. Contrastive embedding — rank suspicious lines and bug types via cosine similarity
  2. Guided correction — generate a single-line JSON fix conditioned on rankings

Requires GPU + PyTorch (see requirements-veridebug-hf.txt).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

# Reuse FixResult shape from cursor_sdk_fixer for drop-in use in react_runner.
from react.cursor_sdk_fixer import FixResult  # noqa: E402

DEFAULT_MODEL_ID = os.environ.get("VERIDEBUG_HF_MODEL", "LLM-EDA/VeriDebug")

KEY_WORDS = ["endmodule", "end", "endcase", "else", "begin"]
REP_QUERY = "Represent this text: "
LINE_QUERY = (
    "Now you are a verilog designer. You are given the design description and "
    "buggy verilog code segment. Infer the bug type in the code segment."
)
TYPE_QUERY = LINE_QUERY
CLS_DESC = "The bug type is "
GEN_INST = "Now you are a verilog designer. You need to fix the bug in the buggy code segment:\n"
JSON_FORMAT = (
    '{"buggy_code": "The buggy code in the systemverilog (just one line of code)", '
    '"correct_code": "The correct code (just one line of code that can directly replace '
    'the buggy code, without any other description)"}'
)

BUG_CLS: dict[str, int] = {
    "width": 0,
    "logic": 0,
    "assignment": 0,
    "initial": 0,
    "data": 0,
    "state": 0,
    "others": 0,
    "comparison": 0,
    "bitwise": 0,
    "condition": 0,
    "signal": 0,
    "arithmetic": 0,
    "value": 0,
}

BUG_DESC: dict[str, str] = {
    "width": "Mismatched bit widths in assignments, operations, or port connections.",
    "logic": "Errors in combinational or sequential logic design.",
    "assignment": "Improper blocking (=) or non-blocking (<=) assignments.",
    "initial": "Incorrect initialization of variables or registers.",
    "data": "Errors in data handling or signed/unsigned misuse.",
    "state": "Flaws in finite state machine design or transitions.",
    "others": "Miscellaneous errors including syntax issues.",
    "comparison": "Incorrect equality or case equality operators.",
    "bitwise": "Errors in bitwise or shift operations.",
    "condition": "Flaws in if-else or case statements.",
    "signal": "Errors in wire/reg declarations or port naming.",
    "arithmetic": "Mistakes in arithmetic operations or overflow.",
    "value": "Incorrect constants or parameter definitions.",
}

_model_singleton: Any = None
_model_id_loaded: str | None = None


@dataclass
class RetrievalResult:
    """Output of the contrastive embedding (representation) phase."""

    ranked_lines: list[str] = field(default_factory=list)
    ranked_type_labels: list[str] = field(default_factory=list)
    top_line: str | None = None
    top_type: str | None = None


@dataclass
class GuidedFix:
    buggy_line: str
    correct_line: str
    raw_generation: str
    retrieval: RetrievalResult


def gritlm_instruction(instruction: str) -> str:
    return "<|user|>\n" + instruction + "\n<|embed|>\n" if instruction else "<|embed|>\n"


def extract_candidate_lines(verilog_code: str) -> tuple[list[str], list[str]]:
    """
    Split RTL into lines and filter to embeddable candidates (from HF example gen_neg).
    Returns (all_nonempty_lines, filtered_candidates).
    """
    lines = [ln.strip() for ln in verilog_code.splitlines()]
    lines = [ln.strip("\t").strip("\r") for ln in lines]
    lines = [ln for ln in lines if ln]

    candidates = [
        ln
        for ln in lines
        if not ln.startswith("//")
        and not ln.startswith("*")
        and not ln.startswith("/*")
        and ln not in KEY_WORDS
    ]
    candidates = [ln for ln in candidates if " " in ln and len(ln.replace(" ", "")) > 4]
    return lines, candidates


def extract_bug_type_label(text: str) -> str | None:
    m = re.search(r"The bug type is (\w+)", text)
    return m.group(1) if m else None


def _cosine_rank(query_emb: Any, doc_embs: list[Any]) -> list[int]:
    import numpy as np
    from scipy.spatial.distance import cosine

    sims = [1.0 - cosine(query_emb, d) for d in doc_embs]
    return list(np.argsort(sims)[::-1])


_llama_grit_registered = False


def _register_llama_grit_architecture() -> None:
    """Register VeriDebug's custom llama_grit types with transformers."""
    global _llama_grit_registered
    if _llama_grit_registered:
        return
    try:
        from react.modeling_llama_gritlm import (  # type: ignore
            LlamaForCausalLMGrit,
            LlamaGritConfig,
            LlamaGritModel,
        )
    except ImportError as e:
        raise RuntimeError(
            "VeriDebug requires react/modeling_llama_gritlm.py (not bundled in the HF weights).\n"
            "Run once from the repo root:\n"
            "  bash scripts/fetch_veridebug_modeling.sh\n"
            "Or see docs/VERIDEBUG_HF.md"
        ) from e

    from transformers import AutoConfig, AutoModel, AutoModelForCausalLM

    AutoConfig.register("llama_grit", LlamaGritConfig, exist_ok=True)
    AutoModel.register(LlamaGritConfig, LlamaGritModel, exist_ok=True)
    AutoModelForCausalLM.register(LlamaGritConfig, LlamaForCausalLMGrit, exist_ok=True)
    _llama_grit_registered = True


def _gpu_vram_gib() -> float:
    import torch

    return float(torch.cuda.get_device_properties(0).total_memory) / (1024**3)


def _quant_bits() -> int | None:
    """Return 4, 8, or None (full precision) for weight loading."""
    bits_env = os.environ.get("VERIDEBUG_HF_BITS", "").strip()
    if bits_env in ("4", "8"):
        return int(bits_env)
    load_8 = os.environ.get("VERIDEBUG_HF_LOAD_IN_8BIT", "").lower()
    if load_8 in ("1", "true", "yes"):
        return 8
    if load_8 in ("0", "false", "no"):
        return None
    load_4 = os.environ.get("VERIDEBUG_HF_LOAD_IN_4BIT", "").lower()
    if load_4 in ("1", "true", "yes"):
        return 4
    if load_4 in ("0", "false", "no"):
        return None
    # 1080 Ti (11GB): 8-bit still OOMs during load; 4-bit fits on GPU.
    if _gpu_vram_gib() <= 12.0:
        return 4
    return None


def _bitsandbytes_config(torch: Any, *, bits: int) -> Any:
    from transformers import BitsAndBytesConfig

    if bits == 4:
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
    return BitsAndBytesConfig(
        load_in_8bit=True,
        llm_int8_threshold=6.0,
    )


def _build_veridebug_model_kwargs() -> dict[str, Any]:
    import torch

    vram_gib = _gpu_vram_gib()
    bits = _quant_bits()
    kwargs: dict[str, Any] = {
        "mode": "unified",
        "low_cpu_mem_usage": True,
    }

    if bits is not None:
        try:
            import bitsandbytes  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                f"VeriDebug on a {vram_gib:.1f}GB GPU requires bitsandbytes ({bits}-bit).\n"
                "  pip install 'bitsandbytes==0.43.1'"
            ) from e
        kwargs["quantization_config"] = _bitsandbytes_config(torch, bits=bits)
        # Pin to GPU 0 — CPU offload hits zeus ulimit -v (~15GB process cap).
        device_map = os.environ.get("VERIDEBUG_HF_DEVICE_MAP", "").strip()
        kwargs["device_map"] = device_map if device_map else {"": 0}
        print(
            f"[VeriDebug-HF] {bits}-bit load (GPU {vram_gib:.1f}GB, device_map={kwargs['device_map']})",
            flush=True,
        )
    else:
        device_map = os.environ.get("VERIDEBUG_HF_DEVICE_MAP", "auto")
        kwargs["device_map"] = device_map
        dtype_name = os.environ.get("VERIDEBUG_HF_TORCH_DTYPE", "float16")
        kwargs["torch_dtype"] = getattr(torch, dtype_name, torch.float16)
        kwargs["max_memory"] = {
            0: f"{max(1, int(vram_gib * 0.9))}GiB",
            "cpu": os.environ.get("VERIDEBUG_HF_CPU_RAM", "32GiB"),
        }

    return kwargs


def get_veridebug_model(model_id: str = DEFAULT_MODEL_ID, *, force_reload: bool = False) -> Any:
    """Lazy-load GritLM unified model (embedding + generation)."""
    global _model_singleton, _model_id_loaded

    if _model_singleton is not None and not force_reload and _model_id_loaded == model_id:
        return _model_singleton

    try:
        import torch

        torch.cuda.empty_cache()
    except ImportError as e:
        raise RuntimeError(
            "PyTorch failed to import (broken CUDA/NCCL install).\n"
            "Reinstall a matching wheel, e.g.:\n"
            "  pip uninstall -y torch torchvision torchaudio\n"
            "  pip install 'numpy<2' 'torch==2.2.2' "
            "--index-url https://download.pytorch.org/whl/cu121 --force-reinstall\n"
            f"Original error: {e}"
        ) from e

    try:
        from gritlm import GritLM  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "gritlm is not installed. Install optional deps:\n"
            "  pip install -r requirements-veridebug-hf.txt"
        ) from e

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available — VeriDebug (~13GB) will not fit in CPU RAM.\n"
            "On zeus with driver 535 / CUDA 12.2, reinstall PyTorch cu121:\n"
            "  pip install 'numpy<2' 'torch==2.2.2' "
            "--index-url https://download.pytorch.org/whl/cu121 --force-reinstall\n"
            "Then verify:\n"
            "  python -c \"import torch; print(torch.cuda.is_available())\""
        )

    kwargs = _build_veridebug_model_kwargs()
    device_map = kwargs.get("device_map", "auto")

    _register_llama_grit_architecture()
    print(
        f"[VeriDebug-HF] Loading {model_id} "
        f"(device_map={device_map}, cuda={torch.cuda.get_device_name(0)})...",
        flush=True,
    )
    try:
        _model_singleton = GritLM(model_id, **kwargs)
    except OSError as exc:
        if "mmap" in str(exc).lower() or "allocate memory" in str(exc).lower():
            raise RuntimeError(
                "Failed to mmap VeriDebug weight shards into RAM.\n"
                "zeus ulimit -v is ~15GB per process (cannot be raised) — use 4-bit GPU-only load:\n"
                "  unset VERIDEBUG_HF_LOAD_IN_8BIT\n"
                "  export VERIDEBUG_HF_BITS=4\n"
                "  export VERIDEBUG_HF_DEVICE_MAP=''\n"
                "Ask admin to raise ulimit -v if mmap still fails."
            ) from exc
        raise
    except RuntimeError as exc:
        if "out of memory" in str(exc).lower():
            raise RuntimeError(
                "CUDA OOM while loading VeriDebug.\n"
                "On 1080 Ti use 4-bit (not 8-bit), all layers on GPU 0:\n"
                "  export VERIDEBUG_HF_BITS=4\n"
                "  unset VERIDEBUG_HF_LOAD_IN_8BIT VERIDEBUG_HF_DEVICE_MAP\n"
                f"Original: {exc}"
            ) from exc
        raise
    _model_id_loaded = model_id
    print(f"[VeriDebug-HF] Model ready on {_model_singleton.device}", flush=True)
    return _model_singleton


def rank_buggy_lines(model: Any, spec: str, buggy_code: str, *, top_k: int = 10) -> list[str]:
    """Contrastive embedding: rank RTL lines by similarity to spec+buggy query."""
    _all_lines, candidates = extract_candidate_lines(buggy_code)
    if not candidates:
        return []

    query = [LINE_QUERY + "\n" + spec + "\n" + buggy_code]
    q_rep = model.encode(
        query,
        instruction=gritlm_instruction("Represent this text:"),
        max_length=4096,
    )
    d_rep = model.encode(
        candidates,
        instruction=gritlm_instruction(""),
        max_length=128,
    )
    import numpy as np

    order = _cosine_rank(np.asarray(q_rep[0]), [np.asarray(d) for d in d_rep])
    ranked = [candidates[i] for i in order[:top_k]]
    return ranked


def rank_bug_types(model: Any, spec: str, buggy_code: str, *, top_k: int = 5) -> list[str]:
    """Contrastive embedding: rank bug-type descriptions."""
    type_docs = [CLS_DESC + name + "." + BUG_DESC[name] for name in BUG_CLS]
    query = [TYPE_QUERY + "\n" + spec + "\n" + buggy_code]

    q_rep = model.encode(
        query,
        instruction=gritlm_instruction(REP_QUERY),
        max_length=4096,
    )
    d_rep = model.encode(
        type_docs,
        instruction=gritlm_instruction(""),
        max_length=128,
    )
    import numpy as np

    order = _cosine_rank(np.asarray(q_rep[0]), [np.asarray(d) for d in d_rep])
    ranked_docs = [type_docs[i] for i in order[:top_k]]
    return ranked_docs


def run_retrieval(
    model: Any,
    spec: str,
    buggy_code: str,
    *,
    top_lines: int = 10,
    top_types: int = 5,
) -> RetrievalResult:
    ranked_lines = rank_buggy_lines(model, spec, buggy_code, top_k=top_lines)
    ranked_types = rank_bug_types(model, spec, buggy_code, top_k=top_types)
    top_type = extract_bug_type_label(ranked_types[0]) if ranked_types else None
    return RetrievalResult(
        ranked_lines=ranked_lines,
        ranked_type_labels=ranked_types,
        top_line=ranked_lines[0] if ranked_lines else None,
        top_type=top_type,
    )


def _parse_generation_json(decoded: str) -> dict[str, str]:
    text = decoded.strip()
    if "}" in text:
        text = text[: text.find("}") + 1]
    data = json.loads(text)
    buggy = str(data.get("buggy_code", "")).strip()
    correct = str(data.get("correct_code", "")).strip()
    if not buggy or not correct:
        raise ValueError(f"Missing buggy_code/correct_code in: {data}")
    return {"buggy_code": buggy, "correct_code": correct}


def guided_correction(
    model: Any,
    spec: str,
    buggy_code: str,
    retrieval: RetrievalResult,
    *,
    sim_context: str = "",
    max_new_tokens: int = 256,
) -> GuidedFix:
    """Generation phase: JSON single-line fix guided by retrieval rankings."""
    extra = ""
    if sim_context.strip():
        extra = f"\n\nSimulation feedback from testbench:\n{sim_context.strip()}\n"

    instruct = (
        f"{GEN_INST}{buggy_code}\n\n"
        f"The specification file of this code is:\n{spec}\n"
        f"{extra}\n"
        f"The possible buggy lines ranking list are:\n{retrieval.ranked_lines}\n\n"
        f"The possible bug type ranking list are:\n{retrieval.ranked_type_labels}\n\n"
        f"Your task is to return me a json to analyze how the code should be modified, "
        f"in the following format:\n{JSON_FORMAT}."
    )

    messages = [{"role": "user", "content": instruct}]
    encoded = model.tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt"
    )
    encoded = encoded.to(model.device)

    gen = model.generate(encoded, max_new_tokens=max_new_tokens, do_sample=True)
    valid_gen = gen[:, encoded.shape[1] :]
    decoded_list = model.tokenizer.batch_decode(valid_gen)
    raw = decoded_list[0] if decoded_list else ""

    parsed = _parse_generation_json(raw)
    return GuidedFix(
        buggy_line=parsed["buggy_code"],
        correct_line=parsed["correct_code"],
        raw_generation=raw,
        retrieval=retrieval,
    )


def apply_line_fix(full_rtl: str, buggy_line: str, correct_line: str) -> tuple[str, bool]:
    """
    Replace one line in full RTL. Tries exact match, then normalized whitespace match.
    Returns (updated_rtl, applied).
    """
    if buggy_line == correct_line:
        return full_rtl, False

    if buggy_line in full_rtl:
        return full_rtl.replace(buggy_line, correct_line, 1), True

    def norm(s: str) -> str:
        return " ".join(s.split())

    buggy_n = norm(buggy_line)
    out_lines: list[str] = []
    applied = False
    for ln in full_rtl.splitlines():
        if not applied and norm(ln) == buggy_n:
            out_lines.append(correct_line)
            applied = True
        else:
            out_lines.append(ln)

    if applied:
        return "\n".join(out_lines) + ("\n" if full_rtl.endswith("\n") else ""), True

    # Last resort: replace first line that contains the buggy line as substring
    for i, ln in enumerate(out_lines):
        if buggy_n in norm(ln):
            out_lines[i] = correct_line
            return "\n".join(out_lines) + ("\n" if full_rtl.endswith("\n") else ""), True

    return full_rtl, False


def _format_sim_context(
    sim_stdout: str,
    sim_stderr: str,
    structured_feedback: Any | None,
) -> str:
    parts: list[str] = []
    if structured_feedback is not None:
        from react.parsers import StructuredFeedback, format_structured_feedback

        if isinstance(structured_feedback, StructuredFeedback):
            parts.append(format_structured_feedback(structured_feedback))
        elif isinstance(structured_feedback, dict):
            parts.append(json.dumps(structured_feedback, indent=2))
    if sim_stdout.strip():
        parts.append(sim_stdout.strip())
    if sim_stderr.strip():
        parts.append("[stderr]\n" + sim_stderr.strip())
    return "\n".join(parts)


def fix_with_veridebug_hf(
    *,
    prob_id: str,
    spec_text: str,
    current_sv: str,
    sim_stdout: str = "",
    sim_stderr: str = "",
    structured_feedback: Any | None = None,
    model_id: str = DEFAULT_MODEL_ID,
    top_lines: int = 10,
    top_types: int = 5,
) -> FixResult:
    """
    Run full VeriDebug HF pipeline and apply a single-line fix to current_sv (TopModule).

    Drop-in alternative to fix_with_cursor_sdk for react_runner iteration 2+.
    """
    model = get_veridebug_model(model_id)
    sim_context = _format_sim_context(sim_stdout, sim_stderr, structured_feedback)

    retrieval = run_retrieval(
        model,
        spec_text,
        current_sv,
        top_lines=top_lines,
        top_types=top_types,
    )

    guided = guided_correction(
        model,
        spec_text,
        current_sv,
        retrieval,
        sim_context=sim_context,
    )

    fixed_sv, applied = apply_line_fix(current_sv, guided.buggy_line, guided.correct_line)

    rationale = (
        f"- Contrastive embedding top line: `{retrieval.top_line}`\n"
        f"- Contrastive embedding top type: `{retrieval.top_type}`\n"
        f"- Guided correction buggy_line: `{guided.buggy_line}`\n"
        f"- Guided correction correct_line: `{guided.correct_line}`\n"
        f"- Line fix applied to TopModule: {applied}\n"
        f"- Ranked lines (top 5): {retrieval.ranked_lines[:5]}\n"
        f"- Ranked types (top 3): {[extract_bug_type_label(t) for t in retrieval.ranked_type_labels[:3]]}"
    )

    if not applied:
        rationale += (
            "\n- WARNING: could not match buggy_line in RTL; returning unchanged module. "
            "Consider --use-cursor-sdk for full-module rewrites."
        )

    return FixResult(
        fixed_sv=fixed_sv,
        rationale=rationale,
        raw_text=guided.raw_generation,
    )
