"""
Hierarchical Area System: Pixel-Perfect Logical-Spatial Correspondence

Implements strict containment hierarchy where every pixel belongs to exactly one logical area.
Handles EGIF cut nesting with proper non-overlapping layout and dynamic resizing.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainterPath, QPolygonF

from egi_core_dau import ElementID, RelationalGraphWithCuts


@dataclass
class LogicalArea:
    """Represents a logical area in the cut hierarchy."""
    area_id: ElementID
    parent: Optional['LogicalArea'] = None
    children: List['LogicalArea'] = field(default_factory=list)
    nesting_level: int = 0
    bounds: Optional[QRectF] = None
    min_size: QRectF = field(default_factory=lambda: QRectF(0, 0, 100, 100))
    elements: Set[ElementID] = field(default_factory=set)
    
    def add_child(self, child: 'LogicalArea'):
        """Add child area and update nesting level."""
        child.parent = self
        child.nesting_level = self.nesting_level + 1
        self.children.append(child)
    
    def get_all_descendants(self) -> List['LogicalArea']:
        """Get all descendant areas recursively."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def contains_point(self, point: QPointF) -> bool:
        """Check if point is within this area's bounds."""
        if not self.bounds:
            return False
        return self.bounds.contains(point)
    
    def get_deepest_area_at_point(self, point: QPointF) -> Optional['LogicalArea']:
        """Find the deepest (most nested) area containing this point."""
        if not self.contains_point(point):
            return None
        
        # Check children first (deeper areas take precedence)
        for child in self.children:
            child_result = child.get_deepest_area_at_point(point)
            if child_result:
                return child_result
        
        # If no child contains the point, this area is the deepest
        return self


class HierarchicalAreaSystem:
    """
    Manages pixel-perfect logical-spatial correspondence for EGI cut hierarchy.
    
    Ensures:
    1. Every pixel belongs to exactly one logical area
    2. Cuts never overlap
    3. Proper nesting reflects logical negation hierarchy
    4. Dynamic resizing propagates to containing cuts
    """
    
    def __init__(self):
        self.root_area: Optional[LogicalArea] = None
        self.areas: Dict[ElementID, LogicalArea] = {}
        self.canvas_bounds: QRectF = QRectF(0, 0, 800, 600)
        self.min_cut_margin: float = 20.0
        self.sibling_spacing: float = 15.0
    
    def build_hierarchy_from_egi(self, egi: RelationalGraphWithCuts) -> LogicalArea:
        """Build area hierarchy from EGI structure."""
        self.areas.clear()
        
        # Create root area (sheet of assertion)
        self.root_area = LogicalArea(
            area_id=egi.sheet,
            nesting_level=0,
            bounds=self.canvas_bounds
        )
        self.areas[egi.sheet] = self.root_area
        
        # Add elements to their areas
        for area_id, element_set in egi.area.items():
            if area_id not in self.areas:
                # Create area if it doesn't exist (for cuts)
                self.areas[area_id] = LogicalArea(area_id=area_id)
            
            # Add non-cut elements to this area
            for elem_id in element_set:
                if not any(cut.id == elem_id for cut in egi.Cut):
                    self.areas[area_id].elements.add(elem_id)
        
        # Build parent-child relationships for cuts
        self._build_cut_hierarchy(egi)
        
        # Layout cuts with proper containment
        self._layout_cut_hierarchy()
        
        return self.root_area
    
    def _build_cut_hierarchy(self, egi: RelationalGraphWithCuts):
        """Build parent-child relationships between cuts."""
        # Find which area each cut belongs to
        cut_areas = {}
        for area_id, element_set in egi.area.items():
            for elem_id in element_set:
                for cut in egi.Cut:
                    if cut.id == elem_id:
                        cut_areas[cut.id] = area_id
        
        # Create cut areas and establish hierarchy
        for cut in egi.Cut:
            if cut.id not in self.areas:
                self.areas[cut.id] = LogicalArea(area_id=cut.id)
            
            # Find parent area
            parent_area_id = cut_areas.get(cut.id, egi.sheet)
            if parent_area_id in self.areas:
                parent_area = self.areas[parent_area_id]
                parent_area.add_child(self.areas[cut.id])
    
    def _layout_cut_hierarchy(self):
        """Layout cuts with non-overlapping containment."""
        if not self.root_area:
            return
        
        # Layout from root down
        self._layout_area_and_children(self.root_area)
    
    def _layout_area_and_children(self, area: LogicalArea):
        """Layout an area and all its children recursively."""
        if not area.children:
            return
        
        # Calculate minimum size needed for children
        total_child_width = 0
        max_child_height = 0
        
        for child in area.children:
            # Recursively layout child first to get its size
            self._layout_area_and_children(child)
            
            child_size = self._calculate_minimum_size(child)
            total_child_width += child_size.width()
            max_child_height = max(max_child_height, child_size.height())
        
        # Add spacing between siblings
        if len(area.children) > 1:
            total_child_width += (len(area.children) - 1) * self.sibling_spacing
        
        # Add margins
        total_width = total_child_width + 2 * self.min_cut_margin
        total_height = max_child_height + 2 * self.min_cut_margin
        
        # Ensure area is large enough for its children
        if area.bounds:
            min_width = max(area.bounds.width(), total_width)
            min_height = max(area.bounds.height(), total_height)
            area.bounds = QRectF(
                area.bounds.x(), area.bounds.y(),
                min_width, min_height
            )
        else:
            area.bounds = QRectF(0, 0, total_width, total_height)
        
        # Position children within area
        self._position_children_in_area(area)
    
    def _calculate_minimum_size(self, area: LogicalArea) -> QRectF:
        """Calculate minimum size needed for area and its contents."""
        if not area.children and not area.elements:
            return area.min_size
        
        # Size based on children
        child_width = 0
        child_height = 0
        
        for child in area.children:
            child_size = self._calculate_minimum_size(child)
            child_width += child_size.width()
            child_height = max(child_height, child_size.height())
        
        if len(area.children) > 1:
            child_width += (len(area.children) - 1) * self.sibling_spacing
        
        # Size based on elements (rough estimate)
        element_area = len(area.elements) * 50 * 30  # Rough element size
        element_width = max(200, int((element_area ** 0.5) * 1.5))
        element_height = max(100, int(element_area / element_width))
        
        # Take maximum of child requirements and element requirements
        total_width = max(child_width, element_width) + 2 * self.min_cut_margin
        total_height = max(child_height, element_height) + 2 * self.min_cut_margin
        
        return QRectF(0, 0, total_width, total_height)
    
    def _position_children_in_area(self, area: LogicalArea):
        """Position child areas within parent area bounds."""
        if not area.children or not area.bounds:
            return
        
        # Calculate available space
        available_width = area.bounds.width() - 2 * self.min_cut_margin
        available_height = area.bounds.height() - 2 * self.min_cut_margin
        
        # Position children horizontally with spacing
        current_x = area.bounds.x() + self.min_cut_margin
        center_y = area.bounds.center().y()
        
        for child in area.children:
            if not child.bounds:
                child_size = self._calculate_minimum_size(child)
                child.bounds = QRectF(0, 0, child_size.width(), child_size.height())
            
            # Center child vertically in available space
            child_y = center_y - child.bounds.height() / 2
            
            # Position child
            child.bounds.moveTo(current_x, child_y)
            
            # Move to next position
            current_x += child.bounds.width() + self.sibling_spacing
    
    def get_area_at_point(self, point: QPointF) -> Optional[LogicalArea]:
        """Find the logical area containing the given point."""
        if not self.root_area:
            return None
        
        return self.root_area.get_deepest_area_at_point(point)
    
    def get_safe_position_in_area(self, area_id: ElementID, preferred_point: Optional[QPointF] = None) -> Optional[QPointF]:
        """Get a safe position within the specified area for placing an element."""
        if area_id not in self.areas:
            return None
        
        area = self.areas[area_id]
        if not area.bounds:
            return None
        
        # Calculate safe bounds (avoiding child cut areas)
        safe_bounds = QRectF(area.bounds)
        margin = 10.0
        safe_bounds = safe_bounds.adjusted(margin, margin, -margin, -margin)
        
        # Subtract child areas from safe bounds
        for child in area.children:
            if child.bounds and safe_bounds.intersects(child.bounds):
                # For simplicity, reduce safe area to avoid child
                # In a full implementation, this would use polygon subtraction
                if child.bounds.center().x() < safe_bounds.center().x():
                    # Child is on left, move safe area to right
                    safe_bounds.setLeft(child.bounds.right() + margin)
                else:
                    # Child is on right, move safe area to left
                    safe_bounds.setRight(child.bounds.left() - margin)
        
        # Return preferred point if it's safe, otherwise return center
        if preferred_point and safe_bounds.contains(preferred_point):
            return preferred_point
        
        if safe_bounds.width() > 0 and safe_bounds.height() > 0:
            return safe_bounds.center()
        
        return None
    
    def resize_area(self, area_id: ElementID, new_size: QRectF):
        """Resize an area and propagate changes to containing areas."""
        if area_id not in self.areas:
            return
        
        area = self.areas[area_id]
        area.bounds = new_size
        
        # Propagate resize to parent if necessary
        if area.parent:
            self._ensure_parent_contains_child(area.parent, area)
    
    def _ensure_parent_contains_child(self, parent: LogicalArea, child: LogicalArea):
        """Ensure parent area is large enough to contain child area."""
        if not parent.bounds or not child.bounds:
            return
        
        # Check if parent needs to grow
        required_left = child.bounds.left() - self.min_cut_margin
        required_right = child.bounds.right() + self.min_cut_margin
        required_top = child.bounds.top() - self.min_cut_margin
        required_bottom = child.bounds.bottom() + self.min_cut_margin
        
        new_left = min(parent.bounds.left(), required_left)
        new_top = min(parent.bounds.top(), required_top)
        new_right = max(parent.bounds.right(), required_right)
        new_bottom = max(parent.bounds.bottom(), required_bottom)
        
        if (new_left != parent.bounds.left() or new_top != parent.bounds.top() or 
            new_right != parent.bounds.right() or new_bottom != parent.bounds.bottom()):
            
            parent.bounds = QRectF(new_left, new_top, 
                                 new_right - new_left, new_bottom - new_top)
            
            # Recursively propagate to grandparent
            if parent.parent:
                self._ensure_parent_contains_child(parent.parent, parent)
    
    def get_all_areas(self) -> List[LogicalArea]:
        """Get all areas in the hierarchy."""
        return list(self.areas.values())
    
    def validate_hierarchy(self) -> List[str]:
        """Validate the hierarchy for consistency."""
        errors = []
        
        if not self.root_area:
            errors.append("No root area defined")
            return errors
        
        # Check for overlapping sibling cuts
        for area in self.areas.values():
            if len(area.children) > 1:
                for i, child1 in enumerate(area.children):
                    for child2 in area.children[i+1:]:
                        if (child1.bounds and child2.bounds and 
                            child1.bounds.intersects(child2.bounds)):
                            errors.append(f"Sibling cuts {child1.area_id} and {child2.area_id} overlap")
        
        # Check that children are contained within parents
        for area in self.areas.values():
            if area.parent and area.parent.bounds and area.bounds:
                if not area.parent.bounds.contains(area.bounds):
                    errors.append(f"Cut {area.area_id} extends outside parent {area.parent.area_id}")
        
        return errors
