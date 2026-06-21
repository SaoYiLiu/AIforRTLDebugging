The `montgomery_mult` module is designed to use the `montgomery_redc` module to compute modular multiplication of unsigned integers without directly performing division operations. The module computes the result of the modular multiplication:
`result = (a * b) mod N` .  The algorithm used to compute modular multiplication is described below.

---

### Montgomery Multiplication Algorithm

The `montgomery_mult(a, b)` algorithm follows these steps:

1. **Input Conditions**:
   - The value of `a` must satisfy `0 < a < N`.
   - The value of `b` must satisfy `0 < b < N`.

2. **Precompute `R^2`**:
   - Compute:
     ```
     R^2 = (R * R) mod N
     ```

3. **Transform Inputs to Montgomery Form**:
   - Compute:
     ```
     a' = montgomery_redc(a * R^2) = (a * R^2) (R^-1) mod N
     b' = montgomery_redc(b * R^2) = (b * R^2) (R^-1) mod N
     ```

4. **Perform Modular Multiplication in Montgomery Form**:
   - Compute:
     ```
     result' = montgomery_redc(a' * b') = (a' * b') (R^-1) mod N
     ```

5. **Convert Result Back to Standard Form**:
   - Compute:
     ```
     result = montgomery_redc(result') = result' (R^-1)  mod N
     ```

---
### Identified Issues During Testing

#### **Issue 1: Incorrect Montgomery Reduction**
The module erroneously computes the Montgomery reduction for the expected result instead of returning the final modular multiplication output. Examples of failing test cases are provided below:

| **a** | **b** | **N** | R    |**R inverse** |**Expected Result** | **DUT Output**       | **Pass/Fail** |
|-------|-------|-------|------|--------------|--------------------|----------------------|---------------|
| 33    | 337   | 499   | 1024 |  96          | 143                | `redc(143) = 255`    | **Fail**      |
| 205   | 79    | 499   | 1024 |  96          | 227                | `redc(227) = 335`    | **Fail**      |

Note: Selection of N,R and R_INVERSE should satisfy the following:
1. Choose a modulus N > 2.
2. Select a radix R, which is a number greater than N (R > N).
3. R is chosen to be a power of 2.
4. R and N are coprime (R and N must not share any common factors other than 1). We assume N is a prime number so that any choice of R is coprime to N.
6. Let R<sup>-1</sup> be an integer such that:
   - 0 < R<sup>-1</sup> < N, where R<sup>-1</sup> is the multiplicative inverse in the N-residue system.
   - The following equation must be satisfied:
     (R* R<sup>-1</sup>) mod N=1

#### **Issue 2: Incorrect `valid_out` Timing**
The `valid_out` signal is expected to have a latency of **four clock cycles**. However, the result is computed and output one clock cycle before `valid_out` is asserted, causing a mismatch in the expected behavior.

---

Fix the issues identified above and provide the corrected code.
