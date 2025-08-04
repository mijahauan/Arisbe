#!/usr/bin/env python3
"""
Constraint-Based Layout Prototype for Existential Graphs

This prototype demonstrates the layered approach:
1. Constraint Solver Layer (Cassowary) - enforces EG logical constraints
2. Rendering Layer (PyCairo) - produces precise visual output

Key EG Constraints:
- Vertices must stay in their assigned areas
- Cuts must not overlap (siblings)
- Cuts must properly contain their contents
- Non-overlapping element positioning
"""

import cairo
from cassowary import Variable, SimplexSolver, REQUIRED, STRONG, MEDIUM, WEAK
from typing import Dict, List, Tuple, Optional
import math
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from egi_core_dau import RelationalGraphWithCuts


class ConstraintLayoutEngine:
    """Layout engine using Cassowary constraint solver for EG-specific constraints."""
    
    def __init__(self):
        self.solver = SimplexSolver()
        self.variables = {}  # element_id -> {x, y, width, height}
        self.constraints = []
        
    def create_variables_for_element(self, element_id: str) -> Dict[str, Variable]:
        """Create position and size variables for an element."""
        vars_dict = {
            'x': Variable(f'{element_id}_x'),
            'y': Variable(f'{element_id}_y'),
            'width': Variable(f'{element_id}_width'),
            'height': Variable(f'{element_id}_height')
        }
        self.variables[element_id] = vars_dict
        return vars_dict
    
    def add_containment_constraint(self, container_id: str, contained_id: str, margin: float = 10.0):
        """Add constraint that contained element must be inside container with margin."""
        container = self.variables[container_id]
        contained = self.variables[contained_id]
        
        # Contained element must be inside container bounds
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
    
    def add_non_overlap_constraint(self, elem1_id: str, elem2_id: str, min_gap: float = 20.0):
        """Add constraint that two elements must not overlap (simplified to horizontal separation)."""
        elem1 = self.variables[elem1_id]
        elem2 = self.variables[elem2_id]
        
        # Simplified: ensure horizontal separation (elem1 is to the left of elem2)
        # This is a simplification but will work for our test case
        constraint = elem1['x'] + elem1['width'] + min_gap <= elem2['x']
        
        self.solver.add_constraint(constraint, STRONG)
        self.constraints.append(constraint)
    
    def add_size_constraints(self, element_id: str, min_width: float = 30.0, min_height: float = 30.0):
        """Add minimum size constraints for an element."""
        vars_dict = self.variables[element_id]
        
        constraints = [
            vars_dict['width'] >= min_width,
            vars_dict['height'] >= min_height
        ]
        
        for constraint in constraints:
            self.solver.add_constraint(constraint, REQUIRED)
            self.constraints.append(constraint)
    
    def add_position_preference(self, element_id: str, preferred_x: float, preferred_y: float, strength=WEAK):
        """Add soft constraint for preferred position."""
        vars_dict = self.variables[element_id]
        
        constraints = [
            vars_dict['x'] == preferred_x,
            vars_dict['y'] == preferred_y
        ]
        
        for constraint in constraints:
            self.solver.add_constraint(constraint, strength)
            self.constraints.append(constraint)
    
    def solve_layout(self) -> Dict[str, Dict[str, float]]:
        """Solve the constraint system and return element positions/sizes."""
        try:
            # Solve the constraint system
            self.solver.solve()
            
            result = {}
            for element_id, vars_dict in self.variables.items():
                result[element_id] = {
                    'x': vars_dict['x'].value,
                    'y': vars_dict['y'].value,
                    'width': vars_dict['width'].value,
                    'height': vars_dict['height'].value
                }
            
            return result
            
        except Exception as e:
            print(f"❌ Constraint solving failed: {e}")
            return {}


class CairoEGRenderer:
    """Cairo-based renderer for Existential Graphs with precise visual control."""
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.ctx = cairo.Context(self.surface)
        
        # Set up coordinate system and background
        self.ctx.set_source_rgb(1, 1, 1)  # White background
        self.ctx.paint()
        
        # Set default drawing properties
        self.ctx.set_line_width(1.0)
        self.ctx.set_source_rgb(0, 0, 0)  # Black lines
    
    def draw_cut(self, x: float, y: float, width: float, height: float, label: str = ""):
        """Draw a cut as a fine-drawn closed curve (ellipse)."""
        # Save current state
        self.ctx.save()
        
        # Draw ellipse
        center_x = x + width / 2
        center_y = y + height / 2
        radius_x = width / 2
        radius_y = height / 2
        
        # Create elliptical path
        self.ctx.save()
        self.ctx.translate(center_x, center_y)
        self.ctx.scale(radius_x, radius_y)
        self.ctx.arc(0, 0, 1, 0, 2 * math.pi)
        self.ctx.restore()
        
        # Fine line for cuts
        self.ctx.set_line_width(1.0)
        self.ctx.set_source_rgb(0, 0, 0)
        self.ctx.stroke()
        
        # Add label if provided
        if label:
            self.ctx.set_font_size(12)
            text_extents = self.ctx.text_extents(label)
            label_x = center_x - text_extents.width / 2
            label_y = y - 5
            self.ctx.move_to(label_x, label_y)
            self.ctx.show_text(label)
        
        # Restore state
        self.ctx.restore()
    
    def draw_vertex(self, x: float, y: float, radius: float = 3.0, label: str = ""):
        """Draw a vertex as a small filled circle."""
        self.ctx.save()
        
        # Draw filled circle
        self.ctx.arc(x, y, radius, 0, 2 * math.pi)
        self.ctx.set_source_rgb(0, 0, 0)
        self.ctx.fill()
        
        # Add label if provided
        if label:
            self.ctx.set_font_size(10)
            text_extents = self.ctx.text_extents(label)
            label_x = x - text_extents.width / 2
            label_y = y - radius - 5
            self.ctx.move_to(label_x, label_y)
            self.ctx.show_text(label)
        
        self.ctx.restore()
    
    def draw_predicate(self, x: float, y: float, width: float, height: float, text: str):
        """Draw a predicate as text with optional background."""
        self.ctx.save()
        
        # Set font
        self.ctx.set_font_size(12)
        self.ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        
        # Center text in the given area
        text_extents = self.ctx.text_extents(text)
        text_x = x + (width - text_extents.width) / 2
        text_y = y + (height + text_extents.height) / 2
        
        # Draw text
        self.ctx.move_to(text_x, text_y)
        self.ctx.set_source_rgb(0, 0, 0)
        self.ctx.show_text(text)
        
        self.ctx.restore()
    
    def draw_line_of_identity(self, x1: float, y1: float, x2: float, y2: float):
        """Draw a line of identity as a heavy line."""
        self.ctx.save()
        
        # Heavy line for identity
        self.ctx.set_line_width(3.0)
        self.ctx.set_source_rgb(0, 0, 0)
        
        self.ctx.move_to(x1, y1)
        self.ctx.line_to(x2, y2)
        self.ctx.stroke()
        
        self.ctx.restore()
    
    def save_to_file(self, filename: str):
        """Save the rendered image to a file."""
        self.surface.write_to_png(filename)
        print(f"✅ Saved EG diagram to {filename}")


def create_test_layout_and_render():
    """Test the constraint-based layout with Cairo rendering."""
    
    print("🧪 Testing Constraint-Based EG Layout + Cairo Rendering")
    print("=" * 60)
    
    # Create layout engine
    layout = ConstraintLayoutEngine()
    
    # Test case: Mixed cut and sheet example
    # EGIF: (Human "Socrates") ~[ (Mortal "Socrates") ]
    
    # Create variables for elements
    sheet_vars = layout.create_variables_for_element("sheet")
    cut1_vars = layout.create_variables_for_element("cut1")
    human_pred_vars = layout.create_variables_for_element("human_pred")
    mortal_pred_vars = layout.create_variables_for_element("mortal_pred")
    socrates_vertex_vars = layout.create_variables_for_element("socrates_vertex")
    
    # Set up sheet as the root container
    layout.solver.add_constraint(sheet_vars['x'] == 50, REQUIRED)
    layout.solver.add_constraint(sheet_vars['y'] == 50, REQUIRED)
    layout.solver.add_constraint(sheet_vars['width'] == 700, REQUIRED)
    layout.solver.add_constraint(sheet_vars['height'] == 500, REQUIRED)
    
    # Size constraints
    layout.add_size_constraints("cut1", min_width=200, min_height=150)
    layout.add_size_constraints("human_pred", min_width=80, min_height=30)
    layout.add_size_constraints("mortal_pred", min_width=80, min_height=30)
    layout.add_size_constraints("socrates_vertex", min_width=10, min_height=10)
    
    # CRITICAL: Area containment constraints
    # Cut1 must be inside sheet
    layout.add_containment_constraint("sheet", "cut1", margin=50)
    
    # Mortal predicate must be inside cut1 (logical containment)
    layout.add_containment_constraint("cut1", "mortal_pred", margin=20)
    
    # Human predicate must be at sheet level (NOT inside cut1)
    layout.add_containment_constraint("sheet", "human_pred", margin=20)
    
    # Socrates vertex must be at sheet level (shared between predicates)
    layout.add_containment_constraint("sheet", "socrates_vertex", margin=20)
    
    # Non-overlap constraints
    layout.add_non_overlap_constraint("human_pred", "cut1", min_gap=30)
    layout.add_non_overlap_constraint("human_pred", "mortal_pred", min_gap=30)
    
    # Position preferences (soft constraints)
    layout.add_position_preference("cut1", 400, 200, strength=MEDIUM)
    layout.add_position_preference("human_pred", 150, 150, strength=MEDIUM)
    layout.add_position_preference("socrates_vertex", 300, 300, strength=WEAK)
    
    # Solve the constraint system
    print("🔧 Solving constraint system...")
    positions = layout.solve_layout()
    
    if not positions:
        print("❌ Layout solving failed!")
        return
    
    print("✅ Constraint system solved!")
    for element_id, pos in positions.items():
        print(f"  {element_id}: x={pos['x']:.1f}, y={pos['y']:.1f}, w={pos['width']:.1f}, h={pos['height']:.1f}")
    
    # Create Cairo renderer
    renderer = CairoEGRenderer(width=800, height=600)
    
    # Render elements using solved positions
    print("\n🎨 Rendering with Cairo...")
    
    # Draw cut
    cut_pos = positions["cut1"]
    renderer.draw_cut(cut_pos['x'], cut_pos['y'], cut_pos['width'], cut_pos['height'], "Cut1")
    
    # Draw predicates
    human_pos = positions["human_pred"]
    renderer.draw_predicate(human_pos['x'], human_pos['y'], human_pos['width'], human_pos['height'], "Human")
    
    mortal_pos = positions["mortal_pred"]
    renderer.draw_predicate(mortal_pos['x'], mortal_pos['y'], mortal_pos['width'], mortal_pos['height'], "Mortal")
    
    # Draw vertex
    vertex_pos = positions["socrates_vertex"]
    renderer.draw_vertex(vertex_pos['x'] + vertex_pos['width']/2, 
                        vertex_pos['y'] + vertex_pos['height']/2, 
                        radius=5, label="Socrates")
    
    # Draw lines of identity (connecting vertex to predicates)
    vertex_center_x = vertex_pos['x'] + vertex_pos['width']/2
    vertex_center_y = vertex_pos['y'] + vertex_pos['height']/2
    
    human_center_x = human_pos['x'] + human_pos['width']/2
    human_center_y = human_pos['y'] + human_pos['height']/2
    
    mortal_center_x = mortal_pos['x'] + mortal_pos['width']/2
    mortal_center_y = mortal_pos['y'] + mortal_pos['height']/2
    
    renderer.draw_line_of_identity(vertex_center_x, vertex_center_y, human_center_x, human_center_y)
    renderer.draw_line_of_identity(vertex_center_x, vertex_center_y, mortal_center_x, mortal_center_y)
    
    # Save the result
    output_file = "/Users/mjh/Sync/GitHub/Arisbe/constraint_layout_test.png"
    renderer.save_to_file(output_file)
    
    print(f"\n🎯 CRITICAL TEST: Area Containment Verification")
    print("-" * 50)
    
    # Verify that Human predicate is OUTSIDE the cut
    human_right = human_pos['x'] + human_pos['width']
    human_bottom = human_pos['y'] + human_pos['height']
    cut_left = cut_pos['x']
    cut_top = cut_pos['y']
    cut_right = cut_pos['x'] + cut_pos['width']
    cut_bottom = cut_pos['y'] + cut_pos['height']
    
    human_inside_cut = (human_pos['x'] >= cut_left and human_right <= cut_right and 
                       human_pos['y'] >= cut_top and human_bottom <= cut_bottom)
    
    # Verify that Mortal predicate is INSIDE the cut
    mortal_right = mortal_pos['x'] + mortal_pos['width']
    mortal_bottom = mortal_pos['y'] + mortal_pos['height']
    
    mortal_inside_cut = (mortal_pos['x'] >= cut_left and mortal_right <= cut_right and 
                        mortal_pos['y'] >= cut_top and mortal_bottom <= cut_bottom)
    
    print(f"Human predicate inside cut: {'❌ WRONG' if human_inside_cut else '✅ CORRECT (outside)'}")
    print(f"Mortal predicate inside cut: {'✅ CORRECT (inside)' if mortal_inside_cut else '❌ WRONG'}")
    
    if not human_inside_cut and mortal_inside_cut:
        print("\n🎉 SUCCESS: Constraint-based layout correctly enforces EG area containment!")
    else:
        print("\n❌ FAILURE: Area containment constraints not properly enforced")
    
    return positions


if __name__ == "__main__":
    create_test_layout_and_render()
