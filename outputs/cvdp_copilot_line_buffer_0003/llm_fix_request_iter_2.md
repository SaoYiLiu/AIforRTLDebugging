Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_line_buffer_0003

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

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
   * The module extracts a window of pixel values from the internal line buffer.
   * The window size and position are defined by `NS_R_OUT`, `NS_C_OUT`, `i_image_row_start`, and `i_image_col_start`.
   * The extracted window is output on `o_image_window`. This happens asynchronously.
   * The internal line buffer adds a row when an `i_valid` signal is asserted. All rows from the buffer are shifted down, the last row is discarded and the first row becomes the input row from `i_row_image`. This happens synchronously.

2. **Row Storing**
   * When an `i_valid` signal is asserted, the internal line buffer will be updated on the next rising edge of the `clk`. As an example, with `NBW_DATA = 8`, `NS_ROW = 3`, `NS_COLUMN = 3`, `i_row_image = 0xa6484d`, and the starting internal line buffer reset with all zeroes, the expected internal line buffer after the rising edge of the clock `clk` is shown below. Where the data stored in line `0`, column `0` is equal to 0xa6.

   | 0xa6  | 0x48  | 0x4d  |
   |-------|-------|-------|
   | 0x00  | 0x00  | 0x00  |
   | 0x00  | 0x00  | 0x00  |


3. **Modes of Operation** (Selected via `i_mode`):
   * All operation modes, when within range of the internal line buffer, will output the window by starting in the top left of the (i_image_row_start, i_image_col_start) position, where the first value is the row selection and the second value is the column selection. From that point, going to the right and down, a window with `NS_R_OUT` rows and `NS_C_OUT` columns is selected. The operation modes differ in the border handling, where either, or both, is true: (`i_image_row_start` + `NS_R_OUT` >= `NS_ROW`) or (`i_image_col_start` + `NS_C_OUT` >= `NS_COLUMN`).
   * `i_mode == 3'b000`: Any selection out of range will be outputted as `0`.
   * `i_mode == 3'b001`: Any selection out of range will be outputted as `CONSTANT`.
   * `i_mode == 3'b010`: Any selection out of range will be outputted as its closest value.
   * `i_mode == 3'b011`: Any selection out of range will be the mirrored position, that is, in the example of section 2's (Row Storing) functional behavior, if the `NS_R_OUT = 1`, `NS_C_OUT = 3`, `i_update_window = 1`, `i_image_row_start = 0` and `i_image_col_start = 2`, the output `o_image_window` must be 0x484d4d.
   * `i_mode == 3'b100`: Any selection out of range will be wrapped around the line buffer. Using the same example from `i_mode == 3'b011`, with the same inputs and parameters, the output `o_image_window` must be 0x48a64d.
   * `i_mode == 3'b101` to `i_mode == 3'b111`: Invalid modes, `o_image_window` must always be `0`.

4. **Output Connection**
   * The output is asynchronously asserted when `i_update_window` is asserted and can't change when `i_update_window` is set to `0`.
   * The output is changed when `i_update_window` is 1, and the window is selected according to the inputs `i_image_row_start`, `i_image_col_start`, `i_mode` and the internal line buffer register.
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

## Current candidate files (line-numbered on patch targets)
### rtl/line_buffer.sv
```verilog
1| module line_buffer #(
   2|     parameter NBW_DATA  = 'd8,  // Bit width of grayscale input/output data
   3|     parameter NS_ROW    = 'd10, // Number of rows
   4|     parameter NS_COLUMN = 'd8,  // Number of columns
   5|     parameter NBW_ROW   = 'd4,  // log2(NS_ROW). Bit width of i_image_row_start
   6|     parameter NBW_COL   = 'd3,  // log2(NS_COLUMN). Bit width of i_image_col_start
   7|     parameter NBW_MODE  = 'd3,  // Bit width of mode input
   8|     parameter NS_R_OUT  = 'd4,  // Number of rows of the output window
   9|     parameter NS_C_OUT  = 'd3,  // Number of columns of the output window
  10|     parameter CONSTANT  = 'd255 // Constant value to use in PAD_CONSTANT mode
  11| ) (
  12|     input  logic                                  clk,
  13|     input  logic                                  rst_async_n,
  14|     input  logic [NBW_MODE-1:0]                   i_mode,
  15|     input  logic                                  i_valid,
  16|     input  logic                                  i_update_window,
  17|     input  logic [NBW_DATA*NS_COLUMN-1:0]         i_row_image,
  18|     input  logic [NBW_ROW-1:0]                    i_image_row_start,
  19|     input  logic [NBW_COL-1:0]                    i_image_col_start,
  20|     output logic [NBW_DATA*NS_R_OUT*NS_C_OUT-1:0] o_image_window
  21| );
  22| 
  23| // ----------------------------------------
  24| // - Wires/Registers creation
  25| // ----------------------------------------
  26| logic [NBW_DATA-1:0] image_buffer_ff [NS_ROW][NS_COLUMN];
  27| logic [NBW_DATA-1:0] row_image [NS_COLUMN];
  28| logic [NBW_DATA-1:0] window [NS_R_OUT][NS_C_OUT];
  29| logic [NBW_DATA*NS_R_OUT*NS_C_OUT-1:0] image_window_ff;
  30| 
  31| // ----------------------------------------
  32| // - Output generation
  33| // ----------------------------------------
  34| always_comb begin : window_assignment
  35|     case(i_mode)
  36|         3'd0: begin // NO_BOUND_PROCESS
  37|             for (int row = 0; row < NS_R_OUT; row++) begin
  38|                 for (int col = 0; col < NS_C_OUT; col++) begin
  39|                     if(i_image_row_start + col >= NS_ROW) begin
  40|                         window[row][col] = 0;
  41|                     end else if (i_image_col_start + row >= NS_COLUMN) begin
  42|                         window[row][col] = 0;
  43|                     end else begin
  44|                         window[row][col] = image_buffer_ff[i_image_row_start + col][i_image_col_start + row];
  45|                     end
  46|                 end
  47|             end
  48|         end
  49|         3'd1: begin // PAD_CONSTANT
  50|             for (int row = 0; row < NS_R_OUT; row++) begin
  51|                 for (int col = 0; col < NS_C_OUT; col++) begin
  52|                     if(i_image_row_start + col >= NS_ROW) begin
  53|                         window[row][col] = CONSTANT;
  54|                     end else if (i_image_col_start + row >= NS_COLUMN) begin
  55|                         window[row][col] = CONSTANT;
  56|                     end else begin
  57|                         window[row][col] = image_buffer_ff[i_image_row_start + col][i_image_col_start + row];
  58|                     end
  59|                 end
  60|             end
  61|         end
  62|         3'd2: begin // EXTEND_NEAR
  63|             for (int row = 0; row < NS_R_OUT; row++) begin
  64|                 for (int col = 0; col < NS_C_OUT; col++) begin
  65|                     if(i_image_row_start + col >= NS_ROW) begin
  66|                         window[row][col] = image_buffer_ff[NS_ROW-1][i_image_col_start + row];
  67|                     end else if (i_image_col_start + row >= NS_COLUMN) begin
  68|                         window[row][col] = image_buffer_ff[i_image_row_start + col][NS_COLUMN-1];
  69|                     end else begin
  70|                         window[row][col] = image_buffer_ff[i_image_row_start + col][i_image_col_start + row];
  71|                     end
  72|                 end
  73|             end
  74|         end
  75|         3'd3: begin // MIRROR_BOUND
  76|             for (int row = 0; row < NS_R_OUT; row++) begin
  77|                 for (int col = 0; col < NS_C_OUT; col++) begin
  78|                     if(i_image_row_start + col >= NS_ROW) begin
  79|                         window[row][col] = image_buffer_ff[2*NS_ROW-1-(i_image_row_start + col)][i_image_col_start + row];
  80|                     end else if (i_image_col_start + row >= NS_COLUMN) begin
  81|                         window[row][col] = image_buffer_ff[i_image_row_start + col][NS_COLUMN-1-(i_image_col_start + row)];
  82|                     end else begin
  83|                         window[row][col] = image_buffer_ff[i_image_row_start + col][i_image_col_start + row];
  84|                     end
  85|                 end
  86|             end
  87|         end
  88|         3'd4: begin // WRAP_AROUND
  89|             for (int row = 0; row < NS_R_OUT; row++) begin
  90|                 for (int col = 0; col < NS_C_OUT; col++) begin
  91|                     if(i_image_row_start + col >= NS_ROW) begin
  92|                         window[row][col] = image_buffer_ff[(i_image_row_start + col)-NS_ROW][i_image_col_start + row];
  93|                     end else if (i_image_col_start + row >= NS_COLUMN) begin
  94|                         window[row][col] = image_buffer_ff[i_image_row_start + col][(i_image_col_start + row)-NS_COLUMN];
  95|                     end else begin
  96|                         window[row][col] = image_buffer_ff[i_image_row_start + col][i_image_col_start + row];
  97|                     end
  98|                 end
  99|             end
 100|         end
 101|         default: begin
 102|             for (int row = 0; row < NS_R_OUT; row++) begin
 103|                 for (int col = 0; col < NS_C_OUT; col++) begin
 104|                     window[row][col] = 0;
 105|                 end
 106|             end
 107|         end
 108|     endcase
 109| end
 110| 
 111| // ----------------------------------------
 112| // - Input control
 113| // ----------------------------------------
 114| generate
 115|     for (genvar col = 0; col < NS_COLUMN; col++) begin : unpack_row_image
 116|         assign row_image[NS_COLUMN-col-1] = i_row_image[(col+1)*NBW_DATA-1-:NBW_DATA];
 117|     end
 118| endgenerate
 119| 
 120| always_ff @(posedge clk or negedge rst_async_n) begin : ctrl_regs
 121|     if(~rst_async_n) begin
 122|         image_window_ff <= 0;
 123|         for (int row = 0; row < NS_ROW; row++) begin
 124|             for (int col = 0; col < NS_COLUMN; col++) begin
 125|                 image_buffer_ff[row][col] <= 0;
 126|             end
 127|         end
 128|     end else begin
 129|         if(i_valid) begin
 130|             for (int col = 0; col < NS_COLUMN; col++) begin
 131|                 image_buffer_ff[0][col] <= row_image[col];
 132|             end
 133| 
 134|             for (int row = 1; row < NS_ROW; row++) begin
 135|                 for (int col = 0; col < NS_COLUMN; col++) begin
 136|                     image_buffer_ff[row][col] <= image_buffer_ff[row-1][col];
 137|                 end
 138|             end
 139|         end
 140| 
 141|         if(i_update_window) begin
 142|             image_window_ff <= o_image_window;
 143|         end
 144|     end
 145| end
 146| 
 147| // ----------------------------------------
 148| // - Output packing
 149| // ----------------------------------------
 150| generate
 151|     for(genvar row = 0; row < NS_R_OUT; row++) begin : out_row
 152|         for(genvar col = 0; col < NS_C_OUT; col++) begin : out_col
 153|             always_comb begin
 154|                 if(i_update_window) begin
 155|                     o_image_window[(row*NS_C_OUT+col+1)*NBW_DATA-1-:NBW_DATA] = window[row][col];
 156|                 end else begin
 157|                     o_image_window[(row*NS_C_OUT+col+1)*NBW_DATA-1-:NBW_DATA] = image_window_ff[(row*NS_C_OUT+col+1)*NBW_DATA-1-:NBW_DATA];
 158|                 end
 159|             end
 160|         end
 161|     end
 162| endgenerate
 163| 
 164| endmodule : line_buffer
```

## Files you must patch
rtl/line_buffer.sv

Primary module: `line_buffer`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0xffffffffffff000000000000 != 0xff0000ff0000ff0000ff0000
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0x7fbfdfeff7fbfc0000000000000 != 0x7f80000ff00001fe00003fc0000
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0xffffffffffffffffffff0000 != 0xffffffffffffffff00ffff00
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0x7fbfdfeff7fbfdfeff7fbfc0000 != 0x7fbfdfeff7fbfdfeff003fdfe00
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0x55d00056140044a4002b3500 != 0x186c4056442b14a435000000
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0x5568000ad14001114800158d400 != 0x1836500ad441585148350000000
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0xffffff000000000000 != 0xff0000ff0000ff0000
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0xff7fbfc0000000000000 != 0xff00001fe00003fc0000
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0xffffffffffffff0000 != 0xffffffffff00ffff00
- cocotb: expected=? actual=[ERROR] DUT o_window does not match model o_window: 0xff7fbfdfeff7fbfc0000 != 0xff7fbfdfeff003fdfe00
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
0.00ns INFO     cocotb.regression                  running test_line_buffer.test_line_buffer (1/1)
                                                            Test the Line Buffer module with edge cases and random data.
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create ctrl_regs via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create window_assignment via any registered implementation
   130.00ns WARNING  ..est_line_buffer.test_line_buffer [ERROR] DUT o_window does not match model o_window: 0xffffffffffff000000000000 != 0xff0000ff0000ff0000ff0000
                                                        assert 79228162514264056118567239680 == 78918682208363011696236625920
                                                        Traceback (most recent call last):
                                                          File "/src/test_line_buffer.py", line 104, in test_line_buffer
                                                            compare_values(dut, model)
                                                          File "/src/test_line_buffer.py", line 25, in compare_values
                                                            assert dut_window == model_window,  f"[ERROR] DUT o_window does not match model o_window: {hex(dut_window)} != {hex(model_window)}"
                                                        AssertionError: [ERROR] DUT o_window does not match model o_window: 0xffffffffffff000000000000 != 0xff0000ff0000ff0000ff0000
                                                        assert 79228162514264056118567239680 == 78918682208363011696236625920
   130.00ns WARNING  cocotb.regression                  test_line_buffer.test_line_buffer failed
   130.00ns INFO     cocotb.regression                  *******************************************************************************************
                                                        ** TEST                               STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        *******************************************************************************************
                                                        ** test_line_buffer.test_line_buffer   FAIL         130.00           0.01      11095.59  **
                                                        *******************************************************************************************
                                                        ** TESTS=1 PASS=0 FAIL=1 SKIP=0                     130.00           0.03       5088.18  **
                                                        *******************************************************************************************
[DEBUG] Parameters: {'NBW_DATA': 8, 'NS_ROW': 15, 'NS_COLUMN': 8, 'NS_R_OUT': 4, 'NS_C_OUT': 3, 'CONSTANT': 255, 'NBW_ROW': 4, 'NBW_COL': 3, 'NBW_MODE': 3}
FAILED
../../src/test_runner.py::test_data[255-3_0-4-8-15-9]      -.--ns INFO     gpi                                ..mbed/gpi_embed.cpp:93   in _embed_init_python              Using Python 3.12.4 interpreter at /venv/bin/python
     -.--ns INFO     gpi                                ../gpi/GpiCommon.cpp:79   in gpi_print_registered_impl       VPI registered
     0.00ns INFO     cocotb                             Running on Icarus Verilog version 13.0 (stable)
     0.00ns INFO     cocotb                             Seeding Python random module with 1782021363
     0.00ns INFO     cocotb                             Initialized cocotb v2.0.1 from /venv/lib/python3.12/site-packages/cocotb
     0.00ns INFO     cocotb                             Running tests
     0.00ns INFO     cocotb.regression                  running test_line_buffer.test_line_buffer (1/1)
                                                            Test the Line Buffer module with edge cases and random data.
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create ctrl_regs via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create window_assignment via any registered implementation
   130.00ns WARNING  ..est_line_buffer.test_line_buffer [ERROR] DUT o_window does not match model o_window: 0x7fbfdfeff7fbfc0000000000000 != 0x7f80000ff00001fe00003fc0000
                                                        assert 161941743997845030794585450741760 == 161625452733302710794604137676800
                                                        Traceback (most recent call last):
                                                          File "/src/test_line_buffer.py", line 104, in test_line_buffer
                                                            compare_values(dut, model)
                                                          File "/src/test_line_buffer.py", line 25, in compare_values
                                                            assert dut_window == model_window,  f"[ERROR] DUT o_window does not match model o_window: {hex(dut_window)} != {hex(model_window)}"
                                                        AssertionError: [ERROR] DUT o_window does not match model o_window: 0x7fbfdfeff7fbfc0000000000000 != 0x7f80000ff00001fe00003fc0000
                                                        assert 161941743997845030794585450741760 == 161625452733302710794604137676800
   130.00ns WARNING  cocotb.regression                  test_line_buffer.test_line_buffer failed
   130.00ns INFO     cocotb.regression                  *******************************************************************************************
                                                        ** TEST                               STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        *******************************************************************************************
                                                        ** test_line_buffer.test_line_buffer   FAIL         130.00           0.01       9662.58  **
                                                        *******************************************************************************************
                                                        ** TESTS=1 PASS=0 FAIL=1 SKIP=0                     130.00           0.03       4972.59  **
                                                        *******************************************************************************************
[DEBUG] Parameters: {'NBW_DATA': 9, 'NS_ROW': 15, 'NS_COLUMN': 8, 'NS_R_OUT': 4, 'NS_C_OUT': 3, 'CONSTANT': 255, 'NBW_ROW': 4, 'NBW_COL': 3, 'NBW_MODE': 3}
FAILED
../../src/test_runner.py::test_data[255-3_0-4-13-10-8]      -.--ns INFO     gpi                                ..mbed/gpi_embed.cpp:93   in _embed_init_python              Using Python 3.12.4 interpreter at /venv/bin/python
     -.--ns INFO     gpi                                ../gpi/GpiCommon.cpp:79   in gpi_print_registered_impl       VPI registered
     0.00ns INFO     cocotb                             Running on Icarus Verilog version 13.0 (stable)
     0.00ns INFO     cocotb                             Seeding Python random module with 1782021364
     0.00ns INFO     cocotb                             Initialized cocotb v2.0.1 from /venv/lib/python3.12/site-packages/cocotb
     0.00ns INFO     cocotb                             Running tests
     0.00ns INFO     cocotb.regression                  running test_line_buffer.test_line_buffer (1/1)
                                                            Test the Line Buffer module with edge cases and random data.
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create ctrl_regs via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create window_assignment via any registered implementation
    70.00ns WARNING  ..est_line_buffer.test_line_buffer [ERROR] DUT o_window does not match model o_window: 0xffffffffffffffffffff0000 != 0xffffffffffffffff00ffff00
                                                        assert 79228162514264337593543884800 == 79228162514264337589265760000
         

[... truncated 884966 chars from end of harness output ...]
```

## Cocotb test excerpt
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
        print(f"i_row_image = {hex(int(dut.i_row_image.value

[... truncated 2367 chars from cocotb test excerpt ...]

ndint(window_col_min, window_col_max)
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

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/line_buffer.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
