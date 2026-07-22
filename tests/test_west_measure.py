from west_measure import (CountingMaterializer, read_quality, peel_proxy,
                          CostBreakdown, QualityReading)
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
