module counter_formal;
    localparam integer W = 4;

    // In formal, avoid `#delay` clock generators. Mark a free-running clock.
    (* gclk *) reg clk;

    // Allow inputs to vary arbitrarily unless constrained.
    (* anyseq *) reg rst_n;
    (* anyseq *) reg en;
    wire [W-1:0] q;

    counter #(.W(W)) dut (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .q(q)
    );

    always @(posedge clk) begin
        // Use $past() so properties match sequential semantics in formal.
        if (!$initstate) begin
            if (!$past(rst_n)) begin
                assert(q == {W{1'b0}});
            end else if ($past(en)) begin
                assert(q == ($past(q) + 1'b1));
            end else begin
                assert(q == $past(q));
            end
        end
    end
endmodule

