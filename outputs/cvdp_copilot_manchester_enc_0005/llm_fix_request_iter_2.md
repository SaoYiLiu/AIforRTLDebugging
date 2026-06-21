Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_manchester_enc_0005

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
Identify and fix the latch inference issue in the provided **Manchester Encoder** module. 

---

**Specifications:**

1. **Module Name:** `manchester_encoder`

2. **Parameters:**

   - `N` (default value: 8) which defines the width of the input data bus (`enc_data_in`).

3. **Expected Behaviour of Encoding process:**
Table for Manchester Encoding (`N=3`, input data from `0` to `7`):
When `enc_valid_in` is '0', the Expected output of `enc_data_out` should be 6'b000000. But with Latch Inference, This output will become unexpected and will corrupt the communication system

| Clock Cycle | clk_in | rst_in | enc_valid_in | enc_data_in | enc_valid_out | enc_data_out (expected)   | enc_data_out (with Latch)
|-------------|--------|--------|--------------|-------------|---------------|-----------------|-----------------|
| 1           | Rising | 1      | 1            | 3'b000      | 0             | 6'b000000       | 6'b000000
| 2           | Rising | 0      | 1            | 3'b000      | 1             | 6'b101010       | 6'b101010
| 3           | Rising | 0      | 1            | 3'b001      | 1             | 6'b101001       | 6'b101001
| 4           | Rising | 0      | 1            | 3'b010      | 1             | 6'b100110       | 6'b100110
| 5           | Rising | 0      | 1            | 3'b011      | 1             | 6'b100101       | 6'b100101
| 6           | Rising | 0      | 1            | 3'b100      | 1             | 6'b011010       | 6'b011010
| 7           | Rising | 0      | 1            | 3'b101      | 1             | 6'b011001       | 6'b011001 
| 8           | Rising | 0      | 0            | 3'b110      | 0             | **6'b000000**       | **6'b011001**
| 9           | Rising | 0      | 0            | 3'b111      | 0             | **6'b000000**       | **6'b011001**

---

## Current candidate files (line-numbered on patch targets)
### rtl/manchester_encoder.sv
```verilog
1| 
   2| // Manchester encoder module
   3| module manchester_encoder #(
   4|     parameter N = 8  // Default width of input data
   5| ) (
   6|     input  logic clk_in,          // Clock input
   7|     input  logic rst_in,          // Active high reset input
   8|     input  logic enc_valid_in,        // Input valid signal
   9|     input  logic [N-1:0] enc_data_in, // N-bit input data
  10|     output logic enc_valid_out,       // Output valid signal
  11|     output logic [2*N-1:0] enc_data_out // 2N-bit output encoded data
  12| );
  13| 
  14|     // Internal register to hold the encoded data
  15|     logic [2*N-1:0] encoded_data;
  16| 
  17|     // Combinational logic to generate Manchester encoded data
  18|     always_comb begin
  19|         if (enc_valid_in) begin
  20|             for (int i = 0; i < N; i++) begin
  21|                 if (enc_data_in[i] == 1'b1) begin
  22|                     enc_data_out[2*i] = 1'b1;
  23|                     enc_data_out[2*i + 1] = 1'b0;
  24|                 end else begin
  25|                     enc_data_out[2*i] = 1'b0;
  26|                     enc_data_out[2*i + 1] = 1'b1;
  27|                 end
  28|             end
  29|             enc_valid_out = 1'b1; // Set the valid signal
  30|         end else begin
  31|             enc_valid_out = 1'b0; // Clear the valid signal if no valid input
  32|         end
  33|     end
  34| 
  35| endmodule
```

## Files you must patch
rtl/manchester_encoder.sv

Primary module: `manchester_encoder`

## Structured harness feedback
```text
error_kind: logic
```



## Raw CVDP harness output excerpt
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.3.2, pluggy-1.6.0 -- /venv/bin/python
cachedir: /code/rundir/.cache
rootdir: /src
collecting ... collected 4 items

../../src/test_runner.py::test_manchester_even[6-test_sequence0-expected_output0]

[stderr]
Network cvdp_react_cvdp_copilot_manchester_enc_0005_1_default Creating 
 Network cvdp_react_cvdp_copilot_manchester_enc_0005_1_default Created 
 Container cvdp_react_cvdp_copilot_manchester_enc_0005_1-direct-run-72dd9bc67061 Creating 
 Container cvdp_react_cvdp_copilot_manchester_enc_0005_1-direct-run-72dd9bc67061 Created 

[harness timed out after 600s]
```

## Cocotb test excerpt
### test_manchester_enc.py
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import os
import json

# Initialize DUT
async def init_dut(dut):
    dut.rst_in.value = 1
    dut.enc_valid_in.value = 0
    dut.enc_data_in.value = 0
    await Timer(10, unit='ns')

# Test: Manchester encoding and decoding
@cocotb.test()
async def test_top_manchester(dut):
    # Fetch test_sequence and expected_output from environment
    test_sequence = json.loads(os.getenv("TEST_SEQUENCE"))
    expected_output = json.loads(os.getenv("EXPECTED_OUTPUT"))

    N = int

[... truncated 89 chars from cocotb test excerpt ...]

nit_dut(dut)
    dut.rst_in.value = 0

    # Apply test_sequence and validate encoded/decoded outputs
    for i, enc_data in enumerate(test_sequence):
        await RisingEdge(dut.clk_in)
        dut.enc_valid_in.value = 1
        dut.enc_data_in.value = enc_data
        await RisingEdge(dut.clk_in)
        dut.enc_valid_in.value = 0

        await RisingEdge(dut.enc_valid_out)
        await Timer(1, unit='ns')
        
        decoded_data = dut.enc_data_out.value
        assert decoded_data == expected_output[i], f"Decoded data mismatch: expected {expected_output[i]}, got {decoded_data}"
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/manchester_encoder.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
