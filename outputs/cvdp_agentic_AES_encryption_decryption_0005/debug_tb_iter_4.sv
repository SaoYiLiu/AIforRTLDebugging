`timescale 1ns/1ps

module tb_debug;

    // -------------------------------------------------------------------------
    // Reset 0 / Run 0 scenario (j==0 => update_key=1)
    // Expected from harness log (latest failure):
    //   0xedb8d013f1f66f3372d9d105136f18f6
    //
    // Set TB_KEY/TB_DATA from cocotb seed printed in the harness log:
    //   "Seeding Python random module with <SEED>"
    // Then run:
    //   python3 -c "import random; random.seed(<SEED>); \
    //     print(hex(random.randint(0,2**128-1))); print(hex(random.randint(0,2**128-1)))"
    // first int = key, second int = ciphertext
    // -------------------------------------------------------------------------
    localparam [127:0] TB_EXPECTED = 128'hedb8d013f1f66f3372d9d105136f18f6;

    // Replace with values from cocotb seed reproduction before expecting PASS
    localparam [127:0] TB_KEY  = 128'h00000000000000000000000000000000;
    localparam [127:0] TB_DATA = 128'h00000000000000000000000000000000;

    reg         clk;
    reg         rst_async_n;
    reg         i_update_key;
    reg         i_start;
    reg [127:0] i_key;
    reg [127:0] i_data;

    wire        o_done;
    wire [127:0] o_data;

    reg         decrypt_busy;
    reg         mismatch_reported;
    reg [3:0]   round_ff_prev;

    wire        tb_mismatch;

    aes128_decrypt dut (
        .clk          (clk),
        .rst_async_n  (rst_async_n),
        .i_update_key (i_update_key),
        .i_key        (i_key),
        .i_data       (i_data),
        .o_done       (o_done),
        .o_data       (o_data)
    );

    // Only flag mismatch when a decrypt operation completes
    assign tb_mismatch = decrypt_busy && o_done && (o_data !== TB_EXPECTED);

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_debug);
    end

    always @(posedge clk) begin
        if (tb_mismatch && !mismatch_reported) begin
            mismatch_reported <= 1'b1;
            $display("First mismatch occurred at time %0t", $time);
            $display("  o_data   = 0x%032h", o_data);
            $display("  expected = 0x%032h", TB_EXPECTED);
        end
    end

    // FSM / key-expansion trace (primary debug value in VCD)
    always @(posedge clk) begin
        if (rst_async_n && dut.round_ff !== round_ff_prev) begin
            $display("t=%0t round_ff %0d -> %0d  key_done=%b  update_key_ff=%b  o_done=%b",
                     $time, round_ff_prev, dut.round_ff,
                     dut.key_done, dut.update_key_ff, o_done);
        end
        if (rst_async_n && dut.key_done && dut.round_ff == 4'd1)
            $display("t=%0t key expansion complete (expanded_key[1407:1280]=0x%032h)",
                     $time, dut.expanded_key[1407:1280]);
        round_ff_prev <= dut.round_ff;
    end

    task drive_idle;
        begin
            i_update_key = 1'b0;
            i_start      = 1'b0;
            i_key        = 128'd0;
            i_data       = 128'd0;
        end
    endtask

    initial begin
        rst_async_n       = 1'b0;
        decrypt_busy      = 1'b0;
        mismatch_reported = 1'b0;
        round_ff_prev     = 4'd0;
        drive_idle();

        // cocotb reset sequence
        @(posedge clk);
        rst_async_n = 1'b1;
        @(posedge clk);

        // Reset 0 / Run 0: key update + decrypt (matches test_aes128_decrypt.py)
        i_key        = TB_KEY;
        i_data       = TB_DATA;
        i_update_key = 1'b1;
        i_start      = 1'b1;
        decrypt_busy = 1'b1;
        @(posedge clk);

        drive_idle();
        @(posedge clk);

        // Wait for decrypt FSM to finish (cocotb: while o_done == 0)
        while (o_done !== 1'b1)
            @(posedge clk);

        if (!mismatch_reported) begin
            if (TB_KEY === 128'd0 && TB_DATA === 128'd0)
                $display("t=%0t INFO: decrypt finished; set TB_KEY/TB_DATA from cocotb seed to compare plaintext", $time);
            else
                $display("t=%0t PASS: o_data matches expected", $time);
        end else begin
            $display("t=%0t FAIL: decrypt completed with wrong plaintext", $time);
        end

        $display("t=%0t FINAL o_data   = 0x%032h", $time, o_data);
        $display("t=%0t FINAL expected = 0x%032h", $time, TB_EXPECTED);

        repeat (4) @(posedge clk);
        $finish;
    end

endmodule
