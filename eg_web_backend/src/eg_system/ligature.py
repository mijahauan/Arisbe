"""
Advanced ligature operations for the EG-HG rebuild project.

This module provides sophisticated ligature management including
splitting, merging, boundary detection, and connected component analysis
for handling lines of identity in existential graphs.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Iterator
from dataclasses import dataclass, replace
from collections import defaultdict, deque
import uuid

from .eg_types import (
    Node, Edge, Context, Ligature,
    NodeId, EdgeId, ContextId, LigatureId, ItemId,
    new_ligature_id, LigatureError, ValidationError,
    pset
)


class LigatureManager:
    """Advanced ligature management operations.
    
    This class provides sophisticated algorithms for managing ligatures
    (lines of identity) in existential graphs, including splitting,
    merging, and boundary detection operations.
    """
    
    @staticmethod
    def find_connected_ligature_components(nodes: Set[NodeId], edges: Set[EdgeId],
                                         existing_ligatures: Dict[LigatureId, Ligature]) -> List[Set[ItemId]]:
        """Find connected components among nodes and edges for ligature formation.
        
        Args:
            nodes: Set of node IDs to analyze.
            edges: Set of edge IDs to analyze.
            existing_ligatures: Existing ligatures to consider.
            
        Returns:
            A list of sets, where each set contains connected item IDs.
        """
        # Build adjacency graph for ligature connectivity
        adjacency = defaultdict(set)
        all_items = set(nodes) | set(edges)
        
        # Add connections from existing ligatures
        for ligature in existing_ligatures.values():
            ligature_items = set(ligature.nodes) | set(ligature.edges)
            # Connect all items in the same ligature
            for item1 in ligature_items:
                for item2 in ligature_items:
                    if item1 != item2 and item1 in all_items and item2 in all_items:
                        adjacency[item1].add(item2)
        
        # Find connected components using DFS
        visited = set()
        components = []
        
        for item in all_items:
            if item not in visited:
                component = set()
                stack = [item]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        component.add(current)
                        
                        for neighbor in adjacency[current]:
                            if neighbor not in visited:
                                stack.append(neighbor)
                
                components.append(component)
        
        return components
    
    @staticmethod
    def create_ligature_from_items(nodes: Set[NodeId], edges: Set[EdgeId],
                                 properties: Optional[Dict[str, Any]] = None) -> Ligature:
        """Create a new ligature from a set of nodes and edges.
        
        Args:
            nodes: Set of node IDs to include in the ligature.
            edges: Set of edge IDs to include in the ligature.
            properties: Optional properties for the ligature.
            
        Returns:
            A new ligature containing the specified items.
        """
        return Ligature.create(
            nodes=nodes,
            edges=edges,
            properties=properties or {}
        )
    
    @staticmethod
    def split_ligature(ligature: Ligature, split_point: ItemId) -> Tuple[Ligature, Ligature]:
        """Split a ligature at a specific item.
        
        Args:
            ligature: The ligature to split.
            split_point: The item ID where to split the ligature.
            
        Returns:
            A tuple of two new ligatures after splitting.
            
        Raises:
            LigatureError: If the split point is not in the ligature.
        """
        if split_point not in ligature.nodes and split_point not in ligature.edges:
            raise LigatureError(f"Split point {split_point} not found in ligature {ligature.id}")
        
        # For now, implement a simple split that separates the split point
        # In a more sophisticated implementation, this would analyze connectivity
        
        if split_point in ligature.nodes:
            # Split at a node
            remaining_nodes = ligature.nodes.remove(split_point)
            split_nodes = pset([split_point])
            
            ligature1 = Ligature.create(
                nodes=remaining_nodes,
                edges=ligature.edges,
                properties=ligature.properties
            )
            
            ligature2 = Ligature.create(
                nodes=split_nodes,
                edges=pset(),
                properties={}
            )
        else:
            # Split at an edge
            remaining_edges = ligature.edges.remove(split_point)
            split_edges = pset([split_point])
            
            ligature1 = Ligature.create(
                nodes=ligature.nodes,
                edges=remaining_edges,
                properties=ligature.properties
            )
            
            ligature2 = Ligature.create(
                nodes=pset(),
                edges=split_edges,
                properties={}
            )
        
        return ligature1, ligature2
    
    @staticmethod
    def merge_ligatures(ligature1: Ligature, ligature2: Ligature) -> Ligature:
        """Merge two ligatures into one.
        
        Args:
            ligature1: The first ligature to merge.
            ligature2: The second ligature to merge.
            
        Returns:
            A new ligature containing all items from both input ligatures.
        """
        merged_nodes = ligature1.nodes.union(ligature2.nodes)
        merged_edges = ligature1.edges.union(ligature2.edges)
        
        # Merge properties (ligature1 takes precedence for conflicts)
        merged_properties = dict(ligature2.properties)
        merged_properties.update(dict(ligature1.properties))
        
        return Ligature.create(
            nodes=merged_nodes,
            edges=merged_edges,
            properties=merged_properties
        )
    
    @staticmethod
    def find_ligature_boundaries(ligature: Ligature, context_boundaries: Dict[ItemId, ContextId]) -> Set[ItemId]:
        """Find items in a ligature that cross context boundaries.
        
        Args:
            ligature: The ligature to analyze.
            context_boundaries: Mapping from item IDs to their context IDs.
            
        Returns:
            A set of item IDs that are at context boundaries.
        """
        boundary_items = set()
        all_items = set(ligature.nodes) | set(ligature.edges)
        
        # Group items by context
        context_groups = defaultdict(set)
        for item_id in all_items:
            if item_id in context_boundaries:
                context_id = context_boundaries[item_id]
                context_groups[context_id].add(item_id)
        
        # If items span multiple contexts, they're at boundaries
        if len(context_groups) > 1:
            # Items that connect different contexts are boundary items
            for context_id, items in context_groups.items():
                if len(context_groups) > 1:  # Multiple contexts involved
                    boundary_items.update(items)
        
        return boundary_items
    
    @staticmethod
    def validate_ligature_consistency(ligature: Ligature, 
                                    available_nodes: Set[NodeId],
                                    available_edges: Set[EdgeId]) -> List[str]:
        """Validate that a ligature is consistent with available graph items.
        
        Args:
            ligature: The ligature to validate.
            available_nodes: Set of node IDs available in the graph.
            available_edges: Set of edge IDs available in the graph.
            
        Returns:
            A list of error messages. Empty list means no errors.
        """
        errors = []
        
        # Check that all nodes in the ligature exist
        for node_id in ligature.nodes:
            if node_id not in available_nodes:
                errors.append(f"Ligature {ligature.id} references non-existent node {node_id}")
        
        # Check that all edges in the ligature exist
        for edge_id in ligature.edges:
            if edge_id not in available_edges:
                errors.append(f"Ligature {ligature.id} references non-existent edge {edge_id}")
        
        # Check that the ligature is not empty
        if len(ligature.nodes) == 0 and len(ligature.edges) == 0:
            errors.append(f"Ligature {ligature.id} is empty")
        
        return errors
    
    @staticmethod
    def compute_ligature_closure(seed_items: Set[ItemId],
                               existing_ligatures: Dict[LigatureId, Ligature]) -> Set[ItemId]:
        """Compute the transitive closure of items connected by ligatures.
        
        Args:
            seed_items: Initial set of item IDs.
            existing_ligatures: Existing ligatures to consider for closure.
            
        Returns:
            The complete set of items connected to the seed items through ligatures.
        """
        closure = set(seed_items)
        changed = True
        
        while changed:
            changed = False
            old_size = len(closure)
            
            for ligature in existing_ligatures.values():
                ligature_items = set(ligature.nodes) | set(ligature.edges)
                
                # If any item in the ligature is in the closure, add all items
                if closure & ligature_items:
                    closure.update(ligature_items)
            
            if len(closure) > old_size:
                changed = True
        
        return closure
    
    @staticmethod
    def find_ligature_intersections(ligatures: List[Ligature]) -> Dict[Tuple[LigatureId, LigatureId], Set[ItemId]]:
        """Find intersections between ligatures.
        
        Args:
            ligatures: List of ligatures to analyze.
            
        Returns:
            A dictionary mapping ligature ID pairs to their intersection items.
        """
        intersections = {}
        
        for i, ligature1 in enumerate(ligatures):
            for j, ligature2 in enumerate(ligatures[i+1:], i+1):
                items1 = set(ligature1.nodes) | set(ligature1.edges)
                items2 = set(ligature2.nodes) | set(ligature2.edges)
                
                intersection = items1 & items2
                if intersection:
                    intersections[(ligature1.id, ligature2.id)] = intersection
        
        return intersections
    
    @staticmethod
    def optimize_ligature_structure(ligatures: Dict[LigatureId, Ligature]) -> Dict[LigatureId, Ligature]:
        """Optimize the structure of ligatures by merging overlapping ones.
        
        Args:
            ligatures: Dictionary of ligatures to optimize.
            
        Returns:
            An optimized dictionary of ligatures with overlaps resolved.
        """
        optimized = {}
        ligature_list = list(ligatures.values())
        processed = set()
        
        for i, ligature in enumerate(ligature_list):
            if ligature.id in processed:
                continue
            
            # Start with the current ligature
            merged = ligature
            processed.add(ligature.id)
            
            # Check for overlaps with remaining ligatures
            for j, other_ligature in enumerate(ligature_list[i+1:], i+1):
                if other_ligature.id in processed:
                    continue
                
                merged_items = set(merged.nodes) | set(merged.edges)
                other_items = set(other_ligature.nodes) | set(other_ligature.edges)
                
                # If there's an overlap, merge them
                if merged_items & other_items:
                    merged = LigatureManager.merge_ligatures(merged, other_ligature)
                    processed.add(other_ligature.id)
            
            optimized[merged.id] = merged
        
        return optimized


class LigatureAnalyzer:
    """Analyzer for complex ligature patterns and relationships."""
    
    @staticmethod
    def analyze_ligature_topology(ligatures: Dict[LigatureId, Ligature]) -> Dict[str, Any]:
        """Analyze the topological properties of ligatures.
        
        Args:
            ligatures: Dictionary of ligatures to analyze.
            
        Returns:
            A dictionary containing topological analysis results.
        """
        analysis = {
            'total_ligatures': len(ligatures),
            'total_items': 0,
            'node_count': 0,
            'edge_count': 0,
            'average_size': 0,
            'size_distribution': defaultdict(int),
            'connectivity_matrix': {},
        }
        
        all_items = set()
        all_nodes = set()
        all_edges = set()
        
        for ligature in ligatures.values():
            ligature_items = set(ligature.nodes) | set(ligature.edges)
            size = len(ligature_items)
            
            all_items.update(ligature_items)
            all_nodes.update(ligature.nodes)
            all_edges.update(ligature.edges)
            
            analysis['size_distribution'][size] += 1
        
        analysis['total_items'] = len(all_items)
        analysis['node_count'] = len(all_nodes)
        analysis['edge_count'] = len(all_edges)
        
        if ligatures:
            total_size = sum(len(set(lig.nodes) | set(lig.edges)) for lig in ligatures.values())
            analysis['average_size'] = total_size / len(ligatures)
        
        return analysis
    
    @staticmethod
    def find_ligature_patterns(ligatures: Dict[LigatureId, Ligature]) -> Dict[str, List[LigatureId]]:
        """Find common patterns in ligature structures.
        
        Args:
            ligatures: Dictionary of ligatures to analyze.
            
        Returns:
            A dictionary mapping pattern names to lists of ligature IDs.
        """
        patterns = {
            'singleton_nodes': [],      # Ligatures with only one node
            'singleton_edges': [],      # Ligatures with only one edge
            'node_only': [],           # Ligatures with only nodes
            'edge_only': [],           # Ligatures with only edges
            'mixed': [],               # Ligatures with both nodes and edges
            'large': [],               # Ligatures with many items (>5)
        }
        
        for ligature_id, ligature in ligatures.items():
            node_count = len(ligature.nodes)
            edge_count = len(ligature.edges)
            total_count = node_count + edge_count
            
            # Check specific singleton cases first
            if node_count == 1 and edge_count == 0:
                patterns['singleton_nodes'].append(ligature_id)
            elif node_count == 0 and edge_count == 1:
                patterns['singleton_edges'].append(ligature_id)
            # Then check general cases
            elif edge_count == 0 and node_count > 0:
                patterns['node_only'].append(ligature_id)
            elif node_count == 0 and edge_count > 0:
                patterns['edge_only'].append(ligature_id)
            elif node_count > 0 and edge_count > 0:
                patterns['mixed'].append(ligature_id)
            
            if total_count > 5:
                patterns['large'].append(ligature_id)
        
        return patterns

