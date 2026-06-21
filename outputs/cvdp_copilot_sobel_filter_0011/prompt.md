Identify and fix issues in the following Sobel Filter implementation in module `sobel_filter`. Maintain the clock (`clk`) polarity and the active-low asynchronous reset (`rst_n`) configuration in the design while addressing and resolving the identified bugs.
#### **Specifications:**

- **Parameters:**  
  - `THRESHOLD` (default value: 128): This parameter defines the threshold for edge detection. Pixels with gradient magnitudes greater than this value are classified as edges.  

### **1. Overview of the Sobel Filter Algorithm:**

The Sobel filter detects edges in an image by first computing the gradients in the horizontal (`Gx`) and vertical (`Gy`) directions, then calculating the gradient magnitude (`|Gx| + |Gy|`) and comparing it to a threshold to determine whether a pixel is part of an edge. 

A 3x3 window of pixels is sent as a continuous stream of inputs through `pixel_in`, and `valid_in` remains high while pixels are supplied. The module uses a 3x3 buffer to store pixel data, ensuring it only outputs valid results once the buffer is fully populated with 9 pixels. Pixels are shifted sequentially to store new incoming pixels. (The input is sent row by row, left to right. Starting from the top row, the traversal proceeds to the bottom row.) The filter performs convolution when the buffer is fully populated and outputs the result. After processing each window, the module clears the buffer and waits for the next set of 9 pixels. Buffer is also cleared when reset is asserted. (active-low). Assume that the handling of overlapping windows is handled externally and this design should process each window as a new one. (no storing of pixels from the previous window)

### **2. Expected Behavior**
The Sobel filter module should adhere to the following specifications:  

- **Valid Signal Assertion:**  
   - The `valid_out` signal must assert (`1`) for 1 clock cycle only when the buffer is fully populated with 9 pixels (9 clock cycles after `valid_in` for the first pixel). During initialization (first 8 clock cycles), `valid_out` must remain `0`.  

- **Accurate Gradient Computation:**  
   - The gradients `Gx` and `Gy` must be calculated using the Sobel kernels with proper handling of signed arithmetic.Each pixel in the 3x3 window is multiplied by the kernel coefficient that corresponds to its relative position in the Sobel kernel. For example:
        - The pixel stored in top-left corner of the buffer is multiplied by -1 (top-left coefficient in the Gx kernel).
        
Then the results are added to compute Gx and Gy and obtain the gradient magnitude.
    
```
     Gx Kernel:     Gy Kernel:
     [-1  0  +1]    [-1  -2  -1]
     [-2  0  +2]    [ 0   0   0]
     [-1  0  +1]    [+1  +2  +1]
```  
   - The `edge_out` signal should classify pixels as edges (`8'd255`) if the gradient magnitude (`|Gx| + |Gy|`) exceeds the `THRESHOLD`. Otherwise, classify as non-edges (`8'd0`). `edge_out`  and `valid_out` should remain zero until the value from a computation is updated.


### **3. Test Cases**
### **Condition for All Test Cases**
- **Input**:
  - `rst_n = 1`, `valid_in = 1`, `pixel_in` provides 9 continuous input values.
 - Following sequence of tests are executed in order

#### **Test Case 1: No Horizontal Edge Detection**  
- **Input Values:**  
  ```
  [ 10  10  10  ]
  [ 255 255 255 ]
  [ 10  10  10  ]
  ``` 
- **Actual Output:**
  - `valid_out`:
     - Asserted high (`1'b1`) after 1 clock cycle of input processing.
     - Remains high for 9 clock cycles.
  
  - `edge_out`:
     - Initially observed as `8'd0` when `valid_out` goes high (1 clock cycle after first `valid_in`).
     - Output value observed as `8'd255` 6 clock cycles after `valid_in` is asserted for the first pixel.  
  
- **Expected Output:**  
  - `valid_out =1'b1` and `edge_out = 8'd0` after 9 clock cycles.  
  - `valid_out` and `edge_out = 8'd0` are cleared to 0 after 1 clock cycle.  
  
#### **Test Case 2: No Vertical Edge Detection**  
- **Input Values:**  
  ```
  [ 10  255 10 ]  
  [ 10  255 10 ]  
  [ 10  255 10 ]  
  ```
- **Actual Output:**
  - `valid_out`:
    - Asserted high (`1'b1`) after 1 clock cycle of input processing.
    - Remains high for 9 clock cycles.

  - `edge_out`:
     - Initially observed as `8'd255` when `valid_out` goes high (1 clock cycle after first `valid_in`).
     - Changes to `8'd0` in the next clock cycle, then reverts to `8'd255` in the subsequent clock cycle.
    
- **Expected Output:**  
  - `valid_out =1'b1` and `edge_out = 8'd0` after 9 clock cycles.  
  - `valid_out` and `edge_out = 8'd0` are cleared to 0 after 1 clock cycle.  

#### **Test Case 3: No Uniform Edge Detection**  
- **Input Values:**  
  ```
  [ 128  128  128 ]  
  [ 128  128  128 ]  
  [ 128  128  128 ]  
  ```
- **Actual Output:**
  - `valid_out`:
     - Asserted high (`1'b1`) after 1 clock cycle of input processing.
     - Remains high for 9 clock cycles.
  
  - `edge_out`:
     - Initially observed as `8'd255` when `valid_out` goes high (1 clock cycle after first `valid_in`).
     - Changes to `8'd0` in the next clock cycle, reverts to `8'd255` in the subsequent clock cycle. It changes to `8'd0` 2 cycles after that, reverts to `8'd255` in the next clock cycle, changes to `8'd0` in 2 clock cycles after, then reverts to `8'd255` in the subsequent clock cycle.
    
- **Expected Output:**  
  - `valid_out =1'b1` and `edge_out = 8'd0` after 9 clock cycles.  
  - `valid_out` and `edge_out = 8'd0` are cleared to 0 after 1 clock cycle.  


#### **Test Case 4: Edge Detection**  
- **Input Values:**  
  ```
  [ 10  20  30 ]  
  [ 20 255  40 ]  
  [ 30  40  50 ]  
  ```
- **Actual Output:**
  - `valid_out`:
     - Asserted high (`1'b1`) after 1 clock cycle of input processing.
     - Remains high for 9 clock cycles.
  
  - `edge_out`:
     - Initially observed as `8'd255` when `valid_out` goes high (1 clock cycle after first `valid_in`).
     - Output value observed as `8'd0` in next clock cycles and switches to `8'd255` in the next clock cycle.It goes back to `8'd0` 5 clock cycles after that and in the next clock cycle it switches to `8'd255`
      
- **Expected Output:**   
  - `valid_out = 1'b1` and `edge_out = 8'd255` after 9 clock cycles.  
  - `valid_out` and `edge_out = 8'd0` are cleared to 0 after 1 clock cycle.  
  
#### **Test Case 5: Edge Detection for Max Value**  
- **Input Values:**  
  ```
  [ 0  255  255 ]  
  [ 0  0    255 ]  
  [ 0  0    0   ]  
  ```
- **Actual Output:**
  - `valid_out`:
     - Asserted high (`1'b1`) after 1 clock cycle of input processing.
     - Remains high for 9 clock cycles.
  
  - `edge_out`:
     - Remain `8'd255` throughout the 9 clock cycles that `valid_out` stays high.
      
- **Expected Output:**  
  - `valid_out =1'b1` and `edge_out = 8'd255` after 9 clock cycles.  
  - `valid_out` and `edge_out = 8'd0` are cleared to 0 after 1 clock cycle.  

#### **Test Case 6: No Edge Detection for Centered Max Value**  
- **Input Values:**  
  ```
  [ 0   0  0 ]  
  [ 0 255  0 ]  
  [ 0   0  0 ]  
  ```
- **Actual Output:**
  - `valid_out`:
     - Asserted high (`1'b1`) after 1 clock cycle of input processing.
     - Remains high for 9 clock cycles.
  
  - `edge_out`:
     - Initially observed as `8'd255` when `valid_out` goes high (1 clock cycle after first `valid_in`).
     - Output value observed as `8'd0` 7 clock cycles after first `valid_in` and reverts to `8'd255` in the next clock cycle.
      
- **Expected Output:**    
  - `valid_out =1'b1` and `edge_out =8'd0` after 9 clock cycles.  
  - `valid_out` and `edge_out = 8'd0` are cleared to 0 after 1 clock cycle.
