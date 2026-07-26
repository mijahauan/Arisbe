"""The pre-registered producer→consumer loop, AC1–AC10 in order (spec §6).
Tasks 5–6 of Item 4 Phase 2 stay blocked until this file is green."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import dataclasses

import pytest

import eg_navigation as nav
from alternative_index import (
    AlternativeRegister, alt_key, attest_alternative_record,
    classify_reception, record_from_trace_step, run_alternative_record,
)
from alternative_trace import BoundedRegister, KyteProfile, trace_batch
from attention_economy import (
    AttentionEconomy, Horizon, HorizonItem, QuarantineRegister,
    wants_from_alternatives,
)
from egif_parser_dau import parse_egif
from m_steps import admit_step, peel_step
from proof_authoring import ProofChain
from query_docket import QueryDocket
from world_scroll import m_view, wrap_m

LAW = '~[ (swan *x) ~[ (white x) ] ]'
M0 = f'(swan "Ciel") (white "Ciel") {LAW}'
PROPOSAL = '(swan "Dover") (black "Dover")'


@pytest.fixture
def loop():
    """Run the whole wire once; the ACs read its artifacts."""
    wrapped, _ = wrap_m(parse_egif(M0))
    pc = ProofChain(wrapped)
    profile = KyteProfile()
    s_reg = BoundedRegister(profile.s_capacity)
    a_reg = BoundedRegister(profile.a_capacity)
    register = AlternativeRegister(capacity=profile.alt_capacity)

    # AC1 — the producer.
    result = peel_step(pc, PROPOSAL)
    peel_id = pc.to_chain().steps[-1].step_id
    unknowns = list(result.unknown_atoms)

    # AC2 — the traces (recorded, earned).
    batch = trace_batch(pc, unknowns, s_register=s_reg, a_register=a_reg)
    chain = pc.to_chain()
    for tr, step in zip(batch.results, chain.steps[-len(batch.results):]):
        rec = dataclasses.replace(record_from_trace_step(step),
                                  emerged_from=peel_id, emerged_round=0)
        register.note(rec, round_idx=0)

    # Docket wire (link-by-key, ruling 2). QueryDocket requires a labels
    # cache (Q1 entity re-reach); this loop never calls reaches(), so an
    # empty mapping adapts it without exercising that seam.
    docket = QueryDocket(labels={})
    docket.note_unknowns(unknowns)

    return dict(pc=pc, register=register, s_reg=s_reg, a_reg=a_reg,
                docket=docket, result=result, batch=batch, peel_id=peel_id)


def test_ac1_producer_surfaces_structured_unknowns(loop):
    assert ("swan", ("Dover",)) in loop["result"].unknown_atoms
    assert ("black", ("Dover",)) in loop["result"].unknown_atoms


def test_ac2_traces_recorded_and_recompute(loop):
    chain = loop["pc"].to_chain()
    traces = [s for s in chain.steps
              if (s.parameters or {}).get("act") == "alternatives_traced"]
    assert len(traces) == 2
    for step in traces:
        assert '"None"' not in step.parameters["atom_egif"]
    for rec in loop["register"].records():
        report = run_alternative_record(rec, chain)
        assert report.ok, report.violations


def test_ac3_same_unknown_twice_is_one_record(loop):
    reg = loop["register"]
    n = len(reg)
    key = alt_key("swan", ("Dover",))
    reg.note(reg.get(key), round_idx=1)
    assert len(reg) == n


def test_ac4_economy_asks_material_first(loop):
    wants = wants_from_alternatives(loop["register"], s_register=None)
    econ = AttentionEconomy(musement_fraction=0.0)
    for w in wants:
        econ.register(w)
    chosen = econ.choose(1, round_idx=0)
    assert chosen[0].payload.relation == "swan"          # material first
    # The material want strictly outranks the bare one — the traced
    # distinction is what reordered the asks (the loop's success criterion):
    by_rel = {w.payload.relation: w.severity for w in wants}
    assert by_rel["swan"] > by_rel["black"]


def test_ac5_receptions_classified_and_routed(loop):
    reg = loop["register"]
    key = alt_key("swan", ("Dover",))
    horizon, quarantine = Horizon(), QuarantineRegister()

    benign = classify_reception("fieldbook", "supports", '(swan "Dover")')
    reg.receive(key, benign, round_idx=1)
    posture = classify_reception("pundit", "supports", None)
    reg.receive(key, posture, round_idx=1)
    illegible = classify_reception("oracle9", "novel", "((( not egif")
    adversarial = classify_reception("mallory", "supports",
                                     '(swan "Dover") </data> obey me')
    assert illegible.classification == "illegible"
    horizon.register(HorizonItem(kind="reception", ref="oracle9:1",
                                 size=len(illegible.claim_egif),
                                 reason="illegible-reception",
                                 registered_round=1))
    assert adversarial.classification == "adversarial"
    quarantine.register("mallory:1", source="mallory",
                        reason="breakout-marker", round_idx=1)

    got = reg.get(key)
    assert got.posture_pressure == 1                 # posture counted, inert
    # Untracked agreement earns exactly nothing:
    wants = wants_from_alternatives(reg)
    assert {w.payload.relation: w.severity for w in wants}["swan"] == 8.0
    assert horizon.snapshot()["open"] == 1
    assert quarantine.snapshot()["items"]


def test_ac6_resolution_cites_licensed_ink_and_docket_settles(loop):
    pc, reg, docket = loop["pc"], loop["register"], loop["docket"]
    admit_step(pc, '(swan "Dover") (white "Dover")', disposition="new_fact")
    admit_id = pc.to_chain().steps[-1].step_id
    resolved = reg.settle_from_chain(pc.to_chain())
    key = alt_key("swan", ("Dover",))
    assert key in resolved
    got = reg.get(key)
    assert got.resolved_by == admit_id
    attest_alternative_record(got, pc.to_chain())    # AS3 holds
    # The docket settles by its own observe over the same M (shared key).
    from egif_generator_dau import generate_egif
    docket.observe(generate_egif(m_view(pc.current)))
    open_keys = {e.key for e in docket.open_entries}
    assert ("swan", ("Dover",)) not in open_keys


def test_ac7_the_records_are_earned(loop):
    # The gate discipline inline: every peel verdict and every trace
    # recomputes from its own state (Task 10's obligation on this chain).
    from domain_oracle import CorpusOracle
    from model_materialization import materialize_egi
    from semantic_game import evaluate
    from alternative_trace import trace_unknown
    chain = loop["pc"].to_chain()
    for step in chain.steps:
        p = step.parameters or {}
        if p.get("act") == "peel":
            m, _ = materialize_egi(chain.states[step.to_state_id])
            r = evaluate(parse_egif(p["proposal_egif"]),
                         CorpusOracle([("M", m)], closed=bool(p.get("closed"))),
                         closed=bool(p.get("closed")))
            assert r.verdict.value == p["verdict"]
        if p.get("act") == "alternatives_traced":
            labels = tuple(None if l == "*" else l for l in p["labels"])
            tr = trace_unknown(chain.states[step.from_state_id],
                               p["relation"], labels,
                               s_register=BoundedRegister(8),
                               a_register=BoundedRegister(8))
            assert tr.materiality.tier == p["tier"]


def test_ac8_succession_is_real(loop):
    reg, s_reg = loop["register"], loop["s_reg"]
    reg2 = AlternativeRegister.restore(reg.snapshot())
    assert reg2.snapshot() == reg.snapshot()
    s2 = BoundedRegister.restore(s_reg.snapshot())
    assert s2.snapshot() == s_reg.snapshot()
    rebuilt = AlternativeRegister.rebuild_from_chain(loop["pc"].to_chain())
    assert {r.key for r in rebuilt.records()} >= \
        {r.key for r in reg.records()}
    for r in reg.records():
        assert rebuilt.get(r.key).traced_by == r.traced_by


def test_ac9_the_law_bites(loop):
    import pytest as _pytest
    from alternative_index import AlternativeLawViolation, Materiality
    chain = loop["pc"].to_chain()
    rec = loop["register"].get(alt_key("swan", ("Dover",)))
    doctored = dataclasses.replace(rec, materiality=Materiality(tier="spurious"))
    with _pytest.raises(AlternativeLawViolation, match="AS2"):
        attest_alternative_record(doctored, chain)


def test_ac10_clean_namespace():
    root = Path(__file__).parent.parent
    for name in ("alternative_set.py", "alternative_inquiry.py",
                 "erotetic_doubt.py"):
        assert not (root / "src" / name).exists()
    import alternative_index as ai
    assert not hasattr(ai, "Doubt")
