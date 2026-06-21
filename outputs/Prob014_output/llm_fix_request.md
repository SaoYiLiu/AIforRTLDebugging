# LLM fix request: Prob014

## Goal
Fix `TopModule` so the DUT matches the reference model under the provided testbench.

## Structured feedback
```text
error_kind: logic

## ChipBench regression
- mismatches: 198 / 405 samples
- first_mismatch_time_ps: 50
- output 'data': 198 mismatches
```

## Connection map
```text
## Connection map (error-focused)
- mismatches: 198 / 405 samples, first_fail_ps=50
- `data` role=dut_output vcd=tb.data_dut
- `data_dut` role=dut_output vcd=tb.data_dut
- `data_ref` role=ref_output vcd=tb.data_ref
- `match` role=compare_ok vcd=tb.tb_match
- `match_dut` role=dut_output vcd=tb.data_dut
- `match_ref` role=ref_output vcd=tb.data_ref
- `tb_match` role=compare_ok vcd=tb.tb_match
- `tb_mismatch` role=compare_fail vcd=tb.tb_mismatch
- compare signals: ['data_ref', 'data_dut', 'tb_match', 'tb_mismatch']
- VCD focus: ['tb.tb_mismatch', 'tb.data_dut', 'tb.data_ref', 'tb.tb_match', 'tb.clk', 'tb.rst_n', 'stim1.clk']
```

## Testbench result (raw)
```text
VCD info: dumpfile wave.vcd opened for output.
Hint: Output 'data' has 198 mismatches. First mismatch occurred at time 50.
Hint: Total mismatched samples is 198 out of 405 samples

Simulation finished at 2026 ps
Mismatches: 198 in 405 samples
```

## Waveform summary (from VCD)
```text
signals (first chunk):
- tb.clk
- tb.data_dut
- tb.data_ref
- tb.rst_n
- tb.stim1.clk
- tb.tb_mismatch

failure_time (ps): 50

causal trace:
- tb.clk @ t=50: 0 (Δ=0 before failure)
- tb.stim1.clk @ t=50: 0 (Δ=0 before failure)
- tb.clk @ t=45: 1 (Δ=5 before failure)
- tb.data_ref @ t=45: 1 (Δ=5 before failure)
- tb.stim1.clk @ t=45: 1 (Δ=5 before failure)
- tb.tb_mismatch @ t=45: 1 (Δ=5 before failure)
- tb.clk @ t=40: 0 (Δ=10 before failure)
- tb.stim1.clk @ t=40: 0 (Δ=10 before failure)
- tb.clk @ t=35: 1 (Δ=15 before failure)
- tb.stim1.clk @ t=35: 1 (Δ=15 before failure)
- tb.clk @ t=30: 0 (Δ=20 before failure)
- tb.stim1.clk @ t=30: 0 (Δ=20 before failure)
- tb.clk @ t=25: 1 (Δ=25 before failure)
- tb.stim1.clk @ t=25: 1 (Δ=25 before failure)
- tb.clk @ t=20: 0 (Δ=30 before failure)
- tb.stim1.clk @ t=20: 0 (Δ=30 before failure)
- tb.clk @ t=15: 1 (Δ=35 before failure)
- tb.rst_n @ t=15: 1 (Δ=35 before failure)
- tb.stim1.clk @ t=15: 1 (Δ=35 before failure)
- tb.clk @ t=10: 0 (Δ=40 before failure)

selected signals:

[tb.tb_mismatch]
0: 0
45: 1
55: 0
65: 1
85: 0
105: 1
115: 0
125: 1
145: 0
165: 1
175: 0
185: 1
205: 0
225: 1
235: 0
245: 1
265: 0
285: 1
295: 0
305: 1
325: 0
345: 1
355: 0
365: 1
385: 0
405: 1
415: 0
425: 1
445: 0
465: 1
475: 0
485: 1
505: 0
525: 1
535: 0
545: 1
565: 0
585: 1
595: 0
605: 1
625: 0
645: 1
655: 0
665: 1
685: 0
705: 1
715: 0
725: 1
745: 0
765: 1
775: 0
785: 1
805: 0
825: 1
835: 0
845: 1
865: 0
885: 1
895: 0
905: 1
925: 0
945: 1
955: 0
965: 1
985: 0
1005: 1
1015: 0
1025: 1
1045: 0
1065: 1
1075: 0
1085: 1
1105: 0
1125: 1
1135: 0
1145: 1
1165: 0
1185: 1
1195: 0
1205: 1
1225: 0
1245: 1
1255: 0
1265: 1
1285: 0
1305: 1
1315: 0
1325: 1
1345: 0
1365: 1
1375: 0
1385: 1
1405: 0
1425: 1
1435: 0
1445: 1
1465: 0
1485: 1
1495: 0
1505: 1
1525: 0
1545: 1
1555: 0
1565: 1
1585: 0
1605: 1
1615: 0
1625: 1
1645: 0
1665: 1
1675: 0
1685: 1
1705: 0
1725: 1
1735: 0
1745: 1
1765: 0
1785: 1
1795: 0
1805: 1
1825: 0
1845: 1
1855: 0
1865: 1
1885: 0
1905: 1
1915: 0
1925: 1
1945: 0
1965: 1
1975: 0
1985: 1
2005: 0
2025: 1

[tb.data_dut]
0: 0

[tb.data_ref]
0: 0
45: 1
55: 0
65: 1
85: 0
105: 1
115: 0
125: 1
145: 0
165: 1
175: 0
185: 1
205: 0
225: 1
235: 0
245: 1
265: 0
285: 1
295: 0
305: 1
325: 0
345: 1
355: 0
365: 1
385: 0
405: 1
415: 0
425: 1
445: 0
465: 1
475: 0
485: 1
505: 0
525: 1
535: 0
545: 1
565: 0
585: 1
595: 0
605: 1
625: 0
645: 1
655: 0
665: 1
685: 0
705: 1
715: 0
725: 1
745: 0
765: 1
775: 0
785: 1
805: 0
825: 1
835: 0
845: 1
865: 0
885: 1
895: 0
905: 1
925: 0
945: 1
955: 0
965: 1
985: 0
1005: 1
1015: 0
1025: 1
1045: 0
1065: 1
1075: 0
1085: 1
1105: 0
1125: 1
1135: 0
1145: 1
1165: 0
1185: 1
1195: 0
1205: 1
1225: 0
1245: 1
1255: 0
1265: 1
1285: 0
1305: 1
1315: 0
1325: 1
1345: 0
1365: 1
1375: 0
1385: 1
1405: 0
1425: 1
1435: 0
1445: 1
1465: 0
1485: 1
1495: 0
1505: 1
1525: 0
1545: 1
1555: 0
1565: 1
1585: 0
1605: 1
1615: 0
1625: 1
1645: 0
1665: 1
1675: 0
1685: 1
1705: 0
1725: 1
1735: 0
1745: 1
1765: 0
1785: 1
1795: 0
1805: 1
1825: 0
1845: 1
1855: 0
1865: 1
1885: 0
1905: 1
1915: 0
1925: 1
1945: 0
1965: 1
1975: 0
1985: 1
2005: 0
2025: 1

[tb.clk]
0: 0
5: 1
10: 0
15: 1
20: 0
25: 1
30: 0
35: 1
40: 0
45: 1
50: 0
55: 1
60: 0
65: 1
70: 0
75: 1
80: 0
85: 1
90: 0
95: 1
100: 0
105: 1
110: 0
115: 1
120: 0
125: 1
130: 0
135: 1
140: 0
145: 1
150: 0
155: 1
160: 0
165: 1
170: 0
175: 1
180: 0
185: 1
190: 0
195: 1
200: 0
205: 1
210: 0
215: 1
220: 0
225: 1
230: 0
235: 1
240: 0
245: 1
250: 0
255: 1
260: 0
265: 1
270: 0
275: 1
280: 0
285: 1
290: 0
295: 1
300: 0
305: 1
310: 0
315: 1
320: 0
325: 1
330: 0
335: 1
340: 0
345: 1
350: 0
355: 1
360: 0
365: 1
370: 0
375: 1
380: 0
385: 1
390: 0
395: 1
400: 0
405: 1
410: 0
415: 1
420: 0
425: 1
430: 0
435: 1
440: 0
445: 1
450: 0
455: 1
460: 0
465: 1
470: 0
475: 1
480: 0
485: 1
490: 0
495: 1
500: 0
505: 1
510: 0
515: 1
520: 0
525: 1
530: 0
535: 1
540: 0
545: 1
550: 0
555: 1
560: 0
565: 1
570: 0
575: 1
580: 0
585: 1
590: 0
595: 1
600: 0
605: 1
610: 0
615: 1
620: 0
625: 1
630: 0
635: 1
640: 0
645: 1
650: 0
655: 1
660: 0
665: 1
670: 0
675: 1
680: 0
685: 1
690: 0
695: 1
700: 0
705: 1
710: 0
715: 1
720: 0
725: 1
730: 0
735: 1
740: 0
745: 1
750: 0
755: 1
760: 0
765: 1
770: 0
775: 1
780: 0
785: 1
790: 0
795: 1
800: 0
805: 1
810: 0
815: 1
820: 0
825: 1
830: 0
835: 1
840: 0
845: 1
850: 0
855: 1
860: 0
865: 1
870: 0
875: 1
880: 0
885: 1
890: 0
895: 1
900: 0
905: 1
910: 0
915: 1
920: 0
925: 1
930: 0
935: 1
940: 0
945: 1
950: 0
955: 1
960: 0
965: 1
970: 0
975: 1
980: 0
985: 1
990: 0
995: 1

[tb.rst_n]
0: 0
15: 1

[tb.stim1.clk]
0: 0
5: 1
10: 0
15: 1
20: 0
25: 1
30: 0
35: 1
40: 0
45: 1
50: 0
55: 1
60: 0
65: 1
70: 0
75: 1
80: 0
85: 1
90: 0
95: 1
100: 0
105: 1
110: 0
115: 1
120: 0
125: 1
130: 0
135: 1
140: 0
145: 1
150: 0
155: 1
160: 0
165: 1
170: 0
175: 1
180: 0
185: 1
190: 0
195: 1
200: 0
205: 1
210: 0
215: 1
220: 0
225: 1
230: 0
235: 1
240: 0
245: 1
250: 0
255: 1
260: 0
265: 1
270: 0
275: 1
280: 0
285: 1
290: 0
295: 1
300: 0
305: 1
310: 0
315: 1
320: 0
325: 1
330: 0
335: 1
340: 0
345: 1
350: 0
355: 1
360: 0
365: 1
370: 0
375: 1
380: 0
385: 1
390: 0
395: 1
400: 0
405: 1
410: 0
415: 1
420: 0
425: 1
430: 0
435: 1
440: 0
445: 1
450: 0
455: 1
460: 0
465: 1
470: 0
475: 1
480: 0
485: 1
490: 0
495: 1
500: 0
505: 1
510: 0
515: 1
520: 0
525: 1
530: 0
535: 1
540: 0
545: 1
550: 0
555: 1
560: 0
565: 1
570: 0
575: 1
580: 0
585: 1
590: 0
595: 1
600: 0
605: 1
610: 0
615: 1
620: 0
625: 1
630: 0
635: 1
640: 0
645: 1
650: 0
655: 1
660: 0
665: 1
670: 0
675: 1
680: 0
685: 1
690: 0
695: 1
700: 0
705: 1
710: 0
715: 1
720: 0
725: 1
730: 0
735: 1
740: 0
745: 1
750: 0
755: 1
760: 0
765: 1
770: 0
775: 1
780: 0
785: 1
790: 0
795: 1
800: 0
805: 1
810: 0
815: 1
820: 0
825: 1
830: 0
835: 1
840: 0
845: 1
850: 0
855: 1
860: 0
865: 1
870: 0
875: 1
880: 0
885: 1
890: 0
895: 1
900: 0
905: 1
910: 0
915: 1
920: 0
925: 1
930: 0
935: 1
940: 0
945: 1
950: 0
955: 1
960: 0
965: 1
970: 0
975: 1
980: 0
985: 1
990: 0
995: 1
```

## Buggy RTL extracted from prompt
```verilog
module TopModule(
    input clk,
    input rst_n,
    output reg data
    );
     
    reg [5:0] q;
     
    always@(posedge clk or negedge rst_n)
        if (!rst_n)
            q <= 6'b001011;
        else
            q <= {q[5], q[4:0]};
     
    always@(posedge clk or negedge rst_n)
        if (!rst_n)
            data <= 1'd0;
        else
            data <= q[5];
endmodule
```

## Current candidate RTL
```verilog
module TopModule(
    input clk,
    input rst_n,
    output reg data
    );
     
    reg [5:0] q;
     
    always@(posedge clk or negedge rst_n)
        if (!rst_n)
            q <= 6'b001011;
        else
            q <= {q[5], q[4:0]};
     
    always@(posedge clk or negedge rst_n)
        if (!rst_n)
            data <= 1'd0;
        else
            data <= q[5];
endmodule
```

## What to do
- Identify the logic bug relative to the spec.
- Output a corrected full `TopModule` implementation.
