"""The Gamma demonstrations (docs/GAMMA_DEMONSTRATIONS.md) — Peirce's attempted
modal drawings expressed in Beta + the diachronic branching DAG, with no modal mark.

Covers: the broken-cut square reproduces all four modal statuses (D1); Peirce's
broken-cut rules and worked inferences hold as trajectory facts, and his CP 4.519
non-inference is exhibited (D2); the would-be pair — de inesse on one sheet vs □G
over courses of experience (D3); real citations in provenance (never fabricated);
the modal route's proposal reading (the compound-meaning reader) + world thumbnails;
and the two challenge-mode targets. Builders are exercised fresh (no corpus reads),
so the suite doesn't depend on seeded state; route tests hit the live corpus copies.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import eg_navigation as nav
import modal_query as mq
from egif_parser_dau import parse_egif

import build_gamma_modal_exemplars as gd


# --------------------------------------------------------------------------- #
# D1 — the broken-cut square                                                   #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def square():
    chain, uod = gd.build_broken_cut_square()
    return chain, uod


def test_square_is_a_forked_converging_frame(square):
    chain, uod = square
    from collections import Counter
    frm = Counter(s.from_state_id for s in chain.steps)
    to = Counter(s.to_state_id for s in chain.steps)
    assert any(v > 1 for v in frm.values())          # fork
    assert any(v > 1 for v in to.values())           # convergence
    assert nav.same_graph(uod.current_egi, parse_egif(gd.SQUARE_GOAL))


def test_square_reads_all_four_modal_statuses(square):
    """Peirce's four modes (CP 2.382) as verdicts of one frame: □ daylight,
    ◇ rains / ◇ mist (not □, so also ◇¬), □¬ thunders."""
    chain, _ = square
    assert mq.necessarily(chain, mq.scribes_relation("daylight")).holds       # □
    for name in ("rains", "mist"):
        assert mq.possibly(chain, mq.scribes_relation(name)).holds            # ◇
        assert not mq.necessarily(chain, mq.scribes_relation(name)).holds     # ◇¬
    assert not mq.possibly(chain, mq.scribes_relation("thunders")).holds      # □¬


def test_lowell_inferences_hold_as_frame_facts(square):
    """Peirce's worked inferences (Lowell IV; Roberts pp. 83–84) on the reflexive
    states reading: □g ⊨ g, □g ⊨ ◇g; and R6(a)'s weakening shape ¬g ⊨ ◇¬g."""
    chain, _ = square
    base = chain.states[chain.initial_state_id]
    for name in ("rains", "daylight", "mist", "thunders"):
        phi = mq.scribes_relation(name)
        if mq.necessarily(chain, phi).holds:
            assert phi(base)                                   # □g ⊨ g (T)
            assert mq.possibly(chain, phi).holds               # □g ⊨ ◇g (D over T)
        if not phi(base):                                      # ¬g at the base
            assert not mq.necessarily(chain, phi).holds        # ⊨ ◇¬g


def test_cp_4519_non_inference_exhibited(square):
    """CP 4.519: g and ◇□g 'can neither of them be inferred from the other' —
    (rains) holds at the base while ◇□rains fails on this frame."""
    chain, _ = square
    base = chain.states[chain.initial_state_id]
    assert mq.scribes_relation("rains")(base)                  # g, actually
    assert not any(
        mq.necessarily(chain, mq.scribes_relation("rains"), base=w).holds
        for w in mq.reachable_states(chain))                   # but not ◇□g


# --------------------------------------------------------------------------- #
# D3 — the would-be pair                                                       #
# --------------------------------------------------------------------------- #

def test_de_inesse_is_the_synchronic_sheet():
    uod = gd.build_would_be_de_inesse()
    assert nav.same_graph(uod.current_egi, parse_egif(gd.DE_INESSE_EGIF))


def test_would_be_holds_at_every_course_and_contrast_is_refuted():
    chain, _ = gd.build_would_be_courses()
    worlds = mq.reachable_states(chain)
    v = {w: gd._closed_verdict(chain.states[w], gd.WOULD_BE_G) for w in worlds}
    assert all(x == "true" for x in v.values())                # □G — the strict reading
    v2 = {w: gd._closed_verdict(chain.states[w], gd.CONTRAST_G2) for w in worlds}
    assert any(x == "false" for x in v2.values())              # the ruin course refutes
    assert any(x == "true" for x in v2.values())               # yet ◇G2


def test_courses_are_the_experiential_register():
    """Every edge a new_fact revision — courses of experience, not Dau inferences
    (the tincture point: choosing R is choosing the mode)."""
    chain, _ = gd.build_would_be_courses()
    admits = [s for s in chain.steps
              if (s.parameters or {}).get("act") == "m_enlargement"]
    assert admits and all(
        s.rule_name == "ADMIT_TO_M"
        and s.parameters.get("disposition") == "new_fact"
        and s.parameters.get("derivation") == ["INS"]     # rule-licensed now
        for s in admits)
    from collections import Counter
    frm = Counter(s.from_state_id for s in chain.steps)
    assert any(v > 1 for v in frm.values())                    # branching courses


# --------------------------------------------------------------------------- #
# Provenance — real citations, never fabricated                                #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("prov_fn", [
    gd.square_provenance, gd.de_inesse_provenance, gd.courses_provenance])
def test_provenance_carries_a_real_peirce_citation(prov_fn):
    from scholarly_citation import citation_for
    prov = prov_fn()
    assert prov["theorem_source"]["author"].startswith("Peirce")
    bundle = citation_for(provenance=prov, name="x")
    assert bundle["has_source"] is True
    assert "Peirce" in bundle["citation"]


# --------------------------------------------------------------------------- #
# The modal route's proposal reading + thumbnails (the compound-meaning reader) #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def client():
    fastapi = pytest.importorskip("fastapi")  # noqa: F841 — web extra required
    from fastapi.testclient import TestClient
    from web_api.main import app
    return TestClient(app)


def _modal(client, uod_id, **params):
    r = client.get(f"/organon/uods/{uod_id}/modal", params=params).json()
    return r


def test_route_default_proposal_reads_the_would_be(client):
    r = _modal(client, "would_be_courses")
    assert r["success"]
    p = r["data"]["proposal"]
    assert p and p["from_annotation"] and p["necessary"]        # □G, pre-filled
    assert not p["unknown_worlds"]
    # every world drawn + badged with G's verdict there
    for w in r["data"]["worlds"]:
        assert w.get("svg") and w.get("verdict") == "true"


def test_route_contrast_proposal_is_possible_not_necessary(client):
    r = _modal(client, "would_be_courses", proposal=gd.CONTRAST_G2)
    p = r["data"]["proposal"]
    assert p["possible"] and not p["necessary"]
    assert p["counterexamples"]                                 # the ruin course, named


def test_route_rejects_a_malformed_proposal(client):
    r = _modal(client, "would_be_courses", proposal="(((")
    assert not r["success"] and r["error"]["code"] == "MODAL_PROPOSAL_INVALID"


def test_route_square_shows_the_square_and_no_proposal_block(client):
    r = _modal(client, "broken_cut_square")
    d = r["data"]
    modal = {x["name"]: x["modal"] for x in d["relations"]}
    assert modal == {"daylight": "necessary", "rains": "possible", "mist": "possible"}
    assert d["proposal"] is None                                # no declared default


def test_route_synchronic_uod_has_no_frame(client):
    r = _modal(client, "would_be_de_inesse")
    assert r["success"] and r["data"]["has_chain"] is False


# --------------------------------------------------------------------------- #
# Challenge targets                                                            #
# --------------------------------------------------------------------------- #

def test_gamma_challenges_parse_and_grade():
    from challenge_mode import get_challenge, grade
    for cid in ("de-inesse", "would-be-course"):
        ch = get_challenge(cid)
        target = parse_egif(ch.prompt_egif)
        report = grade(target, parse_egif(ch.prompt_egif))      # same graph passes
        assert report.matches
