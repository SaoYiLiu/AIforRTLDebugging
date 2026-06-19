module counter #(
    parameter integer W = 4
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         en,
    output reg  [W-1:0] q
);
    always @(posedge clk) begin
        if (!rst_n) begin
            q <= {W{1'b0}};
        end else if (en) begin
            q <= q + 1'b1;
        end
    end
endmodule

