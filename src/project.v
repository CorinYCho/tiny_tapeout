/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_example (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // All output pins must be assigned. If not used, assign to 0.
  assign uo_out  = ui_in + uio_in;  // Example: ou_out is the sum of ui_in and uio_in
  assign uio_out = 0;
  assign uio_oe  = 0;

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, clk, rst_n, 1'b0};

endmodule


/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_corin (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // // All output pins must be assigned. If not used, assign to 0.
  // assign uo_out  = ui_in + uio_in;  // Example: ou_out is the sum of ui_in and uio_in


  // // List all unused inputs to prevent warnings
  // wire _unused = &{ena, clk, rst_n, 1'b0};

  wire reset  = ~rst_n;

  wire        req_phase     = uio_in[3];
  wire        req_rw = uio_in[4];
  wire        req_valid = uio_in[5];
  wire [7:0]  req_data = ui_in;

  wire [7:0]  resp_data;
  wire        resp_valid;
  wire        resp_bz;
  wire        resp_rw;

  mem_top u_ctlr (
    .clk(clk),
    .rst(reset),
    .req_data(req_data),
    .req_phase(req_phase),
    .req_rw(req_rw),
    .req_valid(req_valid),
    .resp_data(resp_data),
    .resp_valid(resp_valid),
    .resp_bz(resp_bz),
    .resp_rw(resp_rw)
  );

  assign uo_out = resp_data;
  assign uio_out = {5'b0, resp_valid, resp_bz, resp_rw};
  assign uio_oe  = 8'b0000_0111;

  // wire _unused = &{ena, 1'b0};
  wire _unused = &{ena, uio_in[7:6], 1'b0};


endmodule

module bank_tracker (
	clk,
	rst,
	req_bank,
	req_row,
	is_open,
	is_hit,
	is_conflict,
	act_en,
	pre_en
);
	reg _sv2v_0;
	parameter signed [31:0] N_BANKS = 2;
	parameter signed [31:0] ROW_W = 2;
	input wire clk;
	input wire rst;
	input wire [$clog2(N_BANKS) - 1:0] req_bank;
	input wire [ROW_W - 1:0] req_row;
	output reg is_open;
	output reg is_hit;
	output reg is_conflict;
	input wire act_en;
	input wire pre_en;
	reg [N_BANKS - 1:0] open_flag;
	reg [(N_BANKS * ROW_W) - 1:0] open_row;
	always @(*) begin
		if (_sv2v_0)
			;
		is_open = open_flag[req_bank];
		is_hit = is_open && (open_row[req_bank * ROW_W+:ROW_W] == req_row);
		is_conflict = is_open && (open_row[req_bank * ROW_W+:ROW_W] != req_row);
	end
	always @(posedge clk or posedge rst)
		if (rst) begin : sv2v_autoblock_1
			reg signed [31:0] i;
			for (i = 0; i < N_BANKS; i = i + 1)
				begin
					open_flag[i] <= 1'sb0;
					open_row[i * ROW_W+:ROW_W] <= 1'sb0;
				end
		end
		else begin
			if (pre_en)
				open_flag[req_bank] <= 1'b0;
			if (act_en) begin
				open_flag[req_bank] <= 1'b1;
				open_row[req_bank * ROW_W+:ROW_W] <= req_row;
			end
		end
	initial _sv2v_0 = 0;
endmodule
module fake_memory (
	clk,
	rst,
	mem_valid,
	mem_cmd,
	mem_bank,
	mem_row,
	mem_col,
	mem_wdata,
	mem_resp_valid,
	mem_resp_rdata,
	mem_resp_rw
);
	parameter signed [31:0] N_BANKS = 2;
	parameter signed [31:0] N_ROWS = 4;
	parameter signed [31:0] N_COLS = 4;
	input wire clk;
	input wire rst;
	input wire mem_valid;
	input wire mem_cmd;
	input wire [$clog2(N_BANKS):0] mem_bank;
	input wire [$clog2(N_ROWS):0] mem_row;
	input wire [$clog2(N_COLS):0] mem_col;
	input wire [7:0] mem_wdata;
	output reg mem_resp_valid;
	output reg [7:0] mem_resp_rdata;
	output reg mem_resp_rw;
	reg [(((N_BANKS * N_ROWS) * N_COLS) * 8) - 1:0] mem_arr;
	reg reg_valid;
	reg reg_cmd;
	reg [1:0] reg_bank;
	reg [1:0] reg_row;
	reg [1:0] reg_col;
	reg [7:0] reg_wdata;
	always @(posedge clk or posedge rst)
		if (rst) begin
			reg_valid <= 1'b0;
			mem_resp_valid <= 1'b0;
			mem_resp_rdata <= 8'h00;
			mem_resp_rw <= 1'b0;
			mem_arr <= 'd0;
		end
		else begin
			reg_valid <= mem_valid;
			reg_cmd <= mem_cmd;
			reg_bank <= mem_bank;
			reg_row <= mem_row;
			reg_col <= mem_col;
			reg_wdata <= mem_wdata;
			mem_resp_valid <= 1'b0;
			if (reg_valid) begin
				mem_resp_valid <= 1'b1;
				mem_resp_rw <= reg_cmd;
				if (!reg_cmd)
					mem_resp_rdata <= mem_arr[((((reg_bank * N_ROWS) + reg_row) * N_COLS) + reg_col) * 8+:8];
				else begin
					mem_arr[((((reg_bank * N_ROWS) + reg_row) * N_COLS) + reg_col) * 8+:8] <= reg_wdata;
					mem_resp_rdata <= 8'h00;
				end
			end
		end
endmodule
module mem_ctrl (
	clk,
	rst,
	entry_valid,
	entry_in,
	entry_accepted,
	mem_valid,
	mem_cmd,
	mem_bank,
	mem_row,
	mem_col,
	mem_wdata,
	mem_resp_valid,
	mem_resp_rdata,
	mem_resp_rw,
	resp_valid,
	resp_data,
	resp_bz,
	resp_rw
);
	reg _sv2v_0;
	input wire clk;
	input wire rst;
	input wire entry_valid;
	input wire [23:0] entry_in;
	output reg entry_accepted;
	output reg mem_valid;
	output reg mem_cmd;
	output reg [1:0] mem_bank;
	output reg [1:0] mem_row;
	output reg [1:0] mem_col;
	output reg [7:0] mem_wdata;
	input wire mem_resp_valid;
	input wire [7:0] mem_resp_rdata;
	input wire mem_resp_rw;
	output reg resp_valid;
	output reg [7:0] resp_data;
	output reg resp_bz;
	output reg resp_rw;
	reg [2:0] cur_state;
	reg [2:0] nxt_state;
	reg [23:0] reg_entry;
	wire is_open;
	wire is_hit;
	wire is_conflict;
	reg act_en;
	reg pre_en;
	always @(posedge clk or posedge rst)
		if (rst)
			cur_state <= 3'd0;
		else
			cur_state <= nxt_state;
	always @(posedge clk or posedge rst)
		if (rst)
			reg_entry <= 1'sb0;
		else if (entry_accepted)
			reg_entry <= entry_in;
	always @(*) begin
		if (_sv2v_0)
			;
		nxt_state = cur_state;
		entry_accepted = 1'b0;
		mem_valid = 1'b0;
		mem_cmd = 1'b0;
		mem_bank = reg_entry[5-:2];
		mem_row = reg_entry[3-:2];
		mem_col = reg_entry[1-:2];
		mem_wdata = reg_entry[13-:8];
		act_en = 1'b0;
		pre_en = 1'b0;
		resp_valid = 1'b0;
		resp_data = 8'h00;
		resp_bz = 1'b0;
		resp_rw = 1'b0;
		case (cur_state)
			3'd0:
				if (entry_valid) begin
					entry_accepted = 1'b1;
					nxt_state = 3'd1;
				end
			3'd1: begin
				resp_bz = 1'b1;
				if (is_hit)
					nxt_state = 3'd4;
				else if (is_conflict)
					nxt_state = 3'd2;
				else
					nxt_state = 3'd3;
			end
			3'd2: begin
				resp_bz = 1'b1;
				pre_en = 1'b1;
				nxt_state = 3'd3;
			end
			3'd3: begin
				resp_bz = 1'b1;
				act_en = 1'b1;
				nxt_state = 3'd4;
			end
			3'd4: begin
				resp_bz = 1'b1;
				mem_valid = 1'b1;
				mem_cmd = reg_entry[22];
				nxt_state = 3'd5;
			end
			3'd5: begin
				resp_bz = 1'b1;
				if (mem_resp_valid) begin
					resp_valid = 1'b1;
					resp_data = mem_resp_rdata;
					resp_rw = mem_resp_rw;
					resp_bz = 1'b0;
					nxt_state = 3'd0;
				end
			end
		endcase
	end
	bank_tracker #(
		.N_BANKS(2),
		.ROW_W(2)
	) u_bank_tracker(
		.clk(clk),
		.rst(rst),
		.req_bank(reg_entry[5-:2]),
		.req_row(reg_entry[3-:2]),
		.is_open(is_open),
		.is_hit(is_hit),
		.is_conflict(is_conflict),
		.act_en(act_en),
		.pre_en(pre_en)
	);
	initial _sv2v_0 = 0;
endmodule
module mem_top (
	clk,
	rst,
	req_data,
	req_phase,
	req_rw,
	req_valid,
	resp_data,
	resp_valid,
	resp_bz,
	resp_rw
);
	input wire clk;
	input wire rst;
	input wire [7:0] req_data;
	input wire req_phase;
	input wire req_rw;
	input wire req_valid;
	output wire [7:0] resp_data;
	output wire resp_valid;
	output wire resp_bz;
	output wire resp_rw;
	wire [23:0] entry_out;
	wire entry_valid;
	wire entry_accepted;
	wire q_full;
	wire mem_valid;
	wire mem_cmd;
	wire [1:0] mem_bank;
	wire [1:0] mem_row;
	wire [1:0] mem_col;
	wire [7:0] mem_wdata;
	wire mem_resp_valid;
	wire [7:0] mem_resp_rdata;
	wire mem_resp_rw;
	request_queue #(.DEPTH(8)) u_rq(
		.clk(clk),
		.rst(rst),
		.req_valid(req_valid),
		.req_rw(req_rw),
		.req_phase(req_phase),
		.req_data(req_data),
		.entry_accepted(entry_accepted),
		.entry_out(entry_out),
		.entry_valid(entry_valid),
		.q_full(q_full)
	);
	mem_ctrl u_ctrl(
		.clk(clk),
		.rst(rst),
		.entry_valid(entry_valid),
		.entry_in(entry_out),
		.entry_accepted(entry_accepted),
		.mem_valid(mem_valid),
		.mem_cmd(mem_cmd),
		.mem_bank(mem_bank),
		.mem_row(mem_row),
		.mem_col(mem_col),
		.mem_wdata(mem_wdata),
		.mem_resp_valid(mem_resp_valid),
		.mem_resp_rdata(mem_resp_rdata),
		.mem_resp_rw(mem_resp_rw),
		.resp_valid(resp_valid),
		.resp_data(resp_data),
		.resp_bz(resp_bz),
		.resp_rw(resp_rw)
	);
	fake_memory #(
		.N_BANKS(2),
		.N_ROWS(4),
		.N_COLS(4)
	) u_fake_mem(
		.clk(clk),
		.rst(rst),
		.mem_valid(mem_valid),
		.mem_cmd(mem_cmd),
		.mem_bank(mem_bank),
		.mem_row(mem_row),
		.mem_col(mem_col),
		.mem_wdata(mem_wdata),
		.mem_resp_valid(mem_resp_valid),
		.mem_resp_rdata(mem_resp_rdata),
		.mem_resp_rw(mem_resp_rw)
	);
endmodule
`default_nettype none
module rq_fsm (
	clk,
	rst,
	req_valid,
	req_rw,
	req_phase,
	in_data,
	bank,
	row,
	col,
	queue_not_full,
	entry_ready,
	entry
);
	input wire clk;
	input wire rst;
	input wire req_valid;
	input wire req_rw;
	input wire req_phase;
	input wire [7:0] in_data;
	input wire [1:0] bank;
	input wire [1:0] row;
	input wire [1:0] col;
	input wire queue_not_full;
	output reg entry_ready;
	output wire [23:0] entry;
	reg [23:0] entry_reg;
	assign entry = entry_reg;
	always @(posedge clk or posedge rst)
		if (rst)
			entry_reg <= 1'sb0;
		else if (req_valid && queue_not_full) begin
			if (!req_rw) begin
				entry_ready <= 1'b1;
				entry_reg[23] <= 1'b1;
				entry_reg[22] <= 1'b0;
				entry_reg[21-:8] <= in_data;
				entry_reg[13-:8] <= 8'h00;
				entry_reg[5-:2] <= bank;
				entry_reg[3-:2] <= row;
				entry_reg[1-:2] <= col;
			end
			else if (!req_phase) begin
				entry_ready <= 1'b0;
				entry_reg[21-:8] <= in_data;
				entry_reg[5-:2] <= bank;
				entry_reg[3-:2] <= row;
				entry_reg[1-:2] <= col;
				entry_reg[23] <= 1'b0;
				entry_reg[22] <= 1'b1;
			end
			else begin
				entry_ready <= 1'b1;
				entry_reg[13-:8] <= in_data;
				entry_reg[23] <= 1'b1;
			end
		end
		else
			entry_ready <= 1'b0;
endmodule
module decode_addr (
	addr,
	bank,
	row,
	col
);
	reg _sv2v_0;
	input wire [7:0] addr;
	output reg [1:0] bank;
	output reg [1:0] row;
	output reg [1:0] col;
	always @(*) begin
		if (_sv2v_0)
			;
		bank = addr[7];
		row = addr[6:5];
		col = addr[4:3];
	end
	initial _sv2v_0 = 0;
endmodule
module request_queue (
	clk,
	rst,
	req_valid,
	req_rw,
	req_phase,
	req_data,
	entry_accepted,
	entry_out,
	entry_valid,
	q_full
);
	parameter signed [31:0] DEPTH = 4;
	parameter signed [31:0] PTR_W = $clog2(DEPTH);
	input wire clk;
	input wire rst;
	input wire req_valid;
	input wire req_rw;
	input wire req_phase;
	input wire [7:0] req_data;
	input wire entry_accepted;
	output wire [23:0] entry_out;
	output wire entry_valid;
	output wire q_full;
	wire [1:0] dec_bank;
	wire [1:0] dec_row;
	wire [1:0] dec_col;
	wire entry_ready;
	wire [23:0] assembled_entry;
	reg [(DEPTH * 24) - 1:0] fifo_mem;
	reg [PTR_W - 1:0] wr_ptr;
	reg [PTR_W - 1:0] rd_ptr;
	reg [PTR_W:0] count;
	assign q_full = count == DEPTH;
	assign entry_valid = count != {(PTR_W >= 0 ? PTR_W + 1 : 1 - PTR_W) {1'sb0}};
	assign entry_out = fifo_mem[rd_ptr * 24+:24];
	decode_addr u_decode(
		.addr(req_data),
		.bank(dec_bank),
		.row(dec_row),
		.col(dec_col)
	);
	rq_fsm u_rq_fsm(
		.clk(clk),
		.rst(rst),
		.req_valid(req_valid),
		.req_rw(req_rw),
		.req_phase(req_phase),
		.in_data(req_data),
		.bank(dec_bank),
		.row(dec_row),
		.col(dec_col),
		.queue_not_full(~q_full),
		.entry_ready(entry_ready),
		.entry(assembled_entry)
	);
	always @(posedge clk or posedge rst)
		if (rst) begin
			wr_ptr <= 1'sb0;
			rd_ptr <= 1'sb0;
			count <= 1'sb0;
		end
		else begin
			if (entry_ready && !q_full) begin
				fifo_mem[wr_ptr * 24+:24] <= assembled_entry;
				wr_ptr <= wr_ptr + 1'b1;
				count <= count + 1'b1;
			end
			if (entry_accepted && entry_valid) begin
				rd_ptr <= rd_ptr + 1'b1;
				count <= count - 1'b1;
			end
		end
endmodule

