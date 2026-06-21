# LLM fix request: Prob007

## Goal
Fix `TopModule` so the DUT matches the reference model under the provided testbench.

## Structured feedback
```text
error_kind: logic

## ChipBench regression
- mismatches: 306 / 357 samples
- first_mismatch_time_ps: 130
- output 'ready_a': 40 mismatches
```

## Connection map
```text
## Connection map (error-focused)
- mismatches: 306 / 357 samples, first_fail_ps=130
- `data_out` role=signal vcd=tb.data_out
- `data_out_dut` role=dut_output vcd=tb.data_out_dut
- `data_out_ref` role=ref_output vcd=tb.data_out_ref
- `match` role=signal vcd=tb.match
- `match_dut` role=signal vcd=tb.match_dut
- `match_ref` role=signal vcd=tb.match_ref
- `ready_a` role=signal vcd=tb.ready_a
- `ready_a_dut` role=dut_output vcd=tb.ready_a_dut
- `ready_a_ref` role=ref_output vcd=tb.ready_a_ref
- `tb_match` role=compare_ok vcd=tb.tb_match
- `tb_mismatch` role=compare_fail vcd=tb.tb_mismatch
- `valid_b` role=signal vcd=tb.valid_b
- `valid_b_dut` role=dut_output vcd=tb.valid_b_dut
- `valid_b_ref` role=ref_output vcd=tb.valid_b_ref
- compare signals: ['ready_a_ref', 'ready_a_dut', 'valid_b_ref', 'valid_b_dut', 'data_out_ref', 'data_out_dut', 'tb_match', 'tb_mismatch']
- VCD focus: ['tb.tb_mismatch', 'tb.ready_a_dut', 'tb.ready_a_ref', 'tb.valid_b_dut', 'tb.valid_b_ref', 'tb.data_out_dut', 'tb.data_out_ref', 'tb.clk', 'tb.rst_n', 'tb.data_in', 'tb.valid_a', 'tb.ready_b']
```

## Testbench result (raw)
```text
VCD info: dumpfile wave.vcd opened for output.
Hint: Output 'ready_a' has 40 mismatches. First mismatch occurred at time 130.
Hint: Output 'valid_b' has 90 mismatches. First mismatch occurred at time 130.
Hint: Output 'data_out' has 294 mismatches. First mismatch occurred at time 140.
Hint: Total mismatched samples is 306 out of 357 samples

Simulation finished at 1786 ps
Mismatches: 306 in 357 samples
```

## Waveform summary (from VCD)
```text
signals (first chunk):
- tb.clk
- tb.data_in[7:0]
- tb.data_out_dut[9:0]
- tb.data_out_ref[9:0]
- tb.ready_a_dut
- tb.ready_a_ref
- tb.ready_b
- tb.rst_n
- tb.stim1.clk
- tb.tb_mismatch
- tb.valid_a
- tb.valid_b_dut
- tb.valid_b_ref

failure_time (ps): 130

causal trace:
- tb.clk @ t=130: 0 (Δ=0 before failure)
- tb.clk @ t=125: 1 (Δ=5 before failure)
- tb.data_in[7:0] @ t=125: 11 (Δ=5 before failure)
- tb.data_out_dut[9:0] @ t=125: 110 (Δ=5 before failure)
- tb.data_out_ref[9:0] @ t=125: 110 (Δ=5 before failure)
- tb.ready_a_dut @ t=125: 0 (Δ=5 before failure)
- tb.tb_mismatch @ t=125: 1 (Δ=5 before failure)
- tb.valid_b_dut @ t=125: 1 (Δ=5 before failure)
- tb.clk @ t=120: 0 (Δ=10 before failure)
- tb.clk @ t=115: 1 (Δ=15 before failure)
- tb.data_in[7:0] @ t=115: 10 (Δ=15 before failure)
- tb.data_out_dut[9:0] @ t=115: 11 (Δ=15 before failure)
- tb.data_out_ref[9:0] @ t=115: 11 (Δ=15 before failure)
- tb.tb_mismatch @ t=115: 0 (Δ=15 before failure)
- tb.clk @ t=110: 0 (Δ=20 before failure)
- tb.clk @ t=105: 1 (Δ=25 before failure)
- tb.data_in[7:0] @ t=105: 1 (Δ=25 before failure)
- tb.data_out_dut[9:0] @ t=105: 1 (Δ=25 before failure)
- tb.data_out_ref[9:0] @ t=105: 1 (Δ=25 before failure)
- tb.tb_mismatch @ t=105: 0 (Δ=25 before failure)

selected signals:

[tb.tb_mismatch]
0: 0
5: 0
105: 0
115: 0
125: 1
255: 0
265: 0
275: 0
285: 0
295: 0
305: 0
315: 0
325: 1
335: 0
345: 1
355: 0
405: 1

[tb.ready_a_dut]
0: x
5: 1
125: 0
175: 1
325: 0
330: 1
410: 0
425: 1
460: 0
475: 1
480: 0
490: 1
510: 0
525: 1
595: 0
610: 1
810: 0
815: 1
820: 0
835: 1
1545: 0
1550: 1
1750: 0
1755: 1
1760: 0
1775: 1

[tb.ready_a_ref]
0: x
5: 1
135: 0
175: 1
235: 0
245: 1
345: 0
350: 1
500: 0
505: 1
510: 0
525: 1
795: 0
800: 1
935: 0
940: 1
1130: 0
1135: 1
1205: 0
1215: 1
1300: 0
1315: 1
1320: 0
1325: 1
1530: 0
1540: 1
1575: 0
1580: 1
1685: 0
1700: 1
1765: 0
1775: 1

[tb.valid_b_dut]
0: x
5: 0
125: 1
175: 0
245: 1
255: 0
285: 1
295: 0
325: 1
335: 0
405: 1
435: 0
455: 1
495: 0
505: 1
535: 0
595: 1
615: 0
725: 1
735: 0
765: 1
775: 0
805: 1
845: 0
865: 1
875: 0
905: 1
915: 0
1105: 1
1115: 0
1145: 1
1155: 0
1425: 1
1435: 0
1545: 1
1555: 0
1665: 1
1675: 0
1745: 1
1785: 0

[tb.valid_b_ref]
0: x
5: 0
135: 1
175: 0
235: 1
245: 0
285: 1
295: 0
345: 1
355: 0
445: 1
455: 0
495: 1
535: 0
625: 1
635: 0
725: 1
735: 0
795: 1
805: 0
865: 1
875: 0
935: 1
945: 0
1035: 1
1045: 0
1125: 1
1145: 0
1205: 1
1225: 0
1295: 1
1335: 0
1425: 1
1435: 0
1525: 1
1545: 0
1575: 1
1585: 0
1685: 1
1705: 0
1765: 1
1785: 0

[tb.data_out_dut[9:0]]
0: x
5: 0
105: 1
115: 11
125: 110
185: 1101
195: 10101
225: 10110
235: 11000
245: 100010
255: 10100
265: 110010
275: 1011010
285: 10000010
305: 10000011
315: 101111100
325: 110001110
345: 1000001110
405: 1010001100
435: 1100100010
445: 1100110100
455: 1110111001
495: 10010011
505: 101100011
545: 111011001
575: 111110101
595: 1010101110
625: 1100110100
635: 1111111001
675: 10101111
705: 110101010
725: 111010010
745: 1010101010
765: 1101001011
775: 11111
795: 11001100
805: 100010101
855: 100101100
865: 110111001
895: 1000000100
905: 1000000111
925: 1010001011
935: 1100001111
955: 1101001100
975: 1101011101
1005: 1101111001
1035: 110100
1055: 1111110
1085: 101000000
1105: 1000101110
1125: 1100011110
1135: 0
1145: 1001010
1155: 10110111
1175: 11111000
1205: 111000000
1235: 111000010
1245: 1001010010
1275: 1011101
1295: 10100010
1315: 100010001
1325: 111101101
1375: 1010011000
1405: 1101010100
1415: 1111011101
1425: 1011111
1455: 101000111
1475: 10111
1495: 10011100
1525: 100110100
1535: 110011111
1545: 111011111
1555: 11101101
1565: 110011000
1575: 1001100110
1655: 1100001010
1665: 1110001100
1675: 11111000
1685: 110110100
1725: 1000001101
1735: 1000110001
1745: 1100100010

[tb.data_out_ref[9:0]]
0: x
5: 0
105: 1
115: 11
125: 110
135: 1010
185: 111
195: 1111
225: 10000
235: 10010
255: 10100
265: 110010
275: 1011010
285: 10000010
305: 10000011
315: 101111100
325: 110001110
345: 1000001110
405: 1010001100
425: 1011100111
435: 1101111101
445: 1110001111
455: 10000101
465: 11011101
485: 111010100
495: 1010101110
545: 1110110
575: 10010010
595: 101001011
625: 111010001
635: 11000101
675: 101111011
705: 1001110110
725: 1010011110
745: 11011000
765: 101111001
775: 110011000
795: 1001000101
805: 1001001
815: 101000011
855: 101011010
865: 111100111
895: 1001011
905: 1001110
925: 11010010
935: 101010110
955: 110010011
975: 110100100
1005: 111000000
1035: 1001111011
1055: 1001010
1085: 100001100
1105: 111111010
1125: 1011101010
1145: 1001010
1155: 100000001
1175: 101000010
1205: 1000001010
1235: 1000001100
1245: 1010011100
1275: 1011111001
1295: 1100111110
1375: 10101011
1405: 101100111
1415: 111110000
1425: 1001110010
1455: 1101011010
1475: 1101110001
1495: 1111110110
1525: 10001110
1545: 1000000
1555: 100101101
1565: 111011000
1575: 1010100110
1655: 1101001010
1665: 1111001100
1675: 11000100
1685: 110000000
1725: 111011001
1735: 111111101
1745: 1011101110
1765: 1110001110

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
```

## Buggy RTL extracted from prompt
```verilog
module TopModule(
	input 				clk 		,   
	input 				rst_n		,
	input		[7:0]	data_in		,
	input				valid_a		,
	input	 			ready_b		,
 
 	output		 		ready_a		,
 	output	reg			valid_b		,
	output  reg [9:0] 	data_out
);
reg 	[1:0]		data_cnt;

assign ready_a = !valid_b | ready_b;

always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		data_cnt <= 'd0;
	else if(valid_a || ready_a)
		data_cnt <= (data_cnt == 2'd3) ? 'd0 : (data_cnt + 1'd1);
end
always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		valid_b <= 'd0;
	else if(data_cnt == 2'd3 && valid_a && ready_a)
		valid_b <= 1'd1;
	else if(valid_b && ready_b)
		valid_b <= 1'd0;
end

always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		data_out <= 'd0;
	else if(ready_b && valid_a && ready_a && (data_cnt == 2'd0))
		data_out <= data_in;
	else if(valid_a && ready_a)
		data_out <= data_out + data_in;
	
end


endmodule
```

## Current candidate RTL
```verilog
module TopModule(
	input 				clk 		,   
	input 				rst_n		,
	input		[7:0]	data_in		,
	input				valid_a		,
	input	 			ready_b		,
 
 	output		 		ready_a		,
 	output	reg			valid_b		,
	output  reg [9:0] 	data_out
);
reg 	[1:0]		data_cnt;

assign ready_a = !valid_b | ready_b;

always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		data_cnt <= 'd0;
	else if(valid_a || ready_a)
		data_cnt <= (data_cnt == 2'd3) ? 'd0 : (data_cnt + 1'd1);
end
always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		valid_b <= 'd0;
	else if(data_cnt == 2'd3 && valid_a && ready_a)
		valid_b <= 1'd1;
	else if(valid_b && ready_b)
		valid_b <= 1'd0;
end

always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		data_out <= 'd0;
	else if(ready_b && valid_a && ready_a && (data_cnt == 2'd0))
		data_out <= data_in;
	else if(valid_a && ready_a)
		data_out <= data_out + data_in;
	
end


endmodule
```

## What to do
- Identify the logic bug relative to the spec.
- Output a corrected full `TopModule` implementation.
