"""
eg_navigation — content-addressable structural selection over an EGI.

Dau's transformation rules (and the ``RuleInteraction`` protocol that drives
them) take **element ids** — the ephemeral UUIDs the engine assigns. Authoring
a proof by id is the friction the Praeclarum dogfood surfaced
(``project-ergasterion-dogfood-findings``): you cannot say "the cut that holds
P", only "cut_6a3f…", and those ids change at every step. This module is the
fix — a small, pure vocabulary for naming elements by **what they are and
where they sit** (relation name, vertex label, containment) so a selection
survives across states and reads like the picture.

It is the query/introspection half of the authoring layer; the *action* half
(applying rules, recording the chain) is ``proof_authoring``. It is also the
introspection a future Ergasterion/Agon HTTP layer wants (``describe`` answers
"which area, what polarity?" — dogfood finding #1).

Area topology is **not** redefined here — it is delegated to
``presentation_ops`` (``element_area`` / ``cut_parents``), the single source of
truth for the area tree. This module adds the *content* layer on top.
"""

from typing import Dict, FrozenSet, List, Optional, Tuple

from egi_core_dau import AreaPolarity, ElementID, RelationalGraphWithCuts
from presentation_ops import cut_parents, element_area


# --------------------------------------------------------------------------- #
# Kind / membership                                                           #
# --------------------------------------------------------------------------- #

def _cut_ids(egi) -> set:
    return {c.id for c in egi.Cut}


def _edge_ids(egi) -> set:
    return {e.id for e in egi.E}


def _vertex_ids(egi) -> set:
    return {v.id for v in egi.V}


def kind_of(egi: RelationalGraphWithCuts, element: ElementID) -> str:
    """One of ``"sheet"``, ``"cut"``, ``"edge"``, ``"vertex"``, ``"unknown"``."""
    if element == egi.sheet:
        return "sheet"
    if element in _cut_ids(egi):
        return "cut"
    if element in _edge_ids(egi):
        return "edge"
    if element in _vertex_ids(egi):
        return "vertex"
    return "unknown"


def area_of(egi: RelationalGraphWithCuts, element: ElementID) -> Optional[ElementID]:
    """The area directly containing ``element`` (``None`` for the sheet).

    Works for vertices, edges, and cuts — delegating to ``presentation_ops``."""
    ea = element_area(egi)
    if element in ea:
        return ea[element]
    return cut_parents(egi).get(element)


def polarity_of(
    egi: RelationalGraphWithCuts, area: ElementID
) -> Tuple[AreaPolarity, int]:
    """``(polarity, depth)`` of an area — POSITIVE (recto, even) or NEGATIVE
    (verso, odd). Thin wrapper over ``egi.area_polarity`` so callers need not
    reach through the core model."""
    return egi.area_polarity(area)


# --------------------------------------------------------------------------- #
# Children of an area                                                         #
# --------------------------------------------------------------------------- #

def child_cuts(egi: RelationalGraphWithCuts, area: ElementID) -> List[ElementID]:
    """Cuts directly inside ``area`` (not recursive)."""
    cuts = _cut_ids(egi)
    return [e for e in egi.area.get(area, ()) if e in cuts]


def child_edges(
    egi: RelationalGraphWithCuts,
    area: ElementID,
    relation: Optional[str] = None,
) -> List[ElementID]:
    """Edges directly inside ``area``; if ``relation`` is given, only those
    whose relation name matches."""
    edges = _edge_ids(egi)
    return [
        e for e in egi.area.get(area, ())
        if e in edges and (relation is None or egi.rel.get(e) == relation)
    ]


def child_vertices(egi: RelationalGraphWithCuts, area: ElementID) -> List[ElementID]:
    """Vertices directly inside ``area`` (not recursive)."""
    verts = _vertex_ids(egi)
    return [e for e in egi.area.get(area, ()) if e in verts]


# --------------------------------------------------------------------------- #
# Content-addressable lookup                                                   #
# --------------------------------------------------------------------------- #

def relation_of(egi: RelationalGraphWithCuts, edge: ElementID) -> Optional[str]:
    """The relation name carried by ``edge`` (``egi.rel``)."""
    return egi.rel.get(edge)


def cut_holding_relation(
    egi: RelationalGraphWithCuts,
    area: ElementID,
    relation: str,
) -> Optional[ElementID]:
    """The child cut of ``area`` that *directly* contains an edge named
    ``relation`` — e.g. "the implication whose antecedent is P". ``None`` if no
    such cut. (Raises nothing; ambiguity returns the first in area order, which
    is deterministic for a given EGI.)"""
    for c in child_cuts(egi, area):
        if child_edges(egi, c, relation):
            return c
    return None


def empty_cut_in(
    egi: RelationalGraphWithCuts, area: ElementID
) -> Optional[ElementID]:
    """The child cut of ``area`` that directly contains *no* edges — the
    "scroll's inner loop" before anything is iterated into it."""
    for c in child_cuts(egi, area):
        if not child_edges(egi, c):
            return c
    return None


def vertices_of_edge(
    egi: RelationalGraphWithCuts, edge: ElementID
) -> Tuple[ElementID, ...]:
    """The vertex sequence incident to ``edge`` (``egi.nu`` — argument order
    preserved)."""
    return tuple(egi.nu.get(edge, ()))


def edges_on_vertex(
    egi: RelationalGraphWithCuts, vertex: ElementID
) -> List[ElementID]:
    """Every edge whose incidence ``ν`` includes ``vertex`` — the relations
    strung along one line of identity."""
    return [e.id for e in egi.E if vertex in tuple(egi.nu.get(e.id, ()))]


def vertex_by_label(
    egi: RelationalGraphWithCuts, label: str
) -> Optional[ElementID]:
    """The vertex carrying ``label`` (a generic/named line of identity), or
    ``None``. Labels need not be unique in general; returns the first found."""
    for v in egi.V:
        if getattr(v, "label", None) == label:
            return v.id
    return None


# --------------------------------------------------------------------------- #
# Closure + structural identity                                               #
# --------------------------------------------------------------------------- #

def closed_subgraph(
    egi: RelationalGraphWithCuts,
    seed,
    *,
    for_erasure: bool = False,
    context_area: Optional[ElementID] = None,
) -> FrozenSet[ElementID]:
    """The closed subgraph generated by ``seed`` (an id or iterable of ids).

    Delegates to ``SubgraphClosureValidator`` — Beta-aware: vertices in
    ancestor areas of ``context_area`` are treated as free, so a relation on a
    line of identity closes without dragging in the whole line. ``for_erasure``
    pulls in every edge referencing a selected vertex (ERA / IT- safety)."""
    from subgraph_closure_validator import SubgraphClosureValidator

    seeds = frozenset([seed] if isinstance(seed, str) else seed)
    area = context_area
    if area is None:
        # Default to the seed's own area (all seeds assumed co-areal).
        first = next(iter(seeds))
        area = area_of(egi, first)
    analysis = SubgraphClosureValidator(egi).analyze_closure(
        seeds, allow_expansion=True, context_area=area, for_erasure=for_erasure
    )
    return analysis.closed_subgraph


def area_signature(
    egi: RelationalGraphWithCuts, area: Optional[ElementID] = None
):
    """An order-insensitive structural signature of an area subtree: relation
    names (with arity) plus nested-cut structure, sibling order dropped (a
    projection artifact, spec §5.3).

    Two **Alpha** graphs are the same iff their sheet signatures match — this
    is the cheap, readable conclusion check for propositional proofs. It does
    **not** capture the W-partition (which lines of identity are shared), so
    for **Beta** graphs it is only a necessary condition; use ``same_graph``
    (full isomorphism) as the authority there."""
    if area is None:
        area = egi.sheet
    rels = sorted(
        (egi.rel.get(e), len(vertices_of_edge(egi, e)))
        for e in child_edges(egi, area)
    )
    subcuts = sorted(area_signature(egi, c) for c in child_cuts(egi, area))
    return ("rels", tuple(rels), "cuts", tuple(subcuts))


def same_graph(
    egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts
) -> bool:
    """Whether two EGIs are the same graph (full isomorphism, Alpha or Beta).

    Uses ``GraphIsomorphismEngine`` over the complete element set of each — the
    authority for proof-conclusion equality when lines of identity make a
    cheap signature insufficient."""
    from graph_isomorphism_engine import GraphIsomorphismEngine

    def all_ids(egi) -> FrozenSet[ElementID]:
        return frozenset(
            [v.id for v in egi.V] + [e.id for e in egi.E] + [c.id for c in egi.Cut]
        )

    result = GraphIsomorphismEngine().test_cross_egi_isomorphism(
        egi1, all_ids(egi1), egi2, all_ids(egi2)
    )
    return result.is_isomorphic


# --------------------------------------------------------------------------- #
# Introspection (the "describe this element" the web layer wants)             #
# --------------------------------------------------------------------------- #

def describe(egi: RelationalGraphWithCuts, element: ElementID) -> Dict:
    """A human/JSON-friendly description of one element: its kind, the area it
    sits in, that area's polarity and depth, and its relation name / vertex
    label / arity as applicable. Pure introspection — the answer to "what is
    this and where does it sit?" that authoring (and a future HTTP selection
    API) needs."""
    k = kind_of(egi, element)
    info: Dict = {"id": element, "kind": k}
    if k in ("edge", "vertex", "cut"):
        area = area_of(egi, element)
        info["area"] = area
        if area is not None:
            pol, depth = egi.area_polarity(area)
            info["area_polarity"] = pol.value
            info["area_depth"] = depth
    if k == "edge":
        info["relation"] = egi.rel.get(element)
        info["arity"] = len(vertices_of_edge(egi, element))
    elif k == "vertex":
        v = next((v for v in egi.V if v.id == element), None)
        info["label"] = getattr(v, "label", None) if v else None
    return info


__all__ = [
    "kind_of", "area_of", "polarity_of",
    "child_cuts", "child_edges", "child_vertices",
    "relation_of", "cut_holding_relation", "empty_cut_in",
    "vertices_of_edge", "edges_on_vertex", "vertex_by_label",
    "closed_subgraph", "area_signature", "same_graph", "describe",
]
