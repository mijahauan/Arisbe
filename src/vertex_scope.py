"""Place a vertex where its line of identity actually runs.

A line of identity between two areas traverses their **least common area**
only. A generic vertex says where it lives through its defining occurrence
(``*x`` in EGIF); a constant has no such occurrence, and in CLIF and CGIF a
bound variable has only a quantifier, whose scope is wider than the line. So a
parser that interns a vertex where it is *first mentioned* puts it in the wrong
area whenever the same individual is mentioned in more than one place.

The symptom is a scope error that survives every cheap check. In

    ~[ ~[ (P "x") ] ~[ (Q "x") ] ]

the vertex belongs in the outer cut, spanning both disjuncts; interned at first
mention it sits inside the first one. Same vertex count, same edge count,
byte-identical canonical text on re-emission — a different graph. In CLIF the
same error changes the *quantifier*, because a bound line's quantifier is read
off its context polarity: an existential interned inside a negation re-emits as
a universal.

**One line per constant.** A constant appearing in several spots is one line
of identity. This is a *normal form*, not a well-formedness law: two vertices
both naming Rex are not malformed, and say exactly what one vertex naming Rex
says, because a name denotes a single individual under any interpretation —
FOPL, Common Logic and the conceptual-graph reading all force that, and in
Peirce's own notation the repeated name is a *selective*, defined as an
abbreviation for the line. What the second vertex costs is writability: no
linear syntax distinguishes one line for a constant from two, so an
unnormalized graph cannot survive its own EGIF. ``normalize_constants`` picks
the one representative every linear form can carry.

The freedom is genuinely empty for constants and genuinely not for generic
lines. A constant vertex contributes "Rex exists", which is true under any
interpretation that gives every name a denotation, and a true conjunct is inert
at any depth; a generic line's area sets its quantifier's scope and polarity.
So multiplicity and placement are meaning for a generic line and normalization
leaves those alone. (This rests on names always denoting. Under a free logic,
where ``~[ "Rex" ]`` would deny that Rex exists, placement would become
load-bearing and this normal form would need revisiting.)

**Outward only.** A vertex is moved when its current area does not already
dominate every occurrence, and then only as far as the least common area. It is
never moved inward: the outermost specification of an individual establishes
its quantification, so hoisting past that would change what the graph says
rather than where it is drawn. An isolated vertex — no incident edge — is left
alone; there is nothing for it to be out of scope of.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from egi_core_dau import ElementID, RelationalGraphWithCuts

__all__ = ["hoist_vertices_to_lca", "normalize_constants", "constants_normalized"]


def _area_of(egi: RelationalGraphWithCuts, element: ElementID) -> Optional[ElementID]:
    for area_id, contents in egi.area.items():
        if element in contents:
            return area_id
    return None


def _ancestors(egi: RelationalGraphWithCuts, area: ElementID) -> List[ElementID]:
    """``area`` and every area enclosing it, innermost first, ending at the sheet."""
    chain = [area]
    current = area
    while current != egi.sheet:
        parent = _area_of(egi, current)
        if parent is None or parent == current:
            break
        chain.append(parent)
        current = parent
    return chain


def _least_common_area(
    egi: RelationalGraphWithCuts, areas: Set[ElementID]
) -> Optional[ElementID]:
    """The deepest area enclosing every area in ``areas``."""
    if not areas:
        return None
    chains = [_ancestors(egi, a) for a in areas]
    common = set(chains[0])
    for chain in chains[1:]:
        common &= set(chain)
    if not common:
        return egi.sheet
    # Deepest common ancestor: the one appearing earliest in any chain.
    for candidate in chains[0]:
        if candidate in common:
            return candidate
    return egi.sheet


def hoist_vertices_to_lca(
    egi: RelationalGraphWithCuts,
) -> RelationalGraphWithCuts:
    """Move each vertex outward to the least common area of its occurrences.

    Occurrences are read from incidence (``nu``), so this needs no bookkeeping
    from the parser that built the graph and can be applied to anything.
    """
    # A quoting name is pinned to its quotation cut: the B-min device requires
    # the two to sit in the same area, because that shared area *is* the drawn
    # attachment between the name and the ink it quotes. Moving the name
    # elsewhere would break the attachment even though the line's occurrences
    # might argue for a different home, so these are left where they are.
    pinned: Set[ElementID] = set(getattr(egi, "quotation", {}) .values())

    occurrences: Dict[ElementID, Set[ElementID]] = {}
    for edge_id, args in egi.nu.items():
        edge_area = _area_of(egi, edge_id)
        if edge_area is None:
            continue
        for vertex_id in args:
            occurrences.setdefault(vertex_id, set()).add(edge_area)

    for vertex_id, areas in occurrences.items():
        if vertex_id in pinned:
            continue
        current = _area_of(egi, vertex_id)
        if current is None:
            continue
        # Already in scope of every occurrence? Then it is where it belongs —
        # in particular a vertex sitting *outside* its uses stays put, because
        # that placement is what fixes its quantification.
        if all(current in _ancestors(egi, area) for area in areas):
            continue
        target = _least_common_area(egi, areas)
        if target is None or target == current:
            continue
        egi = egi.with_vertex_moved_to_context(vertex_id, target)
    return egi


def _constant_twins(egi: RelationalGraphWithCuts) -> Dict[ElementID, ElementID]:
    """Map each redundant constant vertex to the one line that survives it.

    Vertices are grouped by label, never by identity, because that is what the
    ruling turns on: the *name* is what makes two lines one. Generic vertices
    carry no name and are never grouped.
    """
    by_label: Dict[str, List[ElementID]] = {}
    for vertex in egi.V:
        if vertex.is_generic or vertex.label is None:
            continue
        by_label.setdefault(vertex.label, []).append(vertex.id)

    twins: Dict[ElementID, ElementID] = {}
    for ids in by_label.values():
        if len(ids) < 2:
            continue
        survivor, *rest = sorted(ids)
        for twin in rest:
            twins[twin] = survivor
    return twins


def constants_normalized(egi: RelationalGraphWithCuts) -> bool:
    """Does this graph hold at most one line of identity per constant?"""
    return not _constant_twins(egi)


def normalize_constants(
    egi: RelationalGraphWithCuts,
) -> RelationalGraphWithCuts:
    """Give each constant a single line of identity.

    Returns ``egi`` itself when it is already in normal form, so a caller can
    apply this at a boundary without churning graphs that do not need it.

    The merge is meaning-preserving (see the module docstring), so this is a
    choice of representative rather than a repair. It is applied where graphs
    are *constructed* — the drawing reader, the episode primitives that splice
    freshly parsed ink beside standing ink — and never inside the transformation
    rules, which are left exactly as Dau states them.
    """
    twins = _constant_twins(egi)
    if not twins:
        return egi

    # An edge reaching a twin has to be re-hung on the survivor, and the model
    # is immutable with no way to rewrite nu in place: drop those edges, drop
    # the twins, then restore the edges with their arguments redirected. Edge
    # objects and their areas are carried across unchanged, so only the
    # incidence moves.
    affected = [
        edge.id for edge in egi.E
        if any(v in twins for v in egi.nu.get(edge.id, ()))
    ]
    edges_by_id = {edge.id: edge for edge in egi.E}
    carried = [
        (
            edges_by_id[edge_id],
            tuple(twins.get(v, v) for v in egi.nu[edge_id]),
            egi.rel[edge_id],
            egi.get_context(edge_id),
        )
        for edge_id in affected
    ]

    result = egi
    for edge_id in affected:
        result = result.without_element(edge_id)
    for twin in sorted(twins):
        result = result.without_element(twin)
    for edge, arguments, relation, area in carried:
        result = result.with_edge(edge, arguments, relation, context_id=area)
    return result
