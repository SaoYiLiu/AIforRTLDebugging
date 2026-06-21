module fsm_seq_detector
(
    input  bit     clk_in,       // Free Running Clock
    input  logic   rst_in,       // Active HIGH reset
    input  logic   seq_in,       // Continuous 1-bit Sequence Input
    output logic   seq_detected  // '0': Not Detected. '1': Detected. Will be HIGH for 1 Clock cycle Only
);

typedef enum logic [2:0] {S0, S1, S2, S3, S4, S5, S6, S7} state_t;
state_t cur_state, next_state;

logic seq_detected_w;

always @ (posedge clk_in or posedge rst_in)
begin
    if (rst_in)
        cur_state <= S0;
    else
        cur_state <= next_state;
end

always_comb begin
    if (rst_in) begin
        seq_detected_w = 1'b0;
        next_state = S0;
    end
    else begin
        case (cur_state)
            S0: begin
                if (seq_in) begin
                    next_state = S1;
                    seq_detected_w = 1'b0;
                end
                else begin
                    seq_detected_w = 1'b0;
                    next_state = S0;
                end	
            end
            S1: begin
                if (seq_in) begin
                    next_state = S1;
                    seq_detected_w = 1'b0;
                end
                else begin
                    next_state = S2;
                    seq_detected_w = 1'b0;
                end
            end
            S2: begin
                if (seq_in) begin
                    next_state = S3;
                    seq_detected_w = 1'b0;
                end
                else begin
                    next_state = S0;
                    seq_detected_w = 1'b0;
                end
            end
            S3: begin
                if (seq_in) begin
                    next_state = S4;
                    seq_detected_w = 1'b0;
                end
                else begin
                    next_state = S2;
                    seq_detected_w = 1'b0;
                end
            end
            S4: begin
                if (seq_in) begin
                    next_state = S1;
                    seq_detected_w = 1'b0;
                end
                else begin
                    next_state = S5;
                    seq_detected_w = 1'b0;
                end
            end
            S5: begin
                if (seq_in) begin
                    next_state = S3;
                    seq_detected_w = 1'b0;
                end
                else begin
                    next_state = S6;
                    seq_detected_w = 1'b0;
                end
            end
            S6: begin
                if (seq_in) begin
                    next_state = S1;
                    seq_detected_w = 1'b0;
                end
                else begin
                    next_state = S7;
                    seq_detected_w = 1'b0;
                end
            end
            S7: begin
                if (seq_in) begin
                    next_state = S1;
                    seq_detected_w = 1'b1;
                end
                else begin
                    next_state = S0;
                    seq_detected_w = 1'b0;
                end
            end
            default: begin
                next_state = S0;
                seq_detected_w = 1'b0;
            end
        endcase
    end
end

always @ (posedge clk_in or posedge rst_in)
begin
    if (rst_in)
        seq_detected <= 1'b0;
    else
        seq_detected <= seq_detected_w;
end

endmodule