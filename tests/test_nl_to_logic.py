"""
Contract tests for the NL→logic front-end (``src/nl_to_logic.py``) — *LLM proposes,
Arisbe disposes*.

The LLM is the only non-deterministic step and is **mocked** here (a fake client returning
a canned ``emit_fol`` payload), so the suite is deterministic and needs no network. What the
tests pin is the contract that makes the front-end trustworthy:

* the candidate FOL is parsed **deterministically** into an EGI that is the right graph
  (round-trip via ``same_graph``) — the LLM never touches the EGI;
* a malformed candidate is **reported** (``parse_error``), never repaired or crashed on;
* an ``unmappable`` sentence stays honestly unbuilt (``parsed=False``, caveat surfaced);
* ``reconcile`` splits the proposal's vocabulary into **addressable** vs **out-of-signature**
  against M — the vocabulary-miss vs fact-miss distinction;
* ``interpret_against`` reproduces the peel's verdict on known (M, G) pairs.

One opt-in live test (skipped unless ``ANTHROPIC_API_KEY`` is set) exercises the real model.
"""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import nl_to_logic
from nl_to_logic import (
    Proposal,
    build_proposal,
    interpret_against,
    propose,
    reconcile,
)


# A curated model M: the teacher's mammals world (closed = asserted-complete).
TEACHER_M = '(mammal "Rex") (warmblooded "Rex") (mammal "Whale") (warmblooded "Whale")'


def _fake_client(payload: dict):
    """A stand-in anthropic client whose messages.create returns one forced emit_fol call."""
    block = SimpleNamespace(type="tool_use", name="emit_fol", input=payload)
    resp = SimpleNamespace(content=[block])
    return SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: resp))


# ---------------------------------------------------------------------------
# propose: the LLM proposal is parsed deterministically into the right EGI
# ---------------------------------------------------------------------------

def test_propose_parses_into_the_expected_graph():
    fol = "∀x (Bird(x) → Fly(x))"
    client = _fake_client(
        {"fol": fol, "predicates": {"Bird": 1, "Fly": 1}, "constants": [], "confidence": "high"}
    )
    prop = propose("All birds fly", client=client)
    assert prop.parsed and prop.usable
    assert prop.confidence == "high"
    # The EGIF Arisbe derived is the SAME graph as building the FOL directly (round-trip).
    from egif_parser_dau import parse_egif
    from folio_fol import folio_fol_to_egi
    from eg_navigation import same_graph
    assert same_graph(parse_egif(prop.egif), folio_fol_to_egi(fol))


def test_propose_unmappable_stays_honestly_unbuilt():
    client = _fake_client(
        {"fol": "", "predicates": {}, "constants": [],
         "unmappable": "modal necessity is outside the first-order fragment"}
    )
    prop = propose("Necessarily, every triangle has three sides", client=client)
    assert not prop.parsed and not prop.usable
    assert prop.egif is None
    assert "modal" in prop.unmappable


def test_propose_malformed_fol_is_reported_not_crashed():
    client = _fake_client(
        {"fol": "Dog(rex,", "predicates": {"Dog": 1}, "constants": ["rex"]}
    )
    prop = propose("Rex is a dog", client=client)
    assert not prop.parsed
    assert prop.parse_error and prop.egif is None  # reported, no exception


def test_propose_api_failure_is_captured():
    boom = SimpleNamespace(messages=SimpleNamespace(
        create=lambda **kw: (_ for _ in ()).throw(RuntimeError("503 overloaded"))))
    prop = propose("anything", client=boom)
    assert not prop.parsed and "LLM front-end failed" in prop.parse_error


def test_propose_declared_vs_used_vocabulary_mismatch_flagged():
    # The LLM declares a predicate the formula never uses → flagged (self-report check).
    client = _fake_client(
        {"fol": "Bird(\"Tweety\")", "predicates": {"Bird": 1, "Penguin": 1}, "constants": ["Tweety"]}
    )
    prop = propose("Tweety is a bird", client=client)
    assert prop.parsed
    assert "Penguin" in prop.vocab_mismatch


# ---------------------------------------------------------------------------
# build_proposal: the deterministic (--no-llm) half derives the vocabulary
# ---------------------------------------------------------------------------

def test_build_proposal_no_llm_derives_predicates_from_the_ast():
    prop = build_proposal("(hand)", fol="∀x (mammal(x) → warmblooded(x))")
    assert prop.parsed
    assert prop.predicates == {"mammal": 1, "warmblooded": 1}  # derived, no declaration
    assert prop.vocab_mismatch == []                           # nothing declared ⇒ no mismatch


# ---------------------------------------------------------------------------
# reconcile: vocabulary-miss vs fact-miss
# ---------------------------------------------------------------------------

def test_reconcile_splits_addressable_from_out_of_signature():
    prop = build_proposal("x", fol='warmblooded("Rex") ∧ flies("Rex")')
    rep = reconcile(prop, TEACHER_M)
    assert "warmblooded" in rep.addressable        # M speaks this
    assert rep.out_of_signature == ["flies"]       # M cannot even address this (vocab-miss)
    assert not rep.fully_addressable


def test_reconcile_fully_addressable_when_M_knows_every_predicate():
    prop = build_proposal("x", fol="∀x (mammal(x) → warmblooded(x))")
    rep = reconcile(prop, TEACHER_M)
    assert rep.fully_addressable and not rep.out_of_signature


# ---------------------------------------------------------------------------
# interpret_against: reproduce the peel verdict
# ---------------------------------------------------------------------------

def test_interpret_true_on_closed_model():
    prop = build_proposal("Every mammal is warm-blooded",
                          fol="∀x (mammal(x) → warmblooded(x))")
    out = interpret_against(prop, TEACHER_M, closed=True)
    assert out["verdict"] == "true" and out["holds"]


def test_interpret_false_on_a_miss_in_closed_model():
    prop = build_proposal("Rex flies", fol='flies("Rex")')
    out = interpret_against(prop, TEACHER_M, closed=True)
    assert out["verdict"] == "false"  # closed world: an un-derivable atom is FALSE


def test_interpret_matches_the_agon_route_payload():
    # interpret_against mirrors _interpret_payload; on the same inputs the verdict agrees.
    from web_api.routes.agon import _interpret_payload
    prop = build_proposal("x", fol="∀x (mammal(x) → warmblooded(x))")
    mine = interpret_against(prop, TEACHER_M, closed=True)
    theirs = _interpret_payload(TEACHER_M, prop.egif, closed=True)
    assert mine["verdict"] == theirs["verdict"]
    assert mine["holds"] == theirs["holds"]


def test_interpret_refuses_an_unusable_proposal():
    prop = Proposal(nl="x", parse_error="nope")
    with pytest.raises(ValueError):
        interpret_against(prop, TEACHER_M)


# ---------------------------------------------------------------------------
# Opt-in: the real model (skipped without a key)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not (nl_to_logic.ANTHROPIC_AVAILABLE and os.environ.get("ANTHROPIC_API_KEY")),
    reason="needs the 'nl' extra + ANTHROPIC_API_KEY",
)
def test_live_propose_and_interpret():
    sig = {"mammal", "warmblooded"}
    prop = propose("Every mammal is warm-blooded.", vocabulary_hint=sig)
    assert prop.parsed, prop.parse_error
    out = interpret_against(prop, TEACHER_M, closed=True)
    assert out["verdict"] in ("true", "false", "unknown")  # it interprets; don't pin the string
