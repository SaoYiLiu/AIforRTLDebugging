The `fsm_seq_detector` module is designed to detect the sequence `01001110` in a continuous bit stream provided on `seq_in` from MSB to LSB. However, during testing, it was observed that the module fails to detect the sequence when it is present in the input stream. This results in the `seq_detected` signal not asserting HIGH as expected.

#### Test Case Details:
- **Input Sequence**: `1101001110100111000` from MSB to LSB.
- **Expected Output**: The `seq_detected` signal should assert HIGH **twice**, once for each sequence `01001110` occurrence in the input. 
- **Actual Output**: The `seq_detected` signal remains LOW, indicating that the sequence was undetected in both occurrences.

#### Waveform for given Test Case:
```wavedrom
{
  "signal": [
    {"name": "clk_in", "wave": "010101010101010101010101010101010101010"},
    {"name": "rst_in", "wave": "10....................................."},
    {"name": "seq_in", "wave": "01...0.1.0...1.....0.1.0...1.....0....."},
    {"name": "seq_detected(Expected)", "wave": "0....................1.0...........1.0."},
    {"name": "seq_detected(RTL Bug)", "wave": "0......................................"}
  ],
  "config": {
    "hscale": 1
  },
  "head": {
    "text": "Teast Case with Sequence Input: 1101001110100111000"
  }
}
```
Identify and fix the RTL bug to ensure the `fsm_seq_detector` module correctly detects the sequence `01001110` and asserts `seq_detected` HIGH for one clock cycle when the sequence is detected.
