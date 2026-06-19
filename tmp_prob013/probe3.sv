module probe3;
  wire [15:0] a,b;
  assign a=16'bz; assign b=16'bz;
  wire eq = (a===b);
  wire neq = (a!==b);
  wire xeq = (a == b);
  initial begin #1; $display("=== %b !== %b == %b", eq, neq, xeq); $finish; end
endmodule
