// Manchester encoder module
module manchester_encoder #(
    parameter N = 8  // Default width of input data
) (
    input  logic clk_in,          // Clock input
    input  logic rst_in,          // Active high reset input
    input  logic enc_valid_in,        // Input valid signal
    input  logic [N-1:0] enc_data_in, // N-bit input data
    output logic enc_valid_out,       // Output valid signal
    output logic [2*N-1:0] enc_data_out // 2N-bit output encoded data
);

    logic [2*N-1:0] next_enc_data;

    always_comb begin
        for (int i = 0; i < N; i++) begin
            if (enc_data_in[i] == 1'b1) begin
                next_enc_data[2*i]     = 1'b1;
                next_enc_data[2*i + 1] = 1'b0;
            end else begin
                next_enc_data[2*i]     = 1'b0;
                next_enc_data[2*i + 1] = 1'b1;
            end
        end
    end

    always_ff @(posedge clk_in) begin
        if (rst_in) begin
            enc_valid_out <= 1'b0;
            enc_data_out  <= '0;
        end else if (enc_valid_in) begin
            enc_valid_out <= 1'b1;
            enc_data_out  <= next_enc_data;
        end else begin
            enc_valid_out <= 1'b0;
            enc_data_out  <= '0;
        end
    end

endmodule
