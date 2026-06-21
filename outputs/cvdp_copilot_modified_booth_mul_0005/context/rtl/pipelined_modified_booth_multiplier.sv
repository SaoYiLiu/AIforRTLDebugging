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
    reg [4:0] valid_reg; // Extended valid register for more granular state control

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
            valid_reg <= 5'd0;
            done <= 0;
            for (i = 0; i < 8; i = i + 1) 
            begin
                partial_products[i] <= 32'd0;
            end
            s1 <= 0; s2 <= 0; s3 <= 0; s4 <= 0;
            temp_products1 <= 0; temp_products2 <= 0;
            result <= 32'd0;
            done <= 1'b0;
        end 
        else 
        begin
            if (start && !valid_reg[0]) begin
                X_reg <= X;
                Y_reg <= Y;
                valid_reg[0] <= 1;  // Initiate state 1
            end
            else
              valid_reg[0] <= 0;  // Initiate state 1 

            // Process Booth multiplication
            if (valid_reg[0]) begin
                for (i = 0; i < 8; i = i + 1) begin
                    case ({Y_reg[2*i+1], Y_reg[2*i], (i == 0) ? 1'b0 : Y_reg[2*i-1]})
                        3'b000, 3'b111: partial_products[i] <= 32'd0;
                        3'b001, 3'b010: partial_products[i] <= {{16{X_reg[15]}}, X_reg} >> (2*i);
                        3'b011: partial_products[i] <= {{16{X_reg[15]}}, X_reg} >> (2*i + 1);
                        3'b100: partial_products[i] <= -({{16{X_reg[15]}}, X_reg} >> (2*i + 1));
                        3'b101, 3'b110: partial_products[i] <= -({{16{X_reg[15]}}, X_reg} >> (2*i));
                        default: partial_products[i] <= 32'd0;
                    endcase
                end
                valid_reg[1] <= 1; // State 1 done, mark State 2 as ready
                valid_reg[0] <= 0; // Reset state 1 active flag
            end 
            else
              valid_reg[1] <= 0; // State 1 done, mark State 2 as ready

            // State 3: Partial Summation
            if (valid_reg[1]) begin 
                s1 <= partial_products[0] + partial_products[1] + partial_products[2];
                s2 <= partial_products[3] + partial_products[4] + partial_products[5];
                
                valid_reg[2] <= 1; // State 3 done, mark State 4 as ready
                valid_reg[1] <= 0; // Clear state 2 active flag
            end 
            else
              valid_reg[2] <= 0; // State 3 done, mark State 4 as ready 

            // State 4: Sum of Sums
            if (valid_reg[2]) begin 
                s3 <= s1 + s2;
                s4 <= partial_products[6] + partial_products[7];
                
                valid_reg[3] <= 1; // State 4 done, mark State 5 as ready
                valid_reg[2] <= 0; // Clear state 3 active flag
            end 
            else
              valid_reg[3] <= 0; // State 4 done, mark State 5 as ready

            
            // State 5: Final Result
            if (valid_reg[3]) begin
                result <= s3 + s4;
                done <= 1;  // Output done signal
                valid_reg[3] <= 0; // Reset state 5 active flag after result computation
            end 
            else
            begin
              result <= 0;
              done <= 1'b0; 
            end 
            
        end
    end
        
endmodule