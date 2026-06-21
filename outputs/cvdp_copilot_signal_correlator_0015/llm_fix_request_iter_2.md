Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_signal_correlator_0015

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
The Signal Correlator module computes a 4-bit `correlation_output` from two 8-bit inputs (`input_signal` and `reference_signal`), where each matching bit contributes a weight of **+2** to the summation, with the output clamped at `15`. However, the module exhibits incorrect behavior under certain edge cases.

Here follows the specification of the RTL.

---
1. **Correct Weighted Summation:**
   - For each matching bit between the two input signals, the correlator must add a value of `+2` to the summation.
   - The `correlation_output` must always remain within the valid 4-bit range (0-15).

2. **Reset Behavior:**
   - On reset, the correlator must initialize its internal states and outputs (e.g., `correlation_output = 0`) to ensure a predictable starting point.

3. **Edge Case Handling:**
   - The design must handle edge cases where the weighted summation exceeds the maximum value representable by a 4-bit output. In such cases, the output must clamp to the maximum value.

4. **Consistent and Reliable Output:**
   - The correlator must produce accurate and bounded outputs across all valid input conditions, including corner cases and transitions after reset.

---

### **Functional Expectations**

1. **Weighted Summation:**
   - Each matching bit between `input_signal` and `reference_signal` contributes a weight of **+2** to the summation.
   - **Example Input:** `input_signal = 0b10101010`, `reference_signal = 0b10101010`.
   - **Expected Output:** `8` (4 matching bits × 2).

2. **Reset Behavior:**
   - On reset, the correlator initializes all internal states and the `correlation_output` to `0`.
   - **Action:** Assert reset, then deassert reset.
   - **Expected Output:** `correlation_output = 0`.


---
Please provide me with an RTL code that matches the specifications.

## Current candidate files (line-numbered on patch targets)
### rtl/signal_correlator.sv
```verilog
1| module signal_correlator(
   2|     input clk,
   3|     input reset,
   4|     input [7:0] input_signal,
   5|     input [7:0] reference_signal,
   6|     output reg [3:0] correlation_output // 4-bit output
   7| );
   8| 
   9| integer i;
  10| reg [3:0] sum;  
  11| 
  12| always @(posedge clk or posedge reset) begin
  13|     if (reset) begin
  14|         correlation_output <= 0;
  15|         sum = 0;  
  16|     end else begin
  17|         sum = 0;  
  18|         for (i = 0; i < 8; i = i + 1) begin
  19|             sum = sum + (input_signal[i] & reference_signal[i]); 
  20|         end
  21|     end
  22| end
  23| 
  24| endmodule
```

## Files you must patch
rtl/signal_correlator.sv

Primary module: `signal_correlator`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=Clamping test failed: Expected 15, got 0
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
0.00ns INFO     cocotb.regression                  running test_signal_correlator.test_clamping_logic (1/1)
                                                            Test to verify that the clamping logic works correctly in signal_correlator.
    21.00ns WARNING  ..amping_logic.test_clamping_logic Clamping test failed: Expected 15, got 0
                                                        assert 0 == 15
                                                        Traceback (most recent call last):
                                                          File "/src/test_signal_correlator.py", line 33, in test_clamping_logic
                                                            assert output_value == 15, (
                                                        AssertionError: Clamping test failed: Expected 15, got 0
                                                        assert 0 == 15
    21.00ns WARNING  cocotb.regression                  test_signal_correlator.test_clamping_logic failed
    21.00ns INFO     cocotb.regression                  ****************************************************************************************************
                                                        ** TEST                                        STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        ****************************************************************************************************
                                                        ** test_signal_correlator.test_clamping_logic   FAIL          21.00           0.01       3589.55  **
                                                        ****************************************************************************************************
                                                        ** TESTS=1 PASS=0 FAIL=1 SKIP=0                               21.00           0.02       1182.97  **
                                                        ****************************************************************************************************
ERROR    Icarus:runner.py:572 ERROR: Failed 1 of 1 tests.
FAILED
../../src/test_runner.py::test_moving_run[1] 
-------------------------------- live log call ---------------------------------
INFO     Icarus:runner.py:644 Removing: /code/rundir/sim_build
INFO     Icarus:runner.py:632 Running command iverilog -o /code/rundir/sim_build/sim.vvp -s signal_correlator -g2012 -f /code/rundir/sim_build/cmds.f /code/rtl/signal_correlator.sv in directory /code/rundir/sim_build
INFO     Icarus:runner.py:632 Running command vvp -M /venv/lib/python3.12/site-packages/cocotb/libs -m libcocotbvpi_icarus /code/rundir/sim_build/sim.vvp +encoder_in=145 -fst in directory /code/rundir/sim_build
     -.--ns INFO     gpi                                ..mbed/gpi_embed.cpp:93   in _embed_init_python              Using Python 3.12.4 interpreter at /venv/bin/python
     -.--ns INFO     gpi                                ../gpi/GpiCommon.cpp:79   in gpi_print_registered_impl       VPI registered
     0.00ns INFO     cocotb                             Running on Icarus Verilog version 13.0 (stable)
     0.00ns INFO     cocotb                             Seeding Python random module with 1782017269
     0.00ns INFO     cocotb                             Initialized cocotb v2.0.1 from /venv/lib/python3.12/site-packages/cocotb
     0.00ns INFO     cocotb                             Running tests
     0.00ns INFO     cocotb.regression                  running test_signal_correlator.test_clamping_logic (1/1)
                                                            Test to verify that the clamping logic works correctly in signal_correlator.
    21.00ns WARNING  ..amping_logic.test_clamping_logic Clamping test failed: Expected 15, got 0
                                                        assert 0 == 15

[... truncated 97608 chars from end of harness output ...]
```

## Cocotb test excerpt
### test_signal_correlator.py
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_clamping_logic(dut):
    """
    Test to verify that the clamping logic works correctly in signal_correlator.
    The output should clamp to 15 if the sum exceeds the 4-bit range.
    """

    # Start the clock
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())  # 10 ns clock period

    # Reset the DUT
    dut.reset.value = 1
    dut.input_signal.value = 0
    dut.reference_signal.value = 0
    await RisingEdge(dut.clk)  #

[... truncated 78 chars from cocotb test excerpt ...]

lk)  # Allow system to stabilize

    # Test case: Input that triggers clamping
    dut.input_signal.value = 0b11111111  # All bits `1`
    dut.reference_signal.value = 0b11111111  # All bits `1`

    await RisingEdge(dut.clk)  # Wait for one clock cycle
    await Timer(1, unit="ns")  # Small delay for propagation

    # Extract output and check clamping
    output_value = int(dut.correlation_output.value)
    assert output_value == 15, (
        f"Clamping test failed: Expected 15, got {output_value}"
    )

    cocotb.log.info("Clamping logic test passed: Output correctly clamps to 15.")
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/signal_correlator.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
