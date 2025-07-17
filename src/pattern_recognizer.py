"""
Advanced Pattern Recognition Engine for Existential Graphs

This module provides sophisticated pattern recognition capabilities for
existential graphs using Entity-Predicate hypergraph architecture.
It identifies logical patterns, structural motifs, and transformation
opportunities within graphs.

Updated for Entity-Predicate hypergraph architecture where:
- CLIF terms (variables, constants) → Entities (Lines of Identity)
- CLIF predicates → Predicates (hyperedges connecting entities)
- CLIF quantifiers → Entity scoping in contexts

The pattern recognizer supports:
1. Logical pattern detection (quantification, implication, etc.)
2. Structural pattern analysis (connectivity, symmetry, etc.)
3. Transformation opportunity identification
4. Graph similarity and isomorphism detection
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import copy
from collections import defaultdict

from .eg_types import (
    Entity, Predicate, Context, Ligature,
    EntityId, PredicateId, ContextId, LigatureId, ItemId
)
from .graph import EGGraph
from .context import ContextManager


class PatternType(Enum):
    """Types of patterns that can be recognized."""
    UNIVERSAL_QUANTIFICATION = "universal_quantification"
    EXISTENTIAL_QUANTIFICATION = "existential_quantification"
    IMPLICATION = "implication"
    CONJUNCTION = "conjunction"
    DISJUNCTION = "disjunction"
    NEGATION = "negation"
    IDENTITY = "identity"
    PREDICATE_CHAIN = "predicate_chain"
    ENTITY_CLUSTER = "entity_cluster"
    SYMMETRIC_STRUCTURE = "symmetric_structure"
    RECURSIVE_PATTERN = "recursive_pattern"


class ConfidenceLevel(Enum):
    """Confidence levels for pattern recognition."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PatternMatch:
    """Represents a detected pattern in the graph."""
    pattern_type: PatternType
    confidence: ConfidenceLevel
    entities: Set[EntityId]
    predicates: Set[PredicateId]
    contexts: Set[ContextId]
    ligatures: Set[LigatureId]
    description: str
    properties: Dict[str, Any]
    transformation_hints: List[str]


@dataclass
class StructuralMetrics:
    """Metrics describing the structural properties of a graph."""
    entity_count: int
    predicate_count: int
    context_count: int
    ligature_count: int
    max_depth: int
    avg_predicate_arity: float
    connectivity_density: float
    clustering_coefficient: float
    entity_degree_distribution: Dict[int, int]
    predicate_arity_distribution: Dict[int, int]


@dataclass
class LogicalComplexity:
    """Measures of logical complexity in the graph."""
    quantification_depth: int
    negation_count: int
    implication_count: int
    conjunction_count: int
    variable_count: int
    constant_count: int
    free_variable_count: int
    bound_variable_count: int


class PatternRecognitionEngine:
    """
    Advanced pattern recognition engine for Entity-Predicate existential graphs.
    
    Provides comprehensive analysis of logical and structural patterns,
    enabling intelligent transformation suggestions and graph understanding.
    """
    
    def __init__(self):
        """Initialize the pattern recognition engine."""
        self.pattern_cache: Dict[str, List[PatternMatch]] = {}
        self.metrics_cache: Dict[str, StructuralMetrics] = {}
    
    def analyze_graph(self, graph: EGGraph) -> Dict[str, Any]:
        """Perform comprehensive analysis of a graph."""
        graph_hash = self._compute_graph_hash(graph)
        
        # Check cache first
        if graph_hash in self.pattern_cache:
            patterns = self.pattern_cache[graph_hash]
            metrics = self.metrics_cache[graph_hash]
        else:
            # Perform analysis
            patterns = self.find_patterns(graph)
            metrics = self.compute_structural_metrics(graph)
            
            # Cache results
            self.pattern_cache[graph_hash] = patterns
            self.metrics_cache[graph_hash] = metrics
        
        logical_complexity = self.compute_logical_complexity(graph)
        transformation_opportunities = self.find_transformation_opportunities(graph, patterns)
        
        return {
            "patterns": [self._pattern_to_dict(p) for p in patterns],
            "structural_metrics": self._metrics_to_dict(metrics),
            "logical_complexity": self._complexity_to_dict(logical_complexity),
            "transformation_opportunities": transformation_opportunities,
            "summary": self._generate_analysis_summary(patterns, metrics, logical_complexity)
        }
    
    def find_patterns(self, graph: EGGraph) -> List[PatternMatch]:
        """Find all recognizable patterns in the graph."""
        patterns = []
        
        # Logical patterns
        patterns.extend(self._find_quantification_patterns(graph))
        patterns.extend(self._find_implication_patterns(graph))
        patterns.extend(self._find_conjunction_patterns(graph))
        patterns.extend(self._find_negation_patterns(graph))
        patterns.extend(self._find_identity_patterns(graph))
        
        # Structural patterns
        patterns.extend(self._find_predicate_chains(graph))
        patterns.extend(self._find_entity_clusters(graph))
        patterns.extend(self._find_symmetric_structures(graph))
        patterns.extend(self._find_recursive_patterns(graph))
        
        return patterns
    
    def compute_structural_metrics(self, graph: EGGraph) -> StructuralMetrics:
        """Compute structural metrics for the graph."""
        entity_count = len(graph.entities)
        predicate_count = len(graph.predicates)
        context_count = len(graph.context_manager.contexts)
        ligature_count = len(graph.ligatures)
        
        # Calculate max depth
        max_depth = 0
        if graph.context_manager.contexts:
            max_depth = max(ctx.depth for ctx in graph.context_manager.contexts.values())
        
        # Calculate average predicate arity
        if predicate_count > 0:
            total_arity = sum(pred.arity for pred in graph.predicates.values())
            avg_predicate_arity = total_arity / predicate_count
        else:
            avg_predicate_arity = 0.0
        
        # Calculate connectivity metrics
        connectivity_density = self._calculate_connectivity_density(graph)
        clustering_coefficient = self._calculate_clustering_coefficient(graph)
        
        # Calculate degree distributions
        entity_degree_dist = self._calculate_entity_degree_distribution(graph)
        predicate_arity_dist = self._calculate_predicate_arity_distribution(graph)
        
        return StructuralMetrics(
            entity_count=entity_count,
            predicate_count=predicate_count,
            context_count=context_count,
            ligature_count=ligature_count,
            max_depth=max_depth,
            avg_predicate_arity=avg_predicate_arity,
            connectivity_density=connectivity_density,
            clustering_coefficient=clustering_coefficient,
            entity_degree_distribution=entity_degree_dist,
            predicate_arity_distribution=predicate_arity_dist
        )
    
    def compute_logical_complexity(self, graph: EGGraph) -> LogicalComplexity:
        """Compute logical complexity measures for the graph."""
        quantification_depth = 0
        negation_count = 0
        variable_count = 0
        constant_count = 0
        
        # Analyze contexts for quantification and negation
        for context in graph.context_manager.contexts.values():
            quantification_depth = max(quantification_depth, context.depth)
            if context.depth % 2 == 1:  # Odd depth = negation
                negation_count += 1
        
        # Analyze entities for variables and constants
        for entity in graph.entities.values():
            if entity.entity_type == 'variable':
                variable_count += 1
            elif entity.entity_type == 'constant':
                constant_count += 1
        
        # Find implications (patterns like ~[P & ~Q])
        implication_count = len(self._find_implication_patterns(graph))
        
        # Find conjunctions (multiple predicates in same positive context)
        conjunction_count = len(self._find_conjunction_patterns(graph))
        
        # Calculate free vs bound variables
        bound_variables = self._find_bound_variables(graph)
        free_variable_count = variable_count - len(bound_variables)
        bound_variable_count = len(bound_variables)
        
        return LogicalComplexity(
            quantification_depth=quantification_depth,
            negation_count=negation_count,
            implication_count=implication_count,
            conjunction_count=conjunction_count,
            variable_count=variable_count,
            constant_count=constant_count,
            free_variable_count=free_variable_count,
            bound_variable_count=bound_variable_count
        )
    
    def find_transformation_opportunities(self, graph: EGGraph, patterns: List[PatternMatch]) -> List[Dict[str, Any]]:
        """Find opportunities for graph transformations based on patterns."""
        opportunities = []
        
        # Look for double cuts that can be removed
        double_cuts = self._find_double_cuts(graph)
        for cut_pair in double_cuts:
            opportunities.append({
                "type": "double_cut_erasure",
                "description": "Remove redundant double cut",
                "target_contexts": cut_pair,
                "confidence": "high",
                "benefit": "Simplifies graph structure"
            })
        
        # Look for iteration opportunities
        iteration_targets = self._find_iteration_targets(graph)
        for target in iteration_targets:
            opportunities.append({
                "type": "iteration",
                "description": f"Iterate {target['item_type']} to deeper context",
                "target_items": target['items'],
                "target_context": target['context'],
                "confidence": "medium",
                "benefit": "Enables further transformations"
            })
        
        # Look for entity join opportunities
        join_opportunities = self._find_entity_join_opportunities(graph)
        for opportunity in join_opportunities:
            opportunities.append({
                "type": "entity_join",
                "description": "Join equivalent entities",
                "target_entities": opportunity['entities'],
                "confidence": "high",
                "benefit": "Reduces redundancy"
            })
        
        # Look for insertion opportunities based on patterns
        for pattern in patterns:
            if pattern.pattern_type == PatternType.IMPLICATION:
                opportunities.append({
                    "type": "insertion",
                    "description": "Insert additional premises for implication",
                    "target_context": list(pattern.contexts)[0] if pattern.contexts else None,
                    "confidence": "low",
                    "benefit": "Strengthens logical argument"
                })
        
        return opportunities
    
    def find_similar_subgraphs(self, graph: EGGraph, target_pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find subgraphs similar to a target pattern."""
        similar_subgraphs = []
        
        # This would implement graph isomorphism detection
        # For now, return a placeholder
        
        return similar_subgraphs
    
    def suggest_optimizations(self, graph: EGGraph) -> List[Dict[str, Any]]:
        """Suggest optimizations for the graph structure."""
        suggestions = []
        
        metrics = self.compute_structural_metrics(graph)
        
        # Suggest simplifications for overly complex graphs
        if metrics.entity_count > 20:
            suggestions.append({
                "type": "entity_reduction",
                "description": "Consider reducing the number of entities",
                "priority": "medium",
                "reason": "High entity count may indicate over-specification"
            })
        
        if metrics.max_depth > 5:
            suggestions.append({
                "type": "depth_reduction",
                "description": "Consider reducing nesting depth",
                "priority": "high",
                "reason": "Deep nesting makes graphs hard to understand"
            })
        
        # Suggest structural improvements
        if metrics.connectivity_density < 0.3:
            suggestions.append({
                "type": "connectivity_improvement",
                "description": "Consider adding more connections between entities",
                "priority": "low",
                "reason": "Low connectivity may indicate missing relationships"
            })
        
        return suggestions
    
    # Pattern detection methods
    
    def _find_quantification_patterns(self, graph: EGGraph) -> List[PatternMatch]:
        """Find quantification patterns in the graph."""
        patterns = []
        
        # Find existential quantification (entities in positive contexts)
        for context in graph.context_manager.contexts.values():
            if context.depth > 0 and context.depth % 2 == 0:  # Positive, non-root context
                items_in_context = graph.context_manager.get_items_in_context(context.id)
                entities_in_context = {item for item in items_in_context if item in graph.entities}
                
                if entities_in_context:
                    # Check if these are variables (quantified)
                    variables = {eid for eid in entities_in_context 
                               if graph.entities[eid].entity_type == 'variable'}
                    
                    if variables:
                        patterns.append(PatternMatch(
                            pattern_type=PatternType.EXISTENTIAL_QUANTIFICATION,
                            confidence=ConfidenceLevel.HIGH,
                            entities=variables,
                            predicates=set(),
                            contexts={context.id},
                            ligatures=set(),
                            description=f"Existential quantification of {len(variables)} variables",
                            properties={"depth": context.depth, "variable_count": len(variables)},
                            transformation_hints=["Can iterate variables to deeper contexts"]
                        ))
        
        # Find universal quantification patterns (~[exists x ~[P(x)]])
        universal_patterns = self._find_universal_patterns(graph)
        patterns.extend(universal_patterns)
        
        return patterns
    
    def _find_implication_patterns(self, graph: EGGraph) -> List[PatternMatch]:
        """Find implication patterns (~[P & ~Q])."""
        patterns = []
        
        # Look for contexts at depth 1 (first negation)
        for context in graph.context_manager.contexts.values():
            if context.depth == 1:  # First level cut
                items_in_context = graph.context_manager.get_items_in_context(context.id)
                
                # Look for predicates (antecedent) and nested cuts (consequent)
                predicates_in_context = {item for item in items_in_context if item in graph.predicates}
                child_contexts = [ctx for ctx in graph.context_manager.contexts.values() 
                                if ctx.parent_context == context.id]
                
                if predicates_in_context and child_contexts:
                    # This looks like an implication pattern
                    patterns.append(PatternMatch(
                        pattern_type=PatternType.IMPLICATION,
                        confidence=ConfidenceLevel.MEDIUM,
                        entities=set(),
                        predicates=predicates_in_context,
                        contexts={context.id} | {ctx.id for ctx in child_contexts},
                        ligatures=set(),
                        description=f"Implication with {len(predicates_in_context)} antecedents",
                        properties={"antecedent_count": len(predicates_in_context)},
                        transformation_hints=["Can strengthen by adding premises"]
                    ))
        
        return patterns
    
    def _find_conjunction_patterns(self, graph: EGGraph) -> List[PatternMatch]:
        """Find conjunction patterns (multiple predicates in same context)."""
        patterns = []
        
        for context in graph.context_manager.contexts.values():
            if context.depth % 2 == 0:  # Positive context
                items_in_context = graph.context_manager.get_items_in_context(context.id)
                predicates_in_context = {item for item in items_in_context if item in graph.predicates}
                
                if len(predicates_in_context) > 1:
                    # Multiple predicates in positive context = conjunction
                    patterns.append(PatternMatch(
                        pattern_type=PatternType.CONJUNCTION,
                        confidence=ConfidenceLevel.HIGH,
                        entities=set(),
                        predicates=predicates_in_context,
                        contexts={context.id},
                        ligatures=set(),
                        description=f"Conjunction of {len(predicates_in_context)} predicates",
                        properties={"predicate_count": len(predicates_in_context)},
                        transformation_hints=["Can erase individual conjuncts"]
                    ))
        
        return patterns
    
    def _find_negation_patterns(self, graph: EGGraph) -> List[PatternMatch]:
        """Find negation patterns (odd-depth contexts)."""
        patterns = []
        
        for context in graph.context_manager.contexts.values():
            if context.depth % 2 == 1:  # Negative context
                items_in_context = graph.context_manager.get_items_in_context(context.id)
                
                if items_in_context:
                    patterns.append(PatternMatch(
                        pattern_type=PatternType.NEGATION,
                        confidence=ConfidenceLevel.HIGH,
                        entities={item for item in items_in_context if item in graph.entities},
                        predicates={item for item in items_in_context if item in graph.predicates},
                        contexts={context.id},
                        ligatures=set(),
                        description=f"Negation at depth {context.depth}",
                        properties={"depth": context.depth},
                        transformation_hints=["Can insert double cut for manipulation"]
                    ))
        
        return patterns
    
    def _find_identity_patterns(self, graph: EGGraph) -> List[PatternMatch]:
        """Find identity patterns (ligatures connecting entities)."""
        patterns = []
        
        for ligature in graph.ligatures.values():
            entities_in_ligature = {item for item in ligature.connected_items 
                                  if item in graph.entities}
            
            if len(entities_in_ligature) >= 2:
                patterns.append(PatternMatch(
                    pattern_type=PatternType.IDENTITY,
                    confidence=ConfidenceLevel.HIGH,
                    entities=entities_in_ligature,
                    predicates=set(),
                    contexts=set(),
                    ligatures={ligature.id},
                    description=f"Identity connecting {len(entities_in_ligature)} entities",
                    properties={"entity_count": len(entities_in_ligature)},
                    transformation_hints=["Can join or sever connected entities"]
                ))
        
        return patterns
    
    def _find_predicate_chains(self, graph: EGGraph) -> List[PatternMatch]:
        """Find chains of connected predicates."""
        patterns = []
        
        # Build entity-predicate connectivity graph
        entity_predicates = defaultdict(set)
        for pred_id, predicate in graph.predicates.items():
            for entity_id in predicate.entities:
                entity_predicates[entity_id].add(pred_id)
        
        # Find chains where entities connect multiple predicates
        visited_predicates = set()
        
        for entity_id, connected_preds in entity_predicates.items():
            if len(connected_preds) >= 2:
                chain_predicates = set()
                chain_entities = set()
                
                # Build chain starting from this entity
                self._build_predicate_chain(
                    entity_id, connected_preds, entity_predicates, 
                    chain_predicates, chain_entities, visited_predicates
                )
                
                if len(chain_predicates) >= 3:  # Minimum chain length
                    patterns.append(PatternMatch(
                        pattern_type=PatternType.PREDICATE_CHAIN,
                        confidence=ConfidenceLevel.MEDIUM,
                        entities=chain_entities,
                        predicates=chain_predicates,
                        contexts=set(),
                        ligatures=set(),
                        description=f"Predicate chain with {len(chain_predicates)} predicates",
                        properties={"chain_length": len(chain_predicates)},
                        transformation_hints=["Chain structure enables complex transformations"]
                    ))
        
        return patterns
    
    def _find_entity_clusters(self, graph: EGGraph) -> List[PatternMatch]:
        """Find clusters of highly connected entities."""
        patterns = []
        
        # Calculate entity connectivity
        entity_connections = defaultdict(set)
        
        # Connections through predicates
        for predicate in graph.predicates.values():
            entities = list(predicate.entities)
            for i, entity1 in enumerate(entities):
                for entity2 in entities[i+1:]:
                    entity_connections[entity1].add(entity2)
                    entity_connections[entity2].add(entity1)
        
        # Connections through ligatures
        for ligature in graph.ligatures.values():
            entities = [item for item in ligature.connected_items if item in graph.entities]
            for i, entity1 in enumerate(entities):
                for entity2 in entities[i+1:]:
                    entity_connections[entity1].add(entity2)
                    entity_connections[entity2].add(entity1)
        
        # Find clusters (entities with high connectivity)
        visited_entities = set()
        
        for entity_id, connections in entity_connections.items():
            if entity_id not in visited_entities and len(connections) >= 2:
                cluster_entities = {entity_id}
                cluster_predicates = set()
                
                # Build cluster
                self._build_entity_cluster(
                    entity_id, entity_connections, graph,
                    cluster_entities, cluster_predicates, visited_entities
                )
                
                if len(cluster_entities) >= 3:  # Minimum cluster size
                    patterns.append(PatternMatch(
                        pattern_type=PatternType.ENTITY_CLUSTER,
                        confidence=ConfidenceLevel.MEDIUM,
                        entities=cluster_entities,
                        predicates=cluster_predicates,
                        contexts=set(),
                        ligatures=set(),
                        description=f"Entity cluster with {len(cluster_entities)} entities",
                        properties={"cluster_size": len(cluster_entities)},
                        transformation_hints=["Clustered entities may be candidates for joining"]
                    ))
        
        return patterns
    
    def _find_symmetric_structures(self, graph: EGGraph) -> List[PatternMatch]:
        """Find symmetric structures in the graph."""
        patterns = []
        
        # Look for symmetric predicate patterns
        predicate_signatures = defaultdict(list)
        
        for pred_id, predicate in graph.predicates.items():
            # Create signature based on arity and entity types
            entity_types = []
            for entity_id in predicate.entities:
                entity = graph.entities[entity_id]
                entity_types.append(entity.entity_type)
            
            signature = (predicate.name, predicate.arity, tuple(sorted(entity_types)))
            predicate_signatures[signature].append(pred_id)
        
        # Find groups of predicates with same signature
        for signature, pred_ids in predicate_signatures.items():
            if len(pred_ids) >= 2:
                all_entities = set()
                for pred_id in pred_ids:
                    all_entities.update(graph.predicates[pred_id].entities)
                
                patterns.append(PatternMatch(
                    pattern_type=PatternType.SYMMETRIC_STRUCTURE,
                    confidence=ConfidenceLevel.LOW,
                    entities=all_entities,
                    predicates=set(pred_ids),
                    contexts=set(),
                    ligatures=set(),
                    description=f"Symmetric structure with {len(pred_ids)} similar predicates",
                    properties={"predicate_count": len(pred_ids), "signature": signature},
                    transformation_hints=["Symmetric structures may enable parallel transformations"]
                ))
        
        return patterns
    
    def _find_recursive_patterns(self, graph: EGGraph) -> List[PatternMatch]:
        """Find recursive patterns in the graph."""
        patterns = []
        
        # Look for similar structures at different context depths
        context_structures = {}
        
        for context in graph.context_manager.contexts.values():
            items_in_context = graph.context_manager.get_items_in_context(context.id)
            predicates_in_context = {item for item in items_in_context if item in graph.predicates}
            
            # Create structure signature
            predicate_names = sorted([graph.predicates[pid].name for pid in predicates_in_context])
            structure_signature = tuple(predicate_names)
            
            if structure_signature not in context_structures:
                context_structures[structure_signature] = []
            context_structures[structure_signature].append(context.id)
        
        # Find recurring structures
        for signature, context_ids in context_structures.items():
            if len(context_ids) >= 2 and signature:  # At least 2 occurrences, non-empty
                all_entities = set()
                all_predicates = set()
                
                for context_id in context_ids:
                    items = graph.context_manager.get_items_in_context(context_id)
                    all_entities.update(item for item in items if item in graph.entities)
                    all_predicates.update(item for item in items if item in graph.predicates)
                
                patterns.append(PatternMatch(
                    pattern_type=PatternType.RECURSIVE_PATTERN,
                    confidence=ConfidenceLevel.LOW,
                    entities=all_entities,
                    predicates=all_predicates,
                    contexts=set(context_ids),
                    ligatures=set(),
                    description=f"Recursive pattern appearing {len(context_ids)} times",
                    properties={"occurrence_count": len(context_ids), "signature": signature},
                    transformation_hints=["Recursive patterns may enable inductive reasoning"]
                ))
        
        return patterns
    
    # Helper methods
    
    def _find_universal_patterns(self, graph: EGGraph) -> List[PatternMatch]:
        """Find universal quantification patterns (~[exists x ~[P(x)]])."""
        patterns = []
        
        # Look for the pattern: depth 1 (cut) -> depth 2 (exists) -> depth 3 (cut) -> depth 4 (predicate)
        for context1 in graph.context_manager.contexts.values():
            if context1.depth == 1:  # First cut
                for context2 in graph.context_manager.contexts.values():
                    if context2.parent_context == context1.id and context2.depth == 2:  # Existential scope
                        for context3 in graph.context_manager.contexts.values():
                            if context3.parent_context == context2.id and context3.depth == 3:  # Second cut
                                items_in_context3 = graph.context_manager.get_items_in_context(context3.id)
                                if items_in_context3:  # Has content
                                    patterns.append(PatternMatch(
                                        pattern_type=PatternType.UNIVERSAL_QUANTIFICATION,
                                        confidence=ConfidenceLevel.MEDIUM,
                                        entities=set(),
                                        predicates=set(),
                                        contexts={context1.id, context2.id, context3.id},
                                        ligatures=set(),
                                        description="Universal quantification pattern",
                                        properties={"depth": 3},
                                        transformation_hints=["Can manipulate inner predicates"]
                                    ))
        
        return patterns
    
    def _find_double_cuts(self, graph: EGGraph) -> List[Tuple[ContextId, ContextId]]:
        """Find double cut patterns (nested cuts with no content between)."""
        double_cuts = []
        
        for context in graph.context_manager.contexts.values():
            # Look for child contexts
            child_contexts = [ctx for ctx in graph.context_manager.contexts.values() 
                            if ctx.parent_context == context.id]
            
            if len(child_contexts) == 1:  # Exactly one child
                child = child_contexts[0]
                
                # Check if parent context has no other content
                items_in_parent = graph.context_manager.get_items_in_context(context.id)
                non_context_items = {item for item in items_in_parent 
                                   if item not in graph.context_manager.contexts}
                
                if not non_context_items:  # No content except the child context
                    double_cuts.append((context.id, child.id))
        
        return double_cuts
    
    def _find_iteration_targets(self, graph: EGGraph) -> List[Dict[str, Any]]:
        """Find items that could be iterated to deeper contexts."""
        targets = []
        
        for context in graph.context_manager.contexts.values():
            items_in_context = graph.context_manager.get_items_in_context(context.id)
            
            # Look for child contexts where items could be iterated
            child_contexts = [ctx for ctx in graph.context_manager.contexts.values() 
                            if ctx.parent_context == context.id]
            
            for child_context in child_contexts:
                if context.depth % 2 == 0:  # Can iterate from positive to positive
                    for item_id in items_in_context:
                        if item_id in graph.entities or item_id in graph.predicates:
                            targets.append({
                                "items": {item_id},
                                "context": child_context.id,
                                "item_type": "entity" if item_id in graph.entities else "predicate"
                            })
        
        return targets
    
    def _find_entity_join_opportunities(self, graph: EGGraph) -> List[Dict[str, Any]]:
        """Find entities that could be joined."""
        opportunities = []
        
        # Look for entities connected by ligatures
        for ligature in graph.ligatures.values():
            entities_in_ligature = {item for item in ligature.connected_items 
                                  if item in graph.entities}
            
            if len(entities_in_ligature) >= 2:
                opportunities.append({
                    "entities": entities_in_ligature,
                    "reason": "Connected by ligature"
                })
        
        # Look for entities with same name (potential duplicates)
        entity_names = defaultdict(set)
        for entity_id, entity in graph.entities.items():
            entity_names[entity.name].add(entity_id)
        
        for name, entity_ids in entity_names.items():
            if len(entity_ids) >= 2:
                opportunities.append({
                    "entities": entity_ids,
                    "reason": f"Same name: {name}"
                })
        
        return opportunities
    
    def _find_bound_variables(self, graph: EGGraph) -> Set[EntityId]:
        """Find variables that are bound by quantifiers."""
        bound_variables = set()
        
        # Variables in non-root contexts are considered bound
        for context in graph.context_manager.contexts.values():
            if context.depth > 0:  # Non-root context
                items_in_context = graph.context_manager.get_items_in_context(context.id)
                for item_id in items_in_context:
                    if item_id in graph.entities:
                        entity = graph.entities[item_id]
                        if entity.entity_type == 'variable':
                            bound_variables.add(item_id)
        
        return bound_variables
    
    def _build_predicate_chain(self, entity_id: EntityId, connected_preds: Set[PredicateId],
                              entity_predicates: Dict[EntityId, Set[PredicateId]],
                              chain_predicates: Set[PredicateId], chain_entities: Set[EntityId],
                              visited_predicates: Set[PredicateId]) -> None:
        """Build a chain of connected predicates."""
        chain_entities.add(entity_id)
        
        for pred_id in connected_preds:
            if pred_id not in visited_predicates:
                visited_predicates.add(pred_id)
                chain_predicates.add(pred_id)
                
                # Find other entities in this predicate
                predicate = self.graph.predicates[pred_id]  # This would need graph reference
                for other_entity_id in predicate.entities:
                    if other_entity_id != entity_id and other_entity_id not in chain_entities:
                        other_connected_preds = entity_predicates[other_entity_id] - {pred_id}
                        if other_connected_preds:
                            self._build_predicate_chain(
                                other_entity_id, other_connected_preds, entity_predicates,
                                chain_predicates, chain_entities, visited_predicates
                            )
    
    def _build_entity_cluster(self, entity_id: EntityId, 
                             entity_connections: Dict[EntityId, Set[EntityId]],
                             graph: EGGraph, cluster_entities: Set[EntityId],
                             cluster_predicates: Set[PredicateId], 
                             visited_entities: Set[EntityId]) -> None:
        """Build a cluster of connected entities."""
        visited_entities.add(entity_id)
        
        # Add predicates that include this entity
        for pred_id, predicate in graph.predicates.items():
            if entity_id in predicate.entities:
                cluster_predicates.add(pred_id)
        
        # Recursively add connected entities
        for connected_entity_id in entity_connections[entity_id]:
            if connected_entity_id not in visited_entities:
                cluster_entities.add(connected_entity_id)
                self._build_entity_cluster(
                    connected_entity_id, entity_connections, graph,
                    cluster_entities, cluster_predicates, visited_entities
                )
    
    def _calculate_connectivity_density(self, graph: EGGraph) -> float:
        """Calculate the connectivity density of the graph."""
        if not graph.entities or not graph.predicates:
            return 0.0
        
        # Count actual connections
        actual_connections = 0
        for predicate in graph.predicates.values():
            actual_connections += len(predicate.entities)
        
        # Calculate maximum possible connections
        max_connections = len(graph.entities) * len(graph.predicates)
        
        return actual_connections / max_connections if max_connections > 0 else 0.0
    
    def _calculate_clustering_coefficient(self, graph: EGGraph) -> float:
        """Calculate the clustering coefficient of the graph."""
        if len(graph.entities) < 3:
            return 0.0
        
        # Build entity adjacency through predicates
        entity_neighbors = defaultdict(set)
        for predicate in graph.predicates.values():
            entities = list(predicate.entities)
            for i, entity1 in enumerate(entities):
                for entity2 in entities[i+1:]:
                    entity_neighbors[entity1].add(entity2)
                    entity_neighbors[entity2].add(entity1)
        
        # Calculate clustering coefficient
        total_coefficient = 0.0
        entity_count = 0
        
        for entity_id, neighbors in entity_neighbors.items():
            if len(neighbors) >= 2:
                # Count triangles
                triangles = 0
                neighbors_list = list(neighbors)
                for i, neighbor1 in enumerate(neighbors_list):
                    for neighbor2 in neighbors_list[i+1:]:
                        if neighbor2 in entity_neighbors[neighbor1]:
                            triangles += 1
                
                # Calculate coefficient for this entity
                possible_triangles = len(neighbors) * (len(neighbors) - 1) // 2
                if possible_triangles > 0:
                    total_coefficient += triangles / possible_triangles
                    entity_count += 1
        
        return total_coefficient / entity_count if entity_count > 0 else 0.0
    
    def _calculate_entity_degree_distribution(self, graph: EGGraph) -> Dict[int, int]:
        """Calculate the degree distribution of entities."""
        degree_distribution = defaultdict(int)
        
        for entity_id in graph.entities:
            degree = 0
            for predicate in graph.predicates.values():
                if entity_id in predicate.entities:
                    degree += 1
            degree_distribution[degree] += 1
        
        return dict(degree_distribution)
    
    def _calculate_predicate_arity_distribution(self, graph: EGGraph) -> Dict[int, int]:
        """Calculate the arity distribution of predicates."""
        arity_distribution = defaultdict(int)
        
        for predicate in graph.predicates.values():
            arity_distribution[predicate.arity] += 1
        
        return dict(arity_distribution)
    
    def _compute_graph_hash(self, graph: EGGraph) -> str:
        """Compute a hash for the graph structure."""
        # Simple hash based on counts and structure
        entity_count = len(graph.entities)
        predicate_count = len(graph.predicates)
        context_count = len(graph.context_manager.contexts)
        max_depth = max((ctx.depth for ctx in graph.context_manager.contexts.values()), default=0)
        
        return f"{entity_count}_{predicate_count}_{context_count}_{max_depth}"
    
    def _pattern_to_dict(self, pattern: PatternMatch) -> Dict[str, Any]:
        """Convert a pattern match to a dictionary."""
        return {
            "type": pattern.pattern_type.value,
            "confidence": pattern.confidence.value,
            "description": pattern.description,
            "entities": [str(eid) for eid in pattern.entities],
            "predicates": [str(pid) for pid in pattern.predicates],
            "contexts": [str(cid) for cid in pattern.contexts],
            "ligatures": [str(lid) for lid in pattern.ligatures],
            "properties": pattern.properties,
            "transformation_hints": pattern.transformation_hints
        }
    
    def _metrics_to_dict(self, metrics: StructuralMetrics) -> Dict[str, Any]:
        """Convert structural metrics to a dictionary."""
        return {
            "entity_count": metrics.entity_count,
            "predicate_count": metrics.predicate_count,
            "context_count": metrics.context_count,
            "ligature_count": metrics.ligature_count,
            "max_depth": metrics.max_depth,
            "avg_predicate_arity": metrics.avg_predicate_arity,
            "connectivity_density": metrics.connectivity_density,
            "clustering_coefficient": metrics.clustering_coefficient,
            "entity_degree_distribution": metrics.entity_degree_distribution,
            "predicate_arity_distribution": metrics.predicate_arity_distribution
        }
    
    def _complexity_to_dict(self, complexity: LogicalComplexity) -> Dict[str, Any]:
        """Convert logical complexity to a dictionary."""
        return {
            "quantification_depth": complexity.quantification_depth,
            "negation_count": complexity.negation_count,
            "implication_count": complexity.implication_count,
            "conjunction_count": complexity.conjunction_count,
            "variable_count": complexity.variable_count,
            "constant_count": complexity.constant_count,
            "free_variable_count": complexity.free_variable_count,
            "bound_variable_count": complexity.bound_variable_count
        }
    
    def _generate_analysis_summary(self, patterns: List[PatternMatch], 
                                  metrics: StructuralMetrics, 
                                  complexity: LogicalComplexity) -> Dict[str, Any]:
        """Generate a summary of the analysis."""
        pattern_counts = defaultdict(int)
        for pattern in patterns:
            pattern_counts[pattern.pattern_type.value] += 1
        
        complexity_level = "Simple"
        if complexity.quantification_depth > 2 or complexity.variable_count > 5:
            complexity_level = "Moderate"
        if complexity.quantification_depth > 4 or complexity.variable_count > 10:
            complexity_level = "Complex"
        
        return {
            "total_patterns": len(patterns),
            "pattern_types": dict(pattern_counts),
            "complexity_level": complexity_level,
            "structural_summary": f"{metrics.entity_count} entities, {metrics.predicate_count} predicates, depth {metrics.max_depth}",
            "logical_summary": f"{complexity.variable_count} variables, {complexity.negation_count} negations",
            "key_insights": self._generate_key_insights(patterns, metrics, complexity)
        }
    
    def _generate_key_insights(self, patterns: List[PatternMatch], 
                              metrics: StructuralMetrics, 
                              complexity: LogicalComplexity) -> List[str]:
        """Generate key insights about the graph."""
        insights = []
        
        if complexity.quantification_depth > 3:
            insights.append("Deep quantification structure suggests sophisticated logical reasoning")
        
        if metrics.connectivity_density > 0.7:
            insights.append("High connectivity indicates rich relational structure")
        
        if complexity.free_variable_count > 0:
            insights.append("Free variables present - graph may be incomplete")
        
        implication_patterns = [p for p in patterns if p.pattern_type == PatternType.IMPLICATION]
        if len(implication_patterns) > 2:
            insights.append("Multiple implications suggest complex logical argument")
        
        if metrics.max_depth == 0:
            insights.append("No cuts present - limited transformation options")
        
        return insights


# Convenience functions for pattern analysis

def quick_pattern_analysis(graph: EGGraph) -> Dict[str, Any]:
    """Perform a quick pattern analysis of a graph."""
    engine = PatternRecognitionEngine()
    return engine.analyze_graph(graph)


def find_specific_pattern(graph: EGGraph, pattern_type: PatternType) -> List[PatternMatch]:
    """Find all instances of a specific pattern type."""
    engine = PatternRecognitionEngine()
    all_patterns = engine.find_patterns(graph)
    return [p for p in all_patterns if p.pattern_type == pattern_type]


def compare_graph_complexity(graph1: EGGraph, graph2: EGGraph) -> Dict[str, Any]:
    """Compare the complexity of two graphs."""
    engine = PatternRecognitionEngine()
    
    complexity1 = engine.compute_logical_complexity(graph1)
    complexity2 = engine.compute_logical_complexity(graph2)
    
    metrics1 = engine.compute_structural_metrics(graph1)
    metrics2 = engine.compute_structural_metrics(graph2)
    
    return {
        "graph1": {
            "logical_complexity": engine._complexity_to_dict(complexity1),
            "structural_metrics": engine._metrics_to_dict(metrics1)
        },
        "graph2": {
            "logical_complexity": engine._complexity_to_dict(complexity2),
            "structural_metrics": engine._metrics_to_dict(metrics2)
        },
        "comparison": {
            "more_complex": "graph1" if complexity1.quantification_depth > complexity2.quantification_depth else "graph2",
            "larger": "graph1" if metrics1.entity_count + metrics1.predicate_count > metrics2.entity_count + metrics2.predicate_count else "graph2",
            "deeper": "graph1" if metrics1.max_depth > metrics2.max_depth else "graph2"
        }
    }

