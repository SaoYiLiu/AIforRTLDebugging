mcp_server.py is meant to start a local MCP server that exposes three callable “tools” (Icarus compile/run, VCD→text, and SymbiYosys run) so an agent/LLM can invoke them with structured inputs and get structured outputs.

It defines and runs an MCP tool server (over stdio) with three tools your agent can call:

## Quickstart demo (exercise all 3 tools)

This repo includes a tiny counter example:

- `rtl/counter.sv`
- `tb/tb_counter.sv` (writes `waves.vcd`)
- `formal/counter.sby`

In Cursor (after you’ve added the MCP server), try:

- `run_iverilog`:
  - `sources`: `["rtl/counter.sv", "tb/tb_counter.sv"]`
  - `top`: `"tb_counter"`
  - `output`: `"build/a.out"`
  - `run`: `true`
- `vcd_to_text`:
  - `vcd_path`: `"waves.vcd"`
  - first call with `signals: null` to list available signals
  - then call with `signals: ["tb_counter.q", "tb_counter.en", "tb_counter.rst_n"]`
- `run_sby`:
  - `sby_file`: `"formal/counter.sby"`
  - Requires **YosysHQ Yosys** (not Ubuntu apt 0.9); see `docs/SETUP.md`

## First real debug case: UART FIFO (with a bug)

Case folder: `bugs/uart_fifo/`

- **Golden RTL**: `bugs/uart_fifo/rtl/fifo.sv`
- **Buggy RTL**: `bugs/uart_fifo/rtl/fifo_buggy.sv` (empty off-by-one)
- **TB**: `bugs/uart_fifo/tb/tb_fifo.sv` (writes `fifo_waves.vcd`)
- **Formal**:
  - `bugs/uart_fifo/formal/fifo.sby` (should PASS)
  - `bugs/uart_fifo/formal/fifo_buggy.sby` (should FAIL)

