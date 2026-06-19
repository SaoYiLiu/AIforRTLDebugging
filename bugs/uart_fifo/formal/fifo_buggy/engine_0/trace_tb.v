`ifndef VERILATOR
module testbench;
  reg [4095:0] vcdfile;
  reg clock;
`else
module testbench(input clock, output reg genclock);
  initial genclock = 1;
`endif
  reg genclock = 1;
  reg [31:0] cycle = 0;
  fifo_formal UUT (

  );
`ifndef VERILATOR
  initial begin
    if ($value$plusargs("vcd=%s", vcdfile)) begin
      $dumpfile(vcdfile);
      $dumpvars(0, testbench);
    end
    #5 clock = 0;
    while (genclock) begin
      #5 clock = 0;
      #5 clock = 1;
    end
  end
`endif
  initial begin
`ifndef VERILATOR
    #1;
`endif
    UUT._witness_.anyinit_procdff_131 = 1'b0;
    UUT._witness_.anyinit_procdff_132 = 1'b0;
    UUT._witness_.anyinit_procdff_133 = 1'b0;
    UUT.dut.count = 3'b010;
    UUT.dut.dout = 8'b00000001;
    UUT.dut.\mem[0]  = 8'b00000000;
    UUT.dut.\mem[1]  = 8'b00000001;
    UUT.dut.\mem[2]  = 8'b00000000;
    UUT.dut.\mem[3]  = 8'b00000010;
    UUT.dut.rptr = 2'b11;
    UUT.dut.wptr = 2'b00;

    // state 0
    UUT.rst_n = 1'b0;
    UUT.din = 8'b01000000;
    UUT.pop = 1'b0;
    UUT.push = 1'b0;
  end
  always @(posedge clock) begin
    // state 1
    if (cycle == 0) begin
      UUT.rst_n <= 1'b1;
      UUT.din <= 8'b00000000;
      UUT.pop <= 1'b0;
      UUT.push <= 1'b1;
    end

    // state 2
    if (cycle == 1) begin
      UUT.rst_n <= 1'b1;
      UUT.din <= 8'b00000000;
      UUT.pop <= 1'b0;
      UUT.push <= 1'b1;
    end

    genclock <= cycle < 2;
    cycle <= cycle + 1;
  end
endmodule
