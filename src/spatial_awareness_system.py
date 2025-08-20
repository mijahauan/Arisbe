#!/usr/bin/env python3
"""
Spatial Awareness System - Manages cut containment and element space allocation

This system maintains awareness of:
1. Available space within each cut/area
2. Space consumption by existing elements
3. Inside-out propagation of size changes
4. Spatial constraints for positioning and collision detection

Key Principle: Space requirements flow inside-out (deepest cuts → sheet)
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

from egi_core_dau import RelationalGraphWithCuts
from layout_types import LayoutElement, Bounds, Coordinate
from layout_utilities import ElementDimensions, ContainerInfo


class SpaceChangeType(Enum):
    """Types of space changes that can occur."""
    ELEMENT_ADDED = "element_added"
    ELEMENT_REMOVED = "element_removed"
    ELEMENT_RESIZED = "element_resized"
    ELEMENT_MOVED = "element_moved"
    CUT_RESIZED = "cut_resized"


@dataclass
class SpaceAllocation:
    """Tracks space allocation within a container."""
    container_id: str
    total_bounds: Bounds
    available_bounds: Bounds  # Total minus padding
    occupied_regions: List[Bounds] = field(default_factory=list)
    reserved_regions: List[Bounds] = field(default_factory=list)  # For ligature corridors
    padding: float = 30.0
    
    @property
    def available_area(self) -> float:
        """Calculate total available area."""
        x1, y1, x2, y2 = self.available_bounds
        return (x2 - x1) * (y2 - y1)
    
    @property
    def occupied_area(self) -> float:
        """Calculate total occupied area."""
        total = 0.0
        for bounds in self.occupied_regions:
            x1, y1, x2, y2 = bounds
            total += (x2 - x1) * (y2 - y1)
        return total
    
    @property
    def utilization_ratio(self) -> float:
        """Calculate space utilization ratio (0.0 to 1.0)."""
        if self.available_area == 0:
            return 1.0
        return min(1.0, self.occupied_area / self.available_area)
    
    def can_fit_element(self, element_dims: ElementDimensions) -> bool:
        """Check if element can fit in available space."""
        return (element_dims.total_width <= (self.available_bounds[2] - self.available_bounds[0]) and
                element_dims.total_height <= (self.available_bounds[3] - self.available_bounds[1]))


@dataclass
class SpaceRequirement:
    """Space requirement for a container based on its contents."""
    container_id: str
    min_width: float
    min_height: float
    preferred_width: float
    preferred_height: float
    content_elements: Set[str] = field(default_factory=set)
    child_containers: Set[str] = field(default_factory=set)
    
    @property
    def aspect_ratio(self) -> float:
        """Preferred aspect ratio."""
        return self.preferred_width / self.preferred_height if self.preferred_height > 0 else 1.0


class SpatialAwarenessSystem:
    """
    Manages spatial awareness throughout the layout pipeline.
    
    This system tracks:
    - Available space in each container
    - Space consumption by elements
    - Inside-out propagation of size changes
    - Spatial constraints for positioning
    """
    
    def __init__(self):
        self.space_allocations: Dict[str, SpaceAllocation] = {}
        self.space_requirements: Dict[str, SpaceRequirement] = {}
        self.containment_hierarchy: Dict[str, ContainerInfo] = {}
        self.elements: Dict[str, LayoutElement] = {}
        
    def initialize_from_containers(self, containers: Dict[str, ContainerInfo]):
        """Initialize spatial awareness from container hierarchy."""
        self.containment_hierarchy = containers.copy()
        
        # Create space allocations for each container
        for container_id, container in containers.items():
            if container.bounds:
                self._create_space_allocation(container_id, container.bounds)
    
    def _create_space_allocation(self, container_id: str, bounds: Bounds):
        """Create space allocation for a container."""
        x1, y1, x2, y2 = bounds
        padding = 30.0
        
        available_bounds = (
            x1 + padding,
            y1 + padding, 
            x2 - padding,
            y2 - padding
        )
        
        self.space_allocations[container_id] = SpaceAllocation(
            container_id=container_id,
            total_bounds=bounds,
            available_bounds=available_bounds,
            padding=padding
        )
    
    def register_element(self, element: LayoutElement):
        """Register an element and update space allocation."""
        self.elements[element.element_id] = element
        
        # Update space allocation for parent container
        if element.parent_area in self.space_allocations:
            allocation = self.space_allocations[element.parent_area]
            allocation.occupied_regions.append(element.bounds)
    
    def unregister_element(self, element_id: str):
        """Unregister an element and free its space."""
        if element_id in self.elements:
            element = self.elements[element_id]
            
            # Remove from space allocation
            if element.parent_area in self.space_allocations:
                allocation = self.space_allocations[element.parent_area]
                if element.bounds in allocation.occupied_regions:
                    allocation.occupied_regions.remove(element.bounds)
            
            del self.elements[element_id]
    
    def calculate_space_requirements(self) -> Dict[str, SpaceRequirement]:
        """Calculate space requirements for all containers inside-out."""
        requirements = {}
        
        # Process containers in dependency order (deepest first)
        processing_order = self._get_inside_out_order()
        
        for container_id in processing_order:
            container = self.containment_hierarchy[container_id]
            req = self._calculate_container_requirement(container)
            requirements[container_id] = req
        
        self.space_requirements = requirements
        return requirements
    
    def _calculate_container_requirement(self, container: ContainerInfo) -> SpaceRequirement:
        """Calculate space requirement for a single container."""
        
        # Collect dimensions of direct elements
        element_width = 0.0
        element_height = 0.0
        element_count = 0
        
        for element_id in container.element_ids:
            if element_id in self.elements:
                element = self.elements[element_id]
                bounds = element.bounds
                element_width = max(element_width, bounds[2] - bounds[0])
                element_height += (bounds[3] - bounds[1]) + 10  # Vertical stacking with spacing
                element_count += 1
        
        # Collect dimensions of child containers
        child_width = 0.0
        child_height = 0.0
        
        for child_id in container.children_ids:
            if child_id in self.space_requirements:
                child_req = self.space_requirements[child_id]
                child_width = max(child_width, child_req.preferred_width)
                child_height += child_req.preferred_height + 20  # Vertical stacking with spacing
        
        # Calculate total requirements
        content_width = max(element_width, child_width)
        content_height = element_height + child_height
        
        # Add padding and minimum sizes
        padding = 60.0  # 30px on each side
        min_width = max(100.0, content_width + padding)
        min_height = max(70.0, content_height + padding)
        
        # Preferred size includes growth space
        preferred_width = min_width * 1.2  # 20% growth space
        preferred_height = min_height * 1.1  # 10% growth space
        
        return SpaceRequirement(
            container_id=container.container_id,
            min_width=min_width,
            min_height=min_height,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            content_elements=container.element_ids.copy(),
            child_containers=container.children_ids.copy()
        )
    
    def _get_inside_out_order(self) -> List[str]:
        """Get containers in inside-out processing order (deepest first)."""
        order = []
        visited = set()
        
        def visit_depth_first(container_id: str):
            if container_id in visited:
                return
            visited.add(container_id)
            
            container = self.containment_hierarchy[container_id]
            
            # Visit children first (deeper cuts)
            for child_id in container.children_ids:
                visit_depth_first(child_id)
            
            # Then visit this container
            order.append(container_id)
        
        # Find root (sheet) and start traversal
        for container_id, container in self.containment_hierarchy.items():
            if container.parent_id is None:
                visit_depth_first(container_id)
                break
        
        return order
    
    def propagate_size_change(self, container_id: str, 
                            new_requirement: SpaceRequirement) -> List[str]:
        """
        Propagate size change from container up to parents.
        Returns list of containers that need resizing.
        """
        affected_containers = []
        current_id = container_id
        
        while current_id is not None:
            container = self.containment_hierarchy.get(current_id)
            if not container:
                break
            
            # Update space requirement
            self.space_requirements[current_id] = new_requirement
            affected_containers.append(current_id)
            
            # Check if parent needs resizing
            parent_id = container.parent_id
            if parent_id and parent_id in self.space_requirements:
                parent_req = self.space_requirements[parent_id]
                
                # Recalculate parent requirement based on new child size
                updated_parent_req = self._calculate_container_requirement(
                    self.containment_hierarchy[parent_id]
                )
                
                # If parent size needs to change, continue propagation
                if (updated_parent_req.min_width > parent_req.min_width or
                    updated_parent_req.min_height > parent_req.min_height):
                    new_requirement = updated_parent_req
                    current_id = parent_id
                else:
                    break
            else:
                break
        
        return affected_containers
    
    def get_available_positions(self, container_id: str, 
                              element_dims: ElementDimensions) -> List[Coordinate]:
        """Get list of available positions for an element in a container."""
        if container_id not in self.space_allocations:
            return []
        
        allocation = self.space_allocations[container_id]
        
        if not allocation.can_fit_element(element_dims):
            return []
        
        positions = []
        x1, y1, x2, y2 = allocation.available_bounds
        
        # Grid-based position generation
        step_x = max(20, element_dims.total_width + 10)
        step_y = max(20, element_dims.total_height + 10)
        
        y = y1 + element_dims.total_height // 2
        while y + element_dims.total_height // 2 <= y2:
            x = x1 + element_dims.total_width // 2
            while x + element_dims.total_width // 2 <= x2:
                # Check if position conflicts with occupied regions
                proposed_bounds = (
                    x - element_dims.total_width // 2,
                    y - element_dims.total_height // 2,
                    x + element_dims.total_width // 2,
                    y + element_dims.total_height // 2
                )
                
                if not self._bounds_overlap_any(proposed_bounds, allocation.occupied_regions):
                    positions.append((x, y))
                
                x += step_x
            y += step_y
        
        return positions
    
    def _bounds_overlap_any(self, bounds: Bounds, region_list: List[Bounds]) -> bool:
        """Check if bounds overlap with any region in the list."""
        for region in region_list:
            if self._bounds_overlap(bounds, region):
                return True
        return False
    
    def _bounds_overlap(self, bounds1: Bounds, bounds2: Bounds) -> bool:
        """Check if two bounding rectangles overlap."""
        x1_min, y1_min, x1_max, y1_max = bounds1
        x2_min, y2_min, x2_max, y2_max = bounds2
        
        return not (x1_max <= x2_min or x2_max <= x1_min or 
                   y1_max <= y2_min or y2_max <= y1_min)
    
    def reserve_ligature_corridor(self, container_id: str, corridor_bounds: Bounds):
        """Reserve space for ligature routing."""
        if container_id in self.space_allocations:
            allocation = self.space_allocations[container_id]
            allocation.reserved_regions.append(corridor_bounds)
    
    def get_utilization_report(self) -> Dict[str, Dict[str, float]]:
        """Get space utilization report for all containers."""
        report = {}
        
        for container_id, allocation in self.space_allocations.items():
            report[container_id] = {
                'utilization_ratio': allocation.utilization_ratio,
                'available_area': allocation.available_area,
                'occupied_area': allocation.occupied_area,
                'num_elements': len(allocation.occupied_regions)
            }
        
        return report


if __name__ == "__main__":
    # Test spatial awareness system
    print("🧪 Testing Spatial Awareness System")
    
    from layout_utilities import ContainerHierarchy, ElementMeasurement
    from egif_parser_dau import EGIFParser
    
    # Test with simple EGIF
    egif = "*x (Human x) ~[ (Mortal x) ]"
    parser = EGIFParser(egif)
    egi = parser.parse()
    
    # Extract containers and measure elements
    hierarchy = ContainerHierarchy()
    containers = hierarchy.extract_containment_hierarchy(egi)
    
    measurer = ElementMeasurement()
    dimensions = measurer.measure_all_elements(egi)
    
    # Initialize spatial awareness
    spatial_system = SpatialAwarenessSystem()
    
    # Set container bounds (mock)
    for container_id, container in containers.items():
        if container.parent_id is None:
            container.bounds = (0, 0, 800, 600)  # Sheet
        else:
            container.bounds = (100, 100, 300, 200)  # Cut
    
    spatial_system.initialize_from_containers(containers)
    
    # Calculate space requirements
    requirements = spatial_system.calculate_space_requirements()
    
    print(f"📊 Space Requirements:")
    for container_id, req in requirements.items():
        print(f"   {container_id}: {req.preferred_width:.0f}x{req.preferred_height:.0f}")
        print(f"      Elements: {len(req.content_elements)}, Children: {len(req.child_containers)}")
    
    # Get utilization report
    report = spatial_system.get_utilization_report()
    print(f"\n📈 Space Utilization:")
    for container_id, metrics in report.items():
        print(f"   {container_id}: {metrics['utilization_ratio']:.1%} utilized")
        print(f"      Available: {metrics['available_area']:.0f}, Occupied: {metrics['occupied_area']:.0f}")
    
    print("✅ Spatial Awareness System Test Complete")
