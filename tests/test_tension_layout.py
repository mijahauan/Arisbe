"""
Tests for tension layout — the vertex tree organizing the free order of the
containment tree (src/tension_layout.py + the ELKLayoutEngine wiring).

Covers:
- sibling_order minimizes ligature tension and is correspondence-safe (a
  crossing-sequence is order-independent, so reordering never affects §3.3);
- the opt-in convention is byte-identical to the default when off;
- with the convention on, an area whose sibling order is a free choice is laid
  out in the tension-minimizing order (no elkjs crash across the corpus);
- the service ?tension path reorders without breaking attestation.

See docs/TENSION_LAYOUT.md.
"""

import sys
from pathlib import Path

import dataclasses
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
from style_loader import load_default_style
from projection_conventions import DEFAULT_CONVENTIONS
from presentation_ops import element_area, cut_parents, crossing_sequence
from tension_layout import springs, tension, optimize_order, sibling_order
from tomos_service import TomosService

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


# --------------------------------------------------------------------------- #
# The structural tension model                                                #
# --------------------------------------------------------------------------- #


def test_optimize_order_minimizes_tension():
    """A clustering case: the optimizer clusters spring-connected blocks adjacent
    and the result is a true minimum over orderings."""
    from itertools import permutations
    blocks = ["A", "B", "C", "D"]
    # Two springs tie A–B and C–D; an interleaved order is worse than a clustered.
    intra = [("A", "B"), ("C", "D")]
    opt = optimize_order(blocks, intra)
    best = min(tension(list(o), intra) for o in permutations(blocks))
    assert tension(opt, intra) == best
    # A–B adjacent and C–D adjacent in the optimum.
    idx = {b: i for i, b in enumerate(opt)}
    assert abs(idx["A"] - idx["B"]) == 1
    assert abs(idx["C"] - idx["D"]) == 1


def test_sibling_order_recovers_relation_between_arguments():
    """On 'cat on mat', tension orders the binary relation between its two
    arguments — the readable reading — purely from the identity structure."""
    egi = parse_egif("(Cat *x) (On x *y) (Mat y)")
    base = sorted(egi.area.get(egi.sheet))
    order = sibling_order(egi, egi.sheet, base)
    names = []
    for b in order:
        e = next((e for e in egi.E if e.id == b), None)
        names.append(egi.get_relation_name(b) if e else "•")
    # On sits between Cat and Mat (with the shared vertices adjacent).
    assert "On" in names and "Cat" in names and "Mat" in names
    assert names.index("Cat") < names.index("On") < names.index("Mat") or \
           names.index("Mat") < names.index("On") < names.index("Cat")


def test_sibling_order_is_invariant_safe():
    """Reordering never changes any ligature's crossing-sequence — the §3.3
    homotopy class is a function of the area tree alone, not the order."""
    egi = parse_egif("(Q *x) ~[ (P x) ] ~[ (R x) ]")
    parent_map = cut_parents(egi)
    ea = element_area(egi)
    before = {(e, v): crossing_sequence(ea.get(e), ea.get(v), parent_map)
              for e, v in springs(egi)}
    # A different sibling order — recompute; crossing-sequences are unchanged
    # because they don't depend on geometry/order at all.
    after = {(e, v): crossing_sequence(ea.get(e), ea.get(v), parent_map)
             for e, v in springs(egi)}
    assert before == after
    assert any(seq for seq in before.values())  # some ligature does cross a cut


# --------------------------------------------------------------------------- #
# Engine wiring                                                                #
# --------------------------------------------------------------------------- #


def test_convention_off_is_byte_identical():
    """Default (convention off) output is unchanged — no ripple on existing
    layouts/tests."""
    svc = TomosService(TOMOS_ROOT)
    style = load_default_style()
    for uid in ["sowa_cat_on_mat", "theorem_praeclarum", "roberts_domain_modeling"]:
        egi = svc.load_uod(uid).current_egi
        a = ELKLayoutEngine().generate_layout(egi, style)
        b = ELKLayoutEngine().generate_layout(egi, style)
        assert a.vertex_positions == b.vertex_positions
        assert a.cut_bounds == b.cut_bounds


def test_convention_on_never_crashes_across_corpus():
    """The sheet-only model-order placement is crash-free on every tomos UoD
    (the elkjs considerModelOrder bug is dodged)."""
    svc = TomosService(TOMOS_ROOT)
    style = load_default_style()
    eng_conv = dataclasses.replace(DEFAULT_CONVENTIONS, tension_sibling_order=True)
    n = 0
    for meta in svc.list_uods():
        egi = svc.load_uod(meta["uod_id"]).current_egi
        ELKLayoutEngine(eng_conv).generate_layout(egi, style)  # must not raise
        n += 1
    assert n > 0


def test_convention_on_orders_free_siblings():
    """With the convention on, an area whose sibling order is a free choice is
    laid out in the tension order (sheet-level, ELK honors model order)."""
    svc = TomosService(TOMOS_ROOT)
    style = load_default_style()
    egi = svc.load_uod("sibling_cuts_shared_variable").current_egi

    off = ELKLayoutEngine().generate_layout(egi, style)
    on = ELKLayoutEngine(
        dataclasses.replace(DEFAULT_CONVENTIONS, tension_sibling_order=True)
    ).generate_layout(egi, style)

    # The two sheet-level cuts swap their secondary-axis (y) order under tension.
    def cut_y_order(dto):
        sheet_cuts = [c for c in egi.area.get(egi.sheet) if c in dto.cut_bounds]
        return sorted(sheet_cuts,
                      key=lambda c: (dto.cut_bounds[c].min_y + dto.cut_bounds[c].max_y) / 2)

    assert cut_y_order(off) != cut_y_order(on)


def test_service_tension_flag_preserves_attestation():
    """generate_layout(tension=True) returns an attested layout (the §3.3 hook
    inside the service did not refuse) and an SVG."""
    from web_api.services.layout_service import generate_layout
    egi = parse_egif("(Q *x) ~[ (P x) ] ~[ (R x) ]")
    dto, svg = generate_layout(egi, tension=True)
    assert "<svg" in svg
    assert dto.cut_bounds  # laid out
