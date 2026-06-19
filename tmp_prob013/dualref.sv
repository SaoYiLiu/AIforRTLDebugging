module TopModule#(parameter DATA_W=8)(input [DATA_W-1:0] A,B, input vld_in,rst_n,clk, output [DATA_W*2-1:0] lcm_out, output [DATA_W-1:0] mcd_out, output reg vld_out);
RefModule r(.A,.B,.vld_in,.rst_n,.clk,.lcm_out,.mcd_out,.vld_out);
endmodule
