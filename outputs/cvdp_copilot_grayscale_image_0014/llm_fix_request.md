Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_grayscale_image_0014

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
The `conv3x3` module contains a bug that disrupt the accuracy of the convolution operation. Leading the result in incorrect final outputs.

---

### Prompt for the `conv3x3` Module

---

### Expected Behavior:

1. **Element-wise Multiplication (Stage 1):**
   - Each element of the input image data should be multiplied by the corresponding kernel element to produce intermediate results.

2. **Row-wise Summation (Stage 2):**
   - Each row of the kernel and input image data must fully contribute to the convolution result.
   - The summation for each row should include all relevant multiplication results without omission.

3. **Final Summation (Stage 3):**
   - The results of all row-wise summations must be combined accurately to calculate the total convolution sum.

4. **Normalization (Stage 4):**
   - The total convolution sum should be normalized by dividing it by the correct number of elements in the kernel.
   - For a 3x3 kernel, this ensures proper scaling.

5. **Output Accuracy:**
   - The final output must be an accurate and normalized representation of the convolution operation, considering all contributions from the kernel and input image data. Boundary conditions should be handled appropriately. 

---

Provide me with one RTL version that fixes this issue.

## Current candidate files (line-numbered on patch targets)
### rtl/conv3x3.sv
```verilog
1| module conv3x3 (
   2|     input logic          clk,               // Clock signal
   3|     input logic          rst_n,             // Reset signal, active low
   4|     input logic  [7:0]   image_data0,       // Individual pixel data inputs (8-bit each)
   5|     input logic  [7:0]   image_data1,
   6|     input logic  [7:0]   image_data2,
   7|     input logic  [7:0]   image_data3,
   8|     input logic  [7:0]   image_data4,
   9|     input logic  [7:0]   image_data5,
  10|     input logic  [7:0]   image_data6,
  11|     input logic  [7:0]   image_data7,
  12|     input logic  [7:0]   image_data8,
  13|     input logic  [7:0]   kernel0,           // Individual kernel inputs (8-bit each)
  14|     input logic  [7:0]   kernel1,
  15|     input logic  [7:0]   kernel2,
  16|     input logic  [7:0]   kernel3,
  17|     input logic  [7:0]   kernel4,
  18|     input logic  [7:0]   kernel5,
  19|     input logic  [7:0]   kernel6,
  20|     input logic  [7:0]   kernel7,
  21|     input logic  [7:0]   kernel8,
  22|     output logic [15:0]  convolved_data     // 16-bit convolved output
  23| );
  24| 
  25|     // Stage 1: Element-wise multiplication results
  26|     logic [15:0] mult_result0, mult_result1, mult_result2;
  27|     logic [15:0] mult_result3, mult_result4, mult_result5;
  28|     logic [15:0] mult_result6, mult_result7, mult_result8;
  29| 
  30|     // Stage 2: Row-wise partial sums
  31|     logic [19:0] pipeline_sum_stage10, pipeline_sum_stage11, pipeline_sum_stage12;
  32| 
  33|     // Stage 3: Final total sum
  34|     logic [19:0] sum_result;
  35| 
  36|     // Stage 4: Normalized result
  37|     logic [15:0] normalized_result;
  38| 
  39|     // Stage 1: Element-wise multiplications
  40|     always_ff @(posedge clk or negedge rst_n) begin
  41|         if (!rst_n) begin
  42|             mult_result0 <= 0; mult_result1 <= 0; mult_result2 <= 0;
  43|             mult_result3 <= 0; mult_result4 <= 0; mult_result5 <= 0;
  44|             mult_result6 <= 0; mult_result7 <= 0; mult_result8 <= 0;
  45|         end else begin
  46|             mult_result0 <= image_data0 * kernel0;
  47|             mult_result1 <= image_data1 * kernel1;
  48|             mult_result2 <= image_data2 * kernel2;
  49|             mult_result3 <= image_data3 * kernel3;
  50|             mult_result4 <= image_data4 * kernel4;
  51|             mult_result5 <= image_data5 * kernel5;
  52|             mult_result6 <= image_data6 * kernel6;
  53|             mult_result7 <= image_data7 * kernel7;
  54|             mult_result8 <= image_data8 * kernel8;
  55|         end
  56|     end
  57| 
  58|     // Stage 2: Row-wise summation
  59|     always_ff @(posedge clk or negedge rst_n) begin
  60|         if (!rst_n) begin
  61|             pipeline_sum_stage10 <= 0;
  62|             pipeline_sum_stage11 <= 0;
  63|             pipeline_sum_stage12 <= 0;
  64|         end else begin
  65|             pipeline_sum_stage10 <= mult_result0 + mult_result1 + mult_result2;
  66|             pipeline_sum_stage11 <= mult_result3 + mult_result4; 
  67|             pipeline_sum_stage12 <= mult_result6 + mult_result7 + mult_result8;
  68|         end
  69|     end
  70| 
  71|     // Stage 3: Total summation
  72|     always_ff @(posedge clk or negedge rst_n) begin
  73|         if (!rst_n) begin
  74|             sum_result <= 0;
  75|         end else begin
  76|             sum_result <= pipeline_sum_stage10 + pipeline_sum_stage11 + pipeline_sum_stage12;
  77|         end
  78|     end
  79| 
  80|     // Stage 4: Normalization
  81|     always_ff @(posedge clk or negedge rst_n) begin
  82|         if (!rst_n) begin
  83|             convolved_data <= 0;
  84|         end else begin
  85|             convolved_data <= sum_result / 8; // Normalization
  86|         end
  87|     end
  88| 
  89| endmodule
```

## Files you must patch
rtl/conv3x3.sv

Primary module: `conv3x3`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=Error in Row 2 summation!
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
0.00ns INFO     cocotb.regression                  running test_conv3x3.test_bug_detection (1/1)
                                                            Test the conv3x3 module for bug detection.
   120.00ns WARNING  ..bug_detection.test_bug_detection Error in Row 2 summation!
                                                        assert 2 == 3
                                                         +  where 2 = int(LogicArray('00000000000000000010', Range(19, 'downto', 0)))
                                                         +    where LogicArray('00000000000000000010', Range(19, 'downto', 0)) = LogicArrayObject(conv3x3.pipeline_sum_stage11).value
                                                         +      where LogicArrayObject(conv3x3.pipeline_sum_stage11) = HierarchyObject(conv3x3).pipeline_sum_stage11
                                                        Traceback (most recent call last):
                                                          File "/src/test_conv3x3.py", line 55, in test_bug_detection
                                                            assert int(dut.pipeline_sum_stage11.value) == expected_pipeline_sum_stage11, "Error in Row 2 summation!"
                                                        AssertionError: Error in Row 2 summation!
                                                        assert 2 == 3
                                                         +  where 2 = int(LogicArray('00000000000000000010', Range(19, 'downto', 0)))
                                                         +    where LogicArray('00000000000000000010', Range(19, 'downto', 0)) = LogicArrayObject(conv3x3.pipeline_sum_stage11).value
                                                         +      where LogicArrayObject(conv3x3.pipeline_sum_stage11) = HierarchyObject(conv3x3).pipeline_sum_stage11
   120.00ns WARNING  cocotb.regression                  test_conv3x3.test_bug_detection failed
   120.00ns INFO     cocotb.regression                  *****************************************************************************************
                                                        ** TEST                             STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        *****************************************************************************************
                                                        ** test_conv3x3.test_bug_detection   FAIL         120.00           0.01      12867.94  **
                                                        *****************************************************************************************
                                                        ** TESTS=1 PASS=0 FAIL=1 SKIP=0                   120.00           0.02       5425.66  **
                                                        *****************************************************************************************
ERROR    Icarus:runner.py:572 ERROR: Failed 1 of 1 tests.
FAILED

=================================== FAILURES ===================================
_________________________________ test_runner __________________________________

    def test_runner():
    
        runner = get_runner(sim)
        runner.build(
            sources=verilog_sources,
            hdl_toplevel=toplevel,
            # Arguments
            always=True,
            clean=True,
            verbose=True,
            timescale=("1ns", "1ns"),
            log_file="build.log")
    
>       runner.test(hdl_toplevel=toplevel, test_module=module, waves=True)
E       SystemExit: 1

/src/test_runner.py:27: SystemExit
------------------------------ Captured log call -------------------------------
INFO     Icarus:runner.py:632 Running command iverilog -o /code/rundir/sim_build/sim.vvp -s conv3x3 -g2012 -f /code/rundir/sim_build/cmds.f /code/rtl/conv3x3.sv in direct

[... truncated 9540 chars from end of harness output ...]
```

## Cocotb test excerpt
### test_conv3x3.py
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

@cocotb.test()
async def test_bug_detection(dut):
    """Test the conv3x3 module for bug detection."""

    # Generate clock
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # Reset the design
    dut.rst_n.value = 0
    await Timer(20, unit="ns")
    dut.rst_n.value = 1

    # Initialize inputs
    dut.image_data0.value = 1
    dut.image_data1.value = 1
    dut.image_data2.value = 1
    dut.image_data3.value = 1
    dut.image_data4.value = 1
 

[... truncated 877 chars from cocotb test excerpt ...]

 summations
    assert int(dut.pipeline_sum_stage10.value) == expected_pipeline_sum_stage10, "Error in Row 1 summation!"
    assert int(dut.pipeline_sum_stage11.value) == expected_pipeline_sum_stage11, "Error in Row 2 summation!"
    assert int(dut.pipeline_sum_stage12.value) == expected_pipeline_sum_stage12, "Error in Row 3 summation!"

    # Check total sum
    assert int(dut.sum_result.value) == expected_total_sum, "Error in total summation!"

    # Check normalization
    assert int(dut.convolved_data.value) == expected_convolved_data, "Error in normalization: Division should be by 9!"
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/conv3x3.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
