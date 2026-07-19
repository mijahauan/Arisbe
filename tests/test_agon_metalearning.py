"""Tests for the meta-learning instruments (``agon_metalearning``) — §6 of the automated
Endoporeutic Game. Deterministic and LLM-free: the mechanical loop over the swan pool gives
reproducible episodes; the thrash / friction / gaps logic is exercised on hand-built records
(so a single-vote mechanical run is not needed to produce disagreement)."""

from agon_evolution import (
    Agonothetes, ContradictionAgent, CorpusProposer, ObserverAgent, run,
)
from agon_metalearning import (
    AblationVariant, DisputeEpisode, EpisodeRecord, episodes_from, friction_map,
    gaps, mark_decayed, mark_relinquished, proposal_shape, resolution_principles,
    run_ablation, situation_of, stability_report,
)

SWAN_M0 = '(swan "Alba") (white "Alba") (swan "Ciel")'
SWAN_LAW = '~[ (swan *x) ~[ (white x) ] ]'
SWAN_POOL = ['(white "Ciel")', SWAN_LAW, '(swan "Nox") ~[ (white "Nox") ]']


def _swan_run():
    return run(SWAN_M0, CorpusProposer(SWAN_POOL), rounds=3,
               uod_id="ml_swan", name="ml swan", standing_proposal=SWAN_LAW)


# --------------------------------------------------------------------------- #
# Situation signatures                                                         #
# --------------------------------------------------------------------------- #

def test_proposal_shape_classifies_the_structural_kinds():
    assert proposal_shape('(white "Ciel")') == "ground"
    assert proposal_shape(SWAN_LAW) == "law"
    assert proposal_shape('(swan "Nox") ~[ (white "Nox") ]') == "counterexample"
    assert proposal_shape('~[ (white "Nox") ]') == "negation"
    assert proposal_shape("") == "empty"


def test_situation_of_joins_verdict_and_shape():
    assert situation_of('(white "Ciel")', "false") == "false:ground"
    assert situation_of(SWAN_LAW, "true") == "true:law"


# --------------------------------------------------------------------------- #
# Episodes + stickiness over a real run                                        #
# --------------------------------------------------------------------------- #

def test_episodes_capture_the_swan_trajectory_and_stickiness():
    eps = episodes_from(_swan_run(), run_id="swan")
    assert [e.disposition for e in eps] == ["new_fact", "generalization", "challenge_to_M"]
    assert [e.situation for e in eps] == [
        "false:ground", "true:law", "false:counterexample"]
    by_disp = {e.disposition: e for e in eps}
    # the fact and the challenge stick; the law was superseded by the later challenge
    assert by_disp["new_fact"].stuck is True
    assert by_disp["challenge_to_M"].stuck is True
    assert by_disp["generalization"].stuck is False


# --------------------------------------------------------------------------- #
# Decay-erasure vs relinquishment — falling from use is not being overturned   #
# --------------------------------------------------------------------------- #

def test_decay_erasure_reads_stuck_none_not_false():
    """A fact erased by disuse-decay carries no durability evidence — it must not read as
    relinquished (the long-run confound: decay would corrupt every stick-rate)."""
    pool = ['(alpha "A")', '(bravo "B")', '(charlie "C")', '(delta "D")']
    res = run("", CorpusProposer(pool), rounds=4, ttl=2,
              uod_id="ml_decay", name="ml decay")
    eps = episodes_from(res, run_id="decay")
    by_claim = {e.proposal_egif: e for e in eps}
    # alpha and bravo fell from use (idle past ttl) — no evidence either way
    assert by_claim['(alpha "A")'].stuck is None
    assert by_claim['(alpha "A")'].erased_by_decay is True
    assert by_claim['(bravo "B")'].stuck is None
    # the still-warm facts stand
    assert by_claim['(delta "D")'].stuck is True
    assert by_claim['(delta "D")'].erased_by_decay is False
    # and the stick-rate excludes the decayed episodes instead of counting them as failures
    p = {p.situation: p for p in resolution_principles(eps)}["false:ground"]
    assert p.stick_rate == 1.0


def test_disposition_erasure_still_reads_stuck_false():
    """An erasure the *game* performed (a sourced denial → retract_fact) IS durability
    evidence: the admitting move reads stuck=False, not decayed."""
    panel = Agonothetes([ObserverAgent(), ContradictionAgent()])
    pool = ['(beta "B")', '~[ (beta "B") ]']
    res = run("", CorpusProposer(pool), rounds=2, panel=panel,
              uod_id="ml_retract", name="ml retract")
    eps = episodes_from(res, run_id="retract")
    assert eps[0].disposition == "new_fact"
    assert eps[0].stuck is False and eps[0].erased_by_decay is False
    assert eps[1].disposition == "retract_fact" and eps[1].stuck is True


def test_mark_decayed_retro_marks_enlargements_and_spares_relinquishments():
    """The LiveRunner decays across segments, after each segment's episodes were built —
    mark_decayed retro-marks the accumulated records."""
    eps = [
        DisputeEpisode('(hot "Mon")', "consensus", True, 0, "new_fact", True),
        DisputeEpisode('~[ (hot "Mon") ]', "reliable_source", False, 1, "retract_fact", True),
        DisputeEpisode('(cold "Tue")', "consensus", True, 0, "new_fact", True),
    ]
    n = mark_decayed(eps, {"hot"})
    assert n == 1
    assert eps[0].stuck is None and eps[0].erased_by_decay is True   # fell from use
    assert eps[1].stuck is True and eps[1].erased_by_decay is False  # the event happened
    assert eps[2].stuck is True                                      # untouched relation
    assert mark_decayed(eps, set()) == 0


def test_mark_decayed_atoms_is_atom_precise_under_a_surviving_name():
    """The atom-level rulebook (2026-07-03): the runner drops (hot "Mon") to disuse while
    (hot "Tue") stays warm — only the episode whose ATOM fell is retro-marked; the
    same-name sibling still reads durable (name-level marking flipped both)."""
    from agon_metalearning import mark_decayed_atoms
    eps = [
        DisputeEpisode('(hot "Mon")', "consensus", True, 0, "new_fact", True),
        DisputeEpisode('(hot "Tue")', "consensus", True, 0, "new_fact", True),
        DisputeEpisode('~[ (hot "Mon") ]', "reliable_source", False, 1, "retract_fact", True),
    ]
    n = mark_decayed_atoms(eps, {("hot", ("Mon",))})
    assert n == 1
    assert eps[0].stuck is None and eps[0].erased_by_decay is True   # its atom fell
    assert eps[1].stuck is True and eps[1].erased_by_decay is False  # the warm sibling spared
    assert eps[2].stuck is True                                      # relinquishment untouched
    assert mark_decayed_atoms(eps, set()) == 0


def test_within_run_stickiness_reads_atom_decay_under_a_surviving_name():
    """episodes_from's stickiness is atom-precise: an admitted atom that later falls to
    in-run disuse-decay reads (stuck=None, erased_by_decay) even though its relation name
    still stands on the final sheet via a warmer atom."""
    pool = ['(spot "Ciel")'] + ['(spot "Alba")'] * 4     # Ciel admitted once, then idle
    res = run("", CorpusProposer(pool), rounds=5, ttl=2, uod_id="ml_atom", name="ml atom")
    eps = episodes_from(res, run_id="atom")
    ciel = eps[0]
    assert ciel.proposal_egif == '(spot "Ciel")' and ciel.disposition == "new_fact"
    assert ciel.stuck is None and ciel.erased_by_decay is True
    # the name survives on the re-delivered atom — the final sheet still says (spot Alba)
    assert any(res.uod.current_egi.rel[e.id] == "spot" for e in res.uod.current_egi.E)


def test_mark_relinquished_flips_an_earlier_admission_a_later_segment_retracts():
    """The mirror of mark_decayed: a later segment's retract_fact IS durability evidence for
    the earlier admission — atom-precise (a same-relation sibling is spared)."""
    panel = Agonothetes([ObserverAgent(), ContradictionAgent()])
    # a later "segment": M carries both atoms; a sourced denial retracts only (rel "A")
    later = run('(rel "A") (rel "B")', CorpusProposer(['~[ (rel "A") ]']),
                rounds=1, panel=panel, uod_id="ml_rel", name="ml rel")
    earlier = [
        DisputeEpisode('(rel "A")', "consensus", True, 0, "new_fact", True),
        DisputeEpisode('(rel "B")', "consensus", True, 0, "new_fact", True),
        DisputeEpisode('(other "C")', "reliable_source", True, 0, "new_fact", True),
    ]
    assert mark_relinquished(earlier, later) == 1
    assert earlier[0].stuck is False                    # overturned — durability evidence
    assert earlier[1].stuck is True                     # the sibling atom is spared
    assert earlier[2].stuck is True


# --------------------------------------------------------------------------- #
# Resolution principles (stability vs thrash)                                  #
# --------------------------------------------------------------------------- #

def _rec(situation, disposition, slate=None, stuck=True, disagreement=0, branched=()):
    return EpisodeRecord(
        run_id="t", round_idx=0, situation=situation, verdict="false",
        proposal_egif="(p)", disposition=disposition,
        slate=slate or [disposition], branched=list(branched),
        disagreement=disagreement, stuck=stuck)


def test_resolution_principles_finds_a_stable_mapping_and_a_thrash():
    eps = [
        _rec("false:ground", "new_fact"), _rec("false:ground", "new_fact"),
        _rec("false:ground", "new_fact"),                    # a clean principle
        _rec("true:law", "generalization"), _rec("true:law", "definition"),  # split → thrash
    ]
    principles = {p.situation: p for p in resolution_principles(eps)}
    assert principles["false:ground"].dominant == "new_fact"
    assert principles["false:ground"].stability == 1.0
    assert principles["false:ground"].thrash is False
    assert principles["true:law"].thrash is True
    assert principles["true:law"].stability == 0.5


def test_resolution_principles_reports_stick_rate():
    eps = [_rec("s", "new_fact", stuck=True), _rec("s", "new_fact", stuck=False)]
    p = resolution_principles(eps)[0]
    assert p.stick_rate == 0.5


# --------------------------------------------------------------------------- #
# Friction map + gaps                                                          #
# --------------------------------------------------------------------------- #

def test_friction_map_ranks_the_most_contested_situations_first():
    eps = [
        _rec("calm", "new_fact", disagreement=0),
        _rec("contested", "new_fact", slate=["new_fact", "generalization"],
             disagreement=1, branched=["generalization"]),
    ]
    fm = friction_map(eps)
    assert fm[0].situation == "contested"                    # highest mean disagreement first
    assert fm[0].branched_rounds == 1
    assert fm[-1].situation == "calm" and fm[-1].mean_disagreement == 0.0


def test_gaps_flags_a_situation_handled_inconsistently():
    eps = [
        _rec("false:ground", "new_fact"),                    # once revised
        EpisodeRecord("t", 0, "false:ground", "false", "(p)", None, [], [], 0, None),  # once inert
    ]
    found = gaps(eps)
    assert any("false:ground" in g for g in found)


# --------------------------------------------------------------------------- #
# The observable shadow of poise (§4d) — an instrument, not a target           #
# --------------------------------------------------------------------------- #

from agon_metalearning import poise_from_digests, poise_report


def _ep(idx, situation, disposition, disagreement=0, branched=()):
    return EpisodeRecord(
        run_id="t", round_idx=idx, situation=situation, verdict="false",
        proposal_egif="(p)", disposition=disposition,
        slate=[disposition] if disposition else [], branched=list(branched),
        disagreement=disagreement, stuck=True if disposition else None)


def test_swan_run_reads_poised_with_one_absorbed_stumble():
    """The hand-played trajectory is the exemplar: engaged, settled, one fresh irritation
    (the black swan) disposed in a single round — poised, with the stumble on the frontier."""
    rep = poise_report(episodes_from(_swan_run()), window=3)
    assert len(rep.windows) == 1 and rep.windows[0].poised
    assert rep.windows[0].engagement == 1.0 and rep.windows[0].thrash_situations == 0
    assert [s.kind for s in rep.stumbles] == ["relinquishment"]
    assert rep.poised_fraction == 1.0
    assert rep.unrecovered == 1                     # the trace ends on it — frontier, not fall


def test_rigidity_pole_a_dead_window_is_not_poised():
    """No stumbles and no engagement is not poise — it is the dance stopped."""
    eps = [_ep(i, "false:ground", None) for i in range(1, 9)]
    rep = poise_report(eps, window=8)
    assert not rep.windows[0].poised and rep.windows[0].failure == "rigidity"
    assert rep.stumbles == []


def test_thrash_pole_inconsistent_disposition_breaks_poise():
    """The same situation disposed differently within a window is thrash — engagement without
    settlement."""
    eps = [_ep(i, "true:law", "generalization" if i % 2 else "definition")
           for i in range(1, 9)]
    rep = poise_report(eps, window=8)
    assert not rep.windows[0].poised and rep.windows[0].failure == "thrash"
    assert rep.windows[0].thrash_situations == 1


def test_stumble_recovery_is_measured_in_rounds():
    """A stumble's measure is recovery — rounds until a poised window resumes."""
    eps = ([_ep(1, "false:ground", "new_fact"), _ep(2, "false:ground", "new_fact"),
            _ep(3, "false:counterexample", "retract_fact")]
           + [_ep(i, "false:ground", "new_fact") for i in range(4, 13)])
    rep = poise_report(eps, window=8)
    (stumble,) = rep.stumbles
    assert stumble.kind == "relinquishment" and stumble.round_idx == 3
    assert stumble.recovery == 1                    # the very next round opens a poised window
    assert rep.mean_recovery == 1.0 and rep.unrecovered == 0


def test_two_absorbed_stumbles_read_storm_not_thrash():
    """Docket ⑦: two stumbles, each its own situation (so thrash_situations == 0 —
    every situation disposed consistently) still exceed max_stumbles=1. That is
    absorbing-at-rate, not the thrash that never happened."""
    eps = ([_ep(i, f"false:ground{i}", "retract_fact") for i in (1, 2)]
           + [_ep(i, f"false:ground{i}", "new_fact") for i in range(3, 9)])
    rep = poise_report(eps, window=8)
    assert rep.windows[0].thrash_situations == 0
    assert rep.windows[0].stumbles == 2
    assert rep.windows[0].poised is False
    assert rep.windows[0].failure == "storm"


def test_poise_from_digests_reads_the_live_stream():
    from live_runner import SegmentDigest
    calm = SegmentDigest(1, 25, 25, 20, {"new_fact": 25}, 0, 0, 0.5, None)
    dead = SegmentDigest(2, 25, 50, 20, {}, 0, 0, 0.5, None)
    storm = SegmentDigest(3, 25, 75, 20,
                          {"new_fact": 5, "retract_fact": 2, "challenge_to_M": 1}, 0, 1,
                          0.5, None)
    readings = poise_from_digests([calm, dead, storm])
    assert readings[0].poised
    assert readings[1].failure == "rigidity"
    # thrash is not computable from a digest (no per-situation record) — 4 absorbed
    # stumbles read storm, never a thrash claim the digest can't back.
    assert readings[2].failure == "storm" and readings[2].stumbles == 4


# --------------------------------------------------------------------------- #
# Stability + ablation                                                         #
# --------------------------------------------------------------------------- #

def test_stability_report_says_the_swan_run_settled():
    rep = stability_report(_swan_run(), run_id="swan")
    assert rep.rounds == 3 and rep.revising == 3
    assert rep.settle_round == 3
    assert rep.thrash_situations == 0
    assert rep.final_m_relations == 2                         # swan + white survive the challenge


def test_run_ablation_compares_variants_with_fresh_proposers():
    variants = [
        AblationVariant("no_decay", {}),
        AblationVariant("decay_ttl2", {"ttl": 2}),
    ]
    results = run_ablation(SWAN_M0, lambda: CorpusProposer(SWAN_POOL), variants, rounds=3)
    assert [r.label for r in results] == ["no_decay", "decay_ttl2"]
    assert all(r.stability.rounds == 3 for r in results)
    assert all(r.principles for r in results)                 # each arm mined principles
