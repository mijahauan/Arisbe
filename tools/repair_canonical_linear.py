#!/usr/bin/env python3
"""
Repair specific canonical corpus inconsistencies by regenerating deterministically
from a known-good source (prefer CGIF, then EGIF), and overwriting targets.

Repairs:
 - canonical_implication.clif: regenerate from EGIF/CGIF
 - endoporeutic_game_start.egif and .clif: regenerate from CGIF
 - roberts_1973_p57_disjunction.egif: normalize by parse->generate

Usage:
  python tools/repair_canonical_linear.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from egif_parser_dau import parse_egif  # type: ignore
from cgif_parser_dau import parse_cgif  # type: ignore
from clif_parser_dau import parse_clif  # type: ignore
from egif_generator_dau import generate_egif  # type: ignore
from cgif_generator_dau import generate_cgif  # type: ignore
from clif_generator_dau import generate_clif  # type: ignore

CANON = ROOT / "corpus" / "corpus" / "canonical"


def write_text(p: Path, text: str) -> None:
    if not text.endswith("\n"):
        text = text + "\n"
    p.write_text(text, encoding="utf-8")


def regen_from_best(base: Path):
    """Return graph parsed from best available source for a file base without suffix."""
    # Prefer CGIF, then EGIF, then CLIF
    for suf, parser in ((".cgif", parse_cgif), (".egif", parse_egif), (".clif", parse_clif)):
        p = base.with_suffix(suf)
        if p.exists() and p.read_text(encoding="utf-8").strip():
            try:
                return parser(p.read_text(encoding="utf-8"))
            except Exception:
                continue
    raise RuntimeError(f"No parseable source found for {base.name}")


def repair_canonical_implication() -> None:
    base = CANON / "canonical_implication"
    graph = regen_from_best(base)
    clif = generate_clif(graph)
    write_text(base.with_suffix(".clif"), clif)
    print(f"Repaired: {base.with_suffix('.clif')}")


def repair_endoporeutic_game_start() -> None:
    base = CANON / "endoporeutic_game_start"
    # Force use of CGIF if present for stability
    g = None
    p_cgif = base.with_suffix(".cgif")
    if p_cgif.exists():
        g = parse_cgif(p_cgif.read_text(encoding="utf-8"))
    else:
        g = regen_from_best(base)
    egif = generate_egif(g)
    clif = generate_clif(g)
    write_text(base.with_suffix(".egif"), egif)
    write_text(base.with_suffix(".clif"), clif)
    print(f"Repaired: {base.with_suffix('.egif')} and {base.with_suffix('.clif')}")


def repair_roberts_disjunction() -> None:
    base = CANON / "roberts_1973_p57_disjunction"
    # Normalize via parse->generate EGIF
    p = base.with_suffix(".egif")
    g = parse_egif(p.read_text(encoding="utf-8"))
    egif = generate_egif(g)
    write_text(p, egif)
    print(f"Repaired: {p}")


def repair_sibling_cuts_shared_variable() -> None:
    base = CANON / "sibling_cuts_shared_variable"
    p = base.with_suffix(".egif")
    g = parse_egif(p.read_text(encoding="utf-8"))
    egif = generate_egif(g)
    write_text(p, egif)
    print(f"Repaired: {p}")


def main() -> int:
    try:
        repair_canonical_implication()
    except Exception as e:
        print(f"Failed to repair canonical_implication: {e}")
    try:
        repair_endoporeutic_game_start()
    except Exception as e:
        print(f"Failed to repair endoporeutic_game_start: {e}")
    try:
        repair_roberts_disjunction()
    except Exception as e:
        print(f"Failed to repair roberts_1973_p57_disjunction: {e}")
    try:
        repair_sibling_cuts_shared_variable()
    except Exception as e:
        print(f"Failed to repair sibling_cuts_shared_variable: {e}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
