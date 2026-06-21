module caesar_cipher #(
    parameter PHRASE_WIDTH = 32,  // e.g., enough for 4 chars (4×8=32)
    parameter PHRASE_LEN   = PHRASE_WIDTH / 8
)(
    input  wire [PHRASE_WIDTH-1:0]       input_phrase,
    input  wire [(PHRASE_LEN * 5) - 1:0] key_phrase,
    input  wire                          decrypt,
    output reg  [PHRASE_WIDTH-1:0]       output_phrase
);

    integer i;
    reg [7:0] current_char;
    reg [4:0] current_key;

    always @(*) begin
        // Initialize output to zero
        output_phrase = {PHRASE_WIDTH{1'b0}};

        
        if (PHRASE_LEN > 0) begin
            for (i = 0; i < PHRASE_LEN; i = i + 1) begin
                // Extract current character & key
                current_char = input_phrase[i * 8 +: 8];
                current_key  = key_phrase[i * 5 +: 5];

             
                if (decrypt) begin
                    if (current_char >= "A" && current_char <= "Z") begin
                        output_phrase[i * 8 +: 8]
                            = ((current_char - "A" - current_key + 26) % 26) + "A";
                    end
                    else if (current_char >= "a" && current_char <= "z") begin
                        output_phrase[i * 8 +: 8]
                            = ((current_char - "a" - current_key + 26) % 26) + "a";
                    end
                    else begin
                        output_phrase[i * 8 +: 8] = current_char - current_key;
                    end
                end

                else begin
                    if (current_char >= "A" && current_char <= "Z") begin
                        output_phrase[i * 8 +: 8]
                            = ((current_char - "A" + current_key) % 26) + "A";
                    end
                    else if (current_char >= "a" && current_char <= "z") begin
                        output_phrase[i * 8 +: 8]
                            = ((current_char - "a" + current_key) % 26) + "a";
                    end
                    else begin
                        output_phrase[i * 8 +: 8] = current_char + current_key;
                    end
                end
            end
        end
    end

endmodule
