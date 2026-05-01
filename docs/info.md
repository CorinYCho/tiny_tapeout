<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

I created a very basic memory controller module interacting with a request queue 
and a fake memory. There is a bank table module as well that keeps track of all 
the open banks and rows. Currently, it’s just taking the oldest request from the 
request queue and servicing the memory requests in order.


The CPU tb sends address, read/write bit, write data, and request valid signal.
The inputs are req_valid, req_rw (0 for read 1 for write), req_phase, req_addr, req_wdata
The outputs are resp_valid, resp_rw, resp_rdata

## How to test

- Provide 8-bit samples on data_in.
- Pulse go to begin a collection.
- assert finish to end


## External hardware
none 
