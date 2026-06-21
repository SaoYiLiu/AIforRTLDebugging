module axi_alu (
    input  wire        axi_clk_in,
    input  wire        fast_clk_in,
    input  wire        reset_in,

    input  wire        axi_awvalid_i,
    input  wire [7:0]  axi_awlen_i,
    input  wire [2:0]  axi_awsize_i,
    input  wire [1:0]  axi_awburst_i,
    input  wire        axi_wvalid_i,
    input  wire        axi_wlast_i,
    input  wire        axi_bready_i,
    input  wire        axi_arvalid_i,
    input  wire [7:0]  axi_arlen_i,
    input  wire [2:0]  axi_arsize_i,
    input  wire [1:0]  axi_arburst_i,
    input  wire        axi_rready_i,

    output wire        axi_awready_o,
    output wire        axi_wready_o,
    output wire        axi_bvalid_o,
    output wire [1:0]  axi_bresp_o,
    output wire        axi_arready_o,
    output wire        axi_rvalid_o,
    output wire [1:0]  axi_rresp_o,
    output wire        axi_rlast_o,

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
    wire [31:0] data_a, data_b, data_c;

    wire [31:0] operand_a_cdc, operand_b_cdc, operand_c_cdc;
    wire [1:0]  op_select_cdc;
    wire        start_cdc;
    wire [31:0] operand_a_sync, operand_b_sync, operand_c_sync;
    wire [1:0]  op_select_sync;
    wire        start_sync;

    wire [63:0] dsp_result;
    wire [63:0] dsp_result_sync;
    wire [63:0] dsp_result_csr;

    wire        mem_we;
    wire [3:0]  mem_waddr;
    wire [31:0] mem_wdata;
    wire [3:0]  mem_raddr;
    wire [31:0] mem_rdata;

    clock_control u_clock_control (
        .axi_clk_in  (axi_clk_in),
        .fast_clk_in (fast_clk_in),
        .clk_ctrl    (clock_control),
        .clk         (clk)
    );

    assign dsp_result_csr = clock_control ? dsp_result_sync : dsp_result;

    axi_csr_block u_axi_csr_block (
        .axi_aclk_i      (axi_clk_in),
        .axi_areset_i    (reset_in),
        .axi_awvalid_i   (axi_awvalid_i),
        .axi_awready_o   (axi_awready_o),
        .axi_awaddr_i    (axi_awaddr_i),
        .axi_awlen_i     (axi_awlen_i),
        .axi_awsize_i    (axi_awsize_i),
        .axi_awburst_i   (axi_awburst_i),
        .axi_wvalid_i    (axi_wvalid_i),
        .axi_wready_o    (axi_wready_o),
        .axi_wdata_i     (axi_wdata_i),
        .axi_wstrb_i     (axi_wstrb_i),
        .axi_wlast_i     (axi_wlast_i),
        .axi_bvalid_o    (axi_bvalid_o),
        .axi_bresp_o     (axi_bresp_o),
        .axi_bready_i    (axi_bready_i),
        .axi_arvalid_i   (axi_arvalid_i),
        .axi_arready_o   (axi_arready_o),
        .axi_araddr_i    (axi_araddr_i),
        .axi_arlen_i     (axi_arlen_i),
        .axi_arsize_i    (axi_arsize_i),
        .axi_arburst_i   (axi_arburst_i),
        .axi_rvalid_o    (axi_rvalid_o),
        .axi_rresp_o     (axi_rresp_o),
        .axi_rlast_o     (axi_rlast_o),
        .axi_rready_i    (axi_rready_i),
        .axi_rdata_o     (axi_rdata_o),
        .operand_a       (operand_a_cdc),
        .operand_b       (operand_b_cdc),
        .operand_c       (operand_c_cdc),
        .op_select       (op_select_cdc),
        .start           (start_cdc),
        .clock_control   (clock_control),
        .dsp_result_i    (dsp_result_csr),
        .mem_we          (mem_we),
        .mem_waddr       (mem_waddr),
        .mem_wdata       (mem_wdata),
        .mem_raddr       (mem_raddr),
        .mem_rdata       (mem_rdata)
    );

    assign operand_a = clock_control ? operand_a_sync : operand_a_cdc;
    assign operand_b = clock_control ? operand_b_sync : operand_b_cdc;
    assign operand_c = clock_control ? operand_c_sync : operand_c_cdc;
    assign op_select = clock_control ? op_select_sync : op_select_cdc;
    assign start     = clock_control ? start_sync     : start_cdc;

    cdc_synchronizer #(.WIDTH(32)) u_cdc_operand_a (
        .clk_dst(clk), .reset_in(reset_in), .enable(clock_control),
        .data_in(operand_a_cdc), .data_out(operand_a_sync)
    );
    cdc_synchronizer #(.WIDTH(32)) u_cdc_operand_b (
        .clk_dst(clk), .reset_in(reset_in), .enable(clock_control),
        .data_in(operand_b_cdc), .data_out(operand_b_sync)
    );
    cdc_synchronizer #(.WIDTH(32)) u_cdc_operand_c (
        .clk_dst(clk), .reset_in(reset_in), .enable(clock_control),
        .data_in(operand_c_cdc), .data_out(operand_c_sync)
    );
    cdc_synchronizer #(.WIDTH(2)) u_cdc_op_select (
        .clk_dst(clk), .reset_in(reset_in), .enable(clock_control),
        .data_in(op_select_cdc), .data_out(op_select_sync)
    );
    cdc_synchronizer #(.WIDTH(1)) u_cdc_start (
        .clk_dst(clk), .reset_in(reset_in), .enable(clock_control),
        .data_in(start_cdc), .data_out(start_sync)
    );
    cdc_synchronizer #(.WIDTH(64)) u_cdc_dsp_result (
        .clk_dst(axi_clk_in), .reset_in(reset_in), .enable(clock_control),
        .data_in(dsp_result), .data_out(dsp_result_sync)
    );

    memory_block u_memory_block (
        .axi_clk    (axi_clk_in),
        .ctrl_clk   (clk),
        .reset_in   (reset_in),
        .we         (mem_we),
        .write_addr (mem_waddr),
        .write_data (mem_wdata),
        .read_addr  (mem_raddr),
        .read_data  (mem_rdata),
        .address_a  (operand_a[5:0]),
        .address_b  (operand_b[5:0]),
        .address_c  (operand_c[5:0]),
        .data_a     (data_a),
        .data_b     (data_b),
        .data_c     (data_c)
    );

    dsp_block u_dsp_block (
        .clk       (clk),
        .reset_in  (reset_in),
        .operand_a (data_a),
        .operand_b (data_b),
        .operand_c (data_c),
        .op_select (op_select),
        .start     (start),
        .result    (dsp_result)
    );

    assign result_o = dsp_result;

endmodule

module cdc_synchronizer #(parameter WIDTH = 1) (
    input  wire             clk_dst,
    input  wire             reset_in,
    input  wire             enable,
    input  wire [WIDTH-1:0] data_in,
    output reg  [WIDTH-1:0] data_out
);
    reg [WIDTH-1:0] sync1, sync2;

    always @(posedge clk_dst or posedge reset_in) begin
        if (reset_in) begin
            sync1    <= {WIDTH{1'b0}};
            sync2    <= {WIDTH{1'b0}};
            data_out <= {WIDTH{1'b0}};
        end else if (enable) begin
            sync1    <= data_in;
            sync2    <= sync1;
            data_out <= sync2;
        end
    end
endmodule

module clock_control (
    input  wire axi_clk_in,
    input  wire fast_clk_in,
    input  wire clk_ctrl,
    output wire clk
);
    assign clk = clk_ctrl ? fast_clk_in : axi_clk_in;
endmodule

module axi_csr_block (
    input  wire        axi_aclk_i,
    input  wire        axi_areset_i,

    input  wire        axi_awvalid_i,
    output reg         axi_awready_o,
    input  wire [31:0] axi_awaddr_i,
    input  wire [7:0]  axi_awlen_i,
    input  wire [2:0]  axi_awsize_i,
    input  wire [1:0]  axi_awburst_i,

    input  wire        axi_wvalid_i,
    output reg         axi_wready_o,
    input  wire [31:0] axi_wdata_i,
    input  wire [3:0]  axi_wstrb_i,
    input  wire        axi_wlast_i,

    output reg         axi_bvalid_o,
    output reg  [1:0]  axi_bresp_o,
    input  wire        axi_bready_i,

    input  wire        axi_arvalid_i,
    output reg         axi_arready_o,
    input  wire [31:0] axi_araddr_i,
    input  wire [7:0]  axi_arlen_i,
    input  wire [2:0]  axi_arsize_i,
    input  wire [1:0]  axi_arburst_i,

    output reg         axi_rvalid_o,
    output reg  [1:0]  axi_rresp_o,
    output reg         axi_rlast_o,
    input  wire        axi_rready_i,
    output reg  [31:0] axi_rdata_o,

    output reg  [31:0] operand_a,
    output reg  [31:0] operand_b,
    output reg  [31:0] operand_c,
    output reg  [1:0]  op_select,
    output reg         start,
    output reg         clock_control,

    input  wire [63:0] dsp_result_i,

    output reg         mem_we,
    output reg  [3:0]  mem_waddr,
    output reg  [31:0] mem_wdata,
    output wire [3:0]  mem_raddr,
    input  wire [31:0] mem_rdata
);

    reg [31:0] control_reg;
    reg [31:0] clock_reg;

    reg        wr_busy;
    reg [31:0] wr_addr;
    reg [7:0]  wr_len;
    reg [2:0]  wr_size;
    reg [1:0]  wr_burst;
    reg [7:0]  wr_cnt;

    reg        rd_busy;
    reg [31:0] rd_addr;
    reg [7:0]  rd_len;
    reg [2:0]  rd_size;
    reg [1:0]  rd_burst;
    reg [7:0]  rd_cnt;

    assign mem_raddr = is_mem_addr(rd_addr) ? mem_index(rd_addr) : 4'd0;

    function automatic bit is_mem_addr(input [31:0] addr);
        is_mem_addr = (addr >= 32'h0000_0020) && (addr[1:0] == 2'b00);
    endfunction

    function automatic [31:0] normalize_mem_addr(input [31:0] addr);
        reg [31:0] word_index;
        begin
            word_index = (addr - 32'h0000_0020) >> 2;
            word_index = word_index % 16;
            normalize_mem_addr = 32'h0000_0020 + (word_index << 2);
        end
    endfunction

    function automatic [3:0] mem_index(input [31:0] addr);
        mem_index = (normalize_mem_addr(addr) - 32'h0000_0020) >> 2;
    endfunction

    function automatic [31:0] read_data_for_addr(input [31:0] addr);
        begin
            if (is_mem_addr(addr)) begin
                read_data_for_addr = mem_rdata;
            end else begin
                case (addr[6:0])
                    7'h00:   read_data_for_addr = operand_a;
                    7'h04:   read_data_for_addr = operand_b;
                    7'h08:   read_data_for_addr = operand_c;
                    7'h0C:   read_data_for_addr = control_reg;
                    7'h10:   read_data_for_addr = clock_reg;
                    7'h14:   read_data_for_addr = dsp_result_i[31:0];
                    7'h18:   read_data_for_addr = dsp_result_i[63:32];
                    default: read_data_for_addr = 32'd0;
                endcase
            end
        end
    endfunction

    always @(posedge axi_aclk_i or posedge axi_areset_i) begin
        if (axi_areset_i) begin
            operand_a     <= 32'd0;
            operand_b     <= 32'd0;
            operand_c     <= 32'd0;
            control_reg   <= 32'd0;
            clock_reg     <= 32'd0;
            op_select     <= 2'd0;
            start         <= 1'b0;
            clock_control <= 1'b0;

            axi_awready_o <= 1'b0;
            axi_wready_o  <= 1'b0;
            axi_bvalid_o  <= 1'b0;
            axi_bresp_o   <= 2'b00;
            axi_arready_o <= 1'b0;
            axi_rvalid_o  <= 1'b0;
            axi_rresp_o   <= 2'b00;
            axi_rlast_o   <= 1'b0;
            axi_rdata_o   <= 32'd0;

            mem_we        <= 1'b0;
            mem_waddr     <= 4'd0;
            mem_wdata     <= 32'd0;
            wr_busy       <= 1'b0;
            wr_addr       <= 32'd0;
            wr_len        <= 8'd0;
            wr_size       <= 3'd0;
            wr_burst      <= 2'b00;
            wr_cnt        <= 8'd0;

            rd_busy       <= 1'b0;
            rd_addr       <= 32'd0;
            rd_len        <= 8'd0;
            rd_size       <= 3'd0;
            rd_burst      <= 2'b00;
            rd_cnt        <= 8'd0;
        end else begin
            mem_we <= 1'b0;

            if (axi_bvalid_o && axi_bready_i) begin
                axi_bvalid_o <= 1'b0;
            end

            axi_awready_o <= !wr_busy && !axi_bvalid_o;
            if (axi_awready_o && axi_awvalid_i) begin
                wr_addr  <= axi_awaddr_i;
                wr_len   <= axi_awlen_i;
                wr_size  <= axi_awsize_i;
                wr_burst <= axi_awburst_i;
                wr_cnt   <= 8'd0;
                wr_busy  <= 1'b1;
            end

            axi_wready_o <= wr_busy;
            if (wr_busy && axi_wvalid_i && axi_wready_o) begin
                if (wr_addr[1:0] == 2'b00) begin
                    if (is_mem_addr(wr_addr)) begin
                        mem_we    <= 1'b1;
                        mem_waddr <= mem_index(wr_addr);
                        mem_wdata <= axi_wdata_i;
                    end else begin
                        case (wr_addr[6:0])
                            7'h00: operand_a <= axi_wdata_i;
                            7'h04: operand_b <= axi_wdata_i;
                            7'h08: operand_c <= axi_wdata_i;
                            7'h0C: begin
                                control_reg <= axi_wdata_i;
                                op_select   <= axi_wdata_i[1:0];
                                start       <= axi_wdata_i[2];
                            end
                            7'h10: begin
                                clock_reg     <= axi_wdata_i;
                                clock_control <= axi_wdata_i[0];
                            end
                            default: ;
                        endcase
                    end
                end

                if (axi_wlast_i || wr_cnt == wr_len) begin
                    wr_busy      <= 1'b0;
                    axi_bvalid_o <= 1'b1;
                    axi_bresp_o  <= 2'b00;
                end else begin
                    wr_cnt <= wr_cnt + 8'd1;
                    if (wr_burst == 2'b01) begin
                        wr_addr <= wr_addr + (32'd1 << wr_size);
                    end
                end
            end

            axi_arready_o <= !rd_busy && !axi_rvalid_o;
            if (axi_arready_o && axi_arvalid_i) begin
                rd_addr  <= axi_araddr_i;
                rd_len   <= axi_arlen_i;
                rd_size  <= axi_arsize_i;
                rd_burst <= axi_arburst_i;
                rd_cnt   <= 8'd0;
                rd_busy  <= 1'b1;
            end

            if (rd_busy && !axi_rvalid_o) begin
                axi_rdata_o  <= read_data_for_addr(rd_addr);
                axi_rvalid_o <= 1'b1;
                axi_rresp_o  <= 2'b00;
                axi_rlast_o  <= (rd_cnt == rd_len);
            end

            if (axi_rvalid_o && axi_rready_i) begin
                axi_rvalid_o <= 1'b0;
                axi_rlast_o  <= 1'b0;
                if (rd_cnt == rd_len) begin
                    rd_busy <= 1'b0;
                end else begin
                    rd_cnt <= rd_cnt + 8'd1;
                    if (rd_burst == 2'b01) begin
                        rd_addr <= rd_addr + (32'd1 << rd_size);
                    end
                end
            end
        end
    end
endmodule

module memory_block (
    input  wire        axi_clk,
    input  wire        ctrl_clk,
    input  wire        reset_in,
    input  wire        we,
    input  wire [3:0]  write_addr,
    input  wire [31:0] write_data,
    input  wire [3:0]  read_addr,
    output wire [31:0] read_data,
    input  wire [5:0]  address_a,
    input  wire [5:0]  address_b,
    input  wire [5:0]  address_c,
    output reg  [31:0] data_a,
    output reg  [31:0] data_b,
    output reg  [31:0] data_c
);
    reg [31:0] ram [0:15];

    integer i;

    always @(posedge axi_clk or posedge reset_in) begin
        if (reset_in) begin
            for (i = 0; i < 16; i = i + 1) begin
                ram[i] <= 32'd0;
            end
        end else if (we) begin
            ram[write_addr] <= write_data;
        end
    end

    assign read_data = ram[read_addr];

    always @(posedge ctrl_clk or posedge reset_in) begin
        if (reset_in) begin
            data_a <= 32'd0;
            data_b <= 32'd0;
            data_c <= 32'd0;
        end else begin
            data_a <= ram[address_a[3:0]];
            data_b <= ram[address_b[3:0]];
            data_c <= ram[address_c[3:0]];
        end
    end
endmodule

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
        if (reset_in) begin
            result <= 64'd0;
        end else if (start) begin
            case (op_select)
                2'b00:   result <= (operand_a + operand_b) * operand_c;
                2'b01:   result <= operand_a * operand_b;
                2'b10:   result <= operand_a >> operand_b[4:0];
                2'b11:   result <= operand_b ? (operand_a / operand_b) : 64'h0000_0000_DEADDEAD;
                default: result <= 64'd0;
            endcase
        end
    end
endmodule
