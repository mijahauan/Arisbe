"""Ergasterion abstraction routes — author a definition from a selection and
fold/unfold it (build A: the fold-to-define move).

Drives ``/define-fold`` and ``/define-unfold`` over a seeded deriving session:
the round trip, the session-scoped registry, and the refusal paths.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from web_api import main as web_main
from web_api.routes import ergasterion as ergasterion_route
from web_api.services.ergasterion_session_manager import ErgasterionSessionManager
from web_api.services.layout_service import generate_layout


@pytest.fixture
def client():
    return TestClient(web_main.app)


@pytest.fixture
def manager(monkeypatch):
    m = ErgasterionSessionManager()
    monkeypatch.setattr(
        ergasterion_route, "get_ergasterion_session_manager", lambda: m
    )
    return m


def _seed(manager, egif):
    """A deriving session over a known graph (no composing gate to cross)."""
    egi = parse_egif(egif)
    dto, _svg = generate_layout(egi)
    session = manager.create_session(
        initial_egi=egi,
        initial_layout_dto=dto,
        base_source="empty_sheet",
        base_phase="deriving",
    )
    return session, egi


def _vid(egi, name):
    for vid, n in egi.variable_names.items():
        if n == name:
            return vid
    raise KeyError(name)


def _edges_in(egi, area_id):
    return [e.id for e in egi.E if e.id in egi.area.get(area_id, frozenset())]


def test_fold_then_unfold_round_trip(client, manager):
    session, egi = _seed(manager, "[*x] [*y] (in x y) ~[ (in y x) ]")
    sid = session.session_id
    x, y = _vid(egi, "x"), _vid(egi, "y")
    cut = next(iter(egi.Cut)).id
    inner = _edges_in(egi, cut)[0]

    r = client.post(
        f"/ergasterion/sessions/{sid}/define-fold",
        json={"name": "R", "selection": [cut, inner], "ports": [x, y]},
    ).json()
    assert r["success"] is True, r.get("error")
    data = r["data"]
    assert "R" in data["definitions"]["names"]
    spots = data["definitions"]["spots"]
    assert len(spots) == 1 and spots[0]["name"] == "R"
    assert data["egi_summary"]["cut_count"] == 0          # cut abstracted away
    assert data["chain"]["steps"][-1]["rule_name"] == "definition.fold"
    spot_id = spots[0]["edge_id"]

    r2 = client.post(
        f"/ergasterion/sessions/{sid}/define-unfold",
        json={"spot_id": spot_id},
    ).json()
    assert r2["success"] is True, r2.get("error")
    data2 = r2["data"]
    assert data2["egi_summary"]["cut_count"] == 1          # the cut is back
    assert data2["definitions"]["spots"] == []            # no live R spot
    assert "R" in data2["definitions"]["names"]            # definition persists
    assert data2["chain"]["steps"][-1]["rule_name"] == "definition.unfold"


def test_fold_refused_dangling_line(client, manager):
    session, egi = _seed(manager, "[*x] [*y] (in x y) ~[ (in y x) ]")
    sid = session.session_id
    x = _vid(egi, "x")
    outer = _edges_in(egi, egi.sheet)[0]   # (in x y) references y, not a port
    r = client.post(
        f"/ergasterion/sessions/{sid}/define-fold",
        json={"name": "R", "selection": [outer], "ports": [x]},
    ).json()
    assert r["success"] is False
    assert r["error"]["code"] == "FOLD_REFUSED"
    # a refused fold registers no definition
    assert "R" not in manager.get_session(sid).definition_registry


def test_duplicate_name_refused(client, manager):
    session, egi = _seed(manager, "[*x] (man x) (mortal x)")
    sid = session.session_id
    x = _vid(egi, "x")
    e_man = next(e.id for e in egi.E if egi.rel[e.id] == "man")
    e_mortal = next(e.id for e in egi.E if egi.rel[e.id] == "mortal")
    body = {"name": "human", "selection": [e_man, e_mortal], "ports": [x]}
    r1 = client.post(f"/ergasterion/sessions/{sid}/define-fold", json=body).json()
    assert r1["success"] is True, r1.get("error")
    r2 = client.post(f"/ergasterion/sessions/{sid}/define-fold", json=body).json()
    assert r2["success"] is False
    assert r2["error"]["code"] == "DEFINITION_EXISTS"


def test_unfold_non_spot_refused(client, manager):
    session, egi = _seed(manager, "[*x] (man x)")
    sid = session.session_id
    e_man = next(e.id for e in egi.E if egi.rel[e.id] == "man")
    r = client.post(
        f"/ergasterion/sessions/{sid}/define-unfold",
        json={"spot_id": e_man},
    ).json()
    assert r["success"] is False
    assert r["error"]["code"] == "NOT_A_DEFINED_SPOT"


def test_fold_refused_in_composing_phase(client, manager):
    """Abstraction acts on a fixed graph — refused while composing."""
    egi = parse_egif("[*x] (man x)")
    dto, _ = generate_layout(egi)
    session = manager.create_session(
        initial_egi=egi, initial_layout_dto=dto,
        base_source="empty_sheet", base_phase="composing",
    )
    sid = session.session_id
    x = _vid(egi, "x")
    e_man = next(e.id for e in egi.E if egi.rel[e.id] == "man")
    r = client.post(
        f"/ergasterion/sessions/{sid}/define-fold",
        json={"name": "human", "selection": [e_man], "ports": [x]},
    ).json()
    assert r["success"] is False
    assert r["error"]["code"] == "PHASE_REFUSED"
