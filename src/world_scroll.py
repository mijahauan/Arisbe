"""**The standing world-scroll — where M resides** (M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE
§3–§4 established the polarity shift; §9 — ratified 2026-07-16 — relocated M's
*elements* to cells at even depth).

Under the validity discipline nothing contingent stands at depth 0: the sheet is
the world's level, and it carries only what the calculus itself delivers. A domain
model M is what the players have **agreed functions as true in that context** — so
its elements reside in **cut-wrapped cells at level 2, siblings of the hold**::

    sheet:  ~[   ~[ facts · laws … ]   ~[ facts … ]   ~[ ]   ]
             │    └ a CELL: level 2,    └ another      └ a HOLD: empty
             │      POSITIVE — M's content lives here
             └ W: the world-scroll (level 1, negative)

The outer negation is vacuously true so long as **one empty cut** stands among its
contents, so the standing structure asserts nothing ("correspondence, not truth"
untouched). Empty cuts are one kind — the committal register — whether they are
the original hold or the emptied husk of a retracted cell (a *scar*: visible,
audit-legible, structurally indistinguishable from the hold, per verdict D3).

**Recognition is structural, never annotational** — the boundary that does logical
work must be drawn (the honest-picture principle). An annotation may *point*; only
ink decides.

**How M changes here** (the §9 asymmetry — the fallibilist pole):

* enlargement — :func:`enlarge_m`: **INS of a closed cell** ``~[ content ]`` into
  W (insertion is sound in a negative context) — one licensed move; each admitted
  batch is its own cell (verdict D2);
* retraction — :func:`retract_from_m`: **ERA inside a cell** (erasure is sound in
  a positive context, Dau's theorem) — one licensed move; the emptied husk stands;
  refutation-driven retraction and disuse-driven fading are the *same* move,
  distinguished by the step's recorded disposition (surprise vs entropy);
* full replacement — :func:`withdraw_and_resupply`: the rare case (a husk is a cut
  at odd depth, not ERA-licensed) — world-withdrawal, the ERA·DC+·INS triple.

**Reading M back** — :func:`m_view`: every consumer of M's content (oracle,
materializer, theory query, render) reads the **union of the cells' interiors**
when the residence is present and falls back to the sheet when it is not, so
bare sheet-level graphs (inline test fixtures, proposals) keep working unchanged.
Verdict semantics are untouched: the episode was always "given M, then G".

A corollary worth naming: from the blank sheet, **DC+ alone creates the empty
residence** ``~[ ~[ ] ]`` (W + hold, zero cells) — the arena of
``contest_context`` *is* the residence, and every supply after that is an
INS-of-cell. Construction is fully rule-licensed.

Additive, geometry-free, unprotected; every licensed move is an ordinary Dau rule
applied through ``proof_authoring.apply_rule``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from frozendict import frozendict

import eg_navigation as nav
from contest_context import open_arena, posit, Arena
from egi_core_dau import (
    ElementID,
    RelationalGraphWithCuts,
    create_cut,
    create_empty_graph,
)
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from proof_authoring import apply_rule


@dataclass(frozen=True)
class WorldScroll:
    """The standing residence M lives in: ``cut_id`` is W (level 1, negative);
    ``cell_ids`` are the non-empty child cuts (level 2, positive — M's content
    lives in their interiors); ``hold_ids`` are the empty child cuts (the
    committal register: the hold and any scars, one kind per verdict D3)."""

    cut_id: ElementID
    hold_ids: Tuple[ElementID, ...]
    cell_ids: Tuple[ElementID, ...]

    @property
    def hold_id(self) -> ElementID:
        """The first empty cut — kept for callers that name *the* hold; under
        D3 every empty cut keeps the vacuity equally."""
        return self.hold_ids[0]


# ---------------------------------------------------------------------------
# recognition
# ---------------------------------------------------------------------------

def find_world_scroll(egi: RelationalGraphWithCuts) -> Optional[WorldScroll]:
    """Recognize the standing residence, structurally.

    Matches iff the sheet's area holds **exactly one cut W and no edges**
    (isolated sheet vertices are tolerated — bare "something exists" is
    depth-0-legal per the inventory theorem), and W's area holds **only cuts,
    at least one of them empty**: the empty ones are holds/scars (vacuity), the
    non-empty ones are M's cells. A W-level edge or vertex is *not* the shape —
    that ink is the retired level-1 residence, left visible rather than
    misread — and the reader falls back to the sheet.
    """
    sheet_cuts = nav.child_cuts(egi, egi.sheet)
    if len(sheet_cuts) != 1:
        return None
    if nav.child_edges(egi, egi.sheet):
        return None
    w = sheet_cuts[0]
    if nav.child_edges(egi, w) or nav.child_vertices(egi, w):
        return None                       # content at level 1 — not the shape
    children = nav.child_cuts(egi, w)
    holds = tuple(c for c in children if not egi.get_area(c))
    cells = tuple(c for c in children if egi.get_area(c))
    if not holds:
        return None                       # no empty cut — the negation would bind
    return WorldScroll(cut_id=w, hold_ids=holds, cell_ids=cells)


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
    """The area of the residence: W when the world-scroll is present, else the
    sheet. Under cells there is no *single* area holding M's elements — use
    :func:`m_element_ids` / :func:`m_view` for content; this names the room."""
    scroll = find_world_scroll(egi)
    return scroll.cut_id if scroll else egi.sheet


def m_element_ids(egi: RelationalGraphWithCuts) -> frozenset:
    """The ids of M's own top-level content: the union of the cells' areas when
    the residence is present (holds/scars are chrome of the residence, never
    content), else the sheet's area."""
    scroll = find_world_scroll(egi)
    if scroll is None:
        return egi.get_area(egi.sheet)
    ids: set = set()
    for cell in scroll.cell_ids:
        ids |= set(egi.get_area(cell))
    return frozenset(ids)


def m_view(egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
    """**The one shared read primitive.** Identity for a sheet-level M; for a
    resident M, a fresh graph whose sheet holds the union of the cells'
    interiors — element ids preserved (the incremental materializer's rule
    cache and the oracle's provenance key on them), built structurally rather
    than by an EGIF round-trip (relation names like ``Warm-blooded`` must
    survive). Holds and scars are never copied; a law's cut-structure inside a
    cell reads as a sheet-level cut, keeping its Horn shape."""
    scroll = find_world_scroll(egi)
    if scroll is None:
        return egi
    view = create_empty_graph()
    # Two passes ACROSS the cells (shells of every cell before any edge): an
    # EGIF round-trip unifies a constant shared between cells into one vertex
    # scoped in the first cell that mentions it, so a later cell's edge may
    # reference a sibling-cell vertex — the copy must be total over those.
    for cell in scroll.cell_ids:
        view = _copy_shell(egi, view, cell, view.sheet)
    for cell in scroll.cell_ids:
        view = _copy_edges(egi, view, cell, view.sheet)
    return _carry_second_order_maps(egi, view)


def _copy_shell(
    src: RelationalGraphWithCuts,
    dst: RelationalGraphWithCuts,
    src_area: ElementID,
    dst_area: ElementID,
    *,
    skip: set = frozenset(),
) -> RelationalGraphWithCuts:
    """The *shell* pass of the id-preserving copy: every vertex and cut of
    ``src_area``'s subtree into ``dst_area`` (no edges yet)."""
    v_by_id = {v.id: v for v in src.V}
    c_by_id = {c.id: c for c in src.Cut}

    def walk(g, s_area, d_area):
        for vid in nav.child_vertices(src, s_area):
            if vid in skip:
                continue
            g = g.with_vertex_in_context(v_by_id[vid], d_area)
        for cid in nav.child_cuts(src, s_area):
            if cid in skip:
                continue
            g = g.with_cut(c_by_id[cid], context_id=d_area)
            g = walk(g, cid, cid)
        return g

    return walk(dst, src_area, dst_area)


def _copy_edges(
    src: RelationalGraphWithCuts,
    dst: RelationalGraphWithCuts,
    src_area: ElementID,
    dst_area: ElementID,
    *,
    skip: set = frozenset(),
) -> RelationalGraphWithCuts:
    """The *edge* pass of the id-preserving copy — run only after every shell
    an edge might reference has been copied."""
    e_by_id = {e.id: e for e in src.E}

    def walk(g, s_area, d_area):
        for eid in nav.child_edges(src, s_area):
            if eid in skip:
                continue
            g = g.with_edge(e_by_id[eid], src.nu[eid], src.rel[eid],
                            context_id=d_area)
        for cid in nav.child_cuts(src, s_area):
            if cid in skip:
                continue
            g = walk(g, cid, cid)
        return g

    return walk(dst, src_area, dst_area)


def _carry_second_order_maps(
    src: RelationalGraphWithCuts, result: RelationalGraphWithCuts
) -> RelationalGraphWithCuts:
    """B-min: carry the source's second-order maps for the copied elements
    (the with_* builders forward the destination's maps; the source's
    entries must ride along explicitly). A quotation entry carries only
    when both its oval and its quoting name landed in the copy — lifting
    an oval's interior alone yields the quoted graph itself, quotation-free."""
    copied_v = {v.id for v in result.V}
    copied_c = {c.id for c in result.Cut}
    new_sort = {
        vid: s
        for vid, s in src.sort.items()
        if vid in copied_v and vid not in result.sort
    }
    new_quot = {
        cid: vid
        for cid, vid in src.quotation.items()
        if cid in copied_c and vid in copied_v and cid not in result.quotation
    }
    if new_sort or new_quot:
        import dataclasses

        result = dataclasses.replace(
            result,
            sort=frozendict({**result.sort, **new_sort}),
            quotation=frozendict({**result.quotation, **new_quot}),
        )
    return result


def _copy_area(
    src: RelationalGraphWithCuts,
    dst: RelationalGraphWithCuts,
    src_area: ElementID,
    dst_area: ElementID,
    *,
    skip: set = frozenset(),
) -> RelationalGraphWithCuts:
    """Recursively copy ``src_area``'s contents into ``dst_area``, preserving
    element ids/objects. Two passes over the area tree: first the *shell*
    (every vertex and cut), then every edge. A well-scoped graph only needs
    vertices copied per-area before its edges, but some imported theories
    (e.g. the OWL pairwise-disjointness expansion, or a relationalised shared
    constant) carry an edge whose vertex sits in a *sibling* cut — the shell
    pass makes the copy total over those too, byte-identical on well-scoped
    graphs (ids and area assignments are preserved either way)."""
    result = _copy_edges(
        src, _copy_shell(src, dst, src_area, dst_area, skip=skip),
        src_area, dst_area, skip=skip)
    return _carry_second_order_maps(src, result)


def _lift_cut(egi: RelationalGraphWithCuts, cut_id: ElementID
              ) -> RelationalGraphWithCuts:
    """The cut's whole subtree as a standalone graph (ids preserved) — the
    local twin of ``quotation_overlay.lift_cut`` (kept here to avoid the
    import cycle; same ``_copy_area`` machinery)."""
    cut = next((c for c in egi.Cut if c.id == cut_id), None)
    if cut is None:
        raise ValueError(f"cut {cut_id!r} is not in the graph")
    view = create_empty_graph()
    view = view.with_cut(cut, context_id=view.sheet)
    return _copy_area(egi, view, cut_id, cut_id)


# ---------------------------------------------------------------------------
# construction and change — every licensed move a Dau rule
# ---------------------------------------------------------------------------

def wrap_m(m: RelationalGraphWithCuts
           ) -> Tuple[RelationalGraphWithCuts, WorldScroll]:
    """**The gapless inbound construction**: from a blank sheet, DC+ opens the
    residence (the empty double cut — W + hold, asserts nothing), and INS posits
    M as **one closed cell** in W's negative area (sound, fenced): the initial
    supply is one admitted batch (verdict D2). Takes M as a sheet-level graph;
    returns the wrapped graph and its scroll.

    Rule-licensed but *not* id-preserving (INS parses fresh); for the
    id-preserving structural adapter use :func:`wrap_state`."""
    m_egif = generate_egif(m).strip()
    g, arena = open_arena(create_empty_graph())
    if m_egif:
        g = posit(g, arena, f"~[ {m_egif} ]")
    scroll = find_world_scroll(g)
    assert scroll is not None, "wrap_m must construct the recognized residence"
    return g, scroll


def wrap_state(egi: RelationalGraphWithCuts
               ) -> Tuple[RelationalGraphWithCuts, WorldScroll]:
    """**The post-hoc adapter**: re-house an existing sheet-level M inside a
    fresh residence *structurally*, preserving every element id (so a chain of
    states wrapped one by one keeps its cross-state identity): DC+ opens W and
    the hold, a fresh cell cut is added beside the hold, and the sheet's
    contents are copied into the cell. Not a rule application — used only to
    retrofit legacy states, and callers must record that honestly
    (``earned: false``)."""
    scroll = find_world_scroll(egi)
    if scroll is not None:
        return egi, scroll
    g, arena = open_arena(create_empty_graph())
    cell = create_cut()
    g = g.with_cut(cell, context_id=arena.arena)
    g = _copy_area(egi, g, egi.sheet, cell.id)
    scroll = find_world_scroll(g)
    assert scroll is not None, "wrap_state must construct the recognized residence"
    return g, scroll


def enlarge_m(egi: RelationalGraphWithCuts, egif: str
              ) -> RelationalGraphWithCuts:
    """**Enlargement — one licensed move.** INS the content as a **closed
    cell** ``~[ content ]`` into W (a negative context, where insertion is
    unconditionally sound): to add to M is to admit another batch of agreed
    content, landing at even depth where retraction will be a licensed ERA.
    The warrant justifies the *choice* (recorded on the chain step, not
    carried by the ink)."""
    scroll = find_world_scroll(egi)
    if scroll is None:
        raise ValueError(
            "no standing world-scroll to enlarge — M is not resident "
            "(wrap it first: wrap_m / wrap_state)")
    return apply_rule("INS", egi, egif=f"~[ {egif.strip()} ]",
                      target=scroll.cut_id)


def retract_from_m(
    egi: RelationalGraphWithCuts,
    *,
    subgraph_egif: Optional[str] = None,
    relation: Optional[str] = None,
    labels: Optional[List[Optional[str]]] = None,
) -> Tuple[RelationalGraphWithCuts, List[str]]:
    """**Retraction — one licensed move** (the §9 fallibilist pole). ERA the
    matching element(s) *inside a cell* — even depth, positive, where erasure
    is sound (Dau's theorem). The emptied husk stands as a scar; the DAG keeps
    the prior state; ERA never denies the utterance.

    Two forms, combinable in one call:

    * ``subgraph_egif`` — a law / negation *cut* inside a cell: the first cell
      child whose lifted subtree is ``same_graph`` to the parsed target is
      erased as a unit (cut closure takes the subtree).
    * ``relation`` (+ optional exact ``labels``) — atom-level: every matching
      cell-level fact is erased, each its own ERA; an argument vertex private
      to an erased atom goes with it (the for-erasure closure), a shared vertex
      stays.

    Returns the new graph and the executed derivation (one ``"ERA"`` per rule
    application). Raises ``ValueError`` when nothing matches (a retraction must
    have something to retract) and when an erasure would take more than the
    matched element + its private vertices (a cross-cell ligature — surface it,
    never silently erase more)."""
    scroll = find_world_scroll(egi)
    if scroll is None:
        raise ValueError("no standing world-scroll to retract from — M is not resident")
    if subgraph_egif is None and relation is None:
        raise ValueError("retract_from_m needs subgraph_egif and/or relation")

    g = egi
    derivation: List[str] = []

    if subgraph_egif is not None:
        shape = parse_egif(subgraph_egif)
        target_cut = None
        for cell in scroll.cell_ids:
            for cut_id in nav.child_cuts(g, cell):
                try:
                    if nav.same_graph(_lift_cut(g, cut_id), shape):
                        target_cut = cut_id
                        break
                except Exception:
                    continue
            if target_cut:
                break
        if target_cut is None:
            raise ValueError(
                f"no cell-level subgraph matching {subgraph_egif!r} to retract")
        g = apply_rule("ERA", g, selection=[target_cut])
        derivation.append("ERA")
        scroll = find_world_scroll(g)
        if scroll is None:      # cannot happen: ERA inside a cell keeps the shape
            raise ValueError("retraction broke the residence shape — refusing")

    if relation is not None:
        want = tuple(labels) if labels is not None else None
        matches = []
        for e in g.E:
            area = g.get_context(e.id)
            if area not in scroll.cell_ids:
                continue
            if g.rel.get(e.id) != relation:
                continue
            if want is not None:
                got = tuple(g.get_vertex(v).label for v in g.nu.get(e.id, ()))
                if got != want:
                    continue
            matches.append(e.id)
        if not matches:
            raise ValueError(
                f"no cell-level fact {relation}{want if want is not None else ''} "
                "to retract")
        for eid in matches:
            args = list(dict.fromkeys(g.nu.get(eid, ())))
            private = {
                v for v in args
                if not any(v in inc for e2, inc in g.nu.items() if e2 != eid)
            }
            before_ids = ({v.id for v in g.V} | {e.id for e in g.E}
                          | {c.id for c in g.Cut})
            g = apply_rule("ERA", g, selection=[eid])
            after_ids = ({v.id for v in g.V} | {e.id for e in g.E}
                         | {c.id for c in g.Cut})
            removed = before_ids - after_ids
            expected = {eid} | private
            if removed - expected:
                raise ValueError(
                    f"retracting {relation} atom {eid} would erase more than the "
                    f"atom and its private vertices ({sorted(removed - expected)}) "
                    "— a cross-cell ligature; retract the wider content explicitly")
            derivation.append("ERA")

    return g, derivation


def _fresh_double_cut(egi: RelationalGraphWithCuts, area: ElementID
                      ) -> Tuple[RelationalGraphWithCuts, ElementID, ElementID]:
    """DC+ into ``area``; returns (graph, outer_cut_id, inner_cut_id)."""
    from presentation_ops import cut_parents
    before = {c.id for c in egi.Cut}
    g = apply_rule("DC+", egi, target=area)
    fresh = [c.id for c in g.Cut if c.id not in before]
    parents = cut_parents(g)
    outer = next(c for c in fresh if parents.get(c) == area)
    inner = next(c for c in fresh if c != outer)
    return g, outer, inner


def _find_exhibit(
    egi: RelationalGraphWithCuts,
    scroll: WorldScroll,
    proposal_egif: str,
) -> Tuple[ElementID, ElementID, ElementID, List[ElementID]]:
    """Locate a standing episode exhibit for ``proposal_egif``: a cut in some
    cell's area whose own area holds an empty cut (the rider), a cut whose
    subtree is ``same_graph`` to ``~[ proposal ]`` (the entertained candidate),
    and (possibly) the iterated M′ copies. Returns
    ``(host_cell, outer, rider, copy_ids)`` or raises ``ValueError``."""
    def _matches(c: ElementID, shape) -> bool:
        # a cut whose subtree is not self-contained (an iterated copy's line
        # of identity reaching an outside vertex) simply never matches — the
        # same guard as quotation_overlay.find_cut_matching
        try:
            return nav.same_graph(_lift_cut(egi, c), shape)
        except Exception:
            return False

    shape = parse_egif(f"~[ {proposal_egif.strip()} ]")
    for cell in scroll.cell_ids:
        for outer in nav.child_cuts(egi, cell):
            inner_cuts = nav.child_cuts(egi, outer)
            riders = [c for c in inner_cuts if not egi.get_area(c)]
            cands = [c for c in inner_cuts
                     if egi.get_area(c) and _matches(c, shape)]
            if not riders or not cands:
                continue
            rider, cand = riders[0], cands[0]
            copies = [x for x in egi.get_area(outer)
                      if x not in (rider, cand)
                      and x not in {v.id for v in egi.V}]
            return cell, outer, rider, sorted(copies)
    raise ValueError(
        f"no standing episode exhibit for {proposal_egif!r} — entertain it first")


def entertain_episode(
    egi: RelationalGraphWithCuts, proposal_egif: str, *,
    cell: Optional[ElementID] = None,
) -> Tuple[RelationalGraphWithCuts, List[str]]:
    """**Entertain "if M then P" as ink** (M_RESIDENCE §10): inside the agreed
    context (a cell's area, even depth) build the episode exhibit

        ~[  M′  ~[ P ]  ~[ ]  ]

    by three licensed moves — **DC+** (the arena, odd, + the empty inner cut),
    **IT+** of the host cell's content into the arena (inward — the premise is
    M's own ink, identity-preserved), **INS** of ``~[ P ]`` into the negative
    arena. The empty inner cut is the **vacuity rider**: it keeps the pending
    exhibit vacuously true, so the contingent conditional is *entertained*,
    drawn and contestable, while the standing structure asserts nothing.

    Returns the new graph and the executed derivation
    ``["DC+", "IT+"×k, "INS"]``. ``cell`` picks the host (default: the first
    cell); under per-admission cells the iterated premise is the *host cell's*
    content — the episode names which agreed batch it draws on."""
    scroll = find_world_scroll(egi)
    if scroll is None:
        raise ValueError("no standing world-scroll — M is not resident")
    if not scroll.cell_ids:
        raise ValueError("the residence has no cells — nothing to entertain against")
    host = cell if cell is not None else sorted(scroll.cell_ids)[0]
    if host not in scroll.cell_ids:
        raise ValueError(f"{host!r} is not a cell of the residence")

    g, outer, _inner = _fresh_double_cut(egi, host)
    derivation = ["DC+"]
    # Iterate the host cell's top-level edges and cuts into the arena (vertices
    # ride with their edges — lines of identity extend inward; an isolated
    # vertex is iterated explicitly).
    vertex_ids = {v.id for v in g.V}
    used = {v for inc in g.nu.values() for v in inc}
    for eid in sorted(set(g.get_area(host)) - {outer}):
        if eid in vertex_ids and eid in used:
            continue
        g = apply_rule("IT+", g, selection=[eid], target=outer)
        derivation.append("IT+")
    g = apply_rule("INS", g, egif=f"~[ {proposal_egif.strip()} ]", target=outer)
    derivation.append("INS")
    assert find_world_scroll(g) is not None
    return g, derivation


def discharge_episode(
    egi: RelationalGraphWithCuts, proposal_egif: str, *,
    cell: Optional[ElementID] = None,
) -> Tuple[RelationalGraphWithCuts, List[str]]:
    """**Discharge a confirmed episode** — drawn modus ponens (M_RESIDENCE §10;
    FIDELITY §3b corollary 3: a fact reaches an even area *derived, never
    inserted*): **IT−** the iterated M′ copies (the warrant emptied against the
    original one level up), **IT−** the vacuity rider (licensed against the
    residence's standing hold — an identical empty cut in an enclosing area),
    **DC−** the now-clean double cut — P's ink lands at the level of the
    original M, in the agreed context.

    LICENSE IS NOT CERTIFICATION (the ⊥-door, §10): the standing hold is ⊥
    among W's conjuncts, so this sequence is licensed whether or not the
    episode was confirmed — under ruling (b) the calculus stays pure and the
    *earning* rides on the record: ``m_steps.discharge_step`` refuses to record
    a discharge without a confirming PEEL to cite, and the polarity gate
    re-asserts the citation. Returns ``(graph, executed derivation)``."""
    scroll = find_world_scroll(egi)
    if scroll is None:
        raise ValueError("no standing world-scroll — M is not resident")
    host, outer, rider, copies = _find_exhibit(egi, scroll, proposal_egif)
    if cell is not None and host != cell:
        raise ValueError(f"the exhibit for {proposal_egif!r} stands in {host!r}, "
                         f"not {cell!r}")
    g = egi
    derivation: List[str] = []
    for eid in sorted(copies, reverse=True):
        g = apply_rule("IT-", g, selection=[eid])
        derivation.append("IT-")
    g = apply_rule("IT-", g, selection=[rider])
    derivation.append("IT-")
    g = apply_rule("DC-", g, selection=[outer])
    derivation.append("DC-")
    assert find_world_scroll(g) is not None
    return g, derivation


def abandon_episode(
    egi: RelationalGraphWithCuts, proposal_egif: str, *,
    cell: Optional[ElementID] = None,
) -> Tuple[RelationalGraphWithCuts, List[str]]:
    """**Abandon a refuted (or withdrawn) episode**: ERA the whole exhibit cut —
    it stands in a cell's area (even, positive), so erasure is one licensed
    move. The DAG keeps the entertained state; ERA never denies the utterance."""
    scroll = find_world_scroll(egi)
    if scroll is None:
        raise ValueError("no standing world-scroll — M is not resident")
    host, outer, _rider, _copies = _find_exhibit(egi, scroll, proposal_egif)
    if cell is not None and host != cell:
        raise ValueError(f"the exhibit for {proposal_egif!r} stands in {host!r}, "
                         f"not {cell!r}")
    g = apply_rule("ERA", egi, selection=[outer])
    assert find_world_scroll(g) is not None
    return g, ["ERA"]


def withdraw_and_resupply(
    egi: RelationalGraphWithCuts, new_m_egif: str
) -> Tuple[RelationalGraphWithCuts, List[str]]:
    """**Full replacement = world-withdrawal** — the rare case under cells
    (piecemeal retraction is :func:`retract_from_m`; this remains for replacing
    the whole residence, including its husks, which are cuts at odd depth and
    not ERA-licensed):

        ERA [W]   — the residence sits in the positive sheet area: legal, sound, free
        DC+       — open a fresh residence (asserts nothing)
        INS       — posit the amended M as one closed cell

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
        g = posit(g, arena, f"~[ {new_m_egif} ]")
    return g, ["ERA", "DC+", "INS"]


__all__ = [
    "WorldScroll", "find_world_scroll", "is_ligature_closed",
    "m_area", "m_element_ids", "m_view",
    "wrap_m", "wrap_state", "enlarge_m", "retract_from_m",
    "entertain_episode", "discharge_episode", "abandon_episode",
    "withdraw_and_resupply",
]
