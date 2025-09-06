#!/usr/bin/env python3
"""
Migrate legacy corpus in corpus/corpus/ (category folders with .egif/.cgif/.clif)
into the new directory-per-graph layout under corpus/graphs/ using corpus_index.

For each legacy EGIF example:
- Determine graph_id from filename stem
- Create corpus/graphs/<graph_id>/ using corpus_index.create_graph_dir()
- Parse EGIF -> EGI and save to <graph_id>.egi.json (canonical)
- Generate CLIF and CGIF content dynamically from EGI
- Write metadata + generated linear forms into <graph_id>.json
- Optionally copy EGDF/EXPORTS if any are found later (not in legacy layout)

After migration, legacy corpus/corpus/ is considered deprecated.
"""
from __future__ import annotations

import sys
import json
from dataclasses import asdict
from pathlib import Path
from datetime import datetime, timezone

# Ensure src is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / 'src'))

from corpus_index import create_graph_dir, read_info, write_info, graph_paths, CORPUS_ROOT  # type: ignore
from egif_parser_dau import parse_egif  # type: ignore
from egif_generator_dau import generate_egif  # type: ignore
from clif_generator_dau import generate_clif  # type: ignore
from cgif_generator_dau import generate_cgif  # type: ignore
from egi_io import save_egi_json  # type: ignore

LEGACY_ROOT = ROOT / 'corpus' / 'corpus'
NEW_GRAPH_ROOT = ROOT / 'corpus' / 'graphs'


def extract_egif_content(file_path: Path) -> str:
    """Read EGIF file content, stripping comment lines beginning with '#'."""
    lines = file_path.read_text(encoding='utf-8').splitlines()
    egif_lines = []
    for line in lines:
        s = line.strip()
        if s and not s.startswith('#'):
            egif_lines.append(s)
    return ' '.join(egif_lines)


def extract_metadata_from_egif(file_path: Path) -> dict:
    meta: dict = {}
    for raw in file_path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line.startswith('#'):
            break
        # Remove leading '#'
        body = line[1:].strip()
        if ':' not in body:
            continue
        key, val = body.split(':', 1)
        key = key.strip().lower()
        val = val.strip()
        if key == 'category':
            meta['category'] = val
        elif key == 'description':
            meta['description'] = val
        elif key == 'source':
            meta['source'] = val
        elif key == 'pattern':
            meta['logical_pattern'] = val
    return meta


def migrate() -> None:
    if not LEGACY_ROOT.exists():
        print(f"No legacy corpus found at {LEGACY_ROOT}")
        return

    egif_files = sorted(LEGACY_ROOT.rglob('*.egif'))
    print(f"Found {len(egif_files)} legacy EGIF files to migrate.")

    migrated = 0
    errors = 0

    for egif_path in egif_files:
        graph_id = egif_path.stem
        rel = egif_path.relative_to(LEGACY_ROOT)
        print(f"→ Migrating {rel}")
        try:
            # Read content and metadata
            egif_content = extract_egif_content(egif_path)
            file_meta = extract_metadata_from_egif(egif_path)
            if not egif_content:
                raise ValueError('Empty EGIF content')

            # Parse EGIF to EGI
            egi = parse_egif(egif_content)

            # Create graph directory (idempotent)
            gdir = create_graph_dir(graph_id, title=file_meta.get('title', graph_id), category=file_meta.get('category'), tags=[])

            # Save canonical EGI
            paths = graph_paths(gdir)
            save_egi_json(egi, paths['egi'])

            # Generate other linear forms from canonical EGI
            clif_content = generate_clif(egi)
            cgif_content = generate_cgif(egi)
            # Ensure we also have a normalized EGIF string
            egif_norm = generate_egif(egi)

            # Prepare metadata payload for <graph>.json
            try:
                info = read_info(gdir)
            except Exception:
                info = {
                    'id': graph_id,
                    'title': file_meta.get('title', graph_id),
                    'category': file_meta.get('category'),
                    'tags': [],
                    'status': 'draft',
                    'created': datetime.now(timezone.utc).isoformat(),
                    'updated': datetime.now(timezone.utc).isoformat(),
                    'links': {
                        'egi': f'{graph_id}.egi.json',
                        'egdf_dir': 'EGDF/',
                        'exports_dir': 'EXPORTS/'
                    }
                }

            # Embed generated linear forms (read-only convenience; source of truth is EGI)
            info['linear_forms'] = {
                'egif': {
                    'content': egif_norm,
                    'source': 'generated',
                },
                'clif': {
                    'content': clif_content,
                    'source': 'generated',
                },
                'cgif': {
                    'content': cgif_content,
                    'source': 'generated',
                },
            }

            # Carry over descriptive fields if present
            if file_meta.get('description'):
                info['description'] = file_meta['description']
            if file_meta.get('source'):
                info['source'] = file_meta['source']
            if file_meta.get('logical_pattern'):
                info['logical_pattern'] = file_meta['logical_pattern']

            write_info(gdir, info)

            migrated += 1
            print(f"   ✅ Migrated → corpus/graphs/{graph_id}/")
        except Exception as e:
            errors += 1
            print(f"   ❌ ERROR: {e}")

    print()
    print("Migration summary:")
    print(f"  Total EGIF: {len(egif_files)}")
    print(f"  Migrated:   {migrated}")
    print(f"  Errors:     {errors}")
    if migrated:
        print(f"  New layout root: {NEW_GRAPH_ROOT}")
    if errors:
        print("Some items failed to migrate; see messages above.")


if __name__ == '__main__':
    migrate()
