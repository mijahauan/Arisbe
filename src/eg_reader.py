"""Read the EG from a drawn form — the inverse of layout/render.

A drawn form (a ``LayoutDTO``) is **one of three co-equal expressions** of an EG,
alongside its linear form and its EGI.  None of the three is the foundation — the
EG (the thought in the author/reader's mind) is; the three merely express it, and
the correspondence invariant is the claim that they all denote the *same* EG.
``natural_layout`` / the layout engines go EGI→drawn; the linear parsers go
linear→EGI; **this module goes drawn→EG**, completing the symmetry.

It recovers the EG's structure from the drawing by the perceptual moves a person
makes — Peirce's wager that those moves *are* the inference:

- **inside / outside a closed cut line** → which cut contains an element, and the
  nesting of cuts (the area tree);
- **tracing a ligature** from a predicate hook to a vertex → which elements are
  connected (incidence).

The logic is read from **geometry alone**.  It does *not* consult the EGI-derived
``predicate_id`` / ``vertex_id`` carried in ``LigaturePath`` to decide area or
incidence; an element id serves only to *name* a mark ("this dot", "that label"),
exactly as a person would point and say "this one".  Containment is decided by the
drawn cut **shape** (``presentation_ops.point_in_cut`` / ``bounds_in_cut`` keyed on
``style.cut_shape``), so the reading matches what the eye sees in any style.

It recovers everything the drawing encodes: the containing cut, the area, the
co-residents (cuts included), the incidence per predicate, **and the argument
order**.  Order is read by whichever convention the active style draws (see
``style.argument_order_convention``):

- ``"numbered"`` (Dau §11.2; also Sowa CGs) — small numerals ``1..n`` on the lines.
  The numeral on a line *is* ``LigaturePath.port_index`` (what the renderer draws),
  so reading it recovers the order regardless of placement.
- ``"clockwise"`` (Peirce, CP 4.470 / Convention 13) — the hooks are read in
  clockwise order around the spot, starting from the hook vertically above it.  The
  reader recovers the order from the *geometry* (the angle each line leaves the
  predicate), purely perceptually.

So the drawn form carries the full ν — argument order included — and is a genuinely
co-equal expression, not a weaker one.  (Earlier this module declared order
"not visually encoded (R8)"; that was the absence of a drawn convention, not a
limit of pictures — both Peirce and Dau encode it, differently.)
"""

import dataclasses
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from layout_dto import LayoutDTO, Point
from presentation_ops import bounds_in_cut, point_in_cut


@dataclass
class ReadEG:
    """The EG structure recovered from a drawing, by geometry alone."""

    sheet_id: str
    # area id (a cut id, or the sheet) -> the ids of its *direct* children
    # (cuts, predicates, vertices) — the area tree as the eye reads it.
    area: Dict[str, Set[str]] = field(default_factory=dict)
    # predicate id -> the vertices it connects, **in argument order**, read by the
    # style's convention (numbered or clockwise) — the recovered ν sequence.
    incidence: Dict[str, List[str]] = field(default_factory=dict)

    # -- per-element queries (what the author asked to be able to read off any
    #    element: its container, its area's co-residents, its connections) -------

    def container(self, elem_id: str) -> Optional[str]:
        """The area (cut id, or the sheet) that directly contains ``elem_id``."""
        for area_id, kids in self.area.items():
            if elem_id in kids:
                return area_id
        return None

    def co_residents(self, elem_id: str) -> Set[str]:
        """The other elements (cuts included) sharing ``elem_id``'s area."""
        a = self.container(elem_id)
        if a is None:
            return set()
        return self.area.get(a, set()) - {elem_id}

    def connections(self, elem_id: str) -> List[str]:
        """For a predicate, the vertices it connects; for a vertex, the
        predicates incident to it — traced from the drawn ligatures."""
        if elem_id in self.incidence:
            return list(self.incidence[elem_id])
        return [p for p, vs in self.incidence.items() if elem_id in vs]


def _shape(dto: LayoutDTO):
    return getattr(dto.style, "cut_shape", "rounded_rectangle")


def _corner_radius(dto: LayoutDTO) -> float:
    """The drawn corner radius — so containment tests the rounded rectangle the
    renderer actually draws, not a sharp-box proxy (no corner void)."""
    return float(getattr(dto.style, "cut_corner_radius", 0) or 0)


def read_drawing(dto: LayoutDTO) -> ReadEG:
    """Recover the EG structure (area tree + incidence) from a drawn form, using
    only its geometry and the drawn cut shapes — the perceptual reading."""
    shape = _shape(dto)
    radius = _corner_radius(dto)
    cut_ids = list(dto.cut_bounds.keys())

    def box_area(cid: str) -> float:
        b = dto.cut_bounds[cid]
        return (b.max_x - b.min_x) * (b.max_y - b.min_y)

    # Inside/outside a closed line: the deepest cut whose drawn curve contains a
    # point is the smallest one that contains it (cuts nest and do not overlap).
    def deepest_cut_for_point(p: Point) -> Optional[str]:
        best = None
        for cid in cut_ids:
            if point_in_cut(p, dto.cut_bounds[cid], shape, radius):
                if best is None or box_area(cid) < box_area(best):
                    best = cid
        return best

    # A cut's parent is the smallest *other* cut whose drawn curve contains the
    # whole cut.
    def parent_cut_for_cut(cid: str) -> Optional[str]:
        b = dto.cut_bounds[cid]
        best = None
        for oc in cut_ids:
            if oc == cid:
                continue
            if bounds_in_cut(b, dto.cut_bounds[oc], shape, radius):
                if best is None or box_area(oc) < box_area(best):
                    best = oc
        return best

    area: Dict[str, Set[str]] = {dto.sheet_id: set()}
    for cid in cut_ids:
        area.setdefault(cid, set())
    for cid in cut_ids:
        area[parent_cut_for_cut(cid) or dto.sheet_id].add(cid)
    for vid, p in dto.vertex_positions.items():
        area[deepest_cut_for_point(p) or dto.sheet_id].add(vid)
    for pid, p in dto.predicate_positions.items():
        area[deepest_cut_for_point(p) or dto.sheet_id].add(pid)

    # Trace each ligature: its endpoints meet a predicate hook and a vertex dot.
    # Match the *connection* by nearest mark — geometry, not the path's stored ids.
    preds = list(dto.predicate_positions.items())
    verts = list(dto.vertex_positions.items())

    def nearest(pt: Point, items) -> Optional[str]:
        if not items:
            return None
        return min(items, key=lambda kv: (kv[1].x - pt.x) ** 2
                   + (kv[1].y - pt.y) ** 2)[0]

    convention = getattr(dto.style, "argument_order_convention", "numbered")

    def order_key(path, pid: str) -> float:
        """The sort key that recovers argument order from the drawing.  A drawn
        numeral (``order_label``) wins where present — it is the unambiguous mark a
        person reads (Dau's numbers; Peirce's Convention-13 numeric override).
        Otherwise the clockwise convention reads the hook angle, and (fallback for
        an unlabelled drawing) the numbered convention uses ``port_index``."""
        if path.order_label is not None:
            return float(path.order_label)
        if convention == "clockwise":
            # The angle the line leaves the spot, read clockwise from "vertically
            # above" (Peirce).  Screen y grows downward, so increasing atan2(dy,dx)
            # is clockwise; rotate so straight-up (−y) is the 0 start.
            P = dto.predicate_positions[pid]
            ref = path.points[1] if len(path.points) >= 2 else path.points[-1]
            theta = math.atan2(ref.y - P.y, ref.x - P.x)
            return (theta + math.pi / 2) % (2 * math.pi)
        return float(path.port_index)

    # Collect (order_key, vid) per predicate, then sort into the ν sequence.
    pending: Dict[str, List] = {pid: [] for pid in dto.predicate_positions}
    for path in dto.ligature_paths:
        pts = path.points
        if len(pts) < 2:
            continue
        pid = nearest(pts[0], preds)   # predicate-hook end
        vid = nearest(pts[-1], verts)  # vertex end
        if pid is not None and vid is not None:
            pending[pid].append((order_key(path, pid), vid))
    incidence: Dict[str, List[str]] = {
        pid: [vid for _, vid in sorted(items, key=lambda kv: kv[0])]
        for pid, items in pending.items()
    }

    return ReadEG(sheet_id=dto.sheet_id, area=area, incidence=incidence)


def _clockwise_order(dto: LayoutDTO, pid: str) -> List[str]:
    """The vertices of predicate ``pid`` in the clockwise order their hooks leave
    the spot (from 'vertically above'), as the eye reads them — used to decide
    whether the natural placement already shows ν, or needs a numeric override."""
    P = dto.predicate_positions.get(pid)
    if P is None:
        return []
    items = []
    for path in dto.ligature_paths:
        if path.predicate_id != pid or len(path.points) < 2:
            continue
        ref = path.points[1]
        theta = math.atan2(ref.y - P.y, ref.x - P.x)
        items.append(((theta + math.pi / 2) % (2 * math.pi), path.vertex_id))
    return [v for _, v in sorted(items, key=lambda kv: kv[0])]


def assign_order_labels(egi, dto: LayoutDTO) -> LayoutDTO:
    """Return ``dto`` with each ``LigaturePath.order_label`` set per the style's
    argument-order convention, so the drawing carries ν's order visibly:

    - ``"numbered"`` (Dau) — label every line of an ≥2-ary relation (1-based).
    - ``"clockwise"`` (Peirce) — label *only* the relations whose natural
      clockwise hook order does not already match ν (the Convention-13 numeric
      override); relations the placement already shows clockwise stay unlabelled.

    The renderer draws the label and ``read_drawing`` reads it, so the round trip
    recovers the full ν including order under either convention.
    """
    convention = getattr(dto.style, "argument_order_convention", "numbered")
    nu = {e.id: list(egi.nu.get(e.id, ())) for e in egi.E}
    arity = {pid: len(seq) for pid, seq in nu.items()}

    needs_label = {}
    for pid, seq in nu.items():
        if arity[pid] < 2:
            needs_label[pid] = False
        elif convention == "clockwise":
            needs_label[pid] = _clockwise_order(dto, pid) != seq
        else:  # numbered
            needs_label[pid] = True

    new_paths = [
        dataclasses.replace(
            p, order_label=(p.port_index + 1 if needs_label.get(p.predicate_id)
                            else None))
        for p in dto.ligature_paths
    ]
    return dataclasses.replace(dto, ligature_paths=new_paths)


def reading_matches_egi(reading: ReadEG, egi, *, ordered: bool = True) -> bool:
    """Whether the EG read from a drawing is the same EG as ``egi`` — the area
    tree matches exactly and each predicate's incidence matches.  With
    ``ordered`` (default) the incidence must match as a **sequence** (the full ν,
    argument order included, recovered by the style's convention); set
    ``ordered=False`` to compare only the incidence multiset.  This is the drawn→EG
    half of the round trip ``read(render(egi)) == egi``."""
    egi_area = {a: set(c) for a, c in egi.area.items()}
    for a, kids in egi_area.items():
        if reading.area.get(a, set()) != kids:
            return False
    for e in egi.E:
        got = reading.incidence.get(e.id, [])
        want = list(egi.nu.get(e.id, ()))
        if got != want if ordered else sorted(got) != sorted(want):
            return False
    return True


__all__ = ["ReadEG", "read_drawing", "reading_matches_egi", "assign_order_labels"]
