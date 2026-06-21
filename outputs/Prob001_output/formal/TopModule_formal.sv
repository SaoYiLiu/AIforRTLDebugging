module TopModule_formal;
    localparam [7:0] PAT = 8'b0111_0001;

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
        end else if (!rst_n || !$past(rst_n)) begin
            assert(!match);
        end else if (rst_n && $past(rst_n) && $past(rst_n, 2) && $past(rst_n, 3) &&
                     $past(rst_n, 4) && $past(rst_n, 5) && $past(rst_n, 6) &&
                     $past(rst_n, 7)) begin
            assert(match == ({ $past(a, 7), $past(a, 6), $past(a, 5), $past(a, 4),
                               $past(a, 3), $past(a, 2), $past(a, 1), a } == PAT));
        end else begin
            assert(!match);
        end
    end
endmodule
