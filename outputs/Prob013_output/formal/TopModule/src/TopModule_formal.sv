module TopModule_formal;
    localparam integer DATA_W = 8;

    (* gclk *) reg clk;
    (* anyseq *) reg rst_n;
    (* anyseq *) reg [DATA_W-1:0] A;
    (* anyseq *) reg [DATA_W-1:0] B;
    (* anyseq *) reg vld_in;

    wire [DATA_W*2-1:0] lcm_out;
    wire [DATA_W-1:0]   mcd_out;
    wire                vld_out;

    TopModule #(.DATA_W(DATA_W)) dut (
        .clk(clk),
        .rst_n(rst_n),
        .A(A),
        .B(B),
        .vld_in(vld_in),
        .lcm_out(lcm_out),
        .mcd_out(mcd_out),
        .vld_out(vld_out)
    );

    always @(posedge clk) begin
        if ($initstate) begin
            assume(!rst_n);
        end else begin
            if ($past(rst_n))
                assume(A == $past(A) && B == $past(B));

            if (!$past(rst_n)) begin
                assert(!vld_out && (mcd_out == {DATA_W{1'b0}}));
            end else if (!vld_out) begin
                assert(mcd_out == {DATA_W{1'b0}});
            end else if (vld_out && !$past(vld_out)) begin
                assert((A % mcd_out) == 0 && (B % mcd_out) == 0);
            end
        end
    end
endmodule
