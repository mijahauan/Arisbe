"""
FOLIO on Arisbe's own bounded engine (``src/folio_native.py``) — the soundness×coverage
half of the "Both" FOLIO evaluation.

The contract under test is the DL one: the bounded reasoner may **abstain** (``Unknown``)
freely, but a *decided* verdict (``True`` / ``False``) must be **sound** — it never
contradicts gold.  These tests pin the two sound provers (denial-based refutation +
freeze-a-witness), the soundness guard against existential-under-negation, and the honest
abstention everywhere else.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from folio_fol import Atom, BinOp, Not, Quant
from folio_native import (
    NativeResult,
    _denial_reading_unsound,
    decide_native,
    normalize,
)


# ---------------------------------------------------------------------------
# The two sound provers
# ---------------------------------------------------------------------------

def test_ground_entailment_is_true():
    """A Horn chain + a ground fact entails a ground atom (refutation)."""
    r = decide_native(
        ["∀x (Dog(x) → Mammal(x))", "∀x (Mammal(x) → Animal(x))", "Dog(rex)"],
        "Animal(rex)")
    assert r.verdict == "True" and r.via == "refutation"


def test_subsumption_is_true_via_theory_query():
    """A universal conclusion carries no denial to fire — freeze-a-witness recovers it."""
    r = decide_native(
        ["∀x (Dog(x) → Mammal(x))", "∀x (Mammal(x) → Animal(x))"],
        "∀x (Dog(x) → Animal(x))")
    assert r.verdict == "True" and r.via == "theory_query"


def test_disjointness_contradiction_is_false():
    """A disjointness rule ``∀x (A→¬B)`` + the antecedent contradicts the consequent."""
    r = decide_native(["∀x (Cat(x) → ¬Dog(x))", "Cat(felix)"], "Dog(felix)")
    assert r.verdict == "False" and r.via == "refutation"


def test_negative_conclusion_through_a_chain_is_true():
    """``¬Dog(t)`` is entailed via a subclass chain into a disjointness."""
    r = decide_native(
        ["∀x (Cat(x) → ¬Dog(x))", "∀x (Tabby(x) → Cat(x))", "Tabby(t)"], "¬Dog(t)")
    assert r.verdict == "True"


# ---------------------------------------------------------------------------
# Honest abstention
# ---------------------------------------------------------------------------

def test_open_world_non_entailment_abstains():
    """``Mammal(spot)`` does not make ``Dog(spot)`` derivable — abstain, never guess."""
    r = decide_native(["∀x (Dog(x) → Mammal(x))", "Mammal(spot)"], "Dog(spot)")
    assert r.verdict == "Unknown" and not r.decided


def test_never_predicts_uncertain():
    """The bounded engine emits only True / False / Unknown / Unparsed — never Uncertain
    (soundly certifying 'neither' needs a completeness it does not have)."""
    r = decide_native(["∀x (P(x) ∨ Q(x))"], "P(a)")
    assert r.verdict in ("True", "False", "Unknown", "Unparsed")
    assert r.verdict != "Uncertain"


def test_unparsed_passes_through():
    r = decide_native(["Dog(rex,"], "Animal(rex)")
    assert r.verdict == "Unparsed" and not r.parsed


# ---------------------------------------------------------------------------
# The soundness guard — existential under negation
# ---------------------------------------------------------------------------

def test_existential_under_negation_is_flagged():
    """``∃x (P(x) ∧ ¬Q(x))`` puts a witness line under a negation — the universal-denial
    reading would over-fire, so it is flagged unsound."""
    ex = Quant("exists", "x",
               BinOp("and", Atom("P", ("x",)), Not(Atom("Q", ("x",)))))
    assert _denial_reading_unsound([ex]) is True


def test_universal_disjointness_is_sound():
    """``∀x ¬(A(x) ∧ B(x))`` — the line is universal, so the denial reading is sound."""
    disj = Quant("forall", "x", Not(BinOp("and", Atom("A", ("x",)), Atom("B", ("x",)))))
    assert _denial_reading_unsound([disj]) is False


def test_negative_constant_literal_is_sound():
    """A negation over a *constant* (not a bound variable) is a sound denial."""
    assert _denial_reading_unsound([Not(Atom("Q", ("a",)))]) is False


def test_existential_premise_abstains_not_errs():
    """The FOLIO shape that exposed the bug: an existential-negative premise must make the
    engine ABSTAIN, not emit a spurious False (gold here is genuinely Uncertain)."""
    r = decide_native(
        ["∃x (BasketballPlayer(x) ∧ ¬American(x))",
         "∀x (BasketballPlayer(x) → Tall(x))"],
        "American(yuri)")
    assert r.verdict == "Unknown"


def test_existential_negative_conclusion_abstains():
    """``∃x (Evergreen(x) ∧ ¬ObjectOfWorship(x))`` against fir-tree premises is genuinely
    Uncertain — the engine must not refute it into a False."""
    r = decide_native(
        ["∀x (FirTree(x) → Evergreen(x))",
         "∃x (ObjectOfWorship(x) ∧ FirTree(x))"],
        "∃x (Evergreen(x) ∧ ¬ObjectOfWorship(x))")
    assert r.verdict == "Unknown"


# ---------------------------------------------------------------------------
# normalize — the meaning-preserving rewrites toward recognised shapes
# ---------------------------------------------------------------------------

def test_normalize_disjointness_to_denial():
    """``A → ¬B`` becomes ``¬(A ∧ B)`` so it builds as a flat denial."""
    out = normalize(BinOp("implies", Atom("A", ("x",)), Not(Atom("B", ("x",)))))
    assert isinstance(out, Not) and isinstance(out.f, BinOp) and out.f.op == "and"


def test_normalize_exportation():
    """``L → (R → S)`` becomes ``(L ∧ R) → S`` — one Horn rule with a conjunctive body."""
    out = normalize(BinOp("implies", Atom("L", ()),
                          BinOp("implies", Atom("R", ()), Atom("S", ()))))
    assert isinstance(out, BinOp) and out.op == "implies"
    assert isinstance(out.left, BinOp) and out.left.op == "and"


# ---------------------------------------------------------------------------
# The headline invariant: soundness on a curated FOLIO-shaped sample
# ---------------------------------------------------------------------------

# (premises, conclusion, gold) — a handful of each label, including the shapes that
# exposed the two soundness bugs.  Every DECIDED verdict must match gold.
_SAMPLE = [
    (["∀x (Dog(x) → Mammal(x))", "Dog(rex)"], "Mammal(rex)", "True"),
    (["∀x (A(x) → B(x))", "∀x (B(x) → C(x))", "A(a)"], "C(a)", "True"),
    (["∀x (Cat(x) → ¬Dog(x))", "Cat(c)"], "Dog(c)", "False"),
    (["∀x (Penguin(x) → Bird(x))", "Bird(tweety)"], "Penguin(tweety)", "Uncertain"),
    (["∃x (P(x) ∧ ¬Q(x))", "∀x (P(x) → R(x))"], "Q(a)", "Uncertain"),
    (["∀x (FirTree(x) → Evergreen(x))", "∃x (Worship(x) ∧ FirTree(x))"],
     "∃x (Evergreen(x) ∧ ¬Worship(x))", "Uncertain"),
]


def test_soundness_on_sample():
    """No decided verdict contradicts gold (soundness = 1.0); coverage is incidental."""
    wrong = []
    for premises, conclusion, gold in _SAMPLE:
        r = decide_native(premises, conclusion)
        if r.decided and r.verdict != gold:
            wrong.append((premises, conclusion, gold, r.verdict))
    assert not wrong, f"unsound verdicts: {wrong}"


def test_decided_results_carry_a_provenance():
    r = decide_native(["Cat(c)", "∀x (Cat(x) → ¬Dog(x))"], "Dog(c)")
    assert isinstance(r, NativeResult) and r.decided and r.via and r.detail
