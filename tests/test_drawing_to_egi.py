"""Tests for the drawing→EGI builder (src/drawing_to_egi.py).

The builder is the construction half of *fix = read*: it joins the structure
``eg_reader.read_drawing`` recovers (area tree + ordered incidence) with the labels
a freeform drawing carries (relation names, vertex constants) into a real EGI.  The
proof is a corpus round-trip: take a known EGI, render it to a layout, harvest the
labels the renderer would draw, build a fresh EGI back from that layout, and assert
it is the *same graph* (full isomorphism) as the original.  That is the drawing→EGI
half of correspondence, with content as well as structure.

See docs/FREEFORM_COMPOSITION_AND_LEARNING.md (build step 2).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drawing_to_egi import build_egi_from_drawing
from eg_navigation import same_graph
from eg_reader import assign_order_labels
from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
from style_loader import load_default_style, load_style
from tomos_service import TomosService

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"

_STYLES = [
    ("dau", load_default_style()),
    ("peirce", load_style("peirce-authentic@1.0")),
]


def _labels_from(egi):
    """The labels the renderer would draw — what a freeform canvas carries: a
    relation name per predicate, a constant label (or None) per vertex."""
    predicate_labels = {e.id: egi.get_relation_name(e.id) for e in egi.E}
    vertex_labels = {v.id: v.label for v in egi.V}
    return predicate_labels, vertex_labels


def _corpus_egis(n=14):
    svc = TomosService(TOMOS_ROOT)
    out = []
    for meta in svc.list_uods()[:n]:
        try:
            egi = svc.load_uod(meta["uod_id"]).current_egi
        except Exception:
            continue
        if egi is not None:
            out.append((meta["uod_id"], egi))
    return out


@pytest.mark.parametrize("style_name,style", _STYLES)
def test_corpus_round_trip_builds_same_graph(style_name, style):
    """For each corpus UoD, build_egi(render(egi)) is isomorphic to egi — structure
    *and* content recovered, both styles (box and oval)."""
    engine = ELKLayoutEngine()
    checked = 0
    for uod_id, egi in _corpus_egis():
        # A faithful drawing carries argument order (clockwise anchor / numerals),
        # exactly as the render pipeline draws it — assign_order_labels is that step.
        dto = assign_order_labels(egi, engine.generate_layout(egi, style))
        predicate_labels, vertex_labels = _labels_from(egi)
        built = build_egi_from_drawing(dto, predicate_labels, vertex_labels)
        assert same_graph(built, egi), (
            f"{uod_id} did not round-trip drawing→EGI under {style_name}"
        )
        checked += 1
    assert checked > 0


def _build(egif, style=None):
    egi = parse_egif(egif)
    dto = assign_order_labels(
        egi, ELKLayoutEngine().generate_layout(egi, style or load_default_style())
    )
    pl, vl = _labels_from(egi)
    return egi, build_egi_from_drawing(dto, pl, vl)


def test_simple_relation():
    egi, built = _build("(man *x)")
    assert same_graph(built, egi)


def test_nested_cuts_recovers_scroll():
    """~[ (P *x) ~[ (Q x) ] ] — a shared line crossing a cut boundary, the scroll;
    the built EGI must place Q inside the inner cut and share x across both."""
    egi, built = _build("~[ (P *x) ~[ (Q x) ] ]")
    assert same_graph(built, egi)


def test_argument_order_is_recovered():
    """A non-symmetric binary relation: the builder must keep ν's order, not just
    the incidence multiset (loves x y ≠ loves y x)."""
    egi, built = _build('(loves "Romeo" "Juliet")')
    assert same_graph(built, egi)


def test_constant_vs_generic_vertices():
    """A constant vertex (named individual) stays a constant; a generic stays a bare
    line — the carried vertex labels decide."""
    egi, built = _build('(mortal "Socrates")')
    assert same_graph(built, egi)
    # The constant survived as a labelled, non-generic vertex.
    assert any((not v.is_generic) and v.label == "Socrates" for v in built.V)
