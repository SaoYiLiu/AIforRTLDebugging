`timescale 1 ps/1 ps
module mon;
  wire [15:0] lcm_ref = tb.lcm_out_ref;
  wire [15:0] lcm_dut = tb.lcm_out_dut;
  wire clk = tb.clk;
  always @(posedge clk, negedge clk) begin
    if (lcm_ref !== lcm_dut)
      $display("LCM mismatch t=%0d clk=%b ref=%b dut=%b", $time, clk, lcm_ref, lcm_dut);
  end
endmodule
