The given `axi_alu` module is designed to implement a configurable arithmetic/logic processing unit that can be dynamically controlled by a host via an AXI4 interface. The design integrates an AXI4-based control interface with a digitalsignal processing (DSP) engine, a memory block, and clock-domain management with Clock Domain Crossing (CDC) synchronization. However, during testing, it was observed that the module is not functioning as expected as given in the `Actual Behavior` section below.

## Specifications

- **Module Name**: `axi_alu`
- Table of inputs/outputs for `axi_alu` module :

| **Port Name**      | **Direction** | **Width** | **Description**                               |
|--------------------|---------------|-----------|-----------------------------------------------|
| **axi_clk_in**     | Input         | 1         | Slow clock input for AXI transactions         |
| **fast_clk_in**    | Input         | 1         | Fast clock input for high-speed processing    |
| **reset_in**       | Input         | 1         | Active-high reset signal                      |
| **axi_awaddr_i**   | Input         | 32        | Write address for AXI write transactions      |
| **axi_awvalid_i**  | Input         | 1         | Write address valid signal                    |
| **axi_awready_o**  | Output        | 1         | Write address ready signal                    |
| **axi_wdata_i**    | Input         | 32        | Write data input                              |
| **axi_wstrb_i**    | Input         | 4         | Write strobe (byte-wise write enable)         |
| **axi_wvalid_i**   | Input         | 1         | Write data valid signal                       |
| **axi_wready_o**   | Output        | 1         | Write data ready signal                       |
| **axi_bvalid_o**   | Output        | 1         | Write response valid signal                   |
| **axi_bready_i**   | Input         | 1         | Write response ready signal                   |
| **axi_araddr_i**   | Input         | 32        | Read address input                            |
| **axi_arvalid_i**  | Input         | 1         | Read address valid signal                     |
| **axi_arready_o**  | Output        | 1         | Read address ready signal                     |
| **axi_rdata_o**    | Output        | 32        | Read data output                              |
| **axi_rvalid_o**   | Output        | 1         | Read data valid signal                        |
| **axi_rready_i**   | Input         | 1         | Read data ready signal                        |
| **result_o**       | Output        | 64        | DSP block result output                       |

### Actual Behavior:
1. **CDC Logic:**
   - The CDC synchronizers in the given RTL are not correctly gated by the `clock_control` signal. This is leading to incorrect data synchronization when switching between clock domains, leading to potential metastability issues.

2. **AXI Interface:**
   - The AXI write and read logic in the `axi_csr_block` do not correctly handle burst transactions, leading to incorrect address updates and data transfers when AXI Burst transactions are used to initialize RAM memory.
   - Specifically, INCR burst Write transaction Fails as Write address is stuck at start Address. 

3. **Memory Block:**
   - The memory block in the given RTL does not correctly handle the RAM Control and data signals, leading to incorrect writes to the memory array.
   - The `result_address` is not correctly updated, causing incorrect result storage in CSR register

4. **DSP Block:**
   - The DSP block does not correctly pass the result value to CSR, leading to incorrect computation of results when AXI reads result register from CSR Block.
   - DSP result output is not stored in the CSR register.


### Expected Behavior:
1. **Clock Domain Crossing (CDC):**
   - When `clock_control` is HIGH, the design should operate on the `fast_clk_in` domain, and CDC synchronizers should be used to safely transfer data between the `axi_clk_in` and `fast_clk_in` domains. 
      - In this case, The CSR register output signals (`operand_a_addr`, `operand_b_addr`, `operand_c_addr`, `op_select`, `start`)  that are used by DSP block need to be synchronized with CDC double flop synchronizer.
      - CSR input signal (`dsp_result`) from DSP block also need to be synchronized with double flop synchronizer.
   - When `clock_control` is LOW, the design should operate on the `axi_clk_in` domain, and no CDC synchronization should be applied.

2. **AXI Interface:**
   - The AXI interface should correctly handle write and read transactions, including burst transfers, and update the CSR registers accordingly.
   - Burst Transfer signals (`axi_awlen_i`, `axi_awsize_i`, `axi_awburst_i`, `axi_wlast_i`, `axi_arlen_i`, `axi_arsize_i`, `axi_arburst_i`, `axi_rlast_o`) and related response signals (`axi_rresp_o`, `axi_bresp_o`) should be added.
   
| **Address Offset** | **Register Name**       | **Width** | **Description**                                                                 | **Access** |
|--------------------|-------------------------|-----------|---------------------------------------------------------------------------------|------------|
| `0x00`             | `operand_a_addr`        | 32-bit    | Holds the address for operand A in the memory block.                            | Read/Write |
| `0x04`             | `operand_b_addr`        | 32-bit    | Holds the address for operand B in the memory block.                            | Read/Write |
| `0x08`             | `operand_c_addr`        | 32-bit    | Holds the address for operand C in the memory block.                            | Read/Write |
| `0x0C`             | `op_select`             | 2-bit     | Selects the operation to be performed by the DSP block[1:0]                     | Read/Write |
| `0x0C`             | `start`                 | 1-bit     | Starts the DSP operation when set to `1`[2].                                    | Read/Write |
| `0x10`             | `clock_control`         | 1-bit     | Controls the clock selection:<br> - `0`: AXI clock<br> - `1`: Fast clock        | Read/Write |
| `0x14` to `0x1C`   | Reserved                | -         | Reserved for future use.                                                        | -          |
| `0x20` to `0x5C`   | Memory Data Registers   | 32-bit    | Stores data in the memory block. Each address corresponds to a memory location. | Read/Write |
| `result_address`   | `result_address`        | 32-bit    | Outputs the value stored in the first memory location (`ram[0]`).               | Read-Only  |


3. **Memory Block:**
   - The memory block should implement a RAM (16 locations, 32-bit each) that allows synchronous writes and asynchronous reads, with the ability to store and retrieve data based on the provided addresses from above given CSR registers.
    - **Memory Initialization**:
      - On reset (`reset_in` is high), all 16 memory locations are initialized to `0`.
      - The `result_address` output used to store DSP block result is also reset to `0`.
    - **Synchronous Write Operation**:
      - Writes are performed on the rising edge of `axi_clk`.
      - When `we` is high, the `write_data` is written into the memory location specified by `write_address`.
      - The value of `ram[0]` is also copied to the `result_address` output during initial memory Initialization phase.
    - **Asynchronous Read Operation**:
      - Reads are performed on the rising edge of `ctrld_clk` (can be AXI clock or Fast clock).
      - The data from the memory locations specified by `address_a`, `address_b`, and `address_c` are read and assigned to `data_a`, `data_b`, and `data_c`, respectively and send to DSP block.
      - If `reset_in` is high, the outputs `data_a`, `data_b`, and `data_c` are reset to `0`.

4. **DSP Block:**
   - The DSP block should perform the selected arithmetic operation (based on `op_select`) when the `start` signal is asserted, and the result should be available in the `result` output which is passed to CSR block.

### **Test Case 1: AXI Burst Write Operation**
#### **Objective:**
To validate the AXI burst write functionality by checking the correctness of memory writes. The test ensures that data is written sequentially across multiple addresses in a burst transaction.

#### **Test Parameters:**
- **Test Case Name:** `test_burst_write_transaction`
- **Burst Length:** `16` 
- **Clock Frequency:** 
  - **AXI Clock (`axi_clk_in`)**: `50 MHz` (20 ns period)
  - **Fast Clock (`fast_clk_in`)**: `100 MHz` (10 ns period)

#### **Memory Contents After Burst Write:**
Below is a table showing the memory contents after the burst operation:

| AXI Address| Memory Data (Expected)  | Memory Data (Actual)|
|------------|-------------------------|---------------------|
| 0x00000020 | 0x00000005              | 0x00000000          |
| 0x00000024 | 0x00000006              | 0x00000000          |
| 0x00000028 | 0x00000007              | 0x00000000          |
| 0x0000002C | 0x00000008              | 0x00000000          |
| 0x00000030 | 0x00000009              | 0x00000000          |
| 0x00000034 | 0x0000000A              | 0x00000000          |
| 0x00000038 | 0x0000000B              | 0x00000000          |
| 0x0000003C | 0x0000000C              | 0x00000000          |
| 0x00000040 | 0x0000000D              | 0x00000000          |
| 0x00000044 | 0x0000000E              | 0x00000000          |
| 0x00000048 | 0x0000000F              | 0x00000000          |
| 0x0000004C | 0x00000010              | 0x00000000          |
| 0x00000050 | 0x00000011              | 0x00000000          |
| 0x00000054 | 0x00000012              | 0x00000000          |
| 0x00000058 | 0x00000013              | 0x00000000          |
| 0x0000005C | 0x00000014              | 0x00000000          |

### **Test Case 2: AXI ALU Operations** 
#### **Objective:**
To validate the AXI ALU operations for different arithmetic computations, including Multiply-Accumulate (MAC), Multiplication, Right Shift, and Division.

#### **Test Parameters:**
- **Test Case Name:** `test_axi_alu_incremental_data`
- **Clock Control:** `1` (Fast Clock Enabled)
- **Operations Tested:**
  - **0b100** → Multiply-Accumulate (MAC) 
  - **0b101** → Multiplication 
  - **0b110** → Right Shift 
  - **0b111** → Division 

#### **Test Inputs & Results:**
| Test # | op_a | op_b | op_c | op_select            | Clock Ctrl | Expected Result| Actual (Buggy) Result|
|--------|------|------|------|----------------------|------------|----------------|----------------------|
| 1      | 0xA  | 0x5  | 0x2  | 0b00 (MAC)           | 1          | 0xAF           | 0x00                 |
| 2      | 0x4  | 0xA  | 0x6  | 0b01 (Multiplication)| 1          | 0x87           | 0x00                 |
| 3      | 0x4  | 0x0  | 0xE  | 0b10 (Right Shift)   | 1          | 0x00           | 0x00                 |
| 4      | 0x6  | 0xC  | 0xF  | 0b11 (Division)      | 1          | 0x00           | 0x00                 |


Identify and fix the RTL bugs to ensure the correct behaviour.
