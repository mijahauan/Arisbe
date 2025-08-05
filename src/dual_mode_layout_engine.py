#!/usr/bin/env python3
"""
Dual-Mode Layout Engine for Arisbe Bullpen

Implements two distinct positioning modes:
1. PRACTICE MODE: Strict containment enforcement per EGI structure (for initial rendering and formal work)
2. WARMUP MODE: Free movement and flexible positioning (for exploratory "figuring out what to say")

This addresses the critical architectural requirement for different interaction paradigms.
"""

from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
import math

# Handle imports for both module and script execution
try:
    from .egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
    from .layout_engine import LayoutEngine, LayoutResult, LayoutElement, LayoutConstraint
except ImportError:
    from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
    from layout_engine import LayoutEngine, LayoutResult, LayoutElement, LayoutConstraint

# Type aliases
Coordinate = Tuple[float, float]
Bounds = Tuple[float, float, float, float]  # x1, y1, x2, y2


class PositioningMode(Enum):
    """Positioning modes for different use cases in the Bullpen"""
    PRACTICE = "practice"    # Strict containment enforcement per EGI
    WARMUP = "warmup"       # Free movement and flexible positioning


@dataclass
class PositioningConstraints:
    """Constraints for element positioning based on mode"""
    mode: PositioningMode
    enforce_containment: bool
    allow_cross_cut_movement: bool
    maintain_logical_structure: bool
    collision_avoidance_strength: float  # 0.0 = no avoidance, 1.0 = strict avoidance


class DualModeLayoutEngine(LayoutEngine):
    """
    Layout engine that supports both Practice (strict) and Warmup (flexible) positioning modes.
    
    PRACTICE MODE:
    - Strict containment enforcement
    - Elements must stay within their EGI-assigned areas
    - Collision avoidance respects area boundaries
    - Used for initial rendering and formal transformations
    
    WARMUP MODE:
    - Free movement across areas
    - Elements can be repositioned anywhere for exploration
    - Relaxed containment for "figuring out what to say"
    - User-driven positioning takes precedence
    """
    
    def __init__(self, canvas_width: int = 800, canvas_height: int = 600, 
                 default_mode: PositioningMode = PositioningMode.PRACTICE):
        super().__init__(canvas_width, canvas_height)
        self.current_mode = default_mode
        self.user_positions: Dict[ElementID, Coordinate] = {}  # User-specified positions in Warmup mode
        
    def set_positioning_mode(self, mode: PositioningMode):
        """Set the current positioning mode"""
        self.current_mode = mode
        
    def set_user_position(self, element_id: ElementID, position: Coordinate):
        """Set user-specified position for an element (Warmup mode)"""
        self.user_positions[element_id] = position
        
    def clear_user_positions(self):
        """Clear all user-specified positions"""
        self.user_positions.clear()
        
    def layout_graph(self, graph: RelationalGraphWithCuts, 
                    mode: Optional[PositioningMode] = None) -> LayoutResult:
        """
        Generate layout with mode-specific positioning logic.
        
        Args:
            graph: The EGI to layout
            mode: Optional override for positioning mode
        """
        if mode is not None:
            self.current_mode = mode
            
        if self.current_mode == PositioningMode.PRACTICE:
            return self._layout_practice_mode(graph)
        else:
            return self._layout_warmup_mode(graph)
    
    def _layout_practice_mode(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        PRACTICE MODE: Strict containment enforcement per EGI structure.
        Elements must be positioned within their assigned areas.
        """
        # Use the base layout engine with strict containment
        return super().layout_graph(graph)
    
    def _layout_warmup_mode(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        WARMUP MODE: Flexible positioning for exploration.
        User positions take precedence; fallback to loose automatic layout.
        """
        # Start with base layout as foundation
        base_layout = super().layout_graph(graph)
        
        # Override with user-specified positions where available
        modified_elements = {}
        
        for element_id, layout_element in base_layout.elements.items():
            if element_id in self.user_positions:
                # Use user-specified position
                user_pos = self.user_positions[element_id]
                
                # Create new layout element with user position but preserve other properties
                modified_element = LayoutElement(
                    element_id=layout_element.element_id,
                    element_type=layout_element.element_type,
                    position=user_pos,
                    bounds=self._calculate_bounds_around_position(user_pos, layout_element.element_type),
                    parent_area=layout_element.parent_area,  # Keep logical parent for reference
                    contained_elements=layout_element.contained_elements,
                    curve_points=layout_element.curve_points,
                    attachment_points=layout_element.attachment_points
                )
                modified_elements[element_id] = modified_element
            else:
                # Use automatic layout with relaxed constraints
                relaxed_element = self._apply_warmup_positioning(layout_element, base_layout.elements, graph)
                modified_elements[element_id] = relaxed_element
        
        # Create modified layout result
        return LayoutResult(
            elements=modified_elements,
            canvas_bounds=base_layout.canvas_bounds,
            containment_hierarchy=base_layout.containment_hierarchy,
            layout_constraints_satisfied=self._get_warmup_constraints(),
            layout_quality_score=self._calculate_warmup_quality_score(modified_elements)
        )
    
    def _apply_warmup_positioning(self, layout_element: LayoutElement, 
                                 all_elements: Dict[ElementID, LayoutElement],
                                 graph: RelationalGraphWithCuts) -> LayoutElement:
        """Apply relaxed positioning logic for Warmup mode"""
        
        if layout_element.element_type == 'edge':
            # For predicates in Warmup mode, use relaxed collision avoidance
            # that doesn't strictly enforce area boundaries
            position = self._warmup_predicate_positioning(layout_element, all_elements, graph)
            
            return LayoutElement(
                element_id=layout_element.element_id,
                element_type=layout_element.element_type,
                position=position,
                bounds=self._calculate_bounds_around_position(position, layout_element.element_type),
                parent_area=layout_element.parent_area,
                contained_elements=layout_element.contained_elements,
                curve_points=layout_element.curve_points,
                attachment_points=layout_element.attachment_points
            )
        else:
            # For vertices and cuts, keep base positioning but allow some flexibility
            return layout_element
    
    def _warmup_predicate_positioning(self, predicate_element: LayoutElement,
                                     all_elements: Dict[ElementID, LayoutElement],
                                     graph: RelationalGraphWithCuts) -> Coordinate:
        """Calculate predicate position with Warmup mode flexibility"""
        
        # Start with the Practice mode position as baseline
        base_position = predicate_element.position
        
        # Apply gentle collision avoidance without strict area constraints
        adjusted_position = self._avoid_collisions_flexible(
            base_position, all_elements, exclude_types={'vertex'}
        )
        
        return adjusted_position
    
    def _avoid_collisions_flexible(self, position: Coordinate,
                                  all_layouts: Dict[ElementID, LayoutElement],
                                  exclude_types: set = None) -> Coordinate:
        """Flexible collision avoidance for Warmup mode (no strict area bounds)"""
        if exclude_types is None:
            exclude_types = set()
        
        x, y = position
        max_attempts = 10  # Fewer attempts than Practice mode
        attempt = 0
        
        while attempt < max_attempts:
            collision = False
            
            # Check for collisions with existing elements
            for element in all_layouts.values():
                if element.element_type in exclude_types:
                    continue
                    
                # Calculate distance to element center
                elem_x, elem_y = element.position
                distance = ((x - elem_x) ** 2 + (y - elem_y) ** 2) ** 0.5
                
                # Use larger separation distance in Warmup mode for easier manipulation
                min_separation = self.min_element_separation * 0.7  # Relaxed separation
                
                if distance < min_separation:
                    collision = True
                    # Move away from collision with gentle adjustment
                    if distance > 0:
                        move_x = (x - elem_x) / distance * min_separation
                        move_y = (y - elem_y) / distance * min_separation
                        x = elem_x + move_x
                        y = elem_y + move_y
                    else:
                        # Same position - move arbitrarily
                        x += min_separation
                    break
            
            if not collision:
                break
                
            attempt += 1
        
        # Keep within canvas bounds but don't enforce area containment
        x = max(self.margin, min(self.canvas_width - self.margin, x))
        y = max(self.margin, min(self.canvas_height - self.margin, y))
        
        return (x, y)
    
    def _calculate_bounds_around_position(self, position: Coordinate, element_type: str) -> Bounds:
        """Calculate bounds around a given position based on element type"""
        x, y = position
        
        if element_type == 'vertex':
            radius = self.vertex_radius
            return (x - radius, y - radius, x + radius, y + radius)
        elif element_type == 'edge':
            # Predicate bounds
            return (x - 40, y - 15, x + 40, y + 15)
        elif element_type == 'cut':
            # Cut bounds - use minimum size
            size = self.min_cut_size
            return (x - size/2, y - size/2, x + size/2, y + size/2)
        else:
            # Default bounds
            return (x - 20, y - 20, x + 20, y + 20)
    
    def _get_warmup_constraints(self) -> Set[LayoutConstraint]:
        """Get the set of constraints satisfied in Warmup mode"""
        return {
            LayoutConstraint.NON_OVERLAPPING,  # Still avoid overlaps
            LayoutConstraint.ARBITRARY_DEFORMATION  # Allow free movement
        }
    
    def _calculate_warmup_quality_score(self, elements: Dict[ElementID, LayoutElement]) -> float:
        """Calculate layout quality score for Warmup mode"""
        # In Warmup mode, quality is based on user satisfaction and readability
        # rather than strict geometric constraints
        
        # Basic score based on non-overlapping elements
        overlap_penalty = 0.0
        element_list = list(elements.values())
        
        for i, elem1 in enumerate(element_list):
            for elem2 in element_list[i+1:]:
                if self._bounds_overlap(elem1.bounds, elem2.bounds):
                    overlap_penalty += 0.1
        
        base_score = 1.0 - min(overlap_penalty, 0.8)
        
        # Bonus for user-positioned elements (they know what they want)
        user_positioning_bonus = len(self.user_positions) * 0.05
        
        return min(base_score + user_positioning_bonus, 1.0)
    
    def move_element_warmup(self, element_id: ElementID, new_position: Coordinate,
                           graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        Move an element to a new position in Warmup mode.
        This is the primary interaction method for free-form editing.
        """
        if self.current_mode != PositioningMode.WARMUP:
            raise ValueError("move_element_warmup can only be used in Warmup mode")
        
        # Store the user position
        self.set_user_position(element_id, new_position)
        
        # Regenerate layout with new position
        return self.layout_graph(graph)
    
    def validate_practice_containment(self, graph: RelationalGraphWithCuts,
                                    layout_result: LayoutResult) -> List[str]:
        """
        Validate that a layout satisfies Practice mode containment requirements.
        Returns list of validation errors.
        """
        errors = []
        
        for element_id, layout_element in layout_result.elements.items():
            if layout_element.element_type in ['vertex', 'edge']:
                # Check if element is positioned within its assigned area
                expected_area = layout_element.parent_area
                
                if expected_area and expected_area in layout_result.elements:
                    container = layout_result.elements[expected_area]
                    element_pos = layout_element.position
                    container_bounds = container.bounds
                    
                    x, y = element_pos
                    x1, y1, x2, y2 = container_bounds
                    
                    if not (x1 <= x <= x2 and y1 <= y <= y2):
                        element_name = graph.rel.get(element_id, f"Element_{element_id[:8]}")
                        errors.append(
                            f"Element {element_name} ({element_id}) is outside its assigned area {expected_area}"
                        )
        
        return errors


def test_dual_mode_layout():
    """Test the dual-mode layout engine with both modes"""
    from egif_parser_dau import EGIFParser
    
    # Test case: Human outside cut, Mortal inside cut
    egif_text = '*x (Human x) ~[ (Mortal x) ]'
    parser = EGIFParser(egif_text)
    egi = parser.parse()
    
    # Create dual-mode layout engine
    layout_engine = DualModeLayoutEngine()
    
    print("=== PRACTICE MODE TEST ===")
    practice_layout = layout_engine.layout_graph(egi, PositioningMode.PRACTICE)
    
    # Validate Practice mode containment
    errors = layout_engine.validate_practice_containment(egi, practice_layout)
    if errors:
        print("❌ Practice mode containment errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Practice mode containment validation passed")
    
    print("\n=== WARMUP MODE TEST ===")
    warmup_layout = layout_engine.layout_graph(egi, PositioningMode.WARMUP)
    
    # Test user positioning in Warmup mode
    layout_engine.set_positioning_mode(PositioningMode.WARMUP)
    
    # Simulate user moving Human predicate to a new position
    human_edge_id = None
    for element_id, layout_element in warmup_layout.elements.items():
        if layout_element.element_type == 'edge' and egi.rel.get(element_id) == 'Human':
            human_edge_id = element_id
            break
    
    if human_edge_id:
        # Move Human predicate to arbitrary position
        new_position = (400, 200)
        updated_layout = layout_engine.move_element_warmup(human_edge_id, new_position, egi)
        
        moved_element = updated_layout.elements[human_edge_id]
        print(f"✅ Human predicate moved to user position: {moved_element.position}")
    
    print("\n=== MODE COMPARISON ===")
    print(f"Practice mode quality score: {practice_layout.layout_quality_score:.3f}")
    print(f"Warmup mode quality score: {warmup_layout.layout_quality_score:.3f}")


if __name__ == "__main__":
    test_dual_mode_layout()
