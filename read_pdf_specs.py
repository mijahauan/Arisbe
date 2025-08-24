#!/usr/bin/env python3
"""
PDF specification reader for Common Logic and CGIF documents.
Improved to batch-process all PDFs in `docs/references/`, normalize text,
and write machine-readable outputs into `docs/derived/` so downstream tools
and this assistant can search/quote them.
"""

import argparse
import PyPDF2
import os
import re
from typing import List, Dict, Tuple, Optional

# Optional pdfminer.six import for better extraction on some PDFs
try:
    from pdfminer.high_level import extract_text as _pdfminer_extract_text
except Exception:  # pdfminer may not be installed in some envs
    _pdfminer_extract_text = None


def _read_pdf_text_pypdf2(pdf_path: str) -> str:
    """Extract text using PyPDF2."""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        parts: List[str] = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts)


def _read_pdf_text_pdfminer(pdf_path: str) -> str:
    """Extract text using pdfminer.six, if available."""
    if _pdfminer_extract_text is None:
        raise RuntimeError("pdfminer.six not available in this environment")
    return _pdfminer_extract_text(pdf_path) or ""


def read_pdf_text(pdf_path: str, engine: str = "auto") -> str:
    """Extract text from PDF with selectable engine.
    engine: 'auto' (default), 'pypdf2', or 'pdfminer'
    """
    engine = (engine or "auto").lower()
    if engine == "pypdf2":
        return _read_pdf_text_pypdf2(pdf_path)
    if engine == "pdfminer":
        return _read_pdf_text_pdfminer(pdf_path)
    # auto: try PyPDF2 first, then pdfminer if result seems too small
    raw = _read_pdf_text_pypdf2(pdf_path)
    # Heuristic: if fewer than 200 non-whitespace chars, try pdfminer
    if len(re.sub(r"\s+", "", raw)) < 200 and _pdfminer_extract_text is not None:
        try:
            return _read_pdf_text_pdfminer(pdf_path)
        except Exception:
            pass
    return raw


def normalize_text(text: str) -> str:
    """Normalize extracted PDF text for searchability.
    - Normalize Windows/Mac line endings to \n
    - Collapse excessive whitespace lines
    - Fix common hyphenation across line breaks: "exam-\nple" -> "example"
    - Trim trailing spaces per line
    """
    if not text:
        return ""
    # Unify line endings
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    # De-hyphenate common line-break hyphenations (word-
    # nextline -> wordnextline). Keep em-dash and hyphen-in-word when not at EOL.
    t = re.sub(r"(\w+)-\n(\w+)", r"\1\2", t)
    # Remove trailing spaces
    t = "\n".join(line.rstrip() for line in t.split("\n"))
    # Collapse 3+ blank lines to 1
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t


def extract_clif_syntax_rules(pdf_text: str) -> List[str]:
    """Extract CLIF syntax rules from Common Logic specification."""
    rules = []
    lines = pdf_text.split('\n')
    
    # Look for syntax sections
    in_syntax_section = False
    for line in lines:
        line = line.strip()
        if 'syntax' in line.lower() or 'grammar' in line.lower():
            in_syntax_section = True
        elif line.startswith('::=') or '::=' in line:
            rules.append(line)
        elif in_syntax_section and line and not line.isspace():
            if any(keyword in line.lower() for keyword in ['forall', 'exists', 'and', 'or', 'not', 'atom']):
                rules.append(line)
    
    return rules


def process_pdf(pdf_path: str, out_dir: str, engine: str = "auto") -> Tuple[str, str]:
    """Read one PDF, normalize text, and write outputs.
    Returns: (raw_text_path, summary_txt_path)
    """
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    os.makedirs(out_dir, exist_ok=True)
    raw_out = os.path.join(out_dir, f"{base}_extracted.txt")
    summary_out = os.path.join(out_dir, f"{base}_summary.txt")

    raw = read_pdf_text(pdf_path, engine=engine)
    norm = normalize_text(raw)
    with open(raw_out, "w", encoding="utf-8") as f:
        f.write(norm)

    # Heuristic parser selection by filename keywords
    lower_name = base.lower()
    clif_rules: List[str] = []
    cgif_rules: List[str] = []
    if any(k in lower_name for k in ["common_logic", "clif", "mathematical_logic"]):
        clif_rules = extract_clif_syntax_rules(norm)
    if any(k in lower_name for k in ["cgif", "conceptual", "egif", "egpeirce", "existential", "sowa", "peirce", "eg2cg", "roberts"]):
        cgif_rules = extract_cgif_syntax_rules(norm)

    with open(summary_out, "w", encoding="utf-8") as f:
        f.write(f"Source: {os.path.basename(pdf_path)}\n")
        f.write(f"Characters: {len(norm)}\n")
        if clif_rules:
            f.write("\n== CLIF-related snippets ==\n")
            for r in clif_rules[:100]:
                f.write(r + "\n")
        if cgif_rules:
            f.write("\n== CGIF-related snippets ==\n")
            for r in cgif_rules[:100]:
                f.write(r + "\n")

    return raw_out, summary_out


def extract_cgif_syntax_rules(pdf_text: str) -> List[str]:
    """Extract CGIF syntax rules from specification."""
    rules = []
    lines = pdf_text.split('\n')
    
    # Look for CGIF-specific syntax
    for line in lines:
        line = line.strip()
        if any(keyword in line for keyword in ['[', ']', ':', '->', '<-', 'concept', 'relation']):
            rules.append(line)
    
    return rules


def main():
    """Read and analyze PDF specifications.
    Batch mode by default: process all PDFs under docs/references/.
    """
    parser = argparse.ArgumentParser(description="Extract and normalize text from reference PDFs")
    parser.add_argument("--docs-dir", default="docs/references", help="Directory containing source PDFs")
    parser.add_argument("--out-dir", default="docs/derived", help="Directory to write extracted text")
    parser.add_argument("--filter", default="", help="Substring to filter which PDFs to process")
    parser.add_argument("--engine", default="auto", choices=["auto", "pypdf2", "pdfminer"], help="Text extraction engine")
    args = parser.parse_args()

    docs_dir = args.docs_dir
    out_dir = args.out_dir
    flt = args.filter.lower().strip()

    if not os.path.isdir(docs_dir):
        raise SystemExit(f"Docs directory not found: {docs_dir}")

    pdfs = [f for f in os.listdir(docs_dir) if f.lower().endswith(".pdf")]
    if flt:
        pdfs = [f for f in pdfs if flt in f.lower()]
    pdfs.sort()

    if not pdfs:
        print("No PDFs found to process.")
        return

    print(f"Processing {len(pdfs)} PDF(s) from {docs_dir} -> {out_dir} [engine={args.engine}]")
    for name in pdfs:
        path = os.path.join(docs_dir, name)
        try:
            raw_out, summary_out = process_pdf(path, out_dir, engine=args.engine)
            print(f"- {name}: extracted -> {os.path.relpath(raw_out)}, summary -> {os.path.relpath(summary_out)}")
        except Exception as e:
            print(f"! {name}: extraction error: {e}")


if __name__ == "__main__":
    main()
