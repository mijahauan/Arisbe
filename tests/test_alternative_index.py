"""AlternativeRecord / AlternativeRegister — the index over chain steps.

Spec: docs/superpowers/specs/2026-07-26-alternative-index-over-ink-design.md §2.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import dataclasses

import pytest

from alternative_index import (
    AlternativeRecord, Materiality, Reception, TrackRecord, UntrackedSources,
    alt_key,
)


class TestAltKey:
    def test_constants_and_generics(self):
        assert alt_key("white", ("Alba",)) == 'white("Alba")'
        assert alt_key("loves", ("Alba", None)) == 'loves("Alba",*)'
        assert alt_key("rains", ()) == "rains()"

    def test_arity_preserved(self):
        assert alt_key("loves", ("Alba", None)) != alt_key("loves", ("Alba",))


class TestMateriality:
    def test_vector_round_trips(self):
        m = Materiality(tier="material", diverging=("white",),
                        extra_true=('white("Dover")',), extra_false=(),
                        k3_true=None, k3_false=None)
        assert Materiality.from_dict(m.to_dict()) == m

    def test_no_scalar_field(self):
        names = {f.name for f in dataclasses.fields(Materiality)}
        assert "warrant" not in names and "score" not in names


class TestReception:
    def test_round_trips(self):
        r = Reception(source="fieldbook", stance="supports",
                      classification="legible-benign",
                      claim_egif='(swan "Dover")', bears_evidence=True)
        assert Reception.from_dict(r.to_dict()) == r


class TestTrackRecord:
    def test_accuracy(self):
        assert TrackRecord(bets=4, hits=3, misses=1).accuracy == 0.75
        assert TrackRecord(bets=0, hits=0, misses=0).accuracy is None

    def test_untracked_sources_answer_none(self):
        assert UntrackedSources().track_record("anyone") is None


class TestAlternativeRecord:
    def _rec(self, **kw):
        base = dict(
            key=alt_key("swan", ("Dover",)), relation="swan", labels=("Dover",),
            alternatives=('(swan "Dover")', '~[ (swan "Dover") ]'),
        )
        base.update(kw)
        return AlternativeRecord(**base)

    def test_valid_record_and_status(self):
        r = self._rec()
        assert r.status == "untraced"
        traced = dataclasses.replace(r, traced_by="step-2",
                                     materiality=Materiality(tier="bare"))
        assert traced.status == "traced"
        resolved = dataclasses.replace(traced, resolved_by="step-5",
                                       selection='(swan "Dover")')
        assert resolved.status == "resolved"

    def test_opaque_alternative_refused_at_birth(self):
        with pytest.raises(ValueError, match="parse"):
            self._rec(alternatives=("grounding-A", "grounding-B"))

    def test_non_interrogative_kind_refused(self):
        with pytest.raises(ValueError, match="kind"):
            self._rec(kind="modal")

    def test_selection_must_be_an_alternative(self):
        with pytest.raises(ValueError, match="selection"):
            self._rec(resolved_by="step-5", selection='(black "Dover")')

    def test_no_warrant_float_in_namespace(self):
        names = {f.name for f in dataclasses.fields(AlternativeRecord)}
        assert "warrant" not in names and "external_warrant" not in names

    def test_round_trips(self):
        r = self._rec(traced_by="step-2", materiality=Materiality(tier="material",
                      diverging=("white",)), receptions=(Reception(
                          source="s", stance="supports",
                          classification="legible-benign",
                          claim_egif=None, bears_evidence=False),),
                      posture_pressure=1)
        assert AlternativeRecord.from_dict(r.to_dict()) == r


# Import for AlternativeRegister tests
from alternative_index import AlternativeRegister


def _record(rel="swan", labels=("Dover",), **kw):
    base = dict(key=alt_key(rel, labels), relation=rel, labels=labels,
                alternatives=(f'({rel} "{labels[0]}")', f'~[ ({rel} "{labels[0]}") ]'))
    base.update(kw)
    return AlternativeRecord(**base)


class TestAlternativeRegister:
    def test_dedup_by_key_touches_never_forks(self):
        reg = AlternativeRegister(capacity=4)
        reg.note(_record(), round_idx=1)
        reg.note(_record(), round_idx=5)               # same key re-arrives
        assert len(reg) == 1
        assert reg.get(alt_key("swan", ("Dover",))).last_touched_round == 5
        assert reg.get(alt_key("swan", ("Dover",))).emerged_round == 1

    def test_merge_adopts_evidence_never_wipes(self):
        # The V.3 regression pin: a later, less-informed arrival must not
        # reset the traced fields.
        reg = AlternativeRegister(capacity=4)
        traced = _record(traced_by="step-2", materiality=Materiality(tier="material"))
        reg.note(traced, round_idx=1)
        reg.note(_record(), round_idx=2)               # untraced re-arrival
        got = reg.get(traced.key)
        assert got.traced_by == "step-2"
        assert got.materiality.tier == "material"

    def test_lru_displacement_counted(self):
        reg = AlternativeRegister(capacity=2)
        reg.note(_record("apple", ("1",)), round_idx=1)
        reg.note(_record("blue", ("2",)), round_idx=2)
        displaced = reg.note(_record("cat", ("3",)), round_idx=3)
        assert displaced == alt_key("apple", ("1",))
        assert reg.displaced == 1
        assert reg.displaced_keys == [alt_key("apple", ("1",))]
        assert len(reg) == 2

    def test_snapshot_restore_round_trips(self):
        reg = AlternativeRegister(capacity=2)
        reg.note(_record("apple", ("1",)), round_idx=1)
        reg.note(_record("blue", ("2",)), round_idx=2)
        reg.note(_record("cat", ("3",)), round_idx=3)    # displaces apple
        reg2 = AlternativeRegister.restore(reg.snapshot())
        assert reg2.snapshot() == reg.snapshot()

    def test_resolve_and_receive(self):
        reg = AlternativeRegister(capacity=4)
        r = _record()
        reg.note(r, round_idx=1)
        posture = Reception(source="pundit", stance="supports",
                            classification="legible-benign",
                            claim_egif=None, bears_evidence=False)
        got = reg.receive(r.key, posture, round_idx=2)
        assert got.posture_pressure == 1
        resolved = reg.resolve(r.key, resolved_by="step-9",
                               selection='(swan "Dover")')
        assert resolved.status == "resolved"
        assert reg.open_records() == []
