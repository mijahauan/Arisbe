"""
Tests for Style-Aware Layout Engine

Validates that style specifications affect spatial requirements while
maintaining iron-clad guarantees of spatial-logical correspondence.
"""

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from layout_engine_styled import (
    StyleAwareLayoutEngine, ElementDistribution, LigatureRouting
)
from style_loader import StyleSpecification, load_default_style
from egif_parser_dau import parse_egif


class TestStyleAwareLayoutEngine(unittest.TestCase):
    """Test suite for style-aware layout engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.default_style = load_default_style()
        
        # Create a modified style for testing
        large_style_data = self.default_style.raw_style_data.copy()
        large_style_data['vertex']['radius'] = 12.0
        large_style_data['predicate']['char_width_estimate'] = 80.0
        large_style_data['predicate']['height_estimate'] = 30.0
        large_style_data['layout']['element_spacing'] = 60.0
        large_style_data['layout']['cut_padding'] = 30.0
        
        self.large_style = StyleSpecification.from_json_data(large_style_data)
        
    def test_style_affects_spatial_requirements(self):
        """Test that different styles produce different spatial layouts"""
        egif = '*x (Human x) (Mortal x)'
        egi = parse_egif(egif)
        
        # Layout with default style
        engine_default = StyleAwareLayoutEngine(self.default_style)
        layout_default = engine_default.compute_layout(egi)
        
        # Layout with large style
        engine_large = StyleAwareLayoutEngine(self.large_style)
        layout_large = engine_large.compute_layout(egi)
        
        # Layouts should be different due to style differences
        default_viewport = layout_default.viewport_bounds
        large_viewport = layout_large.viewport_bounds
        
        # Large style should require more space
        self.assertGreater(large_viewport.width, default_viewport.width)
        self.assertGreater(large_viewport.height, default_viewport.height)
        
        # But both should have same logical structure
        self.assertEqual(len(layout_default.vertex_positions), len(layout_large.vertex_positions))
        self.assertEqual(len(layout_default.predicate_positions), len(layout_large.predicate_positions))
    
    def test_iron_clad_guarantees_maintained(self):
        """Test that style changes don't break iron-clad guarantees"""
        egif = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'
        egi = parse_egif(egif)
        
        # Test with various styles
        compact_data = self.default_style.raw_style_data.copy()
        compact_data['layout']['element_spacing'] = 20.0
        compact_data['layout']['cut_padding'] = 10.0
        compact_style = StyleSpecification.from_json_data(compact_data)
        
        huge_data = self.default_style.raw_style_data.copy()
        huge_data['vertex']['radius'] = 20.0
        huge_data['predicate']['char_width_estimate'] = 120.0
        huge_style = StyleSpecification.from_json_data(huge_data)
        
        styles = [
            self.default_style,
            self.large_style,
            compact_style,
            huge_style
        ]
        
        for style in styles:
            with self.subTest(style=style):
                engine = StyleAwareLayoutEngine(style)
                layout = engine.compute_layout(egi)
                
                # Iron-clad guarantees must hold
                self.assertEqual(len(layout.vertex_positions), len(egi.V))
                self.assertEqual(len(layout.predicate_positions), len(egi.E))
                self.assertEqual(len(layout.cut_bounds), len(egi.Cut))
                
                # Spatial-logical correspondence
                for area_id, elements in layout.area_hierarchy.items():
                    if area_id in layout.cut_bounds:
                        area_bounds = layout.cut_bounds[area_id]
                        
                        for elem_id in elements:
                            if elem_id in layout.vertex_positions:
                                pos = layout.vertex_positions[elem_id]
                                self.assertTrue(area_bounds.contains_point(pos, margin=5),
                                              f"Vertex {elem_id} outside area {area_id} with style {style}")
                            
                            if elem_id in layout.predicate_positions:
                                pos = layout.predicate_positions[elem_id]
                                self.assertTrue(area_bounds.contains_point(pos, margin=5),
                                              f"Predicate {elem_id} outside area {area_id} with style {style}")
    
    def test_element_distribution_algorithms(self):
        """Test different element distribution algorithms"""
        egif = '*x *y *z (P x) (Q y) (R z)'
        egi = parse_egif(egif)
        
        engine = StyleAwareLayoutEngine(self.default_style)
        
        distributions = [
            ElementDistribution(layout_algorithm="grid"),
            ElementDistribution(layout_algorithm="circular"),
            ElementDistribution(layout_algorithm="linear"),
            ElementDistribution(layout_algorithm="organic")
        ]
        
        layouts = []
        for dist in distributions:
            layout = engine.compute_layout(egi, distribution=dist)
            layouts.append(layout)
            
            # Should have all elements positioned
            self.assertEqual(len(layout.vertex_positions), len(egi.V))
            self.assertEqual(len(layout.predicate_positions), len(egi.E))
        
        # Different distributions should produce different positions
        for i in range(len(layouts)):
            for j in range(i + 1, len(layouts)):
                layout1, layout2 = layouts[i], layouts[j]
                
                # At least some positions should be different
                positions_different = False
                for vertex_id in layout1.vertex_positions:
                    if vertex_id in layout2.vertex_positions:
                        pos1 = layout1.vertex_positions[vertex_id]
                        pos2 = layout2.vertex_positions[vertex_id]
                        if abs(pos1.x - pos2.x) > 1.0 or abs(pos1.y - pos2.y) > 1.0:
                            positions_different = True
                            break
                
                self.assertTrue(positions_different, 
                              f"Distributions {i} and {j} produced identical positions")
    
    def test_ligature_routing_algorithms(self):
        """Test different ligature routing algorithms"""
        egif = '*x (Human x) (Mortal x)'
        egi = parse_egif(egif)
        
        engine = StyleAwareLayoutEngine(self.default_style)
        
        routings = [
            LigatureRouting(routing_algorithm="direct"),
            LigatureRouting(routing_algorithm="manhattan"),
            LigatureRouting(routing_algorithm="orthogonal"),
            LigatureRouting(routing_algorithm="bezier")
        ]
        
        for routing in routings:
            with self.subTest(routing=routing.routing_algorithm):
                layout = engine.compute_layout(egi, ligature_routing=routing)
                
                # Should have ligature paths
                self.assertGreater(len(layout.ligature_paths), 0)
                
                # Each path should have points
                for path in layout.ligature_paths:
                    self.assertGreaterEqual(len(path.points), 2)
                    
                    # First and last points should be at element positions
                    start_point = path.points[0]
                    end_point = path.points[-1]
                    
                    # One should be predicate position, other vertex position
                    pred_pos = layout.predicate_positions.get(path.predicate_id)
                    vertex_pos = layout.vertex_positions.get(path.vertex_id)
                    
                    if pred_pos and vertex_pos:
                        # Allow some tolerance for positioning
                        start_matches_pred = (abs(start_point.x - pred_pos.x) < 5.0 and 
                                            abs(start_point.y - pred_pos.y) < 5.0)
                        end_matches_vertex = (abs(end_point.x - vertex_pos.x) < 5.0 and 
                                            abs(end_point.y - vertex_pos.y) < 5.0)
                        
                        start_matches_vertex = (abs(start_point.x - vertex_pos.x) < 5.0 and 
                                              abs(start_point.y - vertex_pos.y) < 5.0)
                        end_matches_pred = (abs(end_point.x - pred_pos.x) < 5.0 and 
                                          abs(end_point.y - pred_pos.y) < 5.0)
                        
                        self.assertTrue(
                            (start_matches_pred and end_matches_vertex) or 
                            (start_matches_vertex and end_matches_pred),
                            f"Ligature path endpoints don't match element positions"
                        )
    
    def test_grid_distribution_properties(self):
        """Test specific properties of grid distribution"""
        egif = '*a *b *c *d (P a) (Q b) (R c) (S d)'
        egi = parse_egif(egif)
        
        engine = StyleAwareLayoutEngine(self.default_style)
        distribution = ElementDistribution(
            layout_algorithm="grid",
            max_columns=2,
            column_spacing=50.0,
            row_spacing=40.0
        )
        
        layout = engine.compute_layout(egi, distribution=distribution, optimize_readability=False)
        
        # Should have all predicates positioned
        self.assertEqual(len(layout.predicate_positions), 4)
        
        # Check grid properties
        predicate_positions = list(layout.predicate_positions.values())
        
        # Should have elements in roughly grid formation
        x_coords = sorted(set(pos.x for pos in predicate_positions))
        y_coords = sorted(set(pos.y for pos in predicate_positions))
        
        # With max_columns=2, should have at most 2 distinct x coordinates
        self.assertLessEqual(len(x_coords), 2)
        
        # Should have multiple rows for 4 elements with 2 columns
        self.assertGreaterEqual(len(y_coords), 2)
    
    def test_style_hints_generation(self):
        """Test that style hints are properly generated"""
        egif = '*x (Human x)'
        egi = parse_egif(egif)
        
        custom_data = self.default_style.raw_style_data.copy()
        custom_data['vertex']['radius'] = 15.0
        custom_data['predicate']['char_width_estimate'] = 100.0
        custom_data['global']['font_size'] = 16.0
        custom_style = StyleSpecification.from_json_data(custom_data)
        
        engine = StyleAwareLayoutEngine(custom_style)
        layout = engine.compute_layout(egi)
        
        # Should have style hints
        self.assertIn('style_specification', layout.style_hints)
        style_spec = layout.style_hints['style_specification']
        
        # Should match custom style
        self.assertEqual(style_spec['vertex_radius'], 15.0)
        self.assertEqual(style_spec['predicate_width'], 100.0)
        self.assertEqual(style_spec['font_size'], 16.0)
        
        # Should indicate style-aware engine
        self.assertEqual(layout.style_hints['layout_engine'], 'style-aware')
        self.assertTrue(layout.style_hints['style_aware'])


if __name__ == '__main__':
    unittest.main()
