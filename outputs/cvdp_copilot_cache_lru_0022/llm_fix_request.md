Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_cache_lru_0022

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
Please analyze the RTL design for the **fifo_policy** module and identify the root cause of the erroneous behavior observed in the provided table. Ensure **way_replace** remains unchanged during hits while maintaining its correctness during misses or evictions. Use the table below as the primary reference for identifying the bug.

---

## Context:
The **fifo_policy** module demonstrates a bug highlighted in the provided table. The **way_replace** signal is being updated after a cache **hit**, which violates the expected behavior of the module. Specifically, in case of a **hit**, the **way_replace** signal should remain unchanged. Below is a detailed table for your reference:

| Cycle | access | hit   | miss (¬hit) | way_replace (Expected) | way_replace (Observed)  | Error Description         |
|-------|--------|-------|-------------|------------------------|-------------------------|---------------------------|
| 10    | 1      | 1     | 0           | Unchanged (0x01)       | Updated (0x02)          | Updated after hit (WRONG) |
| 20    | 1      | 0     | 1           | Updated (0x03)         | Updated (0x03)          | Behavior is correct       |
| 30    | 1      | 1     | 0           | Unchanged (0x03)       | Updated (0x04)          | Updated after hit (WRONG) |

### Observations:
- During cache hits (**hit** = 1), **way_replace** should remain constant, regardless of the **access** signal.
- The table indicates that **way_replace** is erroneously updated after a hit, as seen in cycles 10 and 30.
- Cache misses are derived as the logical negation of **hit** (**miss** = ¬**hit**).

---

## Correct Functionality of `fifo_policy` Module:

The `fifo_policy` module implements a FIFO-based cache replacement policy. Its primary function is to maintain an array (`fifo_array`) to determine which cache way should be replaced next, based on the FIFO principle. Below are the key details:

### Parameters:
- **NWAYS**: Number of cache ways.
- **NINDEXES**: Number of cache indexes.

### Inputs:
- **clock**: System clock (rising edge).
- **reset**: Reset signal for initializing the FIFO state. Reset is active-high and asynchronous.
- **index**: Cache index, selects the set in the cache.
- **way_select**: Currently selected cache way (input, but not directly used in the FIFO logic).
- **access**: Indicates an access to the cache.
- **hit**: Indicates whether the access was a cache hit. A value of `0` indicates a miss.

### Outputs:
- **way_replace**: The cache way to be replaced is determined based on the FIFO policy. After reset, it remains unchanged until the first miss for the index occurs.

### Functionality:
1. **Initialization**:
   - On reset, all entries in `fifo_array` are initialized to `0`.

2. **Update on Access**:
   - If there is an **access** and it is a **miss** (`~hit`):
     - The `fifo_array` entry for the corresponding index is incremented, indicating the next way to be replaced.

3. **Replacement Decision**:
   - The `fifo_array` value for the given `index` determines the **way_replace**, which is the next cache way to be replaced.

### Constraints:
- During a **cache hit**, the `fifo_array` remains unchanged.
- The **way_replace** output directly reflects the value stored in `fifo_array` for the given `index`.

## Current candidate files (line-numbered on patch targets)
### rtl/fifo_policy.sv
```verilog
1| module fifo_policy #(
   2|     parameter NWAYS = 4,
   3|     parameter NINDEXES = 32
   4| )(
   5|     input clock,
   6|     input reset,
   7|     input [$clog2(NINDEXES)-1:0] index,
   8|     input [$clog2(NWAYS)-1:0] way_select,
   9|     input access,
  10|     input hit,
  11|     output [$clog2(NWAYS)-1:0] way_replace
  12| );
  13| 
  14|     // FIFO array to track next way to be replaced
  15|     reg [$clog2(NWAYS)-1:0] fifo_array [NINDEXES-1:0];
  16| 
  17|     integer i;
  18| 
  19|     // Sequential logic for reset and fifo_array updates
  20|     always_ff @ (posedge clock or posedge reset) begin
  21|         if (reset) begin
  22|             for (i = 0; i < NINDEXES; i++) begin
  23|                 fifo_array[i] <= $clog2(NWAYS)'(0);
  24|             end
  25|         end else begin
  26|             if (access) begin
  27|                 // Set the fifo_array position for the next replacement
  28|                 fifo_array[index] <= fifo_array[index] + $clog2(NWAYS)'(1);
  29|             end
  30|         end
  31|     end
  32| 
  33|     assign way_replace = fifo_array[index];
  34| 
  35| endmodule : fifo_policy
```

## Files you must patch
rtl/fifo_policy.sv

Primary module: `fifo_policy`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=no replace is expected after hit
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
0.00ns INFO     cocotb.regression                  running test_fifo_policy.test_policy_working (1/1)
                                                            Main test function to call all tests.
     0.00ns INFO     test                               Starting test_policy_working...
     0.00ns WARNING  py.warnings                        /src/test_fifo_policy.py:117: DeprecationWarning: Use ``cocotb.start_soon`` instead.
                                                          await cocotb.start(Clock(dut.clock, clock_period, unit="ns", period_high=(clock_period+1)//2 if clock_period%2 else clock_period//2).start())
     0.00ns INFO     test                               NWAYS: 4  NINDEXES: 32
     0.00ns INFO     test                               Starting test_fifo_initialization...
[DEBUG] Reset complete
    15.00ns INFO     test                               test_fifo_initialization passed.
    15.00ns INFO     test                               Test 1: Initialization passed.
    15.00ns INFO     test                               Starting test_fifo_hit_increment...
[DEBUG] Reset complete
    35.00ns DEBUG    test                               Target index: 0, Target way: 0
[DEBUG] way_replace: 01
    55.00ns WARNING  ..licy_working.test_policy_working no replace is expected after hit
                                                        assert 1 == 0
                                                         +  where 1 = int(LogicArray('01', Range(1, 'downto', 0)))
                                                         +    where LogicArray('01', Range(1, 'downto', 0)) = LogicArrayObject(fifo_policy.way_replace).value
                                                         +      where LogicArrayObject(fifo_policy.way_replace) = HierarchyObject(fifo_policy).way_replace
                                                        Traceback (most recent call last):
                                                          File "/src/test_fifo_policy.py", line 127, in test_policy_working
                                                            await test_fifo_hit_increment(dut)
                                                          File "/src/test_fifo_policy.py", line 45, in test_fifo_hit_increment
                                                            assert int(dut.way_replace.value) == 0, "no replace is expected after hit"
                                                        AssertionError: no replace is expected after hit
                                                        assert 1 == 0
                                                         +  where 1 = int(LogicArray('01', Range(1, 'downto', 0)))
                                                         +    where LogicArray('01', Range(1, 'downto', 0)) = LogicArrayObject(fifo_policy.way_replace).value
                                                         +      where LogicArrayObject(fifo_policy.way_replace) = HierarchyObject(fifo_policy).way_replace
    55.00ns WARNING  cocotb.regression                  test_fifo_policy.test_policy_working failed
    55.00ns INFO     cocotb.regression                  **********************************************************************************************
                                                        ** TEST                                  STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        **********************************************************************************************
                                                        ** test_fifo_policy.test_policy_working   FAIL          55.00           0.01       5444.32  **
                                                        **********************************************************************************************
                                                        ** TESTS=1 PASS=0

[... truncated 12362 chars from end of harness output ...]
```

## Cocotb test excerpt
### test_fifo_policy.py
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
import random
import time
import harness_library as hrs_lb


async def test_fifo_initialization(dut):
    """Test if FIFO counters are correctly initialized to 0 after reset."""
    cocotb.log.info("Starting test_fifo_initialization...")

    nindexes = int(dut.NINDEXES.value)

    await hrs_lb.reset(dut)

    index = 0
    assert dut.fifo_array[index].value == 0, f"Counter for index {index} not initialized to 0."

    index = nindexes - 1
    assert dut.fif

[... truncated 2837 chars from cocotb test excerpt ...]

t"

    index = random.randint(1, nindexes - 2)
    for i in range(overflows):
        for n in range(nways):
            target_way = n
            cocotb.log.debug(f"Target index: {index}, Target way: {target_way}")
            await hrs_lb.access_miss(dut, index, target_way)
            assert int(dut.way_replace.value) == (n + 1) % nways, "on a miss, the next position is selected for replacement"

    cocotb.log.info("test_fifo_replacement_order passed.")


@cocotb.test()
async def test_policy_working(dut):
    """Main test function to call all tests."""
    cocotb.log.setLevel("DEBUG"
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/fifo_policy.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
