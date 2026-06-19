module tb;
  reg [15:0] a, b;
  initial begin
    a = 'hz; b = 'hz;
    if (a !== (a ^ b ^ a)) $display("hz hz: XOR cmp says MISMATCH");
    else $display("hz hz: XOR cmp says match");
    a = 16'd24; b = 16'd24;
    if (a !== (a ^ b ^ a)) $display("24 24: MISMATCH");
    else $display("24 24: match");
    a = 'hz; b = 16'd0;
    if (a !== (a ^ b ^ a)) $display("hz 0: MISMATCH");
    else $display("hz 0: match");
  end
endmodule
