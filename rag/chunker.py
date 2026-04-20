"""
Chunk corpus sources into retrieval units.

Strategy:
  - Verilog files: chunk by module boundaries. Each chunk = one module.
    If a module > 2000 tokens, split further on always-block boundaries.
  - Markdown (pitfalls, patterns): chunk by H2 (##) headings.
  - Spec PDF: chunk by page, then post-hoc by instruction where possible.

Output: corpus/chunks.jsonl — one JSON object per chunk with metadata.
"""

import json
import re
from pathlib import Path
from typing import Iterator

import pypdf

ROOT = Path(__file__).parent.parent
CORPUS = ROOT / "corpus"
OUT = CORPUS / "chunks.jsonl"


# ---------- Verilog chunking ----------

MODULE_RE = re.compile(
    r"(module\s+\w+.*?endmodule)", re.DOTALL
)

def chunk_verilog_file(path: Path) -> Iterator[dict]:
    """Yield one chunk per module. Includes filename + line offsets as metadata."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return
    for match in MODULE_RE.finditer(text):
        module_src = match.group(1)
        # Extract module name for the chunk id
        name_match = re.search(r"module\s+(\w+)", module_src)
        module_name = name_match.group(1) if name_match else "unknown"
        yield {
            "source": str(path.relative_to(ROOT)),
            "type": "verilog",
            "module": module_name,
            "text": module_src,
            "n_chars": len(module_src),
        }


def walk_verilog(root: Path) -> Iterator[dict]:
    for ext in ("*.v", "*.sv", "*.svh"):
        for f in root.rglob(ext):
            # Skip testbenches, docs, and third-party sub-deps we don't care about
            if any(skip in f.parts for skip in ("doc", "docs", "scripts")):
                continue
            yield from chunk_verilog_file(f)


# ---------- Markdown chunking ----------

def chunk_markdown(path: Path) -> Iterator[dict]:
    text = path.read_text(encoding="utf-8")
    # Split on H2 headings (## ...)
    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        heading_match = re.match(r"## (.+)", sec)
        heading = heading_match.group(1) if heading_match else "intro"
        yield {
            "source": str(path.relative_to(ROOT)),
            "type": "markdown",
            "heading": heading,
            "text": sec,
            "n_chars": len(sec),
        }


# ---------- PDF chunking ----------

def chunk_pdf(path: Path, chars_per_chunk: int = 1500) -> Iterator[dict]:
    reader = pypdf.PdfReader(str(path))
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        # Roughly fixed-size chunks within a page, overlap 200 chars
        for i in range(0, len(text), chars_per_chunk - 200):
            chunk = text[i : i + chars_per_chunk].strip()
            if len(chunk) < 100:
                continue
            yield {
                "source": str(path.relative_to(ROOT)),
                "type": "pdf",
                "page": page_num + 1,
                "text": chunk,
                "n_chars": len(chunk),
            }


# ---------- Main ----------

def main():
    n = 0
    with OUT.open("w") as out:
        # Verilog: reference_rtl + patterns
        for ref_root in [CORPUS / "reference_rtl", CORPUS / "patterns"]:
            if ref_root.exists():
                for chunk in walk_verilog(ref_root):
                    chunk["id"] = f"chunk_{n:05d}"
                    out.write(json.dumps(chunk) + "\n")
                    n += 1

        # Markdown: pitfalls
        pitfalls = CORPUS / "pitfalls.md"
        if pitfalls.exists():
            for chunk in chunk_markdown(pitfalls):
                chunk["id"] = f"chunk_{n:05d}"
                out.write(json.dumps(chunk) + "\n")
                n += 1

        # PDF: specs
        for pdf in (CORPUS / "specs").glob("*.pdf"):
            for chunk in chunk_pdf(pdf):
                chunk["id"] = f"chunk_{n:05d}"
                out.write(json.dumps(chunk) + "\n")
                n += 1

    print(f"Wrote {n} chunks to {OUT}")
    # Summary by type
    from collections import Counter
    counts = Counter()
    with OUT.open() as f:
        for line in f:
            counts[json.loads(line)["type"]] += 1
    for t, c in counts.items():
        print(f"  {t}: {c}")


if __name__ == "__main__":
    main()
