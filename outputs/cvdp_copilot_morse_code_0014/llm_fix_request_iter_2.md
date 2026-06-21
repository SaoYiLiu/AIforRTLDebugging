Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_morse_code_0014

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
The provided version of an RTL module named `morse_encoder` that encodes ASCII characters into Morse code is giving the wrong outputs. Follows the specifications that this module should address:

---

### **Specifications:**

#### **Inputs and Outputs**
- **Input:**
  - `ascii_in` (8 bits): The ASCII character to be encoded.
- **Outputs:**
  - `morse_out` (6 bits): The Morse code sequence corresponding to the input character.
  - `morse_length` (4 bits): The number of valid bits in the `morse_out` sequence.

---

#### **Expected Behavior**

##### **For Valid Inputs (`A-Z` and `0-9`):**
- Each valid ASCII character must produce a unique Morse code sequence and its corresponding length as defined in a lookup table.

| ASCII Character | Morse Code | Hex Morse Code | Morse Length |
|-----------------|------------|----------------|--------------|
| A (`0x41`)      | `.-`       | `0x01`         | 2            |
| B (`0x42`)      | `-...`     | `0x08`         | 4            |
| C (`0x43`)      | `-.-.`     | `0x0A`         | 4            |
| D (`0x44`)      | `-..`      | `0x04`         | 3            |
| E (`0x45`)      | `.`        | `0x00`         | 1            |
| F (`0x46`)      | `..-.`     | `0x02`         | 4            |
| G (`0x47`)      | `--.`      | `0x06`         | 3            |
| H (`0x48`)      | `....`     | `0x00`         | 4            |
| I (`0x49`)      | `..`       | `0x00`         | 2            |
| J (`0x4A`)      | `.---`     | `0x07`         | 4            |
| K (`0x4B`)      | `-.-`      | `0x05`         | 3            |
| L (`0x4C`)      | `.-..`     | `0x04`         | 4            |
| M (`0x4D`)      | `--`       | `0x03`         | 2            |
| N (`0x4E`)      | `-.`       | `0x02`         | 2            |
| O (`0x4F`)      | `---`      | `0x07`         | 3            |
| P (`0x50`)      | `.--.`     | `0x06`         | 4            |
| Q (`0x51`)      | `--.-`     | `0x0D`         | 4            |
| R (`0x52`)      | `.-.`      | `0x02`         | 3            |
| S (`0x53`)      | `...`      | `0x00`         | 3            |
| T (`0x54`)      | `-`        | `0x01`         | 1            |
| U (`0x55`)      | `..-`      | `0x01`         | 3            |
| V (`0x56`)      | `...-`     | `0x01`         | 4            |
| W (`0x57`)      | `.--`      | `0x03`         | 3            |
| X (`0x58`)      | `-..-`     | `0x09`         | 4            |
| Y (`0x59`)      | `-.--`     | `0x0B`         | 4            |
| Z (`0x5A`)      | `--..`     | `0x0C`         | 4            |
| 0 (`0x30`)      | `-----`    | `0x1F`         | 5            |
| 1 (`0x31`)      | `.----`    | `0x0F`         | 5            |
| 2 (`0x32`)      | `..---`    | `0x07`         | 5            |
| 3 (`0x33`)      | `...--`    | `0x03`         | 5            |
| 4 (`0x34`)      | `....-`    | `0x01`         | 5            |
| 5 (`0x35`)      | `.....`    | `0x00`         | 5            |
| 6 (`0x36`)      | `-....`    | `0x10`         | 5            |
| 7 (`0x37`)      | `--...`    | `0x18`         | 5            |
| 8 (`0x38`)      | `---..`    | `0x1C`         | 5            |
| 9 (`0x39`)      | `----.`    | `0x1E`         | 5            |


##### **For Invalid Inputs (Outside `A-Z` and `0-9`):**
- Any input not explicitly defined in the lookup table must result in:
  - `morse_out = 6'b0`.
  - `morse_length = 0`.

---

#### **Edge Case Handling**
- The lookup table must correctly map valid ASCII characters (`A-Z` and `0-9`) to their respective Morse code sequences.
- Outputs for invalid inputs must be consistent, producing reset values (`morse_out = 6'b0`, `morse_length = 0`) regardless of prior input sequences.
- Ensure no unintended overlap or ambiguity in the lookup table.

---

#### **Requirements**
1. The `morse_encoder` must ensure correctness in the Morse code lookup table for all valid inputs.
2. Invalid inputs must produce consistent outputs that do not interfere with the processing of valid inputs.

---

Please provide me with one RTL version that fixes this issue.

## Current candidate files (line-numbered on patch targets)
### rtl/morse_encoder.sv
```verilog
1| module morse_encoder (
   2|     input wire [7:0] ascii_in,       // ASCII input character
   3|     output reg [5:0] morse_out,      // Morse code output (6 bits max for each letter)
   4|     output reg [3:0] morse_length    // Length of the Morse code sequence
   5| );
   6| 
   7|     always @(*) begin
   8|         case (ascii_in)
   9|             8'h41: begin morse_out = 6'b100;      morse_length = 3; end  // A: .-
  10|             8'h42: begin morse_out = 6'b1000;     morse_length = 4; end  // B: -...
  11|             8'h43: begin morse_out = 6'b1010;     morse_length = 4; end  // C: -.-.
  12|             8'h44: begin morse_out = 6'b100;      morse_length = 3; end  // D: -..
  13|             8'h45: begin morse_out = 6'b1;        morse_length = 3; end  // E: .
  14|             8'h46: begin morse_out = 6'b0010;     morse_length = 4; end  // F: ..-.
  15|             8'h47: begin morse_out = 6'b110;      morse_length = 3; end  // G: --.
  16|             8'h48: begin morse_out = 6'b0000;     morse_length = 4; end  // H: ....
  17|             8'h49: begin morse_out = 6'b00;       morse_length = 2; end  // I: ..
  18|             8'h4A: begin morse_out = 6'b0111;     morse_length = 4; end  // J: .---
  19|             8'h4B: begin morse_out = 6'b101;      morse_length = 3; end  // K: -.-
  20|             8'h4C: begin morse_out = 6'b01;       morse_length = 2; end  // L: .-..
  21|             8'h4D: begin morse_out = 6'b11;       morse_length = 2; end  // M: --
  22|             8'h4E: begin morse_out = 6'b10;       morse_length = 2; end  // N: -.
  23|             8'h4F: begin morse_out = 6'b111;      morse_length = 3; end  // O: ---
  24|             8'h50: begin morse_out = 6'b0110;     morse_length = 4; end  // P: .--.
  25|             8'h51: begin morse_out = 6'b1101;     morse_length = 4; end  // Q: --.-
  26|             8'h52: begin morse_out = 6'b010;      morse_length = 3; end  // R: .-.
  27|             8'h53: begin morse_out = 6'b000;      morse_length = 3; end  // S: ...
  28|             8'h54: begin morse_out = 6'b1;        morse_length = 1; end  // T: -
  29|             8'h55: begin morse_out = 6'b001;      morse_length = 3; end  // U: ..-
  30|             8'h56: begin morse_out = 6'b0001;     morse_length = 4; end  // V: ...-
  31|             8'h57: begin morse_out = 6'b011;      morse_length = 3; end  // W: .--
  32|             8'h58: begin morse_out = 6'b1001;     morse_length = 4; end  // X: -..-
  33|             8'h59: begin morse_out = 6'b1011;     morse_length = 4; end  // Y: -.--
  34|             8'h5A: begin morse_out = 6'b1100;     morse_length = 4; end  // Z: --..
  35|             8'h30: begin morse_out = 6'b11111;    morse_length = 5; end  // 0: -----
  36|             8'h31: begin morse_out = 6'b01111;    morse_length = 5; end  // 1: .----
  37|             8'h32: begin morse_out = 6'b00111;    morse_length = 5; end  // 2: ..---
  38|             8'h33: begin morse_out = 6'b00011;    morse_length = 5; end  // 3: ...--
  39|             8'h34: begin morse_out = 6'b00001;    morse_length = 5; end  // 4: ....-
  40|             8'h35: begin morse_out = 6'b00000;    morse_length = 5; end  // 5: .....
  41|             8'h36: begin morse_out = 6'b10000;    morse_length = 5; end  // 6: -....
  42|             8'h37: begin morse_out = 6'b11000;    morse_length = 5; end  // 7: --...
  43|             8'h38: begin morse_out = 6'b11100;    morse_length = 5; end  // 8: ---..
  44|             8'h39: begin morse_out = 6'b11110;    morse_length = 5; end  // 9: ----.
  45|             default: begin
  46|                 morse_out = 6'b0;                 
  47|                 morse_length = 4'b0;
  48|             end
  49|         endcase
  50|     end
  51| 
  52| endmodule
```

## Files you must patch
rtl/morse_encoder.sv

Primary module: `morse_encoder`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=ascii_in=0x41: Expected morse_out=0b1, got 0b100
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
0.00ns INFO     cocotb.regression                  running test_morse_encoder.test_lut_bug_fix (1/1)
                                                            Test for LUT-related bugs in the morse_encoder module.
     1.00ns WARNING  ..est_lut_bug_fix.test_lut_bug_fix ascii_in=0x41: Expected morse_out=0b1, got 0b100
                                                        assert LogicArray('000100', Range(5, 'downto', 0)) == 1
                                                         +  where LogicArray('000100', Range(5, 'downto', 0)) = LogicArrayObject(morse_encoder.morse_out).value
                                                         +    where LogicArrayObject(morse_encoder.morse_out) = HierarchyObject(morse_encoder).morse_out
                                                        Traceback (most recent call last):
                                                          File "/src/test_morse_encoder.py", line 21, in test_lut_bug_fix
                                                            await drive_and_check(0x41, 0b01, 2)  # Correct Morse: .-
                                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                          File "/src/test_morse_encoder.py", line 16, in drive_and_check
                                                            assert dut.morse_out.value == expected_out, f"ascii_in={hex(ascii_in)}: Expected morse_out={bin(expected_out)}, got {bin(dut.morse_out.value)}"
                                                        AssertionError: ascii_in=0x41: Expected morse_out=0b1, got 0b100
                                                        assert LogicArray('000100', Range(5, 'downto', 0)) == 1
                                                         +  where LogicArray('000100', Range(5, 'downto', 0)) = LogicArrayObject(morse_encoder.morse_out).value
                                                         +    where LogicArrayObject(morse_encoder.morse_out) = HierarchyObject(morse_encoder).morse_out
     1.00ns WARNING  cocotb.regression                  test_morse_encoder.test_lut_bug_fix failed
     1.00ns INFO     cocotb.regression                  *********************************************************************************************
                                                        ** TEST                                 STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        *********************************************************************************************
                                                        ** test_morse_encoder.test_lut_bug_fix   FAIL           1.00           0.01        137.50  **
                                                        *********************************************************************************************
                                                        ** TESTS=1 PASS=0 FAIL=1 SKIP=0                         1.00           0.02         47.96  **
                                                        *********************************************************************************************
ERROR    Icarus:runner.py:572 ERROR: Failed 1 of 1 tests.
FAILED

=================================== FAILURES ===================================
_________________________________ test_runner __________________________________

    def test_runner():
    
        runner = get_runner(sim)
        runner.build(
            sources=verilog_sources,
            hdl_toplevel=toplevel,
            # Arguments
            always=True,
            clean=True,
            verbose=True,
            timescale=("1ns", "1ns"),
            log_file="build.log")
    
>       runner.test(hdl_toplevel=toplevel, test_module=module, waves=True)
E       SystemExit: 1

/src/test_runner.py:27: SystemExit
------------------------------

[... truncated 9978 chars from end of harness output ...]
```

## Cocotb test excerpt
### test_morse_encoder.py
```python
import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_lut_bug_fix(dut):
    """
    Test for LUT-related bugs in the morse_encoder module.
    Verifies the correct Morse code for 'A', 'E', and 'L'.
    """

    # Helper function to drive input and check expected output
    async def drive_and_check(ascii_in, expected_out, expected_length):
        dut.ascii_in.value = ascii_in
        await Timer(1, unit="ns")  # Allow some delay for the outputs to stabilize
        assert dut.morse_out.value == expected_out, f"ascii_in={hex(ascii_in)}: Expected morse_out={bin(expected_out)}, got {bin(dut.morse_out.value)}"
        assert dut.morse_length.value == expected_length, f"ascii_in={hex(ascii_in)}: Expected morse_length={expected_length}, got {dut.morse_length.value}"

    # Test cases for previously buggy LUT entries
    # 'A' (8'h41)
    await drive_and_check(0x41, 0b01, 2)  # Correct Morse: .-

    # 'E' (8'h45)
    await drive_and_check(0x45, 0b0, 1)  # Correct Morse: .

    # 'L' (8'h4C)
    await drive_and_check(0x4C, 0b0100, 4)  # Correct Morse: .-..
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/morse_encoder.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
