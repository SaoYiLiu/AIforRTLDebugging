module xorcmp2;
  reg [7:0] ref, dut;
  reg [15:0] ref16, dut16;
  initial begin
    ref=8'd4; dut=8'd4;
    $display("mcd 4,4: ===%b !==xor %b", ref===dut, ref!==(ref^dut));
    ref=8'd0; dut=8'd0;
    $display("mcd 0,0: ===%b !==xor %b", ref===dut, ref!==(ref^dut));
    ref16=16'd24; dut16=16'd24;
    $display("lcm 24,24: ===%b !==xor %b", ref16===dut16, ref16!==(ref16^dut16));
    ref16=16'bz; dut16=16'bz;
    $display("lcm z,z: ===%b !==xor %b", ref16===dut16, ref16!==(ref16^dut16));
  end
endmodule
