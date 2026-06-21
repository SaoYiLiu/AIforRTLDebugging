# react_cvdp

CVDP cid016 ReAct loop (Docker harness + optional Cursor SDK). ChipBench code under `react/` is unchanged.

## Run (from repo root)

```bash
cd /mnt/c/Users/user/Desktop/AIfordebugging
source .venv/bin/activate

# Recommended entry points (avoid import/path issues on WSL):
python -m react_cvdp \
  --jsonl third_party/cvdp/datasets/cvdp_v1.1.0_nonagentic_code_generation_no_commercial.jsonl \
  --use-cursor-sdk \
  --max-iters 5 \
  --problem-ids cvdp_copilot_32_bit_Brent_Kung_PP_adder_0001 \
  --cvdp-env third_party/cvdp/cvdp_benchmark/.env

# Or:
python run_cvdp_batch.py --jsonl ... --use-cursor-sdk ...
```

## Agentic cid016 (11 problems)

Use the **agentic** JSONL and `--format agentic`:

```bash
export CURSOR_API_KEY="..."

# Single problem (good first smoke test)
python -m react_cvdp \
  --jsonl third_party/cvdp/datasets/cvdp_v1.1.0_agentic_code_generation_no_commercial.jsonl \
  --format agentic \
  --use-cursor-sdk \
  --cursor-transport auto \
  --max-iters 7 \
  --problem-ids cvdp_agentic_lfsr_0001 \
  --cvdp-env third_party/cvdp/cvdp_benchmark/.env

# All agentic cid016
python -m react_cvdp \
  --jsonl third_party/cvdp/datasets/cvdp_v1.1.0_agentic_code_generation_no_commercial.jsonl \
  --format agentic \
  --use-cursor-sdk \
  --max-iters 7 \
  --cvdp-env third_party/cvdp/cvdp_benchmark/.env
```

List ids: `python scripts/list_agentic_cid016.py`

| vs nonagentic | Agentic |
|---------------|---------|
| JSONL file | `*_agentic_*` |
| Record shape | top-level `context` + `patch` (not `input`/`output`) |
| Patch scope | Often multi-file (`patch` keys only are editable) |
| Extra context | Many include `verif/*.sv` — try `--iverilog-precheck` |
| Harness | All 11 cid016 in your v1.1.0 file include embedded harness |

**Suggested starter problems:** `cvdp_agentic_lfsr_0001`, `cvdp_agentic_caesar_cipher_0001`, `cvdp_agentic_barrel_shifter_0001` (single RTL + verif).  
**Harder:** `cvdp_agentic_AES_encryption_decryption_0005`, `cvdp_agentic_monte_carlo_0006` (multi-file patch).

## Cursor SDK

```bash
export CURSOR_API_KEY="..."
export CURSOR_TRANSPORT=bridge   # or rest + CURSOR_CLOUD_REPO_URL
```

## Modules

| File | Role |
|------|------|
| `cvdp_dataset.py` | Load JSONL → `CvdpProblemSpec` |
| `cvdp_staging.py` | Stage harness under `outputs/<problem_id>/` |
| `cvdp_harness_runner.py` | Docker cocotb runner |
| `cvdp_parsers.py` | Parse pytest/cocotb output |
| `cvdp_cursor_fixer.py` | Cursor multi-file RTL patcher |
| `cvdp_debug_tb.py` | Separate Cursor call to author iverilog debug TB (iter 3+) |
| `cvdp_iverilog_runner.py` | Run generated TB + RTL via iverilog/vvp, collect VCD |
| `cvdp_react_runner.py` | Main ReAct loop |
| `cvdp_batch_runner.py` | Batch CLI |

## iverilog debug testbench (iter 3+, Cursor decides)

When `--use-cursor-sdk` is on (default), after a harness **FAIL** from iteration 3 onward:

1. **Separate Cursor call** — Cursor outputs `## DebugSimDecision` (`use: yes|no`) based on whether local iverilog/VCD would help (compile/elab failures → usually no; internal logic bugs → yes).
2. If **yes**: writes `debug_tb_iter_N.sv`, pipeline runs **iverilog + vvp**, dumps `wave_iter_N.vcd`, attaches causal trace to the next RTL-fix prompt.
3. If **no**: writes `debug_tb_skipped_iter_N.txt`; next fix prompt notes the skip rationale.

Docker cocotb harness remains the authoritative PASS/FAIL grade.

Disable the offer entirely with `--no-debug-tb`. Change when the offer starts with `--debug-tb-min-iter 3` (default).
