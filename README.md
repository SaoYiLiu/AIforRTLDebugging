# AI for RTL debugging — LLM-Guided RTL Debug with EDA Tool Feedback

An automated **ReAct** (reason–act–observe) pipeline for **Verilog/SystemVerilog RTL debugging**. A fixer LLM (Cursor) patches RTL using structured evidence from simulation, waveforms, optional formal checks, and benchmark-specific harnesses. Two evaluation tracks are supported:


| Track           | Benchmark                                                | Grading oracle                             |
| --------------- | -------------------------------------------------------- | ------------------------------------------ |
| **ChipBench**   | `third_party/ChipBench/` (one-shot arithmetic debug set) | Local **iverilog** + reference model + VCD |
| **CVDP cid016** | NVIDIA CVDP v1.1.0 JSONL (non-agentic + agentic)         | Official **Docker/cocotb** harness         |


Supporting **MCP tools** (`mcp_server.py`) expose iverilog, VCD parsing, and SymbiYosys to agents; the ReAct runners call the same logic directly in Python.

---

## How to compile, run, and test

### Prerequisites

- **WSL Ubuntu 22.04** (recommended) or Linux with Docker
- System tools: `iverilog`, `vvp`, `yosys`, `symbiyosys` (see [docs/SETUP.md](docs/SETUP.md))
- **Docker** (required for CVDP harness)
- Python 3.10+

Full install (EDA tools + Python venv):

```bash
cd ./AIfordebugging
chmod +x install.sh
./install.sh
source .venv/bin/activate   # after ./install.sh
```

### Environment (Cursor fixer settings)

```bash
export CURSOR_API_KEY=crsr_...
# Optional: bridge (WSL/desktop) vs REST (headless)
export CURSOR_TRANSPORT=auto          # default: try REST API call, fall back to bridge
export CURSOR_CLOUD_REPO_URL="https://github.com/YOU/AIfordebugging"  # if REST
```

### CVDP benchmark setup (one-time)

```bash
# Dataset (already under third_party/cvdp/datasets/ if downloaded)
# Docker image from NVIDIA CVDP benchmark:
cd third_party/cvdp/cvdp_benchmark
docker build -t nvidia/cvdp-sim:v1.0.0 .
# Or set OSS_SIM_IMAGE in third_party/cvdp/cvdp_benchmark/.env
```

### Run — ChipBench (single problem)

- --prob-id: choose a problem from the testbench
- --prompt: problem prompt and buggy RTL code
- --testbench: testbench file
- --ref: golden reference model
- max-iters: maximum number of ReAct Loop iterations before program abortion

```bash
PYTHONPATH=. python -m react.react_runner \
  --prob-id Prob001 \
  --prompt "third_party/ChipBench/Verilog Debugging/dataset_debug_one_shot_arithmetic/Prob001_continuous_input_sequence_detect_prompt.txt" \
  --testbench "third_party/ChipBench/Verilog Debugging/dataset_debug_one_shot_arithmetic/Prob001_continuous_input_sequence_detect_test.sv" \
  --ref "third_party/ChipBench/Verilog Debugging/dataset_debug_one_shot_arithmetic/Prob001_continuous_input_sequence_detect_ref.sv" \
  --use-cursor-sdk \
  --max-iters 3
```

**Batch (Verilog Debugging datasets):**

- --dataset-dir: designate the dataset directory
- --auto-formal: turn on assert generation and formal verification 
- --formal-mode bmc/prove: choose bounded/unbounded proof type

```bash
python run_chipbench_batch.py \
  --dataset-dir "third_party/ChipBench/Verilog Debugging/dataset_debug_one_shot_arithmetic" \
  --use-cursor-sdk \
  --auto-formal \
  --formal-mode bmc \
  --formal-depth 20 \
  --max-iters 5 \
  --output-root outputs
```

Output directory per problem: `outputs/<ProbID>_output/` (`llm_fix_request.md`, `wave.vcd`, `react_trace.md`, …).

### Run — CVDP cid016 (single problem)

- --format: CVDP has to types of testbench: non-agentic and agentic
- --cursor-transport auto/bridge/rest: choose LLM call method; auto uses REST API first before fallback to cursor-sdk bridge.
- --problem-ids: designate problem to solve; omit the flag to run in batch

```bash
PYTHONPATH=. python -m react_cvdp \
  --jsonl third_party/cvdp/datasets/cvdp_v1.1.0_nonagentic_code_generation_no_commercial.jsonl \
  --format nonagentic \
  --use-cursor-sdk \
  --cursor-transport auto \
  --max-iters 5 \
  --problem-ids cvdp_copilot_32_bit_Brent_Kung_PP_adder_0001 \
  --cvdp-env third_party/cvdp/cvdp_benchmark/.env
```

**Agentic subset:**

```bash
PYTHONPATH=. python -m react_cvdp \
  --jsonl third_party/cvdp/datasets/cvdp_v1.1.0_agentic_code_generation_no_commercial.jsonl \
  --format agentic \
  --use-cursor-sdk \
  --max-iters 7 \
  --problem-ids cvdp_agentic_lfsr_0001 \
  --cvdp-env third_party/cvdp/cvdp_benchmark/.env
```

There is no full pytest suite for the ReAct loop; correctness is judged by benchmark harness pass/fail and saved artifacts under `outputs/`.

---

## Key research contributions (this project / this semester)

1. **Unified ReAct RTL debug loop** — Iterative *simulate → parse → enrich evidence → LLM patch → re-simulate*, with explicit structured feedback instead of raw logs alone.
2. **Multi-source evidence fusion for the fixer prompt**
  - Classified errors (`syntax`, `logic`, `compile`, …) with strategy hints
  - **VCD causal tracing** (first mismatch time + signal transitions before failure)
  - **Connection maps** (TB/DUT/ref wiring for waveform interpretation)
  - Optional **SymbiYosys** formal wrapper + counterexample VCD on repeated sim failure (ChipBench)
3. `**cursor_transport`** — Portable Cursor integration: local SDK bridge on WSL/desktop, automatic fallback to Cloud Agents REST on headless hosts.
4. **CVDP cid016 integration (`react_cvdp/`)** — Parallel pipeline that does *not* modify ChipBench code:
  - JSONL load + workspace staging from `input.context` (no golden patch on public HF)
  - Docker Compose cocotb harness as authoritative grade
  - Multi-file RTL patching for agentic problems
  - **Cursor-decided optional iverilog debug TB** (separate call from iter 3+) with local VCD trace fed into the next fix iteration
  - Docker Compose volume merging fix for agentic harness YAML
5. **Benchmark-specific grading hygiene** — e.g. `chipbench_effective_pass()` for tri-state compare artifacts; CVDP cocotb parsers separate from ChipBench iverilog parsers.

---

## Prior work — not counted as this project’s contribution

*Honor-based disclosure. Omitting items here, if later identified, may affect grading.*

### Third-party packages, tools, and frameworks


| Component                                      | Role                                                                       |
| ---------------------------------------------- | -------------------------------------------------------------------------- |
| **Icarus Verilog** (`iverilog`/`vvp`)          | Simulation                                                                 |
| **Yosys / SymbiYosys** (`sby`)                 | Formal verification                                                        |
| **vcdvcd**                                     | VCD parsing                                                                |
| **Cursor** / **cursor-sdk** / Cloud Agents API | LLM fixer                                                                  |
| **MCP** (Model Context Protocol)               | Tool server protocol                                                       |
| **Docker / Docker Compose**                    | CVDP harness execution                                                     |
| **cocotb / pytest**                            | CVDP test execution                                                        |
| **Hugging Face / PyTorch**                     | Optional VeriDebug-HF model ([docs/VERIDEBUG_HF.md](docs/VERIDEBUG_HF.md)) |
| **httpx**                                      | REST transport                                                             |


### Third-party benchmarks and datasets


| Resource                                                  | Location                                |
| --------------------------------------------------------- | --------------------------------------- |
| **ChipBench**                                             | `third_party/ChipBench/`                |
| **NVIDIA CVDP** (v1.1.0 JSONL + `cvdp_benchmark` harness) | `third_party/cvdp/`                     |
| **VeriDebug** paper/model (LLM-EDA/VeriDebug)             | Integrated optionally; not our training |


### Work present before this semester (in this repo or by others)


| Item                                          | Notes                                                                                                       |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `**mcp_server.py`** + counter/UART-FIFO demos | Pre-existing EDA MCP tooling and small RTL examples (`rtl/`, `tb/`, `bugs/uart_fifo/`, `formal/`)           |
| **ReAct / agent paradigm**                    | General LLM pattern; My contribution is the *RTL-specific evidence pipeline*                                |
| **veridebugger-style parsers**                | `react/parsers.py` and `react/vcd_trace.py` note inspiration from veridebugger; extended for ChipBench/CVDP |
| **Cursor IDE / Composer**                     | Commercial fixer                                                                                            |


### What *is* our implementation this semester

- `react/` — ChipBench ReAct runner, parsers, VCD trace, connection map, formal generator/runner, Cursor/VeriDebug fixers, batch runner  
- `react_cvdp/` — CVDP staging, harness runner, cocotb parsers, multi-file fixer, debug-TB path  
- `react/cursor_transport.py` — bridge/REST session handling  
- Integration glue, prompt compaction, artifact layout under `outputs/`

---

## Algorithm

### ReAct loop

![ChipBench Pipeline Flowchart](image/ChipBenchFlowchart.png)



**ChipBench oracle:** `iverilog` compile + `vvp` run; compare DUT vs `ref.sv` via TB; optional formal after repeated failure.

**CVDP oracle:** `docker compose run` cocotb/pytest harness (authoritative PASS/FAIL).

### Pseudocode

```
procedure RUN_REACT(problem, max_iters, use_cursor_sdk):
    workspace ← STAGE(problem)
    buggy_rtl ← workspace.initial_rtl
    debug_evidence ← ∅

    for it in 1 .. max_iters:
        if it > 1 and not use_cursor_sdk:
            break

        if it > 1:
            prompt ← BUILD_FIX_PROMPT(
                spec, buggy_rtl, current_rtl,
                harness_or_sim_log, StructuredFeedback,
                vcd_summary, connection_map, debug_evidence)
            patch ← CURSOR(prompt)                    # bridge or REST
            WRITE_RTL(workspace, patch)

        if CVDP and it ≥ 3 and use_cursor_sdk and last_grade == FAIL:
            decision ← CURSOR_DEBUG_DECISION(...)
            if decision.use:
                tb ← decision.testbench
                sim ← IVERILOG(workspace.rtl, tb)
                debug_evidence ← VCD_CAUSAL_TRACE(sim.wave)

        grade ← RUN_ORACLE(workspace)                 # iverilog or Docker harness
        feedback ← PARSE(grade.stdout, grade.stderr)

        if grade.passed:
            return PASS

    return FAIL
```

### Algorithm description

1. **Staging** — Materialize RTL, testbench/harness, and frozen buggy snapshot. CVDP seeds from JSONL `context` (equivalent to official `--no-patch`); agentic problems copy all `rtl/` files but only `patch` targets are editable by Cursor.
2. **Grading** — Run the benchmark oracle. ChipBench counts mismatches and first mismatch time from TB hints. CVDP runs embedded cocotb tests inside the NVIDIA sim image.
3. **Structured feedback** — Normalize logs into `error_kind`, compile errors, and simulation failures (expected vs actual). Harness failure excerpts are promoted to the top of prompts.
4. **Evidence enrichment (ChipBench)** — On failure: build connection map; run `trace_vcd_failure` on `wave.vcd`; optionally generate/run SymbiYosys wrapper after the second sim failure.
5. **Evidence enrichment (CVDP, iter ≥ 3)** — Separate Cursor call returns `DebugSimDecision: use yes|no`. If yes, Cursor authors a minimal SystemVerilog TB; pipeline runs local iverilog and attaches causal VCD text to the *next* RTL-fix prompt. Docker harness remains the only pass criterion.
6. **Fixing** — Cursor returns `## PatchedFiles` (CVDP multi-file) or `## FixedTopModule` (ChipBench). Prompt size is capped for bridge vs REST limits.
7. **Termination** — Stop on oracle PASS, exhausted `max_iters`, or missing fixer (`--use-cursor-sdk` off after iter 1).

---

## Notable implementation details


| Area               | Detail                                                                                                                             |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Transport**      | `CursorPromptSession` reuses one SDK bridge per batch; poisoned bridge retries once; REST uses linked GitHub repo                  |
| **CVDP compose**   | `_ensure_compose_volumes()` merges `rtl/`, `rundir/`, `verif/` into a single `volumes:` block (fixes agentic `./src:` mount style) |
| **Paths on WSL**   | Avoid `Path.resolve()` on `/mnt/c` in runners; absolute paths without symlink resolution                                           |
| **Hi-Z artifacts** | `chipbench_effective_pass()` treats functional match as PASS when ChipBench XOR compare flags hi-Z on data buses                   |
| **Formal budget**  | Repeat BMC skipped after first completed run or timeout per problem                                                                |
| **Artifacts**      | Per-iter `harness_stdout_iter_N.txt`, `llm_fix_request_iter_N.md`, `cursor_sdk_iter_N.txt`, `react_trace.md`, `result.json`        |


---

## Experimental results

Example summary: ChipBench one shot arithmetic dataset batch run

```
========================================================================
SUMMARY
========================================================================
Problem                                    Status         Time   Mismatches
------------------------------------------------------------------------
Prob001_continuous_input_sequence_detect   PASS       1m 40.8s            0
Prob002_extraneous_items_sequence_detect   PASS       1m 16.3s            0
Prob006_data_serial-to-parallel_circuit    PASS       1m 33.4s            0
Prob007_data_accumulation_output           PASS          45.2s            0
Prob008_non-integer_data_width_conversion_24to128 PASS        1m 8.4s            0        
Prob009_non-integer_data_width_conversion_8to12 PASS       1m 30.5s            0
Prob010_integer_multiple_data_bit_width_conversion_8to16 PASS       1m 41.9s            0 
Prob011_4-bit_carry_look-ahead_adder_circuit PASS        1m 3.2s            0
Prob013_least_common_multiple              FAIL       2m 26.0s          389
Prob014_sequence_generator                 PASS          39.8s            0
Prob016_odd-number_division_with_a_duty_cycle_of_half PASS        1m 4.1s            0    
Prob017_arbitrary_fractional_frequency_division PASS        1m 6.5s            0
Prob019_implement_full_subtractor_using_three_to_eight_decoder PASS          49.7s            0
Prob021_asynchronous_FIFO                  PASS          38.6s            0
Prob022_synchronous_FIFO                   PASS        2m 0.1s            0
Prob023_gray_code_counter                  PASS          52.6s            0
Prob024_multiplication_and_bitwise_operations PASS          36.3s            0
Prob025_pulse_synchronization_circuit      PASS          58.1s            0
Prob028_up_and_down_counter                PASS       1m 36.4s            0
Prob030_simple_implementation_RAM          PASS       1m 17.6s            0
Prob031_johnson_counter                    PASS       1m 12.1s            0
Prob032_pipeline_multiplier                PASS       1m 28.6s            0
Prob033_traffic_lights                     PASS       1m 37.7s            0
Prob034_gaming_machine_billing_program     PASS          49.6s            0
------------------------------------------------------------------------
Passed:       23/24
Failed:       1/24
Errors:       0/24
Success rate: 95.8%
Total time:   29m 53.6s
========================================================================
```

### Observations

- **Non-agentic CVDP cid016:** High pass rate on tried problems with `--use-cursor-sdk` and Docker harness; most fixes in 2–4 iterations.
- **Agentic:** Harder (multi-file RTL, longer prompts); AES and similar crypto blocks remain open.
- **Debug TB path:** Helps on some logic bugs; often declined or fails compile on complex AES (iverilog limitations).
- **REST vs bridge:** Both work; REST used when bridge unavailable; adds latency from polling.

---

## Repository layout

```
AIfordebugging/
├── mcp_server.py           # MCP: iverilog, VCD, sby
├── react/                  # ChipBench ReAct pipeline
├── react_cvdp/             # CVDP cid016 ReAct pipeline
├── run_cvdp_batch.py       # CVDP CLI entry
├── run_chipbench_batch.py  # ChipBench batch CLI entry
├── third_party/
│   ├── ChipBench/          # ChipBench benchmark (external)
│   └── cvdp/               # CVDP dataset + benchmark (external)
├── docs/SETUP.md           # Toolchain install
├── docs/VERIDEBUG_HF.md    # Optional HF fixer
├── scripts/                # Helpers (summarize_results, list_agentic_cid016, …)
├── outputs/                # Run artifacts (gitignored)
├── rtl/, tb/, bugs/        # Small demos (pre-project)
└── requirements.txt
```

---

## References

- NVIDIA CVDP: [cvdp-benchmark](https://github.com/nvidia/cvdp-benchmark) / Hugging Face dataset `cvdp_v1.1.0`
- ChipBench: [https://github.com/zhongkaiyu/ChipBench](https://github.com/zhongkaiyu/ChipBench)
- VeriDebug: [arXiv:2504.19099](https://arxiv.org/abs/2504.19099) (optional `--use-veridebug-hf`)

