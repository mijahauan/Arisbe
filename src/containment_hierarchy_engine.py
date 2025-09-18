"""
Phase 1: Containment Hierarchy Engine

Implements Dau Chapter 21 compliant spatial layout using Abstract Layout Units (ALU).
This is the first phase of the two-phase layout system that establishes proper
logical-spatial correspondence through bottom-up sizing and top-down positioning.

Key Principles:
- Bottom-up sizing: Calculate space requirements from leaf cuts upward
- Top-down positioning: Allocate space from parent to children with guaranteed separation
- Spatial exclusion: Sibling cuts get distinct, non-overlapping regions
- ALU system: All calculations in abstract units, view-independent
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from PySide6.QtCore import QRectF, QPointF

from egi_core_dau import RelationalGraphWithCuts, ElementID


@dataclass
class ALURect:
    """Rectangle in Abstract Layout Units."""
    x: float
    y: float
    width: float
    height: float
    
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def contains_point(self, x: float, y: float) -> bool:
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def to_qrectf(self, scale: float) -> QRectF:
        """Convert to QRectF with given scale factor."""
        return QRectF(self.x * scale, self.y * scale, 
                     self.width * scale, self.height * scale)


@dataclass
class ALUPoint:
    """Point in Abstract Layout Units."""
    x: float
    y: float
    
    def to_qpointf(self, scale: float) -> QPointF:
        """Convert to QPointF with given scale factor."""
        return QPointF(self.x * scale, self.y * scale)


@dataclass
class ContentRequirements:
    """Space requirements for elements within a cut."""
    vertices: List[ElementID]
    edges: List[ElementID]
    child_cuts: List[ElementID]
    min_width: float  # ALU
    min_height: float  # ALU


@dataclass
class ContainmentNode:
    """Node in the containment hierarchy tree."""
    area_id: ElementID
    parent: Optional['ContainmentNode']
    children: List['ContainmentNode']
    content_requirements: ContentRequirements
    allocated_bounds: Optional[ALURect]
    depth: int


class ContainmentHierarchyEngine:
    """
    Phase 1 of two-phase layout: Establishes proper containment hierarchy
    with guaranteed spatial exclusion using Abstract Layout Units.
    """
    
    def __init__(self):
        # ALU constants for element sizing
        self.VERTEX_SIZE = 0.8  # ALU diameter
        self.EDGE_HEIGHT = 1.0  # ALU height for edge text
        self.MIN_CUT_SIZE = 2.0  # ALU minimum cut dimension (size of "M")
        self.CUT_MARGIN = 1.0   # ALU margin inside cuts
        self.SIBLING_SPACING = 0.5  # ALU spacing between sibling cuts
        self.ELEMENT_SPACING = 0.3  # ALU spacing between elements
        
    def create_containment_layout(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, ALURect]:
        """
        Create containment hierarchy layout in Abstract Layout Units.
        
        Returns:
            Dictionary mapping area IDs to their ALU bounds
        """
        print("Phase 1: Creating containment hierarchy layout...")
        
        # Step 1: Build containment tree from EGI area mappings
        containment_tree = self._build_containment_tree(egi)
        
        # Step 2: Calculate content requirements (bottom-up)
        self._calculate_content_requirements(containment_tree, egi)
        
        # Step 3: Allocate space (top-down) with guaranteed separation
        self._allocate_space_top_down(containment_tree)
        
        # Step 4: Extract bounds dictionary
        bounds = self._extract_bounds(containment_tree)
        
        print(f"Phase 1 complete: {len(bounds)} areas positioned")
        return bounds
    
    def _build_containment_tree(self, egi: RelationalGraphWithCuts) -> ContainmentNode:
        """Build containment tree from EGI area mappings."""
        print("Building containment tree from EGI area mappings...")
        
        # Create nodes for all areas
        nodes = {}
        for area_id in egi.area.keys():
            nodes[area_id] = ContainmentNode(
                area_id=area_id,
                parent=None,
                children=[],
                content_requirements=None,
                allocated_bounds=None,
                depth=0
            )
        
        # Establish parent-child relationships
        for parent_area, contents in egi.area.items():
            parent_node = nodes[parent_area]
            
            for element_id in contents:
                # If element is a cut, it's a child area
                if element_id in nodes:
                    child_node = nodes[element_id]
                    child_node.parent = parent_node
                    parent_node.children.append(child_node)
        
        # Calculate depths
        root = nodes[egi.sheet]
        self._calculate_depths(root, 0)
        
        print(f"Containment tree built: {len(nodes)} nodes, root = {egi.sheet}")
        return root
    
    def _calculate_depths(self, node: ContainmentNode, depth: int):
        """Calculate depth for each node in the tree."""
        node.depth = depth
        for child in node.children:
            self._calculate_depths(child, depth + 1)
    
    def _calculate_content_requirements(self, root: ContainmentNode, egi: RelationalGraphWithCuts):
        """Calculate content requirements bottom-up."""
        print("Calculating content requirements (bottom-up)...")
        self._calculate_requirements_recursive(root, egi)
    
    def _calculate_requirements_recursive(self, node: ContainmentNode, egi: RelationalGraphWithCuts):
        """Recursively calculate content requirements."""
        # First, calculate requirements for all children
        for child in node.children:
            self._calculate_requirements_recursive(child, egi)
        
        # Get direct contents of this area
        area_contents = egi.area.get(node.area_id, set())
        
        # Separate elements by type
        vertices = []
        edges = []
        child_cuts = []
        
        for element_id in area_contents:
            if element_id in {v.id for v in egi.V}:
                vertices.append(element_id)
            elif element_id in {e.id for e in egi.E}:
                edges.append(element_id)
            elif any(child.area_id == element_id for child in node.children):
                child_cuts.append(element_id)
        
        # Calculate space requirements
        min_width, min_height = self._calculate_area_space_requirements(
            vertices, edges, node.children
        )
        
        node.content_requirements = ContentRequirements(
            vertices=vertices,
            edges=edges,
            child_cuts=child_cuts,
            min_width=min_width,
            min_height=min_height
        )
        
        print(f"Area {node.area_id}: {len(vertices)}v, {len(edges)}e, {len(child_cuts)}c "
              f"→ {min_width:.1f}×{min_height:.1f} ALU")
    
    def _calculate_area_space_requirements(self, vertices: List[ElementID], 
                                         edges: List[ElementID], 
                                         child_nodes: List[ContainmentNode]) -> Tuple[float, float]:
        """Calculate minimum space requirements for an area's contents."""
        
        # Space for direct elements
        element_width = 0.0
        element_height = 0.0
        
        if vertices:
            # Arrange vertices horizontally
            element_width += len(vertices) * self.VERTEX_SIZE
            element_width += (len(vertices) - 1) * self.ELEMENT_SPACING
            element_height = max(element_height, self.VERTEX_SIZE)
        
        if edges:
            # Arrange edges horizontally (simplified - actual text width would be measured)
            edge_width = len(edges) * 3.0  # Estimated 3 ALU per edge text
            edge_width += (len(edges) - 1) * self.ELEMENT_SPACING
            element_width = max(element_width, edge_width)
            element_height = max(element_height, self.EDGE_HEIGHT)
        
        # Space for child cuts (arranged horizontally)
        child_width = 0.0
        child_height = 0.0
        
        if child_nodes:
            for child in child_nodes:
                if child.content_requirements:
                    child_width += child.content_requirements.min_width
                    child_height = max(child_height, child.content_requirements.min_height)
            
            # Add spacing between child cuts
            child_width += (len(child_nodes) - 1) * self.SIBLING_SPACING
        
        # Total requirements: max of elements and children, plus margins
        total_width = max(element_width, child_width) + 2 * self.CUT_MARGIN
        total_height = element_height + child_height + 3 * self.CUT_MARGIN  # Space between elements and children
        
        # Ensure minimum cut size
        total_width = max(total_width, self.MIN_CUT_SIZE)
        total_height = max(total_height, self.MIN_CUT_SIZE)
        
        return total_width, total_height
    
    def _allocate_space_top_down(self, root: ContainmentNode):
        """Allocate space top-down with guaranteed separation."""
        print("Allocating space (top-down) with guaranteed separation...")
        
        # Root gets initial bounds (will be adjusted based on content)
        if root.content_requirements:
            root_width = root.content_requirements.min_width
            root_height = root.content_requirements.min_height
        else:
            root_width = 10.0  # Default ALU
            root_height = 8.0   # Default ALU
        
        root.allocated_bounds = ALURect(
            x=-root_width / 2,
            y=-root_height / 2,
            width=root_width,
            height=root_height
        )
        
        # Recursively allocate space to children
        self._allocate_children_space(root)
    
    def _allocate_children_space(self, parent: ContainmentNode):
        """Allocate space to children with guaranteed non-overlapping regions."""
        if not parent.children or not parent.allocated_bounds:
            return
        
        # Calculate available space for children
        available_bounds = ALURect(
            x=parent.allocated_bounds.x + self.CUT_MARGIN,
            y=parent.allocated_bounds.y + self.CUT_MARGIN,
            width=parent.allocated_bounds.width - 2 * self.CUT_MARGIN,
            height=parent.allocated_bounds.height - 2 * self.CUT_MARGIN
        )
        
        # Reserve space for parent's direct elements (simplified)
        element_height = 1.5  # ALU reserved for parent elements
        child_area = ALURect(
            x=available_bounds.x,
            y=available_bounds.y + element_height,
            width=available_bounds.width,
            height=available_bounds.height - element_height
        )
        
        # Arrange children horizontally with guaranteed separation
        current_x = child_area.x
        
        for i, child in enumerate(parent.children):
            if not child.content_requirements:
                continue
                
            child_width = child.content_requirements.min_width
            child_height = child.content_requirements.min_height
            
            # GUARANTEED DISTINCT POSITIONING
            child.allocated_bounds = ALURect(
                x=current_x,
                y=child_area.y + (child_area.height - child_height) / 2,
                width=child_width,
                height=child_height
            )
            
            # GUARANTEED ADVANCEMENT
            current_x += child_width + self.SIBLING_SPACING
            
            print(f"Allocated {child.area_id}: {child.allocated_bounds.x:.1f},{child.allocated_bounds.y:.1f} "
                  f"{child.allocated_bounds.width:.1f}×{child.allocated_bounds.height:.1f} ALU")
            
            # Recursively allocate to grandchildren
            self._allocate_children_space(child)
    
    def _extract_bounds(self, root: ContainmentNode) -> Dict[ElementID, ALURect]:
        """Extract bounds dictionary from containment tree."""
        bounds = {}
        self._extract_bounds_recursive(root, bounds)
        return bounds
    
    def _extract_bounds_recursive(self, node: ContainmentNode, bounds: Dict[ElementID, ALURect]):
        """Recursively extract bounds from tree."""
        if node.allocated_bounds:
            bounds[node.area_id] = node.allocated_bounds
        
        for child in node.children:
            self._extract_bounds_recursive(child, bounds)
