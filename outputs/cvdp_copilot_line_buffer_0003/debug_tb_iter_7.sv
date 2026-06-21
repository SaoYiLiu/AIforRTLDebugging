`timescale 1ns/1ps

// Build (spec geometry):
//   iverilog -g2012 -o sim tb_debug.sv rtl/line_buffer.sv && vvp sim
// View:
//   gtkwave wave.vcd

module tb_debug;

    // ------------------------------------------------------------------
    // Spec-table geometry (3x3 buffer, 2x2 window) — cycles 5/8/10
    // ------------------------------------------------------------------
    localparam NBW_DATA_S  = 8;
    localparam NS_ROW_S    = 3;
    localparam NS_COLUMN_S = 3;
    localparam NS_R_OUT_S  = 2;
    localparam NS_C_OUT_S  = 2;
    localparam CONSTANT_S  = 255;
    localparam WIN_W_S     = NBW_DATA_S * NS_R_OUT_S * NS_C_OUT_S;

    reg clk;
    reg rst_async_n;
    reg [2:0]  i_mode_s;
    reg        i_valid_s;
    reg        i_update_window_s;
    reg [23:0] i_row_image_s;
    reg [1:0]  i_image_row_start_s;
    reg [1:0]  i_image_col_start_s;
    wire [WIN_W_S-1:0] o_image_window_s;

    line_buffer #(
        .NBW_DATA (NBW_DATA_S),
        .NS_ROW   (NS_ROW_S),
        .NS_COLUMN(NS_COLUMN_S),
        .NBW_ROW  (2),
        .NBW_COL  (2),
        .NBW_MODE (3),
        .NS_R_OUT (NS_R_OUT_S),
        .NS_C_OUT (NS_C_OUT_S),
        .CONSTANT (CONSTANT_S)
    ) dut_spec (
        .clk               (clk),
        .rst_async_n       (rst_async_n),
        .i_mode            (i_mode_s),
        .i_valid           (i_valid_s),
        .i_update_window   (i_update_window_s),
        .i_row_image       (i_row_image_s),
        .i_image_row_start (i_image_row_start_s),
        .i_image_col_start (i_image_col_start_s),
        .o_image_window    (o_image_window_s)
    );

    // ------------------------------------------------------------------
    // Harness geometry (first failure params: 10x8, 4x3 window)
    // ------------------------------------------------------------------
    localparam NBW_DATA_H  = 8;
    localparam NS_ROW_H    = 10;
    localparam NS_COLUMN_H = 8;
    localparam NS_R_OUT_H  = 4;
    localparam NS_C_OUT_H  = 3;
    localparam CONSTANT_H  = 255;
    localparam WIN_W_H     = NBW_DATA_H * NS_R_OUT_H * NS_C_OUT_H;

    reg [2:0]  i_mode_h;
    reg        i_valid_h;
    reg        i_update_window_h;
    reg [63:0] i_row_image_h;
    reg [3:0]  i_image_row_start_h;
    reg [2:0]  i_image_col_start_h;
    wire [WIN_W_H-1:0] o_image_window_h;

    line_buffer #(
        .NBW_DATA (NBW_DATA_H),
        .NS_ROW   (NS_ROW_H),
        .NS_COLUMN(NS_COLUMN_H),
        .NBW_ROW  (4),
        .NBW_COL  (3),
        .NBW_MODE (3),
        .NS_R_OUT (NS_R_OUT_H),
        .NS_C_OUT (NS_C_OUT_H),
        .CONSTANT (CONSTANT_H)
    ) dut_h (
        .clk               (clk),
        .rst_async_n       (rst_async_n),
        .i_mode            (i_mode_h),
        .i_valid           (i_valid_h),
        .i_update_window   (i_update_window_h),
        .i_row_image       (i_row_image_h[NBW_DATA_H*NS_COLUMN_H-1:0]),
        .i_image_row_start (i_image_row_start_h),
        .i_image_col_start (i_image_col_start_h),
        .o_image_window    (o_image_window_h)
    );

    // ------------------------------------------------------------------
    reg tb_mismatch;
    reg tb_first_mismatch_done;
    integer tb_cycle;

    initial clk = 1'b0;
    always #5 clk = ~clk;

    // ------------------------------------------------------------------
    task reset_all;
        begin
            rst_async_n = 1'b0;
            i_mode_s = 3'd0;
            i_valid_s = 1'b0;
            i_update_window_s = 1'b0;
            i_row_image_s = 24'h0;
            i_image_row_start_s = 2'd0;
            i_image_col_start_s = 2'd0;

            i_mode_h = 3'd0;
            i_valid_h = 1'b0;
            i_update_window_h = 1'b0;
            i_row_image_h = 64'h0;
            i_image_row_start_h = 4'd0;
            i_image_col_start_h = 3'd0;

            repeat (2) @(posedge clk);
            rst_async_n = 1'b1;
            @(posedge clk);
        end
    endtask

    task check_spec;
        input [255:0] tag;
        input [WIN_W_S-1:0] expected;
        begin
            if (o_image_window_s !== expected) begin
                tb_mismatch = 1'b1;
                if (!tb_first_mismatch_done) begin
                    tb_first_mismatch_done = 1'b1;
                    $display("First mismatch occurred at time %0t", $time);
                end
                $display("SPEC MISMATCH %0s @ %0t", tag, $time);
                $display("  DUT  = 0x%0h", o_image_window_s);
                $display("  GOLD = 0x%0h", expected);
            end else begin
                $display("SPEC PASS %0s @ %0t o=0x%0h", tag, $time, o_image_window_s);
            end
        end
    endtask

    task spec_cycle;
        input [2:0]  mode;
        input        valid;
        input        upd;
        input [23:0] row_img;
        input [1:0]  rs;
        input [1:0]  cs;
        input [WIN_W_S-1:0] gold;
        input [255:0] tag;
        begin
            i_mode_s = mode;
            i_valid_s = valid;
            i_update_window_s = upd;
            i_row_image_s = row_img;
            i_image_row_start_s = rs;
            i_image_col_start_s = cs;
            @(posedge clk);
            #1;
            check_spec(tag, gold);
            tb_cycle = tb_cycle + 1;
        end
    endtask

    // Minimal cocotb-order reference for harness both-high check
    reg [NBW_DATA_H-1:0] ref_buf [0:9][0:7];
    reg [WIN_W_H-1:0]    ref_window;
    reg [WIN_W_H-1:0]    last_h_window;
    integer ri, ci, wr, wc, sr, sc;

    task ref_reset_h;
        integer r, c;
        begin
            for (r = 0; r < NS_ROW_H; r = r + 1)
                for (c = 0; c < NS_COLUMN_H; c = c + 1)
                    ref_buf[r][c] = 8'h00;
            ref_window = {WIN_W_H{1'b0}};
        end
    endtask

    task ref_add_line_h;
        input [63:0] row_word;
        integer c, r;
        reg [NBW_DATA_H-1:0] row_image [0:7];
        begin
            for (c = 0; c < NS_COLUMN_H; c = c + 1)
                row_image[NS_COLUMN_H-c-1] =
                    row_word[(c+1)*NBW_DATA_H-1 -: NBW_DATA_H];
            for (c = 0; c < NS_COLUMN_H; c = c + 1)
                ref_buf[0][c] = row_image[c];
            for (r = 1; r < NS_ROW_H; r = r + 1)
                for (c = 0; c < NS_COLUMN_H; c = c + 1)
                    ref_buf[r][c] = ref_buf[r-1][c];
        end
    endtask

    task ref_update_h;
        input [2:0] mode;
        input [3:0] rs;
        input [2:0] cs;
        reg [WIN_W_H-1:0] packed;
        begin
            packed = {WIN_W_H{1'b0}};
            for (wr = 0; wr < NS_R_OUT_H; wr = wr + 1) begin
                for (wc = 0; wc < NS_C_OUT_H; wc = wc + 1) begin
                    sr = rs + wr;
                    sc = cs + wc;
                    if (mode == 3'd1) begin
                        if (sr >= NS_ROW_H || sc >= NS_COLUMN_H)
                            ref_buf[0][0] = ref_buf[0][0]; // no-op placeholder
                    end
                    if (sr >= NS_ROW_H || sc >= NS_COLUMN_H)
                        packed[(wr*NS_C_OUT_H+wc+1)*NBW_DATA_H-1 -: NBW_DATA_H] = CONSTANT_H;
                    else
                        packed[(wr*NS_C_OUT_H+wc+1)*NBW_DATA_H-1 -: NBW_DATA_H] = ref_buf[sr][sc];
                end
            end
            ref_window = packed;
        end
    endtask

    task drive_h;
        input [2:0] mode;
        input valid;
        input upd;
        input [63:0] row_img;
        input [3:0] rs;
        input [2:0] cs;
        begin
            i_mode_h = mode;
            i_valid_h = valid;
            i_update_window_h = upd;
            i_row_image_h = row_img;
            i_image_row_start_h = rs;
            i_image_col_start_h = cs;
            @(posedge clk);
            #1;
            if (upd) ref_update_h(mode, rs, cs);
            if (valid) ref_add_line_h(row_img);
            if (upd) last_h_window = ref_window;
        end
    endtask

    task check_h;
        input [255:0] tag;
        begin
            if (o_image_window_h !== ref_window) begin
                tb_mismatch = 1'b1;
                if (!tb_first_mismatch_done) begin
                    tb_first_mismatch_done = 1'b1;
                    $display("First mismatch occurred at time %0t", $time);
                end
                $display("HARN MISMATCH %0s @ %0t", tag, $time);
                $display("  DUT  = 0x%0h", o_image_window_h);
                $display("  REF  = 0x%0h", ref_window);
                $display("  valid=%b upd=%b mode=%0d rs=%0d cs=%0d",
                         i_valid_h, i_update_window_h, i_mode_h,
                         i_image_row_start_h, i_image_col_start_h);
            end else begin
                $display("HARN PASS %0s @ %0t o=0x%0h", tag, $time, o_image_window_h);
            end
        end
    endtask

    task check_h_hold;
        input [255:0] tag;
        begin
            if (o_image_window_h !== last_h_window) begin
                tb_mismatch = 1'b1;
                if (!tb_first_mismatch_done) begin
                    tb_first_mismatch_done = 1'b1;
                    $display("First mismatch occurred at time %0t", $time);
                end
                $display("HOLD MISMATCH %0s @ %0t dut=0x%0h expect=0x%0h",
                         tag, $time, o_image_window_h, last_h_window);
            end else begin
                $display("HOLD PASS %0s @ %0t", tag, $time);
            end
        end
    endtask

    // ------------------------------------------------------------------
    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_debug);

        tb_mismatch = 1'b0;
        tb_first_mismatch_done = 1'b0;
        tb_cycle = 0;

        reset_all();
        ref_reset_h();

        $display("=== SPEC TABLE (3x3 / 2x2) ===");

        // Load rows for later cycles (2, 7, 8)
        spec_cycle(3'd5, 1'b0, 1'b0, 24'h823cfd, 2'd1, 2'd1, 32'h0, "c1");
        spec_cycle(3'd4, 1'b1, 1'b0, 24'h30f90e, 2'd1, 2'd1, 32'h0, "c2");
        spec_cycle(3'd0, 1'b0, 1'b1, 24'h887534, 2'd1, 2'd0, 32'h0, "c3");
        spec_cycle(3'd4, 1'b0, 1'b0, 24'hc36ed8, 2'd2, 2'd0, 32'h0, "c4");
        spec_cycle(3'd1, 1'b0, 1'b1, 24'hfd77b0, 2'd0, 2'd2, 32'hff00ff0e, "c5 PAD");
        spec_cycle(3'd5, 1'b1, 1'b1, 24'h0bd533, 2'd0, 2'd2, 32'h0, "c6 inv");
        spec_cycle(3'd4, 1'b1, 1'b0, 24'haad861, 2'd1, 2'd1, 32'h0, "c7");
        spec_cycle(3'd3, 1'b1, 1'b1, 24'h11f57c, 2'd2, 2'd1, 32'h0ef90ef9, "c8 MIRROR");
        spec_cycle(3'd0, 1'b0, 1'b1, 24'hbf2ce0, 2'd2, 2'd2, 32'h00000033, "c9");
        spec_cycle(3'd2, 1'b0, 1'b1, 24'hbdfa0f, 2'd1, 2'd0, 32'hd50bd8aa, "c10 EXTEND");

        $display("=== HARNESS GEOM: both-high + hold ===");

        drive_h(3'd4, 1'b1, 1'b0, 64'h0102030405060708, 4'd0, 3'd0);
        check_h("load0");
        drive_h(3'd4, 1'b1, 1'b0, 64'h1112131415161718, 4'd0, 3'd0);
        check_h("load1");
        drive_h(3'd4, 1'b1, 1'b0, 64'h2122232425262728, 4'd0, 3'd0);
        check_h("load2");

        // Critical: valid+update same cycle (cocotb order in drive_h)
        drive_h(3'd1, 1'b1, 1'b1, 64'ha0a1a2a3a4a5a6a7a8, 4'd1, 3'd2);
        check_h("both_high");

        // Hold: deassert update, change inputs — output must freeze
        i_update_window_h = 1'b0;
        i_mode_h = 3'd0;
        i_image_row_start_h = 4'd7;
        i_image_col_start_h = 3'd7;
        @(posedge clk);
        #1;
        check_h_hold("hold_after_update");

        if (tb_mismatch)
            $display("SUMMARY: FAIL — inspect dut_spec/dut_h: image_buffer_ff, image_buffer_snapshot, buffer_view, image_window_ff");
        else
            $display("SUMMARY: PASS");

        #20 $finish;
    end

endmodule
