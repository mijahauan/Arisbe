"""**The revision episode, unpacked** (`src/revision_episode.py`).

`challenge_to_M` did four things in one call — and `proof_character` said so, reading
the old swan chain as *"4 of 4 steps REVISE the model"* with the deduction inside
them invisible. These tests pin the four beats, and the two claims that make the
unpacking worth doing:

* **The conflict is DERIVED, not declared.** Six ordinary Dau rules end in the EMPTY
  CUT. The old panel recognised a refuting *shape* and asserted a conflict; nothing
  ever drew one. Deriving it required scribing the premiss that was never on M's
  sheet — *nothing is both black and white*.
* **A revision is not a deduction.** The absurdity forces only that *something* give;
  choosing which is abduction. So the two ways out are a real FORK in the DAG (the
  road not taken stays navigable), and the chain's character is **ampliative**, never
  "a proof".
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

import proof_character as pc  # noqa: E402
import revision_episode as ep  # noqa: E402

LAW = '~[ (swan *x) ~[ (white x) ] ]'
DISJOINT = '~[ (black *y) (white y) ]'
BLACK_SWAN = '(swan "Nox") (black "Nox")'


# --- beat 2: the conflict is DERIVED --------------------------------------- #

def test_the_contradiction_is_derived_to_the_empty_cut():
    """Six Dau rules — instantiate the law, deiterate, discharge the double cut,
    instantiate disjointness, deiterate both conjuncts — and the cut is EMPTY.
    Absurdity, shown. The conflict now *appears to someone*."""
    ex = ep.exhibit_conflict(f"{BLACK_SWAN} {LAW} {DISJOINT}",
                             individual="Nox", law_relation="swan",
                             disjoint_relation="black")
    assert ex.absurd, ex.summary
    assert ex.steps == ["UI", "IT-", "DC-", "UI", "IT-", "IT-"]
    assert "empty cut" in ex.summary
    # every move is checkable — the derivation is a real chain, not a claim
    assert ex.chain is not None and len(ex.chain.steps) == 6


def test_no_conflict_where_there_is_none():
    """The negative control that earns the positive: a WHITE swan raises no
    contradiction, and the exhibit says so rather than manufacturing one."""
    ex = ep.exhibit_conflict(f'(swan "Ciel") (white "Ciel") {LAW} {DISJOINT}',
                             individual="Ciel", law_relation="swan",
                             disjoint_relation="black")
    assert not ex.absurd
    assert "no contradiction" in ex.summary


def test_without_the_disjointness_premiss_nothing_can_be_derived():
    """The premiss the conflict always needed, and never had. A black swan refutes
    'all swans are white' ONLY given that nothing is both black and white — and that
    law lived in the Challenger's code, not on M's sheet. Absent it, the observation
    and the law simply coexist."""
    ex = ep.exhibit_conflict(f"{BLACK_SWAN} {LAW}",          # no disjointness
                             individual="Nox", law_relation="swan",
                             disjoint_relation="black")
    assert not ex.absurd, "a conflict must not be derivable from premisses that lack it"


def test_a_failed_exhibit_is_a_finding_not_a_crash():
    ex = ep.exhibit_conflict("(swan \"Nox\")", individual="Nox",
                             law_relation="swan", disjoint_relation="black")
    assert ex.absurd is False and ex.reason      # says why; raises nothing


# --- beat 3: the alternatives are two, and a choice ------------------------- #

def test_two_ways_to_restore_consistency():
    alts = ep.alternatives("all swans are white", "Nox is a black swan")
    keys = {a.key for a in alts}
    assert keys == {"relinquish_law", "reject_report"}
    for a in alts:
        assert a.consequence.strip()             # each states its cost


# --- the character: a revision is NOT a proof ------------------------------- #

class _Step:
    def __init__(self, rule, sid="s"):
        self.rule_name, self.step_id, self.parameters = rule, sid, {}


def test_a_model_revision_is_ampliative_not_deduction():
    """Peirce divides reasoning three ways; only DEDUCTION splits into corollarial
    and theorematic. A step that revises M is neither — no rule of inference compels
    it. Calling such a chain 'corollarial' would be a category error."""
    r = pc.character_of([_Step("REVISE_M", "s1"), _Step("REVISE_M", "s2")])
    assert r.character == pc.AMPLIATIVE
    assert r.ampliative_steps == ["s1", "s2"]
    assert "not deduction" in r.summary and "not 'a proof'" in r.summary


def test_ampliative_reports_its_deductive_core():
    """The unpacked episode is ampliative AROUND a deductive core — and says so."""
    r = pc.character_of([_Step("IT-"), _Step("DC-"), _Step("REVISE_M", "s3")])
    assert r.character == pc.AMPLIATIVE
    assert "deductive core of 2" in r.summary


# --- the exemplar: four beats, and a real fork ------------------------------ #

@pytest.fixture(scope="module")
def episode():
    import build_swan_episode as swan
    return swan.build_episode_chain()


def test_the_four_beats_are_recorded_individually(episode):
    chain, _uod = episode
    # PEEL steps are verdict records, not beats — filter to the acts themselves.
    acts = [s for s in chain.steps if (s.parameters or {}).get("act") != "peel"]
    beats = [s.parameters.get("beat") for s in acts]
    assert beats[0] == ep.PROPOSE
    assert beats[1] == ep.EXHIBIT
    assert beats[2] == ep.DISPOSE and beats[3] == ep.DISPOSE   # the two branches
    # the PROPOSE is rule-licensed under the polarity shift: INS into the arena
    assert acts[0].parameters.get("derivation") == ["INS"]
    # the EXHIBIT carries its derivation and does NOT touch M (it is a proof)
    exh = acts[1].parameters
    assert exh["absurd"] and exh["derivation"] == ["UI", "IT-", "DC-", "UI", "IT-", "IT-"]
    assert exh["working_copy"] is True
    # each DISPOSE is ONE licensed ERA inside a cell (sweep #2, the cells
    # residence: relinquish the law / deny the report's atom — the fallibilist
    # pole; no whole-world withdrawal needed)
    assert acts[2].parameters["act"] == "m_retraction"
    assert acts[2].parameters["derivation"] == ["ERA"]
    assert acts[3].parameters["act"] == "m_retraction"
    assert acts[3].parameters["derivation"] == ["ERA"]


def test_the_choice_is_a_real_fork_in_the_dag(episode):
    """'Having two alternatives in mind' IS the branch. Both dispositions hang off the
    same parent state; the road not taken stays navigable."""
    chain, _uod = episode
    revising = [s for s in chain.steps if s.rule_name == "RETRACT_FROM_M"]
    forked = {s.from_state_id for s in revising}
    assert len(forked) == 1, "the two ways out must share a parent state"
    branches = {s.branch_id for s in chain.steps if s.branch_id}
    assert branches == {"relinquish-the-law", "reject-the-report"}


def test_the_episode_reads_as_ampliative_around_a_deductive_core(episode):
    chain, _uod = episode
    c = pc.character_of_chain(chain)
    assert c.character == pc.AMPLIATIVE
    assert "deductive core" in c.summary


def test_the_main_line_relinquishes_the_law_and_admits_the_swan(episode):
    """The disposition actually performs what it says: after the chosen branch, the
    over-general law is gone and the anomaly is on M's sheet."""
    import build_swan_generalization as swan_old
    from eg_navigation import child_cuts
    chain, _uod = episode
    main = next(s for s in chain.steps if s.branch_id == "relinquish-the-law")
    after = chain.states[main.to_state_id]
    assert swan_old._verdict(after) == "false"        # 'all swans are white' now FALSE
    rels = set(after.rel.values())
    assert "black" in rels                            # the anomaly was admitted
