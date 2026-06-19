`timescale 1ps/1ps
module tb;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0, vld_in=0; reg [7:0] A=0,B=0;
  wire [15:0] lr, ld;
  RefModule good1(.A,.B,.vld_in,.rst_n,.clk,.lcm_out(lr),.mcd_out(),.vld_out());
  TopModule dut1(.A,.B,.vld_in,.rst_n,.clk,.lcm_out(ld),.mcd_out(),.vld_out());
  always @(posedge clk, negedge clk) begin
    if (lr !== (lr ^ ld ^ lr))
      $display("MISMATCH t=%0d lr=%b ld=%b xor=%b", $time, lr, ld, (lr ^ ld ^ lr));
    else
      $display("MATCH t=%0d lr=%b ld=%b", $time, lr, ld);
  end
  initial begin
    repeat(3) @(posedge clk); rst_n=1; @(posedge clk);
    A=12; B=8; vld_in=1; @(posedge clk); vld_in=0;
    repeat(25) @(posedge clk);
    $finish;
  end
endmodule
