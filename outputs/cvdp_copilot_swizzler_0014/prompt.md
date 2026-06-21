The *swizzler* module is designed to reorder bits (based on a mapping), optionally reverse them if config_in is low, and then apply various operations dictated by operation_mode.
Below is a table showing the *expected* and *actual* values for three representative test cases:

| Test Case | data_in | Expected data_out | Actual data_out | Expected error_flag | Actual error_flag  |
|-----------|---------|-------------------|-----------------|---------------------|--------------------|
| 1         | 0xAA    | 0xAA              | 0x80            | 0                   | 1                  |
| 2         | 0xAA    | 0x55              | 0x80            | 0                   | 1                  |
| 3         | 0x55    | 0x55              | 0x80            | 0                   | 1                  |
| 4         | 0x55    | 0xAA              | 0x0             | 0                   | 1                  |
| 5         | 0xAA    | 0xAA              | 0x8             | 0                   | 1                  |
| 6         | 0xAA    | 0x55              | 0x7e            | 0                   | 1                  |
| 7         | 0xAA    | 0x55              | 0xX0            | 0                   | 1                  |
| 8         | 0xAA    | 0x55              | 0x0             | 0                   | 1                  |
| 9         | 0xAA    | 0x00              | 0x80            | 1                   | 1                  |
| 10        | 0xAA    | 0x00              | 0x00            | 0                   | 0                  |


### Test Case Details

## 1.
*Identity Mapping (Test 1)*  
- *Clock:* 100 MHz  
- *Reset:* Active-High  
- *Input:*  
  - data_in = 0xAA  
  - mapping_in = 0x01234567  
  - config_in = 1  
  - operation_mode = 3'b000  
- *Expected Output:*  
  - data_out = 0xAA  
  - error_flag = 0  
- *Actual Output:*  
  - data_out = 0x80  
  - error_flag = 1  

## 2.
*Swap Halves (Test 5)*  
- *Clock:* 100 MHz  
- *Reset:* Active-High  
- *Input:*  
  - data_in = 0xAA  
  - mapping_in = 0x01234567  
  - config_in = 1  
  - operation_mode = 3'b011  
- *Expected Output:*  
  - data_out = 0xAA  
  - error_flag = 0  
- *Actual Output:*  
  - data_out = 0x8  
  - error_flag = 1  

## 3.
Invalid Mapping (Test 9) 
- *Clock:* 100 MHz  
- *Reset:* Active-High  
- *Input:*  
  - data_in = 0xAA  
  - mapping_in = 0x81234567  
  - config_in = 1  
  - operation_mode = 3'b000  
- *Expected Output:*  
  - data_out = 0x00  
  - error_flag = 1  
- *Actual Output:*  
  - data_out = 0x80  
  - error_flag = 1  

Identify and fix the underlying bugs in the RTL so that each test case’s outputs match the expected results.
