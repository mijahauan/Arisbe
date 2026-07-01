"""Tests for the live runner (``live_runner``) — running the automated Endoporeutic Game against
a live source with bounded, paced, checkpointed segments. Deterministic and offline: a
``ReplaySource`` stands in for a live stream and the clock/sleep are injected, so pacing, decay,
checkpointing and every stop condition are exercised with no network and no real waiting.

The headline: **disuse-decay bounds |M| across segments** — which is what keeps per-round cost,
memory, and disk flat over an indefinite run (per-round cost was measured super-linear in |M|)."""

import os
import tempfile

from discourse_membrane import DiscourseFeed, DiscourseItem
from live_runner import LiveRunConfig, LiveRunner, ReplaySource
from wiki_dispute_membrane import Resolution, WikiDispute, WikiDisputeFeed, WikiEdit


def _fact_batches(n, reuse=False):
    """n batches, one new fact each (or the same fact if reuse=True)."""
    return [[DiscourseItem("d", "s", f'(topic{0 if reuse else i} "X")')] for i in range(n)]


def _zero_clock():
    return 0.0


# --------------------------------------------------------------------------- #
# The replay source                                                           #
# --------------------------------------------------------------------------- #

def test_replay_source_yields_then_exhausts():
    src = ReplaySource([["a"], ["b"]])
    assert list(src.fetch()) == ["a"] and not src.exhausted()
    assert list(src.fetch()) == ["b"] and src.exhausted()
    assert list(src.fetch()) == []


# --------------------------------------------------------------------------- #
# Segmentation + carry-forward                                                 #
# --------------------------------------------------------------------------- #

def test_runner_makes_one_segment_per_batch_and_carries_M_forward():
    r = LiveRunner("", ReplaySource(_fact_batches(3)), DiscourseFeed,
                   LiveRunConfig(ttl=None, checkpoint=False), clock=_zero_clock).run()
    assert r.stopped_because == "source_exhausted"
    assert [d.segment for d in r.segments] == [1, 2, 3]
    assert r.total_rounds == 3
    assert '(topic0 "X")' in r.final_model_egif and '(topic2 "X")' in r.final_model_egif


# --------------------------------------------------------------------------- #
# Decay bounds |M| across segments — the core operational control              #
# --------------------------------------------------------------------------- #

def test_decay_bounds_M_across_segments():
    r = LiveRunner("", ReplaySource(_fact_batches(8)), DiscourseFeed,
                   LiveRunConfig(ttl=2, checkpoint=False), clock=_zero_clock).run()
    assert all(d.m_relations <= 2 for d in r.segments[2:])   # stabilises at ~ttl
    assert any(d.decayed > 0 for d in r.segments)


def test_without_decay_M_grows_unbounded():
    r = LiveRunner("", ReplaySource(_fact_batches(8)), DiscourseFeed,
                   LiveRunConfig(ttl=None, checkpoint=False), clock=_zero_clock).run()
    assert r.segments[-1].m_relations == 8                   # every fact retained


# --------------------------------------------------------------------------- #
# Stop conditions                                                              #
# --------------------------------------------------------------------------- #

def test_max_rounds_stop():
    r = LiveRunner("", ReplaySource(_fact_batches(20)), DiscourseFeed,
                   LiveRunConfig(max_rounds=3, checkpoint=False), clock=_zero_clock).run()
    assert r.stopped_because == "max_rounds" and r.total_rounds == 3


def test_max_seconds_stop_uses_injected_clock():
    clk = [0.0]
    r = LiveRunner("", ReplaySource(_fact_batches(20)), DiscourseFeed,
                   LiveRunConfig(max_seconds=2.5, min_interval_s=1.0, checkpoint=False),
                   clock=lambda: clk[0], sleep=lambda s: clk.__setitem__(0, clk[0] + s)).run()
    assert r.stopped_because == "max_seconds"


def test_stop_file_stop():
    sf = tempfile.mktemp()
    open(sf, "w").close()
    try:
        r = LiveRunner("", ReplaySource(_fact_batches(20)), DiscourseFeed,
                       LiveRunConfig(stop_file=sf, checkpoint=False), clock=_zero_clock).run()
        assert r.stopped_because == "stop_file"
    finally:
        os.remove(sf)


def test_max_m_relations_stop():
    r = LiveRunner("", ReplaySource(_fact_batches(20)), DiscourseFeed,
                   LiveRunConfig(ttl=None, max_m_relations=2, checkpoint=False),
                   clock=_zero_clock).run()
    assert r.stopped_because == "max_m_relations"


# --------------------------------------------------------------------------- #
# Pacing                                                                       #
# --------------------------------------------------------------------------- #

def test_pacing_sleeps_between_polls():
    sleeps = []
    LiveRunner("", ReplaySource(_fact_batches(3)), DiscourseFeed,
               LiveRunConfig(min_interval_s=0.5, checkpoint=False),
               clock=_zero_clock, sleep=lambda s: sleeps.append(s)).run()
    assert sleeps and all(s == 0.5 for s in sleeps)          # paced, first segment not delayed


# --------------------------------------------------------------------------- #
# Checkpointing + evaluation                                                   #
# --------------------------------------------------------------------------- #

def test_checkpoints_persist_each_segment(tmp_path):
    from tomos_service import TomosService
    svc = TomosService(tmp_path)
    r = LiveRunner("", ReplaySource(_fact_batches(3)), DiscourseFeed,
                   LiveRunConfig(ttl=None), uod_id="ck", service=svc, clock=_zero_clock).run()
    assert [d.checkpoint_uod for d in r.segments] == ["ck_seg1", "ck_seg2", "ck_seg3"]
    assert svc.load_uod("ck_seg3") is not None               # a checkpoint is a real saved UoD


def test_evaluate_hook_feeds_the_digest():
    def evaluate(feed, res):
        from agon_metalearning import mechanism_principles
        return {"durable": [p.mechanism for p in mechanism_principles(feed.episodes(res))
                            if p.durable]}
    batch = [WikiDispute('(hot "Mon")', [WikiEdit("a", True)],
                         Resolution("reliable_source", True))]
    r = LiveRunner("", ReplaySource([batch]), WikiDisputeFeed,
                   LiveRunConfig(ttl=None, checkpoint=False),
                   evaluate=evaluate, clock=_zero_clock).run()
    assert r.segments[0].extra["durable"] == ["reliable_source"]
