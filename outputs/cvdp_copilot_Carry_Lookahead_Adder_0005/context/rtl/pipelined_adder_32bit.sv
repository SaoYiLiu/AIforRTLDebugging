module pipelined_adder_32bit (
    input clk,       // Synchronous to posedge of clk 
    input reset,     // Synchronous active high reset
    input [31:0] A,  // 32 bit operand for addition  
    input [31:0] B,  // 32 bit operand for addition  
    input start,     // Active high signal to indicate when valid input data is provided
    output [31:0] S, // Final sum or result 
    output Co,       // Final carry out 
    output done      // Completion signal, active high when computation is complete    
);

    wire [7:0] A1, B1, A2, B2, A3, B3;
    wire carry1, carry2, carry3;
    wire [7:0] s13, s23, s12, A21, B21, A31, B31, A32, B32;
    wire [7:0] s1, s2, s3;
    wire control2, control1, control3, control4;

    dff #(1) FF00 (.clk(clk), .reset(reset), .D(1'b1), .Q(control1));

    dff #(8) FF11 (.clk(clk), .reset(reset), .D(A[15:8]), .Q(A1));
    dff #(8) FF12 (.clk(clk), .reset(reset), .D(B[15:8]), .Q(B1));
    dff #(8) FF13 (.clk(clk), .reset(reset), .D(A[23:16]), .Q(A2));
    dff #(8) FF14 (.clk(clk), .reset(reset), .D(B[23:16]), .Q(B2));
    dff #(8) FF15 (.clk(clk), .reset(reset), .D(A[31:24]), .Q(A3));
    dff #(8) FF16 (.clk(clk), .reset(reset), .D(B[31:24]), .Q(B3));

    carry_lookahead_adder #(8) ADD1 (.clk(clk), .reset(reset), .A(A[7:0]), .B(B[7:0]), .Cin(1'b0), .S(s1), .carry(carry1));

    dff #(1) FF01 (.clk(clk), .reset(reset), .D(control1), .Q(control2));

    dff #(8) FF21 (.clk(clk), .reset(reset), .D(s1), .Q(s12));
    dff #(8) FF23 (.clk(clk), .reset(reset), .D(A3), .Q(A21));
    dff #(8) FF24 (.clk(clk), .reset(reset), .D(B3), .Q(B21));
    dff #(8) FF25 (.clk(clk), .reset(reset), .D(A2), .Q(A31));
    dff #(8) FF26 (.clk(clk), .reset(reset), .D(B2), .Q(B31));

    carry_lookahead_adder #(8) ADD2 (.clk(clk), .reset(reset), .A(A1), .B(B1), .Cin(carry1), .S(s2), .carry(carry2));

    dff #(1) FF10 (.clk(clk), .reset(reset), .D(control2), .Q(control3));

    dff #(8) FF31 (.clk(clk), .reset(reset), .D(s2), .Q(s13));
    dff #(8) FF32 (.clk(clk), .reset(reset), .D(s12), .Q(s23));
    dff #(8) FF35 (.clk(clk), .reset(reset), .D(A31), .Q(A32));
    dff #(8) FF36 (.clk(clk), .reset(reset), .D(B31), .Q(B32));

    carry_lookahead_adder #(8) ADD3 (.clk(clk), .reset(reset), .A(A21), .B(B21), .Cin(carry2), .S(s3), .carry(carry3));

    dff #(1) FF111 (.clk(clk), .reset(reset), .D(control3), .Q(done));

    dff #(8) FF41 (.clk(clk), .reset(reset), .D(s13), .Q(S[7:0]));
    dff #(8) FF42 (.clk(clk), .reset(reset), .D(s23), .Q(S[15:8]));
    dff #(8) FF43 (.clk(clk), .reset(reset), .D(s3), .Q(S[23:16]));

    carry_lookahead_adder #(8) ADD4 (.clk(clk), .reset(reset), .A(A32), .B(B32), .Cin(carry3), .S(S[31:24]), .carry(Co));

endmodule

module carry_lookahead_adder #(parameter WIDTH = 32) (
    input [WIDTH-1:0] A,    // WIDTH bit operand for addition
    input [WIDTH-1:0] B,    // WIDTH bit operand for addition
    input Cin, clk, reset,  // Cin -> carry in, clk -> Synchronous to posedge of clk , reset -> Synchronous active high reset           
    output reg [WIDTH-1:0] S, // Final sum or result 
    output reg carry          // Final carry out           
);

    wire [WIDTH-1:0] P;
    wire [WIDTH-1:0] G;
    reg [WIDTH:0] C;

    wire [WIDTH-1:0] S1;
    wire carry1;

    // Generate (G) and Propagate (P) 
    genvar i;
    generate
        for (i = 0; i < WIDTH; i = i + 1) begin
            assign P[i] = A[i] ^ B[i];   
            assign G[i] = A[i] & B[i];   
        end
    endgenerate

    // Carry Calculation:
    generate
        for (i = 0; i < WIDTH; i = i + 1) begin
            always @(posedge clk) begin
                if (reset) begin
                    C <= 0; 
                end else begin
                    C[0] <= Cin;
                    C[i+1] <= G[i] | (P[i] & C[i]);
                end
            end
        end
    endgenerate

    // Final sum
    generate
        for (i = 0; i < WIDTH; i = i + 1) begin
            assign S1[i] = P[i] ^ C[i]; 
        end
    endgenerate

    // Final sum
    assign carry1 = C[WIDTH-1];

    always @(posedge clk) begin
        if (reset) begin
            S <= 0; 
            carry <= 0;   
        end else begin
            S <= S1; 
            carry <= carry1;
        end 
    end

endmodule 

module dff #(parameter WIDTH = 1) (
    input clk,               // clk -> Synchronous to posedge of clk 
    input reset,             // reset -> Synchronous active high reset
    input [WIDTH-1:0] D,     // D -> Data signal 
    output reg [WIDTH-1:0] Q // Q -> Output signal 
);
    always @(posedge clk) begin
        if (reset)
            Q <= {WIDTH{1'b0}};
        else
            Q <= D;
    end
endmodule