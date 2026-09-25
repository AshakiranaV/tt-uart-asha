# UART Hello Transmitter — Tiny Tapeout (Sky130)

[![](https://github.com/AshakiranaV/tt-uart-asha/workflows/gds/badge.svg)](https://github.com/AshakiranaV/tt-uart-asha/actions/workflows/gds.yaml)
[![](https://github.com/AshakiranaV/tt-uart-asha/workflows/docs/badge.svg)](https://github.com/AshakiranaV/tt-uart-asha/actions/workflows/docs.yaml)
[![](https://github.com/AshakiranaV/tt-uart-asha/workflows/test/badge.svg)](https://github.com/AshakiranaV/tt-uart-asha/actions/workflows/test.yaml)
[![](https://github.com/AshakiranaV/tt-uart-asha/workflows/fpga/badge.svg)](https://github.com/AshakiranaV/tt-uart-asha/actions/workflows/fpga.yaml)

A small UART transmitter, designed and hardened for [Tiny Tapeout](https://tinytapeout.com) on the SkyWater 130nm open-source PDK.

## What it does

On a rising edge at `ui[0]`, the design transmits the message **"HI ASHA"** followed by a newline, once, as a standard 8N1 UART frame at 9600 baud, generated from a 50 MHz system clock. `uo[1]` (busy) stays high for the ~8.3 ms duration of the transmission.

Full pin-by-pin description and test instructions: [docs/info.md](docs/info.md)

## Design

- **Edge detector** — converts a held trigger into a single-cycle start pulse, so holding the input doesn't retrigger the message.
- **Baud generator** — divides the 50 MHz clock by 5208 to produce 9600-baud bit ticks, running only during an active transmission.
- **Transmit engine** — loads each character into a 10-bit shift register (`{stop, data[7:0], start}`), shifts it out LSB-first each baud tick, and steps through an 8-character message ROM.

## Status

- RTL verified with a cocotb testbench (`test/`)
- Hardened end-to-end through the open-source RTL-to-GDS flow (OpenLane/LibreLane, Sky130 PDK) — see the `gds` badge above
- top module: `tt_um_ashakiranav_uart_tx`, 1×1 tile

## Repo layout

- `src/` — Verilog source
- `test/` — cocotb testbench
- `docs/info.md` — full project datasheet
- `info.yaml` — Tiny Tapeout project metadata

## About Tiny Tapeout

[Tiny Tapeout](https://tinytapeout.com) shares a shuttle wafer across many small designs, making it cheap to get a digital design onto real silicon. Built from the [Tiny Tapeout Verilog template](https://github.com/TinyTapeout/ttsky-verilog-template).
