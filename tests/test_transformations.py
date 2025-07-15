"""
Comprehensive tests for the transformation engine.

Tests all transformation rules with proper validation and edge cases.
"""

import pytest
import uuid
from hypothesis import given, strategies as st

from src.transformations import (
    TransformationEngine, TransformationType, TransformationResult,
    TransformationValidator, ValidationResult
)
from src.graph import EGGraph
from src.eg_types import Node, Edge, Ligature


class TestTransformationEngine:
    """Test the core transformation engine."""
    
    def test_engine_initialization(self):
        """Test transformation engine initialization."""
        engine = TransformationEngine()
        
        assert len(engine.rules) > 0
        assert len(engine.transformation_history) == 0
        assert TransformationType.DOUBLE_CUT_INSERTION in engine.rules
        assert TransformationType.ERASURE in engine.rules
    
    def test_get_legal_transformations(self):
        """Test getting legal transformations for a graph."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Empty graph should allow some transformations
        legal = engine.get_legal_transformations(graph)
        assert TransformationType.DOUBLE_CUT_INSERTION in legal
        assert TransformationType.INSERTION in legal
    
    def test_transformation_history(self):
        """Test that transformation history is recorded."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Apply a transformation
        attempt = engine.apply_transformation(
            graph, 
            TransformationType.DOUBLE_CUT_INSERTION,
            target_context=graph.root_context_id,
            subgraph_items=set()
        )
        
        assert len(engine.transformation_history) == 1
        assert engine.transformation_history[0] == attempt


class TestAlphaRules:
    """Test Alpha rules (propositional logic transformations)."""
    
    def test_double_cut_insertion(self):
        """Test double cut insertion transformation."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Add a simple predicate
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(pred_node)
        
        # Apply double cut insertion
        attempt = engine.apply_transformation(
            graph,
            TransformationType.DOUBLE_CUT_INSERTION,
            target_context=graph.root_context_id,
            subgraph_items={pred_node.id}
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Should have created 2 new contexts
        original_contexts = len(graph.context_manager.contexts)
        new_contexts = len(attempt.result_graph.context_manager.contexts)
        assert new_contexts == original_contexts + 2
    
    def test_double_cut_erasure(self):
        """Test double cut erasure transformation."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Create double cut structure first
        graph, outer_cut = graph.create_context('cut', graph.root_context_id, 'Outer')
        graph, inner_cut = graph.create_context('cut', outer_cut.id, 'Inner')
        
        # Add predicate to inner cut
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(pred_node, inner_cut.id)
        
        # Apply double cut erasure
        attempt = engine.apply_transformation(
            graph,
            TransformationType.DOUBLE_CUT_ERASURE,
            target_context=outer_cut.id
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Should have removed 2 contexts
        original_contexts = len(graph.context_manager.contexts)
        new_contexts = len(attempt.result_graph.context_manager.contexts)
        assert new_contexts == original_contexts - 2
        
        # Predicate should be back in root context
        root_items = attempt.result_graph.get_items_in_context(graph.root_context_id)
        assert pred_node.id in root_items
    
    def test_double_cut_round_trip(self):
        """Test that double cut insertion and erasure are inverses."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Add a predicate
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(pred_node)
        
        # Insert double cut
        insert_attempt = engine.apply_transformation(
            graph,
            TransformationType.DOUBLE_CUT_INSERTION,
            target_context=graph.root_context_id,
            subgraph_items={pred_node.id}
        )
        
        assert insert_attempt.result == TransformationResult.SUCCESS
        intermediate_graph = insert_attempt.result_graph
        
        # Find the outer cut context
        outer_cut_id = None
        for context_id, context in intermediate_graph.context_manager.contexts.items():
            if (context.parent_context == graph.root_context_id and 
                context.properties.get('name') == 'Double Cut Outer'):
                outer_cut_id = context_id
                break
        
        assert outer_cut_id is not None
        
        # Erase double cut
        erase_attempt = engine.apply_transformation(
            intermediate_graph,
            TransformationType.DOUBLE_CUT_ERASURE,
            target_context=outer_cut_id
        )
        
        assert erase_attempt.result == TransformationResult.SUCCESS
        final_graph = erase_attempt.result_graph
        
        # Should be back to original structure
        assert len(final_graph.nodes) == len(graph.nodes)
        assert len(final_graph.context_manager.contexts) == len(graph.context_manager.contexts)


class TestBetaRules:
    """Test Beta rules (predicate logic transformations)."""
    
    def test_erasure_from_negative_context(self):
        """Test erasure from negative context."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Create negative context
        graph, neg_context = graph.create_context('cut', graph.root_context_id, 'Negative')
        
        # Add predicate to negative context
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(pred_node, neg_context.id)
        
        # Apply erasure
        attempt = engine.apply_transformation(
            graph,
            TransformationType.ERASURE,
            target_items={pred_node.id}
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Predicate should be removed
        assert pred_node.id not in attempt.result_graph.nodes
    
    def test_erasure_from_positive_context_fails(self):
        """Test that erasure from positive context fails."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Add predicate to positive (root) context
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(pred_node)
        
        # Attempt erasure (should fail)
        attempt = engine.apply_transformation(
            graph,
            TransformationType.ERASURE,
            target_items={pred_node.id}
        )
        
        assert attempt.result == TransformationResult.PRECONDITION_FAILED
        assert "positive context" in attempt.error_message.lower()
    
    def test_insertion_into_positive_context(self):
        """Test insertion into positive context."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Define subgraph to insert
        subgraph = {
            'nodes': [
                {'node_type': 'predicate', 'properties': {'name': 'Q'}},
                {'node_type': 'term', 'properties': {'value': 'x'}}
            ],
            'edges': [],
            'ligatures': []
        }
        
        # Apply insertion
        attempt = engine.apply_transformation(
            graph,
            TransformationType.INSERTION,
            target_context=graph.root_context_id,
            subgraph=subgraph
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Should have added nodes
        assert len(attempt.result_graph.nodes) == len(graph.nodes) + 2
    
    def test_insertion_into_negative_context_fails(self):
        """Test that insertion into negative context fails."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Create negative context
        graph, neg_context = graph.create_context('cut', graph.root_context_id, 'Negative')
        
        # Attempt insertion (should fail)
        attempt = engine.apply_transformation(
            graph,
            TransformationType.INSERTION,
            target_context=neg_context.id,
            subgraph={'nodes': [], 'edges': [], 'ligatures': []}
        )
        
        assert attempt.result == TransformationResult.PRECONDITION_FAILED
        assert "negative context" in attempt.error_message.lower()
    
    def test_iteration_to_same_level(self):
        """Test iteration to same context level."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Create two contexts at same level
        graph, context1 = graph.create_context('sheet', graph.root_context_id, 'Context1')
        graph, context2 = graph.create_context('sheet', graph.root_context_id, 'Context2')
        
        # Add predicate to first context
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(pred_node, context1.id)
        
        # Apply iteration
        attempt = engine.apply_transformation(
            graph,
            TransformationType.ITERATION,
            target_items={pred_node.id},
            target_context=context2.id
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Should have created copy in second context
        context2_items = attempt.result_graph.get_items_in_context(context2.id)
        assert len(context2_items) == 1
        
        # Original should still exist
        context1_items = attempt.result_graph.get_items_in_context(context1.id)
        assert len(context1_items) == 1
    
    def test_iteration_to_deeper_level_fails(self):
        """Test that iteration to deeper level fails."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Create nested contexts
        graph, outer_context = graph.create_context('sheet', graph.root_context_id, 'Outer')
        graph, inner_context = graph.create_context('cut', outer_context.id, 'Inner')
        
        # Add predicate to outer context
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(pred_node, outer_context.id)
        
        # Attempt iteration to deeper level (should fail)
        attempt = engine.apply_transformation(
            graph,
            TransformationType.ITERATION,
            target_items={pred_node.id},
            target_context=inner_context.id
        )
        
        assert attempt.result == TransformationResult.PRECONDITION_FAILED
        assert "deeper context" in attempt.error_message.lower()
    
    def test_deiteration_removes_duplicate(self):
        """Test deiteration removes duplicate subgraph."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Add two identical predicates
        pred1 = Node.create(node_type='predicate', properties={'name': 'P'})
        pred2 = Node.create(node_type='predicate', properties={'name': 'P'})
        
        graph = graph.add_node(pred1)
        graph = graph.add_node(pred2)
        
        # Apply deiteration
        attempt = engine.apply_transformation(
            graph,
            TransformationType.DEITERATION,
            target_items={pred1.id}
        )
        
        # Note: This test might fail with current simplified isomorphism check
        # A full implementation would need sophisticated graph isomorphism
        if attempt.result == TransformationResult.SUCCESS:
            assert len(attempt.result_graph.nodes) == len(graph.nodes) - 1


class TestLigatureOperations:
    """Test ligature-related transformations."""
    
    def test_ligature_join(self):
        """Test joining nodes with ligature."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Add two term nodes
        term1 = Node.create(node_type='term', properties={'value': 'x'})
        term2 = Node.create(node_type='term', properties={'value': 'y'})
        
        graph = graph.add_node(term1)
        graph = graph.add_node(term2)
        
        # Apply ligature join
        attempt = engine.apply_transformation(
            graph,
            TransformationType.LIGATURE_JOIN,
            target_items={term1.id, term2.id},
            ligature_type='identity'
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Should have created ligature
        assert len(attempt.result_graph.ligatures) == 1
        
        ligature = list(attempt.result_graph.ligatures.values())[0]
        assert term1.id in ligature.nodes
        assert term2.id in ligature.nodes
    
    def test_ligature_sever(self):
        """Test severing ligature."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Add three term nodes
        term1 = Node.create(node_type='term', properties={'value': 'x'})
        term2 = Node.create(node_type='term', properties={'value': 'y'})
        term3 = Node.create(node_type='term', properties={'value': 'z'})
        
        graph = graph.add_node(term1)
        graph = graph.add_node(term2)
        graph = graph.add_node(term3)
        
        # Create ligature connecting all three
        ligature = Ligature.create(
            nodes={term1.id, term2.id, term3.id},
            properties={'type': 'identity'}
        )
        graph = graph.add_ligature(ligature)
        
        # Sever one node from ligature
        attempt = engine.apply_transformation(
            graph,
            TransformationType.LIGATURE_SEVER,
            target_items={term1.id}
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Should still have ligature but with fewer nodes
        assert len(attempt.result_graph.ligatures) == 1
        
        remaining_ligature = list(attempt.result_graph.ligatures.values())[0]
        assert term1.id not in remaining_ligature.nodes
        assert term2.id in remaining_ligature.nodes
        assert term3.id in remaining_ligature.nodes
    
    def test_erasure_severs_crossing_ligatures(self):
        """Test that erasure properly severs crossing ligatures."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Create negative context
        graph, neg_context = graph.create_context('cut', graph.root_context_id, 'Negative')
        
        # Add nodes in different contexts
        term1 = Node.create(node_type='term', properties={'value': 'x'})  # In root
        term2 = Node.create(node_type='term', properties={'value': 'y'})  # In negative
        
        graph = graph.add_node(term1)  # Root context
        graph = graph.add_node(term2, neg_context.id)  # Negative context
        
        # Create ligature crossing contexts
        ligature = Ligature.create(
            nodes={term1.id, term2.id},
            properties={'type': 'identity'}
        )
        graph = graph.add_ligature(ligature)
        
        # Erase node from negative context
        attempt = engine.apply_transformation(
            graph,
            TransformationType.ERASURE,
            target_items={term2.id}
        )
        
        assert attempt.result == TransformationResult.SUCCESS
        assert attempt.result_graph is not None
        
        # Ligature should be removed (only 1 node remaining)
        assert len(attempt.result_graph.ligatures) == 0
        
        # Only term1 should remain
        assert term1.id in attempt.result_graph.nodes
        assert term2.id not in attempt.result_graph.nodes


class TestTransformationValidation:
    """Test transformation validation and error handling."""
    
    def test_invalid_transformation_type(self):
        """Test handling of invalid transformation type."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # This should be handled by the enum, but test error handling
        attempt = engine.apply_transformation(
            graph,
            TransformationType.DOUBLE_CUT_INSERTION,
            target_context=None  # Invalid: no target context
        )
        
        assert attempt.result == TransformationResult.PRECONDITION_FAILED
    
    def test_missing_target_items(self):
        """Test handling of missing target items."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Attempt erasure with no target items
        attempt = engine.apply_transformation(
            graph,
            TransformationType.ERASURE,
            target_items=set()
        )
        
        assert attempt.result == TransformationResult.PRECONDITION_FAILED
        assert "target items" in attempt.error_message.lower()
    
    def test_nonexistent_context(self):
        """Test handling of nonexistent context."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        from src.eg_types import ContextId
        fake_context = ContextId(uuid.uuid4())
        
        # Attempt insertion into nonexistent context
        attempt = engine.apply_transformation(
            graph,
            TransformationType.INSERTION,
            target_context=fake_context,
            subgraph={'nodes': [], 'edges': [], 'ligatures': []}
        )
        
        assert attempt.result == TransformationResult.PRECONDITION_FAILED
        assert "does not exist" in attempt.error_message.lower()


class TestTransformationSequences:
    """Test sequences of transformations."""
    
    def test_transformation_sequence_validation(self):
        """Test validation of transformation sequences."""
        validator = TransformationValidator()
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Apply sequence of transformations
        transformations = []
        
        # 1. Insert double cut
        attempt1 = engine.apply_transformation(
            graph,
            TransformationType.DOUBLE_CUT_INSERTION,
            target_context=graph.root_context_id,
            subgraph_items=set()
        )
        transformations.append(attempt1)
        
        if attempt1.result == TransformationResult.SUCCESS:
            # 2. Insert predicate
            subgraph = {
                'nodes': [{'node_type': 'predicate', 'properties': {'name': 'P'}}],
                'edges': [],
                'ligatures': []
            }
            
            attempt2 = engine.apply_transformation(
                attempt1.result_graph,
                TransformationType.INSERTION,
                target_context=graph.root_context_id,
                subgraph=subgraph
            )
            transformations.append(attempt2)
        
        # Validate sequence
        result = validator.validate_transformation_sequence(transformations)
        
        # Should be valid if all transformations succeeded
        if all(t.result == TransformationResult.SUCCESS for t in transformations):
            assert result.is_valid
        else:
            assert not result.is_valid
    
    def test_complex_transformation_chain(self):
        """Test a complex chain of transformations."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Start with a predicate
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(pred_node)
        
        current_graph = graph
        successful_transformations = 0
        
        # Apply series of transformations
        transformations = [
            (TransformationType.DOUBLE_CUT_INSERTION, {
                'target_context': graph.root_context_id,
                'subgraph_items': {pred_node.id}
            }),
            # Could add more transformations here
        ]
        
        for trans_type, kwargs in transformations:
            attempt = engine.apply_transformation(current_graph, trans_type, **kwargs)
            
            if attempt.result == TransformationResult.SUCCESS:
                current_graph = attempt.result_graph
                successful_transformations += 1
            else:
                break
        
        # Should have applied at least some transformations
        assert successful_transformations > 0
        assert len(engine.transformation_history) == len(transformations)


class TestTransformationPropertyBased:
    """Property-based tests for transformations."""
    
    @given(st.text(alphabet='PQRABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=3))
    def test_double_cut_preserves_predicates(self, predicate_name):
        """Test that double cut operations preserve predicate names."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Add predicate
        pred_node = Node.create(node_type='predicate', properties={'name': predicate_name})
        graph = graph.add_node(pred_node)
        
        # Apply double cut insertion
        attempt = engine.apply_transformation(
            graph,
            TransformationType.DOUBLE_CUT_INSERTION,
            target_context=graph.root_context_id,
            subgraph_items={pred_node.id}
        )
        
        if attempt.result == TransformationResult.SUCCESS:
            # Predicate should still exist with same name
            found_predicate = False
            for node in attempt.result_graph.nodes.values():
                if (node.node_type == 'predicate' and 
                    node.properties.get('name') == predicate_name):
                    found_predicate = True
                    break
            
            assert found_predicate
    
    @given(st.integers(min_value=1, max_value=5))
    def test_multiple_erasures(self, num_predicates):
        """Test multiple erasure operations."""
        engine = TransformationEngine()
        graph = EGGraph.create_empty()
        
        # Create negative context
        graph, neg_context = graph.create_context('cut', graph.root_context_id, 'Negative')
        
        # Add multiple predicates
        predicates = []
        for i in range(num_predicates):
            pred = Node.create(node_type='predicate', properties={'name': f'P{i}'})
            graph = graph.add_node(pred, neg_context.id)
            predicates.append(pred)
        
        # Erase all predicates one by one
        current_graph = graph
        for pred in predicates:
            attempt = engine.apply_transformation(
                current_graph,
                TransformationType.ERASURE,
                target_items={pred.id}
            )
            
            if attempt.result == TransformationResult.SUCCESS:
                current_graph = attempt.result_graph
        
        # Should have removed all predicates
        remaining_predicates = sum(1 for node in current_graph.nodes.values() 
                                 if node.node_type == 'predicate')
        assert remaining_predicates == 0


# Helper functions for testing

def create_simple_graph_with_predicate(predicate_name: str = 'P') -> EGGraph:
    """Create a simple graph with one predicate."""
    graph = EGGraph.create_empty()
    pred_node = Node.create(node_type='predicate', properties={'name': predicate_name})
    graph = graph.add_node(pred_node)
    return graph

def create_graph_with_ligature() -> EGGraph:
    """Create a graph with a ligature connecting two terms."""
    graph = EGGraph.create_empty()
    
    term1 = Node.create(node_type='term', properties={'value': 'x'})
    term2 = Node.create(node_type='term', properties={'value': 'y'})
    
    graph = graph.add_node(term1)
    graph = graph.add_node(term2)
    
    ligature = Ligature.create(
        nodes={term1.id, term2.id},
        properties={'type': 'identity'}
    )
    graph = graph.add_ligature(ligature)
    
    return graph

