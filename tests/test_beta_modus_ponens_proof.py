"""
Beta modus ponens as a diachronic exemplar — the tomos's first proof with a
**line of identity**.

    P(x), P(x)→Q(x)  ⊢  P(x) ∧ Q(x)

Built by ``tools/build_beta_modus_ponens_chain.py`` as a real
``TransformationChain`` anchored at the *premises* (not the blank sheet) — so
alongside Praeclarum (a theorem from ⊤) it exhibits the other shape of a
reasoning episode: inference from an asserted context.

These tests parallel ``test_praeclarum_proof.py`` but lean on
``eg_navigation.same_graph`` (full isomorphism) for conclusion/soundness
checks, because a line of identity (the W-partition) is exactly what a cheap
structural signature cannot see.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from build_beta_modus_ponens_chain import (
    CONCLUSION_EGIF,
    PREMISES_EGIF,
    UOD_ID,
    build_beta_modus_ponens_chain,
)
from correspondence_attestation import attest_correspondence
from eg_navigation import edges_on_vertex, same_graph
from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
from proof_authoring import replay_step
from style_loader import load_default_style
from tomos_service import TomosService


# Peirce's two steps: deiteration then double-cut erasure.
EXPECTED = [("2e", "IT-"), ("3e", "DC-")]


@pytest.fixture(scope="module")
def built():
    return build_beta_modus_ponens_chain()


# --------------------------------------------------------------------------- #
# Shape                                                                        #
# --------------------------------------------------------------------------- #

def test_two_steps_in_order(built):
    chain, _uod = built
    assert len(chain.steps) == 2
    got = [(s.parameters["peirce_label"], s.rule_name) for s in chain.steps]
    assert got == EXPECTED


def test_chain_is_anchored_at_the_premises_not_a_blank_sheet(built):
    """Unlike Praeclarum, this inference starts from a non-trivial context —
    the asserted premises P(x) ∧ (P(x)→Q(x))."""
    chain, _uod = built
    base = chain.states[chain.initial_state_id]
    assert len(base.E) + len(base.Cut) > 0, "base must be the premise graph"
    assert same_graph(base, parse_egif(PREMISES_EGIF))
    # Linear, connected.
    for prev, nxt in zip(chain.steps, chain.steps[1:]):
        assert nxt.from_state_id == prev.to_state_id


# --------------------------------------------------------------------------- #
# Conclusion (Beta: full isomorphism, not a signature)                        #
# --------------------------------------------------------------------------- #

def test_conclusion_is_P_and_Q_on_one_line(built):
    _chain, uod = built
    assert same_graph(uod.current_egi, parse_egif(CONCLUSION_EGIF))
    # The whole point of Beta: a single line of identity carries both P and Q.
    g = uod.current_egi
    assert len(g.V) == 1, "one line of identity"
    vx = next(iter(g.V)).id
    assert sorted(g.rel[e] for e in edges_on_vertex(g, vx)) == ["P", "Q"]


# --------------------------------------------------------------------------- #
# Soundness — every step replays                                              #
# --------------------------------------------------------------------------- #

def test_every_step_is_a_sound_rule_application(built):
    chain, _uod = built
    for step in chain.steps:
        frm = chain.states[step.from_state_id]
        expected = chain.states[step.to_state_id]
        replayed = replay_step(frm, step.parameters)
        assert same_graph(replayed, expected), (
            f"{step.step_id} ({step.rule_name}) did not reproduce its to_state"
        )


# --------------------------------------------------------------------------- #
# Attestation — §3.3 at every state (lines of identity included)              #
# --------------------------------------------------------------------------- #

def test_correspondence_attests_at_every_state(built):
    chain, _uod = built
    engine, style = ELKLayoutEngine(), load_default_style()
    for sid, egi in chain.states.items():
        dto = engine.generate_layout(egi, style)
        attest_correspondence(egi, dto, context=f"beta-mp:{sid}")


# --------------------------------------------------------------------------- #
# Round-trip                                                                  #
# --------------------------------------------------------------------------- #

def test_exemplar_round_trips_through_the_corpus(tmp_path, built):
    chain, uod = built
    service = TomosService(tmp_path / "tomos")
    service.save_uod_with_chain(uod, chain)

    loaded = service.load_chain(UOD_ID)
    assert loaded is not None
    assert [s.rule_name for s in loaded.steps] == [r for _, r in EXPECTED]
    assert same_graph(loaded.current_egi, parse_egif(CONCLUSION_EGIF))
    assert loaded.steps[0].parameters["peirce_label"] == "2e"
