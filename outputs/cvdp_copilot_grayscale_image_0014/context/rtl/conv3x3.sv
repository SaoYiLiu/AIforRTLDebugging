module conv3x3 (
    input logic          clk,               // Clock signal
    input logic          rst_n,             // Reset signal, active low
    input logic  [7:0]   image_data0,       // Individual pixel data inputs (8-bit each)
    input logic  [7:0]   image_data1,
    input logic  [7:0]   image_data2,
    input logic  [7:0]   image_data3,
    input logic  [7:0]   image_data4,
    input logic  [7:0]   image_data5,
    input logic  [7:0]   image_data6,
    input logic  [7:0]   image_data7,
    input logic  [7:0]   image_data8,
    input logic  [7:0]   kernel0,           // Individual kernel inputs (8-bit each)
    input logic  [7:0]   kernel1,
    input logic  [7:0]   kernel2,
    input logic  [7:0]   kernel3,
    input logic  [7:0]   kernel4,
    input logic  [7:0]   kernel5,
    input logic  [7:0]   kernel6,
    input logic  [7:0]   kernel7,
    input logic  [7:0]   kernel8,
    output logic [15:0]  convolved_data     // 16-bit convolved output
);

    // Stage 1: Element-wise multiplication results
    logic [15:0] mult_result0, mult_result1, mult_result2;
    logic [15:0] mult_result3, mult_result4, mult_result5;
    logic [15:0] mult_result6, mult_result7, mult_result8;

    // Stage 2: Row-wise partial sums
    logic [19:0] pipeline_sum_stage10, pipeline_sum_stage11, pipeline_sum_stage12;

    // Stage 3: Final total sum
    logic [19:0] sum_result;

    // Stage 4: Normalized result
    logic [15:0] normalized_result;

    // Stage 1: Element-wise multiplications
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mult_result0 <= 0; mult_result1 <= 0; mult_result2 <= 0;
            mult_result3 <= 0; mult_result4 <= 0; mult_result5 <= 0;
            mult_result6 <= 0; mult_result7 <= 0; mult_result8 <= 0;
        end else begin
            mult_result0 <= image_data0 * kernel0;
            mult_result1 <= image_data1 * kernel1;
            mult_result2 <= image_data2 * kernel2;
            mult_result3 <= image_data3 * kernel3;
            mult_result4 <= image_data4 * kernel4;
            mult_result5 <= image_data5 * kernel5;
            mult_result6 <= image_data6 * kernel6;
            mult_result7 <= image_data7 * kernel7;
            mult_result8 <= image_data8 * kernel8;
        end
    end

    // Stage 2: Row-wise summation
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pipeline_sum_stage10 <= 0;
            pipeline_sum_stage11 <= 0;
            pipeline_sum_stage12 <= 0;
        end else begin
            pipeline_sum_stage10 <= mult_result0 + mult_result1 + mult_result2;
            pipeline_sum_stage11 <= mult_result3 + mult_result4; 
            pipeline_sum_stage12 <= mult_result6 + mult_result7 + mult_result8;
        end
    end

    // Stage 3: Total summation
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_result <= 0;
        end else begin
            sum_result <= pipeline_sum_stage10 + pipeline_sum_stage11 + pipeline_sum_stage12;
        end
    end

    // Stage 4: Normalization
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            convolved_data <= 0;
        end else begin
            convolved_data <= sum_result / 8; // Normalization
        end
    end

endmodule