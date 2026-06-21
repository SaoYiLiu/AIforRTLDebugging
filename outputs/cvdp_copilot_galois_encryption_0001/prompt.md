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

   * Key update: When `i_update_key` is asserted and a rising edge of `clk` happens, the internal register for the key is updated with the value from `i_key`. The RTL does not need to handle a situation where the key is updated while an encryption or decryption is being performed, as the input `i_update_key` must not be `1` during the module's encrypt/decrypt operation.
   * Encryption key usage: The stored key is combined with the encryption operation result in its last step by performing an XOR operation: The byte [31:24] of the key must perform an XOR operation with all bytes in row 0 of the resulting matrix. The byte [23:16] of the key must perform an XOR operation with all bytes in row 1 of the resulting matrix. The byte [15:8] of the key must perform an XOR operation with all bytes in row 2 of the resulting matrix. Finally, the byte [7:0] of the key must perform an XOR operation with all bytes in row 3 of the resulting matrix.
   * Decryption key usage: The stored key is combined with the input data as the first step of the decryption process. Its combination follows the same rules as the one in the encryption operation, where an XOR operation will be performed with the key's bytes and the matrix rows.

### Encryption

When both `i_valid` and `i_encrypt` signals are asserted, and a rising edge of `clk` happens, the module must perform an encryption operation.

   1. Its latency must be `3` clock cycles, measured from the rising edge where `i_valid` is read as `1` to the rising edge where `o_valid` is `1`.
   2. The matrix `M` below is multiplied by the `data_in` matrix using GF(2^8) operations, where the result `Re` = `M` x `data_in`.
   3. Next, the `Re` matrix performs an XOR operation with the key for each column. Example: The bytes in row 2, any column, will perform an XOR operation with the byte [15:8] from the stored key.
   4. And finally, the result is mapped to the `128-bit output the same way the input data was mapped to the input matrix.

* `M` matrix:

     |  8'h02  |  8'h03  |  8'h01  |  8'h01  |
     |:-------:|:-------:|:-------:|:-------:|
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
