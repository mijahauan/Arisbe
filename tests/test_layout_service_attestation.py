"""
Boundary-event attestation tests for src/web_api/services/layout_service.py.

The web layout service is the single point at which every (EGI, DTO)
pair leaves the system bound for the renderer.  Per
docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §6 and §8 bullet 1, it must
attest §3.3 correspondence before handing the pair onward.

This file verifies both directions of that contract:

1. **Happy path** — calling the service on a valid tomos UoD does not
   raise and produces a (DTO, SVG) pair.
2. **Refusal** — if the underlying ELK engine is monkeypatched to
   return a deliberately corrupted DTO, the service raises
   ``CorrespondenceViolation`` instead of letting the bad pair leave.

The refusal direction is the load-bearing one: it proves that drift
between picture and proposition cannot reach a user via this
boundary, even if some upstream component (ELK, the renderer, the
post-transformation re-layout path) regresses.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from correspondence_attestation import CorrespondenceViolation
from layout_dto import LayoutDTO, Point
from tomos_service import TomosService
from web_api.services import layout_service


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


@pytest.fixture(scope="module")
def tomos():
    return TomosService(TOMOS_ROOT)


def test_layout_service_happy_path(tomos):
    """A valid tomos UoD goes through the service without raising."""
    uod = tomos.load_uod(tomos.list_uods()[0]["uod_id"])
    dto, svg = layout_service.generate_layout(uod.current_egi)
    assert isinstance(dto, LayoutDTO)
    assert isinstance(svg, str) and svg


def test_layout_service_refuses_broken_dto(tomos, monkeypatch):
    """A corrupted DTO causes the service to raise CorrespondenceViolation."""
    uod = tomos.load_uod(tomos.list_uods()[0]["uod_id"])
    egi = uod.current_egi

    # Build a real DTO via the legitimate engine, then drop one vertex
    # from its vertex_positions to fabricate a §3.3 totality failure.
    from elk_layout_engine import ELKLayoutEngine
    from style_loader import load_default_style

    real_engine = ELKLayoutEngine()
    real_dto = real_engine.generate_layout(egi, load_default_style())
    assert real_dto.vertex_positions, "test corpus item has no vertices"
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

    monkeypatch.setattr(layout_service, "ELKLayoutEngine", lambda: _BrokenEngine())

    with pytest.raises(CorrespondenceViolation) as excinfo:
        layout_service.generate_layout(egi)
    msg = str(excinfo.value)
    assert "totality" in msg
    assert victim in msg
    assert "layout_service.generate_layout" in msg


def test_layout_service_attestation_message_carries_context(tomos, monkeypatch):
    """The context label ``layout_service.generate_layout`` reaches the message."""
    uod = tomos.load_uod(tomos.list_uods()[0]["uod_id"])
    egi = uod.current_egi

    # Build an empty DTO — every EGI element is missing.
    broken_dto = LayoutDTO(
        vertex_positions={},
        predicate_positions={},
        cut_bounds={},
        ligature_paths=[],
        area_hierarchy={},
        viewport_bounds=type(
            "VB", (), {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0}
        )(),
        sheet_id=egi.sheet,
        style=None,
    )

    class _BrokenEngine:
        def generate_layout(self, *args, **kwargs):
            return broken_dto

    monkeypatch.setattr(layout_service, "ELKLayoutEngine", lambda: _BrokenEngine())

    with pytest.raises(CorrespondenceViolation) as excinfo:
        layout_service.generate_layout(egi)
    # Context propagates verbatim.
    assert "Correspondence violated at layout_service.generate_layout" in str(
        excinfo.value
    )
