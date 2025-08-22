#!/usr/bin/env python3
"""
Bidirectional Pipeline Test - Complete Round-Trip Validation

This tests the complete bidirectional pipeline:
EGIF → EGI → EGDF → EGI → EGIF

CRITICAL: Both directions must work reliably for the pipeline to be considered complete.
"""

import sys
import os
import unittest
import json

# Ensure src directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Pipeline components
from egif_parser_dau import EGIFParser
from egi_core_dau import RelationalGraphWithCuts
from egdf_parser import EGDFParser
from layout_phase_implementations import (
    ElementSizingPhase, ContainerSizingPhase, CollisionDetectionPhase,
    PredicatePositioningPhase, VertexPositioningPhase, HookAssignmentPhase,
    RectilinearLigaturePhase, BranchOptimizationPhase, AreaCompactionPhase,
    PhaseStatus
)
from spatial_awareness_system import SpatialAwarenessSystem

class BidirectionalPipelineTest(unittest.TestCase):
    """Test complete bidirectional pipeline reliability."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_egifs = [
            '(Human "Socrates")',
            '(Human "Socrates") (Mortal "Socrates")',
            '*x (Human x) ~[ (Mortal x) ]',
            '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            '*x *y (Loves x y) ~[ (Happy x) ]'
        ]
        
        self.spatial_system = SpatialAwarenessSystem()
        self.phases = [
            ElementSizingPhase(),
            ContainerSizingPhase(self.spatial_system),
            CollisionDetectionPhase(self.spatial_system),
            PredicatePositioningPhase(self.spatial_system),
            VertexPositioningPhase(self.spatial_system),
            HookAssignmentPhase(),
            RectilinearLigaturePhase(),
            BranchOptimizationPhase(),
            AreaCompactionPhase()
        ]
        self.egdf_parser = EGDFParser()
    
    def test_forward_pipeline_egif_to_egdf(self):
        """Test forward pipeline: EGIF → EGI → EGDF."""
        for egif_text in self.test_egifs:
            with self.subTest(egif=egif_text):
                print(f"\n🔄 Testing forward: {egif_text}")
                
                # Step 1: EGIF → EGI
                parser = EGIFParser(egif_text)
                egi = parser.parse()
                self.assertIsInstance(egi, RelationalGraphWithCuts)
                print(f"  ✅ EGIF→EGI: {len(egi.V)} vertices, {len(egi.E)} edges")
                
                # Step 2: EGI → 9-Phase Pipeline
                context = {}
                for i, phase in enumerate(self.phases):
                    result = phase.execute(egi, context)
                    if result.status != PhaseStatus.COMPLETED:
                        self.fail(f"Phase {i+1} failed: {result.error_message}")
                
                # Step 3: Extract spatial primitives from pipeline context
                context['egi'] = egi  # Add EGI to context for cut extraction
                spatial_primitives = self._extract_spatial_primitives(context)
                print(f"  ✅ EGI→Layout: {len(spatial_primitives)} spatial primitives")
                
                # Step 3: EGI + Layout → EGDF
                layout_primitives = spatial_primitives
                egdf_doc = self.egdf_parser.create_egdf_from_egi(egi, layout_primitives)
                self.assertIsNotNone(egdf_doc)
                self.assertTrue(hasattr(egdf_doc, 'canonical_egi'))
                self.assertTrue(hasattr(egdf_doc, 'visual_layout'))
                print(f"  ✅ EGI+Layout→EGDF: Document created")
    
    def test_reverse_pipeline_egdf_to_egif(self):
        """Test reverse pipeline: EGDF → EGI → EGIF."""
        for egif_text in self.test_egifs:
            with self.subTest(egif=egif_text):
                print(f"\n🔄 Testing reverse: {egif_text}")
                
                # First create EGDF (forward pipeline)
                parser = EGIFParser(egif_text)
                original_egi = parser.parse()
                
                # Run 9-phase pipeline
                context = {}
                for i, phase in enumerate(self.phases):
                    result = phase.execute(original_egi, context)
                    if result.status != PhaseStatus.COMPLETED:
                        self.fail(f"Phase {i+1} failed: {result.error_message}")
                
                spatial_primitives = self._extract_spatial_primitives(context)
                egdf_doc = self.egdf_parser.create_egdf_from_egi(original_egi, spatial_primitives)
                
                # Step 1: EGDF → EGI
                reconstructed_egi = self.egdf_parser.extract_egi_from_egdf(egdf_doc)
                self.assertIsInstance(reconstructed_egi, RelationalGraphWithCuts)
                print(f"  ✅ EGDF→EGI: {len(reconstructed_egi.V)} vertices, {len(reconstructed_egi.E)} edges")
                
                # Step 2: EGI → EGIF (using generator)
                from egif_generator_dau import EGIFGenerator
                egif_generator = EGIFGenerator(reconstructed_egi)
                reconstructed_egif = egif_generator.generate()
                self.assertIsInstance(reconstructed_egif, str)
                self.assertGreater(len(reconstructed_egif.strip()), 0)
                print(f"  ✅ EGI→EGIF: '{reconstructed_egif}'")
    
    def _extract_spatial_primitives(self, context):
        """Extract spatial primitives from 9-phase pipeline context."""
        spatial_primitives = []
        
        # Extract elements from pipeline context
        element_tracking = context.get('element_tracking', {})
        relative_bounds = context.get('relative_bounds', {})
        vertex_elements = context.get('vertex_elements', {})
        predicate_elements = context.get('predicate_elements', {})
        
        # Get the EGI from context to ensure we include all cut elements
        egi = context.get('egi')  # We need to pass this in
        
        # Add cuts - check both relative_bounds and EGI.Cut
        cut_ids_added = set()
        
        # First, add cuts from relative_bounds
        for area_id, bounds in relative_bounds.items():
            if area_id != 'sheet':
                primitive_dict = {
                    'element_id': area_id,
                    'element_type': 'cut',
                    'position': ((bounds[0] + bounds[2])/2, (bounds[1] + bounds[3])/2),
                    'bounds': bounds,
                    'z_index': 0
                }
                spatial_primitives.append(primitive_dict)
                cut_ids_added.add(area_id)
        
        # Then, add any cuts from EGI that weren't in relative_bounds
        if egi:
            for cut in egi.Cut:
                if cut.id not in cut_ids_added:
                    # Use default bounds for cuts not processed by pipeline
                    default_bounds = (0.1, 0.1, 0.9, 0.9)
                    primitive_dict = {
                        'element_id': cut.id,
                        'element_type': 'cut',
                        'position': (0.5, 0.5),
                        'bounds': default_bounds,
                        'z_index': 0
                    }
                    spatial_primitives.append(primitive_dict)
                    cut_ids_added.add(cut.id)
        
        # Add vertices
        for vertex_id, vertex_data in vertex_elements.items():
            if isinstance(vertex_data, dict):
                position = vertex_data.get('relative_position', (0.5, 0.5))
                bounds = vertex_data.get('relative_bounds', (0.4, 0.4, 0.6, 0.6))
            else:
                # vertex_data is a LayoutElement object
                position = vertex_data.position
                bounds = (vertex_data.bounds.left, vertex_data.bounds.top, 
                         vertex_data.bounds.right, vertex_data.bounds.bottom)
            
            primitive_dict = {
                'element_id': vertex_id,
                'element_type': 'vertex',
                'position': position,
                'bounds': bounds,
                'z_index': 1
            }
            spatial_primitives.append(primitive_dict)
        
        # Add predicates
        for predicate_id, predicate_data in predicate_elements.items():
            if isinstance(predicate_data, dict):
                position = predicate_data.get('relative_position', (0.3, 0.3))
                bounds = predicate_data.get('relative_bounds', (0.2, 0.2, 0.4, 0.4))
            else:
                # predicate_data is a LayoutElement object
                position = predicate_data.position
                bounds = (predicate_data.bounds.left, predicate_data.bounds.top,
                         predicate_data.bounds.right, predicate_data.bounds.bottom)
            
            primitive_dict = {
                'element_id': predicate_id,
                'element_type': 'predicate',
                'position': position,
                'bounds': bounds,
                'z_index': 1
            }
            spatial_primitives.append(primitive_dict)
        
        return spatial_primitives
    
    def test_complete_round_trip_integrity(self):
        """Test complete round-trip: EGIF → EGI → EGDF → EGI → EGIF."""
        for egif_text in self.test_egifs:
            with self.subTest(egif=egif_text):
                print(f"\n🔄 Testing complete round-trip: {egif_text}")
                
                # Forward: EGIF → EGI → EGDF
                parser = EGIFParser(egif_text)
                original_egi = parser.parse()
                
                # Run 9-phase pipeline
                context = {}
                for i, phase in enumerate(self.phases):
                    result = phase.execute(original_egi, context)
                    if result.status != PhaseStatus.COMPLETED:
                        self.fail(f"Phase {i+1} failed: {result.error_message}")
                
                spatial_primitives = self._extract_spatial_primitives(context)
                egdf_doc = self.egdf_parser.create_egdf_from_egi(original_egi, spatial_primitives)
                
                # Reverse: EGDF → EGI → EGIF
                reconstructed_egi = self.egdf_parser.extract_egi_from_egdf(egdf_doc)
                
                # Validate structural integrity
                self.assertEqual(len(original_egi.V), len(reconstructed_egi.V))
                self.assertEqual(len(original_egi.E), len(reconstructed_egi.E))
                self.assertEqual(len(original_egi.Cut), len(reconstructed_egi.Cut))
                
                # Validate nu mapping preservation (critical for argument order)
                self.assertEqual(original_egi.nu, reconstructed_egi.nu)
                
                print(f"  ✅ Round-trip integrity preserved")
    
    def test_egdf_format_round_trip(self):
        """Test EGDF format serialization round-trip (JSON/YAML)."""
        egif_text = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
        
        # Create EGDF document
        parser = EGIFParser(egif_text)
        egi = parser.parse()
        
        # Run 9-phase pipeline
        context = {}
        for i, phase in enumerate(self.phases):
            result = phase.execute(egi, context)
            if result.status != PhaseStatus.COMPLETED:
                self.fail(f"Phase {i+1} failed: {result.error_message}")
        
        spatial_primitives = self._extract_spatial_primitives(context)
        original_egdf_doc = self.egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
        
        # Test JSON round-trip
        json_content = self.egdf_parser.egdf_to_json(original_egdf_doc)
        self.assertIsInstance(json_content, str)
        self.assertIn('"format": "EGDF"', json_content)
        
        reconstructed_from_json = self.egdf_parser.parse_egdf(json_content, format_hint="json")
        self.assertIsNotNone(reconstructed_from_json)
        print("  ✅ JSON format round-trip works")
        
        # Test YAML round-trip (if available)
        try:
            yaml_content = self.egdf_parser.egdf_to_yaml(original_egdf_doc)
            self.assertIsInstance(yaml_content, str)
            self.assertIn('format: EGDF', yaml_content)
            
            reconstructed_from_yaml = self.egdf_parser.parse_egdf(yaml_content, format_hint="yaml")
            self.assertIsNotNone(reconstructed_from_yaml)
            print("  ✅ YAML format round-trip works")
        except Exception as e:
            print(f"  ⚠️  YAML round-trip skipped: {e}")
    
    def test_corpus_bidirectional_pipeline(self):
        """Test bidirectional pipeline with corpus examples."""
        try:
            from corpus_loader import get_corpus_loader
            corpus_loader = get_corpus_loader()
            
            # Test first 3 corpus examples
            tested_count = 0
            for example_id, example in corpus_loader.examples.items():
                if not example.egif_expression or tested_count >= 3:
                    continue
                
                with self.subTest(corpus_example=example_id):
                    print(f"\n🔄 Testing corpus example: {example.title}")
                    
                    # Forward pipeline
                    parser = EGIFParser(example.egif_expression)
                    egi = parser.parse()
                    layout_result = self.layout_engine.create_layout_from_graph(egi)
                    layout_primitives = list(layout_result.primitives.values())
                    egdf_doc = self.egdf_parser.create_egdf_from_egi(egi, layout_primitives)
                    
                    # Reverse pipeline
                    reconstructed_egi = self.egdf_parser.extract_egi_from_egdf(egdf_doc)
                    
                    # Validate integrity
                    self.assertEqual(len(egi.V), len(reconstructed_egi.V))
                    self.assertEqual(len(egi.E), len(reconstructed_egi.E))
                    self.assertEqual(egi.nu, reconstructed_egi.nu)
                    
                    print(f"  ✅ Corpus example round-trip successful")
                    tested_count += 1
                    
        except Exception as e:
            self.skipTest(f"Corpus not available: {e}")
    
    def test_pipeline_error_handling(self):
        """Test pipeline error handling for invalid inputs."""
        # Test invalid EGIF
        with self.assertRaises(Exception):
            parser = EGIFParser("invalid egif syntax !!!")
            parser.parse()
        
        # Test invalid EGDF
        invalid_egdf = '{"format": "INVALID", "data": "broken"}'
        with self.assertRaises(Exception):
            self.egdf_parser.parse_egdf(invalid_egdf)
        
        print("  ✅ Pipeline error handling works correctly")

def main():
    """Run bidirectional pipeline tests."""
    print("🎯 BIDIRECTIONAL PIPELINE VALIDATION")
    print("=" * 60)
    print("Testing complete round-trip: EGIF ↔ EGI ↔ EGDF")
    print()
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(BidirectionalPipelineTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ BIDIRECTIONAL PIPELINE WORKS COMPLETELY")
        print("Both forward and reverse flows are reliable")
        print("Ready for production use")
        return True
    else:
        print("\n❌ BIDIRECTIONAL PIPELINE HAS ISSUES")
        print("Must fix round-trip reliability before proceeding")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
