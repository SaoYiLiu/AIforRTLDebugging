Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_cdc_pulse_synchronizer_0004

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
The `cdc_pulse_synchronizer` module synchronizes a single pulse from a source clock domain (`src_clock`) to a single pulse in the destination clock domain (`des_clock`). However, during testing with a **source clock frequency of 100 MHz** and a **destination clock frequency of 250 MHz**, it was found that the module exhibited an unexpected behavior. Instead of generating a single pulse in the destination clock domain, it generated two pulses for a single pulse in the source clock domain.

Identify and Fix the RTL Bug to ensure that only a single pulse is generated in the destination clock domain for each pulse in the source clock domain.

**Test Case Details:**
- **Source Clock Frequency (`src_clock`):** 100 MHz
- **Destination Clock Frequency (`des_clock`):** 250 MHz
- **Input:** A single pulse on `src_pulse`
- **Expected Output:** A single pulse on `des_pulse`
- **Actual Output:** Two pulses on `des_pulse`

### Waveform for CDC pulse synchronization (src_clock frequency: 100MHz, des_clock frequency: 250MHz):

```wavedrom
{
  "signal": [
    {"name": "src_clock", "wave": "0.1.0.1.0.1.0.1.0.1"},
    {"name": "des_clock", "wave": "0101010101010101010"},
    {"name": "rst_in", "wave": "10................."},
    {"name": "src_pulse", "wave": "0.1...0............"},
    {"name": "des_pulse(Expected)", "wave": "0......1.0........."},
    {"name": "des_pulse(RTL Bug)", "wave": "0......1.0...1.0..."}
  ],
  "config": {
    "hscale": 1
  },
  "head": {
    "text": "Functionality with src_clock = 100MHz, des_clock = 250MHz"
  }
}
```

## Current candidate files (line-numbered on patch targets)
### rtl/cdc_pulse_synchronizer.sv
```verilog
1| module cdc_pulse_synchronizer (
   2|     input  logic src_clock,   // Source Clock Domain
   3|     input  logic des_clock,   // Destination Clock Domain
   4|     input  logic rst_in,      // Reset
   5|     input  logic src_pulse,   // Source Pulse
   6|     output logic des_pulse    // Destination Pulse
   7| );
   8| 
   9|     logic pls_toggle;      
  10|     logic pls_toggle_synca;
  11|     logic pls_toggle_syncc;
  12| 
  13|     //--------------------------------------------------
  14|     //   Toggle Flop Circuit
  15|     //---------------------------------------------------
  16| 
  17|     always_ff @(posedge src_clock or posedge rst_in) begin
  18|         if (rst_in) begin
  19|             pls_toggle <= 1'b0;
  20|         end else if (src_pulse) begin
  21|             pls_toggle <= ~pls_toggle;
  22|         end else begin
  23|             pls_toggle <= 1'b0;
  24|         end
  25|     end
  26| 
  27|     //--------------------------------------------------
  28|     //   Double Flop Bit Synchronizer
  29|     //---------------------------------------------------
  30| 
  31|     always_ff @(posedge des_clock or posedge rst_in) begin
  32|         if (rst_in) begin
  33|             pls_toggle_synca <= 1'b0;
  34|         end else begin
  35|             pls_toggle_synca <= pls_toggle;
  36|         end
  37|     end
  38| 
  39|     //--------------------------------------------------
  40|     //   Delay Logic of Output signal
  41|     //---------------------------------------------------
  42| 
  43|     always_ff @(posedge des_clock or posedge rst_in) begin
  44|         if (rst_in) begin
  45|             pls_toggle_syncc <= 1'b0;
  46|         end else begin
  47|             pls_toggle_syncc <= pls_toggle_synca;
  48|         end
  49|     end
  50| 
  51|     //--------------------------------------------------
  52|     //   Assign Statement for posedge and negedge detection
  53|     //---------------------------------------------------
  54| 
  55|     assign des_pulse = pls_toggle_syncc ^ pls_toggle_synca; 
  56| endmodule
```

## Files you must patch
rtl/cdc_pulse_synchronizer.sv

Primary module: `cdc_pulse_synchronizer`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=des_pulse was not received within 4 des_clock cycles
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
497.00ns INFO     cocotb.regression                  running test_cdc_pulse_synchronizer.test_random_clocks_and_reset (6/11)
   498.00ns INFO     cocotb.cdc_pulse_synchronizer      Iteration 1: Selected src_clock frequency: 90.91 MHz
   498.00ns INFO     cocotb.cdc_pulse_synchronizer      Iteration 1: Selected des_clock frequency: 71.43 MHz
   568.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 0
   582.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 1
   638.00ns INFO     cocotb.cdc_pulse_synchronizer      Iteration 2: Selected src_clock frequency: 125.00 MHz
   638.00ns INFO     cocotb.cdc_pulse_synchronizer      Iteration 2: Selected des_clock frequency: 62.50 MHz
   694.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 0
   702.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 1
   764.00ns INFO     cocotb.cdc_pulse_synchronizer      Iteration 3: Selected src_clock frequency: 50.00 MHz
   764.00ns INFO     cocotb.cdc_pulse_synchronizer      Iteration 3: Selected des_clock frequency: 52.63 MHz
   830.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 0
   834.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 0
   840.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 0
   846.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 0
   859.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 0
   859.00ns WARNING  ..set.test_random_clocks_and_reset des_pulse was not received within 4 des_clock cycles
                                                        assert False
                                                        Traceback (most recent call last):
                                                          File "/src/test_cdc_pulse_synchronizer.py", line 96, in test_random_clocks_and_reset
                                                            await run_test(dut)
                                                          File "/src/test_cdc_pulse_synchronizer.py", line 37, in run_test
                                                            assert des_pulse_received, "des_pulse was not received within 4 des_clock cycles"
                                                        AssertionError: des_pulse was not received within 4 des_clock cycles
                                                        assert False
   859.00ns WARNING  cocotb.regression                  test_cdc_pulse_synchronizer.test_random_clocks_and_reset failed

8147.00ns INFO     cocotb.regression                  running test_cdc_pulse_synchronizer.test_src_100MHz_des_1MHz (11/11)
  9148.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 0
 10148.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 0
 11148.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 0
 12148.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 0
 13148.00ns INFO     cocotb.cdc_pulse_synchronizer      des_pulse = 0
 13148.00ns WARNING  ..es_1MHz.test_src_100MHz_des_1MHz des_pulse was not received within 4 des_clock cycles
                                                        assert False
                                                        Traceback (most recent call last):
                                                          File "/src/test_cdc_pulse_synchronizer.py", line 173, in test_src_100MHz_des_1MHz
                                                            await run_test(dut)
                                                          File "/src/test_cdc_pulse_synchronizer.py", line 37, in run_test
                                                            assert des_pulse_received, "des_pulse was not received within 4 des_clock cycles"
                                                        AssertionError: des_pulse was not received within 4 des_clock cycles
                                                        assert False
 13148.00ns W

[... truncated 18789 chars from end of harness output ...]
```

## Cocotb test excerpt
### test_cdc_pulse_synchronizer.py
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import random

# Initialize DUT
async def init_dut(dut):
    dut.rst_in.value = 1
    dut.src_pulse.value = 0
    await RisingEdge(dut.src_clock)
    await RisingEdge(dut.src_clock)
    await RisingEdge(dut.src_clock)
    await RisingEdge(dut.src_clock)

# Test Case Run: src_pulse toggles and observe des_pulse
async def run_test(dut):
    await RisingEdge(dut.src_clock)
    dut.rst_in.value = 0

    # Toggle src_pulse once
    for _ in range(1):
        await 

[... truncated 2849 chars from cocotb test excerpt ...]

 to frequency in MHz

        dut._log.info(f"Iteration {iteration + 1}: Selected src_clock frequency: {src_frequency:.2f} MHz")
        dut._log.info(f"Iteration {iteration + 1}: Selected des_clock frequency: {des_frequency:.2f} MHz")

        cocotb.start_soon(Clock(dut.src_clock, src_period, unit='ns', period_high=(src_period+1)//2 if src_period%2 else src_period//2).start())
        cocotb.start_soon(Clock(dut.des_clock, des_period, unit='ns', period_high=(des_period+1)//2 if des_period%2 else des_period//2).start())
        await init_dut(dut)
        await run_test(dut)
        await
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/cdc_pulse_synchronizer.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
