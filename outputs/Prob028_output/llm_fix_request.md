# LLM fix request: Prob028

## Goal
Fix `TopModule` so the DUT matches the reference model under the provided testbench.

## Structured feedback
```text
error_kind: logic

## ChipBench regression
- mismatches: 230 / 289 samples
- first_mismatch_time_ps: 120
- output 'number': 230 mismatches
```

## Connection map
```text
## Connection map (error-focused)
- mismatches: 230 / 289 samples, first_fail_ps=120
- `match` role=signal vcd=tb.match
- `match_dut` role=dut_output vcd=tb.match_dut
- `match_ref` role=ref_output vcd=tb.match_ref
- `number` role=signal vcd=tb.number
- `number_dut` role=signal vcd=tb.number_dut
- `number_ref` role=signal vcd=tb.number_ref
- `tb_match` role=compare_ok vcd=tb.tb_match
- `tb_mismatch` role=compare_fail vcd=tb.tb_mismatch
- `zero` role=signal vcd=tb.zero
- `zero_dut` role=signal vcd=tb.zero_dut
- `zero_ref` role=signal vcd=tb.zero_ref
- compare signals: ['match_dut', 'match_ref', 'tb_match', 'tb_mismatch']
- VCD focus: ['tb_mismatch', 'tb.tb_mismatch', 'match_dut', 'match_ref', 'tb.match_dut', 'tb.match_ref', 'tb.number_ref', 'tb.zero_ref', 'tb.number_dut', 'tb.zero_dut']
```

## Testbench result (raw)
```text
VCD info: dumpfile wave.vcd opened for output.
Hint: Output 'number' has 230 mismatches. First mismatch occurred at time 120.
Hint: Output 'zero' has 54 mismatches. First mismatch occurred at time 200.
Hint: Total mismatched samples is 230 out of 289 samples

Simulation finished at 1446 ps
Mismatches: 230 in 289 samples
```

## Waveform summary (from VCD)
```text
signals (first chunk):
- tb.clk
- tb.mode
- tb.number_dut[3:0]
- tb.number_ref[3:0]
- tb.rst_n
- tb.stim1.clk
- tb.tb_mismatch
- tb.zero_dut
- tb.zero_ref

failure_time (ps): 120

causal trace:
- tb.number_dut[3:0] @ t=115: 1111 (Δ=5 before failure)
- tb.number_ref[3:0] @ t=115: 1 (Δ=5 before failure)
- tb.tb_mismatch @ t=115: 1 (Δ=5 before failure)
- tb.zero_dut @ t=115: 1 (Δ=5 before failure)
- tb.zero_ref @ t=115: 1 (Δ=5 before failure)
- tb.number_dut[3:0] @ t=105: 0 (Δ=15 before failure)
- tb.number_ref[3:0] @ t=105: 0 (Δ=15 before failure)
- tb.tb_mismatch @ t=105: 0 (Δ=15 before failure)
- tb.zero_dut @ t=105: 0 (Δ=15 before failure)
- tb.zero_ref @ t=105: 0 (Δ=15 before failure)
- tb.number_dut[3:0] @ t=95: 1001 (Δ=25 before failure)
- tb.number_ref[3:0] @ t=95: 1001 (Δ=25 before failure)
- tb.tb_mismatch @ t=95: 0 (Δ=25 before failure)
- tb.zero_dut @ t=95: 1 (Δ=25 before failure)
- tb.zero_ref @ t=95: 1 (Δ=25 before failure)
- tb.clk @ t=120: 0 (Δ=0 before failure)
- tb.stim1.clk @ t=120: 0 (Δ=0 before failure)
- tb.clk @ t=115: 1 (Δ=5 before failure)
- tb.stim1.clk @ t=115: 1 (Δ=5 before failure)
- tb.clk @ t=110: 0 (Δ=10 before failure)

selected signals:

[tb.tb_mismatch]
0: 0
5: 0
95: 0
105: 0
115: 1
645: 0
655: 1
785: 0
795: 0
805: 1
1075: 0
1085: 0
1095: 0
1105: 0
1115: 0
1125: 0
1135: 0
1145: 0
1155: 0
1165: 0
1175: 0
1185: 0
1195: 1
1365: 0
1375: 0
1385: 0
1395: 1

[tb.number_ref[3:0]]
0: x
5: 0
95: 1001
105: 0
115: 1
125: 10
135: 11
145: 100
155: 101
165: 110
175: 111
185: 1000
195: 1001
205: 0
215: 1
225: 10
235: 11
245: 100
255: 11
265: 10
275: 1
285: 0
295: 1001
305: 1000
315: 111
325: 110
335: 101
345: 100
355: 11
365: 10
375: 1
385: 0
395: 1001
405: 0
415: 1001
425: 0
435: 1001
445: 1000
455: 111
465: 1000
475: 1001
485: 0
495: 1
505: 0
515: 1
525: 10
535: 11
545: 100
555: 11
565: 10
575: 1
585: 0
595: 1
605: 10
615: 1
625: 0
635: 1001
645: 0
655: 1
665: 0
675: 1
685: 10
695: 1
705: 0
715: 1
725: 0
735: 1
745: 0
755: 1001
765: 0
775: 1
785: 10
795: 1
805: 10
815: 1
825: 10
835: 1
845: 10
855: 11
865: 100
875: 101
885: 100
895: 11
905: 100
915: 11
925: 100
935: 101
945: 110
955: 111
965: 1000
975: 111
985: 110
995: 101
1005: 110
1015: 111
1025: 1000
1035: 1001
1045: 1000
1055: 1001
1065: 1000
1075: 1001
1085: 0
1095: 1001
1105: 0
1115: 1001
1125: 0
1135: 1001
1145: 0
1155: 1001
1165: 0
1175: 1001
1185: 1000
1195: 1001
1205: 0
1215: 1001
1225: 1000
1235: 111
1245: 1000
1255: 111
1265: 110
1275: 111
1285: 110
1295: 111
1305: 110
1315: 101
1325: 100
1335: 101
1345: 100
1355: 101
1365: 110
1375: 101
1385: 100
1395: 101
1405: 100
1415: 11
1425: 100
1435: 11
1445: 100

[tb.zero_ref]
0: x
5: 0
95: 1
105: 0
115: 1
125: 0
215: 1
225: 0
295: 1
305: 0
395: 1
405: 0
415: 1
425: 0
435: 1
445: 0
495: 1
505: 0
515: 1
525: 0
595: 1
605: 0
635: 1
645: 0
655: 1
665: 0
675: 1
685: 0
715: 1
725: 0
735: 1
745: 0
755: 1
765: 0
775: 1
785: 0
1095: 1
1105: 0
1115: 1
1125: 0
1135: 1
1145: 0
1155: 1
1165: 0
1175: 1
1185: 0
1215: 1
1225: 0

[tb.number_dut[3:0]]
0: x
5: 0
95: 1001
105: 0
115: 1111
125: 1110
135: 1101
145: 1100
155: 1011
165: 1010
175: 1001
185: 0
195: 1111
205: 1110
215: 1101
225: 1100
235: 1011
245: 1010
255: 1001
265: 1000
275: 111
285: 110
295: 101
305: 100
315: 11
325: 10
335: 1
345: 0
355: 1001
365: 1000
375: 111
385: 110
395: 101
405: 100
415: 11
425: 10
435: 1
445: 0
455: 1001
465: 0
475: 1111
485: 1110
495: 1101
505: 1100
515: 1011
525: 1010
535: 1001
545: 0
555: 1001
565: 1000
575: 111
585: 110
595: 101
605: 100
615: 11
625: 10
635: 1
645: 0
655: 1111
665: 1110
675: 1101
685: 1100
695: 1011
705: 1010
715: 1001
725: 1000
735: 111
745: 110
755: 101
765: 100
775: 11
785: 10
795: 1
805: 0
815: 1001
825: 0
835: 1001
845: 0
855: 1111
865: 1110
875: 1101
885: 1100
895: 1011
905: 1010
915: 1001
925: 0
935: 1111
945: 1110
955: 1101
965: 1100
975: 1011
985: 1010
995: 1001
1005: 0
1015: 1111
1025: 1110
1035: 1101
1045: 1100
1055: 1011
1065: 1010
1075: 1001
1085: 0
1095: 1001
1105: 0
1115: 1001
1125: 0
1135: 1001
1145: 0
1155: 1001
1165: 0
1175: 1001
1185: 1000
1195: 111
1205: 110
1215: 101
1225: 100
1235: 11
1245: 10
1255: 1
1265: 0
1275: 1111
1285: 1110
1295: 1101
1305: 1100
1315: 1011
1325: 1010
1335: 1001
1345: 1000
1355: 111
1365: 110
1375: 101
1385: 100
1395: 11
1405: 10
1415: 1
1425: 0
1435: 1001
1445: 0

[tb.zero_dut]
0: x
5: 0
95: 1
105: 0
115: 1
125: 0
195: 1
205: 0
355: 1
365: 0
455: 1
465: 0
475: 1
485: 0
555: 1
565: 0
655: 1
665: 0
815: 1
825: 0
835: 1
845: 0
855: 1
865: 0
935: 1
945: 0
1015: 1
1025: 0
1095: 1
1105: 0
1115: 1
1125: 0
1135: 1
1145: 0
1155: 1
1165: 0
1175: 1
1185: 0
1275: 1
1285: 0
1435: 1
1445: 0
```

## Buggy RTL extracted from prompt
```verilog
module TopModule(
	input clk,
	input rst_n,
	input mode,
	output reg [3:0]number,
	output reg zero
	);

	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			begin 
				zero <= 1'd0;
			end
		else if (number == 4'd0)
			begin
				zero <= 1'b1;
			end
		else 
			begin	
				zero <= 1'b0;
			end
		
	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			begin 
				number <= 4'b0;
			end
		else if(mode)
			begin
				if(number == 9)
					number <= 0;
				else
					number <= number - 1'd1;
			end
		else if(!mode)
			begin
				if(number == 0)
					number <= 9;
				else
					number <= number - 1'd1;
			end
		else number <= number;
endmodule
```

## Current candidate RTL
```verilog
module TopModule(
	input clk,
	input rst_n,
	input mode,
	output reg [3:0]number,
	output reg zero
	);

	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			begin 
				zero <= 1'd0;
			end
		else if (number == 4'd0)
			begin
				zero <= 1'b1;
			end
		else 
			begin	
				zero <= 1'b0;
			end
		
	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			begin 
				number <= 4'b0;
			end
		else if(mode)
			begin
				if(number == 9)
					number <= 0;
				else
					number <= number - 1'd1;
			end
		else if(!mode)
			begin
				if(number == 0)
					number <= 9;
				else
					number <= number - 1'd1;
			end
		else number <= number;
endmodule
```

## What to do
- Identify the logic bug relative to the spec.
- Output a corrected full `TopModule` implementation.
