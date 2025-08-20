#!/usr/bin/env python3
"""
Spatial Constraint Integration - Integrates spatial awareness into the pipeline

This module bridges the spatial awareness system with the layout pipeline,
ensuring that positioning and collision-avoidance maintain proper awareness
of cut containment and space allocation.

Key Integration Points:
1. Container sizing uses spatial requirements
2. Collision detection respects spatial exclusion zones  
3. Element positioning considers available space
4. Size changes propagate inside-out through hierarchy
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass

from egi_core_dau import RelationalGraphWithCuts
from layout_types import LayoutResult, LayoutElement, Bounds, Coordinate
# Define PhaseResult and PhaseStatus locally since layout_pipeline_design was removed
from enum import Enum
from dataclasses import dataclass
from typing import Set, Dict, Any, Optional

class PhaseStatus(Enum):
    PENDING = "pending"
    READY = "ready" 
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class PhaseResult:
    phase_name: str
    status: PhaseStatus
    elements_modified: Set[str]
    dependencies_satisfied: Set[str]
    quality_metrics: Dict[str, Any]
    error_message: Optional[str] = None
from layout_utilities import ElementDimensions, ContainerInfo
from spatial_awareness_system import SpatialAwarenessSystem, SpaceRequirement, SpaceAllocation


class SpatiallyAwareContainerSizing:
    """Container sizing that integrates with spatial awareness system."""
    
    def __init__(self, spatial_system: SpatialAwarenessSystem):
        self.spatial_system = spatial_system
        self.cut_padding = 30.0
    
    def size_containers_with_spatial_awareness(self, 
                                             containers: Dict[str, ContainerInfo],
                                             elements: Dict[str, LayoutElement]) -> Dict[str, Bounds]:
        """Size containers using relative coordinate system with proportional allocation."""
        
        # Step 1: Calculate nesting depth and proportional areas
        depth_allocation = self._calculate_proportional_areas(containers)
        
        # Step 2: Initialize containers with proportional bounds
        container_bounds = self._initialize_proportional_containers(containers, depth_allocation)
        
        # Step 3: Assess content size requirements (leaf-first)
        content_requirements = self._assess_content_requirements(containers, elements)
        
        # Step 4: Apply dynamic shrinking based on actual content
        container_bounds = self._apply_content_based_shrinking(
            containers, container_bounds, content_requirements
        )
        
        # Step 5: Position elements within their relative coordinate spaces
        positioned_elements = self._position_elements_relatively(
            containers, elements, container_bounds
        )
        
        # Update elements with relative positions
        elements.update(positioned_elements)
        
        # Update container objects with final bounds
        for container_id, bounds in container_bounds.items():
            if container_id in containers:
                containers[container_id].bounds = bounds
        
        return container_bounds
    
    def _calculate_proportional_areas(self, containers: Dict[str, ContainerInfo]) -> Dict[str, float]:
        """Calculate proportional area allocation based on nesting depth."""
        # Calculate max depth
        max_depth = 0
        depths = {}
        
        def get_depth(container_id: str) -> int:
            if container_id in depths:
                return depths[container_id]
            
            container = containers[container_id]
            if container.parent_id is None:
                depth = 0
            else:
                depth = get_depth(container.parent_id) + 1
            
            depths[container_id] = depth
            return depth
        
        for container_id in containers:
            depth = get_depth(container_id)
            max_depth = max(max_depth, depth)
        
        # Allocate proportional areas: deeper containers get smaller allocation
        # Sheet gets remaining area after all cuts allocated
        allocation = {}
        if max_depth == 0:
            # Only sheet
            for container_id in containers:
                allocation[container_id] = 1.0
        else:
            # Reserve 4% for sheet, distribute 96% among cuts
            cut_area = 0.96
            area_per_level = cut_area / max_depth
            
            for container_id, depth in depths.items():
                if depth == 0:  # Sheet
                    allocation[container_id] = 0.04
                else:  # Cuts get proportional allocation
                    allocation[container_id] = area_per_level
        
        return allocation
    
    def _initialize_proportional_containers(self, 
                                          containers: Dict[str, ContainerInfo],
                                          depth_allocation: Dict[str, float]) -> Dict[str, Bounds]:
        """Initialize containers with proportional bounds in relative coordinates."""
        container_bounds = {}
        
        # Use unit square (0,0,1,1) as base coordinate system
        base_width = 1.0
        base_height = 1.0
        
        # Find sheet (root container)
        sheet_id = None
        for container_id, container in containers.items():
            if container.parent_id is None:
                sheet_id = container_id
                container_bounds[container_id] = (0.0, 0.0, base_width, base_height)
                break
        
        # Position cuts within their parents using proportional allocation
        for container_id, container in containers.items():
            if container_id == sheet_id:
                continue
            
            parent_bounds = container_bounds.get(container.parent_id)
            if not parent_bounds:
                continue
            
            px, py, pw, ph = parent_bounds
            allocation = depth_allocation[container_id]
            
            # Calculate proportional size within parent
            # Use sqrt for area-to-dimension conversion
            size_factor = allocation ** 0.5
            
            # Center the cut within parent with proportional size
            cut_width = (pw - px) * size_factor
            cut_height = (ph - py) * size_factor
            
            # Center positioning
            cut_x = px + ((pw - px) - cut_width) / 2
            cut_y = py + ((ph - py) - cut_height) / 2
            
            container_bounds[container_id] = (cut_x, cut_y, cut_x + cut_width, cut_y + cut_height)
        
        return container_bounds
    
    def _assess_content_requirements(self, 
                                   containers: Dict[str, ContainerInfo],
                                   elements: Dict[str, LayoutElement]) -> Dict[str, float]:
        """Assess actual content size requirements for each container."""
        requirements = {}
        
        for container_id, container in containers.items():
            content_size = 0.0
            
            # Sum up element sizes in this container
            for element_id in container.element_ids:
                if element_id in elements:
                    # Estimate element size (relative units)
                    element = elements[element_id]
                    if element.element_type == 'predicate':
                        # Predicates need space for text
                        content_size += 0.1  # 10% of unit space per predicate
                    elif element.element_type == 'vertex':
                        # Vertices are smaller
                        content_size += 0.05  # 5% of unit space per vertex
            
            # Minimum size even for empty containers
            requirements[container_id] = max(0.02, content_size)  # At least 2%
        
        return requirements
    
    def _apply_content_based_shrinking(self, 
                                     containers: Dict[str, ContainerInfo],
                                     container_bounds: Dict[str, Bounds],
                                     content_requirements: Dict[str, float]) -> Dict[str, Bounds]:
        """Shrink containers based on actual content requirements."""
        adjusted_bounds = container_bounds.copy()
        
        # Process from deepest to shallowest
        processing_order = self._get_leaf_to_root_order(containers)
        
        for container_id in processing_order:
            if container_id not in content_requirements:
                continue
            
            current_bounds = adjusted_bounds[container_id]
            cx, cy, cw, ch = current_bounds
            current_area = (cw - cx) * (ch - cy)
            required_area = content_requirements[container_id]
            
            # Shrink if current area is much larger than required
            if current_area > required_area * 2:  # Only shrink if >2x larger
                shrink_factor = (required_area * 1.5) / current_area  # Leave 50% buffer
                shrink_factor = max(0.3, min(1.0, shrink_factor))  # Limit shrinking
                
                # Apply shrinking while maintaining center position
                center_x = (cx + cw) / 2
                center_y = (cy + ch) / 2
                new_width = (cw - cx) * shrink_factor
                new_height = (ch - cy) * shrink_factor
                
                new_bounds = (
                    center_x - new_width / 2,
                    center_y - new_height / 2,
                    center_x + new_width / 2,
                    center_y + new_height / 2
                )
                
                adjusted_bounds[container_id] = new_bounds
        
        return adjusted_bounds
    
    def _position_elements_relatively(self, 
                                    containers: Dict[str, ContainerInfo],
                                    elements: Dict[str, LayoutElement],
                                    container_bounds: Dict[str, Bounds]) -> Dict[str, LayoutElement]:
        """Position elements within their containers using relative coordinates."""
        positioned_elements = {}
        
        for container_id, container in containers.items():
            if container_id not in container_bounds:
                continue
            
            container_bound = container_bounds[container_id]
            cx, cy, cw, ch = container_bound
            
            # Position elements within this container
            element_count = len(container.element_ids)
            if element_count == 0:
                continue
            
            # Simple grid layout within container
            cols = max(1, int(element_count ** 0.5))
            rows = (element_count + cols - 1) // cols
            
            for i, element_id in enumerate(container.element_ids):
                if element_id not in elements:
                    continue
                
                element = elements[element_id]
                
                # Calculate grid position
                col = i % cols
                row = i // cols
                
                # Relative position within container (with padding)
                padding = 0.1  # 10% padding
                usable_width = (cw - cx) * (1 - 2 * padding)
                usable_height = (ch - cy) * (1 - 2 * padding)
                
                rel_x = cx + (cw - cx) * padding + (col + 0.5) * usable_width / cols
                rel_y = cy + (ch - cy) * padding + (row + 0.5) * usable_height / rows
                
                # Element bounds (small relative size)
                element_width = usable_width / cols * 0.8
                element_height = usable_height / rows * 0.8
                
                positioned_element = LayoutElement(
                    element_id=element.element_id,
                    element_type=element.element_type,
                    position=(rel_x, rel_y),
                    bounds=(
                        rel_x - element_width / 2,
                        rel_y - element_height / 2,
                        rel_x + element_width / 2,
                        rel_y + element_height / 2
                    ),
                    parent_area=container_id
                )
                
                positioned_elements[element_id] = positioned_element
        
        return positioned_elements
    
    def _initialize_all_containers(self, containers: Dict[str, ContainerInfo]) -> Dict[str, Bounds]:
        """Initialize all containers with minimal bounds, positioning siblings."""
        container_bounds = {}
        
        # First pass: identify sheet
        sheet_id = None
        for container_id, container in containers.items():
            if container.parent_id is None:
                sheet_id = container_id
                container_bounds[container_id] = (0, 0, 800, 600)
                break
        
        # Second pass: position all other containers
        sibling_positions = {}  # parent_id -> next_x_offset
        
        for container_id, container in containers.items():
            if container_id == sheet_id:
                continue
                
            parent_id = container.parent_id
            if parent_id not in sibling_positions:
                sibling_positions[parent_id] = 0
            
            # Position siblings with horizontal spacing
            base_x = 120 + (sibling_positions[parent_id] * 120)  # 120px spacing
            base_y = 120
            
            bounds = (base_x, base_y, base_x + 100, base_y + 70)
            container_bounds[container_id] = bounds
            
            sibling_positions[parent_id] += 1
        
        return container_bounds
    
    def _get_leaf_to_root_order(self, containers: Dict[str, ContainerInfo]) -> List[str]:
        """Get processing order from deepest containers to root."""
        # Calculate depth for each container
        depths = {}
        
        def calculate_depth(container_id: str) -> int:
            if container_id in depths:
                return depths[container_id]
            
            container = containers[container_id]
            if container.parent_id is None:
                depth = 0
            else:
                depth = calculate_depth(container.parent_id) + 1
            
            depths[container_id] = depth
            return depth
        
        # Calculate depths for all containers
        for container_id in containers:
            calculate_depth(container_id)
        
        # Sort by depth (deepest first)
        return sorted(containers.keys(), key=lambda cid: depths[cid], reverse=True)
    
    def _position_element_in_container(self, 
                                     element: LayoutElement,
                                     container_id: str,
                                     container_bounds: Dict[str, Bounds],
                                     all_elements: Dict[str, LayoutElement]) -> LayoutElement:
        """Position element within container, avoiding collisions."""
        
        container_bound = container_bounds[container_id]
        cx, cy, cw, ch = container_bound
        padding = 20
        
        # Get existing elements in this container
        existing_elements = [e for e in all_elements.values() 
                           if hasattr(e, 'parent_area') and e.parent_area == container_id]
        
        # Find collision-free position
        element_width = getattr(element, 'width', 50)
        element_height = getattr(element, 'height', 30)
        
        # Try grid positions
        for y_offset in range(padding, int(ch - cy - element_height - padding), 20):
            for x_offset in range(padding, int(cw - cx - element_width - padding), 20):
                test_x = cx + x_offset + element_width // 2
                test_y = cy + y_offset + element_height // 2
                
                test_bounds = (
                    test_x - element_width // 2,
                    test_y - element_height // 2,
                    test_x + element_width // 2,
                    test_y + element_height // 2
                )
                
                # Check for collisions
                collision = False
                for existing in existing_elements:
                    if hasattr(existing, 'bounds') and self._bounds_overlap(test_bounds, existing.bounds):
                        collision = True
                        break
                
                if not collision:
                    # Create positioned element
                    return LayoutElement(
                        element_id=element.element_id,
                        element_type=element.element_type,
                        position=(test_x, test_y),
                        bounds=test_bounds,
                        parent_area=container_id
                    )
        
        # Fallback position
        return LayoutElement(
            element_id=element.element_id,
            element_type=element.element_type,
            position=(cx + 50, cy + 50),
            bounds=(cx + 25, cy + 35, cx + 75, cy + 65),
            parent_area=container_id
        )
    
    def _expand_parents_for_element(self, 
                                  element: LayoutElement,
                                  container_id: str,
                                  containers: Dict[str, ContainerInfo],
                                  container_bounds: Dict[str, Bounds]):
        """Expand all parent containers to accommodate the new element."""
        
        current_container_id = container_id
        
        while current_container_id is not None:
            current_bounds = container_bounds[current_container_id]
            cx, cy, cw, ch = current_bounds
            
            # Check if element extends beyond current container
            ex, ey, ew, eh = element.bounds
            padding = self.cut_padding
            
            # Calculate required expansion
            new_cx = min(cx, ex - padding)
            new_cy = min(cy, ey - padding)
            new_cw = max(cw, ew + padding)
            new_ch = max(ch, eh + padding)
            
            # Update container bounds if expansion needed
            if (new_cx, new_cy, new_cw, new_ch) != current_bounds:
                container_bounds[current_container_id] = (new_cx, new_cy, new_cw, new_ch)
            
            # Move up to parent
            container = containers.get(current_container_id)
            current_container_id = container.parent_id if container else None
    
    def _validate_current_state(self, 
                              container_bounds: Dict[str, Bounds],
                              elements: Dict[str, LayoutElement]) -> bool:
        """Validate current state for containment and collision constraints."""
        
        # Check all elements are within their containers
        for element in elements.values():
            if hasattr(element, 'parent_area') and element.parent_area in container_bounds:
                container_bound = container_bounds[element.parent_area]
                if not self._element_within_container(element.bounds, container_bound):
                    return False
        
        # Check no element collisions within same container
        container_elements = {}
        for element in elements.values():
            if hasattr(element, 'parent_area'):
                container_elements.setdefault(element.parent_area, []).append(element)
        
        for container_id, elems in container_elements.items():
            for i, elem1 in enumerate(elems):
                for j, elem2 in enumerate(elems):
                    if i < j and self._bounds_overlap(elem1.bounds, elem2.bounds):
                        return False
        
        return True
    
    def _element_within_container(self, element_bounds: Bounds, container_bounds: Bounds) -> bool:
        """Check if element is fully within container."""
        ex, ey, ew, eh = element_bounds
        cx, cy, cw, ch = container_bounds
        return cx <= ex and cy <= ey and ew <= cw and eh <= ch
    
    def _validate_container_assignment(self, 
                                     proposed_bounds: Bounds, 
                                     existing_bounds: Dict[str, Bounds],
                                     container_id: str) -> bool:
        """Validate that proposed bounds don't collide with existing assignments."""
        
        for existing_id, existing_bound in existing_bounds.items():
            if existing_id != container_id:
                if self._bounds_overlap(proposed_bounds, existing_bound):
                    return False
        return True
    
    def _resolve_container_collision(self, 
                                   proposed_bounds: Bounds,
                                   existing_bounds: Dict[str, Bounds],
                                   container: ContainerInfo,
                                   requirements: Dict[str, SpaceRequirement]) -> Bounds:
        """Resolve collision by finding non-overlapping position."""
        
        px, py, pw, ph = proposed_bounds
        width = pw - px
        height = ph - py
        
        # Try positions with increasing offset
        for offset in range(0, 200, 20):
            # Try horizontal offset first
            test_bounds = (px + offset, py, px + offset + width, py + height)
            if self._validate_container_assignment(test_bounds, existing_bounds, container.container_id):
                return test_bounds
            
            # Try vertical offset
            test_bounds = (px, py + offset, px + width, py + offset + height)
            if self._validate_container_assignment(test_bounds, existing_bounds, container.container_id):
                return test_bounds
        
        # If no position found, use original with warning
        return proposed_bounds
    
    def _calculate_container_bounds(self, 
                                  container_id: str,
                                  container: ContainerInfo,
                                  requirements: Dict[str, SpaceRequirement],
                                  existing_bounds: Dict[str, Bounds]) -> Bounds:
        """Calculate container bounds that properly contain all children."""
        
        # Use spatial requirements as base size
        req = requirements.get(container_id)
        if req:
            base_width = req.preferred_width
            base_height = req.preferred_height
        else:
            base_width = 200
            base_height = 170
        
        # Calculate initial bounds based on parent positioning
        if container.parent_id and container.parent_id in existing_bounds:
            parent_bounds = existing_bounds[container.parent_id]
            bounds = self._position_within_parent_space_new(
                container_id, base_width, base_height, parent_bounds, existing_bounds
            )
        else:
            # Root container or fallback
            bounds = (100, 100, 100 + base_width, 100 + base_height)
        
        # Ensure children will fit if they exist
        if container.children_ids:
            # Reserve space for children with proper spacing
            child_count = len(container.children_ids)
            min_child_width = 100
            min_child_height = 70
            padding = self.cut_padding
            
            # Calculate required space for children
            required_width = max(base_width, (child_count * min_child_width) + ((child_count + 1) * padding))
            required_height = max(base_height, min_child_height + (2 * padding))
            
            # Expand bounds if needed
            x, y, _, _ = bounds
            bounds = (x, y, x + required_width, y + required_height)
        
        return bounds
    
    def _position_within_parent_space_new(self, 
                                        container_id: str,
                                        width: float,
                                        height: float,
                                        parent_bounds: Bounds,
                                        existing_bounds: Dict[str, Bounds]) -> Bounds:
        """Position container within parent with proper spacing."""
        
        px, py, pw, ph = parent_bounds
        padding = 20
        
        # Count existing siblings
        sibling_count = len([b for b in existing_bounds.values() 
                           if self._is_within_bounds(b, parent_bounds)])
        
        # Position siblings side by side with spacing
        x = px + padding + (sibling_count * (width + padding))
        y = py + padding
        
        # Ensure we don't exceed parent bounds
        if x + width > pw - padding:
            # Wrap to next row
            x = px + padding
            y = py + padding + 80
        
        return (x, y, x + width, y + height)
    
    def _position_within_parent_bounds(self, 
                                     child_bounds: Bounds,
                                     parent_bounds: Bounds,
                                     existing_bounds: Dict[str, Bounds]) -> Bounds:
        """Position child bounds within parent, avoiding siblings."""
        
        px, py, pw, ph = parent_bounds
        cx, cy, cw, ch = child_bounds
        child_width = cw - cx
        child_height = ch - cy
        
        # Find non-overlapping position within parent
        padding = 20
        best_x = px + padding
        best_y = py + padding
        
        # Simple horizontal layout for siblings
        sibling_count = len([b for b in existing_bounds.values() 
                           if self._is_within_bounds(b, parent_bounds)])
        
        if sibling_count > 0:
            best_x = px + padding + (sibling_count * (child_width + 20))
        
        # Ensure we stay within parent bounds
        if best_x + child_width > pw - padding:
            best_x = px + padding
            best_y = py + padding + 80  # Move to next row
        
        return (best_x, best_y, best_x + child_width, best_y + child_height)
    
    def _is_within_bounds(self, inner_bounds: Bounds, outer_bounds: Bounds) -> bool:
        """Check if inner bounds are within outer bounds."""
        ix, iy, iw, ih = inner_bounds
        ox, oy, ow, oh = outer_bounds
        return ox <= ix and oy <= iy and iw <= ow and ih <= oh
    
    def _position_within_parent_space(self, 
                                    container_id: str,
                                    requirement: SpaceRequirement,
                                    parent_bounds: Bounds,
                                    existing_containers: Dict[str, Bounds]) -> Bounds:
        """Position container within parent's available space, avoiding siblings."""
        
        parent_x, parent_y, parent_w, parent_h = parent_bounds
        padding = self.cut_padding
        
        # Available area within parent (minus padding)
        available_x = parent_x + padding
        available_y = parent_y + padding  
        available_w = parent_w - parent_x - (2 * padding)
        available_h = parent_h - parent_y - (2 * padding)
        
        # Simple side-by-side positioning for sibling cuts
        sibling_count = len([bounds for bounds in existing_containers.values() 
                           if self._is_sibling_container(bounds, parent_bounds)])
        
        # Position siblings horizontally with spacing
        sibling_width = max(100, requirement.preferred_width)
        sibling_spacing = 20
        
        x = available_x + (sibling_count * (sibling_width + sibling_spacing))
        y = available_y + 20  # Small vertical offset
        
        # Ensure we don't exceed parent bounds
        if x + sibling_width > parent_x + parent_w - padding:
            # Wrap to next row
            x = available_x
            y = available_y + 80  # Move to next row
        
        proposed_bounds = (
            x, y, 
            x + sibling_width,
            y + max(70, requirement.preferred_height)
        )
        
        return proposed_bounds
    
    def _is_sibling_container(self, bounds: Bounds, parent_bounds: Bounds) -> bool:
        """Check if bounds represent a container within the parent."""
        px, py, pw, ph = parent_bounds
        bx, by, bw, bh = bounds
        
        # Container is inside parent if all corners are within parent bounds
        return (px <= bx and py <= by and bw <= pw and bh <= ph)
    
    def _bounds_overlap(self, bounds1: Bounds, bounds2: Bounds) -> bool:
        """Check if two bounding rectangles overlap."""
        x1_min, y1_min, x1_max, y1_max = bounds1
        x2_min, y2_min, x2_max, y2_max = bounds2
        
        return not (x1_max <= x2_min or x2_max <= x1_min or 
                   y1_max <= y2_min or y2_max <= y1_min)
    
    def _calculate_overlap_area(self, bounds1: Bounds, bounds2: Bounds) -> float:
        """Calculate overlapping area between two bounds."""
        if not self._bounds_overlap(bounds1, bounds2):
            return 0.0
        
        x1_min, y1_min, x1_max, y1_max = bounds1
        x2_min, y2_min, x2_max, y2_max = bounds2
        
        overlap_x = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        overlap_y = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        
        return overlap_x * overlap_y
    
    def _get_inside_out_order(self, containers: Dict[str, ContainerInfo]) -> List[str]:
        """Get containers in inside-out processing order."""
        order = []
        visited = set()
        
        def visit(container_id: str):
            if container_id in visited:
                return
            visited.add(container_id)
            
            container = containers[container_id]
            for child_id in container.children_ids:
                visit(child_id)
            
            order.append(container_id)
        
        # Find sheet and start traversal
        for container_id, container in containers.items():
            if container.parent_id is None:
                visit(container_id)
                break
        
        return order


class SpatiallyAwareCollisionDetection:
    """Collision detection that respects spatial exclusion zones."""
    
    def __init__(self, spatial_system: SpatialAwarenessSystem):
        self.spatial_system = spatial_system
    
    def find_collision_free_position_with_exclusion(self,
                                                   container_id: str,
                                                   element_dims: ElementDimensions,
                                                   existing_elements: List[LayoutElement]) -> Optional[Coordinate]:
        """Find position that avoids collisions AND respects spatial exclusion zones."""
        
        # Get available positions from spatial system
        available_positions = self.spatial_system.get_available_positions(
            container_id, element_dims
        )
        
        if not available_positions:
            return None
        
        # Filter positions that don't collide with existing elements
        for position in available_positions:
            proposed_bounds = (
                position[0] - element_dims.total_width // 2,
                position[1] - element_dims.total_height // 2,
                position[0] + element_dims.total_width // 2,
                position[1] + element_dims.total_height // 2
            )
            
            # Check collision with existing elements
            collision = False
            for element in existing_elements:
                if self._bounds_overlap(proposed_bounds, element.bounds):
                    collision = True
                    break
            
            # Also check exclusion from child cuts (spatial exclusion principle)
            if not collision and self._violates_spatial_exclusion(container_id, proposed_bounds):
                collision = True
            
            if not collision:
                return position
        
        return None
    
    def _violates_spatial_exclusion(self, container_id: str, proposed_bounds: Bounds) -> bool:
        """Check if position violates spatial exclusion from child cuts."""
        
        # Get container info
        container = self.spatial_system.containment_hierarchy.get(container_id)
        if not container:
            return False
        
        # Check if proposed bounds overlap with any child container bounds
        for child_id in container.children_ids:
            child_allocation = self.spatial_system.space_allocations.get(child_id)
            if child_allocation:
                # Child cuts create exclusion zones - parent elements cannot overlap
                if self._bounds_overlap(proposed_bounds, child_allocation.total_bounds):
                    return True
        
        return False
    
    def _bounds_overlap(self, bounds1: Bounds, bounds2: Bounds) -> bool:
        """Check if two bounding rectangles overlap."""
        x1_min, y1_min, x1_max, y1_max = bounds1
        x2_min, y2_min, x2_max, y2_max = bounds2
        
        return not (x1_max <= x2_min or x2_max <= x1_min or 
                   y1_max <= y2_min or y2_max <= y1_min)


class SpatialChangePropagatior:
    """Handles inside-out propagation of spatial changes."""
    
    def __init__(self, spatial_system: SpatialAwarenessSystem):
        self.spatial_system = spatial_system
    
    def handle_element_addition(self, element: LayoutElement) -> List[str]:
        """Handle addition of new element and propagate size changes."""
        
        # Register element with spatial system
        self.spatial_system.register_element(element)
        
        # Check if parent container needs resizing
        container_id = element.parent_area
        container = self.spatial_system.containment_hierarchy.get(container_id)
        
        if container:
            # Recalculate space requirement for container
            new_requirement = self.spatial_system._calculate_container_requirement(container)
            
            # Propagate size change up the hierarchy
            affected_containers = self.spatial_system.propagate_size_change(
                container_id, new_requirement
            )
            
            return affected_containers
        
        return []
    
    def handle_element_removal(self, element_id: str) -> List[str]:
        """Handle removal of element and propagate size changes."""
        
        element = self.spatial_system.elements.get(element_id)
        if not element:
            return []
        
        container_id = element.parent_area
        
        # Unregister element
        self.spatial_system.unregister_element(element_id)
        
        # Recalculate and propagate size changes
        container = self.spatial_system.containment_hierarchy.get(container_id)
        if container:
            new_requirement = self.spatial_system._calculate_container_requirement(container)
            affected_containers = self.spatial_system.propagate_size_change(
                container_id, new_requirement
            )
            return affected_containers
        
        return []
    
    def handle_element_resize(self, element_id: str, new_dimensions: ElementDimensions) -> List[str]:
        """Handle element resize and propagate changes."""
        
        element = self.spatial_system.elements.get(element_id)
        if not element:
            return []
        
        # Update element bounds based on new dimensions
        pos = element.position
        new_bounds = (
            pos[0] - new_dimensions.total_width // 2,
            pos[1] - new_dimensions.total_height // 2,
            pos[0] + new_dimensions.total_width // 2,
            pos[1] + new_dimensions.total_height // 2
        )
        
        # Update element
        element.bounds = new_bounds
        
        # Update spatial allocation
        container_id = element.parent_area
        allocation = self.spatial_system.space_allocations.get(container_id)
        if allocation:
            # Remove old bounds and add new bounds
            if element.bounds in allocation.occupied_regions:
                allocation.occupied_regions.remove(element.bounds)
            allocation.occupied_regions.append(new_bounds)
        
        # Propagate size changes
        container = self.spatial_system.containment_hierarchy.get(container_id)
        if container:
            new_requirement = self.spatial_system._calculate_container_requirement(container)
            affected_containers = self.spatial_system.propagate_size_change(
                container_id, new_requirement
            )
            return affected_containers
        
        return []


if __name__ == "__main__":
    # Test spatial constraint integration
    print("🧪 Testing Spatial Constraint Integration")
    
    from layout_utilities import ContainerHierarchy, ElementMeasurement
    from egif_parser_dau import EGIFParser
    
    # Test with simple EGIF
    egif = "*x (Human x) ~[ (Mortal x) ]"
    parser = EGIFParser(egif)
    egi = parser.parse()
    
    # Set up spatial awareness
    spatial_system = SpatialAwarenessSystem()
    hierarchy = ContainerHierarchy()
    containers = hierarchy.extract_containment_hierarchy(egi)
    
    # Test spatially aware container sizing
    spatially_aware_sizer = SpatiallyAwareContainerSizing(spatial_system)
    container_bounds = spatially_aware_sizer.size_containers_with_spatial_awareness(
        containers, {}
    )
    
    print(f"📦 Spatially Aware Container Bounds:")
    for container_id, bounds in container_bounds.items():
        print(f"   {container_id}: {bounds}")
    
    # Test spatial exclusion collision detection
    collision_detector = SpatiallyAwareCollisionDetection(spatial_system)
    
    # Mock element dimensions
    from layout_utilities import ElementDimensions
    test_dims = ElementDimensions(width=50, height=20, clearance_width=10, clearance_height=10)
    
    # Test position finding with exclusion
    for container_id in containers.keys():
        position = collision_detector.find_collision_free_position_with_exclusion(
            container_id, test_dims, []
        )
        if position:
            print(f"   Available position in {container_id}: {position}")
        else:
            print(f"   No available position in {container_id}")
    
    print("✅ Spatial Constraint Integration Test Complete")
