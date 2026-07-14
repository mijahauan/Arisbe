"""**The arena** — the place set aside for testing (`src/contest_context.py`).

A contest must happen *somewhere*, and that somewhere must be a **negated context**,
so that what happens inside cannot ramify outward. The author's OS-sandbox analogy is
exact — and, unusually, it is a **theorem** rather than a convention:

* the sheet **asserts**, so there is nowhere on a blank sheet to put a hypothesis
  without thereby claiming it;
* **Insertion is sound only in a negative context** — that IS the isolation
  guarantee: whatever you scribe there, the enclosing sheet stays true;
* **DC+ is the only move that makes such a place while asserting nothing** — the
  empty double cut is logically inert, yet it creates a negative arena (posit here)
  and a positive hold (conclude here). Filled, it is a **scroll**: A → B.

And the corpus already obeys it, which is the evidence that it was not invented after
the fact: every proof starting from the blank sheet begins **DC+ then INS**.
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from contest_context import (  # noqa: E402
    Arena, is_arena, open_arena, polarity_of, posit, preparatory_moves,
)
from egif_generator_dau import generate_egif  # noqa: E402
from egif_parser_dau import parse_egif  # noqa: E402
from proof_authoring import apply_rule  # noqa: E402


# --- the preparatory step is FORCED, not stylistic --------------------------- #

def test_a_blank_sheet_must_first_MAKE_a_place():
    """There is no negative context on a blank sheet, so nothing can be supposed
    there. The first act of a contest from nothing is to build the arena."""
    assert preparatory_moves(parse_egif("")) == ["DC+"]


def test_a_graph_that_already_carries_a_cut_needs_no_preparation():
    """The place is already there — posit straight into it. (This is why
    `ex_falso_quodlibet`, which starts from `~[ (P) ]`, goes straight to INS.)"""
    assert preparatory_moves(parse_egif("~[ (P) ]")) == []


def test_the_arena_asserts_nothing():
    """DC+ is logically inert: the graph after says exactly what the graph before
    said. Making a place to test in must not itself be a claim."""
    g, _ = open_arena(parse_egif(""))
    assert generate_egif(g).strip() == "~[ ~[ ] ]"      # the empty double cut


def test_the_arena_is_negative_and_the_hold_is_positive():
    g, arena = open_arena(parse_egif(""))
    assert polarity_of(g, arena.arena) == "negative"    # posit here — free, sound
    assert polarity_of(g, arena.hold) == "positive"     # conclude here — must be earned
    assert is_arena(g, arena.arena) and not is_arena(g, arena.hold)


# --- the isolation guarantee: a malfunction within does not ramify outward ---- #

def test_positing_wild_content_in_the_arena_cannot_disturb_the_sheet():
    """THE SANDBOX. Whatever is supposed inside the arena, everything the sheet
    asserted outside it still stands. This is not a policy — it is the soundness of
    Insertion in a negative context."""
    sheet = parse_egif('(Established "a")')
    g, arena = open_arena(sheet)
    g = posit(g, arena, "(Wild *z) (Nonsense z)")
    out = generate_egif(g)
    assert '(Established "a")' in out          # the assertion survives, untouched
    assert "Wild" in out and "Nonsense" in out  # …and the supposition is FENCED inside


def test_you_may_suppose_freely_but_not_conclude_freely():
    """The asymmetry IS the guarantee. Insertion into the negative arena is
    permitted; insertion into the positive hold is REFUSED — a conclusion has to be
    earned, not scribed. You can suppose anything; you cannot conclude anything."""
    g, arena = open_arena(parse_egif(""))
    posit(g, arena, "(Human *x)")              # free
    with pytest.raises(AssertionError, match="negative"):
        apply_rule("INS", g, egif="(Mortal *y)", target=arena.hold)


def test_positing_outside_a_negative_context_is_refused_with_a_reason():
    """Positing on the sheet would ASSERT the hypothesis, not suppose it. The module
    refuses, and says why — never silently."""
    g = parse_egif("")
    fake = Arena(arena=g.sheet, hold=g.sheet)          # the sheet is positive
    with pytest.raises(ValueError, match="negative context"):
        posit(g, fake, "(P *x)")


# --- the corpus already obeys this ------------------------------------------- #

@pytest.mark.parametrize("uod_id", ["peirce_law", "theorem_praeclarum"])
def test_blank_sheet_proofs_in_the_corpus_begin_by_making_the_place(uod_id):
    """The evidence that this is discovered, not decreed: every proof in the corpus
    that starts from the blank sheet opens with DC+ (make the arena) and then INS
    (posit into it). It could not be otherwise — insertion has nowhere else to go."""
    from tomos_service import TomosService
    chain = TomosService(REPO / "tomos").load_chain(uod_id)
    if chain is None or not chain.steps:
        pytest.skip(f"{uod_id} carries no chain")
    start = generate_egif(chain.states[chain.initial_state_id]).strip()
    assert start == "", f"{uod_id} does not start from the blank sheet"
    rules = [s.rule_name for s in chain.steps]
    assert rules[0] == "DC+", "a blank-sheet proof must first MAKE the place"
    assert "INS" in rules[:3], "…and then posit into it"
    # and the preparatory reader agrees with the corpus, on the corpus's own graph
    assert preparatory_moves(chain.states[chain.initial_state_id]) == ["DC+"]


def test_a_corollarial_proof_never_opens_an_arena():
    """`beta_modus_ponens` needs no insertion (it only unpacks what is given), so it
    never posits, so it never needs a place to posit in. The arena is required
    exactly when something must be SUPPOSED."""
    from tomos_service import TomosService
    chain = TomosService(REPO / "tomos").load_chain("beta_modus_ponens")
    if chain is None or not chain.steps:
        pytest.skip("no chain")
    rules = [s.rule_name for s in chain.steps]
    assert "INS" not in rules and "DC+" not in rules


# --- where the transport IS needed, and where it is NOT ---------------------- #
# The author's inference: adding needs a negative context, removing needs a positive
# one, so a model must be manageable in both — "lots of moving around". Both halves
# are true, but they land on DIFFERENT operations, and the split is the point.

from contest_context import carry_in, deliberate, sheet_elements  # noqa: E402
from proof_authoring import apply_rule  # noqa: E402
import eg_navigation as _nav  # noqa: E402

M_EGIF = '(swan "Ciel") ~[ (swan *x) ~[ (white x) ] ]'


def test_REVISING_M_needs_no_transport_at_all():
    """Committing is cheap and LOCAL.

    Remove: ERA acts in place — M sits on the sheet, which is positive.
    Add: no rule applies at all, so there is nothing to reposition; you juxtapose,
         and pay in warrant (model_acts).
    Neither move requires carrying M anywhere."""
    m = parse_egif(M_EGIF)
    law = _nav.cut_holding_relation(m, m.sheet, "swan")
    out = apply_rule("ERA", m, selection=[law])          # in place, no arena
    assert "~[" not in generate_egif(out)                # the law is gone


def test_DELIBERATING_about_M_is_where_the_transport_lives():
    """Thinking is expensive and requires MOVING:
         DC+  open the arena (negative; asserts nothing)
         IT+  carry a working copy of M inside (less- → more-enclosed: sound)
         INS  posit the hypothesis there (the context is negative: sound)"""
    m = parse_egif(M_EGIF)
    g, arena = deliberate(m, '(swan "Nox") (black "Nox")')
    out = generate_egif(g)
    # M is still asserted OUTSIDE — untouched
    assert '(swan "Ciel")' in out
    # …and a working copy + the hypothesis are FENCED inside the arena
    inside = _nav.child_edges(g, arena.arena)
    names = {g.rel[e] for e in inside if e in g.rel}
    assert "black" in names and "swan" in names


def test_nothing_derived_inside_the_fence_changes_M():
    """THE SAFETY PROPERTY that makes the transport worth its cost. You may reason
    freely under a working copy of M — and M itself is not touched by any of it. What
    the arena can yield is a CONDITIONAL, never a new assertion about M."""
    m = parse_egif(M_EGIF)
    before = generate_egif(m)
    g, arena = deliberate(m, '(black "Nox")')
    # go on supposing wild things inside — M outside is still exactly M
    g = apply_rule("INS", g, egif="(Anything *z)", target=arena.arena)
    sheet_now = {g.rel[e] for e in _nav.child_edges(g, g.sheet) if e in g.rel}
    assert "Anything" not in sheet_now
    assert '(swan "Ciel")' in before and '(swan "Ciel")' in generate_egif(g)


def test_carry_in_uses_iteration_in_its_licensed_direction():
    """IT+ copies from a LESS-enclosed context into a MORE-enclosed one — sheet
    (depth 0) → arena (depth 1) is exactly its direction, and it is sound as a
    weakening: A → B entails (A ∧ M) → B."""
    m = parse_egif(M_EGIF)
    g, arena = open_arena(m)
    g2 = carry_in(g, arena, sheet_elements(m))
    assert polarity_of(g2, arena.arena) == "negative"
    assert len(_nav.child_edges(g2, arena.arena)) >= 1     # M's content arrived
