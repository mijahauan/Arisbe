"""**The standing world-scroll — where M resides** (the polarity shift of
M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE §3–§4, made operational).

Under the validity discipline nothing contingent stands at depth 0: the sheet is
the world's level, and it carries only what the calculus itself delivers. A domain
model M is a *supposition* — so it lives at level 1, the antecedent area of a
standing scroll::

    sheet:  ~[  M-facts  M-law-scrolls   ~[ ]  ]
             └ W: the world-scroll (level 1, negative) — M's residence
                                          └ H: the hold (level 2, positive) — empty

The empty hold matters twice over. ``~[ M ]`` alone would *deny* M; ``~[ M ~[ ] ]``
is a scroll with a blank consequent — vacuously true, logically inert — which is
exactly what a standing supposition should assert: nothing. And the hold is the
committal area where a conclusion may one day be drawn (``contest_context.Arena``
is this same shape; the world-scroll is a standing arena).

**Recognition is structural, never annotational** — the boundary that does logical
work must be drawn (the honest-picture principle). An annotation may *point*; only
ink decides.

**How M changes here** (the §4 asymmetry flip):

* enlargement — :func:`enlarge_m`: **INS** into level 1, a genuine Dau rule
  (insertion is sound in a negative context — you may always suppose more);
* relinquishment — :func:`withdraw_and_resupply`: **not** piecemeal erasure
  (erasing from an antecedent *strengthens* the conditional — unsound at odd
  depth) but world-withdrawal: **ERA** the whole scroll (it sits in the positive
  sheet area), **DC+** a fresh one, **INS** the amended M. The DAG keeps the
  withdrawn world as a prior state.

**Reading M back** — :func:`m_view` / :func:`m_area`: every consumer of M's
content (oracle, materializer, theory query, render) reads the antecedent area
when the scroll is present and falls back to the sheet when it is not, so
legacy sheet-level Ms (the live loops, inline test fixtures) keep working
unchanged. Verdict semantics are untouched: the episode was always
"given M, then G".

Additive, geometry-free, unprotected; every licensed move is an ordinary Dau rule
applied through ``proof_authoring.apply_rule``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import eg_navigation as nav
from contest_context import open_arena, posit, Arena
from egi_core_dau import (
    ElementID,
    RelationalGraphWithCuts,
    create_empty_graph,
)
from egif_generator_dau import generate_egif
from proof_authoring import apply_rule


@dataclass(frozen=True)
class WorldScroll:
    """The standing scroll M resides in: ``cut_id`` is W (level 1, negative —
    the antecedent area holding M), ``hold_id`` is H (level 2, positive — the
    empty committal area)."""

    cut_id: ElementID
    hold_id: ElementID


# ---------------------------------------------------------------------------
# recognition
# ---------------------------------------------------------------------------

def find_world_scroll(egi: RelationalGraphWithCuts) -> Optional[WorldScroll]:
    """Recognize the standing world-scroll, structurally.

    Matches iff the sheet's area holds **exactly one cut W and no edges**
    (isolated vertices are tolerated — bare "something exists" is depth-0-legal
    per the inventory theorem), and W's area holds **exactly one empty cut H**
    (H's area is entirely empty). Anything else — several sheet cuts, a sheet
    edge, no empty cut in W, or several — is *not* the shape, and the reader
    falls back to the sheet: an ambiguous scroll is left visible rather than
    misread.
    """
    sheet_cuts = nav.child_cuts(egi, egi.sheet)
    if len(sheet_cuts) != 1:
        return None
    if nav.child_edges(egi, egi.sheet):
        return None
    w = sheet_cuts[0]
    empty_cuts = [c for c in nav.child_cuts(egi, w) if not egi.get_area(c)]
    if len(empty_cuts) != 1:
        return None
    return WorldScroll(cut_id=w, hold_id=empty_cuts[0])


def is_ligature_closed(egi: RelationalGraphWithCuts, scroll: WorldScroll) -> bool:
    """No line of identity crosses W's boundary: every vertex used by an edge
    inside W's full context is itself inside it. The withdrawal ERA needs this
    (Dau's for-erasure closure refuses a boundary-crossing cut), so builders
    must keep it and the corpus gate asserts it."""
    inside = set(egi.get_full_context(scroll.cut_id))
    for edge_id in inside:
        if edge_id in egi.nu:
            if any(v not in inside for v in egi.nu[edge_id]):
                return False
    return True


# ---------------------------------------------------------------------------
# reading M
# ---------------------------------------------------------------------------

def m_area(egi: RelationalGraphWithCuts) -> ElementID:
    """The area M's content lives in: W if the world-scroll is present, else
    the sheet — the backward-compatibility seam every reader goes through."""
    scroll = find_world_scroll(egi)
    return scroll.cut_id if scroll else egi.sheet


def m_element_ids(egi: RelationalGraphWithCuts) -> frozenset:
    """The ids of M's own top-level content: W's area minus the hold when
    scrolled (the empty hold is chrome of the residence, not a denial in M),
    else the sheet's area."""
    scroll = find_world_scroll(egi)
    if scroll is None:
        return egi.get_area(egi.sheet)
    return frozenset(egi.get_area(scroll.cut_id) - {scroll.hold_id})


def m_view(egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
    """**The one shared read primitive.** Identity for a sheet-level M; for a
    world-scrolled M, a fresh graph whose sheet holds W's contents minus the
    hold — element ids preserved (the incremental materializer's rule cache and
    the oracle's provenance key on them), built structurally rather than by an
    EGIF round-trip (relation names like ``Warm-blooded`` must survive)."""
    scroll = find_world_scroll(egi)
    if scroll is None:
        return egi
    view = create_empty_graph()
    return _copy_area(egi, view, scroll.cut_id, view.sheet,
                      skip={scroll.hold_id})


def _copy_area(
    src: RelationalGraphWithCuts,
    dst: RelationalGraphWithCuts,
    src_area: ElementID,
    dst_area: ElementID,
    *,
    skip: set = frozenset(),
) -> RelationalGraphWithCuts:
    """Recursively copy ``src_area``'s contents into ``dst_area``, preserving
    element ids/objects. Per area: vertices first, then edges (their vertices
    are in the same or an enclosing area, already copied), then cuts."""
    v_by_id = {v.id: v for v in src.V}
    e_by_id = {e.id: e for e in src.E}
    c_by_id = {c.id: c for c in src.Cut}

    def walk(g, s_area, d_area):
        for vid in nav.child_vertices(src, s_area):
            if vid in skip:
                continue
            g = g.with_vertex_in_context(v_by_id[vid], d_area)
        for eid in nav.child_edges(src, s_area):
            if eid in skip:
                continue
            g = g.with_edge(e_by_id[eid], src.nu[eid], src.rel[eid],
                            context_id=d_area)
        for cid in nav.child_cuts(src, s_area):
            if cid in skip:
                continue
            g = g.with_cut(c_by_id[cid], context_id=d_area)
            g = walk(g, cid, cid)
        return g

    return walk(dst, src_area, dst_area)


# ---------------------------------------------------------------------------
# construction and change — every licensed move a Dau rule
# ---------------------------------------------------------------------------

def wrap_m(m: RelationalGraphWithCuts
           ) -> Tuple[RelationalGraphWithCuts, WorldScroll]:
    """**The gapless inbound construction** (Departure II's DC+ · INS nesting):
    from a blank sheet, DC+ opens the standing scroll (asserts nothing), INS
    posits M into its negative antecedent area (sound, fenced). Takes M as a
    sheet-level graph; returns the wrapped graph and its scroll.

    Rule-licensed but *not* id-preserving (INS parses fresh); for the
    id-preserving structural adapter use :func:`wrap_state`."""
    m_egif = generate_egif(m).strip()
    g, arena = open_arena(create_empty_graph())
    if m_egif:
        g = posit(g, arena, m_egif)
    return g, WorldScroll(cut_id=arena.arena, hold_id=arena.hold)


def wrap_state(egi: RelationalGraphWithCuts
               ) -> Tuple[RelationalGraphWithCuts, WorldScroll]:
    """**The post-hoc adapter**: re-house an existing sheet-level M inside a
    fresh world-scroll *structurally*, preserving every element id (so a chain
    of states wrapped one by one keeps its cross-state identity). Not a rule
    application — used only to retrofit states produced by the legacy loop,
    and callers must record that honestly (``earned: false``)."""
    if find_world_scroll(egi) is not None:
        scroll = find_world_scroll(egi)
        return egi, scroll
    g, arena = open_arena(create_empty_graph())
    g = _copy_area(egi, g, egi.sheet, arena.arena)
    return g, WorldScroll(cut_id=arena.arena, hold_id=arena.hold)


def enlarge_m(egi: RelationalGraphWithCuts, egif: str
              ) -> RelationalGraphWithCuts:
    """**Enlargement — a genuine rule at last.** INS the content into W (a
    negative context, where insertion is unconditionally sound): to add to M
    is to suppose more. This is the polarity flip paying off — the old
    ``assert_fact`` juxtaposition needed a warrant *instead of* a rule; this
    needs the rule, and the warrant justifies the *choice* (recorded on the
    chain step, not carried by the ink)."""
    scroll = find_world_scroll(egi)
    if scroll is None:
        raise ValueError(
            "no standing world-scroll to enlarge — M is not resident at level 1 "
            "(wrap it first: wrap_m / wrap_state)")
    return apply_rule("INS", egi, egif=egif, target=scroll.cut_id)


def withdraw_and_resupply(
    egi: RelationalGraphWithCuts, new_m_egif: str
) -> Tuple[RelationalGraphWithCuts, List[str]]:
    """**Relinquishment = world-withdrawal** (the §4 asymmetry): you cannot
    un-suppose a premise piecemeal (ERA at odd depth is unsound — it would
    *strengthen* the conditional), so the whole supposition is withdrawn and an
    amended one supplied:

        ERA [W]   — the scroll sits in the positive sheet area: legal, sound, free
        DC+       — open a fresh standing scroll (asserts nothing)
        INS       — posit the amended M into its antecedent area

    Executed with real rule applications; returns the new graph and the
    derivation ``["ERA", "DC+", "INS"]``. The withdrawn world is not destroyed:
    the caller's chain keeps the prior state — the DAG remembers."""
    scroll = find_world_scroll(egi)
    if scroll is None:
        raise ValueError("no standing world-scroll to withdraw")
    g = apply_rule("ERA", egi, selection=[scroll.cut_id])
    g, arena = open_arena(g)
    new_m_egif = new_m_egif.strip()
    if new_m_egif:
        g = posit(g, arena, new_m_egif)
    return g, ["ERA", "DC+", "INS"]


__all__ = [
    "WorldScroll", "find_world_scroll", "is_ligature_closed",
    "m_area", "m_element_ids", "m_view",
    "wrap_m", "wrap_state", "enlarge_m", "withdraw_and_resupply",
]
