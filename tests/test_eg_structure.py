"""
Tests for the coordinate-free structure endpoint (the adaptive-scope viewer spike).

`src/eg_structure.py` + the Organon routes `GET /organon/uods/{id}/structure` and
`POST /organon/structure` produce the projection-independent facts every candidate
projection realizes: containment tree + polarity + depth, recursive content counts, and
per-ligature required crossing-sequences. The contract under test:

1. structure of a known nested EGIF is correct (tree, depth/polarity, counts, crossings);
2. `subtree_summary` counts recursively;
3. both routes return well-formed structure JSON;
4. it is **O(n), not geometric** — even the corpus's biggest graph builds far faster than
   a layout would (the perf-frontier win), and the route never runs a layout engine.
"""

import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from eg_structure import egi_structure, subtree_summary
from tomos_service import TomosService
from web_api import main as web_main

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"

# ∀x (P(x) → ¬∃(Q(x) ∧ R(x))) shape — three nested cuts, one shared line.
NESTED = "~[ [*x] (P x) ~[ (Q x) ~[ (R x) ] ] ]"


@pytest.fixture(scope="module")
def client():
    return TestClient(web_main.app)


@pytest.fixture(scope="module")
def corpus_ids():
    return [u["uod_id"] for u in TomosService(TOMOS_ROOT).list_uods()]


def test_structure_of_nested_egif():
    s = egi_structure(parse_egif(NESTED))
    assert s["counts"] == {"areas": 4, "cuts": 3, "vertices": 1, "predicates": 3, "max_depth": 3}
    # depth → polarity parity: sheet/2 positive, 1/3 negative.
    by_depth = {a["depth"]: a["polarity"] for a in s["areas"]}
    assert by_depth == {0: "positive", 1: "negative", 2: "positive", 3: "negative"}
    # the sheet has exactly one child cut; nesting is a chain.
    sheet = next(a for a in s["areas"] if a["kind"] == "sheet")
    assert len(sheet["child_cuts"]) == 1
    assert sheet["summary"] == {"cuts": 3, "vertices": 1, "predicates": 3}


def test_crossing_sequences_grow_with_depth():
    """The shared line x reaches P (depth 1), Q (depth 2), R (depth 3); the deeper the
    predicate, the more cut boundaries its ligature must cross."""
    s = egi_structure(parse_egif(NESTED))
    name = {p["id"]: p["name"] for p in s["predicates"]}
    crossings = {name[l["predicate_id"]]: len(l["crossings"]) for l in s["ligatures"]}
    assert crossings["P"] < crossings["Q"] < crossings["R"]


def test_subtree_summary_recursive():
    egi = parse_egif(NESTED)
    # the innermost cut (holds only R) summarizes to one predicate, nothing nested.
    inner = next(a for a in egi_structure(egi)["areas"]
                 if a["summary"] == {"cuts": 0, "vertices": 0, "predicates": 1})
    assert subtree_summary(egi, inner["id"]) == {"cuts": 0, "vertices": 0, "predicates": 1}


def test_route_structure_from_egif(client):
    r = client.post("/organon/structure", json={"egif": NESTED})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["structure"]["counts"]["cuts"] == 3


def test_route_empty_egif_refused(client):
    body = client.post("/organon/structure", json={"egif": "  "}).json()
    assert body["success"] is False and body["error"]["code"] == "EMPTY_EGIF"


def test_route_uod_structure(client, corpus_ids):
    assert corpus_ids, "tomos corpus is empty"
    uid = "porphyry_tree" if "porphyry_tree" in corpus_ids else corpus_ids[0]
    body = client.get(f"/organon/uods/{uid}/structure").json()
    assert body["success"] is True
    s = body["data"]["structure"]
    assert s["counts"]["areas"] >= 1
    assert all("depth" in a and "polarity" in a for a in s["areas"])


def test_structure_is_cheap_on_the_biggest_uod(corpus_ids):
    """The whole point: structure is O(n), not a layout. The biggest corpus graph
    builds in well under a second — where ELK is super-linear (seconds to ~74s)."""
    tomos = TomosService(TOMOS_ROOT)
    biggest, n = None, -1
    for uid in corpus_ids:
        u = tomos.load_uod(uid, attest=False)
        if u and u.current_egi and len(u.current_egi.Cut) > n:
            biggest, n = u.current_egi, len(u.current_egi.Cut)
    assert biggest is not None
    t0 = time.time()
    s = egi_structure(biggest)
    assert time.time() - t0 < 0.5
    assert s["counts"]["cuts"] == n
