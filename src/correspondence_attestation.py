"""
Runtime attestation of the linear-graphical correspondence invariant.

docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §6 ("Boundary events — when the
invariant attaches") names the points at which correspondence becomes
mandatory: save to tomos corpus, assert in Agon, apply a transformation
rule, load from corpus, and (future) submit a stylus drawing.  §8's
first open question is whether to run the check in production as well
as in CI — "Cost: constant-factor overhead at save/load/apply time.
Benefit: catches drift in production, not only in CI."

This module is the answer to that question.  It exposes:

- ``check_correspondence(egi, dto)`` — runs every §3.3 property check
  and returns a list of human-readable failure messages.  Empty list
  means the (EGI, drawing) pair denotes the same object.
- ``attest_correspondence(egi, dto, *, context=None)`` — wraps
  ``check_correspondence``: returns None on success, raises
  ``CorrespondenceViolation`` on failure.  This is the hook for
  boundary events.
- ``is_in_correspondence(egi, dto)`` — boolean wrapper for callers
  that need a predicate, not an exception.

All three are pure functions of (EGI, LayoutDTO) and do not mutate
either argument.  They reuse the area-topology helpers from
``presentation_ops`` so the runtime check and the §7 property tests
share their internal vocabulary.
"""

from typing import List, Optional, Sequence

from egi_core_dau import RelationalGraphWithCuts
from layout_dto import LayoutDTO
from presentation_ops import (
    bounds_in_cut,
    box_intrudes_cut,
    boxes_overlap,
    count_cut_crossings,
    crossing_sequence,
    cut_parents,
    element_area,
    path_intersects_box,
    point_in_cut,
    predicate_label_box,
    resolve_cut_boundaries,
    vertex_label_box,
)


class CorrespondenceViolation(AssertionError):
    """Raised when an (EGI, LayoutDTO) pair fails §3.3 correspondence.

    Inherits ``AssertionError`` so it surfaces as a contract violation,
    not a generic runtime error.  The exception's ``args[0]`` is the
    fully formatted multi-line failure report; ``failures`` and
    ``context`` are exposed as attributes for callers that want
    structured access.
    """

    def __init__(self, failures: Sequence[str], context: Optional[str] = None):
        self.failures: List[str] = list(failures)
        self.context = context
        if context:
            header = (
                f"Correspondence violated at {context} "
                f"({len(self.failures)} failure(s)):"
            )
        else:
            header = f"Correspondence violated ({len(self.failures)} failure(s)):"
        super().__init__(header + "\n" + "\n".join(self.failures))


def check_correspondence(
    egi: RelationalGraphWithCuts, dto: LayoutDTO
) -> List[str]:
    """Run every §3.3 property check on (egi, dto).  Returns failures.

    The returned list is empty when the pair is in correspondence.
    Non-empty means the pair violates one or more §3.3 properties; each
    entry is a human-readable explanation of which property failed.

    Properties checked, in order:
      - Totality and injectivity (every EGI element appears in the DTO
        and vice versa);
      - Containment fidelity (cut bounds geometrically contain the
        elements the EGI says are in their areas, and sub-cut bounds
        nest correctly);
      - Incidence fidelity (LigaturePath count + vertex multiset per
        predicate matches ν);
      - Identity fidelity:
          - endpoint placement (path[-1] coincides with the vertex
            position; both endpoints lie in their respective areas'
            cut bounds);
          - crossing-multiset equality (the ligature crosses each
            authorized cut's boundary exactly once and no other cut's
            boundary at all, where the authorized set is the area-tree
            path between predicate-area and vertex-area — the
            projection-independent ``crossing_sequence``);
          - shared-identity connectedness (the union of paths ending at
            a vertex forms one connected component rooted at the
            vertex's drawn position);
      - Argument order (LigaturePath.port_index sequenced by ascending
        port reproduces ν exactly).
    """
    failures: List[str] = []

    # The cut's drawn shape (from the style) is authoritative for containment:
    # "inside the cut" means inside the curve the renderer draws — the inscribed
    # ellipse for an oval/circle style, the box otherwise — so the shape is
    # immaterial to *which* area an element is in.
    cut_shape = getattr(dto.style, "cut_shape", "rounded_rectangle")
    # The drawn corner radius, so containment tests the rounded rectangle the
    # renderer draws (not a sharp-box proxy) — exact, no corner void.
    cut_radius = float(getattr(dto.style, "cut_corner_radius", 0) or 0)
    # Phase 4: the literal drawn boundary polyline per cut (a freeform human-drawn
    # cut, or a hand-drawn wobbled oval), or None where the analytic shape above is
    # already exact.  Containment/crossing read off this curve so the test matches
    # the picture — wobble and all (docs/EXACT_CORRESPONDENCE.md Phase 4).
    cut_boundaries = resolve_cut_boundaries(dto)

    egi_v_ids = {v.id for v in egi.V}
    egi_e_ids = {e.id for e in egi.E}
    egi_cut_ids = {c.id for c in egi.Cut}

    # Totality.
    for kind, want, have in (
        ("vertex", egi_v_ids, set(dto.vertex_positions.keys())),
        ("predicate", egi_e_ids, set(dto.predicate_positions.keys())),
        ("cut", egi_cut_ids, set(dto.cut_bounds.keys())),
    ):
        missing = want - have
        if missing:
            failures.append(
                f"  totality: {kind}(s) missing from DTO: {sorted(missing)}"
            )

    # Injectivity.
    extra_v = set(dto.vertex_positions.keys()) - egi_v_ids
    extra_e = set(dto.predicate_positions.keys()) - egi_e_ids
    extra_cuts = set(dto.cut_bounds.keys()) - egi_cut_ids - {egi.sheet}
    if extra_v:
        failures.append(
            f"  injectivity: stray vertex IDs in DTO: {sorted(extra_v)}"
        )
    if extra_e:
        failures.append(
            f"  injectivity: stray predicate IDs in DTO: {sorted(extra_e)}"
        )
    if extra_cuts:
        failures.append(
            f"  injectivity: stray cut IDs in DTO: {sorted(extra_cuts)}"
        )

    # Containment.
    for cut in egi.Cut:
        bounds = dto.cut_bounds.get(cut.id)
        if bounds is None:
            continue
        cbnd = cut_boundaries.get(cut.id)
        for elem_id in egi.area.get(cut.id, frozenset()):
            # A vertex is a dot — point containment.  A predicate is a label box,
            # checked as an *extent* in the dedicated block below (it falls through
            # here: no vertex pos, no cut bounds).
            pos = dto.vertex_positions.get(elem_id)
            if pos is not None:
                if not point_in_cut(pos, bounds, cut_shape, cut_radius, cbnd):
                    failures.append(
                        f"  containment: {elem_id} in egi.area[{cut.id}] "
                        f"at ({pos.x:.1f},{pos.y:.1f}) outside cut bounds"
                    )
                continue
            child = dto.cut_bounds.get(elem_id)
            if child is None:
                continue
            if not bounds_in_cut(child, bounds, cut_shape, cut_radius, cbnd):
                failures.append(
                    f"  containment: sub-cut {elem_id} in egi.area[{cut.id}] "
                    f"is not fully inside parent bounds"
                )

    # Incidence — count + multiset.
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

    elem_area_map = element_area(egi)
    cut_ids = {c.id for c in egi.Cut}
    parent_map = cut_parents(egi)

    # Extent (Phase 3): a predicate's drawn label BOX — not its anchor point — is its
    # containment.  The box must sit wholly inside every ancestor cut and wholly
    # outside every non-ancestor cut; a box that straddles a cut boundary cannot be
    # read into a single area, so the reader could not recover which area the
    # predicate is in (`docs/EXACT_CORRESPONDENCE.md` Phase 3).
    for edge in egi.E:
        ppos = dto.predicate_positions.get(edge.id)
        if ppos is None:
            continue
        box = predicate_label_box(egi.get_relation_name(edge.id), ppos, dto.style)
        p_area = elem_area_map.get(edge.id, egi.sheet)
        ancestors = set()
        cur = p_area
        while cur in cut_ids:
            ancestors.add(cur)
            cur = parent_map.get(cur, egi.sheet)
        for cut in egi.Cut:
            cbounds = dto.cut_bounds.get(cut.id)
            if cbounds is None:
                continue
            if cut.id in ancestors:
                if not bounds_in_cut(box, cbounds, cut_shape, cut_radius,
                                     cut_boundaries.get(cut.id)):
                    failures.append(
                        f"  extent: predicate {edge.id} label box straddles out "
                        f"of its area cut {cut.id}"
                    )
            elif box_intrudes_cut(box, cbounds, cut_shape, cut_radius):
                failures.append(
                    f"  extent: predicate {edge.id} label box intrudes into "
                    f"cut {cut.id} (not on its area chain)"
                )

    # Occlusion (Phase 3b): a mark the reader cannot recover breaks
    # correspondence.  Three ways a label is rendered illegible:
    #   (1) text-on-text — two label boxes overlapping each other;
    #   (2) a cut boundary stroke bisecting a vertex/constant label box (the
    #       predicate analogue is the no-straddle extent check above);
    #   (3) a line of identity the label is NOT incident to running through the
    #       box — a strike-through (built below, after the boxes are gathered).
    # Each label box comes from the renderer's single source of truth
    # (`predicate_label_box` / `vertex_label_box`) so the test and the drawing agree
    # (`docs/EXACT_CORRESPONDENCE.md` Phase 3b).  Boxes that only abut are legible
    # and not flagged.
    #
    # Property (3)'s constructive partner ships with it: `elk_layout_engine`
    # routes non-incident ligatures *around* label boxes (treated as soft
    # obstacles that yield to forbidden cuts), so honest layouts pass and only a
    # genuine strike-through — the shared-vertex fan-in after IT+ that surfaced
    # it (`roberts_domain_modeling`) — is refused.  `path_intersects_box` is the
    # shared obstacle-test primitive.
    show_vertex_labels = (
        getattr(dto.style, "vertex_rendering_mode", "dot_and_label") != "dot_only"
    )
    label_boxes = []  # (kind, elem_id, box)
    for edge in egi.E:
        ppos = dto.predicate_positions.get(edge.id)
        if ppos is None:
            continue
        label_boxes.append(
            ("predicate", edge.id,
             predicate_label_box(egi.get_relation_name(edge.id), ppos, dto.style))
        )
    if show_vertex_labels:
        for vertex in egi.V:
            if not getattr(vertex, "label", None):
                continue
            vpos = dto.vertex_positions.get(vertex.id)
            if vpos is None:
                continue
            label_boxes.append(
                ("vertex", vertex.id,
                 vertex_label_box(vertex.label, vpos, dto.style,
                                  dto.ligature_paths, vertex.id,
                                  egi=egi, cut_bounds=dto.cut_bounds))
            )

    # (1) text-on-text overlap (each unordered pair once).
    for i in range(len(label_boxes)):
        k1, id1, b1 = label_boxes[i]
        for j in range(i + 1, len(label_boxes)):
            k2, id2, b2 = label_boxes[j]
            if boxes_overlap(b1, b2):
                failures.append(
                    f"  occlusion: {k1} {id1} label box overlaps "
                    f"{k2} {id2} label box (text-on-text)"
                )

    # (2) a vertex/constant label box bisected by a cut boundary — the box must sit
    # wholly inside every ancestor cut and wholly outside every other cut, like the
    # predicate extent check.  (Predicate boxes are already covered above.)
    for kind, eid, box in label_boxes:
        if kind != "vertex":
            continue
        area = elem_area_map.get(eid, egi.sheet)
        ancestors = set()
        cur = area
        while cur in cut_ids:
            ancestors.add(cur)
            cur = parent_map.get(cur, egi.sheet)
        for cut in egi.Cut:
            cbounds = dto.cut_bounds.get(cut.id)
            if cbounds is None:
                continue
            if cut.id in ancestors:
                if not bounds_in_cut(box, cbounds, cut_shape, cut_radius,
                                     cut_boundaries.get(cut.id)):
                    failures.append(
                        f"  occlusion: vertex {eid} label box straddles out "
                        f"of its area cut {cut.id}"
                    )
            elif box_intrudes_cut(box, cbounds, cut_shape, cut_radius):
                failures.append(
                    f"  occlusion: vertex {eid} label box intrudes into "
                    f"cut {cut.id} (not on its area chain)"
                )

    # (3) a label box struck through by a line of identity it is NOT incident
    # to.  An incident line legitimately meets the label at its anchor (a
    # predicate's own hook line; a vertex's own ligature); any *other* ligature
    # running through the open interior of the box bisects the text and the
    # reader cannot recover it — a genuine occlusion.  The constructive partner
    # keeps non-incident lines clear: ``elk_layout_engine`` routes ligatures
    # around label boxes (treated as obstacles), so this check attests the
    # routed result.  Uses ``path_intersects_box`` (open interior — a line
    # grazing the border is legible and not flagged).
    for kind, eid, box in label_boxes:
        for path in dto.ligature_paths:
            incident = (
                (kind == "predicate" and path.predicate_id == eid)
                or (kind == "vertex" and path.vertex_id == eid)
            )
            if incident:
                continue
            if path_intersects_box(path.points, box):
                failures.append(
                    f"  occlusion: {kind} {eid} label box struck through by "
                    f"line of identity ({path.predicate_id} → {path.vertex_id}) "
                    f"it is not incident to"
                )

    # Identity 1/3: endpoint placement.
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
            area = elem_area_map.get(eid)
            if area in cut_ids:
                bounds = dto.cut_bounds.get(area)
                pt = pts[end_idx]
                if bounds is not None and not point_in_cut(
                        pt, bounds, cut_shape, cut_radius, cut_boundaries.get(area)):
                    failures.append(
                        f"  identity-endpoint: ({path.predicate_id} → "
                        f"{path.vertex_id}) {label_str} endpoint outside "
                        f"egi.area[{area}] cut bounds"
                    )

    # Identity 2/3: crossing-multiset equality.
    #
    # The projection-independent fact is the *required crossing-sequence*
    # — the cuts on the area-tree path between predicate-area and
    # vertex-area (``crossing_sequence``).  A faithful drawing realizes
    # it exactly: each authorized cut's boundary crossed once (net),
    # every other cut's boundary not crossed at all.  This supersedes the
    # earlier sampled area-membership check (point/midpoint containment),
    # which could not see a curve that crossed an *authorized* cut the
    # wrong number of times (in-out-in) nor a dip into a forbidden cut
    # *between* samples.  We count true boundary crossings instead of
    # sampling — see ``presentation_ops.count_boundary_crossings``.
    cut_bounds = dto.cut_bounds
    for path in dto.ligature_paths:
        v_area = elem_area_map.get(path.vertex_id, egi.sheet)
        p_area = elem_area_map.get(path.predicate_id, egi.sheet)
        required = set(crossing_sequence(p_area, v_area, parent_map))
        for cut in egi.Cut:
            bounds = cut_bounds.get(cut.id)
            if bounds is None:
                continue
            actual = count_cut_crossings(path.points, bounds, cut_shape, cut_radius,
                                         cut_boundaries.get(cut.id))
            if cut.id in required:
                if actual != 1:
                    failures.append(
                        f"  identity-crossing: ({path.predicate_id} → "
                        f"{path.vertex_id}) crosses authorized cut {cut.id} "
                        f"{actual}×, want 1 (net once)"
                    )
            elif actual > 0:
                failures.append(
                    f"  identity-crossing: ({path.predicate_id} → "
                    f"{path.vertex_id}) enters forbidden cut {cut.id} "
                    f"({actual} boundary crossing(s)); not on its area chain"
                )

    # Identity 3/3: shared-identity connectedness.
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
            # Already reported by incidence.
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

    # Argument order.
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


def attest_correspondence(
    egi: RelationalGraphWithCuts,
    dto: LayoutDTO,
    *,
    context: Optional[str] = None,
) -> None:
    """Raise CorrespondenceViolation if (egi, dto) is not in correspondence.

    Returns None on success.  ``context`` is a human-readable label
    included in the violation message ("after applying ERA", "loading
    from corpus", etc.) — pass something descriptive at every hook
    point so post-mortem reports tell you which boundary event failed.
    """
    failures = check_correspondence(egi, dto)
    if failures:
        raise CorrespondenceViolation(failures, context=context)


def is_in_correspondence(
    egi: RelationalGraphWithCuts, dto: LayoutDTO
) -> bool:
    """Predicate wrapper around ``check_correspondence``."""
    return not check_correspondence(egi, dto)


# ---------------------------------------------------------------------------
# Overview attestation — the navigation-projection contract.
#
# An overview (docs/ADAPTIVE_SCOPE_VIEWER.md) is a *deliberately incomplete*
# drawing: it collapses deep cuts into content-sized placeholders so a graph too
# large to draw whole can still be navigated.  It therefore CANNOT satisfy §3.3
# totality, and pretending otherwise would be exactly the drift §3.3 exists to
# catch.  ``attest_overview`` is the honest weaker contract a lossy map can make:
#
#   P1  Visible-part correspondence.  Form the quotient EGI (each collapsed cut →
#       a leaf placeholder holding only synthetic boundary predicates for the
#       lines that enter it) and run FULL §3.3 on it.  Everything drawn is exactly
#       right — containment, incidence, crossing-multiset, argument order — and
#       each boundary line crosses into its placeholder once and ends there (the
#       synthetic predicate makes §3.3 check this for free).
#   P2  Faithful summary.  Each placeholder's claimed badge equals the true
#       coordinate-free facts of its hidden subtree (counts + polarity + boundary
#       degree).  The placeholder tells the whole truth about what it hides and
#       claims nothing more — *form*, never actuality.
#
# The expansion law ties the weak contract to the strong one: with no collapsed
# cuts the quotient is the EGI itself and ``attest_overview`` ≡
# ``attest_correspondence``; expanding all the way down lands on the real,
# fully-§3.3-attested picture.
# ---------------------------------------------------------------------------


class OverviewViolation(AssertionError):
    """Raised when an overview (EGI, LayoutDTO, collapsed-cut claims) triple is
    not faithful.  Like ``CorrespondenceViolation`` it inherits ``AssertionError``
    and carries the formatted failures; ``failures`` / ``context`` are exposed."""

    def __init__(self, failures: Sequence[str], context: Optional[str] = None):
        self.failures: List[str] = list(failures)
        self.context = context
        if context:
            header = (
                f"Overview faithfulness violated at {context} "
                f"({len(self.failures)} failure(s)):"
            )
        else:
            header = f"Overview faithfulness violated ({len(self.failures)} failure(s)):"
        super().__init__(header + "\n" + "\n".join(self.failures))


# Badge keys an overview placeholder claims (all exact functions of the EGI).
_BADGE_KEYS = ("cuts", "vertices", "predicates", "polarity", "boundary_degree")


def check_overview(
    egi: RelationalGraphWithCuts,
    dto: LayoutDTO,
    collapsed_cuts,
) -> List[str]:
    """Run the overview faithfulness checks.  Returns failures ([] = faithful).

    ``collapsed_cuts`` is a mapping ``{cut_id: badge}`` — the placeholders the
    drawing claims, each with the badge it shows the reader (``cuts`` /
    ``vertices`` / ``predicates`` / ``polarity`` / ``boundary_degree``).  Pass an
    empty mapping for a full (uncollapsed) drawing, where this reduces to
    ``check_correspondence``.
    """
    from overview_projection import (
        collapse_quotient,
        frontier_placeholders,
        overview_summary,
    )

    failures: List[str] = []
    claims = dict(collapsed_cuts)

    cut_ids = {c.id for c in egi.Cut}
    bad = set(claims) - cut_ids
    if bad:
        failures.append(f"  overview: claimed placeholders are not cuts: {sorted(bad)}")
        # Drop the non-cuts so the quotient can still build for the rest.
        for b in bad:
            claims.pop(b, None)

    # A claimed placeholder must be a *frontier* cut (no collapsed ancestor) —
    # a placeholder nested inside another collapsed cut is hidden, never drawn.
    frontier = frontier_placeholders(egi, claims.keys())
    not_frontier = set(claims) - frontier
    if not_frontier:
        failures.append(
            f"  overview: claimed placeholders hidden inside another "
            f"placeholder (not drawn): {sorted(not_frontier)}"
        )

    # P1 — full §3.3 on the quotient.
    try:
        quotient = collapse_quotient(egi, claims.keys())
        failures.extend(check_correspondence(quotient, dto))
    except Exception as exc:  # malformed collapse → report, don't crash
        failures.append(f"  overview: could not build quotient: {exc}")

    # P2 — faithful summary: claimed badge == the true facts of the hidden subtree.
    real = overview_summary(egi, claims.keys())
    for cid, badge in claims.items():
        truth = real.get(cid)
        if truth is None:
            continue  # already reported as not-a-cut / not-frontier
        for key in _BADGE_KEYS:
            if key not in badge:
                failures.append(
                    f"  overview-summary: placeholder {cid} badge missing '{key}'"
                )
                continue
            if badge[key] != truth[key]:
                failures.append(
                    f"  overview-summary: placeholder {cid} claims {key}="
                    f"{badge[key]!r}, true {key}={truth[key]!r}"
                )

    return failures


def attest_overview(
    egi: RelationalGraphWithCuts,
    dto: LayoutDTO,
    collapsed_cuts,
    *,
    context: Optional[str] = None,
) -> None:
    """Raise ``OverviewViolation`` if the overview is not faithful; else None.

    The navigation-projection backstop, hooked at the overview render boundary
    the way ``attest_correspondence`` is hooked at the full-drawing boundary.
    ``context`` is a human-readable label included in the violation message.
    """
    failures = check_overview(egi, dto, collapsed_cuts)
    if failures:
        raise OverviewViolation(failures, context=context)


__all__ = [
    "CorrespondenceViolation",
    "OverviewViolation",
    "attest_correspondence",
    "attest_overview",
    "check_correspondence",
    "check_overview",
    "is_in_correspondence",
]
