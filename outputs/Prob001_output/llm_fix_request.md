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
- tb.clk
- tb.match_dut
- tb.match_ref
- tb.rst_n
- tb.stim1.clk
- tb.tb_mismatch

failure_time (ps): 200

causal trace:
- tb.clk @ t=200: 0 (Δ=0 before failure)
- tb.stim1.clk @ t=200: 0 (Δ=0 before failure)
- tb.a @ t=195: 1 (Δ=5 before failure)
- tb.clk @ t=195: 1 (Δ=5 before failure)
- tb.match_ref @ t=195: 1 (Δ=5 before failure)
- tb.stim1.clk @ t=195: 1 (Δ=5 before failure)
- tb.tb_mismatch @ t=195: 1 (Δ=5 before failure)
- tb.clk @ t=190: 0 (Δ=10 before failure)
- tb.stim1.clk @ t=190: 0 (Δ=10 before failure)
- tb.a @ t=185: 0 (Δ=15 before failure)
- tb.clk @ t=185: 1 (Δ=15 before failure)
- tb.stim1.clk @ t=185: 1 (Δ=15 before failure)
- tb.clk @ t=180: 0 (Δ=20 before failure)
- tb.stim1.clk @ t=180: 0 (Δ=20 before failure)
- tb.a @ t=175: 1 (Δ=25 before failure)
- tb.clk @ t=175: 1 (Δ=25 before failure)
- tb.stim1.clk @ t=175: 1 (Δ=25 before failure)
- tb.clk @ t=170: 0 (Δ=30 before failure)
- tb.stim1.clk @ t=170: 0 (Δ=30 before failure)
- tb.clk @ t=165: 1 (Δ=35 before failure)

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

## Buggy RTL extracted from prompt
```verilog
module TopModule(
	input clk,
	input rst_n,
	input a,
	output reg match
	);

	reg [7:0] a_tem;
	
	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			begin 
				match <= 1'b0;
			end
		else if (a_tem == 8'b0111_0001)
			begin
				match <= 1'b1;
			end
		else 
			begin	
				match <= 1'b0;
			end
		
	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			begin 
				a_tem <= 8'b0;
			end
		else 
			begin
				a_tem <= {a, a_tem[6:0]};
			end
endmodule
```

## Current candidate RTL
```verilog
module TopModule(
	input clk,
	input rst_n,
	input a,
	output reg match
	);

	reg [7:0] a_tem;
	
	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			begin 
				match <= 1'b0;
			end
		else if (a_tem == 8'b0111_0001)
			begin
				match <= 1'b1;
			end
		else 
			begin	
				match <= 1'b0;
			end
		
	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			begin 
				a_tem <= 8'b0;
			end
		else 
			begin
				a_tem <= {a, a_tem[6:0]};
			end
endmodule
```

## What to do
- Identify the logic bug relative to the spec.
- Output a corrected full `TopModule` implementation.
