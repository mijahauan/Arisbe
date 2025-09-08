"""
Platform-agnostic constraint/validation engine for EGI drawings.
Implements the exact constraint policy specified:

PERMISSIVE MODE (syntactic constraints only):
- Free drag during movement
- Snap back on invalid drop (cuts overlap or elements superimposed)
- Allow renaming vertices and predicates
- Allow re-ordering arity

STRICT MODE (semantic constraints ON):
- Option 2: Automatic adjustments during drag/insertion
  - Parent elements adjust (cuts expand, elements move away)
  - Area elements move away from encroaching elements
- Prohibit renaming
- Prohibit re-ordering arity

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
from enum import Enum

Rect = Tuple[float, float, float, float]
Point = Tuple[float, float]


class ConstraintMode(Enum):
    """Constraint modes matching the specified policy."""
    PERMISSIVE = "permissive"  # Syntactic only - free drag, snap back on invalid drop
    STRICT = "strict"          # Semantic ON - automatic adjustments, prohibit renaming


class ValidationResult:
    """Result of constraint validation."""
    def __init__(self, valid: bool, message: str = "", adjustments: Optional[Dict[str, Any]] = None):
        self.valid = valid
        self.message = message
        self.adjustments = adjustments or {}


def _rect_to_scene(rect: Rect) -> Rect:
    """Convert rect to scene coordinates (already absolute in DTO)."""
    return rect


def _rect_contains(a: Rect, b: Rect, eps: float = 0.5) -> bool:
    """Check if rect a fully contains rect b with epsilon tolerance."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return (
        ax - eps <= bx
        and ay - eps <= by
        and ax + aw + eps >= bx + bw
        and ay + ah + eps >= by + bh
    )


def _rect_intersects(a: Rect, b: Rect) -> bool:
    """Check if two rectangles intersect."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (
        ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay
    )


def _rect_contains_point(r: Rect, p: Point) -> bool:
    """Check if rectangle contains point."""
    x, y, w, h = r
    px, py = p
    return (x <= px <= x + w) and (y <= py <= y + h)


def _expand_rect_to_contain(parent: Rect, child: Rect, margin: float = 10.0) -> Rect:
    """Expand parent rectangle to fully contain child with margin."""
    px, py, pw, ph = parent
    cx, cy, cw, ch = child
    
    # Calculate required bounds
    new_left = min(px, cx - margin)
    new_top = min(py, cy - margin)
    new_right = max(px + pw, cx + cw + margin)
    new_bottom = max(py + ph, cy + ch + margin)
    
    return (new_left, new_top, new_right - new_left, new_bottom - new_top)


def _move_elements_away(elements: List[Dict[str, Any]], obstacle: Rect, min_distance: float = 15.0) -> Dict[str, Any]:
    """Move elements away from an obstacle rectangle."""
    adjustments = {}
    
    for elem in elements:
        elem_id = elem.get('id')
        elem_type = elem.get('type')
        
        if elem_type == 'vertex':
            pos = elem.get('pos', (0.0, 0.0))
            if _point_too_close_to_rect(pos, obstacle, min_distance):
                new_pos = _push_point_away_from_rect(pos, obstacle, min_distance)
                adjustments[elem_id] = {'pos': new_pos}
                
        elif elem_type == 'predicate':
            rect = elem.get('rect', (0.0, 0.0, 0.0, 0.0))
            if _rect_too_close_to_rect(rect, obstacle, min_distance):
                new_rect = _push_rect_away_from_rect(rect, obstacle, min_distance)
                adjustments[elem_id] = {'rect': new_rect}
                
        elif elem_type == 'cut':
            rect = elem.get('rect', (0.0, 0.0, 0.0, 0.0))
            if _rect_too_close_to_rect(rect, obstacle, min_distance):
                new_rect = _push_rect_away_from_rect(rect, obstacle, min_distance)
                adjustments[elem_id] = {'rect': new_rect}
    
    return adjustments


def _point_too_close_to_rect(point: Point, rect: Rect, min_distance: float) -> bool:
    """Check if point is too close to rectangle."""
    px, py = point
    rx, ry, rw, rh = rect
    
    # Find closest point on rectangle to the point
    closest_x = max(rx, min(px, rx + rw))
    closest_y = max(ry, min(py, ry + rh))
    
    # Calculate distance
    dx = px - closest_x
    dy = py - closest_y
    distance = (dx * dx + dy * dy) ** 0.5
    
    return distance < min_distance


def _rect_too_close_to_rect(rect1: Rect, rect2: Rect, min_distance: float) -> bool:
    """Check if two rectangles are too close."""
    return _rect_intersects(rect1, rect2) or _rect_distance(rect1, rect2) < min_distance


def _rect_distance(rect1: Rect, rect2: Rect) -> float:
    """Calculate minimum distance between two rectangles."""
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    
    # Calculate separation on each axis
    dx = max(0, max(x1 - (x2 + w2), x2 - (x1 + w1)))
    dy = max(0, max(y1 - (y2 + h2), y2 - (y1 + h1)))
    
    return (dx * dx + dy * dy) ** 0.5


def _push_point_away_from_rect(point: Point, rect: Rect, min_distance: float) -> Point:
    """Push point away from rectangle to maintain minimum distance."""
    px, py = point
    rx, ry, rw, rh = rect
    
    # Find direction to push
    center_x = rx + rw / 2
    center_y = ry + rh / 2
    
    dx = px - center_x
    dy = py - center_y
    
    if dx == 0 and dy == 0:
        # Point is at center, push up
        return (px, ry - min_distance)
    
    # Normalize direction and push
    length = (dx * dx + dy * dy) ** 0.5
    if length > 0:
        dx /= length
        dy /= length
    
    # Push to minimum distance from rectangle edge
    push_distance = min_distance + max(rw, rh) / 2
    return (center_x + dx * push_distance, center_y + dy * push_distance)


def _push_rect_away_from_rect(rect1: Rect, rect2: Rect, min_distance: float) -> Rect:
    """Push rect1 away from rect2 to maintain minimum distance."""
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    
    # Calculate centers
    c1x, c1y = x1 + w1 / 2, y1 + h1 / 2
    c2x, c2y = x2 + w2 / 2, y2 + h2 / 2
    
    # Direction from rect2 to rect1
    dx = c1x - c2x
    dy = c1y - c2y
    
    if dx == 0 and dy == 0:
        # Overlapping centers, push up
        new_y = y2 - h1 - min_distance
        return (x1, new_y, w1, h1)
    
    # Normalize direction
    length = (dx * dx + dy * dy) ** 0.5
    if length > 0:
        dx /= length
        dy /= length
    
    # Calculate required separation
    required_distance = min_distance + (w1 + w2) / 2 + (h1 + h2) / 2
    
    # New center position
    new_c1x = c2x + dx * required_distance
    new_c1y = c2y + dy * required_distance
    
    # Convert back to rect coordinates
    new_x = new_c1x - w1 / 2
    new_y = new_c1y - h1 / 2
    
    return (new_x, new_y, w1, h1)


def validate_syntactic_constraints(dto: Dict[str, Any]) -> ValidationResult:
    """
    Validate syntactic constraints (always enforced in both modes):
    - Cuts must be nested or disjoint (no partial overlaps)
    - No element spatial overlaps
    - Ligature bridge validation
    """
    # 1. Cut nesting validation
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
                return ValidationResult(
                    False, 
                    f"SYNTACTIC VIOLATION: Cuts partially overlap - {cut_ids[i]} vs {cut_ids[j]}"
                )

    # 2. Spatial overlap validation
    violations = _check_spatial_overlaps(dto)
    if violations:
        return ValidationResult(False, f"SYNTACTIC VIOLATION: {violations[0]}")

    # 3. Ligature bridge validation
    bridge_info = _check_ligature_crossings(dto)
    
    return ValidationResult(True, "Syntactic constraints satisfied", {"bridges_needed": bridge_info})


def validate_semantic_constraints(dto: Dict[str, Any]) -> ValidationResult:
    """
    Validate semantic constraints (only enforced in STRICT mode):
    - Area containment (elements must be in assigned areas)
    - Logical structure preservation
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

    if violations:
        return ValidationResult(False, f"SEMANTIC VIOLATION: {violations[0]}", {"violations": violations})
    
    return ValidationResult(True, "Semantic constraints satisfied")


def validate_movement_permissive(dto: Dict[str, Any], element_id: str, element_type: str, 
                                new_position: Any) -> ValidationResult:
    """
    PERMISSIVE MODE movement validation:
    - Allow free drag during movement
    - Validate on drop, return snap-back if invalid
    """
    # Create trial DTO with new position
    trial_dto = dict(dto)
    trial_dto['cuts'] = {k: dict(v) for k, v in dto.get('cuts', {}).items()}
    trial_dto['vertices'] = {k: dict(v) for k, v in dto.get('vertices', {}).items()}
    trial_dto['predicates'] = {k: dict(v) for k, v in dto.get('predicates', {}).items()}
    
    # Apply new position
    if element_type == 'vertex' and element_id in trial_dto['vertices']:
        trial_dto['vertices'][element_id]['pos'] = new_position
    elif element_type == 'predicate' and element_id in trial_dto['predicates']:
        trial_dto['predicates'][element_id]['rect'] = new_position
    elif element_type == 'cut' and element_id in trial_dto['cuts']:
        trial_dto['cuts'][element_id]['rect'] = new_position
    
    # Validate syntactic constraints only
    result = validate_syntactic_constraints(trial_dto)
    
    if not result.valid:
        # Return original position for snap-back
        original_position = None
        if element_type == 'vertex' and element_id in dto['vertices']:
            original_position = dto['vertices'][element_id].get('pos')
        elif element_type == 'predicate' and element_id in dto['predicates']:
            original_position = dto['predicates'][element_id].get('rect')
        elif element_type == 'cut' and element_id in dto['cuts']:
            original_position = dto['cuts'][element_id].get('rect')
        
        return ValidationResult(
            False, 
            f"Invalid drop: {result.message}. Snapping back to original position.",
            {element_id: {element_type: original_position}}
        )
    
    return ValidationResult(True, "Movement allowed")


def validate_movement_strict(dto: Dict[str, Any], element_id: str, element_type: str, 
                           new_position: Any) -> ValidationResult:
    """
    STRICT MODE movement validation:
    - Option 2: Automatic adjustments to accommodate movement
    - Parent elements adjust (cuts expand, elements move away)
    - Area elements move away from encroaching elements
    """
    # Create trial DTO with new position
    trial_dto = dict(dto)
    trial_dto['cuts'] = {k: dict(v) for k, v in dto.get('cuts', {}).items()}
    trial_dto['vertices'] = {k: dict(v) for k, v in dto.get('vertices', {}).items()}
    trial_dto['predicates'] = {k: dict(v) for k, v in dto.get('predicates', {}).items()}
    
    # Apply new position
    if element_type == 'vertex' and element_id in trial_dto['vertices']:
        trial_dto['vertices'][element_id]['pos'] = new_position
    elif element_type == 'predicate' and element_id in trial_dto['predicates']:
        trial_dto['predicates'][element_id]['rect'] = new_position
    elif element_type == 'cut' and element_id in trial_dto['cuts']:
        trial_dto['cuts'][element_id]['rect'] = new_position
    
    adjustments = {}
    
    # Get the moved element's new bounds
    moved_element_bounds = None
    if element_type == 'vertex':
        x, y = new_position
        radius = trial_dto['vertices'][element_id].get('radius', 4.0)
        moved_element_bounds = (x - radius, y - radius, radius * 2, radius * 2)
    elif element_type == 'predicate':
        moved_element_bounds = new_position
    elif element_type == 'cut':
        moved_element_bounds = new_position
    
    if moved_element_bounds:
        # Find elements that need to move away
        elements_to_adjust = []
        
        # Check vertices
        for vid, v in trial_dto['vertices'].items():
            if vid != element_id:
                pos = v.get('pos', (0.0, 0.0))
                if _point_too_close_to_rect(pos, moved_element_bounds, 15.0):
                    elements_to_adjust.append({
                        'id': vid, 'type': 'vertex', 'pos': pos
                    })
        
        # Check predicates
        for pid, p in trial_dto['predicates'].items():
            if pid != element_id:
                rect = p.get('rect', (0.0, 0.0, 0.0, 0.0))
                if _rect_too_close_to_rect(rect, moved_element_bounds, 10.0):
                    elements_to_adjust.append({
                        'id': pid, 'type': 'predicate', 'rect': rect
                    })
        
        # Check cuts
        for cid, c in trial_dto['cuts'].items():
            if cid != element_id:
                rect = c.get('rect', (0.0, 0.0, 0.0, 0.0))
                if _rect_too_close_to_rect(rect, moved_element_bounds, 10.0):
                    elements_to_adjust.append({
                        'id': cid, 'type': 'cut', 'rect': rect
                    })
        
        # Calculate adjustments to move elements away
        element_adjustments = _move_elements_away(elements_to_adjust, moved_element_bounds)
        adjustments.update(element_adjustments)
        
        # Check if parent cuts need to expand
        if element_type in ['vertex', 'predicate']:
            area_id = None
            if element_type == 'vertex':
                area_id = trial_dto['vertices'][element_id].get('area_id')
            else:
                area_id = trial_dto['predicates'][element_id].get('area_id')
            
            if area_id and area_id in trial_dto['cuts']:
                parent_rect = trial_dto['cuts'][area_id].get('rect', (0.0, 0.0, 0.0, 0.0))
                if not _rect_contains_point(parent_rect, new_position if element_type == 'vertex' else (new_position[0] + new_position[2]/2, new_position[1] + new_position[3]/2)):
                    # Expand parent cut
                    expanded_rect = _expand_rect_to_contain(parent_rect, moved_element_bounds)
                    adjustments[area_id] = {'rect': expanded_rect}
    
    # Apply adjustments to trial DTO and validate
    for adj_id, adj_data in adjustments.items():
        if adj_id in trial_dto['vertices'] and 'pos' in adj_data:
            trial_dto['vertices'][adj_id]['pos'] = adj_data['pos']
        elif adj_id in trial_dto['predicates'] and 'rect' in adj_data:
            trial_dto['predicates'][adj_id]['rect'] = adj_data['rect']
        elif adj_id in trial_dto['cuts'] and 'rect' in adj_data:
            trial_dto['cuts'][adj_id]['rect'] = adj_data['rect']
    
    # Validate both syntactic and semantic constraints
    syntactic_result = validate_syntactic_constraints(trial_dto)
    if not syntactic_result.valid:
        return ValidationResult(False, f"Automatic adjustment failed: {syntactic_result.message}")
    
    semantic_result = validate_semantic_constraints(trial_dto)
    if not semantic_result.valid:
        return ValidationResult(False, f"Automatic adjustment failed: {semantic_result.message}")
    
    return ValidationResult(True, "Movement allowed with automatic adjustments", adjustments)


def validate_naming_change(mode: ConstraintMode, element_type: str, element_id: str, new_name: str) -> ValidationResult:
    """
    Validate naming changes based on constraint mode:
    - PERMISSIVE: Allow renaming
    - STRICT: Prohibit renaming
    """
    if mode == ConstraintMode.STRICT:
        return ValidationResult(False, "Renaming prohibited in STRICT mode")
    
    return ValidationResult(True, "Renaming allowed in PERMISSIVE mode")


def validate_arity_change(mode: ConstraintMode, predicate_id: str, new_arity: int) -> ValidationResult:
    """
    Validate arity changes based on constraint mode:
    - PERMISSIVE: Allow arity reordering
    - STRICT: Prohibit arity reordering
    """
    if mode == ConstraintMode.STRICT:
        return ValidationResult(False, "Arity reordering prohibited in STRICT mode")
    
    return ValidationResult(True, "Arity reordering allowed in PERMISSIVE mode")


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
    
    # Vertices - circular bounds with padding
    for vid, v in dto.get("vertices", {}).items():
        x, y = v.get("pos", (0.0, 0.0))
        radius = v.get("radius", 4.0)
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


def suggest_area_for_point(dto: Dict[str, Any], pos: Point, sheet_id: str) -> str:
    """Pick the deepest cut whose rect contains the point, else sheet."""
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

