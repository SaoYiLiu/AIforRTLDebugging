# LLM fix request: Prob006

## Goal
Fix `TopModule` so the DUT matches the reference model under the provided testbench.

## Structured feedback
```text
error_kind: logic

## ChipBench regression
- mismatches: 74 / 151 samples
- first_mismatch_time_ps: 220
- output 'valid_b': 30 mismatches
```

## Connection map
```text
## Connection map (error-focused)
- mismatches: 74 / 151 samples, first_fail_ps=220
- `data_b` role=signal vcd=tb.data_b
- `data_b_dut` role=dut_output vcd=tb.data_b_dut
- `data_b_ref` role=ref_output vcd=tb.data_b_ref
- `match` role=signal vcd=tb.match
- `match_dut` role=dut_output vcd=tb.match_dut
- `match_ref` role=ref_output vcd=tb.match_ref
- `ready_a_dut` role=dut_output vcd=tb.ready_a_dut
- `ready_a_ref` role=ref_output vcd=tb.ready_a_ref
- `tb_match` role=compare_ok vcd=tb.tb_match
- `tb_mismatch` role=compare_fail vcd=tb.tb_mismatch
- `valid_b` role=signal vcd=tb.valid_b
- `valid_b_dut` role=dut_output vcd=tb.valid_b_dut
- `valid_b_ref` role=ref_output vcd=tb.valid_b_ref
- compare signals: ['data_b_dut', 'data_b_ref', 'ready_a_dut', 'ready_a_ref', 'tb_match', 'tb_mismatch', 'valid_b_dut', 'valid_b_ref']
- VCD focus: ['tb.tb_mismatch', 'tb.valid_b_dut', 'tb.valid_b_ref', 'tb.data_b_dut', 'tb.data_b_ref', 'tb.ready_a_dut', 'tb.ready_a_ref', 'tb.valid_a', 'tb.data_a', 'tb.clk', 'tb.rst_n', 'stim1.clk']
```

## Testbench result (raw)
```text
VCD info: dumpfile wave.vcd opened for output.
Hint: Output 'ready_a' has no mismatches.
Hint: Output 'valid_b' has 30 mismatches. First mismatch occurred at time 220.
Hint: Output 'data_b' has 68 mismatches. First mismatch occurred at time 220.
Hint: Total mismatched samples is 74 out of 151 samples

Simulation finished at 756 ps
Mismatches: 74 in 151 samples
```

## Waveform summary (from VCD)
```text
signals (first chunk):
- tb.clk
- tb.data_a
- tb.data_b_dut[5:0]
- tb.data_b_ref[5:0]
- tb.ready_a_dut
- tb.ready_a_ref
- tb.rst_n
- tb.stim1.clk
- tb.tb_mismatch
- tb.valid_a
- tb.valid_b_dut
- tb.valid_b_ref

failure_time (ps): 220

causal trace:
- tb.clk @ t=220: 0 (Δ=0 before failure)
- tb.stim1.clk @ t=220: 0 (Δ=0 before failure)
- tb.clk @ t=215: 1 (Δ=5 before failure)
- tb.data_b_dut[5:0] @ t=215: 111110 (Δ=5 before failure)
- tb.stim1.clk @ t=215: 1 (Δ=5 before failure)
- tb.tb_mismatch @ t=215: 1 (Δ=5 before failure)
- tb.valid_b_dut @ t=215: 1 (Δ=5 before failure)
- tb.clk @ t=210: 0 (Δ=10 before failure)
- tb.stim1.clk @ t=210: 0 (Δ=10 before failure)
- tb.clk @ t=205: 1 (Δ=15 before failure)
- tb.stim1.clk @ t=205: 1 (Δ=15 before failure)
- tb.clk @ t=200: 0 (Δ=20 before failure)
- tb.stim1.clk @ t=200: 0 (Δ=20 before failure)
- tb.clk @ t=195: 1 (Δ=25 before failure)
- tb.stim1.clk @ t=195: 1 (Δ=25 before failure)
- tb.valid_a @ t=195: 1 (Δ=25 before failure)
- tb.clk @ t=190: 0 (Δ=30 before failure)
- tb.stim1.clk @ t=190: 0 (Δ=30 before failure)
- tb.clk @ t=185: 1 (Δ=35 before failure)
- tb.data_a @ t=185: 1 (Δ=35 before failure)

selected signals:

[tb.tb_mismatch]
35: 0
95: 0
105: 0
155: 0
165: 0
215: 1
335: 0
345: 0
395: 1
585: 0
635: 1
645: 0
695: 1
705: 0
715: 1

[tb.valid_b_dut]
95: 1
105: 0
155: 1
165: 0
215: 1
225: 0
275: 1
285: 0
335: 1
345: 0
395: 1
405: 0
455: 1
465: 0
515: 1
525: 0
575: 1
585: 0
635: 1
645: 0
695: 1
705: 0
755: 1

[tb.valid_b_ref]
95: 1
105: 0
155: 1
165: 0
245: 1
255: 0
315: 1
345: 0
435: 1
475: 0
565: 1
575: 0
715: 1
725: 0

[tb.data_b_dut[5:0]]
95: 10101
155: 110011
215: 111110
275: 100001
335: 100110
395: 11100
515: 111110
575: 111111

[tb.data_b_ref[5:0]]
95: 10101
155: 110011
245: 111
335: 100110
465: 110011
565: 111111
715: 1011

[tb.ready_a_dut]
35: 1

[tb.ready_a_ref]
35: 1

[tb.valid_a]
45: 1
165: 0
195: 1
260: 0
265: 1
285: 0
290: 1
310: 0
330: 1
340: 0
355: 1
365: 0
370: 1
380: 0
390: 1
395: 0
400: 1
405: 0
415: 1
430: 0
435: 1
440: 0
445: 1
450: 0
455: 1
475: 0
485: 1
490: 0
495: 1
520: 0
535: 1
555: 0
560: 1
565: 0
570: 1
580: 0
585: 1
590: 0
595: 1
600: 0
605: 1
610: 0
615: 1
620: 0
630: 1
640: 0
655: 1
660: 0
670: 1
675: 0
680: 1
685: 0
700: 1
705: 0
710: 1
720: 0
730: 1
735: 0
745: 1
750: 0
755: 1
```

## Buggy RTL extracted from prompt
```verilog
module TopModule(
    input               clk         ,  
    input               rst_n       ,
    input               valid_a     ,
    input               data_a      ,
  
    output  reg         ready_a     ,
    output  reg         valid_b     ,
    output  reg [5:0]   data_b
);
    reg [5:0] data_r;
    reg [2:0] cnt;
 
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            cnt <= 0;
        else
            cnt <= ~ready_a&&~valid_a? cnt:
                   cnt      ==      5? 0  :
                   cnt+1;
    end
     
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            data_r <= 6'b0;
        else
            data_r <= ready_a&&valid_a? {data_a, data_r[5:1]}: data_r;
    end
     
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            data_b <= 6'b0;
        else
            data_b <= cnt==5&&valid_a? {data_a, data_r[5:1]}: data_b;
    end
     
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            valid_b <= 0;
        else
            valid_b <= cnt==5;
    end
     
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            ready_a <= 0;
        else
            ready_a <= 1;
    end
endmodule
```

## Current candidate RTL
```verilog
module TopModule(
    input               clk         ,  
    input               rst_n       ,
    input               valid_a     ,
    input               data_a      ,
  
    output  reg         ready_a     ,
    output  reg         valid_b     ,
    output  reg [5:0]   data_b
);
    reg [5:0] data_r;
    reg [2:0] cnt;
 
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            cnt <= 0;
        else
            cnt <= ~ready_a&&~valid_a? cnt:
                   cnt      ==      5? 0  :
                   cnt+1;
    end
     
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            data_r <= 6'b0;
        else
            data_r <= ready_a&&valid_a? {data_a, data_r[5:1]}: data_r;
    end
     
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            data_b <= 6'b0;
        else
            data_b <= cnt==5&&valid_a? {data_a, data_r[5:1]}: data_b;
    end
     
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            valid_b <= 0;
        else
            valid_b <= cnt==5;
    end
     
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            ready_a <= 0;
        else
            ready_a <= 1;
    end
endmodule
```

## What to do
- Identify the logic bug relative to the spec.
- Output a corrected full `TopModule` implementation.
