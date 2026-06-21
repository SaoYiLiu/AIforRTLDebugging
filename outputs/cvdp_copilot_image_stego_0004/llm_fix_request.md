Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_image_stego_0004

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
The `image_stego` module is designed to embed an input stream (`data_in`) into an image (`img_in`) based on the number of bits per pixel (`bpp`). However, the module exhibits unexpected behavior in the following scenario:

1. **No Embedding for `bpp=2'b10` and `bpp=2'b11`**  
   - When `bpp=10` or `bpp=11`, the output `img_out` remains identical to `img_in`, rather than embedding more bits from `data_in`.

---

## **Test Case Details**

Below are the relevant test vectors showing **Expected vs. Actual** outputs.

### **TC 1: `bpp = 2'b00`**

| img_in                           | data_in          |         Expected img_out         |          Actual img_out          |
|----------------------------------|------------------|:--------------------------------:|:--------------------------------:|
| 00000001000000010000000100000001 | 1111111111111111 | 00000001000000010000000100000001 | 00000001000000010000000100000001 |

### **TC 2: `bpp = 2'b01`**

| img_in                           | data_in          |         Expected img_out         |          Actual img_out          |
|----------------------------------|------------------|:--------------------------------:|:--------------------------------:|
| 00000001000000010000000100000001 | 0000000000001111 | 00000000000000000000001100000011 | 00000000000000000000001100000011 |

### **TC 3: `bpp = 2'b10`**

| img_in                           | data_in          |         Expected img_out         |          Actual img_out          |
|----------------------------------|------------------|:--------------------------------:|:--------------------------------:|
| 00000001000000010000000100000001 | 1111111111111111 | 00000111000001110000011100000111 | 00000001000000010000000100000001 |

### **TC 4: `bpp = 2'b11`**

| img_in                           | data_in          |         Expected img_out         |          Actual img_out          |
|----------------------------------|------------------|:--------------------------------:|:--------------------------------:|
| 00000001000000010000000100000001 | 1111111111111111 | 00001111000011110000111100001111 | 00000001000000010000000100000001 |

---

## **Summary of Issues**

- For `bpp=00` and `bpp=01`, the embedding works correctly.
- For `bpp=10` and `bpp=11`, the output simply passes through `img_in` without embedding any new bits from `data_in`.

---

**Identify and fix** the portion of the RTL logic that causes the output to ignore `data_in` when `bpp=10` or `bpp=11`. 
Ensure that:
1. **`bpp=2'b10`** properly embeds the corresponding bits from `data_in`.
2. **`bpp=2'b11`** also embeds the intended (higher) number of bits from `data_in`.

## Current candidate files (line-numbered on patch targets)
### rtl/image_stego.sv
```verilog
1| module image_stego #(
   2|   parameter row = 2,
   3|   parameter col = 2
   4| )(
   5|   input  [(row*col*8)-1:0] img_in,
   6|   input  [(row*col*4)-1:0] data_in,
   7|   input  [1:0]             bpp,
   8|   output [(row*col*8)-1:0] img_out
   9| );
  10| 
  11|   genvar i;
  12|   generate
  13|     for(i = 0; i < row*col; i++) begin
  14|       assign img_out[(i*8)+7:(i*8)] = (bpp[1] == 1'b0)
  15|                                       ? (bpp[0] == 1'b0
  16|                                          ? {img_in[(i*8)+7 : (i*8)+1], data_in[i]}
  17|                                          : {img_in[(i*8)+7 : (i*8)+2], data_in[(2*i)+1], data_in[2*i]}) 
  18|                                       : img_in[(i*8)+7 : (i*8)]; 
  19|     end
  20|   endgenerate
  21| 
  22| endmodule
```

## Files you must patch
rtl/image_stego.sv

Primary module: `image_stego`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=[EDGE CASE - ALTERNATING BITS] Mismatch: got=0b10101010010101011010101001010101, expected=0b10101101010100101010110101010010
- cocotb: expected=? actual=[RANDOM TEST Trial 1] Mismatch: got=0b00101010100010000011001100110111, expected=0b00101110100011110011010100110010
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
8.00ns INFO     cocotb.regression                  running test_image_stego.test_edgecase_alternating_bits (4/5)
                                                            Edge case test: Alternating bits in img_in and data_in.
     9.00ns INFO     cocotb.image_stego                 === [EDGE CASE TEST - ALTERNATING BITS] Starting ===
    11.00ns INFO     cocotb.image_stego                 Inputs : img_in=0b10101010010101011010101001010101, data_in=0b1010101010101010, bpp=10
    11.00ns INFO     cocotb.image_stego                 Output : actual=0b10101010010101011010101001010101, expected=0b10101101010100101010110101010010
    11.00ns WARNING  ..s.test_edgecase_alternating_bits [EDGE CASE - ALTERNATING BITS] Mismatch: got=0b10101010010101011010101001010101, expected=0b10101101010100101010110101010010
                                                        assert 2857740885 == 2907876690
                                                        Traceback (most recent call last):
                                                          File "/src/test_image_stego.py", line 188, in test_edgecase_alternating_bits
                                                            assert actual_val == expected_val, \
                                                        AssertionError: [EDGE CASE - ALTERNATING BITS] Mismatch: got=0b10101010010101011010101001010101, expected=0b10101101010100101010110101010010
                                                        assert 2857740885 == 2907876690
    11.00ns WARNING  cocotb.regression                  test_image_stego.test_edgecase_alternating_bits failed
    11.00ns INFO     cocotb.regression                  running test_image_stego.test_random (5/5)
                                                            Random test: feed random images/data across all possible bpp values.
    12.00ns INFO     cocotb.image_stego                 === [RANDOM TEST] Starting ===
    14.00ns INFO     cocotb.image_stego                 [Trial 0] bpp=01, img_in=0b00111110100000100110100100011110, data_in=0b0100010111100100
    14.00ns INFO     cocotb.image_stego                 [Trial 0] actual=0b00111111100000100110100100011100, expected=0b00111111100000100110100100011100
    16.00ns INFO     cocotb.image_stego                 [Trial 1] bpp=10, img_in=0b00101010100010000011001100110111, data_in=0b1001110111101010
    16.00ns INFO     cocotb.image_stego                 [Trial 1] actual=0b00101010100010000011001100110111, expected=0b00101110100011110011010100110010
    16.00ns WARNING  ..otb.Test test_random.test_random [RANDOM TEST Trial 1] Mismatch: got=0b00101010100010000011001100110111, expected=0b00101110100011110011010100110010
                                                        assert 713569079 == 781137202
                                                        Traceback (most recent call last):
                                                          File "/src/test_image_stego.py", line 231, in test_random
                                                            assert actual_val == expected_val, \
                                                        AssertionError: [RANDOM TEST Trial 1] Mismatch: got=0b00101010100010000011001100110111, expected=0b00101110100011110011010100110010
                                                        assert 713569079 == 781137202
    16.00ns WARNING  cocotb.regression                  test_image_stego.test_random failed
    16.00ns INFO     cocotb.regression                  *********************************************************************************************************
                                                        ** TEST                                             STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        ******************************************************************************

[... truncated 17447 chars from end of harness output ...]
```

## Cocotb test excerpt
### test_image_stego.py
```python
import cocotb
from cocotb.triggers import Timer
import os
import random

def compute_expected_output(img_in, data_in, bpp, row, col):
    """
    Replicates the logic in the Verilog code for each pixel:
        - bpp = 00: LSB replaced by data_in[i]
        - bpp = 01: 2 LSB replaced by data_in[2*i+1 : 2*i]
        - bpp = 10: 3 LSB replaced by data_in[3*i+2 : 3*i]
        - bpp = 11: 4 LSB replaced by data_in[4*i+3 : 4*i]
    """
    total_pixels = row * col
    out_val = 0

    for i in range(total_pixels):
        pixel = (img_in >> (i*8)) & 0xFF  # extract

[... truncated 2837 chars from cocotb test excerpt ...]

val:0{total_pixels*8}b}, "
                  f"data_in=0b{data_val:0{total_pixels*4}b}, bpp={bpp:02b}")
    dut._log.info(f"Output : actual=0b{actual_val:0{total_pixels*8}b}, "
                  f"expected=0b{expected_val:0{total_pixels*8}b}")

    assert actual_val == expected_val, \
        f"[EDGE CASE - ALL ZEROS] Mismatch: got=0b{actual_val:0{total_pixels*8}b}, expected=0b{expected_val:0{total_pixels*8}b}"

    dut._log.info("=== [EDGE CASE TEST - ALL ZEROS] PASSED ===")


@cocotb.test()
async def test_edgecase_all_ones(dut):
    """
    Edge case test: All ones in img_in and data_in.
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/image_stego.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
