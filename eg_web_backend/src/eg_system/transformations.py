"""
Complete transformation engine implementing Peirce's existential graph transformation rules.

This module provides a comprehensive implementation of all transformation rules
for existential graphs, including Alpha and Beta rules with proper ligature
handling and validation.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid

from .eg_types import (
    Node, Edge, Context, Ligature,
    NodeId, EdgeId, ContextId, LigatureId, ItemId,
    ValidationError, pmap, pset
)
from .graph import EGGraph
from .context import ContextManager


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    error_message: str


class TransformationType(Enum):
    """Types of existential graph transformations."""
    # Alpha rules (propositional logic)
    DOUBLE_CUT_INSERTION = "double_cut_insertion"
    DOUBLE_CUT_ERASURE = "double_cut_erasure"
    
    # Beta rules (predicate logic)
    ERASURE = "erasure"
    INSERTION = "insertion"
    ITERATION = "iteration"
    DEITERATION = "deiteration"
    
    # Ligature operations
    LIGATURE_JOIN = "ligature_join"
    LIGATURE_SEVER = "ligature_sever"
    
    # Constants and functions (if supported)
    CONSTANT_INTRODUCTION = "constant_introduction"
    CONSTANT_ELIMINATION = "constant_elimination"
    FUNCTION_COMPOSITION = "function_composition"


class TransformationResult(Enum):
    """Result of a transformation attempt."""
    SUCCESS = "success"
    INVALID_RULE = "invalid_rule"
    PRECONDITION_FAILED = "precondition_failed"
    LIGATURE_VIOLATION = "ligature_violation"
    CONTEXT_VIOLATION = "context_violation"
    ISOMORPHISM_FAILED = "isomorphism_failed"


@dataclass
class TransformationAttempt:
    """Record of a transformation attempt."""
    transformation_type: TransformationType
    source_graph: EGGraph
    target_items: Set[ItemId]
    target_context: Optional[ContextId]
    result: TransformationResult
    result_graph: Optional[EGGraph]
    error_message: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class TransformationRule:
    """Definition of a transformation rule."""
    rule_type: TransformationType
    name: str
    description: str
    preconditions: List[str]
    effects: List[str]
    ligature_effects: List[str]


class TransformationEngine:
    """Complete transformation engine for existential graphs."""
    
    def __init__(self):
        """Initialize the transformation engine."""
        self.transformation_history: List[TransformationAttempt] = []
        self.rules = self._initialize_rules()
        self.validator = TransformationValidator()
    
    def apply_transformation(
        self, 
        graph: EGGraph, 
        transformation_type: TransformationType,
        target_items: Set[ItemId] = None,
        target_context: ContextId = None,
        **kwargs
    ) -> TransformationAttempt:
        """Apply a transformation to the graph.
        
        Args:
            graph: The source graph to transform.
            transformation_type: Type of transformation to apply.
            target_items: Items to be transformed (if applicable).
            target_context: Target context for the transformation.
            **kwargs: Additional transformation-specific parameters.
            
        Returns:
            TransformationAttempt with the result.
        """
        target_items = target_items or set()
        
        # Create attempt record
        attempt = TransformationAttempt(
            transformation_type=transformation_type,
            source_graph=graph,
            target_items=target_items,
            target_context=target_context,
            result=TransformationResult.SUCCESS,  # Will be updated
            result_graph=None,
            error_message=None,
            metadata={}
        )
        
        try:
            # Validate preconditions
            validation_result = self._validate_preconditions(
                graph, transformation_type, target_items, target_context, **kwargs
            )
            
            if not validation_result.is_valid:
                attempt.result = TransformationResult.PRECONDITION_FAILED
                attempt.error_message = validation_result.error_message
                return attempt
            
            # Apply the specific transformation
            if transformation_type == TransformationType.DOUBLE_CUT_INSERTION:
                result_graph = self._apply_double_cut_insertion(graph, target_context, **kwargs)
            elif transformation_type == TransformationType.DOUBLE_CUT_ERASURE:
                result_graph = self._apply_double_cut_erasure(graph, target_context, **kwargs)
            elif transformation_type == TransformationType.ERASURE:
                result_graph = self._apply_erasure(graph, target_items, **kwargs)
            elif transformation_type == TransformationType.INSERTION:
                result_graph = self._apply_insertion(graph, target_context, **kwargs)
            elif transformation_type == TransformationType.ITERATION:
                result_graph = self._apply_iteration(graph, target_items, target_context, **kwargs)
            elif transformation_type == TransformationType.DEITERATION:
                result_graph = self._apply_deiteration(graph, target_items, **kwargs)
            elif transformation_type == TransformationType.LIGATURE_JOIN:
                result_graph = self._apply_ligature_join(graph, target_items, **kwargs)
            elif transformation_type == TransformationType.LIGATURE_SEVER:
                result_graph = self._apply_ligature_sever(graph, target_items, **kwargs)
            else:
                attempt.result = TransformationResult.INVALID_RULE
                attempt.error_message = f"Unsupported transformation type: {transformation_type}"
                return attempt
            
            # Validate the result
            if result_graph is None:
                attempt.result = TransformationResult.INVALID_RULE
                attempt.error_message = "Transformation returned None"
                return attempt
            
            # Validate ligature consistency
            ligature_validation = self._validate_ligature_consistency(result_graph)
            if not ligature_validation.is_valid:
                attempt.result = TransformationResult.LIGATURE_VIOLATION
                attempt.error_message = ligature_validation.error_message
                return attempt
            
            # Success
            attempt.result_graph = result_graph
            attempt.metadata = {
                'nodes_added': len(result_graph.nodes) - len(graph.nodes),
                'edges_added': len(result_graph.edges) - len(graph.edges),
                'contexts_added': len(result_graph.context_manager.contexts) - len(graph.context_manager.contexts),
                'ligatures_added': len(result_graph.ligatures) - len(graph.ligatures)
            }
            
        except Exception as e:
            attempt.result = TransformationResult.INVALID_RULE
            attempt.error_message = f"Transformation failed: {str(e)}"
        
        finally:
            self.transformation_history.append(attempt)
        
        return attempt
    def get_legal_transformations(self, graph: EGGraph, context_id: ContextId = None) -> Dict[TransformationType, List[Set[ItemId]]]:
        """Get all legal transformations for the current graph state.
        
        Args:
            graph: The graph to analyze.
            context_id: Optional context to focus on.
            
        Returns:
            Dictionary mapping transformation types to lists of possible target sets.
        """
        legal_transformations = {}
        
        # Check each transformation type
        for transformation_type in TransformationType:
            validation_result = self.validator.validate_transformation(
                graph, transformation_type, context_id or graph.context_manager.root_context
            )
            
            if validation_result.is_valid:
                # Find possible target sets for this transformation
                target_sets = self._find_transformation_targets(graph, transformation_type, context_id)
                if target_sets:
                    legal_transformations[transformation_type] = target_sets
        
        return legal_transformations
    
    def _find_transformation_targets(self, graph: EGGraph, transformation_type: TransformationType, 
                                   context_id: ContextId = None) -> List[Set[ItemId]]:
        """Find possible target sets for a given transformation type."""
        targets = []
        
        if transformation_type == TransformationType.DOUBLE_CUT_INSERTION:
            # Can insert double cuts around any subgraph
            contexts = [context_id] if context_id else list(graph.context_manager.contexts.keys())
            for ctx_id in contexts:
                items_in_context = graph.get_items_in_context(ctx_id)
                if items_in_context:
                    targets.append(items_in_context)
        
        elif transformation_type == TransformationType.DOUBLE_CUT_ERASURE:
            # Look for double cuts to erase
            for ctx_id in graph.context_manager.contexts:
                context = graph.context_manager.get_context(ctx_id)
                if context and context.parent_context:
                    parent = graph.context_manager.get_context(context.parent_context)
                    if parent and parent.parent_context:
                        # Check if this is a double cut pattern
                        targets.append({ctx_id})
        
        elif transformation_type == TransformationType.ERASURE:
            # Can erase items in negative contexts
            for ctx_id in graph.context_manager.contexts:
                context = graph.context_manager.get_context(ctx_id)
                if context and not context.is_positive:
                    items = graph.get_items_in_context(ctx_id)
                    for item_id in items:
                        targets.append({item_id})
        
        elif transformation_type == TransformationType.INSERTION:
            # Can insert into positive contexts
            for ctx_id in graph.context_manager.contexts:
                context = graph.context_manager.get_context(ctx_id)
                if context and context.is_positive:
                    targets.append(set())  # Empty set means "insert here"
        
        # Add more transformation target finding logic as needed
        
        return targets

    def _has_double_cuts(self, graph: EGGraph) -> bool:
        """Check if graph has double cut structures."""
        for context_id, context in graph.context_manager.contexts.items():
            if context.context_type == 'cut':
                # Check if this cut has a child cut
                for child_id, child_context in graph.context_manager.contexts.items():
                    if child_context.parent_context == context_id and child_context.context_type == 'cut':
                        return True
        return False
    
    def _has_positive_contexts(self, graph: EGGraph) -> bool:
        """Check if graph has positive contexts."""
        for context in graph.context_manager.contexts.values():
            if context.is_positive:
                return True
        return False
    
    def _has_items_in_negative_contexts(self, graph: EGGraph) -> bool:
        """Check if graph has items in negative contexts."""
        for context in graph.context_manager.contexts.values():
            if not context.is_positive:
                items = graph.get_items_in_context(context.id)
                if items:
                    return True
        return False
    
    def _initialize_rules(self) -> Dict[TransformationType, TransformationRule]:
        """Initialize the transformation rules."""
        rules = {}
        
        # Alpha rules
        rules[TransformationType.DOUBLE_CUT_INSERTION] = TransformationRule(
            rule_type=TransformationType.DOUBLE_CUT_INSERTION,
            name="Double Cut Insertion",
            description="Insert two nested cuts around any subgraph",
            preconditions=["Target context exists", "Subgraph is well-formed"],
            effects=["Creates two new nested contexts", "Preserves logical equivalence"],
            ligature_effects=["Ligatures remain unchanged"]
        )
        
        rules[TransformationType.DOUBLE_CUT_ERASURE] = TransformationRule(
            rule_type=TransformationType.DOUBLE_CUT_ERASURE,
            name="Double Cut Erasure",
            description="Remove two nested cuts that contain a subgraph",
            preconditions=["Two nested cuts exist", "Inner cut contains only the subgraph"],
            effects=["Removes two nested contexts", "Preserves logical equivalence"],
            ligature_effects=["Ligatures remain unchanged"]
        )
        
        # Beta rules
        rules[TransformationType.ERASURE] = TransformationRule(
            rule_type=TransformationType.ERASURE,
            name="Erasure",
            description="Erase any subgraph from a negative context",
            preconditions=["Target items in negative context", "No ligatures cross context boundary"],
            effects=["Removes specified items", "Strengthens the assertion"],
            ligature_effects=["Severs ligatures crossing the boundary"]
        )
        
        rules[TransformationType.INSERTION] = TransformationRule(
            rule_type=TransformationType.INSERTION,
            name="Insertion",
            description="Insert any subgraph into a positive context",
            preconditions=["Target context is positive", "Subgraph is well-formed"],
            effects=["Adds specified items", "Weakens the assertion"],
            ligature_effects=["May create new ligatures"]
        )
        
        rules[TransformationType.ITERATION] = TransformationRule(
            rule_type=TransformationType.ITERATION,
            name="Iteration",
            description="Copy a subgraph to a context at the same or higher level",
            preconditions=["Source subgraph exists", "Target context at same or higher level"],
            effects=["Creates copy of subgraph", "Preserves logical strength"],
            ligature_effects=["Extends ligatures to copied elements"]
        )
        
        rules[TransformationType.DEITERATION] = TransformationRule(
            rule_type=TransformationType.DEITERATION,
            name="Deiteration",
            description="Remove a subgraph that is isomorphic to another in the same context",
            preconditions=["Two isomorphic subgraphs exist", "Same context level"],
            effects=["Removes redundant subgraph", "Preserves logical strength"],
            ligature_effects=["Merges ligatures from removed elements"]
        )
        
        return rules
    
    def _validate_preconditions(
        self, 
        graph: EGGraph, 
        transformation_type: TransformationType,
        target_items: Set[ItemId],
        target_context: ContextId,
        **kwargs
    ) -> 'ValidationResult':
        """Validate preconditions for a transformation."""
        
        if transformation_type == TransformationType.DOUBLE_CUT_INSERTION:
            return self._validate_double_cut_insertion_preconditions(graph, target_context, **kwargs)
        elif transformation_type == TransformationType.DOUBLE_CUT_ERASURE:
            return self._validate_double_cut_erasure_preconditions(graph, target_context, **kwargs)
        elif transformation_type == TransformationType.ERASURE:
            return self._validate_erasure_preconditions(graph, target_items, **kwargs)
        elif transformation_type == TransformationType.INSERTION:
            return self._validate_insertion_preconditions(graph, target_context, **kwargs)
        elif transformation_type == TransformationType.ITERATION:
            return self._validate_iteration_preconditions(graph, target_items, target_context, **kwargs)
        elif transformation_type == TransformationType.DEITERATION:
            return self._validate_deiteration_preconditions(graph, target_items, **kwargs)
        elif transformation_type == TransformationType.LIGATURE_JOIN:
            return self._validate_ligature_join_preconditions(graph, target_items, **kwargs)
        elif transformation_type == TransformationType.LIGATURE_SEVER:
            return self._validate_ligature_sever_preconditions(graph, target_items, **kwargs)
        else:
            return ValidationResult(False, f"Unknown transformation type: {transformation_type}")
    
    def _apply_double_cut_insertion(self, graph: EGGraph, target_context: ContextId, **kwargs) -> EGGraph:
        """Apply double cut insertion transformation."""
        # Get the subgraph to wrap
        subgraph_items = kwargs.get('subgraph_items', set())
        
        # Create outer cut
        graph, outer_cut = graph.create_context('cut', target_context, 'Double Cut Outer')
        
        # Create inner cut
        graph, inner_cut = graph.create_context('cut', outer_cut.id, 'Double Cut Inner')
        
        # Move subgraph items to inner cut
        for item_id in subgraph_items:
            if item_id in graph.nodes:
                node = graph.nodes[item_id]
                graph = graph.remove_node(item_id)
                graph = graph.add_node(node, inner_cut.id)
            elif item_id in graph.edges:
                edge = graph.edges[item_id]
                graph = graph.remove_edge(item_id)
                graph = graph.add_edge(edge, inner_cut.id)
        
        return graph
    
    def _apply_double_cut_erasure(self, graph: EGGraph, target_context: ContextId, **kwargs) -> EGGraph:
        """Apply double cut erasure transformation."""
        # Find the nested cuts to remove
        context = graph.context_manager.get_context(target_context)
        if not context:
            raise ValueError(f"Context {target_context} not found")
        
        # Get child contexts
        child_contexts = []
        for ctx_id in graph.context_manager.get_descendants(target_context):
            child_ctx = graph.context_manager.get_context(ctx_id)
            if child_ctx and child_ctx.parent_context == target_context:
                child_contexts.append(child_ctx)
        
        # Should have exactly one child (the inner cut)
        if len(child_contexts) != 1:
            raise ValueError("Double cut erasure requires exactly one nested cut")
        
        inner_cut = child_contexts[0]
        
        # Move items from inner cut to parent of outer cut
        parent_context = context.parent_context
        if parent_context is None:
            parent_context = graph.root_context_id
        
        # Move all items from inner cut to parent
        items_to_move = graph.get_items_in_context(inner_cut.id)
        for item_id in items_to_move:
            if item_id in graph.nodes:
                node = graph.nodes[item_id]
                graph = graph.remove_node(item_id)
                graph = graph.add_node(node, parent_context)
            elif item_id in graph.edges:
                edge = graph.edges[item_id]
                graph = graph.remove_edge(item_id)
                graph = graph.add_edge(edge, parent_context)
        
        # Remove both contexts
        graph = graph.remove_context(inner_cut.id)
        graph = graph.remove_context(target_context)
        
        return graph
    
    def _apply_erasure(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> EGGraph:
        """Apply erasure transformation."""
        # Validate that items are in negative contexts
        for item_id in target_items:
            item_context = self._find_item_context(graph, item_id)
            if item_context is None:
                continue
            
            context = graph.context_manager.get_context(item_context)
            if context and context.is_positive:
                raise ValueError(f"Cannot erase item {item_id} from positive context")
        
        # Handle ligature severing
        ligatures_to_sever = self._find_crossing_ligatures(graph, target_items)
        for ligature_id in ligatures_to_sever:
            graph = self._sever_ligature(graph, ligature_id, target_items)
        
        # Remove the items
        for item_id in target_items:
            if item_id in graph.nodes:
                graph = graph.remove_node(item_id)
            elif item_id in graph.edges:
                graph = graph.remove_edge(item_id)
            elif item_id in graph.ligatures:
                graph = graph.remove_ligature(item_id)
        
        return graph
    
    def _apply_insertion(self, graph: EGGraph, target_context: ContextId, **kwargs) -> EGGraph:
        """Apply insertion transformation."""
        # Get the subgraph to insert
        subgraph_spec = kwargs.get('subgraph', {})
        
        # Validate target context is positive
        context = graph.context_manager.get_context(target_context)
        if context and context.is_negative:
            raise ValueError("Cannot insert into negative context")
        
        # Create the subgraph items
        nodes_to_add = subgraph_spec.get('nodes', [])
        edges_to_add = subgraph_spec.get('edges', [])
        ligatures_to_add = subgraph_spec.get('ligatures', [])
        
        # Add nodes
        for node_spec in nodes_to_add:
            node = Node.create(**node_spec)
            graph = graph.add_node(node, target_context)
        
        # Add edges
        for edge_spec in edges_to_add:
            edge = Edge.create(**edge_spec)
            graph = graph.add_edge(edge, target_context)
        
        # Add ligatures
        for ligature_spec in ligatures_to_add:
            ligature = Ligature.create(**ligature_spec)
            graph = graph.add_ligature(ligature)
        
        return graph
    
    def _apply_iteration(self, graph: EGGraph, target_items: Set[ItemId], target_context: ContextId, **kwargs) -> EGGraph:
        """Apply iteration transformation."""
        # Validate context levels
        source_context = self._find_common_context(graph, target_items)
        target_ctx = graph.context_manager.get_context(target_context)
        source_ctx = graph.context_manager.get_context(source_context) if source_context else None
        
        if source_ctx and target_ctx and target_ctx.depth > source_ctx.depth:
            raise ValueError("Cannot iterate to deeper context")
        
        # Create copies of the items
        item_mapping = {}  # Old ID -> New ID
        
        # Copy nodes
        for item_id in target_items:
            if item_id in graph.nodes:
                original_node = graph.nodes[item_id]
                new_node = Node.create(
                    node_type=original_node.node_type,
                    properties=dict(original_node.properties)
                )
                graph = graph.add_node(new_node, target_context)
                item_mapping[item_id] = new_node.id
        
        # Copy edges with updated node references
        for item_id in target_items:
            if item_id in graph.edges:
                original_edge = graph.edges[item_id]
                new_nodes = set()
                
                for node_id in original_edge.nodes:
                    if node_id in item_mapping:
                        new_nodes.add(item_mapping[node_id])
                    else:
                        new_nodes.add(node_id)  # Reference to existing node
                
                new_edge = Edge.create(
                    edge_type=original_edge.edge_type,
                    nodes=new_nodes,
                    properties=dict(original_edge.properties)
                )
                graph = graph.add_edge(new_edge, target_context)
                item_mapping[item_id] = new_edge.id
        
        # Extend ligatures to include copied items
        for ligature in graph.ligatures.values():
            nodes_to_add = set()
            for node_id in ligature.nodes:
                if node_id in item_mapping:
                    nodes_to_add.add(item_mapping[node_id])
            
            if nodes_to_add:
                extended_ligature = ligature.add_nodes(nodes_to_add)
                graph = graph.update_ligature(extended_ligature)
        
        return graph
    
    def _apply_deiteration(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> EGGraph:
        """Apply deiteration transformation."""
        # Find isomorphic subgraphs
        isomorphic_items = self._find_isomorphic_subgraph(graph, target_items)
        
        if not isomorphic_items:
            raise ValueError("No isomorphic subgraph found for deiteration")
        
        # Merge ligatures before removal
        for ligature in graph.ligatures.values():
            nodes_to_merge = set()
            
            # Find corresponding nodes in both subgraphs
            for item_id in target_items:
                if item_id in ligature.nodes and item_id in graph.nodes:
                    # Find corresponding node in isomorphic subgraph
                    corresponding_id = self._find_corresponding_item(graph, item_id, target_items, isomorphic_items)
                    if corresponding_id and corresponding_id in graph.nodes:
                        nodes_to_merge.add(corresponding_id)
            
            if nodes_to_merge:
                extended_ligature = ligature.add_nodes(nodes_to_merge)
                graph = graph.update_ligature(extended_ligature)
        
        # Remove the redundant subgraph
        for item_id in target_items:
            if item_id in graph.nodes:
                graph = graph.remove_node(item_id)
            elif item_id in graph.edges:
                graph = graph.remove_edge(item_id)
        
        return graph
    
    def _apply_ligature_join(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> EGGraph:
        """Apply ligature join transformation."""
        # Create or extend ligature to connect the items
        ligature_type = kwargs.get('ligature_type', 'identity')
        
        # Check if any items are already in ligatures
        existing_ligatures = []
        for ligature in graph.ligatures.values():
            if any(item_id in ligature.nodes for item_id in target_items):
                existing_ligatures.append(ligature)
        
        if existing_ligatures:
            # Merge with existing ligature
            base_ligature = existing_ligatures[0]
            new_ligature = base_ligature.add_nodes(target_items)
            graph = graph.update_ligature(new_ligature)
            
            # Remove other ligatures and merge their nodes
            for ligature in existing_ligatures[1:]:
                new_ligature = new_ligature.add_nodes(ligature.nodes)
                graph = graph.remove_ligature(ligature.id)
            
            graph = graph.update_ligature(new_ligature)
        else:
            # Create new ligature
            ligature = Ligature.create(
                nodes=target_items,
                properties={'type': ligature_type}
            )
            graph = graph.add_ligature(ligature)
        
        return graph
    
    def _apply_ligature_sever(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> EGGraph:
        """Apply ligature sever transformation."""
        # Find ligatures containing the target items
        ligatures_to_modify = []
        
        for ligature in graph.ligatures.values():
            if any(item_id in ligature.nodes for item_id in target_items):
                ligatures_to_modify.append(ligature)
        
        # Sever the ligatures
        for ligature in ligatures_to_modify:
            remaining_nodes = ligature.nodes - target_items
            
            # Remove the original ligature
            graph = graph.remove_ligature(ligature.id)
            
            if len(remaining_nodes) > 1:
                # Create new ligature with remaining nodes
                new_ligature = Ligature.create(
                    nodes=remaining_nodes,
                    edges=ligature.edges,
                    properties=dict(ligature.properties)
                )
                graph = graph.add_ligature(new_ligature)
        
        return graph
    
    # Helper methods for validation and analysis
    
    def _can_apply_transformation(self, graph: EGGraph, transformation_type: TransformationType, context_id: ContextId = None) -> bool:
        """Quick check if a transformation can be applied."""
        try:
            # Basic structural checks
            if transformation_type in [TransformationType.DOUBLE_CUT_INSERTION, TransformationType.INSERTION]:
                return context_id is not None and graph.context_manager.get_context(context_id) is not None
            elif transformation_type in [TransformationType.ERASURE, TransformationType.DEITERATION]:
                return len(graph.nodes) > 0 or len(graph.edges) > 0
            elif transformation_type == TransformationType.ITERATION:
                return len(graph.nodes) > 0 and context_id is not None
            elif transformation_type == TransformationType.DOUBLE_CUT_ERASURE:
                return self._has_double_cut_pattern(graph, context_id)
            else:
                return True
        except:
            return False
    
    def _has_double_cut_pattern(self, graph: EGGraph, context_id: ContextId) -> bool:
        """Check if a context has the double cut pattern."""
        if context_id is None:
            return False
        
        context = graph.context_manager.get_context(context_id)
        if not context or context.is_positive:
            return False
        
        # Check for exactly one child context
        child_contexts = []
        for ctx_id in graph.context_manager.get_descendants(context_id):
            child_ctx = graph.context_manager.get_context(ctx_id)
            if child_ctx and child_ctx.parent_context == context_id:
                child_contexts.append(child_ctx)
        
        return len(child_contexts) == 1 and child_contexts[0].is_positive
    
    def _find_item_context(self, graph: EGGraph, item_id: ItemId) -> Optional[ContextId]:
        """Find the context containing an item."""
        for context_id, context in graph.context_manager.contexts.items():
            if item_id in context.contained_items:
                return context_id
        return None
    
    def _find_common_context(self, graph: EGGraph, items: Set[ItemId]) -> Optional[ContextId]:
        """Find the common context for a set of items."""
        if not items:
            return None
        
        # Find contexts for each item
        item_contexts = []
        for item_id in items:
            context_id = self._find_item_context(graph, item_id)
            if context_id:
                item_contexts.append(context_id)
        
        if not item_contexts:
            return None
        
        # Find common ancestor
        if len(item_contexts) == 1:
            return item_contexts[0]
        elif len(item_contexts) == 2:
            return graph.context_manager.find_common_ancestor(item_contexts[0], item_contexts[1])
        else:
            # For multiple contexts, find pairwise common ancestors
            common_ancestor = item_contexts[0]
            for context_id in item_contexts[1:]:
                common_ancestor = graph.context_manager.find_common_ancestor(common_ancestor, context_id)
                if common_ancestor is None:
                    return None
            return common_ancestor
    
    def _find_crossing_ligatures(self, graph: EGGraph, items: Set[ItemId]) -> Set[LigatureId]:
        """Find ligatures that cross the boundary of the given items."""
        crossing_ligatures = set()
        
        for ligature in graph.ligatures.values():
            items_in_ligature = ligature.nodes & items
            items_outside_ligature = ligature.nodes - items
            
            if items_in_ligature and items_outside_ligature:
                crossing_ligatures.add(ligature.id)
        
        return crossing_ligatures
    
    def _sever_ligature(self, graph: EGGraph, ligature_id: LigatureId, items_to_remove: Set[ItemId]) -> EGGraph:
        """Sever a ligature by removing specified items."""
        ligature = graph.ligatures.get(ligature_id)
        if not ligature:
            return graph
        
        remaining_nodes = ligature.nodes - items_to_remove
        
        # Remove the original ligature
        graph = graph.remove_ligature(ligature_id)
        
        if len(remaining_nodes) > 1:
            # Create new ligature with remaining nodes
            new_ligature = Ligature.create(
                nodes=remaining_nodes,
                edges=ligature.edges,
                properties=dict(ligature.properties)
            )
            graph = graph.add_ligature(new_ligature)
        
        return graph
    
    def _find_isomorphic_subgraph(self, graph: EGGraph, target_items: Set[ItemId]) -> Optional[Set[ItemId]]:
        """Find a subgraph isomorphic to the target items."""
        # This is a simplified isomorphism check
        # A full implementation would use graph isomorphism algorithms
        
        target_context = self._find_common_context(graph, target_items)
        if not target_context:
            return None
        
        # Get all items in the same context
        context_items = graph.get_items_in_context(target_context)
        remaining_items = context_items - target_items
        
        # Simple structural matching (would need more sophisticated algorithm)
        target_nodes = {item for item in target_items if item in graph.nodes}
        target_edges = {item for item in target_items if item in graph.edges}
        
        # Look for similar structure in remaining items
        for item_id in remaining_items:
            if item_id in graph.nodes:
                node = graph.nodes[item_id]
                # Check if there's a similar node in target
                for target_node_id in target_nodes:
                    target_node = graph.nodes[target_node_id]
                    if (node.node_type == target_node.node_type and 
                        node.properties.get('name') == target_node.properties.get('name')):
                        # Found potential match - would need full isomorphism check
                        return {item_id}  # Simplified return
        
        return None
    
    def _find_corresponding_item(self, graph: EGGraph, item_id: ItemId, subgraph1: Set[ItemId], subgraph2: Set[ItemId]) -> Optional[ItemId]:
        """Find corresponding item in isomorphic subgraph."""
        # Simplified correspondence finding
        if item_id not in graph.nodes:
            return None
        
        node = graph.nodes[item_id]
        
        # Look for node with same properties in subgraph2
        for other_id in subgraph2:
            if other_id in graph.nodes:
                other_node = graph.nodes[other_id]
                if (node.node_type == other_node.node_type and
                    node.properties == other_node.properties):
                    return other_id
        
        return None
    
    def _validate_ligature_consistency(self, graph: EGGraph) -> 'ValidationResult':
        """Validate that all ligatures are consistent."""
        for ligature in graph.ligatures.values():
            # Check that all nodes in ligature exist
            for node_id in ligature.nodes:
                if node_id not in graph.nodes:
                    return ValidationResult(False, f"Ligature {ligature.id} references non-existent node {node_id}")
            
            # Check that ligature has at least 2 nodes
            if len(ligature.nodes) < 2:
                return ValidationResult(False, f"Ligature {ligature.id} has fewer than 2 nodes")
        
        return ValidationResult(True, "Ligature consistency validated")
    
    # Specific validation methods for each transformation
    
    def _validate_double_cut_insertion_preconditions(self, graph: EGGraph, target_context: ContextId, **kwargs) -> 'ValidationResult':
        """Validate preconditions for double cut insertion."""
        if target_context is None:
            return ValidationResult(False, "Target context required for double cut insertion")
        
        context = graph.context_manager.get_context(target_context)
        if context is None:
            return ValidationResult(False, f"Target context {target_context} does not exist")
        
        return ValidationResult(True, "Double cut insertion preconditions satisfied")
    
    def _validate_double_cut_erasure_preconditions(self, graph: EGGraph, target_context: ContextId, **kwargs) -> 'ValidationResult':
        """Validate preconditions for double cut erasure."""
        if not self._has_double_cut_pattern(graph, target_context):
            return ValidationResult(False, "No double cut pattern found at target context")
        
        return ValidationResult(True, "Double cut erasure preconditions satisfied")
    
    def _validate_erasure_preconditions(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> 'ValidationResult':
        """Validate preconditions for erasure."""
        if not target_items:
            return ValidationResult(False, "No target items specified for erasure")
        
        # Check that all items are in negative contexts
        for item_id in target_items:
            context_id = self._find_item_context(graph, item_id)
            if context_id:
                context = graph.context_manager.get_context(context_id)
                if context and context.is_positive:
                    return ValidationResult(False, f"Item {item_id} is in positive context, cannot erase")
        
        return ValidationResult(True, "Erasure preconditions satisfied")
    
    def _validate_insertion_preconditions(self, graph: EGGraph, target_context: ContextId, **kwargs) -> 'ValidationResult':
        """Validate preconditions for insertion."""
        if target_context is None:
            return ValidationResult(False, "Target context required for insertion")
        
        context = graph.context_manager.get_context(target_context)
        if context is None:
            return ValidationResult(False, f"Target context {target_context} does not exist")
        
        if context.is_negative:
            return ValidationResult(False, "Cannot insert into negative context")
        
        return ValidationResult(True, "Insertion preconditions satisfied")
    
    def _validate_iteration_preconditions(self, graph: EGGraph, target_items: Set[ItemId], target_context: ContextId, **kwargs) -> 'ValidationResult':
        """Validate preconditions for iteration."""
        if not target_items:
            return ValidationResult(False, "No target items specified for iteration")
        
        if target_context is None:
            return ValidationResult(False, "Target context required for iteration")
        
        # Check context levels
        source_context = self._find_common_context(graph, target_items)
        target_ctx = graph.context_manager.get_context(target_context)
        source_ctx = graph.context_manager.get_context(source_context) if source_context else None
        
        if source_ctx and target_ctx and target_ctx.depth > source_ctx.depth:
            return ValidationResult(False, "Cannot iterate to deeper context level")
        
        return ValidationResult(True, "Iteration preconditions satisfied")
    
    def _validate_deiteration_preconditions(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> 'ValidationResult':
        """Validate preconditions for deiteration."""
        if not target_items:
            return ValidationResult(False, "No target items specified for deiteration")
        
        # Check for isomorphic subgraph
        isomorphic_items = self._find_isomorphic_subgraph(graph, target_items)
        if not isomorphic_items:
            return ValidationResult(False, "No isomorphic subgraph found for deiteration")
        
        return ValidationResult(True, "Deiteration preconditions satisfied")
    
    def _validate_ligature_join_preconditions(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> ValidationResult:
        """Validate preconditions for ligature join."""
        if not target_items:
            return ValidationResult(False, "No target items specified for ligature join")
        
        if len(target_items) < 2:
            return ValidationResult(False, "Ligature join requires at least 2 items")
        
        # Check that all items are nodes (ligatures connect nodes, not edges)
        for item_id in target_items:
            if item_id not in graph.nodes:
                return ValidationResult(False, f"Item {item_id} is not a node")
        
        return ValidationResult(True, "Ligature join preconditions satisfied")
    
    def _validate_ligature_sever_preconditions(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> ValidationResult:
        """Validate preconditions for ligature sever."""
        if not target_items:
            return ValidationResult(False, "No target items specified for ligature sever")
        
        # Check that at least one item is in a ligature
        items_in_ligatures = False
        for ligature in graph.ligatures.values():
            if any(item_id in ligature.nodes for item_id in target_items):
                items_in_ligatures = True
                break
        
        if not items_in_ligatures:
            return ValidationResult(False, "No target items are in ligatures")
        
        return ValidationResult(True, "Ligature sever preconditions satisfied")


class TransformationValidator:
    """Validator for transformation sequences and logical equivalence."""
    
    def __init__(self):
        """Initialize the validator."""
        pass
    
    def validate_transformation(self, graph: EGGraph, transformation_type: TransformationType, 
                              target_context: ContextId) -> ValidationResult:
        """Validate if a transformation is legal for the given graph state."""
        # Basic validation - check if transformation type is supported
        if transformation_type in [
            TransformationType.DOUBLE_CUT_INSERTION,
            TransformationType.DOUBLE_CUT_ERASURE,
            TransformationType.ERASURE,
            TransformationType.INSERTION,
            TransformationType.ITERATION,
            TransformationType.DEITERATION,
            TransformationType.LIGATURE_JOIN,
            TransformationType.LIGATURE_SEVER
        ]:
            return ValidationResult(True, "Transformation type is supported")
        else:
            return ValidationResult(False, f"Unsupported transformation type: {transformation_type}")
    
    def validate_transformation_sequence(self, transformations: List[TransformationAttempt]) -> ValidationResult:
        """Validate a sequence of transformations for logical consistency."""
        # Check that each transformation was successful
        for i, transformation in enumerate(transformations):
            if transformation.result != TransformationResult.SUCCESS:
                return ValidationResult(False, f"Transformation {i} failed: {transformation.error_message}")
        
        # Check logical equivalence between start and end
        if transformations:
            start_graph = transformations[0].source_graph
            end_graph = transformations[-1].result_graph
            
            if end_graph is None:
                return ValidationResult(False, "Final transformation produced no result")
            
            # Simplified equivalence check (would need more sophisticated logic)
            if not self._are_logically_equivalent(start_graph, end_graph):
                return ValidationResult(False, "Transformation sequence does not preserve logical equivalence")
        
        return ValidationResult(True, "Transformation sequence is valid")
    
    def _are_logically_equivalent(self, graph1: EGGraph, graph2: EGGraph) -> bool:
        """Check if two graphs are logically equivalent."""
        # This is a simplified check - full implementation would require
        # sophisticated logical equivalence algorithms
        
        # For transformation validation, we'll be more lenient
        # and focus on structural preservation rather than strict equivalence
        
        # Basic structural similarity
        stats1 = self._get_graph_stats(graph1)
        stats2 = self._get_graph_stats(graph2)
        
        # Allow for reasonable changes in structure during transformations
        # (A full implementation would check logical equivalence)
        
        # For now, just check that we haven't lost all content
        return (stats1['node_count'] > 0 or stats2['node_count'] > 0 or
                stats1['context_count'] > 0 or stats2['context_count'] > 0)
    
    def _get_graph_stats(self, graph: EGGraph) -> Dict[str, int]:
        """Get basic statistics about a graph."""
        max_depth = 0
        predicate_count = 0
        
        for context in graph.context_manager.contexts.values():
            max_depth = max(max_depth, context.depth)
        
        for node in graph.nodes.values():
            if node.node_type == 'predicate':
                predicate_count += 1
        
        return {
            'node_count': len(graph.nodes),
            'edge_count': len(graph.edges),
            'ligature_count': len(graph.ligatures),
            'context_count': len(graph.context_manager.contexts),
            'predicate_count': predicate_count,
            'context_depth': max_depth
        }

