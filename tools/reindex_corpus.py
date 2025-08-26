#!/usr/bin/env python3
"""
Rebuild corpus/corpus/corpus_index.json by scanning per-entry metadata files.

Rules:
- Include each metadata JSON under --root that is not an .egi.json.
- Infer category from immediate parent directory name.
- Include summary fields useful for browsing and teaching.
- Sort entries by category then id.

Usage:
  python tools/reindex_corpus.py --root corpus/corpus --out corpus/corpus/corpus_index.json
"""
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any


def summarize_entry(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    parent = path.parent.name
    entry = {
        "id": data.get("id", path.stem),
        "category": data.get("category", parent),
        "title": data.get("title"),
        "description": data.get("description"),
        "source": None,
        "logical_pattern": data.get("logical_pattern"),
        "tags": data.get("tags", data.get("topic_tags", [])),
        "path": str(path.relative_to(Path.cwd())) if str(Path.cwd()) in str(path) else str(path),
    }
    src = data.get("source")
    if isinstance(src, dict):
        # Prefer a compact string form if possible
        parts = []
        if src.get("author"): parts.append(src["author"]) 
        if src.get("work"): parts.append(src["work"]) 
        if src.get("year"): parts.append(str(src["year"]))
        if src.get("page"): parts.append(f"p.{src['page']}")
        entry["source"] = ", ".join(parts) if parts else src
    else:
        entry["source"] = src
    return entry


def main():
    ap = argparse.ArgumentParser(description="Rebuild corpus index from entry metadata")
    ap.add_argument("--root", default="corpus/corpus", help="Root directory containing entries")
    ap.add_argument("--out", default="corpus/corpus/corpus_index.json", help="Output index path")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"Root not found: {root}")

    entries: List[Dict[str, Any]] = []
    for p in root.rglob("*.json"):
        # Skip EGI JSONs
        if p.name.endswith(".egi.json"):
            continue
        # Skip index files themselves
        if p.name == "corpus_index.json":
            continue
        try:
            entries.append(summarize_entry(p))
        except Exception as e:
            print(f"Skipping {p}: {e}")

    entries.sort(key=lambda e: (e.get("category") or "", e.get("id") or ""))
    index = {
        "name": "EGRF v3.0 Corpus",
        "description": "Corpus of Existential Graph examples for testing EGRF v3.0",
        "version": "1.0.0",
        "examples": entries,
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote index with {len(entries)} entries to {out_path}")


if __name__ == "__main__":
    main()
