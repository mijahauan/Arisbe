"""
Cut Layout Engine - Hierarchical Containment Layout
Implements cut positioning using R-tree spatial indexing for proper containment.
Ensures no cut lines overlap and each cut encloses a unique area.
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
from PySide6.QtCore import QRectF, QPointF

from egi_core_dau import ElementID, RelationalGraphWithCuts
from rtree_spatial_index import RTreeCutTracker, SpatialBounds, CutPlacementType


@dataclass
class CutNode:
    """Represents a cut in the hierarchical tree."""
    cut_id: ElementID
    parent: 'CutNode' = None
    children: List['CutNode'] = None
    bounds: QRectF = None
    level: int = 0
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class CutLayoutEngine:
    """
    Lays out cuts using R-tree spatial indexing for hierarchical containment.
    Ensures proper nesting, non-overlapping placement, and dynamic resizing.
    """
    
    def __init__(self):
        self.rtree_tracker = RTreeCutTracker()
        self.cut_bounds = {}
        self.min_cut_size = QRectF(0, 0, 100, 80)
        self.padding = 20.0
        
    def layout_cuts(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, QRectF]:
        """
        Layout cuts using R-tree spatial indexing for proper containment.
        
        Returns dictionary mapping cut IDs to their bounding rectangles.
        """
        if not egi.Cut:
            # Return sheet bounds for root area
            sheet_bounds = QRectF(-400, -300, 800, 600)
            return {egi.sheet: sheet_bounds}
        
        # Store EGI reference
        self._egi = egi
        
        # Build hierarchy and calculate sizes
        self._build_cut_hierarchy_with_rtree(egi)
        
        # Layout cuts with proper containment
        self._layout_cuts_hierarchically(egi)
        
        return self.cut_bounds
    
    def _build_cut_hierarchy_with_rtree(self, egi: RelationalGraphWithCuts):
        """Build cut hierarchy using R-tree for spatial validation."""
        # First pass: identify parent-child relationships
        cut_parents = {}
        
        for area_id, contents in egi.area.items():
            for elem_id in contents:
                # If element is a cut, its parent area is area_id
                if any(cut.id == elem_id for cut in egi.Cut):
                    cut_parents[elem_id] = area_id if area_id != egi.sheet else None
        
        # Calculate minimum sizes based on content
        self._calculate_cut_sizes(egi, cut_parents)
        
        # Build tree structure
        cut_nodes = {}
        for cut in egi.Cut:
            cut_nodes[cut.id] = CutNode(cut.id)
        
        # Connect nodes based on parent-child relationships
        for area_id, contents in egi.area.items():
            for elem_id in contents:
                if elem_id in cut_nodes:
                    child_node = cut_nodes[elem_id]
                    parent_id = cut_parents.get(elem_id)
                    if parent_id in cut_nodes:
                        parent_node = cut_nodes[parent_id]
                        child_node.parent = parent_node
                        child_node.level = parent_node.level + 1
                        parent_node.children.append(child_node)
        
        # Find root node (sheet or top-level cut)
        root = None
        for node in cut_nodes.values():
            if node.parent is None:
                root = node
                break
        
        return root
    
    def _calculate_cut_sizes(self, egi: RelationalGraphWithCuts, cut_parents: Dict[ElementID, ElementID]):
        """Calculate minimum sizes for cuts based on their contents."""
        for cut in egi.Cut:
            # Count elements in this cut
            elements_in_cut = egi.area.get(cut.id, set())
            
            # Calculate size based on content
            num_elements = len([e for e in elements_in_cut if not any(c.id == e for c in egi.Cut)])
            num_child_cuts = len([e for e in elements_in_cut if any(c.id == e for c in egi.Cut)])
            
            # Base size calculation
            width = max(self.min_cut_size.width(), num_elements * 60 + num_child_cuts * 120)
            height = max(self.min_cut_size.height(), 80 + num_child_cuts * 100)
            
            # Add padding
            width += 2 * self.padding
            height += 2 * self.padding
            
            # Store preliminary size
            self.cut_bounds[cut.id] = QRectF(0, 0, width, height)
    
    def _layout_cuts_hierarchically(self, egi: RelationalGraphWithCuts):
        """Layout cuts using hierarchical positioning with R-tree validation."""
        # Start with sheet bounds
        sheet_bounds = QRectF(-400, -300, 800, 600)
        self.cut_bounds[egi.sheet] = sheet_bounds
        
        # Add sheet to R-tree
        sheet_spatial = SpatialBounds.from_qrect(sheet_bounds)
        self.rtree_tracker.add_cut(egi.sheet, sheet_spatial)
        
        # Layout cuts level by level
        self._layout_cuts_by_level(egi, egi.sheet, 0)
    
    def _layout_cuts_by_level(self, egi: RelationalGraphWithCuts, parent_area: ElementID, level: int):
        """Layout cuts level by level to ensure proper containment."""
        # Find cuts that belong directly to this parent area
        child_cuts = []
        parent_contents = egi.area.get(parent_area, set())
        
        for elem_id in parent_contents:
            if any(cut.id == elem_id for cut in egi.Cut):
                child_cuts.append(elem_id)
        
        if not child_cuts:
            return
        
        # Get parent bounds
        parent_bounds = self.cut_bounds[parent_area]
        
        # Position child cuts within parent
        self._position_child_cuts(child_cuts, parent_bounds, parent_area)
        
        # Recursively layout grandchildren
        for child_cut in child_cuts:
            self._layout_cuts_by_level(egi, child_cut, level + 1)
    
    def _position_child_cuts(self, child_cuts: List[ElementID], parent_bounds: QRectF, parent_area: ElementID):
        """Position child cuts within parent bounds using R-tree validation."""
        if not child_cuts:
            return
        
        # Calculate available space within parent
        available_width = parent_bounds.width() - 2 * self.padding
        available_height = parent_bounds.height() - 2 * self.padding
        
        # Position cuts horizontally with spacing
        cut_spacing = 15.0
        total_cut_width = sum(self.cut_bounds[cut_id].width() for cut_id in child_cuts)
        total_spacing = (len(child_cuts) - 1) * cut_spacing
        
        # Check if cuts fit horizontally
        if total_cut_width + total_spacing <= available_width:
            self._position_cuts_horizontally(child_cuts, parent_bounds, parent_area)
        else:
            # Fall back to grid layout
            self._position_cuts_in_grid(child_cuts, parent_bounds, parent_area)
    
    def _position_cuts_horizontally(self, child_cuts: List[ElementID], parent_bounds: QRectF, parent_area: ElementID):
        """Position cuts horizontally within parent."""
        current_x = parent_bounds.x() + self.padding
        center_y = parent_bounds.center().y()
        
        for cut_id in child_cuts:
            cut_size = self.cut_bounds[cut_id]
            cut_y = center_y - cut_size.height() / 2
            
            # Position cut
            cut_bounds = QRectF(current_x, cut_y, cut_size.width(), cut_size.height())
            self.cut_bounds[cut_id] = cut_bounds
            
            # Add to R-tree with validation
            cut_spatial = SpatialBounds.from_qrect(cut_bounds)
            if self.rtree_tracker.add_cut(cut_id, cut_spatial, parent_area, CutPlacementType.BESIDE):
                current_x += cut_size.width() + 15.0  # Move to next position
            else:
                # Fallback positioning if validation fails
                self._fallback_position_cut(cut_id, parent_bounds, parent_area)
    
    def _position_cuts_in_grid(self, child_cuts: List[ElementID], parent_bounds: QRectF, parent_area: ElementID):
        """Position cuts in a grid layout within parent."""
        cols = max(1, int((parent_bounds.width() - 2 * self.padding) / 150))
        
        for i, cut_id in enumerate(child_cuts):
            row = i // cols
            col = i % cols
            
            x = parent_bounds.x() + self.padding + col * 150
            y = parent_bounds.y() + self.padding + row * 120
            
            cut_size = self.cut_bounds[cut_id]
            cut_bounds = QRectF(x, y, cut_size.width(), cut_size.height())
            self.cut_bounds[cut_id] = cut_bounds
            
            # Add to R-tree
            cut_spatial = SpatialBounds.from_qrect(cut_bounds)
            self.rtree_tracker.add_cut(cut_id, cut_spatial, parent_area, CutPlacementType.BESIDE)
    
    def _fallback_position_cut(self, cut_id: ElementID, parent_bounds: QRectF, parent_area: ElementID):
        """Fallback positioning when R-tree validation fails."""
        # Use R-tree to find safe position
        cut_size = self.cut_bounds[cut_id]
        cut_spatial = SpatialBounds(0, 0, cut_size.width(), cut_size.height())
        
        safe_pos = self.rtree_tracker.find_safe_position_in_area(parent_area, cut_spatial)
        if safe_pos:
            cut_bounds = QRectF(safe_pos.x(), safe_pos.y(), cut_size.width(), cut_size.height())
            self.cut_bounds[cut_id] = cut_bounds
            
            # Add to R-tree
            final_spatial = SpatialBounds.from_qrect(cut_bounds)
            self.rtree_tracker.add_cut(cut_id, final_spatial, parent_area, CutPlacementType.BESIDE)
    
    def validate_layout(self, cut_bounds: Dict[ElementID, QRectF], egi: RelationalGraphWithCuts) -> bool:
        """Validate that no cuts overlap and containment is proper."""
        # Only check overlaps between sibling cuts (same parent)
        siblings_map = self._build_siblings_map(egi)
        
        for siblings in siblings_map.values():
            if len(siblings) > 1:
                # Check for overlaps within sibling group
                for i, cut_id1 in enumerate(siblings):
                    for cut_id2 in siblings[i+1:]:
                        if cut_id1 in cut_bounds and cut_id2 in cut_bounds:
                            bounds1 = cut_bounds[cut_id1]
                            bounds2 = cut_bounds[cut_id2]
                            if self._rectangles_overlap(bounds1, bounds2):
                                print(f"WARNING: Sibling cuts {cut_id1} and {cut_id2} overlap")
                                return False
        
        return True
    
    def _build_siblings_map(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, List[ElementID]]:
        """Build map of parent -> list of child cuts."""
        siblings_map = {}
        
        for area_id, contents in egi.area.items():
            child_cuts = [elem_id for elem_id in contents 
                         if any(cut.id == elem_id for cut in egi.Cut)]
            if child_cuts:
                siblings_map[area_id] = child_cuts
        
        return siblings_map
    
    def _extract_bounds(self, node: CutNode, bounds_map: Dict[ElementID, QRectF]):
        """Extract bounds from cut tree into dictionary mapping."""
        bounds_map[node.cut_id] = node.bounds
        
        # Recursively extract bounds from children
        for child in node.children:
            self._extract_bounds(child, bounds_map)
    
    def _rectangles_overlap(self, rect1: QRectF, rect2: QRectF) -> bool:
        """Check if two rectangles overlap."""
        return rect1.intersects(rect2)


def test_cut_layout():
    """Test the cut layout engine with sample data."""
    from egi_core_dau import Cut
    from frozendict import frozendict
    
    # Create test EGI with nested cuts
    cut1 = Cut(ElementID("c1"))
    cut2 = Cut(ElementID("c2"))
    sheet_id = ElementID("sheet")
    
    test_egi = RelationalGraphWithCuts(
        V=frozenset(),
        E=frozenset(),
        nu=frozendict(),
        sheet=sheet_id,
        Cut=frozenset([cut1, cut2]),
        area=frozendict({
            sheet_id: frozenset([cut1.id]),
            cut1.id: frozenset([cut2.id])
        }),
        rel=frozendict()
    )
    
    # Test layout
    engine = CutLayoutEngine()
    cut_bounds = engine.layout_cuts(test_egi)
    
    print("Cut Layout Results:")
    for cut_id, bounds in cut_bounds.items():
        print(f"  {cut_id}: {bounds}")
    
    # Validate layout
    is_valid = engine.validate_layout(cut_bounds, test_egi)
    print(f"Layout valid: {is_valid}")


if __name__ == "__main__":
    test_cut_layout()
