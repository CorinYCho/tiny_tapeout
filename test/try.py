# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# -----------------------------------------------------------------------------
# Pin helpers
# -----------------------------------------------------------------------------

def set_req(dut, *, valid=0, rw=0, phase=0, data=0):
    dut.ui_in.value = data & 0xFF
    uio = 0
    uio |= ((phase & 1) << 3)
    uio |= ((rw    & 1) << 4)
    uio |= ((valid & 1) << 5)
    dut.uio_in.value = uio


def get_resp(dut):
    """Returns (resp_data, resp_valid, resp_rw, has_x).
    Reads internal control signals first — uo_out may stay X in GL due to
    tristate buffers, so we only use it for data and tolerate X there."""
    try:
        resp_valid = int(dut.user_project.resp_valid.value)
        resp_rw    = int(dut.user_project.resp_rw.value)
    except ValueError:
        return 0, 0, 0, True  # internal signals still X

    # uo_out goes through tristate buffers in GL and may stay X — treat as 0
    try:
        resp_data = dut.uo_out.value.to_unsigned()
    except ValueError:
        resp_data = 0

    return resp_data, resp_valid, resp_rw, False


def safe_uio_str(dut):
    try:
        return f"{dut.uio_out.value.to_unsigned():08b}"
    except ValueError:
        return str(dut.uio_out.value)


def make_addr(bank, row, col):
    return ((bank & 0x1) << 7) | ((row & 0x3) << 5) | ((col & 0x3) << 3)


# -----------------------------------------------------------------------------
# Tasks
# -----------------------------------------------------------------------------

async def cpu_write(dut, addr, wdata):
    await RisingEdge(dut.clk)
    await Timer(2, unit="ns")
    set_req(dut, valid=1, rw=1, phase=0, data=addr)

    await RisingEdge(dut.clk)
    await Timer(2, unit="ns")
    set_req(dut, valid=1, rw=1, phase=1, data=wdata)

    await RisingEdge(dut.clk)
    await Timer(2, unit="ns")
    set_req(dut, valid=0)

    for cycle in range(500):
        await RisingEdge(dut.clk)
        await Timer(2, unit="ns")
        _, resp_valid, resp_rw, has_x = get_resp(dut)
        dut._log.info(f"  cpu_write poll [{cycle}]: uio_out={safe_uio_str(dut)} valid={resp_valid} rw={resp_rw} x={has_x}")
        if not has_x and resp_valid and resp_rw:
            return

    raise AssertionError("cpu_write: timed out waiting for write ack (resp_valid && resp_rw)")


async def cpu_read(dut, addr):
    await RisingEdge(dut.clk)
    await Timer(2, unit="ns")
    set_req(dut, valid=1, rw=0, phase=0, data=addr)

    await RisingEdge(dut.clk)
    await Timer(2, unit="ns")
    set_req(dut, valid=0)

    for cycle in range(500):
        await RisingEdge(dut.clk)
        await Timer(2, unit="ns")
        resp_data, resp_valid, resp_rw, has_x = get_resp(dut)
        dut._log.info(f"  cpu_read  poll [{cycle}]: uio_out={safe_uio_str(dut)} valid={resp_valid} rw={resp_rw} x={has_x} data=0x{resp_data:02X}")
        if not has_x and resp_valid and not resp_rw:
            return resp_data

    raise AssertionError("cpu_read: timed out waiting for read response (resp_valid && !resp_rw)")


# -----------------------------------------------------------------------------
# Main test
# -----------------------------------------------------------------------------

@cocotb.test(timeout_time=10, timeout_unit="ms")
async def test_mem_top(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0

    # Hold reset for 5 cycles
    dut.rst_n.value = 0
    for _ in range(5):
        await RisingEdge(dut.clk)
    await Timer(2, unit="ns")
    dut.rst_n.value = 1

    # Log internal state after reset to confirm design is alive
    await RisingEdge(dut.clk)
    await Timer(2, unit="ns")
    dut._log.info(f"post-reset: resp_valid={dut.user_project.resp_valid.value} resp_rw={dut.user_project.resp_rw.value}")

    # Extra settling cycles for GL
    for _ in range(19):
        await RisingEdge(dut.clk)
    await Timer(2, unit="ns")

    dut._log.info("TEST: write 0xAB -> bank0/row0/col0, read back")

    await cpu_write(dut, make_addr(0, 0, 0), 0xAB)
    rdata = await cpu_read(dut, make_addr(0, 0, 0))

    assert rdata == 0xAB, f"FAILED: got 0x{rdata:02X}, expected 0xAB"
    dut._log.info("PASSED")