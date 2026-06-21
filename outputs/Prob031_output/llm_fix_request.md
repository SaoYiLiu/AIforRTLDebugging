# LLM fix request: Prob031

## Goal
Fix `TopModule` so the DUT matches the reference model under the provided testbench.

## Structured feedback
```text
error_kind: logic

## ChipBench regression
- mismatches: 352 / 421 samples
- first_mismatch_time_ps: 100
- output 'Q': 352 mismatches
```

## Connection map
```text
## Connection map (error-focused)
- mismatches: 352 / 421 samples, first_fail_ps=100
- `Q` role=signal vcd=tb.Q
- `Q_dut` role=signal vcd=tb.Q_dut
- `Q_ref` role=signal vcd=tb.Q_ref
- `match` role=signal vcd=tb.match
- `match_dut` role=dut_output vcd=tb.match_dut
- `match_ref` role=ref_output vcd=tb.match_ref
- `tb_match` role=compare_ok vcd=tb.tb_match
- `tb_mismatch` role=compare_fail vcd=tb.tb_mismatch
- compare signals: ['match_dut', 'match_ref', 'tb_match', 'tb_mismatch']
- VCD focus: ['tb_mismatch', 'tb.tb_mismatch', 'match_dut', 'match_ref', 'tb.match_dut', 'tb.match_ref', 'tb.Q_ref', 'tb.Q_dut']
```

## Testbench result (raw)
```text
VCD info: dumpfile wave.vcd opened for output.
Hint: Output 'Q' has 352 mismatches. First mismatch occurred at time 100.
Hint: Total mismatched samples is 352 out of 421 samples

Simulation finished at 2106 ps
Mismatches: 352 in 421 samples
```

## Waveform summary (from VCD)
```text
signals (first chunk):
- tb.Q_dut[3:0]
- tb.Q_ref[3:0]
- tb.clk
- tb.rst_n
- tb.stim1.clk
- tb.tb_mismatch

failure_time (ps): 100

causal trace:
- tb.Q_ref[3:0] @ t=95: 1000 (Δ=5 before failure)
- tb.tb_mismatch @ t=95: 1 (Δ=5 before failure)
- tb.Q_dut[3:0] @ t=5: 0 (Δ=95 before failure)
- tb.Q_ref[3:0] @ t=5: 0 (Δ=95 before failure)
- tb.tb_mismatch @ t=5: 0 (Δ=95 before failure)
- tb.Q_dut[3:0] @ t=0: x (Δ=100 before failure)
- tb.Q_ref[3:0] @ t=0: x (Δ=100 before failure)
- tb.tb_mismatch @ t=0: 0 (Δ=100 before failure)
- tb.clk @ t=100: 0 (Δ=0 before failure)
- tb.stim1.clk @ t=100: 0 (Δ=0 before failure)
- tb.clk @ t=95: 1 (Δ=5 before failure)
- tb.rst_n @ t=95: 1 (Δ=5 before failure)
- tb.stim1.clk @ t=95: 1 (Δ=5 before failure)
- tb.clk @ t=90: 0 (Δ=10 before failure)
- tb.stim1.clk @ t=90: 0 (Δ=10 before failure)
- tb.clk @ t=85: 1 (Δ=15 before failure)
- tb.stim1.clk @ t=85: 1 (Δ=15 before failure)
- tb.clk @ t=80: 0 (Δ=20 before failure)
- tb.stim1.clk @ t=80: 0 (Δ=20 before failure)
- tb.clk @ t=75: 1 (Δ=25 before failure)

selected signals:

[tb.tb_mismatch]
0: 0
5: 0
95: 1
165: 0
175: 1
245: 0
255: 1
325: 0
335: 1
405: 0
415: 1
485: 0
495: 1
565: 0
575: 1
645: 0
655: 1
725: 0
735: 1
805: 0
815: 1
885: 0
895: 1
965: 0
975: 1
1045: 0
1055: 1
1125: 0
1135: 1
1205: 0
1215: 1
1285: 0
1295: 1
1365: 0
1375: 1
1445: 0
1455: 1
1525: 0
1535: 1
1605: 0
1615: 1
1685: 0
1695: 1
1765: 0
1775: 1
1845: 0
1855: 1
1925: 0
1935: 1
2005: 0
2015: 1
2085: 0
2095: 1

[tb.Q_ref[3:0]]
0: x
5: 0
95: 1000
105: 1100
115: 1110
125: 1111
135: 111
145: 11
155: 1
165: 0
175: 1000
185: 1100
195: 1110
205: 1111
215: 111
225: 11
235: 1
245: 0
255: 1000
265: 1100
275: 1110
285: 1111
295: 111
305: 11
315: 1
325: 0
335: 1000
345: 1100
355: 1110
365: 1111
375: 111
385: 11
395: 1
405: 0
415: 1000
425: 1100
435: 1110
445: 1111
455: 111
465: 11
475: 1
485: 0
495: 1000
505: 1100
515: 1110
525: 1111
535: 111
545: 11
555: 1
565: 0
575: 1000
585: 1100
595: 1110
605: 1111
615: 111
625: 11
635: 1
645: 0
655: 1000
665: 1100
675: 1110
685: 1111
695: 111
705: 11
715: 1
725: 0
735: 1000
745: 1100
755: 1110
765: 1111
775: 111
785: 11
795: 1
805: 0
815: 1000
825: 1100
835: 1110
845: 1111
855: 111
865: 11
875: 1
885: 0
895: 1000
905: 1100
915: 1110
925: 1111
935: 111
945: 11
955: 1
965: 0
975: 1000
985: 1100
995: 1110
1005: 1111
1015: 111
1025: 11
1035: 1
1045: 0
1055: 1000
1065: 1100
1075: 1110
1085: 1111
1095: 111
1105: 11
1115: 1
1125: 0
1135: 1000
1145: 1100
1155: 1110
1165: 1111
1175: 111
1185: 11
1195: 1
1205: 0
1215: 1000
1225: 1100
1235: 1110
1245: 1111
1255: 111
1265: 11
1275: 1
1285: 0
1295: 1000
1305: 1100
1315: 1110
1325: 1111
1335: 111
1345: 11
1355: 1
1365: 0
1375: 1000
1385: 1100
1395: 1110
1405: 1111
1415: 111
1425: 11
1435: 1
1445: 0
1455: 1000
1465: 1100
1475: 1110
1485: 1111
1495: 111
1505: 11
1515: 1
1525: 0
1535: 1000
1545: 1100
1555: 1110
1565: 1111
1575: 111
1585: 11
1595: 1
1605: 0
1615: 1000
1625: 1100
1635: 1110
1645: 1111
1655: 111
1665: 11
1675: 1
1685: 0
1695: 1000
1705: 1100
1715: 1110
1725: 1111
1735: 111
1745: 11
1755: 1
1765: 0
1775: 1000
1785: 1100
1795: 1110
1805: 1111
1815: 111
1825: 11
1835: 1
1845: 0
1855: 1000
1865: 1100
1875: 1110
1885: 1111
1895: 111
1905: 11
1915: 1
1925: 0
1935: 1000
1945: 1100
1955: 1110
1965: 1111
1975: 111
1985: 11
1995: 1
2005: 0
2015: 1000
2025: 1100
2035: 1110
2045: 1111
2055: 111
2065: 11

[tb.Q_dut[3:0]]
0: x
5: 0
```

## Buggy RTL extracted from prompt
```verilog
module TopModule(
   input                clk ,
   input                rst_n,
 
   output reg [3:0]     Q  
);
    always@(posedge clk or negedge rst_n)begin
        if(!rst_n) Q <= 'd0;
        else Q <= {Q[0], Q[3 : 1]};
    end
endmodule
```

## Current candidate RTL
```verilog
module TopModule(
   input                clk ,
   input                rst_n,
 
   output reg [3:0]     Q  
);
    always@(posedge clk or negedge rst_n)begin
        if(!rst_n) Q <= 'd0;
        else Q <= {Q[0], Q[3 : 1]};
    end
endmodule
```

## What to do
- Identify the logic bug relative to the spec.
- Output a corrected full `TopModule` implementation.
