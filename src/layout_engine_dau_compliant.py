"""
Dau-Compliant Layout Engine for Existential Graph Instances (EGI)

This layout engine strictly adheres to Frithjof Dau's formalism for EGI visualization,
ensuring logical isomorphism between the mathematical EGI structure and its spatial representation.

Key Principles:
1. Area mapping defines containment hierarchy (container → elements)
2. Topological correctness over geometric preferences
3. Bottom-up sizing strategy from leaves to root
4. Connection-driven element placement
5. Minimal ligature crossings while preserving logic
"""

import math
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple, Any
from collections import defaultdict, deque

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from style_loader import StyleSpecification


@dataclass(frozen=True)
class Point:
    """2D point for spatial positioning"""
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass(frozen=True)
class BoundingBox:
    """Rectangular bounds for containers and elements"""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    
    @property
    def width(self) -> float:
        return self.max_x - self.min_x
    
    @property
    def height(self) -> float:
        return self.max_y - self.min_y
    
    @property
    def center(self) -> Point:
        return Point((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)
    
    def contains_point(self, point: Point, margin: float = 0) -> bool:
        return (self.min_x + margin <= point.x <= self.max_x - margin and 
                self.min_y + margin <= point.y <= self.max_y - margin)
    
    def expand(self, margin: float) -> 'BoundingBox':
        return BoundingBox(
            self.min_x - margin, self.min_y - margin,
            self.max_x + margin, self.max_y + margin
        )


@dataclass(frozen=True)
class RelativePosition:
    """Position of an element relative to its containing area"""
    element_id: ElementID
    container_id: ElementID
    local_position: Point  # Position within the container's coordinate system
    element_type: str  # 'vertex', 'edge', 'cut'


@dataclass(frozen=True)
class ContainerLayout:
    """Layout specification for a single container (cut or sheet)"""
    container_id: ElementID
    parent_container: Optional[ElementID]
    relative_bounds: BoundingBox  # Position within parent (or absolute if root)
    direct_elements: Set[ElementID]  # Elements directly in this container
    child_containers: Set[ElementID]  # Nested containers
    nesting_level: int  # Depth in containment hierarchy


@dataclass(frozen=True)
class LigaturePath:
    """Specification for drawing a ligature with topological correctness"""
    edge_id: ElementID
    vertex_ids: Tuple[ElementID, ...]  # Connected vertices in order
    path_points: Tuple[Point, ...]  # Ordered points defining the path
    boundary_crossings: Tuple[ElementID, ...]  # Which cut boundaries are crossed (in order)
    is_identity: bool = False  # Whether this represents identity relation
    
    @property
    def points(self) -> Tuple[Point, ...]:
        """Compatibility property for SVG renderer"""
        return self.path_points


@dataclass
class ConnectionConstraint:
    """Constraint representing a required connection between elements"""
    edge_id: ElementID
    vertex_id: ElementID
    edge_container: ElementID
    vertex_container: ElementID
    crosses_boundaries: Tuple[ElementID, ...]  # Boundaries that must be crossed
    min_crossings: int  # Minimum number of boundary crossings required


@dataclass
class LayoutSpecification:
    """Complete abstract layout description for GUI rendering"""
    
    # Hierarchical container structure
    containers: Dict[ElementID, ContainerLayout] = field(default_factory=dict)
    
    # Element positions within containers  
    element_positions: Dict[ElementID, RelativePosition] = field(default_factory=dict)
    
    # Ligature path specifications
    ligature_paths: List[LigaturePath] = field(default_factory=list)
    
    # Overall spatial bounds
    total_bounds: BoundingBox = field(default_factory=lambda: BoundingBox(0, 0, 400, 300))
    
    # Style hints for rendering
    style_hints: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def viewport_bounds(self) -> BoundingBox:
        """Compatibility property for SVG renderer"""
        return self.total_bounds
    
    @property
    def vertex_positions(self) -> Dict[ElementID, Point]:
        """Compatibility property - extract vertex positions"""
        return {
            pos.element_id: pos.local_position 
            for pos in self.element_positions.values() 
            if pos.element_type == 'vertex'
        }
    
    @property 
    def predicate_positions(self) -> Dict[ElementID, Point]:
        """Compatibility property - extract predicate positions"""
        return {
            pos.element_id: pos.local_position 
            for pos in self.element_positions.values() 
            if pos.element_type == 'edge'
        }
    
    @property
    def cut_bounds(self) -> Dict[ElementID, BoundingBox]:
        """Compatibility property - extract cut bounds"""
        return {
            container_id: container.relative_bounds
            for container_id, container in self.containers.items()
            if container_id != 'sheet'  # Exclude sheet from cut rendering
        }


class ContainmentHierarchyAnalyzer:
    """Analyzes EGI area mapping to build containment hierarchy"""
    
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        
    def build_containment_hierarchy(self) -> Dict[ElementID, ContainerLayout]:
        """Build containment hierarchy from EGI area mapping"""
        
        # Step 1: Identify all containers (cuts + sheet)
        all_containers = {cut.id for cut in self.egi.Cut} | {self.egi.sheet}
        
        # Step 2: Build parent-child relationships
        container_children = defaultdict(set)  # container -> set of child containers
        container_elements = {}  # container -> set of direct elements
        container_parent = {}  # container -> parent container
        
        # Process area mapping: area[container] -> elements directly in container
        for container_id, direct_elements in self.egi.area.items():
            container_elements[container_id] = set(direct_elements)
            
            # Find child containers among the direct elements
            child_containers = direct_elements & all_containers
            container_children[container_id] = child_containers
            
            # Set parent relationships
            for child_id in child_containers:
                container_parent[child_id] = container_id
        
        # Step 3: Calculate nesting levels
        nesting_levels = self._calculate_nesting_levels(container_parent)
        
        # Step 4: Build ContainerLayout objects
        containers = {}
        for container_id in all_containers:
            # Get non-container elements (vertices and edges)
            direct_elements = container_elements.get(container_id, set())
            non_container_elements = direct_elements - all_containers
            
            containers[container_id] = ContainerLayout(
                container_id=container_id,
                parent_container=container_parent.get(container_id),
                relative_bounds=BoundingBox(0, 0, 100, 100),  # Will be calculated later
                direct_elements=non_container_elements,
                child_containers=container_children[container_id],
                nesting_level=nesting_levels[container_id]
            )
        
        return containers
    
    def _calculate_nesting_levels(self, container_parent: Dict[ElementID, ElementID]) -> Dict[ElementID, int]:
        """Calculate nesting level for each container (sheet = 0)"""
        levels = {self.egi.sheet: 0}
        
        # BFS to assign levels
        queue = deque([self.egi.sheet])
        while queue:
            current = queue.popleft()
            current_level = levels[current]
            
            # Find children of current container
            for container_id, parent_id in container_parent.items():
                if parent_id == current and container_id not in levels:
                    levels[container_id] = current_level + 1
                    queue.append(container_id)
        
        return levels


class ConnectionAnalyzer:
    """Analyzes ν mapping to understand ligature requirements"""
    
    def __init__(self, egi: RelationalGraphWithCuts, containers: Dict[ElementID, ContainerLayout]):
        self.egi = egi
        self.containers = containers
        
    def analyze_connections(self) -> List[ConnectionConstraint]:
        """Analyze all connections and their boundary crossing requirements"""
        constraints = []
        
        # Process each edge and its connected vertices
        for edge_id, vertex_sequence in self.egi.nu.items():
            if not vertex_sequence:
                continue
                
            # Find which container contains this edge
            edge_container = self._find_element_container(edge_id)
            if not edge_container:
                continue
            
            # Analyze connection to each vertex
            for vertex_id in vertex_sequence:
                vertex_container = self._find_element_container(vertex_id)
                if not vertex_container:
                    continue
                
                # Calculate required boundary crossings
                crossings = self._calculate_boundary_crossings(edge_container, vertex_container)
                
                constraint = ConnectionConstraint(
                    edge_id=edge_id,
                    vertex_id=vertex_id,
                    edge_container=edge_container,
                    vertex_container=vertex_container,
                    crosses_boundaries=tuple(crossings),
                    min_crossings=len(crossings)
                )
                constraints.append(constraint)
        
        return constraints
    
    def _find_element_container(self, element_id: ElementID) -> Optional[ElementID]:
        """Find which container directly contains the given element"""
        for container_id, container in self.containers.items():
            if element_id in container.direct_elements:
                return container_id
        return None
    
    def _calculate_boundary_crossings(self, container1: ElementID, container2: ElementID) -> List[ElementID]:
        """Calculate which boundaries must be crossed to connect elements in different containers"""
        if container1 == container2:
            return []  # Same container, no crossings needed
        
        # Find path from container1 to container2 through containment hierarchy
        path1_to_root = self._path_to_root(container1)
        path2_to_root = self._path_to_root(container2)
        
        # Find lowest common ancestor
        lca = self._find_lca(path1_to_root, path2_to_root)
        
        # Boundaries to cross: from container1 up to (but not including) LCA,
        # then from LCA down to container2
        crossings = []
        
        # From container1 up to LCA
        current = container1
        while current != lca:
            parent = self.containers[current].parent_container
            if parent:
                crossings.append(current)  # Cross boundary of current container
                current = parent
            else:
                break
        
        # From LCA down to container2 (in reverse order)
        path_lca_to_container2 = []
        current = container2
        while current != lca:
            parent = self.containers[current].parent_container
            if parent:
                path_lca_to_container2.append(current)
                current = parent
            else:
                break
        
        # Add crossings in correct order
        crossings.extend(reversed(path_lca_to_container2))
        
        return crossings
    
    def _path_to_root(self, container_id: ElementID) -> List[ElementID]:
        """Get path from container to root (sheet)"""
        path = []
        current = container_id
        while current:
            path.append(current)
            current = self.containers[current].parent_container
        return path
    
    def _find_lca(self, path1: List[ElementID], path2: List[ElementID]) -> ElementID:
        """Find lowest common ancestor of two paths to root"""
        # Convert to sets for intersection
        set1 = set(path1)
        set2 = set(path2)
        
        # Find common ancestors
        common = set1 & set2
        
        # Return the one with highest nesting level (lowest in hierarchy)
        if common:
            return max(common, key=lambda c: self.containers[c].nesting_level)
        
        # Fallback to sheet
        return self.egi.sheet


class SpatialRequirementsCalculator:
    """Calculates spatial requirements using bottom-up strategy"""
    
    def __init__(self, egi: RelationalGraphWithCuts, containers: Dict[ElementID, ContainerLayout], 
                 style: StyleSpecification):
        self.egi = egi
        self.containers = containers
        self.style = style
        
    def calculate_spatial_requirements(self) -> Dict[ElementID, BoundingBox]:
        """Calculate size requirements for all containers using bottom-up approach"""
        
        # Sort containers by nesting level (deepest first)
        sorted_containers = sorted(
            self.containers.items(), 
            key=lambda item: item[1].nesting_level, 
            reverse=True
        )
        
        container_sizes = {}
        
        # Process containers from deepest to shallowest
        for container_id, container in sorted_containers:
            size = self._calculate_container_size(container_id, container, container_sizes)
            container_sizes[container_id] = size
        
        return container_sizes
    
    def _calculate_container_size(self, container_id: ElementID, container: ContainerLayout,
                                existing_sizes: Dict[ElementID, BoundingBox]) -> BoundingBox:
        """Calculate size requirements for a single container"""
        
        # Base spacing from style
        element_spacing = self.style.element_spacing
        container_padding = self.style.cut_padding
        
        # Count direct elements
        vertex_count = len([e for e in container.direct_elements if self._is_vertex(e)])
        edge_count = len([e for e in container.direct_elements if self._is_edge(e)])
        
        # Calculate space needed for direct elements
        elements_width = 0
        elements_height = 0
        
        if vertex_count + edge_count > 0:
            # Arrange in grid
            total_elements = vertex_count + edge_count
            cols = math.ceil(math.sqrt(total_elements))
            rows = math.ceil(total_elements / cols)
            
            element_width = max(self.style.predicate_char_width * 8, self.style.vertex_radius * 4)
            element_height = max(self.style.predicate_height, self.style.vertex_radius * 4)
            
            elements_width = cols * element_width + (cols - 1) * element_spacing
            elements_height = rows * element_height + (rows - 1) * element_spacing
        
        # Calculate space needed for child containers
        child_width = 0
        child_height = 0
        
        if container.child_containers:
            # Arrange child containers
            child_count = len(container.child_containers)
            child_cols = math.ceil(math.sqrt(child_count))
            child_rows = math.ceil(child_count / child_cols)
            
            # Get maximum child size
            max_child_width = 0
            max_child_height = 0
            
            for child_id in container.child_containers:
                if child_id in existing_sizes:
                    child_size = existing_sizes[child_id]
                    max_child_width = max(max_child_width, child_size.width)
                    max_child_height = max(max_child_height, child_size.height)
            
            child_width = child_cols * max_child_width + (child_cols - 1) * element_spacing
            child_height = child_rows * max_child_height + (child_rows - 1) * element_spacing
        
        # Total size is maximum of elements and children, plus padding
        total_width = max(elements_width, child_width) + 2 * container_padding
        total_height = max(elements_height, child_height) + 2 * container_padding
        
        # Minimum size
        min_size = 100
        total_width = max(total_width, min_size)
        total_height = max(total_height, min_size)
        
        return BoundingBox(0, 0, total_width, total_height)
    
    def _is_vertex(self, element_id: ElementID) -> bool:
        return any(v.id == element_id for v in self.egi.V)
    
    def _is_edge(self, element_id: ElementID) -> bool:
        return any(e.id == element_id for e in self.egi.E)


class OptimalElementPlacer:
    """Places elements optimally within containers to minimize ligature length"""
    
    def __init__(self, egi: RelationalGraphWithCuts, containers: Dict[ElementID, ContainerLayout],
                 container_sizes: Dict[ElementID, BoundingBox], 
                 connection_constraints: List[ConnectionConstraint],
                 style: StyleSpecification):
        self.egi = egi
        self.containers = containers
        self.container_sizes = container_sizes
        self.connection_constraints = connection_constraints
        self.style = style
        
    def place_elements_optimally(self) -> Dict[ElementID, RelativePosition]:
        """Place all elements optimally within their containers"""
        
        # First, position containers within their parents
        container_positions = self._position_containers()
        
        # Then, position elements within containers
        element_positions = {}
        
        for container_id, container in self.containers.items():
            if container.direct_elements:
                positions = self._place_elements_in_container(container_id, container)
                element_positions.update(positions)
        
        return element_positions
    
    def _position_containers(self) -> Dict[ElementID, BoundingBox]:
        """Position containers within their parent containers"""
        positioned = {}
        
        # Start with sheet (root)
        sheet_size = self.container_sizes[self.egi.sheet]
        positioned[self.egi.sheet] = BoundingBox(0, 0, sheet_size.width, sheet_size.height)
        
        # Process containers level by level
        for level in range(1, 10):  # Max 10 levels should be enough
            level_containers = [
                (cid, container) for cid, container in self.containers.items()
                if container.nesting_level == level and cid not in positioned
            ]
            
            if not level_containers:
                break
                
            for container_id, container in level_containers:
                parent_id = container.parent_container
                if parent_id and parent_id in positioned:
                    parent_bounds = positioned[parent_id]
                    container_size = self.container_sizes[container_id]
                    
                    # Simple positioning: center within parent with some offset
                    padding = self.style.cut_padding
                    x = parent_bounds.min_x + padding
                    y = parent_bounds.min_y + padding
                    
                    positioned[container_id] = BoundingBox(
                        x, y, x + container_size.width, y + container_size.height
                    )
        
        return positioned
    
    def _place_elements_in_container(self, container_id: ElementID, 
                                   container: ContainerLayout) -> Dict[ElementID, RelativePosition]:
        """Place elements optimally within a single container"""
        
        positions = {}
        elements = list(container.direct_elements)
        
        if not elements:
            return positions
        
        # Get container bounds
        container_bounds = self.container_sizes[container_id]
        padding = self.style.cut_padding
        
        # Available space for elements
        available_width = container_bounds.width - 2 * padding
        available_height = container_bounds.height - 2 * padding
        
        # Separate vertices and edges
        vertices = [e for e in elements if self._is_vertex(e)]
        edges = [e for e in elements if self._is_edge(e)]
        
        # Place edges first (they anchor the layout)
        edge_positions = self._place_edges_in_grid(
            edges, available_width, available_height, padding
        )
        
        # Place vertices optimally relative to connected edges
        vertex_positions = self._place_vertices_optimally(
            vertices, edge_positions, available_width, available_height, padding
        )
        
        # Combine positions
        all_positions = {**edge_positions, **vertex_positions}
        
        # Convert to RelativePosition objects
        for element_id, local_pos in all_positions.items():
            element_type = 'vertex' if self._is_vertex(element_id) else 'edge'
            positions[element_id] = RelativePosition(
                element_id=element_id,
                container_id=container_id,
                local_position=local_pos,
                element_type=element_type
            )
        
        return positions
    
    def _place_edges_in_grid(self, edges: List[ElementID], width: float, height: float, 
                           padding: float) -> Dict[ElementID, Point]:
        """Place edges in a grid layout within available space"""
        positions = {}
        
        if not edges:
            return positions
        
        # Calculate grid dimensions
        count = len(edges)
        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)
        
        # Calculate spacing
        col_spacing = width / cols if cols > 1 else 0
        row_spacing = height / rows if rows > 1 else 0
        
        # Place edges
        for i, edge_id in enumerate(edges):
            row = i // cols
            col = i % cols
            
            x = padding + col * col_spacing + col_spacing / 2
            y = padding + row * row_spacing + row_spacing / 2
            
            positions[edge_id] = Point(x, y)
        
        return positions
    
    def _place_vertices_optimally(self, vertices: List[ElementID], 
                                edge_positions: Dict[ElementID, Point],
                                width: float, height: float, padding: float) -> Dict[ElementID, Point]:
        """Place vertices optimally relative to their connected edges"""
        positions = {}
        
        for vertex_id in vertices:
            # Find connected edges in this container
            connected_edges = []
            for constraint in self.connection_constraints:
                if (constraint.vertex_id == vertex_id and 
                    constraint.edge_id in edge_positions):
                    connected_edges.append(constraint.edge_id)
            
            if connected_edges:
                # Position vertex at centroid of connected edges
                total_x = sum(edge_positions[edge_id].x for edge_id in connected_edges)
                total_y = sum(edge_positions[edge_id].y for edge_id in connected_edges)
                
                optimal_x = total_x / len(connected_edges)
                optimal_y = total_y / len(connected_edges)
                
                # Ensure position is within bounds
                optimal_x = max(padding, min(width + padding, optimal_x))
                optimal_y = max(padding, min(height + padding, optimal_y))
                
                positions[vertex_id] = Point(optimal_x, optimal_y)
            else:
                # No connected edges in this container, place at center
                positions[vertex_id] = Point(width / 2 + padding, height / 2 + padding)
        
        return positions
    
    def _is_vertex(self, element_id: ElementID) -> bool:
        return any(v.id == element_id for v in self.egi.V)
    
    def _is_edge(self, element_id: ElementID) -> bool:
        return any(e.id == element_id for e in self.egi.E)


class LigaturePathCalculator:
    """Calculates optimal ligature paths with minimal crossings"""
    
    def __init__(self, egi: RelationalGraphWithCuts, 
                 element_positions: Dict[ElementID, RelativePosition],
                 connection_constraints: List[ConnectionConstraint]):
        self.egi = egi
        self.element_positions = element_positions
        self.connection_constraints = connection_constraints
        
    def calculate_ligature_paths(self) -> List[LigaturePath]:
        """Calculate all ligature paths with topological correctness"""
        paths = []
        
        # Group constraints by edge
        edge_constraints = defaultdict(list)
        for constraint in self.connection_constraints:
            edge_constraints[constraint.edge_id].append(constraint)
        
        # Calculate path for each edge
        for edge_id, constraints in edge_constraints.items():
            vertex_ids = tuple(c.vertex_id for c in constraints)
            
            # Calculate path points
            path_points = self._calculate_path_points(edge_id, constraints)
            
            # Determine boundary crossings
            boundary_crossings = self._determine_boundary_crossings(constraints)
            
            # Check if this is an identity relation
            is_identity = self._is_identity_relation(edge_id)
            
            path = LigaturePath(
                edge_id=edge_id,
                vertex_ids=vertex_ids,
                path_points=tuple(path_points),
                boundary_crossings=tuple(boundary_crossings),
                is_identity=is_identity
            )
            paths.append(path)
        
        return paths
    
    def _calculate_path_points(self, edge_id: ElementID, 
                             constraints: List[ConnectionConstraint]) -> List[Point]:
        """Calculate the points defining the ligature path"""
        
        # Get edge position
        edge_pos = None
        for pos in self.element_positions.values():
            if pos.element_id == edge_id:
                edge_pos = pos.local_position
                break
        
        if not edge_pos:
            return []
        
        # For now, create simple straight lines to each vertex
        points = [edge_pos]
        
        for constraint in constraints:
            vertex_pos = None
            for pos in self.element_positions.values():
                if pos.element_id == constraint.vertex_id:
                    vertex_pos = pos.local_position
                    break
            
            if vertex_pos:
                points.append(vertex_pos)
        
        return points
    
    def _determine_boundary_crossings(self, constraints: List[ConnectionConstraint]) -> List[ElementID]:
        """Determine which boundaries are crossed by this ligature"""
        all_crossings = set()
        
        for constraint in constraints:
            all_crossings.update(constraint.crosses_boundaries)
        
        return list(all_crossings)
    
    def _is_identity_relation(self, edge_id: ElementID) -> bool:
        """Check if this edge represents an identity relation"""
        # Check if relation name indicates identity
        relation_name = self.egi.rel.get(edge_id, "")
        return relation_name in ["=", "identity", "id"]


class DauCompliantLayoutEngine:
    """Main layout engine that orchestrates all phases"""
    
    def __init__(self, style: StyleSpecification):
        self.style = style
        
    def compute_layout(self, egi: RelationalGraphWithCuts) -> LayoutSpecification:
        """Compute complete layout specification from EGI"""
        
        # Phase 1: Hierarchical Structure Analysis
        hierarchy_analyzer = ContainmentHierarchyAnalyzer(egi)
        containers = hierarchy_analyzer.build_containment_hierarchy()
        
        # Phase 2: Connection Analysis
        connection_analyzer = ConnectionAnalyzer(egi, containers)
        connection_constraints = connection_analyzer.analyze_connections()
        
        # Phase 3: Bottom-Up Spatial Requirements
        spatial_calculator = SpatialRequirementsCalculator(egi, containers, self.style)
        container_sizes = spatial_calculator.calculate_spatial_requirements()
        
        # Phase 4: Optimal Element Placement
        element_placer = OptimalElementPlacer(
            egi, containers, container_sizes, connection_constraints, self.style
        )
        element_positions = element_placer.place_elements_optimally()
        
        # Phase 5: Ligature Path Calculation
        ligature_calculator = LigaturePathCalculator(egi, element_positions, connection_constraints)
        ligature_paths = ligature_calculator.calculate_ligature_paths()
        
        # Update container bounds with calculated sizes
        updated_containers = {}
        for container_id, container in containers.items():
            size = container_sizes[container_id]
            updated_container = ContainerLayout(
                container_id=container.container_id,
                parent_container=container.parent_container,
                relative_bounds=size,
                direct_elements=container.direct_elements,
                child_containers=container.child_containers,
                nesting_level=container.nesting_level
            )
            updated_containers[container_id] = updated_container
        
        # Calculate total bounds
        sheet_size = container_sizes[egi.sheet]
        total_bounds = BoundingBox(0, 0, sheet_size.width, sheet_size.height)
        
        # Create style hints
        style_hints = {
            'font_family': self.style.font_family,
            'font_size': self.style.font_size,
            'vertex_radius': self.style.vertex_radius,
            'cut_shape': 'rectangle',  # Dau prefers rectangles
            'element_spacing': self.style.element_spacing,
            'cut_padding': self.style.cut_padding
        }
        
        return LayoutSpecification(
            containers=updated_containers,
            element_positions=element_positions,
            ligature_paths=ligature_paths,
            total_bounds=total_bounds,
            style_hints=style_hints
        )
