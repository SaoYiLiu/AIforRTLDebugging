Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_caesar_cipher_0024

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
The `caesar_cipher` module shifts each character of an `input_phrase` using per-character shift values from `key_phrase`, supporting **encryption** (`decrypt = 1'b0`) and **decryption** (`decrypt = 1'b1`). However, the module exhibits **unexpected behavior** under certain conditions due to the following issues:

1. **Uppercase Encryption (Missing Wrap-Around)**  
   When encrypting uppercase letters (`"A"` … `"Z"`), any shift beyond `'Z'` results in wrong characters.

2. **Uppercase Decryption (Wrong Direction)**  
   In decryption mode for uppercase letters, the shift key is **added** instead of being reversed, causing letters to move **further forward**.

3. **Non-Alphabetic Characters (Forced `+1` When Key=0)**  
   For characters outside `'A'..'Z'` or `'a'..'z'`, if the associated key is `0`, the module **increments** these characters by **1**, resulting in unintended transformations when no shift is expected.


---

## **Test Case Details**

Below are **three key test scenarios** that highlight each bug. For each test, the module is in **encryption** mode (if stated) or **decryption** mode, and we compare the **expected** vs. **actual** output to pinpoint the issues.

### **TC 1: Uppercase Encryption Wrap-Around**

| Mode    | Input Phrase | Key | Expected Output | Actual Output |
|---------|:------------:|:---:|:---------------:|:-------------:|
| Encrypt | XYZ          | 5   | CDE             | ]^_           |

---

### **TC 2: Uppercase Decryption in Wrong Direction**

| Mode    | Input Phrase (encrypted) | Key | Expected Output |     Actual Output     |
|---------|:------------------------:|:---:|:---------------:|:---------------------:|
| Decrypt | CDE                      | 5   | XYZ             | KLM (shifted forward) |
---

### **TC 3: Non-Alphabetic Characters with Zero Key**

| Mode    | Input Phrase |      Key      |        Expected Output       |       Actual Output      |
|---------|:------------:|:-------------:|:----------------------------:|:------------------------:|
| Encrypt | a1!@z        | 3, 1, 0, 0, 5 | d2!@e (or no shift if key=0) | d0"Ae (extra increments) |


---

Identify and fix these RTL Bugs to ensure the module behaves as expected in all scenarios.

## Current candidate files (line-numbered on patch targets)
### rtl/caesar_cipher.sv
```verilog
1| module caesar_cipher #(
   2|     parameter PHRASE_WIDTH = 32,  // e.g., enough for 4 chars (4×8=32)
   3|     parameter PHRASE_LEN   = PHRASE_WIDTH / 8
   4| )(
   5|     input  wire [PHRASE_WIDTH-1:0]       input_phrase,
   6|     input  wire [(PHRASE_LEN * 5) - 1:0] key_phrase,
   7|     input  wire                          decrypt,
   8|     output reg  [PHRASE_WIDTH-1:0]       output_phrase
   9| );
  10| 
  11|     integer i;
  12|     reg [7:0] current_char;
  13|     reg [4:0] current_key;
  14| 
  15|     always @(*) begin
  16|         // Initialize output to zero
  17|         output_phrase = {PHRASE_WIDTH{1'b0}};
  18| 
  19|         
  20|         if (PHRASE_LEN > 0) begin
  21|             for (i = 0; i < PHRASE_LEN; i = i + 1) begin
  22|                 // Extract current character & key
  23|                 current_char = input_phrase[i * 8 +: 8];
  24|                 current_key  = key_phrase[i * 5 +: 5];
  25| 
  26|              
  27|                 if (decrypt) begin
  28|                     if (current_char >= "A" && current_char <= "Z") begin
  29|                         output_phrase[i * 8 +: 8]
  30|                             = ((current_char - "A" + current_key + 26) % 26) + "A";
  31|                     end
  32|                     else if (current_char >= "a" && current_char <= "z") begin
  33|                         output_phrase[i * 8 +: 8]
  34|                             = ((current_char - "a" - current_key + 26) % 26) + "a";
  35|                     end
  36|                     else begin
  37|                         output_phrase[i * 8 +: 8] = current_char - current_key;
  38|                     end
  39|                 end
  40| 
  41|                 else begin
  42|                     if (current_char >= "A" && current_char <= "Z") begin
  43|                         output_phrase[i * 8 +: 8]
  44|                             = current_char + current_key;
  45|                     end
  46|                     else if (current_char >= "a" && current_char <= "z") begin
  47|                         output_phrase[i * 8 +: 8]
  48|                             = ((current_char - "a" + current_key) % 26) + "a";
  49|                     end
  50|                     else begin
  51|                         if (current_key == 0) begin
  52|                             output_phrase[i * 8 +: 8] = current_char + 1;
  53|                         end
  54|                         else begin
  55|                             output_phrase[i * 8 +: 8] = current_char - current_key;
  56|                         end
  57|                     end
  58|                 end
  59|             end
  60|         end
  61|     end
  62| 
  63| endmodule
```

## Files you must patch
rtl/caesar_cipher.sv

Primary module: `caesar_cipher`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=Test failed for input= gbU egI, key=[12, 15, 12, 19, 14, 9, 21, 10]. Expected: ,vnN.nbS, Got: vnhnbS
- cocotb: expected=? actual=Test failed for special characters input. Got: 	?
- cocotb: expected=? actual=Decryption failed. Expected: kueYkApI, Got: kueskUpI
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
0.00ns INFO     cocotb.regression                  running test_caesar_cipher.test_caesar_cipher_numeric_key (1/4)
                                                            Test Caesar Cipher RTL module with numeric key (random tests)
     4.00ns INFO     test                               Numeric Key Test:
                                                          Input Phrase:  gbU egI
                                                          Key Phrase: [12, 15, 12, 19, 14, 9, 21, 10]
                                                          Expected: ,vnN.nbS
                                                          DUT Output: vnhnbS
     4.00ns WARNING  ..y.test_caesar_cipher_numeric_key Test failed for input= gbU egI, key=[12, 15, 12, 19, 14, 9, 21, 10]. Expected: ,vnN.nbS, Got: vnhnbS
                                                        assert '\x14vnh\x12nbS' == ',vnN.nbS'
                                                        Traceback (most recent call last):
                                                          File "/src/test_caesar_cipher.py", line 84, in test_caesar_cipher_numeric_key
                                                            assert dut_output == expected_output, (
                                                        AssertionError: Test failed for input= gbU egI, key=[12, 15, 12, 19, 14, 9, 21, 10]. Expected: ,vnN.nbS, Got: vnhnbS
                                                        assert '\x14vnh\x12nbS' == ',vnN.nbS'
     4.00ns WARNING  cocotb.regression                  test_caesar_cipher.test_caesar_cipher_numeric_key failed
     4.00ns INFO     cocotb.regression                  running test_caesar_cipher.test_caesar_cipher_special_characters (2/4)
                                                            Test Caesar Cipher RTL module with special characters in the input
     9.00ns INFO     test                               Special Characters Test:
                                                          Input Phrase: !@#$%^&*
                                                          Key Phrase: [24, 1, 5, 20, 11, 25, 1, 18]
                                                          Expected Output: 9A(80w'<
                                                          DUT Output: 	?
                                                        E%
     9.00ns WARNING  ..caesar_cipher_special_characters Test failed for special characters input. Got: 	?
                                                        E%, Expected: 9A(80w'<
                                                        assert '\t?\x1e\x10\x1aE%\x18' == "9A(80w'<"
                                                        Traceback (most recent call last):
                                                          File "/src/test_caesar_cipher.py", line 135, in test_caesar_cipher_special_characters
                                                            assert dut_output == expected_output, (
                                                        AssertionError: Test failed for special characters input. Got: 	?
                                                        E%, Expected: 9A(80w'<
                                                        assert '\t?\x1e\x10\x1aE%\x18' == "9A(80w'<"
     9.00ns WARNING  cocotb.regression                  test_caesar_cipher.test_caesar_cipher_special_characters failed

14.00ns INFO     cocotb.regression                  running test_caesar_cipher.test_caesar_cipher_encryption_decryption (4/4)
                                                            Test Caesar Cipher RTL module: encryption followed by decryption
    19.00ns INFO     test                               Encryption-Decryption Test (Encryption phase):
                                                          Original Input: kueYkApI
                                                          Numeric Key: [14, 15, 7,

[... truncated 20213 chars from end of harness output ...]
```

## Cocotb test excerpt
### test_caesar_cipher.py
```python
# test_caesar_cipher_numeric_key.py
import cocotb
from cocotb.triggers import Timer
import random
import string

def caesar_cipher_sw(input_phrase, numeric_key, decrypt=False):
    """
    Calculate the Caesar Cipher result for a given input and numeric key.
    If decrypt=True, reverse the encryption.
    """
    result = []
    for i in range(len(input_phrase)):
        char = input_phrase[i]
        key = numeric_key[i]

        if decrypt:
            # Reverse the key for decryption
            key = -key

        if "A" <= char <= "Z":
            # Up

[... truncated 2840 chars from cocotb test excerpt ...]


    await Timer(2, unit="ns")

    # Prepare special characters input (truncated to PHRASE_LEN if needed)
    input_phrase = "!@#$%^&*()"[:PHRASE_LEN]
    numeric_key = [random.randint(0, 25) for _ in range(PHRASE_LEN)]

    # Convert to bit vectors
    input_phrase_bits = int.from_bytes(input_phrase.encode(), 'big')
    numeric_key_bits = 0
    for i, key_val in enumerate(numeric_key):
        shift_amount = 5 * (PHRASE_LEN - 1 - i)
        numeric_key_bits |= (key_val << shift_amount)

    # Drive DUT inputs
    dut.input_phrase.value = input_phrase_bits
    dut.key_phrase.value = numer
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/caesar_cipher.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
