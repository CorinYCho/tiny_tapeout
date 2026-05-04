Mini Memory Controller !!

I created a very basic memory controller interacting with a request queue 
and a fake memory. The design accepts CPU read/write requests over an 
11-bit interface, queues them in a FIFO, issues the correct sequence of 
DRAM-like commands (PRE → ACT → RD/WR) to a fake memory model, and returns 
responses to the CPU. The memory controller has a bank table as well that 
keeps track of all the open banks and rows. It takes the oldest request from 
the request queue and services the memory requests in order.

