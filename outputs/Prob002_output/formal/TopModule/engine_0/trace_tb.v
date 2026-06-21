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
    // UUT.$past$TopModule_formal.\sv:17$2$8  = 1'b0;
    UUT._witness_.anyinit_procdff_103 = 1'b0;
    UUT._witness_.anyinit_procdff_104 = 1'b0;
    UUT._witness_.anyinit_procdff_106 = 1'b1;
    UUT._witness_.anyinit_procdff_107 = 1'b0;
    UUT._witness_.anyinit_procdff_108 = 1'b1;
    UUT._witness_.anyinit_procdff_109 = 1'b0;
    UUT._witness_.anyinit_procdff_115 = 1'b0;
    UUT._witness_.anyinit_procdff_83 = 1'b0;
    UUT._witness_.anyinit_procdff_84 = 1'b0;
    UUT._witness_.anyinit_procdff_85 = 1'b0;
    UUT._witness_.anyinit_procdff_86 = 1'b0;
    UUT._witness_.anyinit_procdff_87 = 1'b0;
    UUT._witness_.anyinit_procdff_88 = 1'b0;
    UUT._witness_.anyinit_procdff_89 = 1'b0;
    UUT._witness_.anyinit_procdff_90 = 1'b1;
    UUT._witness_.anyinit_procdff_99 = 1'b1;

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

    genclock <= cycle < 1;
    cycle <= cycle + 1;
  end
endmodule
