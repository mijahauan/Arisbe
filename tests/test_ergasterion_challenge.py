"""Tests for challenge-mode routes (correspondence, learned by doing — build step 4).

docs/FREEFORM_COMPOSITION_AND_LEARNING.md

- ``GET /ergasterion/challenges`` — the difficulty gradient (prompts only, no drawing).
- ``POST /ergasterion/sessions/{id}/grade-challenge`` — read a freehand drawing and
  grade it against a target with the legible diff; ill-formed ink returns validity
  feedback (not a grade); the session is never mutated.

The drawing JSON is produced the same way the freeform round-trip tests produce it —
render a known EGI's faithful ink — so a faithful drawing of the *target* grades as a
match, and a faithful drawing of a *different* graph fails with EG-vocabulary findings.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from eg_reader import assign_order_labels
from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
from presentation_ops import cut_boundary, resolve_cut_boundaries
from style_loader import load_default_style
from web_api import main as web_main
from web_api.routes import ergasterion as ergasterion_route
from web_api.services.ergasterion_session_manager import ErgasterionSessionManager


@pytest.fixture
def client():
    return TestClient(web_main.app)


@pytest.fixture(autouse=True)
def fresh_manager(monkeypatch):
    mgr = ErgasterionSessionManager()
    monkeypatch.setattr(
        ergasterion_route, "get_ergasterion_session_manager", lambda: mgr)
    return mgr


def _drawing_from_egi(egif: str):
    """The faithful ink of an EGI, as the canvas would post it."""
    egi = parse_egif(egif)
    style = load_default_style()
    dto = assign_order_labels(egi, ELKLayoutEngine().generate_layout(egi, style))
    boundaries = resolve_cut_boundaries(dto)

    vertices = []
    for vid, p in dto.vertex_positions.items():
        v = next(v for v in egi.V if v.id == vid)
        vertices.append({"id": vid, "x": p.x, "y": p.y, "label": v.label})
    predicates = [
        {"id": pid, "x": p.x, "y": p.y, "label": egi.get_relation_name(pid)}
        for pid, p in dto.predicate_positions.items()
    ]
    cuts = []
    for cid, bounds in dto.cut_bounds.items():
        poly = boundaries.get(cid) or cut_boundary(
            bounds, style.cut_shape, float(style.cut_corner_radius or 0))
        cuts.append({"id": cid, "boundary": [[pt.x, pt.y] for pt in poly]})
    lines = [
        {"predicate_id": lp.predicate_id, "vertex_id": lp.vertex_id,
         "points": [[pt.x, pt.y] for pt in lp.points],
         "port_index": lp.port_index, "order_label": lp.order_label}
        for lp in dto.ligature_paths
    ]
    return {"sheet_id": dto.sheet_id, "vertices": vertices,
            "predicates": predicates, "cuts": cuts, "lines": lines}


def _open(client) -> str:
    r = client.post("/ergasterion/sessions", json={"base_source": "empty_sheet"})
    assert r.status_code == 200, r.text
    return r.json()["data"]["session_id"]


# ---------------------------------------------------------------------------
# The bank listing
# ---------------------------------------------------------------------------

def test_list_challenges(client):
    r = client.get("/ergasterion/challenges")
    assert r.status_code == 200, r.text
    challenges = r.json()["data"]["challenges"]
    assert challenges
    # prompts present, difficulty ascending, no drawing leaked
    diffs = [c["difficulty"] for c in challenges]
    assert diffs == sorted(diffs)
    for c in challenges:
        assert c["prompt_egif"]
        assert "drawing" not in c


# ---------------------------------------------------------------------------
# Grading a faithful attempt — by challenge id and by raw target
# ---------------------------------------------------------------------------

def test_faithful_drawing_of_target_passes_by_id(client):
    sid = _open(client)
    drawing = _drawing_from_egi('(man "Socrates")')
    r = client.post(f"/ergasterion/sessions/{sid}/grade-challenge",
                    json={"challenge_id": "one-relation", "drawing": drawing})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["gradeable"] is True
    assert data["matches"] is True
    assert data["findings"] == []
    assert "egif" in data["target_linear_forms"]["forms"]


def test_faithful_drawing_passes_by_raw_target(client):
    sid = _open(client)
    drawing = _drawing_from_egi('~[ (P *x) ~[ (Q x) ] ]')
    r = client.post(f"/ergasterion/sessions/{sid}/grade-challenge",
                    json={"target_egif": "~[ (P *x) ~[ (Q x) ] ]", "drawing": drawing})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["matches"] is True


def test_session_is_not_mutated_by_grading(client):
    sid = _open(client)
    before = client.get(f"/ergasterion/sessions/{sid}").json()["data"]["phase"]
    drawing = _drawing_from_egi('(man "Socrates")')
    client.post(f"/ergasterion/sessions/{sid}/grade-challenge",
                json={"challenge_id": "one-relation", "drawing": drawing})
    after = client.get(f"/ergasterion/sessions/{sid}").json()["data"]["phase"]
    assert before == after == "composing"


# ---------------------------------------------------------------------------
# Grading a wrong attempt — EG-vocabulary findings
# ---------------------------------------------------------------------------

def test_wrong_graph_fails_with_findings(client):
    sid = _open(client)
    # Draw a different graph than the target asks for.
    drawing = _drawing_from_egi('(man "Socrates") (mortal "Socrates")')
    r = client.post(f"/ergasterion/sessions/{sid}/grade-challenge",
                    json={"challenge_id": "one-relation", "drawing": drawing})
    data = r.json()["data"]
    assert data["gradeable"] is True
    assert data["matches"] is False
    assert any(f["kind"] == "extra" for f in data["findings"])


def test_argument_order_error_reported(client):
    sid = _open(client)
    drawing = _drawing_from_egi('(loves "Juliet" "Romeo")')
    r = client.post(f"/ergasterion/sessions/{sid}/grade-challenge",
                    json={"challenge_id": "argument-order", "drawing": drawing})
    data = r.json()["data"]
    assert data["matches"] is False
    assert any(f["kind"] == "order" for f in data["findings"])


# ---------------------------------------------------------------------------
# Error / edge handling
# ---------------------------------------------------------------------------

def test_unknown_challenge_id(client):
    sid = _open(client)
    r = client.post(f"/ergasterion/sessions/{sid}/grade-challenge",
                    json={"challenge_id": "nope", "drawing": _drawing_from_egi('(man "Socrates")')})
    body = r.json()
    assert body["success"] is False
    assert body["error"]["code"] == "CHALLENGE_NOT_FOUND"


def test_no_target_given(client):
    sid = _open(client)
    r = client.post(f"/ergasterion/sessions/{sid}/grade-challenge",
                    json={"drawing": _drawing_from_egi('(man "Socrates")')})
    body = r.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NO_TARGET"


def test_ill_formed_drawing_returns_validity_not_grade(client):
    sid = _open(client)
    # A dangling line: a line whose endpoint touches no mark — ill-formed.
    drawing = {
        "sheet_id": "sheet",
        "vertices": [{"id": "v1", "x": 0.0, "y": 0.0, "label": None}],
        "predicates": [{"id": "p1", "x": 200.0, "y": 0.0, "label": "man"}],
        "cuts": [],
        "lines": [{"predicate_id": "p1", "vertex_id": "v1",
                   "points": [[200.0, 0.0], [400.0, 0.0]]}],  # runs off to nowhere
    }
    r = client.post(f"/ergasterion/sessions/{sid}/grade-challenge",
                    json={"challenge_id": "one-relation", "drawing": drawing})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["gradeable"] is False
    assert "validity" in data
    assert data["validity"]["is_well_formed"] is False
