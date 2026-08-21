<!---
This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.
You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project is a UART transmitter that sends the message "HI ASHA" followed by a newline,
once, every time it is triggered. The UART frame format is 8N1 (one start bit, 8 data bits
LSB first, one stop bit) at 9600 baud, generated from a 50 MHz system clock.

Internally the design has three parts:

1. **Edge detector** - a registered copy of the trigger input is compared with the live
   input, producing a single-cycle start pulse on a rising edge. Holding the button does
   not retrigger the message.
2. **Baud generator** - a counter divides the 50 MHz clock by 5208 to produce one tick per
   bit period (9600 baud). It only runs while a transmission is active.
3. **Transmit engine** - each character is loaded into a 10-bit shift register as
   {stop, data[7:0], start}. On every baud tick the LSB is driven onto the TX line and the
   register shifts right. After 10 bits the next character is loaded from a small ROM
   holding the 8-character message. When the last character finishes, the line returns to
   idle (high) and the busy flag clears.

## How to test

1. Apply a 50 MHz clock and release reset (rst_n high).
2. Connect uo[0] (TX) to a USB-serial adapter RX pin, configured for 9600 baud 8N1.
3. Pulse ui[0] from low to high.
4. The terminal should print: `HI ASHA`
5. uo[1] (busy) stays high for the ~8.3 ms duration of the transmission.

## External hardware

A USB-to-serial adapter (3.3 V logic) and a serial terminal program (e.g. minicom, PuTTY)
to observe the transmitted message. A push button on ui[0] can be used as the trigger.
