Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_galois_encryption_0001

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
The `galois_encryption` module can encrypt or decrypt a data input with a provided key by performing Galois Field operations. The module has two main input interfaces: The first updates the key, and the second sends the valid input data with the desired operation (encrypt or decrypt). The module operates synchronously in the rising edge of a clock (`clk`) and an asynchronous active low reset signal (`rst_async_n`), that resets its control registers.

To perform Galois Field operations, each byte is interpreted as one of the 256 elements of a finite field, also known as Galois Field, denoted by GF(2<sup>8</sup>). Two operations are performed in these bytes: multiplication and addition. To define those operations, each byte `b` (b<sub>7</sub>, b<sub>6</sub>, b<sub>5</sub>, b<sub>4</sub>, b<sub>3</sub>, b<sub>2</sub>, b<sub>1</sub>, b<sub>0</sub>) is interpreted as a polynomial, denoted by `b(x)`, such as: $`b(x) = \sum_{k=0}^7 b_k * x^k`$.

In this context, these operations can be described as:
1. Addition: Defined as an XOR operation.
   * Example: If an addition of 8'h57 is performed with 8'h83, the result must be 8'hd4.
2. Multiplication: Defined in two steps, where within both steps the individual coefficients of the polynomials are reduced modulo 2:
   1. The two polynomials that represent the bytes are multiplied as polynomials.
   2. The resulting polynomial is reduced modulo the following fixed polynomial: $`m(x) = x^8 + x^4 + x^3 + x + 1`$. In hexadecimal notation, this polynomial is represented as 0x11B (since its coefficients map to the bits 100011011 = 0x11B).
   * The modular reduction by `m(x)` may be applied to intermediate steps in the calculation. In particular, the product `b*8'h02`, where `b` represents a byte, can be expressed as a function of `b`:
      * If $`b_7 == 1`$, then $`b*0x02 = \{b_6, b_5, b_4, b_3, b_2, b_1, b_0, 0\}\ XOR\ 0x1B`$
      * Else, then $`b*0x02 = \{b_6, b_5, b_4, b_3, b_2, b_1, b_0, 0\}`$
      * To reduce an overflow caused by shifting left (x2), we only need to XOR with the lower 8 bits of 0x11B, which is 0x1B. So, 0x1B is the remainder when 0x11B is shifted left once and truncated to 8 bits.
   * Example: If a multiplication of 0x57 is performed with 0x13, the result must be 0xFE:
      1. Given $`0x13 = 0x10 + 0x02 + 0x01`$, then $`0x57 * 0x13 = 0x57 * 0x10 + 0x57 * 0x02 + 0x57 * 0x01`$.
      2. To calculate the components of the multiplication:
         * $`0x57 * 0x01 = 0x57`$
         * $`0x57 * 0x02 = 0xAE`$ (within the GF(2<sup>8</sup>), so there is no need to perform a reduction by the fixed polynomial)
         * $`0x57 * 0x10 = (0x57 * 0x02) * 0x08 =`$
           $`(0xAE * 0x02) * 0x04 = (0x15C \ XOR \ 0x11B) * 0x04 =`$
           $`(0x47 * 0x02) * 0x02 = 0x8E * 0x02 = 0x11C \ XOR \ 0x11B = 0x07`$
      3. Then $`0x57 * 0x13 = 0x07 + 0xAE + 0x57`$. But, to perform additions in GF(2<sup>8</sup>) an XOR must be used. Then, finally: $`0x57 * 0x13 = 0x07 \ XOR \ 0xAE \ XOR \ 0x57 = 0xFE`$

--------------------------------

# Specifications

* Module Name: `galois_encryption`
* Parameters:
   * `NBW_DATA`: Defines the bit width of input and output data. It must be fixed at 128.
   * `NBW_KEY`: Defines the bit width of the key. It must be fixed at 32.

# Interface Signals

* **Clock** (`clk`): Synchronizes operation in its rising edge.
* **Reset** (`rst_async_n`): Active low, asynchronous reset that resets the internal control registers.
* **Operation Select Signal** (`i_encrypt`): Selects which operation to perform. If `i_encrypt == 1` then it performs the encryption operation, else it performs the decryption operation.
* **Input Valid Signal** (`i_valid`): Indicates when `i_data` signal is valid (`i_valid == 1`) and can be used to perform operations.
* **Input Data Signal** (`i_data`): Data to perform operations.
* **Update Key Signal** (`i_update_key`): Signal that indicates that the internal key must be updated. When `i_update_key == 1`, the internal key must be updated to the input key signal.
* **Key Signal** (`i_key`): Input key signal.
* **Output Valid Signal** (`o_valid`): Indicates when `o_data` signal is valid (`o_valid == 1`) and can be read outside the module.
* **Output Data Signal** (`o_data`): Data result of operations.

# Functional Behavior

## **Input data mapping**

The input data must be mapped to a 4x4 array, `data_in`, where the data is stored as described in the table below. As an example `data_in[1][2] = i_data[55:48]`:

   | i_data[127:120] | i_data[95:88] | i_data[63:56] | i_data[31:24] |
   |:---------------:|:-------------:|:-------------:|:-------------:|
   | i_data[119:112] | i_data[87:80] | i_data[55:48] | i_data[23:16] |
   | i_data[111:104] | i_data[79:72] | i_data[47:40] | i_data[15:8]  |
   | i_data[103:96]  | i_data[71:64] | i_data[39:32] | i_data[7:0]   |

## **Operation**

### Encryption/Decryption Key

   * Key update: When `i_update_key` is asserted and a rising edge of `clk` happens, the internal register for the ke

[... truncated 1952 chars from task prompt ...]

-------:|:-------:|:-------:|
     |  8'h01  |  8'h02  |  8'h03  |  8'h01  |
     |  8'h01  |  8'h01  |  8'h02  |  8'h03  |
     |  8'h03  |  8'h01  |  8'h01  |  8'h02  |



### Decryption

When both `i_valid == 1` and `i_encrypt == 0`, and a rising edge of `clk` happens, the module must perform a decryption operation.

   1. Its latency must be `3` clock cycles, measured from the rising edge where `i_valid` is read as `1` to the rising edge where `o_valid` is `1`.
   2. The input matrix `data_in` performs an XOR operation with the key for each column, resulting in a `data_key` matrix. Example: The bytes in row 2, any column, will perform an XOR operation with the byte [15:8] from the stored key.
   3. Next, the matrix `N` below is multiplied by the `data_key` matrix using GF(2^8) operations, where the result `Rd` = `N` x `data_key`.
   4. And finally, the result matrix `Rd` is mapped to the `128`-bit output the same way the input data was mapped to the input matrix.

* `N` matrix:

     | 8'h0e | 8'h0b | 8'h0d | 8'h09 |
     |:-----:|:-----:|:-----:|:-----:|
     | 8'h09 | 8'h0e | 8'h0b | 8'h0d |
     | 8'h0d | 8'h09 | 8'h0e | 8'h0b |
     | 8'h0b | 8'h0d | 8'h09 | 8'h0e |



# Observed Behavior

An example of the observed/expected behavior is shown in the table below. The key used is fixed at 32'h1c598438 and was sent to the RTL before performing any of the operations below.

| Cycle  | i_encrypt | i_valid | i_data                                | Observed o_valid | Observed o_data                         | Expected o_valid | Expected o_data                         |
|--------|-----------|---------|---------------------------------------|------------------|-----------------------------------------|------------------|-----------------------------------------|
| 1      | 1         | 1       | 0xc35939862e130c5ce72307cee3cc97c7    | 0                | 0x00000000000000000000000000000000      | 0                | 0x00000000000000000000000000000000      |
| 2      | 1         | 1       | 0x63132cc679d762f3e1d767c32f8f485f    | 0                | 0x00000000000000000000000000000000      | 0                | 0x00000000000000000000000000000000      |
| 3      | 1         | 1       | 0xa388654744eb20893f269c7e22dc1845    | 0                | 0x00000000000000000000000000000000      | 0                | 0x00000000000000000000000000000000      |
| 4      | 1         | 0       | 0xa388654744eb20893f269c7e22dc1845    | 0                | 0x00000000000000000000000000000000      | 1                | 0x8005174ee4e1d6470834f53d99084354      |
| 5      | 1         | 0       | 0xa388654744eb20893f269c7e22dc1845    | 1                | 0x4cb966be09da49f8d0d8d72db8de603b      | 1                | 0xcdefa6e72587e18545040d2795e30b33      |
| 6      | 1         | 0       | 0xa388654744eb20893f269c7e22dc1845    | 1                | 0x8bcb323211b1c0cb7bcfd179e2d51b8c      | 1                | 0xe019aca51b39eb36eaeb3c3f7ab58510      |
| 7      | 1         | 0       | 0xa388654744eb20893f269c7e22dc1845    | 1                | 0x8bcb323211b1c0cb7bcfd179e2d51b8c      | 0                | 0x00000000000000000000000000000000      |
| 8      | 1         | 0       | 0xa388654744eb20893f269c7e22dc1845    | 0                | 0x00000000000000000000000000000000      | 0                | 0x00000000000000000000000000000000      |
| 9      | 0         | 1       | 0x2eda305dc8d42191b76dd36e478b428f    | 0                | 0x00000000000000000000000000000000      | 0                | 0x00000000000000000000000000000000      |
| 10     | 0         | 1       | 0x9e3c9d3c64dc02c9f18af5e36e4ec2dc    | 0                | 0x00000000000000000000000000000000      | 0                | 0x00000000000000000000000000000000      |
| 11     | 0         | 1       | 0x1602722c2fac205f08c8b011e8ae55d1    | 0                | 0x00000000000000000000000000000000      | 0                | 0x00000000000000000000000000000000      |
| 12     | 0         | 0       | 0x1602722c2fac205f08c8b011e8ae55d1    | 0                | 0x00000000000000000000000000000000      | 1                | 0x28156e337286a90851638a26690c1f82      |
| 13     | 0         | 0       | 0x1602722c2fac205f08c8b011e8ae55d1    | 1                | 0xfeff357f60d7913dc6459719586d335b      | 1                | 0x666912e7fafe0b858ff420cfcdf16c97      |
| 14     | 0         | 0       | 0x1602722c2fac205f08c8b011e8ae55d1    | 1                | 0xc0bfe8124cdf647080dd74860cbdf8e4      | 1                | 0x2961a853e3047e9cb122bab19e3bcd53      |
| 15     | 0         | 0       | 0x1602722c2fac205f08c8b011e8ae55d1    | 1                | 0xc0bfe8124cdf647080dd74860cbdf8e4      | 0                | 0x00000000000000000000000000000000      |
| 16     | 0         | 0       | 0x1602722c2fac205f08c8b011e8ae55d1    | 0                | 0x00000000000000000000000000000000      | 0                | 0x00000000000000000000000000000000      |

Identify and fix the RTL bug to ensure the correct generation of `o_valid` and `o_data`.

## Current candidate files (line-numbered on patch targets)
### rtl/galois_encryption.sv
```verilog
1| /*
   2| Galois field (2^8) matrix-based encryption/decryption system using AES's polynomial to perform galois field operations
   3| */
   4| 
   5| module galois_encryption #(
   6|     parameter NBW_DATA = 'd128,
   7|     parameter NBW_KEY  = 'd32
   8| ) (
   9|     input  logic                clk,
  10|     input  logic                rst_async_n,
  11|     input  logic                i_encrypt,
  12|     input  logic                i_valid,
  13|     input  logic [NBW_DATA-1:0] i_data,
  14|     input  logic                i_update_key,
  15|     input  logic [NBW_KEY-1:0]  i_key,
  16|     output logic                o_valid,
  17|     output logic [NBW_DATA-1:0] o_data
  18| );
  19| 
  20| // ----------------------------------------
  21| // - Internal Parameters
  22| // ----------------------------------------
  23| localparam LATENCY  = 'd3;
  24| localparam NBW_WORD = 'd8;
  25| localparam MOD_POLY = 8'h1B;
  26| localparam LINES    = 'd4;
  27| localparam COLUMNS  = 'd4;
  28| 
  29| // ----------------------------------------
  30| // - Wires/Registers creation
  31| // ----------------------------------------
  32| logic [LATENCY:0]    valid_ff;
  33| logic [NBW_KEY-1:0]  key_ff;
  34| logic [NBW_WORD-1:0] data_in_ff      [LINES][COLUMNS];
  35| logic [NBW_WORD-1:0] data_xtimes2_nx [LINES][COLUMNS];
  36| logic [NBW_WORD-1:0] data_xtimes3_nx [LINES][COLUMNS];
  37| logic [NBW_WORD-1:0] data_xtimes9_nx [LINES][COLUMNS];
  38| logic [NBW_WORD-1:0] data_xtimesB_nx [LINES][COLUMNS];
  39| logic [NBW_WORD-1:0] data_xtimesD_nx [LINES][COLUMNS];
  40| logic [NBW_WORD-1:0] data_xtimesE_nx [LINES][COLUMNS];
  41| logic [NBW_WORD-1:0] data_out_nx     [LINES][COLUMNS];
  42| logic [NBW_WORD-1:0] data_xtimes2_ff [LINES][COLUMNS];
  43| logic [NBW_WORD-1:0] data_xtimes3_ff [LINES][COLUMNS];
  44| logic [NBW_WORD-1:0] data_xtimes9_ff [LINES][COLUMNS];
  45| logic [NBW_WORD-1:0] data_xtimesB_ff [LINES][COLUMNS];
  46| logic [NBW_WORD-1:0] data_xtimesD_ff [LINES][COLUMNS];
  47| logic [NBW_WORD-1:0] data_xtimesE_ff [LINES][COLUMNS];
  48| logic [NBW_WORD-1:0] data_out_ff     [LINES][COLUMNS];
  49| 
  50| logic [NBW_WORD-1:0] data_xtimes2 [LINES][COLUMNS];
  51| logic [NBW_WORD-1:0] data_xtimes4 [LINES][COLUMNS];
  52| logic [NBW_WORD-1:0] data_xtimes8 [LINES][COLUMNS];
  53| 
  54| // ----------------------------------------
  55| // - Control registers
  56| // ----------------------------------------
  57| always_ff @(posedge clk or negedge rst_async_n) begin : ctrl_regs
  58|     if (!rst_async_n) begin
  59|         valid_ff <= 0;
  60|         key_ff   <= 0;
  61|     end else begin
  62|         valid_ff[0]         <= i_valid;
  63|         valid_ff[LATENCY:1] <= valid_ff[LATENCY-1:0];
  64|         if(i_update_key) begin
  65|             key_ff <= i_key;
  66|         end
  67|     end
  68| end
  69| 
  70| // ----------------------------------------
  71| // - Data registers
  72| // ----------------------------------------
  73| always_ff @(posedge clk) begin : data_regs
  74|     for (int line = 0; line < LINES; line++) begin
  75|         for (int column = 0; column < COLUMNS; column++) begin
  76|             if(i_valid) begin
  77|                 if(i_encrypt) begin
  78|                     data_in_ff[line][column] <= i_data[NBW_DATA-1-(column*NBW_WORD + line*NBW_WORD*COLUMNS)-:NBW_WORD];
  79|                 end else begin
  80|                     data_in_ff[line][column] <= i_data[NBW_DATA-1-(column*NBW_WORD + line*NBW_WORD*COLUMNS)-:NBW_WORD] ^ key_ff[NBW_KEY-line*NBW_WORD-1-:NBW_WORD];            
  81|                 end
  82|             end
  83| 
  84|             data_xtimes2_ff[line][column] <= data_xtimes2_nx[line][column];
  85|             data_xtimes3_ff[line][column] <= data_xtimes3_nx[line][column];
  86|             data_xtimes9_ff[line][column] <= data_xtimes9_nx[line][column];
  87|             data_xtimesB_ff[line][column] <= data_xtimesB_nx[line][column];
  88|             data_xtimesD_ff[line][column] <= data_xtimesD_nx[line][column];
  89|             data_xtimesE_ff[line][column] <= data_xtimesE_nx[line][column];
  90| 
  91|             if(valid_ff[2]) begin
  92|                 data_out_ff[line][column] <= data_out_nx[line][column];
  93|             end
  94|         end
  95|     end
  96| end
  97| 
  98| // ----------------------------------------
  99| // - Intermediary steps
 100| // ----------------------------------------
 101| 
 102| // Calculate GF(2^8) multiplication by 2, 4 and 8
 103| always_comb begin : multiply_gf2_4_8
 104|     for (int line = 0; line < LINES; line++) begin
 105|         for (int column = 0; column < COLUMNS; column++) begin
 106|             data_xtimes2[line][column] = data_in_ff[line][column] << 1 ^ MOD_POLY;
 107|             data_xtimes4[line][column] = data_in_ff[line][column] << 2 ^ MOD_POLY;
 108|             data_xtimes8[line][column] = data_in_ff[line][column] << 4 ^ MOD_POLY;
 109|         end
 110|     end
 111| end
 112| 
 113| // Calculate GF(2^8) multiplications by the values in the polynomial
 114| always_comb begin : multiply_gf
 115|     for (int line = 0; line < LINES; line++) begin
 116|         for (int column = 0; column < COLUMNS; column++) begin
 117|             data_xtimes2_nx[line][column] = data_xtimes2[line][column];
 118|             if(i_encrypt) begin
 119|                 data_xtimes3_nx[line][column] = data_xtimes2[line][column] ^ data_in_ff[line][column];
 120|                 data_xtimes9_nx[line][column] = data_xtimes9_ff[line][column];
 121|                 data_xtimesB_nx[line][column] = data_xtimesB_ff[line][column];
 122|                 data_xtimesD_nx[line][column] = data_xtimesD_ff[line][column];
 123|                 data_xtimesE_nx[line][column] = data_xtimesE_ff[line][column];
 124|             end else begin
 125|                 data_xtimes3_nx[line][column] = data_xtimes3_ff[line][column];
 126|                 data_xtimes9_nx[line][column] = data_xtimes8[line][column] ^ data_in_ff[line][column];
 127|                 data_xtimesB_nx[line][column] = data_xtimes8[line][column] ^ data_xtimes2[line][column] ^ data_in_ff  [line][column];
 128|                 data_xtimesD_nx[line][column] = data_xtimes8[line][column] ^ data_xtimes4[line][column] ^ data_in_ff  [line][column];
 129|                 data_xtimesE_nx[line][column] = data_xtimes8[line][column] ^ data_xtimes4[line][column] ^ data_xtimes2[line][column] ^ data_in_ff[line][column];
 130|             end
 131|         end
 132|     end
 133| end
 134| 
 135| // Calculate output matrix
 136| always_comb begin : out_matrix
 137|     if(i_encrypt) begin
 138|         for (int column = 0; column < COLUMNS; column++) begin
 139|             data_out_nx[0][column] = data_xtimes2_ff[0][column] ^ data_xtimes3_ff[1][column] ^ data_in_ff[2][column] ^ data_in_ff[3][column];
 140|             data_out_nx[1][column] = data_xtimes2_ff[1][column] ^ data_xtimes3_ff[2][column] ^ data_in_ff[3][column] ^ data_in_ff[0][column];
 141|             data_out_nx[2][column] = data_xtimes2_ff[2][column] ^ data_xtimes3_ff[3][column] ^ data_in_ff[0][column] ^ data_in_ff[1][column];
 142|             data_out_nx[3][column] = data_xtimes2_ff[3][column] ^ data_xtimes3_ff[0][column] ^ data_in_ff[1][column] ^ data_in_ff[2][column];
 143|         end
 144|     end else begin
 145|         for (int column = 0; column < COLUMNS; column++) begin
 146|             data_out_nx[0][column] = data_xtimesE_ff[0][column] ^ data_xtimesB_ff[1][column] ^ data_xtimesD_ff[2][column] ^ data_xtimes9_ff[3][column];
 147|             data_out_nx[1][column] = data_xtimesE_ff[1][column] ^ data_xtimesB_ff[2][column] ^ data_xtimesD_ff[3][column] ^ data_xtimes9_ff[0][column];
 148|             data_out_nx[2][column] = data_xtimesE_ff[2][column] ^ data_xtimesB_ff[3][column] ^ data_xtimesD_ff[0][column] ^ data_xtimes9_ff[1][column];
 149|             data_out_nx[3][column] = data_xtimesE_ff[3][column] ^ data_xtimesB_ff[0][column] ^ data_xtimesD_ff[1][column] ^ data_xtimes9_ff[2][column];
 150|         end
 151|     end
 152| end
 153| 
 154| // ----------------------------------------
 155| // - Assign outputs
 156| // ----------------------------------------
 157| 
 158| // Map output values from lines x columns to a single dimension
 159| always_comb begin : out_mapping
 160|     if(valid_ff[LATENCY]) begin
 161|         for (int line = 0; line < LINES; line++) begin
 162|             for (int column = 0; column < COLUMNS; column++) begin
 163|                 if(i_encrypt) begin
 164|                     o_data[NBW_DATA-(column*NBW_WORD + line*NBW_WORD*COLUMNS)-1-:NBW_WORD] = data_out_ff[line][column] ^ key_ff[NBW_KEY-line*NBW_WORD-1-:NBW_WORD];
 165|                 end else begin
 166|                     o_data[NBW_DATA-(column*NBW_WORD + line*NBW_WORD*COLUMNS)-1-:NBW_WORD] = data_out_ff[line][column];
 167|                 end
 168|             end
 169|         end
 170|     end else begin
 171|         o_data = 0;
 172|     end
 173| end
 174| 
 175| assign o_valid = valid_ff[LATENCY];
 176| 
 177| endmodule : galois_encryption
```

## Files you must patch
rtl/galois_encryption.sv

Primary module: `galois_encryption`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=[ERROR] DUT data output does not match model data output: 0x0 != 0x84d26788dd252342dd7d2901c9d54b91
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
0.00ns INFO     cocotb.regression                  running test_galois_encryption.test_galois_encryption (1/1)
                                                            Test the Galois Encryption module with edge cases and random data.
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create ctrl_regs via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create data_regs via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create multiply_gf via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create multiply_gf2_4_8 via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create out_mapping via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create out_matrix via any registered implementation
    70.00ns WARNING  ..ncryption.test_galois_encryption [ERROR] DUT data output does not match model data output: 0x0 != 0x84d26788dd252342dd7d2901c9d54b91
                                                        assert 0 == 176550577715561571029412483987183848337
                                                        Traceback (most recent call last):
                                                          File "/src/test_galois_encryption.py", line 156, in test_galois_encryption
                                                            assert dut_data_out == model_data_out, f"[ERROR] DUT data output does not match model data output: {hex(dut_data_out)} != {hex(model_data_out)}"
                                                        AssertionError: [ERROR] DUT data output does not match model data output: 0x0 != 0x84d26788dd252342dd7d2901c9d54b91
                                                        assert 0 == 176550577715561571029412483987183848337
    70.00ns WARNING  cocotb.regression                  test_galois_encryption.test_galois_encryption failed
    70.00ns INFO     cocotb.regression                  *******************************************************************************************************
                                                        ** TEST                                           STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        *******************************************************************************************************
                                                        ** test_galois_encryption.test_galois_encryption   FAIL          70.00           0.01       5791.18  **
                                                        *******************************************************************************************************
                                                        ** TESTS=1 PASS=0 FAIL=1 SKIP=0                                  70.00           0.03       2576.08  **
                                                        *******************************************************************************************************
FAILED

=================================== FAILURES ===================================
_________________________________ test_data[0] _________________________________

test = 0

    @pytest.mark.parametrize("test", range(1))
    def test_data(test):
        # Run the simulation with specified parameters
>       runner()

/src/test_runner.py:35: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    def runner():
        # Configure and run the simulation
        sim_runner = get_runner(sim)
        sim_runner.build(
            sources=verilog_sources,
            hdl_toplevel=toplevel,
            always=True,
            clean=True,
            verbose=True,
            timescale=("1ns", "1ns"),
            log_file="sim.log"
        )
    
        # Run the test
>       sim_runner.test(hdl_toplevel=toplevel, test_module=module, waves=True)
E       SystemExit: 1

/src/test_runner.py:29: SystemExit
------------------------------ Captured log call -------------------------------
INFO     Icarus:runner.py:632 Running command iverilog -o /code/rundir/sim_build/sim.vvp -s galois_encryption -g2012 -f /code/rundir/sim_build/cmds.f /code/rtl/galois_encryption.sv in directory /code/rundir/sim_build
INFO     Icarus:runner.py:632 Running command vvp -M /venv/lib/python3.12/site-packages/cocotb/libs -m libcocotbvpi_icarus /code/rundir/sim_build/sim.vvp -fst in directory /code/rundir/sim_build
ERROR    Icarus:runner.py:572 ERROR: Failed 1 of 1 tests.
=============================== warnings summary ===============================
../../venv/lib/python3.12/site-packages/_pytest/cacheprovider.py:477
  /venv/lib/python3.12/site-packages/_pytest/cacheprovider.py:477: PytestCacheWarning: could not create cache path /rundir/harness/.cache/v/cache/nodeids: [Errno 13] Permission denied: '/rundir/harness/pytest-cache-files-vg0t_gy_'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../../venv/lib/python3.12/site-packages/_pytest/cacheprovider.py:429
  /venv/lib/python3.12/site-packages/_pytest/cacheprovider.py:429: PytestCacheWarning: could not create cache path /rundir/harness/.cache/v/cache/lastfailed: [Errno 13] Permission denied: '/rundir/harness/pytest-cache-files-qyw8_2bw'
    config.cache.set("cache/lastfailed", self.lastfailed)

../../venv/lib/python3.12/site-packages/_pytest/stepwise.py:51
  /venv/lib/python3.12/site-packages/_pytest/stepwise.py:51: PytestCacheWarning: could not create cache path /rundir/harness/.cache/v/cache/stepwise: [Errno 13] Permission denied: '/rundir/harness/pytest-cache-files-echhguxl'
    session.config.cache.set(STEPWISE_CACHE_DIR, [])

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED ../../src/test_runner.py::test_data[0] - SystemExit: 1
======================== 1 failed, 3 warnings in 1.56s =========================

[stderr]
Network cvdp_react_cvdp_copilot_galois_encryption_0001_1_default Creating 
 Network cvdp_react_cvdp_copilot_galois_encryption_0001_1_default Created 
 Container cvdp_react_cvdp_copilot_galois_encryption_0001_1-01-new-tb-run-646c59d08a2f Creating 
 Container cvdp_react_cvdp_copilot_galois_encryption_0001_1-01-new-tb-run-646c59d08a2f Created

--- full harness log ---

============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.3.2, pluggy-1.6.0 -- /venv/bin/python
cachedir: /rundir/harness/.cache
rootdir: /src
collecting ... collected 1 item

../../src/test_runner.py::test_data[0]      -.--ns INFO     gpi                                ..mbed/gpi_embed.cpp:93   in _embed_init_python              Using Python 3.12.4 interpreter at /venv/bin/python
     -.--ns INFO     gpi                                ../gpi/GpiCommon.cpp:79   in gpi_print_registered_impl       VPI registered
     0.00ns INFO     cocotb                             Running on Icarus Verilog version 13.0 (stable)
     0.00ns INFO     cocotb                             Seeding Python random module with 1782021038
     0.00ns INFO     cocotb                             Initialized cocotb v2.0.1 from /venv/lib/python3.12/site-packages/cocotb
     0.00ns INFO     cocotb                             Running tests
     0.00ns INFO     cocotb.regression                  running test_galois_encryption.test_galois_encryption (1/1)
                                                            Test the Galois Encryption module with edge cases and random data.
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create ctrl_regs via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpiNamedBegin(33) to object.
     0.00ns WARNING  gpi                                Unable to create data_regs via any registered implementation
     0.00ns WARNING  gpi                                VPI: Not able to map type vpi

[... truncated 6341 chars from end of harness output ...]
```

## Cocotb test excerpt
### test_galois_encryption.py
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import harness_library as hrs_lb
import random

@cocotb.test()
async def test_galois_encryption(dut):
    """Test the Galois Encryption module with edge cases and random data."""

    # Start the clock
    cocotb.start_soon(Clock(dut.clk, 10, unit='ns').start())

    model = hrs_lb.GaloisEncryption(0)

    # Retrieve parameters from the DUT
    NBW_DATA = int(dut.NBW_DATA.value)
    NBW_KEY = int(dut.NBW_KEY.value)

    debug = 0

    # Range for input values
    d

[... truncated 2839 chars from cocotb test excerpt ...]

es not match model data output: {hex(dut_data_out)} != {hex(model_data_out)}"
            assert dut_valid_out == model_valid_out, f"[ERROR] DUT valid output does not match model valid output: {hex(dut_valid_out)} != {hex(model_valid_out)}"

            # Wait for latency
            await RisingEdge(dut.clk)
            dut_data_out = int(dut.o_data.value)
            dut_valid_out = int(dut.o_valid.value)
            if debug:
                dut_valid_in = dut.i_valid.value
                dut_encrypt_in = dut.i_encrypt.value
                cocotb.log.info(f"\nSET VALID TO 0. Clock 1")
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/galois_encryption.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
