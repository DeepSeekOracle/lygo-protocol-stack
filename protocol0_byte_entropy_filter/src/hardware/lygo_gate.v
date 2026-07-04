// LYGO P0 Nano Gate — compact Verilog ROM decision (Q16.16 risk compare)
// risk thresholds: >=0.70 QUARANTINE, >=0.45 SOFTEN, else AMPLIFY
// size > MAX_BYTES => QUARANTINE

module lygo_gate #(
    parameter MAX_BYTES = 8192
) (
    input  wire        clk,
    input  wire        valid_in,
    input  wire [15:0] size_in,
    input  wire [15:0] risk_q16,  // risk * 65536
    output reg  [1:0]  verdict_out, // 0=AMPLIFY 1=SOFTEN 2=QUARANTINE
    output reg         valid_out
);
    localparam [15:0] RISK_SOFTEN_Q16 = 16'd29491;   // 0.45 * 65536
    localparam [15:0] RISK_QUAR_Q16   = 16'd45875;   // 0.70 * 65536

    always @(posedge clk) begin
        valid_out <= 1'b0;
        if (valid_in) begin
            valid_out <= 1'b1;
            if (size_in > MAX_BYTES[15:0]) begin
                verdict_out <= 2'd2;
            end else if (risk_q16 >= RISK_QUAR_Q16) begin
                verdict_out <= 2'd2;
            end else if (risk_q16 >= RISK_SOFTEN_Q16) begin
                verdict_out <= 2'd1;
            end else begin
                verdict_out <= 2'd0;
            end
        end
    end
endmodule