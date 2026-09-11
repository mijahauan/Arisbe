"""Refusal agreement (spec 2026-09-10 §5.1): the engine refuses exactly what
Dau forbids. Known disagreements live in calculus_ledger.json, each with its
reason; a new one fails here, and so does a repaired one."""
import pytest

from calculus_ledger import assert_extent, check_ledger
from calculus_run import run


def _agree(mode):
    lr = run(mode).layers["refusal"]
    problems = check_ledger("refusal", lr.evaluated_ledgered, lr.failures)
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
