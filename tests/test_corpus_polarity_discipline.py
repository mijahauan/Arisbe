"""**The corpus polarity gate** — the validity discipline held over the real corpus.

M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE §2b–§4, as a standing test:

* every M-bearing (``category=domain_model``) corpus UoD satisfies the
  **depth-0 inventory theorem** — its sheet area holds nothing but cuts (and,
  at most, isolated vertices): no contingent atom stands uncircumscribed;
* each resides in a recognized **standing world-scroll** ``~[ M ~[ ] ]``,
  ligature-closed (so the withdrawal ERA stays available);
* its chain records M-changes as **explicit, rule-licensed steps** — an
  enlargement carries ``derivation: ["INS"]``, a world-withdrawal carries the
  executed ``["ERA", "DC+", "INS"]`` triple;
* every recorded **PEEL verdict is earned, permanently** — recomputing the peel
  against the step's own state reproduces it;
* world-scrolled corpus Ms and legacy sheet-level Ms (the live loops) **coexist**
  through the same oracle.

The phase-2 ontology wrap landed 2026-07-15 (``tools/build_ontologies.py``):
all 7 imported T-boxes now reside in the standing world-scroll — five by the
rule-licensed DC+·INS residence chain, two (``bfo_core``, ``colore_field``) by
the id-preserving structural adapter because their importers emit cross-sibling
vertex references no linear EGIF can express (recorded in their annotations).
The allowlist is EMPTY; it stays here as the named mechanism for any *future*
deliberate debt. The wrapped-post-hoc chain (``agon_evolution_swan``) is
exempt from the explicit-step requirement — its steps are honestly flagged
``residence: "wrapped-post-hoc"`` (the live loop's migration is §8.1's
separate order) — but its *states* satisfy the polarity like every other.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import eg_navigation as nav
from domain_oracle import CorpusOracle
from egif_parser_dau import parse_egif
from model_materialization import materialize_egi
from semantic_game import evaluate
from tomos_service import TomosService
from world_scroll import find_world_scroll, is_ligature_closed, m_view

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"

# Phase-2 debt PAID (2026-07-15): the 7 imported T-box ontologies are wrapped
# by their builder (tools/build_ontologies.py). Empty — every M-bearing corpus
# UoD is under the discipline. Any future deliberate exemption goes here, with
# its reason, so the debt cannot be forgotten silently.
ONTOLOGY_ALLOWLIST: set = set()


@pytest.fixture(scope="module")
def tomos():
    return TomosService(TOMOS_ROOT)


def _m_bearing_ids():
    svc = TomosService(TOMOS_ROOT)
    return [u["uod_id"] for u in svc.list_uods()
            if u.get("category") == "domain_model"
            and u["uod_id"] not in ONTOLOGY_ALLOWLIST]


def _chain_states(tomos, uod_id):
    chain = tomos.load_chain(uod_id)
    if chain is None:
        return None, []
    return chain, list(chain.states.values())


# --------------------------------------------------------------------------- #
# 1 · the depth-0 inventory theorem, over every state of every M-bearing UoD   #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_no_contingent_atom_stands_at_depth_zero(tomos, uod_id):
    """Sheet area = cuts (+ at most isolated vertices). Never an edge."""
    uod = tomos.load_uod(uod_id, attest=False)
    chain, states = _chain_states(tomos, uod_id)
    for egi in [uod.current_egi] + states:
        assert not nav.child_edges(egi, egi.sheet), (
            f"{uod_id}: a relation atom stands uncircumscribed at depth 0 — "
            f"the depth-0 inventory theorem is violated")


@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_m_resides_in_a_standing_world_scroll(tomos, uod_id):
    """Every state carries the recognized shape ~[ M ~[ ] ], ligature-closed."""
    uod = tomos.load_uod(uod_id, attest=False)
    chain, states = _chain_states(tomos, uod_id)
    for egi in [uod.current_egi] + states:
        if not egi.get_area(egi.sheet):
            continue    # the blank sheet — the inventory theorem's "nothing"
                        # case (a construction chain legitimately starts here)
        scroll = find_world_scroll(egi)
        assert scroll is not None, f"{uod_id}: no standing world-scroll"
        assert is_ligature_closed(egi, scroll), (
            f"{uod_id}: a line of identity crosses the world-scroll boundary — "
            f"the withdrawal ERA would be refused")


# --------------------------------------------------------------------------- #
# 2 · explicit steps for M-modification                                        #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_m_changes_are_explicit_rule_licensed_steps(tomos, uod_id):
    chain, _ = _chain_states(tomos, uod_id)
    if chain is None:
        pytest.skip("static board with no chain")
    for step in chain.steps:
        p = step.parameters or {}
        if p.get("residence") == "wrapped-post-hoc":
            continue        # the honest adapter (agon_evolution_swan); see module doc
        if p.get("act") == "m_enlargement":
            assert p.get("derivation") == ["INS"], (
                f"{uod_id}/{step.step_id}: enlargement without its INS derivation")
        if p.get("act") == "world_withdrawal":
            assert p.get("derivation") == ["ERA", "DC+", "INS"], (
                f"{uod_id}/{step.step_id}: withdrawal without the executed triple")
        if step.rule_name in ("REVISE_M", "ADMIT_TO_M") \
                and p.get("act") not in ("m_enlargement", "world_withdrawal"):
            pytest.fail(f"{uod_id}/{step.step_id}: an M-change with no act record")


@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_declared_audit_proposals_have_recorded_peel_steps(tomos, uod_id):
    """A UoD that declares a standing audit-proposal records its verdicts as
    explicit PEEL steps (the wrapped-post-hoc chain exempt, flagged)."""
    anns = tomos.load_annotations(uod_id) or []
    declares = any("audit-proposal" in (a.get("tags") or []) for a in anns)
    chain, _ = _chain_states(tomos, uod_id)
    if not declares or chain is None:
        pytest.skip("no declared audit-proposal / no chain")
    if any((s.parameters or {}).get("residence") == "wrapped-post-hoc"
           for s in chain.steps):
        pytest.skip("wrapped-post-hoc chain (the live loop's own migration is "
                    "the §8.1 order, taken separately)")
    peels = [s for s in chain.steps if (s.parameters or {}).get("act") == "peel"]
    assert peels, f"{uod_id} declares an audit-proposal but records no PEEL step"


# --------------------------------------------------------------------------- #
# 3 · the recorded verdict is earned, permanently                              #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_recorded_peel_verdicts_recompute_identically(tomos, uod_id):
    chain, _ = _chain_states(tomos, uod_id)
    if chain is None:
        pytest.skip("static board with no chain")
    peels = [s for s in chain.steps if (s.parameters or {}).get("act") == "peel"]
    if not peels:
        pytest.skip("no PEEL steps")
    for step in peels:
        p = step.parameters
        state = chain.states[step.to_state_id]
        m = materialize_egi(state)[0] if p.get("materialized", True) else state
        oracle = CorpusOracle([("M", m)], closed=bool(p.get("closed")))
        result = evaluate(parse_egif(p["proposal_egif"]), oracle,
                          closed=bool(p.get("closed")))
        assert result.verdict.value == p["verdict"], (
            f"{uod_id}/{step.step_id}: recorded verdict {p['verdict']!r} does "
            f"not recompute ({result.verdict.value!r}) — the record is not earned")


# --------------------------------------------------------------------------- #
# 4 · coexistence: world-scrolled corpus M + legacy sheet-level M              #
# --------------------------------------------------------------------------- #

def test_scrolled_and_sheet_level_models_coexist_in_one_oracle(tomos):
    zoo = tomos.load_uod("zoo_world", attest=False).current_egi     # scrolled
    live = parse_egif('(swan "Ada") (white "Ada")')                 # sheet-level
    oracle = CorpusOracle([("zoo", materialize_egi(zoo)[0]), ("live", live)],
                          closed=False)
    r_zoo = evaluate(parse_egif('(dog "Rex") (warmblooded "Rex")'), oracle)
    r_live = evaluate(parse_egif('(white "Ada")'), oracle)
    assert r_zoo.verdict.value == "true"     # through the scroll + Horn chain
    assert r_live.verdict.value == "true"    # the legacy fallback, unchanged


# --------------------------------------------------------------------------- #
# 5 · the ontology debt stays visible                                          #
# --------------------------------------------------------------------------- #

def test_the_ontology_allowlist_matches_the_corpus(tomos):
    """The allowlist names exactly the domain_model UoDs still outside the
    discipline — if an ontology is wrapped (phase 2) or a new M-bearing UoD is
    added at sheet level, this fails and the list must be updated *knowingly*."""
    listed = {u["uod_id"] for u in tomos.list_uods()
              if u.get("category") == "domain_model"}
    assert ONTOLOGY_ALLOWLIST <= listed
    for uod_id in sorted(ONTOLOGY_ALLOWLIST):
        egi = tomos.load_uod(uod_id, attest=False).current_egi
        assert find_world_scroll(egi) is None, (
            f"{uod_id} now carries a world-scroll — remove it from the "
            f"allowlist so the gate covers it")
