"""
Tension layout engine — an alternative projection that lays the **line of
identity** taut, so a relation sits **between** its argument vertices (the
Peircean single-line reading) instead of ELK's bipartite two-column split.  See
``docs/TENSION_LAYOUT.md`` §9–§11.

It handles the two cases where that reading is well-defined, and **defers to ELK
for everything else**:

- **One thread** — the whole graph is a single line of identity (a path through
  the cut nest): lay it as one taut collinear thread (``_thread_layout``, §10).
- **One tree** — a single line that *forks* (a degree-≥3 junction; one connected
  acyclic ligature): lay it as a small tree pulled taut through the nest
  (``_tree_layout``, §11).
- **Anything else** — a pure-Alpha graph (no line of identity to organize),
  *multiple* threads (a forest sharing a cut nest), a cyclic ligature, or a
  non-monotone line — tension has no special reading to offer, so the engine
  returns the ELK layout rather than impose a cruder placement of its own.

Containment is safe by construction in the thread/tree paths: a line that crosses
an area's boundary is pinned to a **crossing-point proxy** on that boundary (the
proxy set is *given* by the line's crossing-sequence, the §3.3 invariant), so an
inside element is pulled toward its own boundary, never out of its cut.

This is an **opt-in** engine; ELK remains the default.  Every result — tension or
the ELK deferral — is §3.3-attested at the service boundary like any other.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts
from layout_dto import BoundingBox, LayoutDTO, LigaturePath, Point
from presentation_ops import element_area, cut_parents, crossing_sequence
from tension_layout import (
    springs, stress_majorize, extract_thread, extract_tree,
)
from elk_layout_engine import ELKLayoutEngine
from style_loader import StyleSpecification
from correspondence_attestation import attest_correspondence


@dataclass
class _Area:
    """A laid-out area, in its own local coordinates."""
    vpos: Dict[ElementID, Tuple[float, float]] = field(default_factory=dict)
    ppos: Dict[ElementID, Tuple[float, float]] = field(default_factory=dict)
    cbounds: Dict[ElementID, Tuple[float, float, float, float]] = field(default_factory=dict)
    crossings: Dict[Tuple, Tuple[float, float]] = field(default_factory=dict)
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    box: Tuple[float, float] = (0.0, 0.0)


class TensionLayoutEngine:
    PAD = 26.0      # padding inside a cut around its contents
    GAP = 34.0      # base separation between sibling blocks
    DOT = 6.0       # vertex dot half-size
    T_GAP = 16.0    # thread: minimum clearance between consecutive elements
    T_PAD = 22.0    # thread: horizontal nesting inset per cut level
    T_VPAD = 12.0   # thread: vertical nesting inset (small — the thread is
                    # horizontal, so cuts stay short, hugging their elements)
    STRESS = 120.0  # base stress scale
    TR_PAD = 22.0   # tree: horizontal cut inset
    TR_VPAD = 14.0  # tree: vertical cut inset
    TR_MARGIN = 18.0  # tree: clearance when pushing an outside node off a cut box
    TR_GAP = 14.0   # tree: gap added to each edge's ideal length (label clearance)

    def __init__(self, conventions=None):
        self.conventions = conventions  # parity with ELKLayoutEngine; unused yet

    # ------------------------------------------------------------------ #
    # Public                                                             #
    # ------------------------------------------------------------------ #

    def generate_layout(
        self, egi: RelationalGraphWithCuts, style: StyleSpecification,
        layout_deltas: Optional[Dict] = None,
    ) -> LayoutDTO:
        # The tension engine exists to lay out the **line of identity** (a
        # relation between its arguments, ligatures pulled taut).  A pure-Alpha
        # graph — no lines of identity (no predicate–vertex incidence) — has
        # nothing for tension to organize, so a "tension" layout of it is
        # meaningless; defer to ELK, the meaningful default, rather than impose a
        # node placement that is just a worse ELK.
        if not springs(egi):
            return ELKLayoutEngine(self.conventions).generate_layout(
                egi, style, layout_deltas)

        sizes = ELKLayoutEngine()._compute_element_sizes(egi, style)

        # Ligature-first: if the graph is a single line of identity (one thread,
        # no branches), lay it as one taut collinear thread through the cut nest
        # (docs/TENSION_LAYOUT.md §10) — the Peircean reading. Self-attest: a
        # non-monotone thread that doesn't realize its crossing-sequence falls
        # through to the hierarchical node placement below.
        thread = extract_thread(egi)
        if thread is not None:
            try:
                dto = self._thread_layout(egi, style, sizes, thread)
                attest_correspondence(egi, dto, context="tension_engine.thread")
                return dto
            except Exception:
                pass  # non-monotone / unattestable → hierarchical placement

        # Branch generalization: a single line of identity that *forks* (a
        # degree-≥3 junction) is one connected acyclic tree — lay it as a small
        # tree pulled taut through the cut nest (docs/TENSION_LAYOUT.md §11).
        # Try the compact (per-edge-length) embedding first; fall back to the
        # slacker uniform-spaced one if a tight junction can't route cleanly.
        if extract_tree(egi) is not None:
            for weighted in (True, False):
                try:
                    dto = self._tree_layout(egi, style, sizes, weighted=weighted)
                    attest_correspondence(egi, dto, context="tension_engine.tree")
                    return dto
                except Exception:
                    continue  # try the slacker embedding, then defer to ELK

        # Past tension's frontier: multiple threads (a *forest* of ligatures
        # sharing a cut nest), a cyclic ligature, or a non-monotone line that dives
        # into a cut and back out (docs/TENSION_LAYOUT.md §9). Here the taut
        # single-line/tree reading has nothing to organize, so tension offers no
        # advantage — defer to ELK, the proven default, rather than impose a cruder
        # node placement (the same reasoning as the pure-Alpha case above). ELK's
        # output is §3.3-attested at the service boundary like any other.
        return ELKLayoutEngine(self.conventions).generate_layout(
            egi, style, layout_deltas)

    # ------------------------------------------------------------------ #
    # Ligature-first: a single thread laid collinear through the cut nest #
    # ------------------------------------------------------------------ #

    def _thread_layout(self, egi, style, sizes, thread) -> LayoutDTO:
        """Lay the whole line of identity as one taut collinear thread (y = 0)
        with variable spacing — each gap only as wide as what must fit (label
        clearance, plus one nesting inset per cut boundary that crosses there) —
        and cut boxes sized bottom-up so they telescope and nest by construction.
        See ``docs/TENSION_LAYOUT.md`` §10.  Raises (caught by the caller) on a
        non-monotone thread whose cuts don't come out contiguous."""
        from presentation_ops import crossing_sequence
        ea = element_area(egi)
        pm = cut_parents(egi)
        cut_ids = {c.id for c in egi.Cut}
        edge_ids = {e.id for e in egi.E}

        def width(eid):
            return sizes.get(eid, (2 * self.DOT, 2 * self.DOT))[0]

        # Variable spacing along the thread.
        xs = [0.0]
        for a, b in zip(thread, thread[1:]):
            label_gap = (width(a) + width(b)) / 2 + self.T_GAP
            ncross = len(crossing_sequence(ea.get(a), ea.get(b), pm))
            cross_gap = ((width(a) + width(b)) / 2 + (ncross + 1) * self.T_PAD
                         if ncross else 0.0)
            xs.append(xs[-1] + max(label_gap, cross_gap))

        vpos: Dict = {}
        ppos: Dict = {}
        for eid, x in zip(thread, xs):
            (ppos if eid in edge_ids else vpos)[eid] = Point(x, 0.0)

        # Cut boxes bottom-up (telescoping suffixes ⇒ nesting holds).  The
        # horizontal inset clears labels + crossings; the vertical inset is small
        # (a horizontal thread needs no tall band), so cuts stay short and wide,
        # tending to the alignment of their elements.
        cbounds = self._box_cuts(egi, vpos, ppos, sizes, self.T_PAD, self.T_VPAD,
                                 style=style)

        # Ligature paths: each incidence along the axis through its crossings.
        hook = ELKLayoutEngine._predicate_hook_point
        paths: List[LigaturePath] = []
        for e in egi.E:
            if e.id not in ppos:
                continue
            pc = ppos[e.id]
            pw, ph = sizes.get(e.id, (40.0, 18.0))
            for port, v in enumerate(egi.nu.get(e.id, ())):
                if v not in vpos:
                    continue
                vp = vpos[v]
                lo, hi = sorted((pc.x, vp.x))
                mids = []
                for c in crossing_sequence(ea.get(e.id), ea.get(v), pm):
                    b = cbounds[c]
                    edge = (b.min_x if abs(b.min_x - lo) < abs(b.max_x - lo)
                            else b.max_x)
                    edge = min(max(edge, lo), hi)
                    mids.append(Point(edge, 0.0))
                mids.sort(key=lambda p: abs(p.x - pc.x))
                h = hook(pc, pw, ph, mids[0] if mids else vp)
                paths.append(LigaturePath(e.id, v, tuple([h] + mids + [vp]), port))

        allx = [p.x for p in list(vpos.values()) + list(ppos.values())]
        ally = [p.y for p in list(vpos.values()) + list(ppos.values())]
        for b in cbounds.values():
            allx += [b.min_x, b.max_x]; ally += [b.min_y, b.max_y]
        m = 40.0
        vb = (BoundingBox(min(allx) - m, min(ally) - m, max(allx) + m, max(ally) + m)
              if allx else BoundingBox(0, 0, 100, 100))
        return LayoutDTO(
            vertex_positions=vpos, predicate_positions=ppos, cut_bounds=cbounds,
            ligature_paths=paths,
            area_hierarchy={a: set(c) for a, c in egi.area.items()},
            viewport_bounds=vb, sheet_id=egi.sheet, style=style,
        )

    # ------------------------------------------------------------------ #
    # Cut boxing — bottom-up bounding box of each cut's drawn contents    #
    # ------------------------------------------------------------------ #

    def _box_cuts(self, egi, vpos, ppos, sizes, hpad, vpad, style=None) -> Dict:
        """Size every cut to the bounding box of its direct children (a sub-cut
        enters as its own already-sized box) plus an inset, bottom-up — so the
        boxes nest by construction.  Shared by the thread and tree layouts.

        For an **oval** style (Peirce/Sowa) the renderer draws an ellipse
        *inscribed* in the box, which is smaller than the box — so a fixed
        additive inset leaves contents at the corners sitting on (or outside) the
        ellipse.  There the box is instead grown ∝ its content (the same √2 rule
        as ``ELKLayoutEngine._oval_padding``) so the inscribed ellipse contains
        the contents; bottom-up, the growth propagates outward in one pass."""
        cut_ids = {c.id for c in egi.Cut}
        oval = ELKLayoutEngine._cut_is_oval(style) if style is not None else False
        k = (math.sqrt(2.0) - 1.0) / 2.0  # ≈ 0.2071 (see _oval_padding)
        cbounds: Dict = {}

        def box(cid):
            if cid in cbounds:
                return cbounds[cid]
            bxs: List[float] = []
            bys: List[float] = []
            for child in egi.area.get(cid, ()):
                if child in cut_ids:
                    b = box(child)
                    bxs += [b.min_x, b.max_x]; bys += [b.min_y, b.max_y]
                else:
                    p = vpos.get(child) or ppos.get(child)
                    if p is None:
                        continue
                    w, h = sizes.get(child, (10.0, 10.0))
                    bxs += [p.x - w / 2, p.x + w / 2]
                    bys += [p.y - h / 2, p.y + h / 2]
            if not bxs:
                bxs, bys = [0.0], [0.0]
            ph, pv = hpad, vpad
            if oval:
                ph = max(ph, (max(bxs) - min(bxs)) * k + 4.0)
                pv = max(pv, (max(bys) - min(bys)) * k + 4.0)
            b = BoundingBox(min(bxs) - ph, min(bys) - pv,
                            max(bxs) + ph, max(bys) + pv)
            cbounds[cid] = b
            return b

        for c in egi.Cut:
            box(c.id)
        return cbounds

    # ------------------------------------------------------------------ #
    # Ligature-first: a branching line of identity laid as a taut tree    #
    # ------------------------------------------------------------------ #

    def _tree_layout(self, egi, style, sizes, *, weighted: bool = True) -> LayoutDTO:
        """Lay a single *branching* line of identity (one connected acyclic
        ligature, a degree-≥3 junction) as a small **tree pulled taut** through
        the cut nest (docs/TENSION_LAYOUT.md §11) — the branch generalization of
        the collinear thread.

        The incidence graph (predicates + vertices, one node per element) is
        embedded by global stress majorization, with each ligature's
        crossing-sequence inserted as **chained proxy nodes** so a deep incidence
        relaxes to a straight run through the boundaries it must cross.  Stress
        alone ignores containment (it can pull an outside junction *into* a cut's
        hull), so after the solve any node that landed inside a cut it does **not**
        belong to is pushed back out to the nearest boundary; the cut boxes are
        re-derived and the push repeats to a fixpoint.  Raises (caught by the
        caller) on a layout the push can't make containment-clean — it falls
        through to hierarchical placement.

        ``weighted`` gives each edge its own ideal length (a crossing-proxy hop
        stays short, an incidence gets its label's room) so the tree stays
        **compact**; the caller tries this first and falls back to the unweighted
        (uniform-spaced, larger but slacker) embedding if the compact one can't
        route cleanly — a tight junction whose outside line would then re-cross a
        sibling cut.
        """
        ea = element_area(egi)
        pm = cut_parents(egi)
        cut_ids = {c.id for c in egi.Cut}
        edge_ids = {e.id for e in egi.E}
        vids = {v.id for v in egi.V}

        # Half-extent each node needs clear around it: a predicate its label, a
        # vertex its dot, a crossing proxy just the cut inset (a short boundary
        # hop).  An edge's ideal length is the two half-extents plus a gap — so
        # each edge is only as long as it must be (the cure for a branched
        # ligature spreading far past what it needs).
        def ext(n):
            if isinstance(n, tuple):
                return self.TR_PAD
            if n in vids:
                return self.DOT
            w, h = sizes.get(n, (40.0, 18.0))
            return 0.5 * max(w, h)

        # Incidence tree + per-ligature crossing proxies (chained pred→…→vertex).
        nodes = set()
        edges: List[Tuple] = []
        edge_len: Dict[Tuple, float] = {}
        for e in egi.E:
            for v in egi.nu.get(e.id, ()):
                seq = crossing_sequence(ea.get(e.id), ea.get(v), pm)
                chain = [e.id] + [("x", e.id, v, c) for c in seq] + [v]
                for a, b in zip(chain, chain[1:]):
                    edges.append((a, b)); nodes.add(a); nodes.add(b)
                    edge_len[(a, b)] = ext(a) + ext(b) + self.TR_GAP
        order = sorted(nodes, key=str)  # deterministic node order (L1)
        if weighted:
            sol = stress_majorize(order, edges, edge_len=edge_len)
            pos: Dict = {n: Point(x, y) for n, (x, y) in sol.items()}
        else:
            # Unweighted (uniform graph-distance) shape, then compacted to the
            # smallest size whose element boxes don't overlap — the balanced fan
            # at minimal scale (no magic constant), the slacker fallback.
            sol = stress_majorize(order, edges)
            s = self._compact_scale(
                {n: sol[n] for n in order if not isinstance(n, tuple)}, sizes)
            pos = {n: Point(x * s, y * s) for n, (x, y) in sol.items()}

        # Each cut's transitive members (what may legitimately sit in its box).
        member = {c.id: set() for c in egi.Cut}
        for el in [e.id for e in egi.E] + [v.id for v in egi.V] + [c.id for c in egi.Cut]:
            a = ea.get(el)
            while a in member:
                member[a].add(el)
                a = pm.get(a)

        def real(n):
            return not isinstance(n, tuple)

        def boxes():
            vp = {n: p for n, p in pos.items() if real(n) and n in vids}
            pp = {n: p for n, p in pos.items() if real(n) and n in edge_ids}
            return self._box_cuts(egi, vp, pp, sizes, self.TR_PAD, self.TR_VPAD,
                                  style=style)

        cbounds = boxes()
        for _ in range(40):
            moved = False
            for cid in sorted(cut_ids):
                b = cbounds[cid]
                for n in order:
                    if not real(n) or n in member[cid] or n == cid:
                        continue
                    p = pos[n]
                    if b.min_x <= p.x <= b.max_x and b.min_y <= p.y <= b.max_y:
                        pos[n] = Point(*self._push_out(p, b, self.TR_MARGIN))
                        moved = True
            if not moved:
                break
            cbounds = boxes()

        vpos = {n: pos[n] for n in vids if n in pos}
        ppos = {n: pos[n] for n in edge_ids if n in pos}

        # Ligature paths: straight pred→vertex run, each required crossing snapped
        # to where that segment meets the cut box (so the crossing is realized).
        hook = ELKLayoutEngine._predicate_hook_point
        paths: List[LigaturePath] = []
        for e in egi.E:
            if e.id not in ppos:
                continue
            pc = ppos[e.id]
            pw, ph = sizes.get(e.id, (40.0, 18.0))
            p_area = ea.get(e.id)
            for port, v in enumerate(egi.nu.get(e.id, ())):
                if v not in vpos:
                    continue
                vp = vpos[v]
                mids: List[Point] = []
                for c in crossing_sequence(p_area, ea.get(v), pm):
                    hit = self._seg_box_hit(pc, vp, cbounds[c])
                    if hit is not None:
                        mids.append(hit)
                mids.sort(key=lambda m: (m.x - pc.x) ** 2 + (m.y - pc.y) ** 2)
                h = hook(pc, pw, ph, mids[0] if mids else vp)
                if p_area in cbounds:
                    h = Point(*self._clamp_inside(h.x, h.y, cbounds[p_area]))
                paths.append(LigaturePath(e.id, v, tuple([h] + mids + [vp]), port))

        allx = [p.x for p in list(vpos.values()) + list(ppos.values())]
        ally = [p.y for p in list(vpos.values()) + list(ppos.values())]
        for b in cbounds.values():
            allx += [b.min_x, b.max_x]; ally += [b.min_y, b.max_y]
        m = 40.0
        vb = (BoundingBox(min(allx) - m, min(ally) - m, max(allx) + m, max(ally) + m)
              if allx else BoundingBox(0, 0, 100, 100))
        return LayoutDTO(
            vertex_positions=vpos, predicate_positions=ppos, cut_bounds=cbounds,
            ligature_paths=paths,
            area_hierarchy={a: set(c) for a, c in egi.area.items()},
            viewport_bounds=vb, sheet_id=egi.sheet, style=style,
        )

    def _compact_scale(self, elem_pos: Dict, sizes) -> float:
        """The smallest uniform scale (≥ a small floor) at which no two element
        boxes overlap — every pair separated by at least ``GAP`` in some axis.
        Uniform scaling preserves the stress arrangement (so the layout's shape /
        attestation is unchanged), just at the most compact size."""
        items = sorted(elem_pos.items(), key=lambda kv: str(kv[0]))
        s = 1.0
        for i in range(len(items)):
            ka, (ax, ay) = items[i]
            wa, ha = sizes.get(ka, (2 * self.DOT, 2 * self.DOT))
            for j in range(i + 1, len(items)):
                kb, (bx, by) = items[j]
                wb, hb = sizes.get(kb, (2 * self.DOT, 2 * self.DOT))
                dx, dy = abs(ax - bx), abs(ay - by)
                reqx = (wa + wb) / 2 + self.GAP
                reqy = (ha + hb) / 2 + self.GAP
                sx = reqx / dx if dx > 1e-6 else float("inf")
                sy = reqy / dy if dy > 1e-6 else float("inf")
                pair = min(sx, sy)
                if pair != float("inf"):
                    s = max(s, pair)
        return s

    @staticmethod
    def _push_out(p: Point, b: BoundingBox, margin: float) -> Tuple[float, float]:
        """Move ``p`` (inside box ``b``) just outside ``b``'s nearest edge."""
        dl, dr = p.x - b.min_x, b.max_x - p.x
        dt, db = p.y - b.min_y, b.max_y - p.y
        m = min(dl, dr, dt, db)
        if m == dl:
            return (b.min_x - margin, p.y)
        if m == dr:
            return (b.max_x + margin, p.y)
        if m == dt:
            return (p.x, b.min_y - margin)
        return (p.x, b.max_y + margin)

    @staticmethod
    def _seg_box_hit(p: Point, q: Point, b: BoundingBox) -> Optional[Point]:
        """Where segment ``p→q`` first meets rectangle ``b``'s boundary (nearest
        ``p``), or ``None`` if it misses — used to snap a ligature's crossing onto
        the cut boundary so the crossing-sequence is realized geometrically."""
        dx, dy = q.x - p.x, q.y - p.y
        hits: List[Tuple[float, Point]] = []
        for ex in (b.min_x, b.max_x):
            if abs(dx) > 1e-9:
                t = (ex - p.x) / dx
                y = p.y + t * dy
                if 0.0 <= t <= 1.0 and b.min_y - 1e-6 <= y <= b.max_y + 1e-6:
                    hits.append((t, Point(ex, y)))
        for ey in (b.min_y, b.max_y):
            if abs(dy) > 1e-9:
                t = (ey - p.y) / dy
                x = p.x + t * dx
                if 0.0 <= t <= 1.0 and b.min_x - 1e-6 <= x <= b.max_x + 1e-6:
                    hits.append((t, Point(x, ey)))
        if not hits:
            return None
        hits.sort(key=lambda z: z[0])
        return hits[0][1]


    @staticmethod
    # ------------------------------------------------------------------ #
    # Ligature paths through the crossing points                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _clamp_inside(x, y, b: BoundingBox, eps: float = 1.0):
        return (min(max(x, b.min_x + eps), b.max_x - eps),
                min(max(y, b.min_y + eps), b.max_y - eps))


__all__ = ["TensionLayoutEngine"]
