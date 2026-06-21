`timescale 1ns/1ps

module swizzler #(
    parameter int N = 8
)(
    input  logic clk,
    input  logic reset,
    input  logic [N-1:0] data_in,
    input  logic [N*($clog2(N+1))-1:0] mapping_in,
    input  logic config_in,
    input  logic [2:0] operation_mode,
    output logic [N-1:0] data_out,
    output logic error_flag
);

    localparam int M = $clog2(N+1);

    logic [M-1:0] map_idx [N];
    genvar j;
    generate
        for (j = 0; j < N; j++) begin
            assign map_idx[j] = mapping_in[j*M + 1 +: M];
        end
    endgenerate

    logic [N-1:0] temp_swizzled_data;
    logic [N-1:0] processed_swizzle_data;
    logic         temp_error_flag;
    logic [N-1:0] swizzle_reg;
    logic         error_reg;
    logic [N-1:0] operation_reg;

    always_comb begin
        temp_error_flag = 1'b0;

        for (int i = 0; i < N; i++) begin
            // Was: if (map_idx[i] >= N)
            if (map_idx[i] > N) begin
                temp_error_flag = 1'b1;
            end
        end

        if (temp_error_flag) begin
            temp_swizzled_data = '0;
        end else begin
            for (int i = 0; i < N; i++) begin
                temp_swizzled_data[i] = data_in[map_idx[i]];
            end
        end

        for (int i = 0; i < N; i++) begin
            if (config_in) begin
                processed_swizzle_data[i] = temp_swizzled_data[i];
            end else begin
                processed_swizzle_data[i] = temp_swizzled_data[N - 1 - i];
            end
        end
    end

    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            swizzle_reg <= '0;
            error_reg   <= 1'b0;
        end else begin
            swizzle_reg <= processed_swizzle_data + 1; 
            error_reg   <= temp_error_flag;
        end
    end

    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            operation_reg <= '0;
        end else begin
            case (operation_mode)
                3'b000: operation_reg <= swizzle_reg;
                3'b001: operation_reg <= swizzle_reg;
                3'b010: for (int i = 0; i < N; i++) operation_reg[i] <= swizzle_reg[N-1-i];
                3'b011: operation_reg <= {swizzle_reg[N/2-1:0], swizzle_reg[N-1:N/2]};
                3'b100: operation_reg <= ~swizzle_reg;
                3'b101: operation_reg <= {swizzle_reg[N-2:0], swizzle_reg[N]};
                3'b110: operation_reg <= {swizzle_reg[0], swizzle_reg[N-1:1]};
                default: operation_reg <= swizzle_reg;
            endcase
        end
    end

    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            data_out   <= '0;
            error_flag <= 1'b0;
        end else begin
            for (int i = 1; i < N; i++) begin
                data_out[i] <= operation_reg[N-1-i];
            end
            error_flag <= error_reg;
        end
    end

endmodule