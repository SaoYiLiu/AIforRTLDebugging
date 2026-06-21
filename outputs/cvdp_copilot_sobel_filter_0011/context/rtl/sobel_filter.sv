module sobel_filter (
    input            clk,
    input            rst_n,
    input      [7:0] pixel_in,
    input            valid_in,
    output reg [7:0] edge_out,
    output reg       valid_out
);
    // Internal signals for gradients
    reg signed [10:0] Gx, Gy;  // To accommodate larger values after convolution
    reg [7:0] pixel_buffer[0:8]; // 3x3 pixel window
    integer i;

    // Parameters for thresholding
    parameter THRESHOLD = 11'd128;

    // Sliding window logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1) begin
                pixel_buffer[i] <= 8'd0;
            end    
        end else if (valid_in) begin
            pixel_buffer[8] <= pixel_buffer[7];
            pixel_buffer[7] <= pixel_buffer[6];
            pixel_buffer[6] <= pixel_buffer[5];
            pixel_buffer[5] <= pixel_buffer[4];
            pixel_buffer[4] <= pixel_buffer[3];
            pixel_buffer[3] <= pixel_buffer[2];
            pixel_buffer[2] <= pixel_buffer[1];
            pixel_buffer[1] <= pixel_buffer[0];
            pixel_buffer[0] <= pixel_in;
        end
    end

    // Sobel convolution and edge detection
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            Gx        <= 11'sd0;
            Gy        <= 11'sd0;
            edge_out  <= 8'd0;
            valid_out <= 1'b0;
        end else if (valid_in) begin
            // Compute Gx and Gy using Sobel kernels
            Gx <= -pixel_buffer[6] - (pixel_buffer[3] << 1) - pixel_buffer[0]
                  +pixel_buffer[8] + (pixel_buffer[5] << 1) + pixel_buffer[2];
            Gy <= -pixel_buffer[6] - (pixel_buffer[7] << 1) - pixel_buffer[8]
                  +pixel_buffer[0] + (pixel_buffer[1] << 1) + pixel_buffer[2];

            // Compute gradient magnitude (simplified as |Gx| + |Gy|)
            edge_out <= ((Gx < 0 ? -Gx : Gx) + (Gy < 0 ? -Gy : Gy)) > THRESHOLD ? 8'd255 : 8'd0;

            // Set valid output
            valid_out <= 1'b1;
        end else begin
            valid_out <= 1'b0;
        end
    end
endmodule