module tb;
  reg [15:0] a, b, c;
  initial begin
    a = 'hz; b = 'hz;
    c = a ^ b ^ a;
    $display("a=%b b=%b c=%b a!==c=%0d a===b=%0d", a,b,c, a!==c, a===b);
    a = 16'bzzzzzzzzzzzzzzzz; b = 16'bzzzzzzzzzzzzzzzz;
    c = a ^ b ^ a;
    $display("16z: c=%b a!==c=%0d a===b=%0d", c, a!==c, a===b);
  end
endmodule
