The `FILO_RTL` module is designed to implement a synchronous First-In-Last-Out (FILO) buffer with push and pop operations driven by a single clock domain. During testing, it was observed that the `data_out` signal consistently outputs the last pushed value for all pop operations, failing to follow the expected LIFO behavior during `pop` operations. This issue indicates a potential problem with the stack pointer (`top`) logic or memory access during `pop` operations.

Below is a table showing the expected and actual values for `data_out` during pop operations:
| test cases | Expected value (data_out) | Actual value (data_out) |
|------------|---------------------------|-------------------------|
| PUSH 1     | 11                        | 11                      |
| PUSH 2     | 12                        | 12                      |
| PUSH 3     | 13                        | 13                      |
| POP 1      | 13                        | 13                      |
| POP 2      | 12                        | 13                      |
| POP 3      | 11                        | 13                      |

### Test Case Details:
##
  - **Source Clock Frequency:**
    - Clock (`clk`): 100 MHz
  - **Reset:**
    - Asynchronous Reset: Asserted (`reset=1`) after initialization.
  - **Expected Behavior:**
    - During valid pop operations (`pop=1` and `empty=0`), the `data_out` signal should produce the value stored in the FILO at the current top pointer (`top`) location, following FILO behavior.

  - **Actual Behavior:**
    - The `data_out` signal consistently outputs the last pushed value `13` during all pop operations, indicating that the FILO is not correctly decrementing the top pointer or reading the correct memory location.

### Example Test Case Behavior:
##
**Test Case:**

  - **Push Values:** `11`, `12`, `13`
  - **Expected Output:**
`data_out = 13` (first pop), `data_out = 12` (second pop), `data_out = 11` (third pop).
  - **Actual Output:**
`data_out = 13` (first pop), `data_out = 13` (second pop), `data_out = 13` (third pop).
