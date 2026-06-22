Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging a Verilog RTL module called TopModule.

## Problem
Prob002

## Error type
logic

## Fix strategy
The design compiles but fails simulation against the reference model. Use structured mismatch data and the causal waveform trace to find where DUT diverges from ref. Make minimal targeted logic fixes; preserve correct behavior elsewhere.

## Previous iteration rationale (prioritize this)
- **Suspected bug (L017–L050):** `match_f` and `match_b` are evaluated against the **pre-shift** value of `a_tem`, while the shift update `a_tem <= {a, a_tem[7:0]}` (L047) happens in the same clock cycle. The newest input bit is not included in the window used for detection.
- **Wrong structure:** Splitting detection into two separate flags (L009–L038) and combining them with `assign match = match_b && match_f` (L050) still checks the old register contents, not the 9-bit window **after** the incoming bit is shifted in.
- **Waveform evidence:** `match_ref` pulses high at 105, 145, 195, and 415 ps, but `match_dut` stays **0 for the entire simulation**. All 8 mismatches are ref=1, dut=0 — the DUT never detects the pattern.
- **Causal trace at first failure (110 ps):** The last input change before failure is `tb.a @ 95: 0`, consistent with the final bit of `110` arriving at the clock edge near 105 ps. The reference model detects the completed `011XXX110` window; the DUT evaluates one cycle too early (before that bit enters `a_tem[8]`).
- **Fix:** Remove `match_f`/`match_b`. Form the next shift-register value `{a, a_tem[7:0]}`, update `a_tem` from it, and register `match` from the **post-shift** window: `(a_shift[8:6] == 3'b011) && (a_shift[2:0] == 3'b110)`.

## Spec (from prompt file)
I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  rst_n
 - input  a
 - output match

The module should implement a sequence detection circuit that detects the
pattern "011XXX110" in the input data stream. The pattern consists of 9 bits
where the first 3 bits are "011", the last 3 bits are "110", and the middle
3 bits can be any value (don't care).

The sequence detection should work as follows:
- Monitor the input data stream continuously
- Detect when the pattern "011XXX110" appears in the input
- Output match signal should be high when the pattern is detected
- Output match signal should be low at all other times

Implementation approach:
The module should use a 9-bit shift register to store the last 9 input bits.
The match signal should be asserted when:
- The first 3 bits (bits 8:6) equal "011" AND
- The last 3 bits (bits 2:0) equal "110"
- The middle 3 bits (bits 5:3) can be any value

### Timing and Behavior:
- When rst_n is low, the module should reset to its initial state
- On every positive clock edge (clk), the module should shift in the new input bit
- The output match is updated sequentially
- The detection is continuous - the module checks for the pattern on every clock cycle

## Current candidate RTL (line-numbered — fix this module)
```verilog
L001: module TopModule(
L002:     input clk,
L003:     input rst_n,
L004:     input a,
L005:     output reg match
L006: );
L007: 
L008:     reg [8:0] a_tem;
L009:     wire [8:0] a_shift = {a, a_tem[7:0]};
L010: 
L011:     always @(posedge clk or negedge rst_n)
L012:         if (!rst_n) begin
L013:             a_tem <= 9'b0;
L014:             match <= 1'b0;
L015:         end else begin
L016:             a_tem <= a_shift;
L017:             match <= (a_shift[8:6] == 3'b011) && (a_shift[2:0] == 3'b110);
L018:         end
L019: 
L020: endmodule
```

## Structured tool feedback
```text
error_kind: logic

## ChipBench regression
- mismatches: 8 / 237 samples
- first_mismatch_time_ps: 110
- output 'match': 8 mismatches
```

## Connection map (testbench wiring — use for waveform interpretation)
```text
## Connection map (error-focused)
- mismatches: 8 / 237 samples, first_fail_ps=110
- `match` role=signal vcd=tb.match
- `match_dut` role=dut_output vcd=tb.match_dut
- `match_ref` role=ref_output vcd=tb.match_ref
- `tb_match` role=compare_ok vcd=tb.tb_match
- `tb_mismatch` role=compare_fail vcd=tb.tb_mismatch
- compare signals: ['match_dut', 'match_ref', 'tb_match', 'tb_mismatch']
- VCD focus: ['tb_mismatch', 'tb.tb_mismatch', 'match_dut', 'match_ref', 'tb.match_dut', 'tb.match_ref']
```

## Raw simulation output
```text
VCD info: dumpfile wave.vcd opened for output.
Hint: Output 'match' has 8 mismatches. First mismatch occurred at time 110.
Hint: Total mismatched samples is 8 out of 237 samples

Simulation finished at 1186 ps
Mismatches: 8 in 237 samples
```

## Waveform evidence
```text
failure_time (ps): 110

## Causal trace (transitions before failure)
- tb.match_ref @ t=105: 1 (Δ=5 ps before failure)
- tb.tb_mismatch @ t=105: 1 (Δ=5 ps before failure)
- tb.a @ t=95: 0 (Δ=15 ps before failure)
- tb.a @ t=65: 1 (Δ=45 ps before failure)
- tb.a @ t=55: 0 (Δ=55 ps before failure)
- tb.a @ t=25: 1 (Δ=85 ps before failure)

## Available signals (partial)
- tb.a
- tb.match_dut
- tb.match_ref
- tb.rst_n
- tb.tb_mismatch

## Waveform: tb.tb_mismatch
0: 0
105: 1
115: 0
145: 1
155: 0
195: 1
205: 0
415: 1
425: 0

## Waveform: tb.match_dut
0: 0

## Waveform: tb.match_ref
0: 0
105: 1
115: 0
145: 1
155: 0
195: 1
205: 0
415: 1
425: 0
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
