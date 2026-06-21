module axis_rgb2ycbcr #(
    parameter PIXEL_WIDTH = 16,
    parameter FIFO_DEPTH = 16
)(
    input  wire            aclk,
    input  wire            aresetn,

    // AXI Stream Slave Interface (Input)
    input  wire [15:0]     s_axis_tdata,
    input  wire            s_axis_tvalid,
    output wire            s_axis_tready,
    input  wire            s_axis_tlast,
    input  wire            s_axis_tuser,

    // AXI Stream Master Interface (Output)
    output wire [15:0]     m_axis_tdata,
    output wire            m_axis_tvalid,
    input  wire            m_axis_tready,
    output wire            m_axis_tlast,
    output wire            m_axis_tuser
);

    // -----------------------------
    // FIFO Buffer (16-depth buffer)
    // -----------------------------
    reg [15:0] fifo_data [0:FIFO_DEPTH-1];
    reg        fifo_tlast [0:FIFO_DEPTH-1];
    reg        fifo_tuser [0:FIFO_DEPTH-1];

    reg [3:0]  write_ptr, read_ptr; // 4-bit pointers for FIFO
    reg        full;
    wire       empty;

    wire       fifo_write = s_axis_tvalid && !full;
    wire       fifo_read  = !empty && m_axis_tready;

    // -----------------------------
    // RGB Extraction
    // -----------------------------
    wire [7:0] r = {s_axis_tdata[15:11], 3'b0}; // 5-bit to 8-bit
    wire [7:0] g = {s_axis_tdata[10:5],  2'b0}; // 6-bit to 8-bit
    wire [7:0] b = {s_axis_tdata[4:0],   3'b0}; // 5-bit to 8-bit

    // -----------------------------
    // RGB to YCbCr Conversion
    // -----------------------------
    wire [7:0] y_calc  = (( 77 * r + 150 * g +  29 * b) >> 8) + 16;
    wire [7:0] cb_calc = ((-43 * r - 85 * g + 128 * b) >> 8) + 128;
    wire [7:0] cr_calc = ((128 * r - 107 * g - 21 * b) >> 8) + 128;

    // -----------------------------
    // FIFO Buffer Write
    // -----------------------------
    always @(posedge aclk) begin
        if (!aresetn) begin
            write_ptr <= 0;
            full <= 0;
        end else if (fifo_write) begin
            fifo_data[write_ptr] <= {y_calc[7:3], cb_calc[7:2], cr_calc[7:3]};
            fifo_tlast[write_ptr] <= s_axis_tlast;
            fifo_tuser[write_ptr] <= s_axis_tuser;
            write_ptr <= write_ptr + 1;
            full <= (write_ptr == FIFO_DEPTH-1);
        end
    end

    // -----------------------------
    // FIFO Buffer Read
    // -----------------------------
    always @(posedge aclk) begin
        if (!aresetn) begin
            read_ptr <= 0;
        end else if (fifo_read) begin
            read_ptr <= read_ptr + 1;
        end
    end
    assign empty = (read_ptr == write_ptr);

    // -----------------------------
    // AXI-Stream Output Signals
    // -----------------------------
    assign s_axis_tready = !full;
    assign m_axis_tvalid = !empty;
    assign m_axis_tdata  = fifo_data[read_ptr];
    assign m_axis_tlast  = fifo_tlast[read_ptr];
    assign m_axis_tuser  = fifo_tuser[read_ptr];

endmodule
