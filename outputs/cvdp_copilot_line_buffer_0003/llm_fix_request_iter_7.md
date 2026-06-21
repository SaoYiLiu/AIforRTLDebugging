Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_line_buffer_0003

## Error type
compile

## Fix strategy
Fix all compile/build errors before attempting logic changes. Address each harness log error.

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
  31| logic [NBW_DATA-1:0] window_capture [NS_R_OUT][NS_C_OUT];
  32| logic [NBW_DATA*NS_R_OUT*NS_C_OUT-1:0] packed_window;
  33| logic [NBW_DATA*NS_R_OUT*NS_C_OUT-1:0] packed_capture;
  34| logic [NBW_DATA*NS_R_OUT*NS_C_OUT-1:0] image_window_ff;
  35| 
  36| // ----------------------------------------
  37| // - Buffer view for live window extraction
  38| // ----------------------------------------
  39| always_comb begin
  40|     for (int row = 0; row < NS_ROW; row++) begin
  41|         for (int col = 0; col < NS_COLUMN; col++) begin
  42|             if (i_valid && i_update_window)
  43|                 buffer_view[row][col] = image_buffer_snapshot[row][col];
  44|             else
  45|                 buffer_view[row][col] = image_buffer_ff[row][col];
  46|         end
  47|     end
  48| end
  49| 
  50| // ----------------------------------------
  51| // - Window pixel helper
  52| // ----------------------------------------
  53| function automatic logic [NBW_DATA-1:0] get_window_pixel(
  54|     input logic [NBW_DATA-1:0] buf [NS_ROW][NS_COLUMN],
  55|     input int wr,
  56|     input int wc,
  57|     input logic [2:0] mode
  58| );
  59|     int src_row;
  60|     int src_col;
  61|     int row_dist;
  62|     int col_dist;
  63| 
  64|     src_row = i_image_row_start + wr;
  65|     src_col = i_image_col_start + wc;
  66| 
  67|     case (mode)
  68|         3'd0: begin
  69|             if (src_row >= NS_ROW || src_col >= NS_COLUMN)
  70|                 get_window_pixel = {NBW_DATA{1'b0}};
  71|             else
  72|                 get_window_pixel = buf[src_row][src_col];
  73|         end
  74|         3'd1: begin
  75|             if (src_row >= NS_ROW || src_col >= NS_COLUMN)
  76|                 get_window_pixel = CONSTANT;
  77|             else
  78|                 get_window_pixel = buf[src_row][src_col];
  79|         end
  80|         3'd2: begin
  81|             if (src_row >= NS_ROW)
  82|                 src_row = NS_ROW - 1;
  83|             if (src_col >= NS_COLUMN)
  84|                 src_col = NS_COLUMN - 1;
  85|             get_window_pixel = buf[src_row][src_col];
  86|         end
  87|         3'd3: begin
  88|             if (src_row >= NS_ROW) begin
  89|                 row_dist = src_row - (NS_ROW - 1);
  90|                 if (row_dist < (NS_ROW - 1))
  91|                     src_row = (NS_ROW - 1) - row_dist;
  92|                 else
  93|                     src_row = 2 * (NS_ROW - 1) - row_dist;
  94|             end
  95|             if (src_col >= NS_COLUMN) begin
  96|                 col_dist = src_col - (NS_COLUMN - 1);
  97|                 if (col_dist < (NS_COLUMN - 1))
  98|                     src_col = (NS_COLUMN - 1) - col_dist;
  99|                 else
 100|                     src_col = 2 * (NS_COLUMN - 1) - col_dist;
 101|             end
 102|             get_window_pixel = buf[src_row][src_col];
 103|         end
 104|         3'd4: begin
 105|             if (src_row >= NS_ROW)
 106|                 src_row = src_row - NS_ROW;
 107|             if (src_col >= NS_COLUMN)
 108|                 src_col = src_col - NS_COLUMN;
 109|             get_window_pixel = buf[src_row][src_col];
 110|         end
 111|         default: get_window_pixel = {NBW_DATA{1'b0}};
 112|     endcase
 113| endfunction
 114| 
 115| // ----------------------------------------
 116| // - Output generation
 117| // ----------------------------------------
 118| always_comb begin : window_assignment
 119|     for (int row = 0; row < NS_R_OUT; row++) begin
 120|         for (int col = 0; col < NS_C_OUT; col++) begin
 121|             window[row][col]        = get_window_pixel(buffer_view, row, col, i_mode);
 122|             window_capture[row][col] = get_window_pixel(image_buffer_ff, row, col, i_mode);
 123|         end
 124|     end
 125| end
 126| 
 127| always_comb begin : window_pack
 128|     for (int row = 0; row < NS_R_OUT; row++) begin
 129|         for (int col = 0; col < NS_C_OUT; col++) begin
 130|             packed_window[(row*NS_C_OUT+col+1)*NBW_DATA-1-:NBW_DATA]  = window[row][col];
 131|             packed_capture[(row*NS_C_OUT+col+1)*NBW_DATA-1-:NBW_DATA] = window_capture[row][col];
 132|         end
 133|     end
 134| end
 135| 
 136| assign o_image_window = i_update_window ? packed_window : image_window_ff;
 137| 
 138| // ----------------------------------------
 139| // - Input control
 140| // ----------------------------------------
 141| generate
 142|     for (genvar col = 0; col < NS_COLUMN; col++) begin : unpack_row_image
 143|         assign row_image[NS_COLUMN-col-1] = i_row_image[(col+1)*NBW_DATA-1-:NBW_DATA];
 144|     end
 145| endgenerate
 146| 
 147| always_ff @(posedge clk or negedge rst_async_n) begin : ctrl_regs
 148|     if(~rst_async_n) begin
 149|         image_window_ff <= 0;
 150|         for (int row = 0; row < NS_ROW; row++) begin
 151|             for (int col = 0; col < NS_COLUMN; col++) begin
 152|                 image_buffer_ff[row][col] <= 0;
 153|                 image_buffer_snapshot[row][col] <= 0;
 154|             end
 155|         end
 156|     end else begin
 157|         if(i_update_window) begin
 158|             image_window_ff <= packed_capture;
 159|         end
 160| 
 161|         if(i_valid) begin
 162|             for (int row = 0; row < NS_ROW; row++) begin
 163|                 for (int col = 0; col < NS_COLUMN; col++) begin
 164|                     image_buffer_snapshot[row][col] <= image_buffer_ff[row][col];
 165|                 end
 166|             end
 167| 
 168|             for (int col = 0; col < NS_COLUMN; col++) begin
 169|                 image_buffer_ff[0][col] <= row_image[col];
 170|             end
 171| 
 172|             for (int row = 1; row < NS_ROW; row++) begin
 173|                 for (int col = 0; col < NS_COLUMN; col++) begin
 174|                     image_buffer_ff[row][col] <= image_buffer_ff[row-1][col];
 175|                 end
 176|             end
 177|         end
 178|     end
 179| end
 180| 
 181| endmodule : line_buffer
```

## Files you must patch
rtl/line_buffer.sv

Primary module: `line_buffer`

## Structured harness feedback
```text
error_kind: compile

## Compile errors
- L0 [compile]: iverilog/cocotb build failed (see harness log) — hint: Fix syntax/elaboration errors before debugging logic.
```

## Previous iteration rationale (prioritize this)
- **Harness shows DUT stuck at `0x0`:** Failures like `0x0 != 0xff0000ff0000ff0000ff0000` at 130 ns occur because line 106 drives **`o_image_window = image_window_ff` only**, with no combinational path when `i_update_window=1`. The spec (section 4) requires the output to update **asynchronously** while `i_update_window` is asserted; cocotb compares immediately after the edge when the model has a live window.
- **Hold register is still required:** When `i_update_window=0`, output must not change (spec section 4). `image_window_ff` must latch the last computed window on posedges where `i_update_window=1` (lines 127–128), but it must not be the sole output driver.
- **Correct output mux:** Restore `o_image_window = i_update_window ? packed_window : image_window_ff` so live comb updates appear when updating, and `image_window_ff` holds the value when not updating.
- **Pre-shift capture for cocotb ordering:** When `i_valid` and `i_update_window` are both 1, cocotb calls `update_inputs()` before `add_line()`. `packed_capture` (latched into `image_window_ff`) must read **`image_buffer_ff` before the shift** at posedge. `packed_window` (live output) must read **`image_buffer_snapshot`** after the shift NBA when both signals are high, so comb output does not use the post-shift buffer.
- **Snapshot timing:** Capture `image_buffer_snapshot <= image_buffer_ff` inside the `if (i_valid)` block before the shift (lines 131–140), matching the prior working snapshot approach for the live comb path only.
- **Window indexing/border logic unchanged:** `src_row = i_image_row_start + row`, independent extend/wrap/mirror handling remains correct for spec cycles 5/8/10.

## Raw CVDP harness output excerpt
```text
## Key failure excerpts
# Windows accumulates the output in a single blocking
                    # read() call run on child threads, with the timeout
                    # being done in a join() on those threads.  communicate()
                    # _after_ kill() is required to collect that and add it
                    # to the exception.
                    exc.stdout, exc.stderr = process.communicate()
                else:
                    # POSIX _communicate already populated the output so
                    # far into the TimeoutExpired exception.
                    process.wait()
                raise
            except:  # Including KeyboardInterrupt, communicate handled that.
                process.kill()
                # We don't call process.wait() as .__exit__ does that for us.
                raise
            retcode = process.poll()
            if check and retcode:
>               raise CalledProcessError(retcode, process.args,
                                         output=stdout, stderr=stderr)
E               subprocess.CalledProcessError: Command '['iverilog', '-o', '/code/rundir/sim_build/sim.vvp', '-s', 'line_buffer', '-g2012', '-Pline_buffer.NBW_DATA=14', '-Pline_buffer.NS_ROW=9', '-Pline_buffer.NS_COLUMN=13', '-Pline_buffer.NS_R_OUT=2', '-Pline_buffer.NS_C_OUT=1', '-Pline_buffer.CONSTANT=162', '-Pline_buffer.NBW_ROW=4', '-Pline_buffer.NBW_COL=4', '-Pline_buffer.NBW_MODE=3', '-f', '/code/rundir/sim_build/cmds.f', '/code/rtl/line_buffer.sv']' returned non-zero exit status 12.

/usr/lib/python3.12/subprocess.py:571: CalledProcessError
------------------------------ Captured log call -------------------------------
INFO     Icarus:runner.py:644 Removing: /code/rundir/sim_build
INFO     Icarus:runner.py:632 Running command iverilog -o /code/rundir/sim_build/sim.vvp -s line_buffer -g2012 -Pline_buffer.NBW_DATA=14 -Pline_buffer.NS_ROW=9 -Pline_buffer.NS_COLUMN=13 -Pline_buffer.NS_R_OUT=2 -Pline_buffer.NS_C_OUT=1 -Pline_buffer.CONSTANT=162 -Pline_buffer.NBW_ROW=4 -Pline_buffer.NBW_COL=4 -Pline_buffer.NBW_MODE=3 -f /code/rundir/sim_build/cmds.f /code/rtl/line_buffer.sv in directory /code/rundir/sim_build
=============================== warnings summary ===============================
../../venv/lib/python3.12/site-packages/_pytest/cacheprovider.py:477
  /venv/lib/python3.12/site-packages/_pytest/cacheprovider.py:477: PytestCacheWarning: could not create cache path /rundir/harness/.cache/v/cache/nodeids: [Errno 13] Permission denied: '/rundir/harness/pytest-cache-files-764wsh73'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../../venv/lib/python3.12/site-packages/_pytest/cacheprovider.py:429
  /venv/lib/python3.12/site-packages/_pytest/cacheprovider.py:429: PytestCacheWarning: could not create cache path /rundir/harness/.cache/v/cache/lastfailed: [Errno 13] Permission denied: '/rundir/harness/pytest-cache-files-b4djk5do'
    config.cache.set("cache/lastfailed", self.lastfailed)

../../venv/lib/python3.12/site-packages/_pytest/stepwise.py:51
  /venv/lib/python3.12/site-packages/_pytest/stepwise.py:51: PytestCacheWarning: could not create cache path /rundir/harness/.cache/v/cache/stepwise: [Errno 13] Permission denied: '/rundir/harness/pytest-cache-files-t7jhpwrw'
    session.config.cache.set(STEPWISE_CACHE_DIR, [])

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED ../../src/test_runner.py::test_data[255-3-4-8-10-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[255-3-4-8-10-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[255-3-4-8-9-8] - subprocess.Called...
FAILED ../../src/test_runner.py::test_data[255-3-4-8-9-14] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[255-3-4-13-10-8] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[255-3-4-13-10-14] - subprocess.Cal...
FAILED ../../src/test_runner.py::test_data[255-3-4-13-9-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[255-3-4-13-9-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[255-3-2-8-10-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[255-3-2-8-10-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[255-3-2-8-9-8] - subprocess.Called...
FAILED ../../src/test_runner.py::test_data[255-3-2-8-9-14] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[255-3-2-13-10-8] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[255-3-2-13-10-14] - subprocess.Cal...
FAILED ../../src/test_runner.py::test_data[255-3-2-13-9-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[255-3-2-13-9-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[255-1-4-8-10-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[255-1-4-8-10-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[255-1-4-8-9-8] - subprocess.Called...
FAILED ../../src/test_runner.py::test_data[255-1-4-8-9-14] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[255-1-4-13-10-8] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[255-1-4-13-10-14] - subprocess.Cal...
FAILED ../../src/test_runner.py::test_data[255-1-4-13-9-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[255-1-4-13-9-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[255-1-2-8-10-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[255-1-2-8-10-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[255-1-2-8-9-8] - subprocess.Called...
FAILED ../../src/test_runner.py::test_data[255-1-2-8-9-14] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[255-1-2-13-10-8] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[255-1-2-13-10-14] - subprocess.Cal...
FAILED ../../src/test_runner.py::test_data[255-1-2-13-9-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[255-1-2-13-9-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[162-3-4-8-10-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[162-3-4-8-10-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[162-3-4-8-9-8] - subprocess.Called...
FAILED ../../src/test_runner.py::test_data[162-3-4-8-9-14] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[162-3-4-13-10-8] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[162-3-4-13-10-14] - subprocess.Cal...
FAILED ../../src/test_runner.py::test_data[162-3-4-13-9-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[162-3-4-13-9-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[162-3-2-8-10-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[162-3-2-8-10-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[162-3-2-8-9-8] - subprocess.Called...
FAILED ../../src/test_runner.py::test_data[162-3-2-8-9-14] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[162-3-2-13-10-8] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[162-3-2-13-10-14] - subprocess.Cal...
FAILED ../../src/test_runner.py::test_data[162-3-2-13-9-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[162-3-2-13-9-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[162-1-4-8-10-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[162-1-4-8-10-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[162-1-4-8-9-8] - subprocess.Called...
FAILED ../../src/test_runner.py::test_data[162-1-4-8-9-14] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[162-1-4-13-10-8] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[162-1-4-13-10-14] - subprocess.Cal...
FAILED ../../src/test_runner.py::test_data[162-1-4-13-9-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[162-1-4-13-9-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[162-1-2-8-10-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[162-1-2-8-10-14] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[162-1-2-8-9-8] - subprocess.Called...
FAILED ../../src/test_runner.py::test_data[162-1-2-8-9-14] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[162-1-2-13-10-8] - subprocess.Call...
FAILED ../../src/test_runner.py::test_data[162-1-2-13-10-14] - subprocess.Cal...
FAILED ../../src/test_runner.py::test_data[162-1-2-13-9-8] - subprocess.Calle...
FAILED ../../src/test_runner.py::test_data[162-1-2-13-9-14] - subprocess.Call...
======================= 64 failed, 3 warnings in 11.15s ========================

[stderr]
Network cvdp_react_cvdp_copilot_line_buffer_0003_6_default Creating 
 Network cvdp_react_cvdp_copilot_line_buffer_0003_6_default Created 
 Container cvdp_react_cvdp_copilot_line_buffer_000

[... truncated 431989 chars from end of harness output ...]
```

## Local iverilog debug
Skipped — Cursor judged a local iverilog/VCD sim would not help this failure.

```text
- The harness **`error_kind` is `compile`**, not logic — iverilog exits with status 12 before any simulation runs, so a VCD testbench cannot elaborate or produce useful waves.
- The failure is **`iverilog ... /code/rtl/line_buffer.sv` returned non-zero exit status 12`** across all parameter sets; that is a syntax/elaboration problem, not a runtime mismatch on `o_image_window`.
- The truncated DUT shows a new **`function automatic get_window_pixel(..., input logic buf [NS_ROW][NS_COLUMN], ...)`** — Icarus Verilog (-g2012) commonly rejects **unpacked array ports on functions**, especially with parameterized dimensions; the fix is to remove or inline that helper, not to debug waveforms.
- A `tb_debug` module **depends on the same DUT elaboration** and will fail with the identical compile error, adding no information beyond re-running `iverilog rtl/line_buffer.sv`.
- The next iteration should **replace the function with inline `always_comb` logic** (as in earlier passing-elaboration revisions) while keeping the output mux / snapshot / capture structure — compile-first, then re-run cocotb for logic.
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
