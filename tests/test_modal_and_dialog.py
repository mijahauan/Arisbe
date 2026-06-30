"""
Tests for the second exemplar pass (docs/EXEMPLARS.md §5):

  * src/modal_query.py — read ◇/□ off the branching DAG (the trajectory reading of
    MODALITY_WITHOUT_GAMMA §1), exercised on the `possible_and_necessary` exemplar.
  * src/model_revision.py — the minimal step by which a model M transforms through
    dialog (enlargement / relinquishment), exercised on the `dialogue_model_revision`
    exemplar where the audited verdict flips as M is revised.
"""

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "tools"))

import eg_navigation as nav  # noqa: E402
from egif_parser_dau import parse_egif  # noqa: E402

import modal_query as mq  # noqa: E402
import model_revision as mr  # noqa: E402
import build_modal_branching as modal  # noqa: E402
import build_dialog_model_evolution as dialog  # noqa: E402


# --------------------------------------------------------------------------- #
# modal_query — ◇ / □ over the branching DAG                                   #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def modal_chain():
    chain, _uod = modal.build_modal_branching_chain()
    return chain


def test_frame_reachability(modal_chain):
    """The diamond: four reachable worlds from the root, one trajectory endpoint."""
    assert len(mq.reachable_states(modal_chain)) == 4
    leaves = mq.leaf_states(modal_chain)
    assert len(leaves) == 1  # both lines converge on a single (cold) endpoint


def test_necessity_is_convergence(modal_chain):
    """□(cold) — cold is scribed on every reachable sheet (necessity as convergence)."""
    r = mq.necessarily(modal_chain, mq.scribes_relation("cold"))
    assert r.holds and not r.counterexamples
    assert len(r.considered) == 4


def test_possibility_is_branching(modal_chain):
    """◇(cloudy) holds (some sheet) but □(cloudy) fails (not every sheet)."""
    assert mq.possibly(modal_chain, mq.scribes_relation("cloudy")).holds
    nec = mq.necessarily(modal_chain, mq.scribes_relation("cloudy"))
    assert not nec.holds and nec.counterexamples  # the worlds where cloudy is gone


def test_possibility_false_for_absent_relation(modal_chain):
    r = mq.possibly(modal_chain, mq.scribes_relation("sunny"))
    assert not r.holds and not r.witnesses


def test_leaves_reading_differs_from_states(modal_chain):
    """Over trajectory endpoints, the convergent (cold) is necessary but the
    transient (cloudy) is not even possible — it never survives to an endpoint."""
    assert mq.necessarily(modal_chain, mq.scribes_relation("cold"), over="leaves").holds
    assert not mq.possibly(modal_chain, mq.scribes_relation("cloudy"), over="leaves").holds


def test_equals_graph_and_is_blank_predicates(modal_chain):
    assert mq.possibly(modal_chain, mq.equals_graph("(cold)")).holds
    assert not mq.possibly(modal_chain, mq.is_blank()).holds


# --------------------------------------------------------------------------- #
# model_revision — enlargement / relinquishment                               #
# --------------------------------------------------------------------------- #

def test_assert_fact_enlarges():
    m = parse_egif('(patient "Ann")')
    m2 = mr.assert_fact(m, '(insured "Ann")')
    assert nav.same_graph(m2, parse_egif('(patient "Ann") (insured "Ann")'))


def test_retract_relation_relinquishes():
    m = parse_egif('(patient "Ann") (insured "Ann") (insured "Ben")')
    m2 = mr.retract_relation(m, "insured")
    assert nav.same_graph(m2, parse_egif('(patient "Ann")'))


def test_retract_absent_relation_raises():
    with pytest.raises(ValueError):
        mr.retract_relation(parse_egif('(patient "Ann")'), "insured")


def test_revise_with_disposition_dispatches():
    m = parse_egif('(patient "Ann")')
    grown = mr.revise_with_disposition(m, mr.DISPOSITION_NEW_FACT, fact_egif='(insured "Ann")')
    assert nav.same_graph(grown, parse_egif('(patient "Ann") (insured "Ann")'))
    shrunk = mr.revise_with_disposition(grown, mr.DISPOSITION_RETRACT, relation="insured")
    assert nav.same_graph(shrunk, parse_egif('(patient "Ann")'))


# --------------------------------------------------------------------------- #
# The dialogue exemplar — a verdict that flips as M is revised                 #
# --------------------------------------------------------------------------- #

def test_dialogue_audit_verdict_flips():
    """'Every patient is insured' moves FALSE→TRUE→FALSE→TRUE as the dialogue admits
    Ben's insurance, a new patient Cal, then Cal's coverage."""
    chain, _uod = dialog.build_dialogue_chain()
    verdicts = [dialog._verdict(chain.states[chain.initial_state_id])] + [
        dialog._verdict(chain.states[s.to_state_id]) for s in chain.steps]
    assert verdicts == ["false", "true", "false", "true"]


def test_dialogue_chain_records_revisions():
    chain, uod = dialog.build_dialogue_chain()
    assert len(chain.steps) == 3
    assert all(s.rule_name == "ADMIT_FACT" for s in chain.steps)
    assert all(s.parameters.get("disposition") == "new_fact" for s in chain.steps)
