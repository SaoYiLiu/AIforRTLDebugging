The String_to_ASCII_Converter module is designed to convert an 8-character input string into its corresponding ASCII values.  ASCII (American Standard Code for Information Interchange) is a character encoding standard that maps characters to specific numeric values, typically in the range of 0 to 127. A "string" is a sequence of characters represented in various encodings, such as UTF-8 or custom formats.

In this module, a custom encoding (char_in) is used for the input string, which maps characters to specific numeric ranges for easier processing within the module. During testing, it was observed that the buggy RTL failed to produce all outputs simultaneously in a single clock cycle. Instead, it generates sequential outputs across multiple clock cycles, indicating a timing or design issue that affects the expected parallel conversion of the input string to its ASCII values. 

---

## Input Format:
The char_in input array uses custom encoding, where each 8-bit value corresponds to a character's encoded value. This encoding is not equivalent to standard ASCII, and proper mapping must be applied during input preparation.

## Custom Encoding Scheme:
- Digits (0-9): Mapped to values 0 to 9.
- Uppercase Letters (A-Z): Mapped to values 10 to 35 (A = 10, B = 11, ..., Z = 35).
- Lowercase Letters (a-z): Mapped to values 36 to 61 (a = 36, b = 37, ..., z = 61).
- Special Characters (! to @): Mapped to values 62 to 95 (! = 62, " = 63, ..., @ = 95).

## Observed Behavior
During testing, the following issues were observed:
1. The `ascii_out` values appeared sequentially across multiple clock cycles.
2. The `valid` signal remained asserted during this time, indicating ongoing processing instead of immediate completion.

### Test Sequence

| Clock Cycle | start | char_in    | Expected ascii_out                | Actual ascii_out             | valid | ready |
|-------------|-------|------------|-----------------------------------|------------------------------|-------|-------|
| 1           | 1     | "A1b!C3d@" | [65, 49, 98, 33, 67, 51, 100, 64] | [0, 0, 0, 0, 0, 0, 0, 0]     | 1     | 0     |
| 2           | 0     | "A1b!C3d@" | [0, 0, 0, 0, 0, 0, 0, 0]          | [65, 0, 0, 0, 0, 0, 0, 0]    | 1     | 0     |
| 3           | 0     | "A1b!C3d@" | [0, 0, 0, 0, 0, 0, 0, 0]          | [65, 49, 0, 0, 0, 0, 0, 0]   | 1     | 0     |
| 4           | 0     | "A1b!C3d@" | [0, 0, 0, 0, 0, 0, 0, 0]          | [65, 49, 98, 0, 0, 0, 0, 0]  | 1     | 0     |
| 5           | 0     | "A1b!C3d@" | [0, 0, 0, 0, 0, 0, 0, 0]          | [65, 49, 98, 33, 0, 0, 0, 0] | 1     | 0     |

---

## Expected Behavior

When `start` is asserted:
- All 8 characters from the input `char_in` should be processed simultaneously.
- The ascii_out array should contain the ASCII values corresponding to all input characters within 1 clock cycle, and it should be reset to all zeros after processing is completed to ensure proper initialization for subsequent operations.
- The `valid` signal should be asserted in the same cycle, and `ready` should deassert until processing is complete.

When processing completes:
- The `ready` signal should assert to indicate readiness for new inputs.
- The `valid` signal should deassert.

### Expected Output (within 1 clock cycle):
- **ASCII values**: [65, 49, 98, 33, 67, 51, 100, 64]
- **valid**: Should assert immediately after `start`.
- **ready**: Should deassert during processing and assert immediately after completion.

---

## Example Test Case Behavior

**Input:**
- `char_in = ["A", "1", "b", "!", "C", "3", "d", "@"]`
- `start = 1`

**Expected Output:**
- **ascii_out**: [65, 49, 98, 33, 67, 51, 100, 64]
- **valid**: 1 (asserted immediately after start)
- **ready**: 0 (deasserted during processing, asserted after completion)

**Actual Output (spread across cycles):**

| Clock Cycle | ascii_out Values                  | valid | ready |
|-------------|-----------------------------------|-------|-------|
| 1           | [65, 0, 0, 0, 0, 0, 0, 0]         | 1     | 0     |
| 2           | [65, 49, 0, 0, 0, 0, 0, 0]        | 1     | 0     |
| 3           | [65, 49, 98, 0, 0, 0, 0, 0]       | 1     | 0     |
| 4           | [65, 49, 98, 33, 0, 0, 0, 0]      | 1     | 0     |
| 5           | [65, 49, 98, 33, 67, 0, 0, 0]     | 1     | 0     |
| 6           | [65, 49, 98, 33, 67, 51, 0, 0]    | 1     | 0     |
| 7           | [65, 49, 98, 33, 67, 51, 100, 0]  | 1     | 0     |
| 8           | [65, 49, 98, 33, 67, 51, 100, 64] | 1     | 1     |

---


- Identify and fix the RTL bug to ensure that all outputs (ascii_out) are generated in parallel within a single clock cycle when the start signal is asserted.
