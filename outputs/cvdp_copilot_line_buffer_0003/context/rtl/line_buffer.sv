module line_buffer #(
    parameter NBW_DATA  = 'd8,  // Bit width of grayscale input/output data
    parameter NS_ROW    = 'd10, // Number of rows
    parameter NS_COLUMN = 'd8,  // Number of columns
    parameter NBW_ROW   = 'd4,  // log2(NS_ROW). Bit width of i_image_row_start
    parameter NBW_COL   = 'd3,  // log2(NS_COLUMN). Bit width of i_image_col_start
    parameter NBW_MODE  = 'd3,  // Bit width of mode input
    parameter NS_R_OUT  = 'd4,  // Number of rows of the output window
    parameter NS_C_OUT  = 'd3,  // Number of columns of the output window
    parameter CONSTANT  = 'd255 // Constant value to use in PAD_CONSTANT mode
) (
    input  logic                                  clk,
    input  logic                                  rst_async_n,
    input  logic [NBW_MODE-1:0]                   i_mode,
    input  logic                                  i_valid,
    input  logic                                  i_update_window,
    input  logic [NBW_DATA*NS_COLUMN-1:0]         i_row_image,
    input  logic [NBW_ROW-1:0]                    i_image_row_start,
    input  logic [NBW_COL-1:0]                    i_image_col_start,
    output logic [NBW_DATA*NS_R_OUT*NS_C_OUT-1:0] o_image_window
);

// ----------------------------------------
// - Wires/Registers creation
// ----------------------------------------
logic [NBW_DATA-1:0] image_buffer_ff [NS_ROW][NS_COLUMN];
logic [NBW_DATA-1:0] row_image [NS_COLUMN];
logic [NBW_DATA-1:0] window [NS_R_OUT][NS_C_OUT];
logic [NBW_DATA*NS_R_OUT*NS_C_OUT-1:0] image_window_ff;

// ----------------------------------------
// - Output generation
// ----------------------------------------
always_comb begin : window_assignment
    case(i_mode)
        3'd0: begin // NO_BOUND_PROCESS
            for (int row = 0; row < NS_R_OUT; row++) begin
                for (int col = 0; col < NS_C_OUT; col++) begin
                    if(i_image_row_start + col >= NS_ROW) begin
                        window[row][col] = 0;
                    end else if (i_image_col_start + row >= NS_COLUMN) begin
                        window[row][col] = 0;
                    end else begin
                        window[row][col] = image_buffer_ff[i_image_row_start + col][i_image_col_start + row];
                    end
                end
            end
        end
        3'd1: begin // PAD_CONSTANT
            for (int row = 0; row < NS_R_OUT; row++) begin
                for (int col = 0; col < NS_C_OUT; col++) begin
                    if(i_image_row_start + col >= NS_ROW) begin
                        window[row][col] = CONSTANT;
                    end else if (i_image_col_start + row >= NS_COLUMN) begin
                        window[row][col] = CONSTANT;
                    end else begin
                        window[row][col] = image_buffer_ff[i_image_row_start + col][i_image_col_start + row];
                    end
                end
            end
        end
        3'd2: begin // EXTEND_NEAR
            for (int row = 0; row < NS_R_OUT; row++) begin
                for (int col = 0; col < NS_C_OUT; col++) begin
                    if(i_image_row_start + col >= NS_ROW) begin
                        window[row][col] = image_buffer_ff[NS_ROW-1][i_image_col_start + row];
                    end else if (i_image_col_start + row >= NS_COLUMN) begin
                        window[row][col] = image_buffer_ff[i_image_row_start + col][NS_COLUMN-1];
                    end else begin
                        window[row][col] = image_buffer_ff[i_image_row_start + col][i_image_col_start + row];
                    end
                end
            end
        end
        3'd3: begin // MIRROR_BOUND
            for (int row = 0; row < NS_R_OUT; row++) begin
                for (int col = 0; col < NS_C_OUT; col++) begin
                    if(i_image_row_start + col >= NS_ROW) begin
                        window[row][col] = image_buffer_ff[2*NS_ROW-1-(i_image_row_start + col)][i_image_col_start + row];
                    end else if (i_image_col_start + row >= NS_COLUMN) begin
                        window[row][col] = image_buffer_ff[i_image_row_start + col][NS_COLUMN-1-(i_image_col_start + row)];
                    end else begin
                        window[row][col] = image_buffer_ff[i_image_row_start + col][i_image_col_start + row];
                    end
                end
            end
        end
        3'd4: begin // WRAP_AROUND
            for (int row = 0; row < NS_R_OUT; row++) begin
                for (int col = 0; col < NS_C_OUT; col++) begin
                    if(i_image_row_start + col >= NS_ROW) begin
                        window[row][col] = image_buffer_ff[(i_image_row_start + col)-NS_ROW][i_image_col_start + row];
                    end else if (i_image_col_start + row >= NS_COLUMN) begin
                        window[row][col] = image_buffer_ff[i_image_row_start + col][(i_image_col_start + row)-NS_COLUMN];
                    end else begin
                        window[row][col] = image_buffer_ff[i_image_row_start + col][i_image_col_start + row];
                    end
                end
            end
        end
        default: begin
            for (int row = 0; row < NS_R_OUT; row++) begin
                for (int col = 0; col < NS_C_OUT; col++) begin
                    window[row][col] = 0;
                end
            end
        end
    endcase
end

// ----------------------------------------
// - Input control
// ----------------------------------------
generate
    for (genvar col = 0; col < NS_COLUMN; col++) begin : unpack_row_image
        assign row_image[NS_COLUMN-col-1] = i_row_image[(col+1)*NBW_DATA-1-:NBW_DATA];
    end
endgenerate

always_ff @(posedge clk or negedge rst_async_n) begin : ctrl_regs
    if(~rst_async_n) begin
        image_window_ff <= 0;
        for (int row = 0; row < NS_ROW; row++) begin
            for (int col = 0; col < NS_COLUMN; col++) begin
                image_buffer_ff[row][col] <= 0;
            end
        end
    end else begin
        if(i_valid) begin
            for (int col = 0; col < NS_COLUMN; col++) begin
                image_buffer_ff[0][col] <= row_image[col];
            end

            for (int row = 1; row < NS_ROW; row++) begin
                for (int col = 0; col < NS_COLUMN; col++) begin
                    image_buffer_ff[row][col] <= image_buffer_ff[row-1][col];
                end
            end
        end

        if(i_update_window) begin
            image_window_ff <= o_image_window;
        end
    end
end

// ----------------------------------------
// - Output packing
// ----------------------------------------
generate
    for(genvar row = 0; row < NS_R_OUT; row++) begin : out_row
        for(genvar col = 0; col < NS_C_OUT; col++) begin : out_col
            always_comb begin
                if(i_update_window) begin
                    o_image_window[(row*NS_C_OUT+col+1)*NBW_DATA-1-:NBW_DATA] = window[row][col];
                end else begin
                    o_image_window[(row*NS_C_OUT+col+1)*NBW_DATA-1-:NBW_DATA] = image_window_ff[(row*NS_C_OUT+col+1)*NBW_DATA-1-:NBW_DATA];
                end
            end
        end
    end
endgenerate

endmodule : line_buffer