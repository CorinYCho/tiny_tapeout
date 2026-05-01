# # # SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# # # SPDX-License-Identifier: Apache-2.0

# # import cocotb
# # from cocotb.clock import Clock
# # from cocotb.triggers import ClockCycles


# # @cocotb.test()
# # async def test_project(dut):
# #     dut._log.info("Start")

# #     # Set the clock period to 10 us (100 KHz)
# #     clock = Clock(dut.clk, 10, unit="us")
# #     cocotb.start_soon(clock.start())

# #     # Reset
# #     dut._log.info("Reset")
# #     dut.ena.value = 1
# #     dut.ui_in.value = 0
# #     dut.uio_in.value = 0
# #     dut.rst_n.value = 0
# #     await ClockCycles(dut.clk, 10)
# #     dut.rst_n.value = 1

# #     dut._log.info("Test project behavior")

# #     # Set the input values you want to test
# #     dut.ui_in.value = 20
# #     dut.uio_in.value = 30

# #     # Wait for one clock cycle to see the output values
# #     await ClockCycles(dut.clk, 1)

# #     # The following assersion is just an example of how to check the output values.
# #     # Change it to match the actual expected output of your module:
# #     assert dut.uo_out.value == 50

# #     # Keep testing the module by changing the input values, waiting for
# #     # one or more clock cycles, and asserting the expected output values.

#     # SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# # SPDX-License-Identifier: Apache-2.0

# import cocotb
# from cocotb.clock import Clock
# from cocotb.triggers import ClockCycles, RisingEdge, Timer


# # ---------------------------------------------------------------------------
# # Pin helpers
# # ---------------------------------------------------------------------------

# def set_req(dut, *, valid=0, rw=0, phase=0, data=0):
#     """Drive the mem_top request pins through the TT wrapper."""
#     dut.ui_in.value  = data & 0xFF
#     uio = (dut.uio_in.value.integer if hasattr(dut.uio_in.value, 'integer') else int(dut.uio_in.value)) & ~(0x7 << 3)
#     uio |= ((phase & 1) << 3) | ((rw & 1) << 4) | ((valid & 1) << 5)
#     dut.uio_in.value = uio


# def get_resp(dut):
#     """Return (resp_data, resp_valid, resp_bz, resp_rw) from uio_out / uo_out."""
#     resp_data  = int(dut.uo_out.value)
#     uio_out    = int(dut.uio_out.value)
#     resp_rw    = (uio_out >> 0) & 1
#     resp_bz    = (uio_out >> 1) & 1
#     resp_valid = (uio_out >> 2) & 1
#     return resp_data, resp_valid, resp_bz, resp_rw


# def make_addr(bank, row, col):
#     """Replicate the SV make_addr function: {bank[0], row[1:0], col[1:0], 3'b000}."""
#     return ((bank & 0x1) << 7) | ((row & 0x3) << 5) | ((col & 0x3) << 3)


# # ---------------------------------------------------------------------------
# # Async task equivalents
# # ---------------------------------------------------------------------------

# async def idle_cycle(dut):
#     set_req(dut, valid=0, rw=0, phase=0, data=0)
#     await RisingEdge(dut.clk)
#     await Timer(1, units="ns")


# async def cpu_write(dut, addr, wdata):
#     # addr phase
#     await RisingEdge(dut.clk)
#     await Timer(1, units="ns")
#     set_req(dut, valid=1, rw=1, phase=0, data=addr)

#     # data phase
#     await RisingEdge(dut.clk)
#     await Timer(1, units="ns")
#     set_req(dut, valid=1, rw=1, phase=1, data=wdata)

#     # de-assert
#     await RisingEdge(dut.clk)
#     await Timer(1, units="ns")
#     set_req(dut, valid=0)

#     # wait for write ack: resp_valid && resp_rw
#     while True:
#         _, resp_valid, _, resp_rw = get_resp(dut)
#         if resp_valid and resp_rw:
#             break
#         await RisingEdge(dut.clk)
#         await Timer(1, units="ns")

#     await RisingEdge(dut.clk)
#     await Timer(1, units="ns")


# async def cpu_read(dut, addr):
#     await RisingEdge(dut.clk)
#     await Timer(1, units="ns")
#     set_req(dut, valid=1, rw=0, phase=0, data=addr)

#     await RisingEdge(dut.clk)
#     await Timer(1, units="ns")
#     set_req(dut, valid=0)

#     # wait for read response: resp_valid && !resp_rw
#     while True:
#         resp_data, resp_valid, _, resp_rw = get_resp(dut)
#         if resp_valid and not resp_rw:
#             break
#         await RisingEdge(dut.clk)
#         await Timer(1, units="ns")

#     rdata = resp_data
#     await RisingEdge(dut.clk)
#     await Timer(1, units="ns")
#     return rdata


# async def check_write_read(dut, addr, wdata):
#     await cpu_write(dut, addr, wdata)
#     rdata = await cpu_read(dut, addr)
#     return rdata


# async def do_reset(dut):
#     dut.rst_n.value = 0
#     await RisingEdge(dut.clk)
#     await Timer(1, units="ns")
#     dut.rst_n.value = 1
#     await RisingEdge(dut.clk)
#     await Timer(1, units="ns")


# # ---------------------------------------------------------------------------
# # Main test
# # ---------------------------------------------------------------------------

# @cocotb.test()
# async def test_mem_top(dut):
#     dut._log.info("Start")

#     clock = Clock(dut.clk, 10, units="ns")  # 100 MHz
#     cocotb.start_soon(clock.start())

#     # Initialise inputs
#     dut.ena.value    = 1
#     dut.ui_in.value  = 0
#     dut.uio_in.value = 0
#     set_req(dut, valid=0, rw=0, phase=0, data=0)

#     await do_reset(dut)

#     pass_cnt = 0
#     fail_cnt = 0

#     # ------------------------------------------------------------------
#     # TEST 0 – initialisation: unwritten cell should read back 0x00
#     # ------------------------------------------------------------------
#     dut._log.info("TEST 0 initialization")
#     rdata = await cpu_read(dut, make_addr(0, 2, 3))
#     if rdata == 0x00:
#         dut._log.info("TEST 0 PASSED")
#         pass_cnt += 1
#     else:
#         dut._log.error(f"TEST 0 FAILED: got 0x{rdata:02X}, expected 0x00")
#         fail_cnt += 1

#     # ------------------------------------------------------------------
#     # TEST 1 – simple write + read in bank 0
#     # ------------------------------------------------------------------
#     dut._log.info("TEST 1 WRITE AND READ IN BANK 0")
#     rdata = await check_write_read(dut, make_addr(0, 0, 0), 0xAB)
#     if rdata == 0xAB:
#         dut._log.info("TEST 1 PASSED")
#         pass_cnt += 1
#     else:
#         dut._log.error(f"TEST 1 FAILED: got 0x{rdata:02X}, expected 0xAB")
#         fail_cnt += 1

#     await idle_cycle(dut)

#     # ------------------------------------------------------------------
#     # TEST 2 – simple write + read in bank 1
#     # ------------------------------------------------------------------
#     dut._log.info("TEST 2 WRITE AND READ IN BANK 1")
#     rdata = await check_write_read(dut, make_addr(1, 1, 2), 0x5A)
#     if rdata == 0x5A:
#         dut._log.info("TEST 2 PASSED")
#         pass_cnt += 1
#     else:
#         dut._log.error(f"TEST 2 FAILED: got 0x{rdata:02X}, expected 0x5A")
#         fail_cnt += 1

#     await idle_cycle(dut)

#     # ------------------------------------------------------------------
#     # TEST 3 – row conflict: write to row 0 then row 1 in bank 0
#     # ------------------------------------------------------------------
#     dut._log.info("TEST 3 TESTING ROW CONFLICT")
#     rdata = await check_write_read(dut, make_addr(0, 0, 1), 0xDE)
#     if rdata == 0xDE:
#         dut._log.info("TEST 3a PASSED")
#         pass_cnt += 1
#     else:
#         dut._log.error(f"TEST 3a FAILED: got 0x{rdata:02X}, expected 0xDE")
#         fail_cnt += 1

#     rdata = await check_write_read(dut, make_addr(0, 1, 1), 0xAD)
#     if rdata == 0xAD:
#         dut._log.info("TEST 3b PASSED")
#         pass_cnt += 1
#     else:
#         dut._log.error(f"TEST 3b FAILED: got 0x{rdata:02X}, expected 0xAD")
#         fail_cnt += 1

#     # ------------------------------------------------------------------
#     # TEST 4 – verify bank 0 row 0 still holds old data after row conflict
#     # ------------------------------------------------------------------
#     dut._log.info("TEST 4 READ THAT BANK 0 STILL HAS OLD DATA")
#     rdata = await cpu_read(dut, make_addr(0, 0, 1))
#     if rdata == 0xDE:
#         dut._log.info("TEST 4 PASSED")
#         pass_cnt += 1
#     else:
#         dut._log.error(f"TEST 4 FAILED: got 0x{rdata:02X}, expected 0xDE")
#         fail_cnt += 1

#     await idle_cycle(dut)

#     # ------------------------------------------------------------------
#     # TEST 5 – overwriting the same address
#     # ------------------------------------------------------------------
#     dut._log.info("TEST 5 OVERWRITING PREVIOUS ADDRESS")
#     await cpu_write(dut, make_addr(1, 3, 3), 0xFF)
#     await cpu_write(dut, make_addr(1, 3, 3), 0x11)
#     rdata = await cpu_read(dut, make_addr(1, 3, 3))
#     if rdata == 0x11:
#         dut._log.info("TEST 5 PASSED")
#         pass_cnt += 1
#     else:
#         dut._log.error(f"TEST 5 FAILED: got 0x{rdata:02X}, expected 0x11")
#         fail_cnt += 1

#     await idle_cycle(dut)

#     # ------------------------------------------------------------------
#     # TEST 6 – all-zeros data
#     # ------------------------------------------------------------------
#     dut._log.info("TEST 6 ALL ZEROS DATA")
#     rdata = await check_write_read(dut, make_addr(0, 0, 0), 0x00)
#     if rdata == 0x00:
#         dut._log.info("TEST 6 PASSED")
#         pass_cnt += 1
#     else:
#         dut._log.error(f"TEST 6 FAILED: got 0x{rdata:02X}, expected 0x00")
#         fail_cnt += 1

#     await idle_cycle(dut)

#     # ------------------------------------------------------------------
#     # TEST 7 – all-ones data
#     # ------------------------------------------------------------------
#     dut._log.info("TEST 7 ALL ONES DATA")
#     rdata = await check_write_read(dut, make_addr(1, 1, 1), 0xFF)
#     if rdata == 0xFF:
#         dut._log.info("TEST 7 PASSED")
#         pass_cnt += 1
#     else:
#         dut._log.error(f"TEST 7 FAILED: got 0x{rdata:02X}, expected 0xFF")
#         fail_cnt += 1

#     await idle_cycle(dut)

#     # ------------------------------------------------------------------
#     # TEST 8 – same row/col in different banks are independent
#     # ------------------------------------------------------------------
#     dut._log.info("TEST 8 SAME ROW COL FOR DIFFERENT BANKS")
#     await cpu_write(dut, make_addr(0, 0, 0), 0xAA)
#     await cpu_write(dut, make_addr(1, 0, 0), 0x55)
#     rdata0 = await cpu_read(dut, make_addr(0, 0, 0))
#     rdata1 = await cpu_read(dut, make_addr(1, 0, 0))
#     if rdata0 == 0xAA and rdata1 == 0x55:
#         dut._log.info("TEST 8 PASSED")
#         pass_cnt += 1
#     else:
#         dut._log.error(
#             f"TEST 8 FAILED: bank0=0x{rdata0:02X} (exp 0xAA), bank1=0x{rdata1:02X} (exp 0x55)"
#         )
#         fail_cnt += 1

#     await idle_cycle(dut)

#     # ------------------------------------------------------------------
#     # TEST 9 – write-read-write-read same cell
#     # ------------------------------------------------------------------
#     dut._log.info("TEST 9 WRITE READ WRITE READ SAME CELL")
#     await cpu_write(dut, make_addr(0, 1, 0), 0xC3)
#     rdata = await cpu_read(dut, make_addr(0, 1, 0))
#     if rdata != 0xC3:
#         dut._log.error(f"TEST 9 FAILED first write: got 0x{rdata:02X}, expected 0xC3")
#         fail_cnt += 1

#     await cpu_write(dut, make_addr(0, 1, 0), 0x3C)
#     rdata = await cpu_read(dut, make_addr(0, 1, 0))
#     if rdata == 0x3C:
#         dut._log.info("TEST 9 PASSED")
#         pass_cnt += 1
#     else:
#         dut._log.error(f"TEST 9 FAILED second write: got 0x{rdata:02X}, expected 0x3C")
#         fail_cnt += 1

#     await idle_cycle(dut)

#     # ------------------------------------------------------------------
#     # TEST 11 – exhaustive fill of all 8 cells (2 banks × 2 rows × 2 cols)
#     # ------------------------------------------------------------------
#     dut._log.info("TEST 11 EXHAUSTIVE FILL ALL 8 CELLS")
#     expected = {}
#     for b in range(2):
#         for r in range(2):
#             for c in range(2):
#                 val = (b * 4 + r * 2 + c + 1) & 0xFF
#                 expected[(b, r, c)] = val
#                 await cpu_write(dut, make_addr(b, r, c), val)

#     all_pass = True
#     for b in range(2):
#         for r in range(2):
#             for c in range(2):
#                 rdata = await cpu_read(dut, make_addr(b, r, c))
#                 exp   = expected[(b, r, c)]
#                 if rdata != exp:
#                     dut._log.error(
#                         f"TEST 11 FAILED bank{b} row{r} col{c}: got 0x{rdata:02X}, exp 0x{exp:02X}"
#                     )
#                     all_pass = False
#                     fail_cnt += 1

#     if all_pass:
#         dut._log.info("TEST 11 PASSED")
#         pass_cnt += 1

#     await idle_cycle(dut)

#     # ------------------------------------------------------------------
#     # TEST 12 – back-to-back reads after reset should return 0x00
#     # ------------------------------------------------------------------
#     dut._log.info("TEST 12 BACK TO BACK READS NO WRITE")
#     await do_reset(dut)

#     r1 = await cpu_read(dut, make_addr(0, 0, 0))
#     r2 = await cpu_read(dut, make_addr(0, 0, 0))
#     if r1 == 0x00 and r2 == 0x00:
#         dut._log.info("TEST 12 PASSED")
#         pass_cnt += 1
#     else:
#         dut._log.error(f"TEST 12 FAILED: r1=0x{r1:02X}, r2=0x{r2:02X}, expected 0x00 both")
#         fail_cnt += 1

#     await idle_cycle(dut)

#     # ------------------------------------------------------------------
#     # Scoreboard
#     # ------------------------------------------------------------------
#     dut._log.info(f"Results: {pass_cnt} PASSED / {fail_cnt} FAILED")
#     assert fail_cnt == 0, f"{fail_cnt} test(s) failed"

# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer


# -----------------------------------------------------------------------------
# Pin helpers
# -----------------------------------------------------------------------------

def set_req(dut, *, valid=0, rw=0, phase=0, data=0):
    """
    Drive the mem_top request pins through the Tiny Tapeout wrapper.
    """

    dut.ui_in.value = data & 0xFF

    # Safely read current uio_in value
    try:
        uio = dut.uio_in.value.to_unsigned()
    except ValueError:
        # If signal still contains X/Z, default to 0
        uio = 0

    # Clear bits [5:3]
    uio &= ~(0x7 << 3)

    # Insert control bits
    uio |= ((phase & 1) << 3)
    uio |= ((rw    & 1) << 4)
    uio |= ((valid & 1) << 5)

    dut.uio_in.value = uio


def get_resp(dut):
    """
    Read response signals from TT wrapper.
    Returns:
        (resp_data, resp_valid, resp_bz, resp_rw)
    """

    try:
        resp_data = dut.uo_out.value.to_unsigned()
    except ValueError:
        resp_data = 0

    try:
        uio_out = dut.uio_out.value.to_unsigned()
    except ValueError:
        uio_out = 0

    resp_rw    = (uio_out >> 0) & 1
    resp_bz    = (uio_out >> 1) & 1
    resp_valid = (uio_out >> 2) & 1

    return resp_data, resp_valid, resp_bz, resp_rw


def make_addr(bank, row, col):
    """
    Replicate SV:
    {bank[0], row[1:0], col[1:0], 3'b000}
    """

    return (
        ((bank & 0x1) << 7) |
        ((row  & 0x3) << 5) |
        ((col  & 0x3) << 3)
    )


# -----------------------------------------------------------------------------
# Async task equivalents
# -----------------------------------------------------------------------------

async def idle_cycle(dut):

    set_req(dut, valid=0, rw=0, phase=0, data=0)

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")


async def cpu_write(dut, addr, wdata):

    # Address phase
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    set_req(
        dut,
        valid=1,
        rw=1,
        phase=0,
        data=addr
    )

    # Data phase
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    set_req(
        dut,
        valid=1,
        rw=1,
        phase=1,
        data=wdata
    )

    # Deassert
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    set_req(dut, valid=0)

    # Wait for write acknowledge
    while True:

        _, resp_valid, _, resp_rw = get_resp(dut)

        if resp_valid and resp_rw:
            break

        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")


async def cpu_read(dut, addr):

    # Address phase
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    set_req(
        dut,
        valid=1,
        rw=0,
        phase=0,
        data=addr
    )

    # Deassert
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    set_req(dut, valid=0)

    # Wait for read response
    while True:

        resp_data, resp_valid, _, resp_rw = get_resp(dut)

        if resp_valid and not resp_rw:
            break

        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")

    rdata = resp_data

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    return rdata


async def check_write_read(dut, addr, wdata):

    await cpu_write(dut, addr, wdata)

    rdata = await cpu_read(dut, addr)

    return rdata


async def do_reset(dut):

    dut.rst_n.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.rst_n.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")


# -----------------------------------------------------------------------------
# Main test
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_mem_top(dut):

    dut._log.info("Start")

    # 100 MHz clock
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # Initialize wrapper inputs
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    set_req(
        dut,
        valid=0,
        rw=0,
        phase=0,
        data=0
    )

    # Reset
    await do_reset(dut)

    pass_cnt = 0
    fail_cnt = 0

    # -------------------------------------------------------------------------
    # TEST 0
    # -------------------------------------------------------------------------

    dut._log.info("TEST 0 initialization")

    rdata = await cpu_read(
        dut,
        make_addr(0, 2, 3)
    )

    if rdata == 0x00:
        dut._log.info("TEST 0 PASSED")
        pass_cnt += 1
    else:
        dut._log.error(
            f"TEST 0 FAILED: got 0x{rdata:02X}, expected 0x00"
        )
        fail_cnt += 1

    # -------------------------------------------------------------------------
    # TEST 1
    # -------------------------------------------------------------------------

    dut._log.info("TEST 1 WRITE AND READ IN BANK 0")

    rdata = await check_write_read(
        dut,
        make_addr(0, 0, 0),
        0xAB
    )

    if rdata == 0xAB:
        dut._log.info("TEST 1 PASSED")
        pass_cnt += 1
    else:
        dut._log.error(
            f"TEST 1 FAILED: got 0x{rdata:02X}, expected 0xAB"
        )
        fail_cnt += 1

    await idle_cycle(dut)

    # -------------------------------------------------------------------------
    # TEST 2
    # -------------------------------------------------------------------------

    dut._log.info("TEST 2 WRITE AND READ IN BANK 1")

    rdata = await check_write_read(
        dut,
        make_addr(1, 1, 2),
        0x5A
    )

    if rdata == 0x5A:
        dut._log.info("TEST 2 PASSED")
        pass_cnt += 1
    else:
        dut._log.error(
            f"TEST 2 FAILED: got 0x{rdata:02X}, expected 0x5A"
        )
        fail_cnt += 1

    await idle_cycle(dut)

    # -------------------------------------------------------------------------
    # TEST 3
    # -------------------------------------------------------------------------

    dut._log.info("TEST 3 TESTING ROW CONFLICT")

    rdata = await check_write_read(
        dut,
        make_addr(0, 0, 1),
        0xDE
    )

    if rdata == 0xDE:
        dut._log.info("TEST 3a PASSED")
        pass_cnt += 1
    else:
        dut._log.error(
            f"TEST 3a FAILED: got 0x{rdata:02X}, expected 0xDE"
        )
        fail_cnt += 1

    rdata = await check_write_read(
        dut,
        make_addr(0, 1, 1),
        0xAD
    )

    if rdata == 0xAD:
        dut._log.info("TEST 3b PASSED")
        pass_cnt += 1
    else:
        dut._log.error(
            f"TEST 3b FAILED: got 0x{rdata:02X}, expected 0xAD"
        )
        fail_cnt += 1

    # -------------------------------------------------------------------------
    # TEST 4
    # -------------------------------------------------------------------------

    dut._log.info("TEST 4 READ THAT BANK 0 STILL HAS OLD DATA")

    rdata = await cpu_read(
        dut,
        make_addr(0, 0, 1)
    )

    if rdata == 0xDE:
        dut._log.info("TEST 4 PASSED")
        pass_cnt += 1
    else:
        dut._log.error(
            f"TEST 4 FAILED: got 0x{rdata:02X}, expected 0xDE"
        )
        fail_cnt += 1

    await idle_cycle(dut)

    # -------------------------------------------------------------------------
    # TEST 5
    # -------------------------------------------------------------------------

    dut._log.info("TEST 5 OVERWRITING PREVIOUS ADDRESS")

    addr = make_addr(1, 3, 3)

    await cpu_write(dut, addr, 0xFF)
    await cpu_write(dut, addr, 0x11)

    rdata = await cpu_read(dut, addr)

    if rdata == 0x11:
        dut._log.info("TEST 5 PASSED")
        pass_cnt += 1
    else:
        dut._log.error(
            f"TEST 5 FAILED: got 0x{rdata:02X}, expected 0x11"
        )
        fail_cnt += 1

    await idle_cycle(dut)

    # -------------------------------------------------------------------------
    # TEST 6
    # -------------------------------------------------------------------------

    dut._log.info("TEST 6 ALL ZEROS DATA")

    rdata = await check_write_read(
        dut,
        make_addr(0, 0, 0),
        0x00
    )

    if rdata == 0x00:
        dut._log.info("TEST 6 PASSED")
        pass_cnt += 1
    else:
        dut._log.error(
            f"TEST 6 FAILED: got 0x{rdata:02X}, expected 0x00"
        )
        fail_cnt += 1

    await idle_cycle(dut)

    # -------------------------------------------------------------------------
    # TEST 7
    # -------------------------------------------------------------------------

    dut._log.info("TEST 7 ALL ONES DATA")

    rdata = await check_write_read(
        dut,
        make_addr(1, 1, 1),
        0xFF
    )

    if rdata == 0xFF:
        dut._log.info("TEST 7 PASSED")
        pass_cnt += 1
    else:
        dut._log.error(
            f"TEST 7 FAILED: got 0x{rdata:02X}, expected 0xFF"
        )
        fail_cnt += 1

    await idle_cycle(dut)

    # -------------------------------------------------------------------------
    # TEST 8
    # -------------------------------------------------------------------------

    dut._log.info("TEST 8 SAME ROW COL FOR DIFFERENT BANKS")

    await cpu_write(dut, make_addr(0, 0, 0), 0xAA)
    await cpu_write(dut, make_addr(1, 0, 0), 0x55)

    rdata0 = await cpu_read(dut, make_addr(0, 0, 0))
    rdata1 = await cpu_read(dut, make_addr(1, 0, 0))

    if rdata0 == 0xAA and rdata1 == 0x55:
        dut._log.info("TEST 8 PASSED")
        pass_cnt += 1
    else:
        dut._log.error(
            f"TEST 8 FAILED: "
            f"bank0=0x{rdata0:02X} bank1=0x{rdata1:02X}"
        )
        fail_cnt += 1

    await idle_cycle(dut)

    # -------------------------------------------------------------------------
    # TEST 9
    # -------------------------------------------------------------------------

    dut._log.info("TEST 9 WRITE READ WRITE READ SAME CELL")

    addr = make_addr(0, 1, 0)

    await cpu_write(dut, addr, 0xC3)

    rdata = await cpu_read(dut, addr)

    if rdata != 0xC3:
        dut._log.error(
            f"TEST 9 FAILED first write: got 0x{rdata:02X}"
        )
        fail_cnt += 1

    await cpu_write(dut, addr, 0x3C)

    rdata = await cpu_read(dut, addr)

    if rdata == 0x3C:
        dut._log.info("TEST 9 PASSED")
        pass_cnt += 1
    else:
        dut._log.error(
            f"TEST 9 FAILED second write: got 0x{rdata:02X}"
        )
        fail_cnt += 1

    await idle_cycle(dut)

    # -------------------------------------------------------------------------
    # TEST 11
    # -------------------------------------------------------------------------

    dut._log.info("TEST 11 EXHAUSTIVE FILL ALL 8 CELLS")

    expected = {}

    for b in range(2):
        for r in range(2):
            for c in range(2):

                val = (b * 4 + r * 2 + c + 1) & 0xFF

                expected[(b, r, c)] = val

                await cpu_write(
                    dut,
                    make_addr(b, r, c),
                    val
                )

    all_pass = True

    for b in range(2):
        for r in range(2):
            for c in range(2):

                rdata = await cpu_read(
                    dut,
                    make_addr(b, r, c)
                )

                exp = expected[(b, r, c)]

                if rdata != exp:

                    dut._log.error(
                        f"TEST 11 FAILED "
                        f"bank{b} row{r} col{c}: "
                        f"got 0x{rdata:02X}, exp 0x{exp:02X}"
                    )

                    all_pass = False
                    fail_cnt += 1

    if all_pass:
        dut._log.info("TEST 11 PASSED")
        pass_cnt += 1

    await idle_cycle(dut)

    # -------------------------------------------------------------------------
    # TEST 12
    # -------------------------------------------------------------------------

    dut._log.info("TEST 12 BACK TO BACK READS NO WRITE")

    await do_reset(dut)

    r1 = await cpu_read(
        dut,
        make_addr(0, 0, 0)
    )

    r2 = await cpu_read(
        dut,
        make_addr(0, 0, 0)
    )

    if r1 == 0x00 and r2 == 0x00:
        dut._log.info("TEST 12 PASSED")
        pass_cnt += 1
    else:
        dut._log.error(
            f"TEST 12 FAILED: "
            f"r1=0x{r1:02X}, r2=0x{r2:02X}"
        )
        fail_cnt += 1

    await idle_cycle(dut)

    # -------------------------------------------------------------------------
    # Scoreboard
    # -------------------------------------------------------------------------

    dut._log.info(
        f"Results: {pass_cnt} PASSED / {fail_cnt} FAILED"
    )

    assert fail_cnt == 0, (
        f"{fail_cnt} test(s) failed"
    )