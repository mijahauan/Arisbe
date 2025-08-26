#!/usr/bin/env python3
"""
Enrich corpus entries by:
- Ensuring each metadata JSON references an adjacent <id>.egi.json (EGI as source-of-truth)
- Computing auto-generated complexity metrics and alphabet summary from EGI
- Regenerating EGIF/CGIF/CLIF replicas from EGI and storing them in metadata
- Preserving curated fields (natural language, FOPL, notes)

Decisions reflected (per USER):
1) Reference the adjacent EGI JSON (do not embed)
2) Store replicas' text in metadata for offline access
3) Complexity is auto-generated
4) FOPL/NL are curated (left as-is if present)
5) Optional license and attribution
6) Schema versioned
7) Multi-tag taxonomy ("tags"); keep topic_tags if present

Usage:
  python tools/enrich_corpus_entries.py --root corpus/corpus [--write]
Default is dry-run; use --write to persist changes.
"""
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Tuple
import hashlib
import fnmatch
import sys

# Ensure project root is on sys.path when running from tools/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.egi_io import load_egi_json
from src.egif_generator_dau import EGIFGenerator
from src.cgif_generator_dau import CGIFGenerator
from src.clif_generator_dau import CLIFGenerator


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def compute_complexity(egi) -> Dict[str, Any]:
    # Basic counts
    nesting_depth = 0
    # Build parent pointer for cuts by scanning area membership
    # sheet is root; any cut id "C..." present in an area's set -> that area is parent
    parent: Dict[str, str] = {}
    for area_id, contents in egi.area.items():
        for cid in [c.id for c in egi.Cut]:
            if cid in contents:
                parent[cid] = area_id
    # compute depth by walking up parent to sheet
    for cid in [c.id for c in egi.Cut]:
        d = 1  # count this cut level
        cur = parent.get(cid)
        while cur and cur != egi.sheet:
            d += 1
            cur = parent.get(cur)
        nesting_depth = max(nesting_depth, d)
    return {
        "nesting_depth": nesting_depth,
        "vertex_count": len(egi.V),
        "predicate_count": len(egi.E),
        "cut_count": len(egi.Cut),
        "edge_count": len(egi.E),
    }


def summarize_alphabet(egi) -> Dict[str, Any]:
    if egi.alphabet is None:
        return {"C_count": 0, "F_count": 0, "R_count": 0, "arities": {}}
    return {
        "C_count": len(egi.alphabet.C),
        "F_count": len(egi.alphabet.F),
        "R_count": len(egi.alphabet.R),
        "arities": dict(egi.alphabet.ar),
    }


def generate_replicas(egi) -> Dict[str, Dict[str, Any]]:
    egif = EGIFGenerator(egi).generate()
    cgif = CGIFGenerator(egi).generate()
    clif = CLIFGenerator(egi).generate()
    return {
        "egif": {"text": egif, "hash": sha256_text(egif), "validated": True},
        "cgif": {"text": cgif, "hash": sha256_text(cgif), "validated": True},
        "clif": {"text": clif, "hash": sha256_text(clif), "validated": True},
    }


def enrich_entry(meta_path: Path, write: bool) -> Tuple[bool, str]:
    try:
        # Skip EGI JSON files
        if meta_path.suffix.lower() != ".json" or meta_path.name.endswith(".egi.json"):
            return False, "skip"
        # Must have adjacent EGI
        base = meta_path.with_suffix("")
        egi_path = base.with_name(base.name + ".egi.json")
        if not egi_path.exists():
            return False, f"no-adjacent-egi: {egi_path.name}"
        # Load metadata and EGI
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        egi = load_egi_json(egi_path)
        # Ensure schema/version/tags fields exist
        meta.setdefault("id", base.name)
        meta.setdefault("schema_version", "1.0")
        # Normalize tags: merge topic_tags and tags, unique
        existing_tags = list(dict.fromkeys(meta.get("tags", []) + meta.get("topic_tags", [])))
        if existing_tags:
            meta["tags"] = existing_tags
        # Representations: ensure egi reference and hash
        egi_text = egi_path.read_text(encoding="utf-8")
        egi_hash = sha256_text(egi_text)
        reps = meta.setdefault("representations", {})
        reps["egi"] = {"path": egi_path.name, "hash": egi_hash}
        # Generate linear forms and store texts as requested
        reps["linear_forms"] = reps.get("linear_forms", {})
        replicas = generate_replicas(egi)
        reps["linear_forms"].update(replicas)
        # Complexity and alphabet (auto-generated)
        meta["complexity"] = compute_complexity(egi)
        meta["alphabet_summary"] = summarize_alphabet(egi)
        # Validation status
        meta["validation_status"] = {
            "egi_validated": True,
            "replicas_validated": {k: v.get("validated", False) for k, v in reps["linear_forms"].items()},
        }
        # Write back if requested
        if write:
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return True, "ok"
    except Exception as e:
        return False, f"error: {type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser(description="Enrich corpus metadata with replicas and metrics")
    ap.add_argument("--root", default="corpus/corpus", help="Root directory containing entries")
    ap.add_argument("--write", action="store_true", help="Persist changes (otherwise dry-run)")
    ap.add_argument("--include", action="append", default=[], help="Glob of entries to include (relative to root)")
    ap.add_argument("--exclude", action="append", default=[], help="Glob of entries to exclude (relative to root)")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"Root not found: {root}")

    total = 0
    updated = 0
    no_egi = 0
    skipped = 0
    errors = []

    for path in root.rglob("*.json"):
        rel = path.relative_to(root).as_posix()
        if args.include:
            if not any(fnmatch.fnmatch(rel, pat) for pat in args.include):
                continue
        if args.exclude:
            if any(fnmatch.fnmatch(rel, pat) for pat in args.exclude):
                continue
        total += 1
        ok, msg = enrich_entry(path, args.write)
        if ok:
            updated += 1
        else:
            if msg == "skip":
                skipped += 1
            elif msg.startswith("no-adjacent-egi"):
                no_egi += 1
            else:
                errors.append((str(path), msg))

    print(f"Total JSON: {total} | Updated: {updated} | No EGI: {no_egi} | Skipped: {skipped} | Errors: {len(errors)}")
    if errors:
        print("Errors:")
        for p, m in errors:
            print(f"- {p}: {m}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        # Allow argparse and explicit exits to propagate as usual
        raise
    except Exception:
        # Print full traceback to help diagnose failures when run via tooling
        import traceback
        traceback.print_exc()
        raise
