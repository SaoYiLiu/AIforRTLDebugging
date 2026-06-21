# ReAct trace: Prob019

## Step 1
**Thought**: I need the buggy RTL and spec first.

**Action**: Read prompt file and extract TopModule.

**Observation**: Extracted 109 lines of TopModule RTL.

## Step 2
**Thought**: Start from the buggy RTL extracted from the prompt.

**Action**: Use extracted TopModule as initial candidate.

**Observation**: Candidate = buggy RTL.

## Step 3
**Thought**: Run simulation to compare DUT vs reference.

**Action**: run_iverilog(tb, ref, fixed) [iteration 1]

**Observation**: compile.rc=0, run.rc=0

## Step 4
**Thought**: There are mismatches; use simulation evidence (and waveform summary) to propose a patch.

**Action**: Call fixer() for iteration 2.

**Observation**: Cursor SDK produced candidate (len=3049 chars).

## Step 5
**Thought**: Run simulation to compare DUT vs reference.

**Action**: run_iverilog(tb, ref, fixed) [iteration 2]

**Observation**: compile.rc=0, run.rc=0

