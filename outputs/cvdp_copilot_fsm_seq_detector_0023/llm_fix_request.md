Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_fsm_seq_detector_0023

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
The `fsm_seq_detector` module is designed to detect the sequence `01001110` in a continuous bit stream provided on `seq_in` from MSB to LSB. However, during testing, it was observed that the module fails to detect the sequence when it is present in the input stream. This results in the `seq_detected` signal not asserting HIGH as expected.

#### Test Case Details:
- **Input Sequence**: `1101001110100111000` from MSB to LSB.
- **Expected Output**: The `seq_detected` signal should assert HIGH **twice**, once for each sequence `01001110` occurrence in the input. 
- **Actual Output**: The `seq_detected` signal remains LOW, indicating that the sequence was undetected in both occurrences.

#### Waveform for given Test Case:
```wavedrom
{
  "signal": [
    {"name": "clk_in", "wave": "010101010101010101010101010101010101010"},
    {"name": "rst_in", "wave": "10....................................."},
    {"name": "seq_in", "wave": "01...0.1.0...1.....0.1.0...1.....0....."},
    {"name": "seq_detected(Expected)", "wave": "0....................1.0...........1.0."},
    {"name": "seq_detected(RTL Bug)", "wave": "0......................................"}
  ],
  "config": {
    "hscale": 1
  },
  "head": {
    "text": "Teast Case with Sequence Input: 1101001110100111000"
  }
}
```
Identify and fix the RTL bug to ensure the `fsm_seq_detector` module correctly detects the sequence `01001110` and asserts `seq_detected` HIGH for one clock cycle when the sequence is detected.

## Current candidate files (line-numbered on patch targets)
### rtl/fsm_seq_detector.sv
```verilog
1| module fsm_seq_detector
   2| (
   3|     input  bit     clk_in,       // Free Running Clock
   4|     input  logic   rst_in,       // Active HIGH reset
   5|     input  logic   seq_in,       // Continuous 1-bit Sequence Input
   6|     output logic   seq_detected  // '0': Not Detected. '1': Detected. Will be HIGH for 1 Clock cycle Only
   7| );
   8| 
   9| typedef enum logic [2:0] {S0, S1, S2, S3, S4, S5, S6, S7} state_t;
  10| state_t cur_state, next_state;
  11| 
  12| logic seq_detected_w;
  13| 
  14| always @ (posedge clk_in or posedge rst_in)
  15| begin
  16|     if (rst_in)
  17|         cur_state <= S0;
  18|     else
  19|         cur_state <= next_state;
  20| end
  21| 
  22| always_comb begin
  23|     if (rst_in) begin
  24|         seq_detected_w = 1'b0;
  25|         next_state = S0;
  26|     end
  27|     else begin
  28|         case (cur_state)
  29|             S0: begin
  30|                 if (seq_in) begin
  31|                     next_state = S1;
  32|                     seq_detected_w = 1'b0;
  33|                 end
  34|                 else begin
  35|                     seq_detected_w = 1'b0;
  36|                     next_state = S0;
  37|                 end	
  38|             end
  39|             S1: begin
  40|                 if (seq_in) begin
  41|                     next_state = S1;
  42|                     seq_detected_w = 1'b0;
  43|                 end
  44|                 else begin
  45|                     next_state = S2;
  46|                     seq_detected_w = 1'b0;
  47|                 end
  48|             end
  49|             S2: begin
  50|                 if (seq_in) begin
  51|                     next_state = S3;
  52|                     seq_detected_w = 1'b0;
  53|                 end
  54|                 else begin
  55|                     next_state = S0;
  56|                     seq_detected_w = 1'b0;
  57|                 end
  58|             end
  59|             S3: begin
  60|                 if (seq_in) begin
  61|                     next_state = S4;
  62|                     seq_detected_w = 1'b0;
  63|                 end
  64|                 else begin
  65|                     next_state = S2;
  66|                     seq_detected_w = 1'b0;
  67|                 end
  68|             end
  69|             S4: begin
  70|                 if (seq_in) begin
  71|                     next_state = S1;
  72|                     seq_detected_w = 1'b0;
  73|                 end
  74|                 else begin
  75|                     next_state = S5;
  76|                     seq_detected_w = 1'b0;
  77|                 end
  78|             end
  79|             S5: begin
  80|                 if (seq_in) begin
  81|                     next_state = S3;
  82|                     seq_detected_w = 1'b0;
  83|                 end
  84|                 else begin
  85|                     next_state = S6;
  86|                     seq_detected_w = 1'b0;
  87|                 end
  88|             end
  89|             S6: begin
  90|                 if (seq_in) begin
  91|                     next_state = S1;
  92|                     seq_detected_w = 1'b0;
  93|                 end
  94|                 else begin
  95|                     next_state = S7;
  96|                     seq_detected_w = 1'b0;
  97|                 end
  98|             end
  99|             S7: begin
 100|                 if (seq_in) begin
 101|                     next_state = S1;
 102|                     seq_detected_w = 1'b1;
 103|                 end
 104|                 else begin
 105|                     next_state = S0;
 106|                     seq_detected_w = 1'b0;
 107|                 end
 108|             end
 109|             default: begin
 110|                 next_state = S0;
 111|                 seq_detected_w = 1'b0;
 112|             end
 113|         endcase
 114|     end
 115| end
 116| 
 117| always @ (posedge clk_in or posedge rst_in)
 118| begin
 119|     if (rst_in)
 120|         seq_detected <= 1'b0;
 121|     else
 122|         seq_detected <= seq_detected_w;
 123| end
 124| 
 125| endmodule
```

## Files you must patch
rtl/fsm_seq_detector.sv

Primary module: `fsm_seq_detector`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=Error at step 8
- cocotb: expected=? actual=Error at step 14
- cocotb: expected=? actual=Error at step 10
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
145.00ns INFO     cocotb.regression                  running test_fsm_seq_det.test_detection_at_start (2/6)
   186.00ns INFO     cocotb.fsm_seq_detector            Input: 1, Decoded Output: 0, test_sequence: 0
   196.00ns INFO     cocotb.fsm_seq_detector            Input: 0, Decoded Output: 0, test_sequence: 1
   206.00ns INFO     cocotb.fsm_seq_detector            Input: 1, Decoded Output: 0, test_sequence: 0
   216.00ns INFO     cocotb.fsm_seq_detector            Input: 0, Decoded Output: 0, test_sequence: 0
   226.00ns INFO     cocotb.fsm_seq_detector            Input: 0, Decoded Output: 0, test_sequence: 1
   236.00ns INFO     cocotb.fsm_seq_detector            Input: 1, Decoded Output: 0, test_sequence: 1
   246.00ns INFO     cocotb.fsm_seq_detector            Input: 1, Decoded Output: 0, test_sequence: 1
   256.00ns INFO     cocotb.fsm_seq_detector            Input: 1, Decoded Output: 0, test_sequence: 0
   266.00ns INFO     cocotb.fsm_seq_detector            Input: 0, Decoded Output: 0, test_sequence: 1
   271.00ns WARNING  ..at_start.test_detection_at_start Error at step 8
                                                        assert Logic('0') == 1
                                                         +  where Logic('0') = LogicObject(fsm_seq_detector.seq_detected).value
                                                         +    where LogicObject(fsm_seq_detector.seq_detected) = HierarchyObject(fsm_seq_detector).seq_detected
                                                        Traceback (most recent call last):
                                                          File "/src/test_fsm_seq_det.py", line 64, in test_detection_at_start
                                                            assert dut.seq_detected.value == expected_output[i], f"Error at step {i}"
                                                        AssertionError: Error at step 8
                                                        assert Logic('0') == 1
                                                         +  where Logic('0') = LogicObject(fsm_seq_detector.seq_detected).value
                                                         +    where LogicObject(fsm_seq_detector.seq_detected) = HierarchyObject(fsm_seq_detector).seq_detected
   271.00ns WARNING  cocotb.regression                  test_fsm_seq_det.test_detection_at_start failed

437.00ns INFO     cocotb.regression                  running test_fsm_seq_det.test_multiple_occurrences (4/6)
   478.00ns INFO     cocotb.fsm_seq_detector            Input: 1, Decoded Output: 0, test_sequence: 0
   488.00ns INFO     cocotb.fsm_seq_detector            Input: 0, Decoded Output: 0, test_sequence: 1
   498.00ns INFO     cocotb.fsm_seq_detector            Input: 1, Decoded Output: 0, test_sequence: 0
   508.00ns INFO     cocotb.fsm_seq_detector            Input: 0, Decoded Output: 0, test_sequence: 0
   518.00ns INFO     cocotb.fsm_seq_detector            Input: 0, Decoded Output: 0, test_sequence: 1
   528.00ns INFO     cocotb.fsm_seq_detector            Input: 1, Decoded Output: 0, test_sequence: 1
   538.00ns INFO     cocotb.fsm_seq_detector            Input: 1, Decoded Output: 0, test_sequence: 1
   548.00ns INFO     cocotb.fsm_seq_detector            Input: 1, Decoded Output: 0, test_sequence: 0
   558.00ns INFO     cocotb.fsm_seq_detector            Input: 0, Decoded Output: 0, test_sequence: 0
   563.00ns WARNING  ..rences.test_multiple_occurrences Error at step 8
                                                        assert Logic('0') == 1
                                                         +  where Logic('0') = LogicObject(fsm_seq_detector.seq_detected).value
                                                         +    where LogicObject(fsm_seq_detector.seq_detected) = HierarchyObject(fsm_seq_detector).seq_detected
                                                        Traceback (most 

[... truncated 27802 chars from end of harness output ...]
```

## Cocotb test excerpt
### test_fsm_seq_det.py
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ClockCycles, Timer
import test_runner
import json
import os


async def init_dut(dut):
    dut.rst_in.value     = 1
    dut.seq_in.value    = 1

    await RisingEdge(dut.clk_in)

@cocotb.test()
async def test_reset(dut):
    cocotb.start_soon(Clock(dut.clk_in, 10, unit='ns').start())
    await init_dut(dut)

    # Retrieve test_sequence and expected_output from environment variables
    test_sequence = [0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0]  # Sequence at the start
   

[... truncated 2838 chars from cocotb test excerpt ...]

ut.seq_detected.value}, test_sequence: {test_sequence[i]}")
        await FallingEdge(dut.clk_in)
        assert dut.seq_detected.value == expected_output[i], f"Error at step {i}"

@cocotb.test()
async def test_multiple_occurrences(dut):
    cocotb.start_soon(Clock(dut.clk_in, 10, unit='ns').start())
    await init_dut(dut)

    # Retrieve test_sequence and expected_output from environment variables
    test_sequence = [0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0]
    expected_output = [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1]  # Two detections
    # -----------------------
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/fsm_seq_detector.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
