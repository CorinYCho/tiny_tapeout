import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_mem_top(dut):

    cocotb.start_soon(Clock(dut.clk, 40, units="ns").start())

    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    dut.rst_n.value  = 0

    # reset for 10 cycles
    for _ in range(10):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1

    # settle for 10 cycles
    for _ in range(10):
        await RisingEdge(dut.clk)

    # --- WRITE addr=0x00, data=0x03 ---

    # addr phase: drive AFTER rising edge
    await RisingEdge(dut.clk)
    await Timer(2, units="ns")
    dut.ui_in.value  = 0x00
    dut.uio_in.value = (1<<5)|(1<<4)  # valid=1, rw=1, phase=0

    # data phase
    await RisingEdge(dut.clk)
    await Timer(2, units="ns")
    dut.ui_in.value  = 0x03
    dut.uio_in.value = (1<<5)|(1<<4)|(1<<3)  # valid=1, rw=1, phase=1

    # deassert
    await RisingEdge(dut.clk)
    await Timer(2, units="ns")
    dut.ui_in.value  = 0
    dut.uio_in.value = 0

    # wait for write ack: sample AFTER each rising edge + settle
    for _ in range(500):
        await RisingEdge(dut.clk)
        await Timer(2, units="ns")
        try:
            resp_valid = (int(dut.uio_out.value) >> 2) & 1
            resp_rw    = (int(dut.uio_out.value) >> 0) & 1
        except ValueError:
            dut._log.info("write poll: X/Z, waiting")
            continue
        dut._log.info(f"write poll: resp_valid={resp_valid} resp_rw={resp_rw}")
        if resp_valid and resp_rw:
            break
    else:
        assert False, "write ack never arrived"

    # --- READ addr=0x00 ---

    # addr phase
    await RisingEdge(dut.clk)
    await Timer(2, units="ns")
    dut.ui_in.value  = 0x00
    dut.uio_in.value = (1<<5)  # valid=1, rw=0, phase=0

    # deassert
    await RisingEdge(dut.clk)
    await Timer(2, units="ns")
    dut.ui_in.value  = 0
    dut.uio_in.value = 0

    # wait for read response
    resp_data = 0
    for _ in range(500):
        await RisingEdge(dut.clk)
        await Timer(2, units="ns")
        try:
            resp_valid = (int(dut.uio_out.value) >> 2) & 1
            resp_rw    = (int(dut.uio_out.value) >> 0) & 1
            resp_data  = int(dut.uo_out.value)
        except ValueError:
            dut._log.info("read poll: X/Z, waiting")
            continue
        dut._log.info(f"read poll: resp_valid={resp_valid} resp_rw={resp_rw} data=0x{resp_data:02X}")
        if (resp_valid and not resp_rw) or (resp_data != 0 and not resp_rw):
            break
    else:
        assert False, "read response never arrived"

    assert resp_data == 0x03, f"FAILED: got 0x{resp_data:02X}, expected 0x03"
    dut._log.info("PASSED")