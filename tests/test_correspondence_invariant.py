"""
Linear-graphical correspondence invariant — property tests.

See docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md for the contract these tests
enforce. This file attacks all six of the test shapes listed in §7 of
the spec:

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
  - Identity (2/3):  area-chain traversal — every path point and segment
                     midpoint lies on the ancestor chain between the
                     vertex's and the predicate's areas.
  - Identity (3/3):  shared-identity connectedness — for each vertex,
                     the count of paths matches ν references and the
                     union of paths forms one connected component
                     rooted at the vertex's position.
  - Argument order:  the LigaturePath.port_index field realises ν's
                     argument ordering — sorting a predicate's paths by
                     port_index reproduces ν exactly.
  - Transformation invariance: every rule application (DC+, ERA, IT+)
                     preserves correspondence on the post-EGI's drawing.
  - Regime-3 non-interference: every projection-only mutation (vertex
                     translation, interior-preserving cut reshape,
                     on-chain ligature reroute) leaves the EGI
                     structurally untouched and keeps the mutated
                     drawing in correspondence.
"""

import sys
from pathlib import Path

import pytest

# Match the repo's test convention: prepend src/ so bare imports work.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

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


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_incidence_fidelity_argument_order(uod_id, tomos, engine, style):
    """LigaturePath.port_index realises ν's argument ordering.

    For every predicate E in egi.E with ν(E) = (v_1, v_2, ..., v_n):

      - The LigaturePaths with predicate_id == E.id, sorted by
        port_index ascending, yield exactly the vertex sequence
        (v_1, v_2, ..., v_n).
      - port_index values for E's paths are exactly {0, 1, ..., n-1}.

    A repeated vertex in ν (e.g. (Eq *x x)) produces two paths with the
    same vertex_id but distinct port_index values — the test enforces
    that distinction.

    Together with the incidence fidelity test (multiset match), this
    closes off §3.3 "Incidence fidelity" — the drawing's hooks realise
    ν not just as a bag but as an ordered tuple.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §3.3 (Incidence
    fidelity — "argument order is visually distinguishable and matches
    ν"), §5.4 (Predicate hook order).
    """
    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi
    dto = engine.generate_layout(egi, style)

    paths_by_predicate: dict = {}
    for p in dto.ligature_paths:
        paths_by_predicate.setdefault(p.predicate_id, []).append(p)

    failures = []
    for edge in egi.E:
        edge_id = edge.id
        nu_seq = egi.nu.get(edge_id)
        if nu_seq is None:
            continue  # surfaced by the incidence test
        paths = paths_by_predicate.get(edge_id, [])
        if len(paths) != len(nu_seq):
            continue  # surfaced by the incidence test

        port_values = sorted(p.port_index for p in paths)
        expected_ports = list(range(len(nu_seq)))
        if port_values != expected_ports:
            failures.append(
                f"  predicate {edge_id}: port_index values are "
                f"{port_values}; expected {expected_ports}"
            )
            continue

        ordered_vertices = tuple(
            p.vertex_id for p in sorted(paths, key=lambda x: x.port_index)
        )
        expected = tuple(nu_seq)
        if ordered_vertices != expected:
            failures.append(
                f"  predicate {edge_id}: paths sorted by port_index give "
                f"vertex sequence {ordered_vertices}; ν says {expected}"
            )

    assert not failures, (
        f"[{uod_id}] argument-order fidelity violated:\n"
        + "\n".join(failures)
    )


# --------------------------------------------------------------------------- #
# Transformation invariance — §7 test shape #2                                #
# --------------------------------------------------------------------------- #
#
# For each Dau rule applied to each tomos UoD at a deterministic site, we
# render the post-state and re-run every correspondence check.  This catches
# rule-induced drift: a rule that produces a structurally valid EGI whose
# rendered drawing nevertheless fails the invariant.
#
# Site picking is per-rule and intentionally simple — one site per UoD per
# rule, chosen by a deterministic rule.  Exhaustive site enumeration is left
# to a Hypothesis-driven companion suite (out of scope here).
#
# The check helper below bundles every property test's logic into one pass.
# We deliberately do not refactor the per-property tests to use it: those
# tests give focused error messages per property on the original corpus,
# and that locality is worth keeping.  The helper exists for post-state
# checks where "the drawing matches the EGI" is the single question.


def _check_correspondence(label, egi, dto):
    """Run every §3.3 check on (egi, dto). Returns list of failure messages."""
    failures = []
    egi_v_ids = {v.id for v in egi.V}
    egi_e_ids = {e.id for e in egi.E}
    egi_cut_ids = {c.id for c in egi.Cut}

    # Totality
    for kind, want, have in (
        ("vertex", egi_v_ids, dto.vertex_positions.keys()),
        ("predicate", egi_e_ids, dto.predicate_positions.keys()),
        ("cut", egi_cut_ids, dto.cut_bounds.keys()),
    ):
        missing = want - have
        if missing:
            failures.append(
                f"  totality: {kind}(s) missing from DTO: {sorted(missing)}"
            )

    # Injectivity
    extra_v = dto.vertex_positions.keys() - egi_v_ids
    extra_e = dto.predicate_positions.keys() - egi_e_ids
    extra_cuts = dto.cut_bounds.keys() - egi_cut_ids - {egi.sheet}
    if extra_v:
        failures.append(f"  injectivity: stray vertex IDs in DTO: {sorted(extra_v)}")
    if extra_e:
        failures.append(f"  injectivity: stray predicate IDs in DTO: {sorted(extra_e)}")
    if extra_cuts:
        failures.append(f"  injectivity: stray cut IDs in DTO: {sorted(extra_cuts)}")

    # Containment
    for cut in egi.Cut:
        bounds = dto.cut_bounds.get(cut.id)
        if bounds is None:
            continue
        for elem_id in egi.area.get(cut.id, frozenset()):
            pos = dto.vertex_positions.get(elem_id) or dto.predicate_positions.get(
                elem_id
            )
            if pos is not None:
                if not (
                    bounds.min_x <= pos.x <= bounds.max_x
                    and bounds.min_y <= pos.y <= bounds.max_y
                ):
                    failures.append(
                        f"  containment: {elem_id} in egi.area[{cut.id}] "
                        f"at ({pos.x:.1f},{pos.y:.1f}) outside cut bounds"
                    )
                continue
            child = dto.cut_bounds.get(elem_id)
            if child is None:
                continue
            if not (
                bounds.min_x <= child.min_x
                and bounds.max_x >= child.max_x
                and bounds.min_y <= child.min_y
                and bounds.max_y >= child.max_y
            ):
                failures.append(
                    f"  containment: sub-cut {elem_id} in egi.area[{cut.id}] "
                    f"is not fully inside parent bounds"
                )

    # Incidence — count + multiset
    paths_by_pred: dict = {}
    for p in dto.ligature_paths:
        paths_by_pred.setdefault(p.predicate_id, []).append(p)
    for edge in egi.E:
        nu_seq = egi.nu.get(edge.id)
        if nu_seq is None:
            failures.append(f"  incidence: predicate {edge.id} has no entry in ν")
            continue
        paths = paths_by_pred.get(edge.id, [])
        if len(paths) != len(nu_seq):
            failures.append(
                f"  incidence: predicate {edge.id} arity mismatch — "
                f"ν says {len(nu_seq)}, DTO has {len(paths)}"
            )
            continue
        if sorted(p.vertex_id for p in paths) != sorted(nu_seq):
            failures.append(
                f"  incidence: predicate {edge.id} vertex multiset mismatch — "
                f"ν names {sorted(nu_seq)}, DTO connects "
                f"{sorted(p.vertex_id for p in paths)}"
            )

    # Identity 1/3: endpoint placement
    elem_area = _element_area_map(egi)
    cut_ids = {c.id for c in egi.Cut}
    for path in dto.ligature_paths:
        pts = path.points
        if len(pts) < 2:
            failures.append(
                f"  identity-endpoint: ({path.predicate_id} → {path.vertex_id}) "
                f"has only {len(pts)} point(s)"
            )
            continue
        vpos = dto.vertex_positions.get(path.vertex_id)
        if vpos is not None and (pts[-1].x, pts[-1].y) != (vpos.x, vpos.y):
            failures.append(
                f"  identity-endpoint: ({path.predicate_id} → {path.vertex_id}) "
                f"last point {pts[-1]} ≠ vertex position {vpos}"
            )
        for end_idx, eid, label_str in (
            (-1, path.vertex_id, "vertex"),
            (0, path.predicate_id, "predicate"),
        ):
            area = elem_area.get(eid)
            if area in cut_ids:
                bounds = dto.cut_bounds.get(area)
                pt = pts[end_idx]
                if bounds is not None and not (
                    bounds.min_x <= pt.x <= bounds.max_x
                    and bounds.min_y <= pt.y <= bounds.max_y
                ):
                    failures.append(
                        f"  identity-endpoint: ({path.predicate_id} → "
                        f"{path.vertex_id}) {label_str} endpoint outside "
                        f"egi.area[{area}] cut bounds"
                    )

    # Identity 2/3: area-chain traversal
    parent_map = _cut_parent_map(egi)

    def _depth(cid):
        d = 0
        cur = cid
        while parent_map.get(cur) is not None:
            cur = parent_map[cur]
            d += 1
        return d

    def _deepest(point):
        cands = [
            cid
            for cid, b in dto.cut_bounds.items()
            if cid in cut_ids
            and b.min_x < point.x < b.max_x
            and b.min_y < point.y < b.max_y
        ]
        if not cands:
            return egi.sheet
        return max(cands, key=_depth)

    for path in dto.ligature_paths:
        v_area = elem_area.get(path.vertex_id, egi.sheet)
        p_area = elem_area.get(path.predicate_id, egi.sheet)
        allowed = _chain_between(v_area, p_area, parent_map)
        for i, pt in enumerate(path.points):
            area = _deepest(pt)
            if area not in allowed:
                failures.append(
                    f"  identity-chain: ({path.predicate_id} → {path.vertex_id}) "
                    f"point[{i}] in area {area} off chain {sorted(allowed)}"
                )
        for i in range(len(path.points) - 1):
            mid = Point(
                (path.points[i].x + path.points[i + 1].x) / 2,
                (path.points[i].y + path.points[i + 1].y) / 2,
            )
            area = _deepest(mid)
            if area not in allowed:
                failures.append(
                    f"  identity-chain: ({path.predicate_id} → {path.vertex_id}) "
                    f"midpoint[{i}→{i+1}] in area {area} off chain "
                    f"{sorted(allowed)}"
                )

    # Identity 3/3: shared-identity connectedness
    paths_by_vertex: dict = {}
    for p in dto.ligature_paths:
        paths_by_vertex.setdefault(p.vertex_id, []).append(p)
    expected_count: dict = {}
    for nu_seq in egi.nu.values():
        for vid in nu_seq:
            expected_count[vid] = expected_count.get(vid, 0) + 1
    for vertex in egi.V:
        vid = vertex.id
        paths = paths_by_vertex.get(vid, [])
        if len(paths) != expected_count.get(vid, 0):
            # Already reported by incidence — skip
            continue
        if not paths:
            continue
        vpos = dto.vertex_positions.get(vid)
        if vpos is None:
            continue
        adj: dict = {}
        nodes: set = set()
        for p in paths:
            for pt in p.points:
                nodes.add((pt.x, pt.y))
            for i in range(len(p.points) - 1):
                a = (p.points[i].x, p.points[i].y)
                b = (p.points[i + 1].x, p.points[i + 1].y)
                if a == b:
                    continue
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)
        start = (vpos.x, vpos.y)
        if start not in nodes:
            failures.append(
                f"  identity-connected: vertex {vid} pos not in path union"
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
        if nodes - visited:
            failures.append(
                f"  identity-connected: vertex {vid} has disconnected paths "
                f"({len(nodes - visited)} unreachable points)"
            )

    # Argument order
    for edge in egi.E:
        nu_seq = egi.nu.get(edge.id)
        if nu_seq is None:
            continue
        paths = paths_by_pred.get(edge.id, [])
        if len(paths) != len(nu_seq):
            continue
        ports = sorted(p.port_index for p in paths)
        if ports != list(range(len(nu_seq))):
            failures.append(
                f"  arg-order: predicate {edge.id} port indices {ports} "
                f"≠ {list(range(len(nu_seq)))}"
            )
            continue
        ordered = tuple(
            p.vertex_id for p in sorted(paths, key=lambda x: x.port_index)
        )
        if ordered != tuple(nu_seq):
            failures.append(
                f"  arg-order: predicate {edge.id} sorted vertex sequence "
                f"{ordered} ≠ ν {tuple(nu_seq)}"
            )

    return failures


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_transformation_invariance_dc_plus(uod_id, tomos, engine, style):
    """DC+ applied at the sheet preserves the correspondence invariant.

    DC+ (Double Cut Insertion) has no polarity restriction and is always
    applicable with an empty selection — it just adds two empty nested
    cuts in the target area.  We pick the sheet as the target area for
    every UoD; this gives a deterministic post-state per UoD that adds
    exactly two cuts to the existing structure.

    The post-state is then rendered and every correspondence check from
    §3.3 is run via _check_correspondence.  Any failure means the rule's
    EGI output is structurally valid (the rule itself succeeded) but
    its rendered drawing has drifted out of correspondence — exactly the
    kind of bug §7 shape #2 is meant to catch.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §4.2 (Asserted regime
    — invariant must hold after every transformation rule), §7 (test
    shape #2 — transformation invariance).
    """
    from formal_transformation_rules import FormalTransformationEngine

    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi

    t_engine = FormalTransformationEngine()
    result = t_engine.apply_rule("DC+", egi, egi.sheet, frozenset())
    assert result.success, f"DC+ at sheet failed for {uod_id}: {result.error_message}"

    post_egi = result.result_egi
    post_dto = engine.generate_layout(post_egi, style)

    failures = _check_correspondence(f"{uod_id}+DC+", post_egi, post_dto)
    assert not failures, (
        f"[{uod_id}] post-DC+ drawing fails correspondence:\n"
        + "\n".join(failures)
    )


def _pick_era_site(egi):
    """Return (area_id, selection) for a deterministic ERA application, or None.

    ERA needs a positive-polarity area with a non-empty direct selection
    whose closure is closed.  We pick the first edge (in stable ID
    order) that lives in a positive area, and offer it as a singleton
    selection — ERA's closure expansion handles semi-free vertices.

    Returns None if no UoD edge sits in a positive area.
    """
    cut_ids = {c.id for c in egi.Cut}
    elem_area = _element_area_map(egi)
    for edge in sorted(egi.E, key=lambda e: e.id):
        area = elem_area.get(edge.id)
        if area is None:
            continue
        polarity, _ = egi.area_polarity(area)
        from egi_core_dau import AreaPolarity

        if polarity is AreaPolarity.POSITIVE:
            return area, frozenset([edge.id])
    return None


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_transformation_invariance_era(uod_id, tomos, engine, style):
    """ERA at the first positive-area edge preserves correspondence.

    Pick the lowest-ID edge in a positive area (or skip if none exists)
    and erase it; the closure validator will pull in semi-free vertices
    automatically.  Render the post-state and check every §3.3 property.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §4.2 (the invariant
    must hold after every rule application), §7 (test shape #2 —
    transformation invariance).
    """
    from formal_transformation_rules import FormalTransformationEngine

    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi

    site = _pick_era_site(egi)
    if site is None:
        pytest.skip(f"{uod_id} has no edge in a positive area")
    target_area, selection = site

    t_engine = FormalTransformationEngine()
    result = t_engine.apply_rule("ERA", egi, target_area, selection)
    if not result.success:
        pytest.skip(
            f"ERA rejected for {uod_id} at {target_area}: {result.error_message}"
        )

    post_egi = result.result_egi
    post_dto = engine.generate_layout(post_egi, style)

    failures = _check_correspondence(f"{uod_id}+ERA", post_egi, post_dto)
    assert not failures, (
        f"[{uod_id}] post-ERA drawing fails correspondence:\n"
        + "\n".join(failures)
    )


def _pick_it_plus_site(egi):
    """Return (source_area, target_area, selection) for an IT+ application, or None.

    IT+ copies a subgraph from a source area into a strictly-enclosed
    target area.  We pick the lowest-ID edge as the selection; its area
    becomes the source.  The target is the lowest-ID cut whose ancestry
    chain includes the source (i.e., a descendant of source, source !=
    target), so a true into-cut iteration happens.

    Returns None if no edge has a strictly-deeper cut to iterate into.
    """
    elem_area = _element_area_map(egi)
    parent_map = _cut_parent_map(egi)

    def is_descendant(candidate, ancestor):
        cur = candidate
        while cur is not None:
            cur = parent_map.get(cur)
            if cur == ancestor:
                return True
        return False

    for edge in sorted(egi.E, key=lambda e: e.id):
        src = elem_area.get(edge.id)
        if src is None:
            continue
        for cut in sorted(egi.Cut, key=lambda c: c.id):
            if is_descendant(cut.id, src):
                return src, cut.id, frozenset([edge.id])
    return None


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_transformation_invariance_iteration(uod_id, tomos, engine, style):
    """IT+ copying a sheet-level edge into a descendant cut preserves correspondence.

    IT+ deep-copies a selected subgraph (vertices, edges, cuts and their
    interiors) into a strictly-enclosed target area.  The new edges in
    the deeper area introduce fresh ligature geometry that crosses no
    cut boundaries (the copies are self-contained), but the post-state
    has one more predicate and possibly one more vertex than the
    pre-state.  Layout must place them correctly inside the target cut.

    Skip UoDs with no edge that has a strictly-deeper cut available.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §4.2, §7 (test shape
    #2 — transformation invariance), §5.2 (Beta-style ligatures —
    iteration is one of the rules that creates them in regime 2).
    """
    from formal_transformation_rules import FormalTransformationEngine

    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi

    site = _pick_it_plus_site(egi)
    if site is None:
        pytest.skip(f"{uod_id} has no edge with a strictly-deeper cut to iterate into")
    src, tgt, selection = site

    t_engine = FormalTransformationEngine()
    result = t_engine.apply_rule("IT+", egi, tgt, selection)
    if not result.success:
        pytest.skip(
            f"IT+ rejected for {uod_id} ({src} → {tgt}): {result.error_message}"
        )

    post_egi = result.result_egi
    post_dto = engine.generate_layout(post_egi, style)

    failures = _check_correspondence(f"{uod_id}+IT+", post_egi, post_dto)
    assert not failures, (
        f"[{uod_id}] post-IT+ drawing fails correspondence:\n"
        + "\n".join(failures)
    )


# --------------------------------------------------------------------------- #
# Regime-3 non-interference — §7 test shape #6                                #
# --------------------------------------------------------------------------- #
#
# §4.3 / §5.5 of the spec scope regime 3 as the projection-only free
# dimension: a user may reposition a vertex, reshape a cut, or reroute a
# ligature — operations that touch the drawing alone — and the EGI must
# remain structurally identical.  §5.5 names this "preserved by
# construction": a *legitimate* regime-3 op is one whose effect on the
# `(EGI, projection)` pair is provably restricted to the projection
# component.
#
# These tests synthesise regime-3 mutations directly on the LayoutDTO and
# assert two things for each:
#
#   1. EGI structural equality — the snapshot of (V, E, Cut, ν, area, ρ)
#      taken before the mutation equals the snapshot taken after.  This
#      is the load-bearing assertion.
#   2. The mutated drawing still satisfies §3.3 correspondence.  This is
#      the "preserved by construction" half: a mutation that *could* be
#      called regime-3 in shape but breaks the area mapping or the
#      W-realisation by side-effect is, in the spec's terms, not regime
#      3 at all.  Reusing `_check_correspondence` makes this explicit.
#
# The mutations are hand-engineered to respect their regime-3 constraint
# (stays in same area; interior-preserving; on-chain).  If a future
# refactor causes a LayoutDTO field to alias EGI state, or causes the
# correspondence check to fail post-mutation, these tests will catch it.


def _structurally_equal_egi(pre, post):
    """Compare two EGIs on (V, E, Cut, ν, area, ρ).  Returns (ok, diffs)."""
    diffs = []
    if {v.id for v in pre.V} != {v.id for v in post.V}:
        diffs.append(
            f"V differs: {sorted({v.id for v in pre.V})} ≠ "
            f"{sorted({v.id for v in post.V})}"
        )
    if {e.id for e in pre.E} != {e.id for e in post.E}:
        diffs.append(
            f"E differs: {sorted({e.id for e in pre.E})} ≠ "
            f"{sorted({e.id for e in post.E})}"
        )
    if {c.id for c in pre.Cut} != {c.id for c in post.Cut}:
        diffs.append(
            f"Cut differs: {sorted({c.id for c in pre.Cut})} ≠ "
            f"{sorted({c.id for c in post.Cut})}"
        )
    pre_nu = {k: tuple(v) for k, v in pre.nu.items()}
    post_nu = {k: tuple(v) for k, v in post.nu.items()}
    if pre_nu != post_nu:
        diffs.append(f"ν differs: {pre_nu} ≠ {post_nu}")
    pre_area = {k: frozenset(v) for k, v in pre.area.items()}
    post_area = {k: frozenset(v) for k, v in post.area.items()}
    if pre_area != post_area:
        diffs.append(f"area differs: {pre_area} ≠ {post_area}")
    pre_rel = dict(pre.rel)
    post_rel = dict(post.rel)
    if pre_rel != post_rel:
        diffs.append(f"ρ differs: {pre_rel} ≠ {post_rel}")
    if pre.sheet != post.sheet:
        diffs.append(f"sheet differs: {pre.sheet} ≠ {post.sheet}")
    return (not diffs), diffs


def _clone_dto(
    dto,
    vertex_positions=None,
    predicate_positions=None,
    cut_bounds=None,
    ligature_paths=None,
):
    """Return a new LayoutDTO with the given fields replaced.  Unspecified
    fields are shallow-copied so the original DTO is left untouched.
    """
    return LayoutDTO(
        vertex_positions=(
            vertex_positions
            if vertex_positions is not None
            else dict(dto.vertex_positions)
        ),
        predicate_positions=(
            predicate_positions
            if predicate_positions is not None
            else dict(dto.predicate_positions)
        ),
        cut_bounds=(
            cut_bounds if cut_bounds is not None else dict(dto.cut_bounds)
        ),
        ligature_paths=(
            ligature_paths
            if ligature_paths is not None
            else list(dto.ligature_paths)
        ),
        area_hierarchy={k: set(v) for k, v in dto.area_hierarchy.items()},
        viewport_bounds=dto.viewport_bounds,
        sheet_id=dto.sheet_id,
        style=dto.style,
    )


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_regime3_identity_null_op(uod_id, tomos, engine, style):
    """The structural-equality helper agrees on an EGI re-rendered untouched.

    The null op: snapshot the EGI, render a layout, render *again* with
    no mutation in between, assert the EGI is structurally identical to
    its snapshot.  This is trivially true (EGIs are immutable; rendering
    is read-only) but it pins down the helper's behaviour and gives the
    other three sub-tests a known-good baseline.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §4.3 (Presentation-only
    — invariant preserved by construction), §7 (test shape #6).
    """
    uod = tomos.load_uod(uod_id)
    egi_before = uod.current_egi
    _ = engine.generate_layout(egi_before, style)
    _ = engine.generate_layout(egi_before, style)
    egi_after = uod.current_egi

    ok, diffs = _structurally_equal_egi(egi_before, egi_after)
    assert ok, f"[{uod_id}] null-op rendered changed EGI:\n  " + "\n  ".join(diffs)


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_regime3_vertex_translation(uod_id, tomos, engine, style):
    """Shifting vertex positions (regime-3) leaves the EGI structurally equal.

    For each vertex with margin on all sides of its containing area, shift
    its position by a small offset that stays inside the area.  Update the
    corresponding LigaturePath endpoints so the identity-endpoint property
    is preserved.  Then:

      - assert the EGI snapshot taken before the mutation is structurally
        equal to the EGI snapshot taken after (the regime-3 contract);
      - assert the mutated DTO still satisfies every §3.3 property
        (preserved by construction).

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §4.3, §5.5 (the
    structural impossibility of regime-3 abuse — a vertex shift that
    would push the vertex outside its area is *not* a regime-3 op and
    must be refused; here we only synthesise shifts that respect the
    area boundary), §7 (test shape #6).
    """
    uod = tomos.load_uod(uod_id)
    egi_before = uod.current_egi
    dto = engine.generate_layout(egi_before, style)

    elem_area = _element_area_map(egi_before)
    cut_ids = {c.id for c in egi_before.Cut}
    delta = 0.5  # ELK uses pixel-scale layouts; sub-pixel shift is always safe

    # Pick the shift per vertex so it stays inside its area.  A vertex
    # whose area is the sheet has no bound to respect; a vertex in a cut
    # must keep `pos + delta` strictly inside the cut bounds.
    new_positions: dict = {}
    shifted_vertices: set = set()
    for vid, pos in dto.vertex_positions.items():
        area = elem_area.get(vid)
        if area in cut_ids:
            bounds = dto.cut_bounds.get(area)
            if bounds is None:
                continue
            # Need delta margin on the +x and +y sides; otherwise skip.
            if pos.x + delta >= bounds.max_x or pos.y + delta >= bounds.max_y:
                continue
        new_positions[vid] = Point(pos.x + delta, pos.y + delta)
        shifted_vertices.add(vid)

    if not shifted_vertices:
        pytest.skip(f"{uod_id} has no vertex with margin to translate")

    # Update ligature endpoints whose vertex moved (vertex-side endpoint
    # is the last point; its coords must match the new vertex position).
    new_paths = []
    for path in dto.ligature_paths:
        if path.vertex_id not in shifted_vertices:
            new_paths.append(path)
            continue
        new_last = new_positions[path.vertex_id]
        pts = list(path.points)
        pts[-1] = new_last
        new_paths.append(
            LigaturePath(
                predicate_id=path.predicate_id,
                vertex_id=path.vertex_id,
                points=tuple(pts),
                port_index=path.port_index,
            )
        )

    merged_positions = dict(dto.vertex_positions)
    merged_positions.update(new_positions)
    mutated = _clone_dto(
        dto, vertex_positions=merged_positions, ligature_paths=new_paths
    )

    egi_after = uod.current_egi
    ok, diffs = _structurally_equal_egi(egi_before, egi_after)
    assert ok, (
        f"[{uod_id}] vertex-translation regime-3 op changed EGI:\n  "
        + "\n  ".join(diffs)
    )

    failures = _check_correspondence(
        f"{uod_id}+regime3-vertex-shift", egi_before, mutated
    )
    assert not failures, (
        f"[{uod_id}] post-translation drawing fails correspondence "
        f"(presented {len(shifted_vertices)} shifted vertices):\n"
        + "\n".join(failures)
    )


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_regime3_cut_reshape_interior_preserving(uod_id, tomos, engine, style):
    """Expanding cut bounds outward (regime-3) leaves the EGI structurally equal.

    For each cut C in the EGI, grow its bounds by a small padding on all
    four sides.  Two regime-3 constraints must hold for the expansion to
    qualify as presentation-only:

      1. **Interior-preserving outward**: every element the EGI says is
         in `area[C]` must still lie inside the new bounds.  Because the
         expansion only grows bounds outward, this is trivially true and
         we assert it for clarity.
      2. **Interior-preserving inward**: no element from outside `area[C]`
         is pulled inside the new bounds.  This is the load-bearing part
         of §5.5 ("a cut's redrawn boundary cannot move elements into or
         out of its area").  If the expansion would absorb a sibling
         element, we skip that cut — that wider expansion is *not* a
         regime-3 op.

    If at least one cut can be expanded under the above constraints,
    apply all such expansions, then assert:

      - the EGI is structurally unchanged;
      - the mutated DTO still satisfies every §3.3 property — in
        particular, containment fidelity, since the cut bounds are now
        wider but their `area`-content is unchanged.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §4.3, §5.5
    ("structural impossibility of regime-3 abuse" — cut reshape), §7.
    """
    uod = tomos.load_uod(uod_id)
    egi_before = uod.current_egi
    dto = engine.generate_layout(egi_before, style)

    cut_ids = {c.id for c in egi_before.Cut}
    elem_area = _element_area_map(egi_before)
    pad = 0.5  # sub-pixel expansion: small enough to almost never absorb a sibling

    # Build a position lookup for every vertex and predicate so we can
    # test the inward-preservation constraint for each candidate expansion.
    pos_map: dict = {}
    pos_map.update({vid: p for vid, p in dto.vertex_positions.items()})
    pos_map.update({eid: p for eid, p in dto.predicate_positions.items()})

    new_bounds_updates: dict = {}
    reshaped: list = []
    for cid in cut_ids:
        bounds = dto.cut_bounds.get(cid)
        if bounds is None:
            continue
        expanded = BoundingBox(
            min_x=bounds.min_x - pad,
            min_y=bounds.min_y - pad,
            max_x=bounds.max_x + pad,
            max_y=bounds.max_y + pad,
        )
        own_area_members = egi_before.area.get(cid, frozenset())
        # Inward-preservation check: scan every element not in area[cid]
        # and reject if its drawn position would fall inside the expanded
        # box.  Cuts themselves are checked by bounds overlap, not point
        # containment (a child cut already lives inside us; a sibling
        # cut's bounds must not enter ours).
        violation = False
        for elem_id, elem_pos in pos_map.items():
            if elem_id in own_area_members:
                continue
            # Skip elements already inside `cid` via deeper nesting; those
            # are not "outside" elements being absorbed.  We detect this
            # by checking whether the original bounds already contain
            # them — if so, they were already ours by nesting.
            if (
                bounds.min_x <= elem_pos.x <= bounds.max_x
                and bounds.min_y <= elem_pos.y <= bounds.max_y
            ):
                continue
            if (
                expanded.min_x <= elem_pos.x <= expanded.max_x
                and expanded.min_y <= elem_pos.y <= expanded.max_y
            ):
                violation = True
                break
        if violation:
            continue
        new_bounds_updates[cid] = expanded
        reshaped.append(cid)

    if not reshaped:
        pytest.skip(
            f"{uod_id} has no cut whose bounds can be padded without "
            f"absorbing a non-area element"
        )

    merged_bounds = dict(dto.cut_bounds)
    merged_bounds.update(new_bounds_updates)
    mutated = _clone_dto(dto, cut_bounds=merged_bounds)

    egi_after = uod.current_egi
    ok, diffs = _structurally_equal_egi(egi_before, egi_after)
    assert ok, (
        f"[{uod_id}] cut-reshape regime-3 op changed EGI:\n  "
        + "\n  ".join(diffs)
    )

    failures = _check_correspondence(
        f"{uod_id}+regime3-cut-reshape", egi_before, mutated
    )
    assert not failures, (
        f"[{uod_id}] post-reshape drawing fails correspondence "
        f"(expanded {len(reshaped)} cut(s)):\n" + "\n".join(failures)
    )


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_regime3_ligature_reroute_on_chain(uod_id, tomos, engine, style):
    """Perturbing interior waypoints (regime-3) leaves the EGI structurally equal.

    A ligature reroute is regime-3 only if the perturbation does not
    change which areas the path visits — i.e., the path stays on the
    ancestor chain between predicate-area and vertex-area.  Endpoints
    must not move (those are pinned by the predicate hook and the vertex
    position; moving them would be a different operation entirely).

    For each ligature, build a candidate perturbation: nudge the middle
    waypoint diagonally if the path already has ≥ 3 points, otherwise
    insert a perpendicular kink at the midpoint of the straight 2-point
    segment.  (ELK currently emits straight 2-point paths for most
    tomos UoDs; without the kink fallback the test would skip 100% of
    the corpus.)  Accept the perturbation only if the new interior
    point and the midpoints of its two adjacent segments still lie on
    the area chain — the same deepest-containing-cut logic the
    area-chain traversal test uses.  Apply all accepted perturbations
    together and assert:

      - the EGI is structurally unchanged;
      - the mutated DTO still satisfies every §3.3 property.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §4.3, §5.5 (ligature
    reroute — "cannot change which areas the path visits"), §7.
    """
    uod = tomos.load_uod(uod_id)
    egi_before = uod.current_egi
    dto = engine.generate_layout(egi_before, style)

    elem_area = _element_area_map(egi_before)
    cut_ids = {c.id for c in egi_before.Cut}
    parent_map = _cut_parent_map(egi_before)

    def depth(cid):
        d = 0
        cur = cid
        while parent_map.get(cur) is not None:
            cur = parent_map[cur]
            d += 1
        return d

    def deepest_containing_cut(point):
        cands = [
            cid
            for cid, b in dto.cut_bounds.items()
            if cid in cut_ids
            and b.min_x < point.x < b.max_x
            and b.min_y < point.y < b.max_y
        ]
        if not cands:
            return egi_before.sheet
        return max(cands, key=depth)

    delta = 0.25  # sub-pixel waypoint perturbation; small enough to stay in-area
    rerouted = 0
    new_paths = []
    for path in dto.ligature_paths:
        pts = list(path.points)
        if len(pts) < 2:
            new_paths.append(path)
            continue

        v_area = elem_area.get(path.vertex_id, egi_before.sheet)
        p_area = elem_area.get(path.predicate_id, egi_before.sheet)
        allowed = _chain_between(v_area, p_area, parent_map)

        # Pick a candidate perturbation depending on how many points the
        # path has.  Both shapes are regime-3 as long as the resulting
        # interior point and its adjacent segment midpoints stay on the
        # area chain — i.e., the path visits exactly the same area set
        # before and after.
        if len(pts) >= 3:
            # Nudge the middle waypoint diagonally.
            mid_idx = len(pts) // 2
            if mid_idx in (0, len(pts) - 1):
                new_paths.append(path)
                continue
            candidate = Point(pts[mid_idx].x + delta, pts[mid_idx].y + delta)
            new_pts = pts[:]
            new_pts[mid_idx] = candidate
        else:
            # Insert a perpendicular kink at the midpoint of the
            # straight 2-point segment.  This is still a regime-3 op:
            # the path is the same set of areas, just drawn with a
            # tiny bend instead of a straight line.
            a, b = pts[0], pts[1]
            mx = (a.x + b.x) / 2
            my = (a.y + b.y) / 2
            dx = b.x - a.x
            dy = b.y - a.y
            length = (dx * dx + dy * dy) ** 0.5
            if length == 0:
                # Degenerate path (endpoints coincident); leave it.
                new_paths.append(path)
                continue
            # Unit perpendicular (rotated +90°): (-dy, dx) / length.
            nx = -dy / length
            ny = dx / length
            candidate = Point(mx + delta * nx, my + delta * ny)
            new_pts = [a, candidate, b]
            mid_idx = 1

        seg_mid_left = Point(
            (new_pts[mid_idx - 1].x + new_pts[mid_idx].x) / 2,
            (new_pts[mid_idx - 1].y + new_pts[mid_idx].y) / 2,
        )
        seg_mid_right = Point(
            (new_pts[mid_idx].x + new_pts[mid_idx + 1].x) / 2,
            (new_pts[mid_idx].y + new_pts[mid_idx + 1].y) / 2,
        )
        if (
            deepest_containing_cut(new_pts[mid_idx]) not in allowed
            or deepest_containing_cut(seg_mid_left) not in allowed
            or deepest_containing_cut(seg_mid_right) not in allowed
        ):
            # Perturbation would leave the chain — not regime-3 for this
            # path.  Pass it through unchanged.
            new_paths.append(path)
            continue

        new_paths.append(
            LigaturePath(
                predicate_id=path.predicate_id,
                vertex_id=path.vertex_id,
                points=tuple(new_pts),
                port_index=path.port_index,
            )
        )
        rerouted += 1

    if rerouted == 0:
        pytest.skip(
            f"{uod_id} has no ligature whose interior waypoint can be "
            f"nudged while staying on the area chain"
        )

    mutated = _clone_dto(dto, ligature_paths=new_paths)

    egi_after = uod.current_egi
    ok, diffs = _structurally_equal_egi(egi_before, egi_after)
    assert ok, (
        f"[{uod_id}] ligature-reroute regime-3 op changed EGI:\n  "
        + "\n  ".join(diffs)
    )

    failures = _check_correspondence(
        f"{uod_id}+regime3-ligature-reroute", egi_before, mutated
    )
    assert not failures, (
        f"[{uod_id}] post-reroute drawing fails correspondence "
        f"(rerouted {rerouted} ligature(s)):\n" + "\n".join(failures)
    )
