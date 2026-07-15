"""Render M — the ambient-model side of an Agon interpretation inning.

The interpretation register peels a proposal **G** against a reference model
**M** ([`docs/DOMAIN_ORACLE_AND_M.md`](../docs/DOMAIN_ORACLE_AND_M.md)). Until now
only G was drawn; M sat as a wall of raw EGIF text. This module supplies the two
*read-only, doctrine-clean* pieces the in-view-set design teed up
([`docs/THE_MINIMAL_IN_VIEW_SET.md`](../docs/THE_MINIMAL_IN_VIEW_SET.md) §11–12,
recommendations (c) + (d)) so a reader can see *what the terms mean* without
leaving the board:

  • **(d) the ground / legend** — `vocabulary_overlap`: G's vocabulary and M's,
    and how they meet (shared / G-only = the addressability gap / M-only = what M
    knows beyond G). The interpretive ground stated in words.

  • **(c) the relevant-neighborhood M-fragment** — `m_fragment`: draw only the
    part of M that G *touches* (the oracle's ego-graph slice), not all of M.
    Governed by Relevance (Sperber & Wilson) capped at a small budget (Cowan ~4
    chunks): seed = M's sheet atoms whose relation name or constant G uses, then
    one hop out to whatever else M says about *those individuals*. The rest is a
    **horizon** ("more of M lies here") — referenced, not drawn.

Both are the "fourth thing": navigation / chrome over attested objects, never a
corpus-promotion source, and they bear no actuality (no mark, no truth claim).
Kept pure — no web/layout imports — so it is unit-testable; the caller renders
the returned fragment EGI through the ordinary `generate_layout` path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Set

from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import parse_egif

# `ontology_signature(egi) -> set of relation names` (M's vocabulary), shared
# with the NL→logic reconcile path.
from dl_reasoning import ontology_signature

# A modest budget: a handful of atoms keeps the M-fragment within working memory
# (Cowan ~4 chunks; an atom is finer-grained than a chunk, so a few per chunk).
DEFAULT_FRAGMENT_BUDGET = 8


def _constants(egi: RelationalGraphWithCuts) -> Set[str]:
    """The constant (named-individual) labels an EGI mentions."""
    return {v.label for v in egi.V if (not v.is_generic and v.label)}


def vocabulary_overlap(g_egi: RelationalGraphWithCuts,
                       m_egi: RelationalGraphWithCuts) -> dict:
    """The ground / legend (d): G's and M's vocabularies and how they meet.

    `g_only_relations` is the **addressability gap** — terms G uses that M cannot
    speak to (the same notion as out-of-signature in the NL→logic reconcile).
    `m_only_relations` is **what M knows beyond G** — the context a reader needs.
    """
    g_rels, m_rels = ontology_signature(g_egi), ontology_signature(m_egi)
    g_consts, m_consts = _constants(g_egi), _constants(m_egi)
    return {
        "g": {"relations": sorted(g_rels), "constants": sorted(g_consts)},
        "m": {"relations": sorted(m_rels), "constants": sorted(m_consts)},
        "shared_relations": sorted(g_rels & m_rels),
        "shared_constants": sorted(g_consts & m_consts),
        "g_only_relations": sorted(g_rels - m_rels),
        "m_only_relations": sorted(m_rels - g_rels),
    }


@dataclass
class FragmentResult:
    """The M-fragment G touches, plus what was left at the horizon."""
    egi: Optional[RelationalGraphWithCuts]   # the drawn fragment (None if empty)
    egif: str                                # its linear form ("" if empty)
    shown: int                               # atoms drawn
    horizon: int                             # M sheet-atoms NOT drawn ("more lies here")
    nested: bool                             # M has cuts/structure not shown at all
    empty: bool                              # nothing in M touches G's vocabulary
    matched_relations: List[str] = field(default_factory=list)
    matched_constants: List[str] = field(default_factory=list)


def _sheet_atoms(egi: RelationalGraphWithCuts):
    """M's sheet-level atoms as (edge_id, relation, vertex-tuple, constant-labels)."""
    vmap = {v.id: v for v in egi.V}
    edge_ids = {e.id for e in egi.E}
    out = []
    for eid in egi.area.get(egi.sheet, ()):
        if eid not in edge_ids:
            continue
        verts = tuple(egi.nu[eid])
        rel = egi.get_relation_name(eid)
        consts = {vmap[v].label for v in verts
                  if (not vmap[v].is_generic and vmap[v].label)}
        out.append((eid, rel, verts, consts))
    return out, vmap


def _atom_egif(rel, verts, vmap, varname, seen) -> str:
    """One atom as EGIF; generics get `*x` on first appearance, `x` after."""
    parts = []
    for vid in verts:
        v = vmap[vid]
        if not v.is_generic and v.label:
            parts.append('"%s"' % v.label)
        else:
            name = varname[vid]
            parts.append((name if vid in seen else "*" + name))
            seen.add(vid)
    return "(" + rel + ((" " + " ".join(parts)) if parts else "") + ")"


def m_fragment(m_egi: RelationalGraphWithCuts,
               g_egi: RelationalGraphWithCuts,
               *, budget: int = DEFAULT_FRAGMENT_BUDGET) -> FragmentResult:
    """The relevant-neighborhood M-fragment (c): the part of M that G touches.

    Operates on M's **sheet-level atoms** — which is the whole of a flat fact
    model and of a *materialized* (forward-chained) theory; nested structure M
    keeps undrawn is reported via `nested` so the horizon stays honest.
    """
    from world_scroll import m_view

    # A world-scrolled M is read through its antecedent area (the validity
    # discipline); a legacy sheet-level M passes through unchanged.
    m_egi = m_view(m_egi)
    g_rels = ontology_signature(g_egi)
    g_consts = _constants(g_egi)
    atoms, vmap = _sheet_atoms(m_egi)
    total_sheet = len(atoms)
    nested = len(m_egi.area) > 1  # area keys = sheet + each cut

    # Seed: atoms whose relation G uses, or that mention an individual G mentions.
    seed = [a for a in atoms if (a[1] in g_rels) or (a[3] & g_consts)]
    seed_ids = {a[0] for a in seed}
    # The neighborhood reaches one hop out — to whatever else M says about those
    # same individuals (shared constant label) or along the same line of identity
    # (shared generic vertex). Both make M's ego-graph around G.
    touched_consts = set().union(*[a[3] for a in seed]) if seed else set()
    touched_vids = set().union(*[set(a[2]) for a in seed]) if seed else set()
    hop = [a for a in atoms if a[0] not in seed_ids
           and ((a[3] & touched_consts) or (set(a[2]) & touched_vids))]

    ordered = seed + hop
    kept = ordered[:budget]
    horizon = total_sheet - len(kept)

    matched_relations = sorted({a[1] for a in seed if a[1] in g_rels})
    kept_consts = set().union(*[a[3] for a in kept]) if kept else set()
    matched_constants = sorted(g_consts & kept_consts)

    if not kept:
        return FragmentResult(
            egi=None, egif="", shown=0, horizon=horizon, nested=nested,
            empty=True, matched_relations=matched_relations, matched_constants=[],
        )

    # Build the fragment's EGIF and re-parse to a valid EGI (the renderer's input).
    varname, seen, n = {}, set(), 0
    for _eid, _rel, verts, _consts in kept:
        for vid in verts:
            v = vmap[vid]
            if (v.is_generic or not v.label) and vid not in varname:
                varname[vid] = "x%d" % n
                n += 1
    egif = " ".join(_atom_egif(rel, verts, vmap, varname, seen)
                    for _eid, rel, verts, _consts in kept)
    try:
        frag_egi = parse_egif(egif)
    except Exception:
        # A fragment that won't round-trip is reported as text-only, never crashes
        # the inning; the legend + horizon still inform the reader.
        return FragmentResult(
            egi=None, egif=egif, shown=len(kept), horizon=horizon, nested=nested,
            empty=False, matched_relations=matched_relations,
            matched_constants=matched_constants,
        )

    return FragmentResult(
        egi=frag_egi, egif=egif, shown=len(kept), horizon=horizon, nested=nested,
        empty=False, matched_relations=matched_relations,
        matched_constants=matched_constants,
    )
