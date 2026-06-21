The ```apb_dsp_op``` module in the provided buggy RTL is designed to use an APB interface for performing DSP operations on an SRAM where DSP operation can be performed with the APB interface clock or a faster clock. However, during testing, it was observed that the module fails to follow the APB handshake mechanism. Specifically, the PSLVERR should be asserted when an invalid APB address is accessed (PSEL = 1'b1, PENABLE = 1'b1, and address out of valid range). In addition, the selection between clk_dsp and PCLK clock signals is performed using a direct MUX-based clock switching mechanism, which is discouraged because it can introduce design hazards, clock domain crossing issues (CDC), and it is generally considered poor practice.

### Interface

 The following table presents the ```apb_dsp_op```  interface:

| Signal     | Width | Samples | In/Out | Description                              |
|------------|-------|---------|--------|------------------------------------------|
| clk_dsp    | 1     | 1       | Input  | Faster clock of 500 MHz to DSP operation |
| en_clk_dsp | 1     | 1       | Input  | Enable faster DSP clock                  |
| PCLK       | 1     | 1       | Input  | APB clock of 50 MHz                      |
| PRESETn    | 1     | 1       | Input  | Active low asynchronous APB Reset        |
| PADDR      | 8     | 1       | Input  | APB address                              |
| PWRITE     | 1     | 1       | Input  | Write/Read enable                        |
| PWDATA     | 32    | 1       | Input  | Write data                               |
| PSEL       | 1     | 1       | Input  | DSP selector                             |
| PENABLE    | 1     | 1       | Input  | APB enable                               |
| PRDATA     | 32    | 1       | Output | Read data                                |
| PREADY     | 1     | 1       | Output | Ready signal                             |
| PSLVERR    | 1     | 1       | Output | Error signal                             |

### APB Transaction Timing

An **APB protocol** transaction consists of a **setup phase** (where the address and control signals are set) and an **access phase** (where data is transferred when `PENABLE` is asserted). The **slave responds with `PREADY`** to indicate that the transaction is complete and provides the **read data (`PRDATA`) if it is a read operation**. Additionally, the slave **asserts `PSLVERR` to flag an error** when an invalid operation occurs (e.g., accessing an invalid address). 

**Write Cycle (PWRITE = 1):**

- T0: Master asserts PSEL and PWRITE, sets PADDR and PWDATA.
- T1: Master asserts PENABLE, and the slave must set PREADY = 1 immediately (since no wait states).
- T2: Transaction completes when PSEL is deasserted.

**Read Cycle (PWRITE = 0):**

- T0: Master asserts PSEL with target PADDR.
- T1: Master asserts PENABLE, and the slave must set PRDATA and PREADY = 1 immediately.
- T2: Master reads PRDATA, and the transaction completes when PSEL is deasserted.

### Correct PREADY and PSLVERR Handling

PREADY behavior:
- At the start of an APB transaction, the master asserts PSEL and sets the address (PADDR), but PENABLE remains low in this initial cycle. At this stage, PREADY is undefined.

- In the following clock cycle, when PENABLE is asserted (1'b1), the slave must immediately assert PREADY (1'b1), indicating that it is ready to complete the transaction. Since the slave does not support wait states, PREADY is always high during the second phase of the APB transaction.

- Once the master deasserts PSEL, the transaction is considered complete, and PREADY becomes undefined again until the next transaction is initiated.

PSLVERR behavior:
- When a transaction begins, the APB master asserts PSEL and sets the target address (PADDR). At this stage, the PENABLE signal is still low, and PSLVERR remains undefined.

- In the next clock cycle, when PENABLE is asserted (1'b1), the slave evaluates whether the requested transaction is valid. If the operation is correct (i.e., a valid register is accessed or an SRAM address is within range), PSLVERR remains low (0).

- However, if the transaction contains an error, such as accessing an invalid register, attempting a write operation on a read-only register, or addressing an out-of-bounds SRAM location, the slave asserts PSLVERR (1'b1) during the same cycle that PENABLE is high.

- Regardless of whether PSLVERR is asserted or not, PREADY must always be high (1'b1) in a no-wait-state slave, ensuring that the transaction completes in a single clock cycle. After the APB master deasserts PSEL, both PREADY and PSLVERR become undefined until the next transaction begins.

### Clock Domain Crossing (CDC) Synchronization

**Clock Domain Crossing (CDC)** refers to the process of transferring data or control signals between different clock domains in a digital system. A **clock domain** consists of a group of registers and logic that operate under the same clock signal. When a signal transitions from one clock domain to another, **timing issues such as metastability, data corruption, or race conditions can occur**, especially if the two clocks are asynchronous or have different frequencies. To ensure reliable data transfer, these issues must be addressed using appropriate synchronization techniques:

- en_clk_dsp comes from APB (PCLK) but is used in DSP (clk_dsp). Using en_clk_dsp directly in clk_dsp domain without synchronization can result in metastability, glitches, and timing violations. A dual-flop synchronizer or CDC FIFO is recommended.

- SRAM read data (sram_data_out) should be generated in clk_dsp but is used in PCLK. Without synchronization, APB reads could capture invalid data.

- SRAM writes are triggered by APB (PCLK), but memory updates should happen in clk_dsp. If sram_we changes unpredictably, it can cause glitches in memory updates.

### Parameters
- **ADDR_WIDTH**: Width of the address (8 bits).
- **DATA_WIDTH**: Width of the data (32 bits).

### Register Bank
| Register       | Address | Default Value | Permission | Description                                              |
|----------------|---------|---------------|------------|----------------------------------------------------------|
| REG_OPERAND_A  | 0x00    | 32'h0         | W/R        | Holds the SRAM address to read the value for operand A   |
| REG_OPERAND_B  | 0x01    | 32'h0         | W/R        | Holds the SRAM address to read the value for operand B   |
| REG_OPERAND_C  | 0x02    | 32'h0         | W/R        | Holds the SRAM address to read the value for operand C   |
| REG_OPERAND_O  | 0x03    | 32'h0         | W/R        | Holds the SRAM address to write the value for operand O  |
| REG_CONTROL    | 0x04    | 32'h0         | W/R        | Holds the value equivalent to the operation control mode |
| REG_WDATA_SRAM | 0x05    | 32'h0         | W/R        | Holds the data to be written to SRAM                     |
| REG_ADDR_SRAM  | 0x06    | 32'h0         | W/R        | Holds the address to be read or written to SRAM          |

### Control Modes

The module operates in different control modes, which are configured according to the value in the internal register ```reg_control```. The operating modes are described below:
   - 32'd1: Enables writing to SRAM.
   - 32'd2: Enables reading from SRAM.
   - 32'd3: Enables reading the A operand.
   - 32'd4: Enables reading the B operand.
   - 32'd5: Enables reading the C operand.
   - 32'd6: Enables writing the O operand.
   - Other values: Only performs write and read operations on internal registers.

At reset, PREADY must initialize to 1'b0 and transition to 1'b1 only after detecting a valid APB transaction, `PSLVERR` should be cleared on reset. When both `PSEL` and `PENABLE` are asserted, `PSLVERR` should be set if `PADDR` is invalid or if the SRAM address is out of bounds, otherwise, `PSLVERR` should be deasserted. Additionally, synchronize the SRAM to the same clock domain as the DSP to ensure consistency in memory operations. Identify and fix any RTL bugs to guarantee the correct APB handshake, considering that this implementation does not support wait states. Address clock domain crossing (CDC) issues by implementing a clock domain synchronizer, such as a dual-flop synchronizer or an asynchronous FIFO, for data transfer between the APB and DSP clock domains. Also, ensure a proper selection mechanism between clk_dsp and PCLK to prevent potential metastability or glitches.
