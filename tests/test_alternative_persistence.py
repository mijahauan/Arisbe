"""Register persistence at the tomos boundary — attested, atomic, raising."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import dataclasses

import pytest

from alternative_index import (
    AlternativeLawViolation, AlternativeRegister, Materiality,
    record_from_trace_step,
)
from alternative_trace import BoundedRegister, trace_step
from egif_parser_dau import parse_egif
from m_steps import peel_step
from proof_authoring import ProofChain
from tomos_service import TomosService
from world_scroll import wrap_m

LAW = '~[ (swan *x) ~[ (white x) ] ]'
M0 = f'(swan "Ciel") (white "Ciel") {LAW}'


@pytest.fixture
def tomos(tmp_path):
    return TomosService(tmp_path / "corpus")


def _uod_with_trace(tomos):
    wrapped, _ = wrap_m(parse_egif(M0))
    pc = ProofChain(wrapped)
    peel_step(pc, '(swan "Dover")')
    peel_id = pc.to_chain().steps[-1].step_id
    s, a = BoundedRegister(8), BoundedRegister(8)
    trace_step(pc, "swan", ("Dover",), s_register=s, a_register=a)
    rec = dataclasses.replace(
        record_from_trace_step(pc.to_chain().steps[-1]), emerged_from=peel_id)
    chain, uod = pc.to_uod(uod_id="alt_persist_fixture", name="fixture",
                           description="Task 9 persistence fixture")
    tomos.save_uod_with_chain(uod, chain)
    reg = AlternativeRegister()
    reg.note(rec, round_idx=0)
    return uod, pc, reg


class TestRegisterPersistence:
    def test_round_trips(self, tomos):
        uod, pc, reg = _uod_with_trace(tomos)
        tomos.save_alternative_register(uod.uod_id, reg, chain=pc.to_chain())
        loaded = tomos.load_alternative_register(uod.uod_id)
        assert loaded.snapshot() == reg.snapshot()

    def test_attests_at_the_boundary(self, tomos):
        uod, pc, reg = _uod_with_trace(tomos)
        key = reg.records()[0].key
        doctored = dataclasses.replace(
            reg.get(key), materiality=Materiality(tier="spurious"))
        reg._records[key] = doctored
        with pytest.raises(AlternativeLawViolation):
            tomos.save_alternative_register(uod.uod_id, reg, chain=pc.to_chain())

    def test_missing_sidecar_loads_empty(self, tomos):
        uod, _, _ = _uod_with_trace(tomos)
        loaded = tomos.load_alternative_register(uod.uod_id)
        assert len(loaded) == 0

    def test_save_failure_raises_never_prints(self, tomos):
        reg = AlternativeRegister()
        with pytest.raises(KeyError):
            tomos.save_alternative_register("no_such_uod", reg)


class TestRetirement:
    def test_old_modules_gone(self):
        root = Path(__file__).parent.parent
        for name in ("alternative_set.py", "alternative_inquiry.py",
                     "erotetic_doubt.py"):
            assert not (root / "src" / name).exists(), name

    def test_uod_carries_no_alternative_fields(self):
        import universe_of_discourse as uodm
        import dataclasses as dc
        names = {f.name for f in dc.fields(uodm.UniverseOfDiscourse)}
        assert "alternatives_by_state" not in names
        assert "all_alternatives" not in names
        assert not hasattr(uodm.UniverseOfDiscourse, "select_alternative_at_state")
        assert not hasattr(uodm.UniverseOfDiscourse, "doubts_by_state")

    def test_no_warrant_float_in_new_namespace(self):
        import alternative_index, alternative_trace
        import dataclasses as dc
        from alternative_index import AlternativeRecord, Materiality, Reception
        for cls in (AlternativeRecord, Materiality, Reception):
            names = {f.name for f in dc.fields(cls)}
            assert "warrant" not in names and "external_warrant" not in names
