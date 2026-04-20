#!/usr/bin/env bash
# Convert rv32ui-p-* ELF tests to hex files for Verilator $readmemh
set -e
SRC_DIR="tests/riscv-tests/isa"
OUT_DIR="tests/hex"
mkdir -p "$OUT_DIR"

for elf in "$SRC_DIR"/rv32ui-p-*; do
    # skip .dump files, only process actual ELFs
    [[ "$elf" == *.dump ]] && continue
    name=$(basename "$elf")
    # Convert ELF → binary → hex (32-bit words, one per line)
    riscv64-unknown-elf-objcopy -O binary "$elf" "$OUT_DIR/$name.bin"
    # hexdump: 4-byte words, little-endian, one per line
    hexdump -v -e '1/4 "%08x\n"' "$OUT_DIR/$name.bin" > "$OUT_DIR/$name.hex"
    rm "$OUT_DIR/$name.bin"
done

echo "Generated $(ls $OUT_DIR/*.hex | wc -l) hex files in $OUT_DIR"
