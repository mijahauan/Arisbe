#!/usr/bin/env python3

"""
Performance Test for EGRF Round-trip Conversion (Fixed)

Tests the performance of EGRF generation and parsing with large graphs.
Properly structured for pytest.
"""

import unittest
import time
from typing import List, Dict

# Import EG-CL-Manus2 types
from graph import EGGraph
from eg_types import Entity, Predicate
from egrf import EGRFGenerator, EGRFParser


class TestEGRFPerformance(unittest.TestCase):
    """Performance tests for EGRF round-trip conversion."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = EGRFGenerator()
        self.parser = EGRFParser(validation_enabled=False)  # Disable validation for performance
    
    def create_large_graph(self, num_entities: int, num_predicates: int) -> EGGraph:
        """Create a large graph for performance testing."""
        graph = EGGraph.create_empty()
        entities = []
        
        # Add entities
        for i in range(num_entities):
            entity = Entity.create(name=f"Entity_{i}", entity_type="constant")
            graph = graph.add_entity(entity, graph.root_context_id)
            entities.append(entity)
        
        # Add predicates with varying arities
        for i in range(num_predicates):
            # Vary predicate arity (1-3 entities per predicate)
            arity = (i % 3) + 1
            connected_entities = entities[i % len(entities):i % len(entities) + arity]
            entity_ids = [e.id for e in connected_entities]
            
            predicate = Predicate.create(name=f"Predicate_{i}", entities=entity_ids)
            graph = graph.add_predicate(predicate, graph.root_context_id)
        
        return graph
    
    def run_performance_test(self, num_entities: int, num_predicates: int) -> Dict:
        """Run performance test for specific graph size."""
        # Create large graph
        start_time = time.time()
        graph = self.create_large_graph(num_entities, num_predicates)
        creation_time = time.time() - start_time
        
        # Generate EGRF
        start_time = time.time()
        egrf_doc = self.generator.generate(graph)
        generation_time = time.time() - start_time
        
        # Parse back to EG-CL-Manus2
        start_time = time.time()
        result = self.parser.parse(egrf_doc)
        parsing_time = time.time() - start_time
        
        # Validate result
        self.assertTrue(result.is_successful, f"Parsing failed: {result.errors}")
        
        reconstructed_graph = result.graph
        self.assertEqual(len(graph.entities), len(reconstructed_graph.entities))
        self.assertEqual(len(graph.predicates), len(reconstructed_graph.predicates))
        
        total_time = creation_time + generation_time + parsing_time
        
        return {
            'entities': num_entities,
            'predicates': num_predicates,
            'creation_time': creation_time,
            'generation_time': generation_time,
            'parsing_time': parsing_time,
            'total_time': total_time,
            'success': result.is_successful,
            'warnings': len(result.warnings),
            'errors': len(result.errors)
        }
    
    def test_small_graph_performance(self):
        """Test performance with small graphs (10 entities, 10 predicates)."""
        result = self.run_performance_test(10, 10)
        
        # Performance assertions
        self.assertLess(result['total_time'], 1.0, "Small graph should process in under 1 second")
        self.assertTrue(result['success'])
        self.assertEqual(result['errors'], 0)
    
    def test_medium_graph_performance(self):
        """Test performance with medium graphs (50 entities, 50 predicates)."""
        result = self.run_performance_test(50, 50)
        
        # Performance assertions
        self.assertLess(result['total_time'], 2.0, "Medium graph should process in under 2 seconds")
        self.assertTrue(result['success'])
        self.assertEqual(result['errors'], 0)
    
    def test_large_graph_performance(self):
        """Test performance with large graphs (100 entities, 100 predicates)."""
        result = self.run_performance_test(100, 100)
        
        # Performance assertions
        self.assertLess(result['total_time'], 5.0, "Large graph should process in under 5 seconds")
        self.assertTrue(result['success'])
        self.assertEqual(result['errors'], 0)
    
    def test_entity_heavy_graph_performance(self):
        """Test performance with entity-heavy graphs (200 entities, 50 predicates)."""
        result = self.run_performance_test(200, 50)
        
        # Performance assertions
        self.assertLess(result['total_time'], 5.0, "Entity-heavy graph should process in under 5 seconds")
        self.assertTrue(result['success'])
        self.assertEqual(result['errors'], 0)
    
    def test_predicate_heavy_graph_performance(self):
        """Test performance with predicate-heavy graphs (50 entities, 200 predicates)."""
        result = self.run_performance_test(50, 200)
        
        # Performance assertions
        self.assertLess(result['total_time'], 5.0, "Predicate-heavy graph should process in under 5 seconds")
        self.assertTrue(result['success'])
        self.assertEqual(result['errors'], 0)
    
    def test_performance_scaling(self):
        """Test that performance scales reasonably with graph size."""
        # Test different sizes
        small_result = self.run_performance_test(10, 10)
        medium_result = self.run_performance_test(50, 50)
        
        # Performance should scale reasonably (not exponentially)
        size_ratio = (50 * 50) / (10 * 10)  # 25x larger
        time_ratio = medium_result['total_time'] / small_result['total_time']
        
        # Time ratio should be less than 100x (allowing for some overhead)
        self.assertLess(time_ratio, 100, 
                       f"Performance scaling too poor: {time_ratio}x time for {size_ratio}x size")
    
    def test_generation_vs_parsing_performance(self):
        """Test that generation and parsing have similar performance characteristics."""
        result = self.run_performance_test(100, 100)
        
        generation_time = result['generation_time']
        parsing_time = result['parsing_time']
        
        # Neither should be more than 10x slower than the other
        if generation_time > 0 and parsing_time > 0:
            ratio = max(generation_time, parsing_time) / min(generation_time, parsing_time)
            self.assertLess(ratio, 10, 
                           f"Generation/parsing performance too imbalanced: {ratio}x difference")


if __name__ == '__main__':
    unittest.main(verbosity=2)

