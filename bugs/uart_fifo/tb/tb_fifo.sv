module tb_fifo;
    localparam integer W = 8;
    localparam integer DEPTH = 4;

    reg clk;
    reg rst_n;

    reg push;
    reg [W-1:0] din;
    wire full;

    reg pop;
    wire [W-1:0] dout;
    wire empty;

`ifdef USE_BUGGY
    fifo_buggy #(.W(W), .DEPTH(DEPTH)) dut (
`else
    fifo #(.W(W), .DEPTH(DEPTH)) dut (
`endif
        .clk(clk), .rst_n(rst_n),
        .push(push), .din(din), .full(full),
        .pop(pop), .dout(dout), .empty(empty)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    integer i;
    reg [W-1:0] expected;

    initial begin
        $dumpfile("fifo_waves.vcd");
        $dumpvars(0, tb_fifo);

        rst_n = 1'b0;
        push = 1'b0;
        pop  = 1'b0;
        din  = 0;
        expected = 0;

        repeat (2) @(posedge clk);
        rst_n = 1'b1;

        // Push 1 element
        @(posedge clk);
        push = 1'b1; din = 8'hA5;
        @(posedge clk);
        push = 1'b0;

        // Now FIFO should NOT be empty.
        @(posedge clk);
        if (empty) begin
            $display("FAIL: empty asserted with one element in FIFO");
            $finish;
        end

        // Pop should return 0xA5
        pop = 1'b1;
        @(posedge clk);
        pop = 1'b0;
        @(posedge clk);
        if (dout !== 8'hA5) begin
            $display("FAIL: expected 0xA5, got 0x%0h", dout);
            $finish;
        end

        $display("PASS");
        $finish;
    end
endmodule

