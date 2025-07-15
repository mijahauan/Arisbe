"""
Tests for the EGGraph unified graph operations.
"""

import pytest
from hypothesis import given, strategies as st

from src.graph import EGGraph
from src.eg_types import (
    Node, Edge, Context, Ligature,
    NodeId, EdgeId, ContextId, LigatureId,
    new_node_id, new_edge_id, new_context_id, new_ligature_id,
    NodeError, EdgeError, ContextError, LigatureError,
    pmap, pset
)


class TestEGGraphBasics:
    """Test basic EGGraph operations."""
    
    def test_create_empty_graph(self):
        """Test creating an empty graph."""
        graph = EGGraph.create_empty()
        
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
        assert len(graph.ligatures) == 0
        assert graph.context_manager.root_context is not None
        assert graph.root_context_id == graph.context_manager.root_context.id
    
    def test_graph_statistics(self):
        """Test graph statistics calculation."""
        graph = EGGraph.create_empty()
        stats = graph.get_graph_statistics()
        
        assert stats['num_contexts'] == 1  # Root context
        assert stats['num_nodes'] == 0
        assert stats['num_edges'] == 0
        assert stats['num_ligatures'] == 0
        assert stats['connected_components'] == 0
        assert stats['max_context_depth'] == 0
    
    def test_graph_string_representation(self):
        """Test string representation of graph."""
        graph = EGGraph.create_empty()
        str_repr = str(graph)
        
        assert 'EGGraph' in str_repr
        assert 'contexts=1' in str_repr
        assert 'nodes=0' in str_repr


class TestEGGraphNodeOperations:
    """Test node operations in EGGraph."""
    
    def test_add_node_to_root_context(self):
        """Test adding a node to the root context."""
        graph = EGGraph.create_empty()
        node = Node.create(node_type='variable', properties={'name': 'x'})
        
        new_graph = graph.add_node(node)
        
        assert node.id in new_graph.nodes
        assert new_graph.get_node(node.id) == node
        assert node.id in new_graph.get_items_in_context(new_graph.root_context_id)
        
        # Original graph unchanged
        assert node.id not in graph.nodes
    
    def test_add_node_to_specific_context(self):
        """Test adding a node to a specific context."""
        graph = EGGraph.create_empty()
        new_graph, cut_context = graph.create_context('cut')
        
        node = Node.create(node_type='variable')
        final_graph = new_graph.add_node(node, cut_context.id)
        
        assert node.id in final_graph.nodes
        assert node.id in final_graph.get_items_in_context(cut_context.id)
        assert node.id not in final_graph.get_items_in_context(final_graph.root_context_id)
    
    def test_add_node_to_nonexistent_context(self):
        """Test adding a node to a non-existent context."""
        graph = EGGraph.create_empty()
        node = Node.create(node_type='variable')
        fake_context_id = new_context_id()
        
        with pytest.raises(ContextError):
            graph.add_node(node, fake_context_id)
    
    def test_remove_node(self):
        """Test removing a node from the graph."""
        graph = EGGraph.create_empty()
        node = Node.create(node_type='variable')
        
        # Add node
        graph_with_node = graph.add_node(node)
        assert node.id in graph_with_node.nodes
        
        # Remove node
        graph_without_node = graph_with_node.remove_node(node.id)
        assert node.id not in graph_without_node.nodes
        assert node.id not in graph_without_node.get_items_in_context(graph_without_node.root_context_id)
    
    def test_remove_nonexistent_node(self):
        """Test removing a non-existent node."""
        graph = EGGraph.create_empty()
        fake_node_id = new_node_id()
        
        with pytest.raises(NodeError):
            graph.remove_node(fake_node_id)
    
    def test_remove_node_from_edges(self):
        """Test that removing a node also removes it from edges."""
        graph = EGGraph.create_empty()
        
        # Create nodes and edge
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        edge = Edge.create(edge_type='relation', nodes={node1.id, node2.id})
        
        # Add to graph
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        graph = graph.add_edge(edge)
        
        # Verify edge contains both nodes
        assert node1.id in graph.get_edge(edge.id).nodes
        assert node2.id in graph.get_edge(edge.id).nodes
        
        # Remove one node
        graph = graph.remove_node(node1.id)
        
        # Verify node is removed from edge
        updated_edge = graph.get_edge(edge.id)
        assert node1.id not in updated_edge.nodes
        assert node2.id in updated_edge.nodes


class TestEGGraphEdgeOperations:
    """Test edge operations in EGGraph."""
    
    def test_add_edge(self):
        """Test adding an edge to the graph."""
        graph = EGGraph.create_empty()
        
        # Create nodes first
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        
        # Create and add edge
        edge = Edge.create(edge_type='relation', nodes={node1.id, node2.id})
        new_graph = graph.add_edge(edge)
        
        assert edge.id in new_graph.edges
        assert new_graph.get_edge(edge.id) == edge
        assert edge.id in new_graph.get_items_in_context(new_graph.root_context_id)
    
    def test_add_edge_with_nonexistent_nodes(self):
        """Test adding an edge with non-existent nodes."""
        graph = EGGraph.create_empty()
        fake_node_id = new_node_id()
        edge = Edge.create(edge_type='relation', nodes={fake_node_id})
        
        with pytest.raises(NodeError):
            graph.add_edge(edge)
    
    def test_remove_edge(self):
        """Test removing an edge from the graph."""
        graph = EGGraph.create_empty()
        
        # Create nodes and edge
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        edge = Edge.create(edge_type='relation', nodes={node1.id, node2.id})
        
        # Add to graph
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        graph = graph.add_edge(edge)
        
        # Remove edge
        new_graph = graph.remove_edge(edge.id)
        
        assert edge.id not in new_graph.edges
        assert edge.id not in new_graph.get_items_in_context(new_graph.root_context_id)
    
    def test_remove_nonexistent_edge(self):
        """Test removing a non-existent edge."""
        graph = EGGraph.create_empty()
        fake_edge_id = new_edge_id()
        
        with pytest.raises(EdgeError):
            graph.remove_edge(fake_edge_id)


class TestEGGraphLigatureOperations:
    """Test ligature operations in EGGraph."""
    
    def test_add_ligature(self):
        """Test adding a ligature to the graph."""
        graph = EGGraph.create_empty()
        
        # Create nodes
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        
        # Create and add ligature
        ligature = Ligature.create(nodes={node1.id, node2.id})
        new_graph = graph.add_ligature(ligature)
        
        assert ligature.id in new_graph.ligatures
        assert new_graph.get_ligature(ligature.id) == ligature
    
    def test_add_ligature_with_nonexistent_items(self):
        """Test adding a ligature with non-existent items."""
        graph = EGGraph.create_empty()
        fake_node_id = new_node_id()
        ligature = Ligature.create(nodes={fake_node_id})
        
        with pytest.raises(NodeError):
            graph.add_ligature(ligature)
    
    def test_remove_ligature(self):
        """Test removing a ligature from the graph."""
        graph = EGGraph.create_empty()
        
        # Create nodes and ligature
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        ligature = Ligature.create(nodes={node1.id, node2.id})
        
        # Add to graph
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        graph = graph.add_ligature(ligature)
        
        # Remove ligature
        new_graph = graph.remove_ligature(ligature.id)
        
        assert ligature.id not in new_graph.ligatures


class TestEGGraphTraversal:
    """Test graph traversal operations."""
    
    def test_find_incident_edges(self):
        """Test finding edges incident to a node."""
        graph = EGGraph.create_empty()
        
        # Create nodes
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        node3 = Node.create(node_type='variable')
        
        # Create edges
        edge1 = Edge.create(edge_type='relation', nodes={node1.id, node2.id})
        edge2 = Edge.create(edge_type='relation', nodes={node1.id, node3.id})
        edge3 = Edge.create(edge_type='relation', nodes={node2.id, node3.id})
        
        # Add to graph
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        graph = graph.add_node(node3)
        graph = graph.add_edge(edge1)
        graph = graph.add_edge(edge2)
        graph = graph.add_edge(edge3)
        
        # Test incident edges
        incident_to_node1 = graph.find_incident_edges(node1.id)
        assert len(incident_to_node1) == 2
        assert edge1 in incident_to_node1
        assert edge2 in incident_to_node1
        assert edge3 not in incident_to_node1
    
    def test_get_neighbors(self):
        """Test getting neighbors of a node."""
        graph = EGGraph.create_empty()
        
        # Create nodes and edges
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        node3 = Node.create(node_type='variable')
        edge1 = Edge.create(edge_type='relation', nodes={node1.id, node2.id})
        edge2 = Edge.create(edge_type='relation', nodes={node1.id, node3.id})
        
        # Add to graph
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        graph = graph.add_node(node3)
        graph = graph.add_edge(edge1)
        graph = graph.add_edge(edge2)
        
        # Test neighbors
        neighbors = graph.get_neighbors(node1.id)
        assert len(neighbors) == 2
        assert node2.id in neighbors
        assert node3.id in neighbors
        assert node1.id not in neighbors
    
    def test_find_path(self):
        """Test finding a path between two nodes."""
        graph = EGGraph.create_empty()
        
        # Create a chain: node1 - node2 - node3
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        node3 = Node.create(node_type='variable')
        edge1 = Edge.create(edge_type='relation', nodes={node1.id, node2.id})
        edge2 = Edge.create(edge_type='relation', nodes={node2.id, node3.id})
        
        # Add to graph
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        graph = graph.add_node(node3)
        graph = graph.add_edge(edge1)
        graph = graph.add_edge(edge2)
        
        # Test path finding
        path = graph.find_path(node1.id, node3.id)
        assert path == [node1.id, node2.id, node3.id]
        
        # Test path to self
        self_path = graph.find_path(node1.id, node1.id)
        assert self_path == [node1.id]
        
        # Test no path (add isolated node)
        node4 = Node.create(node_type='variable')
        graph = graph.add_node(node4)
        no_path = graph.find_path(node1.id, node4.id)
        assert no_path is None
    
    def test_find_connected_components(self):
        """Test finding connected components."""
        graph = EGGraph.create_empty()
        
        # Create two separate components
        # Component 1: node1 - node2
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        edge1 = Edge.create(edge_type='relation', nodes={node1.id, node2.id})
        
        # Component 2: node3 - node4
        node3 = Node.create(node_type='variable')
        node4 = Node.create(node_type='variable')
        edge2 = Edge.create(edge_type='relation', nodes={node3.id, node4.id})
        
        # Isolated node
        node5 = Node.create(node_type='variable')
        
        # Add to graph
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        graph = graph.add_node(node3)
        graph = graph.add_node(node4)
        graph = graph.add_node(node5)
        graph = graph.add_edge(edge1)
        graph = graph.add_edge(edge2)
        
        # Test connected components
        components = graph.find_connected_components()
        assert len(components) == 3
        
        # Check that each component contains the expected nodes
        component_sizes = [len(comp) for comp in components]
        component_sizes.sort()
        assert component_sizes == [1, 2, 2]  # One isolated, two pairs


class TestEGGraphContextOperations:
    """Test context-related operations in EGGraph."""
    
    def test_create_context(self):
        """Test creating a new context."""
        graph = EGGraph.create_empty()
        new_graph, cut_context = graph.create_context('cut', name='Test Cut')
        
        assert cut_context.context_type == 'cut'
        assert cut_context.properties.get('name') == 'Test Cut'
        assert cut_context.parent_context == graph.root_context_id
        assert cut_context.depth == 1
        
        # Verify context is in the manager
        assert new_graph.context_manager.has_context(cut_context.id)
    
    def test_get_items_in_context(self):
        """Test getting items in a specific context."""
        graph = EGGraph.create_empty()
        
        # Create a cut context
        graph, cut_context = graph.create_context('cut')
        
        # Add items to different contexts
        root_node = Node.create(node_type='variable')
        cut_node = Node.create(node_type='variable')
        
        graph = graph.add_node(root_node)  # Goes to root by default
        graph = graph.add_node(cut_node, cut_context.id)
        
        # Test context contents
        root_items = graph.get_items_in_context(graph.root_context_id)
        cut_items = graph.get_items_in_context(cut_context.id)
        
        assert root_node.id in root_items
        assert cut_node.id in cut_items
        assert cut_node.id not in root_items
        assert root_node.id not in cut_items
    
    def test_get_nodes_in_context(self):
        """Test getting nodes in a specific context."""
        graph = EGGraph.create_empty()
        
        # Add nodes and edges
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        edge = Edge.create(edge_type='relation', nodes={node1.id, node2.id})
        
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        graph = graph.add_edge(edge)
        
        # Get nodes in root context
        nodes_in_root = graph.get_nodes_in_context(graph.root_context_id)
        assert len(nodes_in_root) == 2
        assert node1 in nodes_in_root
        assert node2 in nodes_in_root
    
    def test_get_edges_in_context(self):
        """Test getting edges in a specific context."""
        graph = EGGraph.create_empty()
        
        # Add nodes and edges
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        edge = Edge.create(edge_type='relation', nodes={node1.id, node2.id})
        
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        graph = graph.add_edge(edge)
        
        # Get edges in root context
        edges_in_root = graph.get_edges_in_context(graph.root_context_id)
        assert len(edges_in_root) == 1
        assert edge in edges_in_root


class TestEGGraphValidation:
    """Test graph validation operations."""
    
    def test_validate_consistent_graph(self):
        """Test validation of a consistent graph."""
        graph = EGGraph.create_empty()
        
        # Create a simple valid graph
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        edge = Edge.create(edge_type='relation', nodes={node1.id, node2.id})
        ligature = Ligature.create(nodes={node1.id})
        
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        graph = graph.add_edge(edge)
        graph = graph.add_ligature(ligature)
        
        # Validate
        errors = graph.validate_graph_consistency()
        assert errors == []
    
    def test_trace_ligature_path(self):
        """Test tracing ligature paths."""
        graph = EGGraph.create_empty()
        
        # Create nodes and ligature
        node1 = Node.create(node_type='variable')
        node2 = Node.create(node_type='variable')
        ligature = Ligature.create(nodes={node1.id, node2.id})
        
        graph = graph.add_node(node1)
        graph = graph.add_node(node2)
        graph = graph.add_ligature(ligature)
        
        # Test tracing
        found_ligature = graph.trace_ligature_path(node1.id)
        assert found_ligature == ligature
        
        found_ligature = graph.trace_ligature_path(node2.id)
        assert found_ligature == ligature
        
        # Test non-existent item
        fake_node_id = new_node_id()
        no_ligature = graph.trace_ligature_path(fake_node_id)
        assert no_ligature is None


class TestEGGraphImmutability:
    """Test immutability of EGGraph operations."""
    
    def test_add_node_immutability(self):
        """Test that adding a node doesn't modify the original graph."""
        graph = EGGraph.create_empty()
        node = Node.create(node_type='variable')
        
        original_node_count = len(graph.nodes)
        new_graph = graph.add_node(node)
        
        assert len(graph.nodes) == original_node_count
        assert len(new_graph.nodes) == original_node_count + 1
        assert node.id not in graph.nodes
        assert node.id in new_graph.nodes
    
    def test_remove_node_immutability(self):
        """Test that removing a node doesn't modify the original graph."""
        graph = EGGraph.create_empty()
        node = Node.create(node_type='variable')
        
        graph_with_node = graph.add_node(node)
        graph_without_node = graph_with_node.remove_node(node.id)
        
        assert node.id in graph_with_node.nodes
        assert node.id not in graph_without_node.nodes
        assert len(graph_with_node.nodes) == 1
        assert len(graph_without_node.nodes) == 0

