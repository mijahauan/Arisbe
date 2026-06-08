"""
Tests for src/correspondence_attestation.py.

Two layers:

1. Happy-path corpus sweep — for every tomos UoD, render the layout
   and confirm ``attest_correspondence`` accepts it.  This is
   redundant with the §7 property tests in
   ``test_correspondence_invariant.py`` (those run the same checks
   through ``_check_correspondence``), but it pins down that the
   module-level entry point agrees with the test-level helper at
   every UoD.

2. Adversarial unit tests — construct a (DTO, EGI) pair that
   deliberately violates one §3.3 property and confirm
   ``attest_correspondence`` raises ``CorrespondenceViolation`` with
   the expected failure surfaced in the message.

The intent is to make the module a load-bearing contract: if a
production boundary hook calls ``attest_correspondence`` and gets a
clean return, the (EGI, drawing) pair really is in correspondence.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from correspondence_attestation import (
    CorrespondenceViolation,
    attest_correspondence,
    check_correspondence,
    is_in_correspondence,
)
from elk_layout_engine import ELKLayoutEngine
from layout_dto import BoundingBox, LayoutDTO, LigaturePath, Point
from style_loader import load_default_style
from tomos_service import TomosService


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


@pytest.fixture(scope="module")
def tomos():
    return TomosService(TOMOS_ROOT)


@pytest.fixture(scope="module")
def engine():
    return ELKLayoutEngine()


@pytest.fixture(scope="module")
def style():
    return load_default_style()


def _uod_ids():
    service = TomosService(TOMOS_ROOT)
    return [u["uod_id"] for u in service.list_uods()]


# --------------------------------------------------------------------------- #
# Happy-path corpus sweep                                                     #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_attest_accepts_freshly_rendered_corpus(uod_id, tomos, engine, style):
    """Every tomos UoD's freshly-rendered DTO is attested as in correspondence."""
    egi = tomos.load_uod(uod_id).current_egi
    dto = engine.generate_layout(egi, style)
    attest_correspondence(egi, dto, context=f"freshly-rendered {uod_id}")


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_is_in_correspondence_predicate_agrees(uod_id, tomos, engine, style):
    """is_in_correspondence returns True for freshly-rendered DTOs."""
    egi = tomos.load_uod(uod_id).current_egi
    dto = engine.generate_layout(egi, style)
    assert is_in_correspondence(egi, dto)
    assert check_correspondence(egi, dto) == []


# --------------------------------------------------------------------------- #
# Adversarial unit tests — each constructs a deliberately broken DTO and      #
# asserts the corresponding §3.3 property is the one named in the failure.   #
# --------------------------------------------------------------------------- #


def _baseline(tomos, engine, style):
    """Find a UoD whose layout has at least one cut and at least one ligature.

    Returns (egi, dto).  Most tomos UoDs satisfy this; we just take the
    first that does so the adversarial tests have material to corrupt.
    """
    for u in tomos.list_uods():
        egi = tomos.load_uod(u["uod_id"]).current_egi
        dto = engine.generate_layout(egi, style)
        if egi.Cut and dto.ligature_paths:
            return egi, dto
    pytest.skip("no tomos UoD has both a cut and a ligature")


def _clone_dto(dto, **overrides):
    """Return a new DTO with the given fields overridden."""
    return LayoutDTO(
        vertex_positions=overrides.get(
            "vertex_positions", dict(dto.vertex_positions)
        ),
        predicate_positions=overrides.get(
            "predicate_positions", dict(dto.predicate_positions)
        ),
        cut_bounds=overrides.get("cut_bounds", dict(dto.cut_bounds)),
        ligature_paths=overrides.get(
            "ligature_paths", list(dto.ligature_paths)
        ),
        area_hierarchy={k: set(v) for k, v in dto.area_hierarchy.items()},
        viewport_bounds=dto.viewport_bounds,
        sheet_id=dto.sheet_id,
        style=dto.style,
    )


def test_attest_raises_on_missing_vertex_position(tomos, engine, style):
    """Removing a vertex from vertex_positions triggers a totality failure."""
    egi, dto = _baseline(tomos, engine, style)
    missing_vid = next(iter(dto.vertex_positions))
    new_positions = {
        k: v for k, v in dto.vertex_positions.items() if k != missing_vid
    }
    broken = _clone_dto(dto, vertex_positions=new_positions)

    with pytest.raises(CorrespondenceViolation) as excinfo:
        attest_correspondence(egi, broken, context="missing-vertex test")
    msg = str(excinfo.value)
    assert "totality" in msg
    assert missing_vid in msg
    # The context label propagates.
    assert "missing-vertex test" in msg
    # Structured access still works.
    assert any("totality" in f for f in excinfo.value.failures)


def test_attest_raises_on_stray_predicate_id(tomos, engine, style):
    """Adding a predicate position not in the EGI triggers an injectivity failure."""
    egi, dto = _baseline(tomos, engine, style)
    new_predicates = dict(dto.predicate_positions)
    new_predicates["stray_predicate_xyz"] = Point(0, 0)
    broken = _clone_dto(dto, predicate_positions=new_predicates)

    with pytest.raises(CorrespondenceViolation) as excinfo:
        attest_correspondence(egi, broken)
    assert "injectivity" in str(excinfo.value)
    assert "stray_predicate_xyz" in str(excinfo.value)


def test_attest_raises_on_vertex_outside_cut(tomos, engine, style):
    """Moving a vertex outside its cut bounds triggers a containment failure."""
    # Find a UoD with a vertex that lives inside a cut.
    target = None
    for u in tomos.list_uods():
        egi = tomos.load_uod(u["uod_id"]).current_egi
        dto = engine.generate_layout(egi, style)
        cut_ids = {c.id for c in egi.Cut}
        for area_id, contents in egi.area.items():
            if area_id not in cut_ids:
                continue
            for elem_id in contents:
                if elem_id in dto.vertex_positions:
                    target = (egi, dto, elem_id, area_id)
                    break
            if target:
                break
        if target:
            break
    if target is None:
        pytest.skip("no tomos UoD has a vertex inside a cut")

    egi, dto, vid, cid = target
    bounds = dto.cut_bounds[cid]
    new_positions = dict(dto.vertex_positions)
    # Place the vertex outside the cut to the right.
    new_positions[vid] = Point(bounds.max_x + 100, dto.vertex_positions[vid].y)
    broken = _clone_dto(dto, vertex_positions=new_positions)

    with pytest.raises(CorrespondenceViolation) as excinfo:
        attest_correspondence(egi, broken)
    failures = excinfo.value.failures
    # At least one containment failure mentioning our vertex; the
    # identity-endpoint check will also fire because the ligature path's
    # last point no longer coincides with the vertex's new position
    # (we didn't cascade — and that's the point: the violation is real).
    assert any("containment" in f and vid in f for f in failures), (
        f"expected containment failure for {vid}, got:\n  "
        + "\n  ".join(failures)
    )


def test_containment_is_read_from_the_drawn_shape(engine):
    """The drawn cut boundary is authoritative for containment, so the *shape*
    determines which area an element is in.  A predicate placed near a box corner
    (inside the box, outside the inscribed ellipse) is contained under a box
    style (Dau) but *not* under an oval style (Peirce) — same geometry, the shape
    decides.  This is the principled replacement for episodic style-padding."""
    import dataclasses
    from egif_parser_dau import parse_egif
    from style_loader import load_default_style, load_style

    egi = parse_egif("~[ (P) ]")  # one cut, one nullary predicate inside it
    (cut_id,) = [c.id for c in egi.Cut]
    (pid,) = [e.id for e in egi.E]
    dau = load_default_style()
    dto = engine.generate_layout(egi, dau)
    b = dto.cut_bounds[cut_id]
    # A point just inside the box's top-left corner — well outside the inscribed
    # ellipse ((−0.9)²+(−0.9)² = 1.62 > 1 in the ellipse's unit frame).
    corner = Point(b.min_x + 0.05 * (b.max_x - b.min_x),
                   b.min_y + 0.05 * (b.max_y - b.min_y))
    moved = _clone_dto(dto, predicate_positions={**dto.predicate_positions,
                                                 pid: corner})

    # Box style: the corner is inside → attests.
    attest_correspondence(egi, moved)  # must not raise

    # Oval style: same point, now outside the drawn ellipse → refused.
    oval = dataclasses.replace(moved, style=load_style("peirce-authentic@1.0"))
    with pytest.raises(CorrespondenceViolation) as excinfo:
        attest_correspondence(egi, oval)
    assert any("containment" in f and pid in f for f in excinfo.value.failures)


def test_attest_raises_on_ligature_endpoint_mismatch(tomos, engine, style):
    """If a ligature's last point doesn't equal its vertex position, raise."""
    egi, dto = _baseline(tomos, engine, style)
    if not dto.ligature_paths:
        pytest.skip("baseline UoD has no ligature paths")
    target = dto.ligature_paths[0]
    # Shift the last point by (10, 10), leaving the vertex position alone.
    pts = list(target.points)
    pts[-1] = Point(pts[-1].x + 10.0, pts[-1].y + 10.0)
    new_paths = list(dto.ligature_paths)
    new_paths[0] = LigaturePath(
        predicate_id=target.predicate_id,
        vertex_id=target.vertex_id,
        points=tuple(pts),
        port_index=target.port_index,
    )
    broken = _clone_dto(dto, ligature_paths=new_paths)

    with pytest.raises(CorrespondenceViolation) as excinfo:
        attest_correspondence(egi, broken)
    assert "identity-endpoint" in str(excinfo.value)


def test_attest_raises_on_forbidden_cut_crossing(engine, style):
    """A ligature that dips into a cut not on its area chain is rejected.

    This is the capability the earlier sampled area-membership check
    lacked: point/midpoint sampling could miss a curve that crossed into
    a forbidden cut and back out between samples.  The crossing-multiset
    check counts true boundary crossings, so a forbidden-cut excursion is
    caught regardless of where its turning points fall.

    Construction: render a sibling-cut graph (clean to start), then
    splice a waypoint at the center of a cut that is NOT on a chosen
    ligature's required-crossing path.  The detour enters and exits that
    forbidden cut (two boundary crossings) — exactly what must be
    refused.
    """
    from egif_parser_dau import parse_egif
    from natural_layout import natural_layout

    egi = parse_egif("(P *x) ~[ (Q x) ] ~[ (R x) ]")
    dto = engine.generate_layout(egi, style)
    # Sanity: the freshly-rendered sibling graph is in correspondence.
    assert check_correspondence(egi, dto) == []

    nat = natural_layout(egi)
    paths = {
        (p.predicate_id, p.vertex_id, p.port_index): p
        for p in dto.ligature_paths
    }

    target = None
    for lig in nat.ligatures:
        required = set(lig.required_crossings)
        path = paths.get((lig.predicate_id, lig.vertex_id, lig.port_index))
        if path is None or len(path.points) < 2:
            continue
        for cut in egi.Cut:
            if cut.id in required:
                continue
            bounds = dto.cut_bounds.get(cut.id)
            if bounds is not None:
                target = (path, cut.id, bounds)
                break
        if target:
            break
    if target is None:
        pytest.skip("no forbidden-cut / ligature pair to corrupt")

    path, forbidden_cid, bounds = target
    center = Point((bounds.min_x + bounds.max_x) / 2,
                   (bounds.min_y + bounds.max_y) / 2)
    pts = list(path.points)
    detoured = [pts[0], center] + pts[1:]  # dip into the forbidden cut

    new_paths = [p for p in dto.ligature_paths if p is not path]
    new_paths.append(
        LigaturePath(
            predicate_id=path.predicate_id,
            vertex_id=path.vertex_id,
            points=tuple(detoured),
            port_index=path.port_index,
        )
    )
    broken = _clone_dto(dto, ligature_paths=new_paths)

    with pytest.raises(CorrespondenceViolation) as excinfo:
        attest_correspondence(egi, broken)
    msg = str(excinfo.value)
    assert "identity-crossing" in msg
    assert forbidden_cid in msg


def test_correspondence_violation_message_contains_context(tomos, engine, style):
    """The exception's message includes the context label and failure count."""
    egi, dto = _baseline(tomos, engine, style)
    new_positions = dict(dto.vertex_positions)
    if not new_positions:
        pytest.skip("baseline UoD has no vertex positions")
    new_positions["stray_vid"] = Point(0, 0)
    broken = _clone_dto(dto, vertex_positions=new_positions)

    with pytest.raises(CorrespondenceViolation) as excinfo:
        attest_correspondence(
            egi, broken, context="after applying ERA at sheet"
        )
    msg = str(excinfo.value)
    assert "after applying ERA at sheet" in msg
    assert "Correspondence violated at" in msg
    assert "failure" in msg
