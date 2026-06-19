`timescale 1 ps/1 ps
module probe2;
  wire [15:0] lcm_ref, lcm_dut;
  wire [7:0] mcd_ref, mcd_dut;
  wire vld_ref, vld_dut;
  wire tb_match;
  
  assign lcm_ref = 16'bz;
  assign lcm_dut = 16'bz;
  assign mcd_ref = 8'd0;
  assign mcd_dut = 8'd0;
  assign vld_ref = 1'b0;
  assign vld_dut = 1'b0;
  
  assign tb_match = ( { lcm_ref, mcd_ref, vld_ref } === ( { lcm_ref, mcd_ref, vld_ref } ^ { lcm_dut, mcd_dut, vld_dut } ^ { lcm_ref, mcd_ref, vld_ref } ) );
  
  wire lcm_mis = (lcm_ref !== ( lcm_ref ^ lcm_dut ^ lcm_ref ));
  
  initial begin
    #1;
    $display("tb_match=%b lcm_individual_mis=%b", tb_match, lcm_mis);
    $finish;
  end
endmodule
