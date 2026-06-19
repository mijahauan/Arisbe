"""Authoring a definition from a live selection — the abstraction front door
(`definition_from_selection`) that build A wires into the workshop UI.

The riskiest piece: re-rooting a selected sub-structure into a standalone body
EGI so `fold_selection` can fold under it and `expand_at` can unfold it, with the
original recovered exactly (`same_graph`).
"""

import pytest

from egif_parser_dau import parse_egif
from eg_navigation import same_graph
from definitions import (
    DefinitionRegistry,
    definition_from_selection,
    expand_at,
    fold_selection,
)


def _vid(egi, name):
    for vid, n in egi.variable_names.items():
        if n == name:
            return vid
    raise KeyError(name)


def _edges_in(egi, area_id):
    return [e.id for e in egi.E if e.id in egi.area.get(area_id, frozenset())]


def test_author_fold_unfold_round_trip():
    """Name a cut-with-content as R(x,y), fold the selection under it, then
    unfold the spot — the original graph comes back exactly."""
    host = parse_egif("[*x] [*y] (in x y) ~[ (in y x) ]")
    x, y = _vid(host, "x"), _vid(host, "y")
    cut = next(iter(host.Cut)).id
    inner = _edges_in(host, cut)[0]          # (in y x), inside the cut
    selection = {cut, inner}
    ports = [x, y]

    defn = definition_from_selection(host, selection, ports, "R")
    assert defn.arity == 2
    reg = DefinitionRegistry([defn])

    folded = fold_selection(host, reg, "R", selection, ports)
    assert "R" in set(folded.rel.values())          # the named spot exists
    assert len(folded.Cut) == len(host.Cut) - 1      # the cut was abstracted away

    spot = next(eid for eid, rel in folded.rel.items() if rel == "R")
    unfolded = expand_at(folded, reg, spot)
    assert same_graph(unfolded, host)                # exact inverse


def test_flat_selection_round_trip():
    """A flat (cut-free) selection — two relations sharing a line — folds and
    unfolds cleanly with one port."""
    host = parse_egif("[*x] (man x) (mortal x)")
    x = _vid(host, "x")
    e_man = next(e.id for e in host.E if host.rel[e.id] == "man")
    e_mortal = next(e.id for e in host.E if host.rel[e.id] == "mortal")
    selection = {e_man, e_mortal}
    ports = [x]

    defn = definition_from_selection(host, selection, ports, "human")
    reg = DefinitionRegistry([defn])
    folded = fold_selection(host, reg, "human", selection, ports)
    assert sorted(folded.rel.values()) == ["human"]

    spot = next(eid for eid, rel in folded.rel.items() if rel == "human")
    assert same_graph(expand_at(folded, reg, spot), host)


def test_dangling_line_is_refused():
    """A selected edge touching a vertex that is neither selected nor a port has
    a dangling line — the abstraction is refused, not silently closed."""
    host = parse_egif("[*x] [*y] (in x y) ~[ (in y x) ]")
    x = _vid(host, "x")
    outer = _edges_in(host, host.sheet)[0]   # (in x y) — references y, not a port
    with pytest.raises(ValueError):
        definition_from_selection(host, {outer}, [x], "R")


def test_empty_selection_is_refused():
    host = parse_egif("[*x] (man x)")
    x = _vid(host, "x")
    with pytest.raises(ValueError):
        definition_from_selection(host, set(), [x], "R")
