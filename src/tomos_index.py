#!/usr/bin/env python3
"""
Tomos Index utilities for directory-per-graph storage.

Layout:
- tomos/
  - index.json                # lightweight listing for fast browsing
  - graphs/
    - <graph_id>/
      - <graph_id>.egi.json   # canonical EGI source of truth
      - <graph_id>.json       # metadata + generated linear forms references
      - EGDF/                 # derived EGDF documents
      - EXPORTS/              # exported artifacts (tex/pdf/png/txt)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Repository-relative paths
REPO_ROOT = Path(__file__).resolve().parents[1]
TOMOS_ROOT = REPO_ROOT / "tomos"
GRAPH_ROOT = TOMOS_ROOT / "graphs"
INDEX_PATH = TOMOS_ROOT / "index.json"


@dataclass
class CorpusEntry:
    id: str
    title: str
    category: Optional[str]
    tags: List[str]
    path: Path
    updated: Optional[str] = None
    has_egdf: Optional[bool] = None
    has_exports: Optional[bool] = None


def _ensure_dirs() -> None:
    TOMOS_ROOT.mkdir(parents=True, exist_ok=True)
    GRAPH_ROOT.mkdir(parents=True, exist_ok=True)


def load_index() -> Dict[str, Any]:
    _ensure_dirs()
    if INDEX_PATH.exists():
        try:
            return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    # default empty index
    idx = {"name": "Arisbe Tomos", "version": "0.1", "entries": []}
    save_index(idx)
    return idx


def save_index(idx: Dict[str, Any]) -> None:
    _ensure_dirs()
    INDEX_PATH.write_text(json.dumps(idx, indent=2, sort_keys=False), encoding="utf-8")


def list_entries(idx: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    if idx is None:
        idx = load_index()
    return list(idx.get("entries", []))


def upsert_entry(entry: Dict[str, Any]) -> None:
    idx = load_index()
    entries = idx.setdefault("entries", [])
    # replace by id or append
    for i, e in enumerate(entries):
        if e.get("id") == entry.get("id"):
            entries[i] = entry
            break
    else:
        entries.append(entry)
    save_index(idx)


def create_graph_dir(
    graph_id: str,
    title: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Path:
    _ensure_dirs()
    safe_id = graph_id.strip()
    if not safe_id:
        raise ValueError("graph_id must be non-empty")
    gdir = GRAPH_ROOT / safe_id
    gdir.mkdir(parents=True, exist_ok=True)
    (gdir / "EGDF").mkdir(exist_ok=True)
    (gdir / "EXPORTS").mkdir(exist_ok=True)
    # initialize info.json if missing
    info_path = gdir / f"{safe_id}.json"
    now = datetime.now(timezone.utc).isoformat()
    if not info_path.exists():
        info = {
            "id": safe_id,
            "title": title or safe_id,
            "category": category,
            "tags": tags or [],
            "created": now,
            "updated": now,
            "status": "draft",
            "links": {
                "egi": f"{safe_id}.egi.json",
                "egdf_dir": "EGDF/",
                "exports_dir": "EXPORTS/",
            },
        }
        info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    # initialize empty egi.json if missing
    egi_path = gdir / f"{safe_id}.egi.json"
    if not egi_path.exists():
        egi_path.write_text(
            json.dumps(
                {
                    "sheet": "sheet",
                    "V": [],
                    "E": [],
                    "Cut": [],
                    "nu": {},
                    "rel": {},
                    "area": {},
                    "alphabet": None,
                    "rho": {},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    # upsert into index
    entry = {
        "id": safe_id,
        "title": title or safe_id,
        "category": category,
        "tags": tags or [],
        "path": str(gdir.relative_to(REPO_ROOT)),
        "updated": now,
        "has_egdf": False,
        "has_exports": False,
    }
    upsert_entry(entry)
    return gdir


def read_info(gdir: Path) -> Dict[str, Any]:
    """Read the graph's metadata file (<graph_id>.json)."""
    fname = f"{gdir.name}.json"
    return json.loads((gdir / fname).read_text(encoding="utf-8"))


def write_info(gdir: Path, info: Dict[str, Any]) -> None:
    """Write the graph's metadata file (<graph_id>.json), updating timestamp."""
    info["updated"] = datetime.now(timezone.utc).isoformat()
    fname = f"{gdir.name}.json"
    (gdir / fname).write_text(json.dumps(info, indent=2), encoding="utf-8")


def graph_paths(gdir: Path) -> Dict[str, Path]:
    """Return resolved paths for this graph directory with user-preferred naming."""
    return {
        "egi": gdir / f"{gdir.name}.egi.json",
        "info": gdir / f"{gdir.name}.json",
        "egdf_dir": gdir / "EGDF",
        "exports_dir": gdir / "EXPORTS",
    }


def export_path(
    gdir: Path, kind: str, version_hint: Optional[str] = None, ext: str = ""
) -> Path:
    p = graph_paths(gdir)["exports_dir"]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    version = version_hint or ts
    name = f"{kind}@{version}{('.' + ext) if ext else ''}"
    return p / name


def egdf_path(
    gdir: Path, style_id: str, author: str = "auto", version_hint: Optional[str] = None
) -> Path:
    p = graph_paths(gdir)["egdf_dir"]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    version = version_hint or ts
    name = f"{style_id}@{author}@{version}.json"
    return p / name
