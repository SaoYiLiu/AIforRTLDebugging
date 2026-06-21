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
