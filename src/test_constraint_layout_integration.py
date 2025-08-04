#!/usr/bin/env python3
"""
Test Constraint-Based Layout Integration

This script tests the new constraint-based layout engine against all the 
problematic EGIF test cases that failed with the Graphviz approach.

Key Test Cases:
1. Mixed cut and sheet: (Human "Socrates") ~[ (Mortal "Socrates") ]
2. Nested cuts: ~[ ~[ (P "x") ] ]
3. Binary relations: (Loves "John" "Mary")
4. Deeply nested with shared constant: *x ~[ ~[ (P x) ] ]
5. Sibling cuts: ~[ (P "x") ] ~[ (Q "x") ]
"""

import sys
import os
import cairo

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from egif_parser_dau import parse_egif
from constraint_layout_engine import create_constraint_based_layout
from clean_diagram_renderer import CleanDiagramRenderer


class ConstraintLayoutTester:
    """Test suite for constraint-based layout engine."""
    
    def __init__(self):
        self.test_cases = [
            {
                'name': 'Mixed Cut and Sheet',
                'egif': '(Human "Socrates") ~[ (Mortal "Socrates") ]',
                'description': 'Human predicate should be outside cut, Mortal inside'
            },
            {
                'name': 'Nested Cuts',
                'egif': '~[ ~[ (P "x") ] ]',
                'description': 'Inner cut should be visually inside outer cut'
            },
            {
                'name': 'Binary Relations',
                'egif': '(Loves "John" "Mary")',
                'description': 'Both vertices should be at sheet level'
            },
            {
                'name': 'Deeply Nested with Shared Constant',
                'egif': '*x ~[ ~[ (P x) ] ]',
                'description': 'Variable x should be at sheet level, predicate P in innermost cut'
            },
            {
                'name': 'Sibling Cuts',
                'egif': '~[ (P "x") ] ~[ (Q "x") ]',
                'description': 'Two cuts should not overlap, shared vertex at sheet level'
            },
            {
                'name': 'Complex Nested Structure',
                'egif': '*x (Human x) ~[ (Mortal x) ~[ (Wise x) ] ]',
                'description': 'Human at sheet, Mortal in outer cut, Wise in inner cut'
            }
        ]
    
    def run_all_tests(self):
        """Run all test cases and generate visual outputs."""
        
        print("🧪 Testing Constraint-Based Layout Engine")
        print("=" * 60)
        
        results = []
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n📋 Test {i}: {test_case['name']}")
            print(f"EGIF: {test_case['egif']}")
            print(f"Expected: {test_case['description']}")
            print("-" * 40)
            
            result = self.run_single_test(test_case, i)
            results.append(result)
        
        # Summary
        print(f"\n📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in results if r['success'])
        total = len(results)
        
        for result in results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['name']}")
            if not result['success']:
                print(f"     Error: {result['error']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Constraint-based layout is working correctly!")
        else:
            print("⚠️  Some tests failed. Review the errors above.")
        
        return results
    
    def run_single_test(self, test_case: dict, test_number: int) -> dict:
        """Run a single test case."""
        
        try:
            # Parse EGIF
            print("🔍 Parsing EGIF...")
            graph = parse_egif(test_case['egif'])
            
            if not graph:
                return {
                    'name': test_case['name'],
                    'success': False,
                    'error': 'EGIF parsing failed'
                }
            
            print(f"✅ Parsed graph: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
            
            # Generate constraint-based layout
            print("🔧 Generating constraint-based layout...")
            primitives = create_constraint_based_layout(graph, canvas_width=800, canvas_height=600)
            
            if not primitives:
                return {
                    'name': test_case['name'],
                    'success': False,
                    'error': 'Layout generation failed'
                }
            
            print(f"✅ Generated {len(primitives)} layout primitives")
            
            # Render with Cairo
            print("🎨 Rendering with Cairo...")
            output_file = f"/Users/mjh/Sync/GitHub/Arisbe/constraint_test_{test_number}_{test_case['name'].lower().replace(' ', '_')}.png"
            
            success = self.render_with_cairo(primitives, output_file)
            
            if success:
                print(f"✅ Saved diagram to {output_file}")
                
                # Verify area containment
                containment_ok = self.verify_area_containment(graph, primitives)
                
                return {
                    'name': test_case['name'],
                    'success': containment_ok,
                    'error': None if containment_ok else 'Area containment verification failed',
                    'output_file': output_file
                }
            else:
                return {
                    'name': test_case['name'],
                    'success': False,
                    'error': 'Rendering failed'
                }
        
        except Exception as e:
            return {
                'name': test_case['name'],
                'success': False,
                'error': str(e)
            }
    
    def render_with_cairo(self, primitives, output_file: str) -> bool:
        """Render layout primitives using Cairo."""
        
        try:
            # Create Cairo surface and context
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 600)
            ctx = cairo.Context(surface)
            
            # White background
            ctx.set_source_rgb(1, 1, 1)
            ctx.paint()
            
            # Set default drawing properties
            ctx.set_source_rgb(0, 0, 0)
            ctx.set_line_width(1.0)
            
            # Draw primitives by type
            
            # 1. Draw cuts first (background)
            for primitive in primitives:
                if hasattr(primitive, 'cut_id'):
                    self.draw_cut(ctx, primitive)
            
            # 2. Draw edges (lines of identity)
            for primitive in primitives:
                if hasattr(primitive, 'start_x'):
                    self.draw_edge(ctx, primitive)
            
            # 3. Draw predicates
            for primitive in primitives:
                if hasattr(primitive, 'relation_name'):
                    self.draw_predicate(ctx, primitive)
            
            # 4. Draw vertices (foreground)
            for primitive in primitives:
                if hasattr(primitive, 'vertex_id'):
                    self.draw_vertex(ctx, primitive)
            
            # Save to file
            surface.write_to_png(output_file)
            return True
            
        except Exception as e:
            print(f"❌ Rendering error: {e}")
            return False
    
    def draw_cut(self, ctx, primitive):
        """Draw a cut as an ellipse."""
        ctx.save()
        
        center_x = primitive.x + primitive.width / 2
        center_y = primitive.y + primitive.height / 2
        radius_x = primitive.width / 2
        radius_y = primitive.height / 2
        
        # Create elliptical path
        ctx.save()
        ctx.translate(center_x, center_y)
        ctx.scale(radius_x, radius_y)
        ctx.arc(0, 0, 1, 0, 2 * 3.14159)
        ctx.restore()
        
        # Fine line for cuts
        ctx.set_line_width(1.0)
        ctx.set_source_rgb(0, 0, 0)
        ctx.stroke()
        
        # Label
        ctx.set_font_size(10)
        text = f"Cut {primitive.cut_id}"
        text_extents = ctx.text_extents(text)
        label_x = center_x - text_extents.width / 2
        label_y = primitive.y - 5
        ctx.move_to(label_x, label_y)
        ctx.show_text(text)
        
        ctx.restore()
    
    def draw_vertex(self, ctx, primitive):
        """Draw a vertex as a filled circle."""
        ctx.save()
        
        ctx.arc(primitive.x, primitive.y, 4, 0, 2 * 3.14159)
        ctx.set_source_rgb(0, 0, 0)
        ctx.fill()
        
        # Label
        ctx.set_font_size(9)
        text = primitive.vertex_id
        text_extents = ctx.text_extents(text)
        label_x = primitive.x - text_extents.width / 2
        label_y = primitive.y - 8
        ctx.move_to(label_x, label_y)
        ctx.show_text(text)
        
        ctx.restore()
    
    def draw_predicate(self, ctx, primitive):
        """Draw a predicate as text."""
        ctx.save()
        
        ctx.set_font_size(12)
        text = primitive.relation_name
        text_extents = ctx.text_extents(text)
        
        text_x = primitive.x + (primitive.width - text_extents.width) / 2
        text_y = primitive.y + (primitive.height + text_extents.height) / 2
        
        ctx.move_to(text_x, text_y)
        ctx.set_source_rgb(0, 0, 0)
        ctx.show_text(text)
        
        ctx.restore()
    
    def draw_edge(self, ctx, primitive):
        """Draw an edge as a heavy line."""
        ctx.save()
        
        ctx.set_line_width(2.0)
        ctx.set_source_rgb(0, 0, 0)
        
        ctx.move_to(primitive.start_x, primitive.start_y)
        ctx.line_to(primitive.end_x, primitive.end_y)
        ctx.stroke()
        
        ctx.restore()
    
    def verify_area_containment(self, graph, primitives) -> bool:
        """Verify that area containment is logically correct."""
        
        print("🔍 Verifying area containment...")
        
        # Create lookup tables
        cut_bounds = {}
        element_positions = {}
        
        for primitive in primitives:
            if hasattr(primitive, 'cut_id'):
                cut_bounds[primitive.cut_id] = {
                    'x': primitive.x,
                    'y': primitive.y,
                    'width': primitive.width,
                    'height': primitive.height
                }
            elif hasattr(primitive, 'vertex_id'):
                element_positions[primitive.vertex_id] = {
                    'x': primitive.x,
                    'y': primitive.y,
                    'logical_area': primitive.area_id
                }
            elif hasattr(primitive, 'relation_name'):
                element_positions[primitive.predicate_id] = {
                    'x': primitive.x,
                    'y': primitive.y,
                    'width': primitive.width,
                    'height': primitive.height,
                    'logical_area': primitive.area_id
                }
        
        # Check containment for each element
        containment_errors = 0
        
        for element_id, pos in element_positions.items():
            logical_area = pos['logical_area']
            
            if logical_area == graph.sheet:
                # Element should be outside all cuts
                for cut_id, cut_bounds_data in cut_bounds.items():
                    if self.point_inside_bounds(pos, cut_bounds_data):
                        print(f"❌ {element_id} should be at sheet level but is inside cut {cut_id}")
                        containment_errors += 1
            else:
                # Element should be inside its logical area (cut)
                if logical_area in cut_bounds:
                    if not self.point_inside_bounds(pos, cut_bounds[logical_area]):
                        print(f"❌ {element_id} should be inside cut {logical_area} but is outside")
                        containment_errors += 1
                    else:
                        print(f"✅ {element_id} correctly inside cut {logical_area}")
                else:
                    print(f"⚠️  Cannot verify containment for {element_id} in area {logical_area}")
        
        if containment_errors == 0:
            print("✅ All area containment constraints satisfied!")
            return True
        else:
            print(f"❌ {containment_errors} area containment errors found")
            return False
    
    def point_inside_bounds(self, point, bounds) -> bool:
        """Check if a point is inside rectangular bounds."""
        if 'width' in point:  # Rectangle (predicate)
            return (point['x'] >= bounds['x'] and 
                   point['x'] + point['width'] <= bounds['x'] + bounds['width'] and
                   point['y'] >= bounds['y'] and 
                   point['y'] + point['height'] <= bounds['y'] + bounds['height'])
        else:  # Point (vertex)
            return (point['x'] >= bounds['x'] and 
                   point['x'] <= bounds['x'] + bounds['width'] and
                   point['y'] >= bounds['y'] and 
                   point['y'] <= bounds['y'] + bounds['height'])


if __name__ == "__main__":
    tester = ConstraintLayoutTester()
    results = tester.run_all_tests()
