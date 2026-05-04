Mini Memory Controller !!

My project implements a lightweight memory controller that interfaces between
a CPU host and a small fake DRAM-style memory. The controller accepts read and 
write requests from an 11-bit input interface, queues them in a FIFO queue, and
issues a sequence of DRAM-like commands (PRE → ACT → RD/WR) to a fake memory 
model, and returns responses to the CPU. 

Internally, the memory controller is composed of a request decoder that parses 
incoming CPU transactions, a bank tracker that keeps track of open banks/rows, 
and a FIFO storing all the decoded requests. The fake memory itself is 
parameterized to 1 bank, 2 rows, and 2 columns, sized small to fit 
within the gate budget.

The CPU test protocol uses an 8-bit data bus (req_data) with three control 
signals: req_valid, req_rw, and req_phase. 

Read requests are single cycle, following the form
cycle 0: req_valid=1, req_rw=0, req_phase=x, req_data=ADDR

Write requests are two cycles, following the form
cycle 0: req_valid=1, req_rw=1, req_phase=0, req_data=ADDR
cycle 1: req_valid=1, req_rw=1, req_phase=1, req_data=WDATA

On the output side, resp_data returns read data, resp_valid pulses when a 
response is ready, resp_rw echoes back the transaction type, and resp_bz 
signals when the controller is busy and cannot accept new requests. 

This design runs safely at 50 MHz.

The design was originally written in SystemVerilog and converted to Verilog
using sv2v for synthesis compatibility. Testing was done mostly using the 
SystemVerilog code and tb, then through a much simpler cocotb tb, validating
the converted Verilog. 

A more detailed description of the project can be found under the docs folder.
