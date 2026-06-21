module sobel_filter (
    input            clk,
    input            rst_n,
    input      [7:0] pixel_in,
    input            valid_in,
    output reg [7:0] edge_out,
    output reg       valid_out
);
    reg signed [10:0] Gx, Gy;
    reg signed [10:0] gx_val, gy_val, mag;
    reg [7:0] pixel_buffer[0:8];
    reg [3:0] pixel_count;
    integer i;

    parameter THRESHOLD = 11'd128;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1) begin
                pixel_buffer[i] <= 8'd0;
            end
            pixel_count <= 4'd0;
            Gx        <= 11'sd0;
            Gy        <= 11'sd0;
            edge_out  <= 8'd0;
            valid_out <= 1'b0;
        end else begin
            valid_out <= 1'b0;
            edge_out  <= 8'd0;

            if (valid_in) begin
                if (pixel_count == 4'd8) begin
                    gx_val = -$signed({3'b0, pixel_buffer[7]})
                           - ($signed({3'b0, pixel_buffer[4]}) << 1)
                           -  $signed({3'b0, pixel_buffer[1]})
                           +  $signed({3'b0, pixel_buffer[5]})
                           + ($signed({3'b0, pixel_buffer[2]}) << 1)
                           +  $signed({3'b0, pixel_in});

                    gy_val = -$signed({3'b0, pixel_buffer[7]})
                           - ($signed({3'b0, pixel_buffer[6]}) << 1)
                           -  $signed({3'b0, pixel_buffer[5]})
                           +  $signed({3'b0, pixel_buffer[1]})
                           + ($signed({3'b0, pixel_buffer[0]}) << 1)
                           +  $signed({3'b0, pixel_in});

                    mag = (gx_val < 0 ? -gx_val : gx_val)
                        + (gy_val < 0 ? -gy_val : gy_val);

                    Gx        <= gx_val;
                    Gy        <= gy_val;
                    edge_out  <= (mag > THRESHOLD) ? 8'd255 : 8'd0;
                    valid_out <= 1'b1;

                    for (i = 0; i < 9; i = i + 1) begin
                        pixel_buffer[i] <= 8'd0;
                    end
                    pixel_count <= 4'd0;
                end else begin
                    pixel_buffer[8] <= pixel_buffer[7];
                    pixel_buffer[7] <= pixel_buffer[6];
                    pixel_buffer[6] <= pixel_buffer[5];
                    pixel_buffer[5] <= pixel_buffer[4];
                    pixel_buffer[4] <= pixel_buffer[3];
                    pixel_buffer[3] <= pixel_buffer[2];
                    pixel_buffer[2] <= pixel_buffer[1];
                    pixel_buffer[1] <= pixel_buffer[0];
                    pixel_buffer[0] <= pixel_in;
                    pixel_count <= pixel_count + 1'b1;
                end
            end else begin
                for (i = 0; i < 9; i = i + 1) begin
                    pixel_buffer[i] <= 8'd0;
                end
                pixel_count <= 4'd0;
            end
        end
    end
endmodule
