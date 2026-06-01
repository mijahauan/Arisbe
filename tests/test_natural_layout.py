"""
Tests for the coordinate-free ``natural_layout`` module.

``natural_layout(egi)`` builds the projection-independent structure that
any faithful drawing must realize: the cut-containment tree, element
areas, and — the load-bearing part — each ligature's required
crossing-sequence (the cuts whose boundary the line must cross,
derived purely from the area tree).

These tests pin:
1. The required crossing-sequence on the canonical Beta graph
   ``~[ (P *x) ~[ (Q x) ] ]`` — Q→x crosses exactly the inner cut;
   P→x crosses nothing (same area).
2. A two-deep nesting — a ligature from the innermost area to the sheet
   crosses both cuts, outermost-last (ordered, outward from predicate).
3. ``authorized_crossings`` is symmetric in the set it yields and empty
   for same-area incidences.
4. **Dimension-free discipline**: the module imports no geometry
   (``layout_dto`` / ``Point`` / ``BoundingBox``). This is what keeps a
   future 3-D projection additive; a regression here is a real
   architectural violation, not a style nit.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from natural_layout import authorized_crossings, natural_layout


def _ligs_by_relation(egi, nat):
    """Map relation-name -> list of NaturalLigature, for assertions."""
    out = {}
    for lig in nat.ligatures:
        rel = egi.get_relation_name(lig.predicate_id)
        out.setdefault(rel, []).append(lig)
    return out


# --------------------------------------------------------------------------- #
# 1. Canonical Beta graph                                                     #
# --------------------------------------------------------------------------- #


def test_modus_ponens_shape_crossings():
    """~[ (P *x) ~[ (Q x) ] ]: Q→x crosses the inner cut once; P→x crosses none."""
    egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
    nat = natural_layout(egi)
    by_rel = _ligs_by_relation(egi, nat)

    assert "P" in by_rel and "Q" in by_rel
    p_lig = by_rel["P"][0]
    q_lig = by_rel["Q"][0]

    # P and x share the outer cut's area → no crossing.
    assert p_lig.required_crossings == ()

    # Q is one cut deeper than x → cross exactly one cut.
    assert len(q_lig.required_crossings) == 1
    crossed = q_lig.required_crossings[0]
    assert crossed in {c.id for c in egi.Cut}

    # The crossed cut is the one whose parent area holds x (the inner cut).
    # x's area is the outer cut; the crossed cut is nested inside it.
    assert nat.cut_parent.get(crossed) == nat.element_area[q_lig.vertex_id]


# --------------------------------------------------------------------------- #
# 2. Two-deep nesting, ordered outward from the predicate                     #
# --------------------------------------------------------------------------- #


def test_two_deep_nesting_orders_outward():
    """A predicate two cuts deep, sharing identity with a sheet-level vertex,
    crosses both cuts — innermost first (outward from the predicate)."""
    # x is defined on the sheet; R sits two cuts deep and references it.
    egi = parse_egif("(P *x) ~[ ~[ (R x) ] ]")
    nat = natural_layout(egi)
    by_rel = _ligs_by_relation(egi, nat)

    r_lig = by_rel["R"][0]
    crossings = r_lig.required_crossings
    assert len(crossings) == 2, f"expected 2 crossings, got {crossings}"

    # Ordered outward: first the inner cut (R's own area), then its parent.
    inner, outer = crossings
    assert nat.cut_parent.get(inner) == outer, (
        "crossings should be ordered innermost-first (outward from predicate)"
    )
    # The outer cut sits directly on the sheet (x's area).
    assert nat.cut_parent.get(outer) == egi.sheet


# --------------------------------------------------------------------------- #
# 3. authorized_crossings unit behavior                                       #
# --------------------------------------------------------------------------- #


def test_same_area_has_no_crossings():
    parent_map = {"c1": "sheet", "c2": "c1"}
    assert authorized_crossings("c1", "c1", parent_map) == ()
    assert authorized_crossings(None, "c1", parent_map) == ()


def test_authorized_crossings_path_excludes_meet():
    # c2 nested in c1 nested in sheet. From c2 to sheet: cross c2 then c1.
    parent_map = {"c1": "sheet", "c2": "c1"}
    assert authorized_crossings("c2", "sheet", parent_map) == ("c2", "c1")
    # Reverse direction yields the same set, reordered inward to vertex.
    assert set(authorized_crossings("sheet", "c2", parent_map)) == {"c1", "c2"}


def test_authorized_crossings_siblings_cross_both_to_meet():
    # c1 and c2 are siblings under the sheet; meet is the sheet (not crossed).
    parent_map = {"c1": "sheet", "c2": "sheet"}
    assert set(authorized_crossings("c1", "c2", parent_map)) == {"c1", "c2"}


# --------------------------------------------------------------------------- #
# 4. Dimension-free discipline                                                #
# --------------------------------------------------------------------------- #


def test_natural_layout_imports_no_geometry():
    """natural_layout must not depend on geometry — that keeps 3-D additive.

    Reads the module source and asserts it neither imports ``layout_dto``
    nor references the geometric types, and that it imports no projection
    module (the layout engine / renderer / projection conventions). A
    failure here means a 2-D assumption — coordinates, distances, or a
    rendering choice — has leaked into the projection-independent layer,
    which is exactly what would turn a future 3-D projection from an
    additive step into a rewrite.
    """
    src = (Path(__file__).parent.parent / "src" / "natural_layout.py").read_text()
    # Strip the module docstring, which mentions these names in prose.
    body = src.split('"""', 2)[-1]

    # No geometry.
    assert "import layout_dto" not in body
    assert "from layout_dto" not in body
    assert "BoundingBox" not in body
    assert "Point" not in body

    # No projection modules — natural_layout is upstream of every
    # projection and must never depend on one.
    for projection_module in (
        "elk_layout_engine",
        "simple_svg_renderer",
        "projection_conventions",
        "layout_service",
    ):
        assert projection_module not in body, (
            f"natural_layout must not import the projection module "
            f"'{projection_module}' — keep the natural layer coordinate-free"
        )
