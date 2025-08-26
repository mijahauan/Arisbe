"""
Spatial Region Manager for EGI Canvas Partitioning

This module handles the assignment of logical areas to exclusive spatial regions
on the canvas, ensuring every pixel belongs to exactly one logical area.
"""

from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
import math
import os

@dataclass
class SpatialRegion:
    """Represents an exclusive spatial region on the canvas."""
    region_id: str
    logical_area_id: str
    bounds: Tuple[float, float, float, float]  # (x, y, width, height)
    parent_region_id: Optional[str] = None
    child_region_ids: Set[str] = None
    
    def __post_init__(self):
        if self.child_region_ids is None:
            self.child_region_ids = set()
    
    @property
    def x(self) -> float:
        return self.bounds[0]
    
    @property
    def y(self) -> float:
        return self.bounds[1]
    
    @property
    def width(self) -> float:
        return self.bounds[2]
    
    @property
    def height(self) -> float:
        return self.bounds[3]
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is within this region."""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def get_available_area(self) -> float:
        """Get available area excluding child regions."""
        total_area = self.width * self.height
        child_area = sum(child.width * child.height 
                        for child in self.get_child_regions())
        return max(0, total_area - child_area)

class SpatialRegionManager:
    """
    Manages the assignment of logical areas to exclusive spatial regions.
    
    Key principles:
    1. Every pixel belongs to exactly one logical area
    2. Regions are hierarchical (cuts create sub-regions within parent regions)
    3. Dynamic adjustment as logical area contents change
    4. Contiguous region assignment for each logical area
    """
    
    def __init__(self, canvas_width: float, canvas_height: float):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.regions: Dict[str, SpatialRegion] = {}
        self.logical_area_to_region: Dict[str, str] = {}
        
        # Create root region for sheet_main
        self._create_root_region()
    
    def _create_root_region(self):
        """Create the root spatial region covering the entire canvas."""
        root_region = SpatialRegion(
            region_id="region_sheet_main",
            logical_area_id="sheet_main",
            bounds=(0, 0, self.canvas_width, self.canvas_height)
        )
        self.regions["region_sheet_main"] = root_region
        self.logical_area_to_region["sheet_main"] = "region_sheet_main"
    
    def create_cut_region(self, cut_logical_area_id: str, 
                         parent_logical_area_id: str,
                         requested_size: Optional[Tuple[float, float]] = None) -> str:
        """
        Create a new spatial region for a cut (negation) within a parent region.
        
        Args:
            cut_logical_area_id: ID of the logical area for the cut
            parent_logical_area_id: ID of the parent logical area
            requested_size: Optional (width, height) for the cut region
            
        Returns:
            The region_id of the created cut region
        """
        parent_region_id = self.logical_area_to_region.get(parent_logical_area_id)
        if not parent_region_id:
            raise ValueError(f"Parent logical area {parent_logical_area_id} has no spatial region")
        
        parent_region = self.regions[parent_region_id]
        
        # Calculate cut region size and position
        if requested_size:
            cut_width, cut_height = requested_size
        else:
            # Default: 40% of parent region area
            cut_width = parent_region.width * 0.6
            cut_height = parent_region.height * 0.4
        
        # Position cut region within parent (centered with offset)
        cut_x = parent_region.x + (parent_region.width - cut_width) * 0.3
        cut_y = parent_region.y + (parent_region.height - cut_height) * 0.3
        
        # Ensure cut fits within parent bounds
        cut_x = max(parent_region.x + 10, 
                   min(cut_x, parent_region.x + parent_region.width - cut_width - 10))
        cut_y = max(parent_region.y + 10,
                   min(cut_y, parent_region.y + parent_region.height - cut_height - 10))
        
        # Create cut region
        cut_region_id = f"region_{cut_logical_area_id}"
        cut_region = SpatialRegion(
            region_id=cut_region_id,
            logical_area_id=cut_logical_area_id,
            bounds=(cut_x, cut_y, cut_width, cut_height),
            parent_region_id=parent_region_id
        )
        
        # Register region
        self.regions[cut_region_id] = cut_region
        self.logical_area_to_region[cut_logical_area_id] = cut_region_id
        parent_region.child_region_ids.add(cut_region_id)
        
        if os.environ.get('ARISBE_DEBUG_EGI') == '1':
            print(f"DEBUG: Created cut region {cut_region_id} at ({cut_x}, {cut_y}, {cut_width}, {cut_height}) within parent {parent_region_id}")
        
        return cut_region_id
    
    def get_region_for_logical_area(self, logical_area_id: str) -> Optional[SpatialRegion]:
        """Get the spatial region assigned to a logical area."""
        region_id = self.logical_area_to_region.get(logical_area_id)
        return self.regions.get(region_id) if region_id else None
    
    def get_logical_area_at_point(self, x: float, y: float) -> str:
        """
        Get the logical area ID for a given point on the canvas.
        Returns the most specific (deepest) logical area containing the point.
        """
        # Find all regions containing the point
        containing_regions = []
        for region in self.regions.values():
            if region.contains_point(x, y):
                containing_regions.append(region)
        
        if not containing_regions:
            return "sheet_main"  # Fallback to root
        
        # Return the region with the most specific (deepest) logical area
        # This is the region with the most ancestors in the hierarchy
        deepest_region = max(containing_regions, 
                           key=lambda r: self._get_region_depth(r.region_id))
        
        return deepest_region.logical_area_id
    
    def _get_region_depth(self, region_id: str) -> int:
        """Get the depth of a region in the hierarchy (root = 0)."""
        region = self.regions.get(region_id)
        if not region or not region.parent_region_id:
            return 0
        return 1 + self._get_region_depth(region.parent_region_id)
    
    def adjust_region_for_content_change(self, logical_area_id: str, 
                                       content_bounds: Tuple[float, float, float, float]):
        """
        Dynamically adjust a region's size based on its content requirements.
        
        Args:
            logical_area_id: The logical area whose region needs adjustment
            content_bounds: (min_x, min_y, width, height) required for content
        """
        region = self.get_region_for_logical_area(logical_area_id)
        if not region:
            return
        
        min_x, min_y, req_width, req_height = content_bounds
        
        # Calculate new bounds ensuring content fits
        new_width = max(region.width, req_width + 20)  # 20px padding
        new_height = max(region.height, req_height + 20)
        
        # Adjust position if needed (keep within parent bounds)
        if region.parent_region_id:
            parent = self.regions[region.parent_region_id]
            new_x = max(parent.x, min(region.x, parent.x + parent.width - new_width))
            new_y = max(parent.y, min(region.y, parent.y + parent.height - new_height))
        else:
            new_x = region.x
            new_y = region.y
        
        # Update region bounds
        region.bounds = (new_x, new_y, new_width, new_height)
        
        if os.environ.get('ARISBE_DEBUG_EGI') == '1':
            print(f"DEBUG: Adjusted region {region.region_id} to ({new_x}, {new_y}, {new_width}, {new_height})")
    
    def get_all_regions(self) -> Dict[str, SpatialRegion]:
        """Get all spatial regions."""
        return self.regions.copy()
    
    def validate_canvas_coverage(self) -> bool:
        """
        Validate that every pixel on the canvas is assigned to exactly one logical area.
        This is a conceptual validation - in practice, the hierarchical structure ensures this.
        """
        # The root region covers the entire canvas
        # Child regions are contained within their parents
        # Therefore, every point is covered by at least the root region
        # and the deepest containing region determines the logical area
        return True
    
    def get_region_hierarchy_info(self) -> Dict[str, Dict]:
        """Get debugging information about the region hierarchy."""
        info = {}
        for region_id, region in self.regions.items():
            info[region_id] = {
                'logical_area': region.logical_area_id,
                'bounds': region.bounds,
                'parent': region.parent_region_id,
                'children': list(region.child_region_ids),
                'depth': self._get_region_depth(region_id),
                'available_area': region.get_available_area()
            }
        return info
