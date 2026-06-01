"""
Tests for transformation-chain persistence in ``tomos_service``.

The chain model captures a Peircean reasoning episode as the diachronic
unit it actually is: a base state (the context) plus an ordered
sequence of rule applications, each producing a new state.  These
tests pin down the round-trip contract for the V1 persistence format:

1. **Round-trip** — a chain built in memory and saved via
   ``save_uod_with_chain`` loads back via ``load_chain`` with the same
   steps, the same state IDs, and EGIs equal to what was written.
2. **Empty chain** — a chain with zero steps (just a base state) is
   still a valid chain and round-trips.
3. **Disk shape** — ``history/chain.jsonl`` and
   ``history/states/<state_id>.egi.json`` files exist after save.  The
   JSONL header carries the schema version and the initial-state id.
4. **§3.3 refusal aborts cleanly** — when the layout engine is
   monkeypatched to produce a drifted DTO, ``save_uod_with_chain``
   raises ``CorrespondenceViolation`` from inside its delegated
   ``save_uod`` call, and no chain files appear on disk.
5. **Absent / broken chain** — ``load_chain`` returns ``None`` for a
   UoD that has no chain files at all, and also for a chain whose JSONL
   references a missing state snapshot (refuses to return a partial
   chain).

The chain is intentionally constructed in-memory here without going
through ``RuleInteraction`` — the persistence layer's contract is
"whatever chain you hand me round-trips faithfully," independent of
how the chain was built.  Live rule-application integration is
covered by the Ergasterion route tests.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from correspondence_attestation import CorrespondenceViolation
from egif_parser_dau import parse_egif
from layout_dto import LayoutDTO
import tomos_service
from tomos_service import (
    CHAIN_SCHEMA_VERSION,
    ChainStep,
    TomosService,
    TransformationChain,
)
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDCategory,
    UoDMetadata,
    UoDType,
)


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #


@pytest.fixture
def tomos_root(tmp_path):
    """Isolated tomos root per test so saves don't pollute the real corpus."""
    return tmp_path / "tomos"


@pytest.fixture
def tomos(tomos_root):
    return TomosService(tomos_root)


def _make_uod(uod_id: str, egi, *, name: str = "Test chain UoD") -> UniverseOfDiscourse:
    """Build a fresh PRACTICE_SESSION UoD with the given current EGI."""
    now = datetime.now(timezone.utc)
    meta = UoDMetadata(
        uod_id=uod_id,
        uod_type=UoDType.HISTORICAL,
        name=name,
        description="Synthesised in test for chain-persistence round-trip.",
        category=UoDCategory.PRACTICE_SESSION,
        created=now,
        last_modified=now,
    )
    return UniverseOfDiscourse(metadata=meta, current_egi=egi)


def _simple_chain() -> tuple[TransformationChain, "UniverseOfDiscourse"]:
    """Build a two-step chain on a small base EGI.

    The steps are not real rule applications — they're synthetic state
    transitions used to exercise the persistence shape.  The persisted
    chain is what's under test, not the soundness of the moves.
    """
    base = parse_egif("(P *x) (Q *y)")
    middle = parse_egif("(P *x)")
    final = parse_egif("(R *x)")

    initial_id = "state-initial"
    middle_id = "state-middle"
    final_id = "state-final"

    steps = [
        ChainStep(
            step_id="step-1",
            rule_name="ERA",
            from_state_id=initial_id,
            to_state_id=middle_id,
            parameters={"selected_elements": ["e_q"]},
            timestamp="2026-05-31T12:00:00+00:00",
            user_annotation=None,
        ),
        ChainStep(
            step_id="step-2",
            rule_name="INS",
            from_state_id=middle_id,
            to_state_id=final_id,
            parameters={"egif_content": "(R *x)"},
            timestamp="2026-05-31T12:01:00+00:00",
            user_annotation="testing notes",
        ),
    ]
    chain = TransformationChain(
        initial_state_id=initial_id,
        steps=steps,
        states={
            initial_id: base,
            middle_id: middle,
            final_id: final,
        },
    )
    uod = _make_uod("chain-test-uod", final)
    return chain, uod


# --------------------------------------------------------------------------- #
# 1. Round-trip                                                               #
# --------------------------------------------------------------------------- #


def test_save_and_load_chain_round_trip(tomos):
    """A chain saved via save_uod_with_chain loads back identically."""
    chain, uod = _simple_chain()
    tomos.save_uod_with_chain(uod, chain)

    loaded = tomos.load_chain(uod.uod_id)
    assert loaded is not None

    assert loaded.initial_state_id == chain.initial_state_id
    assert [s.step_id for s in loaded.steps] == [s.step_id for s in chain.steps]
    assert [s.rule_name for s in loaded.steps] == [s.rule_name for s in chain.steps]
    assert loaded.steps[0].parameters == chain.steps[0].parameters
    assert loaded.steps[1].user_annotation == "testing notes"

    # The EGI snapshots should be present for every referenced state.
    assert set(loaded.states.keys()) == set(chain.states.keys())

    # Current-state convenience properties stay consistent.
    assert loaded.current_state_id == chain.current_state_id
    assert len(loaded.current_egi.V) == len(chain.current_egi.V)
    assert len(loaded.current_egi.E) == len(chain.current_egi.E)


# --------------------------------------------------------------------------- #
# 2. Empty chain                                                              #
# --------------------------------------------------------------------------- #


def test_empty_chain_round_trips(tomos):
    """A chain with no steps is just a base state — also a valid chain.

    In Peircean terms, this is the limit case: a context with no
    asserted moves against it.  The persistence layer should accept it.
    """
    base = parse_egif("(P *x)")
    initial_id = "state-only"
    chain = TransformationChain(
        initial_state_id=initial_id,
        steps=[],
        states={initial_id: base},
    )
    uod = _make_uod("empty-chain-uod", base)

    tomos.save_uod_with_chain(uod, chain)
    loaded = tomos.load_chain(uod.uod_id)

    assert loaded is not None
    assert loaded.steps == []
    assert loaded.initial_state_id == initial_id
    assert loaded.current_state_id == initial_id  # No steps → current == initial


# --------------------------------------------------------------------------- #
# 3. Disk shape                                                               #
# --------------------------------------------------------------------------- #


def test_chain_persistence_writes_expected_files(tomos, tomos_root):
    """save_uod_with_chain produces chain.jsonl + per-state snapshots."""
    chain, uod = _simple_chain()
    tomos.save_uod_with_chain(uod, chain)

    uod_dir = tomos_root / "universes" / uod.uod_id
    history_dir = uod_dir / "history"
    states_dir = history_dir / "states"

    assert (history_dir / "chain.jsonl").exists()
    assert states_dir.exists()
    for state_id in chain.states:
        assert (states_dir / f"{state_id}.egi.json").exists(), (
            f"missing snapshot for state {state_id}"
        )


def test_chain_jsonl_header_carries_schema_version_and_initial_state(
    tomos, tomos_root
):
    """The first JSONL line is the initial-state header with schema version."""
    chain, uod = _simple_chain()
    tomos.save_uod_with_chain(uod, chain)

    chain_jsonl = tomos_root / "universes" / uod.uod_id / "history" / "chain.jsonl"
    with open(chain_jsonl, "r", encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]

    import json

    header = json.loads(lines[0])
    assert header["type"] == "initial"
    assert header["initial_state_id"] == chain.initial_state_id
    assert header["schema_version"] == CHAIN_SCHEMA_VERSION

    # Subsequent lines are step records in order.
    assert len(lines) - 1 == len(chain.steps)
    for jsonl_line, step in zip(lines[1:], chain.steps):
        rec = json.loads(jsonl_line)
        assert rec["type"] == "step"
        assert rec["step_id"] == step.step_id
        assert rec["rule_name"] == step.rule_name


# --------------------------------------------------------------------------- #
# 4. §3.3 refusal aborts cleanly                                              #
# --------------------------------------------------------------------------- #


def test_save_with_chain_refuses_drifted_final_state(
    tomos, tomos_root, monkeypatch
):
    """A §3.3 violation at save_uod attestation aborts before chain writes.

    Monkeypatches the ELK engine factory used by ``_attest_uod_in_correspondence``
    to return a DTO that's missing one vertex (a totality failure).
    ``save_uod_with_chain`` delegates to ``save_uod`` first, which
    raises ``CorrespondenceViolation`` before any disk writes — so no
    chain artefacts should appear on disk.
    """
    chain, uod = _simple_chain()

    # Build a real DTO via the legitimate engine, then drop a vertex.
    from elk_layout_engine import ELKLayoutEngine
    from style_loader import load_default_style

    real_dto = ELKLayoutEngine().generate_layout(
        uod.current_egi, load_default_style()
    )
    victim = next(iter(real_dto.vertex_positions))
    broken_positions = {
        k: v for k, v in real_dto.vertex_positions.items() if k != victim
    }
    broken_dto = LayoutDTO(
        vertex_positions=broken_positions,
        predicate_positions=dict(real_dto.predicate_positions),
        cut_bounds=dict(real_dto.cut_bounds),
        ligature_paths=list(real_dto.ligature_paths),
        area_hierarchy={k: set(v) for k, v in real_dto.area_hierarchy.items()},
        viewport_bounds=real_dto.viewport_bounds,
        sheet_id=real_dto.sheet_id,
        style=real_dto.style,
    )

    class _BrokenEngine:
        def generate_layout(self, *args, **kwargs):
            return broken_dto

    monkeypatch.setattr(tomos_service, "ELKLayoutEngine", lambda: _BrokenEngine())

    with pytest.raises(CorrespondenceViolation) as excinfo:
        tomos.save_uod_with_chain(uod, chain)

    assert "totality" in str(excinfo.value)
    assert uod.uod_id in str(excinfo.value)

    # Refusal must be clean: no chain artefacts on disk.
    uod_dir = tomos_root / "universes" / uod.uod_id
    chain_jsonl = uod_dir / "history" / "chain.jsonl"
    assert not chain_jsonl.exists(), (
        "save_uod_with_chain wrote chain.jsonl despite attestation failure"
    )
    states_dir = uod_dir / "history" / "states"
    if states_dir.exists():
        assert not any(states_dir.iterdir()), (
            "save_uod_with_chain wrote state snapshots despite attestation failure"
        )


# --------------------------------------------------------------------------- #
# 5. Absent / broken chain                                                    #
# --------------------------------------------------------------------------- #


def test_load_chain_returns_none_for_unknown_uod(tomos):
    """An unknown UoD id yields None, not an error."""
    assert tomos.load_chain("does-not-exist") is None


def test_load_chain_returns_none_when_no_chain_files(tomos):
    """A UoD saved without chain files (plain save_uod) has no chain to load."""
    base = parse_egif("(P *x)")
    uod = _make_uod("no-chain-uod", base)
    tomos.save_uod(uod)

    assert tomos.load_chain(uod.uod_id) is None


def test_load_chain_returns_none_on_missing_state_snapshot(
    tomos, tomos_root
):
    """A chain.jsonl that references a missing snapshot is treated as broken.

    We refuse to return a half-loaded chain — better to return ``None``
    so the caller can decide what to do than to silently substitute or
    fail later.
    """
    chain, uod = _simple_chain()
    tomos.save_uod_with_chain(uod, chain)

    # Delete one state snapshot to simulate corruption.
    states_dir = tomos_root / "universes" / uod.uod_id / "history" / "states"
    victim = next(iter(states_dir.glob("*.egi.json")))
    victim.unlink()

    assert tomos.load_chain(uod.uod_id) is None
