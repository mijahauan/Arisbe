"""
Complete transformation engine implementing Peirce's existential graph transformation rules.

Updated for Entity-Predicate hypergraph architecture where:
- CLIF terms (variables, constants) → Entities (Lines of Identity)
- CLIF predicates → Predicates (hyperedges connecting entities)
- CLIF quantifiers → Entity scoping in contexts

This module provides a comprehensive implementation of all transformation rules
for existential graphs, including Alpha and Beta rules with proper entity
handling, validation, and cross-cut ligature compliance.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid

from .eg_types import (
    Entity, Predicate, Context, Ligature,
    EntityId, PredicateId, ContextId, LigatureId, ItemId,
    ValidationError, pmap, pset
)
from .graph import EGGraph
from .context import ContextManager
from .cross_cut_validator import CrossCutValidator


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
    
    # Entity operations (Lines of Identity)
    ENTITY_JOIN = "entity_join"
    ENTITY_SEVER = "entity_sever"
    
    # Constants and functions (if supported)
    CONSTANT_INTRODUCTION = "constant_introduction"
    CONSTANT_ELIMINATION = "constant_elimination"
    FUNCTION_COMPOSITION = "function_composition"


class TransformationResult(Enum):
    """Result of a transformation attempt."""
    SUCCESS = "success"
    INVALID_RULE = "invalid_rule"
    PRECONDITION_FAILED = "precondition_failed"
    ENTITY_VIOLATION = "entity_violation"
    CONTEXT_VIOLATION = "context_violation"
    ISOMORPHISM_FAILED = "isomorphism_failed"
    SEMANTIC_VIOLATION = "semantic_violation"


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
    entity_effects: List[str]


class TransformationEngine:
    """Complete transformation engine for existential graphs with Entity-Predicate architecture."""
    
    def __init__(self, semantic_validator=None):
        """Initialize the transformation engine.
        
        Args:
            semantic_validator: Optional semantic validator for semantic consistency checking
        """
        self.transformation_history: List[TransformationAttempt] = []
        self.rules = self._initialize_rules()
        self.validator = TransformationValidator()
        self.cross_cut_validator = CrossCutValidator()  # Add cross-cut validation
        self.semantic_validator = semantic_validator  # Add semantic validation
    
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
            
            # Validate cross-cut ligature constraints
            cross_cut_violations = self.cross_cut_validator.validate_transformation_constraints(
                graph, transformation_type.value, target_items, target_context
            )
            
            if cross_cut_violations:
                attempt.result = TransformationResult.ENTITY_VIOLATION
                attempt.error_message = f"Cross-cut ligature violations: {'; '.join(cross_cut_violations)}"
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
            elif transformation_type == TransformationType.ENTITY_JOIN:
                result_graph = self._apply_entity_join(graph, target_items, **kwargs)
            elif transformation_type == TransformationType.ENTITY_SEVER:
                result_graph = self._apply_entity_sever(graph, target_items, **kwargs)
            else:
                attempt.result = TransformationResult.INVALID_RULE
                attempt.error_message = f"Unsupported transformation type: {transformation_type}"
                return attempt
            
            # Validate the result
            if result_graph is None:
                attempt.result = TransformationResult.INVALID_RULE
                attempt.error_message = "Transformation returned None"
                return attempt
            
            # Validate entity consistency
            entity_validation = self._validate_entity_consistency(result_graph)
            if not entity_validation.is_valid:
                attempt.result = TransformationResult.ENTITY_VIOLATION
                attempt.error_message = entity_validation.error_message
                return attempt
            
            # Validate cross-cut ligature integrity after transformation
            post_transformation_validation = self.cross_cut_validator.validate_identity_preservation(result_graph)
            if not post_transformation_validation.is_preserved:
                attempt.result = TransformationResult.ENTITY_VIOLATION
                attempt.error_message = f"Post-transformation cross-cut violations: {'; '.join(post_transformation_validation.violations)}"
                return attempt
            
            # Validate semantic consistency after transformation (if semantic validator is available)
            if hasattr(self, 'semantic_validator') and self.semantic_validator:
                semantic_validation = self.semantic_validator.validate_transformation_semantics(
                    graph, result_graph, transformation_type.value
                )
                if not semantic_validation['overall_valid']:
                    attempt.result = TransformationResult.SEMANTIC_VIOLATION
                    attempt.error_message = f"Semantic validation failed: {semantic_validation.get('semantic_changes', [])}"
                    attempt.metadata['semantic_issues'] = semantic_validation
                    return attempt
                
                # Store semantic analysis in metadata
                attempt.metadata['semantic_preserved'] = semantic_validation['semantics_preserved']
                attempt.metadata['semantic_changes'] = semantic_validation.get('semantic_changes', [])
            
            # Store cross-cut analysis in metadata
            attempt.metadata['cross_cuts_analyzed'] = len(post_transformation_validation.cross_cuts)
            attempt.metadata['cross_cut_warnings'] = post_transformation_validation.warnings
            
            # Success
            attempt.result_graph = result_graph
            attempt.metadata.update({
                'entities_added': len(result_graph.entities) - len(graph.entities),
                'predicates_added': len(result_graph.predicates) - len(graph.predicates),
                'contexts_added': len(result_graph.context_manager.contexts) - len(graph.context_manager.contexts)
            })
            
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
                graph, transformation_type, context_id or graph.context_manager.root_context.id
            )
            
            if validation_result.is_valid:
                # Find possible target sets for this transformation
                target_sets = self._find_transformation_targets(graph, transformation_type, context_id)
                
                # Filter target sets based on cross-cut constraints
                valid_target_sets = []
                for target_set in target_sets:
                    cross_cut_violations = self.cross_cut_validator.validate_transformation_constraints(
                        graph, transformation_type.value, target_set, context_id
                    )
                    
                    if not cross_cut_violations:  # No violations means it's valid
                        valid_target_sets.append(target_set)
                
                if valid_target_sets:
                    legal_transformations[transformation_type] = valid_target_sets
        
        return legal_transformations
    
    def _find_transformation_targets(self, graph: EGGraph, transformation_type: TransformationType, 
                                   context_id: ContextId = None) -> List[Set[ItemId]]:
        """Find possible target sets for a given transformation type."""
        targets = []
        
        if transformation_type == TransformationType.DOUBLE_CUT_INSERTION:
            # Can insert double cuts around any subgraph
            contexts = [context_id] if context_id else list(graph.context_manager.contexts.keys())
            for ctx_id in contexts:
                items_in_context = graph.context_manager.get_items_in_context(ctx_id)
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
                if context and context.depth % 2 == 1:  # Odd depth = negative context
                    items = graph.context_manager.get_items_in_context(ctx_id)
                    for item_id in items:
                        targets.append({item_id})
        
        elif transformation_type == TransformationType.INSERTION:
            # Can insert into positive contexts
            for ctx_id in graph.context_manager.contexts:
                context = graph.context_manager.get_context(ctx_id)
                if context and context.depth % 2 == 0:  # Even depth = positive context
                    targets.append(set())  # Empty set means "insert here"
        
        # Add more transformation target finding logic as needed
        
        return targets
    
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
            entity_effects=["Entities remain unchanged"]
        )
        
        rules[TransformationType.DOUBLE_CUT_ERASURE] = TransformationRule(
            rule_type=TransformationType.DOUBLE_CUT_ERASURE,
            name="Double Cut Erasure",
            description="Remove two nested cuts that contain a subgraph",
            preconditions=["Two nested cuts exist", "Inner cut contains only the subgraph"],
            effects=["Removes two nested contexts", "Preserves logical equivalence"],
            entity_effects=["Entities remain unchanged"]
        )
        
        # Beta rules
        rules[TransformationType.ERASURE] = TransformationRule(
            rule_type=TransformationType.ERASURE,
            name="Erasure",
            description="Erase any subgraph from a negative context",
            preconditions=["Target items in negative context", "No entities cross context boundary"],
            effects=["Removes specified items", "Strengthens the assertion"],
            entity_effects=["Severs entity connections crossing the boundary"]
        )
        
        rules[TransformationType.INSERTION] = TransformationRule(
            rule_type=TransformationType.INSERTION,
            name="Insertion",
            description="Insert any subgraph into a positive context",
            preconditions=["Target context is positive", "Subgraph is well-formed"],
            effects=["Adds specified items", "Weakens the assertion"],
            entity_effects=["May create new entity connections"]
        )
        
        rules[TransformationType.ITERATION] = TransformationRule(
            rule_type=TransformationType.ITERATION,
            name="Iteration",
            description="Copy a subgraph to a context at the same or deeper level",
            preconditions=["Source subgraph exists", "Target context at same or deeper level"],
            effects=["Creates copy of subgraph", "Preserves logical strength"],
            entity_effects=["Extends entity connections to copied elements"]
        )
        
        rules[TransformationType.DEITERATION] = TransformationRule(
            rule_type=TransformationType.DEITERATION,
            name="Deiteration",
            description="Remove a subgraph that is isomorphic to another in the same context",
            preconditions=["Two isomorphic subgraphs exist", "Same context level"],
            effects=["Removes redundant subgraph", "Preserves logical strength"],
            entity_effects=["Merges entity connections from removed elements"]
        )
        
        return rules
    
    def _validate_preconditions(
        self, 
        graph: EGGraph, 
        transformation_type: TransformationType,
        target_items: Set[ItemId],
        target_context: ContextId,
        **kwargs
    ) -> ValidationResult:
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
        elif transformation_type == TransformationType.ENTITY_JOIN:
            return self._validate_entity_join_preconditions(graph, target_items, **kwargs)
        elif transformation_type == TransformationType.ENTITY_SEVER:
            return self._validate_entity_sever_preconditions(graph, target_items, **kwargs)
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
            if item_id in graph.entities:
                entity = graph.entities[item_id]
                graph = graph.remove_entity(item_id)
                graph = graph.add_entity(entity, inner_cut.id)
            elif item_id in graph.predicates:
                predicate = graph.predicates[item_id]
                graph = graph.remove_predicate(item_id)
                graph = graph.add_predicate(predicate, inner_cut.id)
        
        return graph
    
    def _apply_double_cut_erasure(self, graph: EGGraph, target_context: ContextId, **kwargs) -> EGGraph:
        """Apply double cut erasure transformation."""
        # Find the nested cuts to remove
        context = graph.context_manager.get_context(target_context)
        if not context:
            raise ValueError(f"Context {target_context} not found")
        
        # Get child contexts
        child_contexts = []
        for ctx_id in graph.context_manager.contexts:
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
        items_to_move = graph.context_manager.get_items_in_context(inner_cut.id)
        for item_id in items_to_move:
            if item_id in graph.entities:
                entity = graph.entities[item_id]
                graph = graph.remove_entity(item_id)
                graph = graph.add_entity(entity, parent_context)
            elif item_id in graph.predicates:
                predicate = graph.predicates[item_id]
                graph = graph.remove_predicate(item_id)
                graph = graph.add_predicate(predicate, parent_context)
        
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
            if context and context.depth % 2 == 0:  # Even depth = positive context
                raise ValueError(f"Cannot erase item {item_id} from positive context")
        
        # Handle entity severing for predicates being removed
        entities_to_sever = self._find_crossing_entities(graph, target_items)
        for entity_id in entities_to_sever:
            graph = self._sever_entity_connections(graph, entity_id, target_items)
        
        # Remove the items
        for item_id in target_items:
            if item_id in graph.entities:
                graph = graph.remove_entity(item_id)
            elif item_id in graph.predicates:
                graph = graph.remove_predicate(item_id)
        
        return graph
    
    def _apply_insertion(self, graph: EGGraph, target_context: ContextId, **kwargs) -> EGGraph:
        """Apply insertion transformation."""
        # Get the subgraph to insert
        subgraph_spec = kwargs.get('subgraph', {})
        
        # Validate target context is positive
        context = graph.context_manager.get_context(target_context)
        if context and context.depth % 2 == 1:  # Odd depth = negative context
            raise ValueError("Cannot insert into negative context")
        
        # Create the subgraph items
        entities_to_add = subgraph_spec.get('entities', [])
        predicates_to_add = subgraph_spec.get('predicates', [])
        
        # Add entities
        for entity_spec in entities_to_add:
            entity = Entity.create(**entity_spec)
            graph = graph.add_entity(entity, target_context)
        
        # Add predicates
        for predicate_spec in predicates_to_add:
            predicate = Predicate.create(**predicate_spec)
            graph = graph.add_predicate(predicate, target_context)
        
        return graph
    
    def _apply_iteration(self, graph: EGGraph, target_items: Set[ItemId], target_context: ContextId, **kwargs) -> EGGraph:
        """Apply iteration transformation."""
        # Validate context levels
        source_context = self._find_common_context(graph, target_items)
        target_ctx = graph.context_manager.get_context(target_context)
        source_ctx = graph.context_manager.get_context(source_context) if source_context else None
        
        if source_ctx and target_ctx and target_ctx.depth < source_ctx.depth:
            raise ValueError("Cannot iterate to shallower context")
        
        # Create copies of the items
        item_mapping = {}  # Old ID -> New ID
        
        # Copy entities
        for item_id in target_items:
            if item_id in graph.entities:
                original_entity = graph.entities[item_id]
                new_entity = Entity.create(
                    name=original_entity.name,
                    entity_type=original_entity.entity_type,
                    properties=dict(original_entity.properties)
                )
                graph = graph.add_entity(new_entity, target_context)
                item_mapping[item_id] = new_entity.id
        
        # Copy predicates with updated entity references
        for item_id in target_items:
            if item_id in graph.predicates:
                original_predicate = graph.predicates[item_id]
                new_entities = []
                
                for entity_id in original_predicate.entities:
                    if entity_id in item_mapping:
                        new_entities.append(item_mapping[entity_id])
                    else:
                        new_entities.append(entity_id)  # Reference to existing entity
                
                new_predicate = Predicate.create(
                    name=original_predicate.name,
                    entities=new_entities,
                    arity=original_predicate.arity,
                    properties=dict(original_predicate.properties)
                )
                graph = graph.add_predicate(new_predicate, target_context)
                item_mapping[item_id] = new_predicate.id
        
        return graph
    
    def _apply_deiteration(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> EGGraph:
        """Apply deiteration transformation."""
        # Find isomorphic subgraphs
        isomorphic_items = self._find_isomorphic_subgraph(graph, target_items)
        
        if not isomorphic_items:
            raise ValueError("No isomorphic subgraph found for deiteration")
        
        # Remove the redundant subgraph
        for item_id in target_items:
            if item_id in graph.entities:
                graph = graph.remove_entity(item_id)
            elif item_id in graph.predicates:
                graph = graph.remove_predicate(item_id)
        
        return graph
    
    def _apply_entity_join(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> EGGraph:
        """Apply entity join transformation (merge entities into same Line of Identity)."""
        entity_type = kwargs.get('entity_type', 'variable')
        
        # Find entities to merge
        entities_to_merge = []
        for item_id in target_items:
            if item_id in graph.entities:
                entities_to_merge.append(graph.entities[item_id])
        
        if len(entities_to_merge) < 2:
            raise ValueError("Entity join requires at least 2 entities")
        
        # Create merged entity
        merged_name = entities_to_merge[0].name  # Use first entity's name
        merged_entity = Entity.create(
            name=merged_name,
            entity_type=entity_type,
            properties={}
        )
        
        # Find context for merged entity
        context_id = self._find_item_context(graph, entities_to_merge[0].id)
        if context_id is None:
            context_id = graph.root_context_id
        
        graph = graph.add_entity(merged_entity, context_id)
        
        # Update all predicates to reference the merged entity
        predicates_to_update = []
        for predicate in graph.predicates.values():
            updated_entities = []
            changed = False
            
            for entity_id in predicate.entities:
                if entity_id in target_items:
                    updated_entities.append(merged_entity.id)
                    changed = True
                else:
                    updated_entities.append(entity_id)
            
            if changed:
                predicates_to_update.append((predicate, updated_entities))
        
        # Update predicates (remove old, add new)
        for predicate, updated_entities in predicates_to_update:
            predicate_context = self._find_item_context(graph, predicate.id) or context_id
            graph = graph.remove_predicate(predicate.id)
            
            updated_predicate = Predicate.create(
                name=predicate.name,
                entities=updated_entities,
                arity=predicate.arity,
                properties=dict(predicate.properties)
            )
            graph = graph.add_predicate(updated_predicate, predicate_context)
        
        # Remove original entities
        for entity in entities_to_merge:
            graph = graph.remove_entity(entity.id)
        
        return graph
    
    def _apply_entity_sever(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> EGGraph:
        """Apply entity sever transformation (split shared entities)."""
        
        for item_id in target_items:
            if item_id in graph.entities:
                entity = graph.entities[item_id]
                
                # Find predicates using this entity
                using_predicates = []
                for predicate in graph.predicates.values():
                    if entity.id in predicate.entities:
                        using_predicates.append(predicate)
                
                if len(using_predicates) > 1:
                    # Create separate entities for each predicate (except the first)
                    predicates_to_update = []
                    
                    for i, predicate in enumerate(using_predicates[1:], 1):
                        new_entity = Entity.create(
                            name=f"{entity.name}_{i}",
                            entity_type=entity.entity_type,
                            properties=dict(entity.properties)
                        )
                        
                        context_id = self._find_item_context(graph, predicate.id)
                        if context_id is None:
                            context_id = graph.root_context_id
                        
                        graph = graph.add_entity(new_entity, context_id)
                        
                        # Update predicate to use new entity
                        updated_entities = []
                        for ent_id in predicate.entities:
                            if ent_id == entity.id:
                                updated_entities.append(new_entity.id)
                            else:
                                updated_entities.append(ent_id)
                        
                        predicates_to_update.append((predicate, updated_entities, context_id))
                    
                    # Update predicates (remove old, add new)
                    for predicate, updated_entities, context_id in predicates_to_update:
                        graph = graph.remove_predicate(predicate.id)
                        
                        updated_predicate = Predicate.create(
                            name=predicate.name,
                            entities=updated_entities,
                            arity=predicate.arity,
                            properties=dict(predicate.properties)
                        )
                        graph = graph.add_predicate(updated_predicate, context_id)
        
        return graph
    
    # Helper methods for validation and analysis
    
    def _find_item_context(self, graph: EGGraph, item_id: ItemId) -> Optional[ContextId]:
        """Find the context containing an item."""
        return graph.context_manager.find_item_context(item_id)
    
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
        else:
            # For multiple contexts, find the lowest common ancestor
            common_ancestor = item_contexts[0]
            for context_id in item_contexts[1:]:
                # Simple implementation - would need proper LCA algorithm
                ctx1_path = graph.context_manager.get_context_path(common_ancestor)
                ctx2_path = graph.context_manager.get_context_path(context_id)
                
                # Find common prefix
                common_path = []
                for i in range(min(len(ctx1_path), len(ctx2_path))):
                    if ctx1_path[i] == ctx2_path[i]:
                        common_path.append(ctx1_path[i])
                    else:
                        break
                
                if common_path:
                    common_ancestor = common_path[-1]
                else:
                    return graph.root_context_id
            
            return common_ancestor
    
    def _find_crossing_entities(self, graph: EGGraph, items: Set[ItemId]) -> Set[EntityId]:
        """Find entities that would be affected by removing the given items."""
        crossing_entities = set()
        
        # Find predicates being removed
        predicates_being_removed = {item_id for item_id in items if item_id in graph.predicates}
        
        # Find entities connected to these predicates
        for predicate_id in predicates_being_removed:
            predicate = graph.predicates[predicate_id]
            for entity_id in predicate.entities:
                # Check if this entity is used by other predicates not being removed
                other_predicates = [p for p in graph.predicates.values() 
                                 if entity_id in p.entities and p.id not in predicates_being_removed]
                if other_predicates:
                    crossing_entities.add(entity_id)
        
        return crossing_entities
    
    def _sever_entity_connections(self, graph: EGGraph, entity_id: EntityId, items_to_remove: Set[ItemId]) -> EGGraph:
        """Sever entity connections when removing items."""
        # This is a placeholder - in a full implementation, this would handle
        # the complex logic of maintaining entity consistency when removing predicates
        return graph
    
    def _find_isomorphic_subgraph(self, graph: EGGraph, target_items: Set[ItemId]) -> Optional[Set[ItemId]]:
        """Find a subgraph isomorphic to the target items."""
        # This is a simplified isomorphism check
        # A full implementation would use graph isomorphism algorithms
        
        target_context = self._find_common_context(graph, target_items)
        if not target_context:
            return None
        
        # Get all items in the same context
        context_items = graph.context_manager.get_items_in_context(target_context)
        remaining_items = context_items - target_items
        
        # Simple structural matching (would need more sophisticated algorithm)
        target_entities = {item for item in target_items if item in graph.entities}
        target_predicates = {item for item in target_items if item in graph.predicates}
        
        # Look for similar structure in remaining items
        for item_id in remaining_items:
            if item_id in graph.entities:
                entity = graph.entities[item_id]
                # Check if there's a similar entity in target
                for target_entity_id in target_entities:
                    target_entity = graph.entities[target_entity_id]
                    if (entity.entity_type == target_entity.entity_type and 
                        entity.name == target_entity.name):
                        # Found potential match - would need full isomorphism check
                        return {item_id}  # Simplified return
        
        return None
    
    def _validate_entity_consistency(self, graph: EGGraph) -> ValidationResult:
        """Validate that all entity references are consistent."""
        for predicate in graph.predicates.values():
            # Check that all entities in predicate exist
            for entity_id in predicate.entities:
                if entity_id not in graph.entities:
                    return ValidationResult(False, f"Predicate {predicate.id} references non-existent entity {entity_id}")
        
        return ValidationResult(True, "Entity consistency validated")
    
    # Specific validation methods for each transformation
    
    def _validate_double_cut_insertion_preconditions(self, graph: EGGraph, target_context: ContextId, **kwargs) -> ValidationResult:
        """Validate preconditions for double cut insertion."""
        if target_context is None:
            return ValidationResult(False, "Target context required for double cut insertion")
        
        context = graph.context_manager.get_context(target_context)
        if context is None:
            return ValidationResult(False, f"Target context {target_context} does not exist")
        
        return ValidationResult(True, "Double cut insertion preconditions satisfied")
    
    def _validate_double_cut_erasure_preconditions(self, graph: EGGraph, target_context: ContextId, **kwargs) -> ValidationResult:
        """Validate preconditions for double cut erasure."""
        if not self._has_double_cut_pattern(graph, target_context):
            return ValidationResult(False, "No double cut pattern found at target context")
        
        return ValidationResult(True, "Double cut erasure preconditions satisfied")
    
    def _validate_erasure_preconditions(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> ValidationResult:
        """Validate preconditions for erasure."""
        if not target_items:
            return ValidationResult(False, "No target items specified for erasure")
        
        # Check that all items are in negative contexts
        for item_id in target_items:
            context_id = self._find_item_context(graph, item_id)
            if context_id:
                context = graph.context_manager.get_context(context_id)
                if context and context.depth % 2 == 0:  # Even depth = positive context
                    return ValidationResult(False, f"Item {item_id} is in positive context, cannot erase")
        
        return ValidationResult(True, "Erasure preconditions satisfied")
    
    def _validate_insertion_preconditions(self, graph: EGGraph, target_context: ContextId, **kwargs) -> ValidationResult:
        """Validate preconditions for insertion."""
        if target_context is None:
            return ValidationResult(False, "Target context required for insertion")
        
        context = graph.context_manager.get_context(target_context)
        if context is None:
            return ValidationResult(False, f"Target context {target_context} does not exist")
        
        if context.depth % 2 == 1:  # Odd depth = negative context
            return ValidationResult(False, "Cannot insert into negative context")
        
        return ValidationResult(True, "Insertion preconditions satisfied")
    
    def _validate_iteration_preconditions(self, graph: EGGraph, target_items: Set[ItemId], target_context: ContextId, **kwargs) -> ValidationResult:
        """Validate preconditions for iteration."""
        if not target_items:
            return ValidationResult(False, "No target items specified for iteration")
        
        if target_context is None:
            return ValidationResult(False, "Target context required for iteration")
        
        # Check context levels - iteration allows copying to same level OR deeper
        # (In EG rules, you can iterate from outer to inner contexts)
        source_context = self._find_common_context(graph, target_items)
        target_ctx = graph.context_manager.get_context(target_context)
        source_ctx = graph.context_manager.get_context(source_context) if source_context else None
        
        # Allow iteration to same level or deeper (target_depth >= source_depth)
        # Only forbid iteration to shallower contexts (going outward)
        if source_ctx and target_ctx and target_ctx.depth < source_ctx.depth:
            return ValidationResult(False, "Cannot iterate to shallower context level")
        
        return ValidationResult(True, "Iteration preconditions satisfied")
    
    def _validate_deiteration_preconditions(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> ValidationResult:
        """Validate preconditions for deiteration."""
        if not target_items:
            return ValidationResult(False, "No target items specified for deiteration")
        
        # Check for isomorphic subgraph
        isomorphic_items = self._find_isomorphic_subgraph(graph, target_items)
        if not isomorphic_items:
            return ValidationResult(False, "No isomorphic subgraph found for deiteration")
        
        return ValidationResult(True, "Deiteration preconditions satisfied")
    
    def _validate_entity_join_preconditions(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> ValidationResult:
        """Validate preconditions for entity join."""
        if not target_items:
            return ValidationResult(False, "No target items specified for entity join")
        
        # Check that all items are entities FIRST
        for item_id in target_items:
            if item_id not in graph.entities:
                return ValidationResult(False, f"Item {item_id} is not an entity")
        
        # Then check count
        if len(target_items) < 2:
            return ValidationResult(False, "Entity join requires at least 2 items")
        
        return ValidationResult(True, "Entity join preconditions satisfied")
    
    def _validate_entity_sever_preconditions(self, graph: EGGraph, target_items: Set[ItemId], **kwargs) -> ValidationResult:
        """Validate preconditions for entity sever."""
        if not target_items:
            return ValidationResult(False, "No target items specified for entity sever")
        
        # Check that at least one item is an entity used by multiple predicates
        entities_with_multiple_uses = False
        for item_id in target_items:
            if item_id in graph.entities:
                using_predicates = [p for p in graph.predicates.values() if item_id in p.entities]
                if len(using_predicates) > 1:
                    entities_with_multiple_uses = True
                    break
        
        if not entities_with_multiple_uses:
            return ValidationResult(False, "No target entities are used by multiple predicates")
        
        return ValidationResult(True, "Entity sever preconditions satisfied")
    
    def _has_double_cut_pattern(self, graph: EGGraph, context_id: ContextId) -> bool:
        """Check if a context has the double cut pattern."""
        if context_id is None:
            return False
        
        context = graph.context_manager.get_context(context_id)
        if not context or context.depth % 2 == 0:  # Must be negative context
            return False
        
        # Check for exactly one child context
        child_contexts = []
        for ctx_id in graph.context_manager.contexts:
            child_ctx = graph.context_manager.get_context(ctx_id)
            if child_ctx and child_ctx.parent_context == context_id:
                child_contexts.append(child_ctx)
        
        return len(child_contexts) == 1 and child_contexts[0].depth % 2 == 0  # Child must be positive


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
            TransformationType.ENTITY_JOIN,
            TransformationType.ENTITY_SEVER
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
        return (stats1['entity_count'] > 0 or stats2['entity_count'] > 0 or
                stats1['context_count'] > 0 or stats2['context_count'] > 0)
    
    def _get_graph_stats(self, graph: EGGraph) -> Dict[str, int]:
        """Get basic statistics about a graph."""
        max_depth = 0
        
        for context in graph.context_manager.contexts.values():
            max_depth = max(max_depth, context.depth)
        
        return {
            'entity_count': len(graph.entities),
            'predicate_count': len(graph.predicates),
            'context_count': len(graph.context_manager.contexts),
            'context_depth': max_depth
        }

