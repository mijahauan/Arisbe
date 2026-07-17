"""The explicit-step vocabulary (m_steps.py): PEEL / ADMIT_TO_M /
RETRACT_FROM_M / REVISE_M.

Each step is earned — the transform runs real rules or a real evaluation — and
the recorded parameters are re-checkable (the sweep gate recomputes verdicts)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

import eg_navigation as nav
from egif_parser_dau import parse_egif
from m_steps import (admit_step, challenge_step, peel_step, retract_step,
                     revise_step)
from proof_authoring import ProofChain
from proof_character import character_of_chain
from world_scroll import find_world_scroll, m_view, wrap_m

LAW = "~[ (swan *x) ~[ (white x) ] ]"
M0 = f'(swan "Ciel") (white "Ciel") {LAW}'
PROPOSAL = "~[ (swan *x) ~[ (white x) ] ]"


def _chain_from(m_egif: str) -> ProofChain:
    wrapped, _ = wrap_m(parse_egif(m_egif))
    return ProofChain(wrapped)


class TestPeelStep:
    def test_verdict_recorded_and_state_unchanged(self):
        pc = _chain_from(M0)
        before = pc.current
        result = peel_step(pc, PROPOSAL, closed=True)
        step = pc.to_chain().steps[-1]
        assert step.rule_name == "PEEL"
        assert step.parameters["verdict"] == result.verdict.value == "true"
        assert step.parameters["earned"] is True
        assert step.parameters["proposal_egif"] == PROPOSAL
        # identity transform, fresh state (never a self-loop)
        assert step.from_state_id != step.to_state_id
        assert nav.same_graph(pc.current, before)

    def test_false_verdict_carries_counterexample(self):
        pc = _chain_from('(swan "Nox") (black "Nox") ~[ (black *y) (white y) ]')
        result = peel_step(pc, PROPOSAL, closed=True)
        assert result.verdict.value == "false"
        step = pc.to_chain().steps[-1]
        assert step.parameters["counterexample"]

    def test_peel_is_neutral_for_proof_character(self):
        pc = _chain_from(M0)
        peel_step(pc, PROPOSAL, closed=True)
        ch = character_of_chain(pc.to_chain())
        assert ch.character == "corollarial"       # a verdict record adds nothing


class TestAdmitStep:
    def test_enlargement_is_recorded_and_real(self):
        pc = _chain_from(M0)
        admit_step(pc, '(swan "Dover") (white "Dover")',
                   disposition="new_fact", mode="induction", warrant="census")
        step = pc.to_chain().steps[-1]
        assert step.rule_name == "ADMIT_TO_M"
        assert step.parameters["derivation"] == ["INS"]
        assert step.parameters["warrant"] == "census"
        assert nav.same_graph(
            m_view(pc.current),
            parse_egif(f'{M0} (swan "Dover") (white "Dover")'))

    def test_admit_is_ampliative(self):
        pc = _chain_from(M0)
        admit_step(pc, '(swan "Dover")')
        assert character_of_chain(pc.to_chain()).character == "ampliative"

    def test_refuses_without_scroll(self):
        pc = ProofChain(parse_egif(M0))   # sheet-level M, no scroll
        with pytest.raises(ValueError, match="world-scroll"):
            admit_step(pc, '(swan "Dover")')


class TestReviseStep:
    def test_world_withdrawal_executes_and_records(self):
        pc = _chain_from(M0)
        new_m = '(swan "Ciel") (white "Ciel") (swan "Nox") (black "Nox")'
        revise_step(pc, new_m, subgraph_egif=LAW,
                    fact_egif='(swan "Nox") (black "Nox")',
                    reason="the black swan")
        step = pc.to_chain().steps[-1]
        assert step.rule_name == "REVISE_M"
        assert step.parameters["derivation"] == ["ERA", "DC+", "INS"]
        assert step.parameters["subgraph_egif"] == LAW
        assert nav.same_graph(m_view(pc.current), parse_egif(new_m))
        assert find_world_scroll(pc.current) is not None

    def test_dag_keeps_the_withdrawn_world(self):
        pc = _chain_from(M0)
        withdrawn_id = pc.current_state_id
        revise_step(pc, '(swan "Nox")')
        chain = pc.to_chain()
        assert chain.steps[-1].from_state_id == withdrawn_id
        assert nav.same_graph(m_view(chain.states[withdrawn_id]),
                              parse_egif(M0))


class TestRetractStep:
    def test_retraction_is_recorded_and_real(self):
        pc = _chain_from(M0)
        retract_step(pc, relation="white", labels=["Ciel"],
                     disposition="retract_fact", reason="deprecated value")
        step = pc.to_chain().steps[-1]
        assert step.rule_name == "RETRACT_FROM_M"
        assert step.parameters["act"] == "m_retraction"
        assert step.parameters["derivation"] == ["ERA"]
        assert step.parameters["relation"] == "white"
        assert step.parameters["earned"] is True
        assert nav.same_graph(
            m_view(pc.current), parse_egif(f'(swan "Ciel") {LAW}'))

    def test_flavor_records_the_faded_tense(self):
        # disuse-decay and refutation are ONE licensed move, distinguished by
        # the recorded disposition/flavor (§9.7's "faded"; D6's pruned:disuse)
        pc = _chain_from(M0)
        retract_step(pc, relation="white", labels=["Ciel"],
                     flavor="pruned:disuse")
        step = pc.to_chain().steps[-1]
        assert step.parameters["flavor"] == "pruned:disuse"
        assert step.parameters["derivation"] == ["ERA"]

    def test_law_retraction_is_one_era(self):
        # the swan relinquishment collapses to ONE move (§9.3)
        pc = _chain_from(M0)
        retract_step(pc, subgraph_egif=LAW, disposition="challenge_to_M")
        step = pc.to_chain().steps[-1]
        assert step.parameters["derivation"] == ["ERA"]
        assert nav.same_graph(
            m_view(pc.current), parse_egif('(swan "Ciel") (white "Ciel")'))

    def test_dag_keeps_the_prior_state(self):
        pc = _chain_from(M0)
        prior_id = pc.current_state_id
        retract_step(pc, subgraph_egif=LAW)
        chain = pc.to_chain()
        assert chain.steps[-1].from_state_id == prior_id
        assert nav.same_graph(m_view(chain.states[prior_id]), parse_egif(M0))

    def test_retract_is_ampliative(self):
        pc = _chain_from(M0)
        retract_step(pc, relation="white", labels=["Ciel"])
        assert character_of_chain(pc.to_chain()).character == "ampliative"

    def test_refuses_without_scroll(self):
        pc = ProofChain(parse_egif(M0))
        with pytest.raises(ValueError, match="world-scroll"):
            retract_step(pc, relation="white")


class TestChallengeStep:
    def test_challenge_is_one_composite_step(self):
        """The black-swan move: ERA the law + INS the anomaly, ONE step."""
        pc = _chain_from(M0)
        n_states = len(pc.to_chain().states)
        challenge_step(pc, subgraph_egif=LAW,
                       fact_egif='(swan "Nox") (black "Nox")',
                       reason="the black swan")
        chain = pc.to_chain()
        step = chain.steps[-1]
        assert step.rule_name == "REVISE_M"
        assert step.parameters["act"] == "m_revision"
        assert step.parameters["derivation"] == ["ERA", "INS"]
        assert len(chain.states) == n_states + 1   # one step, one new state
        assert nav.same_graph(
            m_view(pc.current),
            parse_egif('(swan "Ciel") (white "Ciel") (swan "Nox") '
                       '(black "Nox")'))

    def test_husk_stands_as_scar(self):
        pc = _chain_from(LAW)   # M is just the law
        challenge_step(pc, subgraph_egif=LAW, fact_egif='(black "Nox")')
        scroll = find_world_scroll(pc.current)
        # the emptied cell reads as a second empty cut beside the hold
        assert len(scroll.hold_ids) == 2
        assert len(scroll.cell_ids) == 1   # the anomaly's fresh cell

    def test_requires_content(self):
        pc = _chain_from(M0)
        with pytest.raises(ValueError, match="requires"):
            challenge_step(pc)


class TestTrajectory:
    def test_swan_trajectory_shape(self):
        """The dialogue_swan_revision shape in miniature: peel, challenge,
        peel — verdicts flip TRUE → FALSE, the revision ONE licensed step."""
        pc = _chain_from(M0)
        r1 = peel_step(pc, PROPOSAL, closed=True)
        assert r1.verdict.value == "true"
        challenge_step(
            pc, subgraph_egif=LAW,
            fact_egif='(swan "Nox") (black "Nox") ~[ (black *y) (white y) ]')
        r2 = peel_step(pc, PROPOSAL, closed=True)
        assert r2.verdict.value == "false"

    def test_world_withdrawal_trajectory_still_available(self):
        """The triple remains the rare full-replacement path."""
        pc = _chain_from(M0)
        revise_step(
            pc,
            '(swan "Ciel") (white "Ciel") (swan "Nox") (black "Nox") '
            '~[ (black *y) (white y) ]',
            subgraph_egif=LAW)
        r2 = peel_step(pc, PROPOSAL, closed=True)
        assert r2.verdict.value == "false"
