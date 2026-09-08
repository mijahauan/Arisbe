"""The browse index must agree with the records that own the truth.

``GET /organon/uods`` reads ``name``, ``total_states`` and
``total_transformations`` out of ``tomos/index.json``, a cache written at import
time. It drifted: every literature UoD listed under its slug after
``uod.meta.json`` had gained a real title, and all 52 rows reported "1 state /
0 transformations" — including ``theorem_praeclarum``, whose recorded chain is
seven steps. The archive misreported itself as a wall of static pictures, and
no test could see it, because every other test reads the UoD directly rather
than the list.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_tomos_index_is_current():
    """`tools/refresh_tomos_index.py --check` must pass.

    If this fails, a UoD's name or its recorded chain has changed without the
    browse cache being rebuilt. The fix is to run the refresher, not to edit
    index.json by hand.
    """
    proc = subprocess.run(
        [sys.executable, "tools/refresh_tomos_index.py", "--check"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert proc.returncode == 0, (
        "tomos/index.json has drifted from the per-UoD records:\n"
        f"{proc.stdout}\n{proc.stderr}"
    )


def test_worked_derivations_are_visible_in_the_listing():
    """A UoD with a recorded chain must not list as static.

    The count is what tells a reader which entries carry a derivation worth
    stepping through. Reporting 0 for all of them hides the archive's substance
    behind a uniform surface.
    """
    import json
    index = json.loads((REPO / "tomos" / "index.json").read_text())
    rows = {e["uod_id"]: e for e in index["universes"]}

    chained = [
        uid for uid, e in rows.items()
        if (REPO / "tomos" / e["path"] / "history" / "chain.jsonl").exists()
    ]
    assert chained, "no UoD carries a recorded chain — check the corpus layout"

    misreported = [
        uid for uid in chained if rows[uid]["total_transformations"] == 0
    ]
    assert not misreported, (
        f"{len(misreported)} UoD(s) carry a recorded chain but list as having "
        f"no transformations: {sorted(misreported)[:5]}"
    )
