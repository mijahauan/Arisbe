#!/usr/bin/env python3
"""
Ingest a multi-example EGIF file by splitting it into individual examples,
parsing each snippet into an EGI, and writing adjacent metadata + .egi.json files.

Usage:
  python tools/ingest_multi_egif.py --file corpus/corpus/challenging/classical_syllogisms.egif \
      --outdir corpus/corpus/challenging --prefix classical_syllogisms --write

Defaults:
  - outdir: directory of the input file
  - prefix: basename of the input file without extension
  - dry-run unless --write is specified

Notes:
  - Title is derived from comment headers like '# Example 1: Barbara syllogism' when present.
  - ID is prefix + '_' + a slug from the title if available, otherwise a 1-based index.
  - Category is the name of the outdir.
  - Only minimal metadata is written; run enrich to generate replicas and metrics:
      python tools/organon.py enrich --root <outdir> --include '<prefix>*' --write
"""
import argparse
import json
import re
from pathlib import Path
from typing import List, Tuple, Optional
import sys

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.egif_parser_dau import parse_egif
from src.egi_io import save_egi_json


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "example"


def split_examples(lines: List[str]) -> List[Tuple[str, List[str]]]:
    """Split file lines into examples.
    Returns a list of (title, snippet_lines). Title may be empty.

    Heuristics:
    - Start a new example when encountering a blank line that follows content lines.
    - Comment headers starting with '# Example' or '# #' provide titles.
    - Accumulate leading consecutive comment lines as header for the next snippet.
    """
    examples: List[Tuple[str, List[str]]] = []
    header_comments: List[str] = []
    snippet: List[str] = []

    def finalize_current():
        nonlocal header_comments, snippet
        content = [ln for ln in snippet if ln.strip() and not ln.strip().startswith('#')]
        if content:
            # title from header
            title = ""
            for hc in header_comments:
                m = re.match(r"^#\s*Example\s*[:#-]?\s*(.*)$", hc.strip(), re.IGNORECASE)
                if m:
                    title = m.group(1).strip()
                    break
                # Fallback: take first non-empty comment line without 'Example'
                if not title and hc.strip().startswith('#'):
                    t = hc.strip('#').strip()
                    if t:
                        title = t
                        # don't break; prefer an 'Example' line if it appears later
            examples.append((title, snippet.copy()))
        header_comments = []
        snippet = []

    seen_content = False
    for raw in lines:
        line = raw.rstrip('\n')
        if not seen_content:
            if line.strip().startswith('#'):
                header_comments.append(line)
                continue
            if not line.strip():
                # still in prelude
                continue
            # first content line
            seen_content = True

        # Once content has started, collect lines until a blank line that separates examples
        if line.strip() == "":
            # Potential boundary: finalize if snippet has any content
            finalize_current()
            seen_content = False  # allow collecting a new header for next example
            continue

        snippet.append(line)

    # Final snippet
    finalize_current()
    return examples


def build_metadata(outdir: Path, entry_id: str, title: str, description: Optional[str]) -> dict:
    return {
        "id": entry_id,
        "title": title or entry_id.replace('_', ' ').title(),
        "description": description or "",
        "category": outdir.name,
        "schema_version": "1.0",
        "tags": [],
        "source": None,
        "logical_pattern": None,
        "notes": "",
    }


def main():
    ap = argparse.ArgumentParser(description="Ingest a multi-example EGIF file into per-example EGI + metadata")
    ap.add_argument("--file", required=True, help="Path to .egif file containing multiple examples")
    ap.add_argument("--outdir", help="Directory to write outputs (default: same as input)")
    ap.add_argument("--prefix", help="Prefix for generated IDs (default: basename of input)")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing metadata/EGI files")
    ap.add_argument("--write", action="store_true", help="Persist outputs (default: dry-run)")
    args = ap.parse_args()

    in_path = Path(args.file)
    if not in_path.exists():
        raise SystemExit(f"Input not found: {in_path}")
    outdir = Path(args.outdir) if args.outdir else in_path.parent
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or in_path.stem

    lines = in_path.read_text(encoding='utf-8').splitlines()
    examples = split_examples(lines)

    if not examples:
        print("No examples found (nothing to do).")
        return 0

    print(f"Found {len(examples)} examples in {in_path}.")

    written = 0
    for idx, (title, snippet_lines) in enumerate(examples, start=1):
        text = "\n".join(snippet_lines).strip()
        # Parse to EGI
        try:
            graph = parse_egif(text)
        except Exception as e:
            print(f"- [{idx}] ERROR parsing snippet: {e}")
            continue

        # Determine ID
        slug = slugify(title) if title else f"ex{idx}"
        entry_id = f"{prefix}_{slug}"
        base = outdir / entry_id
        meta_path = base.with_suffix('.json')
        egi_path = base.with_suffix('.egi.json')

        if not args.overwrite and (meta_path.exists() or egi_path.exists()):
            print(f"- [{idx}] Skip existing: {entry_id}")
            continue

        # Build minimal metadata; enrichment will fill replicas and metrics
        metadata = build_metadata(outdir, entry_id, title, description=None)

        if args.write:
            meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
            save_egi_json(graph, egi_path)
            print(f"- [{idx}] Wrote {meta_path.name} and {egi_path.name}")
            written += 1
        else:
            print(f"- [{idx}] Would write {meta_path.name} and {egi_path.name}")

    print(f"Done. Examples processed: {len(examples)}, written: {written} (dry-run={not args.write}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
