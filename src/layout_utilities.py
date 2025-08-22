#!/usr/bin/env python3
"""
Layout Utilities - Reusable Components for EG Layout Pipeline

Extracted from inside_out_layout_engine.py to provide modular, reusable
components that can be used by different phases of the layout pipeline.
Each utility has clear dependencies and can be used independently.
"""

from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
import math

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from layout_types import LayoutElement, Bounds, Coordinate


@dataclass
class ElementDimensions:
    """Dimensions and clearance requirements for an element."""
    width: float
    height: float
    clearance_width: float
    clearance_height: float
    
    @property
    def total_width(self) -> float:
        return self.width + self.clearance_width
    
    @property
    def total_height(self) -> float:
        return self.height + self.clearance_height


@dataclass
class ContainerInfo:
    """Information about a logical container (cut or sheet)."""
    container_id: str
    parent_id: Optional[str]
    children_ids: Set[str]  # Direct child containers
    element_ids: Set[str]   # Direct child elements (vertices, predicates)
    bounds: Optional[Bounds] = None  # Calculated inside-out
    depth: int = 0  # Nesting depth (0 = sheet)


class ElementMeasurement:
    """Utility for measuring elements and calculating their space requirements."""
    
    def __init__(self, 
                 vertex_name_clearance: float = 25.0,
                 predicate_hook_clearance: float = 15.0):
        self.vertex_name_clearance = vertex_name_clearance
        self.predicate_hook_clearance = predicate_hook_clearance
        self.char_width = 8.0  # Approximate character width
        self.char_height = 12.0  # Approximate character height
        self.vertex_radius = 8.0  # Default vertex radius
    
    def measure_vertex(self, vertex: Vertex, egi: RelationalGraphWithCuts) -> ElementDimensions:
        """Calculate dimensions for a vertex including name clearance."""
        vertex_name = egi.rel.get(vertex.id, "")
        
        # Base vertex dimensions
        base_width = self.vertex_radius * 2
        base_height = self.vertex_radius * 2
        
        # Name dimensions if present
        name_width = len(vertex_name) * self.char_width if vertex_name else 0
        name_height = self.char_height if vertex_name else 0
        
        # Total dimensions including clearance
        total_width = max(base_width, name_width) + self.vertex_name_clearance
        total_height = base_height + name_height + self.vertex_name_clearance
        
        return ElementDimensions(
            width=max(base_width, name_width),
            height=base_height + name_height,
            clearance_width=self.vertex_name_clearance,
            clearance_height=self.vertex_name_clearance
        )
    
    def measure_predicate(self, edge: Edge, egi: RelationalGraphWithCuts) -> ElementDimensions:
        """Calculate dimensions for a predicate including hook clearance."""
        predicate_text = egi.rel.get(edge.id, "P")
        
        # Text dimensions
        text_width = len(predicate_text) * self.char_width
        text_height = self.char_height
        
        # Total dimensions including hook clearance
        total_width = text_width + (self.predicate_hook_clearance * 2)
        total_height = text_height + self.predicate_hook_clearance
        
        return ElementDimensions(
            width=text_width,
            height=text_height,
            clearance_width=self.predicate_hook_clearance * 2,
            clearance_height=self.predicate_hook_clearance
        )
    
    def measure_all_elements(self, egi: RelationalGraphWithCuts) -> Dict[str, ElementDimensions]:
        """Measure all elements in the EGI and return their dimensions."""
        dimensions = {}
        
        # Measure vertices
        for vertex in egi.V:
            dimensions[vertex.id] = self.measure_vertex(vertex, egi)
        
        # Measure predicates (edges that are not lines of identity)
        for edge in egi.E:
            if egi.rel.get(edge.id) != "=":  # Not a line of identity
                dimensions[edge.id] = self.measure_predicate(edge, egi)
        
        return dimensions


class CollisionDetection:
    """Utility for collision detection and collision-free placement."""
    
    def __init__(self, element_spacing: float = 40.0):
        self.element_spacing = element_spacing
    
    def bounds_overlap(self, bounds1: Bounds, bounds2: Bounds) -> bool:
        """Check if two bounding rectangles overlap."""
        x1_min, y1_min, x1_max, y1_max = bounds1
        x2_min, y2_min, x2_max, y2_max = bounds2
        
        # No overlap if one is completely to the left, right, above, or below the other
        if (x1_max <= x2_min or x2_max <= x1_min or 
            y1_max <= y2_min or y2_max <= y1_min):
            return False
        
        return True
    
    def find_collision_free_position(self, 
                                   container_bounds: Bounds,
                                   existing_elements: List[LayoutElement],
                                   element_dimensions: ElementDimensions,
                                   padding: float = 30.0) -> Coordinate:
        """Find a collision-free position within the container for an element."""
        
        # Starting position with padding from container edge
        container_x, container_y, container_width, container_height = container_bounds
        start_x = container_x + padding
        start_y = container_y + padding
        
        # Available space within container
        available_width = container_width - (2 * padding)
        available_height = container_height - (2 * padding)
        
        # Try positions in a grid pattern until we find one without collision
        max_attempts = 100
        attempt = 0
        
        while attempt < max_attempts:
            # Calculate grid position
            cols = max(1, int(available_width // (element_dimensions.total_width + self.element_spacing)))
            if cols == 0:
                cols = 1
            
            row = attempt // cols
            col = attempt % cols
            
            x = start_x + col * (element_dimensions.total_width + self.element_spacing)
            y = start_y + row * (element_dimensions.total_height + self.element_spacing)
            
            # Check if position is within container bounds
            if (x + element_dimensions.total_width > container_x + container_width - padding or
                y + element_dimensions.total_height > container_y + container_height - padding):
                attempt += 1
                continue
            
            # Check for collisions with existing elements
            proposed_bounds = (
                x - element_dimensions.total_width // 2,
                y - element_dimensions.total_height // 2,
                x + element_dimensions.total_width // 2,
                y + element_dimensions.total_height // 2
            )
            
            collision = False
            for existing_element in existing_elements:
                if self.bounds_overlap(proposed_bounds, existing_element.bounds):
                    collision = True
                    break
            
            if not collision:
                return (x, y)
            
            attempt += 1
        
        # Fallback: use grid position with guaranteed spacing
        cols = max(1, int(available_width // (element_dimensions.total_width + self.element_spacing)))
        row = len(existing_elements) // cols
        col = len(existing_elements) % cols
        x = start_x + col * (element_dimensions.total_width + self.element_spacing)
        y = start_y + row * (element_dimensions.total_height + self.element_spacing)
        
        return (x, y)


class ContainerHierarchy:
    """Utility for extracting and managing EGI containment hierarchy."""
    
    def extract_containment_hierarchy(self, egi: RelationalGraphWithCuts) -> Dict[str, ContainerInfo]:
        """Extract containment hierarchy directly from EGI."""
        containers = {}
        
        # Create sheet container using actual sheet ID from EGI
        sheet_id = egi.sheet
        sheet = ContainerInfo(
            container_id=sheet_id,
            parent_id=None,
            children_ids=set(),
            element_ids=set(),
            depth=0
        )
        containers[sheet_id] = sheet
        
        # Create cut containers (first pass - just create them)
        for cut in egi.Cut:  # Capital C - it's the set of cuts
            # Find parent by checking area mapping
            parent_id = sheet_id  # Default to sheet
            for context_id, area_contents in egi.area.items():
                if cut.id in area_contents:
                    parent_id = context_id
                    break
            
            cut_container = ContainerInfo(
                container_id=cut.id,
                parent_id=parent_id,
                children_ids=set(),
                element_ids=set()
            )
            containers[cut.id] = cut_container
        
        # Second pass - establish parent-child relationships and calculate depths
        for cut_id, cut_container in containers.items():
            if cut_id == sheet_id:
                continue  # Skip sheet
            
            parent_id = cut_container.parent_id
            if parent_id in containers:
                parent = containers[parent_id]
                parent.children_ids.add(cut_id)
                # Set depth based on parent depth
                cut_container.depth = parent.depth + 1
        
        # Assign vertices to containers using area mapping
        for vertex in egi.V:  # Capital V - it's the set of vertices
            container_id = self._get_element_container(vertex.id, egi, sheet_id)
            if container_id in containers:
                containers[container_id].element_ids.add(vertex.id)
        
        # Assign predicates to containers using area mapping
        for edge in egi.E:  # Capital E - it's the set of edges
            if egi.rel.get(edge.id) != "=":  # Not a line of identity
                container_id = self._get_element_container(edge.id, egi, sheet_id)
                if container_id in containers:
                    containers[container_id].element_ids.add(edge.id)
        
        return containers
    
    def _get_element_container(self, element_id: str, egi: RelationalGraphWithCuts, sheet_id: str) -> str:
        """Find which container (cut or sheet) contains the given element."""
        # Check area mapping to find container
        for context_id, area_contents in egi.area.items():
            if element_id in area_contents:
                return context_id
        
        # Default to sheet if not found in any area
        return sheet_id
    
    def get_container_processing_order(self, containers: Dict[str, ContainerInfo]) -> List[str]:
        """Get containers in processing order (children before parents)."""
        order = []
        visited = set()
        
        def visit(container_id: str):
            if container_id in visited:
                return
            visited.add(container_id)
            
            # Visit children first
            container = containers[container_id]
            for child_id in container.children_ids:
                visit(child_id)
            
            # Then visit this container
            order.append(container_id)
        
        # Start from sheet (root) - find the sheet by looking for container with no parent
        sheet_id = None
        for container_id, container in containers.items():
            if container.parent_id is None:
                sheet_id = container_id
                break
        
        if sheet_id:
            visit(sheet_id)
        return order


class HookPositioning:
    """Utility for calculating hook positions on predicate boundaries."""
    
    def get_hook_position(self, 
                         element: LayoutElement, 
                         target_element: LayoutElement) -> Coordinate:
        """Calculate hook position on element boundary using cardinal points."""
        
        # For vertices, use center position
        if element.element_type == 'vertex':
            return element.position
        
        # For predicates, calculate hook position on boundary
        if element.element_type == 'predicate':
            predicate_bounds = element.bounds
            predicate_center = element.position
            target_pos = target_element.position
            
            # Calculate relative direction to target
            dx = target_pos[0] - predicate_center[0]
            dy = target_pos[1] - predicate_center[1]
            
            # Choose cardinal point based on dominant direction
            if abs(dx) > abs(dy):
                if dx > 0:  # Target is to the right, use East hook
                    return (predicate_bounds[2], predicate_center[1])
                else:  # Target is to the left, use West hook
                    return (predicate_bounds[0], predicate_center[1])
            else:
                if dy > 0:  # Target is below, use South hook
                    return (predicate_center[0], predicate_bounds[3])
                else:  # Target is above, use North hook
                    return (predicate_center[0], predicate_bounds[1])
        
        return element.position
    
    def assign_cardinal_hooks(self, 
                            predicate_element: LayoutElement,
                            connected_vertices: List[LayoutElement]) -> Dict[str, Coordinate]:
        """Assign cardinal point hooks to connected vertices based on their positions."""
        hooks = {}
        predicate_center = predicate_element.position
        predicate_bounds = predicate_element.bounds
        
        # Sort vertices by angle from predicate center
        vertex_angles = []
        for vertex in connected_vertices:
            dx = vertex.position[0] - predicate_center[0]
            dy = vertex.position[1] - predicate_center[1]
            angle = math.atan2(dy, dx)
            vertex_angles.append((vertex.element_id, angle))
        
        # Sort by angle to get consistent ordering
        vertex_angles.sort(key=lambda x: x[1])
        
        # Assign to cardinal points in order
        if predicate_bounds is None:
            # Fallback to position-based hooks if no bounds
            cardinal_points = [
                ('E', (predicate_center[0] + 25, predicate_center[1])),  # East
                ('S', (predicate_center[0], predicate_center[1] + 25)),  # South
                ('W', (predicate_center[0] - 25, predicate_center[1])),  # West
                ('N', (predicate_center[0], predicate_center[1] - 25))   # North
            ]
        else:
            cardinal_points = [
                ('E', (predicate_bounds.right, predicate_center[1])),  # East
                ('S', (predicate_center[0], predicate_bounds.bottom)),  # South
                ('W', (predicate_bounds.left, predicate_center[1])),  # West
                ('N', (predicate_center[0], predicate_bounds.top))   # North
            ]
        
        for i, (vertex_id, _) in enumerate(vertex_angles):
            cardinal_idx = i % len(cardinal_points)
            direction, position = cardinal_points[cardinal_idx]
            hooks[vertex_id] = position
        
        return hooks


class ContainerSizing:
    """Utility for inside-out container sizing based on content."""
    
    def __init__(self, cut_padding: float = 30.0, min_container_size: float = 100.0):
        self.cut_padding = cut_padding
        self.min_container_size = min_container_size
    
    def calculate_container_size(self, 
                               container: ContainerInfo,
                               elements: Dict[str, LayoutElement],
                               child_containers: Dict[str, ContainerInfo]) -> Tuple[float, float]:
        """Calculate size needed for container based on its contents."""
        
        if container.parent_id is None:
            # Sheet container - use fixed canvas size for now
            return (800.0, 600.0)
        
        # Calculate bounding box of all contained elements and child containers
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        
        # Include direct elements
        for element_id in container.element_ids:
            if element_id in elements:
                element = elements[element_id]
                min_x = min(min_x, element.bounds[0])
                min_y = min(min_y, element.bounds[1])
                max_x = max(max_x, element.bounds[2])
                max_y = max(max_y, element.bounds[3])
        
        # Include child containers
        for child_id in container.children_ids:
            if child_id in child_containers and child_containers[child_id].bounds:
                child_bounds = child_containers[child_id].bounds
                min_x = min(min_x, child_bounds[0])
                min_y = min(min_y, child_bounds[1])
                max_x = max(max_x, child_bounds[2])
                max_y = max(max_y, child_bounds[3])
        
        # Calculate content size with padding
        if min_x != float('inf'):  # Has contents
            content_width = max_x - min_x + 2 * self.cut_padding
            content_height = max_y - min_y + 2 * self.cut_padding
            
            # Ensure minimum size based on content density
            element_count = len(container.element_ids) + len(container.children_ids)
            min_width = max(self.min_container_size, element_count * 60)
            min_height = max(self.min_container_size * 0.7, element_count * 40)
            
            content_width = max(content_width, min_width)
            content_height = max(content_height, min_height)
        else:  # Empty container - size based on depth level
            # Deeper cuts are smaller, shallower cuts are larger
            base_size = max(self.min_container_size - container.depth * 20, 60)
            content_width = base_size
            content_height = base_size * 0.7
        
        return (content_width, content_height)


if __name__ == "__main__":
    # Test the utilities
    print("🧪 Testing Layout Utilities")
    
    from egif_parser_dau import EGIFParser
    
    # Test with simple EGIF
    egif = "*x (Human x) ~[ (Mortal x) ]"
    parser = EGIFParser(egif)
    egi = parser.parse()
    
    # Test element measurement
    measurer = ElementMeasurement()
    dimensions = measurer.measure_all_elements(egi)
    print(f"📏 Measured {len(dimensions)} elements:")
    for element_id, dims in dimensions.items():
        print(f"   {element_id}: {dims.total_width}x{dims.total_height}")
    
    # Test container hierarchy
    hierarchy = ContainerHierarchy()
    containers = hierarchy.extract_containment_hierarchy(egi)
    print(f"📦 Found {len(containers)} containers:")
    for container_id, container in containers.items():
        print(f"   {container_id} (depth {container.depth}): {len(container.element_ids)} elements")
    
    print("✅ Layout Utilities Test Complete")
