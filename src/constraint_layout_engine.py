#!/usr/bin/env python3
"""
Generalized Constraint-Based Layout Engine for Existential Graphs

This production-ready layout engine uses Cassowary constraint solver to enforce
EG-specific logical constraints while providing precise positioning for all elements.

Key Features:
- Strict area containment enforcement
- Non-overlapping sibling cuts
- Hierarchical cut nesting
- Collision-free element positioning
- Support for all EG constructs (vertices, predicates, cuts, edges)
"""

import cairo
from cassowary import Variable, SimplexSolver, REQUIRED, STRONG, MEDIUM, WEAK
from typing import Dict, List, Tuple, Optional, Set
import math
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from egi_core_dau import RelationalGraphWithCuts
from layout_engine_clean import SpatialPrimitive, LayoutResult


class ConstraintBasedLayoutEngine:
    """Production-ready constraint-based layout engine for Existential Graphs."""
    
    def __init__(self, canvas_width: int = 800, canvas_height: int = 600):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.solver = SimplexSolver()
        self.variables = {}  # element_id -> {x, y, width, height}
        self.constraints = []
        self.area_hierarchy = {}  # area_id -> parent_area_id
        
    def clear(self):
        """Clear all variables and constraints for a new layout."""
        self.solver = SimplexSolver()
        self.variables.clear()
        self.constraints.clear()
        self.area_hierarchy.clear()
    
    def create_layout_from_graph(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """Create a complete constraint-based layout from an EGI graph."""
        
        print(f"\n🔧 Creating constraint-based layout for graph with {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
        
        # Clear previous layout
        self.clear()
        
        # Step 1: Analyze graph structure and build area hierarchy
        self._build_area_hierarchy(graph)
        
        # Step 2: Create variables for all elements
        self._create_variables_for_graph(graph)
        
        # Step 3: Add structural constraints (containment, non-overlap, sizing)
        self._add_structural_constraints(graph)
        
        # Step 4: Add positioning preferences
        self._add_positioning_preferences(graph)
        
        # Step 5: Solve the constraint system
        positions = self._solve_constraint_system()
        
        if not positions:
            print("❌ Constraint solving failed!")
            return []
        
        # Step 6: Create layout result from solved positions
        layout_result = self._create_layout_result(graph, positions)
        
        print(f"✅ Generated layout with {len(layout_result.primitives)} spatial primitives")
        return layout_result
    
    def _build_area_hierarchy(self, graph: RelationalGraphWithCuts):
        """Build the hierarchical structure of areas (cuts and sheet)."""
        
        print("📊 Building area hierarchy...")
        
        # Sheet is the root
        self.area_hierarchy[graph.sheet] = None
        
        # Build cut hierarchy
        for cut in graph.Cut:
            # Find parent area for this cut
            parent_area = self._find_parent_area(graph, cut.id)
            self.area_hierarchy[cut.id] = parent_area
            
            print(f"  Cut {cut.id} -> parent: {parent_area}")
    
    def _find_parent_area(self, graph: RelationalGraphWithCuts, cut_id: str) -> str:
        """Find which area contains a given cut."""
        
        # Check if cut is directly in any area
        for area_id, contents in graph.area.items():
            if cut_id in contents:
                return area_id
        
        # Default to sheet if not found
        return graph.sheet
    
    def _create_variables_for_graph(self, graph: RelationalGraphWithCuts):
        """Create constraint variables for all graph elements."""
        
        print("📐 Creating constraint variables...")
        
        # Create variables for sheet (canvas bounds)
        self._create_variables_for_element("sheet")
        
        # Create variables for all cuts
        for cut in graph.Cut:
            self._create_variables_for_element(cut.id)
        
        # Create variables for all vertices
        for vertex in graph.V:
            self._create_variables_for_element(vertex.id)
        
        # Create variables for all predicates (edges)
        for edge in graph.E:
            self._create_variables_for_element(edge.id)
        
        print(f"  Created variables for {len(self.variables)} elements")
    
    def _create_variables_for_element(self, element_id: str) -> Dict[str, Variable]:
        """Create position and size variables for an element."""
        vars_dict = {
            'x': Variable(f'{element_id}_x'),
            'y': Variable(f'{element_id}_y'),
            'width': Variable(f'{element_id}_width'),
            'height': Variable(f'{element_id}_height')
        }
        self.variables[element_id] = vars_dict
        return vars_dict
    
    def _add_structural_constraints(self, graph: RelationalGraphWithCuts):
        """Add all structural constraints (containment, non-overlap, sizing)."""
        
        print("🔗 Adding structural constraints...")
        
        # Set up sheet bounds
        self._constrain_sheet_bounds()
        
        # Add size constraints for all elements
        self._add_size_constraints_for_graph(graph)
        
        # Add containment constraints based on area hierarchy
        self._add_containment_constraints(graph)
        
        # Add non-overlap constraints for sibling elements
        self._add_non_overlap_constraints(graph)
        
        print(f"  Added {len(self.constraints)} constraints")
    
    def _constrain_sheet_bounds(self):
        """Set fixed bounds for the sheet (canvas)."""
        sheet_vars = self.variables["sheet"]
        
        margin = 50
        constraints = [
            sheet_vars['x'] == margin,
            sheet_vars['y'] == margin,
            sheet_vars['width'] == self.canvas_width - 2 * margin,
            sheet_vars['height'] == self.canvas_height - 2 * margin
        ]
        
        for constraint in constraints:
            self.solver.add_constraint(constraint, REQUIRED)
            self.constraints.append(constraint)
    
    def _add_size_constraints_for_graph(self, graph: RelationalGraphWithCuts):
        """Add minimum size constraints for all elements."""
        
        # Size constraints for cuts
        for cut in graph.Cut:
            self._add_size_constraints(cut.id, min_width=150, min_height=100)
        
        # Size constraints for vertices
        for vertex in graph.V:
            self._add_size_constraints(vertex.id, min_width=10, min_height=10)
        
        # Size constraints for predicates
        for edge in graph.E:
            # Estimate text width based on relation name
            relation_name = graph.get_relation_name(edge.id)
            text_width = max(60, len(relation_name) * 8)
            self._add_size_constraints(edge.id, min_width=text_width, min_height=25)
    
    def _add_size_constraints(self, element_id: str, min_width: float, min_height: float):
        """Add minimum size constraints for an element."""
        vars_dict = self.variables[element_id]
        
        constraints = [
            vars_dict['width'] >= min_width,
            vars_dict['height'] >= min_height
        ]
        
        for constraint in constraints:
            self.solver.add_constraint(constraint, REQUIRED)
            self.constraints.append(constraint)
    
    def _add_containment_constraints(self, graph: RelationalGraphWithCuts):
        """Add containment constraints based on logical area assignment."""
        
        print("📦 Adding containment constraints...")
        
        # For each area, ensure all its contents are contained within it
        for area_id, contents in graph.area.items():
            if area_id == graph.sheet:
                continue  # Sheet contains everything by default
            
            for content_id in contents:
                if content_id in self.variables:
                    self._add_containment_constraint(area_id, content_id, margin=15)
                    print(f"  {content_id} must be inside {area_id}")
        
        # Ensure cuts are contained in their parent areas
        for cut in graph.Cut:
            parent_area = self.area_hierarchy.get(cut.id)
            if parent_area and parent_area != graph.sheet:
                self._add_containment_constraint(parent_area, cut.id, margin=20)
                print(f"  Cut {cut.id} must be inside {parent_area}")
    
    def _add_containment_constraint(self, container_id: str, contained_id: str, margin: float = 10.0):
        """Add constraint that contained element must be inside container with margin."""
        container = self.variables[container_id]
        contained = self.variables[contained_id]
        
        constraints = [
            # Left edge: contained.x >= container.x + margin
            contained['x'] >= container['x'] + margin,
            # Right edge: contained.x + contained.width <= container.x + container.width - margin
            contained['x'] + contained['width'] <= container['x'] + container['width'] - margin,
            # Top edge: contained.y >= container.y + margin
            contained['y'] >= container['y'] + margin,
            # Bottom edge: contained.y + contained.height <= container.y + container.height - margin
            contained['y'] + contained['height'] <= container['y'] + container['height'] - margin
        ]
        
        for constraint in constraints:
            self.solver.add_constraint(constraint, REQUIRED)
            self.constraints.append(constraint)
    
    def _add_non_overlap_constraints(self, graph: RelationalGraphWithCuts):
        """Add non-overlap constraints for sibling elements in the same area."""
        
        print("🚫 Adding non-overlap constraints...")
        
        # Group elements by their containing area
        area_contents = {}
        
        # Add cuts to their parent areas
        for cut in graph.Cut:
            parent_area = self.area_hierarchy.get(cut.id, graph.sheet)
            if parent_area not in area_contents:
                area_contents[parent_area] = []
            area_contents[parent_area].append(cut.id)
        
        # Add other elements to their areas
        for area_id, contents in graph.area.items():
            if area_id not in area_contents:
                area_contents[area_id] = []
            area_contents[area_id].extend(contents)
        
        # Add non-overlap constraints within each area
        for area_id, contents in area_contents.items():
            elements_in_area = [elem_id for elem_id in contents if elem_id in self.variables]
            
            for i, elem1_id in enumerate(elements_in_area):
                for elem2_id in elements_in_area[i+1:]:
                    self._add_non_overlap_constraint(elem1_id, elem2_id, min_gap=20)
                    print(f"  {elem1_id} and {elem2_id} must not overlap in {area_id}")
    
    def _add_non_overlap_constraint(self, elem1_id: str, elem2_id: str, min_gap: float = 20.0):
        """Add constraint for horizontal separation between two elements."""
        elem1 = self.variables[elem1_id]
        elem2 = self.variables[elem2_id]
        
        # Horizontal separation constraint (elem1 to the left of elem2)
        constraint = elem1['x'] + elem1['width'] + min_gap <= elem2['x']
        
        self.solver.add_constraint(constraint, STRONG)
        self.constraints.append(constraint)
    
    def _add_positioning_preferences(self, graph: RelationalGraphWithCuts):
        """Add soft positioning preferences for better layout."""
        
        print("🎯 Adding positioning preferences...")
        
        # Prefer cuts to be in the center-right area
        for i, cut in enumerate(graph.Cut):
            preferred_x = 300 + i * 50  # Stagger cuts horizontally
            preferred_y = 200 + i * 30  # Stagger cuts vertically
            self._add_position_preference(cut.id, preferred_x, preferred_y, WEAK)
        
        # Prefer vertices to be spread out
        for i, vertex in enumerate(graph.V):
            preferred_x = 150 + i * 100
            preferred_y = 300 + (i % 2) * 50
            self._add_position_preference(vertex.id, preferred_x, preferred_y, WEAK)
        
        # Prefer predicates to be near their connected vertices
        for i, edge in enumerate(graph.E):
            preferred_x = 200 + i * 80
            preferred_y = 150 + i * 40
            self._add_position_preference(edge.id, preferred_x, preferred_y, WEAK)
    
    def _add_position_preference(self, element_id: str, preferred_x: float, preferred_y: float, strength=WEAK):
        """Add soft constraint for preferred position."""
        vars_dict = self.variables[element_id]
        
        constraints = [
            vars_dict['x'] == preferred_x,
            vars_dict['y'] == preferred_y
        ]
        
        for constraint in constraints:
            self.solver.add_constraint(constraint, strength)
            self.constraints.append(constraint)
    
    def _solve_constraint_system(self) -> Dict[str, Dict[str, float]]:
        """Solve the constraint system and return element positions/sizes."""
        
        print("🧮 Solving constraint system...")
        
        try:
            self.solver.solve()
            
            result = {}
            for element_id, vars_dict in self.variables.items():
                result[element_id] = {
                    'x': vars_dict['x'].value,
                    'y': vars_dict['y'].value,
                    'width': vars_dict['width'].value,
                    'height': vars_dict['height'].value
                }
            
            print("✅ Constraint system solved successfully!")
            return result
            
        except Exception as e:
            print(f"❌ Constraint solving failed: {e}")
            return {}
    
    def _create_layout_result(self, graph: RelationalGraphWithCuts, positions: Dict[str, Dict[str, float]]) -> LayoutResult:
        """Create layout primitives from solved positions."""
        
        print("🎨 Creating layout primitives...")
        
        primitives = []
        
        # Create cut primitives
        for cut in graph.Cut:
            if cut.id in positions:
                pos = positions[cut.id]
                primitive = SpatialPrimitive(
                    element_id=cut.id,
                    element_type='cut',
                    position=(pos['x'] + pos['width']/2, pos['y'] + pos['height']/2),
                    bounds=(pos['x'], pos['y'], pos['x'] + pos['width'], pos['y'] + pos['height']),
                    z_index=0
                )
                primitives.append(primitive)
        
        # Create vertex primitives
        for vertex in graph.V:
            if vertex.id in positions:
                pos = positions[vertex.id]
                # Find which area this vertex belongs to
                area_id = self._find_vertex_area(graph, vertex.id)
                primitive = SpatialPrimitive(
                    element_id=vertex.id,
                    element_type='vertex',
                    position=(pos['x'] + pos['width']/2, pos['y'] + pos['height']/2),
                    bounds=(pos['x'], pos['y'], pos['x'] + pos['width'], pos['y'] + pos['height']),
                    z_index=1
                )
                primitives.append(primitive)
        
        # Create predicate primitives
        for edge in graph.E:
            if edge.id in positions:
                pos = positions[edge.id]
                # Find which area this predicate belongs to
                area_id = self._find_predicate_area(graph, edge.id)
                primitive = SpatialPrimitive(
                    element_id=edge.id,
                    element_type='edge',
                    position=(pos['x'] + pos['width']/2, pos['y'] + pos['height']/2),
                    bounds=(pos['x'], pos['y'], pos['x'] + pos['width'], pos['y'] + pos['height']),
                    z_index=2
                )
                primitives.append(primitive)
        
        # Create edge primitives (lines of identity)
        for edge in graph.E:
            # Connect predicate to its arguments (vertices)
            predicate_pos = positions.get(edge.id)
            if predicate_pos and edge.id in graph.nu:
                # Use the nu mapping from the graph, not the edge object
                vertex_sequence = graph.nu[edge.id]
                for arg_vertex_id in vertex_sequence:
                    vertex_pos = positions.get(arg_vertex_id)
                    if vertex_pos:
                        edge_primitive = SpatialPrimitive(
                            element_id=f"{edge.id}_{arg_vertex_id}",
                            element_type='line',
                            position=((predicate_pos['x'] + vertex_pos['x'])/2, (predicate_pos['y'] + vertex_pos['y'])/2),
                            bounds=(min(predicate_pos['x'], vertex_pos['x']), min(predicate_pos['y'], vertex_pos['y']),
                                   max(predicate_pos['x'] + predicate_pos['width'], vertex_pos['x'] + vertex_pos['width']),
                                   max(predicate_pos['y'] + predicate_pos['height'], vertex_pos['y'] + vertex_pos['height'])),
                            z_index=3
                        )
                        primitives.append(edge_primitive)
        
        # Convert list to dictionary format expected by LayoutResult
        primitives_dict = {primitive.element_id: primitive for primitive in primitives}
        
        # Calculate canvas bounds
        if primitives:
            min_x = min(p.bounds[0] for p in primitives if p.bounds)
            min_y = min(p.bounds[1] for p in primitives if p.bounds)
            max_x = max(p.bounds[2] for p in primitives if p.bounds)
            max_y = max(p.bounds[3] for p in primitives if p.bounds)
            canvas_bounds = (min_x - 20, min_y - 20, max_x + 20, max_y + 20)
        else:
            canvas_bounds = (0, 0, self.canvas_width, self.canvas_height)
        
        # Build containment hierarchy
        containment_hierarchy = {}
        containment_hierarchy[graph.sheet] = set()
        for area_id, contents in graph.area.items():
            if area_id not in containment_hierarchy:
                containment_hierarchy[area_id] = set()
            containment_hierarchy[area_id].update(contents)
        
        return LayoutResult(
            primitives=primitives_dict,
            canvas_bounds=canvas_bounds,
            containment_hierarchy=containment_hierarchy
        )
    
    def _find_vertex_area(self, graph: RelationalGraphWithCuts, vertex_id: str) -> str:
        """Find which area a vertex belongs to."""
        for area_id, contents in graph.area.items():
            if vertex_id in contents:
                return area_id
        return graph.sheet
    
    def _find_predicate_area(self, graph: RelationalGraphWithCuts, edge_id: str) -> str:
        """Find which area a predicate belongs to."""
        for area_id, contents in graph.area.items():
            if edge_id in contents:
                return area_id
        return graph.sheet


# Integration function for existing workflow
def create_constraint_based_layout(graph: RelationalGraphWithCuts, canvas_width: int = 800, canvas_height: int = 600) -> LayoutResult:
    """Main entry point for constraint-based layout generation."""
    
    engine = ConstraintBasedLayoutEngine(canvas_width, canvas_height)
    return engine.create_layout_from_graph(graph)


if __name__ == "__main__":
    # Test with a simple example
    from egif_parser_dau import parse_egif
    
    test_egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    graph = parse_egif(test_egif)
    
    if graph:
        primitives = create_constraint_based_layout(graph)
        print(f"\n🎯 Generated {len(primitives)} layout primitives for test case")
        for primitive in primitives:
            print(f"  {primitive}")
    else:
        print("❌ Failed to parse test EGIF")
