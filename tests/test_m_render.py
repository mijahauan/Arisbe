"""Render M — the ambient-model side of an Agon interpretation inning.

Tests the two read-only pieces of `src/m_render.py` (the in-view-set design's
recommendations (d) + (c), docs/THE_MINIMAL_IN_VIEW_SET.md §11–12):

* `vocabulary_overlap` (d) — the ground/legend: G's and M's vocabularies and how
  they meet (shared / G-only addressability gap / M-only beyond-G context).
* `m_fragment` (c) — the relevant-neighborhood: draw only the part of M that G
  touches (seed by shared relation/individual, one hop along same-individual /
  same-line), the rest left at a reported horizon, capped at a budget.
"""

from egif_parser_dau import parse_egif
from egi_core_dau import RelationalGraphWithCuts
from dl_reasoning import ontology_signature
from m_render import vocabulary_overlap, m_fragment


def _consts(egi):
    return {v.label for v in egi.V if (not v.is_generic and v.label)}


# --- (d) the ground / legend -------------------------------------------------

def test_vocabulary_overlap_splits_shared_gonly_monly():
    m = parse_egif('(Mammal "Whale") (Aquatic "Whale") (Bird "Robin")')
    g = parse_egif('(Mammal "Whale") (Dragon "Whale")')
    vo = vocabulary_overlap(g, m)
    assert vo["shared_relations"] == ["Mammal"]
    assert "Whale" in vo["shared_constants"]
    # Dragon: G uses it, M cannot address it — the addressability gap.
    assert vo["g_only_relations"] == ["Dragon"]
    # M knows Aquatic/Bird beyond what G says — the context.
    assert set(vo["m_only_relations"]) == {"Aquatic", "Bird"}


# --- (c) the relevant-neighborhood M-fragment --------------------------------

def test_fragment_keeps_what_g_touches_and_one_hop():
    m = parse_egif('(Mammal "Whale") (Aquatic "Whale") (Bird "Robin")')
    g = parse_egif('(Mammal "Whale")')
    fr = m_fragment(g_egi=g, m_egi=m)
    assert not fr.empty
    # Mammal(Whale) is the seed (relation + individual); Aquatic(Whale) is one hop
    # out (same individual). Bird(Robin) is untouched → horizon.
    assert fr.shown == 2 and fr.horizon == 1
    assert fr.matched_relations == ["Mammal"] and fr.matched_constants == ["Whale"]
    assert fr.egi is not None
    assert ontology_signature(fr.egi) == {"Mammal", "Aquatic"}
    assert _consts(fr.egi) == {"Whale"}


def test_fragment_empty_when_vocabulary_is_alien():
    m = parse_egif('(Mammal "Whale") (Bird "Robin")')
    g = parse_egif('(Dragon "Smaug")')
    fr = m_fragment(g_egi=g, m_egi=m)
    assert fr.empty and fr.egi is None and fr.shown == 0
    # The whole of M is at the horizon — nothing of it is drawn.
    assert fr.horizon == 2


def test_fragment_follows_a_line_of_identity_one_hop():
    # M: one generic line through two predicates; G touches P → Q comes along.
    m = parse_egif("(P *x) (Q x) (R *y)")
    g = parse_egif("(P *z)")
    fr = m_fragment(g_egi=g, m_egi=m)
    assert not fr.empty and fr.shown == 2  # P and Q (shared line); R untouched
    assert fr.horizon == 1
    assert ontology_signature(fr.egi) == {"P", "Q"}


def test_fragment_respects_budget_and_reports_horizon():
    atoms = " ".join('(Knows "Whale" "n%d")' % i for i in range(12))
    m = parse_egif(atoms)
    g = parse_egif('(Knows "Whale" "n0")')
    fr = m_fragment(g_egi=g, m_egi=m, budget=4)
    assert fr.shown == 4 and fr.horizon == 8
    assert fr.egi is not None


def test_fragment_flags_nested_structure_left_undrawn():
    m = parse_egif('(Mammal "Whale") ~[ (Secret "Whale") ]')
    g = parse_egif('(Mammal "Whale")')
    fr = m_fragment(g_egi=g, m_egi=m)
    assert fr.nested is True   # the cut's content is not drawn at the sheet level
    assert fr.shown == 1       # only the sheet atom Mammal(Whale) is in the slice
