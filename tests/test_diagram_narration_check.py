"""The diagram↔narration correspondence check (prototype of the §10 harness in
``docs/THE_MINIMAL_IN_VIEW_SET.md``).

These tests pin three things:
  1. the harness loads the transcribed Praeclarum chain and scores it;
  2. the operated/locative narration split and the structural decomposition are
     what the §10 design specifies (so the 100 % result is *earned*, not an
     artifact of a trivial metric);
  3. the metric actually *bites* — a doctored narration that claims to operate on
     a predicate the move never touches scores < 100 % (the falsifier).
"""

from dataclasses import replace
from pathlib import Path

import pytest

from diagram_narration_check import (
    ChainReport,
    WorkedStep,
    _relation_alphabet,
    check_chain,
    honest_limits,
    load_worked_chain,
    parse_narration,
    score_step,
    step_sets,
)

PRAECLARUM = Path(__file__).resolve().parent.parent / "tomos/universes/theorem_praeclarum"


@pytest.fixture(scope="module")
def chain():
    return load_worked_chain(PRAECLARUM)


@pytest.fixture(scope="module")
def alphabet(chain):
    return _relation_alphabet(chain)


def _step(chain, step_id) -> WorkedStep:
    return next(s for s in chain.steps if s.step_id == step_id)


# --- loading -----------------------------------------------------------------


def test_loads_seven_steps_with_narration_and_egis(chain):
    assert len(chain.steps) == 7
    assert chain.initial_state_id == "s0"
    for s in chain.steps:
        assert s.narration  # every step carries a transcribed narration
        assert s.from_egi is not None and s.to_egi is not None
    # the chain alphabet is exactly the Praeclarum predicates
    assert _relation_alphabet(chain) == {"P", "Q", "R", "S"}


def test_missing_chain_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_worked_chain(tmp_path)


# --- structural decomposition (step_sets) ------------------------------------


def test_ins_step_adds_all_four_predicates(chain):
    # step-2 inserts the antecedent (P⊃R)(Q⊃S): four predicate edges appear.
    sets = step_sets(_step(chain, "step-2"))
    added_rels = {
        _step(chain, "step-2").to_egi.rel.get(e) for e in sets.added
    } - {None}
    assert added_rels == {"P", "Q", "R", "S"}
    assert not sets.removed


def test_deiterate_step_removes_the_redundant_copy(chain):
    # step-6 IT- deiterates the inner Q: structure is *removed*, none added.
    sets = step_sets(_step(chain, "step-6"))
    assert sets.removed
    assert not sets.added


def test_dc_minus_removes_a_cut(chain):
    # step-7 DC- erases the double cut around S: cuts removed, S persists.
    sets = step_sets(_step(chain, "step-7"))
    assert sets.removed  # the double cut goes
    # S itself is standing material, not removed.
    to_egi = _step(chain, "step-7").to_egi
    assert any(to_egi.rel.get(e.id) == "S" for e in to_egi.E)


# --- the operated/locative narration split -----------------------------------


def test_insert_into_locus_splits_object_from_address(chain, alphabet):
    # "Insert Q into the cut holding the iterated (P⊃R)":
    #   Q is the operated object; P,R only name the address.
    parse = parse_narration(_step(chain, "step-4"), alphabet)
    assert parse.operated_tokens == {"Q"}
    assert parse.locative_tokens == {"P", "R"}
    assert parse.introduces and parse.references_prior


def test_erase_double_cut_around_S_is_purely_locative(chain, alphabet):
    # "Erase the double cut around S": the operated thing is a *cut* (no
    # predicate token); S is only the locative anchor.
    parse = parse_narration(_step(chain, "step-7"), alphabet)
    assert parse.operated_tokens == set()
    assert parse.locative_tokens == {"S"}


def test_iterate_object_before_locus(chain, alphabet):
    # "Iterate (Q⊃S) into the cut around R": Q,S operated; R locative.
    parse = parse_narration(_step(chain, "step-5"), alphabet)
    assert parse.operated_tokens == {"Q", "S"}
    assert parse.locative_tokens == {"R"}


def test_restatement_role_is_distinguished_from_operated():
    # The third role the corpus forced: a predicate in a clause restating the
    # resulting proposition (after a dash / arrow / result verb) is restatement,
    # not the operated object.  Use branching_confluence step-2 "Then erase (Q),
    # leaving (R)": Q is erased (operated), R only names what is left (restatement).
    branching = load_worked_chain(
        PRAECLARUM.parent / "branching_confluence")
    alpha = _relation_alphabet(branching)
    step2 = next(s for s in branching.steps if s.step_id == "step-2")
    parse = parse_narration(step2, alpha)
    assert parse.operated_tokens == {"Q"}
    assert parse.restatement_tokens == {"R"}
    assert "R" not in parse.operated_tokens


# --- the headline result: the bridge holds on Praeclarum ---------------------


def test_praeclarum_bridge_holds(chain):
    report = check_chain(chain)
    assert isinstance(report, ChainReport)
    # operated predicates all land in the focal set Φ; locative anchors all
    # resolve to standing material Ρ; every stance is structurally witnessed.
    assert report.mean_center_coverage == pytest.approx(1.0)
    assert report.mean_locative_grounding == pytest.approx(1.0)
    assert report.reference_alignment_rate == pytest.approx(1.0)


def test_praeclarum_is_sub_budget_and_says_so(chain):
    report = check_chain(chain)
    assert report.sub_budget is True
    limits = honest_limits(report)
    assert any("sub-budget" in lim for lim in limits)
    # the deterministic-alignment caveat is always surfaced
    assert any("nl_to_logic" in lim for lim in limits)


# --- the falsifier: the metric must be able to fail --------------------------


def test_operated_token_outside_focus_fails_center_coverage(chain, alphabet):
    # Doctor step-3 (IT+ iterating (P⊃R)) to claim it *operates on S*.  S is
    # untouched by this move and lies outside the focal set Φ even after the D3
    # effect set (it is not in any cut whose scope changed), so center coverage
    # must drop below 100 %.  This proves the corpus 100 % is earned, not vacuous.
    real = _step(chain, "step-3")
    doctored = replace(real, narration="Iterate S into the inner cut.")
    parse = parse_narration(doctored, alphabet)
    assert parse.operated_tokens == {"S"}  # now claimed as the object

    score = score_step(doctored, alphabet)
    assert "S" in score.uncovered_operated
    assert score.center_coverage < 1.0


def test_locative_token_on_fresh_material_fails_grounding(chain, alphabet):
    # Doctor step-2 (which ADDS P,Q,R,S) to *locate* by R: "Insert Q into the
    # cut around R".  R was just introduced by this very move (not standing),
    # so the locative anchor is ungrounded — grounding must drop below 100 %.
    real = _step(chain, "step-2")
    doctored = replace(real, narration="Insert Q into the cut around R.")
    parse = parse_narration(doctored, alphabet)
    assert "R" in parse.locative_tokens

    score = score_step(doctored, alphabet)
    assert "R" in score.ungrounded_locative
    assert score.locative_grounding < 1.0


# --- the corpus result: the three salience roles hold everywhere -------------

# Every worked chain in the corpus that carries a narration.
CORPUS = [
    "barbara", "beta_converse_mp", "beta_modus_ponens", "branching_confluence",
    "group_identity", "peirce_law", "theorem_praeclarum",
]


@pytest.mark.parametrize("uod", CORPUS)
def test_three_salience_roles_hold_across_the_corpus(uod):
    # Across all seven transcribed chains, every operated predicate lands in Φ,
    # every locative anchor resolves to standing Ρ, and every restated upshot is
    # in-view V.  This is the headline corpus result — the diagram↔narration
    # bridge holds for all three Centering/DRT roles.
    report = check_chain(load_worked_chain(PRAECLARUM.parent / uod))
    assert report.mean_center_coverage == pytest.approx(1.0)
    assert report.mean_locative_grounding == pytest.approx(1.0)
    assert report.mean_restatement_in_view == pytest.approx(1.0)


def test_macro_step_misaligns_an_honest_residual():
    # group_identity step-1 is a SQUASHED macro move ("insert the f-connection,
    # merge, erase the freed double cut"): the narration's stance is *introduce*
    # ("(M e f f) asserted on the sheet"), yet the net chain-step delta is pure
    # removal — so reference-alignment honestly fails.  The harness must flag
    # this (the D4 squash phenomenon), not paper over it.
    report = check_chain(load_worked_chain(PRAECLARUM.parent / "group_identity"))
    step1 = report.steps[0]
    assert step1.narr_introduces
    assert not step1.struct_adds          # the squashed delta only removes
    assert step1.reference_aligned is False
    # it is the *only* misalignment in the corpus
    assert report.reference_alignment_rate < 1.0
