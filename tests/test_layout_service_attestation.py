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


def test_subtractive_step_preserves_survivor_positions_exactly(tomos):
    """A subtractive step (DC−) keeps every surviving element at its exact
    previous position — positional conservatism (Settle ④a, 1c).

    Renders the state before a DC− and the state after, passing the former as
    ``previous_layout``; every element that survives must have an *identical*
    position, and the served DTO must still attest §3.3.
    """
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent / "tools"))
    from build_beta_modus_ponens_chain import build_beta_modus_ponens_chain

    chain, _uod = build_beta_modus_ponens_chain()
    dc_minus = chain.steps[-1]  # the DC− step
    assert dc_minus.rule_name == "DC-"
    before = chain.states[dc_minus.from_state_id]
    after = chain.states[dc_minus.to_state_id]

    prev_dto, _ = layout_service.generate_layout(before)
    new_dto, _ = layout_service.generate_layout(after, previous_layout=prev_dto)

    prev_pos = {**prev_dto.vertex_positions, **prev_dto.predicate_positions}
    new_pos = {**new_dto.vertex_positions, **new_dto.predicate_positions}
    survivors = set(prev_pos) & set(new_pos)
    assert survivors, "expected surviving elements across a DC− step"
    for eid in survivors:
        assert prev_pos[eid].x == prev_pos[eid].x  # sanity
        assert new_pos[eid].x == pytest.approx(prev_pos[eid].x)
        assert new_pos[eid].y == pytest.approx(prev_pos[eid].y)
    # The double cut's two cuts are gone; survivors did not move.
    assert len(new_dto.cut_bounds) < len(prev_dto.cut_bounds)


def test_dc_plus_wrap_preserves_survivor_positions_exactly(tomos):
    """DC+ (wrap a subgraph in a double cut) adds only cuts, so every existing
    vertex/predicate keeps its exact position and two new cuts appear around
    the wrapped content — positional conservatism for an *additive* step
    (Settle ④a, 1c, additive-cut path).
    """
    from egif_parser_dau import parse_egif
    from rule_interaction import (
        begin_interaction, advance_interaction, apply_interaction,
    )

    before = parse_egif("(P) (Q)")
    p_id = next(e.id for e in before.E if before.get_relation_name(e.id) == "P")
    state = begin_interaction("DC+", before)
    advance_interaction(state, [p_id])  # wrap just P
    result = apply_interaction(state)
    assert result.success, result.message
    after = result.result_egi
    assert len(after.Cut) == len(before.Cut) + 2  # outer + inner

    prev_dto, _ = layout_service.generate_layout(before)
    # The additive-cut path applies (only cuts were added).
    assert layout_service._additive_cut_layout(prev_dto, after, prev_dto.style) is not None
    new_dto, svg = layout_service.generate_layout(after, previous_layout=prev_dto)

    prev_pos = {**prev_dto.predicate_positions, **prev_dto.vertex_positions}
    new_pos = {**new_dto.predicate_positions, **new_dto.vertex_positions}
    for eid in set(prev_pos) & set(new_pos):
        assert new_pos[eid].x == pytest.approx(prev_pos[eid].x)
        assert new_pos[eid].y == pytest.approx(prev_pos[eid].y)
    assert len(new_dto.cut_bounds) == 2 and svg


def test_additive_step_falls_back_to_full_layout(tomos):
    """An additive step (new material) is *not* eligible for the subtractive
    fast path; the service still returns an attested layout."""
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent / "tools"))
    from build_praeclarum_chain import build_praeclarum_chain

    chain, _uod = build_praeclarum_chain()
    ins = next(s for s in chain.steps if s.rule_name == "INS")
    before = chain.states[ins.from_state_id]
    after = chain.states[ins.to_state_id]

    prev_dto, _ = layout_service.generate_layout(before)
    # INS adds new vertices/predicates: neither incremental path applies.
    assert layout_service._subtractive_layout(prev_dto, after, prev_dto.style) is None
    assert layout_service._additive_cut_layout(prev_dto, after, prev_dto.style) is None
    # But the service still produces a valid, attested layout via the engine.
    new_dto, svg = layout_service.generate_layout(after, previous_layout=prev_dto)
    assert isinstance(new_dto, LayoutDTO) and svg


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
