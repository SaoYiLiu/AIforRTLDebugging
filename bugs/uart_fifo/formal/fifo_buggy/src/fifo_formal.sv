module fifo_formal;
    localparam integer W = 8;
    localparam integer DEPTH = 4;

    (* gclk *) reg clk;
    (* anyseq *) reg rst_n;
    (* anyseq *) reg push;
    (* anyseq *) reg pop;
    (* anyseq *) reg [W-1:0] din;

    wire full;
    wire empty;
    wire [W-1:0] dout;

`ifdef USE_BUGGY
    fifo_buggy #(.W(W), .DEPTH(DEPTH)) dut (
`else
    fifo #(.W(W), .DEPTH(DEPTH)) dut (
`endif
        .clk(clk), .rst_n(rst_n),
        .push(push), .din(din), .full(full),
        .pop(pop), .dout(dout), .empty(empty)
    );

    // Property: empty must be equivalent to count==0. We can't see count here,
    // but we can at least enforce: after a successful push (not full), empty
    // must be deasserted in the next cycle (assuming reset was deasserted).
    always @(posedge clk) begin
        // Force a clean reset sequence so internal regs are initialized.
        if ($initstate) begin
            assume(!rst_n);
            assume(!push);
            assume(!pop);
        end else begin
            assume(rst_n);
            // For this demo, prohibit pops so a single push must make the FIFO non-empty.
            assume(!pop);

            if ($past(rst_n) && $past(push) && !$past(full)) begin
                assert(!empty);
            end
        end
    end
endmodule

