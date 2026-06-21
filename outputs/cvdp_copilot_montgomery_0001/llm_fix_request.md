Reply in the agent message only. Do not create, edit, or commit repository files.

You are debugging RTL for a CVDP hardware verification benchmark problem.

## Problem
cvdp_copilot_montgomery_0001

## Error type
logic

## Fix strategy
The design builds but fails cocotb/pytest checks in the CVDP harness. Use failing test cases and expected vs actual values from the harness log. Make minimal targeted fixes.

## Task description excerpt
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

## Current candidate files (line-numbered on patch targets)
### rtl/montgomery_redc.sv
```verilog
1| module montgomery_redc #
   2| (
   3|     parameter N = 7,              
   4|     parameter R = 8,              
   5|     parameter R_INVERSE = 1,
   6|     parameter NWIDTH = $clog2(N), 
   7|     parameter TWIDTH = $clog2(N*R)     
   8| )(
   9|     input  wire [TWIDTH-1:0] T,    
  10|     output wire [NWIDTH-1:0] result 
  11| );
  12|     // Derived parameters
  13|     localparam RWIDTH = $clog2(R)+1;         
  14|               
  15|     localparam [RWIDTH-1:0] N_PRIME = (R * R_INVERSE - 1) / N;       
  16| 
  17|     wire [RWIDTH-1:0] T_mod_R;               
  18|     wire [2*RWIDTH-1:0] T_mod_R_X_N_PRIME;      
  19|     wire [RWIDTH-1:0] m;                     
  20|     wire [NWIDTH:0] t;                      
  21| 
  22|     assign T_mod_R = T[RWIDTH-1:0]; 
  23| 
  24|     assign T_mod_R_X_N_PRIME = T_mod_R * N_PRIME;
  25| 
  26|     assign m = T_mod_R_X_N_PRIME[RWIDTH-1:0];
  27| 
  28|     assign t = (T + m * N) >> RWIDTH;
  29| 
  30|     assign result = (t >= N) ? (t - N) : t;
  31| 
  32| endmodule
```

## Files you must patch
rtl/montgomery_redc.sv

Primary module: `montgomery_redc`

## Structured harness feedback
```text
error_kind: logic

## Simulation failures
- cocotb: expected=? actual=Failure!
```



## Raw CVDP harness output excerpt
```text
## Key failure excerpts
0.00ns INFO     cocotb.regression                  running test_montgomery_redc.test_montgomery_redc (1/1)
     5.00ns WARNING  ..gomery_redc.test_montgomery_redc  Failure!
                                                        assert 593 == 514
                                                        Traceback (most recent call last):
                                                          File "/src/test_montgomery_redc.py", line 24, in test_montgomery_redc
                                                            assert dut_result == exprected_result, " Failure!"
                                                        AssertionError:  Failure!
                                                        assert 593 == 514
     5.00ns WARNING  cocotb.regression                  test_montgomery_redc.test_montgomery_redc failed
     5.00ns INFO     cocotb.regression                  ***************************************************************************************************
                                                        ** TEST                                       STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        ***************************************************************************************************
                                                        ** test_montgomery_redc.test_montgomery_redc   FAIL           5.00           0.01        839.90  **
                                                        ***************************************************************************************************
                                                        ** TESTS=1 PASS=0 FAIL=1 SKIP=0                               5.00           0.02        273.58  **
                                                        ***************************************************************************************************
FAILED

=================================== FAILURES ===================================
__________________________________ test_redc ___________________________________

    def test_redc():
        for _ in range(5):
             N, R, R_INVERSE = ranomize_test_param()
>            runner( N, R, R_INVERSE)

/src/test_runner.py:66: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

N = 673, R = 1024, R_INVERSE = 441

    def runner( N, R, R_INVERSE):
        runner = get_runner(sim)
        runner.build(
            sources=verilog_sources,
            hdl_toplevel=toplevel,
            parameters= {'N':N, 'R':R, 'R_INVERSE': R_INVERSE},
            always=True,
            clean=True,
            verbose=False,
            timescale=("1ns", "1ns"),
            log_file="sim.log")
>       runner.test(hdl_toplevel=toplevel, test_module=module, waves=True)
E       SystemExit: 1

/src/test_runner.py:26: SystemExit
------------------------------ Captured log call -------------------------------
INFO     Icarus:runner.py:632 Running command iverilog -o /code/rundir/sim_build/sim.vvp -s montgomery_redc -g2012 -Pmontgomery_redc.N=673 -Pmontgomery_redc.R=1024 -Pmontgomery_redc.R_INVERSE=441 -f /code/rundir/sim_build/cmds.f /code/rtl/montgomery_redc.sv in directory /code/rundir/sim_build
INFO     Icarus:runner.py:632 Running command vvp -M /venv/lib/python3.12/site-packages/cocotb/libs -m libcocotbvpi_icarus /code/rundir/sim_build/sim.vvp -fst in directory /code/rundir/sim_build
ERROR    Icarus:runner.py:572 ERROR: Failed 1 of 1 tests.
=============================== warnings summary ===============================
../../venv/lib/python3.12/site-packages/_pytest/cacheprovider.py:477
  /venv/lib/python3.12/site-packages/_pytest/cacheprovider.py:477: PytestCacheWarning: could not create cache path /rundir/harness/.cache/v/cache/nodeids: [Errno 13] Permission denied: '/rundir/harness/pytest-cache-files-mke2m1wv'
    config.cache.set

[... truncated 7670 chars from end of harness output ...]
```

## Cocotb test excerpt
### test_montgomery_redc.py
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ClockCycles, Timer
import random
import harness_library as hrs_lb


@cocotb.test()
async def test_montgomery_redc(dut): 
   N = int (dut.N.value)
   R = int (dut.R.value)
   R_INVERSE = int (dut.R_INVERSE.value)
   #TWO_NWIDTH = int (dut.TWO_NWIDTH.value)
   N_PRIME = (R * R_INVERSE - 1) // N
   await hrs_lb.dut_init(dut)


   for i in range(1000):
      T = random.randint(0, R*N-1)
      dut.T.value = T 
      exprected_result = hrs_lb.redc(T, N, R_INVERSE)
      await Timer(5, unit="ns")
      dut_result = int (dut.result.value) 
      assert dut_result == exprected_result, " Failure!"
```

## Task
- Fix the RTL so the CVDP Docker harness passes (cocotb/pytest).
- Output TWO sections:

## Rationale
3-8 bullet points citing line numbers and harness evidence.

## PatchedFiles
For each file in ['rtl/montgomery_redc.sv'], use:

### rtl/your_file.sv
```verilog
<full file contents>
```
