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


def test_ins_placement_pins_survivors_exactly(tomos):
    """INS adds genuinely new vertices/predicates, so it is handled by the
    *placement* builder (Settle ④a, 1c — additive-placement): survivors keep
    their exact positions and only the inserted content is placed in free space.

    The subtractive / additive-cut fast paths don't apply (INS adds material
    they refuse); the placement builder engages and pins survivors at 0px, and
    the served DTO still attests §3.3.
    """
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent / "tools"))
    from build_praeclarum_chain import build_praeclarum_chain

    chain, _uod = build_praeclarum_chain()
    # The 2nd INS in Praeclarum inserts into an area that already has survivors.
    ins_steps = [s for s in chain.steps if s.rule_name == "INS"]
    ins = ins_steps[-1]
    before = chain.states[ins.from_state_id]
    after = chain.states[ins.to_state_id]

    prev_dto, _ = layout_service.generate_layout(before)
    assert layout_service._subtractive_layout(prev_dto, after, prev_dto.style) is None
    assert layout_service._additive_cut_layout(prev_dto, after, prev_dto.style) is None
    # The placement builder *does* apply and pins survivors.
    cand = layout_service._additive_placement_layout(prev_dto, after, prev_dto.style)
    assert cand is not None, "placement builder should engage for this INS"

    new_dto, svg = layout_service.generate_layout(after, previous_layout=prev_dto)
    assert isinstance(new_dto, LayoutDTO) and svg
    prev_pos = {**prev_dto.vertex_positions, **prev_dto.predicate_positions}
    new_pos = {**new_dto.vertex_positions, **new_dto.predicate_positions}
    survivors = set(prev_pos) & set(new_pos)
    assert survivors, "expected surviving elements across the INS step"
    for eid in survivors:
        assert new_pos[eid].x == pytest.approx(prev_pos[eid].x)
        assert new_pos[eid].y == pytest.approx(prev_pos[eid].y)
    # New material did appear.
    assert len(new_pos) > len(survivors)


def test_it_plus_placement_pins_survivors_when_room(tomos):
    """IT+ (copy a subgraph into a deeper area) places the copy in free space
    and pins survivors at 0px when the destination area has room — including
    when the copy *extends a line of identity* (Beta), where the rebuilt
    ligature must still attest §3.3."""
    from egif_parser_dau import parse_egif
    from rule_interaction import (
        begin_interaction, advance_interaction, apply_interaction,
    )

    # Beta: P(x) on the sheet, x shared into a roomy cut; IT+ copies (P x) in,
    # extending the line of identity across the cut boundary.
    before = parse_egif("(P *x) ~[ (Q x) ]")
    p_id = next(e.id for e in before.E if before.get_relation_name(e.id) == "P")
    cut_id = next(iter(before.Cut)).id
    state = begin_interaction("IT+", before)
    advance_interaction(state, [p_id])
    advance_interaction(state, cut_id)
    result = apply_interaction(state)
    assert result.success, result.message
    after = result.result_egi

    prev_dto, _ = layout_service.generate_layout(before)
    cand = layout_service._additive_placement_layout(prev_dto, after, prev_dto.style)
    assert cand is not None, "placement builder should engage for a roomy IT+"

    new_dto, svg = layout_service.generate_layout(after, previous_layout=prev_dto)
    assert isinstance(new_dto, LayoutDTO) and svg
    prev_pos = {**prev_dto.vertex_positions, **prev_dto.predicate_positions}
    new_pos = {**new_dto.vertex_positions, **new_dto.predicate_positions}
    survivors = set(prev_pos) & set(new_pos)
    assert survivors
    for eid in survivors:
        assert new_pos[eid].x == pytest.approx(prev_pos[eid].x)
        assert new_pos[eid].y == pytest.approx(prev_pos[eid].y)


def test_placement_falls_back_when_no_room(tomos):
    """When the new material can't be placed without overlapping a survivor
    sibling, the placement builder declines (returns ``None``) rather than emit
    a colliding layout that §3.3 (topological) can't catch — and the service
    still produces a valid, attested layout via a full re-layout.

    Praeclarum's first IT+ copies into a previously *empty* cut wedged between
    siblings: there is no room to grow it incrementally, so the builder must
    fall back."""
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent / "tools"))
    from build_praeclarum_chain import build_praeclarum_chain

    chain, _uod = build_praeclarum_chain()
    it_plus = next(s for s in chain.steps if s.rule_name == "IT+")
    before = chain.states[it_plus.from_state_id]
    after = chain.states[it_plus.to_state_id]

    prev_dto, _ = layout_service.generate_layout(before)
    assert layout_service._additive_placement_layout(
        prev_dto, after, prev_dto.style
    ) is None, "builder should decline when placement would overlap a sibling"
    # The service still yields a valid, §3.3-attested layout via full re-layout.
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


def test_the_deltas_path_never_serves_unattested_geometry(tomos, monkeypatch):
    """Whatever geometry `generate_layout(deltas=…)` serves has been attested.

    Added 2026-09-22 (docket 6f). `apply_deltas` attests each surviving delta,
    but `rebuild_ligature_anchors` then moved ligature endpoints with nothing
    checking the result, and the clockwise block *keeps* that DTO whenever
    placement is a no-op or its own attestation fails. So this path could serve
    geometry that had never been passed to `attest_correspondence` — observed on
    2 of 5 runs of one fixture, the intermittency coming from ELK ordering. In
    every observed case the geometry did satisfy the check, so it was an
    unverified serve rather than a live violation; the point of a boundary hook
    is that the difference is not left to luck.

    The comparison is on **geometry, not object identity**: the last two steps
    of the pipeline (`assign_order_labels`, `assign_second_order_marks`) return
    fresh DTOs by design and are annotation only — positions, bounds and paths
    are untouched, which is precisely why they need no re-attestation. An
    identity assertion would fail on those and say nothing about the defect.
    """
    uod = tomos.load_uod(tomos.list_uods()[0]["uod_id"])
    egi = uod.current_egi
    base, _svg = layout_service.generate_layout(egi)
    vid = next(iter(base.vertex_positions))
    before = base.vertex_positions[vid]

    def _geometry(d):
        return (
            tuple(sorted((k, v.x, v.y) for k, v in d.vertex_positions.items())),
            tuple(sorted((k, v.x, v.y) for k, v in d.predicate_positions.items())),
            tuple(sorted((k, b.min_x, b.min_y, b.max_x, b.max_y)
                         for k, b in d.cut_bounds.items())),
            tuple(sorted((p.predicate_id, p.vertex_id, p.port_index,
                          tuple((pt.x, pt.y) for pt in p.points))
                         for p in d.ligature_paths)),
        )

    attested, contexts = [], []
    real = layout_service.attest_correspondence

    def spy(e, d, **kwargs):
        result = real(e, d, **kwargs)
        attested.append(_geometry(d))
        contexts.append(kwargs.get("context"))
        return result

    monkeypatch.setattr(layout_service, "attest_correspondence", spy)

    from presentation_deltas import PresentationDelta

    delta = PresentationDelta(
        op="move_vertex", params={"vertex_id": vid, "dx": 25.0, "dy": 18.0})
    served, _svg = layout_service.generate_layout(egi, deltas=[delta])

    assert served.vertex_positions[vid] != before, "the nudge did not take"
    assert attested, "the deltas path attested nothing at all"

    # The claim.
    assert _geometry(served) in attested, (
        "generate_layout served geometry that was never attested — the deltas "
        "path changed it after the last check")

    # And the deterministic half. The assertion above only bites when the
    # rebuild actually moves something, which depends on ELK ordering — on many
    # fixtures the rebuild is a no-op and the served geometry matches the
    # post-delta attestation anyway. That is precisely why the defect survived:
    # it was invisible most of the time. So we also pin that the re-attestation
    # *happens*, which does not depend on the fixture.
    assert "layout_service.rebuild_ligature_anchors" in contexts, (
        "the deltas path did not re-attest after rebuilding ligature anchors; "
        "whatever it serves from there is unverified whenever the rebuild "
        "moves a ligature endpoint")
