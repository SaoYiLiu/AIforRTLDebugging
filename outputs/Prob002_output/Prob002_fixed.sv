module TopModule(
    input clk,
    input rst_n,
    input a,
    output reg match
);

    reg [8:0] a_tem;

    always @(posedge clk or negedge rst_n)
        if (!rst_n) begin
            a_tem <= 9'b0;
            match <= 1'b0;
        end else begin
            match <= (a_tem[8:6] == 3'b011) && (a_tem[2:0] == 3'b110);
            a_tem <= {a, a_tem[8:1]};
        end

endmodule
