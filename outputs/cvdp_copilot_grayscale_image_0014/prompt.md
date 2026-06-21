The `conv3x3` module contains a bug that disrupt the accuracy of the convolution operation. Leading the result in incorrect final outputs.

---

### Prompt for the `conv3x3` Module

---

### Expected Behavior:

1. **Element-wise Multiplication (Stage 1):**
   - Each element of the input image data should be multiplied by the corresponding kernel element to produce intermediate results.

2. **Row-wise Summation (Stage 2):**
   - Each row of the kernel and input image data must fully contribute to the convolution result.
   - The summation for each row should include all relevant multiplication results without omission.

3. **Final Summation (Stage 3):**
   - The results of all row-wise summations must be combined accurately to calculate the total convolution sum.

4. **Normalization (Stage 4):**
   - The total convolution sum should be normalized by dividing it by the correct number of elements in the kernel.
   - For a 3x3 kernel, this ensures proper scaling.

5. **Output Accuracy:**
   - The final output must be an accurate and normalized representation of the convolution operation, considering all contributions from the kernel and input image data. Boundary conditions should be handled appropriately. 

---

Provide me with one RTL version that fixes this issue.
