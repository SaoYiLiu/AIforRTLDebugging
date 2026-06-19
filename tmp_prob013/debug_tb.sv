`timescale 1 ps/1 ps
module debug_tb;
  reg clk=0;
  initial forever #5 clk = ~clk;
  reg rst_n, vld_in;
  reg [7:0] A, B;
  wire [15:0] lcm_ref, lcm_dut;
  wire [7:0] mcd_ref, mcd_dut;
  wire vld_ref, vld_dut;
  RefModule good1(.A,.B,.vld_in,.rst_n,.clk,.lcm_out(lcm_ref),.mcd_out(mcd_ref),.vld_out(vld_ref));
  TopModule dut1(.A,.B,.vld_in,.rst_n,.clk,.lcm_out(lcm_dut),.mcd_out(mcd_dut),.vld_out(vld_dut));
  initial begin
    rst_n=0; A=0; B=0; vld_in=0;
    @(posedge clk); @(posedge clk);
    rst_n=1; @(posedge clk);
    A=12; B=8; vld_in=1; @(posedge clk);
    vld_in=0;
    repeat(15) begin
      @(posedge clk);
      $display("t=%0d ref lcm=%b dut lcm=%b match=%b vld_r=%b vld_d=%b mcd_r=%0d mcd_d=%0d",
        $time, lcm_ref, lcm_dut, (lcm_ref === lcm_dut), vld_ref, vld_dut, mcd_ref, mcd_dut);
    end
    $finish;
  end
endmodule
