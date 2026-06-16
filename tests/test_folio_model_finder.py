"""
The bounded finite-model finder (``src/folio_model_finder.py``) — the model-construction
half of the FOLIO coverage lever.

The contract: every model it *returns* is genuine (it independently satisfies the formula —
the ``satisfies`` guard); ``None`` certifies nothing.  On that rests the soundness of the
native engine's new ``Uncertain`` verdict, so these pin both the positive certificates and
the honest failures.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from folio_fol import parse_fol
from folio_model_finder import certify_independent, find_model, satisfies


def _p(*ss):
    return [parse_fol(s) for s in ss]


# ---------------------------------------------------------------------------
# Finding models — and the self-checking guard
# ---------------------------------------------------------------------------

def test_finds_a_model_and_it_checks_out():
    asts = _p("∀x (Dog(x) → Mammal(x))", "Dog(rex)")
    m = find_model(asts)
    assert m is not None
    assert satisfies(asts, m)                       # the guard agrees independently
    assert ("Dog", (m.constants["rex"],)) in m.true_atoms
    assert ("Mammal", (m.constants["rex"],)) in m.true_atoms


def test_existential_gets_an_anonymous_witness():
    """``∃x P(x)`` with no constants still has a model — over a single anonymous element."""
    asts = _p("∃x Worship(x)")
    m = find_model(asts)
    assert m is not None and m.domain_size >= 1 and satisfies(asts, m)


def test_disjunction_has_a_model():
    asts = _p("P(a) ∨ Q(a)")
    m = find_model(asts)
    assert m is not None and satisfies(asts, m)
    assert (("P", (m.constants["a"],)) in m.true_atoms
            or ("Q", (m.constants["a"],)) in m.true_atoms)


# ---------------------------------------------------------------------------
# No model — the honest None (a contradiction has none)
# ---------------------------------------------------------------------------

def test_propositional_contradiction_has_no_model():
    assert find_model(_p("P(a)", "¬P(a)")) is None


def test_universal_contradicts_existential_witness():
    """``∀x P(x)`` and ``∃x ¬P(x)`` cannot both hold — no model at any bounded size."""
    assert find_model(_p("∀x P(x)", "∃x ¬P(x)")) is None


def test_disjointness_blocks_the_overlap():
    """A disjointness denial makes the joint membership unsatisfiable."""
    assert find_model(_p("∀x ¬(A(x) ∧ B(x))", "A(c)", "B(c)")) is None


# ---------------------------------------------------------------------------
# The independence certificate — both directions modelled ⇒ Uncertain
# ---------------------------------------------------------------------------

def test_certify_independent_returns_two_genuine_models():
    prem = _p("∀x (Dog(x) → Mammal(x))", "Mammal(spot)")
    concl = parse_fol("Dog(spot)")
    neg = parse_fol("¬Dog(spot)")
    cert = certify_independent(prem, concl, neg)
    assert cert is not None
    m_not_c, m_c = cert
    assert satisfies(prem + [neg], m_not_c)         # premises hold, conclusion fails
    assert satisfies(prem + [concl], m_c)           # premises hold, conclusion holds


def test_certify_independent_none_when_entailed():
    """When M entails C, ``M ∪ {¬C}`` has no model, so no independence certificate exists."""
    prem = _p("∀x (Dog(x) → Mammal(x))", "Dog(rex)")
    concl = parse_fol("Mammal(rex)")
    neg = parse_fol("¬Mammal(rex)")
    assert certify_independent(prem, concl, neg) is None


# ---------------------------------------------------------------------------
# The headline guard: any model found, for any of a battery of shapes, is real
# ---------------------------------------------------------------------------

_SAT_SAMPLES = [
    _p("∀x (P(x) ∨ Q(x))"),
    _p("∀x (Student(x) → Person(x))", "Student(amy)", "¬Genius(amy)"),
    _p("∃x (P(x) ∧ ¬Q(x))", "∀x (P(x) → R(x))"),
    _p("R(a, b)", "∀x ∀y (R(x, y) → R(y, x))"),
]


def test_every_found_model_satisfies_its_formula():
    for asts in _SAT_SAMPLES:
        m = find_model(asts)
        assert m is not None, f"expected a model for {asts}"
        assert satisfies(asts, m), f"unsound model for {asts}: {m.describe()}"
