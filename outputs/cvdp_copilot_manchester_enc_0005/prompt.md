Identify and fix the latch inference issue in the provided **Manchester Encoder** module. 

---

**Specifications:**

1. **Module Name:** `manchester_encoder`

2. **Parameters:**

   - `N` (default value: 8) which defines the width of the input data bus (`enc_data_in`).

3. **Expected Behaviour of Encoding process:**
Table for Manchester Encoding (`N=3`, input data from `0` to `7`):
When `enc_valid_in` is '0', the Expected output of `enc_data_out` should be 6'b000000. But with Latch Inference, This output will become unexpected and will corrupt the communication system

| Clock Cycle | clk_in | rst_in | enc_valid_in | enc_data_in | enc_valid_out | enc_data_out (expected)   | enc_data_out (with Latch)
|-------------|--------|--------|--------------|-------------|---------------|-----------------|-----------------|
| 1           | Rising | 1      | 1            | 3'b000      | 0             | 6'b000000       | 6'b000000
| 2           | Rising | 0      | 1            | 3'b000      | 1             | 6'b101010       | 6'b101010
| 3           | Rising | 0      | 1            | 3'b001      | 1             | 6'b101001       | 6'b101001
| 4           | Rising | 0      | 1            | 3'b010      | 1             | 6'b100110       | 6'b100110
| 5           | Rising | 0      | 1            | 3'b011      | 1             | 6'b100101       | 6'b100101
| 6           | Rising | 0      | 1            | 3'b100      | 1             | 6'b011010       | 6'b011010
| 7           | Rising | 0      | 1            | 3'b101      | 1             | 6'b011001       | 6'b011001 
| 8           | Rising | 0      | 0            | 3'b110      | 0             | **6'b000000**       | **6'b011001**
| 9           | Rising | 0      | 0            | 3'b111      | 0             | **6'b000000**       | **6'b011001**

---
