"""
Basic Integration Tests for Enhanced Dau-Compliant System

This test suite validates the basic integration of the enhanced system
components that we know are working correctly.

Tests focus on:
- Function symbol parsing and generation
- CLIF round-trip integrity
- Cross-cut validation
- Basic semantic validation
"""

import unittest
import sys

from eg_types import Entity, Predicate
from graph import EGGraph
from clif_parser import CLIFParser
from clif_generator import CLIFGenerator
from cross_cut_validator import CrossCutValidator


class TestBasicIntegration(unittest.TestCase):
    """Test basic integration of core system components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.clif_parser = CLIFParser()
        self.clif_generator = CLIFGenerator()
        self.cross_cut_validator = CrossCutValidator()
    
    def test_function_symbol_round_trip(self):
        """Test function symbol round-trip integrity."""
        # Create graph with function symbols
        clif_text = "(and (Person Socrates) (Wise (fatherOf Socrates)))"
        parse_result = self.clif_parser.parse(clif_text)
        self.assertIsNotNone(parse_result.graph)
        
        # Check function predicates were created
        function_predicates = [p for p in parse_result.graph.predicates.values() 
                             if p.predicate_type == 'function']
        self.assertGreater(len(function_predicates), 0)
        
        # Generate CLIF
        clif_result = self.clif_generator.generate(parse_result.graph)
        self.assertIsInstance(clif_result.clif_text, str)
        self.assertIn("Person", clif_result.clif_text)
        self.assertIn("fatherOf", clif_result.clif_text)
        
        # Parse the generated CLIF
        round_trip_result = self.clif_parser.parse(clif_result.clif_text)
        self.assertIsNotNone(round_trip_result.graph)
        
        # Verify function symbols preserved
        rt_function_predicates = [p for p in round_trip_result.graph.predicates.values() 
                                if p.predicate_type == 'function']
        self.assertEqual(len(rt_function_predicates), len(function_predicates))
    
    def test_nested_function_symbols(self):
        """Test nested function symbol handling."""
        # Create graph with nested functions
        clif_text = "(Person (fatherOf (teacherOf Aristotle)))"
        parse_result = self.clif_parser.parse(clif_text)
        self.assertIsNotNone(parse_result.graph)
        
        # Check multiple function predicates were created
        function_predicates = [p for p in parse_result.graph.predicates.values() 
                             if p.predicate_type == 'function']
        self.assertGreaterEqual(len(function_predicates), 2)  # fatherOf and teacherOf
        
        # Round-trip test
        clif_result = self.clif_generator.generate(parse_result.graph)
        round_trip_result = self.clif_parser.parse(clif_result.clif_text)
        self.assertIsNotNone(round_trip_result.graph)
        
        # Verify nested structure preserved
        rt_function_predicates = [p for p in round_trip_result.graph.predicates.values() 
                                if p.predicate_type == 'function']
        self.assertEqual(len(rt_function_predicates), len(function_predicates))
    
    def test_cross_cut_validation_basic(self):
        """Test basic cross-cut validation functionality."""
        # Create graph with potential cross-cuts
        clif_text = """
        (and 
            (Person Socrates)
            (exists (x) (and (Wise x) (= x Socrates)))
        )
        """
        parse_result = self.clif_parser.parse(clif_text)
        self.assertIsNotNone(parse_result.graph)
        
        # Cross-cut validation should work without errors
        try:
            cross_cut_analysis = self.cross_cut_validator.analyze_cross_cuts(parse_result.graph)
            self.assertIsNotNone(cross_cut_analysis)
        except Exception as e:
            self.fail(f"Cross-cut validation should work without errors: {e}")
    
    def test_complex_clif_parsing(self):
        """Test parsing of complex CLIF expressions."""
        # Create complex CLIF with functions, quantifiers, and equality
        clif_text = """
        (and 
            (Person Socrates)
            (Wise (fatherOf Socrates))
            (= (fatherOf Socrates) (teacherOf Plato))
            (exists (x) (Student x))
            (forall (y) (implies (Student y) (Person y)))
        )
        """
        parse_result = self.clif_parser.parse(clif_text)
        self.assertIsNotNone(parse_result.graph)
        
        # Should have entities, predicates, and contexts
        self.assertGreater(len(parse_result.graph.entities), 0)
        self.assertGreater(len(parse_result.graph.predicates), 0)
        self.assertGreater(len(parse_result.graph.contexts), 0)
        
        # Should have function predicates
        function_predicates = [p for p in parse_result.graph.predicates.values() 
                             if p.predicate_type == 'function']
        self.assertGreater(len(function_predicates), 0)
    
    def test_clif_generation_completeness(self):
        """Test that CLIF generation produces complete output."""
        # Create comprehensive graph
        clif_text = """
        (and 
            (Person Socrates)
            (Wise (fatherOf Socrates))
            (exists (x) (and (Person x) (Student x)))
        )
        """
        parse_result = self.clif_parser.parse(clif_text)
        self.assertIsNotNone(parse_result.graph)
        
        # Generate CLIF
        clif_result = self.clif_generator.generate(parse_result.graph)
        self.assertIsInstance(clif_result.clif_text, str)
        
        # Should contain all key elements
        self.assertIn("Person", clif_result.clif_text)
        self.assertIn("Socrates", clif_result.clif_text)
        self.assertIn("fatherOf", clif_result.clif_text)
        self.assertIn("exists", clif_result.clif_text)
        self.assertIn("Student", clif_result.clif_text)
    
    def test_error_handling(self):
        """Test error handling in parsing and generation."""
        # Test invalid CLIF
        invalid_clif = "(and (Person) (Wise"  # Incomplete
        parse_result = self.clif_parser.parse(invalid_clif)
        self.assertGreater(len(parse_result.errors), 0)
        
        # Test empty graph generation
        empty_graph = EGGraph.create_empty()
        clif_result = self.clif_generator.generate(empty_graph)
        self.assertIsInstance(clif_result.clif_text, str)
    
    def test_entity_predicate_architecture(self):
        """Test that Entity-Predicate architecture is maintained."""
        # Create graph manually
        graph = EGGraph.create_empty()
        
        # Add entities
        socrates = Entity.create(name="Socrates", entity_type="constant")
        graph = graph.add_entity(socrates)
        
        # Add predicates
        person_pred = Predicate.create(name="Person", entities={socrates.id}, arity=1)
        graph = graph.add_predicate(person_pred)
        
        # Verify structure
        self.assertEqual(len(graph.entities), 1)
        self.assertEqual(len(graph.predicates), 1)
        
        # Should generate valid CLIF
        clif_result = self.clif_generator.generate(graph)
        self.assertIn("Person", clif_result.clif_text)
        self.assertIn("Socrates", clif_result.clif_text)
    
    def test_function_predicate_structure(self):
        """Test function predicate structure and properties."""
        # Parse function expression
        clif_text = "(Person (fatherOf Socrates))"
        parse_result = self.clif_parser.parse(clif_text)
        self.assertIsNotNone(parse_result.graph)
        
        # Find function predicate
        function_predicates = [p for p in parse_result.graph.predicates.values() 
                             if p.predicate_type == 'function']
        self.assertGreater(len(function_predicates), 0)
        
        # Check function predicate properties
        father_pred = next((p for p in function_predicates if p.name == 'fatherOf'), None)
        self.assertIsNotNone(father_pred)
        self.assertEqual(father_pred.predicate_type, 'function')
        self.assertIsNotNone(father_pred.return_entity)
        self.assertEqual(father_pred.arity, 2)  # argument + return entity
    
    def test_system_integration_workflow(self):
        """Test complete system integration workflow."""
        # Start with CLIF
        clif_text = "(and (Person Socrates) (Wise (fatherOf Socrates)))"
        
        # 1. Parse
        parse_result = self.clif_parser.parse(clif_text)
        self.assertIsNotNone(parse_result.graph)
        
        # 2. Validate structure
        self.assertGreater(len(parse_result.graph.entities), 0)
        self.assertGreater(len(parse_result.graph.predicates), 0)
        
        # 3. Check function symbols
        function_predicates = [p for p in parse_result.graph.predicates.values() 
                             if p.predicate_type == 'function']
        self.assertGreater(len(function_predicates), 0)
        
        # 4. Cross-cut analysis
        cross_cut_analysis = self.cross_cut_validator.analyze_cross_cuts(parse_result.graph)
        self.assertIsNotNone(cross_cut_analysis)
        
        # 5. Generate CLIF
        clif_result = self.clif_generator.generate(parse_result.graph)
        self.assertIsInstance(clif_result.clif_text, str)
        
        # 6. Round-trip validation
        round_trip_result = self.clif_parser.parse(clif_result.clif_text)
        self.assertIsNotNone(round_trip_result.graph)
        
        # 7. Verify preservation
        rt_function_predicates = [p for p in round_trip_result.graph.predicates.values() 
                                if p.predicate_type == 'function']
        self.assertEqual(len(rt_function_predicates), len(function_predicates))
    
    def test_performance_basic(self):
        """Test basic performance of integrated system."""
        # Create moderately complex graph
        clif_text = """
        (and 
            (Person Socrates)
            (Person Plato)
            (Wise Socrates)
            (Student Plato)
            (= (fatherOf Socrates) (teacherOf Plato))
            (exists (x) (Person x))
        )
        """
        
        # Time the workflow
        import time
        start_time = time.time()
        
        # Complete workflow
        parse_result = self.clif_parser.parse(clif_text)
        self.assertIsNotNone(parse_result.graph)
        
        cross_cut_analysis = self.cross_cut_validator.analyze_cross_cuts(parse_result.graph)
        self.assertIsNotNone(cross_cut_analysis)
        
        clif_result = self.clif_generator.generate(parse_result.graph)
        self.assertIsInstance(clif_result.clif_text, str)
        
        round_trip_result = self.clif_parser.parse(clif_result.clif_text)
        self.assertIsNotNone(round_trip_result.graph)
        
        end_time = time.time()
        workflow_time = end_time - start_time
        
        # Should complete quickly
        self.assertLess(workflow_time, 5.0, "Basic workflow should complete within 5 seconds")


if __name__ == '__main__':
    # Run the basic integration tests
    unittest.main(verbosity=2)

