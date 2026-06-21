module TopModule_formal;
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

    always @(posedge clk) begin
        if ($initstate) begin
            assume(!rst_n);
        end else if (!$past(rst_n, 9)) begin
            assert(!match);
        end else begin
            assert(match == (
                !a && $past(a) && $past(a, 2) &&
                $past(a, 6) && $past(a, 7) && !$past(a, 8)
            ));
        end
    end
endmodule
