module t;
  reg [15:0] ref, dut;
  initial begin
    ref=16'bz; dut=16'b0;
    $display("ref z dut 0: !==xor %b xor=%b", ref!==(ref^dut^ref), (ref^dut^ref));
    ref=16'bz; dut=16'bz;
    $display("ref z dut z: !==xor %b xor=%b", ref!==(ref^dut^ref), (ref^dut^ref));
    ref=16'd24; dut=16'd24;
    $display("ref 24 dut 24: !==xor %b xor=%b", ref!==(ref^dut^ref), (ref^dut^ref));
    ref=16'd24; dut=16'b0;
    $display("ref 24 dut 0: !==xor %b", ref!==(ref^dut^ref));
  end
endmodule
