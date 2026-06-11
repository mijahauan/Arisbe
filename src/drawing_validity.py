"""Fix-time validity of a freeform drawing — is this picture a well-formed EG?

This is the *fix-as-read* gate's well-formedness pass for the freeform composition
canvas (docs/FREEFORM_COMPOSITION_AND_LEARNING.md, build step 1).  It is the twin of
``correspondence_attestation`` but for a different situation:

- ``correspondence_attestation.check_correspondence(egi, dto)`` checks a drawing
  against a **known EGI** — the engine attesting *its own* output.  There is already
  a determinate sign; the question is whether the picture faithfully expresses it.
- **this module** checks a drawing with **no EGI yet** — a human's freeform marks.
  ``eg_reader.read_drawing`` is *sound and faithful*: it reads exactly what is drawn,
  even when what is drawn is not a legal EG.  So before we can turn the reading into
  a determinate sign at gate ①, we must catch the drawings the reader *can* read but
  that **aren't well-formed**, and say so in EG vocabulary — not in pixels.

The cases (from the ``read_drawing`` de-risk, pinned in
``tests/test_eg_reader.py::test_freeform_*``) split into two:

**Errors** — the drawing is not a legal EG, so it has no determinate reading:
  - ``overlapping_cuts`` — two cut curves cross.  A cut is a *boundary*; the areas of
    an EG nest into a tree, so two cuts must nest or lie side by side, never overlap
    (the reader silently makes them siblings, inventing no nesting — so we must
    refuse here).
  - ``dangling_line`` — a line of identity has a loose end: an endpoint that touches
    no mark within tolerance.  A line connects a predicate hook to a vertex; a loose
    end connects to nothing (and is exactly the "stops short / drifts" brittleness).

**Warnings** — the drawing reads, but human intent is ambiguous and a small nudge
would remove the doubt:
  - ``boundary_band`` — a mark sits on a cut's boundary stroke, so which area it is
    in is ambiguous.  Place it clearly inside or outside.
  - ``unwired_predicate`` — a predicate has no lines, so it reads as a 0-ary relation
    (legal, but often unintended — attach lines if it takes arguments).
  - ``label_overlap`` — two labels overlap, so neither can be read apart from the
    other.

Draw-time snapping (line endpoints to hooks/vertices; spot placement clearly in/out
of a cut) is the *complement* of this pass: snapping prevents most of these at the
point of drawing; this pass is the backstop at fix time, in EG terms.  Neither is a
reader rewrite — the reader is correct; these are about *intent* and *legality*.

All checks are pure functions of a ``LayoutDTO`` and reuse the geometry of record
(``presentation_ops``) so "what counts as inside / on the boundary" is the same
curve the renderer draws, the reader reads, and §3.3 attests.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from eg_reader import read_drawing
from layout_dto import LayoutDTO, Point
from presentation_ops import (
    boxes_overlap,
    cut_boundary,
    point_in_polygon,
    predicate_label_box,
    resolve_cut_boundaries,
)

# Default tolerances, in DTO coordinate units.  A vertex dot has radius ~2.5–3, so
# ~10u "touches" a mark and ~6u is "on the boundary stroke".  The freeform canvas
# should pass values derived from the live render scale; these are sane fallbacks.
DEFAULT_TOUCH_TOLERANCE = 10.0
DEFAULT_BOUNDARY_BAND = 6.0


@dataclass(frozen=True)
class ValidityIssue:
    """One well-formedness finding about a drawing, phrased in EG vocabulary.

    ``severity`` is ``"error"`` (the drawing is not a legal EG — it has no
    determinate reading) or ``"warning"`` (it reads, but intent is ambiguous).
    ``code`` is a stable machine tag; ``message`` is the human-facing EG-term
    explanation; ``elements`` names the marks involved (so the UI can highlight).
    """

    code: str
    severity: str
    message: str
    elements: Tuple[str, ...] = ()


@dataclass
class ValidityReport:
    """The result of a fix-time validity pass: the issues plus convenience views."""

    issues: List[ValidityIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidityIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidityIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def is_well_formed(self) -> bool:
        """No errors — the drawing has a determinate EG reading (warnings allowed)."""
        return not self.errors


# --------------------------------------------------------------------------- #
# Geometry helpers (closed-boundary straddle + point-to-boundary distance).
# --------------------------------------------------------------------------- #


def _shape(dto: LayoutDTO):
    return getattr(dto.style, "cut_shape", "rounded_rectangle")


def _radius(dto: LayoutDTO) -> float:
    return float(getattr(dto.style, "cut_corner_radius", 0) or 0)


def _cut_polylines(dto: LayoutDTO) -> Dict[str, Tuple[Point, ...]]:
    """A drawn-boundary polyline for **every** cut — the carried freeform polyline
    where one exists, else the analytic ellipse / rounded-rectangle the renderer
    draws (``cut_boundary``).  This is the same curve ``point_in_cut`` tests, so the
    validity geometry matches the picture (no proxy)."""
    shape = _shape(dto)
    radius = _radius(dto)
    carried = resolve_cut_boundaries(dto)
    out: Dict[str, Tuple[Point, ...]] = {}
    for cid, bounds in dto.cut_bounds.items():
        poly = carried.get(cid)
        if poly is None:
            poly = cut_boundary(bounds, shape, radius)
        out[cid] = tuple(poly)
    return out


def _straddles(poly_a: Sequence[Point], poly_b: Sequence[Point]) -> bool:
    """True iff curve ``poly_a`` is partly inside and partly outside the closed
    curve ``poly_b`` — i.e. ``poly_a`` crosses ``poly_b``'s boundary.  Two cuts that
    nest (one wholly in the other) or lie separate (wholly out) never straddle; only
    an *improper overlap* does."""
    flags = [point_in_polygon(p, poly_b) for p in poly_a]
    return any(flags) and not all(flags)


def _point_to_segment_dist(p: Point, a: Point, b: Point) -> float:
    ax, ay, bx, by = a.x, a.y, b.x, b.y
    dx, dy = bx - ax, by - ay
    seg2 = dx * dx + dy * dy
    if seg2 <= 1e-12:
        return math.hypot(p.x - ax, p.y - ay)
    t = ((p.x - ax) * dx + (p.y - ay) * dy) / seg2
    t = max(0.0, min(1.0, t))
    return math.hypot(p.x - (ax + t * dx), p.y - (ay + t * dy))


def _dist_to_boundary(p: Point, poly: Sequence[Point]) -> float:
    """Shortest distance from ``p`` to the closed polyline ``poly`` (its stroke)."""
    n = len(poly)
    if n < 2:
        return math.inf
    return min(
        _point_to_segment_dist(p, poly[i], poly[(i + 1) % n]) for i in range(n)
    )


def _point_to_box_dist(p: Point, box) -> float:
    """Shortest distance from ``p`` to the axis-aligned ``box`` (0 if inside)."""
    dx = max(box.min_x - p.x, 0.0, p.x - box.max_x)
    dy = max(box.min_y - p.y, 0.0, p.y - box.max_y)
    return math.hypot(dx, dy)


def _attachment_dist(pt: Point, dto: LayoutDTO) -> float:
    """How far ``pt`` is from the nearest mark it could attach to — a vertex *dot*
    (distance to its centre) or a predicate *hook* (distance to its drawn label box,
    since a hook sits on the spot's perimeter, not its centre).  An endpoint within
    ``touch_tolerance`` of either is connected; beyond it, the line has a loose end.
    Returns ``inf`` when there are no marks at all."""
    best = math.inf
    for vid, q in dto.vertex_positions.items():
        best = min(best, math.hypot(q.x - pt.x, q.y - pt.y))
    for pid, q in dto.predicate_positions.items():
        box = predicate_label_box(pid, q, dto.style)
        best = min(best, _point_to_box_dist(pt, box))
    return best


# --------------------------------------------------------------------------- #
# The pass.
# --------------------------------------------------------------------------- #


def validate_drawing(
    dto: LayoutDTO,
    *,
    touch_tolerance: float = DEFAULT_TOUCH_TOLERANCE,
    boundary_band: float = DEFAULT_BOUNDARY_BAND,
) -> ValidityReport:
    """Fix-time well-formedness of a freeform drawing, in EG vocabulary.

    Returns a :class:`ValidityReport`.  ``report.is_well_formed`` is true when there
    are no *errors* (the drawing has a determinate EG reading); warnings flag
    ambiguous-but-readable intent.  The drawing is read with
    ``eg_reader.read_drawing`` so the report can speak about what was read; the
    geometric checks use the same drawn curves the reader and §3.3 use.
    """
    issues: List[ValidityIssue] = []
    polys = _cut_polylines(dto)
    cut_ids = list(dto.cut_bounds.keys())

    # -- ERROR: overlapping cuts (the area system must be a tree) ------------- #
    for i in range(len(cut_ids)):
        for j in range(i + 1, len(cut_ids)):
            a, b = cut_ids[i], cut_ids[j]
            pa, pb = polys[a], polys[b]
            if _straddles(pa, pb) or _straddles(pb, pa):
                issues.append(ValidityIssue(
                    code="overlapping_cuts",
                    severity="error",
                    message=(
                        f"Cuts {a} and {b} overlap. A cut is a boundary and the "
                        f"areas of an EG nest into a tree — two cuts must nest one "
                        f"inside the other or lie side by side, never crossing."
                    ),
                    elements=(a, b),
                ))

    # -- ERROR: dangling lines (a loose end touches no mark) ------------------ #
    preds = [(pid, p) for pid, p in dto.predicate_positions.items()]
    verts = [(vid, p) for vid, p in dto.vertex_positions.items()]
    for path in dto.ligature_paths:
        pts = path.points
        if len(pts) < 2:
            issues.append(ValidityIssue(
                code="dangling_line",
                severity="error",
                message="A line of identity is degenerate (fewer than two points).",
                elements=(path.vertex_id, path.predicate_id),
            ))
            continue
        # A line connects a predicate hook to a vertex.  A human line need not be
        # drawn in that direction, so a loose end is one that touches *no* mark at
        # all — neither a vertex dot nor a predicate label box, within tolerance.
        for label, end in (("start", pts[0]), ("end", pts[-1])):
            d = _attachment_dist(end, dto)
            if d > touch_tolerance:
                issues.append(ValidityIssue(
                    code="dangling_line",
                    severity="error",
                    message=(
                        f"A line of identity has a loose {label} — it reaches no "
                        f"predicate hook or vertex (nearest mark is {d:.0f}u away). "
                        f"A line must connect a predicate to a vertex."
                        if math.isfinite(d) else
                        f"A line of identity has a loose {label} and the drawing "
                        f"has no marks to connect it to."
                    ),
                    elements=(path.vertex_id, path.predicate_id),
                ))

    # -- WARNING: a mark sitting on a cut boundary (ambiguous area) ----------- #
    named_marks = [("vertex", vid, p) for vid, p in verts] \
        + [("predicate", pid, p) for pid, p in preds]
    for kind, eid, pos in named_marks:
        for cid in cut_ids:
            if _dist_to_boundary(pos, polys[cid]) <= boundary_band:
                issues.append(ValidityIssue(
                    code="boundary_band",
                    severity="warning",
                    message=(
                        f"{kind.capitalize()} {eid} sits on cut {cid}'s boundary, "
                        f"so which area it is in is ambiguous. Place it clearly "
                        f"inside or outside the cut."
                    ),
                    elements=(eid, cid),
                ))

    # -- WARNING: an unwired predicate reads as a 0-ary relation ------------- #
    reading = read_drawing(dto)
    for pid in dto.predicate_positions:
        if not reading.incidence.get(pid):
            issues.append(ValidityIssue(
                code="unwired_predicate",
                severity="warning",
                message=(
                    f"Predicate {pid} has no lines attached, so it reads as a "
                    f"0-ary relation. If it takes arguments, draw a line of "
                    f"identity from each hook to a vertex."
                ),
                elements=(pid,),
            ))

    # -- WARNING: two labels overlap (neither can be read apart) ------------- #
    boxes = []
    for pid, pos in preds:
        name = pid  # freeform: the drawn label text == the relation name
        boxes.append((pid, predicate_label_box(name, pos, dto.style)))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            id1, b1 = boxes[i]
            id2, b2 = boxes[j]
            if boxes_overlap(b1, b2):
                issues.append(ValidityIssue(
                    code="label_overlap",
                    severity="warning",
                    message=(
                        f"Predicate labels {id1} and {id2} overlap — neither can be "
                        f"read apart from the other. Move them apart."
                    ),
                    elements=(id1, id2),
                ))

    return ValidityReport(issues=issues)


__all__ = ["ValidityIssue", "ValidityReport", "validate_drawing",
           "DEFAULT_TOUCH_TOLERANCE", "DEFAULT_BOUNDARY_BAND"]
