"""
Platform-agnostic constraint/validation engine for EGI drawings.
Operates on plain DTOs and has no GUI dependencies.

Implements corrected syntactic vs semantic constraint separation:
- Syntactic: Spatial overlap prevention, cut nesting, ligature bridges
- Semantic: Area containment, logical structure preservation

DTO schema:
{
  'sheet_id': str,
  'cuts': { id: {'rect': (x,y,w,h), 'parent_id': Optional[str]} },
  'vertices': { id: {'pos': (x,y), 'radius': float, 'area_id': str, 'name': Optional[str]} },
  'predicates': { id: {'rect': (x,y,w,h), 'area_id': str, 'text': str} },
  'ligatures': { edge_id: {'path': [(x,y)...], 'width': float, 'vertices': [ids]} },
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


def validate_syntactic_constraints(dto: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate syntactic constraints: spatial overlap prevention and cut nesting.
    Returns (ok, msg, info). Syntactic constraints are always enforced.
    """
    # 1. Cut nesting validation - cuts must be nested or disjoint
    cuts = dto.get("cuts", {})
    cut_rects: Dict[str, Rect] = {}
    for cid, c in cuts.items():
        r = c.get("rect", (0.0, 0.0, 0.0, 0.0))
        cut_rects[cid] = _rect_to_scene(r)

    # Check all cut pairs for proper nesting or disjoint placement
    cut_ids = list(cut_rects.keys())
    for i in range(len(cut_ids)):
        for j in range(i + 1, len(cut_ids)):
            a, b = cut_rects[cut_ids[i]], cut_rects[cut_ids[j]]
            if not (_rect_contains(b, a) or _rect_contains(a, b) or not _rect_intersects(a, b)):
                return False, f"SYNTACTIC VIOLATION: Cut lines overlap - {cut_ids[i]} vs {cut_ids[j]}", {}

    # 2. Spatial overlap validation - no element spatial extents can traverse each other
    violations = _check_spatial_overlaps(dto)
    if violations:
        return False, f"SYNTACTIC VIOLATION: {violations[0]}", {"violations": violations}

    # 3. Ligature bridge validation - check for non-planar crossings
    bridge_info = _check_ligature_crossings(dto)
    
    return True, "Syntactic constraints satisfied", {"bridges_needed": bridge_info}


def validate_semantic_constraints(dto: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate semantic constraints: area containment and logical structure.
    Returns (ok, msg, info). Only enforced when semantic mode is active.
    """
    cuts = dto.get("cuts", {})
    cut_rects: Dict[str, Rect] = {}
    for cid, c in cuts.items():
        r = c.get("rect", (0.0, 0.0, 0.0, 0.0))
        cut_rects[cid] = _rect_to_scene(r)

    violations: List[str] = []

    # Area containment - vertices must be within their assigned areas
    for vid, v in dto.get("vertices", {}).items():
        aid = v.get("area_id")
        if aid and aid in cut_rects:
            area_rect = cut_rects[aid]
            pos = v.get("pos", (0.0, 0.0))
            if not _rect_contains_point(area_rect, pos):
                violations.append(f"Vertex {vid} outside assigned area {aid}")

    # Area containment - predicates must be within their assigned areas
    for pid, p in dto.get("predicates", {}).items():
        aid = p.get("area_id")
        if aid and aid in cut_rects:
            area_rect = cut_rects[aid]
            px, py, pw, ph = p.get("rect", (0.0, 0.0, 0.0, 0.0))
            center = (px + pw / 2.0, py + ph / 2.0)
            if not _rect_contains_point(area_rect, center):
                violations.append(f"Predicate {pid} outside assigned area {aid}")

    # Ligature area constraints - single-area ligatures cannot cross cuts
    ligature_violations = _check_ligature_area_constraints(dto)
    violations.extend(ligature_violations)

    if violations:
        return False, f"SEMANTIC VIOLATION: {violations[0]}", {"violations": violations}
    
    return True, "Semantic constraints satisfied", {}


def _check_spatial_overlaps(dto: Dict[str, Any]) -> List[str]:
    """Check for spatial overlaps between element extents with padding."""
    violations = []
    
    # Get all element bounds with padding
    element_bounds = _get_all_element_bounds_with_padding(dto)
    
    # Check all pairs for overlap
    elements = list(element_bounds.keys())
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            elem_a, elem_b = elements[i], elements[j]
            bounds_a, bounds_b = element_bounds[elem_a], element_bounds[elem_b]
            
            if _rect_intersects(bounds_a, bounds_b):
                violations.append(f"Spatial overlap between {elem_a} and {elem_b}")
    
    return violations


def _get_all_element_bounds_with_padding(dto: Dict[str, Any]) -> Dict[str, Rect]:
    """Get bounding rectangles for all elements including padding."""
    PADDING = 3.0  # pixels of padding around each element
    bounds = {}
    
    # Vertices - circular bounds with padding, expanded for optional name text
    for vid, v in dto.get("vertices", {}).items():
        x, y = v.get("pos", (0.0, 0.0))
        radius = v.get("radius", 4.0)
        name = v.get("name")
        
        if name:
            # Estimate text bounds (rough approximation: 8px per character, 12px height)
            text_width = len(name) * 8.0
            text_height = 12.0
            # Position text below vertex dot
            total_width = max(radius * 2, text_width) + 2 * PADDING
            total_height = radius * 2 + text_height + 2 * PADDING
            bounds[f"vertex_{vid}"] = (x - total_width/2, y - radius - PADDING, total_width, total_height)
        else:
            # Just the dot with padding
            total_radius = radius + PADDING
            bounds[f"vertex_{vid}"] = (x - total_radius, y - total_radius, total_radius * 2, total_radius * 2)
    
    # Predicates - rectangular bounds with padding
    for pid, p in dto.get("predicates", {}).items():
        px, py, pw, ph = p.get("rect", (0.0, 0.0, 0.0, 0.0))
        bounds[f"predicate_{pid}"] = (px - PADDING, py - PADDING, pw + 2*PADDING, ph + 2*PADDING)
    
    # Ligatures - path bounds with width and padding
    for lid, lig in dto.get("ligatures", {}).items():
        path = lig.get("path", [])
        width = lig.get("width", 2.0) + PADDING
        if len(path) >= 2:
            bounds[f"ligature_{lid}"] = _calculate_path_bounds(path, width)
    
    # Cuts - rectangular bounds (no padding, they define boundaries)
    for cid, c in dto.get("cuts", {}).items():
        cx, cy, cw, ch = c.get("rect", (0.0, 0.0, 0.0, 0.0))
        bounds[f"cut_{cid}"] = (cx, cy, cw, ch)
    
    return bounds


def _calculate_path_bounds(path: List[Tuple[float, float]], width: float) -> Rect:
    """Calculate bounding rectangle for a ligature path with given width."""
    if not path:
        return (0.0, 0.0, 0.0, 0.0)
    
    xs = [p[0] for p in path]
    ys = [p[1] for p in path]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    half_width = width / 2.0
    return (min_x - half_width, min_y - half_width, 
            max_x - min_x + width, max_y - min_y + width)


def _check_ligature_crossings(dto: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check for ligature-to-ligature crossings that need bridge icons."""
    ligatures = dto.get("ligatures", {})
    bridges_needed = []
    
    lig_ids = list(ligatures.keys())
    for i in range(len(lig_ids)):
        for j in range(i + 1, len(lig_ids)):
            lig_a, lig_b = ligatures[lig_ids[i]], ligatures[lig_ids[j]]
            path_a = lig_a.get("path", [])
            path_b = lig_b.get("path", [])
            
            crossing_point = _find_path_intersection(path_a, path_b)
            if crossing_point:
                bridges_needed.append({
                    "ligature_a": lig_ids[i],
                    "ligature_b": lig_ids[j],
                    "crossing_point": crossing_point,
                    "bridge_needed": True
                })
    
    return bridges_needed


def _find_path_intersection(path_a: List[Tuple[float, float]], 
                           path_b: List[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
    """Find intersection point between two ligature paths."""
    # Simplified intersection detection - check each segment pair
    for i in range(len(path_a) - 1):
        for j in range(len(path_b) - 1):
            seg_a = (path_a[i], path_a[i + 1])
            seg_b = (path_b[j], path_b[j + 1])
            
            intersection = _line_segment_intersection(seg_a, seg_b)
            if intersection:
                return intersection
    
    return None


def _line_segment_intersection(seg_a: Tuple[Point, Point], 
                              seg_b: Tuple[Point, Point]) -> Optional[Point]:
    """Calculate intersection point of two line segments."""
    (x1, y1), (x2, y2) = seg_a
    (x3, y3), (x4, y4) = seg_b
    
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:  # Parallel lines
        return None
    
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    
    if 0 <= t <= 1 and 0 <= u <= 1:  # Intersection within both segments
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return (ix, iy)
    
    return None


def _check_ligature_area_constraints(dto: Dict[str, Any]) -> List[str]:
    """Check semantic constraint: single-area ligatures cannot cross cuts."""
    violations = []
    
    # This would need more complex implementation based on actual ligature-area relationships
    # For now, return empty list as placeholder
    
    return violations


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
