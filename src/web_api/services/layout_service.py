"""
Layout and SVG generation service for the Arisbe Web API.

Wraps ELKLayoutEngine and SimpleSVGRenderer with anchoring support.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

# Ensure src/ is on path (when imported from web_api/services/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from correspondence_attestation import attest_correspondence, CorrespondenceViolation
from elk_layout_engine import ELKLayoutEngine
from layout_dto import LayoutDTO, BoundingBox, LigaturePath, Point
from simple_svg_renderer import SimpleSVGRenderer
from style_loader import load_default_style, load_style
from egif_generator_dau import EGIFGenerator


@dataclass
class LayoutDelta:
    """Position anchor for an element during re-layout."""
    new_position: Optional[Tuple[float, float]] = None


def _subtractive_layout(prev_dto: LayoutDTO, egi, style) -> Optional[LayoutDTO]:
    """Positional conservatism for a *subtractive* step (Settle ④a, 1c).

    When the new EGI's elements are a *subset* of the previous layout's — a
    purely subtractive transformation (ERA / IT− / DC−) — every surviving
    element can keep its **exact** previous position and the removed elements
    simply vanish.  Nothing moves: maximal conservatism, by construction, with
    no new material to place (the hard part of additive rules).

    Returns ``None`` if any element in the new EGI is absent from *prev_dto*
    (the step *added* material), so the caller falls back to a full layout.
    The reused geometry is still §3.3-attested by the caller; a fallback covers
    the rare case where dropping cuts invalidates a reused ligature path.
    """
    vpos = prev_dto.vertex_positions
    ppos = prev_dto.predicate_positions
    cb = prev_dto.cut_bounds

    # Subtractive ⇔ every element of the new graph already had a position.
    if any(v.id not in vpos for v in egi.V):
        return None
    if any(e.id not in ppos for e in egi.E):
        return None
    if any(c.id not in cb for c in egi.Cut):
        return None

    new_v = {v.id for v in egi.V}
    new_e = {e.id for e in egi.E}
    new_c = {c.id for c in egi.Cut}

    return LayoutDTO(
        vertex_positions={vid: vpos[vid] for vid in new_v},
        predicate_positions={pid: ppos[pid] for pid in new_e},
        cut_bounds={cid: cb[cid] for cid in new_c},
        # A surviving ligature whose endpoints both survive keeps its path; one
        # touching a removed element is dropped.
        ligature_paths=[
            lp for lp in prev_dto.ligature_paths
            if lp.predicate_id in new_e and lp.vertex_id in new_v
        ],
        area_hierarchy={a: set(c) for a, c in egi.area.items()},
        viewport_bounds=prev_dto.viewport_bounds,
        sheet_id=egi.sheet,
        style=style,
    )


def _additive_cut_layout(prev_dto: LayoutDTO, egi, style) -> Optional[LayoutDTO]:
    """Positional conservatism for a step that only adds *cuts* (Settle ④a, 1c).

    DC+ wraps an existing subgraph in a double cut: it introduces two new cuts
    but **no new vertices or predicates**, and the wrapped elements are
    survivors.  So every vertex/predicate keeps its exact previous position and
    we recompute cut bounds bottom-up around those fixed positions — the new
    double cut simply appears around the wrapped content, and ancestor cuts grow
    just enough to contain it.

    Returns ``None`` (caller falls back to a full layout) when the step adds any
    vertex/predicate (INS / IT+ — genuinely new geometry to place), or adds an
    *empty* new cut (no positioned content to anchor it — e.g. an empty double
    cut dropped into a non-empty area).  §3.3 is attested by the caller, with a
    full-layout fallback if the recomputed bounds overlap a sibling.
    """
    vpos = prev_dto.vertex_positions
    ppos = prev_dto.predicate_positions

    # No new vertices/predicates (those would need genuine placement).
    if any(v.id not in vpos for v in egi.V):
        return None
    if any(e.id not in ppos for e in egi.E):
        return None
    new_cuts = {c.id for c in egi.Cut} - set(prev_dto.cut_bounds)
    if not new_cuts:
        return None  # nothing added — the subtractive/identity path handles it

    sizes = ELKLayoutEngine()._compute_element_sizes(egi, style)
    pad = float(getattr(style, "cut_padding", 20) or 20)
    cut_ids = {c.id for c in egi.Cut}
    computed: Dict[str, BoundingBox] = {}

    class _Unplaceable(Exception):
        pass

    def elem_box(eid) -> BoundingBox:
        pos = vpos.get(eid) or ppos.get(eid)
        w, h = sizes.get(eid, (10.0, 10.0))
        return BoundingBox(pos.x - w / 2, pos.y - h / 2, pos.x + w / 2, pos.y + h / 2)

    def cut_box(cid) -> BoundingBox:
        if cid in computed:
            return computed[cid]
        boxes = []
        for c in egi.area.get(cid, frozenset()):
            boxes.append(cut_box(c) if c in cut_ids else elem_box(c))
        if not boxes:
            # Empty cut: keep its prior box if it had one; a *new* empty cut
            # has nothing to anchor it, so we can't place it incrementally.
            if cid in prev_dto.cut_bounds:
                computed[cid] = prev_dto.cut_bounds[cid]
                return computed[cid]
            raise _Unplaceable()
        b = BoundingBox(
            min(x.min_x for x in boxes) - pad,
            min(x.min_y for x in boxes) - pad,
            max(x.max_x for x in boxes) + pad,
            max(x.max_y for x in boxes) + pad,
        )
        computed[cid] = b
        return b

    try:
        for c in egi.Cut:
            cut_box(c.id)
    except _Unplaceable:
        return None

    boxes = list(computed.values())
    eboxes = [elem_box(e) for e in list(vpos) + list(ppos) if e in vpos or e in ppos]
    all_boxes = boxes + eboxes
    margin = float(getattr(style, "diagram_margin", 40) or 40)
    viewport = BoundingBox(
        min(b.min_x for b in all_boxes) - margin,
        min(b.min_y for b in all_boxes) - margin,
        max(b.max_x for b in all_boxes) + margin,
        max(b.max_y for b in all_boxes) + margin,
    ) if all_boxes else prev_dto.viewport_bounds

    return LayoutDTO(
        vertex_positions=dict(vpos),
        predicate_positions=dict(ppos),
        cut_bounds=computed,
        ligature_paths=list(prev_dto.ligature_paths),  # incidence unchanged
        area_hierarchy={a: set(c) for a, c in egi.area.items()},
        viewport_bounds=viewport,
        sheet_id=egi.sheet,
        style=style,
    )


def generate_layout(
    egi,
    previous_layout: Optional[LayoutDTO] = None,
    style_name: Optional[str] = None,
) -> Tuple[LayoutDTO, str]:
    """Generate layout and SVG for an EGI.

    If *previous_layout* is provided, unchanged elements are anchored at
    their previous positions to reduce visual jump.

    *style_name* selects the visual style — the *projection's* visual
    realization of the one coordinate-free ``NaturalLayout`` (Dau, Peirce,
    Sowa, …).  ``None`` uses the default (dau-compliant).  Style varies
    the *manifest*, never the *meaning*: §3.3 attests every styled render
    because its checks are topological (containment / incidence /
    crossings against axis-aligned bounds), not stylistic.

    Returns:
        (layout_dto, svg_string)
    """
    style = load_style(style_name) if style_name else load_default_style()
    engine = ELKLayoutEngine()

    # Positional conservatism (Settle ④a, 1c): when the step only *removed*
    # material, keep every survivor at its exact previous position instead of
    # re-laying-out the whole graph (which drifts everything as it re-balances).
    # Only engages with a previous layout and a subtractive change; additive
    # steps and fresh renders fall through to the full layout.
    dto: Optional[LayoutDTO] = None
    if previous_layout is not None:
        for builder, ctx in (
            (_subtractive_layout, "layout_service.incremental_subtractive"),
            (_additive_cut_layout, "layout_service.incremental_additive_cut"),
        ):
            candidate = builder(previous_layout, egi, style)
            if candidate is None:
                continue
            try:
                attest_correspondence(egi, candidate, context=ctx)
                dto = candidate
                break
            except CorrespondenceViolation:
                # Reused/recomputed geometry no longer corresponds (e.g. a
                # dropped cut mis-crosses a ligature, or a recomputed wrap
                # overlaps a sibling) — fall through to a full layout.
                dto = None

    if dto is None:
        dto = engine.generate_layout(egi, style)
        # Boundary-event attestation (docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md
        # §6, §8 bullet 1).  Every (EGI, DTO) pair we hand to the renderer
        # — initial diagram serve, post-transformation re-render, anywhere
        # else this wrapper is called from — is verified to be in §3.3
        # correspondence before it leaves the service.  A drift between
        # picture and proposition raises CorrespondenceViolation; the
        # system refuses to serve a drawing it can't attest.
        attest_correspondence(egi, dto, context="layout_service.generate_layout")

    # Generate EGIF linear form for the renderer title
    try:
        egif = EGIFGenerator().generate(egi)
    except Exception:
        egif = ""

    renderer = SimpleSVGRenderer()
    svg = renderer.render_to_svg(dto, egif=egif, egi=egi)

    return dto, svg


def attest_and_render(
    egi,
    dto: LayoutDTO,
) -> Tuple[LayoutDTO, str]:
    """Attest and render an *already-built* LayoutDTO — no layout engine pass.

    Used for Settle ④b (manual regime-3 touch-up): a user has nudged a
    vertex / reshaped a cut / rerouted a ligature via ``presentation_ops``,
    producing a new DTO whose geometry must be preserved exactly (re-running
    ELK would discard the nudge).  The (EGI, DTO) pair is still §3.3-attested
    before it leaves the service — a regime-3 op is *defined* to preserve
    correspondence, so this is the runtime guarantee that it did.

    Returns:
        (dto, svg_string) — the same DTO passed in, plus its rendered SVG.
    """
    attest_correspondence(egi, dto, context="layout_service.attest_and_render")

    try:
        egif = EGIFGenerator().generate(egi)
    except Exception:
        egif = ""

    renderer = SimpleSVGRenderer()
    svg = renderer.render_to_svg(dto, egif=egif, egi=egi)
    return dto, svg


def layout_dto_to_dict(dto: LayoutDTO) -> dict:
    """Serialize a LayoutDTO to a JSON-compatible dict."""
    vertex_positions = {
        k: {"x": v.x, "y": v.y} for k, v in dto.vertex_positions.items()
    }
    predicate_positions = {
        k: {"x": v.x, "y": v.y} for k, v in dto.predicate_positions.items()
    }
    cut_bounds = {
        k: {
            "min_x": b.min_x,
            "min_y": b.min_y,
            "max_x": b.max_x,
            "max_y": b.max_y,
        }
        for k, b in dto.cut_bounds.items()
    }
    ligature_paths = [
        {
            "predicate_id": lig.predicate_id,
            "vertex_id": lig.vertex_id,
            "points": [{"x": p.x, "y": p.y} for p in lig.points],
            "port_index": lig.port_index,
        }
        for lig in dto.ligature_paths
    ]
    viewport_bounds = {
        "min_x": dto.viewport_bounds.min_x,
        "min_y": dto.viewport_bounds.min_y,
        "max_x": dto.viewport_bounds.max_x,
        "max_y": dto.viewport_bounds.max_y,
    }
    return {
        "vertex_positions": vertex_positions,
        "predicate_positions": predicate_positions,
        "cut_bounds": cut_bounds,
        "ligature_paths": ligature_paths,
        "viewport_bounds": viewport_bounds,
        "sheet_id": dto.sheet_id,
    }
