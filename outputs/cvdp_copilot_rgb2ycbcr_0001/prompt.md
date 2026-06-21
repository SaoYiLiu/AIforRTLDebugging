The `axis_rgb2ycbcr` module has a bug where the **FIFO read pointer does not correctly track written data**, causing incorrect pixel values to be output. Instead of outputting the correct first pixel in the sequence, the module reads earlier intermediate data, leading to **mismatched YCbCr values** at specific indices of output.

The bug could also be caused by stage buffering of intermediate data, where the pipeline registers (`y_reg`, `cb_reg`, `cr_reg`) introduce unintended delays in the data path, leading to misaligned reads and writes in the FIFO.

---

## Test Case Details

### **Test Case 1:**
**Input Parameters:**  
`IMG_WIDTH` = 6  
`IMG_HEIGHT` = 2  

**Actual Output:**  
Received Pixel 0: 0000, Expected: 8566, Valid Bit: 1
Received Pixel 1: 1410, Expected: 62FD, Valid Bit: 1
Received Pixel 2: 8566, Expected: A952, Valid Bit: 1
Received Pixel 3: 62FD, Expected: EBAF, Valid Bit: 1

**Expected Output:**  
Received Pixel 0: 8566, Expected: 8566, Valid Bit: 1
Received Pixel 1: 62FD, Expected: 62FD, Valid Bit: 1
Received Pixel 2: A952, Expected: A952, Valid Bit: 1
Received Pixel 3: EBAF, Expected: EBAF, Valid Bit: 1


**Discrepancy:**  
- **Pixel 0 incorrectly outputs `0000` instead of `8566`**  
- **Pixel 1 incorrectly outputs `1410` instead of `62FD`**  
Incorrect initial values being read.

---

### **Test Case 2:**
**Input Parameters:**  
`IMG_WIDTH` = 5  
`IMG_HEIGHT` = 3  

**Actual Output:**  
Received Pixel 0: 0000, Expected: 5AD0, Valid Bit: 1
Received Pixel 1: 1410, Expected: 356D, Valid Bit: 1
Received Pixel 2: 5AD0, Expected: 6677, Valid Bit: 1
Received Pixel 3: 356D, Expected: 9BD4, Valid Bit: 1

**Expected Output:**  
Received Pixel 0: 5AD0, Expected: 5AD0, Valid Bit: 1
Received Pixel 1: 356D, Expected: 356D, Valid Bit: 1
Received Pixel 2: 6677, Expected: 6677, Valid Bit: 1
Received Pixel 3: 9BD4, Expected: 9BD4, Valid Bit: 1

**Discrepancy:**  
- **Pixel 0 incorrectly outputs `0000` instead of `5AD0`**  
- **Pixel 1 incorrectly outputs `1410` instead of `356D`**  
Incorrect initial values being read.

---

## **Observations**
1. **Write and Read Pointers Out of Sync:**  
   - The read pointer is **incremented too early**, causing incorrect data to be sent out.

2. **Possible Stage Buffering Issue:**  
   - The intermediate registers (`y_reg`, `cb_reg`, `cr_reg`) might introduce an unintended pipeline delay.
   - **The write pointer updates before `y_reg`, `cb_reg`, `cr_reg` are fully computed,** causing stale or delayed data to be written into the FIFO.
   - This could cause **incorrect alignment between FIFO write and read operations**.
