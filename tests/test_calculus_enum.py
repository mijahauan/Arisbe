"""Tier-A enumeration: built directly, de-duplicated up to isomorphism, shape-complete.

Spec 2026-09-10 §3.1. The old EGIF strategy never offered an empty cut or a
zero-arity relation; these tests make the enumerator prove it offers every
shape the calculus must meet, and that it counts what it discarded.
"""
import eg_navigation as nav
from calculus_enum import (
    DEFAULT_BOUNDS, REQUIRED_SHAPES, Bounds, dedupe, graph_key, lca,
    line_above_uses, shapes, tier_a,
)
from egif_parser_dau import parse_egif


def test_every_required_shape_occurs_in_the_default_slice():
    report = tier_a(DEFAULT_BOUNDS)
    seen = set()
    for _, g in report.graphs:
        seen |= shapes(g)
    assert REQUIRED_SHAPES <= seen, f"missing shapes: {sorted(REQUIRED_SHAPES - seen)}"


def test_no_two_kept_graphs_are_isomorphic():
    report = tier_a(Bounds(max_cuts=1, max_edges=1, max_generics=1,
                           constants=("a",), max_constant_spots=1, max_elements=3,
                           relations=(("P", 1),)))
    gs = [g for _, g in report.graphs]
    for i in range(len(gs)):
        for j in range(i + 1, len(gs)):
            assert not nav.same_graph(gs[i], gs[j])


def test_dedupe_merges_isomorphic_graphs_with_different_ids():
    a = parse_egif("(P *x) ~[ (P x) ]")
    b = parse_egif("(P *y) ~[ (P y) ]")
    kept, dups, key_only = dedupe([("a", a), ("b", b)])
    assert (len(kept), dups, key_only) == (1, 1, 0)
    assert graph_key(a) == graph_key(b)


def test_counts_add_up():
    r = tier_a(DEFAULT_BOUNDS)
    assert r.built == r.refused_by_core + r.duplicates + len(r.graphs)


def test_every_kept_graph_has_dominating_nodes():
    # Dau Def 12.5 is part of what an EGI is (Def 12.7).
    #
    # This comment used to end "since the core would not refuse one", and that
    # was the test's whole justification. It stopped being true at d20b700,
    # which enforces Def 12.5 in the core constructor — the proof is thirty
    # lines up in this very file, where `TierAReport.refused_by_core` counts the
    # ValueError the core raises. A kept graph is one that survived
    # construction, so it has dominating nodes *by construction* and this
    # assertion can no longer fail.
    #
    # Kept anyway, and honestly labelled: it is now a cheap agreement check
    # between the core's enforcement and tarski's independent reading of Def
    # 12.5, and it would bite if enforcement were removed without this file
    # being revisited. What it is NOT is the last line of defence it claims.
    # `refused_by_core` is the number to watch (0 at default bounds: the
    # enumerator builds no violator here), and it is pinned in the extent.
    from tarski import dominating_nodes
    assert all(dominating_nodes(g) for _, g in tier_a(DEFAULT_BOUNDS).graphs)


def test_line_above_uses_is_detected():
    g = parse_egif("[*x] ~[ (P x) ]")
    v = next(iter(g.V)).id
    assert line_above_uses(g, v)
    h = parse_egif("~[ (P *x) ]")
    assert not line_above_uses(h, next(iter(h.V)).id)


def test_lca_of_one_area_is_itself():
    g = parse_egif("~[ (P *x) ]")
    c = next(iter(g.Cut)).id
    assert lca(g, [c]) == c


def test_the_stress_tier_carries_the_shapes_tier_a_cannot():
    from calculus_enum import tier_s
    from tarski import dominating_nodes
    graphs = dict(tier_s())
    assert set(graphs) == {
        "scroll-with-a-line", "deiteration-across-two-cuts", "arguments-swapped",
        "theta-linked-copy", "parity-depth-3", "parity-depth-4",
        "alphabet-and-quotation", "name-against-name", "edge-insertion-target",
        "theta-in-one-context",
    }
    assert all(dominating_nodes(g) for g in graphs.values())
    # every one is beyond the default tier-A bound of 3 elements
    assert all(len(g.V) + len(g.E) + len(g.Cut) > 3 for g in graphs.values())
    # the one shape no linear form carries: B-min maps, so the maps clause bites.
    # `q.alphabet is not None` is no longer a claim about this graph — since
    # 2026-09-24 the core derives an alphabet for every graph — so what is
    # asserted is what maps_carried actually reads on it: a sort and a
    # quotation. (Its rho is all-∗: the clause's rho half is exercised by the
    # constant-bearing graphs of tiers A and B.)
    q = graphs["alphabet-and-quotation"]
    assert q.sort and q.quotation and all(c is None for c in q.rho.values())


def test_the_stress_tier_makes_move_branches_apply_somewhere():
    """Why theta-in-one-context is in the tier, stated as a guard rather than a
    comment. Before it, the default mode had NO graph on which MOVE_BRANCHES
    applies at all — every candidate was refused — so the layers measured the
    rule's refusals and nothing else, and it took the exhaustive run over the
    corpus to find the rule unsound. A rule whose every move is refused is a
    rule nothing is testing. Here Θ genuinely holds (Def 15.1, p.163: x, y and
    the identity edge joining them share one context, so clause 3's
    ctx(e_i) = ctx(v_{i+1}) is satisfied), the engine applies the move, legal()
    judges it legal, and it is an equivalence."""
    from calculus_apply import apply_move
    from calculus_enum import tier_s
    from calculus_rules import legal, moves
    g = dict(tier_s())["theta-in-one-context"]
    applied = [m for m in moves("MOVE_BRANCHES", g, "S") if apply_move(g, m).applied]
    assert applied, "MOVE_BRANCHES applies on no tier-S graph: the rule is unmeasured"
    assert all(legal(g, m)[0] for m in applied), "applied here, but legal() does not judge it legal"


def test_tier_b_covers_every_uod_and_every_chain_state():
    from calculus_enum import TOMOS, tier_b
    from calculus_ledger import assert_extent
    from tomos_service import TomosService
    svc = TomosService(TOMOS)
    uods = [u["uod_id"] for u in svc.list_uods()]
    states = sum(len(c.states) for c in map(svc.load_chain, uods) if c)
    r = tier_b(include_chains=True)
    assert r.sources == len(uods) + states
    assert r.sources == r.duplicates + len(r.graphs)
    assert tier_b(include_chains=False).sources == len(uods)
    assert_extent("tier_b", r.extent())


def test_every_corpus_graph_is_an_egi():
    """Task 10 ruling: a standing guard. Dau Def 12.7 (p.126) makes dominating
    nodes (Def 12.5, p.125) part of what an EGI is; every tier-B source — each
    UoD's current graph and every chain state — is held to it, and the known
    violators are ledgered.

    **What this test buys has changed, and the docstring is corrected rather
    than left flattering (2026-09-21, clause 3 of the admission gate).** It used
    to read "the core does not enforce it and its own check is inverted, so
    nothing else in the repository would catch a stored non-EGI". Both halves
    were true when written and both are now false: `9482d2c` fixed the inverted
    `has_dominating_nodes`, and `d20b700` enforces Def 12.5 in the constructor.

    The consequence is that the failure path below is unreachable. Tier-B
    sources arrive through `svc.load_uod` / `svc.load_chain`, i.e. through the
    core constructor, so a stored non-EGI now raises a ValueError at *load* —
    `dominating_violations(g)` never sees one, `failures` is structurally empty,
    and the legible per-graph ledger report this test advertises cannot be
    produced. A stored non-EGI would surface as an exception escaping the
    fixture (and would redden much of the suite), not as the finding named here.

    It is kept, because two things it does are still real and still load-bearing:
    the whole corpus is proved *loadable* at all, and `assert_extent` pins
    `sources` at 230 — so a silently dropped UoD or chain state is caught. The
    `corpus-egi` ledger is empty and its machinery is kept for the same reason
    `KNOWN_BROKEN`'s is: were enforcement ever relaxed, this reports it legibly
    instead of as a stack trace."""
    from calculus_enum import dominating_violations, tier_b_sources
    from calculus_ledger import Failure, assert_extent, check_ledger, ledgered
    from tarski import dominating_nodes
    known = ledgered("corpus-egi")
    failures, evaluated, bad_states = [], set(), 0
    sources = tier_b_sources(include_chains=True)
    for name, g in sources:
        key = f"B|{name}|graph"
        if key in known:
            evaluated.add(key)
        bad = dominating_violations(g)
        assert bool(bad) == (not dominating_nodes(g))
        if bad:
            bad_states += not name.endswith(":current")
            failures.append(Failure("corpus-egi", key, f"not an EGI (Def 12.5): {len(bad)} "
                                    f"edge-vertex pair(s) on {len({v for _, v in bad})} vertex(es)"))
    problems = check_ledger("corpus-egi", evaluated, failures)
    assert not problems, "\n\n".join(problems)
    assert_extent("corpus-egi", {"sources": len(sources), "not_an_egi": len(failures),
                                 "not_an_egi_chain_states": bad_states})
