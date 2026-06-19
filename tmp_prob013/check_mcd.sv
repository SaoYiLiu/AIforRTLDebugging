`timescale 1ps/1ps
module check_mcd;
  wire clk = tb.clk;
  wire [7:0] mr = tb.mcd_out_ref, md = tb.mcd_out_dut;
  always @(posedge clk, negedge clk) begin
    if (mr != 0 || md != 0)
      $display("t=%0d mcd r=%0d d=%0d xor_fail=%b ===%b", $time, mr, md, (mr !== (mr^md)), (mr===md));
  end
endmodule
