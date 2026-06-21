module radix2_div(
    input            clk,
    input            rst_n,
    input            start,
    input      [7:0] dividend,
    input      [7:0] divisor,
    output reg [7:0] quotient,
    output reg [7:0] remainder,
    output reg       done
);

    reg [7:0] rem;
    reg [3:0] bit_counter;
    reg [7:0] divisor_reg;
    reg       busy;

    // Normal, correct shift and compare logic
    wire [8:0] shifted_rem = {rem, dividend[bit_counter]};
    wire       bit_set     = shifted_rem >= {1'b0, divisor_reg};
    wire [8:0] next_rem    = bit_set ? (shifted_rem - {1'b0, divisor_reg}) : shifted_rem;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            quotient <= 8'd0;
        else if (start && !busy) begin
            if (divisor == 8'd0)
                quotient <= 8'hFF;
            else
                quotient <= 8'd0;
        end
        else if (busy) begin
            quotient[bit_counter] <= bit_set;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            rem <= 8'd0;
        else if (start && !busy)
            rem <= 8'd0;
        else if (busy)
            rem <= next_rem[7:0];
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            remainder <= 8'd0;
        else if (start && !busy && divisor == 8'd0)
            remainder <= 8'hFF;
        else if (busy && bit_counter == 4'd0) begin
            if (next_rem[7:0] != 8'd0)
                remainder <= next_rem[7:0] + 1'b1;
            else
                remainder <= next_rem[7:0];
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            bit_counter <= 4'd0;
        else if (start && !busy) begin
            if (divisor != 8'd0)
                bit_counter <= 4'd7;  // Start from MSB
        end
        else if (busy && bit_counter != 4'd0) begin
            bit_counter <= bit_counter - 4'd1; // Normal decrement
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            divisor_reg <= 8'd0;
        else if (start && !busy && divisor != 8'd0)
            divisor_reg <= divisor;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            done <= 1'b0;
        else if (start && !busy) begin
            if (divisor == 8'd0)
                done <= 1'b1;
            else
                done <= 1'b0;
        end
        else if (busy && bit_counter == 4'd0)
            done <= 1'b1;
        else
            done <= 1'b0;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            busy <= 1'b0;
        else if (start && !busy) begin
            if (divisor != 8'd0)
                busy <= 1'b1;
            else
                busy <= 1'b0;
        end
        else if (busy && bit_counter == 4'd0)
            busy <= 1'b0;
    end

endmodule