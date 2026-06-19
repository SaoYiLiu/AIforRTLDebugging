// BUGGY FIFO: empty flag is wrong when count==1 (off-by-one).
module fifo_buggy #(
    parameter integer W = 8,
    parameter integer DEPTH = 4
) (
    input  wire           clk,
    input  wire           rst_n,

    input  wire           push,
    input  wire [W-1:0]   din,
    output wire           full,

    input  wire           pop,
    output reg  [W-1:0]   dout,
    output wire           empty
);
    localparam integer AW = $clog2(DEPTH);

    reg [W-1:0] mem [0:DEPTH-1];
    reg [AW:0]  count;
    reg [AW-1:0] wptr;
    reg [AW-1:0] rptr;

    // BUG: should be (count==0)
    assign empty = (count <= 1);
    assign full  = (count == DEPTH);

    wire do_push = push && !full;
    wire do_pop  = pop  && !empty;

    always @(posedge clk) begin
        if (!rst_n) begin
            count <= 0;
            wptr  <= 0;
            rptr  <= 0;
            dout  <= {W{1'b0}};
        end else begin
            if (do_push) begin
                mem[wptr] <= din;
                wptr <= (wptr == DEPTH-1) ? 0 : (wptr + 1'b1);
            end
            if (do_pop) begin
                dout <= mem[rptr];
                rptr <= (rptr == DEPTH-1) ? 0 : (rptr + 1'b1);
            end

            case ({do_push, do_pop})
                2'b10: count <= count + 1'b1;
                2'b01: count <= count - 1'b1;
                default: count <= count;
            endcase
        end
    end
endmodule

