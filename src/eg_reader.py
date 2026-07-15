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
from presentation_ops import bounds_in_cut, point_in_cut, resolve_cut_boundaries


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
    # Phase 4: a cut carried as an explicit polyline (a human-drawn freeform cut)
    # is read by point-in-polygon against that literal curve; analytic cuts read
    # the drawn ellipse/rounded-rect from cut_bounds + style.
    boundaries = resolve_cut_boundaries(dto)

    def box_area(cid: str) -> float:
        b = dto.cut_bounds[cid]
        return (b.max_x - b.min_x) * (b.max_y - b.min_y)

    # Inside/outside a closed line: the deepest cut whose drawn curve contains a
    # point is the smallest one that contains it (cuts nest and do not overlap).
    def deepest_cut_for_point(p: Point) -> Optional[str]:
        best = None
        for cid in cut_ids:
            if point_in_cut(p, dto.cut_bounds[cid], shape, radius, boundaries.get(cid)):
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
            if bounds_in_cut(b, dto.cut_bounds[oc], shape, radius, boundaries.get(oc)):
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

    def cw_angle(path, pid: str) -> float:
        """The angular position of the *hook* around the spot, read clockwise from
        'vertically above' (Peirce reads the hooks' positions, not the lines'
        directions — so a line may run straight to a far vertex without disturbing
        the order).  The hook is ``points[0]``, on the spot's edge; screen y grows
        downward, so increasing atan2(dy,dx) is clockwise; rotate so straight-up
        (−y) is the 0 start."""
        P = dto.predicate_positions[pid]
        ref = path.points[0]
        return (math.atan2(ref.y - P.y, ref.x - P.x) + math.pi / 2) % (2 * math.pi)

    def order_key(path, pid: str) -> float:
        """Placement-only sort key (no drawn numeral): the clockwise convention
        reads the hook angle; the numbered convention has no geometric order to
        read, so it falls back to the stored ``port_index``."""
        if convention == "clockwise":
            return cw_angle(path, pid)
        return float(path.port_index)

    # Collect (path, vid) per predicate, then recover the ν sequence.
    pending: Dict[str, List] = {pid: [] for pid in dto.predicate_positions}
    for path in dto.ligature_paths:
        pts = path.points
        if len(pts) < 2:
            continue
        pid = nearest(pts[0], preds)   # predicate-hook end
        vid = nearest(pts[-1], verts)  # vertex end
        if pid is not None and vid is not None:
            pending[pid].append((path, vid))

    def order_predicate(pid: str, items: List) -> List[str]:
        """Recover one predicate's argument order from its drawn lines.  Three
        carriers, in the order a reader trusts them:

        - **full numbering** — every line carries a numeral (Dau's numbered
          convention, or the clockwise full-disambiguation fallback): sort by
          the numerals.
        - **single anchor** — exactly one line carries a numeral (Peirce's
          Convention-13 start index): the *clockwise placement* gives the cyclic
          order and the anchor says where ν begins, so rotate the clockwise sort
          to start at the anchored line.  One mark carries the order at any arity.
        - **placement only** — no numeral: read clockwise from vertically-above
          (clockwise), or fall back to the stored port (numbered-with-numerals-
          hidden, where order simply isn't drawn).
        """
        n = len(items)
        labeled = [(p, v) for (p, v) in items if p.order_label is not None]
        if n >= 2 and len(labeled) == n:
            return [v for _, v in sorted(items, key=lambda pv: pv[0].order_label)]
        if n >= 2 and len(labeled) == 1:
            ranked = sorted(items, key=lambda pv: cw_angle(pv[0], pid))
            anchor = labeled[0][0]
            ai = next(i for i, (p, _) in enumerate(ranked) if p is anchor)
            ranked = ranked[ai:] + ranked[:ai]
            return [v for _, v in ranked]
        return [v for _, v in sorted(items, key=lambda pv: order_key(pv[0], pid))]

    incidence: Dict[str, List[str]] = {
        pid: order_predicate(pid, items) for pid, items in pending.items()
    }

    return ReadEG(sheet_id=dto.sheet_id, area=area, incidence=incidence)


def _clockwise_order(dto: LayoutDTO, pid: str) -> List[str]:
    """The vertices of predicate ``pid`` in the clockwise order of their *hooks*
    around the spot (from 'vertically above'), as the eye reads them — the hook is
    ``points[0]`` on the spot's edge (Peirce reads hook positions, not line
    directions).  Used to decide whether the placement already shows ν."""
    P = dto.predicate_positions.get(pid)
    if P is None:
        return []
    items = []
    for path in dto.ligature_paths:
        if path.predicate_id != pid or len(path.points) < 2:
            continue
        ref = path.points[0]
        theta = math.atan2(ref.y - P.y, ref.x - P.x)
        items.append(((theta + math.pi / 2) % (2 * math.pi), path.vertex_id))
    return [v for _, v in sorted(items, key=lambda kv: kv[0])]


def _rotation_offset(seq: List[str], cyc: List[str]):
    """The k such that ``seq[i] == cyc[(i+k) % n]`` for all i — i.e. ``seq`` is
    ``cyc`` read cyclically starting k steps in — or ``None`` if ``seq`` is not a
    rotation of ``cyc``.  When ν is a rotation of the clockwise hook order, the
    placement already carries the order *up to where you start reading*, so a
    single start anchor (Conv. 13) suffices to pin it — no per-line numbering."""
    n = len(seq)
    if n == 0 or n != len(cyc) or sorted(seq) != sorted(cyc):
        return None
    for k in range(n):
        if all(seq[i] == cyc[(i + k) % n] for i in range(n)):
            return k
    return None


def assign_order_labels(egi, dto: LayoutDTO) -> LayoutDTO:
    """Return ``dto`` with ``LigaturePath.order_label`` set so the drawing carries
    ν's order with as few drawn numerals as the convention allows.

    Under the **clockwise** convention (Peirce) order lives in the *placement* —
    the hooks read clockwise from vertically-above.  So a relation needs:

    - *no numeral* when the clockwise hook order already reads ν;
    - a *single start anchor* (the numeral 1 on ν's first line — Convention 13's
      start index) when ν is a rotation of the clockwise order: the placement
      gives the cyclic order, the anchor says where it begins.  **One mark, any
      arity** — this is the "distinguished argument" carrier, not a number on
      every line;
    - *full numbering* only when the hook order is a genuine permutation of ν
      (not a rotation), which placement cannot disambiguate with one mark.

    Under the **numbered** convention (Dau) every ≥2-ary line is numbered.

    The ``argument_order_numerals`` knob overrides this per drawing: ``"always"``
    numbers every ≥2-ary line, ``"never"`` draws none (rely on placement),
    ``"auto"`` (default) is the per-convention behaviour above.

    The renderer draws the label and ``read_drawing`` reads it back, so the round
    trip recovers the full ν including order; in ``"never"`` mode (or where no
    anchor is drawn) the clockwise placement carries it alone.
    """
    convention = getattr(dto.style, "argument_order_convention", "numbered")
    numerals = getattr(dto.style, "argument_order_numerals", "auto")
    nu = {e.id: list(egi.nu.get(e.id, ())) for e in egi.E}
    arity = {pid: len(seq) for pid, seq in nu.items()}

    # Per predicate: "none" (placement carries it), "anchor" (one start index),
    # or "full" (number every line).
    mode: Dict[str, str] = {}
    for pid, seq in nu.items():
        if arity[pid] < 2 or numerals == "never":
            mode[pid] = "none"
        elif numerals == "always":
            mode[pid] = "full"
        elif convention == "clockwise":
            cw = _clockwise_order(dto, pid)
            if cw == seq:
                mode[pid] = "none"           # placement already reads ν
            elif (len(set(seq)) == len(seq)
                  and _rotation_offset(seq, cw) is not None):
                # One start index pins the rotation — but only when the
                # arguments are distinct: with a repeated vertex (e.g.
                # (sum x y x)) the value-level rotation offset can point at
                # the *other* hook of the repeated vertex than the one that
                # carries ν's first argument, so the anchor would mark the
                # wrong line and the read comes back permuted.
                mode[pid] = "anchor"
            else:
                mode[pid] = "full"           # permutation or repeated argument
        else:  # numbered
            mode[pid] = "full"

    def label_for(p):
        m = mode.get(p.predicate_id, "none")
        if m == "full":
            return p.port_index + 1
        if m == "anchor":
            return 1 if p.port_index == 0 else None  # mark ν's first line only
        return None

    new_paths = [
        dataclasses.replace(p, order_label=label_for(p))
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
