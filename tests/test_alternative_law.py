"""AS1–AS4 — the AlternativeRecord law (spec §4) + settlement + rebuild."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import dataclasses

import pytest

from alternative_index import (
    AlternativeLawViolation, AlternativeRecord, AlternativeRegister,
    Materiality, alt_key, attest_alternative_record, record_from_trace_step,
    run_alternative_record,
)
from alternative_trace import BoundedRegister, trace_step
from egif_parser_dau import parse_egif
from m_steps import admit_step, peel_step
from proof_authoring import ProofChain
from world_scroll import wrap_m

LAW = '~[ (swan *x) ~[ (white x) ] ]'
M0 = f'(swan "Ciel") (white "Ciel") {LAW}'


def _chain():
    wrapped, _ = wrap_m(parse_egif(M0))
    return ProofChain(wrapped)


def _traced(pc):
    s, a = BoundedRegister(32), BoundedRegister(32)
    peel_step(pc, '(swan "Dover")')
    peel_id = pc.to_chain().steps[-1].step_id
    trace_step(pc, "swan", ("Dover",), s_register=s, a_register=a)
    step = pc.to_chain().steps[-1]
    rec = dataclasses.replace(record_from_trace_step(step),
                              emerged_from=peel_id)
    return rec, step


class TestLaw:
    def test_honest_record_passes(self):
        pc = _chain()
        rec, _ = _traced(pc)
        attest_alternative_record(rec, pc.to_chain())     # no raise

    def test_as1_bites_on_content_mismatch(self):
        pc = _chain()
        rec, _ = _traced(pc)
        doctored = dataclasses.replace(rec, relation="black",
                                       key=alt_key("black", ("Dover",)),
                                       alternatives=('(black "Dover")',
                                                     '~[ (black "Dover") ]'))
        with pytest.raises(AlternativeLawViolation, match="AS1"):
            attest_alternative_record(doctored, pc.to_chain())

    def test_as2_bites_on_doctored_materiality(self):
        pc = _chain()
        rec, _ = _traced(pc)
        doctored = dataclasses.replace(
            rec, materiality=Materiality(tier="spurious"))
        with pytest.raises(AlternativeLawViolation, match="AS2"):
            attest_alternative_record(doctored, pc.to_chain())

    def test_as3_bites_on_unlicensed_resolution(self):
        pc = _chain()
        rec, _ = _traced(pc)
        # Cite the PEEL step (not an acknowledged M-act) as the resolver.
        doctored = dataclasses.replace(rec, resolved_by=rec.emerged_from,
                                       selection=rec.alternatives[0])
        with pytest.raises(AlternativeLawViolation, match="AS3"):
            attest_alternative_record(doctored, pc.to_chain())

    def test_as4_horizon_names_untraced(self):
        rec = AlternativeRecord(
            key=alt_key("swan", ("Dover",)), relation="swan",
            labels=("Dover",),
            alternatives=('(swan "Dover")', '~[ (swan "Dover") ]'))
        pc = _chain()
        report = run_alternative_record(rec, pc.to_chain())
        assert report.ok                       # untraced is honest, not illegal
        assert any("untraced" in h for h in report.horizon)


class TestSettlement:
    def test_settles_citing_the_admitting_step(self):
        pc = _chain()
        rec, _ = _traced(pc)
        reg = AlternativeRegister()
        reg.note(rec, round_idx=0)
        admit_step(pc, '(swan "Dover")', disposition="new_fact")
        admit_id = pc.to_chain().steps[-1].step_id
        resolved = reg.settle_from_chain(pc.to_chain())
        assert resolved == [rec.key]
        got = reg.get(rec.key)
        assert got.resolved_by == admit_id
        assert got.selection == '(swan "Dover")'
        attest_alternative_record(got, pc.to_chain())      # AS3 holds

    def test_denial_branch_settles_too(self):
        pc = _chain()
        rec, _ = _traced(pc)
        reg = AlternativeRegister()
        reg.note(rec, round_idx=0)
        admit_step(pc, '~[ (swan "Dover") ]', disposition="new_fact")
        reg.settle_from_chain(pc.to_chain())
        assert reg.get(rec.key).selection == '~[ (swan "Dover") ]'

    def test_no_settlement_without_acknowledged_act(self):
        pc = _chain()
        rec, _ = _traced(pc)
        reg = AlternativeRegister()
        reg.note(rec, round_idx=0)
        assert reg.settle_from_chain(pc.to_chain()) == []

    def test_settlement_survives_a_standing_entertained_exhibit(self):
        """A standing entertained episode exhibit's outer cut becomes
        sheet-level under m_view. _denial_stands must not crash scanning it
        (lift_cut raises ValueError on a non-self-contained subtree) and
        must not let it settle anything unrelated (mention is not
        assertion)."""
        from m_steps import entertain_step
        pc = _chain()
        rec, _ = _traced(pc)
        reg = AlternativeRegister()
        reg.note(rec, round_idx=0)
        entertain_step(pc, '(white "Rex")')
        admit_step(pc, '(mammal "Bob")', disposition="new_fact")
        resolved = reg.settle_from_chain(pc.to_chain())    # must not raise
        assert resolved == []
        assert reg.get(rec.key).status != "resolved"


class TestRebuild:
    def test_register_rebuilds_from_chain_alone(self):
        pc = _chain()
        rec, _ = _traced(pc)
        admit_step(pc, '(swan "Dover")', disposition="new_fact")
        reg = AlternativeRegister()
        reg.note(rec, round_idx=0)
        reg.settle_from_chain(pc.to_chain())
        rebuilt = AlternativeRegister.rebuild_from_chain(pc.to_chain())
        got = rebuilt.get(rec.key)
        assert got is not None
        assert got.status == "resolved"
        assert got.traced_by == reg.get(rec.key).traced_by
        assert got.resolved_by == reg.get(rec.key).resolved_by
