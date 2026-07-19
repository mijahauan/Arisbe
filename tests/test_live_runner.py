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
# Atom units — the RUN_3 F1″ instruments, and the F1″ *dissolution*            #
# (the atom-level decay rulebook, affirmed 2026-07-03: the habit is the fact,  #
#  not the name — a warm hub name no longer pins its idle atom pile)           #
# --------------------------------------------------------------------------- #

def _hub_batches(n):
    """n batches, each a new fact under the SAME relation name — the hub shape."""
    return [[DiscourseItem("d", "s", f'(prop "X{i}")')] for i in range(n)]


def test_atom_level_decay_dissolves_the_warm_hub_name_pinning():
    """The F1″ defect this test used to *pin* (name-level decay never fires while a
    hub name is used every round, so atoms accumulate unboundedly) is dissolved:
    each delivered atom is its own habit, so the idle ones fall at ttl and |M|
    stabilises in the honest unit too."""
    r = LiveRunner("", ReplaySource(_hub_batches(8)), DiscourseFeed,
                   LiveRunConfig(ttl=2, checkpoint=False), clock=_zero_clock).run()
    assert all(d.m_relations == 1 for d in r.segments)       # the name survives throughout
    assert any(d.decayed > 0 for d in r.segments)            # decay reaches the idle atoms now
    atoms = [d.m_atoms for d in r.segments]
    assert max(atoms) <= 3                                   # ≈ ttl, not one-per-round
    assert atoms[-1] == atoms[-2]                            # stabilised, not growing


def test_max_m_atoms_stop_fires_while_names_read_flat():
    r = LiveRunner("", ReplaySource(_hub_batches(20)), DiscourseFeed,
                   LiveRunConfig(ttl=None, max_m_relations=10, max_m_atoms=3, checkpoint=False),
                   clock=_zero_clock).run()
    assert r.stopped_because == "max_m_atoms"                # names never hit their cap
    assert all(d.m_relations <= 1 for d in r.segments)


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


# --------------------------------------------------------------------------- #
# No silent truncation — a batch larger than segment_cap is queued, not dropped #
# --------------------------------------------------------------------------- #

def test_oversized_batch_is_segmented_not_dropped():
    batch = [DiscourseItem("d", "s", f'(topic{i} "X")') for i in range(5)]
    r = LiveRunner("", ReplaySource([batch]), DiscourseFeed,
                   LiveRunConfig(ttl=None, segment_cap=2, checkpoint=False),
                   clock=_zero_clock).run()
    assert r.total_rounds == 5                               # every item processed
    assert [d.rounds for d in r.segments] == [2, 2, 1]       # cap sets cadence, not coverage
    assert '(topic4 "X")' in r.final_model_egif


# --------------------------------------------------------------------------- #
# Resume — a killed process loses at most its in-flight segment                #
# --------------------------------------------------------------------------- #

def test_resume_from_state_continues_the_run(tmp_path):
    sp = str(tmp_path / "state.json")
    batches = _fact_batches(4)
    r1 = LiveRunner("", ReplaySource(batches[:2]), DiscourseFeed,
                    LiveRunConfig(ttl=None, checkpoint=False, state_path=sp),
                    clock=_zero_clock).run()
    assert r1.total_rounds == 2 and os.path.exists(sp)
    r2 = LiveRunner.resume(sp, ReplaySource(batches[2:]), DiscourseFeed,
                           LiveRunConfig(ttl=None, checkpoint=False),
                           clock=_zero_clock).run()
    # continues, never restarts: segment/round numbering is global, all facts carried
    assert [d.segment for d in r2.segments] == [3, 4]
    assert r2.total_rounds == 4
    for i in range(4):
        assert f'(topic{i} "X")' in r2.final_model_egif


def test_resume_restores_the_decay_clock(tmp_path):
    """The disuse ledger continues rather than resets — a resumed run must neither grant
    every relation a fresh ttl nor (the reset-to-zero failure) treat carried facts as
    instantly stale."""
    sp = str(tmp_path / "state.json")
    batches = _fact_batches(4)
    LiveRunner("", ReplaySource(batches[:2]), DiscourseFeed,
               LiveRunConfig(ttl=3, checkpoint=False, state_path=sp),
               clock=_zero_clock).run()
    r2 = LiveRunner.resume(sp, ReplaySource(batches[2:]), DiscourseFeed,
                           LiveRunConfig(ttl=3, checkpoint=False), clock=_zero_clock).run()
    # topic0 was last used in global round 1 → stale exactly at round 4 (4-1=3), not at
    # round 3 (a reset-to-zero ledger would have decayed it a segment early)
    assert [d.decayed for d in r2.segments] == [0, 1]


# --------------------------------------------------------------------------- #
# Cross-segment decay does not corrupt stickiness — the long-run §6 aggregate  #
# --------------------------------------------------------------------------- #

def _consensus(claim):
    return WikiDispute(claim, [WikiEdit("a", True)], Resolution("consensus", True))


def test_runner_decay_reads_as_decay_not_relinquishment_in_episodes():
    from agon_metalearning import mechanism_principles
    batches = [[_consensus('(hot "Mon")')],
               [_consensus('(cold "Tue")')],
               [_consensus('(wind "Wed")')]]
    r = LiveRunner("", ReplaySource(batches), WikiDisputeFeed,
                   LiveRunConfig(ttl=1, checkpoint=False), clock=_zero_clock).run()
    assert len(r.episodes) == 3
    hot, cold, wind = r.episodes
    # hot and cold fell to the runner's cross-segment disuse-decay — retro-marked, not failed
    assert hot.stuck is None and hot.erased_by_decay is True
    assert cold.stuck is None and cold.erased_by_decay is True
    assert wind.stuck is True
    # so consensus still reads durable (1 sticky / 1 with evidence), with the decay reported —
    # without the split the rate would read 1/3 and the finding would be silently corrupted
    p = mechanism_principles(r.episodes)[0]
    assert p.mechanism == "consensus"
    assert p.stick_rate == 1.0 and p.durable is True
    assert p.decay_erased == 2


def test_cross_segment_overturn_reads_as_not_durable():
    """The mirror confound: a bare consensus admitted in segment 1 and overturned by a
    reliably-sourced denial in segment 2 must read stuck=False in the long-run aggregate —
    per-segment stickiness alone would leave it stuck=True (the Wikidata overturn scenario)."""
    from agon_evolution import (
        Agonothetes, ChallengerAgent, ContradictionAgent, GeneralizerAgent, ObserverAgent,
    )
    from agon_metalearning import mechanism_principles
    from wikidata_source import WikidataSource, WikidataStatement as WS
    polls = [
        [WS("Q42", "place of birth", "Cambridge", "normal", referenced=False)],
        [WS("Q42", "place of birth", "Cambridge", "deprecated", referenced=False),
         WS("Q42", "place of birth", "London", "normal", referenced=True)],
    ]
    panel = Agonothetes([ObserverAgent(), GeneralizerAgent(), ChallengerAgent(),
                         ContradictionAgent()])
    r = LiveRunner("", WikidataSource(polls), WikiDisputeFeed,
                   LiveRunConfig(ttl=None, checkpoint=False),
                   panel=panel, clock=_zero_clock).run()
    by_mech = {p.mechanism: p for p in mechanism_principles(r.episodes)}
    assert by_mech["consensus"].stick_rate == 0.0       # the bare value was overturned
    assert by_mech["consensus"].durable is False
    assert by_mech["reliable_source"].stick_rate == 1.0 # the referenced value stands
    assert by_mech["reliable_source"].durable is True


# --------------------------------------------------------------------------- #
# RUN_5 F2⁵ — the habit clock denominated in POLLS (engagement opportunities)  #
# --------------------------------------------------------------------------- #

def _multi_fact_batches():
    """3 polls × 4 facts; topic0 arrives in poll 1 and is never re-delivered."""
    return [
        [DiscourseItem("d", "s", f'(topic0 "X")')] +
        [DiscourseItem("d", "s", f'(a{i} "X")') for i in range(3)],
        [DiscourseItem("d", "s", f'(b{i} "X")') for i in range(4)],
        [DiscourseItem("d", "s", f'(c{i} "X")') for i in range(4)],
    ]


def test_ttl_in_polls_counts_engagement_opportunities_not_rounds():
    """RUN_5 F2⁵: once rounds are ~free, a rounds-denominated ttl is a ~seconds memory and
    no atom survives a poll gap.  Under ttl_unit="polls", ttl=2 means "idle 2 polls":
    topic0 (delivered poll 1, never again) survives poll 2's decay pass and falls only
    at poll 3 — even though far more than 2 ROUNDS have passed by then."""
    r = LiveRunner("", ReplaySource(_multi_fact_batches()), DiscourseFeed,
                   LiveRunConfig(ttl=2, ttl_unit="polls", checkpoint=False),
                   clock=_zero_clock).run()
    # survives the poll-2 pass (idle 1 poll), decays at the poll-3 pass (idle 2 polls)
    assert r.segments[0].decayed == 0
    assert r.segments[1].decayed == 0
    assert r.segments[2].decayed >= 1
    assert '(topic0 "X")' not in r.final_model_egif

    # contrast: the same schedule under the ROUNDS clock kills topic0 a poll earlier
    # (by the end of poll 2, topic0 has been idle 7 rounds ≥ ttl=2)
    r2 = LiveRunner("", ReplaySource(_multi_fact_batches()), DiscourseFeed,
                    LiveRunConfig(ttl=2, ttl_unit="rounds", checkpoint=False),
                    clock=_zero_clock).run()
    assert r2.segments[1].decayed >= 1


def test_resume_restores_the_poll_clock(tmp_path):
    """The poll clock persists through a crash/resume like the round clock — a resumed
    run must not reset poll numbering (which would grant every atom a fresh polls-ttl)."""
    import json as _json
    sp = str(tmp_path / "state.json")
    batches = _multi_fact_batches()
    LiveRunner("", ReplaySource(batches[:2]), DiscourseFeed,
               LiveRunConfig(ttl=2, ttl_unit="polls", checkpoint=False, state_path=sp),
               clock=_zero_clock).run()
    with open(sp) as fh:
        assert _json.load(fh)["poll"] == 2
    r2 = LiveRunner.resume(sp, ReplaySource(batches[2:]), DiscourseFeed,
                           LiveRunConfig(ttl=2, ttl_unit="polls", checkpoint=False),
                           clock=_zero_clock)
    assert r2._poll_idx == 2
    res = r2.run()
    # the resumed poll-3 pass sees topic0 idle 2 polls → it decays exactly on schedule
    assert res.segments[0].decayed >= 1
    assert '(topic0 "X")' not in res.final_model_egif
    with open(sp) as fh:
        assert _json.load(fh)["poll"] == 3


# --------------------------------------------------------------------------- #
# RUN_5 F1⁵ — a §3.3 refusal at the checkpoint is skipped, counted, quarantined #
# --------------------------------------------------------------------------- #

class _RefusingService:
    """A checkpoint service whose save always refuses §3.3 (the F1⁵ coin-flip loss)."""

    def save_uod_with_chain(self, uod, chain):
        from correspondence_attestation import CorrespondenceViolation
        raise CorrespondenceViolation(
            ["  occlusion: vertex A label box overlaps vertex B label box (text-on-text)"],
            context="test refusal")


def test_checkpoint_refusal_skip_counts_and_quarantines(tmp_path):
    """Under checkpoint_refusal="skip" (the unattended posture), a refusal does not end
    the run: it is counted, the digest carries no checkpoint id, and the refused M is
    quarantined (EGIF + error) beside the state file — auditable, never silent."""
    import json as _json
    sp = str(tmp_path / "state.json")
    runner = LiveRunner("", ReplaySource(_fact_batches(2)), DiscourseFeed,
                        LiveRunConfig(ttl=None, checkpoint=True, checkpoint_refusal="skip",
                                      state_path=sp),
                        service=_RefusingService(), clock=_zero_clock)
    res = runner.run()
    assert res.stopped_because == "source_exhausted"        # the run SURVIVED both refusals
    assert runner.checkpoints_refused == 2
    assert all(d.checkpoint_uod is None for d in res.segments)
    q = tmp_path / "refused_seg1.json"
    assert q.exists()
    data = _json.loads(q.read_text())
    assert "occlusion" in data["error"] and data["model_egif"]
    assert '(topic0 "X")' in data["model_egif"]


def test_checkpoint_refusal_raise_is_the_default_contract():
    """Without opting into "skip", the corpus-boundary contract stands: the refusal
    propagates (an attended run should die loudly, as before)."""
    import pytest
    from correspondence_attestation import CorrespondenceViolation
    runner = LiveRunner("", ReplaySource(_fact_batches(1)), DiscourseFeed,
                        LiveRunConfig(ttl=None, checkpoint=True),
                        service=_RefusingService(), clock=_zero_clock)
    with pytest.raises(CorrespondenceViolation):
        runner.run()


# --------------------------------------------------------------------------- #
# RUN_5 F2ᵇ — checkpoint cadence: every Nth segment, coverage untouched        #
# --------------------------------------------------------------------------- #

class _CountingService:
    def __init__(self):
        self.saved = []

    def save_uod_with_chain(self, uod, chain):
        self.saved.append(uod.metadata.uod_id)


def test_checkpoint_every_thins_the_record_not_the_coverage(tmp_path):
    """checkpoint_every=2 saves segments 2 and 4 only — but every segment still
    runs, digests still accumulate, and the resumable state file is still written
    per segment (cadence ≠ coverage)."""
    svc = _CountingService()
    sp = str(tmp_path / "state.json")
    runner = LiveRunner("", ReplaySource(_fact_batches(4)), DiscourseFeed,
                        LiveRunConfig(ttl=None, checkpoint=True, checkpoint_every=2,
                                      state_path=sp),
                        service=svc, clock=_zero_clock)
    res = runner.run()
    assert [d.segment for d in res.segments] == [1, 2, 3, 4]        # all segments ran
    assert svc.saved == ["live_seg2", "live_seg4"]                  # record thinned
    assert [d.checkpoint_uod for d in res.segments] == [
        None, "live_seg2", None, "live_seg4"]
    assert os.path.exists(sp)                                       # state per segment
    import json as _json
    with open(sp) as fh:
        assert _json.load(fh)["segment"] == 4


def test_checkpoint_every_default_keeps_the_old_behavior():
    svc = _CountingService()
    res = LiveRunner("", ReplaySource(_fact_batches(2)), DiscourseFeed,
                     LiveRunConfig(ttl=None, checkpoint=True),
                     service=svc, clock=_zero_clock).run()
    assert svc.saved == ["live_seg1", "live_seg2"]                  # every segment


# --------------------------------------------------------------------------- #
# Docket ④ — M is carried between segments STRUCTURALLY, not as EGIF text      #
# --------------------------------------------------------------------------- #

def _two_cell_M():
    """A resident M whose two admission cells each mention the constant "Opus".
    Per-cell vertex privacy is what is at stake: EGIF has no way to say "two
    distinct vertices, same label, different cells", so a *text* carry merges
    them (world_scroll's documented round-trip accommodation) — which is what
    defeated the licensed cell-scoped ERA and forced the F2¹³ fallback."""
    from egif_parser_dau import parse_egif
    from world_scroll import enlarge_m, wrap_m
    g, _scroll = wrap_m(parse_egif('(pen "Opus")'))
    return enlarge_m(g, '(quill "Opus")')


def _carried(result):
    from egi_io import from_dict
    return from_dict(result.final_model_json)


def test_carry_preserves_resident_M_structurally():
    """Docket ④: a constant shared across two cells survives the segment carry."""
    from eg_navigation import same_graph
    from egi_io import to_dict
    from world_scroll import enlarge_m

    m = _two_cell_M()
    r = LiveRunner(to_dict(m), ReplaySource(_fact_batches(1)), DiscourseFeed,
                   LiveRunConfig(ttl=None, checkpoint=False), clock=_zero_clock).run()
    carried = _carried(r)
    # each cell keeps its own "Opus" vertex — under the EGIF carry this reads 1
    assert len([v for v in carried.V if v.label == "Opus"]) == 2
    # and the carry is total: M is exactly the seed plus the admitted fact
    assert same_graph(carried, enlarge_m(m, '(topic0 "X")'))


def test_carry_preserves_quotation_bearing_cell():
    """V2a.2 composition gate: a banked quotation cell survives the carry.
    The EGIF carry cannot even express such an M — there is no linear syntax
    for the sort, so ``generate_egif`` raises the named limit."""
    import pytest
    from eg_navigation import same_graph
    from egif_generator_dau import generate_egif
    from egif_parser_dau import parse_egif
    from egi_io import to_dict
    from quotation_overlay import scribe_quotation
    from second_order_limits import SecondOrderNotInLinearForm
    from world_scroll import enlarge_m, find_world_scroll

    m = _two_cell_M()
    cell = find_world_scroll(m).cell_ids[0]
    m, _mark, _cut = scribe_quotation(m, "phi", parse_egif('(pen "Opus")'),
                                      context_id=cell)
    with pytest.raises(SecondOrderNotInLinearForm):
        generate_egif(m)

    r = LiveRunner(to_dict(m), ReplaySource(_fact_batches(1)), DiscourseFeed,
                   LiveRunConfig(ttl=None, checkpoint=False), clock=_zero_clock).run()
    carried = _carried(r)
    assert dict(carried.quotation) == dict(m.quotation)   # the device is intact
    assert dict(carried.sort) == dict(m.sort)
    assert same_graph(carried, enlarge_m(m, '(topic0 "X")'))


def test_state_file_carries_the_structural_model(tmp_path):
    """The checkpoint carries the same structural M the run carries — a resumed
    run inherits per-cell privacy rather than a re-merged text reading."""
    import json as _json
    from egi_io import from_dict, to_dict

    sp = str(tmp_path / "state.json")
    LiveRunner(to_dict(_two_cell_M()), ReplaySource(_fact_batches(1)), DiscourseFeed,
               LiveRunConfig(ttl=None, checkpoint=False, state_path=sp),
               clock=_zero_clock).run()
    with open(sp) as fh:
        state = _json.load(fh)
    assert "model_egif" not in state
    assert len([v for v in from_dict(state["model_json"]).V
                if v.label == "Opus"]) == 2


def test_resume_reads_a_legacy_egif_checkpoint(tmp_path):
    """An old-shape state file (pre-④, M as ``model_egif`` text) still resumes:
    it is parsed once and carried structurally thereafter."""
    import json as _json

    sp = str(tmp_path / "state.json")
    with open(sp, "w") as fh:
        _json.dump({"version": 1, "segment": 2, "round": 2, "poll": 2,
                    "total_rounds": 2, "laws": [], "ledger": None,
                    "model_egif": '~[ ~[ ] ~[ (topic0 "X") ] ]'}, fh)
    r = LiveRunner.resume(sp, ReplaySource(_fact_batches(1)), DiscourseFeed,
                          LiveRunConfig(ttl=None, checkpoint=False),
                          clock=_zero_clock).run()
    assert [d.segment for d in r.segments] == [3]         # numbering continues
    assert '(topic0 "X")' in r.final_model_egif           # the legacy M was carried
    with open(sp) as fh:
        assert "model_json" in _json.load(fh)             # rewritten in the new shape
