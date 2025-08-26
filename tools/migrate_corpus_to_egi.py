#!/usr/bin/env python3
"""
Migrate corpus entries to EGI-as-source-of-truth.

- Scans corpus/corpus/ recursively.
- For each linear form (EGIF/CGIF/CLIF) or drawing JSON, parses to an EGI.
- Writes a normalized JSON file alongside the source: <basename>.egi.json

Usage:
  python tools/migrate_corpus_to_egi.py --root corpus/corpus [--overwrite]

Safety:
- By default, does not overwrite existing *.egi.json files unless --overwrite is passed.
- Leaves original files untouched.
"""
import argparse
import json
from pathlib import Path
from typing import Optional, Tuple

from frozendict import frozendict

# Parsers and adapters
try:
    from egif_parser_dau import parse_egif
except Exception:  # pragma: no cover
    parse_egif = None

try:
    from cgif_parser_dau import parse_cgif
except Exception:  # pragma: no cover
    parse_cgif = None

try:
    from clif_parser_dau import parse_clif
except Exception:  # pragma: no cover
    parse_clif = None

try:
    from drawing_to_egi_adapter import drawing_to_relational_graph
except Exception:  # pragma: no cover
    drawing_to_relational_graph = None

from egi_core_dau import RelationalGraphWithCuts, AlphabetDAU


LINEAR_EXTS = {".egif": "egif", ".cgif": "cgif", ".clif": "clif", ".egrf": "egif"}
JSON_EXTS = {".json"}


def egi_to_dict(egi: RelationalGraphWithCuts) -> dict:
    """Serialize EGI to a stable JSON-able dict."""
    return {
        "sheet": egi.sheet,
        "V": [{"id": v.id, "label": v.label, "is_generic": v.is_generic} for v in sorted(egi.V, key=lambda x: x.id)],
        "E": [{"id": e.id} for e in sorted(egi.E, key=lambda x: x.id)],
        "Cut": [{"id": c.id} for c in sorted(egi.Cut, key=lambda x: x.id)],
        "nu": {k: list(v) for k, v in sorted(egi.nu.items())},
        "rel": dict(sorted(egi.rel.items())),
        "area": {k: sorted(list(v)) for k, v in sorted(egi.area.items())},
        "alphabet": None if egi.alphabet is None else {
            "C": sorted(list(egi.alphabet.C)),
            "F": sorted(list(egi.alphabet.F)),
            "R": sorted(list(egi.alphabet.R)),
            "ar": dict(egi.alphabet.ar),
        },
        "rho": {k: v for k, v in sorted(egi.rho.items())},
    }


def parse_file_to_egi(path: Path) -> Tuple[Optional[RelationalGraphWithCuts], Optional[str]]:
    """Return (EGI, error_message)."""
    suffix = path.suffix.lower()
    try:
        if suffix in LINEAR_EXTS:
            fmt = LINEAR_EXTS[suffix]
            text = path.read_text(encoding="utf-8")
            # Some .egrf files may actually be JSON; skip such cases
            if suffix == ".egrf" and text.lstrip().startswith("{"):
                return None, "Skipping .egrf that appears to be JSON"
            if fmt == "egif" and parse_egif:
                return parse_egif(text), None
            if fmt == "cgif" and parse_cgif:
                return parse_cgif(text), None
            if fmt == "clif" and parse_clif:
                return parse_clif(text), None
            return None, f"No parser available for format {fmt} ({path})"
        if suffix in JSON_EXTS and drawing_to_relational_graph:
            # Attempt drawing JSON -> EGI
            data = json.loads(path.read_text(encoding="utf-8"))
            # Heuristic: treat as drawing only if it has drawing-ish keys
            has_vertices = isinstance(data.get("vertices"), list)
            has_predicates = isinstance(data.get("predicates"), list)
            has_ligatures = isinstance(data.get("ligatures"), list)
            if not (has_vertices or has_predicates or has_ligatures):
                return None, "Not a drawing JSON (no vertices/predicates/ligatures)"
            return drawing_to_relational_graph(data), None
        return None, f"Unsupported file type: {suffix}"
    except Exception as e:  # Collect error and continue
        return None, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser(description="Migrate corpus entries to EGI JSON")
    ap.add_argument("--root", default="corpus/corpus", help="Root directory to scan")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing *.egi.json files")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root directory not found: {root}")

    total = 0
    converted = 0
    skipped = 0
    errors = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        # Skip already-converted EGI artifacts as inputs
        if path.name.endswith(".egi.json"):
            continue
        if suffix not in LINEAR_EXTS and suffix not in JSON_EXTS:
            continue
        # Target filename
        out_path = path.with_suffix("")
        out_path = out_path.with_name(out_path.name + ".egi.json")
        total += 1
        if out_path.exists() and not args.overwrite:
            skipped += 1
            continue
        egi, err = parse_file_to_egi(path)
        if egi is None:
            # Treat non-drawing JSON as skipped to avoid noisy errors on metadata files
            if isinstance(err, str) and err.startswith("Not a drawing JSON"):
                skipped += 1
                continue
            errors.append((str(path), err))
            continue
        payload = egi_to_dict(egi)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        converted += 1

    print(f"Processed: {total}, Converted: {converted}, Skipped existing: {skipped}, Errors: {len(errors)}")
    if errors:
        print("\nErrors:")
        for p, err in errors:
            print(f"- {p}: {err}")


if __name__ == "__main__":
    main()
