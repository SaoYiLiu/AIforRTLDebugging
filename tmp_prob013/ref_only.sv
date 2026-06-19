module TopModule(output wire [15:0] o);
  reg [15:0] r;
  assign o = (r == 0) ? 'hz : r;
endmodule
