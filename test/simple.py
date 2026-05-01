import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_mem_top(dut):

    # start 25 MHz clock
    cocotb.start_soon(Clock(dut.clk, 40, unit="ns").start())

    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0

    # reset
    dut.rst_n.value = 0
    for _ in range(10):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    for _ in range(10):
        await RisingEdge(dut.clk)

    # --- WRITE: addr=0x00, data=0x03 ---
    # addr phase: req_valid=1, req_rw=1, req_phase=0, req_data=0x00
    await RisingEdge(dut.clk)
    dut.ui_in.value  = 0x00          # addr
    dut.uio_in.value = (1<<5)|(1<<4) # valid=1, rw=1, phase=0

    # data phase: req_valid=1, req_rw=1, req_phase=1, req_data=0x03
    await RisingEdge(dut.clk)
    dut.ui_in.value  = 0x03          # data
    dut.uio_in.value = (1<<5)|(1<<4)|(1<<3) # valid=1, rw=1, phase=1

    # deassert
    await RisingEdge(dut.clk)
    dut.uio_in.value = 0

    # wait for write ack: resp_valid=1, resp_rw=1
    for _ in range(500):
        await RisingEdge(dut.clk)
        resp_valid = int(dut.user_project.resp_valid.value)
        resp_rw    = int(dut.user_project.resp_rw.value)
        dut._log.info(f"write poll: resp_valid={resp_valid} resp_rw={resp_rw}")
        if resp_valid and resp_rw:
            break
    else:
        assert False, "write ack never arrived"

    # --- READ: addr=0x00 ---
    # addr phase: req_valid=1, req_rw=0, req_phase=0, req_data=0x00
    await RisingEdge(dut.clk)
    dut.ui_in.value  = 0x00
    dut.uio_in.value = (1<<5) # valid=1, rw=0, phase=0

    # deassert
    await RisingEdge(dut.clk)
    dut.uio_in.value = 0

    # wait for read response: resp_valid=1, resp_rw=0
    for _ in range(500):
        await RisingEdge(dut.clk)
        resp_valid = int(dut.user_project.resp_valid.value)
        resp_rw    = int(dut.user_project.resp_rw.value)
        try:
            resp_data = int(dut.user_project.resp_data.value)
        except ValueError:
            resp_data = 0
        dut._log.info(f"read poll: resp_valid={resp_valid} resp_rw={resp_rw} data=0x{resp_data:02X}")
        if resp_valid and not resp_rw:
            break
    else:
        assert False, "read response never arrived"

    assert resp_data == 0x03, f"FAILED: got 0x{resp_data:02X}, expected 0x03"
    dut._log.info("PASSED")