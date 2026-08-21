/*
 * Copyright (c) 2026 Ashakirana V
 * SPDX-License-Identifier: Apache-2.0
 *
 * UART "Hello" transmitter for Tiny Tapeout TTSKY26c.
 * On a rising edge of ui_in[0], transmits "HI ASHA\n" once
 * at 9600 baud (8N1) on uo_out[0]. uo_out[1] is high while busy.
 */

`default_nettype none

module tt_um_ashakiranav_uart_tx (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // ---------- parameters ----------
  localparam CLK_HZ  = 50_000_000;   // must match info.yaml clock_hz
  localparam BAUD    = 9600;
  localparam DIV     = CLK_HZ / BAUD;  // 5208 clocks per bit
  localparam MSG_LEN = 8;

  // ---------- message ROM ----------
  function [7:0] rom (input [2:0] i);
    case (i)
      3'd0: rom = "H";
      3'd1: rom = "I";
      3'd2: rom = " ";
      3'd3: rom = "A";
      3'd4: rom = "S";
      3'd5: rom = "H";
      3'd6: rom = "A";
      3'd7: rom = 8'h0A;  // newline
    endcase
  endfunction

  // ---------- trigger edge detect ----------
  reg trig_d;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) trig_d <= 1'b0;
    else        trig_d <= ui_in[0];
  end
  wire start_pulse = ui_in[0] & ~trig_d;  // rising edge -> one-cycle pulse

  // ---------- baud tick generator ----------
  reg [12:0] baud_cnt;   // counts 0..DIV-1 (5207 fits in 13 bits)
  reg        baud_tick;
  reg        busy;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      baud_cnt  <= 13'd0;
      baud_tick <= 1'b0;
    end else if (busy) begin
      if (baud_cnt == DIV - 1) begin
        baud_cnt  <= 13'd0;
        baud_tick <= 1'b1;
      end else begin
        baud_cnt  <= baud_cnt + 13'd1;
        baud_tick <= 1'b0;
      end
    end else begin
      baud_cnt  <= 13'd0;
      baud_tick <= 1'b0;
    end
  end

  // ---------- transmit engine ----------
  reg [9:0] shifter;   // {stop, data[7:0], start}
  reg [3:0] bit_cnt;   // 0..9 within a frame
  reg [2:0] char_idx;  // which character of the message
  reg       tx;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      busy     <= 1'b0;
      shifter  <= 10'h3FF;
      bit_cnt  <= 4'd0;
      char_idx <= 3'd0;
      tx       <= 1'b1;   // UART line idles HIGH
    end else begin
      if (!busy) begin
        tx <= 1'b1;
        if (start_pulse) begin
          busy     <= 1'b1;
          char_idx <= 3'd0;
          shifter  <= {1'b1, rom(3'd0), 1'b0};  // stop, data, start
          bit_cnt  <= 4'd0;
        end
      end else if (baud_tick) begin
        tx      <= shifter[0];             // LSB first on the wire
        shifter <= {1'b1, shifter[9:1]};   // shift right, fill with 1s
        if (bit_cnt == 4'd9) begin         // 10 bits of the frame sent
          bit_cnt <= 4'd0;
          if (char_idx == MSG_LEN - 1)
            busy <= 1'b0;                  // whole message done
          else begin
            char_idx <= char_idx + 3'd1;
            shifter  <= {1'b1, rom(char_idx + 3'd1), 1'b0};
          end
        end else
          bit_cnt <= bit_cnt + 4'd1;
      end
    end
  end

  // ---------- pin mapping ----------
  assign uo_out[0]   = tx;
  assign uo_out[1]   = busy;
  assign uo_out[7:2] = 6'b0;
  assign uio_out     = 8'b0;
  assign uio_oe      = 8'b0;   // all bidirectional pins configured as inputs

  // silence lint warnings on unused signals
  wire _unused = &{ena, ui_in[7:1], uio_in, 1'b0};

endmodule
