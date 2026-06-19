`timescale 1 ps/1 ps
module probe_tb;
  reg clk=0;
  initial forever #5 clk = ~clk;
  
  wire [15:0] a, b, c;
  // test what ref !== (ref ^ dut ^ ref) does for various z patterns
  
  // Case 1: both all z
  assign a = 16'bz;
  assign b = 16'bz;
  assign c = (a !== (a ^ b ^ a));
  
  // drive 0 when z-z should match
  initial begin
    #1;
    $display("both z: a=%b b=%b mismatch=%b", a, b, c);
    $finish;
  end
endmodule
