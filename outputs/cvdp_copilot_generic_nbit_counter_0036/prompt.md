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
