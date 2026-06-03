"""
Converse modus ponens as a diachronic exemplar — the tomos's first proof
whose conclusion has **crossing lines of identity**, and so the first that
exercises the Peirce **bridge** mark (Tier 3c) inside a real derivation.

    R(x,y), ∀x∀y(R(x,y)→S(y,x))  ⊢  R(x,y) ∧ S(y,x)

Built by ``tools/build_beta_converse_chain.py``. The same two steps as the
plain Beta modus ponens, but over a binary relation whose consequent swaps
the arguments — so the two lines cross in any 2-D drawing (§3.0's worked
example: the bridge recovers the distinction the projection would collapse).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from build_beta_converse_chain import (
    CONCLUSION_EGIF,
    PREMISES_EGIF,
    UOD_ID,
    build_beta_converse_chain,
)
from correspondence_attestation import attest_correspondence
from eg_navigation import same_graph
from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
import render_geometry as rg
from proof_authoring import replay_step
from style_loader import load_default_style
from tomos_service import TomosService
from web_api.services.layout_service import generate_layout


EXPECTED = [("2e", "IT-"), ("3e", "DC-")]


@pytest.fixture(scope="module")
def built():
    return build_beta_converse_chain()


# --------------------------------------------------------------------------- #
# Shape + conclusion                                                          #
# --------------------------------------------------------------------------- #

def test_two_steps_in_order(built):
    chain, _uod = built
    assert [(s.parameters["peirce_label"], s.rule_name) for s in chain.steps] == EXPECTED


def test_anchored_at_premises_and_concludes_the_converse(built):
    chain, uod = built
    base = chain.states[chain.initial_state_id]
    assert same_graph(base, parse_egif(PREMISES_EGIF))
    assert same_graph(uod.current_egi, parse_egif(CONCLUSION_EGIF))
    # Two lines of identity, each carrying R and S.
    g = uod.current_egi
    assert len(g.V) == 2


# --------------------------------------------------------------------------- #
# Soundness + attestation                                                     #
# --------------------------------------------------------------------------- #

def test_every_step_is_a_sound_rule_application(built):
    chain, _uod = built
    for step in chain.steps:
        frm = chain.states[step.from_state_id]
        expected = chain.states[step.to_state_id]
        assert same_graph(replay_step(frm, step.parameters), expected), (
            f"{step.step_id} ({step.rule_name}) did not reproduce its to_state"
        )


def test_correspondence_attests_at_every_state(built):
    chain, _uod = built
    engine, style = ELKLayoutEngine(), load_default_style()
    for sid, egi in chain.states.items():
        dto = engine.generate_layout(egi, style)
        attest_correspondence(egi, dto, context=f"beta-converse:{sid}")


# --------------------------------------------------------------------------- #
# The point of this exemplar: crossing lines → a bridge (Tier 3c)             #
# --------------------------------------------------------------------------- #

def test_conclusion_has_crossing_lines_and_draws_a_bridge(built):
    """The conclusion's two lines cross in the projection, and a style that
    declares the bridge convention (Peirce) draws the hop; Dau leaves the
    crossing unmarked. This ties the exemplar to the Tier-3c work."""
    _chain, uod = built
    dto, peirce_svg = generate_layout(uod.current_egi, style_name="peirce-authentic@1.0")
    # The projection genuinely crosses two distinct lines of identity.
    assert len(rg.ligature_crossings(dto.ligature_paths)) >= 1
    # Peirce draws the hop; Dau (no crossing_marks) does not.
    assert 'id="bridges"' in peirce_svg
    _d, dau_svg = generate_layout(uod.current_egi, style_name="dau-compliant@1.0")
    assert 'id="bridges"' not in dau_svg


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
