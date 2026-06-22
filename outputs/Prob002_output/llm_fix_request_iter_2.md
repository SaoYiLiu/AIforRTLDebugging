Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging a Verilog RTL module called TopModule.

## Problem
Prob002

## Error type
logic

## Fix strategy
The design compiles but fails simulation against the reference model. Use structured mismatch data and the causal waveform trace to find where DUT diverges from ref. Make minimal targeted logic fixes; preserve correct behavior elsewhere.



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
L002: 	input clk,
L003: 	input rst_n,
L004: 	input a,
L005: 	output match
L006: 	);
L007: 
L008: 	reg [8:0] a_tem;
L009: 	reg match_f;
L010: 	reg match_b;
L011: 	
L012: 	always @(posedge clk or negedge rst_n)
L013: 		if (!rst_n)
L014: 			begin 
L015: 				match_f <= 1'b0;
L016: 			end
L017: 		else if (a_tem[8:6] == 3'b011)
L018: 			begin
L019: 				match_f <= 1'b1;
L020: 			end
L021: 		else 
L022: 			begin	
L023: 				match_f <= 1'b0;
L024: 			end
L025: 
L026: 	always @(posedge clk or negedge rst_n)
L027: 		if (!rst_n)
L028: 			begin 
L029: 				match_b <= 1'b0;
L030: 			end
L031: 		else if (a_tem[2:0] == 3'b110)
L032: 			begin
L033: 				match_b <= 1'b1;
L034: 			end
L035: 		else 
L036: 			begin	
L037: 				match_b <= 1'b0;
L038: 			end
L039: 			
L040: 	always @(posedge clk or negedge rst_n)
L041: 		if (!rst_n)
L042: 			begin 
L043: 				a_tem <= 9'b0;
L044: 			end
L045: 		else 
L046: 			begin
L047: 				a_tem <= {a, a_tem[7:0]};
L048: 			end
L049: 			
L050: 	assign match = match_b && match_f;
L051: endmodule
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
