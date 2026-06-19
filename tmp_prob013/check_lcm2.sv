`timescale 1ps/1ps
module check_lcm2;
  wire clk = tb.clk;
  wire [15:0] lr = tb.lcm_out_ref, ld = tb.lcm_out_dut;
  always @(posedge clk, negedge clk) begin
    if (lr !== (lr ^ ld ^ lr))
      $display("TB fail t=%0d ref=%b dut=%b direct!==%b", $time, lr, ld, (lr!==ld));
  end
endmodule
