"""**The corpus polarity gate** — the validity discipline held over the real corpus.

M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE §2b–§4 + the second relocation (§9,
ratified 2026-07-16: M's elements in cells at even depth), as a standing test:

* every M-bearing (``category=domain_model``) corpus UoD satisfies the
  **depth-0 inventory theorem** — its sheet area holds nothing but cuts (and,
  at most, isolated vertices): no contingent atom stands uncircumscribed;
* each resides in the recognized **standing residence**
  ``~[ ~[cell] … ~[ ] ]`` — W holds ONLY cuts, at least one of them empty
  (the hold / any scars; vacuity) — ligature-closed at W (so the withdrawal
  ERA stays available for the rare full replacement);
* its chain records M-changes as **explicit, rule-licensed steps** — an
  enlargement carries ``derivation: ["INS"]`` (a closed cell), a retraction
  one-or-more executed ``"ERA"``s (inside a cell — the fallibilist pole), the
  challenge composite its executed ERA/INS list, a world-withdrawal the
  executed ``["ERA", "DC+", "INS"]`` triple;
* every recorded **PEEL verdict is earned, permanently** — recomputing the peel
  against the step's own state reproduces it;
* resident corpus Ms and bare sheet-level Ms (inline fixtures) **coexist**
  through the same oracle.

Since sweep #2 the live loop (``agon_evolution.run``) emits native
rule-licensed chains (DC+ · INS residence steps + licensed cell moves), so the
old ``wrapped-post-hoc`` exemption is retired — ``agon_evolution_swan`` is held
to the same standard as the hand-built corpus. The allowlist is EMPTY; it
stays here as the named mechanism for any *future* deliberate debt.
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
    """Every state carries the recognized residence ``~[ ~[cell] … ~[ ] ]``
    (the §9.3 inventory: W holds only cuts, at least one empty),
    ligature-closed at W."""
    uod = tomos.load_uod(uod_id, attest=False)
    chain, states = _chain_states(tomos, uod_id)
    for egi in [uod.current_egi] + states:
        if not egi.get_area(egi.sheet):
            continue    # the blank sheet — the inventory theorem's "nothing"
                        # case (a construction chain legitimately starts here)
        scroll = find_world_scroll(egi)
        assert scroll is not None, f"{uod_id}: no standing residence"
        # The §9.3 inventory, asserted explicitly beside the recognition:
        w = scroll.cut_id
        assert not nav.child_edges(egi, w) and not nav.child_vertices(egi, w), (
            f"{uod_id}: content stands at level 1 (the retired shape) — M's "
            f"elements belong in cells at even depth")
        assert scroll.hold_ids, (
            f"{uod_id}: no empty cut in W — the outer negation would bind")
        assert is_ligature_closed(egi, scroll), (
            f"{uod_id}: a line of identity crosses the residence boundary — "
            f"the withdrawal ERA would be refused")


# --------------------------------------------------------------------------- #
# 2 · explicit steps for M-modification                                        #
# --------------------------------------------------------------------------- #

M_ACTS = ("m_enlargement", "m_retraction", "m_revision", "world_withdrawal")
M_RULES = ("REVISE_M", "REVISE_M(sibling)", "ADMIT_TO_M", "RETRACT_FROM_M",
           "DECAY")


@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_m_changes_are_explicit_rule_licensed_steps(tomos, uod_id):
    chain, _ = _chain_states(tomos, uod_id)
    if chain is None:
        pytest.skip("static board with no chain")
    for step in chain.steps:
        p = step.parameters or {}
        if p.get("act") == "m_enlargement":
            assert p.get("derivation") == ["INS"], (
                f"{uod_id}/{step.step_id}: enlargement without its INS derivation")
        if p.get("act") == "m_retraction":
            d = p.get("derivation")
            assert d and set(d) == {"ERA"}, (
                f"{uod_id}/{step.step_id}: retraction without its executed "
                f"licensed ERA(s) — got {d!r}")
        if p.get("act") == "m_revision":
            d = p.get("derivation")
            assert d and set(d) <= {"ERA", "INS"}, (
                f"{uod_id}/{step.step_id}: challenge composite without its "
                f"executed ERA/INS list — got {d!r}")
        if p.get("act") == "world_withdrawal":
            assert p.get("derivation") == ["ERA", "DC+", "INS"], (
                f"{uod_id}/{step.step_id}: withdrawal without the executed triple")
        if step.rule_name in M_RULES and p.get("act") not in M_ACTS:
            pytest.fail(f"{uod_id}/{step.step_id}: an M-change with no act record")


@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_declared_audit_proposals_have_recorded_peel_steps(tomos, uod_id):
    """A UoD that declares a standing audit-proposal records its verdicts as
    explicit PEEL steps — or, for a chain the live loop emitted natively, as
    per-round audited ``standing_verdict``s the audit lens recomputes (the
    loop's steps carry ``proposal``; its standing audit is per-round, not a
    separate step). Either way the verdict is *in the record*."""
    anns = tomos.load_annotations(uod_id) or []
    declares = any("audit-proposal" in (a.get("tags") or []) for a in anns)
    chain, _ = _chain_states(tomos, uod_id)
    if not declares or chain is None:
        pytest.skip("no declared audit-proposal / no chain")
    peels = [s for s in chain.steps if (s.parameters or {}).get("act") == "peel"]
    loop_rounds = [s for s in chain.steps
                   if (s.parameters or {}).get("proposal")]
    assert peels or loop_rounds, (
        f"{uod_id} declares an audit-proposal but records neither PEEL steps "
        f"nor loop-round proposals")


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
