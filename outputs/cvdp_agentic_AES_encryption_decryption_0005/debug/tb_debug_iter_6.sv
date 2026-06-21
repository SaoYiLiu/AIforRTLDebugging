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

    // Harness Reset 0 / Run 0 (update_key=1) — model golden plaintext
    localparam [NBW-1:0] EXP_PT = 128'hebdfac91a5133de82760ac889f4a64d7;

    // Cocotb log: "Seeding Python random module with 1782035203"
    //   key  = random.randint(...)  # first call after seed
    //   ct   = random.randint(...)  # second call
    localparam [NBW-1:0] RUN0_KEY = 128'h4c3b2082e7798b9903e752dd34b68442;
    localparam [NBW-1:0] RUN0_CT  = 128'hc2675c4f3e5c1c7d6b7216c23d23d250;

    // Harness-reported DUT output at 240 ns (for reference in waves/display)
    localparam [NBW-1:0] HARNESS_DUT_ACTUAL = 128'h20f710763f6d871fa87bee19396423fd;

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
            $display("  expected (model)  = 0x%0h", EXP_PT);
            $display("  actual   (DUT)    = 0x%0h", o_data);
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

        // cocotb reset pulse
        @(posedge clk);
        rst_async_n = 1'b1;
        @(posedge clk);

        // Reset 0, Run 0: j==0 => update_key=1, i_start=1
        i_key        = RUN0_KEY;
        i_data       = RUN0_CT;
        i_update_key = 1'b1;
        i_start      = 1'b1;
        check_enable = 1'b1;

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
