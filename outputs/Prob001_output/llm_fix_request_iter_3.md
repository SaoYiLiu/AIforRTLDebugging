Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging a Verilog RTL module called TopModule.

## Problem
Prob001

## Error type
logic

## Fix strategy
The design compiles but fails simulation against the reference model. Use structured mismatch data and the causal waveform trace to find where DUT diverges from ref. Make minimal targeted logic fixes; preserve correct behavior elsewhere.

## Previous iteration rationale (prioritize this)
- **Suspected bug (L010–L032):** `match` and `a_tem` are updated in **separate** `always` blocks. In the `match` block at **L015**, the comparison uses the **current** (pre-shift) value of `a_tem`, while `a_tem` is shifted in the other block at **L031** on the same clock edge.
- **Evidence:** The first mismatch is at **200 ps**, right when the 8th bit (`a=1` at 195 ps) should complete pattern `8'b0111_0001`. `match_ref` asserts at **195–205 ps**, but `match_dut` stays **0** — the DUT is one cycle late.
- **Two mismatches explained:** At **~200 ps**, ref=1 and dut=0 (late assert). On the next posedge, dut would assert `match` based on the now-complete `a_tem` while ref has already de-asserted — a second mismatch sample.
- **Waveform causal trace:** The failure aligns with the final `a` transition at 195 ps completing the target pattern; the DUT never reflects that in the same cycle as the reference.
- **Fix:** Merge into one `always` block and compare **`match` against the next shift-register value** `{a, a_tem[6:0]}`, so `match` updates in the same cycle as the shift that completes (or breaks) the pattern.

## Spec (from prompt file)
I would like you to implement a module named `TopModule` with the following interface. All input and output ports are one bit unless otherwise specified.

- **Input ports**:
  - `clk`
  - `rst_n`
  - `a`

- **Output ports**:
  - `match`

The module should implement an 8-bit shift register that shifts in the input `a` on every positive edge of the clock. The shift register is named `a_tem` and retains the 8 most recent bits of `a`. The module should perform the following functionality:

1. **Reset Behavior**:
   - When `rst_n` is de-asserted (logic 0), the shift register `a_tem` should be cleared to `8'b0`, and the output `match` should be set to `0`.

2. **Shift Register Behavior**:
   - On every positive edge of the clock, if `rst_n` is asserted (logic 1), the input `a` should be shifted into the least significant bit (LSB) of the shift register `a_tem`, and the previous bits should shift left by one position.

3. **Matching Logic**:
   - The output `match` should be asserted (logic 1) whenever the value of the shift register `a_tem` matches the specific 8-bit pattern `8'b0111_0001`.
   - If the shift register does not match this pattern, the output `match` should remain de-asserted (logic 0).

The design must operate synchronously with the clock and use a negative edge active reset (`rst_n`). Ensure the module correctly implements this functionality.

## Current candidate RTL (line-numbered — fix this module)
```verilog
L001: module TopModule(
L002:     input clk,
L003:     input rst_n,
L004:     input a,
L005:     output reg match
L006: );
L007: 
L008:     reg [7:0] a_tem;
L009: 
L010:     always @(posedge clk or negedge rst_n)
L011:         if (!rst_n) begin
L012:             a_tem <= 8'b0;
L013:             match <= 1'b0;
L014:         end else begin
L015:             a_tem <= {a, a_tem[6:0]};
L016:             match <= ({a, a_tem[6:0]} == 8'b0111_0001);
L017:         end
L018: 
L019: endmodule
```

## Structured tool feedback
```text
error_kind: logic

## ChipBench regression
- mismatches: 2 / 455 samples
- first_mismatch_time_ps: 200
- output 'match': 2 mismatches
```

## Connection map (testbench wiring — use for waveform interpretation)
```text
## Connection map (error-focused)
- mismatches: 2 / 455 samples, first_fail_ps=200
- `a` role=signal vcd=tb.a
- `clk` role=clock vcd=tb.clk
- `match` role=signal vcd=tb.match
- `match_dut` role=dut_output vcd=tb.match_dut
- `match_ref` role=ref_output vcd=tb.match_ref
- `rst_n` role=reset vcd=tb.rst_n
- `stim1.clk` role=signal vcd=tb.stim1.clk
- `tb_match` role=compare_ok vcd=tb.tb_match
- `tb_mismatch` role=compare_fail vcd=tb.tb_mismatch
- compare signals: ['match_dut', 'match_ref', 'tb_match', 'tb_mismatch']
- VCD focus: ['tb_mismatch', 'tb.tb_mismatch', 'match_dut', 'match_ref', 'tb.match_dut', 'tb.match_ref', 'stim1.clk', 'tb.clk', 'tb.rst_n', 'tb.a']
```

## Raw simulation output
```text
VCD info: dumpfile wave.vcd opened for output.
Hint: Output 'match' has 2 mismatches. First mismatch occurred at time 200.
Hint: Total mismatched samples is 2 out of 455 samples

Simulation finished at 2276 ps
Mismatches: 2 in 455 samples
```

## Waveform evidence
```text
failure_time (ps): 200

## Causal trace (transitions before failure)
- tb.a @ t=195: 1 (Δ=5 ps before failure)
- tb.match_ref @ t=195: 1 (Δ=5 ps before failure)
- tb.tb_mismatch @ t=195: 1 (Δ=5 ps before failure)
- tb.a @ t=185: 0 (Δ=15 ps before failure)
- tb.a @ t=175: 1 (Δ=25 ps before failure)
- tb.a @ t=145: 0 (Δ=55 ps before failure)
- tb.a @ t=115: 1 (Δ=85 ps before failure)

## Available signals (partial)
- tb.a
- tb.match_dut
- tb.match_ref
- tb.rst_n
- tb.tb_mismatch

## Waveform: tb.tb_mismatch
0: 0
5: 0
195: 1
205: 0

## Waveform: tb.match_dut
0: x
5: 0

## Waveform: tb.match_ref
0: x
5: 0
195: 1
205: 0

## Waveform: tb.rst_n
0: x
5: 0
15: 1
1185: 0
1195: 1

## Waveform: tb.a
0: x
5: 0
35: 1
55: 0
65: 1
75: 0
115: 1
145: 0
175: 1
185: 0
195: 1
255: 0
265: 1
285: 0
295: 1
315: 0
325: 1
335: 0
345: 1
355: 0
365: 1
385: 0
395: 1
405: 0
435: 1
445: 0
455: 1
495: 0
535: 1
545: 0
555: 1
605: 0
625: 1
655: 0
705: 1
715: 0
735: 1
755: 0
805: 1
855: 0
875: 1
905: 0
925: 1
945: 0
955: 1
975: 0
985: 1
1015: 0
1025: 1
1045: 0
1085: 1
1105: 0
1125: 1
1175: 0
1205: 1
```

## Formal verification evidence (SymbiYosys)
```text
(formal not run or passed)
```

## Task
- Output in TWO sections:

## Rationale
3-8 bullet points describing:
- the suspected bug (cite line numbers from the numbered RTL)
- evidence from structured feedback and waveform causal trace
- what change you made

## FixedTopModule
A FULL corrected `TopModule` implementation (verilog). Put it in a single fenced ```verilog block.
