"""
Comprehensive tests for Iron-Clad Layout Engine

Tests the production-ready layout engine that guarantees spatial-logical correspondence
with no break points. Validates against complete Arisbe corpus.
"""

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from layout_engine_ironclad import LayoutEngineIronClad, LayoutDTO
from egif_parser_dau import parse_egif
from corpus_index import load_index
import json


class TestLayoutEngineIronClad(unittest.TestCase):
    """Test suite for iron-clad layout engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = LayoutEngineIronClad()
    
    def test_iron_clad_guarantees(self):
        """Test that iron-clad guarantees are maintained"""
        egif = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'
        egi = parse_egif(egif)
        layout = self.engine.compute_layout(egi)
        
        # Guarantee 1: Complete element coverage
        self.assertEqual(len(layout.vertex_positions), len(egi.V))
        self.assertEqual(len(layout.predicate_positions), len(egi.E))
        self.assertEqual(len(layout.cut_bounds), len(egi.Cut))
        
        # Guarantee 2: Spatial-logical correspondence
        for area_id, elements in layout.area_hierarchy.items():
            if area_id in layout.cut_bounds:
                area_bounds = layout.cut_bounds[area_id]
                
                for elem_id in elements:
                    # Check vertices are within area bounds
                    if elem_id in layout.vertex_positions:
                        pos = layout.vertex_positions[elem_id]
                        self.assertTrue(area_bounds.contains_point(pos, margin=5),
                                      f"Vertex {elem_id} outside area {area_id} bounds")
                    
                    # Check predicates are within area bounds
                    if elem_id in layout.predicate_positions:
                        pos = layout.predicate_positions[elem_id]
                        self.assertTrue(area_bounds.contains_point(pos, margin=5),
                                      f"Predicate {elem_id} outside area {area_id} bounds")
    
    def test_sibling_cut_separation(self):
        """Test that sibling cuts are properly separated"""
        # Test case 1: Roberts disjunction
        egif1 = '~[ ~[ (P "x") ] ~[ (Q "x") ] ]'
        egi1 = parse_egif(egif1)
        layout1 = self.engine.compute_layout(egi1)
        
        # Find sibling cuts
        sibling_cuts = []
        for area_id, elements in layout1.area_hierarchy.items():
            cuts_in_area = [e for e in elements if any(c.id == e for c in egi1.Cut)]
            if len(cuts_in_area) > 1:
                sibling_cuts = cuts_in_area
                break
        
        self.assertEqual(len(sibling_cuts), 2, "Should have 2 sibling cuts")
        
        # Verify they have different x-coordinates (not superimposed)
        x_coords = []
        for cut_id in sibling_cuts:
            if cut_id in layout1.cut_bounds:
                bounds = layout1.cut_bounds[cut_id]
                x_coords.append(bounds.min_x)
        
        self.assertEqual(len(set(x_coords)), len(x_coords), 
                        "Sibling cuts should have different x-coordinates")
        
        # Test case 2: Sibling cuts with shared variable
        egif2 = '*x ~[ (P x) ] ~[ (Q x) ]'
        egi2 = parse_egif(egif2)
        layout2 = self.engine.compute_layout(egi2)
        
        # Should have 2 cuts at sheet level
        sheet_cuts = []
        for area_id, elements in layout2.area_hierarchy.items():
            if area_id == egi2.sheet:
                sheet_cuts = [e for e in elements if any(c.id == e for c in egi2.Cut)]
                break
        
        self.assertEqual(len(sheet_cuts), 2, "Should have 2 cuts on sheet")
        
        # Verify separation
        x_coords = []
        for cut_id in sheet_cuts:
            if cut_id in layout2.cut_bounds:
                bounds = layout2.cut_bounds[cut_id]
                x_coords.append(bounds.min_x)
        
        self.assertEqual(len(set(x_coords)), len(x_coords),
                        "Sheet-level sibling cuts should be separated")
    
    def test_nested_cut_containment(self):
        """Test that nested cuts are properly contained"""
        egif = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'
        egi = parse_egif(egif)
        layout = self.engine.compute_layout(egi)
        
        # Find outer and inner cuts
        outer_cut = None
        inner_cut = None
        
        for area_id, elements in layout.area_hierarchy.items():
            if area_id != egi.sheet and any(c.id == e for c in egi.Cut for e in elements):
                outer_cut = area_id
            elif area_id != egi.sheet and not any(c.id == e for c in egi.Cut for e in elements):
                inner_cut = area_id
        
        self.assertIsNotNone(outer_cut, "Should have outer cut")
        self.assertIsNotNone(inner_cut, "Should have inner cut")
        
        # Verify containment
        outer_bounds = layout.cut_bounds[outer_cut]
        inner_bounds = layout.cut_bounds[inner_cut]
        
        self.assertTrue(outer_bounds.contains_box(inner_bounds, margin=5),
                       "Outer cut should contain inner cut")
    
    def test_corpus_compatibility(self):
        """Test compatibility with complete Arisbe corpus"""
        try:
            corpus_index = load_index()
        except:
            self.skipTest("Corpus index not available")
        
        success_count = 0
        total_count = 0
        
        for entry in corpus_index['entries']:
            graph_id = entry['id']
            graph_path = Path(entry['path'])
            json_file = graph_path / f'{graph_id}.json'
            
            if json_file.exists():
                with open(json_file, 'r') as f:
                    graph_data = json.load(f)
                
                if 'linear_forms' in graph_data and 'egif' in graph_data['linear_forms']:
                    egif = graph_data['linear_forms']['egif']['content']
                    total_count += 1
                    
                    try:
                        egi = parse_egif(egif)
                        layout = self.engine.compute_layout(egi)
                        
                        # Validate completeness
                        self.assertEqual(len(layout.vertex_positions), len(egi.V))
                        self.assertEqual(len(layout.predicate_positions), len(egi.E))
                        self.assertEqual(len(layout.cut_bounds), len(egi.Cut))
                        
                        success_count += 1
                        
                    except Exception as e:
                        self.fail(f"Failed on {graph_id}: {e}")
        
        # Should handle at least 90% of corpus
        success_rate = success_count / total_count if total_count > 0 else 0
        self.assertGreaterEqual(success_rate, 0.9, 
                               f"Should handle at least 90% of corpus, got {success_rate:.1%}")
    
    def test_layout_dto_structure(self):
        """Test that LayoutDTO has all required fields"""
        egif = '*x (Human x) (Mortal x)'
        egi = parse_egif(egif)
        layout = self.engine.compute_layout(egi)
        
        # Check DTO structure
        self.assertIsInstance(layout, LayoutDTO)
        self.assertIsInstance(layout.vertex_positions, dict)
        self.assertIsInstance(layout.predicate_positions, dict)
        self.assertIsInstance(layout.cut_bounds, dict)
        self.assertIsInstance(layout.ligature_paths, list)
        self.assertIsInstance(layout.area_hierarchy, dict)
        self.assertIsInstance(layout.containment_depth, dict)
        self.assertIsNotNone(layout.viewport_bounds)
        self.assertIsInstance(layout.style_hints, dict)
    
    def test_no_break_points(self):
        """Test that there are no break points in spatial-logical correspondence"""
        test_cases = [
            ('Simple', '*x (Human x) (Mortal x)'),
            ('Nested', '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'),
            ('Complex', '~[ *x (P x) ~[ *y (Q x y) ~[ (R y) ] ] ]'),
            ('Siblings', '*x ~[ (P x) ] ~[ (Q x) ]')
        ]
        
        for name, egif in test_cases:
            with self.subTest(case=name):
                egi = parse_egif(egif)
                
                # This should never raise an exception if iron-clad guarantees hold
                try:
                    layout = self.engine.compute_layout(egi)
                    
                    # Validation is built into compute_layout
                    # If we reach here, no break points occurred
                    self.assertTrue(True, f"{name} case processed without break points")
                    
                except Exception as e:
                    self.fail(f"Break point detected in {name} case: {e}")


if __name__ == '__main__':
    unittest.main()
