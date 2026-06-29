"""
Tests for the drawing→EGI learning loop (``src/layout_learning.py``, ROADMAP #14 (d)).

``arrangement_deltas`` is the inverse of ``presentation_deltas.apply_deltas``: it
recovers the regime-3 deltas between Arisbe's *canonical* layout of an EGI and a
*drawn* arrangement of the same EGI (the Peirce-Edition replica-then-parse
signal).  ``generalize_arrangement`` then crystallises those into a regularity
via the existing style ladder — closing the loop.

A "drawn" arrangement is simulated by replaying known regime-3 moves onto the
canonical layout (so it is guaranteed §3.3-valid); the recovered deltas must
match what was applied.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from layout_learning import arrangement_deltas, generalize_arrangement
from layout_dto import BoundingBox
from presentation_deltas import (
    apply_deltas, record_delta, MOVE_VERTEX, MOVE_PREDICATE, RESHAPE_CUT,
)
from web_api.services.layout_service import generate_layout

PEIRCE = "peirce-authentic@1.0"
BETA = "(Human *x) ~[ (Mortal x) ]"


def _canonical(form):
    egi = parse_egif(form)
    dto, _svg = generate_layout(egi, style_name=PEIRCE)
    return egi, dto


def test_identical_layouts_yield_no_deltas():
    egi, dto = _canonical(BETA)
    assert arrangement_deltas(egi, dto, dto) == []


def test_recovers_a_known_vertex_move():
    egi, canonical = _canonical(BETA)
    vid = next(iter(canonical.vertex_positions))
    drawn, dropped = apply_deltas(
        egi, canonical, [record_delta(egi, MOVE_VERTEX,
                                      {"vertex_id": vid, "dx": 12.0, "dy": 7.0})])
    assert not dropped

    learned = arrangement_deltas(egi, canonical, drawn)
    moves = [d for d in learned if d.op == MOVE_VERTEX and d.params["vertex_id"] == vid]
    assert len(moves) == 1
    assert moves[0].params["dx"] == pytest.approx(12.0, abs=0.6)
    assert moves[0].params["dy"] == pytest.approx(7.0, abs=0.6)
    # tagged for the ladder (describe ran): a non-empty structural target.
    assert moves[0].target.get("kind")


def test_recovers_a_known_predicate_move():
    egi, canonical = _canonical(BETA)
    pid = next(iter(canonical.predicate_positions))
    drawn, dropped = apply_deltas(
        egi, canonical, [record_delta(egi, MOVE_PREDICATE,
                                      {"predicate_id": pid, "dx": -9.0, "dy": 4.0})])
    assert not dropped
    learned = arrangement_deltas(egi, canonical, drawn)
    moves = [d for d in learned if d.op == MOVE_PREDICATE and d.params["predicate_id"] == pid]
    assert len(moves) == 1
    assert moves[0].params["dx"] == pytest.approx(-9.0, abs=0.6)


def test_round_trip_reproduces_the_drawn_arrangement():
    """Applying the learned deltas to canonical reproduces the drawn layout
    (positions match) and re-attests §3.3 (apply_deltas drops nothing)."""
    egi, canonical = _canonical(BETA)
    vid = next(iter(canonical.vertex_positions))
    pid = next(iter(canonical.predicate_positions))
    drawn, _ = apply_deltas(egi, canonical, [
        record_delta(egi, MOVE_VERTEX, {"vertex_id": vid, "dx": 10.0, "dy": -6.0}),
        record_delta(egi, MOVE_PREDICATE, {"predicate_id": pid, "dx": 8.0, "dy": 5.0}),
    ])

    learned = arrangement_deltas(egi, canonical, drawn)
    replayed, dropped = apply_deltas(egi, canonical, learned)
    assert not dropped
    assert replayed.vertex_positions[vid].x == pytest.approx(drawn.vertex_positions[vid].x, abs=0.6)
    assert replayed.vertex_positions[vid].y == pytest.approx(drawn.vertex_positions[vid].y, abs=0.6)
    assert replayed.predicate_positions[pid].x == pytest.approx(drawn.predicate_positions[pid].x, abs=0.6)


def test_recovers_a_cut_reshape():
    egi, canonical = _canonical(BETA)
    cid = next(iter(canonical.cut_bounds))
    cb = canonical.cut_bounds[cid]
    bigger = BoundingBox(cb.min_x - 8, cb.min_y - 8, cb.max_x + 8, cb.max_y + 8)
    drawn, dropped = apply_deltas(
        egi, canonical, [record_delta(egi, RESHAPE_CUT, {
            "cut_id": cid,
            "bounds": {"min_x": bigger.min_x, "min_y": bigger.min_y,
                       "max_x": bigger.max_x, "max_y": bigger.max_y},
        })])
    assert not dropped
    learned = arrangement_deltas(egi, canonical, drawn)
    reshapes = [d for d in learned if d.op == RESHAPE_CUT and d.params["cut_id"] == cid]
    assert len(reshapes) == 1


def test_loop_generalizes_to_an_untouched_sibling():
    """The closed loop: a placement learned on one element crystallises (via the
    style ladder) onto an untouched sibling of the same structural kind."""
    egi = parse_egif("(P *x) (Q *y)")  # two generic vertices on the sheet
    x, y = sorted(v.id for v in egi.V)
    learned = [record_delta(egi, MOVE_VERTEX, {"vertex_id": x, "dx": 0.0, "dy": 12.0})]
    synthetic = generalize_arrangement(egi, learned)
    # y was untouched but shares x's kind + area polarity → it gets the intent.
    targets = {d.params["vertex_id"] for d in synthetic if d.op == MOVE_VERTEX}
    assert y in targets
    syn_y = next(d for d in synthetic if d.params.get("vertex_id") == y)
    assert syn_y.params["dy"] == pytest.approx(12.0, abs=0.1)
