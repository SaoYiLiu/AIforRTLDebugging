module pipelined_modified_booth_multiplier (
    input clk,
    input rst,
    input start,
    input signed [15:0] X,
    input signed [15:0] Y,
    output reg signed  [31:0] result,
    output reg done
);

    reg signed [31:0] partial_products [0:7];
    reg signed [15:0] X_reg, Y_reg;
    reg [4:0] valid_pipe;

    integer i;

    // Registers for pipelining the addition stages
    reg signed [31:0] s1, s2, s3, s4;
    reg signed [31:0] temp_products1, temp_products2;

    always @(posedge clk or posedge rst) 
    begin
        if (rst) 
        begin
            X_reg <= 16'd0;
            Y_reg <= 16'd0;
            valid_pipe <= 5'd0;
            done <= 1'b0;
            for (i = 0; i < 8; i = i + 1) 
            begin
                partial_products[i] <= 32'd0;
            end
            s1 <= 0; s2 <= 0; s3 <= 0; s4 <= 0;
            temp_products1 <= 0; temp_products2 <= 0;
            result <= 32'd0;
        end 
        else 
        begin
            // Stage 1: Input registering
            if (start) begin
                X_reg <= X;
                Y_reg <= Y;
            end

            // Stage 2: Booth encoding and partial product generation
            if (valid_pipe[4]) begin
                for (i = 0; i < 8; i = i + 1) begin
                    case ({Y_reg[2*i+1], Y_reg[2*i], (i == 0) ? 1'b0 : Y_reg[2*i-1]})
                        3'b000, 3'b111: partial_products[i] <= 32'd0;
                        3'b001, 3'b010: partial_products[i] <= {{16{X_reg[15]}}, X_reg} << (2*i);
                        3'b011: partial_products[i] <= {{16{X_reg[15]}}, X_reg} << (2*i + 1);
                        3'b100: partial_products[i] <= -({{16{X_reg[15]}}, X_reg} << (2*i + 1));
                        3'b101, 3'b110: partial_products[i] <= -({{16{X_reg[15]}}, X_reg} << (2*i));
                        default: partial_products[i] <= 32'd0;
                    endcase
                end
            end

            // Stage 3: Partial product reduction
            if (valid_pipe[3]) begin 
                s1 <= partial_products[0] + partial_products[1] + partial_products[2];
                s2 <= partial_products[3] + partial_products[4] + partial_products[5];
                temp_products1 <= partial_products[6];
                temp_products2 <= partial_products[7];
            end 

            // Stage 4: Final summation
            if (valid_pipe[2]) begin 
                s3 <= s1 + s2;
                s4 <= temp_products1 + temp_products2;
            end

            // Stage 5: Output result
            if (valid_pipe[1]) begin
                result <= s3 + s4;
                done <= 1'b1;
            end 
            else begin
                done <= 1'b0; 
            end 

            // Shift-register valid propagation through the pipeline
            valid_pipe <= valid_pipe >> 1;
            if (start)
                valid_pipe[4] <= 1'b1;
        end
    end
        
endmodule
