module xorcmp;
  reg [15:0] ref, dut;
  initial begin
    ref=16'd24; dut=16'd24;
    $display("both 24: match=%b ref!==xor %b", (ref === dut), (ref !== (ref^dut)));
    ref=16'bz; dut=16'bz;
    $display("both z: match=%b ref!==xor %b", (ref === dut), (ref !== (ref^dut)));
    ref=16'bz; dut=16'd0;
    $display("ref z dut 0: match=%b ref!==xor %b", (ref === dut), (ref !== (ref^dut)));
    ref=16'd24; dut=16'd0;
    $display("ref 24 dut 0: match=%b ref!==xor %b", (ref === dut), (ref !== (ref^dut)));
  end
endmodule
// rerun
