# Common RTL Pitfalls for RV32I Core Generation

## 1. Blocking vs Non-blocking Assignments

**Rule**: Use `<=` (non-blocking) in sequential `always @(posedge clk)` blocks.
Use `=` (blocking) in combinational `always @*` blocks.

**Bad**:
```verilog
always @(posedge clk) begin
    a = b;        // WRONG: race conditions in simulation
    c = a;
end
```

**Good**:
```verilog
always @(posedge clk) begin
    a <= b;
    c <= a;       // both see old values, as hardware would
end
```

## 2. Register x0 Must Always Read as Zero

The RISC-V architectural zero register x0 is hardwired to 0. Writes are ignored.

**Bad**:
```verilog
assign rs1_data = regfile[rs1_addr];   // wrong if x0 was ever written
```

**Good**:
```verilog
assign rs1_data = (rs1_addr == 5'd0) ? 32'b0 : regfile[rs1_addr];
```

Or equivalently, suppress writes to x0:
```verilog
if (reg_write_en && rd_addr != 5'd0)
    regfile[rd_addr] <= write_data;
```

## 3. Signed vs Unsigned Arithmetic

Verilog defaults to unsigned. RISC-V has both signed and unsigned operations.

- `SRA` (arithmetic right shift) needs `$signed()`:
```verilog
  assign sra_result = $signed(rs1) >>> shamt;
```
- `SLT` (set less than, signed): `$signed(a) < $signed(b)`
- `SLTU` (set less than, unsigned): `a < b`
- `BLT`/`BGE` use signed; `BLTU`/`BGEU` use unsigned.

Using `>>` instead of `>>>` for SRA is a classic silent bug.

## 4. Immediate Sign-Extension by Instruction Type

Each instruction type has a different immediate layout. Getting the sign-extension wrong breaks branches, loads, stores, and JAL silently.

- **I-type** (ADDI, LW, JALR): `{{20{inst[31]}}, inst[31:20]}`
- **S-type** (SW, SH, SB): `{{20{inst[31]}}, inst[31:25], inst[11:7]}`
- **B-type** (BEQ, BNE, ...): `{{19{inst[31]}}, inst[31], inst[7], inst[30:25], inst[11:8], 1'b0}` — note bit 0 is always 0
- **U-type** (LUI, AUIPC): `{inst[31:12], 12'b0}`
- **J-type** (JAL): `{{11{inst[31]}}, inst[31], inst[19:12], inst[20], inst[30:21], 1'b0}`

## 5. Shift Amount Must Be 5 Bits

For RV32I, shifts use only the lower 5 bits of rs2 (or `shamt` field).
```verilog
assign sll_result = rs1 << rs2[4:0];   // NOT rs2[31:0]
```

## 6. Load Byte/Halfword Sign-Extension

- `LB` sign-extends 8 bits → 32 bits
- `LBU` zero-extends
- `LH` sign-extends 16 bits → 32 bits
- `LHU` zero-extends

Easy to get the sign bit wrong, especially when combined with byte-lane selection based on `addr[1:0]`.

## 7. Byte-Enable Logic for Stores

A `SB` writing to address 0x5 must only enable byte lane 1 of the word at 0x4:
```verilog
case (addr[1:0])
    2'b00: be = 4'b0001;
    2'b01: be = 4'b0010;
    2'b10: be = 4'b0100;
    2'b11: be = 4'b1000;
endcase
```

## 8. Branch Target Uses PC, Not PC+4

Branch target = `PC + sign_ext(B_imm)`, NOT `PC + 4 + imm`.

## 9. JALR Clears LSB

```verilog
assign jalr_target = (rs1 + imm) & ~32'b1;
```

## 10. Synchronous Reset Convention

Prefer synchronous reset for FPGA/ASIC portability:
```verilog
always @(posedge clk) begin
    if (rst)
        state <= 0;
    else
        state <= next_state;
end
```

## 11. Latches from Incomplete Combinational Logic

Every combinational `always @*` block must assign outputs in every branch.

**Bad** (infers latch):
```verilog
always @* begin
    if (sel) y = a;
    // y not assigned in else branch → LATCH
end
```

**Good**:
```verilog
always @* begin
    y = 32'b0;      // default assignment
    if (sel) y = a;
end
```

## 12. Verilator-Specific Lint Warnings

- `WIDTH`: assigning a 33-bit sum to a 32-bit register
- `UNOPTFLAT`: combinational loops
- `BLKANDNBLK`: mixing blocking and non-blocking on the same signal

Run `verilator --lint-only -Wall top.v` early and often.
