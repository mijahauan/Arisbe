"""
Contract tests for the Domain Oracle (``src/domain_oracle.py``).

Design-of-record: ``docs/DOMAIN_ORACLE_AND_M.md``.  These pin the first-step
behaviour: a negation-free fragment ``g`` resolves into a model M as CONFIRMED
(with a homomorphism), UNKNOWN (open world), or DENIED (closed world); provenance
names the model that answered; constants and shared lines of identity are honoured;
and a fragment containing a cut is refused.
"""

import pytest

from egif_parser_dau import parse_egif

from domain_oracle import (
    CorpusOracle,
    DomainOracle,
    Mapping,
    ResolveResult,
    Verdict,
    WitnessResult,
)


# ---------------------------------------------------------------------------
# A small worked domain (the vet's knowledge base, à la ARISBE_IN_PRACTICE)
# ---------------------------------------------------------------------------

BISCUIT_M = (
    '(dog "Biscuit") (mammal "Biscuit") (warmblooded "Biscuit")'
)


def corpus(closed: bool = False, **named_egifs) -> CorpusOracle:
    return CorpusOracle.from_egif(named_egifs, closed=closed)


# ---------------------------------------------------------------------------
# CONFIRMED — g maps into M
# ---------------------------------------------------------------------------

def test_confirmed_single_atom():
    oracle = corpus(animals=BISCUIT_M)
    g = parse_egif('(dog "Biscuit")')
    res = oracle.resolve(g)
    assert res.verdict is Verdict.CONFIRMED
    assert res.source == "animals"
    assert isinstance(res.mapping, Mapping)
    # one edge, one vertex bound
    assert len(res.mapping.edges) == 1
    assert len(res.mapping.vertices) == 1


def test_confirmed_conjunction_shared_line():
    """Two relations on one shared line of identity both have to land on the
    same M individual."""
    oracle = corpus(animals=BISCUIT_M)
    g = parse_egif('(dog *x) (mammal x)')   # exists x: dog(x) & mammal(x)
    res = oracle.resolve(g)
    assert res.verdict is Verdict.CONFIRMED
    # both g-edges mapped; the single shared g-vertex mapped once
    assert len(res.mapping.edges) == 2
    assert len(set(res.mapping.vertices.values())) == 1


def test_confirmed_generic_existence():
    oracle = corpus(animals=BISCUIT_M)
    g = parse_egif('(dog *x)')              # exists x: dog(x)
    assert oracle.resolve(g).verdict is Verdict.CONFIRMED


# ---------------------------------------------------------------------------
# UNKNOWN — open world: absent, neither confirmed nor denied
# ---------------------------------------------------------------------------

def test_unknown_open_world_missing_relation():
    oracle = corpus(animals=BISCUIT_M)       # open by default
    g = parse_egif('(reptile "Biscuit")')
    res = oracle.resolve(g)
    assert res.verdict is Verdict.UNKNOWN
    assert "open" in (res.source or "")


def test_unknown_constant_absent():
    oracle = corpus(animals=BISCUIT_M)
    g = parse_egif('(dog "Rex")')            # Rex is not in M
    assert oracle.resolve(g).verdict is Verdict.UNKNOWN


def test_unknown_partial_conjunction_fails_whole():
    """A conjunction is confirmed only if *every* atom maps."""
    oracle = corpus(animals=BISCUIT_M)
    g = parse_egif('(dog *x) (reptile x)')   # dog holds, reptile does not
    assert oracle.resolve(g).verdict is Verdict.UNKNOWN


# ---------------------------------------------------------------------------
# DENIED — closed world: a miss is a provable failure
# ---------------------------------------------------------------------------

def test_denied_closed_world():
    oracle = corpus(animals=BISCUIT_M, closed=True)
    g = parse_egif('(reptile "Biscuit")')
    res = oracle.resolve(g)
    assert res.verdict is Verdict.DENIED
    assert "closed" in (res.source or "")


def test_closed_world_still_confirms_present():
    oracle = corpus(animals=BISCUIT_M, closed=True)
    g = parse_egif('(dog "Biscuit")')
    assert oracle.resolve(g).verdict is Verdict.CONFIRMED


# ---------------------------------------------------------------------------
# Provenance across multiple models
# ---------------------------------------------------------------------------

def test_provenance_names_the_matching_model():
    oracle = corpus(
        animals=BISCUIT_M,
        plants='(tomato "Cherry") (needs_sun "Cherry")',
    )
    assert oracle.resolve(parse_egif('(tomato "Cherry")')).source == "plants"
    assert oracle.resolve(parse_egif('(dog "Biscuit")')).source == "animals"


# ---------------------------------------------------------------------------
# Constants must match by label, not just by shape
# ---------------------------------------------------------------------------

def test_constant_label_must_match():
    oracle = corpus(animals='(dog "Biscuit")')
    # Same shape, different constant — must NOT confirm.
    assert oracle.resolve(parse_egif('(dog "Rex")')).verdict is Verdict.UNKNOWN
    # Exact constant — confirms.
    assert oracle.resolve(parse_egif('(dog "Biscuit")')).verdict is Verdict.CONFIRMED


def test_arity_must_match():
    oracle = corpus(rels='(loves "A" "B")')
    # Binary loves present; a unary loves pattern must not map onto it.
    assert oracle.resolve(parse_egif('(loves *x)')).verdict is Verdict.UNKNOWN
    assert oracle.resolve(parse_egif('(loves "A" "B")')).verdict is Verdict.CONFIRMED


def test_binary_argument_order_respected():
    oracle = corpus(rels='(loves "A" "B")')
    # loves(A,B) holds; loves(B,A) does not (order matters via nu).
    assert oracle.resolve(parse_egif('(loves "B" "A")')).verdict is Verdict.UNKNOWN
    assert oracle.resolve(parse_egif('(loves "A" "B")')).verdict is Verdict.CONFIRMED


# ---------------------------------------------------------------------------
# Refusal: resolve() is for negation-free fragments only
# ---------------------------------------------------------------------------

def test_resolve_refuses_a_cut():
    oracle = corpus(animals=BISCUIT_M)
    g = parse_egif('~[ (dog "Biscuit") ]')   # contains a negation
    with pytest.raises(ValueError):
        oracle.resolve(g)


# ---------------------------------------------------------------------------
# witness() — individuals for the negative-area pick
# ---------------------------------------------------------------------------

def test_witness_returns_individuals():
    oracle = corpus(animals=BISCUIT_M, more='(dog "Rex") (dog "Fido")')
    res = oracle.witness("dog")
    assert isinstance(res, WitnessResult)
    assert set(res.individuals) >= {"Biscuit", "Rex", "Fido"}


def test_witness_honours_partial_binding():
    oracle = corpus(rels='(loves "A" "B") (loves "A" "C") (loves "Z" "B")')
    # Pin position 0 = "A"; expect the second-argument partners of A.
    res = oracle.witness("loves", {0: "A"})
    assert set(res.individuals) >= {"B", "C"}
    assert "Z" not in res.individuals  # Z is a first-arg, filtered out by the pin


# ---------------------------------------------------------------------------
# The interface is abstract
# ---------------------------------------------------------------------------

def test_domain_oracle_is_abstract():
    with pytest.raises(TypeError):
        DomainOracle()  # type: ignore[abstract]
