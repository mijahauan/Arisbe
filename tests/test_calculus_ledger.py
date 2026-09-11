"""The ledger check itself (spec 2026-09-10 §6; Task 10 ruling 1): every
guarantee is shown to bite on hand-built failures before its silence on the
engine means anything. The ledger file is swapped for a temporary one."""
import json

import pytest

import calculus_ledger
from calculus_ledger import Failure, check_ledger

HEAVY = "heavy-dot-negative-only"          # any real refusal classifier id will do
INC = "INCOMPLETE refused but legal (any context); engine: no"
SEV = "SEVERE applied but illegal — legal says: no"


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    path = tmp_path / "ledger.json"
    monkeypatch.setattr(calculus_ledger, "LEDGER", path)

    def write(instances=None, counts=None):
        path.write_text(json.dumps({"entries": [{
            "id": HEAVY, "layer": "refusal", "rule": "VERTEX_INS", "classifier": HEAVY,
            "reason": "test", "instances": instances or {}, "counts": counts or {}}]}))
    return write


def f(key, detail=INC, claims=(HEAVY,)):
    return Failure("refusal", key, detail, claims)


def test_counts_hold_when_equal(ledger):
    ledger(counts={"exhaustive": {"INCOMPLETE": 2}})
    assert check_ledger("refusal", set(), [f("k1"), f("k2"), f("k2")], "exhaustive") == []


def test_a_count_that_rises_fails(ledger):
    ledger(counts={"exhaustive": {"INCOMPLETE": 2}})
    problems = check_ledger("refusal", set(), [f("k1"), f("k2"), f("k3")], "exhaustive")
    assert len(problems) == 1 and "ROSE" in problems[0]


def test_a_count_that_falls_is_shrink(ledger):
    ledger(counts={"exhaustive": {"INCOMPLETE": 2}})
    problems = check_ledger("refusal", set(), [f("k1")], "exhaustive")
    assert len(problems) == 1 and "SHRINK" in problems[0]


def test_unclaimed_or_other_kind_is_new(ledger):
    ledger(counts={"exhaustive": {"INCOMPLETE": 1}})
    problems = check_ledger("refusal", set(),
                            [f("k1"), f("k2", claims=()), f("k3", detail=SEV)], "exhaustive")
    assert any("2 NEW" in p for p in problems)


def test_two_claims_are_reported(ledger):
    ledger(counts={"exhaustive": {"INCOMPLETE": 1}})
    problems = check_ledger("refusal", set(), [f("k1", claims=(HEAVY, "other"))], "exhaustive")
    assert any("claimed by two classifiers" in p for p in problems)


def test_instances_kind_flip_is_new_and_stale(ledger):
    ledger(instances={"INCOMPLETE": ["k1"]})
    problems = check_ledger("refusal", {"k1"}, [f("k1", detail=SEV)])
    assert any("NEW" in p and "kind flipped" in p for p in problems)
    assert any("no longer fail" in p for p in problems)


def test_instances_hold_and_shrink(ledger):
    ledger(instances={"INCOMPLETE": ["k1", "k2"]})
    assert check_ledger("refusal", {"k1"}, [f("k1")]) == []
    problems = check_ledger("refusal", {"k1", "k2"}, [f("k1")])
    assert len(problems) == 1 and "shrink this entry" in problems[0]


def test_instances_catch_classifier_drift(ledger):
    ledger(instances={"INCOMPLETE": ["k1"]})
    problems = check_ledger("refusal", {"k1"}, [f("k1", claims=())])
    assert any("classifier does not claim" in p for p in problems)


def test_an_it_minus_move_above_the_pattern_ceiling_is_counted_not_applied(monkeypatch):
    """Task 10: IT-'s VF2 search does not finish on patterns of 124+ elements;
    records() skips a move whose expanded selection exceeds the ceiling and
    counts it, rather than timing it out."""
    import calculus_run
    from egif_parser_dau import parse_egif
    g = parse_egif("(P *x) ~[ ~[ (P *y) (Q y) ] ]")
    monkeypatch.setattr(calculus_run, "ENGINE_PATTERN_CEILING", {"IT-": 1})
    monkeypatch.setattr(calculus_run, "graphs_for", lambda mode, tier: [("g", g)] if tier == "A" else [])
    tally = calculus_run.Run(calculus_run.MODES["default"])
    recs = [r for r, _ in calculus_run.records("default", tally) if r.move.rule == "IT-"]
    assert all(len(calculus_run.expand(g, r.move.selection)) <= 1 for r in recs)
    assert tally.skipped["A:IT-:engine-does-not-finish"] > 0
    assert tally.moves["A:IT-"] + tally.skipped["A:IT-:engine-does-not-finish"] == 2 ** 7 - 1
