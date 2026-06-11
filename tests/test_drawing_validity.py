"""Tests for the fix-time validity pass (src/drawing_validity.py).

The validity pass is the well-formedness backstop of *fix = read* for the freeform
composition canvas: ``eg_reader.read_drawing`` reads exactly what is drawn, even
when the drawing is not a legal EG, so before a reading becomes a determinate sign
at gate ① we must catch the ill-formed drawings the reader *can* read and report
them in EG vocabulary.  These tests pin the four de-risk cases (overlapping cuts,
dangling line, boundary-band ambiguity, unwired predicate) and confirm clean
engine layouts pass with no errors.

See docs/FREEFORM_COMPOSITION_AND_LEARNING.md (build step 1) and the
``test_freeform_*`` characterizations in tests/test_eg_reader.py.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drawing_validity import validate_drawing
from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
from layout_dto import BoundingBox, LayoutDTO, LigaturePath, Point
from style_loader import load_default_style
from tomos_service import TomosService

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


def _free_dto(verts, preds, cuts, paths, sheet="sheet"):
    """A bare freeform DTO — typed marks at free positions, no EGI (mirrors the
    helper in test_eg_reader.py so the validity cases line up with the reader's)."""
    return LayoutDTO(
        vertex_positions=verts, predicate_positions=preds, cut_bounds=cuts,
        ligature_paths=paths, area_hierarchy={sheet: set()},
        viewport_bounds=BoundingBox(-300, -300, 300, 300),
        sheet_id=sheet, style=load_default_style(),
    )


def _codes(report, severity=None):
    return {i.code for i in report.issues
            if severity is None or i.severity == severity}


# --------------------------------------------------------------------------- #
# Clean engine layouts are well-formed (no false positives).
# --------------------------------------------------------------------------- #


def _corpus_sample(n=12):
    svc = TomosService(TOMOS_ROOT)
    egis = []
    for meta in svc.list_uods()[:n]:
        try:
            egi = svc.load_uod(meta["uod_id"]).current_egi
        except Exception:
            continue
        if egi is not None:
            egis.append(egi)
    return egis


def test_engine_layouts_have_no_errors():
    """A layout the engine produced is a legal EG drawn faithfully, so the validity
    pass must raise no *errors* on it (warnings about 0-ary predicates are allowed —
    they are legal)."""
    engine = ELKLayoutEngine()
    style = load_default_style()
    checked = 0
    for egi in _corpus_sample():
        dto = engine.generate_layout(egi, style)
        report = validate_drawing(dto)
        assert report.is_well_formed, (
            f"engine layout flagged: {[i.message for i in report.errors]}"
        )
        checked += 1
    assert checked > 0


# --------------------------------------------------------------------------- #
# ERROR: overlapping cuts — the area system must be a tree.
# --------------------------------------------------------------------------- #


def test_overlapping_cuts_is_an_error():
    """Two cuts whose curves cross cannot be a valid nesting (the reader makes them
    siblings; the validity pass refuses).  Mirrors
    test_eg_reader.test_freeform_overlapping_cuts_are_not_a_valid_nesting."""
    cuts = {"c1": BoundingBox(0, 0, 100, 100), "c2": BoundingBox(50, 50, 150, 150)}
    report = validate_drawing(_free_dto({}, {}, cuts, []))
    assert not report.is_well_formed
    assert "overlapping_cuts" in _codes(report, "error")


def test_nested_cuts_are_not_overlap():
    """A cut wholly inside another nests — not an overlap error."""
    cuts = {"outer": BoundingBox(0, 0, 200, 200),
            "inner": BoundingBox(50, 50, 100, 100)}
    report = validate_drawing(_free_dto({}, {}, cuts, []))
    assert "overlapping_cuts" not in _codes(report, "error")


def test_separate_cuts_are_not_overlap():
    """Cuts lying side by side are separate — not an overlap error."""
    cuts = {"a": BoundingBox(0, 0, 80, 80), "b": BoundingBox(120, 0, 200, 80)}
    report = validate_drawing(_free_dto({}, {}, cuts, []))
    assert "overlapping_cuts" not in _codes(report, "error")


# --------------------------------------------------------------------------- #
# ERROR: dangling lines — a loose end touches no mark.
# --------------------------------------------------------------------------- #


def test_connected_line_is_not_dangling():
    """A line whose ends reach a predicate hook and a vertex is well-formed."""
    verts = {"x": Point(0, -100)}
    preds = {"P": Point(0, 0)}
    paths = [LigaturePath(predicate_id="P", vertex_id="x",
                          points=(Point(2, -8), Point(0, -98)), port_index=0)]
    report = validate_drawing(_free_dto(verts, preds, {}, paths))
    assert "dangling_line" not in _codes(report, "error")


def test_line_stopping_short_is_dangling():
    """A line that stops short and reaches neither mark has a loose end — exactly
    the brittle drift case from
    test_eg_reader.test_freeform_incidence_is_nearest_endpoint_and_is_brittle, now
    caught as a loose end rather than silently read as a wrong incidence."""
    verts = {"x": Point(0, -100), "y": Point(20, -100)}
    preds = {"P": Point(0, 0)}
    paths = [LigaturePath(predicate_id="P", vertex_id="x",
                          points=(Point(2, -8), Point(15, -55)), port_index=0)]
    report = validate_drawing(_free_dto(verts, preds, {}, paths))
    assert "dangling_line" in _codes(report, "error")


def test_degenerate_line_is_dangling():
    paths = [LigaturePath(predicate_id="P", vertex_id="x",
                          points=(Point(0, 0),), port_index=0)]
    report = validate_drawing(_free_dto({"x": Point(0, -100)}, {"P": Point(0, 0)},
                                        {}, paths))
    assert "dangling_line" in _codes(report, "error")


# --------------------------------------------------------------------------- #
# WARNING: a mark sitting on a cut boundary — ambiguous area.
# --------------------------------------------------------------------------- #


def test_mark_on_boundary_warns():
    """A spot on the cut's drawn boundary stroke is ambiguous; the canvas snaps it,
    the validity pass warns (a warning, not an error — it still reads)."""
    cuts = {"c": BoundingBox(0, 0, 100, 100)}
    report = validate_drawing(_free_dto({"x": Point(0, 50)}, {}, cuts, []))
    assert report.is_well_formed          # readable → no error
    assert "boundary_band" in _codes(report, "warning")


def test_mark_clearly_inside_does_not_warn():
    cuts = {"c": BoundingBox(0, 0, 100, 100)}
    report = validate_drawing(_free_dto({"x": Point(50, 50)}, {}, cuts, []))
    assert "boundary_band" not in _codes(report, "warning")


# --------------------------------------------------------------------------- #
# WARNING: an unwired predicate reads as 0-ary.
# --------------------------------------------------------------------------- #


def test_unwired_predicate_warns():
    report = validate_drawing(_free_dto({}, {"P": Point(0, 0)}, {}, []))
    assert report.is_well_formed          # 0-ary is legal → no error
    assert "unwired_predicate" in _codes(report, "warning")


def test_wired_predicate_does_not_warn():
    verts = {"x": Point(0, -100)}
    preds = {"P": Point(0, 0)}
    paths = [LigaturePath(predicate_id="P", vertex_id="x",
                          points=(Point(2, -8), Point(0, -98)), port_index=0)]
    report = validate_drawing(_free_dto(verts, preds, {}, paths))
    assert "unwired_predicate" not in _codes(report, "warning")


# --------------------------------------------------------------------------- #
# WARNING: overlapping labels.
# --------------------------------------------------------------------------- #


def test_overlapping_labels_warn():
    preds = {"Predicate": Point(0, 0), "Relation": Point(3, 0)}
    report = validate_drawing(_free_dto({}, preds, {}, []))
    assert "label_overlap" in _codes(report, "warning")


def test_separated_labels_do_not_warn():
    preds = {"P": Point(0, 0), "Q": Point(200, 0)}
    report = validate_drawing(_free_dto({}, preds, {}, []))
    assert "label_overlap" not in _codes(report, "warning")
