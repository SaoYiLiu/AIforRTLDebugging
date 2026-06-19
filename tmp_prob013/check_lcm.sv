`timescale 1ps/1ps
module check_lcm;
  wire clk = tb.clk;
  wire [15:0] lr = tb.lcm_out_ref, ld = tb.lcm_out_dut;
  always @(posedge clk, negedge clk) begin
    if (lr !== ld)
      $display("LCM diff t=%0d clk=%b ref=%b dut=%b", $time, clk, lr, ld);
  end
endmodule
