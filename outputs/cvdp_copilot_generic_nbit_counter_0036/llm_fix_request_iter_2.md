Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_generic_nbit_counter_0036

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
The `generic_counter` module implements a parameterized counter supporting multiple operating modes, including **MODULO_256**, and **GRAY** modes. However, during testing with various configurations, the module exhibited unexpected behavior in some modes due to the following RTL bugs:

1. In **MODULO_256 mode (mode_in = 3'b010)**, the counter skips states due to an incorrect increment logic when transitioning near the `ref_modulo` value.
2. In **GRAY mode (mode_in = 3'b100)**, the output `o_count` generates incorrect Gray code values due to an issue in the encoding logic.
3. When **enable_in = 1'b0**, the counter operates continuously even when the `enable_in` signal is LOW.

---

### **Test Case Details**

#### **MODULO_256 Mode**
- **Clock Frequency (`clk_in`):** 100 MHz
- **N**: 8
- **Mode (`mode_in`):** 3'b010
- **Input:** `enable_in` HIGH, `ref_modulo = 100`.
- **Expected Output:** Counter increments sequentially and resets to zero after reaching `ref_modulo`.
- **Actual Output:** Counter skips every alternate state near `ref_modulo`.

---

#### **GRAY Mode**
- **Clock Frequency (`clk_in`):** 100 MHz
- **N**: 3
- **Mode (`mode_in`):** 3'b100
- **Input:** `enable_in` HIGH, `rst_in` LOW.
- **Expected Output:** Output `o_count` generates valid Gray code values.
- **Actual Output:** Output `o_count` produces invalid Gray code values.

---

#### **enable_in is LOW**
- **Clock Frequency (`clk_in`):** 100 MHz
- **N**: 3
- **Mode (`mode_in`):** 3'b001
- **Input:** `enable_in` is toggled from HIGH to LOW.
- **Expected Output:** Counter stops decrementing when `enable_in` is LOW.
- **Actual Output:** Counter continues decrementing even when `enable_in` is LOW.

---

### **Waveforms**

#### **1. MODULO_256 Mode (clk_in frequency: 100 MHz, ref_modulo = 100)**
```wavedrom
{
  "signal": [
    {"name": "clk_in", "wave": "0101010101010101010"},
    {"name": "rst_in", "wave": "10................."},
    {"name": "enable_in", "wave": "1.................."},
    {"name": "mode_in", "wave": "3..................", "data": "3'b010"},
    {"name": "o_count (Expected)", "wave": "0..2.3.4.5.6.7.8.9.0", "data": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]},
    {"name": "o_count (Actual)", "wave": "0..2.4.6.8.........", "data": ["0", "2", "4", "6", "8"]}
  ],
  "config": {
    "hscale": 1
  },
  "head": {
    "text": "MODULO_256 Mode, N=8: Unexpected state skipping near ref_modulo"
  }
}
```

---

#### **2. GRAY Mode (clk_in frequency: 100 MHz)**
```wavedrom
{
  "signal": [
    {"name": "clk_in", "wave": "01010101010101010"},
    {"name": "rst_in", "wave": "10..............."},
    {"name": "enable_in", "wave": "1................"},
    {"name": "mode_in", "wave": "3................", "data": "3'b100"},
    {"name": "o_count (Expected)", "wave": "0..3.2.6.7.5.4.9.", "data": ["0", "1", "3", "2", "6", "7", "5", "4"]},
    {"name": "o_count (Actual)", "wave": "0..2.2.3.3.4.4.5.", "data": ["0", "1", "2", "2", "3", "3", "4", "4"]}
  ],
  "config": {
    "hscale": 1
  },
  "head": {
    "text": "GRAY Mode, N=3: Incorrect Gray code output"
  }
}
```

---

#### **3. enable_in is de-asserted (clk_in frequency: 100 MHz)**
```wavedrom
{
  "signal": [
    {"name": "clk_in", "wave": "01010101010101"},
    {"name": "rst_in", "wave": "10............"},
    {"name": "enable_in", "wave": "1......0......"},
    {"name": "mode_in", "wave": "3.............", "data": "3'b001"},
    {"name": "o_count (Expected)", "wave": "07.6.5.4......", "data": ["0", "7", "6", "5", "4", "3", "2", "1", "0"]},
    {"name": "o_count (Actual)", "wave": "07.6.5.4.3.2.2", "data": ["0", "7", "6", "5", "4", "3", "2", "1", "0"]}
  ],
  "config": {
    "hscale": 1
  },
  "head": {
    "text": "BINARY_DOWN Mode, N=3: Counter decrements values even when enable_in is LOW"
  }
}

```

Identify and fix the RTL bugs to ensure the module behaves as expected in all modes.

## Current candidate files (line-numbered on patch targets)
### rtl/generic_counter.sv
```verilog
1| module generic_counter #(parameter N = 8) (
   2|     input logic clk_in,          // Clock input
   3|     input logic rst_in,          // Active HIGH Reset input
   4|     input logic [2:0] mode_in,   // Mode input (3 bits)
   5|     input logic enable_in,       // Enable input
   6|     input logic [N-1:0] ref_modulo, // Reference modulo value for Modulo-256 counter
   7|     output logic [N-1:0] o_count   // Output count (N bits)
   8| );
   9| 
  10|     parameter BINARY_UP = 3'b000;
  11|     parameter BINARY_DOWN = 3'b001;
  12|     parameter MODULO_256 = 3'b010;
  13|     parameter JOHNSON = 3'b011;
  14|     parameter GRAY = 3'b100;
  15|     parameter RING = 3'b101;
  16| 
  17|     logic [N-1:0] count;
  18| 
  19|     always_ff @(posedge clk_in or posedge rst_in) begin
  20|         if (rst_in) begin
  21|             count <= {N{1'b0}};
  22|         end else begin
  23|             case (mode_in)
  24|                 BINARY_UP: begin
  25|                     count <= count + 1;
  26|                 end
  27|                 BINARY_DOWN: begin
  28|                     count <= count - 1;
  29|                 end
  30|                 MODULO_256: begin
  31|                     if (count == ref_modulo) begin
  32|                         count <= {N{1'b0}};
  33|                     end else begin
  34|                         count <= count + 2;  
  35|                     end
  36|                 end
  37|                 JOHNSON: begin
  38|                     count <= {~count[0], count[N-1:1]};
  39|                 end
  40|                 GRAY: begin
  41|                     count <= count >> 1;  
  42|                 end
  43|                 RING: begin
  44|                     if (count == {N{1'b0}}) begin
  45|                         count <= {{(N-1){1'b0}}, 1'b1};  
  46|                     end else begin
  47|                         count <= {count[N-2:0], count[N-1]};  
  48|                     end
  49|                 end		
  50|                 default: begin
  51|                     count <= {N{1'b0}};
  52|                 end
  53|             endcase
  54|         end
  55|     end
  56| 
  57|     assign o_count = count;
  58| 
  59| endmodule
```

## Files you must patch
rtl/generic_counter.sv

Primary module: `generic_counter`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=assert LogicArray('00000010', Range(7, 'downto', 0)) == 1
- cocotb: expected=? actual=Gray code mismatch at step 1: expected 1, got 00000000
- cocotb: expected=? actual=Expected o_count to remain 00100000, but got 10000000
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
5509.00ns INFO     cocotb.regression                  running test_generic_counter.test_mod_256 (6/8)
  5550.00ns WARNING  ..b.Test test_mod_256.test_mod_256 assert LogicArray('00000010', Range(7, 'downto', 0)) == 1
                                                         +  where LogicArray('00000010', Range(7, 'downto', 0)) = LogicArrayObject(generic_counter.o_count).value
                                                         +    where LogicArrayObject(generic_counter.o_count) = HierarchyObject(generic_counter).o_count
                                                        Traceback (most recent call last):
                                                          File "/src/test_generic_counter.py", line 188, in test_mod_256
                                                            assert dut.o_count.value == i
                                                        AssertionError: assert LogicArray('00000010', Range(7, 'downto', 0)) == 1
                                                         +  where LogicArray('00000010', Range(7, 'downto', 0)) = LogicArrayObject(generic_counter.o_count).value
                                                         +    where LogicArrayObject(generic_counter.o_count) = HierarchyObject(generic_counter).o_count
  5550.00ns WARNING  cocotb.regression                  test_generic_counter.test_mod_256 failed
  5550.00ns INFO     cocotb.regression                  running test_generic_counter.test_gray_counter (7/8)
  5591.00ns WARNING  ..t_gray_counter.test_gray_counter Gray code mismatch at step 1: expected 1, got 00000000
                                                        assert LogicArray('00000000', Range(7, 'downto', 0)) == 1
                                                         +  where LogicArray('00000000', Range(7, 'downto', 0)) = LogicArrayObject(generic_counter.o_count).value
                                                         +    where LogicArrayObject(generic_counter.o_count) = HierarchyObject(generic_counter).o_count
                                                        Traceback (most recent call last):
                                                          File "/src/test_generic_counter.py", line 218, in test_gray_counter
                                                            assert dut.o_count.value == gray_sequence[i], f"Gray code mismatch at step {i}: expected {gray_sequence[i]}, got {dut.o_count.value}"
                                                        AssertionError: Gray code mismatch at step 1: expected 1, got 00000000
                                                        assert LogicArray('00000000', Range(7, 'downto', 0)) == 1
                                                         +  where LogicArray('00000000', Range(7, 'downto', 0)) = LogicArrayObject(generic_counter.o_count).value
                                                         +    where LogicArrayObject(generic_counter.o_count) = HierarchyObject(generic_counter).o_count
  5591.00ns WARNING  cocotb.regression                  test_generic_counter.test_gray_counter failed
  5591.00ns INFO     cocotb.regression                  running test_generic_counter.test_enable (8/8)
  5697.00ns WARNING  ..otb.Test test_enable.test_enable Expected o_count to remain 00100000, but got 10000000
                                                        assert LogicArray('10000000', Range(7, 'downto', 0)) == LogicArray('00100000', Range(7, 'downto', 0))
                                                         +  where LogicArray('10000000', Range(7, 'downto', 0)) = LogicArrayObject(generic_counter.o_count).value
                                                         +    where LogicArrayObject(generic_counter.o_count) = HierarchyObject(generic_counter).o_count
                                                        Traceback (most recent call last):
                                              

[... truncated 15764 chars from end of harness output ...]
```

## Cocotb test excerpt
### test_generic_counter.py
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ClockCycles, Timer

# ----------------------------------------
# - Tests
# ----------------------------------------

async def init_dut(dut):

    dut.rst_in.value     = 1
    dut.mode_in.value    = 0
    dut.enable_in.value  = 0
    dut.ref_modulo.value = 0
    await RisingEdge(dut.clk_in)

@cocotb.test()
async def test_reset(dut):
    cocotb.start_soon(Clock(dut.clk_in, 10, unit='ns').start())
    await init_dut(dut)

    # ----------------------------------

[... truncated 3888 chars from cocotb test excerpt ...]

test_basic(dut):

    cocotb.start_soon(Clock(dut.clk_in, 10, unit='ns').start())
    await init_dut(dut)

    # ----------------------------------------
    # - Check No Operation
    # ----------------------------------------

    await FallingEdge(dut.clk_in)

    dut.mode_in.value   = 5 # Testing Ring Counter
    dut.enable_in.value = 0 # Testing Ring Counter
    
    await RisingEdge(dut.clk_in)
    dut.rst_in.value    = 0

    await FallingEdge(dut.clk_in)
    dut.enable_in.value = 1

    for _ in range(5):
        await FallingEdge(dut.clk_in)

    assert dut.o_count.value == 2 ** 4
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/generic_counter.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
