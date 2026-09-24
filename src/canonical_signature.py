"""
UUID-independent canonical signatures for the elements of a Dau EGI.

The three linear-format generators (EGIF, CGIF, CLIF) need to assign vertex
labels in an order that depends only on graph structure, never on the freshly
minted UUIDs the parser hands out. Without this, two parses of the same input
yield different UUIDs and the generator's iteration order shifts, so
``generate(parse(generate(parse(s))))`` may differ in emitted text from
``generate(parse(s))`` even though both EGIs are structurally identical
(see issue #6).

This module computes a Weisfeiler-Leman-style refinement of vertex colors:

  - Initial color encodes per-vertex facts that don't depend on UUIDs:
    constant vs. generic, the constant name when applicable, area-nesting
    depth.
  - Each round, an edge's signature is (relation name, depth, tuple of
    incident-vertex colors in ν argument order).
  - Each vertex's new color is (old color, sorted multiset of
    (edge signature, arg position) over its incidences).
  - Cuts get signatures by recursive bottom-up encoding of their area
    contents (sorted edge sigs, sorted vertex sigs, sorted nested-cut sigs).

True graph symmetries collapse to equal signatures — that's intrinsic
ambiguity, not a bug.
"""

from typing import Any, Dict, List, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts


TIE_BREAK_BUDGET = 10000
"""Cap on the permutations explored when breaking ties (see ``break_ties``).

Measured 2026-09-24 over 341 graphs (tier A enumerated + the corpus as used):
**10 graphs tie at all**, every one a single class of two, so the real work is
two permutations and the budget is a formality rather than a design constraint.
It exists so that a pathologically symmetric graph degrades *visibly* instead of
hanging — see ``ties_broken`` in the return value.
"""


def compute_canonical_signatures(
    graph: RelationalGraphWithCuts,
    *,
    break_ties: bool = False,
) -> Tuple[Dict[ElementID, Any], Dict[ElementID, Any], Dict[ElementID, Any]]:
    """Return (vertex_sig, edge_sig, cut_sig) for every element of ``graph``.

    Two structurally equivalent EGIs (differing only in UUIDs) produce
    identical signature dictionaries up to UUID renaming, so sorting any
    collection of elements by signature is a UUID-independent canonical
    order.

    ``break_ties`` (default off) additionally resolves *genuine symmetries*,
    which this refinement deliberately collapses to equal colors. Equal colors
    are the honest answer to "are these interchangeable?", and the isomorphism
    engine and the ligature rules rely on that, so nothing here changes for
    them. But a *generator* must still pick one of the interchangeable
    orderings, and with equal keys Python's stable sort falls back to the input
    list order — which comes from iterating a ``frozenset`` of ``uuid4`` ids.
    That is the whole of the nondeterminism measured on
    ``(P *u) (P *v) ~[ (Loves v *y) (Loves u *x) ]``: 200 parses, two texts.

    With ``break_ties=True`` the tie is settled by **individualization**: every
    assignment of distinct ranks within each tied class is tried, each scored by
    a structural certificate that mentions no id, and the lexicographic minimum
    wins. So the order depends on the graph and nothing else, and two
    *differently constructed* copies of one graph order identically — a true
    canonical form rather than merely a reproducible one. Candidates that tie on
    certificate are interchangeable by construction and emit the same text.
    """

    def depth_of(eid: ElementID) -> int:
        d = 0
        try:
            ctx = graph.get_context(eid)
        except ValueError:
            return 0
        while ctx is not None and ctx != graph.sheet:
            d += 1
            try:
                ctx = graph.get_context(ctx)
            except ValueError:
                break
        return d

    vertex_depth = {v.id: depth_of(v.id) for v in graph.V}
    edge_depth = {e.id: depth_of(e.id) for e in graph.E}

    rho = getattr(graph, "rho", None)

    def is_constant(vid: ElementID) -> bool:
        if rho is not None and vid in rho:
            return rho[vid] is not None
        v = graph.get_vertex(vid)
        return not getattr(v, "is_generic", True)

    def constant_name(vid: ElementID) -> str:
        if rho is not None and vid in rho and rho[vid] is not None:
            return rho[vid]
        v = graph.get_vertex(vid)
        return getattr(v, "label", None) or ""

    def ranked(colors: Dict[ElementID, Any]) -> Dict[ElementID, str]:
        """Hash-cons a round's colors to canonical fixed-width rank strings.

        Ranks are assigned by sorting the (UUID-independent) color *values*, so
        two parses of the same structure rank identically. Consing keeps each
        round's colors O(1)-comparable — without it a color embeds the whole
        previous round's color of every neighbour, so colors grow as unshared
        trees, every comparison walks them, and the loop below (which the old
        tuple-equality check never ended early, since ``(old, inc)`` can never
        equal ``old``) went super-linear: ~16 s to generate a 200-atom hub-shaped
        sheet, measured 2026-07-03 (the RUN_4 F2⁗ round-compute wall)."""
        distinct = sorted(set(colors.values()))
        idx = {c: f"{i:08d}" for i, c in enumerate(distinct)}
        return {k: idx[c] for k, c in colors.items()}

    # Second-order maps (B-min): a sorted line must never collapse with an
    # unsorted twin, so the sort joins the initial color; a quotation area
    # must never collapse with a negation, so quoted-ness joins the cut sig.
    # Both are appended uniformly (empty string / 0 when absent), preserving
    # relative order — a first-order graph's canonical order is unchanged.
    sort_map = getattr(graph, "sort", {}) or {}
    quotation_map = getattr(graph, "quotation", {}) or {}

    initial: Dict[ElementID, Any] = {}
    for v in graph.V:
        vid = v.id
        if is_constant(vid):
            initial[vid] = (
                "const",
                vertex_depth[vid],
                constant_name(vid),
                sort_map.get(vid, ""),
            )
        else:
            initial[vid] = ("generic", vertex_depth[vid], sort_map.get(vid, ""))
    vertex_color: Dict[ElementID, str] = ranked(initial)
    n_classes = len(set(vertex_color.values()))

    vertex_incidences: Dict[ElementID, List[Tuple[ElementID, int]]] = {
        v.id: [] for v in graph.V
    }
    for e in graph.E:
        for i, vid in enumerate(graph.get_incident_vertices(e.id)):
            if vid in vertex_incidences:
                vertex_incidences[vid].append((e.id, i))

    for _ in range(len(graph.V) + 1):
        edge_sig: Dict[ElementID, Any] = {}
        for e in graph.E:
            vseq = graph.get_incident_vertices(e.id)
            edge_sig[e.id] = (
                graph.get_relation_name(e.id),
                edge_depth[e.id],
                tuple(vertex_color[v] for v in vseq),
            )
        new_raw: Dict[ElementID, Any] = {}
        for v in graph.V:
            vid = v.id
            inc = sorted(
                (edge_sig[eid], pos) for (eid, pos) in vertex_incidences[vid]
            )
            new_raw[vid] = (vertex_color[vid], tuple(inc))
        new_color = ranked(new_raw)
        new_n = len(set(new_color.values()))
        if new_n == n_classes:
            # WL refinement only ever *splits* color classes (a round's color
            # extends the previous round's), so an unchanged class count means
            # the partition is stable — later rounds cannot discriminate more.
            break
        vertex_color = new_color
        n_classes = new_n

    def final_sigs(colors: Dict[ElementID, str]):
        """(edge_sig, cut_sig) under an arbitrary vertex coloring."""
        esig: Dict[ElementID, Any] = {}
        for e in graph.E:
            vseq = graph.get_incident_vertices(e.id)
            esig[e.id] = (
                graph.get_relation_name(e.id),
                edge_depth[e.id],
                tuple(colors[v] for v in vseq),
            )
        csig: Dict[ElementID, Any] = {}

        def compute_cut_sig(cid: ElementID) -> Any:
            if cid in csig:
                return csig[cid]
            area = graph.get_area(cid)
            esigs = sorted(esig[eid] for eid in area if eid in graph._edge_map)
            vsigs = sorted(colors[vid] for vid in area if vid in graph._vertex_map)
            csigs = sorted(compute_cut_sig(c) for c in area if c in graph._cut_map)
            sig = (tuple(esigs), tuple(vsigs), tuple(csigs), int(cid in quotation_map))
            csig[cid] = sig
            return sig

        for c in graph.Cut:
            compute_cut_sig(c.id)
        return esig, csig

    if break_ties:
        vertex_color = _individualize(graph, vertex_color, final_sigs)

    final_edge_sig, cut_sig = final_sigs(vertex_color)
    return vertex_color, final_edge_sig, cut_sig


def _certificate(colors, edge_sig, cut_sig, variable_names) -> Any:
    """A score for one candidate ordering, mentioning no element id.

    It carries exactly what the three generators sort by — the edge
    signatures, the vertex ranks and the cut signatures — so two candidates
    with equal certificates emit identical text, and choosing between *those*
    cannot matter.

    ``variable_names`` is in here for a reason worth keeping. Two lines can be
    structurally interchangeable — the refinement is *right* to colour them
    equally — while carrying **different names the generator will emit**. CLIF
    preserves the parser's names, so on
    ``(P *u) (P *v) ~[ (Loves v *y) (Loves u *x) ]`` the structure cannot say
    which of ``u``/``v`` should come first, every certificate tied, and the pick
    fell back to enumeration order: still two texts after the structural tie was
    settled. Names stay out of the *colours* (they are not structure, and the
    isomorphism engine must not see them) but they belong in the choice between
    orderings that are otherwise indistinguishable.
    """
    named = tuple(sorted(
        (colors[vid], name) for vid, name in variable_names.items() if vid in colors
    ))
    return (
        tuple(sorted(edge_sig.values())),
        tuple(sorted(colors.values())),
        tuple(sorted(cut_sig.values())),
        named,
    )


def _individualize(graph, vertex_color, final_sigs):
    """Give every vertex a distinct rank, canonically.

    Ties are resolved by trying each assignment of distinct ranks within each
    tied class and keeping the lexicographically smallest certificate. Over
    budget, the colors are returned untouched: a graph symmetric enough to
    exceed it keeps today's behaviour rather than hanging, and says so by
    leaving ties in place.
    """
    import itertools
    import math

    variable_names = dict(getattr(graph, "variable_names", {}) or {})

    classes: Dict[str, List[ElementID]] = {}
    for vid, color in vertex_color.items():
        classes.setdefault(color, []).append(vid)
    tied = [sorted(ids) for color, ids in sorted(classes.items()) if len(ids) > 1]
    if not tied:
        return vertex_color

    work = math.prod(math.factorial(len(ids)) for ids in tied)
    if work > TIE_BREAK_BUDGET:
        return vertex_color

    best_cert = None
    best_colors = vertex_color
    for perms in itertools.product(*(itertools.permutations(ids) for ids in tied)):
        candidate = dict(vertex_color)
        for ids, perm in zip(tied, perms):
            base = vertex_color[ids[0]]
            for rank, vid in enumerate(perm):
                candidate[vid] = f"{base}.{rank:04d}"
        esig, csig = final_sigs(candidate)
        cert = _certificate(candidate, esig, csig, variable_names)
        if best_cert is None or cert < best_cert:
            best_cert, best_colors = cert, candidate
    return best_colors
