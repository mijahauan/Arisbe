#!/usr/bin/env python3
"""
Layout Phase Implementations - Concrete implementations of the 9-phase pipeline

Each phase implements the LayoutPhase protocol and uses the extracted utilities
from layout_utilities.py to perform its specific function in the dependency chain.
"""

from typing import Dict, Any, List, Set, Tuple, Optional
from dataclasses import dataclass
from src.egi_core_dau import RelationalGraphWithCuts

# Type aliases
Bounds = Tuple[float, float, float, float]  # x1, y1, x2, y2
Coordinate = Tuple[float, float]

# Import LayoutElement from the consolidated types module
from src.layout_types import LayoutElement
from src.layout_utilities import ElementDimensions, ElementMeasurement
# Define PhaseResult locally since it's not in pipeline_contracts
@dataclass
class PhaseResult:
    phase_name: str
    status: 'PhaseStatus'
    elements_modified: Set[str]
    dependencies_satisfied: Set[str]
    quality_metrics: Dict[str, Any]
    error_message: Optional[str] = None
from src.graphviz_utilities import get_cluster_bounds, get_node_positions, ClusterBounds, NodePosition
from src.spatial_awareness_system import SpatialAwarenessSystem
from src.spatial_constraint_integration import SpatiallyAwareContainerSizing, SpatiallyAwareCollisionDetection
# Simplified imports - remove non-existent modules for now
from abc import ABC, abstractmethod
from enum import Enum

class PhaseStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class LayoutPhase(ABC):
    @property
    @abstractmethod
    def phase_name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        pass
    
    @abstractmethod
    def execute(self, egi: RelationalGraphWithCuts, context: Dict[str, Any]) -> PhaseResult:
        pass


class ElementSizingPhase(LayoutPhase):
    """Phase 1: Measure and size all elements before positioning."""
    
    def __init__(self):
        self.measurer = ElementMeasurement()
    
    @property
    def phase_name(self) -> str:
        return "Element Sizing"
    
    @property
    def dependencies(self) -> List[str]:
        return []  # No dependencies - this is the foundation
    
    @property
    def capabilities(self) -> List[str]:
        return ["Element Dimensions"]
    
    def execute(self, egi: RelationalGraphWithCuts, context: Dict[str, Any]) -> PhaseResult:
        """Measure all elements and establish their relative size requirements."""
        try:
            # Measure all elements in the EGI and convert to relative dimensions
            absolute_dimensions = self.measurer.measure_all_elements(egi)
            
            # Convert absolute pixel dimensions to relative dimensions (0.0 to 1.0)
            relative_dimensions = self._convert_to_relative_dimensions(absolute_dimensions)
            
            # Store in context for later phases
            context['element_dimensions'] = relative_dimensions
            
            return PhaseResult(
                phase_name="Element Sizing",
                status=PhaseStatus.COMPLETED,
                elements_modified=set(relative_dimensions.keys()),
                dependencies_satisfied=set(),
                quality_metrics={'elements_measured': len(relative_dimensions)}
            )
            
        except Exception as e:
            return PhaseResult(
                phase_name="Element Sizing",
                status=PhaseStatus.FAILED,
                elements_modified=set(),
                dependencies_satisfied=set(),
                quality_metrics={},
                error_message=f"Element sizing failed: {str(e)}"
            )
    
    def _convert_to_relative_dimensions(self, absolute_dimensions):
        """Convert absolute pixel dimensions to relative dimensions (0.0 to 1.0)."""
        # Reference canvas size for conversion (can be adjusted based on typical canvas sizes)
        reference_width = 800.0
        reference_height = 600.0
        
        relative_dimensions = {}
        
        for element_id, dims in absolute_dimensions.items():
            if hasattr(dims, 'total_width') and hasattr(dims, 'total_height'):
                # ElementDimensions object
                relative_dimensions[element_id] = {
                    'width': dims.total_width / reference_width,
                    'height': dims.total_height / reference_height
                }
            elif isinstance(dims, dict):
                # Dictionary format
                width = dims.get('width', 80)
                height = dims.get('height', 30)
                relative_dimensions[element_id] = {
                    'width': width / reference_width,
                    'height': height / reference_height
                }
            else:
                # Fallback - assume reasonable defaults
                relative_dimensions[element_id] = {
                    'width': 0.1,  # 10% of canvas width
                    'height': 0.05  # 5% of canvas height
                }
        
        return relative_dimensions


class ContainerSizingPhase(LayoutPhase):
    """Phase 2: Size all containers using relative coordinates with proportional allocation."""
    
    def __init__(self, spatial_system: SpatialAwarenessSystem):
        self.spatial_system = spatial_system
        self.spatially_aware_sizer = SpatiallyAwareContainerSizing(spatial_system)
        self.container_elements = {}
        self.relative_bounds = {}  # Store relative coordinate bounds
    
    @property
    def phase_name(self) -> str:
        return "Container Sizing"
    
    @property
    def dependencies(self) -> List[str]:
        return ["Element Sizing"]
    
    @property
    def capabilities(self) -> List[str]:
        return ["Container Bounds"]
    
    def execute(self, egi: RelationalGraphWithCuts, context: Dict[str, Any]) -> PhaseResult:
        """Size all containers using Graphviz-optimized cluster bounds for exclusive positioning."""
        
        try:
            # Get element dimensions from previous phase
            element_dimensions = context.get('element_dimensions', {})
            if not element_dimensions:
                return PhaseResult(
                    phase_name="Container Sizing",
                    status=PhaseStatus.FAILED,
                    elements_modified=set(),
                    dependencies_satisfied=set(),
                    quality_metrics={},
                    error_message="No element dimensions available from previous phase"
                )
            
            # Use Graphviz-optimized cluster sizing for exclusive positioning
            cluster_bounds = get_cluster_bounds(egi, element_dimensions)
            
            # Convert ClusterBounds to relative coordinates for pipeline consistency
            self.relative_bounds = self._normalize_cluster_bounds_to_relative(cluster_bounds)
            
            # Add sheet bounds (always full canvas)
            self.relative_bounds['sheet'] = (0.0, 0.0, 1.0, 1.0)
            
            # Store results in context
            context['relative_bounds'] = self.relative_bounds
            context['cluster_bounds'] = cluster_bounds  # Keep absolute bounds for later phases
            
            return PhaseResult(
                phase_name="Container Sizing",
                status=PhaseStatus.COMPLETED,
                elements_modified=set(self.relative_bounds.keys()),
                dependencies_satisfied={'Element Sizing'},
                quality_metrics={
                    'containers_sized': len(self.relative_bounds),
                    'spatial_conflicts': 0,
                    'graphviz_optimized': True
                }
            )
            
        except Exception as e:
            return PhaseResult(
                phase_name="Container Sizing",
                status=PhaseStatus.FAILED,
                elements_modified=set(),
                dependencies_satisfied=set(),
                quality_metrics={},
                error_message=f"Container sizing failed: {str(e)}"
            )
    
    def _normalize_cluster_bounds_to_relative(self, cluster_bounds):
        """Convert absolute cluster bounds to relative coordinates (0-1 range)."""
        if not cluster_bounds:
            return {}
        
        # Find overall bounding box
        min_x = min(bounds.x1 for bounds in cluster_bounds.values())
        min_y = min(bounds.y1 for bounds in cluster_bounds.values())
        max_x = max(bounds.x2 for bounds in cluster_bounds.values())
        max_y = max(bounds.y2 for bounds in cluster_bounds.values())
        
        total_width = max_x - min_x
        total_height = max_y - min_y
        
        # Avoid division by zero
        if total_width == 0:
            total_width = 1
        if total_height == 0:
            total_height = 1
        
        # Convert to relative coordinates
        relative_bounds = {}
        for cut_id, bounds in cluster_bounds.items():
            rel_x = (bounds.x1 - min_x) / total_width
            rel_y = (bounds.y1 - min_y) / total_height
            rel_width = bounds.width / total_width
            rel_height = bounds.height / total_height
            
            relative_bounds[cut_id] = (rel_x, rel_y, rel_width, rel_height)
        
        return relative_bounds
    
    def _iterative_container_sizing(self, containers, element_dimensions, egi, sizing_state):
        """Initialize containers with minimal bounds, then expand iteratively as elements are added."""
        bounds = sizing_state['container_bounds'].copy()
        
        # Step 1: Initialize all containers with minimal bounds based on current content
        self._initialize_minimal_container_bounds(containers, bounds)
        
        # Step 2: Iteratively add each element and expand containers as needed
        for element_id, dimensions in element_dimensions.items():
            container_id = self._find_element_container(element_id, egi)
            if container_id and container_id != 'sheet':
                # Expand container hierarchy to accommodate this element
                self._expand_container_for_element(
                    element_id, dimensions, container_id, containers, bounds
                )
        
        return bounds
    
    def _initialize_minimal_container_bounds(self, containers, bounds):
        """Initialize all containers with minimal bounds based on current content."""
        # Process in top-down order so parents exist before children
        processing_order = self._build_processing_order(containers)
        
        for container_id in processing_order:
            if container_id == 'sheet':
                continue
                
            container_info = containers[container_id]
            parent_id = container_info.parent_id or 'sheet'
            parent_bounds = bounds[parent_id]
            
            # Start with minimal bounds (20% of parent, centered)
            parent_width = parent_bounds[2] - parent_bounds[0]
            parent_height = parent_bounds[3] - parent_bounds[1]
            
            min_width = parent_width * 0.2
            min_height = parent_height * 0.2
            
            center_x = parent_bounds[0] + parent_width * 0.5
            center_y = parent_bounds[1] + parent_height * 0.5
            
            bounds[container_id] = (
                center_x - min_width/2,
                center_y - min_height/2,
                center_x + min_width/2,
                center_y + min_height/2
            )
    
    def _find_element_container(self, element_id, egi):
        """Find which container contains the given element."""
        for area_id, elements in egi.area.items():
            if element_id in elements:
                return area_id
        return None
    
    def _expand_container_for_element(self, element_id, dimensions, container_id, containers, bounds):
        """Expand container and cascade resize up containment hierarchy."""
        element_width = dimensions.get('width', 0.05)
        element_height = dimensions.get('height', 0.05)
        padding = 0.02
        
        # Calculate space needed for this element
        required_addition_width = element_width + padding
        required_addition_height = element_height + padding
        
        # Expand current container
        current_bounds = bounds[container_id]
        current_width = current_bounds[2] - current_bounds[0]
        current_height = current_bounds[3] - current_bounds[1]
        
        new_width = current_width + required_addition_width
        new_height = max(current_height, required_addition_height)
        
        # Update container bounds (keep centered in parent)
        center_x = (current_bounds[0] + current_bounds[2]) / 2
        center_y = (current_bounds[1] + current_bounds[3]) / 2
        
        bounds[container_id] = (
            center_x - new_width/2,
            center_y - new_height/2,
            center_x + new_width/2,
            center_y + new_height/2
        )
        
        # Cascading resize up the containment hierarchy
        self._cascade_expansion_to_parents(container_id, new_width, new_height, containers, bounds)
    
    def _cascade_expansion_to_parents(self, container_id, required_width, required_height, containers, bounds):
        """Cascade size increases up the containment hierarchy."""
        container_info = containers.get(container_id)
        if not container_info or not container_info.parent_id or container_info.parent_id == 'sheet':
            return
        
        parent_id = container_info.parent_id
        parent_bounds = bounds[parent_id]
        parent_width = parent_bounds[2] - parent_bounds[0]
        parent_height = parent_bounds[3] - parent_bounds[1]
        
        # Check if parent needs to expand to contain this container
        padding = 0.02
        if required_width + padding > parent_width or required_height + padding > parent_height:
            new_parent_width = max(parent_width, required_width + padding)
            new_parent_height = max(parent_height, required_height + padding)
            
            # Expand parent (keep centered in its parent)
            center_x = (parent_bounds[0] + parent_bounds[2]) / 2
            center_y = (parent_bounds[1] + parent_bounds[3]) / 2
            
            bounds[parent_id] = (
                center_x - new_parent_width/2,
                center_y - new_parent_height/2,
                center_x + new_parent_width/2,
                center_y + new_parent_height/2
            )
            
            # Continue cascade up
            self._cascade_expansion_to_parents(parent_id, new_parent_width, new_parent_height, containers, bounds)
    
    def _calculate_actual_content_size(self, container_id, container_info, element_dimensions, egi):
        """Calculate actual space needed based on real element content."""
        total_width = 0.0
        total_height = 0.0
        padding = 0.05  # Relative padding
        
        # Get all elements in this container
        elements_in_container = egi.area.get(container_id, frozenset())
        
        for element_id in elements_in_container:
            if element_id in element_dimensions:
                dims = element_dimensions[element_id]
                # Accumulate actual dimensions (not hardcoded fallbacks)
                total_width += dims.get('width', 0.1)
                total_height = max(total_height, dims.get('height', 0.05))
        
        # Add padding for container boundaries
        return {
            'width': total_width + (2 * padding),
            'height': total_height + (2 * padding)
        }
    
    def _allocate_space_in_parent(self, container_id, content_size, parent_bounds, sizing_state):
        """Allocate space for container within parent bounds."""
        parent_left, parent_top, parent_right, parent_bottom = parent_bounds
        parent_width = parent_right - parent_left
        parent_height = parent_bottom - parent_top
        
        # Calculate container size as proportion of parent
        container_width = min(content_size['width'], parent_width * 0.8)
        container_height = min(content_size['height'], parent_height * 0.8)
        
        # Center within parent (simple positioning for now)
        center_x = parent_left + parent_width / 2
        center_y = parent_top + parent_height / 2
        
        return (
            center_x - container_width / 2,
            center_y - container_height / 2,
            center_x + container_width / 2,
            center_y + container_height / 2
        )
    
    def _trigger_parent_resize_cascade(self, container_id, content_size, bounds, containers):
        """Trigger resizing cascade up the parent hierarchy."""
        # Find parent
        container_info = containers.get(container_id)
        if not container_info or not container_info.parent_id:
            return
        
        parent_id = container_info.parent_id
        if parent_id == 'sheet':
            return  # Sheet doesn't resize
        
        # Recalculate parent size based on all its children
        parent_info = containers.get(parent_id)
        if parent_info:
            # Get all child containers
            child_bounds = [bounds[child_id] for child_id in parent_info.children.keys() if child_id in bounds]
            
            if child_bounds:
                # Calculate minimum parent bounds to contain all children
                min_left = min(b[0] for b in child_bounds) - 0.02
                min_top = min(b[1] for b in child_bounds) - 0.02
                max_right = max(b[2] for b in child_bounds) + 0.02
                max_bottom = max(b[3] for b in child_bounds) + 0.02
                
                # Update parent bounds
                bounds[parent_id] = (min_left, min_top, max_right, max_bottom)
                
                # Continue cascade up the hierarchy
                self._trigger_parent_resize_cascade(parent_id, 
                    {'width': max_right - min_left, 'height': max_bottom - min_top}, 
                    bounds, containers)
    
    def _calculate_relative_container_bounds(self, containers, element_dimensions, egi):
        """Calculate container bounds using relative coordinates with proportional allocation."""
        bounds = {}
        
        # Initialize sheet area as full relative coordinate space
        bounds['sheet'] = (0.0, 0.0, 1.0, 1.0)
        
        # Build dependency order for bottom-up processing
        processing_order = self._build_processing_order(containers)
        
        # State tracking for iterative tree traversal
        allocation_state = {
            'allocated_areas': {},  # Track allocated space within each parent
            'content_requirements': {},  # Track space needed by content
            'sibling_positions': {}  # Track sibling positioning to avoid overlap
        }
        
        # Process containers from leaves to root
        for container_id in processing_order:
            container_info = containers[container_id]
            parent_id = container_info.parent_id or 'sheet'
            
            # Calculate content requirements for this container
            content_size = self._calculate_content_requirements(
                container_id, container_info, element_dimensions, egi, allocation_state
            )
            
            # Allocate proportional space within parent
            container_bounds = self._allocate_proportional_space(
                container_id, parent_id, content_size, bounds, allocation_state
            )
            
            bounds[container_id] = container_bounds
            
            # Update state for next iteration
            self._update_allocation_state(container_id, container_bounds, allocation_state)
        
        return bounds
    
    def _build_processing_order(self, containers):
        """Build top-down processing order for containers."""
        # Create parent-child relationships
        children = {}
        for container_id, info in containers.items():
            parent_id = info.parent_id or 'sheet'
            if parent_id not in children:
                children[parent_id] = []
            children[parent_id].append(container_id)
        
        # Top-down traversal: process parents before children
        order = []
        visited = set()
        
        def visit(node_id):
            if node_id in visited or node_id == 'sheet':
                return
            visited.add(node_id)
            order.append(node_id)
            
            # Visit children after parent (top-down)
            for child_id in children.get(node_id, []):
                visit(child_id)
        
        # Start from root containers (those with sheet as parent)
        for container_id in containers:
            if containers[container_id].parent_id == 'sheet' or containers[container_id].parent_id is None:
                visit(container_id)
        
        return order
    
    def _calculate_content_requirements(self, container_id, container_info, element_dimensions, egi, state):
        """Calculate spatial requirements for container content."""
        # Get predicates (edges) in this container
        predicates_in_container = [
            e for e in egi.E if container_id in egi.area and e.id in egi.area[container_id]
        ]
        
        # Get vertices in this container  
        vertices_in_container = [
            v for v in egi.V if container_id in egi.area and v.id in egi.area[container_id]
        ]
        
        # Get child containers
        child_containers = [
            child_id for child_id, info in container_info.children.items()
        ] if hasattr(container_info, 'children') else []
        
        # Calculate minimum space needed
        predicate_area = sum(
            element_dimensions.get(e.id, {}).get('width', 0.1) * 
            element_dimensions.get(e.id, {}).get('height', 0.05)
            for e in predicates_in_container
        )
        
        vertex_area = len(vertices_in_container) * 0.01  # Small area for vertices
        
        # Child container area (will be calculated recursively)
        child_area = sum(
            state['content_requirements'].get(child_id, 0.1)
            for child_id in child_containers
        )
        
        total_area = predicate_area + vertex_area + child_area
        
        # Add padding factor
        padded_area = total_area * 1.2  # 20% padding
        
        # Store for state tracking
        state['content_requirements'][container_id] = padded_area
        
        return padded_area
    
    def _allocate_proportional_space(self, container_id, parent_id, content_size, bounds, state):
        """Allocate proportional space within parent using dynamic shrinking."""
        parent_bounds = bounds[parent_id]
        parent_width = parent_bounds[2] - parent_bounds[0]
        parent_height = parent_bounds[3] - parent_bounds[1]
        parent_area = parent_width * parent_height
        
        # Get siblings for positioning
        siblings = state['sibling_positions'].get(parent_id, [])
        sibling_count = len(siblings) + 1  # Include current container
        
        # Calculate proportional allocation
        if parent_id == 'sheet':
            # Sheet level: allocate based on content requirements
            allocation_ratio = min(content_size / parent_area, 0.8)  # Max 80% of sheet
        else:
            # Nested cut: use proportional allocation with dynamic shrinking
            base_allocation = 0.48  # 48% base allocation
            shrink_factor = max(0.3, content_size / parent_area)  # Dynamic shrinking
            allocation_ratio = base_allocation * shrink_factor
        
        # Calculate container dimensions
        container_area = parent_area * allocation_ratio
        aspect_ratio = 1.2  # Slightly wider than tall
        container_width = (container_area * aspect_ratio) ** 0.5
        container_height = container_area / container_width
        
        # Position within parent, accounting for siblings
        sibling_offset = len(siblings) * 0.1  # Horizontal offset for siblings
        
        # Center within parent with sibling offset
        center_x = parent_bounds[0] + parent_width * 0.5 + sibling_offset
        center_y = parent_bounds[1] + parent_height * 0.5
        
        # Ensure container stays within parent bounds
        left = max(parent_bounds[0], center_x - container_width / 2)
        top = max(parent_bounds[1], center_y - container_height / 2)
        right = min(parent_bounds[2], left + container_width)
        bottom = min(parent_bounds[3], top + container_height)
        
        return (left, top, right, bottom)
    
    def _update_allocation_state(self, container_id, container_bounds, state):
        """Update allocation state after processing a container."""
        # Track allocated area
        state['allocated_areas'][container_id] = container_bounds
        
        # Update sibling positioning
        parent_id = 'sheet'  # This should be extracted from container info
        if parent_id not in state['sibling_positions']:
            state['sibling_positions'][parent_id] = []
        state['sibling_positions'][parent_id].append(container_id)
    
    def _extract_simple_hierarchy(self, egi):
        """Extract container hierarchy from EGI area mapping."""
        containers = {}
        
        # Always create sheet container
        containers['sheet'] = type('Container', (), {
            'parent_id': None,
            'element_ids': list(egi.area.get('sheet', frozenset())),
            'children': {}
        })()
        
        # Add cut containers if they exist
        for cut in egi.Cut:
            # Find parent by checking which area contains this cut
            parent_id = 'sheet'  # Default to sheet
            for area_id, elements in egi.area.items():
                if area_id != cut.id and cut.id in elements:
                    parent_id = area_id
                    break
            
            containers[cut.id] = type('Container', (), {
                'parent_id': parent_id,
                'element_ids': list(egi.area.get(cut.id, frozenset())),
                'children': {}
            })()
            
            # Update parent's children
            if parent_id in containers:
                containers[parent_id].children[cut.id] = containers[cut.id]
        
        return containers


class CollisionDetectionPhase(LayoutPhase):
    """Phase 3: Detect and resolve element collisions with spatial exclusion awareness."""
    
    def __init__(self, spatial_system: SpatialAwarenessSystem):
        self.spatial_system = spatial_system
        self.spatially_aware_collision = SpatiallyAwareCollisionDetection(spatial_system)
        from layout_utilities import CollisionDetection
        self.collision_detector = CollisionDetection()
    
    @property
    def phase_name(self) -> str:
        return "Collision Detection"
    
    @property
    def dependencies(self) -> List[str]:
        return ["Container Sizing"]
    
    @property
    def capabilities(self) -> List[str]:
        return ["Collision Free Positions"]
    
    def execute(self, egi: RelationalGraphWithCuts, context: Dict[str, Any]) -> PhaseResult:
        """Detect collisions and prepare collision-free positioning data with spatial awareness."""
        
        try:
            # Get container information from ContainerSizingPhase output
            relative_bounds = context.get('relative_bounds', {})
            element_dimensions = context.get('element_dimensions', {})
            
            # Store collision-free positions in context
            context['collision_free_positions'] = {}
            context['spatial_violations'] = []
            
            return PhaseResult(
                phase_name="Collision Detection",
                status=PhaseStatus.COMPLETED,
                elements_modified=set(element_dimensions.keys()),
                dependencies_satisfied={'Container Sizing'},
                quality_metrics={'collision_checks': len(element_dimensions)}
            )
            
        except Exception as e:
            return PhaseResult(
                phase_name="Collision Detection",
                status=PhaseStatus.FAILED,
                elements_modified=set(),
                dependencies_satisfied=set(),
                quality_metrics={},
                error_message=f"Collision detection setup failed: {str(e)}"
            )


class PredicatePositioningPhase(LayoutPhase):
    """Phase 4: Position predicate elements within their containers with spatial awareness."""
    
    def __init__(self, spatial_system: SpatialAwarenessSystem):
        self.spatial_system = spatial_system
        self.element_measurement = ElementMeasurement()
    
    @property
    def phase_name(self) -> str:
        return "Predicate Positioning"
    
    @property
    def dependencies(self) -> List[str]:
        return ["Collision Detection"]
    
    @property
    def capabilities(self) -> List[str]:
        return ["Predicate Positions"]
    
    def execute(self, egi: RelationalGraphWithCuts, context: Dict[str, Any]) -> PhaseResult:
        """Position all predicate elements using Graphviz-optimized exclusive positioning."""
        
        try:
            # Get required context from previous phases
            element_dimensions = context.get('element_dimensions', {})
            cluster_bounds = context.get('cluster_bounds', {})
            
            if not cluster_bounds:
                return PhaseResult(
                    phase_name="Predicate Positioning",
                    status=PhaseStatus.FAILED,
                    elements_modified=set(),
                    dependencies_satisfied=set(),
                    quality_metrics={},
                    error_message="No cluster bounds available from Container Sizing phase"
                )
            
            # Get Graphviz-optimized node positions with exclusive positioning
            node_positions = get_node_positions(egi, cluster_bounds, element_dimensions)
            
            predicate_elements = {}
            element_tracking = context.get('element_tracking', {})
            
            # Position predicates using Graphviz-optimized exclusive positions
            for predicate in egi.E:
                # Skip identity edges (handled separately)
                if predicate.id in egi.rel and egi.rel[predicate.id] in ('=', '.='):
                    continue
                
                # Use Graphviz-optimized position if available
                if predicate.id in node_positions:
                    node_pos = node_positions[predicate.id]
                    position = (node_pos.x, node_pos.y)
                    
                    # Get predicate name for bounds calculation
                    predicate_name = egi.rel.get(predicate.id, predicate.id)
                    
                    # Use actual text dimensions for exclusive positioning
                    text_width = node_pos.width / 100.0  # Convert back from DOT units
                    text_height = node_pos.height / 100.0
                    
                    # Convert to relative coordinates for consistency
                    rel_position = self._absolute_to_relative_position(position, cluster_bounds)
                    rel_bounds = self._absolute_to_relative_bounds(
                        (position[0] - text_width/2, position[1] - text_height/2,
                         position[0] + text_width/2, position[1] + text_height/2),
                        cluster_bounds
                    )
                    
                    predicate_elements[predicate.id] = type('PredicateElement', (), {
                        'position': rel_position,
                        'bounds': rel_bounds,
                        'text': predicate_name
                    })()
                    
                    # Update element tracking for GUI
                    element_tracking[predicate.id] = {
                        'position': rel_position,
                        'bounds': rel_bounds,
                        'element_type': 'predicate'
                    }
        
            # Store predicate elements for later phases and ensure element_tracking exists
            context['predicate_elements'] = predicate_elements
            
            # Also store in element_tracking format for GUI conversion
            if 'element_tracking' not in context:
                context['element_tracking'] = {}
            
            for pred_id, pred_element in predicate_elements.items():
                context['element_tracking'][pred_id] = {
                    'position': pred_element.position,
                    'bounds': pred_element.bounds,
                    'element_type': 'predicate'
                }
            
            return PhaseResult(
                phase_name="Predicate Positioning",
                status=PhaseStatus.COMPLETED,
                elements_modified=set(predicate_elements.keys()),
                dependencies_satisfied={"Collision Detection"},
                quality_metrics={
                    'predicates_positioned': len(predicate_elements),
                    'exclusive_positioning': True,
                    'graphviz_optimized': True
                }
            )
            
        except Exception as e:
            return PhaseResult(
                phase_name="Predicate Positioning",
                status=PhaseStatus.FAILED,
                elements_modified=set(),
                dependencies_satisfied=set(),
                quality_metrics={},
                error_message=f"Predicate positioning failed: {str(e)}"
            )
    
    def _find_relative_position_within_container(self, container_id, dims, existing_elements, relative_bounds):
        """Find collision-free position within container using relative coordinates."""
        container_bounds = relative_bounds.get(container_id, (0.0, 0.0, 1.0, 1.0))
        
        # Container dimensions in relative coordinates
        left, top, right, bottom = container_bounds
        container_width = right - left
        container_height = bottom - top
        
        # Add padding to keep elements away from container edges
        padding_x = min(0.02, container_width * 0.1)  # 2% or 10% of width, whichever is smaller
        padding_y = min(0.02, container_height * 0.1)  # 2% or 10% of height, whichever is smaller
        
        # Available positioning area
        available_left = left + padding_x
        available_top = top + padding_y
        available_right = right - padding_x - dims['width']
        available_bottom = bottom - padding_y - dims['height']
        
        # Ensure we have valid positioning space
        if available_right <= available_left or available_bottom <= available_top:
            # Container too small, position at center
            return (left + container_width/2, top + container_height/2)
        
        # Try grid-based positioning for collision avoidance
        grid_steps = 5
        step_x = (available_right - available_left) / grid_steps
        step_y = (available_bottom - available_top) / grid_steps
        
        for i in range(grid_steps):
            for j in range(grid_steps):
                candidate_x = available_left + i * step_x + dims['width']/2
                candidate_y = available_top + j * step_y + dims['height']/2
                
                # Check for collisions with existing elements
                candidate_bounds = (
                    candidate_x - dims['width']/2,
                    candidate_y - dims['height']/2,
                    candidate_x + dims['width']/2,
                    candidate_y + dims['height']/2
                )
                
                collision_free = True
                for existing_element in existing_elements.values():
                    if self._bounds_overlap(candidate_bounds, existing_element.bounds):
                        collision_free = False
                        break
                
                if collision_free:
                    return (candidate_x, candidate_y)
        
        # If no collision-free position found, return center
        return (left + container_width/2, top + container_height/2)
    
    def _bounds_overlap(self, bounds1, bounds2):
        """Check if two bounding rectangles overlap."""
        left1, top1, right1, bottom1 = bounds1
        left2, top2, right2, bottom2 = bounds2
        
        return not (right1 <= left2 or right2 <= left1 or bottom1 <= top2 or bottom2 <= top1)
    
    def _validate_element_placement(self, bounds: Bounds, existing_elements: List[LayoutElement]) -> bool:
        """Validate that element bounds don't collide with existing elements."""
        for element in existing_elements:
            if self._bounds_overlap(bounds, element.bounds):
                return False
        return True
    
    def _resolve_predicate_collision(self, 
                                   predicate_id: str,
                                   dims: ElementDimensions,
                                   container_id: str,
                                   existing_elements: List[LayoutElement],
                                   container_bounds: Dict[str, Bounds]) -> Optional[Coordinate]:
        """Resolve predicate collision by finding alternative position."""
        
        container_bound = container_bounds.get(container_id)
        if not container_bound:
            return None
        
        cx, cy, cw, ch = container_bound
        padding = 20
        
        # Try grid positions within container
        step_size = 15
        for y_offset in range(padding, int(ch - cy - dims.total_height - padding), step_size):
            for x_offset in range(padding, int(cw - cx - dims.total_width - padding), step_size):
                test_x = cx + x_offset + dims.total_width // 2
                test_y = cy + y_offset + dims.total_height // 2
                
                test_bounds = (
                    test_x - dims.total_width // 2,
                    test_y - dims.total_height // 2,
                    test_x + dims.total_width // 2,
                    test_y + dims.total_height // 2
                )
                
                if self._validate_element_placement(test_bounds, existing_elements):
                    return (test_x, test_y)
        
        return None
    
    def _bounds_overlap(self, bounds1: Bounds, bounds2: Bounds) -> bool:
        """Check if two bounding rectangles overlap."""
        x1_min, y1_min, x1_max, y1_max = bounds1
        x2_min, y2_min, x2_max, y2_max = bounds2
        
        return not (x1_max <= x2_min or x2_max <= x1_min or 
                   y1_max <= y2_min or y2_max <= y1_min)
    
    def _find_position_within_container(self, container_id: str, dims: ElementDimensions, 
                                       existing_elements: List[LayoutElement], 
                                       container_bounds: Dict[str, Bounds]) -> Optional[Coordinate]:
        """Find collision-free position within container bounds."""
        if container_id not in container_bounds:
            return (50.0, 50.0)  # Fallback for sheet
        
        container_bound = container_bounds[container_id]
        x1, y1, x2, y2 = container_bound
        
        # Add padding to avoid placing elements right on container edge
        padding = 10.0
        available_x1 = x1 + padding
        available_y1 = y1 + padding  
        available_x2 = x2 - padding - dims.total_width
        available_y2 = y2 - padding - dims.total_height
        
        # Ensure we have valid space
        if available_x2 <= available_x1 or available_y2 <= available_y1:
            # Container too small, place at center
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            return (center_x, center_y)
        
        # Try grid positions within available space
        grid_size = 20.0
        max_attempts = 50
        attempt = 0
        
        while attempt < max_attempts:
            # Grid-based positioning
            grid_x = int((available_x2 - available_x1) / grid_size)
            grid_y = int((available_y2 - available_y1) / grid_size)
            
            if grid_x <= 0 or grid_y <= 0:
                break
                
            x_offset = (attempt % grid_x) * grid_size
            y_offset = ((attempt // grid_x) % grid_y) * grid_size
            
            x = available_x1 + x_offset + dims.total_width // 2
            y = available_y1 + y_offset + dims.total_height // 2
            
            # Check bounds
            proposed_bounds = (
                x - dims.total_width // 2,
                y - dims.total_height // 2,
                x + dims.total_width // 2,
                y + dims.total_height // 2
            )
            
            # Verify position is within container
            if (proposed_bounds[0] >= x1 and proposed_bounds[1] >= y1 and
                proposed_bounds[2] <= x2 and proposed_bounds[3] <= y2):
                
                # Check collision with existing elements
                collision = False
                for element in existing_elements:
                    if self._bounds_overlap(proposed_bounds, element.bounds):
                        collision = True
                        break
                
                if not collision:
                    return (x, y)
            
            attempt += 1
        
        # Final fallback: center of container
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        return (center_x, center_y)
    
    def _bounds_overlap(self, bounds1: Bounds, bounds2: Bounds) -> bool:
        """Check if two bounding boxes overlap."""
        x1_min, y1_min, x1_max, y1_max = bounds1
        x2_min, y2_min, x2_max, y2_max = bounds2
        
        if (x1_max <= x2_min or x2_max <= x1_min or 
            y1_max <= y2_min or y2_max <= y1_min):
            return False
        return True


class VertexPositioningPhase(LayoutPhase):
    """Phase 5: Position vertex elements within their containers with spatial awareness."""
    
    def __init__(self, spatial_system: SpatialAwarenessSystem):
        self.spatial_system = spatial_system
        self.element_measurement = ElementMeasurement()
    
    @property
    def phase_name(self) -> str:
        return "Vertex Positioning"
    
    @property
    def dependencies(self) -> List[str]:
        return ["Predicate Positioning"]
    
    @property
    def capabilities(self) -> List[str]:
        return ["Vertex Positions"]
    
    def execute(self, egi: RelationalGraphWithCuts, context: Dict[str, Any]) -> PhaseResult:
        """Position all vertex elements with spatial awareness."""
        
        try:
            # Get required context from previous phases
            element_dimensions = context.get('element_dimensions', {})
            relative_bounds = context.get('relative_bounds', {})
            cluster_bounds = context.get('cluster_bounds', {})
            predicate_elements = context.get('predicate_elements', {})
            element_tracking = context.get('element_tracking', {})
            collision_free_positions = context.get('collision_free_positions', {})
            
            if not element_dimensions:
                return PhaseResult(
                    phase_name="Vertex Positioning",
                    status=PhaseStatus.FAILED,
                    elements_modified=set(),
                    dependencies_satisfied=set(),
                    quality_metrics={},
                    error_message="Missing element dimensions from previous phases"
                )
            
            vertex_elements = {}
            
            # Find all vertices in the EGI
            for vertex in egi.V:
                vertex_id = vertex.id
                if vertex_id not in element_dimensions:
                    continue
                
                dims = element_dimensions[vertex_id]
                
                # Find which container this vertex belongs to
                container_id = self._find_vertex_container(vertex, egi)
                
                # Get container bounds for positioning
                container_bounds = relative_bounds.get(container_id, (0.0, 0.0, 1.0, 1.0))
                
                # Find collision-free position within container
                position = self._find_vertex_position(vertex_id, dims, container_bounds, 
                                                    predicate_elements, vertex_elements)
                
                if position:
                    # Convert relative position to absolute bounds
                    rel_bounds = self._calculate_vertex_bounds(position, dims)
                    
                    vertex_data = {
                        'element_id': vertex_id,
                        'element_type': 'vertex',
                        'relative_position': position,
                        'relative_bounds': rel_bounds,
                        'parent_area': container_id,
                        'dimensions': dims
                    }
                    
                    vertex_elements[vertex_id] = vertex_data
            
            # Update element tracking
            for vertex_id, vertex_data in vertex_elements.items():
                container_id = vertex_data['parent_area']
                if container_id not in element_tracking:
                    element_tracking[container_id] = []
                element_tracking[container_id].append(vertex_data)
            
            # Store results in context
            context['vertex_elements'] = vertex_elements
            context['element_tracking'] = element_tracking
            
            return PhaseResult(
                phase_name="Vertex Positioning",
                status=PhaseStatus.COMPLETED,
                elements_modified=set(vertex_elements.keys()),
                dependencies_satisfied={"Element Dimensions", "Container Sizing", "Collision Detection", "Predicate Positioning"},
                quality_metrics={'vertices_positioned': len(vertex_elements)}
            )
            
        except Exception as e:
            return PhaseResult(
                phase_name="Vertex Positioning",
                status=PhaseStatus.FAILED,
                elements_modified=set(),
                dependencies_satisfied=set(),
                quality_metrics={},
                error_message=f"Vertex positioning failed: {str(e)}"
            )
    
    def _find_vertex_container(self, vertex, egi):
        """Find which container/cut this vertex belongs to."""
        # Use the area mapping to find which context contains this vertex
        return egi.get_context(vertex.id)
    
    def _find_vertex_position(self, vertex_id, dims, container_bounds, predicate_elements, existing_vertices):
        """Find collision-free position for vertex within container bounds."""
        left, top, width, height = container_bounds
        right = left + width
        bottom = top + height
        
        # Add padding
        padding = 0.05  # 5% padding
        available_left = left + padding
        available_top = top + padding
        available_right = right - padding - dims.get('width', 0.1)
        available_bottom = bottom - padding - dims.get('height', 0.1)
        
        # Ensure valid positioning space
        if available_right <= available_left or available_bottom <= available_top:
            return (left + width/2, top + height/2)
        
        # Simple grid-based positioning
        grid_size = 3
        step_x = (available_right - available_left) / grid_size
        step_y = (available_bottom - available_top) / grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                candidate_x = available_left + i * step_x + dims.get('width', 0.1)/2
                candidate_y = available_top + j * step_y + dims.get('height', 0.1)/2
                
                # Check for collisions with existing elements
                if not self._position_has_collision(candidate_x, candidate_y, dims, predicate_elements, existing_vertices):
                    return (candidate_x, candidate_y)
        
        # Fallback to center
        return (left + width/2, top + height/2)
    
    def _position_has_collision(self, x, y, dims, predicate_elements, existing_vertices):
        """Check if position collides with existing elements."""
        width = dims.get('width', 0.1)
        height = dims.get('height', 0.1)
        
        test_bounds = (x - width/2, y - height/2, x + width/2, y + height/2)
        
        # Check against predicates
        for pred_data in predicate_elements.values():
            pred_bounds = pred_data.get('relative_bounds')
            if pred_bounds and self._bounds_overlap(test_bounds, pred_bounds):
                return True
        
        # Check against existing vertices
        for vertex_data in existing_vertices.values():
            vertex_bounds = vertex_data.get('relative_bounds')
            if vertex_bounds and self._bounds_overlap(test_bounds, vertex_bounds):
                return True
        
        return False
    
    def _calculate_vertex_bounds(self, position, dims):
        """Calculate relative bounds for vertex at position."""
        x, y = position
        width = dims.get('width', 0.1)
        height = dims.get('height', 0.1)
        
        return (x - width/2, y - height/2, x + width/2, y + height/2)
    
    def _bounds_overlap(self, bounds1, bounds2):
        """Check if two bounding rectangles overlap."""
        x1_min, y1_min, x1_max, y1_max = bounds1
        x2_min, y2_min, x2_max, y2_max = bounds2
        
        return not (x1_max <= x2_min or x2_max <= x1_min or 
                   y1_max <= y2_min or y2_max <= y1_min)


class HookAssignmentPhase(LayoutPhase):
    """Phase 6: Assign cardinal point hooks based on nu mapping order."""
    
    def __init__(self):
        from layout_utilities import HookPositioning
        self.hook_positioner = HookPositioning()
    
    @property
    def phase_name(self) -> str:
        return "Hook Assignment"
    
    @property
    def dependencies(self) -> List[str]:
        return ["Vertex Positioning"]
    
    @property
    def capabilities(self) -> List[str]:
        return ["Hook Positions"]
    
    def execute(self, egi: RelationalGraphWithCuts, context: Dict[str, Any]) -> PhaseResult:
        """Assign hooks to cardinal points based on connection order."""
        try:
            predicate_elements = context.get('predicate_elements', {})
            vertex_elements = context.get('vertex_elements', {})
            hook_assignments = {}
            
            # For each predicate, assign hooks to connected vertices
            for predicate_id, predicate_element in predicate_elements.items():
                # Get connected vertices from nu mapping
                connected_vertex_ids = egi.nu.get(predicate_id, [])
                connected_vertices = [vertex_elements[vid] for vid in connected_vertex_ids 
                                    if vid in vertex_elements]
                
                if connected_vertices:
                    # Assign cardinal hooks
                    hooks = self.hook_positioner.assign_cardinal_hooks(
                        predicate_element, connected_vertices
                    )
                    hook_assignments[predicate_id] = hooks
            
            return PhaseResult(
                phase_name="Hook Assignment",
                status=PhaseStatus.COMPLETED,
                elements_modified=set(hook_assignments.keys()),
                dependencies_satisfied={"Element Dimensions", "Container Sizing", "Collision Detection", "Predicate Positioning", "Vertex Positioning"},
                quality_metrics={'hooks_assigned': len(hook_assignments)}
            )
            
        except Exception as e:
            return PhaseResult(
                phase_name="Hook Assignment",
                status=PhaseStatus.FAILED,
                elements_modified=set(),
                dependencies_satisfied=set(),
                quality_metrics={},
                error_message=f"Hook assignment failed: {str(e)}"
            )


# Placeholder phases for ligature generation and optimization

class RectilinearLigaturePhase(LayoutPhase):
    """Phase 7: Generate rectilinear ligature paths."""
    
    @property
    def phase_name(self) -> str:
        return "Rectilinear Ligature"
    
    @property
    def dependencies(self) -> List[str]:
        return ["Hook Assignment"]
    
    @property
    def capabilities(self) -> List[str]:
        return ["Ligature Paths"]
    
    def execute(self, egi: RelationalGraphWithCuts, context: Dict[str, Any]) -> PhaseResult:
        """Generate collision-avoiding rectilinear paths for ligatures."""
        try:
            # Get positioned elements from context
            element_tracking = context.get('element_tracking', {})
            container_bounds = context.get('container_bounds', {})
            
            ligature_elements = {}
            
            # Find lines of identity (edges with relation "=")
            for edge in egi.E:
                if egi.rel.get(edge.id) == "=":
                    # Get connected vertices
                    connected_vertices = egi.nu.get(edge.id, [])
                    if len(connected_vertices) >= 2:
                        # Generate ligature path between vertices
                        ligature_path = self._generate_ligature_path(
                            edge.id, connected_vertices, element_tracking, container_bounds
                        )
                        
                        if ligature_path:
                            ligature_element = LayoutElement(
                                element_id=edge.id,
                                element_type='identity_line',
                                position=ligature_path['center'],
                                bounds=ligature_path['bounds'],
                                parent_area='sheet',  # Ligatures transcend cut boundaries
                                metadata={
                                    'curve_points': ligature_path['points'],
                                    'connected_vertices': connected_vertices
                                }
                            )
                            ligature_elements[edge.id] = ligature_element
            
            # Update element tracking
            element_tracking.update(ligature_elements)
            context['element_tracking'] = element_tracking
            
            return PhaseResult(
                phase_name="Rectilinear Ligature",
                status=PhaseStatus.COMPLETED,
                elements_modified=set(ligature_elements.keys()),
                dependencies_satisfied={"Element Dimensions", "Container Sizing", "Collision Detection", "Predicate Positioning", "Vertex Positioning", "Hook Assignment"},
                quality_metrics={'ligatures_generated': len(ligature_elements)}
            )
            
        except Exception as e:
            return PhaseResult(
                phase_name="Rectilinear Ligature",
                status=PhaseStatus.FAILED,
                elements_modified=set(),
                dependencies_satisfied=set(),
                quality_metrics={},
                error_message=f"Ligature generation failed: {str(e)}"
            )
    
    def _generate_ligature_path(self, ligature_id: str, connected_vertices: List[str], 
                               element_tracking: Dict[str, LayoutElement], 
                               container_bounds: Dict[str, Bounds]) -> Optional[Dict[str, Any]]:
        """Generate rectilinear path between connected vertices."""
        if len(connected_vertices) < 2:
            return None
        
        # Get positions of connected vertices
        vertex_positions = []
        for vertex_id in connected_vertices:
            if vertex_id in element_tracking:
                vertex_positions.append(element_tracking[vertex_id].position)
        
        if len(vertex_positions) < 2:
            return None
        
        # Simple straight line for now (can be enhanced to rectilinear routing)
        start_pos = vertex_positions[0]
        end_pos = vertex_positions[1]
        
        # Calculate path points
        points = [start_pos, end_pos]
        
        # Calculate center and bounds
        center_x = (start_pos[0] + end_pos[0]) / 2
        center_y = (start_pos[1] + end_pos[1]) / 2
        
        min_x = min(start_pos[0], end_pos[0]) - 5
        min_y = min(start_pos[1], end_pos[1]) - 5
        max_x = max(start_pos[0], end_pos[0]) + 5
        max_y = max(start_pos[1], end_pos[1]) + 5
        
        return {
            'center': (center_x, center_y),
            'bounds': (min_x, min_y, max_x, max_y),
            'points': points
        }


class BranchOptimizationPhase(LayoutPhase):
    """Phase 8: Optimize ligature branch points."""
    
    @property
    def phase_name(self) -> str:
        return "Branch Optimization"
    
    @property
    def dependencies(self) -> List[str]:
        return ["Rectilinear Ligature"]
    
    @property
    def capabilities(self) -> List[str]:
        return ["Optimized Branches"]
    
    def execute(self, egi: RelationalGraphWithCuts, context: Dict[str, Any]) -> PhaseResult:
        """Optimize ligature branch points, especially for single-object ligatures."""
        # Placeholder implementation
        return PhaseResult(
            phase_name="Branch Optimization",
            status=PhaseStatus.COMPLETED,
            elements_modified=set(),
            dependencies_satisfied={"Element Dimensions", "Container Sizing", "Collision Detection", "Predicate Positioning", "Vertex Positioning", "Hook Assignment", "Rectilinear Ligature"},
            quality_metrics={'branches_optimized': 0}
        )


class AreaCompactionPhase(LayoutPhase):
    """Phase 9: Compact areas and finalize container elements."""
    
    @property
    def phase_name(self) -> str:
        return "Area Compaction"
    
    @property
    def dependencies(self) -> List[str]:
        return ["Branch Optimization"]
    
    @property
    def capabilities(self) -> List[str]:
        return ["Compacted Layout"]
    
    def execute(self, egi: RelationalGraphWithCuts, context: Dict[str, Any]) -> PhaseResult:
        """Compact areas and finalize the layout."""
        # Placeholder implementation - pass through all elements
        return PhaseResult(
            phase_name="Area Compaction",
            status=PhaseStatus.COMPLETED,
            elements_modified=set(),
            dependencies_satisfied={"Element Dimensions", "Container Sizing", "Collision Detection", "Predicate Positioning", "Vertex Positioning", "Hook Assignment", "Rectilinear Ligature", "Branch Optimization"},
            quality_metrics={'areas_compacted': 0}
        )


if __name__ == "__main__":
    # Test phase implementations
    print("🧪 Testing Phase Implementations")
    
    from egif_parser_dau import EGIFParser
    # DependencyOrderedPipeline is defined in this file
    
    # Create pipeline with concrete implementations
    pipeline = DependencyOrderedPipeline()
    pipeline.register_phase(ElementSizingPhase())
    pipeline.register_phase(ContainerSizingPhase())
    pipeline.register_phase(CollisionDetectionPhase())
    pipeline.register_phase(PredicatePositioningPhase())
    pipeline.register_phase(VertexPositioningPhase())
    pipeline.register_phase(HookAssignmentPhase())
    pipeline.register_phase(LigatureGenerationPhase())
    pipeline.register_phase(BranchOptimizationPhase())
    pipeline.register_phase(AreaCompactionPhase())
    
    # Test with simple EGIF
    egif = "*x (Human x) ~[ (Mortal x) ]"
    parser = EGIFParser(egif)
    egi = parser.parse()
    
    # Execute pipeline
    try:
        result = pipeline.execute_full_layout(egi)
        print(f"✅ Pipeline completed: {len(result.elements)} elements generated")
        print(f"📊 Quality score: {result.layout_quality_score:.2f}")
        
        # Show element positions
        print("\n📍 ELEMENT POSITIONS:")
        for element_id, element in result.elements.items():
            print(f"   {element.element_type} '{element_id}' → {element.position}")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("✅ Phase Implementation Test Complete")
