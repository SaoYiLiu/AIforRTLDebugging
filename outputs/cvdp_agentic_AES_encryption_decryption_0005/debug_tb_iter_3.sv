`timescale 1ns/1ps

module tb_debug;

    // -------------------------------------------------------------------------
    // Cocotb Reset 0 / Run 0 reproduction (seed 1782033944, j=0 -> update_key=1)
    // Harness expected plaintext for this failing run:
    //   0xe90267c3eb4e2f989ebb2d2a19f26a91
    // -------------------------------------------------------------------------
    localparam [127:0] TB_KEY      = 128'h69cd4acf181b4caae9323d5662e4649a;
    localparam [127:0] TB_DATA     = 128'h70b97df2d5f9f054774a4b6640cda5b7;
    localparam [127:0] TB_EXPECTED = 128'he90267c3eb4e2f989ebb2d2a19f26a91;

    logic               clk;
    logic               rst_async_n;
    logic               i_update_key;
    logic               i_start;
    logic [127:0]       i_key;
    logic [127:0]       i_data;
    logic               o_done;
    logic [127:0]       o_data;

    logic               tb_mismatch;
    logic               mismatch_reported;
    logic [3:0]         round_ff_prev;

    aes128_decrypt dut (
        .clk          (clk),
        .rst_async_n  (rst_async_n),
        .i_update_key (i_update_key),
        .i_key        (i_key),
        .i_start      (i_start),
        .i_data       (i_data),
        .o_done       (o_done),
        .o_data       (o_data)
    );

    // Flag mismatch when operation completes with wrong plaintext
    assign tb_mismatch = o_done && (o_data !== TB_EXPECTED);

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;  // 10 ns period, matches cocotb Clock(dut.clk, 10, unit='ns')
    end

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_debug);
    end

    // Log first completion mismatch (matches requested $display format)
    always @(posedge clk) begin
        if (tb_mismatch && !mismatch_reported) begin
            mismatch_reported = 1'b1;
            $display("First mismatch occurred at time %0t", $time);
            $display("  o_data   = 0x%032h", o_data);
            $display("  expected = 0x%032h", TB_EXPECTED);
        end
    end

    // Trace FSM / key-expansion interaction (primary debug value in VCD)
    always @(posedge clk) begin
        if (rst_async_n) begin
            if (dut.round_ff != round_ff_prev) begin
                $display("t=%0t round_ff %0d -> %0d  key_done=%b  update_key_ff=%b  o_done=%b",
                         $time, round_ff_prev, dut.round_ff, dut.key_done,
                         dut.update_key_ff, o_done);
            end
            if (dut.key_done && dut.round_ff == 4'd1)
                $display("t=%0t key expansion complete, starting decrypt round 1", $time);
        end
        round_ff_prev = dut.round_ff;
    end

    task automatic drive_idle();
        i_update_key = 1'b0;
        i_start      = 1'b0;
        i_key        = 128'd0;
        i_data       = 128'd0;
    endtask

    initial begin
        rst_async_n       = 1'b0;
        mismatch_reported = 1'b0;
        round_ff_prev     = 4'd0;
        drive_idle();

        // Mirror cocotb: assert reset for one cycle, then release
        repeat (1) @(posedge clk);
        rst_async_n = 1'b1;
        repeat (1) @(posedge clk);

        // Post-reset check (cocotb compare_values after model.reset())
        if (o_done !== 1'b1)
            $display("t=%0t WARNING: o_done not set after reset (o_done=%b)", $time, o_done);

        // Reset 0 / Run 0: key update + decrypt start (same as test_aes128_decrypt.py)
        i_key        = TB_KEY;
        i_data       = TB_DATA;
        i_update_key = 1'b1;
        i_start      = 1'b1;
        @(posedge clk);

        drive_idle();
        @(posedge clk);

        // Wait until decrypt FSM returns to idle (matches cocotb while o_done==0 loop)
        while (o_done !== 1'b1)
            @(posedge clk);

        if (!mismatch_reported)
            $display("t=%0t PASS: o_data matches expected", $time);
        else
            $display("t=%0t FAIL: decrypt completed with wrong plaintext", $time);

        repeat (4) @(posedge clk);
        $finish;
    end

endmodule
