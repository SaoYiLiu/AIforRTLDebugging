Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_arithmetic_progression_generator_0015

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
The `arithmetic_progression_generator` module is designed to generate an arithmetic sequence based on the input parameters (`start_val`, `step_size`) and the specified number of terms (`SEQUENCE_LENGTH`). However, when `SEQUENCE_LENGTH` is set to `0`, the module fails to handle this edge case appropriately. This results in a **math domain error** when attempting to compute the logarithm of zero (`$clog2(0)`), causing the simulation or synthesis process to fail.

#### **Test Case Details**:
- **Input Parameters**:
  - `SEQUENCE_LENGTH = 0`
  - `start_val = 16'b0` (default after reset)
  - `step_size = 16'b0` (default after reset)
- **Expected Behavior**:
  - The module should **not generate any sequence** when `SEQUENCE_LENGTH = 0`.
  - The `out_val` output should remain in its **initial state**, which is `0` after reset.
  - The `done` flag should **never assert**, as there is no sequence to complete.
  - **No runtime errors** should occur, and the module should avoid invalid calculations.
- **Actual Behavior**:
  - The module attempts to calculate `$clog2(0)` to determine the counter width.
  - This results in a **math domain error**, and the simulation or synthesis process fails.

#### **Expected Output**:
For `SEQUENCE_LENGTH = 0`, the behavior of the module should be as follows:
- `out_val` remains in its reset state, which is `0`.
- `done` should not assert and stay at `0` throughout the operation.

- **Current Bug**:
  - The `arithmetic_progression_generator` module doesn't handle the edge case where `SEQUENCE_LENGTH = 0`, resulting in a **math domain error** when calculating `$clog2(0)`.

#### **Test Case Behavior (Expected After Fix)**:
- **Input**:
  - `SEQUENCE_LENGTH = 0`
  - `start_val = any random value`
  - `step_size = any random value`
- **Expected Output**:
  - `out_val` remains at the reset value (`0`).
  - `done` flag remains `0` (not asserted).

Implementing the fix so the module will handle the edge case of `SEQUENCE_LENGTH = 0` without errors, ensuring that `out_val` remains at its reset value and the `done` flag does not assert unexpectedly. This change prevents runtime issues and guarantees stable output behavior for all valid sequence lengths, including `0`.

## Current candidate files (line-numbered on patch targets)
### rtl/arithmetic_progression_generator.sv
```verilog
1| module arithmetic_progression_generator #(
   2|     parameter DATA_WIDTH = 16,  // Width of the input data
   3|     parameter SEQUENCE_LENGTH = 10 // Number of terms in the progression
   4| )(
   5|     clk,
   6|     resetn,
   7|     enable,
   8|     start_val,
   9|     step_size,
  10|     out_val,
  11|     done
  12| );
  13|   // ----------------------------------------
  14|   // - Local parameter definition
  15|   // ----------------------------------------
  16| 
  17|     localparam WIDTH_OUT_VAL = $clog2(SEQUENCE_LENGTH) + DATA_WIDTH; // Bit width of out_val to prevent overflow
  18| 
  19|   // ----------------------------------------
  20|   // - Interface Definitions
  21|   // ----------------------------------------
  22|     input logic clk;                          // Clock signal
  23|     input logic resetn;                       // Active-low reset
  24|     input logic enable;                       // Enable signal for the generator
  25|     input logic [DATA_WIDTH-1:0] start_val;   // Start value of the sequence
  26|     input logic [DATA_WIDTH-1:0] step_size;   // Step size of the sequence
  27|     output logic [WIDTH_OUT_VAL-1:0] out_val; // Current value of the sequence
  28|     output logic done;                        // High when sequence generation is complete
  29| 
  30| 
  31|   // ----------------------------------------
  32|   // - Internal signals
  33|   // ----------------------------------------
  34|     logic [WIDTH_OUT_VAL-1:0] current_val;  // Register to hold the current value
  35|     logic [$clog2(SEQUENCE_LENGTH)-1:0] counter;  // Counter to track sequence length
  36| 
  37|   // ----------------------------------------
  38|   // - Procedural block
  39|   // ----------------------------------------
  40|     always_ff @(posedge clk or negedge resetn) begin
  41|         if (!resetn) begin
  42|             current_val <= 0;
  43|             counter <= 0;
  44|             done <= 1'b0;
  45|         end else if (enable) begin
  46|             if (!done) begin
  47|                 if (counter == 0) begin
  48|                     current_val <= start_val; // Initialize with start value
  49|                 end else begin
  50|                     current_val <= current_val + step_size; // Compute next term
  51|                 end
  52| 
  53|                 if (counter < SEQUENCE_LENGTH - 1) begin
  54|                     counter <= counter + 1; // Increment counter
  55|                 end else begin
  56|                     done <= 1'b1; // Mark completion
  57|                 end
  58|             end
  59|         end
  60|     end
  61| 
  62|   // ----------------------------------------
  63|   // - Combinational Assignments
  64|   // ----------------------------------------
  65|     assign out_val = current_val;
  66| 
  67| endmodule
```

## Files you must patch
rtl/arithmetic_progression_generator.sv

Primary module: `arithmetic_progression_generator`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=Wrong calculation of WIDTH_OUT_VAL
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
0.00ns INFO     cocotb.regression                  running test_arithmetic_progression_generator.test_arithmetic_progression_generator (1/1)
[INFO] Clock started.
DATA_WIDTH= 19, SEQUENCE_LENGTH= 1, WIDTH_OUT_VAL=19 
Overflow check !
WIDTH_OUT_VAL = 19, EXPECTED_WIDTH_OUT_VAL = 20
    50.00ns WARNING  ..arithmetic_progression_generator Wrong calculation of WIDTH_OUT_VAL
                                                        assert 19 == 20
                                                        Traceback (most recent call last):
                                                          File "/src/test_arithmetic_progression_generator.py", line 158, in test_arithmetic_progression_generator
                                                            assert WIDTH_OUT_VAL == EXPECTED_WIDTH_OUT_VAL, "Wrong calculation of WIDTH_OUT_VAL"
                                                        AssertionError: Wrong calculation of WIDTH_OUT_VAL
                                                        assert 19 == 20
    50.00ns WARNING  cocotb.regression                  test_arithmetic_progression_generator.test_arithmetic_progression_generator failed
    50.00ns INFO     cocotb.regression                  *************************************************************************************************************************************
                                                        ** TEST                                                                         STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        *************************************************************************************************************************************
                                                        ** test_arithmetic_progression_generator.test_arithmetic_progression_generator   FAIL          50.00           0.01       5939.59  **
                                                        *************************************************************************************************************************************
                                                        ** TESTS=1 PASS=0 FAIL=1 SKIP=0                                                                50.00           0.02       2199.43  **
                                                        *************************************************************************************************************************************
[DEBUG] Running simulation with DATA_WIDTH=19, SEQUENCE_LENGTH=0
[DEBUG] Start Value: 0, Step Size: 0
[DEBUG] Parameters: {'DATA_WIDTH': 19, 'SEQUENCE_LENGTH': 0}
FAILED
../../src/test_runner.py::test_arithmetic_progression_generator[1-0-19]      -.--ns INFO     gpi                                ..mbed/gpi_embed.cpp:93   in _embed_init_python              Using Python 3.12.4 interpreter at /venv/bin/python
     -.--ns INFO     gpi                                ../gpi/GpiCommon.cpp:79   in gpi_print_registered_impl       VPI registered
     0.00ns INFO     cocotb                             Running on Icarus Verilog version 13.0 (stable)
     0.00ns INFO     cocotb                             Seeding Python random module with 1782011787
     0.00ns INFO     cocotb                             Initialized cocotb v2.0.1 from /venv/lib/python3.12/site-packages/cocotb
     0.00ns INFO     cocotb                             Running tests
     0.00ns INFO     cocotb.regression                  running test_arithmetic_progression_generator.test_arithmetic_progression_generator (1/1)
[INFO] Clock started.
DATA_WIDTH= 19, SEQUENCE_LENGTH= 1, WIDTH_OUT_VAL=19 
Overflow check !
WIDTH_OUT_VAL = 19, EXPECTED_WIDTH_OUT_VAL = 20
    50.00ns WARNING  ..arithmetic_progression_generator Wrong calculation of WIDTH_OUT_VAL
                                                        assert 19 == 20
                           

[... truncated 60442 chars from end of harness output ...]
```

## Cocotb test excerpt
### test_arithmetic_progression_generator.py
```python
# File: arithmetic_progression_generator.py

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ClockCycles, Timer
import harness_library as hrs_lb
import random
import time
import math

def clog2(N):
    return math.ceil(math.log2(N))

@cocotb.test()
async def test_arithmetic_progression_generator(dut):
     
    # Randomly execute this statement in one of the iterations
    MIN_CLOCK_PERIOD = 4
    # clock_period_ns = random.randint(MIN_CLOCK_PERIOD, 15)  # For example, 10ns clock period
   

[... truncated 2858 chars from cocotb test excerpt ...]

#################################################
        dut.resetn.value = 1
        if reset_system == 1 :
            #reset applied for N cycles after start_cycle 
            reset = 0
            if cycle >= start_cycle_reset and cycle < start_cycle_reset + N_cycles_reset  :
                reset = 1
                dut.resetn.value = 0
                print(f"Reset applied for {N_cycles_reset} cycles!")
                expected_value = 0
                expected_value_s1 = 0
                expected_value_s2 = 0
                expected_done = 0
                expected_done_s1 = 0
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/arithmetic_progression_generator.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
