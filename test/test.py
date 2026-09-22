# SPDX-FileCopyrightText: 2026 Ashakirana V
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

BIT_CYCLES = 5208          # 50 MHz / 9600 baud
MESSAGE = b"HI ASHA\n"     # expected output, 8 characters


def out_bits(dut):
    """uo_out as a plain int (cocotb 2.x LogicArray has no int/shift operators)."""
    value = dut.uo_out.value
    to_unsigned = getattr(value, "to_unsigned", None)
    return to_unsigned() if to_unsigned else int(value)


def tx(dut):
    return out_bits(dut) & 1


def busy(dut):
    return (out_bits(dut) >> 1) & 1


async def reset(dut):
    clock = Clock(dut.clk, 20, unit="ns")   # 50 MHz
    cocotb.start_soon(clock.start())
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)


async def press_button(dut, cycles=5):
    dut.ui_in.value = 1
    await ClockCycles(dut.clk, cycles)
    dut.ui_in.value = 0


async def receive_byte(dut, timeout_bits=3):
    """Act like a UART receiver: wait for the start bit, sample each bit
    in its middle, and check the stop bit. Returns the byte, or None."""
    for _ in range(timeout_bits * BIT_CYCLES):
        await ClockCycles(dut.clk, 1)
        if tx(dut) == 0:
            break
    else:
        return None
    await ClockCycles(dut.clk, BIT_CYCLES // 2)     # middle of start bit
    assert tx(dut) == 0, "start bit not stable (glitch?)"
    await ClockCycles(dut.clk, BIT_CYCLES)          # middle of data bit 0
    value = 0
    for i in range(8):                              # LSB first
        value |= tx(dut) << i
        await ClockCycles(dut.clk, BIT_CYCLES)
    assert tx(dut) == 1, f"stop bit missing after byte 0x{value:02X}"
    return value


@cocotb.test()
async def test_idle_state(dut):
    """After reset: TX idles high, busy is low."""
    await reset(dut)
    assert tx(dut) == 1, "TX should idle high"
    assert busy(dut) == 0, "busy should be low at idle"


@cocotb.test()
async def test_full_message(dut):
    """One press sends all 8 characters with correct framing, then goes idle."""
    await reset(dut)
    await press_button(dut)
    await ClockCycles(dut.clk, 5)
    assert busy(dut) == 1, "busy should assert after trigger"

    received = bytearray()
    for _ in range(len(MESSAGE)):
        b = await receive_byte(dut)
        assert b is not None, f"timed out after receiving {bytes(received)!r}"
        received.append(b)
    dut._log.info(f"Received: {bytes(received)!r}")
    assert bytes(received) == MESSAGE, f"expected {MESSAGE!r}, got {bytes(received)!r}"

    await ClockCycles(dut.clk, BIT_CYCLES)
    assert busy(dut) == 0, "busy should clear after the message"
    assert tx(dut) == 1, "TX should return to idle high"
    assert await receive_byte(dut) is None, "no extra characters after the message"


@cocotb.test()
async def test_press_during_transmission_ignored(dut):
    """A second press mid-message must not restart or repeat the message."""
    await reset(dut)
    await press_button(dut)
    received = bytearray()
    for i in range(len(MESSAGE)):
        received.append(await receive_byte(dut))
        if i == 2:
            await press_button(dut)     # press again during transmission
    assert bytes(received) == MESSAGE, f"message corrupted: {bytes(received)!r}"
    await ClockCycles(dut.clk, BIT_CYCLES)
    assert await receive_byte(dut) is None, "second press should have been ignored"


@cocotb.test()
async def test_second_press_after_idle(dut):
    """After the message ends, a new press sends the message again."""
    await reset(dut)
    for _ in range(2):
        await press_button(dut)
        received = bytearray()
        for _ in range(len(MESSAGE)):
            received.append(await receive_byte(dut))
        assert bytes(received) == MESSAGE
        await ClockCycles(dut.clk, 2 * BIT_CYCLES)
        assert busy(dut) == 0
