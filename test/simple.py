# import cocotb
# from cocotb.clock import Clock
# from cocotb.triggers import RisingEdge, Timer


# @cocotb.test()
# async def test_mem_top(dut):

#     # start 25 MHz clock
#     cocotb.start_soon(Clock(dut.clk, 40, units="ns").start())

#     dut.ena.value    = 1
#     dut.ui_in.value  = 0
#     dut.uio_in.value = 0

#     # reset
#     dut.rst_n.value = 0
#     for _ in range(10):
#         await RisingEdge(dut.clk)
#     # dut.rst_n.value = 1
#     # for _ in range(10):
#     #     await RisingEdge(dut.clk)
#     # await Timer(2, units="ns")

#     dut.rst_n.value = 1
#     for _ in range(10):
#         await RisingEdge(dut.clk)
#     await Timer(2, units="ns")
#     dut._log.info(f"after reset: cur_state={dut.user_project.u_ctlr.cur_state.value}")

#     # --- WRITE: addr=0x00, data=0x03 ---

    
#     # # addr phase
#     # await RisingEdge(dut.clk)
#     # await Timer(2, units="ns")
#     # dut.ui_in.value  = 0x00
#     # dut.uio_in.value = (1<<5)|(1<<4)  # valid=1, rw=1, phase=0

#     # # data phase
#     # await RisingEdge(dut.clk)
#     # await Timer(2, units="ns")
#     # dut.ui_in.value  = 0x03
#     # dut.uio_in.value = (1<<5)|(1<<4)|(1<<3)  # valid=1, rw=1, phase=1
#     # addr phase
#     await RisingEdge(dut.clk)
#     await Timer(2, units="ns")
#     dut.ui_in.value  = 0x00
#     dut.uio_in.value = (1<<5)|(1<<4)  # valid=1, rw=1, phase=0
#     dut._log.info(f"addr phase driven: ui_in={hex(int(dut.ui_in.value))} uio_in={bin(int(dut.uio_in.value))}")
#     dut._log.info(f"addr phase seen:   req_valid={dut.user_project.req_valid.value} req_rw={dut.user_project.req_rw.value} req_data={dut.user_project.req_data.value}")

#     # data phase
#     await RisingEdge(dut.clk)
#     await Timer(2, units="ns")
#     dut.ui_in.value  = 0x03
#     dut.uio_in.value = (1<<5)|(1<<4)|(1<<3)  # valid=1, rw=1, phase=1
#     dut._log.info(f"data phase driven: ui_in={hex(int(dut.ui_in.value))} uio_in={bin(int(dut.uio_in.value))}")
#     dut._log.info(f"data phase seen:   req_valid={dut.user_project.req_valid.value} req_rw={dut.user_project.req_rw.value} req_data={dut.user_project.req_data.value}")

#     # deassert
#     await RisingEdge(dut.clk)
#     await Timer(2, units="ns")
#     dut.uio_in.value = 0

#     # wait for write ack
#     for _ in range(2000):
#         await RisingEdge(dut.clk)
#         await Timer(2, units="ns")
#         try:
#             resp_valid = int(dut.user_project.resp_valid.value)
#             resp_rw    = int(dut.user_project.resp_rw.value)
#         except ValueError:
#             dut._log.info("write poll: X/Z on outputs, waiting...")
#             continue
#         dut._log.info(f"write poll: resp_valid={resp_valid} resp_rw={resp_rw}")
#         if resp_valid and resp_rw:
#             break
#     else:
#         assert False, "write ack never arrived"

#     # --- READ: addr=0x00 ---
#     # addr phase
#     await RisingEdge(dut.clk)
#     await Timer(2, units="ns")
#     dut.ui_in.value  = 0x00
#     dut.uio_in.value = (1<<5)  # valid=1, rw=0, phase=0

#     # deassert
#     await RisingEdge(dut.clk)
#     await Timer(2, units="ns")
#     dut.uio_in.value = 0

#     # wait for read response
#     for _ in range(500):
#         await RisingEdge(dut.clk)
#         await Timer(2, units="ns")
#         try:
#             resp_valid = int(dut.user_project.resp_valid.value)
#             resp_rw    = int(dut.user_project.resp_rw.value)
#             resp_data  = int(dut.user_project.resp_data.value)
#         except ValueError:
#             dut._log.info("read poll: X/Z on outputs, waiting...")
#             continue
#         dut._log.info(f"read poll: resp_valid={resp_valid} resp_rw={resp_rw} data=0x{resp_data:02X}")
#         if resp_valid and not resp_rw:
#             break
#     else:
#         assert False, "read response never arrived"

#     assert resp_data == 0x03, f"FAILED: got 0x{resp_data:02X}, expected 0x03"
#     dut._log.info("PASSED")

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_mem_top(dut):

    # start 25 MHz clock
    cocotb.start_soon(Clock(dut.clk, 40, units="ns").start())

    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0

    # reset
    dut.rst_n.value = 0
    for _ in range(10):
        await RisingEdge(dut.clk)
    # dut.rst_n.value = 1
    # for _ in range(10):
    #     await RisingEdge(dut.clk)
    # await Timer(2, units="ns")

    dut.rst_n.value = 1
    for _ in range(10):
        await RisingEdge(dut.clk)
    await Timer(2, units="ns")
    dut._log.info(f"after reset: cur_state={dut.user_project.u_ctlr.cur_state.value}")

    # --- WRITE: addr=0x00, data=0x03 ---

    
    # # addr phase
    # await RisingEdge(dut.clk)
    # await Timer(2, units="ns")
    # dut.ui_in.value  = 0x00
    # dut.uio_in.value = (1<<5)|(1<<4)  # valid=1, rw=1, phase=0

    # # data phase
    # await RisingEdge(dut.clk)
    # await Timer(2, units="ns")
    # dut.ui_in.value  = 0x03
    # dut.uio_in.value = (1<<5)|(1<<4)|(1<<3)  # valid=1, rw=1, phase=1
    # addr phase
    await RisingEdge(dut.clk)
    await Timer(2, units="ns")
    dut.ui_in.value  = 0x00
    dut.uio_in.value = (1<<5)|(1<<4)  # valid=1, rw=1, phase=0
    dut._log.info(f"addr phase driven: ui_in={hex(int(dut.ui_in.value))} uio_in={bin(int(dut.uio_in.value))}")
    dut._log.info(f"addr phase seen:   req_valid={dut.user_project.req_valid.value} req_rw={dut.user_project.req_rw.value} req_data={dut.user_project.req_data.value}")

    # data phase
    await RisingEdge(dut.clk)
    await Timer(2, units="ns")
    dut.ui_in.value  = 0x03
    dut.uio_in.value = (1<<5)|(1<<4)|(1<<3)  # valid=1, rw=1, phase=1
    dut._log.info(f"data phase driven: ui_in={hex(int(dut.ui_in.value))} uio_in={bin(int(dut.uio_in.value))}")
    dut._log.info(f"data phase seen:   req_valid={dut.user_project.req_valid.value} req_rw={dut.user_project.req_rw.value} req_data={dut.user_project.req_data.value}")

    # deassert
    await RisingEdge(dut.clk)
    await Timer(2, units="ns")
    dut.uio_in.value = 0

    # wait for write ack
    for _ in range(2000):
        await RisingEdge(dut.clk)
        await Timer(2, units="ns")
        try:
            resp_valid = int(dut.user_project.resp_valid.value)
            resp_rw    = int(dut.user_project.resp_rw.value)
        except ValueError:
            dut._log.info("write poll: X/Z on outputs, waiting...")
            continue
        dut._log.info(f"write poll: resp_valid={resp_valid} resp_rw={resp_rw}")
        if resp_valid and resp_rw:
            break
    else:
        assert False, "write ack never arrived"

    # --- READ: addr=0x00 ---
    # addr phase
    await RisingEdge(dut.clk)
    await Timer(2, units="ns")
    dut.ui_in.value  = 0x00
    dut.uio_in.value = (1<<5)  # valid=1, rw=0, phase=0

    # deassert
    await RisingEdge(dut.clk)
    await Timer(2, units="ns")
    dut.uio_in.value = 0

    # wait for read response
    for _ in range(500):
        await RisingEdge(dut.clk)
        await Timer(2, units="ns")
        try:
            resp_valid = int(dut.user_project.resp_valid.value)
            resp_rw    = int(dut.user_project.resp_rw.value)
            resp_data  = int(dut.user_project.resp_data.value)
        except ValueError:
            dut._log.info("read poll: X/Z on outputs, waiting...")
            continue
        dut._log.info(f"read poll: resp_valid={resp_valid} resp_rw={resp_rw} data=0x{resp_data:02X}")
        if resp_valid and not resp_rw:
            break
    else:
        assert False, "read response never arrived"

    assert resp_data == 0x03, f"FAILED: got 0x{resp_data:02X}, expected 0x03"
    dut._log.info("PASSED")