"""
Contract tests for FOLIO FOL parsing + Z3 entailment (``src/folio_fol.py``).

The authoritative-verdict half of the FOLIO evaluation: a parser for FOLIO's FOL syntax
(∀ ∃ ¬ ∧ ∨ → ↔ ⊕, n-ary predicates, lowercase constants, hyphenated names) and a direct
Z3 entailment decision (True = entailed / False = conclusion's negation entailed /
Uncertain = neither). Inline FOL throughout; the dataset run is the harness CLI.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

pytest.importorskip("z3")

from folio_fol import (
    Atom,
    BinOp,
    FolioParseError,
    Not,
    Quant,
    decide_entailment,
    parse_fol,
)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def test_parse_universal_implication():
    f = parse_fol("∀x (Dog(x) → Mammal(x))")
    assert isinstance(f, Quant) and f.kind == "forall" and f.var == "x"
    assert isinstance(f.body, BinOp) and f.body.op == "implies"


def test_parse_operators_and_constants():
    assert parse_fol("Engaged(bonnie)") == Atom("Engaged", ("bonnie",))
    assert parse_fol("¬Students(x)") == Not(Atom("Students", ("x",)))
    assert parse_fol("R(x, y)") == Atom("R", ("x", "y"))
    # xor + biconditional are recognised
    assert parse_fol("A(x) ⊕ B(x)").op == "xor"
    assert parse_fol("A(x) ↔ B(x)").op == "iff"


def test_parse_disjunction_and_hyphenated_name():
    f = parse_fol("∀x (TalentShows(x) ∨ Warm-blooded(x))")
    assert f.body.op == "or"
    assert f.body.right == Atom("Warm-blooded", ("x",))


def test_parse_nested_existential_binary_predicate():
    f = parse_fol("∀x ∃y (Loves(x, y) ∧ Person(y))")
    assert isinstance(f, Quant) and isinstance(f.body, Quant)
    assert f.body.kind == "exists" and f.body.var == "y"


def test_parse_error_is_raised_not_guessed():
    with pytest.raises(FolioParseError):
        parse_fol("Loves(x, )(")          # malformed


# ---------------------------------------------------------------------------
# Entailment (the 3-valued verdict)
# ---------------------------------------------------------------------------

SYLLOGISM = ["∀x (Dog(x) → Mammal(x))", "∀x (Mammal(x) → Warmblooded(x))", "Dog(bonnie)"]


def test_entailment_true():
    assert decide_entailment(SYLLOGISM, "Warmblooded(bonnie)").verdict == "True"


def test_entailment_false_is_contradiction():
    assert decide_entailment(SYLLOGISM, "¬Warmblooded(bonnie)").verdict == "False"


def test_entailment_uncertain():
    assert decide_entailment(SYLLOGISM, "Cat(bonnie)").verdict == "Uncertain"


def test_xor_premise_drives_verdict():
    # Exactly one of P, Q holds; P holds ⟹ ¬Q (entailed).
    prem = ["P(a) ⊕ Q(a)", "P(a)"]
    assert decide_entailment(prem, "¬Q(a)").verdict == "True"
    assert decide_entailment(prem, "Q(a)").verdict == "False"


def test_disjunctive_syllogism():
    prem = ["∀x (Talent(x) ∨ Inactive(x))", "¬Talent(bonnie)"]
    assert decide_entailment(prem, "Inactive(bonnie)").verdict == "True"


def test_unparsed_is_reported_not_decided():
    r = decide_entailment(["Loves(x,)("], "P(a)")
    assert r.verdict == "Unparsed" and not r.parsed and not r.decided
