Reply in the agent message only. Do not create, edit, or commit repository files.

You are helping debug RTL for a CVDP hardware verification benchmark.

**First decide** whether a local **iverilog + VCD** debug simulation would materially help
the next RTL-fix iteration. Only if yes, write a focused SystemVerilog testbench.
Do NOT modify RTL.

## Problem
cvdp_copilot_line_buffer_0003

## Harness error kind
logic

## Task description excerpt
The SystemVerilog code for `line_buffer` module extracts a window of pixel data from an image row buffer. It receives an entire image row as input and outputs a configurable window of pixel values, depending on the selected mode. The module supports different window sizes and positions using configurable parameters and input signals. It operates synchronously on the rising edge of a clock (`clk`) and includes an asynchronous active low reset (`rst_async_n`) to reset internal registers.

------

### Specifications

* **Module Name**: `line_buffer`
* **Parameters**:
   * `NBW_DATA`: Defines the bit width of the grayscale pixel data.
      * Default value: 8.
      * Must be greater than 8.
   * `NS_ROW`: Defines the total number of rows in the input image.
      * Default value: 10.
      * Must be greater than 2.
   * `NS_COLUMN`: Defines the total number of columns in the input image.
      * Default value: 8.
      * Must be greater than 2.
   * `NBW_ROW`: Defines the bit width of the `i_window_row_start` signal.
      * Default value: 4.
      * Must be `log2(NS_ROW)` rounded up.
   * `NBW_COL`: Defines the bit width of the `i_window_col_start` signal.
      * Default value: 3.
      * Must be `log2(NS_COLUMN)` rounded up.
   * `NBW_MODE`: Defines the bit width of the input mode selection signal.
      * Default value: 3.
      * Must be 3.
   * `NS_R_OUT`: Defines the number of rows in the output window.
      * Default value: 4.
      * Must be greater than 0 and less than or equal to `NS_ROW`.
   * `NS_C_OUT`: Defines the number of columns in the output window.
      * Default value: 3.
      * Must be greater than 0 and less than or equal to `NS_COLUMN`.
   * `CONSTANT`: Defines the constant value used in padding mode.
      * Default value: 255.
      * Must be within the range of `NBW_DATA`.

### Interface Signals

* **Clock** (`clk`): Synchronizes operations on its rising edge.
* **Reset** (`rst_async_n`): Active low, asynchronous reset that resets internal registers.
* **Mode Select Signal** (`i_mode`): A `NBW_MODE`-bit signal that selects the operation mode of the buffer.
* **Valid Input Signal** (`i_valid`): Active high signal, synchronous with `clk`. Indicates when the `i_row_image` input data is valid and can be processed.
* **Update Output Window Signal** (`i_update_window`): Active high signal, synchronous with `clk`. Indicates when `o_image_window` should be updated.
* **Image Row Input** (`i_row_image`): A `NBW_DATA*NS_COLUMN`-bit input representing a full row of the image.
* **Window Row Start** (`i_image_row_start`): A `NBW_ROW`-bit input that defines the starting row position of the window.
* **Window Column Start** (`i_image_col_start`): A `NBW_COL`-bit input that defines the starting column position of the window.
* **Window Output** (`o_image_window`): A `NBW_DATA*NS_R_OUT*NS_C_OUT`-bit output representing the extracted window.

### Functional Behavior

1. **Operation**
   * The module extracts a window of pixel values fro

[... truncated 2851 chars from task prompt ...]

tart`, `i_mode` and the internal line buffer register.
   * An example of its connection, where a two by two window is selected from position `0`, `0`, in any operation mode and using the internal line buffer below, would output `o_image_window` = 0x50716325.

   | 0x25  | 0x63  | 0xf0  |
   |-------|-------|-------|
   | 0x71  | 0x50  | 0x25  |
   | 0x65  | 0x5f  | 0x5f  |

# Observed Behavior

In the example below, the parameters were set to:
   * `NBW_DATA = 8`
   * `NS_ROW = 3`
   * `NS_COLUMN = 3`
   * `NS_R_OUT = 2`
   * `NS_C_OUT = 2`
   * `CONSTANT = 255`
   * `NBW_ROW = 2`
   * `NBW_COL = 2`
   * `NBW_MODE = 3`

All inputs were set after the rising edge of the clock `clk`, and after the next rising edge the `clk` the `o_image_window` was observed. The simulation started with a reset, where the internal line buffer must be set to 0, and then this output was observed:

| Cycle | `i_mode` | `i_valid` | `i_update_window` | `i_row_image` | `i_image_row_start` | `i_image_col_start` | Observed `o_image_window` | Expected `o_image_window` |
|-------|----------|-----------|-------------------|---------------|---------------------|---------------------|---------------------------|---------------------------|
| 1     | 5        | 0         | 0                 | 0x823cfd      | 1                   | 1                   | 0x0                       | 0x0                       |
| 2     | 4        | 1         | 0                 | 0x30f90e      | 1                   | 1                   | 0x0                       | 0x0                       |
| 3     | 0        | 0         | 1                 | 0x887534      | 1                   | 0                   | 0x0                       | 0x0                       |
| 4     | 4        | 0         | 0                 | 0xc36ed8      | 2                   | 0                   | 0x0                       | 0x0                       |
| 5     | 1        | 0         | 1                 | 0xfd77b0      | 0                   | 2                   | 0xffff000e                | 0xff00ff0e                |
| 6     | 5        | 1         | 1                 | 0xbd533       | 0                   | 2                   | 0x0                       | 0x0                       |
| 7     | 4        | 1         | 0                 | 0xaad861      | 1                   | 1                   | 0x0                       | 0x0                       |
| 8     | 3        | 1         | 1                 | 0x11f57c      | 2                   | 1                   | 0xe0ef9f9                 | 0xef90ef9                 |
| 9     | 0        | 0         | 1                 | 0xbf2ce0      | 2                   | 2                   | 0x33                      | 0x33                      |
| 10    | 2        | 0         | 1                 | 0xbdfa0f      | 1                   | 0                   | 0xd5d80baa                | 0xd50bd8aa                |

Identify and fix the RTL bug to ensure the correct generation of `o_image_window`.

## DUT RTL (for port/module names — do not edit)
### rtl/line_buffer.sv
```verilog
module line_buffer #(
    parameter NBW_DATA  = 'd8,  // Bit width of grayscale input/output data
    parameter NS_ROW    = 'd10, // Number of rows
    parameter NS_COLUMN = 'd8,  // Number of columns
    parameter NBW_ROW   = 'd4,  // log2(NS_ROW). Bit width of i_image_row_start
    parameter NBW_COL   = 'd3,  // log2(NS_COLUMN). Bit width of i_image_col_start
    parameter NBW_MODE  = 'd3,  // Bit width of mode input
    parameter NS_R_OUT  = 'd4,  // Number of rows of the output window
    parameter NS_C_OUT  = 'd3,  // Number of columns of the output window
    parameter CONSTANT  = 'd255 // Constant value to use in PAD_CONSTANT mode
) (
    input  logic                                  clk,
    input  logic                                  rst_async_n,
    input  logic [NBW_MODE-1:0]                   i_mode,
    input  logic                                  i_valid,
    input  logic                                  i_update_window,
    input  logic [NBW_DATA*NS_COLUMN-1:0]         i_row_image,
    input  logic [NBW_ROW-1:0]                    i_image_row_start,
    input  logic [NBW_COL-1:0]                    i_image_col_start,
    output logic [NBW_DATA*NS_R_OUT*NS_C_OUT-1:0] o_image_window
);

// ----------------------------------------
// - Wires/Registers creation
// ----------------------------------------
logic [NBW_DATA-1:0] image_buffer_ff [NS_ROW][NS_COLUMN];
logic [NBW_DATA-1:0] image_buffer_snapshot [NS_ROW][NS_COLUMN];
logic [NBW_DATA-1:0] buffer_view [NS_ROW][NS_COLUMN];
logic [NBW_DATA-1:0] row_image [NS_COLUMN];
logic [NBW_DATA-1:0] window [NS_R_OUT][NS_C_OUT];
logic [NBW_DATA*NS_R_OUT*NS_C_OUT-1:0] image_window_ff;

// ----------------------------------------
// - Buffer view for window extraction
// ----------------------------------------
always_comb begin
    for (int row = 0; row < NS_ROW; row++) begin
        for (int col = 0; col < NS_COLUMN; col++) begin
            if (i_valid && i_update_window)
                buffer_view[row][col] = image_buffer_snapshot[row][col];
            else
                buffer_view[row][col] = image_buffer_ff[row][col];
        end
    end
end

// ----------------------------------------
// - Output generation
// ----------------------------------------
always_comb begin : window_assignment
    for (int row = 0; row < NS_R_OUT; row++) begin
        for (int col = 0; col < NS_C_OUT; col++) begin
            int src_row;
            int src_col;
            int row_dist;
            int col_dist;

            src_row = i_image_row_start + row;
            src_col = i_image_col_start + col;

            case (i_mode)
                3'd0: begin // NO_BOUND_PROCESS
                    if (src_row >= NS_ROW || src_col >= NS_COLUMN)
                        window[row][col] = 0;
                    else
                        window[row][col] = buffer_view[src_row][src_col];
                end
                3'd1: begin // PAD_CONSTANT
                    if (src_row >= NS_ROW || src_col >= NS_COLUMN)
                        window[row][col] = CONSTANT;
                    else
                        window[row][col] = buffer_view[src_row][src_col];
                end
                3'd2: begin // EXTEND_NEAR
                    if (src_row >= NS_ROW)
                        src_row = NS_ROW - 1;
                    if (src_col >= NS_COLUMN)
                        src_col = NS_COLUMN - 1;
                    window[row][col] = buffer_view[src_row][src_col];
                en
```

Primary module to instantiate: `line_buffer`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0x61d8aa0fa234000000000000 != 0xfa234000000000000000000
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0x6133d81eaa570fa9a2863457000000000000000000000000 != 0xfa9a2863457000000000000000000000000000000000000
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0xa23475 != 0xa23475d8aa3d
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0xa28634577520 != 0xa28634577520d81eaa573de5
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0x34750e76b03d968bafca0f24 != 0x76b03d968bafca0f2435fc50
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0x345775200ede7634b0ff3de596c78bbbafcaca300fb72436 != 0x7634b0ff3de596c78bbbafcaca300fb724363577fc15505d
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0xd0b0f != 0xd0b0f0b94eb
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0xd070b6d0fa9 != 0xd070b6d0fa90b00945eeb51
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0xc3af2c99d16bb58d461d8aa0fa234000000000000 != 0xc99d16bb58d461d8aa0fa234000000000000000000
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0xc193a77f292c9859df71643bbf75894d4206133d81eaa570fa9a2863457000000000000000000000000 != 0xc9859df71643bbf75894d4206133d81eaa570fa9a2863457000000000000000000000000000000000000
```

## Raw CVDP harness failure excerpt
```text
## Key failure excerpts
0.00ns INFO     cocotb.regression                  running test_line_buffer.test_line_buffer (1/1)
                                                            Test the Line Buffer module with edge cases and random data.
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create $ivl_for_loop0 via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create ctrl_regs via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create window_assignment via any registered implementation
   170.00ns WARNING  ..est_line_buffer.test_line_buffer [ERROR] DUT o_window does not match model o_window: 0x61d8aa0fa234000000000000 != 0xfa234000000000000000000
                                                        assert 30281977020398447446303178752 == 4838366693154855178725228544
                                                        Traceback (most recent call last):
                                                          File "/src/test_line_buffer.py", line 104, in test_line_buffer
                                                            compare_values(dut, model)
                                                          File "/src/test_line_buffer.py", line 25, in compare_values
                                                            assert dut_window == model_window,  f"[ERROR] DUT o_window does not match model o_window: {hex(dut_window)} != {hex(model_window)}"
                                                        AssertionError: [ERROR] DUT o_window does not match model o_window: 0x61d8aa0fa234000000000000 != 0xfa234000000000000000000
                                                        assert 30281977020398447446303178752 == 4838366693154855178725228544
   170.00ns WARNING  cocotb.regression                  test_line_buffer.test_line_buffer failed
   170.00ns INFO     cocotb.regression                  *******************************************************************************************
                                                        ** TEST                               STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        *******************************************************************************************
                                                        ** test_line_buffer.test_line_buffer   FAIL         170.00           0.02       7802.59  **
                                                        *******************************************************************************************
                                                        ** TESTS=1 PASS=0 FAIL=1 SKIP=0                     170.00           0.04       4830.58  **
                                                        *******************************************************************************************
[DEBUG] Parameters: {'NBW_DATA': 8, 'NS_ROW': 10, 'NS_COLUMN': 8, 'NS_R_OUT': 4, 'NS_C_OUT': 3, 'CONSTANT': 255, 'NBW_ROW': 4, 'NBW_COL': 3, 'NBW_MODE': 3}
FAILED
../../src/test_runner.py::test_data[255-3-4-8-10-16]      -.--ns INFO     gpi                                ..mbed/gpi_embed.cpp:93   in _embed_init_python              Using Python 3.12.4 interpreter at /venv/bin/python
     -.--ns INFO     gpi                                ../gpi/GpiCommon.cpp:79   in gpi_print_registered_impl       VPI registered
     0.00ns INFO     cocotb                             Running on Icarus Verilog version 13.0 (stable)
     0.00ns INFO     cocotb                             Seeding Python random module with 1782021942
     0.00ns INFO     cocotb                             Initialized cocotb v2.0.1 from /venv/lib/python3.12/site-packages/cocotb
     0.00ns INFO     cocotb                             Running tests
     0.00ns INFO     cocotb.regression                  running test_line_buffer.test_line_buffer (1/1)
                                                            Test the Line Buffer module with edge cases and random data.
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create $ivl_for_loop0 via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create ctrl_regs via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create window_assignment via any registered implementation
   170.00ns WARNING  ..est_line_buffer.test_line_buffer [ERROR] DUT o_window does not match model o_window: 0x6133d81eaa570fa9a2863457000000000000000000000000 != 0xfa9a2863457000000000000000000000000000000000000
                                                        assert 238339876897242645...8090873023753093120 == 384046721494139751...7001521850143473664
                                                        Traceback (most recent call last):
                                                          File "/src/test_line_buffer.py", line 104, in test_line_buffer
                                                            compare_values(dut, model)
                                                          File "/src/test_line_buffer.py", line 25, in compare_values
                                          

[... truncated 957786 chars from end of harness output ...]
```

## Cocotb harness source
### test_line_buffer.py
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
import harness_library as hrs_lb
import random

def compare_values(dut, model, debug=0):
    dut_window  = int(dut.o_image_window.value)

    model_window = model.get_o_window_flat()

    if debug == 1:
        print("\nINPUTS")
        print(f"i_mode = {int(dut.i_mode.value)}")
        print(f"i_valid = {int(dut.i_valid.value)}")
        print(f"i_update_window = {int(dut.i_update_window.value)}")
        print(f"i_row_image = {hex(int(dut.i_row_image.value))}")
        print(f"i_image_row_start = {int(dut.i_image_row_start.value)}")
        print(f"i_image_col_start = {int(dut.i_image_col_start.value)}")
        print("\nOUTPUTS")
        print(f"DUT o_window  = {hex(dut_window)} MODEL o_window  = {hex(model_window)}")
        #print(f"Observed o_image_window = {hex(dut_window)}")
        #print(f"Expected o_image_window = {hex(model_window)}\n")
    
    assert dut_window == model_window,  f"[ERROR] DUT o_window does not match model o_window: {hex(dut_window)} != {hex(model_window)}"

@cocotb.test()
async def test_line_buffer(dut):
    """Test the Line Buffer module with edge cases and random data."""

    cocotb.start_soon(Clock(dut.clk, 10, unit='ns').start())

    # Retrieve parameters from the DUT
    NBW_DATA  = int(dut.NBW_DATA.value)
    NS_ROW    = int(dut.NS_ROW.value)
    NS_COLUMN = int(dut.NS_COLUMN.value)
    NS_R_OUT  = int(dut.NS_R_OUT.value)
    NS_C_OUT  = int(dut.NS_C_OUT.value)
    CONSTANT  = int(dut.CONSTANT.value)

    random.seed(1)

    model = hrs_lb.LineBuffer(nbw_data=NBW_DATA, ns_row=NS_ROW, ns_col=NS_COLUMN, ns_r_out=NS_R_OUT, ns_c_out=NS_C_OUT, pad_constant=CONSTANT)

    resets = 4
    runs = 250

    data_min = int(0)
    data_max = int(2**NBW_DATA - 1)

    window_row_min = int(0)
    window_row_max = int(NS_ROW-1)

    window_col_min = int(0)
    window_col_max = int(NS_COLUMN-1)

    await hrs_lb.dut_init(dut)

    for i in range(resets):
        # Reset DUT
        # Set all inputs to 0
        dut.i_mode.value = 0
        dut.i_valid.value = 0
        dut.i_update_window.value = 0
        dut.i_row_image.value = 0
        dut.i_image_row_start.value = 0
        dut.i_image_col_start.value = 0
        dut.rst_async_n.value = 0
        await RisingEdge(dut.clk)
        dut.rst_async_n.value = 1
        await RisingEdge(dut.clk)

        # Reset model
        model.reset()

        await RisingEdge(dut.clk)

        compare_values(dut, model)

        for j in range(runs):
            valid = random.randint(0,1)
            update_window = random.randint(0,1)
            image_row = 0
            for k in range(NS_COLUMN):
                data = random.randint(data_min, data_max)
                image_row = (image_row << NBW_DATA) | data
            window_row = random.randint(window_row_min, window_row_max)
            window_col = random.randint(window_col_min, window_col_max)
            mode = random.randint(0,5)

            dut.i_mode.value = mode
            dut.i_valid.value = valid
            dut.i_update_window.value = update_window
            dut.i_row_image.value = image_row
            dut.i_image_row_start.value = window_row
            dut.i_image_col_start.value = window_col


            await RisingEdge(dut.clk)
            if update_window:
                model.update_inputs(window_row, window_col, mode)
            if valid:
                model.add_line(image_row)
            compare_values(dut, model)
```

## When to answer **use: no** (skip debug sim)
- Elaboration/synthesis/parameter errors (e.g. `$clog2(0)`); harness log already pinpoints the bug.
- Docker/cocotb compile or import failures that iverilog will not reproduce better.
- Failure is already a single clear expected-vs-actual on outputs; no benefit from waves.
- Design is too complex for a faithful mini-TB (wide buses, AXI, many files, DPI/UVM).
- Prior iterations already show the fix direction without waveform evidence.

## When to answer **use: yes** (write DebugTestbench)
- Functional logic bug with reproducible vectors but unclear **internal** root cause.
- Multi-cycle/FSM behavior where cocotb only reports final output mismatch.
- You can mirror the **specific failing cocotb case** in iverilog-friendly SV.

## Output format

## DebugSimDecision
use: yes | no

## Rationale
3-6 bullets explaining your decision (required for both yes and no).

## DebugTestbench
(Include ONLY when use: yes — otherwise omit this section entirely.)
```verilog
module tb_debug;
  // $dumpfile("wave.vcd"); $dumpvars(0, tb_debug);
  // wire tb_mismatch; $display("First mismatch occurred at time %0t", $time);
  // one failing scenario from harness log
endmodule
```

Requirements when use: yes:
1. Top module name: `tb_debug`
2. Drive the **specific failing test case** (exact inputs/expected outputs).
3. `$dumpfile("wave.vcd");` and `$dumpvars(0, tb_debug);`
4. `tb_mismatch` wire + mismatch time `$display` as above.
5. iverilog-friendly Verilog only (no UVM/DPI/classes).
