"""
Contract tests for the DLCore reasoning services (``src/dl_reasoning.py``).

The DLCore track of a Description-Logic benchmark asks three things of an ontology M:
subsumption (``C ⊑ D``?), instance checking (``a : C``?), and consistency (does M have a
model?).  These pin Arisbe's fragment-honest, signature-aware answers to each — including
the two refusals that make the engine trustworthy as a benchmark oracle: ``UNKNOWN`` (the
fragment can't decide — open-world / non-Horn residue) and ``OUT_OF_SIGNATURE`` (the query
names vocabulary M never defined — the vocabulary-miss the NL-parse use case turns on).

Theories are authored inline (the underlying `entails` / `materialize_egi` are already
corpus-validated in test_theory_query / test_model_materialization); these tests fix the
DLCore *composition* — the verdict mapping, the consistency check, the signature/fragment
classification.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif

from dl_reasoning import (
    DLAnswer,
    check_consistency,
    check_instance,
    check_subsumption,
    ontology_signature,
)

# A small Horn T-box: Dog ⊑ Mammal ⊑ Animal.
TBOX = parse_egif("~[ (Dog *x) ~[ (Mammal x) ] ] ~[ (Mammal *y) ~[ (Animal y) ] ]")
# An A-box + the T-box: Rex is a Dog.
ABOX = parse_egif("(Dog \"Rex\") ~[ (Dog *x) ~[ (Mammal x) ] ] ~[ (Mammal *y) ~[ (Animal y) ] ]")


# ---------------------------------------------------------------------------
# Subsumption
# ---------------------------------------------------------------------------

def test_subsumption_transitive_holds():
    r = check_subsumption(TBOX, "Dog", "Animal")
    assert r.answer is DLAnswer.YES
    assert r.decided


def test_subsumption_underivable_is_no_when_wholly_horn():
    r = check_subsumption(TBOX, "Animal", "Dog")
    assert r.answer is DLAnswer.NO


def test_subsumption_out_of_signature():
    # Reptile is in neither the body nor any axiom — M cannot address it.
    r = check_subsumption(TBOX, "Dog", "Reptile")
    assert r.answer is DLAnswer.OUT_OF_SIGNATURE
    assert "Reptile" in r.detail


def test_subsumption_unknown_on_non_horn_residue():
    # A ⊑ (B ⊔ C): a disjunctive head is non-Horn → the materializer leaves it; the
    # subsumption A ⊑ B is then UNKNOWN (a larger reading might bear), not NO.
    theory = parse_egif("~[ (A *x) ~[ ~[ (B x) ] ~[ (C x) ] ] ]")
    r = check_subsumption(theory, "A", "B")
    assert r.answer is DLAnswer.UNKNOWN
    assert r.unsupported_axioms >= 1


# ---------------------------------------------------------------------------
# Instance checking
# ---------------------------------------------------------------------------

def test_instance_derived_through_rules():
    r = check_instance(ABOX, "Rex", "Animal")
    assert r.answer is DLAnswer.YES
    assert "Animal(Rex)" in r.derived


def test_instance_not_an_instance_when_wholly_horn():
    r = check_instance(ABOX, "Spot", "Mammal")   # Spot is not asserted anywhere
    assert r.answer is DLAnswer.NO


def test_instance_out_of_signature():
    r = check_instance(ABOX, "Rex", "Reptile")
    assert r.answer is DLAnswer.OUT_OF_SIGNATURE


# ---------------------------------------------------------------------------
# Consistency
# ---------------------------------------------------------------------------

def test_consistency_clean_within_fragment():
    # Rex is a Dog; Cat and Dog are disjoint — no individual is both → consistent.
    m = parse_egif('(Dog "Rex") ~[ (Cat *x) (Dog x) ]')
    r = check_consistency(m)
    assert r.answer is DLAnswer.YES


def test_consistency_direct_disjointness_violation():
    # Rex is asserted both Cat and Dog, which are disjoint → inconsistent.
    m = parse_egif('(Cat "Rex") (Dog "Rex") ~[ (Cat *x) (Dog x) ]')
    r = check_consistency(m)
    assert r.answer is DLAnswer.NO
    assert "denial" in r.detail.lower()


def test_consistency_inconsistency_through_the_closure():
    # Dog ⊑ Cat forces Cat(Rex); Cat and Dog disjoint → the Horn closure violates the denial.
    m = parse_egif(
        '(Dog "Rex") ~[ (Dog *x) ~[ (Cat x) ] ] ~[ (Cat *y) (Dog y) ]')
    r = check_consistency(m)
    assert r.answer is DLAnswer.NO


def test_consistency_unknown_when_unsupported_constructs_remain():
    # A non-Horn axiom (disjunctive head) the materializer can't use, and no denial fires
    # → consistency only within the fragment (UNKNOWN), not a clean YES.
    m = parse_egif('(A "a") ~[ (A *x) ~[ ~[ (B x) ] ~[ (C x) ] ] ]')
    r = check_consistency(m)
    assert r.answer is DLAnswer.UNKNOWN
    assert r.unsupported_axioms >= 1


# ---------------------------------------------------------------------------
# Signature helper
# ---------------------------------------------------------------------------

def test_signature_lists_all_relation_names():
    assert ontology_signature(TBOX) == {"Dog", "Mammal", "Animal"}
