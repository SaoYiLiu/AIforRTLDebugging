module morse_encoder (
    input wire [7:0] ascii_in,       // ASCII input character
    output reg [5:0] morse_out,      // Morse code output (6 bits max for each letter)
    output reg [3:0] morse_length    // Length of the Morse code sequence
);

    always @(*) begin
        case (ascii_in)
            8'h41: begin morse_out = 6'b100;      morse_length = 3; end  // A: .-
            8'h42: begin morse_out = 6'b1000;     morse_length = 4; end  // B: -...
            8'h43: begin morse_out = 6'b1010;     morse_length = 4; end  // C: -.-.
            8'h44: begin morse_out = 6'b100;      morse_length = 3; end  // D: -..
            8'h45: begin morse_out = 6'b1;        morse_length = 3; end  // E: .
            8'h46: begin morse_out = 6'b0010;     morse_length = 4; end  // F: ..-.
            8'h47: begin morse_out = 6'b110;      morse_length = 3; end  // G: --.
            8'h48: begin morse_out = 6'b0000;     morse_length = 4; end  // H: ....
            8'h49: begin morse_out = 6'b00;       morse_length = 2; end  // I: ..
            8'h4A: begin morse_out = 6'b0111;     morse_length = 4; end  // J: .---
            8'h4B: begin morse_out = 6'b101;      morse_length = 3; end  // K: -.-
            8'h4C: begin morse_out = 6'b01;       morse_length = 2; end  // L: .-..
            8'h4D: begin morse_out = 6'b11;       morse_length = 2; end  // M: --
            8'h4E: begin morse_out = 6'b10;       morse_length = 2; end  // N: -.
            8'h4F: begin morse_out = 6'b111;      morse_length = 3; end  // O: ---
            8'h50: begin morse_out = 6'b0110;     morse_length = 4; end  // P: .--.
            8'h51: begin morse_out = 6'b1101;     morse_length = 4; end  // Q: --.-
            8'h52: begin morse_out = 6'b010;      morse_length = 3; end  // R: .-.
            8'h53: begin morse_out = 6'b000;      morse_length = 3; end  // S: ...
            8'h54: begin morse_out = 6'b1;        morse_length = 1; end  // T: -
            8'h55: begin morse_out = 6'b001;      morse_length = 3; end  // U: ..-
            8'h56: begin morse_out = 6'b0001;     morse_length = 4; end  // V: ...-
            8'h57: begin morse_out = 6'b011;      morse_length = 3; end  // W: .--
            8'h58: begin morse_out = 6'b1001;     morse_length = 4; end  // X: -..-
            8'h59: begin morse_out = 6'b1011;     morse_length = 4; end  // Y: -.--
            8'h5A: begin morse_out = 6'b1100;     morse_length = 4; end  // Z: --..
            8'h30: begin morse_out = 6'b11111;    morse_length = 5; end  // 0: -----
            8'h31: begin morse_out = 6'b01111;    morse_length = 5; end  // 1: .----
            8'h32: begin morse_out = 6'b00111;    morse_length = 5; end  // 2: ..---
            8'h33: begin morse_out = 6'b00011;    morse_length = 5; end  // 3: ...--
            8'h34: begin morse_out = 6'b00001;    morse_length = 5; end  // 4: ....-
            8'h35: begin morse_out = 6'b00000;    morse_length = 5; end  // 5: .....
            8'h36: begin morse_out = 6'b10000;    morse_length = 5; end  // 6: -....
            8'h37: begin morse_out = 6'b11000;    morse_length = 5; end  // 7: --...
            8'h38: begin morse_out = 6'b11100;    morse_length = 5; end  // 8: ---..
            8'h39: begin morse_out = 6'b11110;    morse_length = 5; end  // 9: ----.
            default: begin
                morse_out = 6'b0;                 
                morse_length = 4'b0;
            end
        endcase
    end

endmodule