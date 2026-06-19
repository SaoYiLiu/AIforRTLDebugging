module TopModule#(parameter DATA_W=8)(input [DATA_W-1:0] A,B, input vld_in,rst_n,clk, output wire [DATA_W*2-1:0] lcm_out, output wire [DATA_W-1:0] mcd_out, output reg vld_out);
    reg [DATA_W*2-1:0] A_reg,B_reg,mcd_out_r1,mult_reg; reg [1:0] c_state,n_state;
    parameter IDLE='d0,lcm1='d1,Finish='d2;
    always @(posedge clk , negedge rst_n) if(~rst_n) c_state<=IDLE; else c_state<=n_state;
    always @(*) case(c_state)
        IDLE: n_state = vld_in ? lcm1 : IDLE;
        lcm1: n_state = (A_reg==B_reg) ? Finish : lcm1;
        Finish: n_state = IDLE;
        default: n_state = IDLE;
    endcase
    always @(posedge clk , negedge rst_n) begin
        if(~rst_n) begin A_reg<=0; B_reg<=0; mcd_out_r1<=0; mult_reg<=0; end
        else case(c_state)
        IDLE: if(vld_in) begin A_reg<=A; B_reg<=B; mult_reg<=A*B; mcd_out_r1<=0; end
              else begin A_reg<=A_reg; B_reg<=B_reg; mult_reg<=mult_reg; mcd_out_r1<=0; end
        lcm1: if(A_reg>B_reg) begin A_reg<=A_reg-B_reg; B_reg<=B_reg; end
              else if(A_reg<B_reg) begin B_reg<=B_reg-A_reg; A_reg<=A_reg; end
              else begin A_reg<=A_reg; B_reg<=B_reg; end
        Finish: mcd_out_r1<=A_reg;
        default: begin A_reg<=0; B_reg<=0; mcd_out_r1<=0; mult_reg<=0; end
        endcase
    end
    assign mcd_out = mcd_out_r1;
    assign lcm_out = (mcd_out_r1 == 0) ? {DATA_W*2{1'bx}} : (mult_reg / mcd_out_r1);
    always @(posedge clk , negedge rst_n) begin
        if(~rst_n) vld_out<=0; else if(c_state==Finish) vld_out<=1; else vld_out<=0;
    end
endmodule
