"""The browse listing must report the corpus as it actually is.

``GET /organon/uods`` reads ``name``, ``total_states`` and
``total_transformations``. Those were cached in ``tomos/index.json`` at import
time and drifted: every literature UoD listed under its slug after
``uod.meta.json`` had gained a real title, and all 52 rows reported "1 state /
0 transformations" — including ``theorem_praeclarum``, whose recorded chain is
seven steps. The archive misreported itself as a wall of static pictures.

Refreshing the file alone did not hold, because ``TomosService`` rewrites the
index from its own in-memory copy and put the stale values straight back. So
these fields are now overlaid at read time from the records that own them
(``TomosService._freshen``), and the index is a path cache.

These tests assert the served result, not the cache, because the served result
is what a reader sees and what the drift corrupted.
"""

from pathlib import Path

import pytest

from tomos_service import TomosService

REPO = Path(__file__).resolve().parent.parent
TOMOS = REPO / "tomos"


@pytest.fixture(scope="module")
def rows():
    return {e["uod_id"]: e for e in TomosService(TOMOS).list_uods()}


def test_a_uod_with_a_recorded_chain_never_lists_as_static(rows):
    """The count is what tells a reader which entries carry a derivation."""
    misreported = []
    for uid, e in rows.items():
        chain = TOMOS / e["path"] / "history" / "chain.jsonl"
        if chain.exists() and e["total_transformations"] == 0:
            misreported.append(uid)
    assert not misreported, (
        f"{len(misreported)} UoD(s) carry a recorded chain but list as having "
        f"no transformations: {sorted(misreported)[:5]}"
    )


def test_the_worked_corpus_is_visible(rows):
    """Enough of the archive shows its work that the listing is informative."""
    worked = [uid for uid, e in rows.items() if e["total_transformations"] > 0]
    assert len(worked) >= 30, (
        f"only {len(worked)} of {len(rows)} UoDs report a derivation; the "
        f"corpus carries far more than that"
    )
    # The longest chains are the ones a reviewer should be able to find.
    assert rows["theorem_praeclarum"]["total_transformations"] >= 7
    assert rows["swan_alternatives"]["total_transformations"] >= 10


def test_no_uod_lists_under_its_slug(rows):
    """No entry may be listed under its own identifier.

    "Sowa Cat On Mat" is what a slug looks like title-cased, and it is what
    John Sowa would have seen first. Two ways this regresses: a record loses
    its curated name, or the listing stops reading the record. Both are caught
    here, because the assertion is about the *name a reader sees*, not about
    agreement between two places that can be wrong together.
    """
    import json
    slugged = []
    for uid, e in rows.items():
        name = e.get("name") or ""
        if name == uid or name == uid.replace("_", " ").title():
            slugged.append(f"{uid} lists as {name!r}")
    assert not slugged, (
        f"{len(slugged)} UoD(s) list under their slug:\n"
        + "\n".join(slugged[:6])
    )


def test_the_listing_agrees_with_the_records(rows):
    """A curated name in uod.meta.json must reach the listing."""
    import json
    disagree = []
    for uid, e in rows.items():
        meta_path = TOMOS / e["path"] / "uod.meta.json"
        if not meta_path.exists():
            continue
        curated = json.loads(meta_path.read_text()).get("name")
        if curated and e["name"] != curated:
            disagree.append(f"{uid}: listing {e['name']!r} != record {curated!r}")
    assert not disagree, "the listing disagrees with the records:\n" + "\n".join(disagree[:5])
