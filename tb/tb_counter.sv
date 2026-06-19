module tb_counter;
    localparam integer W = 4;

    reg clk;
    reg rst_n;
    reg en;
    wire [W-1:0] q;

    counter #(.W(W)) dut (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .q(q)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    initial begin
        $dumpfile("waves.vcd");
        $dumpvars(0, tb_counter);

        rst_n = 1'b0;
        en    = 1'b0;
        repeat (2) @(posedge clk);
        rst_n = 1'b1;

        repeat (3) @(posedge clk);
        en = 1'b1;
        repeat (20) @(posedge clk);
        en = 1'b0;
        repeat (5) @(posedge clk);

        $display("FINAL q=%0d", q);
        $finish;
    end
endmodule

