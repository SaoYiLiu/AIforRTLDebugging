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

logic [NBW_BYTE-1:0] Rcon   [STEPS];
logic [NBW_OUT-1:0]  expanded_key_nx;
logic [NBW_OUT-1:0]  expanded_key_ff;
logic [NBW_KEY-1:0]  next_rkey;
logic [3:0]          gen_idx;
logic [STEPS:0]      key_exp_steps_ff;

logic [NBW_WORD-1:0] RotWord;
logic [NBW_WORD-1:0] SubWord;
logic [NBW_WORD-1:0] RconXor;

assign o_expanded_key = expanded_key_ff;
assign o_done         = key_exp_steps_ff[STEPS];

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

assign Rcon[0] = 8'h01;
assign Rcon[1] = 8'h02;
assign Rcon[2] = 8'h04;
assign Rcon[3] = 8'h08;
assign Rcon[4] = 8'h10;
assign Rcon[5] = 8'h20;
assign Rcon[6] = 8'h40;
assign Rcon[7] = 8'h80;
assign Rcon[8] = 8'h1b;
assign Rcon[9] = 8'h36;

always_comb begin : gen_idx_select
    if      (key_exp_steps_ff[9]) gen_idx = 4'd9;
    else if (key_exp_steps_ff[8]) gen_idx = 4'd8;
    else if (key_exp_steps_ff[7]) gen_idx = 4'd7;
    else if (key_exp_steps_ff[6]) gen_idx = 4'd6;
    else if (key_exp_steps_ff[5]) gen_idx = 4'd5;
    else if (key_exp_steps_ff[4]) gen_idx = 4'd4;
    else if (key_exp_steps_ff[3]) gen_idx = 4'd3;
    else if (key_exp_steps_ff[2]) gen_idx = 4'd2;
    else if (key_exp_steps_ff[1]) gen_idx = 4'd1;
    else if (key_exp_steps_ff[0]) gen_idx = 4'd0;
    else                          gen_idx = 4'd0;
end

sbox uu_sbox0 (
    .i_data(RotWord[NBW_WORD-1-:NBW_BYTE]),
    .o_data(SubWord[NBW_WORD-1-:NBW_BYTE])
);

sbox uu_sbox1 (
    .i_data(RotWord[NBW_WORD-NBW_BYTE-1-:NBW_BYTE]),
    .o_data(SubWord[NBW_WORD-NBW_BYTE-1-:NBW_BYTE])
);

sbox uu_sbox2 (
    .i_data(RotWord[NBW_WORD-2*NBW_BYTE-1-:NBW_BYTE]),
    .o_data(SubWord[NBW_WORD-2*NBW_BYTE-1-:NBW_BYTE])
);

sbox uu_sbox3 (
    .i_data(RotWord[NBW_WORD-3*NBW_BYTE-1-:NBW_BYTE]),
    .o_data(SubWord[NBW_WORD-3*NBW_BYTE-1-:NBW_BYTE])
);

always_comb begin : expand_next_rkey
    RotWord   = '0;
    RconXor   = '0;
    next_rkey = '0;

    unique case (gen_idx)
        4'd0: begin
            RotWord = {expanded_key_ff[1303:1280], expanded_key_ff[1311:1304]};
            RconXor = {SubWord[31:24] ^ Rcon[0], SubWord[23:0]};
            next_rkey[127:96] = expanded_key_ff[1407:1376] ^ RconXor;
            next_rkey[95:64]  = expanded_key_ff[1375:1344] ^ next_rkey[127:96];
            next_rkey[63:32]  = expanded_key_ff[1343:1312] ^ next_rkey[95:64];
            next_rkey[31:0]   = expanded_key_ff[1311:1280] ^ next_rkey[63:32];
        end
        4'd1: begin
            RotWord = {expanded_key_ff[1175:1152], expanded_key_ff[1183:1176]};
            RconXor = {SubWord[31:24] ^ Rcon[1], SubWord[23:0]};
            next_rkey[127:96] = expanded_key_ff[1279:1248] ^ RconXor;
            next_rkey[95:64]  = expanded_key_ff[1247:1216] ^ next_rkey[127:96];
            next_rkey[63:32]  = expanded_key_ff[1215:1184] ^ next_rkey[95:64];
            next_rkey[31:0]   = expanded_key_ff[1183:1152] ^ next_rkey[63:32];
        end
        4'd2: begin
            RotWord = {expanded_key_ff[1047:1024], expanded_key_ff[1055:1048]};
            RconXor = {SubWord[31:24] ^ Rcon[2], SubWord[23:0]};
            next_rkey[127:96] = expanded_key_ff[1151:1120] ^ RconXor;
            next_rkey[95:64]  = expanded_key_ff[1119:1088] ^ next_rkey[127:96];
            next_rkey[63:32]  = expanded_key_ff[1087:1056] ^ next_rkey[95:64];
            next_rkey[31:0]   = expanded_key_ff[1055:1024] ^ next_rkey[63:32];
        end
        4'd3: begin
            RotWord = {expanded_key_ff[919:896], expanded_key_ff[927:920]};
            RconXor = {SubWord[31:24] ^ Rcon[3], SubWord[23:0]};
            next_rkey[127:96] = expanded_key_ff[1023:992] ^ RconXor;
            next_rkey[95:64]  = expanded_key_ff[991:960] ^ next_rkey[127:96];
            next_rkey[63:32]  = expanded_key_ff[959:928] ^ next_rkey[95:64];
            next_rkey[31:0]   = expanded_key_ff[927:896] ^ next_rkey[63:32];
        end
        4'd4: begin
            RotWord = {expanded_key_ff[791:768], expanded_key_ff[799:792]};
            RconXor = {SubWord[31:24] ^ Rcon[4], SubWord[23:0]};
            next_rkey[127:96] = expanded_key_ff[895:864] ^ RconXor;
            next_rkey[95:64]  = expanded_key_ff[863:832] ^ next_rkey[127:96];
            next_rkey[63:32]  = expanded_key_ff[831:800] ^ next_rkey[95:64];
            next_rkey[31:0]   = expanded_key_ff[799:768] ^ next_rkey[63:32];
        end
        4'd5: begin
            RotWord = {expanded_key_ff[663:640], expanded_key_ff[671:664]};
            RconXor = {SubWord[31:24] ^ Rcon[5], SubWord[23:0]};
            next_rkey[127:96] = expanded_key_ff[767:736] ^ RconXor;
            next_rkey[95:64]  = expanded_key_ff[735:704] ^ next_rkey[127:96];
            next_rkey[63:32]  = expanded_key_ff[703:672] ^ next_rkey[95:64];
            next_rkey[31:0]   = expanded_key_ff[671:640] ^ next_rkey[63:32];
        end
        4'd6: begin
            RotWord = {expanded_key_ff[535:512], expanded_key_ff[543:536]};
            RconXor = {SubWord[31:24] ^ Rcon[6], SubWord[23:0]};
            next_rkey[127:96] = expanded_key_ff[639:608] ^ RconXor;
            next_rkey[95:64]  = expanded_key_ff[607:576] ^ next_rkey[127:96];
            next_rkey[63:32]  = expanded_key_ff[575:544] ^ next_rkey[95:64];
            next_rkey[31:0]   = expanded_key_ff[543:512] ^ next_rkey[63:32];
        end
        4'd7: begin
            RotWord = {expanded_key_ff[407:384], expanded_key_ff[415:408]};
            RconXor = {SubWord[31:24] ^ Rcon[7], SubWord[23:0]};
            next_rkey[127:96] = expanded_key_ff[511:480] ^ RconXor;
            next_rkey[95:64]  = expanded_key_ff[479:448] ^ next_rkey[127:96];
            next_rkey[63:32]  = expanded_key_ff[447:416] ^ next_rkey[95:64];
            next_rkey[31:0]   = expanded_key_ff[415:384] ^ next_rkey[63:32];
        end
        4'd8: begin
            RotWord = {expanded_key_ff[279:256], expanded_key_ff[287:280]};
            RconXor = {SubWord[31:24] ^ Rcon[8], SubWord[23:0]};
            next_rkey[127:96] = expanded_key_ff[383:352] ^ RconXor;
            next_rkey[95:64]  = expanded_key_ff[351:320] ^ next_rkey[127:96];
            next_rkey[63:32]  = expanded_key_ff[319:288] ^ next_rkey[95:64];
            next_rkey[31:0]   = expanded_key_ff[287:256] ^ next_rkey[63:32];
        end
        4'd9: begin
            RotWord = {expanded_key_ff[151:128], expanded_key_ff[159:152]};
            RconXor = {SubWord[31:24] ^ Rcon[9], SubWord[23:0]};
            next_rkey[127:96] = expanded_key_ff[255:224] ^ RconXor;
            next_rkey[95:64]  = expanded_key_ff[223:192] ^ next_rkey[127:96];
            next_rkey[63:32]  = expanded_key_ff[191:160] ^ next_rkey[95:64];
            next_rkey[31:0]   = expanded_key_ff[159:128] ^ next_rkey[63:32];
        end
        default: ;
    endcase
end

always_comb begin : expanded_key_update
    expanded_key_nx = expanded_key_ff;

    if(i_start) begin
        expanded_key_nx = {i_key, {(NBW_OUT-NBW_KEY){1'b0}}};
    end else if(|key_exp_steps_ff[STEPS-1:0] && !key_exp_steps_ff[STEPS]) begin
        unique case (gen_idx)
            4'd0: expanded_key_nx[1152+:NBW_KEY] = next_rkey;
            4'd1: expanded_key_nx[1024+:NBW_KEY] = next_rkey;
            4'd2: expanded_key_nx[896+:NBW_KEY]  = next_rkey;
            4'd3: expanded_key_nx[768+:NBW_KEY]  = next_rkey;
            4'd4: expanded_key_nx[640+:NBW_KEY]  = next_rkey;
            4'd5: expanded_key_nx[512+:NBW_KEY]  = next_rkey;
            4'd6: expanded_key_nx[384+:NBW_KEY]  = next_rkey;
            4'd7: expanded_key_nx[256+:NBW_KEY]  = next_rkey;
            4'd8: expanded_key_nx[128+:NBW_KEY]  = next_rkey;
            4'd9: expanded_key_nx[0+:NBW_KEY]    = next_rkey;
            default: ;
        endcase
    end
end

endmodule : aes128_key_expansion
