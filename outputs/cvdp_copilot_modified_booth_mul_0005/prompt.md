The provided pipelined_modified_booth_multiplier` implements a **Pipelined Modified Booth Multiplier** for 16-bit signed multiplication of two binary numbers using a pipeline architecture. 

This design leverages the Modified Booth algorithm, which encodes the multiplier into groups of three bits to reduce the number of partial products. Each bit group dictates an add, subtract, or no operation on the multiplicand, streamlining the multiplication process and enhancing performance by executing these operations across multiple pipeline stages. 

The results from the design do not match the expected value. Identify and correct the issues in the given SystemVerilog code to get the expected behavior.
---

### **Interface Specifications**

**Inputs**:
- `clk`: Clock signal for synchronization. (synchronized to positive edge of this clock)
- `rst`: Asynchronous active high reset to clear all registers and set outputs to zero.
- `start`: Active high start signal to initiate multiplication.
- `[15:0] X, Y`: 16-bit signed integers to be multiplied.

**Outputs**:
- `[31:0] result`: Result of the multiplication (32-bit signed integer).
- `done`: Active high signal to indicate completion of the multiplication process.

---

### Detailed Explanation of Each Pipeline Stage:


### 1. **Input Registering and Control Initialization**
- **Action:** Inputs `X` and `Y` are latched into `X_reg` and `Y_reg`. 

### 2. **Booth Encoding and Partial Product Generation**
- **Action:**The Booth encoding process is performed on the latched input multiplier `Y_reg`. The multiplier is divided into overlapping groups of 3 bits (each pair of bits plus an additional boundary bit). Each group determines whether the multiplicand `X_reg` is added, subtracted, or ignored, and the resulting operation is stored in partial_products.
- Each group of 3 bits is Booth encoded to decide the operation performed on the multiplicand:
  - `000` or `111`: No operation (`0`).
  - `001` or `010`: Add the multiplicand (`+X`).
  - `011`: Add twice the multiplicand (`+2X`).
  - `100`: Subtract twice the multiplicand (`-2X`).
  - `101` or `110`: Subtract the multiplicand (`-X`).
- The result of the encoded operation is left-shifted to align it with the correct bit position in the final product.
- The amount of the left shift is determined by the position of the group in the multiplier, counting from the least significant bit (LSB) towards the most significant bit (MSB).
  - Left Shift Amount: Equal to twice the group index, where the group index starts at 0 for the group closest to the LSB. 


### 3. **Partial Product Reduction**
- **Action:** This stage reduces the number of partial products. `s1` and `s2` combine the first six partial products while `temp_products1` and `temp_products2` temporarily hold the remaining. This prepares for a more manageable summation in the next stage.

### 4. **Final Summation**
- **Action:** Combines the intermediate sums (`s1` and `s2`) and the temporary products into two final partial sums (`s3` and `s4`).

### 5. **Output Result**
- **Action:** Adds the final partial sums (`s3` and `s4`) to compute the final multiplication result.. The `done` signal is asserted, indicating the completion of the multiplication process and the availability of the result.


### Additional Notes:
- A shift register propagates the start signal through the pipeline to maintain synchronization and indicate the timing of valid outputs.
- **Cycle Accuracy:** Each pipeline stage is designed to complete its processing within a single clock cycle, 
- **Data Latency:** Given that each of the five stages processes in one cycle, the total data latency from input to output is 5 cycles. 

--- 

| Count | X      | Y      | Actual Result | Expected Result | Status |
|-------|--------|--------|---------------|-----------------|--------|
| 1     | 13732  | 24065  | 13707         | 330460580       | Fail   |
| 2     | -10615 | 22115  | 968106013     | -234750725      | Fail   |
| 3     | 31629  | -26355 | 25809         | -833582295      | Fail   |
| 4     | -31515 | 21010  | -808184022    | -662130150      | Fail   |
| 5     | -7295  | -13043 | -791942973    | 95148685        | Fail   |
| 6     | -3594  | -12995 | -993266379    | 46704030        | Fail   |
| 7     | 22509  | -2292  | -4303         | -51590628       | Fail   |
| 8     | -5639  | 9286   | -1539569692   | -52363754       | Fail   |
