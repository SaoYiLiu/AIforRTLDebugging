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
  27| logic [NBW_DATA-1:0] image_buffer_snapshot [NS_ROW][NS_COLUMN];
  28| logic [NBW_DATA-1:0] buffer_view [NS_ROW][NS_COLUMN];
  29| logic [NBW_DATA-1:0] row_image [NS_COLUMN];
  30| logic [NBW_DATA-1:0] window [NS_R_OUT][NS_C_OUT];
  31| logic [NBW_DATA*NS_R_OUT*NS_C_OUT-1:0] image_window_ff;
  32| 
  33| // ----------------------------------------
  34| // - Buffer view for window extraction
  35| // ----------------------------------------
  36| always_comb begin
  37|     for (int row = 0; row < NS_ROW; row++) begin
  38|         for (int col = 0; col < NS_COLUMN; col++) begin
  39|             if (i_valid && i_update_window)
  40|                 buffer_view[row][col] = image_buffer_snapshot[row][col];
  41|             else
  42|                 buffer_view[row][col] = image_buffer_ff[row][col];
  43|         end
  44|     end
  45| end
  46| 
  47| // ----------------------------------------
  48| // - Output generation
  49| // ----------------------------------------
  50| always_comb begin : window_assignment
  51|     for (int row = 0; row < NS_R_OUT; row++) begin
  52|         for (int col = 0; col < NS_C_OUT; col++) begin
  53|             int src_row;
  54|             int src_col;
  55|             int row_dist;
  56|             int col_dist;
  57| 
  58|             src_row = i_image_row_start + row;
  59|             src_col = i_image_col_start + col;
  60| 
  61|             case (i_mode)
  62|                 3'd0: begin // NO_BOUND_PROCESS
  63|                     if (src_row >= NS_ROW || src_col >= NS_COLUMN)
  64|                         window[row][col] = 0;
  65|                     else
  66|                         window[row][col] = buffer_view[src_row][src_col];
  67|                 end
  68|                 3'd1: begin // PAD_CONSTANT
  69|                     if (src_row >= NS_ROW || src_col >= NS_COLUMN)
  70|                         window[row][col] = CONSTANT;
  71|                     else
  72|                         window[row][col] = buffer_view[src_row][src_col];
  73|                 end
  74|                 3'd2: begin // EXTEND_NEAR
  75|                     if (src_row >= NS_ROW)
  76|                         src_row = NS_ROW - 1;
  77|                     if (src_col >= NS_COLUMN)
  78|                         src_col = NS_COLUMN - 1;
  79|                     window[row][col] = buffer_view[src_row][src_col];
  80|                 end
  81|                 3'd3: begin // MIRROR_BOUND
  82|                     if (src_row >= NS_ROW) begin
  83|                         row_dist = src_row - (NS_ROW - 1);
  84|                         if (row_dist < (NS_ROW - 1))
  85|                             src_row = (NS_ROW - 1) - row_dist;
  86|                         else
  87|                             src_row = 2 * (NS_ROW - 1) - row_dist;
  88|                     end
  89|                     if (src_col >= NS_COLUMN) begin
  90|                         col_dist = src_col - (NS_COLUMN - 1);
  91|                         if (col_dist < (NS_COLUMN - 1))
  92|                             src_col = (NS_COLUMN - 1) - col_dist;
  93|                         else
  94|                             src_col = 2 * (NS_COLUMN - 1) - col_dist;
  95|                     end
  96|                     window[row][col] = buffer_view[src_row][src_col];
  97|                 end
  98|                 3'd4: begin // WRAP_AROUND
  99|                     if (src_row >= NS_ROW)
 100|                         src_row = src_row - NS_ROW;
 101|                     if (src_col >= NS_COLUMN)
 102|                         src_col = src_col - NS_COLUMN;
 103|                     window[row][col] = buffer_view[src_row][src_col];
 104|                 end
 105|                 default: begin
 106|                     window[row][col] = 0;
 107|                 end
 108|             endcase
 109|         end
 110|     end
 111| end
 112| 
 113| // ----------------------------------------
 114| // - Input control
 115| // ----------------------------------------
 116| generate
 117|     for (genvar col = 0; col < NS_COLUMN; col++) begin : unpack_row_image
 118|         assign row_image[NS_COLUMN-col-1] = i_row_image[(col+1)*NBW_DATA-1-:NBW_DATA];
 119|     end
 120| endgenerate
 121| 
 122| always_ff @(posedge clk or negedge rst_async_n) begin : ctrl_regs
 123|     if(~rst_async_n) begin
 124|         image_window_ff <= 0;
 125|         for (int row = 0; row < NS_ROW; row++) begin
 126|             for (int col = 0; col < NS_COLUMN; col++) begin
 127|                 image_buffer_ff[row][col] <= 0;
 128|                 image_buffer_snapshot[row][col] <= 0;
 129|             end
 130|         end
 131|     end else begin
 132|         if(i_valid) begin
 133|             for (int row = 0; row < NS_ROW; row++) begin
 134|                 for (int col = 0; col < NS_COLUMN; col++) begin
 135|                     image_buffer_snapshot[row][col] <= image_buffer_ff[row][col];
 136|                 end
 137|             end
 138| 
 139|             for (int col = 0; col < NS_COLUMN; col++) begin
 140|                 image_buffer_ff[0][col] <= row_image[col];
 141|             end
 142| 
 143|             for (int row = 1; row < NS_ROW; row++) begin
 144|                 for (int col = 0; col < NS_COLUMN; col++) begin
 145|                     image_buffer_ff[row][col] <= image_buffer_ff[row-1][col];
 146|                 end
 147|             end
 148|         end
 149| 
 150|         if(i_update_window) begin
 151|             image_window_ff <= o_image_window;
 152|         end
 153|     end
 154| end
 155| 
 156| // ----------------------------------------
 157| // - Output packing
 158| // ----------------------------------------
 159| generate
 160|     for(genvar row = 0; row < NS_R_OUT; row++) begin : out_row
 161|         for(genvar col = 0; col < NS_C_OUT; col++) begin : out_col
 162|             always_comb begin
 163|                 if(i_update_window) begin
 164|                     o_image_window[(row*NS_C_OUT+col+1)*NBW_DATA-1-:NBW_DATA] = window[row][col];
 165|                 end else begin
 166|                     o_image_window[(row*NS_C_OUT+col+1)*NBW_DATA-1-:NBW_DATA] = image_window_ff[(row*NS_C_OUT+col+1)*NBW_DATA-1-:NBW_DATA];
 167|                 end
 168|             end
 169|         end
 170|     end
 171| endgenerate
 172| 
 173| endmodule : line_buffer
```

## Files you must patch
rtl/line_buffer.sv

Primary module: `line_buffer`

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

## Previous iteration rationale (prioritize this)
- **Root cause (ordering):** Cocotb applies `model.update_inputs()` **before** `model.add_line()` on each rising edge. When `i_valid` and `i_update_window` are both 1, the reference model extracts the window from the **pre-shift** buffer, but the DUT `always_comb` `window_assignment` reads `image_buffer_ff` **after** the NBA buffer update (lines 115–124), producing wrong pixels (e.g. `0xff00ff33` vs `0xff00ff00` in a both-high scenario).
- **Harness evidence:** Failures like `0x61d8aa0fa234000000000000 != 0xfa234000000000000000000` show the DUT carrying stale/extra non-zero data in upper window bytes while the model expects mostly zeros — consistent with reading the buffer one shift too late, not with wrong packing or reset.
- **Minimal fix:** Add `image_buffer_snapshot` (lines 106–131) captured from `image_buffer_ff` **before** the shift when `i_valid` is asserted. Mux in `window_assignment`: use `image_buffer_snapshot` when `i_valid && i_update_window`, else `image_buffer_ff`.
- **Window indexing and border handling are correct** in the current candidate (lines 42–88): `src_row = i_image_row_start + row`, independent row/column clamp/wrap/mirror — cycle 5 of the spec table (`0xff00ff0e`) reproduces correctly with proper buffer state and indexing.
- **Output hold unchanged:** `image_window_ff` capture (line 127–128) and generate mux (lines 136–148) remain correct; only the comb window source is fixed for the simultaneous-valid case.
- **Input unpack unchanged** (lines 100–104): verified to place `0xa6484d` as `[0xa6, 0x48, 0x4d]` per spec.

## Raw CVDP harness output excerpt
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
                                                            assert dut_window == model_window,  f"[ERROR] DUT o_window does not match model o_window: {hex(dut_window)} != {hex(model_window)}"
                                                        AssertionError: [ERROR] DUT o_window does not match model o_window: 0x6133d81eaa570fa9a2863457000000000000000000000000 != 0xfa9a2863457000000000000000000000000000000000000
                                                        assert 238339876897242645...8090873023753093120 == 384046721494139751...7001521850143473664
   170.00ns WARNING  cocotb.regression                  test_line_buffer.test_line_buffer failed
   170.00ns INFO     cocotb.regression                  *******************************************************************************************
                                                        ** TEST                               STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        *******************************************************************************************
                                                        ** test_line_buffer.test_line_buffer   FAIL         170.00           0.02       7910.71  **
                                                        *******************************************************************************************
                                                        ** TESTS=1 PASS=0 FAIL=1 SKIP=0                     170.00           0.03       4870.17  **
                                                        *******************************************************************************************
[DEBUG] Parameters: {'NBW_DATA': 16, 'NS_ROW': 10, 'NS_COLUMN': 8, 'NS_R_OUT': 4, 'NS_C_OUT': 3, 'CONSTANT': 255, 'NBW_ROW': 4, 'NBW_COL': 3, 'NBW_MODE': 3}
FAILED
../../src/test_runner.py::test_data[255-3-4-8-9-8]      -.--ns INFO     gpi                                ..mbed/gpi_embed.cpp:93   in _embed_init_python              Using Python 3.12.4 interpreter at /venv/bin/python
     -.--ns INFO     gpi                                ../gpi/GpiCommon.cpp:79   in gpi_print_registered_impl       VPI registered
     0.00ns INFO     cocotb                             Running on Icarus Verilog version 13.0 (stable)
     0.00ns INFO     cocotb                             Seeding Python random module with 1782021943
     0.00ns INFO     cocotb                             Initialized cocotb v2.0.1 from /venv/lib/python3.12/site-packages/cocotb
     0.00ns INFO     cocotb                             Running tests
     0.00ns INFO     cocotb.regression                  running test_line_buffer.test_line_buffer (1/1)
                                                            Test the Line Buffer module with edge cases and random data.
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create $ivl_for_loo

[... truncated 954786 chars from end of harness output ...]
```

## Local iverilog debug (generated testbench)

compile_rc=3 run_rc=None passed=False

### iverilog/vvp stderr
```text
/mnt/c/Users/user/Desktop/AIfordebugging/outputs/cvdp_copilot_line_buffer_0003/debug/tb_debug_iter_4.sv:100: syntax error
/mnt/c/Users/user/Desktop/AIfordebugging/outputs/cvdp_copilot_line_buffer_0003/debug/tb_debug_iter_4.sv:252: warning: extra digits given for sized hex constant.
/mnt/c/Users/user/Desktop/AIfordebugging/outputs/cvdp_copilot_line_buffer_0003/debug/tb_debug_iter_4.sv:252: warning: Numeric constant truncated to 64 bits.
/mnt/c/Users/user/Desktop/AIfordebugging/outputs/cvdp_copilot_line_buffer_0003/debug/tb_debug_iter_4.sv:272: syntax error
/mnt/c/Users/user/Desktop/AIfordebugging/outputs/cvdp_copilot_line_buffer_0003/debug/tb_debug_iter_4.sv:273: error: malformed statement
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
