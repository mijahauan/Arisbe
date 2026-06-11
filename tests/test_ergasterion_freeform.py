"""Tests for the freeform composition canvas routes (draw-then-read, build step 2).

The composing phase becomes *draw-then-read*: the browser owns the ink and posts
the whole drawing; the server reads it into a determinate sign only at gate ①.
These pin the two new endpoints:

- ``POST /sessions/{id}/read-drawing`` — non-mutating preview: validity + (when
  well-formed) the EGI's linear forms ("what does it say").
- ``POST /sessions/{id}/fix-drawing`` — gate ①: validate, build the EGI, install it
  as the composing state, cross into deriving; refuse an ill-formed drawing in EG
  vocabulary.

The round-trip oracle: render a known EGI to a layout, serialize that layout into the
drawing JSON the canvas would post, fix it, and assert the read-back EGI is the
*same graph*.  See docs/FREEFORM_COMPOSITION_AND_LEARNING.md.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from eg_navigation import same_graph
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
    """Render an EGI and serialize the layout into the drawing JSON the canvas
    posts — the faithful ink (with argument order carried, as the renderer draws)."""
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
    drawing = {"sheet_id": dto.sheet_id, "vertices": vertices,
               "predicates": predicates, "cuts": cuts, "lines": lines}
    return egi, drawing


def _open(client) -> str:
    r = client.post("/ergasterion/sessions", json={"base_source": "empty_sheet"})
    assert r.status_code == 200, r.text
    return r.json()["data"]["session_id"]


def _egif_of(linear_forms) -> str:
    return linear_forms["forms"]["egif"]["text"]


CASES = [
    "(man *x)",
    "~[ (P *x) ]",
    "~[ (P *x) ~[ (Q x) ] ]",
    '(loves "Romeo" "Juliet")',
]


@pytest.mark.parametrize("egif", CASES)
def test_fix_drawing_round_trips_to_same_graph(client, egif):
    """Posting the faithful ink of an EGI to fix-drawing reads back the same graph,
    and crosses gate ① into deriving."""
    original, drawing = _drawing_from_egi(egif)
    sid = _open(client)
    r = client.post(f"/ergasterion/sessions/{sid}/fix-drawing", json={"drawing": drawing})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["phase"] == "deriving"          # gate ① crossed
    read_back = parse_egif(_egif_of(data["linear_forms"]))
    assert same_graph(read_back, original), (
        f"{egif}: read-back {_egif_of(data['linear_forms'])!r} not isomorphic")


@pytest.mark.parametrize("egif", CASES)
def test_read_drawing_preview_is_non_mutating(client, egif):
    """The preview returns validity + linear forms but does not advance the phase."""
    original, drawing = _drawing_from_egi(egif)
    sid = _open(client)
    r = client.post(f"/ergasterion/sessions/{sid}/read-drawing", json={"drawing": drawing})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["validity"]["is_well_formed"]
    read_back = parse_egif(_egif_of(data["linear_forms"]))
    assert same_graph(read_back, original)
    # Still composing — preview committed nothing.
    g = client.get(f"/ergasterion/sessions/{sid}")
    assert g.json()["data"]["phase"] == "composing"


def test_fix_drawing_refuses_overlapping_cuts(client):
    """An ill-formed drawing (two cuts crossing) is refused at gate ① in EG
    vocabulary, and the session stays composing."""
    drawing = {
        "sheet_id": "sheet",
        "vertices": [], "predicates": [], "lines": [],
        "cuts": [
            {"id": "c1", "boundary": [[0, 0], [100, 0], [100, 100], [0, 100]]},
            {"id": "c2", "boundary": [[50, 50], [150, 50], [150, 150], [50, 150]]},
        ],
    }
    sid = _open(client)
    r = client.post(f"/ergasterion/sessions/{sid}/fix-drawing", json={"drawing": drawing})
    assert r.status_code == 400, r.text
    body = r.json()
    assert body["error"]["code"] == "DRAWING_ILL_FORMED"
    codes = {e["code"] for e in body["error"]["validity"]["errors"]}
    assert "overlapping_cuts" in codes
    g = client.get(f"/ergasterion/sessions/{sid}")
    assert g.json()["data"]["phase"] == "composing"


def _ellipse(cx, cy, rx, ry, n=48):
    """A cut polyline exactly as freeform-canvas.js draws it (sampled ellipse)."""
    import math
    return [[cx + rx * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)] for i in range(n)]


def test_canvas_contract_binary_order(client):
    """A drawing in the exact shape the freeform canvas emits (hook at the
    predicate centre, lines in creation order via port_index) reads back with the
    right argument order — locks the JS serialize()↔backend contract."""
    drawing = {
        "sheet_id": "sheet",
        "vertices": [
            {"id": "v1", "x": -80, "y": 80, "label": "Romeo"},
            {"id": "v2", "x": 80, "y": 80, "label": "Juliet"},
        ],
        "predicates": [{"id": "p1", "x": 0, "y": -40, "label": "loves"}],
        "cuts": [],
        "lines": [
            {"predicate_id": "p1", "vertex_id": "v1",
             "points": [[0, -40], [-80, 80]], "port_index": 0},
            {"predicate_id": "p1", "vertex_id": "v2",
             "points": [[0, -40], [80, 80]], "port_index": 1},
        ],
    }
    sid = _open(client)
    r = client.post(f"/ergasterion/sessions/{sid}/fix-drawing", json={"drawing": drawing})
    assert r.status_code == 200, r.text
    egif = _egif_of(r.json()["data"]["linear_forms"])
    assert same_graph(parse_egif(egif), parse_egif('(loves "Romeo" "Juliet")')), egif


def test_canvas_contract_negation_with_ellipse_cut(client):
    """A negation drawn as the canvas draws it — an ellipse-polyline cut enclosing a
    relation and its line — reads back as ~[ (P *x) ]."""
    drawing = {
        "sheet_id": "sheet",
        "vertices": [{"id": "v1", "x": 0, "y": 30, "label": None}],
        "predicates": [{"id": "p1", "x": 0, "y": -30, "label": "P"}],
        "cuts": [{"id": "c1", "boundary": _ellipse(0, 0, 120, 110)}],
        "lines": [{"predicate_id": "p1", "vertex_id": "v1",
                   "points": [[0, -30], [0, 30]], "port_index": 0}],
    }
    sid = _open(client)
    r = client.post(f"/ergasterion/sessions/{sid}/fix-drawing", json={"drawing": drawing})
    assert r.status_code == 200, r.text
    egif = _egif_of(r.json()["data"]["linear_forms"])
    assert same_graph(parse_egif(egif), parse_egif("~[ (P *x) ]")), egif


def test_state_drawing_seeds_an_editable_graph(client):
    """The Graph↔Argument round-trip: after fixing, the base graph can be fetched
    as a drawing (to seed the canvas for re-editing) and that drawing re-reads to
    the same graph — so re-opening starts from the real graph, not blank."""
    original, drawing = _drawing_from_egi("~[ (P *x) ~[ (Q x) ] ]")
    sid = _open(client)
    fix = client.post(f"/ergasterion/sessions/{sid}/fix-drawing", json={"drawing": drawing})
    assert fix.status_code == 200, fix.text
    base_id = fix.json()["data"]["chain"]["initial_state_id"]

    sd = client.get(f"/ergasterion/sessions/{sid}/state-drawing", params={"state_id": base_id})
    assert sd.status_code == 200, sd.text
    seed = sd.json()["data"]["drawing"]
    # The seed re-reads (via the preview) to the same graph it came from.
    pv = client.post(f"/ergasterion/sessions/{sid}/read-drawing", json={"drawing": seed})
    assert pv.status_code == 200, pv.text
    assert pv.json()["data"]["validity"]["is_well_formed"]
    read_back = parse_egif(_egif_of(pv.json()["data"]["linear_forms"]))
    assert same_graph(read_back, original)


def test_edit_corpus_copy_fixes_independently(client):
    """A graph pulled from the corpus opens already fixed ('deriving'). Editing it
    (here: re-fixing its own seeded drawing) must succeed and yield a fixed line —
    an independent working copy, never a change to the original (there is no
    workshop→corpus route; saving is to scratch under a new name)."""
    r = client.post("/ergasterion/sessions", json={"base_source": "uod:barbara"})
    if not (r.status_code == 200 and r.json().get("success")):
        pytest.skip("barbara UoD not available")
    d = r.json()["data"]
    sid = d["session_id"]
    assert d["phase"] == "deriving"          # a corpus graph is already asserted
    base_id = d["chain"]["initial_state_id"]
    seed = client.get(f"/ergasterion/sessions/{sid}/state-drawing",
                      params={"state_id": base_id}).json()["data"]["drawing"]
    # Fixing the edited copy from the base state must NOT be refused as "already
    # fixed" — it produces a fresh fixed graph to derive on.
    fx = client.post(f"/ergasterion/sessions/{sid}/fix-drawing",
                     json={"drawing": seed, "from_state_id": base_id})
    assert fx.status_code == 200, fx.text
    assert fx.json()["data"]["phase"] == "deriving"


def test_read_drawing_reports_validity_without_building(client):
    """A drawing with a dangling line reports the error and omits linear forms."""
    drawing = {
        "sheet_id": "sheet",
        "vertices": [{"id": "v1", "x": 0, "y": -100, "label": None}],
        "predicates": [{"id": "p1", "x": 0, "y": 0, "label": "P"}],
        "cuts": [],
        # A line whose far end reaches neither the vertex nor the predicate.
        "lines": [{"predicate_id": "p1", "vertex_id": "v1",
                   "points": [[2, -8], [400, 400]]}],
    }
    sid = _open(client)
    r = client.post(f"/ergasterion/sessions/{sid}/read-drawing", json={"drawing": drawing})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert not data["validity"]["is_well_formed"]
    assert "dangling_line" in {e["code"] for e in data["validity"]["errors"]}
    assert "linear_forms" not in data
