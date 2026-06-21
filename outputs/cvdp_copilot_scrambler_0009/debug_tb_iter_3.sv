`timescale 1ns/1ps

module tb_debug;
  localparam ROW_COL_WIDTH  = 16;
  localparam SUB_BLOCKS     = 4;
  localparam DATA_WIDTH     = ROW_COL_WIDTH * ROW_COL_WIDTH;
  localparam OUT_DATA_WIDTH = 8;   // first failing harness configuration
  localparam WAIT_CYCLES    = 4;
  localparam DELAY_WIDTH    = WAIT_CYCLES + SUB_BLOCKS;

  // Expected first output cycle after reset release (matches cocotb ~140ns failure)
  localparam EXPECT_FIRST_OUT_CYCLE = 14;

  reg clk;
  reg rst_n;
  reg i_valid;
  reg [DATA_WIDTH-1:0] in_data;
  wire [OUT_DATA_WIDTH-1:0] out_data;

  // Fixed registration vectors (non-zero, deterministic)
  reg [DATA_WIDTH-1:0] in_vec [0:3];
  integer cycle;
  integer i;
  reg model_expect_nonzero;
  reg tb_mismatch;
  time mismatch_time;

  deinter_block #(
    .ROW_COL_WIDTH (ROW_COL_WIDTH),
    .SUB_BLOCKS    (SUB_BLOCKS),
    .DATA_WIDTH    (DATA_WIDTH),
    .OUT_DATA_WIDTH(OUT_DATA_WIDTH),
    .WAIT_CYCLES   (WAIT_CYCLES)
  ) dut (
    .clk     (clk),
    .rst_n   (rst_n),
    .i_valid (i_valid),
    .in_data (in_data),
    .out_data(out_data)
  );

  initial begin
    in_vec[0] = 256'h79298167522286788569904978703262940766402908262000599647032566384411563930627;
    in_vec[1] = 256'h60921651673859372483073810096561741991422496087236131769723914113145817525896;
    in_vec[2] = 256'h15948969918685278851162349264924257006671784581180143767097893993609160231713;
    in_vec[3] = 256'h22168014708043515441013341973271960023962290487495289978793904859280312343390;
  end

  initial clk = 1'b0;
  always #5 clk = ~clk;

  initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, tb_debug);
  end

  initial begin
    tb_mismatch   = 1'b0;
    mismatch_time = 0;
    cycle         = 0;
    rst_n         = 1'b0;
    i_valid       = 1'b0;
    in_data       = {DATA_WIDTH{1'b0}};
    model_expect_nonzero = 1'b0;

    // Mirror cocotb: hold reset 10ns, release, wait 10ns, then run
    #10;
    rst_n = 1'b1;
    #10;

    for (cycle = 1; cycle <= 20; cycle = cycle + 1) begin
      @(posedge clk);

      case (cycle)
        2: begin i_valid = 1'b1; in_data = in_vec[0]; end
        3: begin i_valid = 1'b1; in_data = in_vec[1]; end
        4: begin i_valid = 1'b1; in_data = in_vec[2]; end
        5: begin i_valid = 1'b1; in_data = in_vec[3]; end
        default: begin i_valid = 1'b0; end
      endcase

      // After delay pipeline completes, model should produce first non-zero beat
      model_expect_nonzero = (cycle >= EXPECT_FIRST_OUT_CYCLE);

      if (model_expect_nonzero && (out_data == {OUT_DATA_WIDTH{1'b0}})) begin
        tb_mismatch   = 1'b1;
        mismatch_time = $time;
        $display("First mismatch occurred at time %0t", $time);
        $display("  cycle=%0d out_data=0x%0h (expected non-zero)", cycle, out_data);
        $display("  start_intra=%b start_intra_ff=0x%0h output_active=%b enable_output=%b",
                 dut.start_intra, dut.start_intra_ff, dut.output_active, dut.enable_output);
        $display("  counter_output=%0d counter_sub_out=%0d",
                 dut.counter_output, dut.counter_sub_out);
      end

      if (cycle == EXPECT_FIRST_OUT_CYCLE && dut.enable_output == 1'b0) begin
        tb_mismatch   = 1'b1;
        mismatch_time = $time;
        $display("First mismatch occurred at time %0t", $time);
        $display("  cycle=%0d enable_output still low (delay chain bug)", cycle);
        $display("  start_intra_ff=0x%0h DELAY_WIDTH=%0d tap=%b",
                 dut.start_intra_ff, DELAY_WIDTH, dut.start_intra_ff[DELAY_WIDTH-1]);
      end

      $display("t=%0t cycle=%0d i_valid=%b out_data=0x%0h enable=%b active=%b ff=0x%0h cnt=%0d",
               $time, cycle, i_valid, out_data,
               dut.enable_output, dut.output_active, dut.start_intra_ff, dut.counter_output);
    end

    #50;
    if (!tb_mismatch)
      $display("No mismatch detected in monitored window.");
    else
      $display("Summary: tb_mismatch=1, first event at time %0t", mismatch_time);
    $finish;
  end
endmodule
