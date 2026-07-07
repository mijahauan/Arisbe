"""Repo-relative filesystem roots for the web API.

Historically every route hardcoded the author's absolute corpus path
(``/Users/mjh/Sync/GitHub/Arisbe/tomos``), so a clone on any other machine served
an empty/broken corpus — the app only ran on one laptop. This resolves the roots
**relative to the repository** (this file is ``src/web_api/paths.py``, so the repo
root is ``parents[2]``), with an environment override for a deployment that keeps
its corpus elsewhere:

    ARISBE_TOMOS     — corpus root (default: <repo>/tomos)
    ARISBE_SCRATCH   — regime-1 scratch store (default: <repo>/scratch)

Surfaced 2026-07-07 by the STORM documentation cold-read (audit G6/G9 portability
finding). Additive; no protected module touched.
"""

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

TOMOS_PATH = Path(os.environ.get("ARISBE_TOMOS", _REPO_ROOT / "tomos"))
SCRATCH_PATH = Path(os.environ.get("ARISBE_SCRATCH", _REPO_ROOT / "scratch"))

__all__ = ["TOMOS_PATH", "SCRATCH_PATH"]
