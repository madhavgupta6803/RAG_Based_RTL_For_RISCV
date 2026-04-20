// Pattern: Pipeline register with synchronous reset and stall/flush control
module pipeline_reg #(parameter W = 32) (
    input              clk,
    input              rst,
    input              stall,
    input              flush,
    input      [W-1:0] d,
    output reg [W-1:0] q
);
    always @(posedge clk) begin
        if (rst || flush)
            q <= {W{1'b0}};
        else if (!stall)
            q <= d;
    end
endmodule
