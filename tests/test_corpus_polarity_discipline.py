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
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import eg_navigation as nav
from canonical_signature import compute_canonical_signatures
from domain_oracle import CorpusOracle
from eg_navigation import same_graph
from egif_parser_dau import parse_egif
from model_materialization import materialize_egi
from semantic_game import evaluate
from tomos_service import TomosService
from world_scroll import (abandon_episode, discharge_episode, enlarge_m,
                          entertain_episode, find_world_scroll,
                          is_ligature_closed, m_view, retract_from_m,
                          withdraw_and_resupply)

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

M_ACTS = ("m_enlargement", "m_retraction", "m_revision", "world_withdrawal",
          "m_discharge", "episode_entertained", "episode_abandoned", "m_refold")
M_RULES = ("REVISE_M", "REVISE_M(sibling)", "ADMIT_TO_M", "RETRACT_FROM_M",
           "DECAY", "ENTERTAIN", "DISCHARGE_TO_M", "ABANDON_EPISODE")


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
        if p.get("act") == "episode_entertained":
            d = p.get("derivation")
            assert d and d[0] == "DC+" and d[-1] == "INS", (
                f"{uod_id}/{step.step_id}: entertain without its executed "
                f"DC+·IT+·INS derivation — got {d!r}")
        if p.get("act") == "m_discharge":
            d = p.get("derivation")
            assert d and d[-1] == "DC-" and set(d[:-1]) == {"IT-"}, (
                f"{uod_id}/{step.step_id}: discharge without its executed "
                f"IT-·…·DC- derivation — got {d!r}")
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


@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_discharges_cite_a_confirming_peel(tomos, uod_id):
    """Ruling (b), M_RESIDENCE §10 — the ⊥-door discipline: the calculus
    licenses a discharge unconditionally, so the *earning* rides on the record.
    Every ``m_discharge`` step must cite an earlier PEEL of the same proposal
    in its own chain whose recorded verdict is *true* (and every recorded peel
    already recomputes — test 3 below)."""
    from eg_navigation import same_graph
    chain, _ = _chain_states(tomos, uod_id)
    if chain is None:
        pytest.skip("static board with no chain")
    discharges = [s for s in chain.steps
                  if (s.parameters or {}).get("act") == "m_discharge"]
    if not discharges:
        pytest.skip("no discharge steps")
    by_id = {s.step_id: (i, s) for i, s in enumerate(chain.steps)}
    for step in discharges:
        p = step.parameters
        cite_id = p.get("confirmed_by")
        assert cite_id and cite_id in by_id, (
            f"{uod_id}/{step.step_id}: a discharge with no confirming citation")
        cite_idx, cite = by_id[cite_id]
        cp = cite.parameters or {}
        assert cite_idx < by_id[step.step_id][0], (
            f"{uod_id}/{step.step_id}: the citation does not precede the discharge")
        assert cp.get("act") == "peel" and cp.get("verdict") == "true", (
            f"{uod_id}/{step.step_id}: the cited step is not a confirming peel")
        assert same_graph(parse_egif(cp["proposal_egif"]),
                          parse_egif(p["proposal_egif"])), (
            f"{uod_id}/{step.step_id}: the cited peel confirms a DIFFERENT proposal")


@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_m_content_never_changes_silently(tomos, uod_id):
    """The m_view tripwire (M_RESIDENCE §10, ruling (b)): any chain step that
    changes M's content — ``m_view`` before vs after — must be an acknowledged
    act. This is what keeps the ⊥-door visible: the licence alone can put
    arbitrary ink into the agreed context, so an *unrecorded* M-change is
    refused at the gate, whatever rules produced it."""
    from eg_navigation import same_graph
    chain, _ = _chain_states(tomos, uod_id)
    if chain is None:
        pytest.skip("static board with no chain")
    for step in chain.steps:
        before = chain.states.get(step.from_state_id)
        after = chain.states.get(step.to_state_id)
        if before is None or after is None:
            continue
        if same_graph(m_view(before), m_view(after)):
            continue
        act = (step.parameters or {}).get("act")
        assert act in M_ACTS, (
            f"{uod_id}/{step.step_id}: M's content changed with no acknowledged "
            f"act (rule {step.rule_name!r}, act {act!r}) — a silent M-change")


def test_the_tripwire_bites_on_a_silent_m_change():
    """The falsifier that earns the tripwire: a chain that changes M's content
    through the ⊥-door (or any raw rule path) WITHOUT an acknowledged act is
    exactly what the gate refuses. Built by hand; must be flagged."""
    from eg_navigation import same_graph
    from proof_authoring import ProofChain, apply_rule
    from world_scroll import _fresh_double_cut, wrap_m

    def bottom_door(g):
        scroll = find_world_scroll(g)
        g, outer, rider = _fresh_double_cut(g, scroll.cell_ids[0])
        g = apply_rule("INS", g, egif='~[ (unicorn "Q") ]', target=outer)
        g = apply_rule("IT-", g, selection=[rider])
        return apply_rule("DC-", g, selection=[outer])

    pc = ProofChain(wrap_m(parse_egif('(dog "Rex")'))[0])
    pc.apply_derived("NOODLE", bottom_door, note="a silent, licensed M-change")
    chain = pc.to_chain()
    flagged = [
        s for s in chain.steps
        if not same_graph(m_view(chain.states[s.from_state_id]),
                          m_view(chain.states[s.to_state_id]))
        and (s.parameters or {}).get("act") not in M_ACTS
    ]
    assert flagged, "the tripwire failed to flag a silent M-change"


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
# 3b · the recorded derivation is earned, permanently (docket ⑤)               #
#      — the PEEL-recomputation discipline extended to M-modifying acts:        #
#      re-execute each recorded act from its own from_state and require the     #
#      result to reproduce to_state. A label alone (``derivation: ["ERA"]``)    #
#      no longer suffices; the transform must actually replay.                  #
# --------------------------------------------------------------------------- #

# same_graph (VF2) is exact but super-linear; the corpus's largest cell
# (sumo_upper — 89 cuts) is intractable for it (>120s). The canonical-signature
# multiset is the UUID-independent structural fingerprint the generators
# canonicalize on: a structural edit changes element counts and/or the colour
# multiset, so it is the gate that bites. VF2 confirms it exactly only where it
# is cheap (below the cut bound); above it the fingerprint stands alone.
_VF2_CUT_BOUND = 40


def _sig_multisets(g):
    vs, es, cs = compute_canonical_signatures(g)
    return (Counter(map(str, vs.values())),
            Counter(map(str, es.values())),
            Counter(map(str, cs.values())))


def _graphs_match(a, b) -> bool:
    """Structural equality: element counts, then the canonical-signature
    multiset (both fast); VF2 confirmation only when the graph is small enough
    to be tractable. A replay that produces a different graph fails here.

    Above ``_VF2_CUT_BOUND`` this is honestly NOT a full isomorphism test.
    Counts + the canonical-signature multiset is a 1-WL-style invariant: it
    WILL catch any replay that changes an element's depth, arity, relation
    name, or the shape of what it's nested in (the ordinary way a mismatched
    replay would show up — see ``test_graphs_match_detects_a_real_mismatch_
    above_the_vf2_bound`` below). It will NOT catch a replay that swaps a
    graph for a differently-CONNECTED but 1-WL-equivalent one (e.g. a 6-cycle
    vs. two disjoint triangles among otherwise-identical generic vertices —
    the textbook WL-1 collision) once that pair sits above the cut bound
    where VF2 is skipped. That collision is constructed and pinned as a named
    known limitation in ``test_graphs_match_known_collision_above_the_vf2_
    bound`` — not hidden, not claimed away. No corpus replay above the bound
    (only ``sumo_upper``'s one ``m_enlargement``) has ever been observed
    anywhere near that pathology; below the bound VF2 confirms exactly."""
    if (len(a.V), len(a.E), len(a.Cut)) != (len(b.V), len(b.E), len(b.Cut)):
        return False
    if _sig_multisets(a) != _sig_multisets(b):
        return False
    if len(a.Cut) <= _VF2_CUT_BOUND:
        return same_graph(a, b)
    return True


# --------------------------------------------------------------------------- #
# 3b-i · the signature-only branch (>40 cuts, VF2 skipped) is itself tested,   #
#        not merely assumed — a real falsifier plus an honest known limit     #
# --------------------------------------------------------------------------- #

def _padded(egif_body: str, n_pad: int) -> str:
    """``egif_body`` plus ``n_pad`` empty sibling cuts, to push a fixture's
    cut count above ``_VF2_CUT_BOUND`` while keeping it otherwise minimal."""
    return egif_body + " " + " ".join("~[ ]" for _ in range(n_pad))


def test_graphs_match_detects_a_real_mismatch_above_the_vf2_bound():
    """The falsifier the signature-only branch was missing: two >40-cut
    graphs, same element counts, but one atom sits one level deeper than the
    other (moved enclosure, the ordinary shape a lying replay would take).
    Depth is part of both the edge and cut signature, so the canonical-
    signature multiset genuinely differs — ``_graphs_match`` must return
    False WITHOUT ever reaching (or needing) VF2."""
    a = parse_egif(_padded("~[ (rel *x) ~[ ] ]", 40))
    b = parse_egif(_padded("~[ ~[ (rel *x) ] ]", 40))
    assert len(a.Cut) > _VF2_CUT_BOUND and len(b.Cut) > _VF2_CUT_BOUND
    assert (len(a.V), len(a.E), len(a.Cut)) == (len(b.V), len(b.E), len(b.Cut))
    assert _sig_multisets(a) != _sig_multisets(b), (
        "fixture bug: the relocated atom should change the signature multiset")
    assert not _graphs_match(a, b), (
        "the signature-only branch failed to catch a genuine relocation")


def test_graphs_match_known_collision_above_the_vf2_bound():
    """Honesty, not completeness: the textbook 1-WL collision (a 6-cycle vs.
    two disjoint triangles, both 2-regular over generic vertices under one
    relation name — the standard example 1-round Weisfeiler-Leman refinement
    cannot separate) built above the cut bound. Counts match, the canonical-
    signature multiset matches, so ``_graphs_match`` returns True — even
    though the two are NOT isomorphic (confirmed directly below the bound,
    where VF2 still runs, on the identical wiring with fewer padding cuts).

    This is a KNOWN, NAMED LIMIT of the signature-only branch above
    ``_VF2_CUT_BOUND`` (docstring on ``_graphs_match``), pinned here rather
    than left to be discovered by a real corpus mismatch. It does not
    contradict the falsifier above: that one shows the branch catches the
    *ordinary* way a replay goes wrong (depth/arity/shape); this one shows
    the specific pathology it cannot — a WL-1-equivalent rewiring — which no
    corpus fixture has ever exhibited."""
    hexagon = ("*v1 *v2 *v3 *v4 *v5 *v6 "
               "(adj v1 v2) (adj v2 v3) (adj v3 v4) "
               "(adj v4 v5) (adj v5 v6) (adj v6 v1)")
    triangles = ("*v1 *v2 *v3 *v4 *v5 *v6 "
                 "(adj v1 v2) (adj v2 v3) (adj v3 v1) "
                 "(adj v4 v5) (adj v5 v6) (adj v6 v4)")

    # Below the bound: VF2 still runs and correctly says NOT isomorphic —
    # the wiring is genuinely different (one 6-cycle vs. two 3-cycles).
    small_hex = parse_egif(_padded(hexagon, 3))
    small_tri = parse_egif(_padded(triangles, 3))
    assert len(small_hex.Cut) <= _VF2_CUT_BOUND
    assert not same_graph(small_hex, small_tri), (
        "fixture bug: the hexagon and the two triangles ARE isomorphic — "
        "not the WL-collision pair intended")

    # Above the bound: identical wiring, just padded past the VF2 skip line
    # (the hexagon/triangle wiring itself contributes zero cuts, so the pad
    # count alone must exceed the bound).
    big_hex = parse_egif(_padded(hexagon, _VF2_CUT_BOUND + 1))
    big_tri = parse_egif(_padded(triangles, _VF2_CUT_BOUND + 1))
    assert len(big_hex.Cut) > _VF2_CUT_BOUND and len(big_tri.Cut) > _VF2_CUT_BOUND
    assert (len(big_hex.V), len(big_hex.E), len(big_hex.Cut)) == (
        len(big_tri.V), len(big_tri.E), len(big_tri.Cut))
    assert _sig_multisets(big_hex) == _sig_multisets(big_tri), (
        "fixture bug: expected the two to collide on the WL-style invariant")
    assert _graphs_match(big_hex, big_tri), (
        "expected the known collision to pass _graphs_match above the bound "
        "(if this now fails, the limitation may be fixed — update the "
        "docstring on _graphs_match and this test together)")


def _enlargement_content(p):
    """The cell body an ``m_enlargement`` step inserted, ready for
    ``enlarge_m`` (which wraps it in one cell ``~[ … ]``). The corpus builders
    record it under several verified keys, all holding the *unwrapped* body
    ``enlarge_m`` wraps: ``fact_egif`` (``m_steps.admit_step``), ``rule_egif``
    (``agon_evolution``'s generalized law), ``egif`` (an axiom builder),
    ``observation`` (the swan-episode builder). ``egif_content``
    (``agon_evolution``'s seed) is the exception — the *already-wrapped* cell
    ``~[ … ]`` — so it is unwrapped once. Each key's wrapped-vs-unwrapped
    reading is fixed, not guessed per call: a wrong reading makes the replay
    mismatch (surfaced), never silently pass. ``None`` = a content key this
    gate does not reconstruct (skip, counted)."""
    for key in ("fact_egif", "rule_egif", "egif", "observation"):
        if p.get(key):
            return p[key]
    ec = p.get("egif_content")
    if ec and ec.strip().startswith("~[") and ec.strip().endswith("]"):
        return ec.strip()[2:-1].strip()
    return None


def _replay_act(before, act, p):
    """Re-execute ``act`` from ``before`` using only recorded params. Returns
    the resulting graph, or ``None`` when the act is not replayable from the
    record (a non-M act, or content under a key this gate does not
    reconstruct, or a ``world_withdrawal`` recorded before ``revise_step``
    captured ``new_m_egif``)."""
    if act == "m_enlargement":
        content = _enlargement_content(p)
        return enlarge_m(before, content) if content is not None else None
    if act == "m_retraction":
        return retract_from_m(before, subgraph_egif=p.get("subgraph_egif"),
                              relation=p.get("relation"),
                              labels=p.get("labels"))[0]
    if act == "m_revision":
        g = before
        if p.get("subgraph_egif") or p.get("relation"):
            g = retract_from_m(g, subgraph_egif=p.get("subgraph_egif"),
                               relation=p.get("relation"),
                               labels=p.get("labels"))[0]
        fact = _enlargement_content(p)
        if fact:
            g = enlarge_m(g, fact)
        return g
    if act == "episode_entertained":
        return entertain_episode(before, p["proposal_egif"])[0]
    if act == "m_discharge":
        return discharge_episode(before, p["proposal_egif"])[0]
    if act == "episode_abandoned":
        return abandon_episode(before, p["proposal_egif"])[0]
    if act == "world_withdrawal":
        if "new_m_egif" not in p:
            return None    # recorded before revise_step captured new_m_egif
        return withdraw_and_resupply(before, p["new_m_egif"])[0]
    return None            # a non-M act carrying a derivation — not replayed


def _replay_derivations(chain):
    """Re-execute every replayable act in ``chain``; return
    ``(replayed, skipped, mismatches, by_act)`` where ``mismatches`` names
    every step whose replay did NOT reproduce its recorded ``to_state`` (a
    real finding), and ``by_act`` is a ``Counter`` of successfully-replayed
    steps keyed by ``act`` (so a caller can hold each act type to its own
    floor, not just the corpus-wide total)."""
    replayed = skipped = 0
    mismatches = []
    by_act = Counter()
    for step in chain.steps:
        p = step.parameters or {}
        act, deriv = p.get("act"), p.get("derivation")
        if not act or not deriv:
            continue
        before = chain.states.get(step.from_state_id)
        after = chain.states.get(step.to_state_id)
        if before is None or after is None:
            continue
        result = _replay_act(before, act, p)
        if result is None:
            skipped += 1
            continue
        if _graphs_match(result, after):
            replayed += 1
            by_act[act] += 1
        else:
            mismatches.append((step.step_id, act))
    return replayed, skipped, mismatches, by_act


@pytest.mark.parametrize("uod_id", _m_bearing_ids())
def test_recorded_derivations_replay_identically(tomos, uod_id):
    """Docket ⑤: the gate re-executes what the record asserts. For every
    M-modifying step, replaying the recorded act from ``from_state`` must
    reproduce ``to_state`` — a chain that did structural surgery while writing
    a benign derivation label is refused here."""
    chain = tomos.load_chain(uod_id)
    if chain is None:
        pytest.skip("static board with no chain")
    _, _, mismatches, _ = _replay_derivations(chain)
    assert not mismatches, (
        f"{uod_id}: recorded derivation(s) do not replay to their to_state — "
        f"{mismatches} — the record is not earned")


# Per-act-type floors, read off the corpus as of 2026-07-19 (31 m_enlargement,
# 2 m_revision, 2 m_retraction replayed across the 15 M-bearing UoDs with
# chains) with a small margin below m_enlargement (the corpus will grow) and
# none below the two-instance acts (any drop there is already the whole
# supply). `total > 0` alone would stay green if a future content-key rename
# silently orphaned an entire act type (e.g. all 31 m_enlargement replays
# going to `skipped`) as long as some other act still replayed — these floors
# make that failure loud and name the act type that dropped.
_REPLAY_FLOORS = {"m_enlargement": 25, "m_retraction": 2, "m_revision": 2}


def test_the_replay_gate_bites_somewhere(tomos):
    """The gate must actually re-execute derivations across the corpus, not
    silently skip everything (a gate that replays nothing proves nothing) —
    and it must keep re-executing EACH act type it has ever covered, not just
    some total across all of them (see ``_REPLAY_FLOORS``)."""
    total = 0
    by_act_total = Counter()
    for u in tomos.list_uods():
        if u.get("category") != "domain_model":
            continue
        chain = tomos.load_chain(u["uod_id"])
        if chain is None:
            continue
        replayed, _, _, by_act = _replay_derivations(chain)
        total += replayed
        by_act_total += by_act
    assert total > 0, "the replay gate re-executed no derivation anywhere"
    for act, floor in _REPLAY_FLOORS.items():
        assert by_act_total.get(act, 0) >= floor, (
            f"the replay gate's '{act}' coverage dropped to "
            f"{by_act_total.get(act, 0)} (floor {floor}) — a content-key "
            f"rename or similar may have silently orphaned this act type "
            f"even though the corpus-wide total stayed positive "
            f"(by_act={dict(by_act_total)!r})")


def test_episode_acts_replay_on_the_worked_exemplar(tomos):
    """The ``episode_entertained`` / ``m_discharge`` replay branches exercised
    on real recorded data. The only corpus UoD carrying them is
    ``episode_discharge`` — a ``theorem_proof``, outside the domain_model gate
    above — so it is replayed here directly rather than left uncovered."""
    chain = tomos.load_chain("episode_discharge")
    if chain is None:
        pytest.skip("no episode_discharge chain")
    replayed, _, mismatches, _ = _replay_derivations(chain)
    assert not mismatches, (
        f"episode_discharge: {mismatches} do not replay to their to_state")
    assert replayed > 0, "episode_discharge replayed no episode derivation"


def test_the_replay_gate_bites_on_a_lying_derivation():
    """The falsifier that earns the gate: a step whose ``derivation: ["ERA"]``
    label lies — it claims a retraction of ``dog`` but the transform actually
    did structural surgery (scribed a unicorn). Replaying the recorded act must
    NOT reproduce the recorded to_state, so the gate flags it. Mirrors the
    silent-⊥-door falsifier above."""
    from proof_authoring import ProofChain
    from world_scroll import wrap_m

    pc = ProofChain(wrap_m(parse_egif('(dog "Rex")'))[0])
    pc.apply_derived(
        "RETRACT_FROM_M", lambda g: enlarge_m(g, '(unicorn "Q")'),
        params={"act": "m_retraction", "derivation": ["ERA"],
                "relation": "dog"})
    chain = pc.to_chain()
    _, _, mismatches, _ = _replay_derivations(chain)
    assert mismatches, "the replay gate failed to detect a lying derivation"


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
