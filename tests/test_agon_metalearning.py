"""Tests for the meta-learning instruments (``agon_metalearning``) — §6 of the automated
Endoporeutic Game. Deterministic and LLM-free: the mechanical loop over the swan pool gives
reproducible episodes; the thrash / friction / gaps logic is exercised on hand-built records
(so a single-vote mechanical run is not needed to produce disagreement)."""

from agon_evolution import CorpusProposer, run
from agon_metalearning import (
    AblationVariant, EpisodeRecord, episodes_from, friction_map, gaps,
    proposal_shape, resolution_principles, run_ablation, situation_of,
    stability_report,
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
