"""
Edge-case audit for the ELK layout engine's ligature routing.

These tests cover three areas NOT exercised by ``test_elk_layout_engine.py``:

1. **Beta cross-cut ligatures** — a vertex defined at the sheet but
   referenced inside a deeply nested cut produces a polyline that must
   enter each enclosing cut exactly once and never enter an unrelated
   (sibling) cut.

2. **Large-EGI layout performance** — ELK's compound-graph layout time
   is non-trivial for hundreds of elements.  A smoke timing assertion
   guards against accidental quadratic regressions.

3. **Dense relation graphs** — n-ary predicates (n ≥ 3) over a small
   vertex set produce edge bundles that should not overlap as collinear
   segments.

The intent is *diagnostic* — see Issue #5.  Tests that surface genuine
bugs are XFAIL'd with a pointer to the follow-up issue rather than
silently masked.
"""

import math
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egi_core_dau import ElementID, RelationalGraphWithCuts
from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
from layout_dto import BoundingBox, LayoutDTO, LigaturePath, Point
from style_loader import load_default_style


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def style():
    return load_default_style()


@pytest.fixture(scope="module")
def engine():
    return ELKLayoutEngine()


# ---------------------------------------------------------------------------
# Geometric helpers
# ---------------------------------------------------------------------------


def _segment_crosses_rect_boundary(p1: Point, p2: Point, bb: BoundingBox) -> bool:
    """True if segment (p1, p2) crosses any edge of *bb*.

    Reuses ELKLayoutEngine's own predicate so the test definition of
    "crossing" matches the engine's.
    """
    return ELKLayoutEngine._seg_crosses_rect(p1, p2, bb)


def _path_boundary_crossings(path: Tuple[Point, ...], bb: BoundingBox) -> int:
    """Number of polyline edges that cross the bounding-box boundary."""
    return sum(
        _segment_crosses_rect_boundary(path[i], path[i + 1], bb)
        for i in range(len(path) - 1)
    )


def _point_strictly_inside(p: Point, bb: BoundingBox, eps: float = 0.5) -> bool:
    """True if *p* is strictly inside *bb* with an *eps* slack on the boundary."""
    return (
        bb.min_x + eps < p.x < bb.max_x - eps
        and bb.min_y + eps < p.y < bb.max_y - eps
    )


def _path_intersects_rect_interior(
    path: Tuple[Point, ...], bb: BoundingBox
) -> bool:
    """True if any polyline edge passes through (or starts inside) *bb*."""
    for i in range(len(path) - 1):
        if _point_strictly_inside(path[i], bb) or _point_strictly_inside(
            path[i + 1], bb
        ):
            return True
        if _segment_crosses_rect_boundary(path[i], path[i + 1], bb):
            return True
    return False


def _build_element_to_area(egi: RelationalGraphWithCuts) -> Dict[ElementID, ElementID]:
    elem_area: Dict[ElementID, ElementID] = {}
    for area_id, contents in egi.area.items():
        for m in contents:
            elem_area[m] = area_id
    return elem_area


def _ancestor_chain(area_id: ElementID, parent_of: Dict[ElementID, ElementID]) -> List[ElementID]:
    chain = [area_id]
    cur = area_id
    while cur in parent_of:
        cur = parent_of[cur]
        chain.append(cur)
    return chain


def _build_cut_parent_map(
    egi: RelationalGraphWithCuts,
) -> Dict[ElementID, ElementID]:
    cut_ids = {c.id for c in egi.Cut}
    parent: Dict[ElementID, ElementID] = {}
    for area_id, contents in egi.area.items():
        for elem_id in contents:
            if elem_id in cut_ids:
                parent[elem_id] = area_id
    return parent


def _authorized_cuts_for(
    pred_area: ElementID,
    vert_area: ElementID,
    cut_parent: Dict[ElementID, ElementID],
) -> Set[ElementID]:
    """Cuts whose *boundary* the ligature is allowed to cross.

    These are exactly the cuts on the area-hierarchy path from
    *pred_area* up to (but excluding) the LCA, plus the path from
    *vert_area* up to (but excluding) the LCA.  Cuts that enclose both
    endpoints (the LCA and its ancestors) are not in this set because
    the ligature lies entirely inside them — no boundary crossing
    occurs.
    """
    if pred_area == vert_area:
        return set()
    pred_chain = _ancestor_chain(pred_area, cut_parent)
    vert_chain = _ancestor_chain(vert_area, cut_parent)
    pred_set, vert_set = set(pred_chain), set(vert_chain)
    out: Set[ElementID] = set()
    for a in pred_chain:
        if a in vert_set:
            break
        out.add(a)
    for a in vert_chain:
        if a in pred_set:
            break
        out.add(a)
    return out


def _touchable_cuts_for(
    pred_area: ElementID,
    vert_area: ElementID,
    cut_parent: Dict[ElementID, ElementID],
) -> Set[ElementID]:
    """Cuts whose bbox the ligature is *permitted to occupy*.

    This is the union of the ancestor chains of *pred_area* and
    *vert_area* (each chain restricted to cuts).  A cut on either chain
    either encloses an endpoint or is crossed by the ligature — both are
    acceptable.  Any cut NOT in this set is "unrelated" and the
    ligature must not intersect its interior bbox.
    """
    pred_chain = _ancestor_chain(pred_area, cut_parent)
    vert_chain = _ancestor_chain(vert_area, cut_parent)
    return set(pred_chain) | set(vert_chain)


# ---------------------------------------------------------------------------
# 1. Beta cross-cut ligature routing
# ---------------------------------------------------------------------------


class TestBetaCrossCutLigatures:
    """A vertex shared across multiple nested cut levels must produce
    ligatures whose polylines respect EG area containment.

    Geometric properties asserted:
    - For each ligature, the polyline crosses each *authorized* enclosing
      cut boundary exactly once.
    - The polyline does not enter the bounding box of any *unauthorized*
      (unrelated / sibling) cut.
    """

    def test_two_level_beta_chain(self, engine, style):
        # Two nested cuts on the shared vertex *x, plus a sibling cut on
        # an unrelated vertex *y.  Ligature R-x must cross the inner and
        # outer cut boundaries exactly once each and stay clear of the
        # sibling cut entirely.
        egi = parse_egif(
            "(P *x) ~[ (Q x) ~[ (R x) ] ] ~[ (S *y) ]"
        )
        dto = engine.generate_layout(egi, style)

        cut_parent = _build_cut_parent_map(egi)
        elem_area = _build_element_to_area(egi)

        # Identify the named cuts by inspecting which predicates each cut
        # transitively contains.
        cut_label: Dict[ElementID, str] = {}
        for cut in egi.Cut:
            preds_in_cut: Set[str] = set()
            stack = [cut.id]
            while stack:
                cur = stack.pop()
                for m in egi.area.get(cur, frozenset()):
                    if m in {e.id for e in egi.E}:
                        preds_in_cut.add(egi.get_relation_name(m))
                    elif m in {c.id for c in egi.Cut}:
                        stack.append(m)
            if "Q" in preds_in_cut and "R" in preds_in_cut:
                cut_label[cut.id] = "outer"
            elif preds_in_cut == {"R"}:
                cut_label[cut.id] = "inner"
            elif "S" in preds_in_cut:
                cut_label[cut.id] = "sibling"

        assert set(cut_label.values()) == {"outer", "inner", "sibling"}, (
            f"unexpected cut labelling: {cut_label}"
        )
        outer_id = next(k for k, v in cut_label.items() if v == "outer")
        inner_id = next(k for k, v in cut_label.items() if v == "inner")
        sibling_id = next(k for k, v in cut_label.items() if v == "sibling")

        # Find the R-x ligature.
        r_edge_id = next(e.id for e in egi.E if egi.get_relation_name(e.id) == "R")
        x_vertex_id = next(iter(egi.nu[r_edge_id]))

        r_to_x = next(
            lp
            for lp in dto.ligature_paths
            if lp.predicate_id == r_edge_id and lp.vertex_id == x_vertex_id
        )

        # Authorized = outer + inner; unauthorized = sibling.
        authorized = _authorized_cuts_for(
            elem_area[r_edge_id], elem_area[x_vertex_id], cut_parent
        )
        assert authorized == {outer_id, inner_id}

        # Exactly one boundary crossing per authorized cut.
        for cut_id in authorized:
            bb = dto.cut_bounds[cut_id]
            crossings = _path_boundary_crossings(r_to_x.points, bb)
            assert crossings == 1, (
                f"ligature R-x crosses authorized cut "
                f"'{cut_label[cut_id]}' boundary {crossings}× (expected 1)\n"
                f"  path={r_to_x.points}\n  cut={bb}"
            )

        # Sibling cut must not be touched.
        sibling_bb = dto.cut_bounds[sibling_id]
        assert not _path_intersects_rect_interior(r_to_x.points, sibling_bb), (
            f"ligature R-x enters sibling-cut bbox {sibling_bb}\n"
            f"  path={r_to_x.points}"
        )

        # Belt-and-braces: every ligature in the dto should also avoid
        # the interior of every cut that doesn't enclose-or-cross-for it.
        for lp in dto.ligature_paths:
            pa, va = elem_area[lp.predicate_id], elem_area[lp.vertex_id]
            touchable = _touchable_cuts_for(pa, va, cut_parent)
            for cid, cbb in dto.cut_bounds.items():
                if cid in touchable:
                    continue
                assert not _path_intersects_rect_interior(lp.points, cbb), (
                    f"ligature "
                    f"{egi.get_relation_name(lp.predicate_id)}-{lp.vertex_id} "
                    f"enters unrelated cut '{cut_label.get(cid, cid)}'\n"
                    f"  path={lp.points}\n  cut={cbb}"
                )

    def test_three_level_beta_chain(self, engine, style):
        """Three-level Beta chain: vertex on sheet, predicates at three depths.

        Each ligature should cross exactly its chain of enclosing cuts."""
        egi = parse_egif(
            "(P *x) ~[ (Q x) ~[ (R x) ~[ (S x) ] ] ]"
        )
        dto = engine.generate_layout(egi, style)

        cut_parent = _build_cut_parent_map(egi)
        elem_area = _build_element_to_area(egi)

        for lp in dto.ligature_paths:
            pa, va = elem_area[lp.predicate_id], elem_area[lp.vertex_id]
            auth = _authorized_cuts_for(pa, va, cut_parent)
            for cid in auth:
                bb = dto.cut_bounds[cid]
                crossings = _path_boundary_crossings(lp.points, bb)
                pred_name = lp.predicate_id  # ids not labels but adequate
                assert crossings == 1, (
                    f"ligature {pred_name}-{lp.vertex_id} "
                    f"crosses authorized cut '{cid}' {crossings}× (expected 1)"
                )


# ---------------------------------------------------------------------------
# 2. Large-EGI layout performance
# ---------------------------------------------------------------------------


def _make_large_egi_text(n_predicates: int = 50) -> str:
    """Return an EGIF source for ~3*n_predicates elements.

    Layout shape: ``n_predicates`` siblings of the form ``~[ (R_i *x_i) ]``.
    Each contributes one cut + one vertex + one predicate, so total elements
    are 3 * n_predicates (e.g. n=50 → 150 elements)."""
    parts = [f"~[ (R{i} *x{i}) ]" for i in range(n_predicates)]
    return " ".join(parts)


class TestLargeEGIPerformance:
    """Soft latency budget — flags accidental quadratic regressions.

    The numbers here are intentionally generous (5s for 150 elements).
    A clean fast run is ~1-3s on the dev laptop documented in
    ``docs/ELK_LAYOUT_IMPLEMENTATION_SUMMARY.md``."""

    LATENCY_BUDGET_SECONDS = 5.0
    N_PREDICATES = 50  # → 150 elements

    def test_large_egi_layout_within_budget(self, engine, style):
        egi = parse_egif(_make_large_egi_text(self.N_PREDICATES))
        total_elements = len(egi.V) + len(egi.E) + len(egi.Cut)
        assert total_elements >= 100, (
            f"sanity: expected ≥100 elements, got {total_elements}"
        )

        t0 = time.perf_counter()
        dto = engine.generate_layout(egi, style)
        elapsed = time.perf_counter() - t0

        # Sanity-check the result is complete.
        assert len(dto.vertex_positions) == len(egi.V)
        assert len(dto.predicate_positions) == len(egi.E)
        assert len(dto.cut_bounds) == len(egi.Cut)

        # Smoke-budget assertion.
        assert elapsed < self.LATENCY_BUDGET_SECONDS, (
            f"layout of {total_elements} elements took {elapsed:.2f}s "
            f"(budget {self.LATENCY_BUDGET_SECONDS}s)"
        )

    def test_layout_above_pipe_buffer_threshold(self, engine, style):
        """Regression test for the elk_worker.js stdout-flush bug.

        Before the worker was patched to drain stdout before exit, the ELK
        subprocess silently truncated its JSON payload at the ~64 KB macOS
        pipe-buffer boundary — observed empirically as a JSONDecodeError
        around column 65528 once the EGI grew past ~240 sheet-level
        elements.  This test uses 100 sibling cuts (300 elements,
        well above the 64 KB cutoff) so the fix can't silently regress.
        """
        egi = parse_egif(_make_large_egi_text(100))  # 300 elements
        dto = engine.generate_layout(egi, style)
        assert len(dto.cut_bounds) == 100
        assert len(dto.vertex_positions) == 100
        assert len(dto.predicate_positions) == 100


# ---------------------------------------------------------------------------
# 3. Dense relation graphs
# ---------------------------------------------------------------------------


def _segments(path: Tuple[Point, ...]) -> List[Tuple[Point, Point]]:
    return [(path[i], path[i + 1]) for i in range(len(path) - 1)]


def _point_distance(a: Point, b: Point) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def _segment_direction(seg: Tuple[Point, Point]) -> Tuple[float, float]:
    p1, p2 = seg
    dx, dy = p2.x - p1.x, p2.y - p1.y
    norm = math.hypot(dx, dy)
    if norm < 1e-9:
        return (0.0, 0.0)
    return (dx / norm, dy / norm)


def _segments_collinear_and_overlapping(
    s1: Tuple[Point, Point],
    s2: Tuple[Point, Point],
    eps_dir: float = 1e-3,
    eps_perp: float = 0.5,
    min_overlap: float = 1.0,
) -> bool:
    """True iff *s1* and *s2* lie on the same line (within *eps*) AND
    their projections onto that line share an interior overlap of at
    least *min_overlap* units.

    A single shared endpoint is OK (lines that meet at one point).
    """
    d1 = _segment_direction(s1)
    d2 = _segment_direction(s2)
    if d1 == (0.0, 0.0) or d2 == (0.0, 0.0):
        return False

    # Direction alignment (parallel, either sense).
    cross = abs(d1[0] * d2[1] - d1[1] * d2[0])
    if cross > eps_dir:
        return False

    # Perpendicular distance from s2's first point to s1's line.
    p1, p2 = s1
    q1, _q2 = s2
    perp = abs((q1.x - p1.x) * d1[1] - (q1.y - p1.y) * d1[0])
    if perp > eps_perp:
        return False

    # Project all four endpoints onto s1's direction.
    def proj(pt: Point) -> float:
        return (pt.x - p1.x) * d1[0] + (pt.y - p1.y) * d1[1]

    a1, a2 = sorted([proj(s1[0]), proj(s1[1])])
    b1, b2 = sorted([proj(s2[0]), proj(s2[1])])
    overlap = min(a2, b2) - max(a1, b1)
    return overlap > min_overlap


class TestDenseRelationLigatures:
    """Multiple n-ary predicates over the same small vertex set.

    Concretely: four ternary predicates R, S, T, U over the same vertex
    triple (*x, *y, *z).  We assert that no two distinct ligature paths
    have overlapping collinear interior segments — i.e. the bundle of
    ligatures meeting at a shared vertex visually fans out rather than
    stacking on top of itself.
    """

    def test_no_overlapping_collinear_segments(self, engine, style):
        egi = parse_egif("(R *x *y *z) (S x y z) (T x y z) (U x y z)")
        dto = engine.generate_layout(egi, style)

        # 4 predicates × 3 vertices = 12 ligatures.
        assert len(dto.ligature_paths) == 12

        problems: List[str] = []
        paths = dto.ligature_paths
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                lpi, lpj = paths[i], paths[j]
                if (lpi.predicate_id, lpi.vertex_id) == (
                    lpj.predicate_id,
                    lpj.vertex_id,
                ):
                    continue
                for si in _segments(lpi.points):
                    for sj in _segments(lpj.points):
                        if _segments_collinear_and_overlapping(si, sj):
                            problems.append(
                                f"  {lpi.predicate_id}-{lpi.vertex_id}  vs  "
                                f"{lpj.predicate_id}-{lpj.vertex_id}\n"
                                f"    {si}\n    {sj}"
                            )
        assert not problems, (
            "distinct ligature paths share collinear-overlapping segments:\n"
            + "\n".join(problems)
        )
