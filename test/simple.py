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
    try:
        resp_data = dut.uo_out.value.to_unsigned()
    except ValueError:
        resp_data = 0
    try:
        uio_out = dut.uio_out.value.to_unsigned()
    except ValueError:
        uio_out = 0
    resp_rw    = (uio_out >> 0) & 1
    resp_valid = (uio_out >> 2) & 1
    return resp_data, resp_valid, resp_rw


def make_addr(bank, row, col):
    return ((bank & 0x1) << 7) | ((row & 0x3) << 5) | ((col & 0x3) << 3)


# -----------------------------------------------------------------------------
# Tasks
# -----------------------------------------------------------------------------

async def cpu_write(dut, addr, wdata):
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    set_req(dut, valid=1, rw=1, phase=0, data=addr)

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    set_req(dut, valid=1, rw=1, phase=1, data=wdata)

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    set_req(dut, valid=0)

    while True:
        _, resp_valid, resp_rw = get_resp(dut)
        if resp_valid and resp_rw:
            break
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")


async def cpu_read(dut, addr):
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    set_req(dut, valid=1, rw=0, phase=0, data=addr)

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    set_req(dut, valid=0)

    while True:
        resp_data, resp_valid, resp_rw = get_resp(dut)
        if resp_valid and not resp_rw:
            break
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")

    rdata = resp_data
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    return rdata


# -----------------------------------------------------------------------------
# Main test
# -----------------------------------------------------------------------------

@cocotb.test(timeout_time=1, timeout_unit="ms")
async def test_mem_top(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0

    # Reset
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    # Single smoke test: write 0xAB to bank0/row0/col0, read it back
    dut._log.info("TEST: write 0xAB -> bank0/row0/col0, read back")

    await cpu_write(dut, make_addr(0, 0, 0), 0xAB)
    rdata = await cpu_read(dut, make_addr(0, 0, 0))

    assert rdata == 0xAB, f"FAILED: got 0x{rdata:02X}, expected 0xAB"
    dut._log.info("PASSED")