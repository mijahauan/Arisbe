"""
Boundary-event attestation tests for tomos_service save_uod and load_uod.

The tomos corpus is the canonical persistent record of asserted UoDs.
Per docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §6, both
``save_uod`` (writing a graph as a persistent record) and ``load_uod``
(retrieving a stored graph) are boundary events at which
correspondence must be attested.

This file verifies both directions for both boundaries:

1. **Happy path** — every UoD in the tomos corpus loads through
   ``load_uod`` without raising.  This is the corpus-wide proof that
   the load-time attestation hook does not reject anything that's
   currently in production.
2. **Save refusal** — when the underlying layout engine is monkeypatched
   to produce a corrupted DTO, ``save_uod`` raises
   ``CorrespondenceViolation`` *before* any disk writes occur.  The
   corpus is never left in a half-saved drifted state.
3. **Load refusal** — same idea on the load side.  A monkeypatched
   engine causes ``load_uod`` to raise rather than silently returning
   a UoD whose drawing would not correspond to its EGI.
4. **Empty-UoD no-op** — a UoD with ``current_egi is None`` does not
   trigger a render-and-attest cycle (there's no claim yet to
   correspond to).

Together these pin down the contract: the persistent record either
holds a §3.3-compliant pair, or no record at all.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from correspondence_attestation import CorrespondenceViolation
from layout_dto import LayoutDTO
import tomos_service
from tomos_service import TomosService


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


@pytest.fixture(scope="module")
def tomos():
    return TomosService(TOMOS_ROOT)


def _uod_ids():
    service = TomosService(TOMOS_ROOT)
    return [u["uod_id"] for u in service.list_uods()]


# --------------------------------------------------------------------------- #
# Happy path                                                                  #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_load_uod_passes_attestation_for_every_corpus_uod(uod_id, tomos):
    """Every tomos UoD loads through the attestation hook without raising.

    Corpus-wide proof that the persistent record matches what the
    layout engine produces from it.  If this ever fails for a UoD,
    something has drifted: either the file was edited externally, or
    the layout engine changed in a way that no longer reproduces the
    saved layout.
    """
    uod = tomos.load_uod(uod_id)
    assert uod is not None
    assert uod.current_egi is not None


# --------------------------------------------------------------------------- #
# Save refusal                                                                #
# --------------------------------------------------------------------------- #


def test_save_uod_refuses_drifted_drawing(tomos, monkeypatch, tmp_path):
    """``save_uod`` raises ``CorrespondenceViolation`` if rendering drifts.

    Monkeypatches the ELK engine the save path uses to return a DTO
    that's missing one vertex — a totality failure.  The attestation
    inside ``save_uod`` raises before any files are written.
    """
    # Take a real UoD as the candidate to save.
    uod = tomos.load_uod(_uod_ids()[0])
    assert uod is not None
    egi = uod.current_egi

    # Build a real DTO via the legitimate engine, then drop a vertex.
    from elk_layout_engine import ELKLayoutEngine
    from style_loader import load_default_style

    real_dto = ELKLayoutEngine().generate_layout(egi, load_default_style())
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

    # Use a temp tomos root so the save path is isolated.
    save_target = TomosService(tmp_path)

    with pytest.raises(CorrespondenceViolation) as excinfo:
        save_target.save_uod(uod)

    msg = str(excinfo.value)
    assert "totality" in msg
    assert victim in msg
    assert "tomos_service.save_uod" in msg
    assert uod.uod_id in msg

    # No partial save: the UoD's directory should not have been created.
    # (The save_uod path creates the directory and writes files only after
    # attestation succeeds; if attestation raised first, no directory
    # exists.)  This is a structural-aborts-cleanly assertion.
    expected_dir = tmp_path / "universes" / uod.uod_id
    assert not expected_dir.exists() or not any(expected_dir.iterdir()), (
        "save_uod created files despite attestation failure"
    )


# --------------------------------------------------------------------------- #
# Load refusal                                                                #
# --------------------------------------------------------------------------- #


def test_load_uod_refuses_drifted_drawing(tomos, monkeypatch):
    """``load_uod`` raises ``CorrespondenceViolation`` if rendering drifts.

    Same monkeypatching trick.  Any drift the engine introduces
    between the persisted EGI and what gets rendered must be surfaced
    at load time, not silently accepted.
    """
    uod = tomos.load_uod(_uod_ids()[0])
    assert uod is not None
    egi = uod.current_egi

    from elk_layout_engine import ELKLayoutEngine
    from style_loader import load_default_style

    real_dto = ELKLayoutEngine().generate_layout(egi, load_default_style())
    new_predicates = dict(real_dto.predicate_positions)
    new_predicates["stray_predicate_load_test"] = real_dto.predicate_positions[
        next(iter(real_dto.predicate_positions))
    ]
    broken_dto = LayoutDTO(
        vertex_positions=dict(real_dto.vertex_positions),
        predicate_positions=new_predicates,
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
        tomos.load_uod(_uod_ids()[0])

    msg = str(excinfo.value)
    assert "injectivity" in msg
    assert "stray_predicate_load_test" in msg
    assert "tomos_service.load_uod" in msg


# --------------------------------------------------------------------------- #
# Empty-UoD no-op                                                             #
# --------------------------------------------------------------------------- #


def test_attest_helper_no_op_for_empty_uod(monkeypatch):
    """A UoD with ``current_egi is None`` does not invoke the layout engine.

    Empty / freshly-created UoDs hold no claim yet; attestation has
    nothing to check.  The helper short-circuits without instantiating
    ELKLayoutEngine.  This test confirms that — if the engine were
    invoked here, the monkeypatched stand-in's ``__call__`` would fire.
    """
    from tomos_service import _attest_uod_in_correspondence

    invoked = []

    def _engine_factory():
        invoked.append(True)
        raise RuntimeError("should not have been called")

    monkeypatch.setattr(tomos_service, "ELKLayoutEngine", _engine_factory)

    class _EmptyUoD:
        current_egi = None

    _attest_uod_in_correspondence(_EmptyUoD(), context="empty-test")
    assert invoked == [], "ELKLayoutEngine was instantiated for an empty UoD"
