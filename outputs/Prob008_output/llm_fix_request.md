# LLM fix request: Prob008

## Goal
Fix `TopModule` so the DUT matches the reference model under the provided testbench.

## Structured feedback
```text
error_kind: logic

## ChipBench regression
- mismatches: 132 / 261 samples
- first_mismatch_time_ps: 110
- output 'valid_out': 132 mismatches
```

## Connection map
```text
## Connection map (error-focused)
- mismatches: 132 / 261 samples, first_fail_ps=110
- `data_out_dut` role=dut_output vcd=tb.data_out_dut
- `data_out_ref` role=ref_output vcd=tb.data_out_ref
- `match` role=compare_ok vcd=tb.match
- `match_dut` role=dut_output vcd=tb.match_dut
- `match_ref` role=ref_output vcd=tb.match_ref
- `tb_match` role=compare_ok vcd=tb.tb_match
- `tb_mismatch` role=compare_fail vcd=tb.tb_mismatch
- `valid_out` role=dut_output vcd=tb.valid_out
- `valid_out_dut` role=dut_output vcd=tb.valid_out_dut
- `valid_out_ref` role=ref_output vcd=tb.valid_out_ref
- compare signals: ['data_out_dut', 'data_out_ref', 'tb_match', 'tb_mismatch', 'valid_out_dut', 'valid_out_ref']
- VCD focus: ['tb.tb_mismatch', 'tb.valid_out_dut', 'tb.valid_out_ref', 'tb.tb_match', 'tb.data_out_dut', 'tb.data_out_ref', 'tb.clk', 'tb.rst_n', 'tb.valid_in', 'tb.data_in']
```

## Testbench result (raw)
```text
VCD info: dumpfile wave.vcd opened for output.
Hint: Output 'valid_out' has 132 mismatches. First mismatch occurred at time 110.
Hint: Output 'data_out' has no mismatches.
Hint: Total mismatched samples is 132 out of 261 samples

Simulation finished at 1306 ps
Mismatches: 132 in 261 samples
```

## Waveform summary (from VCD)
```text
signals (first chunk):
- tb.clk
- tb.data_in[23:0]
- tb.data_out_dut[127:0]
- tb.data_out_ref[127:0]
- tb.rst_n
- tb.stim1.clk
- tb.tb_mismatch
- tb.valid_in
- tb.valid_out_dut
- tb.valid_out_ref

failure_time (ps): 110

causal trace:
- tb.clk @ t=110: 0 (Δ=0 before failure)
- tb.clk @ t=105: 1 (Δ=5 before failure)
- tb.data_in[23:0] @ t=105: 100010001000100010001 (Δ=5 before failure)
- tb.tb_mismatch @ t=105: 1 (Δ=5 before failure)
- tb.valid_in @ t=105: 1 (Δ=5 before failure)
- tb.valid_out_dut @ t=105: 1 (Δ=5 before failure)
- tb.clk @ t=100: 0 (Δ=10 before failure)
- tb.clk @ t=95: 1 (Δ=15 before failure)
- tb.rst_n @ t=95: 1 (Δ=15 before failure)
- tb.clk @ t=90: 0 (Δ=20 before failure)
- tb.clk @ t=85: 1 (Δ=25 before failure)
- tb.clk @ t=80: 0 (Δ=30 before failure)
- tb.clk @ t=75: 1 (Δ=35 before failure)
- tb.clk @ t=70: 0 (Δ=40 before failure)
- tb.clk @ t=65: 1 (Δ=45 before failure)
- tb.clk @ t=60: 0 (Δ=50 before failure)
- tb.clk @ t=55: 1 (Δ=55 before failure)
- tb.clk @ t=50: 0 (Δ=60 before failure)
- tb.clk @ t=45: 1 (Δ=65 before failure)
- tb.clk @ t=40: 0 (Δ=70 before failure)

selected signals:

[tb.tb_mismatch]
0: 0
5: 0
105: 1
155: 0
165: 1
205: 0
215: 1
225: 0
245: 1
275: 0
285: 1
315: 0
325: 1
345: 0
355: 1
365: 0
385: 1
395: 0
415: 1
445: 0
455: 1
465: 0
475: 1
485: 0
515: 1
555: 0
565: 1
575: 0
595: 1
685: 0
695: 0
725: 1
745: 0
755: 1
785: 0
795: 0
825: 1
845: 0
875: 1
905: 0
915: 0
935: 1
945: 0
985: 1
995: 0
1025: 1
1045: 0
1065: 1
1085: 0
1095: 1
1115: 0
1135: 1
1145: 0
1155: 1
1165: 0
1175: 1
1185: 0
1195: 1
1205: 0
1215: 1
1225: 0
1235: 1
1275: 0
1285: 0
1305: 1

[tb.valid_out_dut]
0: x
5: 0
105: 1
225: 0
245: 1
315: 0
325: 1
365: 0
385: 1
395: 0
415: 1
465: 0
475: 1
485: 0
515: 1
575: 0
595: 1
695: 0
725: 1
745: 0
755: 1
795: 0
825: 1
845: 0
875: 1
915: 0
935: 1
945: 0
985: 1
995: 0
1025: 1
1045: 0
1065: 1
1115: 0
1135: 1
1145: 0
1155: 1
1185: 0
1195: 1
1205: 0
1215: 1
1225: 0
1235: 1
1285: 0
1305: 1

[tb.valid_out_ref]
0: x
5: 0
155: 1
165: 0
205: 1
215: 0
275: 1
285: 0
345: 1
355: 0
445: 1
455: 0
555: 1
565: 0
685: 1
695: 0
785: 1
795: 0
905: 1
915: 0
1085: 1
1095: 0
1165: 1
1175: 0
1275: 1
1285: 0

[tb.data_out_dut[127:0]]
0: x
5: 0
155: 10001000100010001000100100010001000100010001000110011001100110011001101000100010001000100010001010101010101010101010101100110
205: 1100110011001100111011101110111011101111000100010001000100010001001100110011001100110011010101010101010101010101011101110111011
275: 10111011110011001100110011001100111111111111111111111111000000000000000000000000000100100011010001010110011110001001101010111100
345: 11011110111100000001001000110100010101100111100000110100010101100111100011011111100110011000110111010111110011010000110100101101
445: 11110111100011000001001111010010101010101010011100100110011001011010011000101010110101011100010101110010110011110100101100110100
555: 11011000000000100110010110110110111100100101010101001111110111100011011110001001110001111111110001010001111010111111011011010011
685: 10001011010010110100100111010010100100101011001110011011001101101100101110000010111000101110110110111110100101001101111111111100
785: 11011110010011010101110010011100001011101001111000000111001010010111000110011001101110100010010011110110000110100101111100001111
905: 11011100101100010111010111000001100011000100001001110011011001001110001111001000101101111010111011000111001100111001000010000110
1085: 11100101000111100000101101110110000111001000011010001001000011110010101111010101111110011010000110110001000110111111010111100101
1165: 10111011110110110100011011011101001010100111010101000010011111000010100000110001110000001011000101001110111000010011011000000100
1275: 10000110011001111110001001011010000101001100111010011110110111001111000000001101110000010010100111100011001011010110000101101010

[tb.data_out_ref[127:0]]
0: x
5: 0
155: 10001000100010001000100100010001000100010001000110011001100110011001101000100010001000100010001010101010101010101010101100110
205: 1100110011001100111011101110111011101111000100010001000100010001001100110011001100110011010101010101010101010101011101110111011
275: 10111011110011001100110011001100111111111111111111111111000000000000000000000000000100100011010001010110011110001001101010111100
345: 11011110111100000001001000110100010101100111100000110100010101100111100011011111100110011000110111010111110011010000110100101101
445: 11110111100011000001001111010010101010101010011100100110011001011010011000101010110101011100010101110010110011110100101100110100
555: 11011000000000100110010110110110111100100101010101001111110111100011011110001001110001111111110001010001111010111111011011010011
685: 10001011010010110100100111010010100100101011001110011011001101101100101110000010111000101110110110111110100101001101111111111100
785: 11011110010011010101110010011100001011101001111000000111001010010111000110011001101110100010010011110110000110100101111100001111
905: 11011100101100010111010111000001100011000100001001110011011001001110001111001000101101111010111011000111001100111001000010000110
1085: 11100101000111100000101101110110000111001000011010001001000011110010101111010101111110011010000110110001000110111111010111100101
1165: 10111011110110110100011011011101001010100111010101000010011111000010100000110001110000001011000101001110111000010011011000000100
1275: 10000110011001111110001001011010000101001100111010011110110111001111000000001101110000010010100111100011001011010110000101101010

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
95: 1

[tb.valid_in]
0: 0
105: 1
225: 0
245: 1
310: 0
315: 1
335: 0
340: 1
360: 0
380: 1
390: 0
405: 1
415: 0
420: 1
430: 0
440: 1
445: 0
450: 1
455: 0
465: 1
480: 0
485: 1
490: 0
495: 1
500: 0
505: 1
525: 0
535: 1
540: 0
545: 1
570: 0
585: 1
605: 0
610: 1
615: 0
620: 1
630: 0
635: 1
640: 0
645: 1
650: 0
655: 1
660: 0
665: 1
670: 0
680: 1
690: 0
705: 1
710: 0
720: 1
725: 0
730: 1
735: 0
750: 1
755: 0
760: 1
770: 0
780: 1
785: 0
795: 1
800: 0
805: 1
810: 0
815: 1
835: 0
845: 1
850: 0
855: 1
860: 0
870: 1
875: 0
880: 1
885: 0
900: 1
905: 0
925: 1
940: 0
945: 1
950: 0
955: 1
960: 0
965: 1
970: 0
980: 1
990: 0
1005: 1
1010: 0
1015: 1
1040: 0
1055: 1
1070: 0
1075: 1
1095: 0
1100: 1
1105: 0
1130: 1
1135: 0
1150: 1
1180: 0
1185: 1
1195: 0
1210: 1
1220: 0
1225: 1
1240: 0
1255: 1
1260: 0
1270: 1
1275: 0
1300: 1
```

## Buggy RTL extracted from prompt
```verilog
module TopModule(
	input 				clk 		,   
	input 				rst_n		,
	input				valid_in	,
	input	[23:0]		data_in		,
 
 	output	reg			valid_out	,
	output  reg [127:0]	data_out
);
    reg [3:0]   cnt;
    reg [127:0] data_lock;
    
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            cnt <= 0;
        else
            cnt <= ~valid_in? cnt:cnt+1;
    end
    
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            valid_out <= 0;
        else
            valid_out <= (cnt==5 || cnt==10 || cnt==15) || valid_in;
    end
    
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            data_lock <= 0;
        else
            data_lock <= valid_in? {data_lock[103:0], data_in}: data_lock;
    end
    
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            data_out <= 0;
        else if(cnt==5)
            data_out <= valid_in? {data_lock[119:0], data_in[23:16]}: data_out;
        else if(cnt==10)
            data_out <= valid_in? {data_lock[111:0], data_in[23: 8]}: data_out;
        else if(cnt==15)
            data_out <= valid_in? {data_lock[103:0], data_in[23: 0]}: data_out;
        else
            data_out <= data_out;
    end
endmodule
```

## Current candidate RTL
```verilog
module TopModule(
	input 				clk 		,   
	input 				rst_n		,
	input				valid_in	,
	input	[23:0]		data_in		,
 
 	output	reg			valid_out	,
	output  reg [127:0]	data_out
);
    reg [3:0]   cnt;
    reg [127:0] data_lock;
    
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            cnt <= 0;
        else
            cnt <= ~valid_in? cnt:cnt+1;
    end
    
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            valid_out <= 0;
        else
            valid_out <= (cnt==5 || cnt==10 || cnt==15) || valid_in;
    end
    
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            data_lock <= 0;
        else
            data_lock <= valid_in? {data_lock[103:0], data_in}: data_lock;
    end
    
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            data_out <= 0;
        else if(cnt==5)
            data_out <= valid_in? {data_lock[119:0], data_in[23:16]}: data_out;
        else if(cnt==10)
            data_out <= valid_in? {data_lock[111:0], data_in[23: 8]}: data_out;
        else if(cnt==15)
            data_out <= valid_in? {data_lock[103:0], data_in[23: 0]}: data_out;
        else
            data_out <= data_out;
    end
endmodule
```

## What to do
- Identify the logic bug relative to the spec.
- Output a corrected full `TopModule` implementation.
