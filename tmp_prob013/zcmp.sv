module gen(output wire [3:0] o);
  assign o = 'hz;
endmodule
module tb;
  wire [3:0] a, b;
  gen g1(.o(a)), g2(.o(b));
  initial begin
    #1;
    if (a !== b) $display("MISMATCH a=%b b=%b", a, b);
    else $display("MATCH");
    if (a === b) $display("=== match");
    $finish;
  end
endmodule
