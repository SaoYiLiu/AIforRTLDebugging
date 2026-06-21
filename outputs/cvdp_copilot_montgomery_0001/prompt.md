The `montgomery_redc` module is designed to implement Montgomery reduction which is a technique used to efficiently compute modular arithmetic of unsigned integers without directly performing division operations. During testing, the `result[NWIDTH-1:0]` output does not match the expected output. The module calculates the following combinationally:

result = T * R<sup>-1</sup> mod N

## Preconditions for Montgomery Reduction

1. Choose a modulus N > 2.
2. Select a radix R, which is a number greater than N (R > N).
3. R is chosen to be a power of 2.
4. R and N are coprime (R and N must not share any common factors other than 1). We assume N is a prime number so that any choice of R is coprime to N.
6. Let R<sup>-1</sup> and N' be integers such that:
   - 0 < R<sup>-1</sup> < N, where R<sup>-1</sup> is the multiplicative inverse in the N-residue system.
   - 0 < N' < R
   - The following equations must be satisfied:
     (R* R<sup>-1</sup>) mod N=1
     R * R<sup>-1</sup> - N * N' = 1

## Montgomery Reduction Algorithm: `montgomery_redc(T)`

The value of T must satisfy 0 < T < RN.

1. **Compute**:
   m = (T mod R) * N' mod R [so 0 < m < R]

2. **Compute**:
   t = (T + m * N) / R

3. **Return**:
   - If t >= N, return t - N
   - Else, return t

It can be proved that:
0 < t < 2N

---
 
### Examples of failing test cases:
The following table lists several test cases where the `montgomery_redc` module produced incorrect outputs compared to the expected results. These discrepancies highlight potential issues in the implementation. Identify and fix the bugs in the design to obtain the expected result.

| **T**      | **N** | **R**   | **R_INVERSE** | **Expected Result**  | **DUT Output** | **Pass/Fail** |
|------------|-------|---------|---------------|----------------------|----------------|---------------|
| 14556      | 109   | 256     | 66            | 79                   | 94             | **Fail**      |
| 10839      | 109   | 256     | 66            | 7                    | 58             | **Fail**      |
| 21975      | 109   | 256     | 66            | 105                  | 107            | **Fail**      |
| 9142       | 109   | 256     | 66            | 57                   | 83             | **Fail**      |
| 2705       | 109   | 256     | 66            | 97                   | 103            | **Fail**      |
| 19560      | 109   | 256     | 66            | 73                   | 91             | **Fail**      |
| 21991      | 109   | 256     | 66            | 71                   | 90             | **Fail**      |
| 2370       | 109   | 256     | 66            | 5                    | 57             | **Fail**      |
