Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_rgb2ycbcr_0001

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
The `axis_rgb2ycbcr` module has a bug where the **FIFO read pointer does not correctly track written data**, causing incorrect pixel values to be output. Instead of outputting the correct first pixel in the sequence, the module reads earlier intermediate data, leading to **mismatched YCbCr values** at specific indices of output.

The bug could also be caused by stage buffering of intermediate data, where the pipeline registers (`y_reg`, `cb_reg`, `cr_reg`) introduce unintended delays in the data path, leading to misaligned reads and writes in the FIFO.

---

## Test Case Details

### **Test Case 1:**
**Input Parameters:**  
`IMG_WIDTH` = 6  
`IMG_HEIGHT` = 2  

**Actual Output:**  
Received Pixel 0: 0000, Expected: 8566, Valid Bit: 1
Received Pixel 1: 1410, Expected: 62FD, Valid Bit: 1
Received Pixel 2: 8566, Expected: A952, Valid Bit: 1
Received Pixel 3: 62FD, Expected: EBAF, Valid Bit: 1

**Expected Output:**  
Received Pixel 0: 8566, Expected: 8566, Valid Bit: 1
Received Pixel 1: 62FD, Expected: 62FD, Valid Bit: 1
Received Pixel 2: A952, Expected: A952, Valid Bit: 1
Received Pixel 3: EBAF, Expected: EBAF, Valid Bit: 1


**Discrepancy:**  
- **Pixel 0 incorrectly outputs `0000` instead of `8566`**  
- **Pixel 1 incorrectly outputs `1410` instead of `62FD`**  
Incorrect initial values being read.

---

### **Test Case 2:**
**Input Parameters:**  
`IMG_WIDTH` = 5  
`IMG_HEIGHT` = 3  

**Actual Output:**  
Received Pixel 0: 0000, Expected: 5AD0, Valid Bit: 1
Received Pixel 1: 1410, Expected: 356D, Valid Bit: 1
Received Pixel 2: 5AD0, Expected: 6677, Valid Bit: 1
Received Pixel 3: 356D, Expected: 9BD4, Valid Bit: 1

**Expected Output:**  
Received Pixel 0: 5AD0, Expected: 5AD0, Valid Bit: 1
Received Pixel 1: 356D, Expected: 356D, Valid Bit: 1
Received Pixel 2: 6677, Expected: 6677, Valid Bit: 1
Received Pixel 3: 9BD4, Expected: 9BD4, Valid Bit: 1

**Discrepancy:**  
- **Pixel 0 incorrectly outputs `0000` instead of `5AD0`**  
- **Pixel 1 incorrectly outputs `1410` instead of `356D`**  
Incorrect initial values being read.

---

## **Observations**
1. **Write and Read Pointers Out of Sync:**  
   - The read pointer is **incremented too early**, causing incorrect data to be sent out.

2. **Possible Stage Buffering Issue:**  
   - The intermediate registers (`y_reg`, `cb_reg`, `cr_reg`) might introduce an unintended pipeline delay.
   - **The write pointer updates before `y_reg`, `cb_reg`, `cr_reg` are fully computed,** causing stale or delayed data to be written into the FIFO.
   - This could cause **incorrect alignment between FIFO write and read operations**.

## Current candidate files (line-numbered on patch targets)
### rtl/axis_rgb2ycbcr.sv
```verilog
1| module axis_rgb2ycbcr #(
   2|     parameter PIXEL_WIDTH = 16,
   3|     parameter FIFO_DEPTH = 16
   4| )(
   5|     input  wire            aclk,
   6|     input  wire            aresetn,
   7| 
   8|     // AXI Stream Slave Interface (Input)
   9|     input  wire [15:0]     s_axis_tdata,
  10|     input  wire            s_axis_tvalid,
  11|     output wire            s_axis_tready,
  12|     input  wire            s_axis_tlast,
  13|     input  wire            s_axis_tuser,
  14| 
  15|     // AXI Stream Master Interface (Output)
  16|     output wire [15:0]     m_axis_tdata,
  17|     output wire            m_axis_tvalid,
  18|     input  wire            m_axis_tready,
  19|     output wire            m_axis_tlast,
  20|     output wire            m_axis_tuser
  21| );
  22| 
  23|     // -----------------------------
  24|     // FIFO Buffer (16-depth buffer)
  25|     // -----------------------------
  26|     reg [15:0] fifo_data [0:FIFO_DEPTH-1];
  27|     reg        fifo_tlast [0:FIFO_DEPTH-1];
  28|     reg        fifo_tuser [0:FIFO_DEPTH-1];
  29| 
  30|     reg [3:0]  write_ptr, read_ptr; // 4-bit pointers for FIFO
  31|     reg        full;
  32|     wire       empty;
  33| 
  34|     wire       fifo_write = s_axis_tvalid && !full;
  35|     wire       fifo_read  = !empty && m_axis_tready;
  36| 
  37|     // -----------------------------
  38|     // RGB Extraction 
  39|     // -----------------------------
  40|     reg [7:0] r, g, b;
  41|     always @(posedge aclk) begin
  42|         if (!aresetn) begin
  43|             r <= 0; g <= 0; b <= 0;
  44|         end else if (fifo_write) begin
  45|             r <= {s_axis_tdata[15:11], 3'b0}; // 5-bit to 8-bit
  46|             g <= {s_axis_tdata[10:5],  2'b0}; // 6-bit to 8-bit
  47|             b <= {s_axis_tdata[4:0],   3'b0}; // 5-bit to 8-bit
  48|         end
  49|     end
  50| 
  51|     // -----------------------------
  52|     // RGB to YCbCr Conversion
  53|     // -----------------------------
  54|     wire [7:0] y_calc  = (( 77 * r + 150 * g +  29 * b) >> 8) + 16;
  55|     wire [7:0] cb_calc = ((-43 * r - 85 * g + 128 * b) >> 8) + 128;
  56|     wire [7:0] cr_calc = ((128 * r - 107 * g - 21 * b) >> 8) + 128;
  57| 
  58|     reg [7:0] y_reg, cb_reg, cr_reg;
  59|     always @(posedge aclk) begin
  60|         if (!aresetn) begin
  61|             y_reg <= 0; cb_reg <= 0; cr_reg <= 0;
  62|         end else if (fifo_write) begin
  63|             y_reg  <= y_calc;
  64|             cb_reg <= cb_calc;
  65|             cr_reg <= cr_calc;
  66|         end
  67|     end
  68| 
  69|     // -----------------------------
  70|     // FIFO Buffer Write
  71|     // -----------------------------
  72|     always @(posedge aclk) begin
  73|         if (!aresetn) begin
  74|             write_ptr <= 0;
  75|             full <= 0;
  76|         end else if (fifo_write) begin
  77|             fifo_data[write_ptr] <= {y_reg[7:3], cb_reg[7:2], cr_reg[7:3]}; // Store YCbCr in buffer
  78|             fifo_tlast[write_ptr] <= s_axis_tlast;
  79|             fifo_tuser[write_ptr] <= s_axis_tuser;
  80|             write_ptr <= write_ptr + 1;
  81|             full <= (write_ptr == FIFO_DEPTH-1);
  82|         end
  83|     end
  84| 
  85|     // -----------------------------
  86|     // FIFO Buffer Read
  87|     // -----------------------------
  88|     always @(posedge aclk) begin
  89|         if (!aresetn) begin
  90|             read_ptr <= 0;
  91|             //empty <= 1;
  92|         end else if (fifo_read) begin
  93|             read_ptr <= read_ptr + 1;
  94|         end
  95|     end
  96|     assign empty = (read_ptr == write_ptr);
  97| 
  98|     // -----------------------------
  99|     // AXI-Stream Output Signals
 100|     // -----------------------------
 101|     assign s_axis_tready = !full; // Only accept data when FIFO is not full
 102|     assign m_axis_tvalid = !empty; // Only transmit when FIFO has data
 103|     assign m_axis_tdata  = fifo_data[read_ptr];
 104|     assign m_axis_tlast  = fifo_tlast[read_ptr];
 105|     assign m_axis_tuser  = fifo_tuser[read_ptr];
 106| 
 107| endmodule
```

## Files you must patch
rtl/axis_rgb2ycbcr.sv

Primary module: `axis_rgb2ycbcr`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=Mismatch greater than 1 at 0: Expected BA73, Got 0000
- cocotb: expected=? actual=Mismatch greater than 1 at 0: Expected E42C, Got 0000
- cocotb: expected=? actual=Mismatch greater than 1 at 0: Expected 7B55, Got 0000
- cocotb: expected=? actual=Mismatch greater than 1 at 0: Expected 34CF, Got 0000
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.3.2, pluggy-1.6.0 -- /venv/bin/python
cachedir: /code/rundir/.cache
rootdir: /src
collecting ... collected 4 items

../../src/test_runner.py::test_runner Running simulation with IMG_WIDTH=4, IMG_HEIGHT=3

-------------------------------- live log call ---------------------------------
INFO     Icarus:runner.py:632 Running command iverilog -o /code/rundir/sim_build/sim.vvp -s axis_rgb2ycbcr -g2012 -DSIMULATION=1 -f /code/rundir/sim_build/cmds.f /code/rtl/axis_rgb2ycbcr.sv in directory /code/rundir/sim_build
INFO     Icarus:runner.py:632 Running command vvp -M /venv/lib/python3.12/site-packages/cocotb/libs -m libcocotbvpi_icarus /code/rundir/sim_build/sim.vvp +IMG_WIDTH=4 +IMG_HEIGHT=3 -fst in directory /code/rundir/sim_build
     -.--ns INFO     gpi                                ..mbed/gpi_embed.cpp:93   in _embed_init_python              Using Python 3.12.4 interpreter at /venv/bin/python
     -.--ns INFO     gpi                                ../gpi/GpiCommon.cpp:79   in gpi_print_registered_impl       VPI registered
     0.00ns INFO     cocotb                             Running on Icarus Verilog version 13.0 (stable)
     0.00ns INFO     cocotb                             Seeding Python random module with 1782016301
     0.00ns INFO     cocotb                             Initialized cocotb v2.0.1 from /venv/lib/python3.12/site-packages/cocotb
     0.00ns INFO     cocotb                             Running tests
     0.00ns INFO     cocotb.regression                  running axis_rgb2ycbcr_tester.test_axis_rgb2ycbcr (1/1)
                                                            Top-Level Test
write pointer: 0000; Read pointer: 0000; fifo data: XXXXXXXXXXXXXXXX
Pixel 0 (value 56651) sent successfully
    65.00ns WARNING  py.warnings                        /src/axis_rgb2ycbcr_tester.py:111: DeprecationWarning: `str(handle)` casts have been deprecated. Use `str(handle.value)` instead.
                                                          print(f"Received Pixel {len(received_pixels)-1}: {pixel:04X}, Expected: {expected_pixels[len(received_pixels)-1]:04X}, Valid Bit: {dut.m_axis_tvalid}")
Received Pixel 0: 0000, Expected: BA73, Valid Bit: 1
diff : 47731
    65.00ns WARNING  cocotb.Task 3.verify_output_stream Mismatch greater than 1 at 0: Expected BA73, Got 0000
                                                        assert 47731 <= 1
                                                         +  where 47731 = abs((0 - 47731))
                                                        Traceback (most recent call last):
                                                          File "/src/axis_rgb2ycbcr_tester.py", line 118, in verify_output_stream
                                                            assert abs(pixel - expected_pixel) <= 1, f"Mismatch greater than 1 at {len(received_pixels)-1}: Expected {expected_pixel:04X}, Got {pixel:04X}"
                                                        AssertionError: Mismatch greater than 1 at 0: Expected BA73, Got 0000
                                                        assert 47731 <= 1
                                                         +  where 47731 = abs((0 - 47731))
    65.00ns WARNING  cocotb.regression                  axis_rgb2ycbcr_tester.test_axis_rgb2ycbcr failed
    65.00ns INFO     cocotb.regression                  ***************************************************************************************************
                                                        ** TEST                                       STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        ***************************************************************************************************
                                

[... truncated 49836 chars from end of harness output ...]
```

## Cocotb test excerpt
(not available)

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/axis_rgb2ycbcr.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
