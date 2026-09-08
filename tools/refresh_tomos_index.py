#!/usr/bin/env python3
"""Rebuild ``tomos/index.json`` from the per-UoD records that own the truth.

The index is a browse cache: ``GET /organon/uods`` reads ``name``,
``total_states`` and ``total_transformations`` straight out of it. Those fields
were written once at import and never refreshed, so the archive misreported
itself in two visible ways:

* every literature UoD listed under its slug, even after ``uod.meta.json``
  carried a real title — "Sowa Cat On Mat" rather than "Sowa's Cat on a Mat";
* all 52 rows claimed "1 state / 0 transformations", including
  ``theorem_praeclarum``, whose recorded chain is seven steps long. A reader
  scanning the list saw a wall of apparently static pictures and had no way to
  tell which ones carry a worked derivation.

Authority: ``<uod>/uod.meta.json`` for identity, ``<uod>/history/chain.jsonl``
for the counts. Nothing here invents a value — a UoD with no chain keeps one
state and no transformations, which is the truth about it.

Usage:
    uv run python tools/refresh_tomos_index.py [--check]

``--check`` reports drift and exits non-zero without writing, for CI.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOMOS = REPO / "tomos"
SHELVES = ("universes", "literature", "graphs")


def _chain_counts(uod_dir: Path) -> tuple[int, int]:
    """(total_states, total_transformations) read from the recorded chain."""
    chain = uod_dir / "history" / "chain.jsonl"
    if not chain.exists():
        return 1, 0
    states: set[str] = set()
    steps = 0
    for line in chain.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") == "initial":
            if rec.get("initial_state_id"):
                states.add(rec["initial_state_id"])
        elif rec.get("type") == "step":
            steps += 1
            for key in ("from_state_id", "to_state_id"):
                if rec.get(key):
                    states.add(rec[key])
    return (len(states) or 1), steps


def build_entries() -> list[dict]:
    entries: list[dict] = []
    for shelf in SHELVES:
        shelf_dir = TOMOS / shelf
        if not shelf_dir.is_dir():
            continue
        for uod_dir in sorted(p for p in shelf_dir.iterdir() if p.is_dir()):
            meta_path = uod_dir / "uod.meta.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            states, steps = _chain_counts(uod_dir)
            entries.append({
                "uod_id": meta.get("uod_id", uod_dir.name),
                "name": meta.get("name") or uod_dir.name,
                "category": meta.get("category", ""),
                "uod_type": meta.get("uod_type", "standalone"),
                "is_static": steps == 0,
                "is_dynamic": steps > 0,
                "created": meta.get("created", ""),
                "last_modified": meta.get("last_modified", ""),
                "total_states": states,
                "total_transformations": steps,
                "authors": meta.get("authors", []),
                "tags": meta.get("tags", []),
                "path": f"{shelf}/{uod_dir.name}",
            })
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report drift and exit non-zero without writing")
    args = ap.parse_args()

    index_path = TOMOS / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    fresh = build_entries()
    current = {e.get("uod_id"): e for e in index.get("universes", [])}

    drift = []
    for e in fresh:
        old = current.get(e["uod_id"])
        if old is None:
            drift.append(f"  + {e['uod_id']} (absent from the index)")
            continue
        for field in ("name", "total_states", "total_transformations"):
            if old.get(field) != e[field]:
                drift.append(
                    f"  ~ {e['uod_id']}.{field}: {old.get(field)!r} -> {e[field]!r}")
    for uid in current:
        if uid not in {e["uod_id"] for e in fresh}:
            drift.append(f"  - {uid} (in the index, absent on disk)")

    if args.check:
        if drift:
            print(f"tomos/index.json is stale in {len(drift)} field(s):")
            print("\n".join(drift[:40]))
            print("\nRun: uv run python tools/refresh_tomos_index.py")
            return 1
        print("tomos/index.json is current.")
        return 0

    if not drift:
        print("tomos/index.json is current; nothing to write.")
        return 0

    index["universes"] = fresh
    index["last_updated"] = datetime.now(timezone.utc).isoformat()
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"tomos/index.json refreshed — {len(drift)} field(s) corrected:")
    print("\n".join(drift[:40]))
    if len(drift) > 40:
        print(f"  ... and {len(drift) - 40} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
