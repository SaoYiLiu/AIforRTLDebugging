The `data_serializer` module converts parallel input data into serial output data in **Verilog**. It supports configurable serialization modes (`BIT_ORDER`) and optional parity (`PARITY`). The module exhibits **two distinct bugs** that disrupt serialization under specific configurations. Your task is to **identify and fix these bugs** to make sure the module matches its specifications.

---

### **Design Specifications**

#### **Input and Output Port List**
| **Port Name**      | **Polarity** | **Width** | **Description**                         |
|--------------------|--------------|-----------|-----------------------------------------|
| `clk`              | Input        | 1         | System clock signal                     |
| `reset`            | Input        | 1         | Active-high synchronous reset           |
| `p_valid_i`        | Input        | 1         | Parallel data valid input               |
| `p_data_i`         | Input        | `DATA_W`  | Parallel data input bus                 |
| `s_ready_i`        | Input        | 1         | Serial output ready input               |
| `tx_en_i`          | Input        | 1         | Enable signal for data transmission     |
| `p_ready_o`        | Output       | 1         | Parallel data ready output              |
| `s_valid_o`        | Output       | 1         | Serial data valid output                |
| `s_data_o`         | Output       | 1         | Serialized data output                  |

---

#### **Parameters**
| **Parameter** | **Default** | **Description**                                      |
|---------------|-------------|------------------------------------------------------|
| `DATA_W`      | `8`         | Width of the parallel input data                     |
| `BIT_ORDER`   | `0`         | Serialization order: 0 => LSB-first, 1 => MSB-first  |
| `PARITY`      | `0`         | Parity configuration: 0 => None, 1 => Even, 2 => Odd |

---

#### **Clock and Reset Definition**
- **Clock (`clk`):** Positive edge-triggered signal.
- **Reset (`reset`):** Active-high synchronous reset.
  - On reset, the module clears all outputs (`p_ready_o`, `s_valid_o`, `s_data_o`) and initializes the internal FSM to the `ST_RX` state.

---

### **Functional Description**

1. **LSB-First Mode (`BIT_ORDER = 0`)**:
   - Data is serialized starting from the least significant bit.
   - If parity is enabled, it is appended as the most significant bit in the serialized stream.

2. **MSB-First Mode (`BIT_ORDER = 1`)**:
   - Data is serialized starting from the most significant bit.
   - If parity is enabled, it is appended as the least significant bit in the serialized stream.

---

### **Bug Analysis**

#### **Bug #1: Nibble Scrambling during Parallel Data Load**
- **Issue:** When `BIT_ORDER = 1` (MSB-first) and `PARITY != 0`, the module incorrectly swaps the high nibble (bits `[7:4]`) and low nibble (bits `[3:0]`) of the parallel input data during loading into the shift register (`shift_reg_d`).
- **Expected Behavior:** The parallel data should be loaded without modification, and the parity bit should be appended as per the `BIT_ORDER` specification.

#### **Bug #2: Extra Shifts during MSB-First Serialization**
- **Issue:** In the `ST_TX` state, the module performs an additional 2-bit shift for `BIT_ORDER = 1` and `PARITY != 0`. This misaligns the serialized output, resulting in incorrect data transmission.
- **Expected Behavior:** Data should shift by 1 bit per clock cycle, maintaining alignment with the specified bit order.

---

### **Simulation Results (Error Analysis)**

Below are the observed simulation results, highlighting the failing test cases:

| **Test Case** | **Configuration**                  | **Inputs**            | **Expected Output** | **Actual Output** | **Status** |
|---------------|------------------------------------|-----------------------|---------------------|-------------------|------------|
| 1             | `BIT_ORDER = 1`, `PARITY = 1`      | `p_data_i = 8'hA5`    | `101001010`         | `010110010`       | **FAIL**   |
| 2             | `BIT_ORDER = 1`, `PARITY = 2`      | `p_data_i = 8'h3C`    | `001111000`         | `000011100`       | **FAIL**   |

---

### **Expected Behavior**

1. **Parallel Data Load**:
   - **No parity (`PARITY = 0`)**: Load the parallel data into `shift_reg_d` unmodified.
   - **With parity (`PARITY = 1 or 2`)**: Append the parity bit to the data according to the `BIT_ORDER` specification.

2. **Serialization**:
   - Shift out one bit per clock cycle, preserving the order specified by `BIT_ORDER`.
   - Ensure proper alignment of the parity bit.

---

### **Waveform Analysis**

#### **Nibble Scrambling Test Case**
```wavedrom
{
  "signal": [
    {"name": "clk", "wave": "p..........."},
    {"name": "p_data_i", "wave": "3...........", "data": "8'hA5"},
    {"name": "shift_reg_d (Expected)", "wave": "2...........", "data": "101001010"},
    {"name": "shift_reg_d (Actual)", "wave": "4...........", "data": "010110010"}
  ]
}
```

#### **Extra Shifts Test Case**
```wavedrom
{
  "signal": [
    {"name": "clk", "wave": "p..........."},
    {"name": "shift_reg_q", "wave": "3...........", "data": "101001010"},
    {"name": "s_data_o (Expected)", "wave": "2...........", "data": "1,0,1,0,0,1,0,1,0"},
    {"name": "s_data_o (Actual)", "wave": "4...........", "data": "0,1,0,1,1,0,0,1,0"}
  ]
}
```

---

Fix the RTL to align with the design specifications and ensure correct functionality under all configurations.
