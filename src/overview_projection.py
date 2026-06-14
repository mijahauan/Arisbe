"""
Overview projection — collapse deep cuts into content-sized placeholders.

The adaptive-scope viewer's deferred *core* (``docs/ADAPTIVE_SCOPE_VIEWER.md``):
a navigation projection that draws only the part of an EGI the reader is looking
at and **collapses the rest into placeholders**, so the drawn graph the layout
engine actually lays out stays small no matter how large the underlying EGI is —
the answer to the layout-perf frontier (ELK is super-linear in nesting depth).

The construction is a **quotient EGI**: ``collapse_quotient(egi, collapsed)``
removes every collapsed cut's hidden subtree and keeps each *frontier* collapsed
cut as a **leaf placeholder**. The one subtlety is a **boundary ligature** — a
line of identity from a vertex *outside* a collapsed cut to a predicate *hidden
inside* it (a vertex always sits at the outermost area its line reaches, so the
hidden element is the *edge*, the visible one the *vertex*). Each such incidence
is represented in the quotient by a **synthetic unary boundary predicate** placed
inside the placeholder, connected to the visible vertex. That keeps the quotient a
valid ``RelationalGraphWithCuts`` *and* makes the ordinary §3.3 correspondence
check (`correspondence_attestation.check_correspondence`) verify the boundary
line's crossing and endpoint for free — the line really does cross into the
placeholder exactly once and terminate there. A synthetic predicate is anonymous
(it leaks neither the hidden relation's name nor its joins), so the placeholder
honestly shows only "a line enters here", never the interior.

Everything here is **read-only and additive** — it never mutates ``egi`` and
produces a *derived* structure used purely for viewing and attestation. The
canonical (fully-expanded) drawing is still governed by full §3.3; an overview is
the weaker, honestly-labelled ``attest_overview`` (in
``correspondence_attestation``).

See also ``eg_structure.subtree_summary`` (the badge counts) and
``docs/ADAPTIVE_SCOPE_VIEWER.md`` (the attestation contract + the membrane /
no-mark-bears-actuality guardrail a placeholder obeys).
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Set, Tuple

from frozendict import frozendict

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts
from eg_structure import subtree_summary

# The relation name worn by a synthetic boundary predicate.  Anonymous on
# purpose: a placeholder shows *that* a line enters, never *what* it connects to
# inside.  (A middle dot — visually a small spot the client can style as a cap.)
BOUNDARY_REL = "·"


def _parent_map(egi: RelationalGraphWithCuts) -> Dict[ElementID, ElementID]:
    """Map every element id to the context (sheet or cut) that directly holds it."""
    parent: Dict[ElementID, ElementID] = {}
    for ctx, children in egi.area.items():
        for ch in children:
            parent[ch] = ctx
    return parent


def _collapsed_ancestor(
    eid: ElementID,
    parent: Dict[ElementID, ElementID],
    collapsed: Set[ElementID],
    sheet: ElementID,
) -> ElementID | None:
    """The *outermost* collapsed cut that strictly contains ``eid`` (its
    placeholder), or ``None`` if ``eid`` is not hidden.  Walking root-ward and
    keeping the last collapsed hit yields the outermost one — the cut actually
    drawn as a placeholder."""
    outermost = None
    cur = parent.get(eid)
    while cur is not None and cur != sheet:
        if cur in collapsed:
            outermost = cur
        cur = parent.get(cur)
    return outermost


def frontier_placeholders(
    egi: RelationalGraphWithCuts, collapsed: Iterable[ElementID]
) -> Set[ElementID]:
    """The collapsed cuts actually drawn as placeholders: those with **no**
    collapsed ancestor (a collapsed cut nested inside another collapsed cut is
    itself hidden, never drawn)."""
    collapsed = set(collapsed)
    parent = _parent_map(egi)
    return {
        c for c in collapsed
        if _collapsed_ancestor(c, parent, collapsed, egi.sheet) is None
    }


def _subtree_element_ids(
    egi: RelationalGraphWithCuts, cut_id: ElementID
) -> Set[ElementID]:
    """Every element id (vertices, edges, cuts) strictly inside ``cut_id``."""
    cut_ids = {c.id for c in egi.Cut}
    inside: Set[ElementID] = set()
    stack: List[ElementID] = list(egi.area.get(cut_id, frozenset()))
    while stack:
        e = stack.pop()
        if e in inside:
            continue
        inside.add(e)
        if e in cut_ids:
            stack.extend(egi.area.get(e, frozenset()))
    return inside


def boundary_incidences(
    egi: RelationalGraphWithCuts, cut_id: ElementID
) -> List[Tuple[ElementID, int, ElementID]]:
    """The boundary ligatures of ``cut_id``: ``(edge_id, port_index, vertex_id)``
    for every hook of an edge **inside** ``cut_id`` to a vertex **outside** it.

    A vertex sits at the outermost area its line reaches, so a vertex outside the
    cut wired to an edge inside it is the only boundary shape; an edge inside the
    cut wired to a vertex inside it is fully internal (summarised, not drawn).
    Independent of any other collapse — a property of ``cut_id`` alone."""
    inside = _subtree_element_ids(egi, cut_id)
    out: List[Tuple[ElementID, int, ElementID]] = []
    for e in egi.E:
        if e.id not in inside:
            continue  # edge outside the cut: not entering it
        for port, vid in enumerate(egi.nu.get(e.id, ())):
            if vid not in inside:
                out.append((e.id, port, vid))
    return out


def boundary_degree(egi: RelationalGraphWithCuts, cut_id: ElementID) -> int:
    """How many lines of identity cross into ``cut_id`` (drawn boundary lines)."""
    return len(boundary_incidences(egi, cut_id))


def synthetic_boundary_id(cut_id: ElementID, edge_id: ElementID, port: int) -> ElementID:
    """Deterministic id of the synthetic boundary predicate standing in for the
    hidden edge ``edge_id``'s ``port``-th hook at placeholder ``cut_id``.  The
    server and the attestation derive the same id, so a served overview DTO and
    its check agree."""
    return f"{cut_id}__bnd__{edge_id}__{port}"


def overview_summary(
    egi: RelationalGraphWithCuts, collapsed: Iterable[ElementID]
) -> Dict[ElementID, dict]:
    """The honest badge for each frontier placeholder: the recursive content
    counts (``eg_structure.subtree_summary``), recto/verso polarity, and the
    boundary degree.  All are exact functions of ``egi`` — *form*, never
    actuality (``docs/MANIFEST_AND_MEANING.md`` floor #6)."""
    parent = _parent_map(egi)
    out: Dict[ElementID, dict] = {}
    for c in frontier_placeholders(egi, collapsed):
        depth = 0
        cur = c
        while cur is not None and cur != egi.sheet:
            cur = parent.get(cur)
            depth += 1
        summary = subtree_summary(egi, c)
        out[c] = {
            "cuts": summary["cuts"],
            "vertices": summary["vertices"],
            "predicates": summary["predicates"],
            "polarity": "negative" if depth % 2 == 1 else "positive",
            "boundary_degree": boundary_degree(egi, c),
        }
    return out


def collapse_quotient(
    egi: RelationalGraphWithCuts, collapsed: Iterable[ElementID]
) -> RelationalGraphWithCuts:
    """The quotient EGI for an overview at the given collapsed-cut set.

    Hidden subtrees are removed; each frontier collapsed cut is kept as a leaf
    placeholder holding one **synthetic unary boundary predicate** per boundary
    incidence (wired to the visible vertex outside).  The result is a valid
    ``RelationalGraphWithCuts`` whose §3.3 correspondence with a drawing attests
    the whole *visible* part — including that each boundary line crosses into its
    placeholder exactly once and terminates there.

    Raises ``ValueError`` if any id in ``collapsed`` is not a cut of ``egi``.
    """
    collapsed = set(collapsed)
    cut_ids = {c.id for c in egi.Cut}
    bad = collapsed - cut_ids
    if bad:
        raise ValueError(f"collapse_quotient: not cuts of egi: {sorted(bad)}")

    parent = _parent_map(egi)

    def placeholder_of(eid: ElementID) -> ElementID | None:
        return _collapsed_ancestor(eid, parent, collapsed, egi.sheet)

    def hidden(eid: ElementID) -> bool:
        return placeholder_of(eid) is not None

    placeholders = frontier_placeholders(egi, collapsed)

    # Kept structural elements: anything not hidden.  A frontier placeholder is
    # kept (drawn) even though it is collapsed; a nested collapsed cut is hidden.
    kept_vertices = [v for v in egi.V if not hidden(v.id)]
    kept_edges = [e for e in egi.E if not hidden(e.id)]
    kept_cuts = [c for c in egi.Cut if (not hidden(c.id)) and c.id not in collapsed]
    kept_cuts += [c for c in egi.Cut if c.id in placeholders]

    new_V = set(kept_vertices)
    new_E = list(kept_edges)
    new_Cut = set(kept_cuts)
    new_nu: Dict[ElementID, Tuple[ElementID, ...]] = {
        e.id: tuple(egi.nu.get(e.id, ())) for e in kept_edges
    }
    new_rel: Dict[ElementID, str] = {
        e.id: egi.get_relation_name(e.id) for e in kept_edges
    }

    # area: keep each kept element in its original (open) context; place each
    # frontier placeholder's synthetic boundary predicates inside it.
    kept_ids = {v.id for v in kept_vertices} | {e.id for e in kept_edges} \
        | {c.id for c in kept_cuts}
    new_area: Dict[ElementID, Set[ElementID]] = {}
    for ctx in [egi.sheet] + [c.id for c in kept_cuts]:
        new_area[ctx] = {x for x in egi.area.get(ctx, frozenset()) if x in kept_ids}

    # Synthetic boundary predicates — one per boundary incidence into each
    # placeholder, wired to the (kept) visible vertex.
    for c in placeholders:
        for edge_id, port, vid in boundary_incidences(egi, c):
            sid = synthetic_boundary_id(c, edge_id, port)
            new_E.append(Edge(id=sid))
            new_nu[sid] = (vid,)
            new_rel[sid] = BOUNDARY_REL
            new_area[c].add(sid)

    kept_vertex_ids = {v.id for v in new_V}
    return RelationalGraphWithCuts(
        V=frozenset(new_V),
        E=frozenset(new_E),
        nu=frozendict(new_nu),
        sheet=egi.sheet,
        Cut=frozenset(new_Cut),
        area=frozendict({k: frozenset(v) for k, v in new_area.items()}),
        rel=frozendict(new_rel),
        rho=frozendict({k: v for k, v in egi.rho.items() if k in kept_vertex_ids}),
    )


__all__ = [
    "BOUNDARY_REL",
    "boundary_degree",
    "boundary_incidences",
    "collapse_quotient",
    "frontier_placeholders",
    "overview_summary",
    "synthetic_boundary_id",
]
