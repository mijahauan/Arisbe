"""
Tests for the HTTP selection-introspection additions (Task 1, 2026-06-01).

The Ergasterion dogfood (memory ``project-ergasterion-dogfood-findings``)
identified two gaps that blocked fluent, selection-driven rule
application over HTTP and that Agon (the selection-heavy arena) will
lean on hardest:

  1. **No area/polarity introspection** — a client could not tell which
     area an element lived in, nor that area's polarity, without
     inferring it from geometry.  Now ``egi_introspection`` exposes it
     and the Ergasterion session payload carries an ``introspection``
     block.
  2. **Rule requirements undiscoverable** — ``RuleInteraction.steps()``
     declared each rule's inputs but they were not served.  Now
     ``GET /rules`` (and ``/rules/{rule}``) describe them, including the
     request field a client should populate for each step.

These tests pin the contract.  Both additions are read-only and
additive — they make no claim about §3.3 correspondence.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from tomos_service import TomosService
from web_api import main as web_main
from web_api.routes import introspect as introspect_route
from web_api.services.introspection import egi_introspection


@pytest.fixture
def client():
    return TestClient(web_main.app)


@pytest.fixture
def isolated_tomos(tmp_path, monkeypatch):
    """A throwaway corpus seeded with one real UoD, wired into the
    /introspect route so the uod_id path is testable without touching the
    real tomos."""
    tmp = tmp_path / "tomos"
    tmp.mkdir(parents=True)
    fresh = TomosService(tmp)
    real = TomosService(Path(__file__).parent.parent / "tomos")
    uod_ids = [u["uod_id"] for u in real.list_uods()]
    seed = next((c for c in ["theorem_praeclarum", "beta_modus_ponens"] if c in uod_ids), uod_ids[0])
    fresh.save_uod(real.load_uod(seed))
    monkeypatch.setattr(introspect_route, "_tomos_service", fresh)
    return {"service": fresh, "seed_id": seed}


# --------------------------------------------------------------------------- #
# egi_introspection — unit                                                    #
# --------------------------------------------------------------------------- #


def test_introspection_sheet_only_is_positive():
    """An empty sheet is a single positive area at depth 0, no parent."""
    egi = parse_egif("")
    intro = egi_introspection(egi)

    assert egi.sheet in intro["areas"]
    sheet = intro["areas"][egi.sheet]
    assert sheet["polarity"] == "positive"
    assert sheet["depth"] == 0
    assert sheet["parent"] is None
    assert sheet["is_sheet"] is True


def test_introspection_cut_interior_is_negative():
    """``~[ (mortal *x) ]`` — the cut interior is negative (verso, depth 1),
    and the vertex + edge inside it report that polarity."""
    egi = parse_egif("~[ (mortal *x) ]")
    intro = egi_introspection(egi)

    # Exactly one cut; its interior is negative at depth 1, sitting on the
    # (positive) sheet.
    assert len(egi.Cut) == 1
    cut = next(iter(egi.Cut))
    cut_area = intro["areas"][cut.id]
    assert cut_area["polarity"] == "negative"
    assert cut_area["depth"] == 1
    assert cut_area["parent"] == egi.sheet
    assert cut_area["is_sheet"] is False

    # The cut-as-element sits in the positive sheet.
    cut_elem = intro["elements"][cut.id]
    assert cut_elem["type"] == "cut"
    assert cut_elem["area"] == egi.sheet
    assert cut_elem["polarity"] == "positive"

    # The vertex and edge live inside the cut → negative.
    vertex = next(iter(egi.V))
    edge = next(iter(egi.E))
    assert intro["elements"][vertex.id]["type"] == "vertex"
    assert intro["elements"][vertex.id]["area"] == cut.id
    assert intro["elements"][vertex.id]["polarity"] == "negative"
    assert intro["elements"][edge.id]["type"] == "edge"
    assert intro["elements"][edge.id]["area"] == cut.id
    assert intro["elements"][edge.id]["polarity"] == "negative"


def test_introspection_covers_every_element():
    """Every vertex, edge, and cut appears exactly once in ``elements``;
    the sheet and every cut appear in ``areas``."""
    egi = parse_egif("(man *x) ~[ (mortal x) ~[ (happy x) ] ]")
    intro = egi_introspection(egi)

    expected_elements = (
        {v.id for v in egi.V} | {e.id for e in egi.E} | {c.id for c in egi.Cut}
    )
    assert set(intro["elements"].keys()) == expected_elements

    expected_areas = {egi.sheet} | {c.id for c in egi.Cut}
    assert set(intro["areas"].keys()) == expected_areas

    # Nesting alternates: sheet positive, first cut negative, inner cut
    # positive again.
    depths = {rec["depth"]: rec["polarity"] for rec in intro["areas"].values()}
    assert depths[0] == "positive"
    assert depths[1] == "negative"
    assert depths[2] == "positive"


# --------------------------------------------------------------------------- #
# Content layer — relation / label / incidence (the "what")                   #
# --------------------------------------------------------------------------- #


def test_introspection_exposes_edge_content():
    """Each edge carries its relation name, arity, and incident vertices (ν
    order) — so a client can name "the edge P" / select by relation."""
    egi = parse_egif("(R *x *y) (S y x)")
    intro = egi_introspection(egi)
    edges = {
        rec["relation"]: rec
        for rec in intro["elements"].values()
        if rec["type"] == "edge"
    }
    assert set(edges) == {"R", "S"}
    assert edges["R"]["arity"] == 2
    assert len(edges["R"]["incident_vertices"]) == 2
    # R(x,y) and S(y,x) share the two lines in *swapped* order — the content
    # a client uses to detect that the two lines cross (the bridge case),
    # entirely from structure, no pixels.
    assert edges["R"]["incident_vertices"] == edges["S"]["incident_vertices"][::-1]


def test_introspection_exposes_vertex_label():
    """A named line of identity reports its label; an anonymous one reports
    ``None`` — the ``label`` key is always present so a client can rely on the
    shape."""
    named = egi_introspection(parse_egif('(P "Socrates")'))
    named_v = [r for r in named["elements"].values() if r["type"] == "vertex"]
    assert len(named_v) == 1 and named_v[0]["label"] == "Socrates"

    anon = egi_introspection(parse_egif("(P *x)"))
    anon_v = [r for r in anon["elements"].values() if r["type"] == "vertex"]
    assert len(anon_v) == 1 and anon_v[0]["label"] is None  # key present, value None


# --------------------------------------------------------------------------- #
# /introspect endpoint                                                        #
# --------------------------------------------------------------------------- #


def test_introspect_endpoint_from_egif(client):
    """``POST /introspect`` with inline text returns areas + content-bearing
    elements for an arbitrary graph (no session needed)."""
    resp = client.post(
        "/introspect", json={"text": "(R *x *y) ~[ (S y x) ]"}
    ).json()
    assert resp["success"] is True
    data = resp["data"]
    assert "areas" in data and "elements" in data
    rels = {
        r["relation"] for r in data["elements"].values() if r["type"] == "edge"
    }
    assert rels == {"R", "S"}
    # S sits inside the cut → negative; R on the sheet → positive.
    by_rel = {
        r["relation"]: r for r in data["elements"].values() if r["type"] == "edge"
    }
    assert by_rel["R"]["polarity"] == "positive"
    assert by_rel["S"]["polarity"] == "negative"


def test_introspect_endpoint_from_uod(client, isolated_tomos):
    """The ``uod_id`` source path introspects a corpus UoD's current EGI."""
    resp = client.post(
        "/introspect", json={"uod_id": isolated_tomos["seed_id"]}
    ).json()
    assert resp["success"] is True
    assert len(resp["data"]["elements"]) > 0


def test_introspect_endpoint_error_paths(client):
    """No source, unknown notation, parse error, and unknown UoD each refuse
    cleanly (no 500)."""
    assert client.post("/introspect", json={}).json()["error"]["code"] == "NO_SOURCE"
    assert client.post(
        "/introspect", json={"text": "(P)", "notation": "xyz"}
    ).json()["error"]["code"] == "BAD_NOTATION"
    assert client.post(
        "/introspect", json={"text": "(P"}
    ).json()["error"]["code"] == "PARSE_ERROR"
    assert client.post(
        "/introspect", json={"uod_id": "does-not-exist"}
    ).json()["error"]["code"] == "UOD_NOT_FOUND"


# --------------------------------------------------------------------------- #
# Ergasterion session payload carries the introspection block                 #
# --------------------------------------------------------------------------- #


def test_session_payload_includes_introspection(client):
    """Opening a workshop session returns an ``introspection`` block whose
    elements match the rendered EGI."""
    opened = client.post(
        "/ergasterion/sessions", json={"base_source": "empty_sheet"}
    ).json()
    assert opened["success"] is True
    data = opened["data"]
    assert "introspection" in data
    intro = data["introspection"]
    assert "areas" in intro and "elements" in intro
    # Empty sheet: one positive area, no elements.
    assert len(intro["areas"]) == 1
    assert next(iter(intro["areas"].values()))["polarity"] == "positive"
    assert intro["elements"] == {}

    # Clean up.
    client.delete(f"/ergasterion/sessions/{data['session_id']}")


def test_session_payload_introspection_carries_content_layer(client):
    """After composing some content, the payload's introspection exposes the
    *content* the click-to-select UI binds to — each edge's relation,
    polarity, and arity — so the selection bar can name "P (negative)" rather
    than echo a raw id. Self-contained: builds the content via apply, no
    corpus dependency."""
    opened = client.post(
        "/ergasterion/sessions", json={"base_source": "empty_sheet"}
    ).json()
    sid = opened["data"]["session_id"]
    try:
        # DC+ → ~[ ~[ ] ]; INS (P) into the outer (negative, depth-1) cut.
        after_dc = client.post(
            f"/ergasterion/sessions/{sid}/apply",
            json={"rule": "DC+", "parameters": {"selected_elements": []}},
        ).json()
        assert after_dc["success"], after_dc
        areas = after_dc["data"]["introspection"]["areas"]
        neg_cut = next(
            aid for aid, a in areas.items()
            if a["polarity"] == "negative" and a["depth"] == 1
        )
        after_ins = client.post(
            f"/ergasterion/sessions/{sid}/apply",
            json={"rule": "INS",
                  "parameters": {"egif_content": "(P)", "target_area": neg_cut}},
        ).json()
        assert after_ins["success"], after_ins

        edges = [
            e for e in after_ins["data"]["introspection"]["elements"].values()
            if e["type"] == "edge"
        ]
        p = next(e for e in edges if e.get("relation") == "P")
        assert p["polarity"] == "negative"        # it sits in the verso cut
        assert p["arity"] == 0                      # a propositional medad
        assert "incident_vertices" in p
    finally:
        client.delete(f"/ergasterion/sessions/{sid}")


# --------------------------------------------------------------------------- #
# /rules — rule requirements                                                  #
# --------------------------------------------------------------------------- #


def test_list_rules_covers_all_six(client):
    """``GET /rules`` lists all six Dau rules with step descriptors."""
    resp = client.get("/rules").json()
    assert resp["success"] is True
    by_name = {r["rule"]: r for r in resp["data"]}
    assert set(by_name.keys()) == {"DC+", "DC-", "ERA", "INS", "IT+", "IT-"}

    # Every step carries id/kind/prompt/optional/parameter.
    for descriptor in resp["data"]:
        for step in descriptor["steps"]:
            assert set(step.keys()) == {
                "step_id",
                "kind",
                "prompt",
                "optional",
                "parameter",
            }


def test_ins_is_two_step_with_egif_and_target_area(client):
    """INS declares two steps: provide EGIF content, then a target area —
    with the request field names a client must populate."""
    resp = client.get("/rules/INS").json()
    assert resp["success"] is True
    steps = resp["data"]["steps"]
    params = [s["parameter"] for s in steps]
    kinds = [s["kind"] for s in steps]
    assert "provide_egif" in kinds
    assert "select_area" in kinds
    assert "egif_content" in params
    assert "target_area" in params


def test_dc_plus_uses_selected_elements(client):
    """DC+ takes a subgraph selection (the Subject) and an optional spot.

    Following the Spot/Subject grammar, DC+ accepts a subgraph to enclose plus
    an optional ``target_area`` spot — selecting a spot with no Subject inserts
    an empty double cut around nothing there.
    """
    resp = client.get("/rules/DC+").json()
    assert resp["success"] is True
    steps = resp["data"]["steps"]
    kinds = {s["kind"] for s in steps}
    params = {s["parameter"] for s in steps}
    assert "select_subgraph" in kinds
    assert "selected_elements" in params
    # The spot step (for an empty double cut in a chosen area) is present.
    assert "select_area" in kinds
    assert "target_area" in params


def test_unknown_rule_refused_cleanly(client):
    """An unknown rule returns an UNKNOWN_RULE error, not a 500."""
    resp = client.get("/rules/NOPE").json()
    assert resp["success"] is False
    assert resp["error"]["code"] == "UNKNOWN_RULE"
