"""
Tests for the core types in the EG-HG system.
"""

import pytest
import uuid
from hypothesis import given, strategies as st

from src.eg_types import (
    Node, Edge, Context, Ligature,
    NodeId, EdgeId, ContextId, LigatureId,
    new_node_id, new_edge_id, new_context_id, new_ligature_id,
    EGError, NodeError, EdgeError, ContextError, LigatureError, ValidationError,
    pmap, pset
)


class TestIdentifierGeneration:
    """Test ID generation functions."""
    
    def test_node_id_generation(self):
        """Test that node IDs are unique."""
        id1 = new_node_id()
        id2 = new_node_id()
        assert id1 != id2
        # Test that they are UUIDs (NewType doesn't change runtime type)
        assert isinstance(id1, uuid.UUID)
        assert isinstance(id2, uuid.UUID)
    
    def test_edge_id_generation(self):
        """Test that edge IDs are unique."""
        id1 = new_edge_id()
        id2 = new_edge_id()
        assert id1 != id2
        assert isinstance(id1, uuid.UUID)
        assert isinstance(id2, uuid.UUID)
    
    def test_context_id_generation(self):
        """Test that context IDs are unique."""
        id1 = new_context_id()
        id2 = new_context_id()
        assert id1 != id2
        assert isinstance(id1, uuid.UUID)
        assert isinstance(id2, uuid.UUID)
    
    def test_ligature_id_generation(self):
        """Test that ligature IDs are unique."""
        id1 = new_ligature_id()
        id2 = new_ligature_id()
        assert id1 != id2
        assert isinstance(id1, uuid.UUID)
        assert isinstance(id2, uuid.UUID)


class TestNode:
    """Test the Node class."""
    
    def test_node_creation_with_defaults(self):
        """Test creating a node with default values."""
        node = Node.create(node_type='variable')
        assert node.node_type == 'variable'
        assert len(node.properties) == 0
        assert node.id is not None
    
    def test_node_creation_with_properties(self):
        """Test creating a node with properties."""
        properties = {'name': 'x', 'type': 'individual'}
        node = Node.create(node_type='variable', properties=properties)
        assert node.properties == pmap(properties)
    
    def test_node_immutability(self):
        """Test that nodes are immutable."""
        node = Node.create(node_type='variable')
        original_id = node.id
        
        # Setting a property should return a new node
        new_node = node.set('name', 'x')
        assert node.id == original_id  # Original unchanged
        assert new_node.id == original_id  # Same ID
        assert 'name' not in node.properties  # Original unchanged
        assert new_node.properties['name'] == 'x'  # New node has property
    
    def test_node_with_property(self):
        """Test setting properties on a node."""
        node = Node.create(node_type='variable')
        new_node = node.set('name', 'x')
        
        assert new_node.properties['name'] == 'x'
        assert 'name' not in node.properties  # Original unchanged
    
    def test_node_without_property(self):
        """Test removing properties from a node."""
        node = Node.create(node_type='variable', properties={'name': 'x', 'type': 'individual'})
        new_node = node.remove('name')
        
        assert 'name' not in new_node.properties
        assert new_node.properties['type'] == 'individual'
        assert node.properties['name'] == 'x'  # Original unchanged
    
    def test_node_string_representation(self):
        """Test string representation of nodes."""
        node = Node.create(node_type='variable', properties={'name': 'x'})
        str_repr = str(node)
        assert 'variable' in str_repr
        assert 'name' in str_repr


class TestEdge:
    """Test the Edge class."""
    
    def test_edge_creation_with_defaults(self):
        """Test creating an edge with default values."""
        edge = Edge.create(edge_type='relation')
        assert edge.edge_type == 'relation'
        assert len(edge.nodes) == 0
        assert len(edge.properties) == 0
        assert edge.id is not None
    
    def test_edge_creation_with_nodes(self):
        """Test creating an edge with nodes."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        nodes = {node1_id, node2_id}
        
        edge = Edge.create(edge_type='relation', nodes=nodes)
        assert edge.nodes == pset(nodes)
    
    def test_edge_with_nodes(self):
        """Test edge with specific nodes."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        nodes = {node1_id, node2_id}
        
        edge = Edge.create(edge_type='relation', nodes=nodes)
        assert node1_id in edge.nodes
        assert node2_id in edge.nodes
        assert len(edge.nodes) == 2
    
    def test_edge_add_node(self):
        """Test adding a node to an edge."""
        edge = Edge.create(edge_type='relation')
        node_id = new_node_id()
        
        new_edge = edge.add_node(node_id)
        assert node_id in new_edge.nodes
        assert len(new_edge.nodes) == 1
        assert len(edge.nodes) == 0  # Original unchanged
    
    def test_edge_remove_node(self):
        """Test removing a node from an edge."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        edge = Edge.create(edge_type='relation', nodes={node1_id, node2_id})
        
        new_edge = edge.remove_node(node1_id)
        assert node1_id not in new_edge.nodes
        assert node2_id in new_edge.nodes
        assert len(new_edge.nodes) == 1
        assert len(edge.nodes) == 2  # Original unchanged
    
    def test_edge_remove_nonexistent_node(self):
        """Test removing a non-existent node from an edge."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        edge = Edge.create(edge_type='relation', nodes={node1_id})
        
        # Should return the same edge if node doesn't exist
        new_edge = edge.remove_node(node2_id)
        assert new_edge == edge
    
    def test_edge_string_representation(self):
        """Test string representation of edges."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        edge = Edge.create(edge_type='relation', nodes={node1_id, node2_id})
        str_repr = str(edge)
        assert 'relation' in str_repr
        assert 'nodes=2' in str_repr


class TestContext:
    """Test the Context class."""
    
    def test_context_creation_with_defaults(self):
        """Test creating a context with default values."""
        context = Context.create(context_type='sheet')
        assert context.context_type == 'sheet'
        assert context.parent_context is None
        assert context.depth == 0
        assert len(context.contained_items) == 0
        assert len(context.properties) == 0
        assert context.id is not None
    
    def test_context_add_item(self):
        """Test adding an item to a context."""
        context = Context.create(context_type='sheet')
        item_id = new_node_id()
        
        new_context = context.add_item(item_id)
        assert item_id in new_context.contained_items
        assert len(new_context.contained_items) == 1
        assert len(context.contained_items) == 0  # Original unchanged
    
    def test_context_remove_item(self):
        """Test removing an item from a context."""
        item1_id = new_node_id()
        item2_id = new_node_id()
        context = Context.create(context_type='sheet', contained_items={item1_id, item2_id})
        
        new_context = context.remove_item(item1_id)
        assert item1_id not in new_context.contained_items
        assert item2_id in new_context.contained_items
        assert len(new_context.contained_items) == 1
        assert len(context.contained_items) == 2  # Original unchanged
    
    def test_context_with_items(self):
        """Test setting items in a context."""
        context = Context.create(context_type='sheet')
        item1_id = new_node_id()
        item2_id = new_node_id()
        items = {item1_id, item2_id}
        
        new_context = context.with_items(items)
        assert new_context.contained_items == pset(items)
        assert len(context.contained_items) == 0  # Original unchanged
    
    def test_context_polarity(self):
        """Test context polarity."""
        positive = Context.create(context_type="sheet", depth=0)
        negative = Context.create(context_type="cut", depth=1)
        assert positive.is_positive
        assert not positive.is_negative
        assert negative.is_negative
        assert not negative.is_positive
    
    def test_context_string_representation(self):
        """Test string representation of contexts."""
        item_id = new_node_id()
        context = Context.create(context_type='cut', depth=1, contained_items={item_id})
        str_repr = str(context)
        assert 'cut' in str_repr
        assert 'depth=1' in str_repr
        assert 'items=1' in str_repr


class TestLigature:
    """Test the Ligature class."""
    
    def test_ligature_creation_with_defaults(self):
        """Test creating a ligature with default values."""
        ligature = Ligature.create()
        assert len(ligature.nodes) == 0
        assert len(ligature.edges) == 0
        assert len(ligature.properties) == 0
        assert ligature.id is not None
    
    def test_ligature_add_node(self):
        """Test adding a node to a ligature."""
        ligature = Ligature.create()
        node_id = new_node_id()
        
        new_ligature = ligature.add_node(node_id)
        assert node_id in new_ligature.nodes
        assert len(new_ligature.nodes) == 1
        assert len(ligature.nodes) == 0  # Original unchanged
    
    def test_ligature_add_edge(self):
        """Test adding an edge to a ligature."""
        ligature = Ligature.create()
        edge_id = new_edge_id()
        
        new_ligature = ligature.add_edge(edge_id)
        assert edge_id in new_ligature.edges
        assert len(new_ligature.edges) == 1
        assert len(ligature.edges) == 0  # Original unchanged
    
    def test_ligature_union(self):
        """Test union of two ligatures."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        edge1_id = new_edge_id()
        edge2_id = new_edge_id()
        
        ligature1 = Ligature.create(nodes={node1_id}, edges={edge1_id})
        ligature2 = Ligature.create(nodes={node2_id}, edges={edge2_id})
        
        union_ligature = ligature1.union(ligature2)
        
        assert node1_id in union_ligature.nodes
        assert node2_id in union_ligature.nodes
        assert edge1_id in union_ligature.edges
        assert edge2_id in union_ligature.edges
        assert len(union_ligature.nodes) == 2
        assert len(union_ligature.edges) == 2
    
    def test_ligature_string_representation(self):
        """Test string representation of ligatures."""
        node_id = new_node_id()
        edge_id = new_edge_id()
        ligature = Ligature.create(nodes={node_id}, edges={edge_id})
        str_repr = str(ligature)
        assert 'nodes=1' in str_repr
        assert 'edges=1' in str_repr


class TestExceptions:
    """Test the exception hierarchy."""
    
    def test_exception_hierarchy(self):
        """Test that all exceptions inherit from EGError."""
        assert issubclass(NodeError, EGError)
        assert issubclass(EdgeError, EGError)
        assert issubclass(ContextError, EGError)
        assert issubclass(LigatureError, EGError)
        assert issubclass(ValidationError, EGError)
    
    def test_exception_creation(self):
        """Test creating exceptions."""
        node_error = NodeError("Node error message")
        edge_error = EdgeError("Edge error message")
        context_error = ContextError("Context error message")
        ligature_error = LigatureError("Ligature error message")
        validation_error = ValidationError("Validation error message")
        
        assert str(node_error) == "Node error message"
        assert str(edge_error) == "Edge error message"
        assert str(context_error) == "Context error message"
        assert str(ligature_error) == "Ligature error message"
        assert str(validation_error) == "Validation error message"


class TestPropertyBasedTypes:
    """Property-based tests for the core types."""
    
    @given(st.text(min_size=1, max_size=50))
    def test_node_property_roundtrip(self, property_value):
        """Test that node properties can be set and retrieved."""
        node = Node.create(node_type='variable')
        new_node = node.set('test_prop', property_value)
        assert new_node.properties['test_prop'] == property_value
    
    @given(st.sets(st.integers(), min_size=0, max_size=10))
    def test_edge_nodes_roundtrip(self, node_indices):
        """Test that edge nodes can be set and retrieved."""
        # Convert integers to actual node IDs
        node_ids = {new_node_id() for _ in node_indices}
        edge = Edge.create(edge_type='relation', nodes=node_ids)
        
        assert len(edge.nodes) == len(node_ids)
        for node_id in node_ids:
            assert node_id in edge.nodes
    
    @given(st.integers(min_value=0, max_value=100))
    def test_ligature_size_consistency(self, num_nodes):
        """Test that ligature size is consistent with added nodes."""
        ligature = Ligature.create()
        node_ids = [new_node_id() for _ in range(num_nodes)]
        
        for node_id in node_ids:
            ligature = ligature.add_node(node_id)
        
        assert len(ligature.nodes) == num_nodes
        for node_id in node_ids:
            assert node_id in ligature.nodes

