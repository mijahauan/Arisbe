"""
Leibniz's *Praeclarum Theorema* as a diachronic exemplar.

    ((P⊃R) ∧ (Q⊃S))  ⊃  ((P∧Q) ⊃ (R∧S))

The tomos's first canonical *worked proof*: Sowa's seven-step Existential
Graph derivation from a blank sheet (``docs/references/
Peirce_Rules_of_Inference.pdf``), built as a real ``TransformationChain``
by ``tools/build_praeclarum_chain.py``.

These tests pin the exemplar down as a genuine Peircean reasoning episode
(``docs/CHAIN_OF_SEMIOSIS.md``) rather than a hand-authored sequence of
states:

1. **Shape** — seven steps in Sowa's order, each Peirce label mapped to the
   matching Dau rule (3i→DC+, 1i→INS, 2i→IT+, 2e→IT-, 3e→DC-).
2. **Conclusion** — the final state *is* the Praeclarum Theorema (compared
   order-insensitively, since sibling order is a projection artifact).
3. **Soundness** — every step replays: re-applying its named rule to its
   own ``from_state`` snapshot reproduces its ``to_state``. This is the
   chain-of-semiosis claim made operational — each transition is a real,
   re-verifiable rule application, not an assertion.
4. **Attestation** — §3.3 holds at every non-blank state along the chain.
5. **Round-trip** — the chain persists and reloads through
   ``save_uod_with_chain`` / ``load_chain`` with steps, states, and
   conclusion intact.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from build_praeclarum_chain import (
    THEOREM_EGIF,
    UOD_ID,
    build_praeclarum_chain,
)
from correspondence_attestation import attest_correspondence
from eg_navigation import area_signature
from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
from proof_authoring import replay_step
from style_loader import load_default_style
from tomos_service import TomosService


# Sowa's seven steps: Peirce's label and our rule, in order.
EXPECTED = [
    ("3i", "DC+"),
    ("1i", "INS"),
    ("2i", "IT+"),
    ("1i", "INS"),
    ("2i", "IT+"),
    ("2e", "IT-"),
    ("3e", "DC-"),
]


@pytest.fixture(scope="module")
def built():
    """Build the proof once for the whole module (it is deterministic)."""
    return build_praeclarum_chain()


# --------------------------------------------------------------------------- #
# 1. Shape                                                                     #
# --------------------------------------------------------------------------- #

def test_seven_steps_in_sowas_order(built):
    chain, _uod = built
    assert len(chain.steps) == 7, "Sowa's proof is exactly seven steps"
    got = [(s.parameters["peirce_label"], s.rule_name) for s in chain.steps]
    assert got == EXPECTED


def test_chain_is_a_connected_linear_episode(built):
    """Each step's ``from_state`` is the previous step's ``to_state`` — one
    unbroken episode anchored at the blank sheet."""
    chain, _uod = built
    assert chain.initial_state_id == "s0"
    assert chain.steps[0].from_state_id == "s0"
    for prev, nxt in zip(chain.steps, chain.steps[1:]):
        assert nxt.from_state_id == prev.to_state_id
    # The blank base really is blank.
    blank = chain.states["s0"]
    assert len(blank.V) + len(blank.E) + len(blank.Cut) == 0


# --------------------------------------------------------------------------- #
# 2. Conclusion                                                               #
# --------------------------------------------------------------------------- #

def test_conclusion_is_the_praeclarum_theorema(built):
    chain, uod = built
    target = area_signature(parse_egif(THEOREM_EGIF))
    assert area_signature(uod.current_egi) == target
    assert area_signature(chain.current_egi) == target  # chain tail agrees


# --------------------------------------------------------------------------- #
# 3. Soundness — every step replays                                           #
# --------------------------------------------------------------------------- #

def test_every_step_is_a_sound_rule_application(built):
    """Re-applying each step's named rule to its own ``from_state`` snapshot,
    with its persisted parameters, reproduces its ``to_state``. A wrong or
    unsound move would diverge here (or be rejected by the engine)."""
    chain, _uod = built
    for step in chain.steps:
        frm = chain.states[step.from_state_id]
        expected = chain.states[step.to_state_id]
        replayed = replay_step(frm, step.parameters)
        assert area_signature(replayed) == area_signature(expected), (
            f"{step.step_id} ({step.rule_name}) did not reproduce its to_state"
        )


# --------------------------------------------------------------------------- #
# 4. Attestation — §3.3 at every state                                        #
# --------------------------------------------------------------------------- #

def test_correspondence_attests_at_every_state(built):
    """Every transition in a reasoning chain is an attestation event: the
    drawing of each non-blank state must §3.3-correspond to its EGI."""
    chain, _uod = built
    engine, style = ELKLayoutEngine(), load_default_style()
    for sid, egi in chain.states.items():
        if len(egi.V) + len(egi.E) + len(egi.Cut) == 0:
            continue  # the blank sheet is trivially faithful
        dto = engine.generate_layout(egi, style)
        attest_correspondence(egi, dto, context=f"praeclarum:{sid}")


# --------------------------------------------------------------------------- #
# 5. Round-trip                                                               #
# --------------------------------------------------------------------------- #

def test_exemplar_round_trips_through_the_corpus(tmp_path, built):
    chain, uod = built
    service = TomosService(tmp_path / "tomos")
    service.save_uod_with_chain(uod, chain)  # §3.3 attests before any write

    loaded = service.load_chain(UOD_ID)
    assert loaded is not None
    assert [s.rule_name for s in loaded.steps] == [r for _, r in EXPECTED]
    assert set(loaded.states) == set(chain.states)
    assert area_signature(loaded.current_egi) == area_signature(
        parse_egif(THEOREM_EGIF)
    )
    # The Peircean annotations survive the round-trip.
    assert loaded.steps[0].parameters["peirce_label"] == "3i"
