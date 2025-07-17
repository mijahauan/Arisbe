"""
Advanced ligature operations for the EG-HG rebuild project.

Updated for Entity-Predicate hypergraph architecture where:
- Ligatures connect Entities (Lines of Identity) rather than Nodes
- Predicates are hyperedges that connect to Entities
- Ligatures represent shared variables/constants across predicates

This module provides sophisticated ligature management including
splitting, merging, boundary detection, and connected component analysis
for handling lines of identity in existential graphs.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Iterator
from dataclasses import dataclass, replace
from collections import defaultdict, deque
import uuid

from .eg_types import (
    Entity, Predicate, Context, Ligature,
    EntityId, PredicateId, ContextId, LigatureId, ItemId,
    new_ligature_id, LigatureError, ValidationError,
    pset
)


class LigatureManager:
    """Advanced ligature management operations for Entity-Predicate architecture.
    
    This class provides sophisticated algorithms for managing ligatures
    (lines of identity) in existential graphs, focusing on entity connections
    rather than node connections.
    """
    
    @staticmethod
    def find_connected_entity_components(entities: Set[EntityId], predicates: Set[PredicateId],
                                       existing_ligatures: Dict[LigatureId, Ligature],
                                       predicate_lookup: Dict[PredicateId, Predicate]) -> List[Set[EntityId]]:
        """Find connected components among entities for ligature formation.
        
        Args:
            entities: Set of entity IDs to analyze.
            predicates: Set of predicate IDs to consider for connections.
            existing_ligatures: Existing ligatures to consider.
            predicate_lookup: Mapping from predicate IDs to predicate objects.
            
        Returns:
            A list of sets, where each set contains connected entity IDs.
        """
        # Build adjacency graph for entity connectivity through predicates
        adjacency = defaultdict(set)
        
        # Add connections from predicates (entities in same predicate are connected)
        for predicate_id in predicates:
            if predicate_id in predicate_lookup:
                predicate = predicate_lookup[predicate_id]
                predicate_entities = [eid for eid in predicate.entities if eid in entities]
                
                # Connect all entities in the same predicate
                for i, entity1 in enumerate(predicate_entities):
                    for entity2 in predicate_entities[i+1:]:
                        adjacency[entity1].add(entity2)
                        adjacency[entity2].add(entity1)
        
        # Add connections from existing ligatures
        for ligature in existing_ligatures.values():
            ligature_entities = [eid for eid in ligature.entities if eid in entities]
            
            # Connect all entities in the same ligature
            for i, entity1 in enumerate(ligature_entities):
                for entity2 in ligature_entities[i+1:]:
                    adjacency[entity1].add(entity2)
                    adjacency[entity2].add(entity1)
        
        # Find connected components using DFS
        visited = set()
        components = []
        
        for entity_id in entities:
            if entity_id not in visited:
                component = set()
                stack = [entity_id]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        component.add(current)
                        
                        for neighbor in adjacency[current]:
                            if neighbor not in visited:
                                stack.append(neighbor)
                
                if component:  # Only add non-empty components
                    components.append(component)
        
        return components
    
    @staticmethod
    def create_ligature_from_entities(entities: Set[EntityId],
                                    properties: Optional[Dict[str, Any]] = None) -> Ligature:
        """Create a new ligature from a set of entities.
        
        Args:
            entities: Set of entity IDs to include in the ligature.
            properties: Optional properties for the ligature.
            
        Returns:
            A new ligature containing the specified entities.
        """
        return Ligature.create(
            entities=entities,
            properties=properties or {}
        )
    
    @staticmethod
    def split_ligature(ligature: Ligature, split_point: EntityId) -> Tuple[Ligature, Ligature]:
        """Split a ligature at a specific entity.
        
        Args:
            ligature: The ligature to split.
            split_point: The entity ID where to split the ligature.
            
        Returns:
            A tuple of two new ligatures after splitting.
            
        Raises:
            LigatureError: If the split point is not in the ligature.
        """
        if split_point not in ligature.entities:
            raise LigatureError(f"Split point {split_point} not found in ligature {ligature.id}")
        
        # Split at the entity
        remaining_entities = ligature.entities.remove(split_point)
        split_entities = pset([split_point])
        
        ligature1 = Ligature.create(
            entities=remaining_entities,
            properties=ligature.properties
        )
        
        ligature2 = Ligature.create(
            entities=split_entities,
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
            A new ligature containing all entities from both input ligatures.
        """
        merged_entities = ligature1.entities.union(ligature2.entities)
        
        # Merge properties (ligature1 takes precedence for conflicts)
        merged_properties = dict(ligature2.properties)
        merged_properties.update(dict(ligature1.properties))
        
        return Ligature.create(
            entities=merged_entities,
            properties=merged_properties
        )
    
    @staticmethod
    def find_ligature_boundaries(ligature: Ligature, context_boundaries: Dict[EntityId, ContextId]) -> Set[EntityId]:
        """Find entities in a ligature that cross context boundaries.
        
        Args:
            ligature: The ligature to analyze.
            context_boundaries: Mapping from entity IDs to their context IDs.
            
        Returns:
            A set of entity IDs that are at context boundaries.
        """
        boundary_entities = set()
        
        # Group entities by context
        context_groups = defaultdict(set)
        for entity_id in ligature.entities:
            if entity_id in context_boundaries:
                context_id = context_boundaries[entity_id]
                context_groups[context_id].add(entity_id)
        
        # If entities span multiple contexts, they're at boundaries
        if len(context_groups) > 1:
            # Entities that connect different contexts are boundary entities
            for context_id, entities in context_groups.items():
                if len(context_groups) > 1:  # Multiple contexts involved
                    boundary_entities.update(entities)
        
        return boundary_entities
    
    @staticmethod
    def validate_ligature_consistency(ligature: Ligature, 
                                    available_entities: Set[EntityId]) -> List[str]:
        """Validate that a ligature is consistent with available graph entities.
        
        Args:
            ligature: The ligature to validate.
            available_entities: Set of entity IDs available in the graph.
            
        Returns:
            A list of error messages. Empty list means no errors.
        """
        errors = []
        
        # Check that all entities in the ligature exist
        for entity_id in ligature.entities:
            if entity_id not in available_entities:
                errors.append(f"Ligature {ligature.id} references non-existent entity {entity_id}")
        
        # Check that the ligature is not empty
        if len(ligature.entities) == 0:
            errors.append(f"Ligature {ligature.id} is empty")
        
        # Check that ligature has at least 2 entities (lines of identity connect multiple things)
        if len(ligature.entities) == 1:
            errors.append(f"Ligature {ligature.id} has only one entity (should connect multiple entities)")
        
        return errors
    
    @staticmethod
    def compute_ligature_closure(seed_entities: Set[EntityId],
                               existing_ligatures: Dict[LigatureId, Ligature]) -> Set[EntityId]:
        """Compute the transitive closure of entities connected by ligatures.
        
        Args:
            seed_entities: Initial set of entity IDs.
            existing_ligatures: Existing ligatures to consider for closure.
            
        Returns:
            The complete set of entities connected to the seed entities through ligatures.
        """
        closure = set(seed_entities)
        changed = True
        
        while changed:
            changed = False
            old_size = len(closure)
            
            for ligature in existing_ligatures.values():
                # If any entity in the ligature is in the closure, add all entities
                if closure & ligature.entities:
                    closure.update(ligature.entities)
            
            if len(closure) > old_size:
                changed = True
        
        return closure
    
    @staticmethod
    def find_ligature_intersections(ligatures: List[Ligature]) -> Dict[Tuple[LigatureId, LigatureId], Set[EntityId]]:
        """Find intersections between ligatures.
        
        Args:
            ligatures: List of ligatures to analyze.
            
        Returns:
            A dictionary mapping ligature ID pairs to their intersection entities.
        """
        intersections = {}
        
        for i, ligature1 in enumerate(ligatures):
            for j, ligature2 in enumerate(ligatures[i+1:], i+1):
                intersection = ligature1.entities & ligature2.entities
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
                
                # If there's an overlap, merge them
                if merged.entities & other_ligature.entities:
                    merged = LigatureManager.merge_ligatures(merged, other_ligature)
                    processed.add(other_ligature.id)
            
            optimized[merged.id] = merged
        
        return optimized
    
    @staticmethod
    def find_entity_sharing_patterns(predicates: Dict[PredicateId, Predicate],
                                   ligatures: Dict[LigatureId, Ligature]) -> Dict[str, List[EntityId]]:
        """Find patterns of entity sharing across predicates and ligatures.
        
        Args:
            predicates: Dictionary of predicates to analyze.
            ligatures: Dictionary of ligatures to analyze.
            
        Returns:
            A dictionary mapping pattern names to lists of entity IDs.
        """
        patterns = {
            'shared_across_predicates': [],  # Entities used by multiple predicates
            'ligature_connected': [],        # Entities connected by ligatures
            'isolated': [],                  # Entities used by only one predicate
            'highly_connected': [],          # Entities used by many predicates (>3)
        }
        
        # Count predicate usage for each entity
        entity_usage = defaultdict(list)
        for predicate_id, predicate in predicates.items():
            for entity_id in predicate.entities:
                entity_usage[entity_id].append(predicate_id)
        
        # Collect entities in ligatures
        ligature_entities = set()
        for ligature in ligatures.values():
            ligature_entities.update(ligature.entities)
        
        # Classify entities by patterns
        for entity_id, predicate_list in entity_usage.items():
            usage_count = len(predicate_list)
            
            if usage_count == 1:
                patterns['isolated'].append(entity_id)
            elif usage_count > 1:
                patterns['shared_across_predicates'].append(entity_id)
                
                if usage_count > 3:
                    patterns['highly_connected'].append(entity_id)
            
            if entity_id in ligature_entities:
                patterns['ligature_connected'].append(entity_id)
        
        return patterns


class LigatureAnalyzer:
    """Analyzer for complex ligature patterns and relationships in Entity-Predicate architecture."""
    
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
            'total_entities': 0,
            'average_size': 0,
            'size_distribution': defaultdict(int),
            'connectivity_matrix': {},
        }
        
        all_entities = set()
        
        for ligature in ligatures.values():
            size = len(ligature.entities)
            all_entities.update(ligature.entities)
            analysis['size_distribution'][size] += 1
        
        analysis['total_entities'] = len(all_entities)
        
        if ligatures:
            total_size = sum(len(ligature.entities) for ligature in ligatures.values())
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
            'binary': [],              # Ligatures connecting exactly 2 entities
            'ternary': [],             # Ligatures connecting exactly 3 entities
            'large': [],               # Ligatures connecting many entities (>5)
            'singleton': [],           # Ligatures with only 1 entity (should be rare)
        }
        
        for ligature_id, ligature in ligatures.items():
            entity_count = len(ligature.entities)
            
            if entity_count == 1:
                patterns['singleton'].append(ligature_id)
            elif entity_count == 2:
                patterns['binary'].append(ligature_id)
            elif entity_count == 3:
                patterns['ternary'].append(ligature_id)
            elif entity_count > 5:
                patterns['large'].append(ligature_id)
        
        return patterns
    
    @staticmethod
    def analyze_entity_connectivity(entities: Set[EntityId],
                                  predicates: Dict[PredicateId, Predicate],
                                  ligatures: Dict[LigatureId, Ligature]) -> Dict[str, Any]:
        """Analyze how entities are connected through predicates and ligatures.
        
        Args:
            entities: Set of entity IDs to analyze.
            predicates: Dictionary of predicates.
            ligatures: Dictionary of ligatures.
            
        Returns:
            A dictionary containing connectivity analysis results.
        """
        analysis = {
            'entity_predicate_connections': defaultdict(list),
            'entity_ligature_connections': defaultdict(list),
            'connectivity_degrees': {},
            'isolated_entities': [],
            'hub_entities': [],  # Entities with high connectivity
        }
        
        # Analyze predicate connections
        for predicate_id, predicate in predicates.items():
            for entity_id in predicate.entities:
                if entity_id in entities:
                    analysis['entity_predicate_connections'][entity_id].append(predicate_id)
        
        # Analyze ligature connections
        for ligature_id, ligature in ligatures.items():
            for entity_id in ligature.entities:
                if entity_id in entities:
                    analysis['entity_ligature_connections'][entity_id].append(ligature_id)
        
        # Calculate connectivity degrees
        for entity_id in entities:
            predicate_degree = len(analysis['entity_predicate_connections'][entity_id])
            ligature_degree = len(analysis['entity_ligature_connections'][entity_id])
            total_degree = predicate_degree + ligature_degree
            
            analysis['connectivity_degrees'][entity_id] = {
                'predicate_degree': predicate_degree,
                'ligature_degree': ligature_degree,
                'total_degree': total_degree
            }
            
            if total_degree == 0:
                analysis['isolated_entities'].append(entity_id)
            elif total_degree > 5:  # Threshold for "hub" entities
                analysis['hub_entities'].append(entity_id)
        
        return analysis
    
    @staticmethod
    def validate_entity_predicate_consistency(entities: Dict[EntityId, Entity],
                                            predicates: Dict[PredicateId, Predicate],
                                            ligatures: Dict[LigatureId, Ligature]) -> List[str]:
        """Validate consistency between entities, predicates, and ligatures.
        
        Args:
            entities: Dictionary of entities.
            predicates: Dictionary of predicates.
            ligatures: Dictionary of ligatures.
            
        Returns:
            A list of error messages. Empty list means no errors.
        """
        errors = []
        
        # Check that all entities referenced by predicates exist
        for predicate_id, predicate in predicates.items():
            for entity_id in predicate.entities:
                if entity_id not in entities:
                    errors.append(f"Predicate {predicate_id} references non-existent entity {entity_id}")
        
        # Check that all entities referenced by ligatures exist
        for ligature_id, ligature in ligatures.items():
            for entity_id in ligature.entities:
                if entity_id not in entities:
                    errors.append(f"Ligature {ligature_id} references non-existent entity {entity_id}")
        
        # Check for orphaned entities (not used by any predicate or ligature)
        used_entities = set()
        
        for predicate in predicates.values():
            used_entities.update(predicate.entities)
        
        for ligature in ligatures.values():
            used_entities.update(ligature.entities)
        
        for entity_id in entities:
            if entity_id not in used_entities:
                errors.append(f"Entity {entity_id} is not used by any predicate or ligature")
        
        return errors

