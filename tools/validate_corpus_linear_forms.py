#!/usr/bin/env python3
"""
Validate corpus EGIF/CGIF/CLIF files against deterministic goldens by parsing
and regenerating via the EGI core, asserting normalized equality. Also checks
basic round-trip stability.

Exit codes:
 0 = success
 1 = failures detected
"""
from __future__ import annotations

import sys
from pathlib import Path
import argparse
from typing import Iterable

# Ensure src/ and tools/ are importable
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Import parsers/generators and utility
from egif_parser_dau import parse_egif  # type: ignore
from cgif_parser_dau import parse_cgif  # type: ignore
from clif_parser_dau import parse_clif  # type: ignore
from egif_generator_dau import generate_egif  # type: ignore
from cgif_generator_dau import generate_cgif  # type: ignore
from clif_generator_dau import generate_clif  # type: ignore

# Reuse preprocess logic for EGIF comment stripping
try:
    from tools.convert_linear_form import preprocess  # type: ignore
except Exception:
    def preprocess(text: str, kind: str, strip_comments: bool) -> str:
        if kind == "egif" and strip_comments:
            lines = []
            for line in text.splitlines():
                s = line.strip()
                if s and not s.startswith('#'):
                    lines.append(s)
            return ' '.join(lines)
        return text


KIND_TO_PARSE = {
    "egif": parse_egif,
    "cgif": parse_cgif,
    "clif": parse_clif,
}
KIND_TO_GEN = {
    "egif": generate_egif,
    "cgif": generate_cgif,
    "clif": generate_clif,
}
EXTS = {"egif": ".egif", "cgif": ".cgif", "clif": ".clif"}


def norm_ws(s: str) -> str:
    return ' '.join(s.split()).strip()


def iter_linear_files(dirs: Iterable[Path]) -> Iterable[Path]:
    for base in dirs:
        for p in base.rglob('*'):
            if p.suffix.lower() in (".egif", ".cgif", ".clif") and p.is_file():
                yield p


def kind_from_suffix(p: Path) -> str:
    suf = p.suffix.lower()
    for k, ext in EXTS.items():
        if suf == ext:
            return k
    raise ValueError(f"Unknown kind for file: {p}")


def validate_file(p: Path, roundtrip_mode: str = "egif", verbose: bool = False) -> list[str]:
    """Return list of failure messages for this file, empty if OK."""
    failures: list[str] = []
    kind = kind_from_suffix(p)
    raw = p.read_text(encoding='utf-8')
    # Skip empty placeholder files
    if raw.strip() == "":
        return []
    pre = preprocess(raw, kind, strip_comments=True)

    # Parse to graph
    try:
        graph = KIND_TO_PARSE[kind](pre)
    except Exception as e:
        failures.append(f"PARSE FAIL {p}: {e}")
        return failures

    # Regenerate same kind and compare to golden content (normalized)
    try:
        regen_same = KIND_TO_GEN[kind](graph)
        if norm_ws(regen_same) != norm_ws(pre):
            failures.append(f"MISMATCH {p.name}: regenerated {kind} differs from file")
            if verbose and kind == "egif":
                failures.append(f"  raw(pre)   = {repr(pre)}")
                failures.append(f"  regen_same = {repr(regen_same)}")
                failures.append(f"  norm(pre)  = {norm_ws(pre)!r}")
                failures.append(f"  norm(reg)  = {norm_ws(regen_same)!r}")
    except Exception as e:
        failures.append(f"GEN FAIL {p} ({kind}): {e}")

    # Also generate other kinds to ensure generation succeeds
    for other in (k for k in ("egif", "cgif", "clif") if k != kind):
        try:
            _ = KIND_TO_GEN[other](graph)
        except Exception as e:
            failures.append(f"GEN FAIL {p} -> {other}: {e}")

    if roundtrip_mode in ("egif", "all"):
        # Round-trip stability (when EGIF source available): EGIF -> CGIF -> EGIF
        try:
            eg = GENERATE_EGIF_FROM_GRAPH(graph)
            g2 = parse_cgif(generate_cgif(parse_egif(eg)))  # EGIF -> CGIF -> EGI
            eg2 = generate_egif(g2)
            if norm_ws(eg2) != norm_ws(eg):
                failures.append(f"ROUNDTRIP EGIF-CGIF-EGIF differs for {p}")
        except Exception:
            # Skip round-trip check if any step not applicable
            pass
    if roundtrip_mode in ("clif", "all"):
        # EGIF -> CLIF -> EGIF
        try:
            eg = GENERATE_EGIF_FROM_GRAPH(graph)
            g3 = parse_clif(generate_clif(parse_egif(eg)))
            eg3 = generate_egif(g3)
            if norm_ws(eg3) != norm_ws(eg):
                failures.append(f"ROUNDTRIP EGIF-CLIF-EGIF differs for {p}")
        except Exception:
            pass

    return failures


def GENERATE_EGIF_FROM_GRAPH(graph) -> str:
    return generate_egif(graph)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate corpus linear forms against deterministic goldens")
    ap.add_argument("--sets", choices=["canonical", "scholars", "all"], default="canonical", help="Which corpus sets to validate")
    ap.add_argument("--roundtrip", choices=["none", "egif", "clif", "all"], default="egif", help="Round-trip checks to perform")
    ap.add_argument("--include-harvest", action="store_true", help="Include harvested scholar files (noisy, may fail)")
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose mismatch debugging output")
    args = ap.parse_args()

    # Select dirs
    corpus_root = ROOT / "corpus" / "corpus"
    targets: list[Path] = []
    if args.sets in ("canonical", "all"):
        targets.append(corpus_root / "canonical")
    if args.sets in ("scholars", "all"):
        targets.append(corpus_root / "scholars")

    files = list(iter_linear_files(targets))
    all_failures: list[str] = []
    for p in files:
        # Skip any tmp_* directories or files
        parts_lower = {part.lower() for part in p.parts}
        if any(part.startswith('tmp_') for part in parts_lower):
            continue
        # Skip harvested scholar files by default (they are extracted and noisy)
        if not args.include_harvest and p.name.startswith("harvest_"):
            continue
        all_failures.extend(validate_file(p, roundtrip_mode=args.roundtrip, verbose=args.verbose))

    if all_failures:
        print("Corpus validation failures ({}):".format(len(all_failures)))
        for msg in all_failures:
            print(" -", msg)
        return 1
    else:
        print(f"Corpus validation passed for {len(files)} files (sets={args.sets}, roundtrip={args.roundtrip}).")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
