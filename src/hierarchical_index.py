"""
Hierarchical index for EGI cut nesting relationships.

This provides efficient O(1) lookup of nesting levels and containment relationships
that are fundamental to EGI logical semantics, not just spatial representation.
The hierarchical structure is core to transformation rules like IT+/IT-.
"""

from dataclasses import dataclass
from typing import Dict, Set, Optional, List
from abc import ABC, abstractmethod


@dataclass(frozen=True)
class NestingInfo:
    """Information about an area's position in the nesting hierarchy."""
    area_id: str
    nesting_level: int  # 0 = sheet, 1 = first cut area, 2 = nested cut area, etc.
    parent_area: Optional[str]  # None for sheet
    child_areas: Set[str]  # Direct children only
    
    @property
    def polarity(self) -> str:
        """Calculate polarity from nesting level."""
        return "positive" if self.nesting_level % 2 == 0 else "negative"


class HierarchicalIndex:
    """
    Efficient hierarchical index for EGI cut nesting relationships.
    
    This is integral to EGI logic for:
    - Polarity calculation (positive/negative areas)
    - Transformation rule validation (IT+/IT- nesting requirements)
    - Containment queries for logical operations
    """
    
    def __init__(self):
        self.areas: Dict[str, NestingInfo] = {}
        self.sheet_id: Optional[str] = None
        self.max_nesting_level: int = 0
    
    def add_area(self, area_id: str, parent_area: Optional[str] = None) -> bool:
        """Add an area to the hierarchical index."""
        if area_id in self.areas:
            return False
        
        # Calculate nesting level
        if parent_area is None:
            # This is the sheet
            nesting_level = 0
            self.sheet_id = area_id
        else:
            if parent_area not in self.areas:
                return False  # Parent must exist first
            parent_info = self.areas[parent_area]
            nesting_level = parent_info.nesting_level + 1
        
        # Create nesting info
        nesting_info = NestingInfo(
            area_id=area_id,
            nesting_level=nesting_level,
            parent_area=parent_area,
            child_areas=set()
        )
        
        self.areas[area_id] = nesting_info
        self.max_nesting_level = max(self.max_nesting_level, nesting_level)
        
        # Update parent's children
        if parent_area is not None:
            parent_info = self.areas[parent_area]
            # Create new NestingInfo with updated children (immutable)
            updated_children = parent_info.child_areas | {area_id}
            updated_parent = NestingInfo(
                area_id=parent_info.area_id,
                nesting_level=parent_info.nesting_level,
                parent_area=parent_info.parent_area,
                child_areas=updated_children
            )
            self.areas[parent_area] = updated_parent
        
        return True
    
    def get_nesting_level(self, area_id: str) -> Optional[int]:
        """Get the nesting level of an area. O(1) lookup."""
        info = self.areas.get(area_id)
        return info.nesting_level if info else None
    
    def get_polarity(self, area_id: str) -> Optional[str]:
        """Get the polarity of an area. O(1) lookup."""
        info = self.areas.get(area_id)
        return info.polarity if info else None
    
    def get_parent(self, area_id: str) -> Optional[str]:
        """Get the parent area of an area. O(1) lookup."""
        info = self.areas.get(area_id)
        return info.parent_area if info else None
    
    def get_children(self, area_id: str) -> Set[str]:
        """Get direct children of an area. O(1) lookup."""
        info = self.areas.get(area_id)
        return info.child_areas if info else set()
    
    def get_ancestors(self, area_id: str) -> List[str]:
        """Get all ancestors from area to sheet. Returns path from area to sheet."""
        if area_id not in self.areas:
            return []
        
        ancestors = []
        current = area_id
        
        while current is not None:
            ancestors.append(current)
            info = self.areas.get(current)
            current = info.parent_area if info else None
        
        return ancestors
    
    def is_ancestor(self, ancestor_id: str, descendant_id: str) -> bool:
        """Check if ancestor_id is an ancestor of descendant_id."""
        ancestors = self.get_ancestors(descendant_id)
        return ancestor_id in ancestors
    
    def get_areas_at_level(self, level: int) -> List[str]:
        """Get all areas at a specific nesting level."""
        return [area_id for area_id, info in self.areas.items() 
                if info.nesting_level == level]
    
    def get_positive_areas(self) -> List[str]:
        """Get all positive polarity areas."""
        return [area_id for area_id, info in self.areas.items() 
                if info.polarity == "positive"]
    
    def get_negative_areas(self) -> List[str]:
        """Get all negative polarity areas."""
        return [area_id for area_id, info in self.areas.items() 
                if info.polarity == "negative"]
    
    def remove_area(self, area_id: str) -> bool:
        """Remove an area and update parent's children."""
        if area_id not in self.areas:
            return False
        
        info = self.areas[area_id]
        
        # Update parent's children
        if info.parent_area is not None:
            parent_info = self.areas[info.parent_area]
            updated_children = parent_info.child_areas - {area_id}
            updated_parent = NestingInfo(
                area_id=parent_info.area_id,
                nesting_level=parent_info.nesting_level,
                parent_area=parent_info.parent_area,
                child_areas=updated_children
            )
            self.areas[info.parent_area] = updated_parent
        
        # Remove the area
        del self.areas[area_id]
        
        # Update max nesting level if needed
        if info.nesting_level == self.max_nesting_level:
            self.max_nesting_level = max(
                (info.nesting_level for info in self.areas.values()), 
                default=0
            )
        
        return True
    
    def validate_containment(self, container_id: str, contained_id: str) -> bool:
        """Validate that container can contain the contained area."""
        if container_id not in self.areas or contained_id not in self.areas:
            return False
        
        container_info = self.areas[container_id]
        contained_info = self.areas[contained_id]
        
        # Container must be at a lower nesting level
        return container_info.nesting_level < contained_info.nesting_level
    
    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about the hierarchical index."""
        return {
            'total_areas': len(self.areas),
            'max_nesting_level': self.max_nesting_level,
            'positive_areas': len(self.get_positive_areas()),
            'negative_areas': len(self.get_negative_areas()),
            'sheet_id': self.sheet_id
        }
