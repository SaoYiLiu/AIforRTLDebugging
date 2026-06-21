module String_to_ASCII_Converter (
    input wire clk,                       // Clock signal
    input wire reset,                     // Reset signal
    input wire start,                     // Start conversion
    input wire [7:0] char_in [7:0],       // 8-character input string (7 bits per character: 0-95)
    output reg [7:0] ascii_out [7:0],    // 8-character ASCII output
    output reg valid,                     // Indicates valid output
    output reg ready                      // Indicates module ready to accept input
);
    // Parameters for character type identification
    localparam DIGIT   = 2'd0;
    localparam UPPER   = 2'd1;
    localparam LOWER   = 2'd2;
    localparam SPECIAL = 2'd3;

    // ASCII Offsets
    localparam DIGIT_OFFSET   = 8'd48;    // '0' = 48
    localparam UPPER_OFFSET   = 8'd65;    // 'A' = 65
    localparam LOWER_OFFSET   = 8'd97;    // 'a' = 97
    localparam SPECIAL_OFFSET = 8'd33;    // First special character '!' = 33

    integer i;

    // Function to determine character type
    function [1:0] determine_char_type;
        input [7:0] char;
        begin
            if (char < 8'd10)
                determine_char_type = DIGIT;    // '0'-'9'
            else if (char < 8'd36)
                determine_char_type = UPPER;    // 'A'-'Z'
            else if (char < 8'd62)
                determine_char_type = LOWER;    // 'a'-'z'
            else
                determine_char_type = SPECIAL;  // Special characters
        end
    endfunction

    // Function to convert encoded character to ASCII
    function [7:0] convert_to_ascii;
        input [7:0] char;
        reg [1:0] char_type;
        begin
            char_type = determine_char_type(char);
            case (char_type)
                DIGIT:   convert_to_ascii = char + DIGIT_OFFSET;
                UPPER:   convert_to_ascii = (char - 8'd10) + UPPER_OFFSET;
                LOWER:   convert_to_ascii = (char - 8'd36) + LOWER_OFFSET;
                SPECIAL: convert_to_ascii = (char - 8'd62) + SPECIAL_OFFSET;
                default: convert_to_ascii = 8'd0;
            endcase
        end
    endfunction

    // Sequential logic
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            for (i = 0; i < 8; i = i + 1)
                ascii_out[i] <= 8'd0;
            valid <= 1'b0;
            ready <= 1'b1;
        end else begin
            if (start && ready) begin
                // Convert all 8 characters in parallel
                for (i = 0; i < 8; i = i + 1)
                    ascii_out[i] <= convert_to_ascii(char_in[i]);
                valid <= 1'b1;
                ready <= 1'b0;
            end else if (!ready) begin
                // Clear outputs and return to idle after one valid cycle
                for (i = 0; i < 8; i = i + 1)
                    ascii_out[i] <= 8'd0;
                valid <= 1'b0;
                ready <= 1'b1;
            end
        end
    end
endmodule
