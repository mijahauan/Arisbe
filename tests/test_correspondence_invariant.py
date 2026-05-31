"""
Linear-graphical correspondence invariant — property tests.

See docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md for the contract these tests
enforce. This file currently attacks the first five of the six test shapes
listed in §7 of the spec:

  - Totality:        every EGI element (V, E, Cut) is represented in the
                     rendered LayoutDTO.
  - Injectivity:     every LayoutDTO entry traces back to a known EGI element
                     (or to the sheet).
  - Containment:     cut bounds nest according to the EGI's `area` mapping.
  - Incidence:       LigaturePaths realise `ν` — for each predicate, the set
                     of ligature paths emitted matches the predicate's arity
                     and the multiset of vertices `ν` names.
  - Identity (1/3):  endpoint placement — each LigaturePath's vertex-side
                     endpoint coincides with the vertex's position, and each
                     endpoint lies in the bounds of its endpoint's egi.area.

Two further layers of identity fidelity remain:

  - Area-chain traversal: the path's point sequence visits only areas on
    the ancestor chain between the vertex's and the predicate's areas
    (no siblings, no detours through unrelated cuts).
  - Connectedness across shared identities: for each vertex referenced by
    multiple predicates in different areas (Beta graphs), the union of
    paths involving that vertex forms one connected geometry rooted at
    the vertex's position.

Argument-order fidelity (which hook is arg 1 vs arg 2) is deferred: the
current LigaturePath does not carry a port index, so order is a renderer-
level concern not visible at this layer.
"""

import sys
from pathlib import Path

import pytest

# Match the repo's test convention: prepend src/ so bare imports work.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elk_layout_engine import ELKLayoutEngine
from layout_dto import Point
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
    """Enumerate UoD IDs from the tomos corpus at collection time."""
    service = TomosService(TOMOS_ROOT)
    return [u["uod_id"] for u in service.list_uods()]


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_render_round_trip_totality_and_injectivity(uod_id, tomos, engine, style):
    """Every EGI element appears in the LayoutDTO and vice versa.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §3.3 (Totality, Injectivity).
    """
    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi
    dto = engine.generate_layout(egi, style)

    egi_v_ids = {v.id for v in egi.V}
    egi_e_ids = {e.id for e in egi.E}
    egi_cut_ids = {c.id for c in egi.Cut}

    # Totality: every EGI element has structural data in the DTO.
    missing_v = egi_v_ids - dto.vertex_positions.keys()
    missing_e = egi_e_ids - dto.predicate_positions.keys()
    missing_cuts = egi_cut_ids - dto.cut_bounds.keys()
    assert not missing_v, (
        f"[{uod_id}] vertices in EGI missing from LayoutDTO.vertex_positions: "
        f"{sorted(missing_v)}"
    )
    assert not missing_e, (
        f"[{uod_id}] predicates in EGI missing from LayoutDTO.predicate_positions: "
        f"{sorted(missing_e)}"
    )
    assert not missing_cuts, (
        f"[{uod_id}] cuts in EGI missing from LayoutDTO.cut_bounds: "
        f"{sorted(missing_cuts)}"
    )

    # Injectivity: every DTO entry traces back to an EGI element (or the sheet).
    extra_v = dto.vertex_positions.keys() - egi_v_ids
    extra_e = dto.predicate_positions.keys() - egi_e_ids
    extra_cuts = dto.cut_bounds.keys() - egi_cut_ids - {egi.sheet}
    assert not extra_v, (
        f"[{uod_id}] LayoutDTO.vertex_positions contains unknown IDs: "
        f"{sorted(extra_v)}"
    )
    assert not extra_e, (
        f"[{uod_id}] LayoutDTO.predicate_positions contains unknown IDs: "
        f"{sorted(extra_e)}"
    )
    assert not extra_cuts, (
        f"[{uod_id}] LayoutDTO.cut_bounds contains IDs that are neither "
        f"cuts nor the sheet: {sorted(extra_cuts)}"
    )


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_render_round_trip_containment_fidelity(uod_id, tomos, engine, style):
    """Cut bounds geometrically contain every element the EGI says lives inside.

    For each cut C, for each element X in egi.area[C]: the LayoutDTO must
    place X inside the bounds of C — a vertex/predicate position must lie
    within the bounds, a sub-cut's bounds must lie inside the parent's bounds.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §3.3 (Containment fidelity),
    §5.1 (Cut containment under regeneration), §5.5 (the structural basis
    of regime 3: objects are undefined outside their area).
    """
    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi
    dto = engine.generate_layout(egi, style)

    failures = []
    for cut in egi.Cut:
        cut_id = cut.id
        bounds = dto.cut_bounds.get(cut_id)
        if bounds is None:
            # Surfaced by the totality test; skip here to avoid duplicate noise.
            continue
        for elem_id in egi.area.get(cut_id, frozenset()):
            pos = dto.vertex_positions.get(elem_id) or dto.predicate_positions.get(elem_id)
            if pos is not None:
                inside = (
                    bounds.min_x <= pos.x <= bounds.max_x
                    and bounds.min_y <= pos.y <= bounds.max_y
                )
                if not inside:
                    failures.append(
                        f"  element {elem_id} (pos=({pos.x:.1f},{pos.y:.1f})) "
                        f"is in egi.area[{cut_id}] but lies outside cut bounds "
                        f"x∈[{bounds.min_x:.1f},{bounds.max_x:.1f}] "
                        f"y∈[{bounds.min_y:.1f},{bounds.max_y:.1f}]"
                    )
                continue
            child_bounds = dto.cut_bounds.get(elem_id)
            if child_bounds is None:
                continue
            contained = (
                bounds.min_x <= child_bounds.min_x
                and bounds.max_x >= child_bounds.max_x
                and bounds.min_y <= child_bounds.min_y
                and bounds.max_y >= child_bounds.max_y
            )
            if not contained:
                failures.append(
                    f"  sub-cut {elem_id} is in egi.area[{cut_id}] but its bounds "
                    f"x∈[{child_bounds.min_x:.1f},{child_bounds.max_x:.1f}] "
                    f"y∈[{child_bounds.min_y:.1f},{child_bounds.max_y:.1f}] "
                    f"are not fully inside parent bounds "
                    f"x∈[{bounds.min_x:.1f},{bounds.max_x:.1f}] "
                    f"y∈[{bounds.min_y:.1f},{bounds.max_y:.1f}]"
                )

    assert not failures, (
        f"[{uod_id}] containment fidelity violated:\n" + "\n".join(failures)
    )


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_render_round_trip_incidence_fidelity(uod_id, tomos, engine, style):
    """LigaturePath set matches `ν` per predicate (count + vertex multiset).

    For each predicate E in egi.E, with `ν(E) = (v_1, ..., v_n)`:

      - The number of LigaturePath entries with `predicate_id == E.id` must
        equal `n` (the arity).
      - The multiset of `vertex_id` values across those LigaturePaths must
        equal the multiset `{v_1, ..., v_n}`.  Multiset, not set: a relation
        may reference the same vertex more than once (e.g. (Eq *x x)).

    Argument *order* (which hook is arg 1 vs arg 2) is not checked here —
    LigaturePath carries no port index, so order is a renderer-internal
    detail not visible at this fidelity layer.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §3.3 (Incidence fidelity),
    §5.4 (Predicate hook order, deferred).
    """
    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi
    dto = engine.generate_layout(egi, style)

    # Index ligature paths by predicate_id once.
    paths_by_predicate: dict = {}
    for path in dto.ligature_paths:
        paths_by_predicate.setdefault(path.predicate_id, []).append(path)

    failures = []
    for edge in egi.E:
        edge_id = edge.id
        nu_vertices = egi.nu.get(edge_id)
        if nu_vertices is None:
            failures.append(
                f"  predicate {edge_id} has no entry in egi.nu — "
                f"EGI itself is malformed"
            )
            continue
        expected_arity = len(nu_vertices)
        actual_paths = paths_by_predicate.get(edge_id, [])
        actual_arity = len(actual_paths)
        if actual_arity != expected_arity:
            failures.append(
                f"  predicate {edge_id}: arity mismatch — "
                f"ν says {expected_arity} arg(s) {tuple(nu_vertices)}, "
                f"LayoutDTO emits {actual_arity} ligature path(s)"
            )
            continue
        expected_vertices = sorted(nu_vertices)
        actual_vertices = sorted(p.vertex_id for p in actual_paths)
        if expected_vertices != actual_vertices:
            failures.append(
                f"  predicate {edge_id}: vertex multiset mismatch — "
                f"ν names {expected_vertices}, "
                f"LayoutDTO connects {actual_vertices}"
            )

    # Injectivity sweep on ligature paths themselves: every path must reference
    # a predicate that exists in the EGI and a vertex it actually names.
    egi_e_ids = {e.id for e in egi.E}
    egi_v_ids = {v.id for v in egi.V}
    for path in dto.ligature_paths:
        if path.predicate_id not in egi_e_ids:
            failures.append(
                f"  ligature path references unknown predicate "
                f"{path.predicate_id} (vertex={path.vertex_id})"
            )
        if path.vertex_id not in egi_v_ids:
            failures.append(
                f"  ligature path references unknown vertex "
                f"{path.vertex_id} (predicate={path.predicate_id})"
            )

    assert not failures, (
        f"[{uod_id}] incidence fidelity violated:\n" + "\n".join(failures)
    )


def _element_area_map(egi):
    """Return {element_id: area_id} for every vertex and edge in *egi*.

    The area map is the inverse of egi.area: instead of "what's in this
    area" it answers "what area is this element in".  Cuts are skipped
    (they are areas, not contents of an area's element set in the sense
    we want here — though a cut's own area is its parent in egi.area).
    """
    cut_ids = {c.id for c in egi.Cut}
    result = {}
    for area_id, contents in egi.area.items():
        for elem_id in contents:
            if elem_id not in cut_ids:
                result[elem_id] = area_id
    return result


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_identity_fidelity_endpoint_placement(uod_id, tomos, engine, style):
    """LigaturePath endpoints sit at the right places, in the right areas.

    For every LigaturePath p = (predicate_id, vertex_id, points):

      - p.points has at least two entries.
      - p.points[-1] equals vertex_positions[vertex_id] exactly — the
        vertex-side endpoint coincides with the vertex's own position.
        (The predicate-side endpoint p.points[0] is a hook on the
        predicate's bounding box, so we do not check it for strict
        equality with the predicate's center — see the area-bounds
        check below.)
      - If the vertex's area is a cut, p.points[-1] lies within that
        cut's bounds.  If the vertex is in the sheet area, no bounds
        check applies (the sheet is unbounded).
      - If the predicate's area is a cut, p.points[0] lies within that
        cut's bounds.  Same sheet exemption.

    The vertex-end bounds check is, in effect, a chained restatement of
    the containment test (vertex position is in vertex's area); but as
    *part of the path* it asserts that the rendered ligature actually
    terminates inside the area the EGI says it lives in.  The predicate-
    end bounds check is the new content: a predicate near the edge of a
    cut should still have its hook drawn inside the same cut.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §3.3 (Identity
    fidelity), §5.2 (Ligatures across cut boundaries — Beta).
    """
    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi
    dto = engine.generate_layout(egi, style)

    elem_area = _element_area_map(egi)
    cut_ids = {c.id for c in egi.Cut}

    def _in_bounds(point, bounds):
        return (
            bounds.min_x <= point.x <= bounds.max_x
            and bounds.min_y <= point.y <= bounds.max_y
        )

    failures = []
    for path in dto.ligature_paths:
        pts = path.points
        if len(pts) < 2:
            failures.append(
                f"  ligature ({path.predicate_id} → {path.vertex_id}) has "
                f"{len(pts)} point(s); a path needs at least two"
            )
            continue

        # Vertex-side endpoint coincides with the vertex's position.
        vert_pos = dto.vertex_positions.get(path.vertex_id)
        if vert_pos is not None:
            last = pts[-1]
            if (last.x, last.y) != (vert_pos.x, vert_pos.y):
                failures.append(
                    f"  ligature ({path.predicate_id} → {path.vertex_id}): "
                    f"last point ({last.x:.2f},{last.y:.2f}) does not "
                    f"coincide with vertex position "
                    f"({vert_pos.x:.2f},{vert_pos.y:.2f})"
                )

        # Vertex endpoint inside the vertex's area (skip sheet).
        v_area = elem_area.get(path.vertex_id)
        if v_area in cut_ids:
            v_bounds = dto.cut_bounds.get(v_area)
            if v_bounds is not None and not _in_bounds(pts[-1], v_bounds):
                failures.append(
                    f"  ligature ({path.predicate_id} → {path.vertex_id}): "
                    f"vertex endpoint ({pts[-1].x:.2f},{pts[-1].y:.2f}) is "
                    f"in egi.area[{v_area}] but lies outside cut bounds "
                    f"x∈[{v_bounds.min_x:.1f},{v_bounds.max_x:.1f}] "
                    f"y∈[{v_bounds.min_y:.1f},{v_bounds.max_y:.1f}]"
                )

        # Predicate endpoint inside the predicate's area (skip sheet).
        p_area = elem_area.get(path.predicate_id)
        if p_area in cut_ids:
            p_bounds = dto.cut_bounds.get(p_area)
            if p_bounds is not None and not _in_bounds(pts[0], p_bounds):
                failures.append(
                    f"  ligature ({path.predicate_id} → {path.vertex_id}): "
                    f"predicate endpoint ({pts[0].x:.2f},{pts[0].y:.2f}) is "
                    f"in egi.area[{p_area}] but lies outside cut bounds "
                    f"x∈[{p_bounds.min_x:.1f},{p_bounds.max_x:.1f}] "
                    f"y∈[{p_bounds.min_y:.1f},{p_bounds.max_y:.1f}]"
                )

    assert not failures, (
        f"[{uod_id}] identity fidelity (endpoint placement) violated:\n"
        + "\n".join(failures)
    )


def _cut_parent_map(egi):
    """Return {cut_id: enclosing area_id} — the area-tree parent map."""
    cut_ids = {c.id for c in egi.Cut}
    parent = {}
    for area_id, contents in egi.area.items():
        for elem_id in contents:
            if elem_id in cut_ids:
                parent[elem_id] = area_id
    return parent


def _chain_between(a, b, parent_map):
    """Return the set of areas on the path from `a` to `b` in the area tree.

    The path goes a → ancestors → LCA → ... → b.  Both endpoints and
    the LCA are included.  `parent_map.get(sheet)` is None — the sheet
    is the tree's root.
    """
    anc_a = []
    cur = a
    while cur is not None:
        anc_a.append(cur)
        cur = parent_map.get(cur)
    anc_a_set = set(anc_a)
    chain_b = []
    cur = b
    while cur is not None and cur not in anc_a_set:
        chain_b.append(cur)
        cur = parent_map.get(cur)
    if cur is None:
        # Disjoint trees — shouldn't happen with a single sheet root.
        return set(chain_b) | anc_a_set
    idx = anc_a.index(cur)
    return set(chain_b) | set(anc_a[: idx + 1])


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_identity_fidelity_area_chain_traversal(uod_id, tomos, engine, style):
    """LigaturePath geometry stays on the ancestor chain between endpoints.

    For every LigaturePath p with predicate area p_area and vertex area
    v_area, let `chain` be the set of areas on the path between p_area
    and v_area in the area tree (both endpoints' areas, their LCA, and
    every area in between, inclusive).

    Every point on p.points, and every segment midpoint, must lie in an
    area that is a member of `chain`.  Equivalently: the path may visit
    p_area, v_area, their LCA, any area on the chain between them, and
    no other cut.  Sibling cuts and unrelated cuts are off-limits.

    "Lies in area X" is computed by deepest-strict-bounds containment:
    of all cuts whose bounds strictly contain the point, pick the one
    with maximal depth in the area tree.  Strict bounds (< not ≤) treat
    boundary-tangent points as outside the cut — this matters because
    ELK's detour routing intentionally runs along the outside edge of
    unauthorized cuts, and we don't want to flag those as violations.

    Segment midpoints catch the case of a straight segment passing
    *through* an unauthorized cut while both endpoints lie outside.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §3.3 (Identity
    fidelity), §5.2 (Ligatures across cut boundaries — Beta), §5.3
    (Sibling cut ordering and ligature crossings).
    """
    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi
    dto = engine.generate_layout(egi, style)

    elem_area = _element_area_map(egi)
    cut_ids = {c.id for c in egi.Cut}
    parent_map = _cut_parent_map(egi)

    def depth(cid):
        d = 0
        cur = cid
        while parent_map.get(cur) is not None:
            cur = parent_map[cur]
            d += 1
        return d

    def deepest_containing_cut(point):
        candidates = [
            cid
            for cid, b in dto.cut_bounds.items()
            if cid in cut_ids
            and b.min_x < point.x < b.max_x
            and b.min_y < point.y < b.max_y
        ]
        if not candidates:
            return egi.sheet
        return max(candidates, key=depth)

    failures = []
    for path in dto.ligature_paths:
        v_area = elem_area.get(path.vertex_id, egi.sheet)
        p_area = elem_area.get(path.predicate_id, egi.sheet)
        allowed = _chain_between(v_area, p_area, parent_map)

        pts = path.points
        # Per-point check
        for i, pt in enumerate(pts):
            area = deepest_containing_cut(pt)
            if area not in allowed:
                failures.append(
                    f"  ligature ({path.predicate_id} → {path.vertex_id}): "
                    f"point[{i}] ({pt.x:.2f},{pt.y:.2f}) lies in area "
                    f"{area}, which is off the chain between v_area={v_area} "
                    f"and p_area={p_area}; allowed: {sorted(allowed)}"
                )

        # Per-segment midpoint check (catches straight crossings of
        # unauthorized cuts where both endpoints are outside).
        for i in range(len(pts) - 1):
            mid = Point(
                (pts[i].x + pts[i + 1].x) / 2,
                (pts[i].y + pts[i + 1].y) / 2,
            )
            area = deepest_containing_cut(mid)
            if area not in allowed:
                failures.append(
                    f"  ligature ({path.predicate_id} → {path.vertex_id}): "
                    f"midpoint of segment[{i}→{i+1}] "
                    f"({mid.x:.2f},{mid.y:.2f}) lies in area {area}, off "
                    f"the chain between v_area={v_area} and p_area={p_area}; "
                    f"allowed: {sorted(allowed)}"
                )

    assert not failures, (
        f"[{uod_id}] identity fidelity (area-chain traversal) violated:\n"
        + "\n".join(failures)
    )


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_identity_fidelity_shared_identity_connectedness(uod_id, tomos, engine, style):
    """The union of paths for one vertex is connected and rooted at its pos.

    The W-partition lets one vertex v stand for many predicate references,
    possibly in different areas (this is what makes Beta graphs Beta).
    The drawing must show those references as one identity line, not as
    disconnected fragments.  Concretely, for every vertex v in egi.V:

      - Count match: the number of LigaturePaths with vertex_id == v.id
        equals the number of times v.id appears across egi.nu (i.e.,
        every W-partition reference is materialised as a path).
      - Connectedness: take the union of all such paths, treating each
        path point as a node and each consecutive (point[i], point[i+1])
        pair as an edge.  BFS from the vertex's drawn position visits
        every node in the union.  Equivalently, the multigraph is one
        connected component containing the vertex's position.

    For non-Beta vertices (single reference, single path), the assertion
    is trivially satisfied — but running it everywhere costs little and
    catches regressions if future routing splits a single ligature.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §3.3 (Identity
    fidelity — "vertices in the same partition class are joined by
    exactly one connected ligature"), §5.2 (Ligatures across cut
    boundaries — Beta).
    """
    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi
    dto = engine.generate_layout(egi, style)

    paths_by_vertex: dict = {}
    for p in dto.ligature_paths:
        paths_by_vertex.setdefault(p.vertex_id, []).append(p)

    # Expected reference count per vertex, from ν.
    expected_count: dict = {}
    for nu_seq in egi.nu.values():
        for vid in nu_seq:
            expected_count[vid] = expected_count.get(vid, 0) + 1

    failures = []
    for vertex in egi.V:
        vid = vertex.id
        paths = paths_by_vertex.get(vid, [])
        expected = expected_count.get(vid, 0)
        actual = len(paths)
        if actual != expected:
            failures.append(
                f"  vertex {vid}: ν references it {expected} time(s) but "
                f"LayoutDTO emits {actual} ligature path(s) ending there"
            )
            continue
        if not paths:
            continue

        v_pos = dto.vertex_positions.get(vid)
        if v_pos is None:
            # Totality test surfaces this — skip to avoid duplicate noise.
            continue

        # Build the multigraph: nodes = path points (keyed by (x, y)),
        # edges = consecutive point pairs.
        adj: dict = {}
        nodes: set = set()
        for p in paths:
            pts = p.points
            for pt in pts:
                nodes.add((pt.x, pt.y))
            for i in range(len(pts) - 1):
                a = (pts[i].x, pts[i].y)
                b = (pts[i + 1].x, pts[i + 1].y)
                if a == b:
                    continue
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)

        # BFS from the vertex's drawn position.
        start = (v_pos.x, v_pos.y)
        if start not in nodes:
            failures.append(
                f"  vertex {vid}: vertex position ({v_pos.x:.2f},"
                f"{v_pos.y:.2f}) is not a node of the path union — the "
                f"identity line is not rooted at the vertex"
            )
            continue
        visited = {start}
        stack = [start]
        while stack:
            n = stack.pop()
            for m in adj.get(n, ()):
                if m not in visited:
                    visited.add(m)
                    stack.append(m)

        unreachable = nodes - visited
        if unreachable:
            failures.append(
                f"  vertex {vid}: union of {len(paths)} ligature path(s) "
                f"is not connected from vertex pos ({v_pos.x:.2f},"
                f"{v_pos.y:.2f}); unreachable points: "
                f"{sorted(unreachable)[:3]}{'...' if len(unreachable) > 3 else ''}"
            )

    assert not failures, (
        f"[{uod_id}] identity fidelity (shared-identity connectedness) "
        f"violated:\n" + "\n".join(failures)
    )
