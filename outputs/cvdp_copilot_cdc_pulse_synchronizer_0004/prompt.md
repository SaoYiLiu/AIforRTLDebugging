The `cdc_pulse_synchronizer` module synchronizes a single pulse from a source clock domain (`src_clock`) to a single pulse in the destination clock domain (`des_clock`). However, during testing with a **source clock frequency of 100 MHz** and a **destination clock frequency of 250 MHz**, it was found that the module exhibited an unexpected behavior. Instead of generating a single pulse in the destination clock domain, it generated two pulses for a single pulse in the source clock domain.

Identify and Fix the RTL Bug to ensure that only a single pulse is generated in the destination clock domain for each pulse in the source clock domain.

**Test Case Details:**
- **Source Clock Frequency (`src_clock`):** 100 MHz
- **Destination Clock Frequency (`des_clock`):** 250 MHz
- **Input:** A single pulse on `src_pulse`
- **Expected Output:** A single pulse on `des_pulse`
- **Actual Output:** Two pulses on `des_pulse`

### Waveform for CDC pulse synchronization (src_clock frequency: 100MHz, des_clock frequency: 250MHz):

```wavedrom
{
  "signal": [
    {"name": "src_clock", "wave": "0.1.0.1.0.1.0.1.0.1"},
    {"name": "des_clock", "wave": "0101010101010101010"},
    {"name": "rst_in", "wave": "10................."},
    {"name": "src_pulse", "wave": "0.1...0............"},
    {"name": "des_pulse(Expected)", "wave": "0......1.0........."},
    {"name": "des_pulse(RTL Bug)", "wave": "0......1.0...1.0..."}
  ],
  "config": {
    "hscale": 1
  },
  "head": {
    "text": "Functionality with src_clock = 100MHz, des_clock = 250MHz"
  }
}
```
