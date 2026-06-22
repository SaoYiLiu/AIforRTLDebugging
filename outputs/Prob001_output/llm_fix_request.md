# LLM fix request: Prob001

## Goal
Fix `TopModule` so the DUT matches the reference model under the provided testbench.

## Structured feedback
```text
error_kind: logic

## ChipBench regression
- mismatches: 2 / 455 samples
- first_mismatch_time_ps: 200
- output 'match': 2 mismatches
```

## Connection map
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

## Testbench result (raw)
```text
VCD info: dumpfile wave.vcd opened for output.
Hint: Output 'match' has 2 mismatches. First mismatch occurred at time 200.
Hint: Total mismatched samples is 2 out of 455 samples

Simulation finished at 2276 ps
Mismatches: 2 in 455 samples
```

## Waveform summary (from VCD)
```text
signals (first chunk):
- tb.a
- tb.match_dut
- tb.match_ref
- tb.rst_n
- tb.tb_mismatch

failure_time (ps): 200

causal trace:
- tb.a @ t=195: 1 (Δ=5 before failure)
- tb.match_ref @ t=195: 1 (Δ=5 before failure)
- tb.tb_mismatch @ t=195: 1 (Δ=5 before failure)
- tb.a @ t=185: 0 (Δ=15 before failure)
- tb.a @ t=175: 1 (Δ=25 before failure)
- tb.a @ t=145: 0 (Δ=55 before failure)
- tb.a @ t=115: 1 (Δ=85 before failure)

selected signals:

[tb.tb_mismatch]
0: 0
5: 0
195: 1
205: 0

[tb.match_dut]
0: x
5: 0

[tb.match_ref]
0: x
5: 0
195: 1
205: 0

[tb.rst_n]
0: x
5: 0
15: 1
1185: 0
1195: 1

[tb.a]
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

## Current candidate RTL
```verilog
module TopModule(
    input clk,
    input rst_n,
    input a,
    output match
);

    reg [7:0] a_tem;

    always @(posedge clk or negedge rst_n)
        if (!rst_n)
            a_tem <= 8'b0;
        else
            a_tem <= {a, a_tem[6:0]};

    assign match = rst_n && ({a, a_tem[6:0]} == 8'b0111_0001);

endmodule
```

## What to do
- Identify the logic bug relative to the spec.
- Output a corrected full `TopModule` implementation.
