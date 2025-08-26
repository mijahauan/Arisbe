#!/usr/bin/env python3
"""
Detect and optionally quarantine noisy scholar corpus files.

Default is a dry run that lists problematic files under `corpus/corpus/scholars/`.
With --move, files are moved to `corpus/rejected_tmp/` preserving filename.

Noise categories detected:
 - empty_placeholder: empty or whitespace-only CLIF files
 - clif_parse_eof: CLIF parser hits EOF at position 0 (likely placeholder)
 - cgif_dup_vertex: CGIF parser reports duplicate vertex labels (legacy harvest)
 - parse_fail: generic parse failure for EGIF/CGIF/CLIF

Usage:
  python tools/quarantine_scholars.py --dry-run            # default
  python tools/quarantine_scholars.py --move               # move files
  python tools/quarantine_scholars.py --pattern egif       # only *.egif
"""
from __future__ import annotations

import sys
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

# Ensure src/ is importable
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Parsers
from egif_parser_dau import parse_egif  # type: ignore
from cgif_parser_dau import parse_cgif  # type: ignore
from clif_parser_dau import parse_clif  # type: ignore

EXT_TO_KIND = {".egif": "egif", ".cgif": "cgif", ".clif": "clif"}
PARSERS = {"egif": parse_egif, "cgif": parse_cgif, "clif": parse_clif}


def detect_issue(p: Path) -> Tuple[str, str] | None:
    """Return (category, message) if file is noisy, else None."""
    kind = EXT_TO_KIND.get(p.suffix.lower())
    if not kind:
        return None

    text = p.read_text(encoding="utf-8", errors="ignore")
    if kind == "clif":
        if text.strip() == "":
            return ("empty_placeholder", "CLIF file is empty/whitespace")
    try:
        PARSERS[kind](text)
        return None
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if kind == "clif" and "EOF" in msg and "position 0" in msg:
            return ("clif_parse_eof", msg)
        if kind == "cgif" and "Vertex v_" in msg and "already exists" in msg:
            return ("cgif_dup_vertex", msg)
        return ("parse_fail", msg)


def iter_scholar_files(pattern: str | None) -> List[Path]:
    base = ROOT / "corpus" / "corpus" / "scholars"
    if not base.exists():
        return []
    files: List[Path] = []
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in EXT_TO_KIND:
            continue
        if pattern and p.suffix.lower() != f".{pattern.lower()}":
            continue
        files.append(p)
    return files


def move_to_quarantine(p: Path) -> Path:
    dest_dir = ROOT / "corpus" / "rejected_tmp"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / p.name
    # Avoid overwriting an existing file with same name
    if dest.exists():
        i = 1
        while True:
            alt = dest_dir / f"{p.stem}_{i}{p.suffix}"
            if not alt.exists():
                dest = alt
                break
            i += 1
    shutil.move(str(p), str(dest))
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description="Detect and optionally quarantine noisy scholar corpus files")
    ap.add_argument("--dry-run", action="store_true", help="List issues only (default)")
    ap.add_argument("--move", action="store_true", help="Move problematic files to corpus/rejected_tmp/")
    ap.add_argument("--pattern", choices=["egif", "cgif", "clif"], help="Limit to a specific extension")
    args = ap.parse_args()

    files = iter_scholar_files(args.pattern)
    issues: Dict[str, List[Tuple[Path, str]]] = {}
    for p in files:
        det = detect_issue(p)
        if not det:
            continue
        cat, msg = det
        issues.setdefault(cat, []).append((p, msg))

    total = sum(len(v) for v in issues.values())
    if total == 0:
        print("No noisy scholar files detected.")
        return 0

    print(f"Detected {total} noisy files:")
    for cat, items in sorted(issues.items()):
        print(f"\n[{cat}] {len(items)} items")
        for p, msg in items:
            print(f" - {p} :: {msg}")

    if args.move and not args.dry_run:
        moved = 0
        for items in issues.values():
            for p, _ in items:
                dest = move_to_quarantine(p)
                print(f"Moved {p} -> {dest}")
                moved += 1
        print(f"Done. Moved {moved} files to corpus/rejected_tmp/.")
    else:
        print("\nDry run only. Use --move to quarantine files.")

    # Non-zero exit to indicate issues found (useful in CI if desired)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
