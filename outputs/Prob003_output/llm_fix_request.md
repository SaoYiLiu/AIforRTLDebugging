# LLM fix request: Prob003

## Goal
Fix `TopModule` so the DUT matches the reference model under the provided testbench.

## Structured feedback
```text
error_kind: logic

## ChipBench regression
- mismatches: 403 / 1215 samples
- first_mismatch_time_ps: 5
- output 'match': 17 mismatches
```

## Testbench result (raw)
```text
VCD info: dumpfile wave.vcd opened for output.
Hint: Output 'match' has 17 mismatches. First mismatch occurred at time 5.
Hint: Output 'not_match' has 387 mismatches. First mismatch occurred at time 5.
Hint: Total mismatched samples is 403 out of 1215 samples

Simulation finished at 6076 ps
Mismatches: 403 in 1215 samples
```

## Waveform summary (from VCD)
```text
signals (first chunk):
- tb.clk
- tb.data
- tb.match_dut
- tb.match_ref
- tb.not_match_dut
- tb.not_match_ref
- tb.rst_n
- tb.stim1.clk
- tb.tb_mismatch

failure_time (ps): 5

causal trace:
- tb.match_dut @ t=5: 0 (Δ=0 before failure)
- tb.not_match_dut @ t=5: 0 (Δ=0 before failure)
- tb.tb_mismatch @ t=5: 0 (Δ=0 before failure)
- tb.match_dut @ t=0: x (Δ=5 before failure)
- tb.match_ref @ t=0: 0 (Δ=5 before failure)
- tb.not_match_dut @ t=0: x (Δ=5 before failure)
- tb.not_match_ref @ t=0: 0 (Δ=5 before failure)
- tb.tb_mismatch @ t=0: 1 (Δ=5 before failure)
- tb.clk @ t=5: 1 (Δ=0 before failure)
- tb.rst_n @ t=5: 1 (Δ=0 before failure)
- tb.stim1.clk @ t=5: 1 (Δ=0 before failure)
- tb.clk @ t=0: 0 (Δ=5 before failure)
- tb.data @ t=0: 0 (Δ=5 before failure)
- tb.rst_n @ t=0: 0 (Δ=5 before failure)
- tb.stim1.clk @ t=0: 0 (Δ=5 before failure)

selected signals:

[tb.match_dut]
0: x
5: 0
2115: 1
2125: 0
2415: 1
2425: 0
4695: 1
4705: 0
4995: 1
5005: 0

[tb.match_ref]
0: 0
2105: 1
2115: 0
2405: 1
2415: 0
4685: 1
4695: 0
4985: 1
4995: 0

[tb.not_match_dut]
0: x
5: 0
75: 1
85: 0
135: 1
145: 0
195: 1
205: 0
255: 1
265: 0
315: 1
325: 0
375: 1
385: 0
435: 1
445: 0
495: 1
505: 0
555: 1
565: 0
615: 1
625: 0
675: 1
685: 0
735: 1
745: 0
795: 1
805: 0
855: 1
865: 0
915: 1
925: 0
975: 1
985: 0
1035: 1
1045: 0
1095: 1
1105: 0
1155: 1
1165: 0
1215: 1
1225: 0
1275: 1
1285: 0
1335: 1
1345: 0
1395: 1
1405: 0
1455: 1
1465: 0
1515: 1
1525: 0
1575: 1
1585: 0
1635: 1
1645: 0
1695: 1
1705: 0
1755: 1
1765: 0
1815: 1
1825: 0
1875: 1
1885: 0
1935: 1
1945: 0
1995: 1
2005: 0
2055: 1
2065: 0
2175: 1
2185: 0
2235: 1
2245: 0
2295: 1
2305: 0
2355: 1
2365: 0
2475: 1
2485: 0
2535: 1
2545: 0
2595: 1
2605: 0
2655: 1
2665: 0
2715: 1
2725: 0
2775: 1
2785: 0
2835: 1
2845: 0
2895: 1
2905: 0
2955: 1
2965: 0
3015: 1
3025: 0
3075: 1
3085: 0
3135: 1
3145: 0
3195: 1
3205: 0
3255: 1
3265: 0
3315: 1
3325: 0
3375: 1
3385: 0
3435: 1
3445: 0
3495: 1
3505: 0
3555: 1
3565: 0
3615: 1
3625: 0
3675: 1
3685: 0
3735: 1
3745: 0
3795: 1
3805: 0
3855: 1
3865: 0
3915: 1
3925: 0
3975: 1
3985: 0
4035: 1
4045: 0
4095: 1
4105: 0
4155: 1
4165: 0
4215: 1
4225: 0
4275: 1
4285: 0
4335: 1
4345: 0
4395: 1
4405: 0
4455: 1
4465: 0
4515: 1
4525: 0
4575: 1
4585: 0
4635: 1
4645: 0
4755: 1
4765: 0
4815: 1
4825: 0
4875: 1
4885: 0
4935: 1
4945: 0

[tb.not_match_ref]
0: 0
65: 1
75: 0
125: 1
135: 0
185: 1
195: 0
245: 1
255: 0
305: 1
315: 0
365: 1
375: 0
425: 1
435: 0
485: 1
495: 0
545: 1
555: 0
605: 1
615: 0
665: 1
675: 0
725: 1
735: 0
785: 1
795: 0
845: 1
855: 0
905: 1
915: 0
965: 1
975: 0
1025: 1
1035: 0
1085: 1
1095: 0
1145: 1
1155: 0
1205: 1
1215: 0
1265: 1
1275: 0
1325: 1
1335: 0
1385: 1
1395: 0
1445: 1
1455: 0
1505: 1
1515: 0
1565: 1
1575: 0
1625: 1
1635: 0
1685: 1
1695: 0
1745: 1
1755: 0
1805: 1
1815: 0
1865: 1
1875: 0
1925: 1
1935: 0
1985: 1
1995: 0
2045: 1
2055: 0
2165: 1
2175: 0
2225: 1
2235: 0
2285: 1
2295: 0
2345: 1
2355: 0
2465: 1
2475: 0
2525: 1
2535: 0
2585: 1
2595: 0
2645: 1
2655: 0
2705: 1
2715: 0
2765: 1
2775: 0
2825: 1
2835: 0
2885: 1
2895: 0
2945: 1
2955: 0
3005: 1
3015: 0
3065: 1
3075: 0
3125: 1
3135: 0
3185: 1
3195: 0
3245: 1
3255: 0
3305: 1
3315: 0
3365: 1
3375: 0
3425: 1
3435: 0
3485: 1
3495: 0
3545: 1
3555: 0
3605: 1
3615: 0
3665: 1
3675: 0
3725: 1
3735: 0
3785: 1
3795: 0
3845: 1
3855: 0
3905: 1
3915: 0
3965: 1
3975: 0
4025: 1
4035: 0
4085: 1
4095: 0
4145: 1
4155: 0
4205: 1
4215: 0
4265: 1
4275: 0
4325: 1
4335: 0
4385: 1
4395: 0
4445: 1
4455: 0
4505: 1
4515: 0
4565: 1
4575: 0
4625: 1
4635: 0
4745: 1
4755: 0
4805: 1
4815: 0
4865: 1
4875: 0
4925: 1
4935: 0

[tb.tb_mismatch]
0: 1
5: 0
65: 1
75: 1
85: 0
125: 1
135: 1
145: 0
185: 1
195: 1
205: 0
245: 1
255: 1
265: 0
305: 1
315: 1
325: 0
365: 1
375: 1
385: 0
425: 1
435: 1
445: 0
485: 1
495: 1
505: 0
545: 1
555: 1
565: 0
605: 1
615: 1
625: 0
665: 1
675: 1
685: 0
725: 1
735: 1
745: 0
785: 1
795: 1
805: 0
845: 1
855: 1
865: 0
905: 1
915: 1
925: 0
965: 1
975: 1
985: 0
1025: 1
1035: 1
1045: 0
1085: 1
1095: 1
1105: 0
1145: 1
1155: 1
1165: 0
1205: 1
1215: 1
1225: 0
1265: 1
1275: 1
1285: 0
1325: 1
1335: 1
1345: 0
1385: 1
1395: 1
1405: 0
1445: 1
1455: 1
1465: 0
1505: 1
1515: 1
1525: 0
1565: 1
1575: 1
1585: 0
1625: 1
1635: 1
1645: 0
1685: 1
1695: 1
1705: 0
1745: 1
1755: 1
1765: 0
1805: 1
1815: 1
1825: 0
1865: 1
1875: 1
1885: 0
1925: 1
1935: 1
1945: 0
1985: 1
1995: 1
2005: 0
2045: 1
2055: 1
2065: 0
2105: 1
2115: 1
2125: 0
2165: 1
2175: 1
2185: 0
2225: 1
2235: 1
2245: 0
2285: 1
2295: 1
2305: 0
2345: 1
2355: 1
2365: 0
2405: 1
2415: 1
2425: 0
2465: 1
2475: 1
2485: 0
2525: 1
2535: 1
2545: 0
2585: 1
2595: 1
2605: 0
2645: 1
2655: 1
2665: 0
2705: 1
2715: 1
2725: 0
2765: 1
2775: 1
2785: 0
2825: 1
2835: 1
2845: 0
2885: 1
2895: 1
2905: 0
2945: 1
2955: 1
2965: 0
3005: 1
3015: 1
3025: 0
3065: 1
3075: 1
3085: 0
3125: 1
3135: 1
3145: 0
3185: 1
3195: 1
3205: 0
3245: 1
3255: 1
3265: 0
3305: 1
3315: 1
3325: 0
3365: 1
3375: 1
3385: 0
3425: 1
3435: 1
3445: 0
3485: 1
3495: 1
3505: 0
3545: 1
3555: 1
3565: 0
3605: 1
3615: 1
3625: 0
3665: 1
3675: 1
3685: 0
3725: 1
3735: 1
3745: 0
3785: 1
3795: 1
3805: 0
3845: 1
3855: 1
3865: 0
3905: 1
3915: 1
3925: 0
3965: 1
3975: 1
3985: 0
```

## Buggy RTL extracted from prompt
```verilog
module TopModule(
	input clk,
	input rst_n,
	input data,
	output reg match,
	output reg not_match
	);


reg [3:0] pstate,nstate;

parameter idle=4'd0,
		  s1=4'd1,
          s2=4'd2,
          s3=4'd3,
          s4=4'd4,
          s5=4'd5,
          s6=4'd6,
		  sf1=4'd7,
          sf2=4'd8,
          sf3=4'd9,
          sf4=4'd10,
          sf5=4'd11,
          sf6=4'd12;

always @(posedge clk or negedge rst_n)
begin
    if(!rst_n)
        pstate<=idle;
    else
        pstate<=nstate;
end

always @(pstate or data)
begin
    case(pstate)
        idle:
            if(data==0)
                nstate=s1;			//First bit matched
            else
                nstate=sf1;
        s1:
            nstate=data?s2:sf2;
        s2:
            nstate=data?s3:sf3;
        s3:
            nstate=data?s4:sf4;
        s4:
            nstate=data?sf5:s5;
        s5:
            nstate=data?sf6:s6;
        s6:
            nstate=data?sf1:s1;
        sf1:
            nstate=sf2;
        sf2:
            nstate=sf3;
        sf3:
            nstate=sf4;
        sf4:
            nstate=sf5;
        sf5:
            nstate=sf6;
        sf6:
			nstate=data?sf1:s1;
        default:
            nstate=idle;
        endcase
end

always @(posedge clk or negedge rst_n) begin
	if (!rst_n) begin
		match <= 1'b0;
		not_match <= 1'b0;
	end
	else if (pstate == s6) begin
		match <= 1'b1;
		not_match <= 1'b0;
	end
	else if (pstate == sf6) begin
		match <= 1'b0;
		not_match <= 1'b1;
	end
	else begin
		match <= 1'b0;
		not_match <= 1'b0;
	end
end

endmodule
```

## Current candidate RTL
```verilog
module TopModule(
	input clk,
	input rst_n,
	input data,
	output reg match,
	output reg not_match
	);


reg [3:0] pstate,nstate;

parameter idle=4'd0,
		  s1=4'd1,
          s2=4'd2,
          s3=4'd3,
          s4=4'd4,
          s5=4'd5,
          s6=4'd6,
		  sf1=4'd7,
          sf2=4'd8,
          sf3=4'd9,
          sf4=4'd10,
          sf5=4'd11,
          sf6=4'd12;

always @(posedge clk or negedge rst_n)
begin
    if(!rst_n)
        pstate<=idle;
    else
        pstate<=nstate;
end

always @(pstate or data)
begin
    case(pstate)
        idle:
            if(data==0)
                nstate=s1;			//First bit matched
            else
                nstate=sf1;
        s1:
            nstate=data?s2:sf2;
        s2:
            nstate=data?s3:sf3;
        s3:
            nstate=data?s4:sf4;
        s4:
            nstate=data?sf5:s5;
        s5:
            nstate=data?sf6:s6;
        s6:
            nstate=data?sf1:s1;
        sf1:
            nstate=sf2;
        sf2:
            nstate=sf3;
        sf3:
            nstate=sf4;
        sf4:
            nstate=sf5;
        sf5:
            nstate=sf6;
        sf6:
			nstate=data?sf1:s1;
        default:
            nstate=idle;
        endcase
end

always @(posedge clk or negedge rst_n) begin
	if (!rst_n) begin
		match <= 1'b0;
		not_match <= 1'b0;
	end
	else if (pstate == s6) begin
		match <= 1'b1;
		not_match <= 1'b0;
	end
	else if (pstate == sf6) begin
		match <= 1'b0;
		not_match <= 1'b1;
	end
	else begin
		match <= 1'b0;
		not_match <= 1'b0;
	end
end

endmodule
```

## What to do
- Identify the logic bug relative to the spec.
- Output a corrected full `TopModule` implementation.
