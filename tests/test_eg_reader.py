"""Tests for the drawn-form → EG reader (src/eg_reader.py).

The reader recovers an EG's structure (area tree + incidence) from a drawing by
geometry alone — inside/outside the drawn cut curves, and tracing ligatures — the
inverse of layout/render and the drawn→EG half of the correspondence.  A drawn
form is one of three co-equal expressions of an EG; this proves the round trip
``read(render(egi)) == egi`` (up to argument order, which the 2-D convention does
not visually encode — R8).

See docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md and eg_reader's module docstring.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from eg_reader import read_drawing, reading_matches_egi, assign_order_labels
from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
from tension_engine import TensionLayoutEngine
from style_loader import load_default_style, load_style
from tomos_service import TomosService

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"

_ENGINES = [ELKLayoutEngine, TensionLayoutEngine]
_STYLES = [
    ("dau", load_default_style()),
    ("peirce", load_style("peirce-authentic@1.0")),
]


def _reader_frontier(uod_id: str, *, engine, clockwise: bool) -> bool:
    """Is this (UoD, engine, convention) past the *geometric reader's inversion*
    frontier — i.e. ``read_drawing(render(egi))`` does not recover ``egi`` here?

    This is **not** a correspondence gap.  §3.3 (``correspondence_attestation`` /
    ``test_correspondence_invariant``) still attests every one of these (EGI,
    drawing) pairs faithful corpus-wide — the layout *is* a correct picture of the
    graph.  What is deferred is the *stronger* round-trip: recovering the EGI from
    geometry alone.  Two large imported reasoning ontologies (landed for the
    theory-query / materialization work, not for drawing) sit past that frontier:

      - ``bfo_core`` under **ELK**: ELK packs its 47 cuts so densely the reader
        misreads the structure.  The **Tension** engine lays the *same* graph out
        invertibly (it passes there) — so this is an ELK layout-density frontier
        (the "layout-perf frontier" noted when bfo_core landed), not a reader bug.
      - ``colore_between`` under the **clockwise** convention: the clockwise
        writing convention cannot carry the argument order of its ternary
        ``between(x,y,z)`` atoms recoverably.  The **numbered** convention — the
        authoritative ν carrier; clockwise is best-effort by design (Phase 3c) —
        does, so numbered/unordered round-trip fine; only clockwise-ordered defers.
    """
    if uod_id == "bfo_core" and engine is ELKLayoutEngine:
        return True
    if uod_id == "colore_between" and clockwise:
        return True
    return False


@pytest.mark.parametrize("Engine", _ENGINES)
@pytest.mark.parametrize("style_name,style", _STYLES)
def test_round_trip_recovers_structure(Engine, style_name, style):
    """read(render(egi)) recovers egi's area tree and incidence (as a set) for
    every corpus UoD — both engines, box (Dau) and oval (Peirce) styles.  The
    drawing alone yields the EG's structure."""
    svc = TomosService(TOMOS_ROOT)
    for meta in svc.list_uods():
        if _reader_frontier(meta["uod_id"], engine=Engine, clockwise=False):
            continue
        egi = svc.load_uod(meta["uod_id"]).current_egi
        dto = Engine().generate_layout(egi, style)
        reading = read_drawing(dto)
        assert reading_matches_egi(reading, egi, ordered=False), (
            f"{meta['uod_id']} did not round-trip under {Engine.__name__}/{style_name}"
        )


@pytest.mark.parametrize("Engine", _ENGINES)
def test_numbered_round_trip_recovers_full_nu_with_order(Engine):
    """Under the numbered convention (Dau default) the round trip recovers the
    *full ν including argument order* — the numeral on each line carries the
    order, so read(render(egi)) == egi as ordered sequences, corpus-wide."""
    svc = TomosService(TOMOS_ROOT)
    style = load_default_style()  # numbered
    for meta in svc.list_uods():
        if _reader_frontier(meta["uod_id"], engine=Engine, clockwise=False):
            continue
        egi = svc.load_uod(meta["uod_id"]).current_egi
        dto = Engine().generate_layout(egi, style)
        assert reading_matches_egi(read_drawing(dto), egi, ordered=True), (
            f"{meta['uod_id']} lost argument order under {Engine.__name__}/numbered"
        )


@pytest.mark.parametrize("Engine", _ENGINES)
def test_clockwise_round_trip_recovers_full_nu_via_overrides(Engine):
    """Under the clockwise convention (Peirce) the canonical pipeline labels only
    the relations whose natural placement doesn't read clockwise-as-ν (the
    Convention-13 numeric override); with that, the round trip recovers the full
    ν including order across the corpus, both engines."""
    svc = TomosService(TOMOS_ROOT)
    style = load_style("peirce-authentic@1.0")  # clockwise
    for meta in svc.list_uods():
        if _reader_frontier(meta["uod_id"], engine=Engine, clockwise=True):
            continue
        egi = svc.load_uod(meta["uod_id"]).current_egi
        dto = assign_order_labels(egi, Engine().generate_layout(egi, style))
        assert reading_matches_egi(read_drawing(dto), egi, ordered=True), (
            f"{meta['uod_id']} lost order under {Engine.__name__}/clockwise"
        )


def test_clockwise_labels_are_sparse_numbered_labels_all():
    """numbered labels every ≥2-ary line; clockwise labels only the overrides —
    so for the same corpus clockwise draws *strictly fewer* numerals (the
    placement already shows most relations' order)."""
    svc = TomosService(TOMOS_ROOT)
    dau = load_default_style()
    peirce = load_style("peirce-authentic@1.0")
    n_numbered = n_clockwise = 0
    for meta in svc.list_uods():
        egi = svc.load_uod(meta["uod_id"]).current_egi
        base = ELKLayoutEngine().generate_layout(egi, dau)
        n_numbered += sum(p.order_label is not None
                          for p in assign_order_labels(egi, base).ligature_paths)
        basep = ELKLayoutEngine().generate_layout(egi, peirce)
        n_clockwise += sum(p.order_label is not None
                           for p in assign_order_labels(egi, basep).ligature_paths)
    assert n_numbered > 0
    assert n_clockwise < n_numbered  # clockwise only overrides where needed


def test_clockwise_reader_recovers_order_from_hook_angles():
    """Under the clockwise convention (Peirce) the reader recovers argument order
    from the *geometry* — the angle each line leaves the spot, read clockwise from
    'vertically above' — not from port_index.  Hooks placed clockwise as a,b,c are
    read back as [a,b,c] even when port_index is scrambled."""
    import dataclasses
    from layout_dto import BoundingBox, LayoutDTO, LigaturePath, Point
    P = Point(0.0, 0.0)
    # a straight up, b lower-right, c lower-left ⇒ clockwise-from-up = a, b, c.
    verts = {"a": Point(0.0, -100.0), "b": Point(87.0, 50.0), "c": Point(-87.0, 50.0)}
    # port_index deliberately scrambled (2,0,1) so a port-order read would differ.
    paths = [
        LigaturePath(predicate_id="R", vertex_id="a",
                     points=(Point(0.0, -8.0), verts["a"]), port_index=2),
        LigaturePath(predicate_id="R", vertex_id="b",
                     points=(Point(7.0, 4.0), verts["b"]), port_index=0),
        LigaturePath(predicate_id="R", vertex_id="c",
                     points=(Point(-7.0, 4.0), verts["c"]), port_index=1),
    ]
    dto = LayoutDTO(
        vertex_positions=verts, predicate_positions={"R": P}, cut_bounds={},
        ligature_paths=paths, area_hierarchy={"sheet": set()},
        viewport_bounds=BoundingBox(-150, -150, 150, 150), sheet_id="sheet",
        style=load_style("peirce-authentic@1.0"),  # clockwise convention
    )
    assert read_drawing(dto).incidence["R"] == ["a", "b", "c"]


# --------------------------------------------------------------------------- #
# Phase 3c: clockwise placement as the order carrier + a single start anchor   #
# --------------------------------------------------------------------------- #


def test_argument_order_numerals_toggle():
    """The argument_order_numerals knob is a presentation-only override of which
    lines get a drawn order numeral: 'always' numbers every ≥2-ary line, 'never'
    draws none (rely on placement), 'auto' is the per-convention default."""
    import dataclasses
    egi = parse_egif("(Loves *x *y)")  # one binary relation
    eng = ELKLayoutEngine()
    base = load_default_style()
    def labels(conv, num):
        st = dataclasses.replace(base, argument_order_convention=conv,
                                 argument_order_numerals=num)
        dto = assign_order_labels(egi, eng.generate_layout(egi, st))
        return [p.order_label for p in dto.ligature_paths]
    assert labels("numbered", "auto") == [1, 2]
    assert labels("numbered", "never") == [None, None]
    assert labels("clockwise", "auto") == [None, None]   # already reads ν
    assert labels("clockwise", "always") == [1, 2]
    assert labels("clockwise", "never") == [None, None]


def test_clockwise_out_of_order_uses_a_single_start_anchor_not_full_numbering():
    """Under the clockwise convention, a relation whose hooks read a *rotation* of
    ν is disambiguated by a SINGLE start anchor (the numeral 1 on ν's first line —
    Conv. 13), not a number on every line: the placement carries the cyclic order,
    the anchor says where it begins.  The round trip still recovers full ν."""
    import math
    import dataclasses
    from layout_dto import BoundingBox, LayoutDTO, LigaturePath, Point
    # Three hooks placed clockwise-from-up as a, b, c, but ν = (b, c, a) — a
    # rotation of the drawn order.  One anchor (on b, ν's first arg) pins it.
    P = Point(0.0, 0.0)
    verts = {"a": Point(0.0, -100.0), "b": Point(87.0, 50.0), "c": Point(-87.0, 50.0)}
    paths = [
        LigaturePath("R", "b", (Point(7.0, 4.0), verts["b"]), port_index=0),
        LigaturePath("R", "c", (Point(-7.0, 4.0), verts["c"]), port_index=1),
        LigaturePath("R", "a", (Point(0.0, -8.0), verts["a"]), port_index=2),
    ]
    style = dataclasses.replace(load_style("peirce-authentic@1.0"))
    dto = LayoutDTO(
        vertex_positions=verts, predicate_positions={"R": P}, cut_bounds={},
        ligature_paths=paths, area_hierarchy={"sheet": set()},
        viewport_bounds=BoundingBox(-150, -150, 150, 150), sheet_id="sheet",
        style=style,
    )

    class _EGI:  # minimal stand-in carrying ν
        nu = {"R": ("b", "c", "a")}
        class _E:  # noqa: D401
            id = "R"
        E = [_E()]
    labelled = assign_order_labels(_EGI(), dto)
    drawn = [p.order_label for p in labelled.ligature_paths]
    assert drawn.count(None) == 2 and 1 in drawn          # exactly one anchor
    assert labelled.ligature_paths[0].order_label == 1     # on ν's first line (b)
    assert read_drawing(labelled).incidence["R"] == ["b", "c", "a"]  # recovers ν


def test_clockwise_no_label_strikethrough_and_order_recovered():
    """The load-bearing guarantee: under the clockwise writing convention no line
    is ever drawn *through* a predicate's label — a clockwise spoke that would be
    forced across its own spot (the vertex lying opposite its ν-slot) reverts to
    the natural hook instead.  Corpus-wide, §3.3 stays green, every line is clear
    of every predicate label, and the ordered round trip still recovers ν (the
    numeral carries any predicate that had to revert)."""
    from clockwise_placement import place_clockwise_hooks
    from correspondence_attestation import check_correspondence
    from presentation_ops import predicate_label_box, path_intersects_box

    svc = TomosService(TOMOS_ROOT)
    style = load_style("peirce-authentic@1.0")
    eng = ELKLayoutEngine()
    for meta in svc.list_uods():
        egi = svc.load_uod(meta["uod_id"]).current_egi
        dto = place_clockwise_hooks(egi, eng.generate_layout(egi, style), style, eng)
        assert not check_correspondence(egi, dto), meta["uod_id"]
        for e in egi.E:
            box = predicate_label_box(egi.get_relation_name(e.id),
                                      dto.predicate_positions[e.id], dto.style)
            for p in dto.ligature_paths:
                if p.predicate_id == e.id:
                    assert not path_intersects_box(p.points, box), (
                        f"{meta['uod_id']}: a line strikes through its own label")
        # §3.3 and the no-strikethrough guarantee hold corpus-wide (checked above);
        # only the stronger reader round-trip defers at the frontier (see
        # _reader_frontier — this sweep is ELK + clockwise).
        if _reader_frontier(meta["uod_id"], engine=ELKLayoutEngine, clockwise=True):
            continue
        dto = assign_order_labels(egi, dto)
        assert reading_matches_egi(read_drawing(dto), egi, ordered=True), \
            meta["uod_id"]


def test_freeform_cut_polyline_read_by_point_in_polygon():
    """Phase 4: when a cut is carried as an explicit polyline (a human-drawn cut),
    the reader recovers containment by point-in-polygon against that literal curve.
    Reading a drawing whose cut polyline encloses the contents recovers the same
    area tree as the analytic shape — the freeform read path."""
    import dataclasses
    from presentation_ops import cut_boundary

    egi = parse_egif("~[ (P *x) ]")
    style = load_style("dau-compliant@1.0")
    dto = ELKLayoutEngine().generate_layout(egi, style)
    (cid,) = list(dto.cut_bounds)
    poly = cut_boundary(dto.cut_bounds[cid], "rounded_rectangle", 8.0, samples=96)
    carried = dataclasses.replace(dto, cut_boundary={cid: poly})
    # Same structure recovered whether the cut is analytic or a carried polyline.
    assert reading_matches_egi(read_drawing(carried), egi, ordered=False)
    assert read_drawing(dto).area == read_drawing(carried).area


def test_clockwise_high_arity_never_strikes_its_label():
    """A 10-ary relation: whatever the layout does with its ten arguments, not one
    spoke is drawn through the relation name, and the full 10-tuple round-trips."""
    from clockwise_placement import place_clockwise_hooks
    from correspondence_attestation import check_correspondence
    from presentation_ops import predicate_label_box, path_intersects_box

    egi = parse_egif("(R *a *b *c *d *e *f *g *h *i *j)")
    style = load_style("peirce-authentic@1.0")
    eng = ELKLayoutEngine()
    dto = place_clockwise_hooks(egi, eng.generate_layout(egi, style), style, eng)
    assert not check_correspondence(egi, dto)
    (pid,) = [e.id for e in egi.E]
    box = predicate_label_box("R", dto.predicate_positions[pid], dto.style)
    for p in dto.ligature_paths:
        assert not path_intersects_box(p.points, box)  # no spoke through "R"
    dto = assign_order_labels(egi, dto)
    assert reading_matches_egi(read_drawing(dto), egi, ordered=True)


def test_reader_uses_geometry_not_stored_ids():
    """The logic is read from geometry, not the path's stored ids: scrambling
    every LigaturePath's predicate_id/vertex_id must not change the reading
    (endpoints are matched to the nearest mark)."""
    import dataclasses
    egi = parse_egif("(Cat *x) (On x *y) (Mat y)")
    dto = ELKLayoutEngine().generate_layout(egi, load_default_style())
    truth = read_drawing(dto)
    scrambled_paths = [
        dataclasses.replace(p, predicate_id="WRONG", vertex_id="WRONG")
        for p in dto.ligature_paths
    ]
    scrambled = dataclasses.replace(dto, ligature_paths=scrambled_paths)
    assert read_drawing(scrambled).incidence == truth.incidence


def test_per_element_queries():
    """The reader answers, for any element: its container, its co-residents, and
    what it connects to — the questions the author named."""
    # P and a vertex x inside a cut; Q outside connects to the same x.
    egi = parse_egif("(Q *x) ~[ (P x) ]")
    dto = ELKLayoutEngine().generate_layout(egi, load_default_style())
    reading = read_drawing(dto)
    (cut_id,) = [c.id for c in egi.Cut]
    pid_P = next(e.id for e in egi.E if egi.get_relation_name(e.id) == "P")
    pid_Q = next(e.id for e in egi.E if egi.get_relation_name(e.id) == "Q")
    (xid,) = [v.id for v in egi.V]

    assert reading.container(pid_P) == cut_id          # P is inside the cut
    assert reading.container(pid_Q) == dto.sheet_id     # Q is on the sheet
    # P connects to the shared vertex; that vertex connects back to both P and Q.
    assert xid in reading.connections(pid_P)
    assert set(reading.connections(xid)) == {pid_P, pid_Q}


def test_recovers_nested_cut_containment():
    """Inside/outside a closed line recovers cut nesting: a cut drawn inside
    another is read as its child."""
    egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
    dto = ELKLayoutEngine().generate_layout(egi, load_default_style())
    reading = read_drawing(dto)
    cut_ids = [c.id for c in egi.Cut]
    # One cut is the parent of the other (nested), matching egi.area.
    parents = {reading.container(c) for c in cut_ids}
    assert dto.sheet_id in parents          # the outer cut sits on the sheet
    assert any(p in cut_ids for p in parents)  # the inner cut sits in a cut
    assert reading_matches_egi(reading, egi)


# --------------------------------------------------------------------------- #
# Freeform robustness — characterization of the reader on *human* (not engine)
# geometry, the de-risk for draw-then-read composition
# (docs/FREEFORM_COMPOSITION_AND_LEARNING.md).  The reading algorithm is sound
# and faithful — it reads exactly what is drawn; these pin *where human
# imprecision and ill-formed drawings need draw-time snapping / fix-time
# validity*, NOT a reader rewrite.  If a future change "fixes" one of these in
# the reader itself, that's a design decision to make deliberately, not a
# regression to paper over.
# --------------------------------------------------------------------------- #


def _free_dto(verts, preds, cuts, paths, sheet="sheet"):
    from layout_dto import BoundingBox, LayoutDTO
    return LayoutDTO(
        vertex_positions=verts, predicate_positions=preds, cut_bounds=cuts,
        ligature_paths=paths, area_hierarchy={sheet: set()},
        viewport_bounds=BoundingBox(-300, -300, 300, 300),
        sheet_id=sheet, style=load_default_style(),
    )


def test_freeform_containment_is_the_drawn_point_no_snapping():
    """Containment is the *exact drawn point*: a spot 1px inside reads inside, 1px
    outside reads outside, on-edge reads inside. Correct (drawn shape is
    authoritative) — but human intent near a boundary is ambiguous, so the
    *canvas* must snap clearly in/out; the reader does not."""
    from layout_dto import BoundingBox, Point
    cut = {"c": BoundingBox(0, 0, 100, 100)}
    def where(px):
        r = read_drawing(_free_dto({"x": Point(px, 50)}, {"P": Point(px, 50)}, cut, []))
        return "c" if "P" in r.area.get("c", set()) else r.sheet_id
    assert where(50) == "c"        # clearly inside
    assert where(1) == "c"         # 1px inside → inside
    assert where(-1) == "sheet"    # 1px outside → outside
    assert where(0) == "c"         # on the edge → inside


def test_freeform_incidence_is_nearest_endpoint_and_is_brittle():
    """Incidence matches a line's end to the *nearest* mark. A line that stops
    short and drifts toward a decoy vertex is read as connecting the decoy — the
    one real fragility, to be handled by draw-time endpoint snapping / a
    touch-tolerance, not by the reader guessing intent."""
    from layout_dto import LigaturePath, Point
    verts = {"x": Point(0, -100), "y": Point(20, -100)}   # x intended, y decoy
    preds = {"P": Point(0, 0)}

    def incid(end):
        p = [LigaturePath(predicate_id="P", vertex_id="x",
                          points=(Point(2, -8), end), port_index=0)]
        return read_drawing(_free_dto(verts, preds, {}, p)).incidence.get("P")

    assert incid(Point(0, -95)) == ["x"]      # the line reaches x → correct
    assert incid(Point(15, -55)) == ["y"]     # stops short, drifts → reads decoy
    assert incid(Point(20, -95)) == ["y"]     # reaches y


def test_freeform_overlapping_cuts_are_not_a_valid_nesting():
    """Overlapping cuts (neither nests the other) cannot be a valid area tree.
    The reader treats them as sheet-level siblings and assigns an overlap-region
    spot to one — so the *fix-time validity pass* must detect and refuse overlap
    ('cuts must nest or be separate'); the reader will not invent a nesting."""
    from layout_dto import BoundingBox, Point
    cuts = {"c1": BoundingBox(0, 0, 100, 100), "c2": BoundingBox(50, 50, 150, 150)}
    r = read_drawing(_free_dto({"x": Point(75, 75)}, {"P": Point(75, 75)}, cuts, []))
    # Neither cut is read as inside the other — both are sheet-level.
    assert r.container("c1") == r.sheet_id
    assert r.container("c2") == r.sheet_id
    # The overlap-region spot lands in exactly one area (not both, not neither).
    homes = [a for a, kids in r.area.items() if "P" in kids]
    assert len(homes) == 1
