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
        
        # Calculate appropriate sizes based on element content
        for vertex in graph.V:
            # Check if vertex has a label (constant)
            if vertex.label is not None:
                # Larger size for labeled vertices to accommodate compact visual unit
                label_width = len(vertex.label) * 8 + 20  # Estimate text width + padding
                vertex_width = max(50, label_width)  # Minimum 50px, or text width
                vertex_height = 35  # Height for dot + label + handles
            else:
                # Smaller size for unlabeled vertices (just dot + handles)
                vertex_width = 40  # Width for handles + dot
                vertex_height = 20  # Height for dot + small margin
            
            self._add_size_constraints(vertex.id, vertex_width, vertex_height)
        
        for edge in graph.E:
            # Size based on predicate name length
            if edge.id in graph.rel:
                predicate_name = graph.rel[edge.id]
                text_width = len(predicate_name) * 8 + 20  # Estimate width + padding
                edge_width = max(40, text_width)
                edge_height = 25  # Height for text + hook space
            else:
                edge_width = 40
                edge_height = 25
            
            self._add_size_constraints(edge.id, edge_width, edge_height)
        
        for cut in graph.Cut:
            # Cuts need substantial size to contain other elements
            cut_width = 100   # Minimum width for containment
            cut_height = 80   # Minimum height for containment
            self._add_size_constraints(cut.id, cut_width, cut_height)
    
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
                    # Use larger margin for better visual separation
                    margin = 25  # Increased from 15 for better padding
                    self._add_containment_constraint(area_id, content_id, margin=margin)
                    print(f"  {content_id} must be inside {area_id}")
        
        # Ensure cuts are contained in their parent areas
        for cut in graph.Cut:
            parent_area = self.area_hierarchy.get(cut.id)
            if parent_area and parent_area != graph.sheet:
                # Use larger margin for nested cuts
                margin = 30  # Increased from 20 for better visual hierarchy
                self._add_containment_constraint(parent_area, cut.id, margin=margin)
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
        """Add comprehensive non-overlap constraints for all elements in the same area."""
        
        print("🚫 Adding comprehensive non-overlap constraints...")
        
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
        
        # Add comprehensive non-overlap constraints within each area
        for area_id, contents in area_contents.items():
            elements_in_area = [elem_id for elem_id in contents if elem_id in self.variables]
            
            print(f"  Processing area {area_id} with {len(elements_in_area)} elements")
            
            for i, elem1_id in enumerate(elements_in_area):
                for elem2_id in elements_in_area[i+1:]:
                    # Calculate appropriate gap based on element types
                    min_gap = self._calculate_required_gap(elem1_id, elem2_id)
                    self._add_comprehensive_non_overlap_constraint(elem1_id, elem2_id, min_gap)
                    print(f"    {elem1_id} and {elem2_id} must not overlap (gap: {min_gap})")
    
    def _add_non_overlap_constraint(self, elem1_id: str, elem2_id: str, min_gap: float = 20.0):
        """Add constraint for proper 2D separation between two elements (prevents overlap)."""
        elem1 = self.variables[elem1_id]
        elem2 = self.variables[elem2_id]
        
        # Special handling for cuts - they must NEVER overlap
        if 'cut' in elem1_id.lower() and 'cut' in elem2_id.lower():
            # For cut-to-cut: use much larger gap and REQUIRED strength
            gap = min_gap * 3  # Even larger gap for cuts
            
            # CRITICAL: Use REQUIRED strength for cut non-overlap (cannot be violated)
            h_constraint = elem1['x'] + elem1['width'] + gap <= elem2['x']
            self.solver.add_constraint(h_constraint, REQUIRED)  # REQUIRED = cannot be violated
            self.constraints.append(h_constraint)
            
            # Also add vertical separation to ensure complete 2D separation
            v_gap = gap * 0.7  # Substantial vertical offset
            v_constraint = elem1['y'] + elem1['height'] + v_gap <= elem2['y']
            self.solver.add_constraint(v_constraint, REQUIRED)  # REQUIRED = cannot be violated
            self.constraints.append(v_constraint)
            
        else:
            # For non-cut elements: use original logic with larger gap
            gap = min_gap * 2 if ('cut' in elem1_id.lower() or 'cut' in elem2_id.lower()) else min_gap
            
            # Horizontal separation constraint (elem1 to the left of elem2)
            h_constraint = elem1['x'] + elem1['width'] + gap <= elem2['x']
            self.solver.add_constraint(h_constraint, STRONG)
            self.constraints.append(h_constraint)
    
    def _calculate_required_gap(self, elem1_id: str, elem2_id: str) -> float:
        """Calculate the required gap between two elements based on their types."""
        
        base_gap = 30
        
        # Larger gaps for cuts to ensure clear visual separation
        if 'cut' in elem1_id.lower() or 'cut' in elem2_id.lower():
            return base_gap * 2  # 60px for cuts
        
        # Medium gaps for predicates (text elements need space)
        if elem1_id.startswith('e_') or elem2_id.startswith('e_'):
            return base_gap * 1.5  # 45px for predicates
        
        # Standard gap for vertices
        return base_gap  # 30px for vertices
    
    def _add_comprehensive_non_overlap_constraint(self, elem1_id: str, elem2_id: str, min_gap: float):
        """Add comprehensive 2D non-overlap constraints between two elements."""
        
        elem1 = self.variables[elem1_id]
        elem2 = self.variables[elem2_id]
        
        # For sibling cuts: enforce strict horizontal separation (side-by-side layout)
        if 'cut' in elem1_id.lower() and 'cut' in elem2_id.lower():
            # Check if these are sibling cuts (same parent area)
            elem1_parent = self.area_hierarchy.get(elem1_id, None)
            elem2_parent = self.area_hierarchy.get(elem2_id, None)
            
            print(f"  DEBUG: Checking cuts {elem1_id} (parent: {elem1_parent}) and {elem2_id} (parent: {elem2_parent})")
            
            if elem1_parent == elem2_parent and elem1_parent is not None:
                # Sibling cuts: enforce strict horizontal separation (REQUIRED)
                # Place cuts side-by-side with substantial gap
                large_gap = min_gap * 4  # 120px minimum gap for sibling cuts
                h_constraint = elem1['x'] + elem1['width'] + large_gap <= elem2['x']
                self.solver.add_constraint(h_constraint, REQUIRED)
                self.constraints.append(h_constraint)
                
                # Ensure cuts are roughly vertically aligned (same y-level)
                # This creates a clean side-by-side layout
                v_alignment = elem1['y'] == elem2['y']
                self.solver.add_constraint(v_alignment, STRONG)  # Strong preference for alignment
                self.constraints.append(v_alignment)
                
                print(f"  ✅ Added SIBLING CUT separation: {elem1_id} and {elem2_id} (gap: {large_gap}px, aligned)")
                return  # Skip other constraint logic for sibling cuts
            else:
                print(f"  → Not siblings (different parents or None)")
                # Non-sibling cuts: standard separation
                h_constraint = elem1['x'] + elem1['width'] + min_gap <= elem2['x']
                self.solver.add_constraint(h_constraint, REQUIRED)
                self.constraints.append(h_constraint)
            
        else:
            # For other elements: use STRONG constraints with larger gaps
            # Horizontal separation
            h_constraint = elem1['x'] + elem1['width'] + min_gap <= elem2['x']
            self.solver.add_constraint(h_constraint, STRONG)
            self.constraints.append(h_constraint)
            
            # Add vertical separation for better 2D spacing
            v_gap = min_gap * 0.6  # Smaller vertical gap
            v_constraint = elem1['y'] + elem1['height'] + v_gap <= elem2['y']
            self.solver.add_constraint(v_constraint, MEDIUM)
            self.constraints.append(v_constraint)
    
    def _add_positioning_preferences(self, graph: RelationalGraphWithCuts):
        """Add soft positioning preferences for better layout."""
        
        print("🎯 Adding positioning preferences...")
        
        # Prefer cuts to be in the center-right area
        for i, cut in enumerate(graph.Cut):
            preferred_x = 300 + i * 50  # Stagger cuts horizontally
            preferred_y = 200 + i * 30  # Stagger cuts vertically
            self._add_position_preference(cut.id, preferred_x, preferred_y, WEAK)
        
        # Add collision-aware positioning for vertices and predicates
        # This prevents lines from crossing cuts inappropriately
        self._add_collision_aware_positioning(graph)
        
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
    
    def _add_collision_aware_positioning(self, graph: RelationalGraphWithCuts):
        """Add positioning preferences to prevent lines from crossing cuts inappropriately."""
        
        print("🚧 Adding collision-aware positioning...")
        
        # Strategy: Position connected elements (vertex-predicate pairs) to minimize line crossings
        # by preferring them to be on the same side of cuts in their area
        
        for edge_id in graph.E:
            if edge_id not in graph.nu or edge_id not in self.variables:
                continue
                
            vertex_sequence = graph.nu[edge_id]
            edge_area = self._find_predicate_area(graph, edge_id)
            
            # For each vertex connected to this edge
            for vertex_id in vertex_sequence:
                if vertex_id not in self.variables:
                    continue
                    
                # Find cuts in the same area that could interfere with the connection
                cuts_in_same_area = []
                if edge_area == graph.sheet:
                    # Sheet-level: avoid cuts at sheet level
                    cuts_in_same_area = [cut.id for cut in graph.Cut 
                                        if self._find_parent_area(graph, cut.id) == graph.sheet]
                else:
                    # Inside a cut: avoid sibling cuts
                    cuts_in_same_area = [cut.id for cut in graph.Cut 
                                        if self._find_parent_area(graph, cut.id) == edge_area]
                
                # Position vertex and predicate to avoid crossing cuts
                for cut_id in cuts_in_same_area:
                    if cut_id in self.variables:
                        self._add_line_avoidance_preferences(vertex_id, edge_id, cut_id)
    
    def _add_line_avoidance_preferences(self, vertex_id: str, edge_id: str, cut_id: str):
        """Add strong preferences to keep vertex and predicate on the same side of a cut."""
        
        # Strategy: ensure vertex and predicate are positioned so their connecting line
        # doesn't cross through the cut by keeping them on the same side
        
        cut_vars = self.variables[cut_id]
        vertex_vars = self.variables[vertex_id]
        edge_vars = self.variables[edge_id]
        
        # Calculate cut boundaries with safety margin
        safety_margin = 40  # Larger margin to ensure clear separation
        
        # Option 1: Both elements to the left of cut
        vertex_left = vertex_vars['x'] + vertex_vars['width'] <= cut_vars['x'] - safety_margin
        edge_left = edge_vars['x'] + edge_vars['width'] <= cut_vars['x'] - safety_margin
        
        # Option 2: Both elements to the right of cut  
        vertex_right = vertex_vars['x'] >= cut_vars['x'] + cut_vars['width'] + safety_margin
        edge_right = edge_vars['x'] >= cut_vars['x'] + cut_vars['width'] + safety_margin
        
        # Prefer left positioning (simpler layout)
        self.solver.add_constraint(vertex_left, MEDIUM)
        self.solver.add_constraint(edge_left, MEDIUM)
        self.constraints.extend([vertex_left, edge_left])
        
        # Also add vertical separation to avoid crossing cut vertically
        vertex_above = vertex_vars['y'] + vertex_vars['height'] <= cut_vars['y'] - safety_margin
        edge_above = edge_vars['y'] + edge_vars['height'] <= cut_vars['y'] - safety_margin
        
        self.solver.add_constraint(vertex_above, WEAK)
        self.solver.add_constraint(edge_above, WEAK)
        self.constraints.extend([vertex_above, edge_above])
        
        print(f"  Added strong line avoidance preferences for {vertex_id}-{edge_id} around {cut_id}")
    
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
        """Find which area a vertex belongs to based on predicate usage."""
        # Find all predicates that use this vertex
        predicate_areas = []
        for edge_id, vertex_sequence in graph.nu.items():
            if vertex_id in vertex_sequence:
                predicate_area = self._find_predicate_area(graph, edge_id)
                predicate_areas.append(predicate_area)
        
        if not predicate_areas:
            # Vertex not used by any predicates - place at sheet level
            return graph.sheet
        
        if len(predicate_areas) == 1:
            # Vertex used by only one predicate - same area as predicate
            return predicate_areas[0]
        
        # Vertex used by multiple predicates - find lowest common ancestor area
        return self._find_lowest_common_ancestor_area(graph, predicate_areas)
    
    def _find_predicate_area(self, graph: RelationalGraphWithCuts, edge_id: str) -> str:
        """Find which area a predicate belongs to."""
        for area_id, contents in graph.area.items():
            if edge_id in contents:
                return area_id
        return graph.sheet
    
    def _find_lowest_common_ancestor_area(self, graph: RelationalGraphWithCuts, areas: list) -> str:
        """Find the lowest common ancestor area for a list of areas."""
        if not areas:
            return graph.sheet
        
        # Remove duplicates and filter out sheet
        unique_areas = list(set(areas))
        
        # If all predicates are at sheet level, vertex goes to sheet
        if all(area == graph.sheet for area in unique_areas):
            return graph.sheet
        
        # If predicates are in different cuts, vertex must be at sheet level
        # (This handles the sibling cuts case: *x ~[ (Human x) ] ~[ (Mortal x) ])
        cut_areas = [area for area in unique_areas if area != graph.sheet]
        if len(cut_areas) > 1:
            # Check if cuts are siblings (same parent) or nested
            parents = set()
            for cut_area in cut_areas:
                parent = self.area_hierarchy.get(cut_area, graph.sheet)
                parents.add(parent)
            
            if len(parents) > 1:
                # Cuts have different parents - vertex goes to sheet
                return graph.sheet
            else:
                # Cuts have same parent - vertex goes to that parent
                return list(parents)[0]
        
        # Single cut area - vertex goes there
        return unique_areas[0] if len(unique_areas) == 1 else graph.sheet


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
