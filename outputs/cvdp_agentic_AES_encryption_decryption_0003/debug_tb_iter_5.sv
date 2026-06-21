`timescale 1ns/1ns

module tb_debug;

    localparam integer CLK_PERIOD = 10;

    // NIST AES-128 ECB vector (deterministic baseline)
    localparam [127:0] NIST_KEY  = 128'h000102030405060708090a0b0c0d0e0f;
    localparam [127:0] NIST_DATA = 128'h00112233445566778899aabbccddeeff;
    localparam [127:0] NIST_EXP  = 128'h69c4e0d86a7b0430d8cdb78070b4c55a;

    // Harness-reported model output at 140 ns (first failure in log)
    localparam [127:0] HARNESS_EXP = 128'h1bb6a8ea67cb82d145ef1c4be0f926a8;

    // Set these from cocotb by printing key/data on the failing iteration, then re-run.
    // Until then, scenario 1 only checks protocol/timing and dumps waves.
    localparam [127:0] HARNESS_KEY  = 128'h0;
    localparam [127:0] HARNESS_DATA = 128'h0;
    localparam bit     HARNESS_CHECK = 1'b0;

    logic                clk;
    logic                rst_async_n;
    logic                i_update_key;
    logic [127:0]        i_key;
    logic                i_start;
    logic [127:0]        i_data;
    logic                o_done;
    logic [127:0]        o_data;

    logic                check_en;
    logic [127:0]        expected;
    logic                tb_mismatch;
    integer              scenario;
    time                 mismatch_time;

    aes128_encrypt dut (
        .clk         (clk),
        .rst_async_n (rst_async_n),
        .i_update_key(i_update_key),
        .i_key       (i_key),
        .i_start     (i_start),
        .i_data      (i_data),
        .o_done      (o_done),
        .o_data      (o_data)
    );

    assign tb_mismatch = check_en && (o_data !== expected);

    always #(CLK_PERIOD/2) clk = ~clk;

    task automatic reset_dut();
        i_start      = 1'b0;
        i_update_key = 1'b0;
        i_key        = '0;
        i_data       = '0;
        rst_async_n  = 1'b0;
        @(posedge clk);
        rst_async_n  = 1'b1;
        @(posedge clk);
    endtask

    task automatic wait_done();
        while (o_done !== 1'b1) begin
            @(posedge clk);
        end
    endtask

    task automatic run_encrypt(
        input logic        update_key,
        input logic [127:0] key,
        input logic [127:0] data
    );
        i_update_key = update_key;
        i_key        = key;
        i_data       = data;
        i_start      = 1'b1;
        @(posedge clk);

        i_start      = 1'b0;
        i_key        = '0;
        i_update_key = 1'b0;
        i_data       = '0;
        @(posedge clk);

        wait_done();
    endtask

    initial begin
        clk         = 1'b0;
        rst_async_n = 1'b0;
        check_en    = 1'b0;
        scenario    = -1;
        mismatch_time = 0;

        $dumpfile("wave.vcd");
        $dumpvars(0, tb_debug);

        // Scenario 0: NIST vector, mirrors cocotb first run (update_key=1)
        scenario = 0;
        reset_dut();
        expected = NIST_EXP;
        check_en = 1'b1;

        $display("[%0t] scenario=%0d start key=%h data=%h update_key=1",
                 $time, scenario, NIST_KEY, NIST_DATA);

        run_encrypt(1'b1, NIST_KEY, NIST_DATA);

        if (tb_mismatch) begin
            mismatch_time = $time;
            $display("tb_mismatch flagged at time %0t (scenario=%0d)", mismatch_time, scenario);
            $display("First mismatch occurred at time %0t", mismatch_time);
            $display("  scenario=%0d o_data=%h expected=%h", scenario, o_data, expected);
            $display("  round_ff=%0d o_done=%b", dut.round_ff, o_done);
            $display("  rk0=%h rk_src0=%h ff_msb=%h comp_msb=%h",
                     dut.expanded_key_ff[1407:1280],
                     dut.rk_source[1407:1280],
                     dut.expanded_key_ff[1407:1280],
                     dut.expanded_key_computed[1407:1280]);
        end else begin
            $display("[%0t] scenario=%0d PASS o_data=%h", $time, scenario, o_data);
        end

        check_en = 1'b0;
        @(posedge clk);

        // Scenario 1: cocotb harness expected output (enable after setting KEY/DATA)
        if (HARNESS_CHECK) begin
            scenario = 1;
            reset_dut();
            expected = HARNESS_EXP;
            check_en = 1'b1;

            $display("[%0t] scenario=%0d start key=%h data=%h update_key=1",
                     $time, scenario, HARNESS_KEY, HARNESS_DATA);

            run_encrypt(1'b1, HARNESS_KEY, HARNESS_DATA);

            if (tb_mismatch) begin
                mismatch_time = $time;
                $display("tb_mismatch flagged at time %0t (scenario=%0d)", mismatch_time, scenario);
                $display("First mismatch occurred at time %0t", mismatch_time);
                $display("  scenario=%0d o_data=%h expected=%h", scenario, o_data, expected);
                $display("  round_ff=%0d o_done=%b", dut.round_ff, o_done);
                $display("  rk0=%h rk_src0=%h",
                         dut.expanded_key_ff[1407:1280],
                         dut.rk_source[1407:1280]);
            end else begin
                $display("[%0t] scenario=%0d PASS o_data=%h", $time, scenario, o_data);
            end
        end else begin
            $display("scenario=1 skipped (set HARNESS_KEY/DATA and HARNESS_CHECK=1 after cocotb print)");
        end

        // Per-cycle visibility during a replay (helps isolate round where state diverges)
        scenario = 2;
        reset_dut();
        expected = NIST_EXP;
        check_en = 1'b0;

        i_update_key = 1'b1;
        i_key        = NIST_KEY;
        i_data       = NIST_DATA;
        i_start      = 1'b1;
        @(posedge clk);

        i_start      = 1'b0;
        i_key        = '0;
        i_update_key = 1'b0;
        i_data       = '0;

        while (o_done !== 1'b1) begin
            @(posedge clk);
            $display("[%0t] busy round_ff=%0d rk_msb=%h ff_msb=%h nx_msb=%h",
                     $time,
                     dut.round_ff,
                     dut.rk_source[127:0],
                     dut.expanded_key_ff[127:0],
                     dut.expanded_key_nx[127:0]);
        end

        check_en = 1'b1;
        @(posedge clk);
        if (tb_mismatch) begin
            mismatch_time = $time;
            $display("tb_mismatch flagged at time %0t (scenario=%0d)", mismatch_time, scenario);
            $display("First mismatch occurred at time %0t", mismatch_time);
            $display("  scenario=%0d o_data=%h expected=%h", scenario, o_data, expected);
        end

        #20;
        $finish;
    end

endmodule
