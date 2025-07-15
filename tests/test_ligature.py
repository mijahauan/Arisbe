"""
Tests for advanced ligature operations.
"""

import pytest
from hypothesis import given, strategies as st

from src.ligature import LigatureManager, LigatureAnalyzer
from src.eg_types import (
    Node, Edge, Ligature,
    NodeId, EdgeId, LigatureId,
    new_node_id, new_edge_id, new_ligature_id,
    LigatureError,
    pset
)


class TestLigatureManager:
    """Test the LigatureManager class."""
    
    def test_create_ligature_from_items(self):
        """Test creating a ligature from nodes and edges."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        edge1_id = new_edge_id()
        
        nodes = {node1_id, node2_id}
        edges = {edge1_id}
        properties = {'type': 'identity'}
        
        ligature = LigatureManager.create_ligature_from_items(nodes, edges, properties)
        
        assert ligature.nodes == pset(nodes)
        assert ligature.edges == pset(edges)
        assert ligature.properties['type'] == 'identity'
    
    def test_find_connected_ligature_components_empty(self):
        """Test finding connected components with no existing ligatures."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        edge1_id = new_edge_id()
        
        nodes = {node1_id, node2_id}
        edges = {edge1_id}
        existing_ligatures = {}
        
        components = LigatureManager.find_connected_ligature_components(
            nodes, edges, existing_ligatures
        )
        
        # Without existing ligatures, each item is its own component
        assert len(components) == 3
        component_sizes = [len(comp) for comp in components]
        assert all(size == 1 for size in component_sizes)
    
    def test_find_connected_ligature_components_with_existing(self):
        """Test finding connected components with existing ligatures."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        node3_id = new_node_id()
        edge1_id = new_edge_id()
        
        # Create existing ligature connecting node1 and node2
        existing_ligature = Ligature.create(nodes={node1_id, node2_id})
        existing_ligatures = {existing_ligature.id: existing_ligature}
        
        nodes = {node1_id, node2_id, node3_id}
        edges = {edge1_id}
        
        components = LigatureManager.find_connected_ligature_components(
            nodes, edges, existing_ligatures
        )
        
        # Should have 2 components: {node1, node2} and {node3}, {edge1}
        assert len(components) == 3
        
        # Find the component with 2 items (connected nodes)
        two_item_component = next(comp for comp in components if len(comp) == 2)
        assert node1_id in two_item_component
        assert node2_id in two_item_component
    
    def test_split_ligature_at_node(self):
        """Test splitting a ligature at a node."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        node3_id = new_node_id()
        
        ligature = Ligature.create(nodes={node1_id, node2_id, node3_id})
        
        ligature1, ligature2 = LigatureManager.split_ligature(ligature, node2_id)
        
        # One ligature should contain the split node, the other the remaining nodes
        assert node2_id in ligature2.nodes
        assert len(ligature2.nodes) == 1
        assert node1_id in ligature1.nodes
        assert node3_id in ligature1.nodes
        assert len(ligature1.nodes) == 2
    
    def test_split_ligature_at_edge(self):
        """Test splitting a ligature at an edge."""
        node1_id = new_node_id()
        edge1_id = new_edge_id()
        edge2_id = new_edge_id()
        
        ligature = Ligature.create(nodes={node1_id}, edges={edge1_id, edge2_id})
        
        ligature1, ligature2 = LigatureManager.split_ligature(ligature, edge1_id)
        
        # One ligature should contain the split edge, the other the remaining items
        assert edge1_id in ligature2.edges
        assert len(ligature2.edges) == 1
        assert len(ligature2.nodes) == 0
        
        assert edge2_id in ligature1.edges
        assert node1_id in ligature1.nodes
    
    def test_split_ligature_invalid_split_point(self):
        """Test splitting a ligature at an invalid split point."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        fake_node_id = new_node_id()
        
        ligature = Ligature.create(nodes={node1_id, node2_id})
        
        with pytest.raises(LigatureError):
            LigatureManager.split_ligature(ligature, fake_node_id)
    
    def test_merge_ligatures(self):
        """Test merging two ligatures."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        node3_id = new_node_id()
        edge1_id = new_edge_id()
        
        ligature1 = Ligature.create(
            nodes={node1_id, node2_id}, 
            properties={'type': 'identity'}
        )
        ligature2 = Ligature.create(
            nodes={node3_id}, 
            edges={edge1_id},
            properties={'source': 'manual'}
        )
        
        merged = LigatureManager.merge_ligatures(ligature1, ligature2)
        
        assert node1_id in merged.nodes
        assert node2_id in merged.nodes
        assert node3_id in merged.nodes
        assert edge1_id in merged.edges
        
        # Properties should be merged (ligature1 takes precedence)
        assert merged.properties['type'] == 'identity'
        assert merged.properties['source'] == 'manual'
    
    def test_find_ligature_boundaries(self):
        """Test finding ligature boundaries across contexts."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        node3_id = new_node_id()
        
        context1_id = new_node_id()  # Using node_id as context_id for simplicity
        context2_id = new_node_id()
        
        ligature = Ligature.create(nodes={node1_id, node2_id, node3_id})
        
        # Map items to contexts
        context_boundaries = {
            node1_id: context1_id,
            node2_id: context1_id,
            node3_id: context2_id,  # This node is in a different context
        }
        
        boundary_items = LigatureManager.find_ligature_boundaries(ligature, context_boundaries)
        
        # All items should be boundary items since they span multiple contexts
        assert len(boundary_items) == 3
        assert node1_id in boundary_items
        assert node2_id in boundary_items
        assert node3_id in boundary_items
    
    def test_validate_ligature_consistency_valid(self):
        """Test validation of a consistent ligature."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        edge1_id = new_edge_id()
        
        ligature = Ligature.create(nodes={node1_id, node2_id}, edges={edge1_id})
        
        available_nodes = {node1_id, node2_id}
        available_edges = {edge1_id}
        
        errors = LigatureManager.validate_ligature_consistency(
            ligature, available_nodes, available_edges
        )
        
        assert errors == []
    
    def test_validate_ligature_consistency_missing_node(self):
        """Test validation of a ligature with missing nodes."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        
        ligature = Ligature.create(nodes={node1_id, node2_id})
        
        available_nodes = {node1_id}  # node2_id is missing
        available_edges = set()
        
        errors = LigatureManager.validate_ligature_consistency(
            ligature, available_nodes, available_edges
        )
        
        assert len(errors) == 1
        assert str(node2_id) in errors[0]
    
    def test_validate_ligature_consistency_empty(self):
        """Test validation of an empty ligature."""
        ligature = Ligature.create()
        
        available_nodes = set()
        available_edges = set()
        
        errors = LigatureManager.validate_ligature_consistency(
            ligature, available_nodes, available_edges
        )
        
        assert len(errors) == 1
        assert 'empty' in errors[0].lower()
    
    def test_compute_ligature_closure(self):
        """Test computing transitive closure of ligature connections."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        node3_id = new_node_id()
        node4_id = new_node_id()
        
        # Create ligatures: {node1, node2} and {node2, node3}
        ligature1 = Ligature.create(nodes={node1_id, node2_id})
        ligature2 = Ligature.create(nodes={node2_id, node3_id})
        
        existing_ligatures = {
            ligature1.id: ligature1,
            ligature2.id: ligature2
        }
        
        # Start with just node1
        seed_items = {node1_id}
        
        closure = LigatureManager.compute_ligature_closure(seed_items, existing_ligatures)
        
        # Should include node1, node2, and node3 (connected through ligatures)
        assert node1_id in closure
        assert node2_id in closure
        assert node3_id in closure
        assert node4_id not in closure  # Not connected
    
    def test_find_ligature_intersections(self):
        """Test finding intersections between ligatures."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        node3_id = new_node_id()
        
        ligature1 = Ligature.create(nodes={node1_id, node2_id})
        ligature2 = Ligature.create(nodes={node2_id, node3_id})
        ligature3 = Ligature.create(nodes={node3_id})
        
        ligatures = [ligature1, ligature2, ligature3]
        
        intersections = LigatureManager.find_ligature_intersections(ligatures)
        
        # Should find intersection between ligature1 and ligature2 (node2)
        assert (ligature1.id, ligature2.id) in intersections
        assert node2_id in intersections[(ligature1.id, ligature2.id)]
        
        # Should find intersection between ligature2 and ligature3 (node3)
        assert (ligature2.id, ligature3.id) in intersections
        assert node3_id in intersections[(ligature2.id, ligature3.id)]
    
    def test_optimize_ligature_structure(self):
        """Test optimizing ligature structure by merging overlaps."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        node3_id = new_node_id()
        
        # Create overlapping ligatures
        ligature1 = Ligature.create(nodes={node1_id, node2_id})
        ligature2 = Ligature.create(nodes={node2_id, node3_id})
        ligature3 = Ligature.create(nodes={new_node_id()})  # Separate ligature
        
        ligatures = {
            ligature1.id: ligature1,
            ligature2.id: ligature2,
            ligature3.id: ligature3
        }
        
        optimized = LigatureManager.optimize_ligature_structure(ligatures)
        
        # Should have 2 ligatures: merged (1+2) and separate (3)
        assert len(optimized) == 2
        
        # Find the merged ligature (should contain all 3 nodes)
        merged_ligature = None
        for lig in optimized.values():
            if len(lig.nodes) == 3:
                merged_ligature = lig
                break
        
        assert merged_ligature is not None
        assert node1_id in merged_ligature.nodes
        assert node2_id in merged_ligature.nodes
        assert node3_id in merged_ligature.nodes


class TestLigatureAnalyzer:
    """Test the LigatureAnalyzer class."""
    
    def test_analyze_ligature_topology(self):
        """Test topological analysis of ligatures."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        edge1_id = new_edge_id()
        
        ligature1 = Ligature.create(nodes={node1_id, node2_id})
        ligature2 = Ligature.create(edges={edge1_id})
        
        ligatures = {
            ligature1.id: ligature1,
            ligature2.id: ligature2
        }
        
        analysis = LigatureAnalyzer.analyze_ligature_topology(ligatures)
        
        assert analysis['total_ligatures'] == 2
        assert analysis['total_items'] == 3  # 2 nodes + 1 edge
        assert analysis['node_count'] == 2
        assert analysis['edge_count'] == 1
        assert analysis['average_size'] == 1.5  # (2 + 1) / 2
        assert analysis['size_distribution'][1] == 1  # One ligature with 1 item
        assert analysis['size_distribution'][2] == 1  # One ligature with 2 items
    
    def test_find_ligature_patterns(self):
        """Test finding patterns in ligature structures."""
        node1_id = new_node_id()
        node2_id = new_node_id()
        edge1_id = new_edge_id()
        
        # Create ligatures with different patterns
        singleton_node = Ligature.create(nodes={node1_id})
        singleton_edge = Ligature.create(edges={edge1_id})
        node_only = Ligature.create(nodes={node1_id, node2_id})
        mixed = Ligature.create(nodes={node1_id}, edges={edge1_id})
        
        # Create large ligature
        large_nodes = {new_node_id() for _ in range(6)}
        large = Ligature.create(nodes=large_nodes)
        
        ligatures = {
            singleton_node.id: singleton_node,
            singleton_edge.id: singleton_edge,
            node_only.id: node_only,
            mixed.id: mixed,
            large.id: large
        }
        
        patterns = LigatureAnalyzer.find_ligature_patterns(ligatures)
        
        assert singleton_node.id in patterns['singleton_nodes']
        assert singleton_edge.id in patterns['singleton_edges']
        assert node_only.id in patterns['node_only']
        assert mixed.id in patterns['mixed']
        assert large.id in patterns['large']
        
        # Check counts
        assert len(patterns['singleton_nodes']) == 1
        assert len(patterns['singleton_edges']) == 1
        assert len(patterns['node_only']) == 2  # singleton_node and node_only
        assert len(patterns['edge_only']) == 0  # singleton_edge is in singleton_edges, not edge_only
        assert len(patterns['mixed']) == 1
        assert len(patterns['large']) == 1


class TestLigatureManagerPropertyBased:
    """Property-based tests for ligature operations."""
    
    @given(st.sets(st.integers(min_value=0, max_value=9), min_size=1, max_size=10))
    def test_merge_ligatures_preserves_items(self, node_indices):
        """Test that merging ligatures preserves all items."""
        # Convert integers to actual node IDs
        all_nodes = [new_node_id() for _ in range(10)]  # Fixed size
        nodes1 = {all_nodes[i] for i in node_indices if i % 2 == 0}
        nodes2 = {all_nodes[i] for i in node_indices if i % 2 == 1}
        
        # Ensure both sets have at least one node
        if not nodes1:
            nodes1 = {all_nodes[0]}
        if not nodes2:
            nodes2 = {all_nodes[1]}
        
        ligature1 = Ligature.create(nodes=nodes1)
        ligature2 = Ligature.create(nodes=nodes2)
        
        merged = LigatureManager.merge_ligatures(ligature1, ligature2)
        
        # All original nodes should be in the merged ligature
        for node_id in nodes1:
            assert node_id in merged.nodes
        for node_id in nodes2:
            assert node_id in merged.nodes
    
    @given(st.integers(min_value=2, max_value=20))
    def test_ligature_closure_transitivity(self, num_nodes):
        """Test that ligature closure is transitive."""
        # Create a chain of ligatures: {0,1}, {1,2}, {2,3}, ...
        nodes = [new_node_id() for _ in range(num_nodes)]
        ligatures = {}
        
        for i in range(num_nodes - 1):
            ligature = Ligature.create(nodes={nodes[i], nodes[i + 1]})
            ligatures[ligature.id] = ligature
        
        # Start with first node
        seed_items = {nodes[0]}
        
        closure = LigatureManager.compute_ligature_closure(seed_items, ligatures)
        
        # Should include all nodes due to transitivity
        for node_id in nodes:
            assert node_id in closure

