module axi_alu (
    input  wire        axi_clk_in,
    input  wire        fast_clk_in,
    input  wire        reset_in,
    
    // AXI Interface
    input  wire        axi_awvalid_i,
    input  wire        axi_wvalid_i,
    input  wire        axi_bready_i,
    input  wire        axi_arvalid_i,
    input  wire        axi_rready_i,
    
    output wire        axi_awready_o,
    output wire        axi_wready_o,
    output wire        axi_bvalid_o,
    output wire        axi_arready_o,
    output wire        axi_rvalid_o,
    
    input  wire [31:0] axi_awaddr_i,
    input  wire [31:0] axi_wdata_i,
    input  wire [31:0] axi_araddr_i,
    
    input  wire [3:0]  axi_wstrb_i,
    output wire [31:0] axi_rdata_o,
    output wire [63:0] result_o
);
    
    wire        clk;
    wire [31:0] operand_a, operand_b, operand_c;
    wire [1:0]  op_select;
    wire        start, clock_control;
    wire [31:0] data_a;
    wire [31:0] data_b;
    wire [31:0] data_c;
    
    wire [31:0] operand_a_cdc, operand_b_cdc, operand_c_cdc;
    wire [1:0]  op_select_cdc;
    wire        start_cdc;
    wire [31:0] operand_a_sync, operand_b_sync, operand_c_sync;
    wire [1:0]  op_select_sync;
    wire        start_sync;

    clock_control u_clock_control (
        .axi_clk_in  (axi_clk_in),
        .fast_clk_in (fast_clk_in),
        .clk_ctrl    (clock_control),
        .clk         (clk)
    );

    axi_csr_block u_axi_csr_block (
        .axi_aclk_i    (axi_clk_in),
        .axi_areset_i  (reset_in),
        .axi_awvalid_i   (axi_awvalid_i),
        .axi_awready_o   (axi_awready_o),
        .axi_awaddr_i    (axi_awaddr_i),
        .axi_wvalid_i    (axi_wvalid_i),
        .axi_wready_o    (axi_wready_o),
        .axi_wdata_i     (axi_wdata_i),
        .axi_wstrb_i     (axi_wstrb_i),
        .axi_bvalid_o    (axi_bvalid_o),
        .axi_bready_i    (axi_bready_i),
        .axi_arvalid_i   (axi_arvalid_i),
        .axi_arready_o   (axi_arready_o),
        .axi_araddr_i    (axi_araddr_i),
        .axi_rvalid_o    (axi_rvalid_o),
        .axi_rready_i    (axi_rready_i),
        .axi_rdata_o     (axi_rdata_o),
        .operand_a     (operand_a_cdc),
        .operand_b     (operand_b_cdc),
        .operand_c     (operand_c_cdc),
        .op_select     (op_select_cdc),
        .start         (start_cdc),
        .clock_control (clock_control)
    );

    // CDC logic is only active when clock_control is HIGH
    assign operand_a = (clock_control) ? operand_a_sync : operand_a_cdc;
    assign operand_b = (clock_control) ? operand_b_sync : operand_b_cdc;
    assign operand_c = (clock_control) ? operand_c_sync : operand_c_cdc;
    assign op_select = (clock_control) ? op_select_sync : op_select_cdc;
    assign start     = (clock_control) ? start_sync : start_cdc;

    // CDC Synchronizers (only used when fast_clk is selected)
    cdc_synchronizer #(.WIDTH(32)) u_cdc_operand_a (.clk_src(axi_clk_in), .clk_dst(clk), .reset_in(reset_in), .data_in(operand_a_cdc), .data_out(operand_a_sync));
    cdc_synchronizer #(.WIDTH(32)) u_cdc_operand_b (.clk_src(axi_clk_in), .clk_dst(clk), .reset_in(reset_in), .data_in(operand_b_cdc), .data_out(operand_b_sync));
    cdc_synchronizer #(.WIDTH(32)) u_cdc_operand_c (.clk_src(axi_clk_in), .clk_dst(clk), .reset_in(reset_in), .data_in(operand_c_cdc), .data_out(operand_c_sync));
    cdc_synchronizer #(.WIDTH(2))  u_cdc_op_select  (.clk_src(axi_clk_in), .clk_dst(clk), .reset_in(reset_in), .data_in(op_select_cdc), .data_out(op_select_sync));
    cdc_synchronizer #(.WIDTH(1))  u_cdc_start      (.clk_src(axi_clk_in), .clk_dst(clk), .reset_in(reset_in), .data_in(start_cdc), .data_out(start_sync));

    memory_block u_memory_block (
        .clk        (clk),
        .reset_in   (reset_in),
        .address_a  (operand_a[5:0]),
        .address_b  (operand_b[5:0]),
        .address_c  (operand_c[5:0]),
        .data_a     (data_a),
        .data_b     (data_b),
        .data_c     (data_c)
    );

    dsp_block u_dsp_block (
        .clk        (clk),
        .reset_in   (reset_in),
        .operand_a  (data_a),
        .operand_b  (data_b),
        .operand_c  (data_c),
        .op_select  (op_select),
        .start      (start),
        .result     (result_o)
    );

endmodule

// ------------------------------------------------------------------
// CDC Synchronizer Module (Double Flop Synchronization)
// ------------------------------------------------------------------
module cdc_synchronizer #(parameter WIDTH = 1) (
    input wire clk_src,  // Source clock
    input wire clk_dst,  // Destination clock
    input wire reset_in, // Reset signal
    input wire [WIDTH-1:0] data_in,  // Data from source domain
    output reg [WIDTH-1:0] data_out  // Synchronized data in destination domain
);
    reg [WIDTH-1:0] data_sync_1, data_sync_2;

    always @(posedge clk_dst or posedge reset_in) begin
        if (reset_in) begin
            data_sync_1 <= {WIDTH{1'b0}};
            data_sync_2 <= {WIDTH{1'b0}};
            data_out    <= {WIDTH{1'b0}};
        end else begin
            data_sync_1 <= data_in;   // First stage
            data_sync_2 <= data_sync_1; // Second stage
            data_out    <= data_sync_2; // Stable output
        end
    end
endmodule

// ------------------------------------------------------------------
// Clock Control Module
// ------------------------------------------------------------------
module clock_control (
    input  wire axi_clk_in,
    input  wire fast_clk_in,
    input  wire clk_ctrl,
    output wire clk
);
    assign clk = clk_ctrl ? fast_clk_in : axi_clk_in;
endmodule

// ------------------------------------------------------------------
// AXI-to-CSR Register Block (With Write Response Handling)
// ------------------------------------------------------------------
module axi_csr_block (
    input  wire        axi_aclk_i,
    input  wire        axi_areset_i,
    
    // AXI Write Address Channel
    input  wire        axi_awvalid_i,
    output reg         axi_awready_o,
    input  wire [31:0] axi_awaddr_i,
    
    // AXI Write Data Channel
    input  wire        axi_wvalid_i,
    output reg         axi_wready_o,
    input  wire [31:0] axi_wdata_i,
    input  wire [3:0]  axi_wstrb_i,
    
    // AXI Write Response Channel (FIXED)
    output reg         axi_bvalid_o,
    input  wire        axi_bready_i,
    
    // AXI Read Address Channel
    input  wire        axi_arvalid_i,
    output reg         axi_arready_o,
    input  wire [31:0] axi_araddr_i,
    
    // AXI Read Data Channel
    output reg         axi_rvalid_o,
    input  wire        axi_rready_i,
    output reg  [31:0] axi_rdata_o,
    
    // CSR Outputs
    output reg  [31:0] operand_a,
    output reg  [31:0] operand_b,
    output reg  [31:0] operand_c,
    output reg  [1:0]  op_select,
    output reg         start,
    output reg         clock_control
);
    reg [31:0] csr_reg [0:4];

    always @(posedge axi_aclk_i or posedge axi_areset_i) begin
        if (axi_areset_i) begin
            operand_a     <= 32'd0;
            operand_b     <= 32'd0;
            operand_c     <= 32'd0;
            op_select     <= 2'd0;
            start         <= 1'b0;
            clock_control <= 1'b0;
            axi_awready_o <= 0;
            axi_wready_o  <= 0;
            axi_bvalid_o  <= 0; // Set response valid
            axi_arready_o <= 0;
            axi_rvalid_o  <= 0;
            axi_rdata_o   <= 32'd0;
            csr_reg[0]    <= 32'd0;
            csr_reg[1]    <= 32'd0;
            csr_reg[2]    <= 32'd0;
            csr_reg[3]    <= 32'd0;
            csr_reg[4]    <= 32'd0;
        end else begin
            // Handle AXI Write
            if (axi_awvalid_i && axi_wvalid_i) begin
                csr_reg[axi_awaddr_i[4:2]] <= axi_wdata_i;
                axi_awready_o <= 1;
                axi_wready_o  <= 1;
                axi_bvalid_o  <= 1; // Set response valid
            end else begin
                axi_awready_o <= 0;
                axi_wready_o  <= 0;
                axi_bvalid_o  <= 0; // Set response valid
            end

            // Handle Write Response
            if (axi_bvalid_o && axi_bready_i) begin
                axi_bvalid_o <= 0; // Clear response once acknowledged
            end

            // Handle AXI Read
            if (axi_arvalid_i) begin
                axi_arready_o <= 1;
                axi_rvalid_o  <= 1;
                axi_rdata_o    <= csr_reg[axi_araddr_i[4:2]];
            end else begin
                axi_arready_o <= 0;
                axi_rvalid_o  <= 0;
            end

            // Update CSR Registers
            operand_a     <= csr_reg[0];
            operand_b     <= csr_reg[1];
            operand_c     <= csr_reg[2];
            op_select     <= csr_reg[3][1:0];
            start         <= csr_reg[3][2];
            clock_control <= csr_reg[4][0];
        end
    end
endmodule

// ------------------------------------------------------------------
// Memory Block (ROM)
// ------------------------------------------------------------------
module memory_block (
    input  wire        clk,
    input  wire        reset_in,
    input  wire [5:0]  address_a,
    input  wire [5:0]  address_b,
    input  wire [5:0]  address_c,
    output wire [31:0] data_a,
    output wire [31:0] data_b,
    output wire [31:0] data_c
);
    reg [31:0] rom [0:63];

    initial begin
        $readmemh("../rom_data.mem", rom);
    end

    assign data_a = (reset_in) ? 32'd0 : rom[address_a];
    assign data_b = (reset_in) ? 32'd0 : rom[address_b];
    assign data_c = (reset_in) ? 32'd0 : rom[address_c];
endmodule

// ------------------------------------------------------------------
// DSP Processing Block
// ------------------------------------------------------------------
module dsp_block (
    input  wire        clk,
    input  wire        reset_in,
    input  wire [31:0] operand_a,
    input  wire [31:0] operand_b,
    input  wire [31:0] operand_c,
    input  wire [1:0]  op_select,
    input  wire        start,
    output reg  [63:0] result
);
    always @(posedge clk or posedge reset_in) begin
        if (reset_in)
            result <= 64'd0;
        else begin
            if (start) begin
                case (op_select)
                    2'b00: result <= (operand_a + operand_b) * operand_c;    // MAC
                    2'b01: result <= operand_a * operand_b;    // Multiplication
                    2'b10: result <= operand_a >> operand_b[4:0]; // Shift Right
                    2'b11: result <= operand_b ? operand_a / operand_b : 64'hDEADDEAD; // Division (handle divide by zero)
                endcase
            end
        end
    end
endmodule