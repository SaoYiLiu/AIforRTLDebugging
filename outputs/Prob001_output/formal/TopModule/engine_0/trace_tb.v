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
  TopModule_formal UUT (

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
    UUT._witness_.anyinit_procdff_151 = 1'b0;
    UUT._witness_.anyinit_procdff_155 = 1'b0;
    UUT._witness_.anyinit_procdff_158 = 1'b0;
    UUT._witness_.anyinit_procdff_159 = 1'b0;
    UUT._witness_.anyinit_procdff_160 = 1'b0;
    UUT._witness_.anyinit_procdff_163 = 1'b0;
    UUT._witness_.anyinit_procdff_164 = 1'b0;
    UUT._witness_.anyinit_procdff_174 = 1'b1;
    UUT._witness_.anyinit_procdff_176 = 1'b1;
    UUT._witness_.anyinit_procdff_185 = 1'b1;
    UUT._witness_.anyinit_procdff_186 = 1'b1;
    UUT._witness_.anyinit_procdff_188 = 1'b1;
    UUT._witness_.anyinit_procdff_190 = 1'b1;
    UUT._witness_.anyinit_procdff_192 = 1'b1;

    // state 0
    UUT.a = 1'b1;
    UUT.rst_n = 1'b0;
  end
  always @(posedge clock) begin
    // state 1
    if (cycle == 0) begin
      UUT.a <= 1'b0;
      UUT.rst_n <= 1'b1;
    end

    // state 2
    if (cycle == 1) begin
      UUT.a <= 1'b1;
      UUT.rst_n <= 1'b1;
    end

    // state 3
    if (cycle == 2) begin
      UUT.a <= 1'b1;
      UUT.rst_n <= 1'b1;
    end

    // state 4
    if (cycle == 3) begin
      UUT.a <= 1'b1;
      UUT.rst_n <= 1'b1;
    end

    // state 5
    if (cycle == 4) begin
      UUT.a <= 1'b0;
      UUT.rst_n <= 1'b1;
    end

    // state 6
    if (cycle == 5) begin
      UUT.a <= 1'b0;
      UUT.rst_n <= 1'b1;
    end

    // state 7
    if (cycle == 6) begin
      UUT.a <= 1'b0;
      UUT.rst_n <= 1'b1;
    end

    // state 8
    if (cycle == 7) begin
      UUT.a <= 1'b1;
      UUT.rst_n <= 1'b1;
    end

    genclock <= cycle < 8;
    cycle <= cycle + 1;
  end
endmodule
