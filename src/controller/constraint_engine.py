"""
Platform-agnostic constraint/validation engine for EGI drawings.
Operates on plain DTOs and has no GUI dependencies.

DTO schema:
{
  'sheet_id': str,
  'cuts': { id: {'rect': (x,y,w,h), 'parent_id': Optional[str]} },
  'vertices': { id: {'pos': (x,y), 'area_id': str} },
  'predicates': { id: {'rect': (x,y,w,h), 'area_id': str} },
  'ligatures': { edge_id: [vertex_ids] },
}
"""
from __future__ import annotations

from typing import Dict, Tuple, Optional, List, Any

Rect = Tuple[float, float, float, float]
Point = Tuple[float, float]


def _rect_to_scene(rect: Rect) -> Rect:
    # Rect is already in absolute coords in DTO
    return rect


def _rect_contains(a: Rect, b: Rect, eps: float = 0.5) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return (
        ax - eps <= bx
        and ay - eps <= by
        and ax + aw + eps >= bx + bw
        and ay + ah + eps >= by + bh
    )


def _rect_intersects(a: Rect, b: Rect) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (
        ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay
    )


def _rect_contains_point(r: Rect, p: Point) -> bool:
    x, y, w, h = r
    px, py = p
    return (x <= px <= x + w) and (y <= py <= y + h)


def validate_syntax(dto: Dict[str, Any], egi_locked: bool) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate syntactic constraints for the given DTO.
    Returns (ok, msg, info). In unlocked mode, out-of-area is informational.
    """
    cuts = dto.get("cuts", {})
    # Build rects map
    rects: Dict[str, Rect] = {}
    for cid, c in cuts.items():
        r = c.get("rect", (0.0, 0.0, 0.0, 0.0))
        rects[cid] = _rect_to_scene(r)

    # Cuts must be nested or disjoint
    ids = list(rects.keys())
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = rects[ids[i]], rects[ids[j]]
            if not (_rect_contains(b, a) or _rect_contains(a, b) or not _rect_intersects(a, b)):
                return False, f"Cuts overlap improperly: {ids[i]} vs {ids[j]}", {}

    # Area containment checks
    allowed = rects
    out_of_area: List[str] = []

    # Vertices: point-in-rect
    for vid, v in dto.get("vertices", {}).items():
        aid = v.get("area_id")
        if aid and aid in allowed:
            r = allowed[aid]
            pos = v.get("pos", (0.0, 0.0))
            if not _rect_contains_point(r, pos):
                if egi_locked:
                    return False, f"Vertex {vid} outside area {aid}", {}
                else:
                    out_of_area.append(f"vertex {vid}->{aid}")

    # Predicates: center-point-in-rect (approx)
    for pid, p in dto.get("predicates", {}).items():
        aid = p.get("area_id")
        if aid and aid in allowed:
            r = allowed[aid]
            rx, ry, rw, rh = p.get("rect", (0.0, 0.0, 0.0, 0.0))
            center = (rx + rw / 2.0, ry + rh / 2.0)
            if not _rect_contains_point(r, center):
                if egi_locked:
                    return False, f"Predicate {pid} outside area {aid}", {}
                else:
                    out_of_area.append(f"predicate {pid}->{aid}")

    if out_of_area:
        return True, "unlocked: area checks informational", {"out_of_area": out_of_area}
    return True, "ok", {}


def suggest_area_for_point(dto: Dict[str, Any], pos: Point, sheet_id: str) -> str:
    """Pick the deepest cut whose rect contains the point, else sheet.
    Deterministic and independent from GUI.
    """
    best = sheet_id
    best_area = None
    for cid, c in dto.get("cuts", {}).items():
        r = c.get("rect", (0.0, 0.0, 0.0, 0.0))
        if _rect_contains_point(r, pos):
            area = r[2] * r[3]
            if best_area is None or area < best_area:
                best_area = area
                best = cid
    return best


# ---------------- Locked-aware move planning APIs -----------------

def select_subgraph(dto: Dict[str, Any], selection: Dict[str, List[str]]) -> Dict[str, Any]:
    """Build a canonical subgraph descriptor from selection ids.
    selection = { 'cuts': [...], 'vertices': [...], 'predicates': [...] }

    If a cut is selected, include its full subtree (cuts + vertices + predicates contained).
    """
    sel_cuts = set(selection.get('cuts', []))
    sel_vertices = set(selection.get('vertices', []))
    sel_predicates = set(selection.get('predicates', []))

    cuts = dto.get('cuts', {})
    vertices = dto.get('vertices', {})
    predicates = dto.get('predicates', {})

    # Compute containment tree for cuts
    # Parent relation is provided in dto['cuts'][cid]['parent_id']
    parent = {cid: c.get('parent_id') for cid, c in cuts.items()}

    # Build children index
    children: Dict[Optional[str], List[str]] = {}
    for cid, pid in parent.items():
        children.setdefault(pid, []).append(cid)

    def gather_cut_subtree(root: str, acc: set):
        if root in acc:
            return
        acc.add(root)
        for ch in children.get(root, []):
            gather_cut_subtree(ch, acc)

    # Start with explicitly selected ids
    all_cuts = set()
    for cid in sel_cuts:
        if cid in cuts:
            gather_cut_subtree(cid, all_cuts)

    # If no cut selected, keep as-is
    if not all_cuts:
        all_cuts = sel_cuts

    # Include elements that live in any selected cut
    # (This captures subtree contents when a cut is selected.)
    all_vertices = set(sel_vertices)
    for vid, v in vertices.items():
        if v.get('area_id') in all_cuts:
            all_vertices.add(vid)

    all_predicates = set(sel_predicates)
    for pid, p in predicates.items():
        if p.get('area_id') in all_cuts:
            all_predicates.add(pid)

    return {
        'cuts': sorted(all_cuts),
        'vertices': sorted(all_vertices),
        'predicates': sorted(all_predicates),
    }


def plan_move(dto: Dict[str, Any], subgraph: Dict[str, List[str]], transform: Dict[str, float], locked: bool) -> Tuple[str, str, Dict[str, Any]]:
    """Plan a movement for a selected subgraph.
    transform: {'dx': float, 'dy': float}
    Returns (status, reason, layout_changes) where status in {'ok','adjusted','reject'}.
    layout_changes maps ids to their new geometry (for cuts: rect, for vertices: pos, for predicates: rect).
    """
    dx = float(transform.get('dx', 0.0))
    dy = float(transform.get('dy', 0.0))
    if dx == 0.0 and dy == 0.0:
        return 'ok', 'no-op', {}

    cuts = dto.get('cuts', {})
    vertices = dto.get('vertices', {})
    predicates = dto.get('predicates', {})

    sel_cuts = set(subgraph.get('cuts', []))
    sel_vertices = set(subgraph.get('vertices', []))
    sel_predicates = set(subgraph.get('predicates', []))

    # Build proposed changes by applying dx,dy
    changes: Dict[str, Any] = {}

    def move_rect(r: Rect) -> Rect:
        x, y, w, h = r
        return (x + dx, y + dy, w, h)

    for cid in sel_cuts:
        if cid in cuts:
            changes[cid] = {'rect': move_rect(cuts[cid].get('rect', (0.0, 0.0, 0.0, 0.0)))}

    for vid in sel_vertices:
        if vid in vertices:
            px, py = vertices[vid].get('pos', (0.0, 0.0))
            changes[vid] = {'pos': (px + dx, py + dy)}

    for pid in sel_predicates:
        if pid in predicates:
            changes.setdefault(pid, {})
            rx, ry, rw, rh = predicates[pid].get('rect', (0.0, 0.0, 0.0, 0.0))
            changes[pid]['rect'] = (rx + dx, ry + dy, rw, rh)

    # Apply proposed changes to a shallow copy of dto for validation
    trial = {
        'sheet_id': dto.get('sheet_id'),
        'cuts': {k: dict(v) for k, v in cuts.items()},
        'vertices': {k: dict(v) for k, v in vertices.items()},
        'predicates': {k: dict(v) for k, v in predicates.items()},
        'ligatures': {k: list(v) for k, v in dto.get('ligatures', {}).items()},
    }

    for cid, upd in changes.items():
        if cid in trial['cuts'] and 'rect' in upd:
            trial['cuts'][cid]['rect'] = upd['rect']
        elif cid in trial['vertices'] and 'pos' in upd:
            trial['vertices'][cid]['pos'] = upd['pos']
        elif cid in trial['predicates'] and 'rect' in upd:
            trial['predicates'][cid]['rect'] = upd['rect']

    # Locked: require that area_ids remain the same for moved elements
    if locked:
        # Build rects map for areas
        area_rects: Dict[str, Rect] = {}
        for aid, c in trial['cuts'].items():
            area_rects[aid] = c.get('rect', (0.0, 0.0, 0.0, 0.0))

        # Check moved vertices
        for vid in sel_vertices:
            v = trial['vertices'].get(vid, {})
            aid = v.get('area_id')
            if aid in area_rects:
                pos = v.get('pos', (0.0, 0.0))
                if not _rect_contains_point(area_rects[aid], pos):
                    return 'reject', f'vertex {vid} would leave area {aid}', {}

        # Check moved predicates (center-in-rect)
        for pid in sel_predicates:
            p = trial['predicates'].get(pid, {})
            aid = p.get('area_id')
            if aid in area_rects:
                rx, ry, rw, rh = p.get('rect', (0.0, 0.0, 0.0, 0.0))
                center = (rx + rw / 2.0, ry + rh / 2.0)
                if not _rect_contains_point(area_rects[aid], center):
                    return 'reject', f'predicate {pid} would leave area {aid}', {}

        # Check moved cuts remain within their parent cuts (or sheet is unconstrained)
        for cid in sel_cuts:
            c = trial['cuts'].get(cid, {})
            pid = c.get('parent_id')
            if pid is None or pid == trial.get('sheet_id'):
                # No parent rect to constrain against
                continue
            parent_rect = trial['cuts'].get(pid, {}).get('rect', (0.0, 0.0, 0.0, 0.0))
            if not _rect_contains(parent_rect, c.get('rect', (0.0, 0.0, 0.0, 0.0))):
                return 'reject', f'cut {cid} would leave parent {pid}', {}

    # Global validation (nesting/disjoint + area checks under locked flag)
    ok, msg, _info = validate_syntax(trial, locked)
    if not ok:
        return 'reject', msg, {}

    return 'ok', 'planned', changes


def commit_move(dto: Dict[str, Any], changes: Dict[str, Any]) -> Dict[str, Any]:
    """Apply layout changes to DTO immutably and return the updated DTO."""
    cuts = {k: dict(v) for k, v in dto.get('cuts', {}).items()}
    vertices = {k: dict(v) for k, v in dto.get('vertices', {}).items()}
    predicates = {k: dict(v) for k, v in dto.get('predicates', {}).items()}

    for cid, upd in changes.items():
        if cid in cuts and 'rect' in upd:
            cuts[cid]['rect'] = upd['rect']
        elif cid in vertices and 'pos' in upd:
            vertices[cid]['pos'] = upd['pos']
        elif cid in predicates and 'rect' in upd:
            predicates[cid]['rect'] = upd['rect']

    return {
        'sheet_id': dto.get('sheet_id'),
        'cuts': cuts,
        'vertices': vertices,
        'predicates': predicates,
        'ligatures': {k: list(v) for k, v in dto.get('ligatures', {}).items()},
    }
