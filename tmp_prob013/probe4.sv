module probe4;
  wire [15:0] a,b;
  assign a=16'bz; assign b=16'bz;
  wire neq = (a !== b);
  wire xtrick = (a !== (a ^ b ^ a));
  initial begin #1; $display("a!==b=%b xtrick=%b", neq, xtrick); $finish; end
endmodule
