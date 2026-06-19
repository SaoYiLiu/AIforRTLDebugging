module TopModule(
	input clk,
	input rst_n,
	input data,
	input data_valid,
	output reg match
	);


reg [3:0] pstate,nstate;

parameter idle=4'd0,
		  s1_d0=4'd1,
          s2_d01=4'd2,
          s3_d011=4'd3,
          s4_d0110=4'd4;

always @(posedge clk or negedge rst_n)
begin
    if(!rst_n)
        pstate<=idle;
    else
        pstate<=nstate;
end

always @(pstate or data or data_valid)
begin
    case(pstate)
        idle:
            if(data_valid && !data)
                nstate=s1_d0;
            else
                nstate=idle;
        s1_d0:
            if (data_valid)
				begin	
					if (data) nstate = s2_d01;
					else nstate = s1_d0;
				end
			else nstate = s1_d0;
        s2_d01:
            if (data_valid)
				begin	
					if (data) nstate = s3_d011;
					else nstate = s1_d0;
				end
			else nstate = s2_d01;
        s3_d011:
            if (data_valid)
				begin	
					if (!data) nstate = s4_d0110;
					else nstate = idle;
				end
			else nstate = s3_d011;
        s4_d0110:
            if (data_valid)
				begin	
					if (!data) nstate = s1_d0;
					else nstate = idle;
				end
			else nstate = idle;
        default:
            nstate=idle;
        endcase
end

always @(pstate or rst_n)
begin
    if (!rst_n)
        match = 1'b0;
    else if (pstate == s4_d0110)
        match = 1'b1;
    else
        match = 1'b0;
end

endmodule
