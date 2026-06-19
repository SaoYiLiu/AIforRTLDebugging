
module ztest;
  wire [15:0] a=16'bz, b=16'bz;
  initial begin
    $display("a===b %b", a===b);
    $display("a!==b %b", a!==b);
    $display("a!==(a^b^a) %b", a!==(a^b^a));
    $display("a^b %b", a^b);
  end
endmodule
