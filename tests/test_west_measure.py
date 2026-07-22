from west_measure import (CountingMaterializer, read_quality, peel_proxy,
                          CostBreakdown, QualityReading, TracingMaterializer)
from agon_evolution import run, CorpusProposer


def test_counting_materializer_accumulates_per_round():
    cm = CountingMaterializer()
    pool = ['(bird "tweety")', '(swan "odette")', '~[ (swan *x) ~[ (white x) ] ]']
    res = run("", CorpusProposer(pool), rounds=6, uod_id="cm-test",
              name="cm", materializer=cm)
    assert len(cm.per_round_atoms) >= 1
    assert cm.total_atoms() == sum(cm.per_round_atoms)
    assert cm.total_atoms() >= 0


def test_read_quality_shape():
    pool = ['(bird "tweety")', '~[ (bird *x) ~[ (flies x) ] ]', '(bird "robin")']
    res = run("", CorpusProposer(pool), rounds=8, uod_id="q-test", name="q")
    q = read_quality(res)
    assert isinstance(q, QualityReading)
    assert q.final_m_size >= 0
    assert 0.0 <= q.k3_ratio <= 1.0
    assert q.k2_stick_rate is None or 0.0 <= q.k2_stick_rate <= 1.0


def test_cost_breakdown_total():
    cb = CostBreakdown(materialization_atoms=100, peel_proxy=20, coordinator_cost=5)
    assert cb.total() == 125


def test_tracing_materializer_records_one_relation_set_per_round():
    tm = TracingMaterializer()
    pool = ['(bird "tweety")', '(swan "odette")', '(bird "robin")']
    run("", CorpusProposer(pool), rounds=5, uod_id="trace-test",
        name="trace", materializer=tm)
    assert len(tm.per_round_relations) == len(tm.per_round_atoms), (
        "one captured relation set per materialization call (== per round)"
    )
    assert all(isinstance(s, frozenset) for s in tm.per_round_relations)
    assert tm.total_atoms() == sum(tm.per_round_atoms)   # base behaviour intact


def test_tracing_materializer_sees_relations_appear_as_m_grows():
    tm = TracingMaterializer()
    pool = ['(bird "tweety")', '(swan "odette")']
    run("", CorpusProposer(pool), rounds=6, uod_id="trace-grow",
        name="trace-grow", materializer=tm, ttl=None)
    # CorpusProposer exhausts after len(pool) rounds regardless of the
    # requested `rounds`, so this run captures 2 rounds, not 6.
    assert len(tm.per_round_relations) >= 2, (
        "need at least two captured rounds to observe growth"
    )
    union = set()
    for s in tm.per_round_relations:
        union |= s
    assert union, "some relation name must have entered M over the run"
    # Genuine growth check: each round's capture (taken *before* that round's
    # own revision lands, since materialize() is called on the pre-round
    # model) is a subset of the next, and the trajectory ends strictly larger
    # than it started — relation names accumulate as M grows in this fixture,
    # they do not vanish (no decay/relinquishment is in play: ttl=None and
    # both proposals are ground new_fact admissions, not laws).
    for prev, nxt in zip(tm.per_round_relations, tm.per_round_relations[1:]):
        assert prev <= nxt, "a relation name disappeared from M between rounds"
    assert tm.per_round_relations[-1] > tm.per_round_relations[0], (
        "the relation set must have strictly grown by the last captured round"
    )


def test_tracing_materializer_is_a_counting_materializer():
    assert issubclass(TracingMaterializer, CountingMaterializer)


def test_tracing_materializer_standing_proposal_breaks_1to1_alignment():
    """Pins the known limit documented on TracingMaterializer: when run() is
    given a standing_proposal, its loop calls _verdict_or_none() every round
    on top of the round's own peel() — a second materialize() call through
    the same shared materializer — so per_round_relations no longer aligns
    1:1 with rounds. This test exists to make that landmine regression-visible,
    not to endorse it as desired behaviour."""
    tm = TracingMaterializer()
    pool = ['(bird "tweety")', '(swan "odette")', '(bird "robin")']
    res = run("", CorpusProposer(pool), rounds=5, uod_id="trace-standing",
              name="trace-standing", materializer=tm,
              standing_proposal='(bird *x)')
    rounds_run = len(res.outcomes)
    assert rounds_run == len(pool)   # CorpusProposer exhausts after len(pool)
    # One peel() for the round's own proposal + one for the standing-proposal
    # audit on every round => twice as many materialize() calls as rounds.
    assert len(tm.per_round_relations) == 2 * rounds_run
    assert len(tm.per_round_relations) > rounds_run, (
        "with standing_proposal set, per_round_relations does NOT align "
        "1:1 with rounds — see TracingMaterializer's docstring"
    )
