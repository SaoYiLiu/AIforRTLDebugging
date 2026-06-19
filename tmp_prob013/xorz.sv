module gen(output wire [15:0] o); assign o = {16{1'bz}}; endmodule
module tb;
  wire [15:0] ref, dut;
  gen r(.o(ref)), d(.o(dut));
  initial begin
    #1;
    if (ref !== (ref ^ dut ^ ref)) $display("MISMATCH ref=%b dut=%b xor=%b", ref, dut, ref^dut^ref);
    else $display("MATCH");
    $finish;
  end
endmodule
