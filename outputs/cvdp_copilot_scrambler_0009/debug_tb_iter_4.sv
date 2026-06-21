`timescale 1ns/1ps

module tb_debug;
  localparam ROW_COL_WIDTH   = 16;
  localparam SUB_BLOCKS      = 4;
  localparam DATA_WIDTH      = ROW_COL_WIDTH * ROW_COL_WIDTH;
  localparam OUT_DATA_WIDTH  = 8;   // first failing harness config
  localparam WAIT_CYCLES     = 4;
  localparam DELAY_WIDTH     = WAIT_CYCLES + SUB_BLOCKS;
  localparam CLK_HALF        = 5;
  localparam FAIL_TIME_NS    = 140; // cocotb first failure time

  reg clk;
  reg rst_n;
  reg i_valid;
  reg [DATA_WIDTH-1:0] in_data;
  wire [OUT_DATA_WIDTH-1:0] out_data;

  integer i;
  integer loop_idx;
  reg tb_mismatch;
  time mismatch_time;

  // cocotb-style: apply inputs, then clock rises, then compare
  reg [DATA_WIDTH-1:0] in_vec [0:3];

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
    in_vec[0] = 256'h0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f202122232425262728;
    in_vec[1] = 256'hA1A2A3A4A5A6A7A8A9AAABACADAEAFB1B2B3B4B5B6B7B8B9BABBBCBDBEBFC1C2C3C4C5C6C7C8;
    in_vec[2] = 256'hF0E1D2C3B4A5968778695A4B3C2D1E0F00112233445566778899AABBCCDDEEFF00112233;
    in_vec[3] = 256'h13579BDF02468ACE13579BDF02468ACE13579BDF02468ACE13579BDF02468ACE1357;
  end

  initial clk = 1'b0;
  always #(CLK_HALF) clk = ~clk;

  initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, tb_debug);
  end

  task apply_inputs;
    input integer idx;
    begin
      if (idx < 4) begin
        i_valid = 1'b1;
        in_data = in_vec[idx];
      end else begin
        i_valid = 1'b0;
        in_data = {DATA_WIDTH{1'b0}};
      end
    end
  endtask

  task sample_and_check;
    input integer idx;
    reg expect_model_active;
    begin
      // Model expects first output around loop i=10 (140ns) for WAIT=4
      expect_model_active = (idx >= 10);

      $display("t=%0t loop_i=%0d rst_n=%b i_valid=%b out_data=0x%0h",
               $time, idx, rst_n, i_valid, out_data);
      $display("  start_intra=%b start_intra_ff=0x%0h delay_done=%b output_active=%b enable_output=%b cnt=%0d sub=%0d",
               dut.start_intra, dut.start_intra_ff, dut.delay_done,
               dut.output_active, dut.enable_output,
               dut.counter_output, dut.counter_sub_out);

      if (expect_model_active && out_data == {OUT_DATA_WIDTH{1'b0}}) begin
        tb_mismatch   = 1'b1;
        mismatch_time = $time;
        $display("First mismatch occurred at time %0t", $time);
        $display("  loop_i=%0d: model expects non-zero out_data, DUT=0", idx);
        $display("  enable_output=%b delay_done=%b start_intra_ff[MSB]=%b",
                 dut.enable_output, dut.delay_done, dut.start_intra_ff[DELAY_WIDTH-1]);
      end

      if ($time == FAIL_TIME_NS) begin
        if (out_data == {OUT_DATA_WIDTH{1'b0}}) begin
          tb_mismatch   = 1'b1;
          mismatch_time = $time;
          $display("First mismatch occurred at time %0t", $time);
          $display("  140ns harness failure reproduced: out_data=0, model expects data");
          $display("  ff=0x%0h enable=%b active=%b", dut.start_intra_ff, dut.enable_output, dut.output_active);
        end
      end
    end
  endtask

  initial begin
    tb_mismatch   = 1'b0;
    mismatch_time = 0;
    rst_n         = 1'b0;
    i_valid       = 1'b0;
    in_data       = {DATA_WIDTH{1'b0}};

    // cocotb: rst_n=0, Timer(10ns)
    #10;
    rst_n = 1'b1;
    // cocotb: Timer(10ns)
    #10;
    // cocotb: await RisingEdge(clk) -- align to next posedge with inputs already stable
    @(posedge clk);

    for (loop_idx = 0; loop_idx < 15; loop_idx = loop_idx + 1) begin
      apply_inputs(loop_idx);
      @(posedge clk);
      sample_and_check(loop_idx);
    end

    #50;
    if (!tb_mismatch)
      $display("PASS: no zero-output mismatch in monitored window.");
    else
      $display("FAIL: tb_mismatch=1 first at time %0t", mismatch_time);
    $finish;
  end
endmodule
