`timescale 1ns/1ns

module tb_debug;
    logic        clk;
    logic        rst_async_n;
    logic        i_update_key;
    logic [127:0] i_key;
    logic        i_start;
    logic [127:0] i_data;
    logic        o_done;
    logic [127:0] o_data;

    // Reference ciphertexts (PyCryptodome / NIST)
    localparam [127:0] NIST_KEY  = 128'h000102030405060708090a0b0c0d0e0f;
    localparam [127:0] NIST_DATA = 128'h00112233445566778899aabbccddeeff;
    localparam [127:0] NIST_EXP  = 128'h69c4e0d86a7b0430d8cdb78070b4c55a;

    // cocotb seed 1782031507, reset i=0, run j=0 (update_key=1)
    localparam [127:0] CVDP_KEY  = 128'h0a237449137cbcdd69133763c1271fc1;
    localparam [127:0] CVDP_DATA = 128'h2d4eeb9aa7831482cb47430c197ab9f9;
    localparam [127:0] CVDP_EXP  = 128'h5e02dca5cab206192f61a8467073de64;

    logic [127:0] exp_data;
    logic         check_en;
    logic         saw_busy;
    logic         tb_mismatch;
    integer       scenario;

    aes128_encrypt dut (
        .clk          (clk),
        .rst_async_n  (rst_async_n),
        .i_update_key (i_update_key),
        .i_key        (i_key),
        .i_start      (i_start),
        .i_data       (i_data),
        .o_done       (o_done),
        .o_data       (o_data)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_debug);
    end

    task automatic pulse_reset;
        begin
            i_start      = 1'b0;
            i_update_key = 1'b0;
            i_key        = '0;
            i_data       = '0;
            rst_async_n  = 1'b0;
            @(posedge clk);
            rst_async_n  = 1'b1;
            @(posedge clk);
        end
    endtask

    // Mirrors cocotb: assert start/update for one cycle, deassert, wait for o_done
    task automatic run_encrypt(
        input logic        update_key,
        input logic [127:0] key,
        input logic [127:0] data,
        input logic [127:0] expected
    );
        begin
            check_en  = 1'b0;
            saw_busy  = 1'b0;
            exp_data  = expected;

            i_update_key = update_key;
            i_key        = key;
            i_data       = data;
            i_start      = 1'b1;

            $display("[%0t] scenario=%0d start key=%h data=%h update_key=%b",
                     $time, scenario, key, data, update_key);

            @(posedge clk);
            i_start      = 1'b0;
            i_update_key = 1'b0;
            i_key        = '0;
            i_data       = '0;

            @(posedge clk);
            check_en = 1'b1;

            while (!o_done) begin
                saw_busy = 1'b1;
                @(posedge clk);
            end

            $display("[%0t] scenario=%0d done round_ff=%0d o_data=%h expected=%h",
                     $time, scenario, dut.round_ff, o_data, expected);

            if (o_data !== expected) begin
                $display("First mismatch occurred at time %0t", $time);
                $display("  scenario=%0d o_data=%h expected=%h", scenario, o_data, expected);
                $display("  round_ff=%0d expanded_key_msb=%h rk_source_msb=%h",
                         dut.round_ff,
                         dut.expanded_key_ff[1407:1280],
                         dut.rk_source[1407:1280]);
            end

            check_en = 1'b0;
            saw_busy = 1'b0;
            scenario = scenario + 1;
            repeat (2) @(posedge clk);
        end
    endtask

    assign tb_mismatch = check_en && o_done && saw_busy && (o_data !== exp_data);

    always @(posedge clk) begin
        if (tb_mismatch)
            $display("tb_mismatch flagged at time %0t (scenario=%0d)", $time, scenario);
        if (check_en && !o_done)
            $display("[%0t] busy round_ff=%0d", $time, dut.round_ff);
    end

    initial begin
        scenario     = 0;
        check_en     = 1'b0;
        saw_busy     = 1'b0;
        exp_data     = '0;
        tb_mismatch  = 1'b0;

        pulse_reset();

        // Deterministic sanity vector
        run_encrypt(1'b1, NIST_KEY, NIST_DATA, NIST_EXP);

        // cocotb-equivalent first randomized case (seed 1782031507)
        pulse_reset();
        run_encrypt(1'b1, CVDP_KEY, CVDP_DATA, CVDP_EXP);

        if (tb_mismatch)
            $display("DEBUG FAIL: mismatch observed");
        else
            $display("DEBUG PASS: both scenarios matched expected ciphertext");

        #50;
        $finish;
    end
endmodule
