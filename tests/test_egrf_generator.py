#!/usr/bin/env python3

"""
Tests for EGRF Generator functionality.

Tests the conversion from EG-CL-Manus2 data structures to EGRF format,
ensuring logical integrity is preserved.
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph import EGGraph
from eg_types import Entity, Predicate, Context
from egrf import EGRFGenerator, LayoutConstraints, EGRFSerializer


class TestEGRFGenerator(unittest.TestCase):
    """Test cases for EGRF generator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = EGRFGenerator()
        
    def test_empty_graph_generation(self):
        """Test generating EGRF from empty graph."""
        eg_graph = EGGraph.create_empty()
        egrf_doc = self.generator.generate(eg_graph)
        
        # Should have root context but no entities or predicates
        self.assertEqual(len(egrf_doc.entities), 0)
        self.assertEqual(len(egrf_doc.predicates), 0)
        self.assertEqual(len(egrf_doc.contexts), 1)  # Root context
        
        # Should have valid metadata
        self.assertEqual(egrf_doc.metadata.title, "Generated from EG-CL-Manus2")
        self.assertIsNotNone(egrf_doc.metadata.description)
    
    def test_simple_entity_predicate_generation(self):
        """Test generating EGRF from simple entity-predicate graph."""
        # Create simple graph: Socrates is a Person
        eg_graph = EGGraph.create_empty()
        
        # Add entity
        socrates = Entity.create(name="Socrates", entity_type="constant")
        eg_graph = eg_graph.add_entity(socrates)
        
        # Add predicate
        person_pred = Predicate.create(name="Person", entities=[socrates.id])
        eg_graph = eg_graph.add_predicate(person_pred)
        
        # Generate EGRF
        egrf_doc = self.generator.generate(eg_graph)
        
        # Validate structure
        self.assertEqual(len(egrf_doc.entities), 1)
        self.assertEqual(len(egrf_doc.predicates), 1)
        self.assertEqual(len(egrf_doc.contexts), 1)
        
        # Validate entity
        entity = egrf_doc.entities[0]
        self.assertEqual(entity.name, "Socrates")
        self.assertEqual(entity.type, "constant")
        self.assertIsNotNone(entity.visual.path)
        
        # Validate predicate
        predicate = egrf_doc.predicates[0]
        self.assertEqual(predicate.name, "Person")
        self.assertEqual(predicate.arity, 1)
        self.assertIn(str(socrates.id), predicate.connected_entities)
        self.assertIsNotNone(predicate.visual.position)
        self.assertTrue(len(predicate.connections) > 0)
        
        # Validate CLIF generation
        clif = egrf_doc.semantics.logical_form.get("clif_equivalent")
        self.assertIsNotNone(clif)
        self.assertIn("Person", clif)
        self.assertIn("Socrates", clif)
    
    def test_multiple_predicates_generation(self):
        """Test generating EGRF from entity with multiple predicates."""
        # Create graph: Socrates is a Person and is Mortal
        eg_graph = EGGraph.create_empty()
        
        # Add entity
        socrates = Entity.create(name="Socrates", entity_type="constant")
        eg_graph = eg_graph.add_entity(socrates)
        
        # Add predicates
        person_pred = Predicate.create(name="Person", entities=[socrates.id])
        mortal_pred = Predicate.create(name="Mortal", entities=[socrates.id])
        
        eg_graph = eg_graph.add_predicate(person_pred)
        eg_graph = eg_graph.add_predicate(mortal_pred)
        
        # Generate EGRF
        egrf_doc = self.generator.generate(eg_graph)
        
        # Validate structure
        self.assertEqual(len(egrf_doc.entities), 1)
        self.assertEqual(len(egrf_doc.predicates), 2)
        
        # Validate entity connects to both predicates
        entity = egrf_doc.entities[0]
        self.assertIsNotNone(entity.visual.path)
        
        # Validate both predicates have connections
        for predicate in egrf_doc.predicates:
            self.assertIn(str(socrates.id), predicate.connected_entities)
            self.assertTrue(len(predicate.connections) > 0)
        
        # Validate CLIF includes both predicates
        clif = egrf_doc.semantics.logical_form.get("clif_equivalent")
        self.assertIn("Person", clif)
        self.assertIn("Mortal", clif)
        self.assertIn("and", clif)
    
    def test_layout_constraints_preservation(self):
        """Test that layout constraints are properly applied."""
        constraints = LayoutConstraints(
            canvas_width=1000.0,
            canvas_height=800.0,
            predicate_width=80.0,
            predicate_height=40.0
        )
        
        generator = EGRFGenerator(constraints)
        
        # Create simple graph
        eg_graph = EGGraph.create_empty()
        socrates = Entity.create(name="Socrates", entity_type="constant")
        eg_graph = eg_graph.add_entity(socrates)
        
        person_pred = Predicate.create(name="Person", entities=[socrates.id])
        eg_graph = eg_graph.add_predicate(person_pred)
        
        # Generate EGRF
        egrf_doc = generator.generate(eg_graph)
        
        # Validate constraints are applied
        predicate = egrf_doc.predicates[0]
        self.assertEqual(predicate.visual.size.width, 80.0)
        self.assertEqual(predicate.visual.size.height, 40.0)
        
        # Validate canvas dimensions
        self.assertEqual(egrf_doc.canvas.width, 1000.0)
        self.assertEqual(egrf_doc.canvas.height, 800.0)
    
    def test_serialization_roundtrip(self):
        """Test that generated EGRF can be serialized and deserialized."""
        # Create simple graph
        eg_graph = EGGraph.create_empty()
        socrates = Entity.create(name="Socrates", entity_type="constant")
        eg_graph = eg_graph.add_entity(socrates)
        
        person_pred = Predicate.create(name="Person", entities=[socrates.id])
        eg_graph = eg_graph.add_predicate(person_pred)
        
        # Generate EGRF
        egrf_doc = self.generator.generate(eg_graph)
        
        # Serialize to JSON
        json_str = EGRFSerializer.to_json(egrf_doc)
        self.assertIsInstance(json_str, str)
        self.assertIn("Socrates", json_str)
        self.assertIn("Person", json_str)
        
        # Deserialize back
        egrf_doc_restored = EGRFSerializer.from_json(json_str, validate=False)
        
        # Validate restoration (entities and predicates are dicts in simplified implementation)
        self.assertEqual(len(egrf_doc_restored.entities), 1)
        self.assertEqual(len(egrf_doc_restored.predicates), 1)
        
        # Check entity data (as dictionary)
        entity_data = egrf_doc_restored.entities[0]
        if isinstance(entity_data, dict):
            self.assertEqual(entity_data.get("name"), "Socrates")
        else:
            self.assertEqual(entity_data.name, "Socrates")
        
        # Check predicate data (as dictionary)
        predicate_data = egrf_doc_restored.predicates[0]
        if isinstance(predicate_data, dict):
            self.assertEqual(predicate_data.get("name"), "Person")
        else:
            self.assertEqual(predicate_data.name, "Person")
    
    def test_hierarchical_consistency(self):
        """Test that hierarchical structure is preserved."""
        # This test would be expanded when we have more complex context handling
        eg_graph = EGGraph.create_empty()
        
        # Add entity and predicate
        socrates = Entity.create(name="Socrates", entity_type="constant")
        eg_graph = eg_graph.add_entity(socrates)
        
        person_pred = Predicate.create(name="Person", entities=[socrates.id])
        eg_graph = eg_graph.add_predicate(person_pred)
        
        # Generate EGRF
        egrf_doc = self.generator.generate(eg_graph)
        
        # Validate context structure
        self.assertEqual(len(egrf_doc.contexts), 1)
        root_context = egrf_doc.contexts[0]
        self.assertEqual(root_context.type, "sheet_of_assertion")
        self.assertIsNone(root_context.parent_context)
        self.assertEqual(root_context.nesting_level, 0)


class TestLayoutConstraints(unittest.TestCase):
    """Test cases for layout constraints."""
    
    def test_default_constraints(self):
        """Test default layout constraints."""
        constraints = LayoutConstraints()
        
        self.assertEqual(constraints.canvas_width, 800.0)
        self.assertEqual(constraints.canvas_height, 600.0)
        self.assertEqual(constraints.predicate_width, 60.0)
        self.assertEqual(constraints.predicate_height, 30.0)
    
    def test_custom_constraints(self):
        """Test custom layout constraints."""
        constraints = LayoutConstraints(
            canvas_width=1200.0,
            canvas_height=900.0,
            predicate_width=100.0,
            predicate_height=50.0,
            entity_spacing=150.0
        )
        
        self.assertEqual(constraints.canvas_width, 1200.0)
        self.assertEqual(constraints.canvas_height, 900.0)
        self.assertEqual(constraints.predicate_width, 100.0)
        self.assertEqual(constraints.predicate_height, 50.0)
        self.assertEqual(constraints.entity_spacing, 150.0)


if __name__ == '__main__':
    unittest.main()

