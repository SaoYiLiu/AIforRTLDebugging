`timescale 1 ps/1 ps
module debug_tb2;
  reg clk=0;
  initial forever #5 clk = ~clk;
  reg rst_n, vld_in;
  reg [7:0] A, B;
  wire [15:0] lcm_ref, lcm_dut;
  wire [7:0] mcd_ref, mcd_dut;
  wire vld_ref, vld_dut;
  RefModule good1(.A,.B,.vld_in,.rst_n,.clk,.lcm_out(lcm_ref),.mcd_out(mcd_ref),.vld_out(vld_ref));
  TopModule dut1(.A,.B,.vld_in,.rst_n,.clk,.lcm_out(lcm_dut),.mcd_out(mcd_dut),.vld_out(vld_dut));
  always @(posedge clk, negedge clk) begin
    if (lcm_ref !== lcm_dut)
      $display("MISMATCH t=%0d edge=%s ref=%b dut=%b", $time, clk?"posedge":"negedge", lcm_ref, lcm_dut);
  end
  initial begin
    rst_n=0; A=0; B=0; vld_in=0;
    @(posedge clk); @(posedge clk); rst_n=1; @(posedge clk);
    A=12; B=8; vld_in=1; @(posedge clk); vld_in=0;
    repeat(20) @(posedge clk);
    $finish;
  end
endmodule
