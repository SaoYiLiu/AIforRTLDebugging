# LLM fix request: Prob030

## Goal
Fix `TopModule` so the DUT matches the reference model under the provided testbench.

## Structured feedback
```text
error_kind: logic

## ChipBench regression
- mismatches: 376 / 427 samples
- first_mismatch_time_ps: 80
- output 'read_data': 376 mismatches
```

## Connection map
```text
## Connection map (error-focused)
- mismatches: 376 / 427 samples, first_fail_ps=80
- `match` role=signal vcd=tb.match
- `match_dut` role=dut_output vcd=tb.match_dut
- `match_ref` role=ref_output vcd=tb.match_ref
- `read_data` role=signal vcd=tb.read_data
- `read_data_dut` role=signal vcd=tb.read_data_dut
- `read_data_ref` role=signal vcd=tb.read_data_ref
- `tb_match` role=compare_ok vcd=tb.tb_match
- `tb_mismatch` role=compare_fail vcd=tb.tb_mismatch
- compare signals: ['match_dut', 'match_ref', 'tb_match', 'tb_mismatch']
- VCD focus: ['tb_mismatch', 'tb.tb_mismatch', 'match_dut', 'match_ref', 'tb.match_dut', 'tb.match_ref', 'tb.read_data_ref', 'tb.read_data_dut']
```

## Testbench result (raw)
```text
VCD info: dumpfile wave.vcd opened for output.
Hint: Output 'read_data' has 376 mismatches. First mismatch occurred at time 80.
Hint: Total mismatched samples is 376 out of 427 samples

Simulation finished at 2136 ps
Mismatches: 376 in 427 samples
```

## Waveform summary (from VCD)
```text
signals (first chunk):
- tb.clk
- tb.read_addr[7:0]
- tb.read_data_dut[3:0]
- tb.read_data_ref[3:0]
- tb.read_en
- tb.rst_n
- tb.stim1.clk
- tb.tb_mismatch
- tb.write_addr[7:0]
- tb.write_data[3:0]
- tb.write_en

failure_time (ps): 80

causal trace:
- tb.read_data_ref[3:0] @ t=75: 1010 (Δ=5 before failure)
- tb.tb_mismatch @ t=75: 1 (Δ=5 before failure)
- tb.read_data_dut[3:0] @ t=0: 0 (Δ=80 before failure)
- tb.read_data_ref[3:0] @ t=0: 0 (Δ=80 before failure)
- tb.tb_mismatch @ t=0: 0 (Δ=80 before failure)
- tb.clk @ t=80: 0 (Δ=0 before failure)
- tb.stim1.clk @ t=80: 0 (Δ=0 before failure)
- tb.clk @ t=75: 1 (Δ=5 before failure)
- tb.read_addr[7:0] @ t=75: 1 (Δ=5 before failure)
- tb.stim1.clk @ t=75: 1 (Δ=5 before failure)
- tb.clk @ t=70: 0 (Δ=10 before failure)
- tb.stim1.clk @ t=70: 0 (Δ=10 before failure)
- tb.clk @ t=65: 1 (Δ=15 before failure)
- tb.read_en @ t=65: 1 (Δ=15 before failure)
- tb.stim1.clk @ t=65: 1 (Δ=15 before failure)
- tb.clk @ t=60: 0 (Δ=20 before failure)
- tb.stim1.clk @ t=60: 0 (Δ=20 before failure)
- tb.clk @ t=55: 1 (Δ=25 before failure)
- tb.stim1.clk @ t=55: 1 (Δ=25 before failure)
- tb.write_en @ t=55: 0 (Δ=25 before failure)

selected signals:

[tb.tb_mismatch]
0: 0
75: 1
95: 0
115: 1
165: 0
205: 1
235: 0
265: 1
305: 0
315: 1
355: 1
685: 0
705: 1
725: 0
755: 1
765: 1
1495: 0
1505: 1
1885: 0
1895: 1
1955: 1
2125: 0
2135: 0

[tb.read_data_ref[3:0]]
0: 0
75: 1010
85: 101
95: 1111
115: 1010
125: 101
165: 1111
205: 111
215: 1010
225: 1101
235: 1111
265: 1101
285: 1100
305: 0
315: 1101
325: 1111
335: 1100
345: 1101
355: 0
395: 1000
405: 1111
425: 1010
445: 1101
455: 1010
465: 1111
515: 1101
565: 1010
685: 1001
705: 1010
725: 1001
755: 1111
765: 1101
775: 1011
785: 1010
835: 1111
855: 11
865: 1000
875: 110
885: 11
895: 1
905: 1000
975: 11
985: 100
1005: 10
1035: 1010
1065: 0
1075: 10
1125: 1011
1135: 111
1145: 1011
1175: 1000
1185: 11
1205: 1011
1215: 11
1295: 1011
1305: 101
1335: 1000
1355: 101
1435: 1000
1445: 1111
1495: 1100
1505: 1111
1525: 1001
1575: 1000
1595: 1001
1615: 100
1705: 1100
1745: 1
1755: 1011
1765: 1
1785: 100
1805: 1011
1855: 1110
1865: 1011
1875: 1110
1885: 1000
1895: 0
1915: 1000
1935: 1011
1945: 1110
1955: 101
1975: 1001
1995: 1011
2065: 1000
2125: 1111
2135: 10

[tb.read_data_dut[3:0]]
0: 0
95: 1111
115: 0
165: 1111
205: 0
235: 1111
265: 0
285: 1111
305: 0
315: 101
325: 11
335: 1000
345: 0
355: 1100
395: 110
405: 11
425: 0
445: 101
455: 0
465: 11
515: 101
565: 100
585: 0
685: 1001
705: 11
725: 1001
755: 1101
765: 110
785: 11
835: 0
855: 1010
865: 1001
875: 1000
885: 1010
895: 11
905: 1001
975: 1000
985: 1101
1005: 111
1035: 1100
1065: 1011
1075: 111
1125: 1010
1135: 0
1145: 1
1175: 100
1185: 1111
1205: 1000
1215: 1100
1295: 1101
1305: 1100
1315: 0
1335: 1100
1355: 0
1405: 1000
1425: 110
1435: 1010
1495: 1100
1505: 1110
1575: 110
1595: 1110
1615: 110
1655: 0
1705: 1010
1745: 1110
1755: 0
1765: 110
1785: 101
1805: 10
1855: 101
1865: 10
1875: 101
1885: 1000
1895: 1001
1915: 100
1935: 10
1945: 101
1955: 110
1975: 10
2065: 1011
2125: 1111
2135: 10
```

## Buggy RTL extracted from prompt
```verilog
module TopModule(
	input clk,
	input rst_n,
	
	input write_en,
	input [7:0]write_addr,
    input [3:0]write_data,
	
	input read_en,
	input [7:0]read_addr,
	output reg [3:0]read_data
);
    reg [3:0] myRAM [7:0];
    
    reg [8:0] i;
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            for(i=0;i<256;i=i+1)
                myRAM[i] <= 0;
        else
            myRAM[write_addr] <= !write_en? write_data: myRAM[write_addr];
    end
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            read_data <= 0;
        else
            read_data <= read_en? myRAM[read_addr]: read_data;
    end
endmodule
```

## Current candidate RTL
```verilog
module TopModule(
	input clk,
	input rst_n,
	
	input write_en,
	input [7:0]write_addr,
    input [3:0]write_data,
	
	input read_en,
	input [7:0]read_addr,
	output reg [3:0]read_data
);
    reg [3:0] myRAM [7:0];
    
    reg [8:0] i;
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            for(i=0;i<256;i=i+1)
                myRAM[i] <= 0;
        else
            myRAM[write_addr] <= !write_en? write_data: myRAM[write_addr];
    end
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n)
            read_data <= 0;
        else
            read_data <= read_en? myRAM[read_addr]: read_data;
    end
endmodule
```

## What to do
- Identify the logic bug relative to the spec.
- Output a corrected full `TopModule` implementation.
