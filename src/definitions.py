"""The definition layer — named graphs (``name(ports) := body``), the term-level
twin of the derived-rule layer in ``src/derived_rules.py``.

A **definition** lets ``(subset z x)``, ``(empty e)``, ``(succ x s)`` stand in for
their spelled-out bodies, the way ``universal_instantiation`` is a named *move*.
It is a **conservative (definitional) extension**: pure abbreviation, always
eliminable.  ``expand`` rewrites every defined-relation edge back to its body via
the shared :func:`eg_splice.splice`; the result is an ordinary Dau-Beta graph, so
**all logic, §3.3 attestation, and EGIF/CGIF/CLIF round-tripping run on the
expanded form** (see ``docs/MATH_FIXTURES_ZFC_PEIRCE_1881.md`` Part III-bis, rule
1).  Expressive power is unchanged — Dau's Beta admits this exactly as FOL admits
defined predicates; in CLIF a definition *is* the biconditional
``(forall (ports) (iff (name ports) body))``, and in Sowa's conceptual graphs it
is the native lambda type/relation definition EGIF otherwise lacks.

**Scope (v1): non-recursive definitions only.**  Peirce's ``+``/``×`` are
*recursion equations* on the successor (``x + S(y) = S(x + y)``) and would expand
without end; they need the schema/recursion machinery, not this layer, and are
deliberately out of scope here.  ``expand`` raises on a (direct or indirect)
recursive definition rather than loop.

Touches no protected module.
"""

from dataclasses import dataclass, replace
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from frozendict import frozendict

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from egif_parser_dau import parse_egif
from eg_splice import _all_ids, splice


class Definition:
    """A named graph ``name(ports) := body``.

    ``ports`` are EGIF variable names appearing in ``body_egif`` (in argument
    order); they are the body's free lines, welded onto a use site's arguments on
    expansion.  ``body_egif`` declares the ports with ``*`` at its top scope and
    its own internal lines likewise — those internal lines are α-renamed fresh on
    every expansion so they never fuse onto host lines.
    """

    def __init__(self, name: str, ports: Sequence[str], body_egif: str):
        self.name = name
        self.ports = tuple(ports)
        self.body_egif = body_egif
        self._body: Optional[RelationalGraphWithCuts] = None
        # When built from a pre-existing body EGI (``from_egi``), the port host
        # ids are known directly and ``variable_names`` lookup is bypassed.
        self._port_ids_override: Optional[Tuple[ElementID, ...]] = None
        # validate ports resolve in the body, eagerly
        missing = [p for p in self.ports if self._port_id(p) is None]
        if missing:
            raise ValueError(
                f"definition {name!r}: ports {missing} are not lines in the body"
            )

    @classmethod
    def from_egi(
        cls,
        name: str,
        port_ids: Sequence[ElementID],
        body_egi: RelationalGraphWithCuts,
        *,
        port_names: Optional[Sequence[str]] = None,
    ) -> "Definition":
        """A definition whose body is an already-built EGI (not EGIF text).

        The companion to the EGIF constructor for **authoring a definition from a
        drawn selection** (:func:`definition_from_selection`): the body is the
        induced sub-EGI re-rooted on its own sheet, and ``port_ids`` are the body
        vertices that the use-site arguments weld onto, in argument order.
        ``variable_names`` lookup is skipped — the port ids are given directly.
        """
        self = cls.__new__(cls)
        self.name = name
        self.ports = tuple(port_names) if port_names is not None else tuple(port_ids)
        self.body_egif = None
        self._body = body_egi
        self._port_ids_override = tuple(port_ids)
        return self

    @property
    def arity(self) -> int:
        return len(self.ports)

    @property
    def body(self) -> RelationalGraphWithCuts:
        if self._body is None:
            self._body = parse_egif(self.body_egif)
        return self._body

    def _port_id(self, name: str) -> Optional[ElementID]:
        for vid, vname in self.body.variable_names.items():
            if vname == name:
                return vid
        return None

    def port_ids(self) -> List[ElementID]:
        """The body vertex ids for ``self.ports``, in argument order."""
        if self._port_ids_override is not None:
            return list(self._port_ids_override)
        return [self._port_id(p) for p in self.ports]

    def __repr__(self) -> str:
        return f"Definition({self.name}/{self.arity})"


class DefinitionRegistry:
    """A set of definitions, keyed by relation name."""

    def __init__(self, definitions: Optional[Sequence[Definition]] = None):
        self._by_name: Dict[str, Definition] = {}
        for d in definitions or ():
            self.add(d)

    def add(self, definition: Definition) -> "DefinitionRegistry":
        if definition.name in self._by_name:
            raise ValueError(f"definition {definition.name!r} already registered")
        self._by_name[definition.name] = definition
        return self

    def get(self, name: str) -> Optional[Definition]:
        return self._by_name.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._by_name

    def names(self) -> List[str]:
        return list(self._by_name)


# A generous cap: any non-recursive expansion terminates well within it, so
# exceeding it means the definitions are (directly or indirectly) recursive.
_MAX_EXPANSIONS = 10_000


def _find_defined_edge(
    egi: RelationalGraphWithCuts, registry: DefinitionRegistry
) -> Optional[ElementID]:
    for eid, rel in egi.rel.items():
        if rel in registry:
            return eid
    return None


def expand(
    egi: RelationalGraphWithCuts, registry: DefinitionRegistry
) -> RelationalGraphWithCuts:
    """Replace **every** defined-relation edge in ``egi`` with its body,
    repeatedly, until only primitive relations remain — the fully-unfolded graph.

    This is the *whole-territory* operation: the result is the Borges 1:1 map,
    typically unreadable, and is meant for **verification only** (proving the
    folded form is a conservative abbreviation of a definite primitive graph —
    e.g. ``test_definitions`` checks a defined axiom is ``same_graph`` to the raw
    fixture).  It is NOT the working move: for reading and reasoning, keep the
    graph folded and use :func:`expand_at` / :func:`fold` to unfold a single spot
    locally and refold it immediately (see ``docs/DEFINITION_NODE.md``).

    Raises ``ValueError`` if expansion does not terminate within
    ``_MAX_EXPANSIONS`` steps — the signature of a recursive definition, which
    this layer does not support.
    """
    g = egi
    for _ in range(_MAX_EXPANSIONS):
        edge = _find_defined_edge(g, registry)
        if edge is None:
            return g
        g = expand_at(g, registry, edge)
    raise ValueError(
        "definition expansion did not terminate — recursive definitions are not "
        "supported by the definition layer (see module docstring)"
    )


@dataclass(frozen=True)
class FoldPoint:
    """The inverse data of one :func:`expand_at` — everything :func:`fold` needs
    to contract an unfolded body back to its named spot.

    ``body_elements`` are the host ids of the spliced-in body (the elements
    :func:`fold` removes); ``ports`` are the host lines the spot welds onto, in
    argument order (they survive the fold); ``area`` is where the named spot sits.
    """

    name: str
    ports: Tuple[ElementID, ...]
    area: ElementID
    body_elements: FrozenSet[ElementID]


def _edge_area(egi: RelationalGraphWithCuts, eid: ElementID) -> ElementID:
    for area_id, contents in egi.area.items():
        if eid in contents:
            return area_id
    return egi.sheet


def expand_at(
    egi: RelationalGraphWithCuts,
    registry: DefinitionRegistry,
    edge_id: ElementID,
    *,
    return_fold_point: bool = False,
):
    """Unfold **one** defined-relation spot in place — the local, reversible move.

    Replaces the single edge ``edge_id`` (whose relation must be defined in
    ``registry``) with the definition body, welding the body's ports onto the
    edge's incident lines.  Every other defined spot is left folded.  Pass
    ``return_fold_point=True`` to also get the :class:`FoldPoint` that
    :func:`fold` consumes to put the spot back (an exact inverse) — the
    fold/unfold pair the design requires so unfolding is always a local, undoable
    experiment, never a one-way slide to the 1:1 map.

    Raises ``ValueError`` if ``edge_id`` is not a defined-relation edge or its
    arity disagrees with the definition.
    """
    rel = egi.rel.get(edge_id)
    if rel is None or rel not in registry:
        raise ValueError(f"edge {edge_id!r} is not a defined-relation spot")
    defn = registry.get(rel)
    ports = tuple(egi.nu[edge_id])
    if len(ports) != defn.arity:
        raise ValueError(
            f"use of {defn.name!r} has arity {len(ports)}, definition has "
            f"{defn.arity}"
        )
    area = _edge_area(egi, edge_id)
    before = _all_ids(egi)
    g = splice(egi, edge_id, defn.body, ports=defn.port_ids())
    if not return_fold_point:
        return g
    body_elements = frozenset(_all_ids(g) - before)
    return g, FoldPoint(
        name=defn.name, ports=ports, area=area, body_elements=body_elements
    )


def fold(egi: RelationalGraphWithCuts, fold_point: FoldPoint) -> RelationalGraphWithCuts:
    """Contract an unfolded body back to its named spot — the exact inverse of
    :func:`expand_at`.

    Removes ``fold_point.body_elements`` (the spliced-in body, closed: a removed
    cut took its whole interior) and re-asserts a single ``fold_point.name`` edge
    on ``fold_point.ports`` in ``fold_point.area``.  ``fold(expand_at(g, e)) ==
    g`` up to ``same_graph`` (the refold edge gets a fresh id; the lines and area
    are unchanged).
    """
    drop = set(fold_point.body_elements)
    new_V = frozenset(v for v in egi.V if v.id not in drop)
    new_E = frozenset(e for e in egi.E if e.id not in drop)
    new_Cut = frozenset(c for c in egi.Cut if c.id not in drop)
    new_nu = frozendict({k: v for k, v in egi.nu.items() if k not in drop})
    new_rel = frozendict({k: v for k, v in egi.rel.items() if k not in drop})
    new_area = {a: (contents - drop) for a, contents in egi.area.items() if a not in drop}
    g = RelationalGraphWithCuts(
        V=new_V, E=new_E, nu=new_nu, sheet=egi.sheet, Cut=new_Cut,
        area=frozendict(new_area), rel=new_rel,
    )
    # Re-assert the named spot on the surviving port lines, in its original area.
    spot = Edge(id=f"e_fold_{fold_point.name}")
    return g.with_edge(spot, fold_point.ports, fold_point.name, fold_point.area)


def _area_depth(egi: RelationalGraphWithCuts, area: ElementID) -> int:
    depth, a = 0, area
    while a != egi.sheet:
        a = _edge_area(egi, a)
        depth += 1
    return depth


def _mark_ports(
    egi: RelationalGraphWithCuts, port_ids: Sequence[ElementID]
) -> RelationalGraphWithCuts:
    """A copy of ``egi`` whose port vertices carry positional constant labels,
    so an isomorphism test between two marked graphs is forced to align port i
    with port i (and to preserve each port's original label/genericity, folded
    into the mark)."""
    index = {p: i for i, p in enumerate(port_ids)}
    new_V = frozenset(
        Vertex(
            id=v.id,
            label=f"__port_{index[v.id]}__{v.label}",
            is_generic=False,
        )
        if v.id in index
        else v
        for v in egi.V
    )
    return replace(egi, V=new_V)


_BODY_SHEET = "_def_body_sheet"


def definition_from_selection(
    egi: RelationalGraphWithCuts,
    selection: Iterable[ElementID],
    ports: Sequence[ElementID],
    name: str,
) -> Definition:
    """Author a :class:`Definition` ``name(ports) := body`` from a live selection.

    The **abstraction front door**: name *this drawn subgraph* and reuse it as a
    single spot.  The body is the sub-structure on ``selection`` **re-rooted** on
    a fresh sheet — selected elements whose host parent is outside the selection
    become top-level in the body, nesting *within* the selection is preserved, and
    the designated ``ports`` (in argument order) are the body's free lines.

    The result feeds :func:`fold_selection` directly: because the body is the
    selection re-rooted, it is isomorphic to the selection by construction, so
    folding under it is sound (and re-checked by ``fold_selection``'s two gates).

    Raises ``ValueError`` if a selected edge references a vertex that is neither
    selected nor a port (the body would be open — make it a port or include it),
    or if the selection holds no edge/cut to abstract.
    """
    ports = tuple(ports)
    sel = frozenset(selection) | frozenset(ports)

    # Host parent (containing area) of each element.
    parent: Dict[ElementID, ElementID] = {}
    for area_id, contents in egi.area.items():
        for x in contents:
            parent[x] = area_id

    def body_parent(x: ElementID) -> ElementID:
        p = parent.get(x, egi.sheet)
        return p if p in sel else _BODY_SHEET

    sel_vertices = [v for v in egi.V if v.id in sel]
    sel_edges = [e for e in egi.E if e.id in sel]
    sel_cuts = [c for c in egi.Cut if c.id in sel]

    if not (sel_edges or sel_cuts):
        raise ValueError("selection holds nothing to abstract (no edge or cut)")

    # Every vertex a selected edge touches must be in the body (selected or port);
    # otherwise the abstraction would have a dangling line.
    for e in sel_edges:
        for vid in egi.nu.get(e.id, ()):
            if vid not in sel:
                raise ValueError(
                    f"selection edge {e.id!r} references vertex {vid!r} outside "
                    "the selection — include it in the selection or mark it a port"
                )

    # Re-rooted area map: each selected element under its host parent if that
    # parent is also selected, else under the fresh body sheet.
    body_area: Dict[ElementID, set] = {_BODY_SHEET: set()}
    for c in sel_cuts:
        body_area[c.id] = set()
    for x in sel:
        body_area.setdefault(body_parent(x), set()).add(x)

    body = RelationalGraphWithCuts(
        V=frozenset(sel_vertices),
        E=frozenset(sel_edges),
        nu=frozendict({e.id: tuple(egi.nu[e.id]) for e in sel_edges}),
        sheet=_BODY_SHEET,
        Cut=frozenset(sel_cuts),
        area=frozendict({k: frozenset(v) for k, v in body_area.items()}),
        rel=frozendict({e.id: egi.rel[e.id] for e in sel_edges}),
        rho=frozendict({k: v for k, v in egi.rho.items() if k in sel}),
    )
    return Definition.from_egi(name, port_ids=ports, body_egi=body)


def fold_selection(
    egi: RelationalGraphWithCuts,
    registry: DefinitionRegistry,
    name: str,
    selection: Iterable[ElementID],
    ports: Sequence[ElementID],
) -> RelationalGraphWithCuts:
    """Contract an arbitrary *selection* under definition ``name`` — the
    selection-driven front door to :func:`fold` (see ``docs/DEFINITION_NODE.md``
    "Open / next").  Where :func:`fold` consumes a :class:`FoldPoint` (the
    provenance of a just-performed :func:`expand_at`), this recognizes a drawn
    body wherever it came from: "fold *this selection* under definition D."

    Args:
        egi: the host graph.
        registry: where ``name`` is defined.
        name: the definition to fold under.
        selection: host element ids forming the candidate definition body
            (the port vertices may be included or omitted; they are counted in
            either way and survive the fold).
        ports: the host lines that become the spot's hooks, **in argument
            order** (aligned with the definition's ports).

    **Soundness gate (essential):** the sub-structure on ``selection`` must be
    isomorphic to the definition body with ``ports`` aligned to the
    definition's ports — folding a non-instance would be an unsound rewrite.
    Checked twice, by construction: (1) the selection is isomorphism-matched
    against the body via ``GraphIsomorphismEngine`` with both graphs'
    ports positionally marked (so the match cannot silently permute hooks);
    (2) after folding, the new spot is re-expanded with :func:`expand_at` and
    the result must be ``same_graph`` to the original — the exact-inverse
    round-trip, which also refuses selections whose internal lines leak edges
    outside the selection.  Raises ``ValueError`` on any failure.

    Returns the host with the selection contracted to a ``name`` spot.
    """
    defn = registry.get(name)
    if defn is None:
        raise ValueError(f"no definition named {name!r} in the registry")
    ports = tuple(ports)
    if len(ports) != defn.arity:
        raise ValueError(
            f"definition {name!r} has arity {defn.arity}, got {len(ports)} ports"
        )
    selection = frozenset(selection) | frozenset(ports)

    # Gate (1): iso-match the selection against the body, ports pinned.
    from graph_isomorphism_engine import GraphIsomorphismEngine

    body = defn.body
    body_ids = frozenset(_all_ids(body) - {body.sheet})
    result = GraphIsomorphismEngine().test_cross_egi_isomorphism(
        _mark_ports(egi, ports), selection,
        _mark_ports(body, defn.port_ids()), body_ids,
    )
    if not result.is_isomorphic:
        raise ValueError(
            f"selection is not an instance of {name!r} with the given port "
            f"alignment: {result.reason}"
        )

    # Build the FoldPoint: the spot sits where the body's top level sits — the
    # shallowest area among the internal (non-port) selection.  (A body whose
    # top level is a cut works the same way: the cut's own area is the host
    # area, its interior is deeper.)
    internal = selection - frozenset(ports)
    if not internal:
        raise ValueError("selection holds nothing to fold besides the ports")
    area = min(
        {_edge_area(egi, eid) for eid in internal},
        key=lambda a: _area_depth(egi, a),
    )
    folded = fold(
        egi,
        FoldPoint(name=name, ports=ports, area=area, body_elements=internal),
    )

    # Gate (2): the exact-inverse round-trip — unfolding the new spot must
    # reproduce the original graph.
    from eg_navigation import same_graph

    if not same_graph(expand_at(folded, registry, f"e_fold_{name}"), egi):
        raise ValueError(
            f"folding the selection under {name!r} is not reversible — the "
            "selection is not a clean instance (e.g. an internal line is used "
            "outside the selection)"
        )
    return folded


__all__ = [
    "Definition", "DefinitionRegistry", "definition_from_selection", "expand",
    "expand_at", "fold", "fold_selection", "FoldPoint",
]
