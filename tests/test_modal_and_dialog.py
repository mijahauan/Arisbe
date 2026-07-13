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
import build_swan_generalization as swan  # noqa: E402


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
# settlement — the forcing three-case table as a named reading                 #
# (docs/FORCING_AND_THE_GAMMA_CROSSING.md §2/§6)                              #
# --------------------------------------------------------------------------- #

def test_settlement_three_cases(modal_chain):
    """□ → settled; ◇∧¬□ → open; ¬◇ → excluded — Cohen's ∅-forces / some-π-forces /
    no-π-forces table read as trajectory semantics."""
    assert mq.settlement(modal_chain, mq.scribes_relation("cold")).status == "settled"
    s = mq.settlement(modal_chain, mq.scribes_relation("cloudy"))
    assert s.status == "open"
    assert s.possible.holds and not s.necessary.holds
    assert "open" in s.summary
    assert mq.settlement(modal_chain, mq.scribes_relation("sunny")).status == "excluded"


def test_settlement_over_leaves_differs_from_states(modal_chain):
    """The transient (cloudy) is open over all reachable states but excluded over
    trajectory endpoints — the reading names its worlds honestly."""
    assert mq.settlement(modal_chain, mq.scribes_relation("cloudy"),
                         over="leaves").status == "excluded"
    assert mq.settlement(modal_chain, mq.scribes_relation("cold"),
                         over="leaves").status == "settled"


def test_settlement_is_deterministic(modal_chain):
    a = mq.settlement(modal_chain, mq.scribes_relation("cloudy"))
    b = mq.settlement(modal_chain, mq.scribes_relation("cloudy"))
    assert (a.status, a.possible.witnesses, a.necessary.counterexamples) == \
           (b.status, b.possible.witnesses, b.necessary.counterexamples)


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


# --------------------------------------------------------------------------- #
# model_revision across the inning-outcome taxonomy                            #
# --------------------------------------------------------------------------- #
#
# The EPG taxonomy of game outcomes (docs/ENDOPOREUTIC_GAME_GUIDE.md §"Taxonomy")
# informs M-revision: only a subset of dispositions transform M, each in a distinct
# Peircean mode. REVISION_TAXONOMY names that subset; revise_with_disposition enacts it.


def test_revision_taxonomy_names_modes_and_kinds():
    """Each M-revising disposition carries a Peircean mode + a structural kind."""
    new_fact = mr.revision_taxonomy(mr.DISPOSITION_NEW_FACT)
    assert new_fact["mode"] == "induction" and new_fact["kind"] == "enlargement"
    challenge = mr.revision_taxonomy(mr.DISPOSITION_CHALLENGE_M)
    assert challenge["mode"] == "abduction" and challenge["kind"] == "relinquishment"
    gen = mr.revision_taxonomy(mr.DISPOSITION_GENERALIZATION)
    assert gen["mode"] == "induction" and gen["content"] == "rule"
    # All three Peircean modes appear across the revising subset.
    modes = {v["mode"] for v in mr.REVISION_TAXONOMY.values()}
    assert {"induction", "deduction", "abduction"} <= modes


def test_non_revising_disposition_is_rejected():
    """A recorded-judgment disposition (no M edit) is not a revision."""
    for key in ("redundancy", "rejection", "open_conjecture", "tautology"):
        with pytest.raises(ValueError):
            mr.revision_taxonomy(key)
        with pytest.raises(ValueError):
            mr.revise_with_disposition(parse_egif("(swan \"a\")"), key)


def test_add_rule_then_retract_subgraph_round_trips():
    """add_rule juxtaposes a law; retract_subgraph erases that sheet-level cut as a
    unit (a genuine ERA) and re-admitting it reconstructs M."""
    m = parse_egif('(swan "a") (white "a")')
    law = '~[ (swan *x) ~[ (white x) ] ]'
    grown = mr.add_rule(m, law)
    assert any(True for _ in nav.child_cuts(grown, grown.sheet)), "the law is a sheet cut"
    shrunk = mr.retract_subgraph(grown, law)
    assert nav.same_graph(shrunk, m), "retracting the law restores the fact-only model"
    # Retracting an absent subgraph is refused (a retraction must have a target).
    with pytest.raises(ValueError):
        mr.retract_subgraph(m, law)


def test_generalization_law_covers_a_newcomer():
    """A generalization (a law) materializes onto a new individual where a bare
    fact-list would not — deduction over an inductive leap."""
    base = parse_egif('(swan "a") (white "a")')
    with_law = mr.revise_with_disposition(base, mr.DISPOSITION_GENERALIZATION,
                                          rule_egif='~[ (swan *x) ~[ (white x) ] ]')
    with_newcomer = mr.revise_with_disposition(with_law, mr.DISPOSITION_NEW_FACT,
                                               fact_egif='(swan "b")')
    # The law covers swan b: "every swan is white" still holds.
    assert swan._verdict(with_newcomer) == "true"
    # Without the law, the bare newcomer would flip it FALSE.
    bare = mr.revise_with_disposition(base, mr.DISPOSITION_NEW_FACT, fact_egif='(swan "b")')
    assert swan._verdict(bare) == "false"


def test_challenge_to_M_relinquishes_the_law_and_admits_the_anomaly():
    """challenge_to_M (2b, abduction) retracts the impugned law and admits the
    refuting anomaly in one revision."""
    m = parse_egif('(swan "a") (white "a")')
    m = mr.add_rule(m, '~[ (swan *x) ~[ (white x) ] ]')
    revised = mr.revise_with_disposition(
        m, mr.DISPOSITION_CHALLENGE_M,
        subgraph_egif='~[ (swan *x) ~[ (white x) ] ]',
        fact_egif='(swan "n") (black "n")')
    assert swan._verdict(revised) == "false"          # the law is gone; n is a non-white swan
    assert not any(True for _ in nav.child_cuts(revised, revised.sheet)), "the law was relinquished"


# --------------------------------------------------------------------------- #
# The swan exemplar — a verdict moving across the taxonomy of modes             #
# --------------------------------------------------------------------------- #

def test_swan_exemplar_walks_the_taxonomy():
    """'Every swan is white' moves FALSE→TRUE→TRUE→TRUE→FALSE as the dialogue
    observes (induction), generalizes (induction), admits a covered newcomer, then
    meets the black swan and revises M (abduction)."""
    chain, _uod = swan.build_swan_chain()
    verdicts = [swan._verdict(chain.states[chain.initial_state_id])] + [
        swan._verdict(chain.states[s.to_state_id]) for s in chain.steps]
    assert verdicts == ["false", "true", "true", "true", "false"]
    # The exemplar exercises more than one mode (the contrast with the insurance walk).
    modes = {s.parameters.get("mode") for s in chain.steps}
    assert {"induction", "abduction"} <= modes
    dispositions = {s.parameters.get("disposition") for s in chain.steps}
    assert {"new_fact", "generalization", "challenge_to_M"} <= dispositions
