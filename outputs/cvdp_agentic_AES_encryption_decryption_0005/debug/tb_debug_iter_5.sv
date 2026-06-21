`timescale 1ns / 1ns

module tb_debug;
    localparam NBW = 128;

    reg                 clk;
    reg                 rst_async_n;
    reg                 i_update_key;
    reg  [NBW-1:0]      i_key;
    reg                 i_start;
    reg  [NBW-1:0]      i_data;
    wire                o_done;
    wire [NBW-1:0]      o_data;

    // Mirrors harness failure message (model golden plaintext after decrypt)
    localparam [NBW-1:0] EXP_PT = 128'h64d81aebd4309a19b7bbb1b5cbd9feda;

    // Deterministic Run-0 vector: key update + decrypt(CT) -> EXP_PT (OpenSSL AES-128-ECB)
    localparam [NBW-1:0] RUN0_KEY = 128'h001122334455667788990aabbccddeeff;
    localparam [NBW-1:0] RUN0_CT  = 128'h4e3036ee09c58e5376c4b58665e82e66;

    // From harness log: DUT produced this wrong value at ~240 ns (Run 0 compare)
    localparam [NBW-1:0] HARNESS_DUT_ACTUAL = 128'h0ea910e6fe32f7e3405239c6193bc;

    reg        check_enable;
    reg        mismatch_reported;
    wire       tb_mismatch;

    aes128_decrypt dut (
        .clk           (clk),
        .rst_async_n   (rst_async_n),
        .i_update_key  (i_update_key),
        .i_key         (i_key),
        .i_start       (i_start),
        .i_data        (i_data),
        .o_done        (o_done),
        .o_data        (o_data)
    );

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_debug);
    end

    initial clk = 1'b0;
    always #5 clk = ~clk;  // 10 ns period, same as cocotb Clock(10, unit="ns")

    assign tb_mismatch = check_enable && o_done && (o_data !== EXP_PT);

    always @(posedge clk) begin
        if (tb_mismatch && !mismatch_reported) begin
            $display("First mismatch occurred at time %0t", $time);
            $display("  expected (model) = 0x%0h", EXP_PT);
            $display("  actual   (DUT)   = 0x%0h", o_data);
            $display("  harness DUT snap  = 0x%0h", HARNESS_DUT_ACTUAL);
            mismatch_reported <= 1'b1;
        end
    end

    initial begin
        check_enable      = 1'b0;
        mismatch_reported = 1'b0;
        i_update_key      = 1'b0;
        i_key             = {NBW{1'b0}};
        i_start           = 1'b0;
        i_data            = {NBW{1'b0}};
        rst_async_n       = 1'b0;

        // cocotb-style reset pulse
        @(posedge clk);
        rst_async_n = 1'b1;
        @(posedge clk);

        // Post-reset sanity (matches compare_values right after model.reset())
        check_enable = 1'b1;
        if (o_done && (o_data !== {NBW{1'b0}})) begin
            $display("Post-reset mismatch at time %0t: o_data=0x%0h", $time, o_data);
        end

        // Reset 0, Run 0: update_key=1, i_start=1 (same protocol as failing cocotb loop)
        i_key         = RUN0_KEY;
        i_data        = RUN0_CT;
        i_update_key  = 1'b1;
        i_start       = 1'b1;

        @(posedge clk);          // sample start
        i_update_key  = 1'b0;
        i_start       = 1'b0;
        i_key         = {NBW{1'b0}};
        i_data        = {NBW{1'b0}};

        @(posedge clk);
        while (!o_done)
            @(posedge clk);

        // Harness compare_values() equivalent
        if (o_data !== EXP_PT) begin
            $display("[ERROR] DUT o_data does not match model o_data: 0x%0h != 0x%0h at time %0t",
                     o_data, EXP_PT, $time);
        end else begin
            $display("PASS: decrypt completed correctly at time %0t", $time);
        end

        #50;
        $finish;
    end
endmodule
