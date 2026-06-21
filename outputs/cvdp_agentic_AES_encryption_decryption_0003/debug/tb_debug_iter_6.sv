`timescale 1ns/1ns

module tb_debug;
    logic clk;
    logic rst_async_n;
    logic i_update_key;
    logic i_start;
    logic [127:0] i_key;
    logic [127:0] i_data;
    logic o_done;
    logic [127:0] o_data;

    wire tb_mismatch;

    aes128_encrypt dut (
        .clk           (clk),
        .rst_async_n   (rst_async_n),
        .i_update_key  (i_update_key),
        .i_key         (i_key),
        .i_start       (i_start),
        .i_data        (i_data),
        .o_done        (o_done),
        .o_data        (o_data)
    );

    // 10 ns period, same as cocotb Clock(dut.clk, 10, unit='ns')
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // NIST AES-128 ECB block (deterministic sanity check)
    localparam [127:0] NIST_KEY  = 128'h000102030405060708090a0b0c0d0e0f;
    localparam [127:0] NIST_DATA = 128'h00112233445566778899aabbccddeeff;
    localparam [127:0] NIST_EXP  = 128'h69c4e0d86a7b0430d8cdb78070b4c55a;

    logic [127:0] exp_data;
    logic [127:0] chk_key;
    logic [127:0] chk_data;
    logic [127:0] chk_exp;
    integer scenario;
    integer cycle_count;
    logic mismatch_seen;

    assign tb_mismatch = (o_done && (o_data !== exp_data));

    task automatic cocotb_reset;
        begin
            i_start      = 1'b0;
            i_update_key = 1'b0;
            i_key        = 128'h0;
            i_data       = 128'h0;
            rst_async_n  = 1'b0;
            @(posedge clk);
            rst_async_n  = 1'b1;
            @(posedge clk);
        end
    endtask

    // Mirrors test_aes128_encrypt.py: one start cycle, clear inputs, wait for o_done
    task automatic cocotb_encrypt_once(
        input logic        update_key,
        input logic [127:0] key,
        input logic [127:0] data
    );
        begin
            i_update_key = update_key;
            i_key        = key;
            i_data       = data;
            i_start      = 1'b1;

            @(posedge clk);
            i_start      = 1'b0;
            i_key        = 128'h0;
            i_update_key = 1'b0;
            i_data       = 128'h0;

            @(posedge clk);
            while (o_done !== 1'b1) begin
                @(posedge clk);
            end
        end
    endtask

    task automatic dump_schedule(input integer sc);
        begin
            $display("[%0t] scenario=%0d round_ff=%0d o_done=%0d o_data=%h expected=%h",
                     $time, sc, dut.round_ff, o_done, o_data, exp_data);
            $display("  valid_key=%h", dut.valid_key);
            $display("  rk0: ff=%h comp=%h rk_src=%h sched=%h",
                     dut.expanded_key_ff[1407:1280],
                     dut.expanded_key_computed[1407:1280],
                     dut.rk_source[1407:1280],
                     dut.round_key_sched[1407:1280]);
            $display("  rk1: ff=%h comp=%h rk_src=%h sched=%h",
                     dut.expanded_key_ff[1279:1152],
                     dut.expanded_key_computed[1279:1152],
                     dut.rk_source[1279:1152],
                     dut.round_key_sched[1279:1152]);
            $display("  rk10: ff=%h comp=%h rk_src=%h sched=%h",
                     dut.expanded_key_ff[127:0],
                     dut.expanded_key_computed[127:0],
                     dut.rk_source[127:0],
                     dut.round_key_sched[127:0]);
        end
    endtask

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_debug);

        i_start      = 1'b0;
        i_update_key = 1'b0;
        i_key        = 128'h0;
        i_data       = 128'h0;
        rst_async_n  = 1'b0;
        exp_data     = 128'h0;
        mismatch_seen = 1'b0;

        // Optional replay of a specific cocotb vector:
        //   vvp sim.vvp +KEY=... +DATA=... +EXP=...
        if (!$value$plusargs("KEY=%h", chk_key))  chk_key  = NIST_KEY;
        if (!$value$plusargs("DATA=%h", chk_data)) chk_data = NIST_DATA;
        if (!$value$plusargs("EXP=%h", chk_exp))  chk_exp  = NIST_EXP;

        // --- Scenario 0: NIST vector, update_key=1 (cocotb j=0 path) ---
        scenario = 0;
        cocotb_reset();
        exp_data = NIST_EXP;
        cocotb_encrypt_once(1'b1, NIST_KEY, NIST_DATA);

        if (o_data !== exp_data) begin
            mismatch_seen = 1'b1;
            $display("First mismatch occurred at time %0t", $time);
            dump_schedule(scenario);
        end

        // --- Scenario 1: user/cocotb replay vector ---
        scenario = 1;
        cocotb_reset();
        exp_data = chk_exp;
        cocotb_encrypt_once(1'b1, chk_key, chk_data);

        if (o_data !== exp_data) begin
            if (!mismatch_seen) begin
                mismatch_seen = 1'b1;
                $display("First mismatch occurred at time %0t", $time);
            end
            dump_schedule(scenario);
        end

        // --- Scenario 2: encrypt again without key update (stored schedule) ---
        scenario = 2;
        exp_data = chk_exp;
        cocotb_encrypt_once(1'b0, 128'h0, chk_data);

        if (o_data !== exp_data) begin
            if (!mismatch_seen) begin
                mismatch_seen = 1'b1;
                $display("First mismatch occurred at time %0t", $time);
            end
            dump_schedule(scenario);
        end

        if (mismatch_seen)
            $display("tb_debug: FAIL (see wave.vcd)");
        else
            $display("tb_debug: PASS");

        #20;
        $finish;
    end

    // Continuous mismatch detector (fires when o_done rises with wrong ciphertext)
    always @(posedge clk) begin
        if (tb_mismatch && !mismatch_seen) begin
            mismatch_seen = 1'b1;
            $display("First mismatch occurred at time %0t", $time);
            dump_schedule(scenario);
        end
    end
endmodule
