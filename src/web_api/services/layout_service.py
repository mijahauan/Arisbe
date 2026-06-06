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


def _additive_placement_layout(prev_dto: LayoutDTO, egi, style) -> Optional[LayoutDTO]:
    """Positional conservatism for a step that adds new *vertices/predicates*
    (Settle ④a, 1c — the additive-placement case: INS / IT+).

    Unlike DC+ (which only wraps survivors in new cuts — ``_additive_cut_layout``)
    INS and IT+ introduce genuinely new geometry that must be *placed*, not just
    kept.  We:

    1. Pin every **survivor** (id present in *prev_dto*) at its exact prior
       position / bounds.
    2. Borrow the new subgraph's **internal** shape from a fresh full-ELK
       reference layout (correct nested-cut bounds, intra-subgraph layout, and —
       for IT+ — an echo of the source's shape via ``_structural_key`` ordering).
    3. Translate that new subgraph **as a rigid group** into free space in its
       target area (below the area's existing content), so survivors don't move.
    4. Grow ancestor (survivor) cut bounds **bottom-up** around the placed group
       (cuts only ever expand), then rebuild *all* ligature paths geometrically
       (endpoints are pinned, so survivor lines stay anchored; new and grown-cut
       lines route correctly).

    The safety net here is **weaker than for other incremental builders**: §3.3 is
    topological (containment / incidence / crossings vs axis-aligned bounds) and
    will *not* catch two elements *visually overlapping* in the same area.  So
    this builder owns overlap-avoidance directly — it runs an explicit
    same-area overlap guard and returns ``None`` (caller falls back to a full
    layout) if the placed group or a grown cut would collide with a sibling, in
    addition to the §3.3 attestation the caller still performs.

    Returns ``None`` whenever the step is not a clean additive placement we can
    handle conservatively (no new vertex/predicate; a survivor disappeared; new
    content spans more than one target area; placement can't be sized; an overlap
    is unavoidable) so the caller cold-lays-out instead.
    """
    vpos = prev_dto.vertex_positions
    ppos = prev_dto.predicate_positions
    cb = prev_dto.cut_bounds

    cur_v = {v.id for v in egi.V}
    cur_e = {e.id for e in egi.E}
    cur_c = {c.id for c in egi.Cut}
    cut_ids = cur_c

    # Purely additive: every prior survivor must still be present.  (INS / IT+
    # never remove; a removal means the subtractive path, not this one.)
    if not set(vpos).issubset(cur_v):
        return None
    if not set(ppos).issubset(cur_e):
        return None
    if not set(cb).issubset(cur_c):
        return None

    new_v = cur_v - set(vpos)
    new_e = cur_e - set(ppos)
    new_c = cur_c - set(cb)
    new_all = new_v | new_e | new_c
    if not (new_v or new_e):
        # No new vertex/predicate — DC+ wrap / subtractive / identity handle it.
        return None

    # Parent area of every element (the sheet has no parent).
    parent_of: Dict[str, str] = {}
    for area_id, contents in egi.area.items():
        for child in contents:
            parent_of[child] = area_id

    # The new subgraph's top-level elements are the new elements whose parent
    # area is *not* itself new — i.e. they sit directly in a survivor area.
    top_new = {eid for eid in new_all if parent_of.get(eid) not in new_c}
    target_areas = {parent_of.get(eid) for eid in top_new}
    if len(target_areas) != 1 or None in target_areas:
        return None  # new content spans >1 area (or the sheet w/o parent) — bail
    target_area = next(iter(target_areas))

    engine = ELKLayoutEngine()
    sizes = engine._compute_element_sizes(egi, style)
    ref = engine.generate_layout(egi, style)
    pad = float(getattr(style, "cut_padding", 20) or 20)
    margin = float(getattr(style, "diagram_margin", 40) or 40)
    gap = pad

    def _box(eid, vp, pp, cbnds) -> Optional[BoundingBox]:
        if eid in vp:
            p = vp[eid]
            w, h = sizes.get(eid, (10.0, 10.0))
            return BoundingBox(p.x - w / 2, p.y - h / 2, p.x + w / 2, p.y + h / 2)
        if eid in pp:
            p = pp[eid]
            w, h = sizes.get(eid, (40.0, 16.0))
            return BoundingBox(p.x - w / 2, p.y - h / 2, p.x + w / 2, p.y + h / 2)
        if eid in cbnds:
            return cbnds[eid]
        return None

    # Reference (full-ELK) box of every new element, and the group's bbox.
    ref_boxes = {
        eid: _box(eid, ref.vertex_positions, ref.predicate_positions, ref.cut_bounds)
        for eid in new_all
    }
    if any(b is None for b in ref_boxes.values()):
        return None
    group = BoundingBox(
        min(b.min_x for b in ref_boxes.values()),
        min(b.min_y for b in ref_boxes.values()),
        max(b.max_x for b in ref_boxes.values()),
        max(b.max_y for b in ref_boxes.values()),
    )

    # Free-space target inside the target area: below its existing survivor
    # content (so survivors don't move), left-aligned to that content.
    survivor_children = [
        c for c in egi.area.get(target_area, frozenset())
        if c not in new_all
    ]
    sib_boxes = [
        _box(c, vpos, ppos, cb) for c in survivor_children
    ]
    sib_boxes = [b for b in sib_boxes if b is not None]
    if sib_boxes:
        place_x = min(b.min_x for b in sib_boxes)
        place_y = max(b.max_y for b in sib_boxes) + gap
    elif target_area in cb:
        # Empty survivor cut being filled (INS into an empty cut).
        place_x = cb[target_area].min_x + pad
        place_y = cb[target_area].min_y + pad
    else:
        # Target is the (empty) sheet — keep the reference placement.
        place_x = group.min_x
        place_y = group.min_y

    tx = place_x - group.min_x
    ty = place_y - group.min_y

    def _shift(b: BoundingBox) -> BoundingBox:
        return BoundingBox(b.min_x + tx, b.min_y + ty, b.max_x + tx, b.max_y + ty)

    # Final vertex / predicate positions: survivors pinned, new translated.
    final_vpos = dict(vpos)
    for vid in new_v:
        p = ref.vertex_positions[vid]
        final_vpos[vid] = Point(p.x + tx, p.y + ty)
    final_ppos = dict(ppos)
    for eid in new_e:
        p = ref.predicate_positions[eid]
        final_ppos[eid] = Point(p.x + tx, p.y + ty)

    # Cut bounds: new cuts take the translated reference box; survivor cuts grow
    # bottom-up to enclose any new content, never shrinking below their prior box.
    new_cut_box = {cid: _shift(ref.cut_bounds[cid]) for cid in new_c}
    computed: Dict[str, BoundingBox] = {}

    def elem_final_box(eid) -> Optional[BoundingBox]:
        return _box(eid, final_vpos, final_ppos, {})

    def cut_box(cid) -> BoundingBox:
        if cid in computed:
            return computed[cid]
        if cid in new_c:
            computed[cid] = new_cut_box[cid]
            return computed[cid]
        b = cb[cid]  # survivor cut: start from its prior box (only grow)
        for child in egi.area.get(cid, frozenset()):
            childb = cut_box(child) if child in cut_ids else elem_final_box(child)
            if childb is None:
                continue
            padded = BoundingBox(
                childb.min_x - pad, childb.min_y - pad,
                childb.max_x + pad, childb.max_y + pad,
            )
            b = BoundingBox(
                min(b.min_x, padded.min_x), min(b.min_y, padded.min_y),
                max(b.max_x, padded.max_x), max(b.max_y, padded.max_y),
            )
        computed[cid] = b
        return b

    for c in egi.Cut:
        cut_box(c.id)

    # Same-area overlap guard — the failure mode §3.3 can't see.
    def _overlaps(a: BoundingBox, b: BoundingBox) -> bool:
        eps = 1.0
        return (a.min_x + eps < b.max_x and b.min_x + eps < a.max_x
                and a.min_y + eps < b.max_y and b.min_y + eps < a.max_y)

    for area_id, contents in egi.area.items():
        boxes = []
        for child in contents:
            cbx = cut_box(child) if child in cut_ids else elem_final_box(child)
            if cbx is not None:
                boxes.append(cbx)
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if _overlaps(boxes[i], boxes[j]):
                    return None

    ligature_paths = engine._build_ligature_paths(
        egi, final_vpos, final_ppos, sizes, computed
    )

    all_boxes = list(computed.values())
    for eid in list(final_vpos) + list(final_ppos):
        b = elem_final_box(eid)
        if b is not None:
            all_boxes.append(b)
    viewport = BoundingBox(
        min(b.min_x for b in all_boxes) - margin,
        min(b.min_y for b in all_boxes) - margin,
        max(b.max_x for b in all_boxes) + margin,
        max(b.max_y for b in all_boxes) + margin,
    ) if all_boxes else prev_dto.viewport_bounds

    return LayoutDTO(
        vertex_positions=final_vpos,
        predicate_positions=final_ppos,
        cut_bounds=computed,
        ligature_paths=ligature_paths,
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
            (_additive_placement_layout, "layout_service.incremental_additive_placement"),
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
