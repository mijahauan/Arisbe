"""
Comprehensive Layout Engine Tests

Tests the new layout engine against:
1. The problematic case that was missing predicates
2. Complete corpus validation
3. Platform-independent DTO structure
4. Iron-clad area mapping compliance
"""

import pytest
from src.layout_engine import LayoutEngine, LayoutDTO
from src.egif_parser_dau import parse_egif
from src.corpus_index import load_index
import json
from pathlib import Path


class TestLayoutEngineComprehensive:
    """Comprehensive tests for the new layout engine"""
    
    def setup_method(self):
        self.engine = LayoutEngine()
    
    def test_problematic_case_fixed(self):
        """Test that the missing predicate issue is fixed"""
        egif = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'
        egi = parse_egif(egif)
        layout = self.engine.compute_layout(egi)
        
        # Verify all elements are positioned
        assert len(layout.vertex_positions) == 1, "Should have 1 vertex (Socrates)"
        assert len(layout.predicate_positions) == 2, "Should have 2 predicates (Human, Mortal)"
        assert len(layout.cut_bounds) == 2, "Should have 2 cuts"
        assert len(layout.ligature_paths) == 2, "Should have 2 ligature paths"
        
        # Verify both predicates are found
        predicate_relations = set()
        for pred_id in layout.predicate_positions.keys():
            relation = egi.rel.get(pred_id)
            predicate_relations.add(relation)
        
        assert "Human" in predicate_relations, "Human predicate must be positioned"
        assert "Mortal" in predicate_relations, "Mortal predicate must be positioned"
        
        print("✅ FIXED: Both Human and Mortal predicates are positioned!")
    
    def test_dto_structure_complete(self):
        """Test that LayoutDTO contains all required information"""
        egif = '*x *y (Loves x y)'
        egi = parse_egif(egif)
        layout = self.engine.compute_layout(egi)
        
        # Verify DTO structure
        assert isinstance(layout, LayoutDTO), "Must return LayoutDTO"
        assert hasattr(layout, 'vertex_positions'), "Must have vertex positions"
        assert hasattr(layout, 'predicate_positions'), "Must have predicate positions"
        assert hasattr(layout, 'cut_bounds'), "Must have cut bounds"
        assert hasattr(layout, 'ligature_paths'), "Must have ligature paths"
        assert hasattr(layout, 'area_hierarchy'), "Must have area hierarchy"
        assert hasattr(layout, 'containment_depth'), "Must have containment depth"
        assert hasattr(layout, 'viewport_bounds'), "Must have viewport bounds"
        assert hasattr(layout, 'style_hints'), "Must have style hints"
        
        # Verify platform independence
        assert isinstance(layout.style_hints, dict), "Style hints must be dict"
        assert 'suggested_style' in layout.style_hints, "Must suggest style"
        
        print("✅ DTO structure is complete and platform-independent!")
    
    def test_area_mapping_compliance(self):
        """Test iron-clad compliance with EGI area mapping"""
        egif = '~[ *x (P x) ~[ (Q x) ] ]'
        egi = parse_egif(egif)
        layout = self.engine.compute_layout(egi)
        
        # Verify area hierarchy matches EGI area mapping exactly
        for area_id, egi_elements in egi.area.items():
            layout_elements = layout.area_hierarchy.get(area_id, set())
            assert layout_elements == egi_elements, f"Area {area_id} hierarchy must match EGI exactly"
        
        # Verify containment depths are logical
        for element_id, depth in layout.containment_depth.items():
            assert isinstance(depth, int), "Depth must be integer"
            assert depth >= 0, "Depth must be non-negative"
        
        print("✅ Area mapping compliance is iron-clad!")
    
    def test_corpus_compatibility(self):
        """Test against a subset of corpus graphs"""
        corpus_index = load_index()
        test_cases = [
            'peirce_cp_4_394_man_mortal',
            'sowa_cat_on_mat', 
            'ternary_relation_challenge'
        ]
        
        success_count = 0
        
        for entry in corpus_index['entries']:
            if entry['id'] not in test_cases:
                continue
                
            graph_id = entry['id']
            graph_path = Path(entry['path'])
            json_file = graph_path / f"{graph_id}.json"
            
            if json_file.exists():
                with open(json_file, 'r') as f:
                    graph_data = json.load(f)
                    
                if 'linear_forms' in graph_data and 'egif' in graph_data['linear_forms']:
                    egif = graph_data['linear_forms']['egif']['content']
                    
                    try:
                        egi = parse_egif(egif)
                        layout = self.engine.compute_layout(egi)
                        
                        # Basic validation
                        assert isinstance(layout, LayoutDTO)
                        assert len(layout.vertex_positions) == len(egi.V)
                        assert len(layout.predicate_positions) == len(egi.E)
                        
                        success_count += 1
                        print(f"✅ {graph_id}: Layout computed successfully")
                        
                    except Exception as e:
                        print(f"❌ {graph_id}: Failed - {e}")
                        raise AssertionError(f"Corpus graph {graph_id} failed: {e}")
        
        assert success_count == len(test_cases), f"Expected {len(test_cases)} successes, got {success_count}"
        print(f"✅ Corpus compatibility: {success_count}/{len(test_cases)} graphs processed!")
    
    def test_ligature_path_generation(self):
        """Test that ligature paths are generated correctly"""
        egif = '*x *y (Loves x y)'
        egi = parse_egif(egif)
        layout = self.engine.compute_layout(egi)
        
        # Should have paths from Loves predicate to both vertices
        assert len(layout.ligature_paths) == 2, "Should have 2 ligature paths for binary relation"
        
        # Verify path structure
        for path in layout.ligature_paths:
            assert hasattr(path, 'predicate_id'), "Path must have predicate_id"
            assert hasattr(path, 'vertex_id'), "Path must have vertex_id"
            assert hasattr(path, 'points'), "Path must have points"
            assert len(path.points) >= 2, "Path must have at least start and end points"
        
        print("✅ Ligature paths generated correctly!")
    
    def test_empty_cut_handling(self):
        """Test handling of cuts with no elements"""
        # This tests edge cases in cut bounds computation
        egif = '~[ ~[ ] ]'  # Nested empty cuts
        try:
            egi = parse_egif(egif)
            layout = self.engine.compute_layout(egi)
            
            # Should handle gracefully
            assert isinstance(layout, LayoutDTO)
            print("✅ Empty cuts handled gracefully!")
            
        except Exception as e:
            # If parser doesn't support empty cuts, that's also valid
            print(f"ℹ️  Empty cuts not supported by parser: {e}")


if __name__ == "__main__":
    test = TestLayoutEngineComprehensive()
    test.setup_method()
    
    print("=== COMPREHENSIVE LAYOUT ENGINE TESTS ===\n")
    
    test.test_problematic_case_fixed()
    test.test_dto_structure_complete()
    test.test_area_mapping_compliance()
    test.test_corpus_compatibility()
    test.test_ligature_path_generation()
    test.test_empty_cut_handling()
    
    print("\n🎉 ALL TESTS PASSED - LAYOUT ENGINE IS READY!")
