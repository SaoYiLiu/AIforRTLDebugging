module aes128_decrypt #(
    parameter NBW_KEY  = 'd128,
    parameter NBW_DATA = 'd128
) (
    input  logic                clk,
    input  logic                rst_async_n,
    input  logic                i_update_key,
    input  logic [NBW_KEY-1:0]  i_key,
    input  logic                i_start,
    input  logic [NBW_DATA-1:0] i_data,
    output logic                o_done,
    output logic [NBW_DATA-1:0] o_data
);

localparam NBW_BYTE   = 'd8;
localparam NBW_EX_KEY = 'd1408;

logic [NBW_BYTE-1:0]   current_data_nx[4][4];
logic [NBW_BYTE-1:0]   current_data_ff[4][4];
logic [NBW_BYTE-1:0]   AddRoundKey[4][4];
logic [NBW_BYTE-1:0]   SubBytes[4][4];
logic [NBW_BYTE-1:0]   ShiftRows[4][4];
logic [NBW_BYTE-1:0]   xtimes02[4][4];
logic [NBW_BYTE-1:0]   xtimes04[4][4];
logic [NBW_BYTE-1:0]   xtimes08[4][4];
logic [NBW_BYTE-1:0]   xtimes09[4][4];
logic [NBW_BYTE-1:0]   xtimes0b[4][4];
logic [NBW_BYTE-1:0]   xtimes0d[4][4];
logic [NBW_BYTE-1:0]   xtimes0e[4][4];
logic [NBW_BYTE-1:0]   MixColumns[4][4];
logic [NBW_BYTE-1:0]   RoundOut[4][4];
logic                  key_done;
logic                  update_key_ff;
logic [3:0]            round_ff;
logic [NBW_EX_KEY-1:0] expanded_key;

assign o_done = (round_ff == 4'd0);

generate
    for(genvar i = 0; i < 4; i++) begin : out_row
        for(genvar j = 0; j < 4; j++) begin : out_col
            assign o_data[NBW_DATA-(4*j+i)*NBW_BYTE-1-:NBW_BYTE] = current_data_ff[i][j];
        end
    end
endgenerate

always_ff @(posedge clk or negedge rst_async_n) begin : inv_cypher_regs
    if(!rst_async_n) begin
        round_ff      <= 4'd0;
        update_key_ff <= 1'b0;
        for(int i = 0; i < 4; i++) begin
            for(int j = 0; j < 4; j++) begin
                current_data_ff[i][j] <= 8'd0;
            end
        end
    end else begin
        if(i_start & o_done) begin
            round_ff      <= 4'd1;
            update_key_ff <= i_update_key;
        end else if(round_ff == 4'd1) begin
            if(!update_key_ff || key_done) begin
                round_ff <= 4'd2;
            end
        end else if(round_ff > 4'd1 && round_ff < 4'd11) begin
            round_ff <= round_ff + 4'd1;
        end else if(round_ff == 4'd11) begin
            round_ff <= 4'd0;
        end

        for(int i = 0; i < 4; i++) begin
            for(int j = 0; j < 4; j++) begin
                current_data_ff[i][j] <= current_data_nx[i][j];
            end
        end
    end
end

always_comb begin : next_data
    for(int i = 0; i < 4; i++) begin
        for(int j = 0; j < 4; j++) begin
            if(i_start & o_done) begin
                current_data_nx[i][j] = i_data[NBW_DATA-(4*j+i)*NBW_BYTE-1-:NBW_BYTE];
            end else if(round_ff == 4'd1) begin
                if(!update_key_ff || key_done) begin
                    current_data_nx[i][j] = RoundOut[i][j];
                end else begin
                    current_data_nx[i][j] = current_data_ff[i][j];
                end
            end else if(round_ff != 4'd0) begin
                current_data_nx[i][j] = RoundOut[i][j];
            end else begin
                current_data_nx[i][j] = current_data_ff[i][j];
            end
        end
    end
end

generate
    for(genvar i = 0; i < 4; i++) begin : row
        for(genvar j = 0; j < 4; j++) begin : col
            inv_sbox uu_inv_sbox0 (
                .i_data(ShiftRows[i][j]),
                .o_data(SubBytes[i][j])
            );
        end
    end
endgenerate

always_comb begin : decypher_logic
    // InvShiftRows first: row r cyclically shifted right by r positions
    ShiftRows[0][0] = current_data_ff[0][0];
    ShiftRows[0][1] = current_data_ff[0][1];
    ShiftRows[0][2] = current_data_ff[0][2];
    ShiftRows[0][3] = current_data_ff[0][3];

    ShiftRows[1][0] = current_data_ff[1][3];
    ShiftRows[1][1] = current_data_ff[1][0];
    ShiftRows[1][2] = current_data_ff[1][1];
    ShiftRows[1][3] = current_data_ff[1][2];

    ShiftRows[2][0] = current_data_ff[2][2];
    ShiftRows[2][1] = current_data_ff[2][3];
    ShiftRows[2][2] = current_data_ff[2][0];
    ShiftRows[2][3] = current_data_ff[2][1];

    ShiftRows[3][0] = current_data_ff[3][1];
    ShiftRows[3][1] = current_data_ff[3][2];
    ShiftRows[3][2] = current_data_ff[3][3];
    ShiftRows[3][3] = current_data_ff[3][0];

    for(int i = 0; i < 4; i++) begin
        for(int j = 0; j < 4; j++) begin
            if(round_ff > 4'd0) begin
                AddRoundKey[i][j] = SubBytes[i][j] ^ expanded_key[NBW_EX_KEY-(11-round_ff)*NBW_KEY-(4*j+i)*NBW_BYTE-1-:NBW_BYTE];
            end else begin
                AddRoundKey[i][j] = 8'd0;
            end
        end
    end

    for(int i = 0; i < 4; i++) begin
        for(int j = 0; j < 4; j++) begin
            if(AddRoundKey[i][j][NBW_BYTE-1]) begin
                xtimes02[i][j] = {AddRoundKey[i][j][NBW_BYTE-2:0], 1'b0} ^ 8'h1B;
                xtimes04[i][j] = {xtimes02[i][j][NBW_BYTE-2:0], 1'b0} ^ 8'h1B;
                xtimes08[i][j] = {xtimes04[i][j][NBW_BYTE-2:0], 1'b0} ^ 8'h1B;
            end else begin
                xtimes02[i][j] = {AddRoundKey[i][j][NBW_BYTE-2:0], 1'b0};
                xtimes04[i][j] = {xtimes02[i][j][NBW_BYTE-2:0], 1'b0};
                xtimes08[i][j] = {xtimes04[i][j][NBW_BYTE-2:0], 1'b0};
            end

            xtimes0e[i][j] = xtimes08[i][j] ^ xtimes04[i][j] ^ xtimes02[i][j];
            xtimes0b[i][j] = xtimes08[i][j] ^ xtimes02[i][j] ^ AddRoundKey[i][j];
            xtimes0d[i][j] = xtimes08[i][j] ^ xtimes04[i][j] ^ AddRoundKey[i][j];
            xtimes09[i][j] = xtimes08[i][j] ^ AddRoundKey[i][j];
        end

        MixColumns[0][i] = xtimes0e[0][i] ^ xtimes0b[1][i] ^ xtimes0d[2][i] ^ xtimes09[3][i];
        MixColumns[1][i] = xtimes09[0][i] ^ xtimes0e[1][i] ^ xtimes0b[2][i] ^ xtimes0d[3][i];
        MixColumns[2][i] = xtimes0d[0][i] ^ xtimes09[1][i] ^ xtimes0e[2][i] ^ xtimes0b[3][i];
        MixColumns[3][i] = xtimes0b[0][i] ^ xtimes0d[1][i] ^ xtimes09[2][i] ^ xtimes0e[3][i];
    end

    for(int i = 0; i < 4; i++) begin
        for(int j = 0; j < 4; j++) begin
            if(round_ff == 4'd1) begin
                RoundOut[i][j] = current_data_ff[i][j] ^ expanded_key[NBW_EX_KEY-(11-round_ff)*NBW_KEY-(4*j+i)*NBW_BYTE-1-:NBW_BYTE];
            end else if(round_ff >= 4'd2 && round_ff <= 4'd10) begin
                RoundOut[i][j] = MixColumns[i][j];
            end else if(round_ff == 4'd11) begin
                RoundOut[i][j] = AddRoundKey[i][j];
            end else begin
                RoundOut[i][j] = current_data_ff[i][j];
            end
        end
    end
end

aes128_key_expansion uu_aes128_key_expansion (
    .clk           (clk                            ),
    .rst_async_n   (rst_async_n                    ),
    .i_start       (i_start & i_update_key & o_done),
    .i_key         (i_key                          ),
    .o_done        (key_done                       ),
    .o_expanded_key(expanded_key                   )
);

endmodule : aes128_decrypt
