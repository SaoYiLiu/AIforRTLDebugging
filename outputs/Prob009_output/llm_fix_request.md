# LLM fix request: Prob009

## Goal
Fix `TopModule` so the DUT matches the reference model under the provided testbench.

## Structured feedback
```text
error_kind: logic

## ChipBench regression
- mismatches: 96 / 127 samples
- first_mismatch_time_ps: 40
- output 'valid_out': 36 mismatches
```

## Connection map
```text
## Connection map (error-focused)
- mismatches: 96 / 127 samples, first_fail_ps=40
- `data_out` role=signal vcd=tb.data_out
- `data_out_dut` role=dut_output vcd=tb.data_out_dut
- `data_out_ref` role=ref_output vcd=tb.data_out_ref
- `match` role=signal vcd=tb.match
- `match_dut` role=dut_output vcd=tb.{valid_out_dut,data_out_dut}
- `match_ref` role=ref_output vcd=tb.{valid_out_ref,data_out_ref}
- `tb_match` role=compare_ok vcd=tb.tb_match
- `tb_mismatch` role=compare_fail vcd=tb.tb_mismatch
- `valid_out` role=signal vcd=tb.valid_out
- `valid_out_dut` role=dut_output vcd=tb.valid_out_dut
- `valid_out_ref` role=ref_output vcd=tb.valid_out_ref
- compare signals: ['valid_out_ref', 'valid_out_dut', 'data_out_ref', 'data_out_dut', 'tb_match', 'tb_mismatch']
- VCD focus: ['tb.tb_mismatch', 'tb.data_out_dut', 'tb.data_out_ref', 'tb.valid_out_dut', 'tb.valid_out_ref', 'tb.valid_in', 'tb.data_in', 'tb.tb_match', 'tb.clk', 'tb.rst_n']
```

## Testbench result (raw)
```text
VCD info: dumpfile wave.vcd opened for output.
Hint: Output 'valid_out' has 36 mismatches. First mismatch occurred at time 40.
Hint: Output 'data_out' has 96 mismatches. First mismatch occurred at time 40.
Hint: Total mismatched samples is 96 out of 127 samples

Simulation finished at 636 ps
Mismatches: 96 in 127 samples
```

## Waveform summary (from VCD)
```text
signals (first chunk):
- tb.clk
- tb.data_in[7:0]
- tb.data_out_dut[11:0]
- tb.data_out_ref[11:0]
- tb.rst_n
- tb.stim1.clk
- tb.tb_mismatch
- tb.valid_in
- tb.valid_out_dut
- tb.valid_out_ref

failure_time (ps): 40

causal trace:
- tb.clk @ t=40: 0 (Δ=0 before failure)
- tb.clk @ t=35: 1 (Δ=5 before failure)
- tb.data_in[7:0] @ t=35: 10101010 (Δ=5 before failure)
- tb.data_out_dut[11:0] @ t=35: 1010 (Δ=5 before failure)
- tb.tb_mismatch @ t=35: 1 (Δ=5 before failure)
- tb.valid_in @ t=35: 1 (Δ=5 before failure)
- tb.valid_out_dut @ t=35: 1 (Δ=5 before failure)
- tb.clk @ t=30: 0 (Δ=10 before failure)
- tb.clk @ t=25: 1 (Δ=15 before failure)
- tb.rst_n @ t=25: 1 (Δ=15 before failure)
- tb.clk @ t=20: 0 (Δ=20 before failure)
- tb.clk @ t=15: 1 (Δ=25 before failure)
- tb.clk @ t=10: 0 (Δ=30 before failure)
- tb.clk @ t=5: 1 (Δ=35 before failure)
- tb.data_out_dut[11:0] @ t=5: 0 (Δ=35 before failure)
- tb.data_out_ref[11:0] @ t=5: 0 (Δ=35 before failure)
- tb.tb_mismatch @ t=5: 0 (Δ=35 before failure)
- tb.valid_out_dut @ t=5: 0 (Δ=35 before failure)
- tb.valid_out_ref @ t=5: 0 (Δ=35 before failure)
- tb.clk @ t=0: 0 (Δ=40 before failure)

selected signals:

[tb.tb_mismatch]
0: 0
5: 0
35: 1
45: 0
55: 1
165: 0
175: 1
245: 0
255: 1
345: 0
355: 1
425: 0
435: 1
455: 0
465: 0
515: 1
555: 0
565: 1

[tb.data_out_dut[11:0]]
0: x
5: 0
35: 1010
45: 101010100101
55: 10101010001
65: 100100011
155: 110111101000
165: 100011010000
175: 11011000
185: 100011001010
245: 10111010101
255: 10111001111
305: 101101100100
345: 10011111000
355: 100010010101
425: 100110110011
435: 1111001011
445: 101111101101
455: 110111011111
515: 110111110100
555: 10011010010
565: 1011100010
585: 100110111010
595: 101000011010

[tb.data_out_ref[11:0]]
0: x
5: 0
45: 101010100101
55: 10100010010
95: 1101000111
105: 100010011010
125: 101111001101
135: 111011011110
165: 100011010000
175: 110110001100
215: 101010100110
245: 10111010101
275: 110011111101
285: 100010110110
345: 10011111000
355: 100101010001
395: 110100110100
425: 100110110011
445: 110010111110
455: 110111011111
555: 10011010010
565: 111000101001
595: 101110100001
615: 101011011100

[tb.valid_out_dut]
0: x
5: 0
35: 1
75: 0
155: 1
195: 0
245: 1
265: 0
305: 1
315: 0
345: 1
365: 0
425: 1
465: 0
515: 1
525: 0
555: 1
575: 0
585: 1
605: 0

[tb.valid_out_ref]
0: x
5: 0
45: 1
65: 0
95: 1
115: 0
125: 1
145: 0
165: 1
185: 0
215: 1
225: 0
245: 1
255: 0
275: 1
295: 0
345: 1
365: 0
395: 1
405: 0
425: 1
435: 0
445: 1
465: 0
555: 1
575: 0
595: 1
605: 0
615: 1
625: 0

[tb.valid_in]
0: 0
35: 1
75: 0
95: 1
140: 0
145: 1
165: 0
170: 1
190: 0
210: 1
220: 0
235: 1
245: 0
250: 1
260: 0
270: 1
275: 0
280: 1
285: 0
295: 1
310: 0
315: 1
320: 0
325: 1
330: 0
335: 1
355: 0
365: 1
370: 0
375: 1
400: 0
415: 1
435: 0
440: 1
445: 0
450: 1
460: 0
465: 1
470: 0
475: 1
480: 0
485: 1
490: 0
495: 1
500: 0
510: 1
520: 0
535: 1
540: 0
550: 1
555: 0
560: 1
565: 0
580: 1
585: 0
590: 1
600: 0
610: 1
615: 0
625: 1
630: 0
635: 1

[tb.data_in[7:0]]
0: 0
35: 10101010
45: 1010101
55: 10010
65: 110100
75: 11111111
85: 11101110
95: 1111000
105: 10011010
115: 10111100
125: 11011110
140: 10000001
145: 1100011
150: 10001101
155: 10010
160: 1101
165: 111101
170: 10001100
175: 11000110
180: 10101010
185: 1110111
190: 10001111
195: 11001110
200: 11000101
205: 10111101
210: 1100101
215: 1010
220: 100000
225: 10011101
230: 10011
235: 1010011
240: 11010101
245: 10101110
250: 11001111
255: 1010
260: 111100
265: 10001010
270: 11011000
275: 10001001
280: 10110110
285: 10101110
290: 101010
295: 1110001
300: 1001111
305: 111010
310: 10101
315: 11011001
320: 1001100
325: 10001111
330: 10110111
335: 1011100
340: 10001001
345: 11010000
350: 1010001
355: 1100
360: 11001000
365: 111101
370: 1111110
375: 111001
380: 11010011
385: 1111000
390: 1001001
395: 101010
400: 10000110
405: 10011100
410: 100110
415: 10100011
420: 10110011
425: 1000100
430: 11001011
435: 1011010
440: 11101101
445: 1100101
450: 11011111
455: 1000100
460: 101010
465: 1110
470: 10011010
475: 11000011
480: 1001110
485: 1010
490: 111000
495: 10111000
500: 10010011
505: 1011001
510: 1001101
515: 1101101
520: 11001010
525: 10010101
530: 100
535: 1101001
540: 10001000
545: 101101
550: 101110
555: 11100
560: 101001
565: 10000110
570: 111101
575: 1110000
580: 10111010
585: 11111010
590: 11010
595: 110111
600: 11000000
605: 10110110
610: 11011100
615: 1111000
620: 11011011
625: 1111001
630: 1100001
635: 10100001

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
```

## Buggy RTL extracted from prompt
```verilog
module TopModule(
	input 				   clk 		,   
	input 			      rst_n		,
	input				      valid_in	,
	input	[7:0]			   data_in	,
 
 	output  reg			   valid_out,
	output  reg [11:0]   data_out
);
reg 	[7:0]		data_lock;
reg 	[1:0]		valid_cnt		;
always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		data_lock <= 'd0;
	else if(valid_in )
		data_lock <= data_in;
end
always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		valid_cnt <= 'd0;
	else if(!valid_in)begin
		if(valid_cnt == 2'd2)
			valid_cnt <= 2'd0;
		else
			valid_cnt <= valid_cnt + 1'd1;
	end 
end
always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		valid_out <= 'd0;
	else if(valid_in && valid_cnt == 2'd1)
		valid_out <= 1'd1;
	else if(valid_in && valid_cnt == 2'd2)
		valid_out <= 1'd1;
	else
		valid_out <= 'd0;
end
always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		data_out <= 'd0;
	else if(valid_in && valid_cnt == 2'd1)
		data_out <= {data_lock, data_in[7:4]};
	else if(valid_in && valid_cnt == 2'd2)
		data_out <= {data_lock[3:0], data_in};
end
endmodule
```

## Current candidate RTL
```verilog
module TopModule(
	input 				   clk 		,   
	input 			      rst_n		,
	input				      valid_in	,
	input	[7:0]			   data_in	,
 
 	output  reg			   valid_out,
	output  reg [11:0]   data_out
);
reg 	[7:0]		data_lock;
reg 	[1:0]		valid_cnt		;
always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		data_lock <= 'd0;
	else if(valid_in )
		data_lock <= data_in;
end
always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		valid_cnt <= 'd0;
	else if(!valid_in)begin
		if(valid_cnt == 2'd2)
			valid_cnt <= 2'd0;
		else
			valid_cnt <= valid_cnt + 1'd1;
	end 
end
always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		valid_out <= 'd0;
	else if(valid_in && valid_cnt == 2'd1)
		valid_out <= 1'd1;
	else if(valid_in && valid_cnt == 2'd2)
		valid_out <= 1'd1;
	else
		valid_out <= 'd0;
end
always @(posedge clk or negedge rst_n ) begin
	if(!rst_n) 
		data_out <= 'd0;
	else if(valid_in && valid_cnt == 2'd1)
		data_out <= {data_lock, data_in[7:4]};
	else if(valid_in && valid_cnt == 2'd2)
		data_out <= {data_lock[3:0], data_in};
end
endmodule
```

## What to do
- Identify the logic bug relative to the spec.
- Output a corrected full `TopModule` implementation.
