module TopModule_formal;
    localparam [7:0] TARGET = 8'b0111_0001;

    (* gclk *) reg clk;
    (* anyseq *) reg rst_n;
    (* anyseq *) reg a;
    wire match;

    TopModule dut (
        .clk(clk),
        .rst_n(rst_n),
        .a(a),
        .match(match)
    );

    // Golden shift-register state (RefModule behavior, not instantiated).
    reg [7:0] gold_a_tem;

    always @(posedge clk) begin
        if (!rst_n)
            gold_a_tem <= 8'b0;
        else
            gold_a_tem <= {gold_a_tem[6:0], a};
    end

    always @(posedge clk) begin
        if ($initstate) begin
            assume(!rst_n);
            assume(!a);
        end else if (!rst_n || !$past(rst_n)) begin
            assert(match == 1'b0);
        end else begin
            assert(gold_a_tem == { $past(gold_a_tem[6:0]), $past(a) });
            assert(match == ($past(gold_a_tem) == TARGET));
        end
    end
endmodule
