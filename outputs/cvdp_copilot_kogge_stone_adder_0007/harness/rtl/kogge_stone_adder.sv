module kogge_stone_adder (
    input logic clk,
    input logic reset,
    input logic [15:0] A,
    input logic [15:0] B,
    input logic start,
    output logic [16:0] Sum,
    output logic done
);

    logic [15:0] G0, G1, G2, G3, G4;
    logic [15:0] P0, P1, P2, P3, P4;
    logic [16:0] carry;
    logic [16:0] sum_comb;
    logic [3:0] stage;
    logic active;

    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            Sum <= 0;
            done <= 0;
            active <= 0;
            stage <= 0;
        end else if (start && !active) begin
            active <= 1;
            stage <= 0;
            done <= 0;
            Sum <= 0;
        end else if (active) begin
            if (stage == 4) begin
                Sum <= sum_comb;
                done <= 1;
                active <= 0;
            end else begin
                stage <= stage + 1;
            end
        end else if (!start) begin
            done <= 0;
        end
    end

    always_comb begin
        G1 = 0; G2 = 0; G3 = 0; G4 = 0;
        P1 = 0; P2 = 0; P3 = 0; P4 = 0;
        carry = 0;
        sum_comb = 0;

        for (int i = 0; i < 16; i++) begin
            G0[i] = A[i] & B[i];
            P0[i] = A[i] ^ B[i];
        end

        if (stage >= 0) begin
            for (int i = 0; i < 16; i++) begin
                if (i >= 1) begin
                    G1[i] = G0[i] | (P0[i] & G0[i - 1]);
                    P1[i] = P0[i] & P0[i - 1];
                end else begin
                    G1[i] = G0[i];
                    P1[i] = P0[i];
                end
            end
        end

        if (stage >= 1) begin
            for (int i = 0; i < 16; i++) begin
                if (i >= 2) begin
                    G2[i] = G1[i] | (P1[i] & G1[i - 2]);
                    P2[i] = P1[i] & P1[i - 2];
                end else begin
                    G2[i] = G1[i];
                    P2[i] = P1[i];
                end
            end
        end

        if (stage >= 2) begin
            for (int i = 0; i < 16; i++) begin
                if (i >= 4) begin
                    G3[i] = G2[i] | (P2[i] & G2[i - 4]);
                    P3[i] = P2[i] & P2[i - 4];
                end else begin
                    G3[i] = G2[i];
                    P3[i] = P2[i];
                end
            end
        end

        if (stage >= 3) begin
            for (int i = 0; i < 16; i++) begin
                if (i >= 8) begin
                    G4[i] = G3[i] | (P3[i] & G3[i - 8]);
                    P4[i] = P3[i] & P3[i - 8];
                end else begin
                    G4[i] = G3[i];
                    P4[i] = P3[i];
                end
            end

            carry[0] = 0;
            for (int i = 1; i <= 16; i++) begin
                carry[i] = G4[i - 1] | (P4[i - 1] & carry[i - 1]);
            end

            for (int i = 0; i < 16; i++) begin
                sum_comb[i] = P0[i] ^ carry[i];
            end
            sum_comb[16] = carry[16];
        end
    end
endmodule
