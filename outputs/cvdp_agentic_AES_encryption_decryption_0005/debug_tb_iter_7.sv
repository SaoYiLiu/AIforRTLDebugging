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

    // Harness Reset 0 / Run 0 — model golden plaintext (exact from failure log)
    localparam [NBW-1:0] EXP_PT = 128'h50aa02fc1efbbd83e14756e3775a0607;

    // Fill from cocotb log line:
    //   "Seeding Python random module with <SEED>"
    // then in Python: random.seed(SEED); key=random.randint(0,2**128-1); ct=random.randint(...)
    // (first two random.randint calls after seed, before Run 0 loop body re-seeds)
    localparam [NBW-1:0] RUN0_KEY = 128'h00000000000000000000000000000000; // <-- replace from seed
    localparam [NBW-1:0] RUN0_CT  = 128'h00000000000000000000000000000000; // <-- replace from seed

    // Harness-reported DUT output at ~240 ns (reference for wave compare)
    localparam [NBW-1:0] HARNESS_DUT_ACTUAL = 128'he8a0e27d28e748ede962064b0b9d03da;

    reg        check_enable;
    reg        mismatch_reported;
    wire       tb_mismatch;

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

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_debug);
    end

    initial clk = 1'b0;
    always #5 clk = ~clk;

    assign tb_mismatch = check_enable && o_done && (o_data !== EXP_PT);

    always @(posedge clk) begin
        if (tb_mismatch && !mismatch_reported) begin
            $display("First mismatch occurred at time %0t", $time);
            $display("  expected (model) = 0x%0h", EXP_PT);
            $display("  actual   (DUT)   = 0x%0h", o_data);
            $display("  harness DUT snap = 0x%0h", HARNESS_DUT_ACTUAL);
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

        // Reset 0, Run 0: j==0 => update_key=1, i_start=1
        i_key        = RUN0_KEY;
        i_data       = RUN0_CT;
        i_update_key = 1'b1;
        i_start      = 1'b1;
        check_enable = 1'b1;

        $display("Run0 key=0x%0h ct=0x%0h", RUN0_KEY, RUN0_CT);

        @(posedge clk);
        i_update_key = 1'b0;
        i_start      = 1'b0;
        i_key        = {NBW{1'b0}};
        i_data       = {NBW{1'b0}};

        @(posedge clk);
        while (!o_done)
            @(posedge clk);

        if (o_data !== EXP_PT)
            $display("[ERROR] DUT o_data does not match model o_data: 0x%0h != 0x%0h at time %0t",
                     o_data, EXP_PT, $time);
        else
            $display("PASS at time %0t", $time);

        #50;
        $finish;
    end
endmodule
