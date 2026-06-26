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
    # Doctor step-7's narration to claim it *erases S* (S as operated object).
    # The move does not touch the S edge (S persists), so S has no bearer in the
    # focal set Φ — center coverage must drop below 100 %.  This proves the
    # 100 % on the real chain is earned, not vacuous.
    real = _step(chain, "step-7")
    doctored = replace(real, narration="Erase S.")
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
