#!/usr/bin/env python3
"""
Layout Post-Processor

This module post-processes Graphviz layout results to fix spacing and overlap issues
that cannot be resolved through DOT parameters alone.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from layout_engine_clean import LayoutResult, SpatialPrimitive

@dataclass
class SpacingConstraints:
    """Spacing constraints for post-processing."""
    min_cut_separation: float = 50.0  # Minimum gap between sibling cuts
    min_element_separation: float = 20.0  # Minimum gap between any elements
    cut_padding: float = 30.0  # Minimum padding inside cuts
    nested_cut_margin: float = 25.0  # Margin for nested cuts within parents

class LayoutPostProcessor:
    """Post-processes layout results to enforce spacing constraints."""
    
    def __init__(self, constraints: Optional[SpacingConstraints] = None):
        self.constraints = constraints or SpacingConstraints()
    
    def process_layout(self, layout_result: LayoutResult) -> LayoutResult:
        """
        Post-process a layout result to fix spacing and overlap issues.
        
        Steps:
        1. Fix nested cut positioning (proper containment without overlap)
        2. Enforce minimum separation between sibling cuts
        3. Ensure adequate padding within cuts
        4. Adjust element positions to prevent crowding
        """
        # If there are no predicates, do not touch the layout. Pure-cut diagrams
        # should rely entirely on Graphviz cluster containment; any translation risks
        # violating the containment hierarchy visually.
        primitives = layout_result.primitives or {}
        if not any(getattr(p, 'element_type', None) == 'predicate' for p in primitives.values()):
            # Pure-cut diagrams must be exactly what Graphviz emits. No adjustments.
            return layout_result

        print("🔧 Post-processing layout for spacing fixes...")
        
        # Create a copy to modify
        processed_primitives = dict(layout_result.primitives)
        hierarchy = getattr(layout_result, 'containment_hierarchy', {}) or {}
        
        # IMPORTANT: Do not mutate cut bounds at all. Graphviz cluster nesting
        # is the source of truth for containment. We only nudge non-cut elements.

        # Step A: Nudge predicates inward to avoid crossing cut boundaries
        processed_primitives = self._nudge_predicates_inside_cuts(processed_primitives)

        # Step B: Adjust element positions to prevent crowding (non-cut elements only)
        processed_primitives = self._prevent_element_crowding(processed_primitives)
        
        print("✅ Layout post-processing complete")
        
        # Preserve global metadata from the input layout result
        return LayoutResult(
            primitives=processed_primitives,
            canvas_bounds=getattr(layout_result, 'canvas_bounds', None),
            containment_hierarchy=getattr(layout_result, 'containment_hierarchy', {})
        )

    @classmethod
    def canonical(cls) -> "LayoutPostProcessor":
        """Factory for a deterministic, canonical preset.
        Values align with Dau-compliant spacing and prior validated theme settings.
        """
        return cls(
            constraints=SpacingConstraints(
                min_cut_separation=50.0,
                min_element_separation=25.0,
                cut_padding=35.0,
                nested_cut_margin=30.0,
            )
        )

    def process_canonical(self, layout_result: LayoutResult) -> LayoutResult:
        """Wrapper to process with canonical constraints (deterministic)."""
        return self.process_layout(layout_result)

    def _enforce_child_containment_strict(self, primitives: Dict[str, SpatialPrimitive]) -> Dict[str, SpatialPrimitive]:
        """Definitively prevent child cuts from touching/overlapping parent boundaries.
        Strategy (rect-aligned ovals):
        - Sort cuts by area descending (parents before children).
        - For each parent, compute inner rect = parent.bounds inset by nested_cut_margin.
        - For each child whose center lies inside parent, clamp child's rect to be fully
          contained in inner rect by minimal translation; if too large, shrink to fit
          (max 7% shrink to avoid distortion). Then de-overlap siblings within the same parent.
        """
        cuts = [(k, v) for k, v in primitives.items() if v.element_type == 'cut' and v.bounds]
        if len(cuts) <= 1:
            return primitives
        # Parents first
        cuts.sort(key=lambda kv: self._calculate_area(kv[1].bounds), reverse=True)
        margin = self.constraints.nested_cut_margin

        # Map parent -> list of child ids for sibling deoverlap
        parent_children: Dict[str, List[str]] = {}

        for p_id, p in cuts:
            px1, py1, px2, py2 = p.bounds
            inner = (px1 + margin, py1 + margin, px2 - margin, py2 - margin)
            ix1, iy1, ix2, iy2 = inner
            # Skip degenerate
            if ix2 <= ix1 or iy2 <= iy1:
                continue

            for c_id, c in cuts:
                if c_id == p_id or not c.bounds:
                    continue
                cx1, cy1, cx2, cy2 = c.bounds
                ccx, ccy = (cx1 + cx2) / 2.0, (cy1 + cy2) / 2.0
                # Child if center inside parent rect
                if not (ccx >= px1 and ccx <= px2 and ccy >= py1 and ccy <= py2):
                    continue
                parent_children.setdefault(p_id, []).append(c_id)

                # Desired clamped rect preserving size
                w, h = (cx2 - cx1), (cy2 - cy1)
                # If larger than inner rect, cap size with small shrink
                max_w = max(2.0, (ix2 - ix1))
                max_h = max(2.0, (iy2 - iy1))
                shrink_w = min(0.07 * w, max(0.0, w - max_w))
                shrink_h = min(0.07 * h, max(0.0, h - max_h))
                w_adj = max(2.0, w - shrink_w)
                h_adj = max(2.0, h - shrink_h)
                # Clamp center into inner rect allowing half size
                min_cx = ix1 + w_adj / 2.0
                max_cx = ix2 - w_adj / 2.0
                min_cy = iy1 + h_adj / 2.0
                max_cy = iy2 - h_adj / 2.0
                new_cx = min(max(ccx, min_cx), max_cx)
                new_cy = min(max(ccy, min_cy), max_cy)
                nb = (new_cx - w_adj / 2.0, new_cy - h_adj / 2.0,
                      new_cx + w_adj / 2.0, new_cy + h_adj / 2.0)
                primitives[c_id] = SpatialPrimitive(
                    element_id=c.element_id,
                    element_type=c.element_type,
                    position=(new_cx, new_cy),
                    bounds=nb,
                    z_index=getattr(c, 'z_index', 0),
                )

        # De-overlap siblings per parent with small radial offsets
        for p_id, child_ids in parent_children.items():
            if len(child_ids) <= 1:
                continue
            # Simple iterative push apart up to N passes
            for _ in range(4):
                moved = False
                for i in range(len(child_ids)):
                    for j in range(i + 1, len(child_ids)):
                        a = primitives.get(child_ids[i])
                        b = primitives.get(child_ids[j])
                        if not a or not b or not a.bounds or not b.bounds:
                            continue
                        ax1, ay1, ax2, ay2 = a.bounds
                        bx1, by1, bx2, by2 = b.bounds
                        # Check overlap
                        if ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1:
                            continue
                        # Compute minimal separating vector (prefer horizontal)
                        overlap_x = min(ax2 - bx1, bx2 - ax1)
                        overlap_y = min(ay2 - by1, by2 - ay1)
                        if overlap_x <= overlap_y:
                            dx = (overlap_x / 2.0) + 2.0
                            a_off = -dx
                            b_off = dx
                            a_nb = (ax1 + a_off, ay1, ax2 + a_off, ay2)
                            b_nb = (bx1 + b_off, by1, bx2 + b_off, by2)
                            primitives[a.element_id] = SpatialPrimitive(
                                element_id=a.element_id,
                                element_type=a.element_type,
                                position=((a_nb[0] + a_nb[2]) / 2.0, (a_nb[1] + a_nb[3]) / 2.0),
                                bounds=a_nb,
                                z_index=getattr(a, 'z_index', 0),
                            )
                            primitives[b.element_id] = SpatialPrimitive(
                                element_id=b.element_id,
                                element_type=b.element_type,
                                position=((b_nb[0] + b_nb[2]) / 2.0, (b_nb[1] + b_nb[3]) / 2.0),
                                bounds=b_nb,
                                z_index=getattr(b, 'z_index', 0),
                            )
                        else:
                            dy = (overlap_y / 2.0) + 2.0
                            a_off = -dy
                            b_off = dy
                            a_nb = (ax1, ay1 + a_off, ax2, ay2 + a_off)
                            b_nb = (bx1, by1 + b_off, bx2, by2 + b_off)
                            primitives[a.element_id] = SpatialPrimitive(
                                element_id=a.element_id,
                                element_type=a.element_type,
                                position=((a_nb[0] + a_nb[2]) / 2.0, (a_nb[1] + a_nb[3]) / 2.0),
                                bounds=a_nb,
                                z_index=getattr(a, 'z_index', 0),
                            )
                            primitives[b.element_id] = SpatialPrimitive(
                                element_id=b.element_id,
                                element_type=b.element_type,
                                position=((b_nb[0] + b_nb[2]) / 2.0, (b_nb[1] + b_nb[3]) / 2.0),
                                bounds=b_nb,
                                z_index=getattr(b, 'z_index', 0),
                            )
                        moved = True
                if not moved:
                    break

        return primitives
    
    def _fix_nested_cuts(self, primitives: Dict[str, SpatialPrimitive]) -> Dict[str, SpatialPrimitive]:
        """Fix nested cut positioning to ensure proper containment without overlap."""
        
        cuts = [(k, v) for k, v in primitives.items() if v.element_type == 'cut']
        
        if len(cuts) < 2:
            return primitives  # No nesting to fix
        
        print(f"   Fixing {len(cuts)} nested cuts...")
        
        # Sort cuts by area (smaller cuts are likely nested inside larger ones)
        cuts.sort(key=lambda x: self._calculate_area(x[1].bounds) if x[1].bounds else 0)
        
        for i, (cut_id, cut) in enumerate(cuts):
            if not cut.bounds:
                continue
                
            # Check if this cut is nested inside any larger cut
            for j, (parent_id, parent_cut) in enumerate(cuts[i+1:], i+1):
                if not parent_cut.bounds:
                    continue
                    
                if self._is_contained(cut.bounds, parent_cut.bounds):
                    # This is a nested cut - ensure proper margin and shrink if necessary
                    new_bounds = self._adjust_nested_cut_bounds(cut.bounds, parent_cut.bounds)
                    # If still larger than parent's inner area, shrink to fit
                    pb = parent_cut.bounds
                    margin = self.constraints.nested_cut_margin
                    ax1, ay1, ax2, ay2 = pb[0]+margin, pb[1]+margin, pb[2]-margin, pb[3]-margin
                    nx1, ny1, nx2, ny2 = new_bounds
                    if (nx2-nx1) > (ax2-ax1) or (ny2-ny1) > (ay2-ay1):
                        # Clamp to inner rect (preserve center)
                        cx = (nx1 + nx2)/2.0
                        cy = (ny1 + ny2)/2.0
                        w = min(nx2-nx1, ax2-ax1)
                        h = min(ny2-ny1, ay2-ay1)
                        new_bounds = (cx - w/2.0, cy - h/2.0, cx + w/2.0, cy + h/2.0)
                    
                    # Update the cut bounds
                    primitives[cut_id] = SpatialPrimitive(
                        element_id=cut.element_id,
                        element_type=cut.element_type,
                        position=((new_bounds[0]+new_bounds[2])/2.0, (new_bounds[1]+new_bounds[3])/2.0),
                        bounds=new_bounds,
                        z_index=getattr(cut, 'z_index', 0),
                    )
                    
                    print(f"     Adjusted nested cut {cut_id[:8]} within {parent_id[:8]}")
                    break
        
        return primitives

    def _nudge_predicates_inside_cuts(self, primitives: Dict[str, SpatialPrimitive]) -> Dict[str, SpatialPrimitive]:
        """Translate predicate boxes inward so they don't overlap cut boundaries.
        Strategy:
        - For each predicate, find the smallest cut that contains its center.
        - Compute an inner rect (cut bounds minus nested_cut_margin).
        - Clamp predicate center into inner rect and ensure full bounds containment.
        """
        cuts = [(k, v) for k, v in primitives.items() if v.element_type == 'cut' and v.bounds]
        preds = [(k, v) for k, v in primitives.items() if v.element_type == 'predicate' and v.bounds]
        if not cuts or not preds:
            return primitives

        # Sort cuts by area ascending to find smallest containing cut first
        cuts.sort(key=lambda kv: self._calculate_area(kv[1].bounds))

        margin = self.constraints.nested_cut_margin

        for pid, pred in preds:
            px1, py1, px2, py2 = pred.bounds
            pcx, pcy = (px1+px2)/2.0, (py1+py2)/2.0
            pw, ph = (px2 - px1), (py2 - py1)
            parent_bounds = None
            for cid, c in cuts:
                cx1, cy1, cx2, cy2 = c.bounds
                if pcx >= cx1 and pcy >= cy1 and pcx <= cx2 and pcy <= cy2:
                    parent_bounds = c.bounds
                    break
            if not parent_bounds:
                continue
            cx1, cy1, cx2, cy2 = parent_bounds
            # Inner rect we must fit entirely within
            ix1, iy1, ix2, iy2 = cx1 + margin, cy1 + margin, cx2 - margin, cy2 - margin
            if ix2 <= ix1 or iy2 <= iy1:
                continue
            # Clamp center into inner rect allowing half predicate size
            min_cx = ix1 + pw / 2.0
            max_cx = ix2 - pw / 2.0
            min_cy = iy1 + ph / 2.0
            max_cy = iy2 - ph / 2.0
            new_cx = min(max(pcx, min_cx), max_cx)
            new_cy = min(max(pcy, min_cy), max_cy)
            nb = (new_cx - pw/2.0, new_cy - ph/2.0, new_cx + pw/2.0, new_cy + ph/2.0)
            if nb != pred.bounds:
                primitives[pid] = SpatialPrimitive(
                    element_id=pred.element_id,
                    element_type=pred.element_type,
                    position=(new_cx, new_cy),
                    bounds=nb,
                    z_index=getattr(pred, 'z_index', 0),
                )
        return primitives
    
    def _enforce_cut_separation(self, primitives: Dict[str, SpatialPrimitive],
                                hierarchy: Dict[str, set]) -> Dict[str, SpatialPrimitive]:
        """Enforce minimum separation between true sibling cuts (same parent only)."""
        # Build siblings: parent -> [cut_ids]
        siblings: Dict[str, List[str]] = {}
        cut_ids = {k for k, v in primitives.items() if v.element_type == 'cut'}
        for parent, contents in hierarchy.items():
            sibs = [cid for cid in contents if cid in cut_ids]
            if len(sibs) > 1:
                siblings[parent] = sibs

        total_pairs = sum(max(0, len(v)-1) for v in siblings.values())
        if total_pairs:
            print(f"   Enforcing separation between {sum(len(v) for v in siblings.values())} cuts...")

        for parent, sibs in siblings.items():
            for i in range(len(sibs)):
                for j in range(i+1, len(sibs)):
                    c1_id, c2_id = sibs[i], sibs[j]
                    c1, c2 = primitives.get(c1_id), primitives.get(c2_id)
                    if not c1 or not c2 or not c1.bounds or not c2.bounds:
                        continue
                    separation = self._calculate_separation(c1.bounds, c2.bounds)
                    if separation < self.constraints.min_cut_separation:
                        new_b = self._move_cut_away(c1.bounds, c2.bounds, self.constraints.min_cut_separation)
                        cx = (new_b[0] + new_b[2]) / 2.0
                        cy = (new_b[1] + new_b[3]) / 2.0
                        primitives[c2_id] = SpatialPrimitive(
                            element_id=c2.element_id,
                            element_type=c2.element_type,
                            position=(cx, cy),
                            bounds=new_b,
                            z_index=getattr(c2, 'z_index', 0),
                        )
                        print(f"     Separated cuts {c1_id[:8]} and {c2_id[:8]}")
        return primitives
    
    def _enforce_cut_padding(self, primitives: Dict[str, SpatialPrimitive]) -> Dict[str, SpatialPrimitive]:
        """Ensure adequate padding within cuts for contained elements."""
        
        cuts = [(k, v) for k, v in primitives.items() if v.element_type == 'cut']
        predicates = [(k, v) for k, v in primitives.items() if v.element_type == 'predicate']
        
        print(f"   Enforcing padding for {len(cuts)} cuts containing {len(predicates)} predicates...")
        
        for cut_id, cut in cuts:
            if not cut.bounds:
                continue
            
            # Find predicates that should be inside this cut
            contained_predicates = []
            for pred_id, pred in predicates:
                if pred.bounds and self._is_roughly_contained(pred.bounds, cut.bounds):
                    contained_predicates.append((pred_id, pred))
            
            if contained_predicates:
                # Ensure cut is large enough to contain predicates with padding
                required_bounds = self._calculate_required_cut_bounds(contained_predicates, 
                                                                    self.constraints.cut_padding)
                
                if self._bounds_area(required_bounds) > self._bounds_area(cut.bounds):
                    # Expand the cut
                    cx = (required_bounds[0] + required_bounds[2]) / 2.0
                    cy = (required_bounds[1] + required_bounds[3]) / 2.0
                    primitives[cut_id] = SpatialPrimitive(
                        element_id=cut.element_id,
                        element_type=cut.element_type,
                        position=(cx, cy),
                        bounds=required_bounds,
                        z_index=getattr(cut, 'z_index', 0),
                    )
                    
                    print(f"     Expanded cut {cut_id[:8]} for proper padding")
        
        return primitives
    
    def _prevent_element_crowding(self, primitives: Dict[str, SpatialPrimitive]) -> Dict[str, SpatialPrimitive]:
        """Adjust element positions to prevent crowding among non-cut elements."""
        # Ignore cuts (handled separately) and any internal anchors defensively
        all_elements = [(k, v) for k, v in primitives.items()
                        if v.element_type != 'cut' and not k.startswith('anchor_')]
        
        print(f"   Preventing crowding among {len(all_elements)} elements...")
        
        # Check all pairs for minimum separation
        adjustments_made = 0
        for i, (elem1_id, elem1) in enumerate(all_elements):
            for j, (elem2_id, elem2) in enumerate(all_elements[i+1:], i+1):
                if not elem1.bounds or not elem2.bounds:
                    continue
                
                separation = self._calculate_separation(elem1.bounds, elem2.bounds)
                if separation < self.constraints.min_element_separation:
                    # Move second element away from first
                    new_bounds = self._move_element_away(elem1.bounds, elem2.bounds,
                                                       self.constraints.min_element_separation)
                    cx = (new_bounds[0] + new_bounds[2]) / 2.0
                    cy = (new_bounds[1] + new_bounds[3]) / 2.0
                    primitives[elem2_id] = SpatialPrimitive(
                        element_id=elem2.element_id,
                        element_type=elem2.element_type,
                        position=(cx, cy),
                        bounds=new_bounds,
                        z_index=getattr(elem2, 'z_index', 0),
                    )
                    
                    adjustments_made += 1
                    if adjustments_made <= 3:  # Limit output
                        print(f"     Separated elements {elem1_id[:8]} and {elem2_id[:8]}")
        
        if adjustments_made > 3:
            print(f"     ... and {adjustments_made - 3} more element separations")
        
        return primitives
    
    # Helper methods
    
    def _calculate_area(self, bounds: Tuple[float, float, float, float]) -> float:
        """Calculate area of bounds."""
        x1, y1, x2, y2 = bounds
        return (x2 - x1) * (y2 - y1)
    
    def _bounds_area(self, bounds: Tuple[float, float, float, float]) -> float:
        """Calculate area of bounds."""
        return self._calculate_area(bounds)
    
    def _is_contained(self, inner_bounds: Tuple[float, float, float, float],
                     outer_bounds: Tuple[float, float, float, float]) -> bool:
        """Check if inner bounds are contained within outer bounds."""
        ix1, iy1, ix2, iy2 = inner_bounds
        ox1, oy1, ox2, oy2 = outer_bounds
        
        return (ix1 >= ox1 and iy1 >= oy1 and ix2 <= ox2 and iy2 <= oy2)
    
    def _is_roughly_contained(self, inner_bounds: Tuple[float, float, float, float],
                            outer_bounds: Tuple[float, float, float, float]) -> bool:
        """Check if inner bounds are roughly contained (with some tolerance)."""
        ix1, iy1, ix2, iy2 = inner_bounds
        ox1, oy1, ox2, oy2 = outer_bounds
        
        tolerance = 5.0  # Allow some overlap
        return (ix1 >= ox1 - tolerance and iy1 >= oy1 - tolerance and 
                ix2 <= ox2 + tolerance and iy2 <= oy2 + tolerance)
    
    def _calculate_separation(self, bounds1: Tuple[float, float, float, float],
                            bounds2: Tuple[float, float, float, float]) -> float:
        """Calculate minimum separation between two bounds."""
        x1_min, y1_min, x1_max, y1_max = bounds1
        x2_min, y2_min, x2_max, y2_max = bounds2
        
        # Calculate gaps in both dimensions
        gap_x = max(0, min(abs(x1_max - x2_min), abs(x2_max - x1_min)))
        gap_y = max(0, min(abs(y1_max - y2_min), abs(y2_max - y1_min)))
        
        # If they overlap, separation is 0
        if (x1_max > x2_min and x2_max > x1_min and 
            y1_max > y2_min and y2_max > y1_min):
            return 0.0
        
        # Return minimum gap
        return min(gap_x, gap_y) if gap_x > 0 and gap_y > 0 else max(gap_x, gap_y)
    
    def _adjust_nested_cut_bounds(self, nested_bounds: Tuple[float, float, float, float],
                                parent_bounds: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """Adjust nested cut bounds to ensure proper margin within parent."""
        nx1, ny1, nx2, ny2 = nested_bounds
        px1, py1, px2, py2 = parent_bounds
        
        margin = self.constraints.nested_cut_margin
        
        # Ensure nested cut is properly positioned within parent with margin
        new_x1 = max(nx1, px1 + margin)
        new_y1 = max(ny1, py1 + margin)
        new_x2 = min(nx2, px2 - margin)
        new_y2 = min(ny2, py2 - margin)
        
        # Ensure minimum size
        if new_x2 - new_x1 < 50:
            center_x = (new_x1 + new_x2) / 2
            new_x1 = center_x - 25
            new_x2 = center_x + 25
        
        if new_y2 - new_y1 < 30:
            center_y = (new_y1 + new_y2) / 2
            new_y1 = center_y - 15
            new_y2 = center_y + 15
        
        return (new_x1, new_y1, new_x2, new_y2)
    
    def _move_cut_away(self, fixed_bounds: Tuple[float, float, float, float],
                      moving_bounds: Tuple[float, float, float, float],
                      min_separation: float) -> Tuple[float, float, float, float]:
        """Move a cut away from another to achieve minimum separation."""
        fx1, fy1, fx2, fy2 = fixed_bounds
        mx1, my1, mx2, my2 = moving_bounds
        
        # Calculate current separation
        current_sep = self._calculate_separation(fixed_bounds, moving_bounds)
        needed_move = min_separation - current_sep
        
        if needed_move <= 0:
            return moving_bounds
        
        # Move horizontally (prefer horizontal movement)
        if mx1 > fx2:  # Moving cut is to the right
            offset_x = needed_move
            offset_y = 0
        elif mx2 < fx1:  # Moving cut is to the left
            offset_x = -needed_move
            offset_y = 0
        else:  # Vertical movement needed
            if my1 > fy2:  # Moving cut is below
                offset_x = 0
                offset_y = needed_move
            else:  # Moving cut is above
                offset_x = 0
                offset_y = -needed_move
        
        return (mx1 + offset_x, my1 + offset_y, mx2 + offset_x, my2 + offset_y)
    
    def _move_element_away(self, fixed_bounds: Tuple[float, float, float, float],
                          moving_bounds: Tuple[float, float, float, float],
                          min_separation: float) -> Tuple[float, float, float, float]:
        """Move an element away from another to achieve minimum separation."""
        return self._move_cut_away(fixed_bounds, moving_bounds, min_separation)
    
    def _calculate_required_cut_bounds(self, contained_elements: List[Tuple[str, SpatialPrimitive]],
                                     padding: float) -> Tuple[float, float, float, float]:
        """Calculate required bounds for a cut to contain elements with padding."""
        if not contained_elements:
            return (0, 0, 100, 50)  # Default size
        
        # Find bounding box of all contained elements
        min_x = min(elem.bounds[0] for _, elem in contained_elements if elem.bounds)
        min_y = min(elem.bounds[1] for _, elem in contained_elements if elem.bounds)
        max_x = max(elem.bounds[2] for _, elem in contained_elements if elem.bounds)
        max_y = max(elem.bounds[3] for _, elem in contained_elements if elem.bounds)
        
        # Add padding
        return (min_x - padding, min_y - padding, max_x + padding, max_y + padding)
