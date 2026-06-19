module counter_formal;
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

    // Formal clock
    always #1 clk = ~clk;

    // Make reset eventually deassert (keeps proof simple)
    initial begin
        clk  = 1'b0;
        rst_n = 1'b0;
        en = 1'b0;
        #2;
        rst_n = 1'b1;
    end

    reg [W-1:0] q_prev;
    always @(posedge clk) begin
        q_prev <= q;

        if (!rst_n) begin
            assert(q == {W{1'b0}});
        end else if (en) begin
            assert(q == (q_prev + 1'b1));
        end else begin
            assert(q == q_prev);
        end
    end
endmodule

