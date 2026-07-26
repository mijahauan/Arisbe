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

    def test_denial_settles_despite_coreference_and_attests(self):
        """Finding 2 repro: the admitted cell's "Dover" constant co-refers
        between the swan atom and the black-denial's interior — the EGIF
        parser interns it to ONE vertex at the LCA, so the denial's vertex
        is not self-contained under the cut. The old lift_cut-based
        _denial_stands raised and was swallowed, so settlement never fired
        and AS3 spuriously rejected the resolution."""
        pc = _chain()
        s, a = BoundedRegister(32), BoundedRegister(32)
        peel_step(pc, '(black "Dover")')
        peel_id = pc.to_chain().steps[-1].step_id
        trace_step(pc, "black", ("Dover",), s_register=s, a_register=a)
        step = pc.to_chain().steps[-1]
        rec = dataclasses.replace(record_from_trace_step(step),
                                  emerged_from=peel_id)
        reg = AlternativeRegister()
        reg.note(rec, round_idx=0)
        admit_step(pc, '(swan "Dover") ~[ (black "Dover") ]',
                  disposition="new_fact")
        resolved = reg.settle_from_chain(pc.to_chain())
        assert resolved == [rec.key]
        got = reg.get(rec.key)
        assert got.selection == '~[ (black "Dover") ]'
        attest_alternative_record(got, pc.to_chain())      # AS3 holds


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


class TestAS1Tightened:
    """A non-emergence emerged_from is now a violation (the silent pass died
    — spec 2026-07-26-close-the-arc §3, AC14)."""

    def _chain_with_admit(self):
        from egif_parser_dau import parse_egif
        from m_steps import admit_step, peel_step
        from proof_authoring import ProofChain
        from world_scroll import wrap_m
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        peel_step(pc, '(black "Dover")')
        peel_id = pc.to_chain().steps[-1].step_id
        admit_step(pc, '(white "Ciel")', disposition="new_fact")
        admit_id = pc.to_chain().steps[-1].step_id
        return pc.to_chain(), peel_id, admit_id

    def test_emerged_from_a_non_emergence_step_is_refused(self):
        chain, _peel_id, admit_id = self._chain_with_admit()
        rec = AlternativeRecord(
            key=alt_key("black", ("Dover",)), relation="black",
            labels=("Dover",),
            alternatives=('(black "Dover")', '~[ (black "Dover") ]'),
            emerged_from=admit_id)          # an admit is not an emergence
        report = run_alternative_record(rec, chain)
        assert any("AS1" in v and "emergence" in v for v in report.violations)

    def test_peel_emergence_still_passes(self):
        chain, peel_id, _ = self._chain_with_admit()
        rec = AlternativeRecord(
            key=alt_key("black", ("Dover",)), relation="black",
            labels=("Dover",),
            alternatives=('(black "Dover")', '~[ (black "Dover") ]'),
            emerged_from=peel_id)
        assert run_alternative_record(rec, chain).ok

    def test_survey_emergence_passes_and_rebuild_reads_surveys(self):
        from alternative_survey import thin_spot_step
        from egif_parser_dau import parse_egif
        from proof_authoring import ProofChain
        from world_scroll import wrap_m
        wrapped, _ = wrap_m(parse_egif(
            '(swan "Ciel") ~[ (dragon *x) ~[ (fears x) ] ]'))
        pc = ProofChain(wrapped)
        thin_spot_step(pc)
        chain = pc.to_chain()
        from alternative_survey import records_from_survey_step
        recs = records_from_survey_step(chain.steps[-1])
        assert recs
        for rec in recs:
            assert run_alternative_record(rec, chain).ok
        rebuilt = AlternativeRegister.rebuild_from_chain(chain)
        assert {r.key for r in recs} <= {r.key for r in rebuilt.records()}
        assert all(rebuilt.get(r.key).kind == "hypothetical" for r in recs)


class TestAS3Introduction:
    """AS3 checks introduced-by-step, not stands-at-step (spec §3, AC15):
    a bystander acknowledged step whose from_state already held the answer
    cannot be cited as the resolution."""

    def _chain_two_admits(self):
        from egif_parser_dau import parse_egif
        from m_steps import admit_step, peel_step
        from proof_authoring import ProofChain
        from world_scroll import wrap_m
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        peel_step(pc, '(black "Dover")')
        peel_id = pc.to_chain().steps[-1].step_id
        admit_step(pc, '(black "Dover")', disposition="new_fact")
        introducing_id = pc.to_chain().steps[-1].step_id
        admit_step(pc, '(grey "Gull")', disposition="new_fact")
        bystander_id = pc.to_chain().steps[-1].step_id
        return pc, peel_id, introducing_id, bystander_id

    def _record(self, peel_id, resolved_by=None, selection=None):
        return AlternativeRecord(
            key=alt_key("black", ("Dover",)), relation="black",
            labels=("Dover",),
            alternatives=('(black "Dover")', '~[ (black "Dover") ]'),
            emerged_from=peel_id, resolved_by=resolved_by,
            selection=selection)

    def test_bystander_step_refused(self):
        pc, peel_id, _intro, bystander = self._chain_two_admits()
        rec = self._record(peel_id, resolved_by=bystander,
                           selection='(black "Dover")')
        report = run_alternative_record(rec, pc.to_chain())
        assert any("AS3" in v and "introduce" in v for v in report.violations)

    def test_introducing_step_passes(self):
        pc, peel_id, intro, _ = self._chain_two_admits()
        rec = self._record(peel_id, resolved_by=intro,
                           selection='(black "Dover")')
        assert run_alternative_record(rec, pc.to_chain()).ok

    def test_settle_cites_the_introducing_step(self):
        pc, peel_id, intro, _ = self._chain_two_admits()
        reg = AlternativeRegister(capacity=8)
        reg.note(self._record(peel_id), round_idx=0)
        resolved = reg.settle_from_chain(pc.to_chain())
        assert resolved == [alt_key("black", ("Dover",))]
        assert reg.get(alt_key("black", ("Dover",))).resolved_by == intro
