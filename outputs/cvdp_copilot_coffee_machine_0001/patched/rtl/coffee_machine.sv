module coffee_machine #(
    parameter NBW_DLY    = 'd5,
    parameter NBW_BEANS  = 'd2,
    parameter NS_BEANS   = 'd4,
    parameter NS_OP      = 'd3, // Fixed
    parameter NS_SENSOR  = 'd4  // Fixed
) (
    input  logic                 clk,
    input  logic                 rst_async_n,
    input  logic [NBW_DLY-1:0]   i_grind_delay,
    input  logic [NBW_DLY-1:0]   i_heat_delay,
    input  logic [NBW_DLY-1:0]   i_pour_delay,
    input  logic [NBW_BEANS-1:0] i_bean_sel,
    input  logic [NS_OP-1:0]     i_operation_sel,
    input  logic                 i_start,
    input  logic [NS_SENSOR-1:0] i_sensor,
    output logic [NS_BEANS-1:0]  o_bean_sel,
    output logic                 o_grind_beans,
    output logic                 o_use_powder,
    output logic                 o_heat_water,
    output logic                 o_pour_coffee,
    output logic                 o_error
);

// Fixed delays (bean selection and powder usage)
localparam SEL_CYCLES    = 'd3;
localparam POWDER_CYCLES = 'd2;

typedef enum logic [2:0] {
    IDLE     = 3'b000,
    BEAN_SEL = 3'b001,
    GRIND    = 3'b011,
    POWDER   = 3'b111,
    HEAT     = 3'b110,
    POUR     = 3'b100
} state_t;

// ----------------------------------------
// - Wires/Registers creation
// ----------------------------------------
state_t state_ff, state_nx;
logic [NBW_DLY:0]     counter_ff, counter_nx;
logic [NBW_DLY-1:0]   grind_delay_ff, heat_delay_ff, pour_delay_ff;
logic [NS_OP-1:0]     operation_sel_ff;
logic [NBW_BEANS-1:0] bean_sel_in_ff;
logic                 start_ff;

logic idle_error;
assign idle_error = (i_sensor[0] | i_sensor[3])
                  | (&i_operation_sel[2:1])
                  | (i_operation_sel[1] & i_sensor[1])
                  | (((i_operation_sel == 3'b001) || (i_operation_sel == 3'b100)) & i_sensor[2]);

// Output assignment (error conditions)
always_comb begin : error_logic
    if(state_ff == IDLE) begin
        o_error = idle_error;
    end else begin
        o_error = i_sensor[3];
    end
end

// ----------------------------------------
// - Registers
// ----------------------------------------
always_ff @(posedge clk) begin : data_regs
    start_ff <= i_start & ~idle_error;

    if(i_start && state_ff == IDLE) begin
        operation_sel_ff <= i_operation_sel;
        grind_delay_ff   <= i_grind_delay;
        heat_delay_ff    <= i_heat_delay;
        pour_delay_ff    <= i_pour_delay;
        bean_sel_in_ff   <= i_bean_sel;
    end

    counter_ff <= counter_nx;
end

always_ff @(posedge clk or negedge rst_async_n) begin : reset_regs
    if(~rst_async_n) begin
        state_ff <= IDLE;
    end else begin
        state_ff <= state_nx;
    end
end

// ----------------------------------------
// - FSM update
// ----------------------------------------
always_comb begin
    if(i_sensor[3]) begin
        counter_nx = 0;
        state_nx   = IDLE;
    end else begin
        case(state_ff)
            IDLE: begin
                counter_nx = 0;

                if(start_ff) begin
                    if(~(|operation_sel_ff[2:1])) begin
                        state_nx = HEAT;
                    end else if(operation_sel_ff[1]) begin
                        state_nx = BEAN_SEL;
                    end else if(operation_sel_ff[0]) begin
                        state_nx = POUR;
                    end else begin
                        state_nx = POWDER;
                    end
                end else begin
                    state_nx = IDLE;
                end
            end
            BEAN_SEL: begin
                if(counter_ff >= (SEL_CYCLES - 1'b1)) begin
                    counter_nx = 0;
                    state_nx   = GRIND;
                end else begin
                    counter_nx = counter_ff + 1'b1;
                    state_nx   = BEAN_SEL;
                end
            end
            GRIND: begin
                if(counter_ff >= (grind_delay_ff - 1'b1)) begin
                    counter_nx = 0;
                    if(operation_sel_ff[0]) begin
                        state_nx = POWDER;
                    end else begin
                        state_nx = HEAT;
                    end
                end else begin
                    counter_nx = counter_ff + 1'b1;
                    state_nx   = GRIND;
                end
            end
            POWDER: begin
                if(counter_ff >= (POWDER_CYCLES - 1'b1)) begin
                    counter_nx = 0;
                    state_nx   = POUR;
                end else begin
                    counter_nx = counter_ff + 1'b1;
                    state_nx   = POWDER;
                end
            end
            HEAT: begin
                if(counter_ff >= (heat_delay_ff - 1'b1)) begin
                    counter_nx = 0;
                    if(|operation_sel_ff[1:0]) begin
                        state_nx = POWDER;
                    end else begin
                        state_nx = POUR;
                    end
                end else begin
                    counter_nx = counter_ff + 1'b1;
                    state_nx   = HEAT;
                end
            end
            POUR: begin
                if(counter_ff >= (pour_delay_ff - 1'b1)) begin
                    counter_nx = 0;
                    state_nx   = IDLE;
                end else begin
                    counter_nx = counter_ff + 1'b1;
                    state_nx   = POUR;
                end
            end
            default: begin
                counter_nx = 0;
                state_nx   = IDLE;
            end
        endcase
    end
end

// ----------------------------------------
// - Controller outputs
// ----------------------------------------
always_comb begin
    case(state_ff)
        IDLE: begin
            o_bean_sel      = {NS_BEANS{1'b0}};
            o_use_powder    = 1'b0;
            o_grind_beans   = 1'b0;
            o_heat_water    = 1'b0;
            o_pour_coffee   = 1'b0;
        end
        BEAN_SEL: begin
            o_bean_sel                      = {NS_BEANS{1'b0}};
            o_bean_sel[bean_sel_in_ff]      = 1'b1;
            o_grind_beans                   = 1'b0;
            o_use_powder                    = 1'b0;
            o_heat_water                    = 1'b0;
            o_pour_coffee                   = 1'b0;
        end
        GRIND: begin
            o_bean_sel                      = {NS_BEANS{1'b0}};
            o_bean_sel[bean_sel_in_ff]      = 1'b1;
            o_grind_beans                   = 1'b1;
            o_use_powder                    = 1'b0;
            o_heat_water                    = 1'b0;
            o_pour_coffee                   = 1'b0;
        end
        POWDER: begin
            o_bean_sel      = {NS_BEANS{1'b0}};
            o_grind_beans   = 1'b0;
            o_use_powder    = 1'b1;
            o_heat_water    = 1'b0;
            o_pour_coffee   = 1'b0;
        end
        HEAT: begin
            o_bean_sel      = {NS_BEANS{1'b0}};
            o_grind_beans   = 1'b0;
            o_use_powder    = 1'b0;
            o_heat_water    = 1'b1;
            o_pour_coffee   = 1'b0;
        end
        POUR: begin
            o_bean_sel      = {NS_BEANS{1'b0}};
            o_grind_beans   = 1'b0;
            o_use_powder    = 1'b0;
            o_heat_water    = 1'b0;
            o_pour_coffee   = 1'b1;
        end
        default: begin
            o_bean_sel      = {NS_BEANS{1'b0}};
            o_grind_beans   = 1'b0;
            o_use_powder    = 1'b0;
            o_heat_water    = 1'b0;
            o_pour_coffee   = 1'b0;
        end
    endcase
end

endmodule : coffee_machine
