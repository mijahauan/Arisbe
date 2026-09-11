"""Refusal agreement (spec 2026-09-10 §5.1): the engine refuses exactly what
Dau forbids. Known disagreements live in calculus_ledger.json, each with its
reason; a new one fails here, and so does a repaired one."""
import pytest

from calculus_ledger import assert_extent, check_ledger
from calculus_run import run


def _agree(mode):
    lr = run(mode).layers["refusal"]
    problems = check_ledger("refusal", lr.evaluated_ledgered, lr.failures, mode)
    assert not problems, "\n\n".join(problems)


def _extent(mode):
    r = run(mode)
    assert_extent(f"{mode}:run", r.extent())
    assert_extent(f"{mode}:refusal", dict(sorted(r.layers["refusal"].counts.items())))


def test_key_separates_a_target_that_is_selected():
    """Task 6 review: signing the target alone merged an illegal move (IT+ of a
    cut into itself, Def 15.2 p.164: c ∉ Cut₀) with a legal sibling."""
    from calculus_ledger import instance_key
    from calculus_rules import Move
    from canonical_signature import compute_canonical_signatures
    from egif_parser_dau import parse_egif

    g = parse_egif("~[ ] ~[ ]")
    c1, c2 = sorted(c.id for c in g.Cut)
    sigs = compute_canonical_signatures(g)
    key = lambda t: instance_key("A", "g", g, Move("IT+", (c1,), t), sigs)  # noqa: E731
    assert key(c1) != key(c2)


def test_key_separates_a_selection_by_its_incidences():
    """Task 10 ruling: signing the selection as a multiset merged ERA{e1,v1}
    (an edge with its own vertex: legal) with ERA{e1,v2} (an edge and a
    stranger's vertex: the stranger's edge would dangle) in (P *x) (P *y)."""
    from calculus_ledger import instance_key
    from calculus_rules import Move, legal
    from canonical_signature import compute_canonical_signatures
    from egif_parser_dau import parse_egif

    g = parse_egif("(P *x) (P *y)")
    e1 = sorted(g.nu)[0]
    own, = g.nu[e1]
    other, = (v.id for v in g.V if v.id != own)
    sigs = compute_canonical_signatures(g)
    a, b = Move("ERA", (e1, own)), Move("ERA", (e1, other))
    assert legal(g, a)[0] is True and legal(g, b)[0] is False
    assert instance_key("A", "g", g, a, sigs) != instance_key("A", "g", g, b, sigs)


def test_key_separates_a_target_that_encloses_the_selection():
    """Task 10: in ~[ (p) ] ~[ (p) ], DC+{e1}→c1 (e1's own context: legal) and
    DC+{e1}→c2 (a sibling cut: the selection is not directly in it) shared a
    key while the target was signed only by its relation to the selection."""
    from calculus_enum import build
    from calculus_ledger import instance_key
    from calculus_rules import Move, legal
    from canonical_signature import compute_canonical_signatures

    # built directly, as tier A builds it: EGIF has no 0-ary relation syntax
    g = build({"c1": "S", "c2": "S"}, [], [("p", (), "c1"), ("p", (), "c2")])
    e1, own, other = "e1", "c1", "c2"
    sigs = compute_canonical_signatures(g)
    a, b = Move("DC+", (e1,), own), Move("DC+", (e1,), other)
    assert legal(g, a)[0] is True and legal(g, b)[0] is False
    assert instance_key("A", "g", g, a, sigs) != instance_key("A", "g", g, b, sigs)


def test_key_separates_a_selection_by_its_common_context():
    """Task 10 (exhaustive tier B): two edges have no incidence between them, so
    {R, Q} in one cut and {Q, R'} across sibling cuts (R and R' alike) shared a
    key; the pair's lowest common context now separates them."""
    from calculus_enum import build
    from calculus_ledger import instance_key
    from calculus_rules import Move
    from canonical_signature import compute_canonical_signatures

    g = build({"c1": "S", "c2": "S"}, [], [("r", (), "c1"), ("q", (), "c1"), ("r", (), "c2")])
    sigs = compute_canonical_signatures(g)
    key = lambda sel: instance_key("A", "g", g, Move("DC+", sel, "S"), sigs)  # noqa: E731
    assert key(("e1", "e2")) != key(("e2", "e3"))


def test_key_separates_a_target_within_the_source_context():
    """Task 10 (exhaustive tier B, episode_discharge:s2): IT+ of one selection
    into two alike empty cuts — one within the selection's context, one in a
    sibling branch — shared a key; the target now records where its chain
    meets each selected element's context."""
    from calculus_enum import build
    from calculus_ledger import instance_key
    from calculus_rules import Move, legal
    from canonical_signature import compute_canonical_signatures

    g = build({"c1": "S", "c2": "S", "c3": "c1", "c4": "c1", "c5": "c2"}, [], [])
    sigs = compute_canonical_signatures(g)
    vs, es, cs = sigs
    assert cs["c4"] == cs["c5"]       # alike empty cuts, one under c1 and one under c2
    a, b = Move("IT+", ("c3",), "c4"), Move("IT+", ("c3",), "c5")
    assert legal(g, a)[0] is True and legal(g, b)[0] is False
    assert instance_key("A", "g", g, a, sigs) != instance_key("A", "g", g, b, sigs)


def test_refusal_agreement():
    _agree("default")


def test_refusal_extent():
    _extent("default")


@pytest.mark.exhaustive
def test_refusal_agreement_exhaustive():
    _agree("exhaustive")


@pytest.mark.exhaustive
def test_refusal_extent_exhaustive():
    _extent("exhaustive")
