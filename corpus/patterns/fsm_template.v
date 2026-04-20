// Pattern: Two-process FSM (state register + next-state logic)
module fsm_template (
    input  clk,
    input  rst,
    input  start,
    input  done,
    output reg busy
);
    localparam IDLE = 2'd0, RUN = 2'd1, WAIT = 2'd2;
    reg [1:0] state, next_state;

    // State register
    always @(posedge clk) begin
        if (rst) state <= IDLE;
        else     state <= next_state;
    end

    // Next-state logic
    always @* begin
        next_state = state;   // default: stay
        case (state)
            IDLE: if (start) next_state = RUN;
            RUN:  if (done)  next_state = WAIT;
            WAIT: next_state = IDLE;
        endcase
    end

    // Output logic
    always @* begin
        busy = (state != IDLE);
    end
endmodule
