#!/usr/bin/env python3
"""
Layout Post-Processor

This module post-processes Graphviz layout results to fix spacing and overlap issues
that cannot be resolved through DOT parameters alone.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from layout_result import LayoutResult, LayoutPrimitive

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
        print("🔧 Post-processing layout for spacing fixes...")
        
        # Create a copy to modify
        processed_primitives = dict(layout_result.primitives)
        
        # Step 1: Fix nested cut positioning
        processed_primitives = self._fix_nested_cuts(processed_primitives)
        
        # Step 2: Enforce sibling cut separation
        processed_primitives = self._enforce_cut_separation(processed_primitives)
        
        # Step 3: Ensure adequate padding within cuts
        processed_primitives = self._enforce_cut_padding(processed_primitives)
        
        # Step 4: Adjust element positions to prevent crowding
        processed_primitives = self._prevent_element_crowding(processed_primitives)
        
        print("✅ Layout post-processing complete")
        
        return LayoutResult(primitives=processed_primitives)
    
    def _fix_nested_cuts(self, primitives: Dict[str, LayoutPrimitive]) -> Dict[str, LayoutPrimitive]:
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
                    # This is a nested cut - ensure proper margin
                    new_bounds = self._adjust_nested_cut_bounds(cut.bounds, parent_cut.bounds)
                    
                    # Update the cut bounds
                    primitives[cut_id] = LayoutPrimitive(
                        element_id=cut.element_id,
                        element_type=cut.element_type,
                        position=cut.position,
                        bounds=new_bounds,
                        style=cut.style
                    )
                    
                    print(f"     Adjusted nested cut {cut_id[:8]} within {parent_id[:8]}")
                    break
        
        return primitives
    
    def _enforce_cut_separation(self, primitives: Dict[str, LayoutPrimitive]) -> Dict[str, LayoutPrimitive]:
        """Enforce minimum separation between sibling cuts."""
        
        cuts = [(k, v) for k, v in primitives.items() if v.element_type == 'cut']
        
        if len(cuts) < 2:
            return primitives
        
        print(f"   Enforcing separation between {len(cuts)} cuts...")
        
        # Check all pairs of cuts for adequate separation
        for i, (cut1_id, cut1) in enumerate(cuts):
            for j, (cut2_id, cut2) in enumerate(cuts[i+1:], i+1):
                if not cut1.bounds or not cut2.bounds:
                    continue
                
                # Skip if one cut is nested inside the other
                if (self._is_contained(cut1.bounds, cut2.bounds) or 
                    self._is_contained(cut2.bounds, cut1.bounds)):
                    continue
                
                # Check separation
                separation = self._calculate_separation(cut1.bounds, cut2.bounds)
                if separation < self.constraints.min_cut_separation:
                    # Move cuts apart
                    new_cut2_bounds = self._move_cut_away(cut1.bounds, cut2.bounds, 
                                                        self.constraints.min_cut_separation)
                    
                    primitives[cut2_id] = LayoutPrimitive(
                        element_id=cut2.element_id,
                        element_type=cut2.element_type,
                        position=cut2.position,
                        bounds=new_cut2_bounds,
                        style=cut2.style
                    )
                    
                    print(f"     Separated cuts {cut1_id[:8]} and {cut2_id[:8]}")
        
        return primitives
    
    def _enforce_cut_padding(self, primitives: Dict[str, LayoutPrimitive]) -> Dict[str, LayoutPrimitive]:
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
                    primitives[cut_id] = LayoutPrimitive(
                        element_id=cut.element_id,
                        element_type=cut.element_type,
                        position=cut.position,
                        bounds=required_bounds,
                        style=cut.style
                    )
                    
                    print(f"     Expanded cut {cut_id[:8]} for proper padding")
        
        return primitives
    
    def _prevent_element_crowding(self, primitives: Dict[str, LayoutPrimitive]) -> Dict[str, LayoutPrimitive]:
        """Adjust element positions to prevent crowding."""
        
        all_elements = list(primitives.items())
        
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
                    
                    primitives[elem2_id] = LayoutPrimitive(
                        element_id=elem2.element_id,
                        element_type=elem2.element_type,
                        position=elem2.position,
                        bounds=new_bounds,
                        style=elem2.style
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
    
    def _calculate_required_cut_bounds(self, contained_elements: List[Tuple[str, LayoutPrimitive]],
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
