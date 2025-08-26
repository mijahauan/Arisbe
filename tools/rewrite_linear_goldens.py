#!/usr/bin/env python3
"""
Rewrite corpus EGIF/CGIF/CLIF files in-place to their deterministic canonical
form by parsing via the EGI core and regenerating. Use with care.

Usage:
  python tools/rewrite_linear_goldens.py [canonical|scholars|all]

Defaults to canonical.
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

EXT_TO_KIND = {".egif": "egif", ".cgif": "cgif", ".clif": "clif"}
PARSERS = {"egif": parse_egif, "cgif": parse_cgif, "clif": parse_clif}
GENERATORS = {"egif": generate_egif, "cgif": generate_cgif, "clif": generate_clif}


def targets_from_arg(arg: str) -> list[Path]:
    base = ROOT / "corpus" / "corpus"
    if arg == "scholars":
        return [base / "scholars"]
    if arg == "all":
        return [base / "canonical", base / "scholars"]
    return [base / "canonical"]


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else "canonical"
    dirs = targets_from_arg(arg)

    files: list[Path] = []
    for d in dirs:
        if not d.exists():
            continue
        for p in d.rglob('*'):
            if p.suffix.lower() in EXT_TO_KIND and p.is_file():
                files.append(p)

    changed = 0
    for p in files:
        kind = EXT_TO_KIND[p.suffix.lower()]
        text = p.read_text(encoding='utf-8')
        try:
            graph = PARSERS[kind](text)
            regen = GENERATORS[kind](graph)
        except Exception as e:
            print(f"SKIP {p} ({kind}): {e}")
            continue
        if text != regen:
            p.write_text(regen if regen.endswith('\n') else regen + '\n', encoding='utf-8')
            changed += 1
            print(f"Rewrote: {p}")
    print(f"Done. Rewrote {changed} of {len(files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
