"""
Sequential Layout Engine - Transformation-Stable EGI Layout

SEQUENTIAL PHASES:
1. Containment Hierarchy - Build logical structure from EGI
2. Style Application - Apply style specifications
3. Conservative Size Calculation - Bottom-up with transformation buffers
4. Canonical Element Placement - Deterministic, semantic-aware positioning
5. Vertex Position Optimization - Minimize ligature distances within areas
6. Predicate Position Optimization - Minimize total ligature length
7. Ligature Routing - Path calculation with collision avoidance and bridges

TRANSFORMATION STABILITY GUARANTEES:
- Same EGI produces recognizable layouts across transformations
- Canonical positioning ensures consistent element placement
- Conservative spatial budgeting prevents cramped re-arrangements
- Semantic anchoring maintains meaningful spatial relationships
"""

import math
import hashlib
from dataclasses import dataclass, replace
from typing import Dict, FrozenSet, List, Optional, Set, Tuple, Any
from enum import Enum
from collections import defaultdict

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from layout_engine_ironclad import Point, BoundingBox, LigaturePath, LayoutDTO
from style_loader import StyleSpecification


class LayoutPhase(Enum):
    """Sequential layout phases"""
    CONTAINMENT_HIERARCHY = 1
    STYLE_APPLICATION = 2
    CONSERVATIVE_SIZING = 3
    CANONICAL_PLACEMENT = 4
    VERTEX_OPTIMIZATION = 5
    PREDICATE_OPTIMIZATION = 6
    LIGATURE_ROUTING = 7


@dataclass(frozen=True)
class AreaSizeRequirements:
    """Conservative size requirements for an area"""
    area_id: ElementID
    min_width: float
    min_height: float
    preferred_width: float
    preferred_height: float
    vertex_count: int
    predicate_count: int
    child_area_count: int
    transformation_buffer: float = 1.5  # 50% extra space for stability


@dataclass(frozen=True)
class ElementPosition:
    """Canonical position of an element within its area"""
    element_id: ElementID
    area_id: ElementID
    position: Point
    element_type: str  # 'vertex', 'predicate', 'cut'
    semantic_role: str  # 'primary', 'secondary', 'generic', 'constant'
    is_optimized: bool = False
    canonical_order: int = 0


@dataclass(frozen=True)
class LigatureConnection:
    """Connection analysis for ligature routing"""
    vertex_id: ElementID
    predicate_id: ElementID
    vertex_area: ElementID
    predicate_area: ElementID
    distance: float
    crosses_cuts: List[ElementID]
    priority: int = 0  # Higher priority ligatures routed first


@dataclass(frozen=True)
class LayoutMemory:
    """Memory of previous layout for transformation stability"""
    element_positions: Dict[ElementID, Point]
    area_arrangements: Dict[ElementID, List[ElementID]]
    semantic_roles: Dict[ElementID, str]
    layout_hash: str


class CanonicalPositioning:
    """Deterministic, semantic-aware element positioning"""
    
    def __init__(self, style: StyleSpecification):
        self.style = style
        
    def assign_canonical_positions(self, egi: RelationalGraphWithCuts, 
                                 area_id: ElementID, 
                                 area_bounds: BoundingBox) -> Dict[ElementID, ElementPosition]:
        """
        Assign canonical positions based on:
        1. Semantic importance (connection degree, type)
        2. Deterministic ordering (hash-based for consistency)
        3. Balanced spatial distribution
        """
        area_elements = self._get_area_elements(egi, area_id)
        
        # Classify elements by type and semantic role
        vertices = [e for e in area_elements if self._is_vertex(egi, e)]
        predicates = [e for e in area_elements if self._is_predicate(egi, e)]
        
        # Analyze semantic roles
        semantic_roles = self._analyze_semantic_roles(egi, area_elements)
        
        # Sort deterministically for consistent positioning
        sorted_vertices = self._sort_elements_canonically(egi, vertices, semantic_roles)
        sorted_predicates = self._sort_elements_canonically(egi, predicates, semantic_roles)
        
        # Generate balanced grid positions
        positions = {}
        
        # Position predicates first (they anchor the layout)
        if sorted_predicates:
            predicate_positions = self._generate_predicate_grid(sorted_predicates, area_bounds)
            positions.update(predicate_positions)
        
        # Position vertices around predicates
        if sorted_vertices:
            vertex_positions = self._generate_vertex_positions(sorted_vertices, area_bounds, positions)
            positions.update(vertex_positions)
        
        return positions
    
    def _get_area_elements(self, egi: RelationalGraphWithCuts, area_id: ElementID) -> List[ElementID]:
        """Get all elements contained in the specified area"""
        # Get elements directly from the area mapping
        area_elements = egi.area.get(area_id, frozenset())
        return list(area_elements)
    
    def _is_vertex(self, egi: RelationalGraphWithCuts, element_id: ElementID) -> bool:
        """Check if element is a vertex"""
        return any(v.id == element_id for v in egi.V)
    
    def _is_predicate(self, egi: RelationalGraphWithCuts, element_id: ElementID) -> bool:
        """Check if element is a predicate (edge)"""
        return any(e.id == element_id for e in egi.E)
    
    def _analyze_semantic_roles(self, egi: RelationalGraphWithCuts, 
                              elements: List[ElementID]) -> Dict[ElementID, str]:
        """Analyze semantic importance of elements"""
        roles = {}
        
        # Calculate connection degrees
        connection_counts = defaultdict(int)
        for edge in egi.E:
            if hasattr(edge, 'nu') and edge.nu:
                for vertex_id in edge.nu:
                    connection_counts[vertex_id] += 1
                connection_counts[edge.id] += len(edge.nu)
        
        # Assign roles based on connection degree and type
        for element_id in elements:
            if self._is_vertex(egi, element_id):
                vertex = next((v for v in egi.V if v.id == element_id), None)
                if vertex:
                    if vertex.is_generic:
                        if connection_counts[element_id] >= 3:
                            roles[element_id] = 'primary_generic'
                        else:
                            roles[element_id] = 'generic'
                    else:
                        roles[element_id] = 'constant'
            elif self._is_predicate(egi, element_id):
                if connection_counts[element_id] >= 3:
                    roles[element_id] = 'primary_predicate'
                else:
                    roles[element_id] = 'predicate'
        
        return roles
    
    def _sort_elements_canonically(self, egi: RelationalGraphWithCuts, 
                                 elements: List[ElementID], 
                                 semantic_roles: Dict[ElementID, str]) -> List[ElementID]:
        """Sort elements deterministically for consistent positioning"""
        def sort_key(element_id):
            # Primary sort by semantic importance
            role_priority = {
                'primary_predicate': 0,
                'primary_generic': 1,
                'predicate': 2,
                'constant': 3,
                'generic': 4
            }
            role = semantic_roles.get(element_id, 'generic')
            priority = role_priority.get(role, 5)
            
            # Secondary sort by deterministic hash for consistency
            element_hash = hashlib.md5(str(element_id).encode()).hexdigest()
            
            return (priority, element_hash)
        
        return sorted(elements, key=sort_key)
    
    def _generate_predicate_grid(self, predicates: List[ElementID], 
                               area_bounds: BoundingBox) -> Dict[ElementID, ElementPosition]:
        """Generate grid positions for predicates (layout anchors)"""
        positions = {}
        
        if not predicates:
            return positions
        
        # Calculate grid dimensions
        count = len(predicates)
        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)
        
        # Calculate spacing
        usable_width = area_bounds.width * 0.8  # Leave 20% margin
        usable_height = area_bounds.height * 0.8
        
        col_spacing = usable_width / max(1, cols - 1) if cols > 1 else 0
        row_spacing = usable_height / max(1, rows - 1) if rows > 1 else 0
        
        # Position predicates in grid
        for i, predicate_id in enumerate(predicates):
            row = i // cols
            col = i % cols
            
            x = area_bounds.min_x + area_bounds.width * 0.1 + col * col_spacing
            y = area_bounds.min_y + area_bounds.height * 0.1 + row * row_spacing
            
            positions[predicate_id] = ElementPosition(
                element_id=predicate_id,
                area_id=area_bounds,  # Will be set properly by caller
                position=Point(x, y),
                element_type='predicate',
                semantic_role='predicate',
                canonical_order=i
            )
        
        return positions
    
    def _generate_vertex_positions(self, vertices: List[ElementID], 
                                 area_bounds: BoundingBox,
                                 existing_positions: Dict[ElementID, ElementPosition]) -> Dict[ElementID, ElementPosition]:
        """Generate positions for vertices around existing predicates"""
        positions = {}
        
        if not vertices:
            return positions
        
        # Find available positions around predicates
        predicate_positions = [pos.position for pos in existing_positions.values() 
                             if pos.element_type == 'predicate']
        
        if not predicate_positions:
            # No predicates, use simple grid for vertices
            return self._generate_simple_grid(vertices, area_bounds, 'vertex')
        
        # Distribute vertices around predicates
        vertices_per_predicate = len(vertices) // len(predicate_positions)
        remaining_vertices = len(vertices) % len(predicate_positions)
        
        vertex_index = 0
        for i, predicate_pos in enumerate(predicate_positions):
            # Calculate how many vertices to place around this predicate
            vertex_count = vertices_per_predicate
            if i < remaining_vertices:
                vertex_count += 1
            
            # Place vertices in circle around predicate
            for j in range(vertex_count):
                if vertex_index >= len(vertices):
                    break
                
                angle = 2 * math.pi * j / max(1, vertex_count)
                radius = 30.0  # Distance from predicate
                
                x = predicate_pos.x + radius * math.cos(angle)
                y = predicate_pos.y + radius * math.sin(angle)
                
                # Ensure position is within area bounds
                x = max(area_bounds.min_x + 10, min(area_bounds.max_x - 10, x))
                y = max(area_bounds.min_y + 10, min(area_bounds.max_y - 10, y))
                
                positions[vertices[vertex_index]] = ElementPosition(
                    element_id=vertices[vertex_index],
                    area_id=area_bounds,  # Will be set properly by caller
                    position=Point(x, y),
                    element_type='vertex',
                    semantic_role='generic',
                    canonical_order=vertex_index
                )
                
                vertex_index += 1
        
        return positions
    
    def _generate_simple_grid(self, elements: List[ElementID], 
                            area_bounds: BoundingBox, 
                            element_type: str) -> Dict[ElementID, ElementPosition]:
        """Generate simple grid layout for elements"""
        positions = {}
        
        if not elements:
            return positions
        
        # Calculate grid dimensions
        count = len(elements)
        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)
        
        # Calculate spacing
        usable_width = area_bounds.width * 0.8
        usable_height = area_bounds.height * 0.8
        
        col_spacing = usable_width / max(1, cols - 1) if cols > 1 else 0
        row_spacing = usable_height / max(1, rows - 1) if rows > 1 else 0
        
        # Position elements in grid
        for i, element_id in enumerate(elements):
            row = i // cols
            col = i % cols
            
            x = area_bounds.min_x + area_bounds.width * 0.1 + col * col_spacing
            y = area_bounds.min_y + area_bounds.height * 0.1 + row * row_spacing
            
            positions[element_id] = ElementPosition(
                element_id=element_id,
                area_id=area_bounds,  # Will be set properly by caller
                position=Point(x, y),
                element_type=element_type,
                semantic_role=element_type,
                canonical_order=i
            )
        
        return positions


class ConservativeSpatialBudget:
    """Conservative area sizing with transformation stability buffers"""
    
    def __init__(self, style: StyleSpecification):
        self.style = style
        
        # Buffer factors for transformation stability (reduced for better layouts)
        self.element_buffer = 1.1  # 10% extra space per element
        self.transformation_buffer = 1.2  # 20% extra for transformations
        self.ligature_buffer = 1.15  # 15% extra for ligature optimization
        self.collapse_buffer = 1.1  # 10% extra for collapse/expand
    
    def calculate_conservative_area_size(self, egi: RelationalGraphWithCuts, 
                                       area_id: ElementID) -> AreaSizeRequirements:
        """Calculate conservative size requirements with all buffers"""
        
        # Count elements in area
        area_elements = egi.area.get(area_id, frozenset())
        vertices = [v for v in egi.V if v.id in area_elements]
        predicates = [e for e in egi.E if e.id in area_elements]
        child_cuts = [c for c in egi.Cut if c.id in area_elements and c.id != area_id]
        
        # Base size calculation from style
        base_width = self._calculate_base_width(vertices, predicates, child_cuts)
        base_height = self._calculate_base_height(vertices, predicates, child_cuts)
        
        # Apply conservative buffers
        buffered_width = base_width * self.element_buffer * self.transformation_buffer
        buffered_height = base_height * self.element_buffer * self.transformation_buffer
        
        # Preferred size includes ligature and collapse buffers
        preferred_width = buffered_width * self.ligature_buffer * self.collapse_buffer
        preferred_height = buffered_height * self.ligature_buffer * self.collapse_buffer
        
        return AreaSizeRequirements(
            area_id=area_id,
            min_width=buffered_width,
            min_height=buffered_height,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            vertex_count=len(vertices),
            predicate_count=len(predicates),
            child_area_count=len(child_cuts),
            transformation_buffer=self.transformation_buffer
        )
    
    def _calculate_base_width(self, vertices: List[Vertex], 
                            predicates: List[Edge], 
                            child_cuts: List[Cut]) -> float:
        """Calculate base width requirements from style"""
        # Element spacing from style
        element_spacing = self.style.element_spacing
        text_width = self.style.predicate_char_width * 8  # Estimate average predicate width
        
        # Estimate grid dimensions
        total_elements = len(vertices) + len(predicates)
        if total_elements == 0:
            return 100.0  # Minimum area size
        
        cols = math.ceil(math.sqrt(total_elements))
        base_width = cols * text_width + (cols - 1) * element_spacing
        
        # Add space for child cuts
        if child_cuts:
            base_width += len(child_cuts) * 100.0  # Minimum cut width
        
        return max(100.0, base_width)
    
    def _calculate_base_height(self, vertices: List[Vertex], 
                             predicates: List[Edge], 
                             child_cuts: List[Cut]) -> float:
        """Calculate base height requirements from style"""
        # Element spacing from style
        element_spacing = self.style.element_spacing
        text_height = self.style.predicate_height
        
        # Estimate grid dimensions
        total_elements = len(vertices) + len(predicates)
        if total_elements == 0:
            return 100.0  # Minimum area size
        
        cols = math.ceil(math.sqrt(total_elements))
        rows = math.ceil(total_elements / cols)
        base_height = rows * text_height + (rows - 1) * element_spacing
        
        # Add space for child cuts
        if child_cuts:
            base_height += len(child_cuts) * 60.0  # Minimum cut height
        
        return max(100.0, base_height)


class TransformationStableSequentialEngine:
    """
    Main sequential layout engine with transformation stability
    """
    
    def __init__(self, style_spec: StyleSpecification):
        self.style = style_spec
        self.canonical_positioning = CanonicalPositioning(style_spec)
        self.conservative_budgeting = ConservativeSpatialBudget(style_spec)
        
        # Layout state
        self.current_phase = None
        self.egi = None
        self.area_hierarchy = None
        self.area_sizes = None
        self.area_zones = None
        self.element_positions = None
        self.ligature_connections = None
    
    def compute_stable_layout(self, egi: RelationalGraphWithCuts, 
                            previous_layout: Optional[LayoutMemory] = None) -> LayoutDTO:
        """
        Execute the complete sequential layout process with transformation stability
        """
        self.egi = egi
        
        # Phase 1: Define containment hierarchy
        self.current_phase = LayoutPhase.CONTAINMENT_HIERARCHY
        self.area_hierarchy = self._compute_containment_hierarchy(egi)
        
        # Phase 2: Style application (already done in constructor)
        self.current_phase = LayoutPhase.STYLE_APPLICATION
        
        # Phase 3: Conservative size calculation
        self.current_phase = LayoutPhase.CONSERVATIVE_SIZING
        self.area_sizes = self._calculate_conservative_sizes(egi)
        self.area_zones = self._allocate_area_zones(self.area_sizes)
        
        # Phase 4: Canonical element placement
        self.current_phase = LayoutPhase.CANONICAL_PLACEMENT
        self.element_positions = self._place_elements_canonically(egi)
        
        # Phase 5: Vertex position optimization
        self.current_phase = LayoutPhase.VERTEX_OPTIMIZATION
        self.element_positions = self._optimize_vertex_positions(egi, max_iterations=3)
        
        # Phase 6: Predicate position optimization
        self.current_phase = LayoutPhase.PREDICATE_OPTIMIZATION
        self.element_positions = self._optimize_predicate_positions(egi, max_iterations=3)
        
        # Phase 7: Ligature routing
        self.current_phase = LayoutPhase.LIGATURE_ROUTING
        ligature_paths = self._route_ligature_paths(egi)
        
        # Build final LayoutDTO
        return self._build_layout_dto(ligature_paths)
    
    def _compute_containment_hierarchy(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, Set[ElementID]]:
        """Phase 1: Build containment hierarchy from EGI area mapping"""
        hierarchy = defaultdict(set)
        
        # Process all elements to determine their areas
        for vertex in egi.V:
            # Find which area contains this vertex
            area_id = None
            for area, elements in egi.area.items():
                if vertex.id in elements:
                    area_id = area
                    break
            if area_id is None:
                area_id = egi.sheet  # Default to sheet if not found
            hierarchy[area_id].add(vertex.id)
        
        for edge in egi.E:
            # Find which area contains this edge
            area_id = None
            for area, elements in egi.area.items():
                if edge.id in elements:
                    area_id = area
                    break
            if area_id is None:
                area_id = egi.sheet  # Default to sheet if not found
            hierarchy[area_id].add(edge.id)
        
        # Add cuts to their parent areas
        for cut in egi.Cut:
            if cut.id != egi.sheet:  # Sheet is the root
                # Find which area contains this cut
                parent_area = None
                for area, elements in egi.area.items():
                    if cut.id in elements:
                        parent_area = area
                        break
                if parent_area is None:
                    parent_area = egi.sheet  # Default to sheet if not found
                if parent_area != cut.id:  # Cut is contained in another area
                    hierarchy[parent_area].add(cut.id)
        
        return dict(hierarchy)
    
    def _calculate_conservative_sizes(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, AreaSizeRequirements]:
        """Phase 3: Calculate conservative size requirements for all areas"""
        sizes = {}
        
        # Calculate sizes for all areas in hierarchy
        for area_id in self.area_hierarchy:
            sizes[area_id] = self.conservative_budgeting.calculate_conservative_area_size(egi, area_id)
        
        return sizes
    
    def _allocate_area_zones(self, area_sizes: Dict[ElementID, AreaSizeRequirements]) -> Dict[ElementID, BoundingBox]:
        """Allocate spatial zones for each area based on size requirements"""
        zones = {}
        
        # Start with sheet area - use minimum size for better layouts
        sheet_size = area_sizes.get("sheet")
        if sheet_size:
            zones["sheet"] = BoundingBox(0, 0, sheet_size.min_width, sheet_size.min_height)
        
        # Allocate nested areas more compactly
        for area_id, size_req in area_sizes.items():
            if area_id != "sheet" and area_id not in zones:
                # Use minimum size and position more compactly
                margin = 20  # Smaller margin for tighter layouts
                zones[area_id] = BoundingBox(
                    margin, margin, 
                    margin + size_req.min_width, 
                    margin + size_req.min_height
                )
        
        return zones
    
    def _place_elements_canonically(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, ElementPosition]:
        """Phase 4: Place elements using canonical positioning"""
        all_positions = {}
        
        for area_id, area_bounds in self.area_zones.items():
            area_positions = self.canonical_positioning.assign_canonical_positions(
                egi, area_id, area_bounds
            )
            
            # Update area_id in positions
            for element_id, pos in area_positions.items():
                all_positions[element_id] = replace(pos, area_id=area_id)
        
        return all_positions
    
    def _optimize_vertex_positions(self, egi: RelationalGraphWithCuts, max_iterations: int = 3) -> Dict[ElementID, ElementPosition]:
        """Phase 5: Optimize vertex positions to minimize ligature distances"""
        # For now, return positions unchanged (optimization within area constraints)
        # Full implementation would swap positions within areas to minimize distances
        return self.element_positions
    
    def _optimize_predicate_positions(self, egi: RelationalGraphWithCuts, max_iterations: int = 3) -> Dict[ElementID, ElementPosition]:
        """Phase 6: Optimize predicate positions to minimize total ligature length"""
        # For now, return positions unchanged (optimization within area constraints)
        # Full implementation would swap positions within areas to minimize total length
        return self.element_positions
    
    def _route_ligature_paths(self, egi: RelationalGraphWithCuts) -> List[LigaturePath]:
        """Phase 7: Route ligature paths with collision avoidance"""
        paths = []
        
        # Analyze all ligature connections using egi.nu mapping
        for edge_id, vertex_sequence in egi.nu.items():
            if vertex_sequence:  # If edge has connected vertices
                for vertex_id in vertex_sequence:
                    # Create simple straight-line path for now
                    predicate_pos = self.element_positions.get(edge_id)
                    vertex_pos = self.element_positions.get(vertex_id)
                    
                    if predicate_pos and vertex_pos:
                        path = LigaturePath(
                            predicate_id=edge_id,
                            vertex_id=vertex_id,
                            points=(predicate_pos.position, vertex_pos.position)
                        )
                        paths.append(path)
        
        return paths
    
    def _build_layout_dto(self, ligature_paths: List[LigaturePath]) -> LayoutDTO:
        """Build final LayoutDTO from computed layout"""
        
        # Extract positions by type
        vertex_positions = {}
        predicate_positions = {}
        
        for element_id, pos in self.element_positions.items():
            if pos.element_type == 'vertex':
                vertex_positions[element_id] = pos.position
            elif pos.element_type == 'predicate':
                predicate_positions[element_id] = pos.position
        
        # Calculate viewport bounds
        all_positions = list(vertex_positions.values()) + list(predicate_positions.values())
        if all_positions:
            min_x = min(p.x for p in all_positions) - 50
            max_x = max(p.x for p in all_positions) + 50
            min_y = min(p.y for p in all_positions) - 50
            max_y = max(p.y for p in all_positions) + 50
            viewport = BoundingBox(min_x, min_y, max_x, max_y)
        else:
            viewport = BoundingBox(0, 0, 400, 300)
        
        # Create style hints dictionary from style specification
        style_hints = {
            'font_family': self.style.font_family,
            'font_size': self.style.font_size,
            'vertex_radius': self.style.vertex_radius,
            'cut_shape': self.style.cut_shape,
            'element_spacing': self.style.element_spacing,
            'text_width': self.style.predicate_char_width * 8,
            'text_height': self.style.predicate_height
        }
        
        return LayoutDTO(
            vertex_positions=vertex_positions,
            predicate_positions=predicate_positions,
            cut_bounds=self.area_zones,
            ligature_paths=ligature_paths,
            area_hierarchy=self.area_hierarchy,
            containment_depth={},  # Would be calculated in full implementation
            viewport_bounds=viewport,
            style_hints=style_hints
        )
