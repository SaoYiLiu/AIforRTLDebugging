module signed_sequential_booth_multiplier #(parameter WIDTH = 8) (
    input  wire signed [WIDTH-1:0] A,
    input  wire signed [WIDTH-1:0] B,
    input  wire clk,
    input  wire rst,
    input  wire start,
    output reg  signed [2*WIDTH-1:0] result,
    output reg done
);

    // FSM states
    typedef enum logic [2:0] {
        IDLE     = 3'b000,
        ENCODE   = 3'b001, 
        PARTIAL  = 3'b010, 
        ADDITION = 3'b011, 
        DONE     = 3'b100
    } state_t;

    state_t state, next_state;

    // Registers for control and data signals
    reg signed [2*WIDTH-1:0] partial_products [0:WIDTH/2-1];
    reg signed [2*WIDTH-1:0] multiplicand;
    reg signed [WIDTH:0] booth_bits; 
    reg signed [2*WIDTH-1:0] accumulator;  
    reg [2:0] encoding_bits [0:WIDTH/2-1];
    reg [$clog2(WIDTH/2):0] addition_counter; // Counter for addition cycles
    integer i;

    // State machine: Sequential process for state transitions
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= IDLE;
        end else begin
            state <= next_state;
        end
    end

    // State machine: Combinational process for next-state logic
    always @(*) begin
        case (state)
            IDLE: begin
                if (start) begin
                    next_state = ENCODE;
                end else begin
                    next_state = IDLE;
                end
            end

            ENCODE: begin
                next_state = PARTIAL;
            end

            PARTIAL: begin
                next_state = ADDITION;
            end

            ADDITION: begin
                if (addition_counter == WIDTH/2 - 1) begin
                    next_state = DONE;
                end else begin
                    next_state = ADDITION;
                end
            end

            DONE: begin
                if (!start) begin
                    next_state = IDLE;
                end else begin
                    next_state = DONE;
                end
            end

            default: begin
                next_state = IDLE;
            end
        endcase
    end

    // Signal assignments: Perform operations based on current state
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            done <= 0;
            result <= 0;
            accumulator <= 0;
            addition_counter <= 0;
            multiplicand <= 0;
            booth_bits <= 0;
            for (i = 0; i < WIDTH/2; i = i + 1) begin
                encoding_bits[i] <= 0;
                partial_products[i] <= 0;
            end
        end else begin
            case (state)
                IDLE: begin
                    // Prepare for new computation
                    done <= 0;
                    result <= 0;
                    if (start) begin
                        multiplicand <= {{(WIDTH){A[WIDTH-1]}}, A}; // Sign-extend A
                        booth_bits <= {B, 1'b0};
                        accumulator <= 0;
                        addition_counter <= 0;
                        for (i = 0; i < WIDTH/2; i = i + 1) begin
                            partial_products[i] <= 0;
                        end
                    end
                end

                ENCODE: begin
                    // Extract 3-bit Booth segments
                    for (i = 0; i < WIDTH/2; i = i + 1) begin
                        encoding_bits[i] <= booth_bits[2*i +: 3];
                    end
                end

                PARTIAL: begin
                    // Generate partial products based on Booth encoding
                    for (i = 0; i < WIDTH/2; i = i + 1) begin
                        case (encoding_bits[i])
                            3'b001, 3'b010: partial_products[i] <= (multiplicand << (2 * i));
                            3'b011:         partial_products[i] <= ((multiplicand << 1) << (2 * i));
                            3'b100:         partial_products[i] <= -((multiplicand << 1) << (2 * i));
                            3'b101, 3'b110: partial_products[i] <= -(multiplicand << (2 * i));
                            default:        partial_products[i] <= 0;
                        endcase
                    end
                end

                ADDITION: begin
                    accumulator <= accumulator + partial_products[addition_counter];
                    if (addition_counter < WIDTH/2 - 1) begin
                        addition_counter <= addition_counter + 1;
                    end
                end

                DONE: begin
                    // Output the result
                    result <= accumulator;
                    done <= 1;
                end
            endcase
        end
    end
endmodule
