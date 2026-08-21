# SPDX-FileCopyrightText: 2026 Ashakirana V
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

BIT_CYCLES = 5208  # 50 MHz / 9600 baud


@cocotb.test()
async def test_uart_hello(dut):
    dut._log.info("Start")

    # 50 MHz clock: 20 ns period
    clock = Clock(dut.clk, 20, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)

    # TX must idle high, busy low
    assert dut.uo_out.value[0] == 1, "TX should idle high"
    assert (dut.uo_out.value >> 1) & 1 == 0, "busy should be low at idle"

    # Trigger transmission (rising edge on ui_in[0])
    dut.ui_in.value = 1
    await ClockCycles(dut.clk, 5)
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 5)

    # Busy must assert
    assert (dut.uo_out.value >> 1) & 1 == 1, "busy should assert after trigger"

    # Wait for the start bit (TX goes low), bounded wait
    found_start = False
    for _ in range(2 * BIT_CYCLES):
        await ClockCycles(dut.clk, 1)
        if dut.uo_out.value[0] == 0:
            found_start = True
            break
    assert found_start, "start bit not seen on TX"

    # Move to the middle of data bit 0: 1.5 bit periods from start-bit edge
    await ClockCycles(dut.clk, BIT_CYCLES + BIT_CYCLES // 2)

    # Sample 8 data bits, LSB first
    byte = 0
    for i in range(8):
        bit = int(dut.uo_out.value[0])
        byte |= bit << i
        await ClockCycles(dut.clk, BIT_CYCLES)

    dut._log.info(f"First byte received: 0x{byte:02X}")
    assert byte == ord("H"), f"expected 'H' (0x48), got 0x{byte:02X}"
