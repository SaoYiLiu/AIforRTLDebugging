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
