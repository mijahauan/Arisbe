"""
Adapter to convert EGILogicalSystem (logical areas model) into
Dau's RelationalGraphWithCuts structure consumed by the spatial engine.
"""
from typing import Dict, FrozenSet, Iterable, Set, Tuple
from dataclasses import dataclass

from frozendict import frozendict

from egi_logical_areas import EGILogicalSystem, EGIGraph
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut


def _collect_area_elements(sys: EGILogicalSystem, area_id: str) -> Set[str]:
    """Union all element IDs from graphs directly contained in the given area.
    Note: This does not recurse into child cuts; containment of child cuts is
    represented by including their cut IDs directly in the parent's area.
    """
    area = sys.logical_areas.get(area_id)
    if not area:
        return set()
    elems: Set[str] = set()
    for g in area.contained_graphs:
        # vertices, edges, cuts are already IDs (strings)
        elems.update(g.vertices)
        elems.update(g.edges)
        elems.update(g.cuts)
    # Add direct child cuts to the parent's area set
    for cid in area.child_areas:
        if cid in sys.logical_areas and sys.logical_areas[cid].is_cut:
            elems.add(cid)
    return elems


def logical_to_relational_graph(sys: EGILogicalSystem) -> RelationalGraphWithCuts:
    """Convert an EGILogicalSystem to a Dau RelationalGraphWithCuts.

    Mapping rules:
    - Each unique vertex ID -> Vertex (generic by default)
    - Each unique edge ID -> Edge
    - Each logical cut area -> Cut with same ID
    - nu: from edges to ordered tuple of incident vertices (arbitrary ordering)
    - rel: relation names carried from EGIGraph.relation_mapping when present
            If multiple graphs define the same edge's relation, last one wins.
    - area: For each context (⊤ and every Cut), map to the set of element IDs
            directly contained in that area (no recursion); parents include their
            direct child cut IDs.
    - sheet: sys.sheet_id
    """
    # Gather sets
    all_vertex_ids: Set[str] = set()
    all_edge_ids: Set[str] = set()
    all_cut_ids: Set[str] = set()

    # Collect from all areas' contained graphs
    for aid, area in sys.logical_areas.items():
        for g in area.contained_graphs:
            all_vertex_ids.update(g.vertices)
            all_edge_ids.update(g.edges)
            all_cut_ids.update(g.cuts)
        # Each logical cut area itself is a cut element
        if area.is_cut:
            all_cut_ids.add(aid)

    # Build objects
    V = frozenset(Vertex(id=vid, label=None, is_generic=True) for vid in all_vertex_ids)
    E = frozenset(Edge(id=eid) for eid in all_edge_ids)
    CutSet = frozenset(Cut(id=cid) for cid in all_cut_ids)

    # Build nu and rel
    nu_map: Dict[str, Tuple[str, ...]] = {}
    rel_map: Dict[str, str] = {}
    for aid, area in sys.logical_areas.items():
        for g in area.contained_graphs:
            for eid, vset in g.nu_mapping.items():
                # Ensure deterministic order for tuple
                nu_map[eid] = tuple(sorted(vset))
            for eid, rname in g.relation_mapping.items():
                rel_map[eid] = rname

    # Build area mapping for sheet and each cut
    area_map: Dict[str, FrozenSet[str]] = {}
    # Sheet area (root): directly contained elements and its direct child cuts
    area_map[sys.sheet_id] = frozenset(_collect_area_elements(sys, sys.sheet_id))
    # Each cut area
    for cid, area in sys.logical_areas.items():
        if area.is_cut:
            area_map[cid] = frozenset(_collect_area_elements(sys, cid))

    # Instantiate relational graph
    rgc = RelationalGraphWithCuts(
        V=V,
        E=E,
        nu=frozendict(nu_map),
        sheet=sys.sheet_id,
        Cut=CutSet,
        area=frozendict(area_map),
        rel=frozendict(rel_map),
    )
    return rgc
