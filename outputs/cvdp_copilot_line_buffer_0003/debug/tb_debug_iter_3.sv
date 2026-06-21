`timescale 1ns/1ps

// Compile with:
//   iverilog -g2012 -o sim rtl/line_buffer.sv tb_debug.sv && vvp sim
// View:
//   gtkwave wave.vcd

module tb_debug;

    localparam int NBW_DATA  = 8;
    localparam int NS_ROW    = 3;
    localparam int NS_COLUMN = 3;
    localparam int NS_R_OUT  = 2;
    localparam int NS_C_OUT  = 2;
    localparam int CONSTANT  = 255;
    localparam int NBW_ROW   = 2;
    localparam int NBW_COL   = 2;
    localparam int WIN_W     = NBW_DATA * NS_R_OUT * NS_C_OUT;

    logic clk;
    logic rst_async_n;
    logic [2:0]                   i_mode;
    logic                         i_valid;
    logic                         i_update_window;
    logic [NBW_DATA*NS_COLUMN-1:0] i_row_image;
    logic [NBW_ROW-1:0]           i_image_row_start;
    logic [NBW_COL-1:0]           i_image_col_start;
    logic [WIN_W-1:0]             o_image_window;

    // ------------------------------------------------------------------
    // DUT
    // ------------------------------------------------------------------
    line_buffer #(
        .NBW_DATA (NBW_DATA),
        .NS_ROW   (NS_ROW),
        .NS_COLUMN(NS_COLUMN),
        .NBW_ROW  (NBW_ROW),
        .NBW_COL  (NBW_COL),
        .NBW_MODE (3),
        .NS_R_OUT (NS_R_OUT),
        .NS_C_OUT (NS_C_OUT),
        .CONSTANT (CONSTANT)
    ) dut (
        .clk               (clk),
        .rst_async_n       (rst_async_n),
        .i_mode            (i_mode),
        .i_valid           (i_valid),
        .i_update_window   (i_update_window),
        .i_row_image       (i_row_image),
        .i_image_row_start (i_image_row_start),
        .i_image_col_start (i_image_col_start),
        .o_image_window    (o_image_window)
    );

    // ------------------------------------------------------------------
    // Clock
    // ------------------------------------------------------------------
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // ------------------------------------------------------------------
    // Mismatch tracking
    // ------------------------------------------------------------------
    reg        tb_mismatch;
    reg        tb_first_mismatch_done;
    integer    tb_cycle;
    reg [WIN_W-1:0] tb_expected;

    // ------------------------------------------------------------------
    // Reference buffer (mirrors cocotb model ordering:
    //   after posedge: update_window -> add_line -> compare)
    // ------------------------------------------------------------------
    reg [NBW_DATA-1:0] ref_buf [0:NS_ROW-1][0:NS_COLUMN-1];
    reg [WIN_W-1:0]    ref_window;

    function automatic [NBW_DATA-1:0] slice_pixel(input [NBW_DATA*NS_COLUMN-1:0] row_word, input int col);
        slice_pixel = row_word[(col+1)*NBW_DATA-1 -: NBW_DATA];
    endfunction

    task automatic ref_reset;
        integer r, c;
        begin
            for (r = 0; r < NS_ROW; r = r + 1)
                for (c = 0; c < NS_COLUMN; c = c + 1)
                    ref_buf[r][c] = {NBW_DATA{1'b0}};
            ref_window = {WIN_W{1'b0}};
        end
    endtask

    task automatic ref_add_line(input [NBW_DATA*NS_COLUMN-1:0] row_word);
        integer r, c;
        reg [NBW_DATA-1:0] row_image [0:NS_COLUMN-1];
        begin
            for (c = 0; c < NS_COLUMN; c = c + 1)
                row_image[NS_COLUMN-c-1] = slice_pixel(row_word, c);

            for (c = 0; c < NS_COLUMN; c = c + 1)
                ref_buf[0][c] = row_image[c];

            for (r = 1; r < NS_ROW; r = r + 1)
                for (c = 0; c < NS_COLUMN; c = c + 1)
                    ref_buf[r][c] = ref_buf[r-1][c];
        end
    endtask

    function automatic int mirror_idx(input int idx, input int size);
        int dist;
        begin
            if (idx < size)
                mirror_idx = idx;
            else begin
                dist = idx - (size - 1);
                if (dist < (size - 1))
                    mirror_idx = (size - 1) - dist;
                else
                    mirror_idx = 2 * (size - 1) - dist;
            end
        end
    endfunction

    task automatic ref_compute_window(
        input [2:0] mode,
        input [NBW_ROW-1:0] rs,
        input [NBW_COL-1:0] cs
    );
        integer wr, wc;
        integer sr, sc;
        reg [NBW_DATA-1:0] pix;
        reg [WIN_W-1:0] packed;
        begin
            packed = {WIN_W{1'b0}};
            for (wr = 0; wr < NS_R_OUT; wr = wr + 1) begin
                for (wc = 0; wc < NS_C_OUT; wc = wc + 1) begin
                    sr = rs + wr;
                    sc = cs + wc;
                    case (mode)
                        3'd0: pix = (sr >= NS_ROW || sc >= NS_COLUMN) ? {NBW_DATA{1'b0}} : ref_buf[sr][sc];
                        3'd1: pix = (sr >= NS_ROW || sc >= NS_COLUMN) ? CONSTANT[NBW_DATA-1:0] : ref_buf[sr][sc];
                        3'd2: begin
                            if (sr >= NS_ROW) sr = NS_ROW - 1;
                            if (sc >= NS_COLUMN) sc = NS_COLUMN - 1;
                            pix = ref_buf[sr][sc];
                        end
                        3'd3: begin
                            if (sr >= NS_ROW) sr = mirror_idx(sr, NS_ROW);
                            if (sc >= NS_COLUMN) sc = mirror_idx(sc, NS_COLUMN);
                            pix = ref_buf[sr][sc];
                        end
                        3'd4: begin
                            if (sr >= NS_ROW) sr = sr - NS_ROW;
                            if (sc >= NS_COLUMN) sc = sc - NS_COLUMN;
                            pix = ref_buf[sr][sc];
                        end
                        default: pix = {NBW_DATA{1'b0}};
                    endcase
                    packed[(wr*NS_C_OUT+wc+1)*NBW_DATA-1 -: NBW_DATA] = pix;
                end
            end
            ref_window = packed;
        end
    endtask

    // ------------------------------------------------------------------
    // Apply one vector, clock once, check (spec table methodology)
    // ------------------------------------------------------------------
    task apply_cycle(
        input [2:0]  mode,
        input        valid,
        input        upd,
        input [23:0] row_img,
        input [1:0]  rs,
        input [1:0]  cs,
        input [WIN_W-1:0] golden
    );
        begin
            i_mode            = mode;
            i_valid           = valid;
            i_update_window   = upd;
            i_row_image       = row_img;
            i_image_row_start = rs;
            i_image_col_start = cs;

            @(posedge clk);
            #1; // let NBA settle

            // cocotb model order after posedge
            if (upd)
                ref_compute_window(mode, rs, cs);
            if (valid)
                ref_add_line(row_img);

            tb_expected = golden;

            if (o_image_window !== golden) begin
                tb_mismatch = 1'b1;
                if (!tb_first_mismatch_done) begin
                    tb_first_mismatch_done = 1'b1;
                    $display("First mismatch occurred at time %0t (spec cycle %0d)", $time, tb_cycle);
                end
                $display("CYCLE %0d MISMATCH @ %0t", tb_cycle, $time);
                $display("  inputs: mode=%0d valid=%0d upd=%0d row=0x%h rs=%0d cs=%0d",
                         mode, valid, upd, row_img, rs, cs);
                $display("  DUT   o_image_window = 0x%h", o_image_window);
                $display("  SPEC  expected         = 0x%h", golden);
                $display("  REF   model window    = 0x%h", ref_window);
            end else begin
                $display("CYCLE %0d PASS @ %0t  o_image_window=0x%h", tb_cycle, $time, o_image_window);
            end

            tb_cycle = tb_cycle + 1;
        end
    endtask

    // ------------------------------------------------------------------
    // Main stimulus — spec observed-behavior table (3x3 / 2x2 window)
    // ------------------------------------------------------------------
    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_debug);

        tb_mismatch             = 1'b0;
        tb_first_mismatch_done  = 1'b0;
        tb_cycle                = 1;

        clk               = 1'b0;
        rst_async_n       = 1'b0;
        i_mode            = 3'd0;
        i_valid           = 1'b0;
        i_update_window   = 1'b0;
        i_row_image       = '0;
        i_image_row_start = '0;
        i_image_col_start = '0;

        ref_reset();

        // Reset pulse
        repeat (2) @(posedge clk);
        rst_async_n = 1'b1;
        @(posedge clk);
        #1;
        ref_reset();

        $display("=== line_buffer spec-table debug sim (NBW=8 NS_ROW=3 NS_COL=3 win=2x2) ===");

        // | Cycle | mode | valid | upd | row_image | rs | cs | expected |
        apply_cycle(3'd5, 1'b0, 1'b0, 24'h823cfd, 2'd1, 2'd1, 32'h00000000); // 1
        apply_cycle(3'd4, 1'b1, 1'b0, 24'h30f90e, 2'd1, 2'd1, 32'h00000000); // 2 load row
        apply_cycle(3'd0, 1'b0, 1'b1, 24'h887534, 2'd1, 2'd0, 32'h00000000); // 3
        apply_cycle(3'd4, 1'b0, 1'b0, 24'hc36ed8, 2'd2, 2'd0, 32'h00000000); // 4
        apply_cycle(3'd1, 1'b0, 1'b1, 24'hfd77b0, 2'd0, 2'd2, 32'hff00ff0e); // 5 PAD — key fail
        apply_cycle(3'd5, 1'b1, 1'b1, 24'h0bd533, 2'd0, 2'd2, 32'h00000000); // 6 invalid mode
        apply_cycle(3'd4, 1'b1, 1'b0, 24'haad861, 2'd1, 2'd1, 32'h00000000); // 7 load row
        apply_cycle(3'd3, 1'b1, 1'b1, 24'h11f57c, 2'd2, 2'd1, 32'h0ef90ef9); // 8 MIRROR — key fail
        apply_cycle(3'd0, 1'b0, 1'b1, 24'hbf2ce0, 2'd2, 2'd2, 32'h00000033); // 9
        apply_cycle(3'd2, 1'b0, 1'b1, 24'hbdfa0f, 2'd1, 2'd0, 32'hd50bd8aa); // 10 EXTEND — key fail

        if (tb_mismatch)
            $display("=== SUMMARY: FAIL (see wave.vcd — inspect dut.image_buffer_ff, dut.window, dut.image_window_ff) ===");
        else
            $display("=== SUMMARY: PASS all 10 spec-table cycles ===");

        #20 $finish;
    end

endmodule
