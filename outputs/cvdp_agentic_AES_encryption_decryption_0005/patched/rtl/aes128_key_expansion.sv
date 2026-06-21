module aes128_key_expansion #(
    parameter NBW_KEY = 'd128,
    parameter NBW_OUT = 'd1408
) (
    input  logic               clk,
    input  logic               rst_async_n,
    input  logic               i_start,
    input  logic [NBW_KEY-1:0] i_key,
    output logic               o_done,
    output logic [NBW_OUT-1:0] o_expanded_key
);

localparam NBW_BYTE = 'd8;
localparam NBW_WORD = 'd32;
localparam STEPS    = 'd10;

logic [NBW_OUT-1:0] expanded_key_nx;
logic [NBW_OUT-1:0] expanded_key_ff;
logic [STEPS:0]     key_exp_steps_ff;

logic [NBW_WORD-1:0] rotword_0, rotword_1, rotword_2, rotword_3, rotword_4;
logic [NBW_WORD-1:0] rotword_5, rotword_6, rotword_7, rotword_8, rotword_9;

logic [NBW_WORD-1:0] subword_0, subword_1, subword_2, subword_3, subword_4;
logic [NBW_WORD-1:0] subword_5, subword_6, subword_7, subword_8, subword_9;

logic [NBW_WORD-1:0] rcon_xor_0, rcon_xor_1, rcon_xor_2, rcon_xor_3, rcon_xor_4;
logic [NBW_WORD-1:0] rcon_xor_5, rcon_xor_6, rcon_xor_7, rcon_xor_8, rcon_xor_9;

logic [NBW_WORD-1:0] nk0_0, nk0_1, nk0_2, nk0_3;
logic [NBW_WORD-1:0] nk1_0, nk1_1, nk1_2, nk1_3;
logic [NBW_WORD-1:0] nk2_0, nk2_1, nk2_2, nk2_3;
logic [NBW_WORD-1:0] nk3_0, nk3_1, nk3_2, nk3_3;
logic [NBW_WORD-1:0] nk4_0, nk4_1, nk4_2, nk4_3;
logic [NBW_WORD-1:0] nk5_0, nk5_1, nk5_2, nk5_3;
logic [NBW_WORD-1:0] nk6_0, nk6_1, nk6_2, nk6_3;
logic [NBW_WORD-1:0] nk7_0, nk7_1, nk7_2, nk7_3;
logic [NBW_WORD-1:0] nk8_0, nk8_1, nk8_2, nk8_3;
logic [NBW_WORD-1:0] nk9_0, nk9_1, nk9_2, nk9_3;

logic [NBW_KEY-1:0] nrk0, nrk1, nrk2, nrk3, nrk4, nrk5, nrk6, nrk7, nrk8, nrk9;

logic               active_write;
logic [NBW_OUT-1:0] ek_write_mux;

assign o_expanded_key = expanded_key_ff;
assign o_done         = key_exp_steps_ff[STEPS];

assign active_write = |key_exp_steps_ff[STEPS-1:0] && !key_exp_steps_ff[STEPS];

assign expanded_key_nx = i_start ? {i_key, {(NBW_OUT-NBW_KEY){1'b0}}} :
                         active_write ? ek_write_mux : expanded_key_ff;

assign ek_write_mux = key_exp_steps_ff[0] ? {expanded_key_ff[NBW_OUT-1:1280], nrk0, expanded_key_ff[1151:0]} :
                      key_exp_steps_ff[1] ? {expanded_key_ff[NBW_OUT-1:1152], nrk1, expanded_key_ff[1023:0]} :
                      key_exp_steps_ff[2] ? {expanded_key_ff[NBW_OUT-1:1024], nrk2, expanded_key_ff[895:0]} :
                      key_exp_steps_ff[3] ? {expanded_key_ff[NBW_OUT-1:896],  nrk3, expanded_key_ff[767:0]} :
                      key_exp_steps_ff[4] ? {expanded_key_ff[NBW_OUT-1:768],  nrk4, expanded_key_ff[639:0]} :
                      key_exp_steps_ff[5] ? {expanded_key_ff[NBW_OUT-1:640],  nrk5, expanded_key_ff[511:0]} :
                      key_exp_steps_ff[6] ? {expanded_key_ff[NBW_OUT-1:512],  nrk6, expanded_key_ff[383:0]} :
                      key_exp_steps_ff[7] ? {expanded_key_ff[NBW_OUT-1:384],  nrk7, expanded_key_ff[255:0]} :
                      key_exp_steps_ff[8] ? {expanded_key_ff[NBW_OUT-1:256],  nrk8, expanded_key_ff[127:0]} :
                      key_exp_steps_ff[9] ? {expanded_key_ff[NBW_OUT-1:128],  nrk9} :
                      expanded_key_ff;

always_ff @(posedge clk or negedge rst_async_n) begin : reset_regs
    if(~rst_async_n) begin
        expanded_key_ff  <= {NBW_OUT{1'b0}};
        key_exp_steps_ff <= '0;
    end else begin
        expanded_key_ff <= expanded_key_nx;

        if(i_start) begin
            key_exp_steps_ff <= {{(STEPS-1){1'b0}}, 1'b1};
        end else begin
            if(key_exp_steps_ff[STEPS]) begin
                key_exp_steps_ff <= '0;
            end else if(|key_exp_steps_ff[STEPS-1:0]) begin
                key_exp_steps_ff <= key_exp_steps_ff << 1'b1;
            end
        end
    end
end

assign rotword_0 = {expanded_key_ff[1303:1280], expanded_key_ff[1311:1304]};
assign rotword_1 = {expanded_key_ff[1175:1152], expanded_key_ff[1183:1176]};
assign rotword_2 = {expanded_key_ff[1047:1024], expanded_key_ff[1055:1048]};
assign rotword_3 = {expanded_key_ff[919:896],   expanded_key_ff[927:920]};
assign rotword_4 = {expanded_key_ff[791:768],   expanded_key_ff[799:792]};
assign rotword_5 = {expanded_key_ff[663:640],   expanded_key_ff[671:664]};
assign rotword_6 = {expanded_key_ff[535:512],   expanded_key_ff[543:536]};
assign rotword_7 = {expanded_key_ff[407:384],   expanded_key_ff[415:408]};
assign rotword_8 = {expanded_key_ff[279:256],   expanded_key_ff[287:280]};
assign rotword_9 = {expanded_key_ff[151:128],   expanded_key_ff[159:152]};

sbox uu_sbox0_0 (.i_data(rotword_0[31:24]), .o_data(subword_0[31:24]));
sbox uu_sbox0_1 (.i_data(rotword_0[23:16]), .o_data(subword_0[23:16]));
sbox uu_sbox0_2 (.i_data(rotword_0[15:8]),  .o_data(subword_0[15:8]));
sbox uu_sbox0_3 (.i_data(rotword_0[7:0]),   .o_data(subword_0[7:0]));

sbox uu_sbox1_0 (.i_data(rotword_1[31:24]), .o_data(subword_1[31:24]));
sbox uu_sbox1_1 (.i_data(rotword_1[23:16]), .o_data(subword_1[23:16]));
sbox uu_sbox1_2 (.i_data(rotword_1[15:8]),  .o_data(subword_1[15:8]));
sbox uu_sbox1_3 (.i_data(rotword_1[7:0]),   .o_data(subword_1[7:0]));

sbox uu_sbox2_0 (.i_data(rotword_2[31:24]), .o_data(subword_2[31:24]));
sbox uu_sbox2_1 (.i_data(rotword_2[23:16]), .o_data(subword_2[23:16]));
sbox uu_sbox2_2 (.i_data(rotword_2[15:8]),  .o_data(subword_2[15:8]));
sbox uu_sbox2_3 (.i_data(rotword_2[7:0]),   .o_data(subword_2[7:0]));

sbox uu_sbox3_0 (.i_data(rotword_3[31:24]), .o_data(subword_3[31:24]));
sbox uu_sbox3_1 (.i_data(rotword_3[23:16]), .o_data(subword_3[23:16]));
sbox uu_sbox3_2 (.i_data(rotword_3[15:8]),  .o_data(subword_3[15:8]));
sbox uu_sbox3_3 (.i_data(rotword_3[7:0]),   .o_data(subword_3[7:0]));

sbox uu_sbox4_0 (.i_data(rotword_4[31:24]), .o_data(subword_4[31:24]));
sbox uu_sbox4_1 (.i_data(rotword_4[23:16]), .o_data(subword_4[23:16]));
sbox uu_sbox4_2 (.i_data(rotword_4[15:8]),  .o_data(subword_4[15:8]));
sbox uu_sbox4_3 (.i_data(rotword_4[7:0]),   .o_data(subword_4[7:0]));

sbox uu_sbox5_0 (.i_data(rotword_5[31:24]), .o_data(subword_5[31:24]));
sbox uu_sbox5_1 (.i_data(rotword_5[23:16]), .o_data(subword_5[23:16]));
sbox uu_sbox5_2 (.i_data(rotword_5[15:8]),  .o_data(subword_5[15:8]));
sbox uu_sbox5_3 (.i_data(rotword_5[7:0]),   .o_data(subword_5[7:0]));

sbox uu_sbox6_0 (.i_data(rotword_6[31:24]), .o_data(subword_6[31:24]));
sbox uu_sbox6_1 (.i_data(rotword_6[23:16]), .o_data(subword_6[23:16]));
sbox uu_sbox6_2 (.i_data(rotword_6[15:8]),  .o_data(subword_6[15:8]));
sbox uu_sbox6_3 (.i_data(rotword_6[7:0]),   .o_data(subword_6[7:0]));

sbox uu_sbox7_0 (.i_data(rotword_7[31:24]), .o_data(subword_7[31:24]));
sbox uu_sbox7_1 (.i_data(rotword_7[23:16]), .o_data(subword_7[23:16]));
sbox uu_sbox7_2 (.i_data(rotword_7[15:8]),  .o_data(subword_7[15:8]));
sbox uu_sbox7_3 (.i_data(rotword_7[7:0]),   .o_data(subword_7[7:0]));

sbox uu_sbox8_0 (.i_data(rotword_8[31:24]), .o_data(subword_8[31:24]));
sbox uu_sbox8_1 (.i_data(rotword_8[23:16]), .o_data(subword_8[23:16]));
sbox uu_sbox8_2 (.i_data(rotword_8[15:8]),  .o_data(subword_8[15:8]));
sbox uu_sbox8_3 (.i_data(rotword_8[7:0]),   .o_data(subword_8[7:0]));

sbox uu_sbox9_0 (.i_data(rotword_9[31:24]), .o_data(subword_9[31:24]));
sbox uu_sbox9_1 (.i_data(rotword_9[23:16]), .o_data(subword_9[23:16]));
sbox uu_sbox9_2 (.i_data(rotword_9[15:8]),  .o_data(subword_9[15:8]));
sbox uu_sbox9_3 (.i_data(rotword_9[7:0]),   .o_data(subword_9[7:0]));

assign rcon_xor_0 = {subword_0[31:24] ^ 8'h01, subword_0[23:0]};
assign rcon_xor_1 = {subword_1[31:24] ^ 8'h02, subword_1[23:0]};
assign rcon_xor_2 = {subword_2[31:24] ^ 8'h04, subword_2[23:0]};
assign rcon_xor_3 = {subword_3[31:24] ^ 8'h08, subword_3[23:0]};
assign rcon_xor_4 = {subword_4[31:24] ^ 8'h10, subword_4[23:0]};
assign rcon_xor_5 = {subword_5[31:24] ^ 8'h20, subword_5[23:0]};
assign rcon_xor_6 = {subword_6[31:24] ^ 8'h40, subword_6[23:0]};
assign rcon_xor_7 = {subword_7[31:24] ^ 8'h80, subword_7[23:0]};
assign rcon_xor_8 = {subword_8[31:24] ^ 8'h1b, subword_8[23:0]};
assign rcon_xor_9 = {subword_9[31:24] ^ 8'h36, subword_9[23:0]};

assign nk0_0 = expanded_key_ff[1407:1376] ^ rcon_xor_0;
assign nk0_1 = expanded_key_ff[1375:1344] ^ nk0_0;
assign nk0_2 = expanded_key_ff[1343:1312] ^ nk0_1;
assign nk0_3 = expanded_key_ff[1311:1280] ^ nk0_2;
assign nrk0  = {nk0_0, nk0_1, nk0_2, nk0_3};

assign nk1_0 = expanded_key_ff[1279:1248] ^ rcon_xor_1;
assign nk1_1 = expanded_key_ff[1247:1216] ^ nk1_0;
assign nk1_2 = expanded_key_ff[1215:1184] ^ nk1_1;
assign nk1_3 = expanded_key_ff[1183:1152] ^ nk1_2;
assign nrk1  = {nk1_0, nk1_1, nk1_2, nk1_3};

assign nk2_0 = expanded_key_ff[1151:1120] ^ rcon_xor_2;
assign nk2_1 = expanded_key_ff[1119:1088] ^ nk2_0;
assign nk2_2 = expanded_key_ff[1087:1056] ^ nk2_1;
assign nk2_3 = expanded_key_ff[1055:1024] ^ nk2_2;
assign nrk2  = {nk2_0, nk2_1, nk2_2, nk2_3};

assign nk3_0 = expanded_key_ff[1023:992] ^ rcon_xor_3;
assign nk3_1 = expanded_key_ff[991:960] ^ nk3_0;
assign nk3_2 = expanded_key_ff[959:928] ^ nk3_1;
assign nk3_3 = expanded_key_ff[927:896] ^ nk3_2;
assign nrk3  = {nk3_0, nk3_1, nk3_2, nk3_3};

assign nk4_0 = expanded_key_ff[895:864] ^ rcon_xor_4;
assign nk4_1 = expanded_key_ff[863:832] ^ nk4_0;
assign nk4_2 = expanded_key_ff[831:800] ^ nk4_1;
assign nk4_3 = expanded_key_ff[799:768] ^ nk4_2;
assign nrk4  = {nk4_0, nk4_1, nk4_2, nk4_3};

assign nk5_0 = expanded_key_ff[767:736] ^ rcon_xor_5;
assign nk5_1 = expanded_key_ff[735:704] ^ nk5_0;
assign nk5_2 = expanded_key_ff[703:672] ^ nk5_1;
assign nk5_3 = expanded_key_ff[671:640] ^ nk5_2;
assign nrk5  = {nk5_0, nk5_1, nk5_2, nk5_3};

assign nk6_0 = expanded_key_ff[639:608] ^ rcon_xor_6;
assign nk6_1 = expanded_key_ff[607:576] ^ nk6_0;
assign nk6_2 = expanded_key_ff[575:544] ^ nk6_1;
assign nk6_3 = expanded_key_ff[543:512] ^ nk6_2;
assign nrk6  = {nk6_0, nk6_1, nk6_2, nk6_3};

assign nk7_0 = expanded_key_ff[511:480] ^ rcon_xor_7;
assign nk7_1 = expanded_key_ff[479:448] ^ nk7_0;
assign nk7_2 = expanded_key_ff[447:416] ^ nk7_1;
assign nk7_3 = expanded_key_ff[415:384] ^ nk7_2;
assign nrk7  = {nk7_0, nk7_1, nk7_2, nk7_3};

assign nk8_0 = expanded_key_ff[383:352] ^ rcon_xor_8;
assign nk8_1 = expanded_key_ff[351:320] ^ nk8_0;
assign nk8_2 = expanded_key_ff[319:288] ^ nk8_1;
assign nk8_3 = expanded_key_ff[287:256] ^ nk8_2;
assign nrk8  = {nk8_0, nk8_1, nk8_2, nk8_3};

assign nk9_0 = expanded_key_ff[255:224] ^ rcon_xor_9;
assign nk9_1 = expanded_key_ff[223:192] ^ nk9_0;
assign nk9_2 = expanded_key_ff[191:160] ^ nk9_1;
assign nk9_3 = expanded_key_ff[159:128] ^ nk9_2;
assign nrk9  = {nk9_0, nk9_1, nk9_2, nk9_3};

endmodule : aes128_key_expansion
