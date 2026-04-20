# RAG for RISC-V RTL Generation

ML Intern case study — Fermions. Building a RAG pipeline that generates
Verilog RTL for an in-order RV32I core, then simulating with Verilator.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your API keys
```

See `submission_<firstname>_<lastname>.md` for the full writeup.

## Repo layout
- `corpus/` — knowledge base (specs, reference RTL, patterns, pitfalls)
- `rag/` — retrieval + generation pipeline
- `rtl/generated/` — raw LLM output
- `rtl/final/` — post-fix RTL used for simulation
- `sim/` — Verilator testbench
- `tests/` — riscv-tests
- `results/` — ISA test results, benchmarks, prompt traces
