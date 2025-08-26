#!/usr/bin/env python3
"""
Organon CLI: corpus management for Arisbe.

Subcommands:
  - new:      Create a new corpus entry skeleton (metadata + optional EGI).
  - enrich:   Enrich metadata from adjacent EGI (replicas, metrics).
  - validate: Validate corpus entries for schema/EGI presence.
  - reindex:  Rebuild corpus_index.json from per-entry metadata.
  - migrate:  Convert legacy linear/drawing entries to EGI (.egi.json).

Examples:
  # Create a new entry skeleton under canonical/
  python tools/organon.py new --dir corpus/corpus/canonical --id example_entry --title "Example"

  # Enrich, validate, and reindex the corpus
  python tools/organon.py enrich --root corpus/corpus --write
  python tools/organon.py validate --root corpus/corpus
  python tools/organon.py reindex --root corpus/corpus --out corpus/corpus/corpus_index.json
"""
import argparse
import json
import subprocess
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def run_script(script: str, *args: str) -> int:
    """Run a tool script with arguments, returning return code."""
    cmd = ["python", str(TOOLS / script), *args]
    proc = subprocess.run(cmd, cwd=str(ROOT))
    return proc.returncode


def cmd_new(args: argparse.Namespace) -> None:
    target_dir = Path(args.dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    base = target_dir / args.id
    meta_path = base.with_suffix('.json')
    if meta_path.exists() and not args.overwrite:
        raise SystemExit(f"Metadata already exists: {meta_path} (use --overwrite)")

    metadata = {
        "id": args.id,
        "title": args.title or args.id.replace('_', ' ').title(),
        "description": args.description or "",
        "category": target_dir.name,
        "schema_version": "1.0",
        "tags": args.tags or [],
        "source": {
            "author": args.author or None,
            "work": args.work or None,
            "year": args.year,
            "page": args.page,
        },
        "logical_pattern": args.logical_pattern,
        "notes": args.notes or "",
    }
    # Clean None fields in source
    if isinstance(metadata.get("source"), dict):
        metadata["source"] = {k: v for k, v in metadata["source"].items() if v is not None}
        if not metadata["source"]:
            metadata["source"] = None

    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote metadata: {meta_path}")

    # Optionally place an EGI file
    if args.from_egi:
        src = Path(args.from_egi)
        if not src.exists():
            raise SystemExit(f"--from-egi not found: {src}")
        dest = base.with_suffix('.egi.json')
        dest.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
        print(f"Copied EGI: {dest}")

    # Optionally auto-enrich
    if args.enrich:
        code = run_script("enrich_corpus_entries.py", "--root", str(target_dir), "--write")
        if code != 0:
            raise SystemExit(f"Enrich failed with exit code {code}")


def cmd_enrich(args: argparse.Namespace) -> None:
    cli_args = ["--root", args.root]
    if args.write:
        cli_args.append("--write")
    for pat in args.include or []:
        cli_args += ["--include", pat]
    for pat in args.exclude or []:
        cli_args += ["--exclude", pat]
    code = run_script("enrich_corpus_entries.py", *cli_args)
    raise SystemExit(code)


def cmd_ingest_multi_egif(args: argparse.Namespace) -> None:
    cli = ["--file", args.file]
    if args.outdir:
        cli += ["--outdir", args.outdir]
    if args.prefix:
        cli += ["--prefix", args.prefix]
    if args.overwrite:
        cli.append("--overwrite")
    if args.write:
        cli.append("--write")
    code = run_script("ingest_multi_egif.py", *cli)
    raise SystemExit(code)


def cmd_validate(args: argparse.Namespace) -> None:
    cli = ["--root", args.root]
    for pat in args.include or []:
        cli += ["--include", pat]
    for pat in args.exclude or []:
        cli += ["--exclude", pat]
    code = run_script("validate_corpus.py", *cli)
    raise SystemExit(code)


def cmd_reindex(args: argparse.Namespace) -> None:
    out = args.out or str(Path(args.root) / "corpus_index.json")
    code = run_script("reindex_corpus.py", "--root", args.root, "--out", out)
    raise SystemExit(code)


def cmd_migrate(args: argparse.Namespace) -> None:
    cli = ["--root", args.root]
    if args.overwrite:
        cli.append("--overwrite")
    code = run_script("migrate_corpus_to_egi.py", *cli)
    raise SystemExit(code)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="organon", description="Organon CLI - corpus management for Arisbe")
    sub = p.add_subparsers(dest="cmd", required=True)

    # new
    pn = sub.add_parser("new", help="Create a new corpus entry skeleton")
    pn.add_argument("--dir", required=True, help="Target directory (e.g., corpus/corpus/canonical)")
    pn.add_argument("--id", required=True, help="Entry id / basename")
    pn.add_argument("--title")
    pn.add_argument("--description")
    pn.add_argument("--tags", nargs='*')
    pn.add_argument("--author")
    pn.add_argument("--work")
    pn.add_argument("--year", type=int)
    pn.add_argument("--page")
    pn.add_argument("--logical_pattern")
    pn.add_argument("--notes")
    pn.add_argument("--from-egi", help="Path to an existing .egi.json to copy adjacent to metadata")
    pn.add_argument("--overwrite", action="store_true")
    pn.add_argument("--enrich", action="store_true", help="Run enrichment after creating")
    pn.set_defaults(func=cmd_new)

    # enrich
    pe = sub.add_parser("enrich", help="Enrich metadata from adjacent EGIs")
    pe.add_argument("--root", default="corpus/corpus")
    pe.add_argument("--write", action="store_true")
    pe.add_argument("--include", action="append", default=[], help="Glob of entries to include (relative to root)")
    pe.add_argument("--exclude", action="append", default=[], help="Glob of entries to exclude (relative to root)")
    pe.set_defaults(func=cmd_enrich)

    # validate
    pv = sub.add_parser("validate", help="Validate corpus entries")
    pv.add_argument("--root", default="corpus/corpus")
    pv.add_argument("--include", action="append", default=[], help="Glob of entries to include (relative to root)")
    pv.add_argument("--exclude", action="append", default=[], help="Glob of entries to exclude (relative to root)")
    pv.set_defaults(func=cmd_validate)

    # reindex
    pr = sub.add_parser("reindex", help="Rebuild corpus_index.json")
    pr.add_argument("--root", default="corpus/corpus")
    pr.add_argument("--out")
    pr.set_defaults(func=cmd_reindex)

    # migrate
    pm = sub.add_parser("migrate", help="Convert legacy entries to EGI (.egi.json)")
    pm.add_argument("--root", default="corpus/corpus")
    pm.add_argument("--overwrite", action="store_true")
    pm.set_defaults(func=cmd_migrate)

    # ingest-multi-egif
    pie = sub.add_parser("ingest-multi-egif", help="Split a multi-example .egif file into per-example EGI + metadata")
    pie.add_argument("--file", required=True, help="Path to .egif containing multiple examples")
    pie.add_argument("--outdir", help="Output directory (default: same as input)")
    pie.add_argument("--prefix", help="ID prefix (default: input basename)")
    pie.add_argument("--overwrite", action="store_true")
    pie.add_argument("--write", action="store_true")
    pie.set_defaults(func=cmd_ingest_multi_egif)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
