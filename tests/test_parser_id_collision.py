"""RUN_5 F1ᵇ — element ids are ``uuid4().hex[:8]`` (32 bits), and a machine-scale
sheet parsed thousands of times makes a birthday collision statistically due (observed
live 2026-07-04: ``ValueError: Vertex v_4599e538 already exists`` crashed an unattended
14 h run mid-revision). The parser is the high-volume creation path; it must regenerate
a fresh id on collision rather than die."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import egif_parser_dau
from egi_core_dau import Cut, Edge, Vertex


def _colliding(factory, id_of):
    """Wrap a create_* factory so its SECOND call returns an element whose id
    equals the first call's — the 32-bit birthday collision, made deterministic."""
    state = {"first": None, "collided": False}

    def wrapper(*a, **kw):
        el = factory(*a, **kw)
        if state["first"] is None:
            state["first"] = el.id
            return el
        if not state["collided"]:
            state["collided"] = True
            if isinstance(el, Vertex):
                return Vertex(id=state["first"], label=el.label,
                              is_generic=el.is_generic)
            if isinstance(el, Edge):
                return Edge(id=state["first"])
            return Cut(id=state["first"])
        return el

    return wrapper, state


def test_vertex_id_collision_is_regenerated_not_fatal(monkeypatch):
    wrapper, state = _colliding(egif_parser_dau.create_vertex, "v")
    monkeypatch.setattr(egif_parser_dau, "create_vertex", wrapper)
    g = egif_parser_dau.parse_egif('(man "Socrates") (mortal *x) (happy *y)')
    assert state["collided"], "the collision was never exercised"
    assert len(g.V) == 3
    assert len({v.id for v in g.V}) == 3          # all ids distinct


def test_edge_id_collision_is_regenerated_not_fatal(monkeypatch):
    wrapper, state = _colliding(egif_parser_dau.create_edge, "e")
    monkeypatch.setattr(egif_parser_dau, "create_edge", wrapper)
    g = egif_parser_dau.parse_egif('(pred "A") (qred "B")')
    assert state["collided"]
    assert len({e.id for e in g.E}) == 2


def test_cut_id_collision_is_regenerated_not_fatal(monkeypatch):
    wrapper, state = _colliding(egif_parser_dau.create_cut, "c")
    monkeypatch.setattr(egif_parser_dau, "create_cut", wrapper)
    g = egif_parser_dau.parse_egif('~[ (pred "A") ] ~[ (qred "B") ]')
    assert state["collided"]
    assert len({c.id for c in g.Cut}) == 2
