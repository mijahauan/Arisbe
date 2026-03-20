"""
Area-Based Spatial Constraint System

Implements the fundamental principle that EGI areas define spatial extents
that constrain element positioning and ligature routing. This ensures that
the logical structure (EGI.area mappings) directly corresponds to spatial
boundaries that cannot be violated.

Key Principles:
- Each area has spatial extent = cut bounds minus nested cut bounds
- Elements can only exist within their area's spatial extent
- Ligatures can cross area boundaries only at connection endpoints
- Phase 2 optimization must respect these absolute spatial constraints
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from PySide6.QtCore import QRectF, QPointF

from egi_core_dau import RelationalGraphWithCuts, ElementID
from containment_hierarchy_engine import ALURect, ALUPoint


@dataclass
class AreaSpatialExtent:
    """Spatial extent available for elements within an area."""
    area_id: ElementID
    total_bounds: ALURect  # Full cut bounds
    available_bounds: ALURect  # Total bounds minus nested cuts
    nested_cut_bounds: List[ALURect]  # Bounds of nested cuts (forbidden zones)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within available area (not in nested cuts)."""
        # Must be within total bounds
        if not self.total_bounds.contains_point(x, y):
            return False
        
        # Must not be within any nested cut
        for nested_bounds in self.nested_cut_bounds:
            if nested_bounds.contains_point(x, y):
                return False
        
        return True
    
    def clamp_point_to_area(self, x: float, y: float) -> Tuple[float, float]:
        """Clamp point to nearest valid position within area with boundary clearance."""
        # CRITICAL: Elements must be INSIDE boundaries, not ON them
        boundary_clearance = 0.8  # ALU clearance from cut boundaries - increased for visibility
        
        # Clamp to available bounds (not total bounds) with clearance
        inner_left = self.available_bounds.x + boundary_clearance
        inner_right = self.available_bounds.x + self.available_bounds.width - boundary_clearance
        inner_top = self.available_bounds.y + boundary_clearance  
        inner_bottom = self.available_bounds.y + self.available_bounds.height - boundary_clearance
        
        clamped_x = max(inner_left, min(inner_right, x))
        clamped_y = max(inner_top, min(inner_bottom, y))
        
        # If clamped point is in a nested cut, move to nearest edge
        for nested_bounds in self.nested_cut_bounds:
            if nested_bounds.contains_point(clamped_x, clamped_y):
                # Move to nearest edge of the nested cut
                # Simple implementation: move to left edge
                clamped_x = nested_bounds.x - 0.1  # Small margin
        
        return clamped_x, clamped_y


class AreaSpatialConstraintSystem:
    """
    Manages spatial constraints based on EGI area mappings.
    
    Ensures that logical areas correspond to spatial extents that
    absolutely constrain element positioning and ligature routing.
    """
    
    def __init__(self):
        self.area_extents: Dict[ElementID, AreaSpatialExtent] = {}
    
    def calculate_area_extents(self, egi: RelationalGraphWithCuts, 
                             cut_bounds: Dict[ElementID, ALURect]) -> Dict[ElementID, AreaSpatialExtent]:
        """
        Calculate spatial extents for each area based on cut bounds.
        
        Args:
            egi: The EGI structure with area mappings
            cut_bounds: Cut bounds from Phase 1 containment hierarchy
            
        Returns:
            Dictionary mapping area IDs to their spatial extents
        """
        print("Calculating area spatial extents...")
        
        area_extents = {}
        
        for area_id in egi.area.keys():
            if area_id not in cut_bounds:
                continue
                
            total_bounds = cut_bounds[area_id]
            
            # Find nested cuts within this area
            nested_cuts = []
            area_contents = egi.area.get(area_id, set())
            
            for element_id in area_contents:
                if element_id in cut_bounds and element_id != area_id:
                    nested_cuts.append(cut_bounds[element_id])
            
            # Calculate available bounds (simplified - could be more sophisticated)
            # For now, use total bounds with margin for nested cuts
            margin = 1.0  # ALU margin around nested cuts
            available_bounds = ALURect(
                x=total_bounds.x + margin,
                y=total_bounds.y + margin,
                width=total_bounds.width - 2 * margin,
                height=total_bounds.height - 2 * margin
            )
            
            area_extent = AreaSpatialExtent(
                area_id=area_id,
                total_bounds=total_bounds,
                available_bounds=available_bounds,
                nested_cut_bounds=nested_cuts
            )
            
            area_extents[area_id] = area_extent
            
            print(f"Area {area_id}: total={total_bounds.width:.1f}×{total_bounds.height:.1f}, "
                  f"available={available_bounds.width:.1f}×{available_bounds.height:.1f}, "
                  f"nested_cuts={len(nested_cuts)}")
        
        self.area_extents = area_extents
        return area_extents
    
    def constrain_element_position(self, element_id: ElementID, 
                                 proposed_position: ALUPoint,
                                 egi: RelationalGraphWithCuts) -> ALUPoint:
        """
        Constrain element position to its area's spatial extent.
        
        Args:
            element_id: Element to position
            proposed_position: Desired position
            egi: EGI structure for area lookup
            
        Returns:
            Constrained position within area bounds
        """
        # Find element's area
        element_area = egi.get_context(element_id)
        
        if element_area not in self.area_extents:
            print(f"WARNING: No spatial extent for area {element_area}")
            return proposed_position
        
        area_extent = self.area_extents[element_area]
        
        # Check if proposed position is valid
        if area_extent.contains_point(proposed_position.x, proposed_position.y):
            return proposed_position
        
        # Clamp to valid position
        constrained_x, constrained_y = area_extent.clamp_point_to_area(
            proposed_position.x, proposed_position.y
        )
        
        print(f"CONSTRAINED {element_id}: ({proposed_position.x:.1f},{proposed_position.y:.1f}) "
              f"→ ({constrained_x:.1f},{constrained_y:.1f}) within area {element_area}")
        
        return ALUPoint(constrained_x, constrained_y)
    
    def validate_ligature_path(self, start_pos: ALUPoint, end_pos: ALUPoint,
                             start_area: ElementID, end_area: ElementID) -> bool:
        """
        Validate that ligature path respects area boundaries.
        
        Args:
            start_pos: Starting position
            end_pos: Ending position  
            start_area: Area of starting element
            end_area: Area of ending element
            
        Returns:
            True if path is valid, False if it violates area constraints
        """
        # Same area: path must stay within area
        if start_area == end_area:
            if start_area not in self.area_extents:
                return True  # No constraints available
                
            area_extent = self.area_extents[start_area]
            
            # Simple validation: check if both endpoints are in area
            start_valid = area_extent.contains_point(start_pos.x, start_pos.y)
            end_valid = area_extent.contains_point(end_pos.x, end_pos.y)
            
            return start_valid and end_valid
        
        # Cross-area: path can cross boundaries at endpoints only
        # More sophisticated path validation would check intermediate points
        return True
    
    def get_area_extent(self, area_id: ElementID) -> Optional[AreaSpatialExtent]:
        """Get spatial extent for an area."""
        return self.area_extents.get(area_id)
    
    def get_available_positioning_space(self, area_id: ElementID) -> Optional[ALURect]:
        """Get available positioning space within an area."""
        if area_id in self.area_extents:
            return self.area_extents[area_id].available_bounds
        return None
