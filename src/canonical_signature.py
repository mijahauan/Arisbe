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


def compute_canonical_signatures(
    graph: RelationalGraphWithCuts,
) -> Tuple[Dict[ElementID, Any], Dict[ElementID, Any], Dict[ElementID, Any]]:
    """Return (vertex_sig, edge_sig, cut_sig) for every element of ``graph``.

    Two structurally equivalent EGIs (differing only in UUIDs) produce
    identical signature dictionaries up to UUID renaming, so sorting any
    collection of elements by signature is a UUID-independent canonical
    order.
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

    vertex_color: Dict[ElementID, Any] = {}
    for v in graph.V:
        vid = v.id
        if is_constant(vid):
            vertex_color[vid] = ("const", vertex_depth[vid], constant_name(vid))
        else:
            vertex_color[vid] = ("generic", vertex_depth[vid])

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
        new_color: Dict[ElementID, Any] = {}
        for v in graph.V:
            vid = v.id
            inc = sorted(
                (edge_sig[eid], pos) for (eid, pos) in vertex_incidences[vid]
            )
            new_color[vid] = (vertex_color[vid], tuple(inc))
        if new_color == vertex_color:
            break
        vertex_color = new_color

    final_edge_sig: Dict[ElementID, Any] = {}
    for e in graph.E:
        vseq = graph.get_incident_vertices(e.id)
        final_edge_sig[e.id] = (
            graph.get_relation_name(e.id),
            edge_depth[e.id],
            tuple(vertex_color[v] for v in vseq),
        )

    cut_sig: Dict[ElementID, Any] = {}

    def compute_cut_sig(cid: ElementID) -> Any:
        if cid in cut_sig:
            return cut_sig[cid]
        area = graph.get_area(cid)
        esigs = sorted(final_edge_sig[eid] for eid in area if eid in graph._edge_map)
        vsigs = sorted(vertex_color[vid] for vid in area if vid in graph._vertex_map)
        csigs = sorted(compute_cut_sig(c) for c in area if c in graph._cut_map)
        sig = (tuple(esigs), tuple(vsigs), tuple(csigs))
        cut_sig[cid] = sig
        return sig

    for c in graph.Cut:
        compute_cut_sig(c.id)

    return vertex_color, final_edge_sig, cut_sig
