`timescale 1ns/1ps

module lygo_gate_tb;
    reg clk = 0;
    reg valid_in;
    reg [15:0] size_in;
    reg [15:0] risk_q16;
    wire [1:0] verdict_out;
    wire valid_out;

    lygo_gate #(.MAX_BYTES(8192)) uut (
        .clk(clk), .valid_in(valid_in), .size_in(size_in), .risk_q16(risk_q16),
        .verdict_out(verdict_out), .valid_out(valid_out)
    );

    always #5 clk = ~clk;

    initial begin
        valid_in = 0; size_in = 0; risk_q16 = 0;
        #20;
        valid_in = 1; size_in = 100; risk_q16 = 16'd10000; #10; // AMPLIFY
        if (verdict_out !== 2'd0) $display("FAIL low risk");
        valid_in = 1; size_in = 100; risk_q16 = 16'd32000; #10; // SOFTEN
        if (verdict_out !== 2'd1) $display("FAIL soften");
        valid_in = 1; size_in = 100; risk_q16 = 16'd50000; #10; // QUARANTINE
        if (verdict_out !== 2'd2) $display("FAIL quarantine");
        valid_in = 1; size_in = 9000; risk_q16 = 0; #10;
        if (verdict_out !== 2'd2) $display("FAIL oversize");
        $display("lygo_gate_tb done");
        $finish;
    end
endmodule