<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

I created a very basic memory controller module interacting with a request queue 
and a fake memory. There is a bank table module as well that keeps track of all 
the open banks and rows. It takes the oldest request from the 
request queue and services the memory requests in order.

The CPU tb sends the memory address and a read or write request, which is put
into the request queue. My memory controller is the interface between the request
queue and fake memory, servicing the decoded requests when the memory bus is idle.
The memory controller also has a bank table that keeps track of which bank/row
is open, and if the project wants to develop further, the bank table can be
used for scheduling the memory requests in different ways.

## How to test
Since my memory controller module is doing data reads and writes to fake memory, 
I am used a simulator to do all the testing.

- Provide 8-bit samples on data_in.
- Pulse go to begin a collection.
- assert finish to end


## External hardware
none 
