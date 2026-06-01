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
from web_api import main as web_main
from web_api.services.introspection import egi_introspection


@pytest.fixture
def client():
    return TestClient(web_main.app)


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
    """DC+ takes a single subgraph selection via ``selected_elements``."""
    resp = client.get("/rules/DC+").json()
    assert resp["success"] is True
    steps = resp["data"]["steps"]
    assert any(s["parameter"] == "selected_elements" for s in steps)
    assert all(s["kind"] == "select_subgraph" for s in steps)


def test_unknown_rule_refused_cleanly(client):
    """An unknown rule returns an UNKNOWN_RULE error, not a 500."""
    resp = client.get("/rules/NOPE").json()
    assert resp["success"] is False
    assert resp["error"]["code"] == "UNKNOWN_RULE"
