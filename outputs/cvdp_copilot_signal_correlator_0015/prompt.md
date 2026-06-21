The Signal Correlator module computes a 4-bit `correlation_output` from two 8-bit inputs (`input_signal` and `reference_signal`), where each matching bit contributes a weight of **+2** to the summation, with the output clamped at `15`. However, the module exhibits incorrect behavior under certain edge cases.

Here follows the specification of the RTL.

---
1. **Correct Weighted Summation:**
   - For each matching bit between the two input signals, the correlator must add a value of `+2` to the summation.
   - The `correlation_output` must always remain within the valid 4-bit range (0-15).

2. **Reset Behavior:**
   - On reset, the correlator must initialize its internal states and outputs (e.g., `correlation_output = 0`) to ensure a predictable starting point.

3. **Edge Case Handling:**
   - The design must handle edge cases where the weighted summation exceeds the maximum value representable by a 4-bit output. In such cases, the output must clamp to the maximum value.

4. **Consistent and Reliable Output:**
   - The correlator must produce accurate and bounded outputs across all valid input conditions, including corner cases and transitions after reset.

---

### **Functional Expectations**

1. **Weighted Summation:**
   - Each matching bit between `input_signal` and `reference_signal` contributes a weight of **+2** to the summation.
   - **Example Input:** `input_signal = 0b10101010`, `reference_signal = 0b10101010`.
   - **Expected Output:** `8` (4 matching bits × 2).

2. **Reset Behavior:**
   - On reset, the correlator initializes all internal states and the `correlation_output` to `0`.
   - **Action:** Assert reset, then deassert reset.
   - **Expected Output:** `correlation_output = 0`.


---
Please provide me with an RTL code that matches the specifications.
