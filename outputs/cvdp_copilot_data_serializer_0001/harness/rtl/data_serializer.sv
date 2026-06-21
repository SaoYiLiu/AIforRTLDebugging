module data_serializer #(
  parameter DATA_W   = 8,
  parameter BIT_ORDER= 0,
  parameter PARITY   = 0
)(
  input                  clk,
  input                  reset,
  // Parallel data interface
  input                  p_valid_i,
  input  [DATA_W-1:0]    p_data_i,
  output                 p_ready_o,
  // Serial data interface
  output                 s_valid_o,
  output                 s_data_o,
  input                  s_ready_i,
  // Transmission enable
  input                  tx_en_i
);

  // Local constants
  localparam ST_RX = 1'b0;
  localparam ST_TX = 1'b1;

  // If PARITY != 0 => We use 1 extra bit for parity
  localparam EXTRA_BIT = (PARITY == 0) ? 0 : 1;
  localparam SHIFT_W   = DATA_W + EXTRA_BIT;

  // Internal regs
  reg                    state_q, state_d;
  reg  [SHIFT_W-1:0]     shift_reg_q, shift_reg_d;
  reg  [$clog2(SHIFT_W)-1:0] count_q, count_d;

  // Parity calculation
  wire parity_bit_even = ^p_data_i;   // XOR => "even"
  wire parity_bit_odd  = ~^p_data_i;  // invert XOR => "odd"

  wire parity_bit = (PARITY == 1) ? parity_bit_even :
                    (PARITY == 2) ? parity_bit_odd  :
                                    1'b0; // NONE

  // Sequential state & register updates
  always @(posedge clk or posedge reset) begin
    if (reset) begin
      state_q     <= ST_RX;
      shift_reg_q <= {SHIFT_W{1'b0}};
      count_q     <= 0;
    end else begin
      state_q     <= state_d;
      shift_reg_q <= shift_reg_d;
      count_q     <= count_d;
    end
  end

  // Next-state logic
  always @* begin
    // Default assignments
    state_d     = state_q;
    shift_reg_d = shift_reg_q;
    count_d     = count_q;

    case (state_q)

      // ST_RX: Load parallel data + parity
      ST_RX: begin
        if (p_valid_i) begin
          if (BIT_ORDER == 0) begin
            // LSB-first => store LSB in shift_reg_d[0]
            if (EXTRA_BIT == 1)
              shift_reg_d = {parity_bit, p_data_i};  // 9 bits if PARITY!=0
            else
              shift_reg_d = p_data_i;                // 8 bits if PARITY=0
          end
          else begin
            // MSB-first => store MSB in shift_reg_d[SHIFT_W-1]
            // Parity appended as LSB when EXTRA_BIT=1
            if (EXTRA_BIT == 1)
              shift_reg_d = {p_data_i, parity_bit};
            else
              shift_reg_d = p_data_i;
          end

          count_d = 0;
          state_d = ST_TX;
        end
      end

      // ST_TX: Shift bits out until SHIFT_W done
      ST_TX: begin
        // Only shift if s_ready_i & tx_en_i
        if (s_ready_i && tx_en_i) begin
          if (count_q == (SHIFT_W - 1)) begin
            // Done sending SHIFT_W bits
            state_d   = ST_RX;
            count_d   = 0;
          end
          else begin
            if (BIT_ORDER == 1) begin
              // MSB-first => shift left by 1
              shift_reg_d = {shift_reg_q[SHIFT_W-2:0], 1'b0};
              count_d     = count_q + 1;
            end
            else begin
              // LSB-first => shift right by 1
              shift_reg_d = {1'b0, shift_reg_q[SHIFT_W-1:1]};
              count_d     = count_q + 1;
            end
          end
        end
      end

      default: begin
        state_d = ST_RX; // safe fallback
      end
    endcase
  end

  // Outputs
  assign s_valid_o = (state_q == ST_TX);

  // LSB-first => s_data_o = shift_reg_q[0]
  // MSB-first => s_data_o = shift_reg_q[SHIFT_W-1]
  assign s_data_o  = (BIT_ORDER == 0) ? shift_reg_q[0] : shift_reg_q[SHIFT_W-1];

  assign p_ready_o = (state_q == ST_RX);

endmodule
