#!/usr/bin/env python3
"""
Convert between linear forms (EGIF, CGIF, CLIF) via the EGI core.

Usage examples:
  # Auto-detect input from extension; write output file next to input
  python tools/convert_linear_form.py --in corpus/corpus/scholars/sowa_cat_on_mat.egif --to cgif

  # Explicitly specify input kind and write to stdout
  python tools/convert_linear_form.py --in some.clif --from clif --to egif --stdout

  # Convert CGIF -> CLIF
  python tools/convert_linear_form.py -i sample.cgif -t clif

Supported kinds: egif, cgif, clif
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure src/ is on sys.path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Parsers / Generators
from egif_parser_dau import parse_egif  # type: ignore
from cgif_parser_dau import parse_cgif  # type: ignore
from clif_parser_dau import parse_clif  # type: ignore
from egif_generator_dau import generate_egif  # type: ignore
from cgif_generator_dau import generate_cgif  # type: ignore
from clif_generator_dau import generate_clif  # type: ignore

KIND_EXT = {
    "egif": ".egif",
    "cgif": ".cgif",
    "clif": ".clif",
}

PARSERS = {
    "egif": parse_egif,
    "cgif": parse_cgif,
    "clif": parse_clif,
}

GENERATORS = {
    "egif": generate_egif,
    "cgif": generate_cgif,
    "clif": generate_clif,
}


def detect_kind_from_path(p: Path) -> str | None:
    ext = p.suffix.lower()
    for k, e in KIND_EXT.items():
        if ext == e:
            return k
    return None


def preprocess(text: str, kind: str, strip_comments: bool) -> str:
    if kind == "egif" and strip_comments:
        lines = []
        for line in text.splitlines():
            s = line.strip()
            if s and not s.startswith('#'):
                lines.append(s)
        return ' '.join(lines)
    return text


def convert(text: str, src_kind: str, dst_kind: str, strip_comments: bool = True) -> str:
    if src_kind not in PARSERS:
        raise ValueError(f"Unsupported source kind: {src_kind}")
    if dst_kind not in GENERATORS:
        raise ValueError(f"Unsupported destination kind: {dst_kind}")
    pre = preprocess(text, src_kind, strip_comments)
    egi = PARSERS[src_kind](pre)
    return GENERATORS[dst_kind](egi)


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert between EGIF/CGIF/CLIF via EGI core")
    ap.add_argument("--in", "-i", dest="inp", required=False, help="Input file path (or omit to read stdin)")
    ap.add_argument("--from", "-f", dest="src_kind", choices=["egif", "cgif", "clif"], help="Input kind (auto-detect by extension if omitted)")
    ap.add_argument("--to", "-t", dest="dst_kind", required=True, choices=["egif", "cgif", "clif"], help="Output kind")
    ap.add_argument("--out", "-o", dest="outp", help="Output file path (default: beside input with new extension)")
    ap.add_argument("--stdout", action="store_true", help="Write converted content to stdout instead of a file")
    ap.add_argument("--no-strip-comments", action="store_true", help="Do not strip EGIF comments before parsing")
    args = ap.parse_args()

    # Read input
    if args.inp:
        in_path = Path(args.inp)
        if not in_path.exists():
            print(f"Input not found: {in_path}", file=sys.stderr)
            return 2
        inp_text = in_path.read_text(encoding="utf-8")
        src_kind = args.src_kind or detect_kind_from_path(in_path)
        if not src_kind:
            print("Cannot auto-detect input kind; specify --from", file=sys.stderr)
            return 2
    else:
        # stdin mode requires explicit kind
        if not args.src_kind:
            print("Reading stdin: you must specify --from {egif|cgif|clif}", file=sys.stderr)
            return 2
        src_kind = args.src_kind
        inp_text = sys.stdin.read()

    # Perform conversion
    try:
        converted = convert(inp_text, src_kind, args.dst_kind, strip_comments=not args.no_strip_comments)
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        return 1

    # Output
    if args.stdout or not args.inp:
        sys.stdout.write(converted if converted.endswith("\n") else converted + "\n")
        return 0

    # Determine output path
    if args.outp:
        out_path = Path(args.outp)
    else:
        # beside input
        out_ext = KIND_EXT[args.dst_kind]
        out_path = in_path.with_suffix(out_ext)
    out_path.write_text(converted if converted.endswith("\n") else converted + "\n", encoding="utf-8")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
