module TopModule(
	input clk,
	input rst_n,

	output reg [5:0]second,
	output reg [5:0]minute
	);

	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			minute <= 6'd0;
		else if (second == 6'd60)
			minute <= minute + 1'b1;
		else
			minute <= minute;

	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			second <= 6'd0;
		else if (second == 6'd60)
			second <= 6'd1;
		else if (minute == 6'd60)
			second <= second;
		else
			second <= second + 1'b1;

endmodule
