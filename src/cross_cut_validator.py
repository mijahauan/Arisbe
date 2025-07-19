"""
Cross-cut ligature validation system for Dau compliance.

This module implements comprehensive validation for cross-cut ligatures to ensure
identity preservation across context boundaries, maintaining semantic consistency
and Dau compliance for all graph transformations.

Key Features:
- Cross-cut detection and analysis
- Identity preservation validation
- Ligature integrity enforcement
- Semantic consistency checking
- Transformation constraint validation
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Iterator
from dataclasses import dataclass
from collections import defaultdict, deque
from enum import Enum
import uuid

from eg_types import (
    Entity, Predicate, Context, Ligature,
    EntityId, PredicateId, ContextId, LigatureId, ItemId,
    ValidationError, pmap, pset
)
from graph import EGGraph
from ligature import LigatureManager


class CrossCutType(Enum):
    """Types of cross-cut scenarios."""
    SIMPLE_CROSS = "simple_cross"  # Entity crosses one context boundary
    MULTI_CROSS = "multi_cross"    # Entity crosses multiple context boundaries
    NESTED_CROSS = "nested_cross"  # Entity crosses nested context boundaries
    LIGATURE_CROSS = "ligature_cross"  # Ligature spans multiple contexts


@dataclass
class CrossCutInfo:
    """Information about a cross-cut entity or ligature."""
    entity_id: EntityId
    contexts: Set[ContextId]
    cross_cut_type: CrossCutType
    depth_span: int  # Number of context levels spanned
    ligature_id: Optional[LigatureId] = None
    predicates_involved: Set[PredicateId] = None
    
    def __post_init__(self):
        if self.predicates_involved is None:
            self.predicates_involved = set()


@dataclass
class IdentityPreservationResult:
    """Result of identity preservation validation."""
    is_preserved: bool
    violations: List[str]
    warnings: List[str]
    cross_cuts: List[CrossCutInfo]


class CrossCutValidator:
    """Comprehensive cross-cut ligature validation system."""
    
    def __init__(self):
        """Initialize the cross-cut validator."""
        self.ligature_manager = LigatureManager()
    
    def analyze_cross_cuts(self, graph: EGGraph) -> List[CrossCutInfo]:
        """Analyze all cross-cut scenarios in the graph.
        
        Args:
            graph: The existential graph to analyze.
            
        Returns:
            List of CrossCutInfo objects describing all cross-cuts.
        """
        cross_cuts = []
        
        # Build entity-to-contexts mapping
        entity_contexts = self._build_entity_context_mapping(graph)
        
        # Analyze each entity for cross-cuts
        for entity_id, contexts in entity_contexts.items():
            if len(contexts) > 1:
                cross_cut_info = self._analyze_entity_cross_cut(
                    entity_id, contexts, graph
                )
                cross_cuts.append(cross_cut_info)
        
        # Analyze ligatures for cross-cuts
        ligature_cross_cuts = self._analyze_ligature_cross_cuts(graph, entity_contexts)
        cross_cuts.extend(ligature_cross_cuts)
        
        return cross_cuts
    
    def validate_identity_preservation(self, graph: EGGraph) -> IdentityPreservationResult:
        """Validate that identity is preserved across all cross-cuts.
        
        Args:
            graph: The existential graph to validate.
            
        Returns:
            IdentityPreservationResult with validation details.
        """
        violations = []
        warnings = []
        
        # Analyze cross-cuts
        cross_cuts = self.analyze_cross_cuts(graph)
        
        # Validate each cross-cut
        for cross_cut in cross_cuts:
            validation_result = self._validate_cross_cut_identity(cross_cut, graph)
            violations.extend(validation_result.get('violations', []))
            warnings.extend(validation_result.get('warnings', []))
        
        # Check ligature consistency across contexts
        ligature_violations = self._validate_ligature_consistency_across_contexts(graph)
        violations.extend(ligature_violations)
        
        # Check semantic consistency
        semantic_violations = self._validate_semantic_consistency(graph, cross_cuts)
        violations.extend(semantic_violations)
        
        return IdentityPreservationResult(
            is_preserved=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            cross_cuts=cross_cuts
        )
    
    def validate_transformation_constraints(self, graph: EGGraph, 
                                          transformation_type: str,
                                          target_items: Set[ItemId],
                                          target_context: ContextId) -> List[str]:
        """Validate cross-cut constraints for a proposed transformation.
        
        Args:
            graph: The current graph state.
            transformation_type: Type of transformation being attempted.
            target_items: Items involved in the transformation.
            target_context: Context where transformation is being applied.
            
        Returns:
            List of constraint violations. Empty list means valid.
        """
        violations = []
        
        # Get cross-cuts that would be affected
        affected_cross_cuts = self._get_affected_cross_cuts(
            graph, target_items, target_context
        )
        
        # Validate based on transformation type
        if transformation_type == "erasure":
            violations.extend(self._validate_erasure_constraints(
                graph, affected_cross_cuts, target_context
            ))
        elif transformation_type == "insertion":
            violations.extend(self._validate_insertion_constraints(
                graph, affected_cross_cuts, target_context
            ))
        elif transformation_type == "iteration":
            violations.extend(self._validate_iteration_constraints(
                graph, affected_cross_cuts, target_context
            ))
        elif transformation_type == "deiteration":
            violations.extend(self._validate_deiteration_constraints(
                graph, affected_cross_cuts, target_context
            ))
        
        return violations
    
    def _build_entity_context_mapping(self, graph: EGGraph) -> Dict[EntityId, Set[ContextId]]:
        """Build mapping from entities to the contexts they appear in.
        
        Args:
            graph: The existential graph to analyze.
            
        Returns:
            Dictionary mapping entity IDs to sets of context IDs.
        """
        entity_contexts = defaultdict(set)
        
        # Check each context for its entities
        for context_id, context in graph.contexts.items():
            # Get entities directly in this context
            context_entities = self._get_entities_in_context(graph, context_id)
            for entity_id in context_entities:
                entity_contexts[entity_id].add(context_id)
        
        return dict(entity_contexts)
    
    def _get_entities_in_context(self, graph: EGGraph, context_id: ContextId) -> Set[EntityId]:
        """Get all entities that appear in a specific context.
        
        Args:
            graph: The existential graph.
            context_id: The context to analyze.
            
        Returns:
            Set of entity IDs in the context.
        """
        entities = set()
        
        # Get items in this context
        items = graph.get_items_in_context(context_id)
        
        # Add direct entities
        for item_id in items:
            if item_id in graph.entities:
                entities.add(item_id)
        
        # Add entities from predicates in this context
        for item_id in items:
            if item_id in graph.predicates:
                predicate = graph.predicates[item_id]
                entities.update(predicate.entities)
        
        # Add entities from ligatures in this context
        for item_id in items:
            if item_id in graph.ligatures:
                ligature = graph.ligatures[item_id]
                entities.update(ligature.entities)
        
        return entities
    
    def _analyze_entity_cross_cut(self, entity_id: EntityId, 
                                contexts: Set[ContextId], 
                                graph: EGGraph) -> CrossCutInfo:
        """Analyze a specific entity's cross-cut scenario.
        
        Args:
            entity_id: The entity to analyze.
            contexts: Set of contexts the entity appears in.
            graph: The existential graph.
            
        Returns:
            CrossCutInfo describing the cross-cut scenario.
        """
        # Determine cross-cut type
        cross_cut_type = self._determine_cross_cut_type(contexts, graph)
        
        # Calculate depth span
        depth_span = self._calculate_depth_span(contexts, graph)
        
        # Find predicates involving this entity
        predicates_involved = set()
        for predicate_id, predicate in graph.predicates.items():
            if entity_id in predicate.entities:
                predicates_involved.add(predicate_id)
        
        # Check if entity is part of a ligature
        ligature_id = self._find_entity_ligature(entity_id, graph)
        
        return CrossCutInfo(
            entity_id=entity_id,
            contexts=contexts,
            cross_cut_type=cross_cut_type,
            depth_span=depth_span,
            ligature_id=ligature_id,
            predicates_involved=predicates_involved
        )
    
    def _analyze_ligature_cross_cuts(self, graph: EGGraph, 
                                   entity_contexts: Dict[EntityId, Set[ContextId]]) -> List[CrossCutInfo]:
        """Analyze ligatures that span multiple contexts.
        
        Args:
            graph: The existential graph.
            entity_contexts: Mapping of entities to their contexts.
            
        Returns:
            List of CrossCutInfo for ligatures that cross contexts.
        """
        ligature_cross_cuts = []
        
        for ligature_id, ligature in graph.ligatures.items():
            # Get all contexts this ligature spans
            ligature_contexts = set()
            for entity_id in ligature.entities:
                if entity_id in entity_contexts:
                    ligature_contexts.update(entity_contexts[entity_id])
            
            # If ligature spans multiple contexts, it's a cross-cut
            if len(ligature_contexts) > 1:
                # Create cross-cut info for the ligature
                # Use the first entity as representative
                representative_entity = next(iter(ligature.entities))
                
                cross_cut_info = CrossCutInfo(
                    entity_id=representative_entity,
                    contexts=ligature_contexts,
                    cross_cut_type=CrossCutType.LIGATURE_CROSS,
                    depth_span=self._calculate_depth_span(ligature_contexts, graph),
                    ligature_id=ligature_id,
                    predicates_involved=self._get_predicates_for_ligature(ligature, graph)
                )
                
                ligature_cross_cuts.append(cross_cut_info)
        
        return ligature_cross_cuts
    
    def _determine_cross_cut_type(self, contexts: Set[ContextId], graph: EGGraph) -> CrossCutType:
        """Determine the type of cross-cut based on context relationships.
        
        Args:
            contexts: Set of contexts involved in the cross-cut.
            graph: The existential graph.
            
        Returns:
            CrossCutType enum value.
        """
        if len(contexts) == 2:
            # Check if contexts are nested
            context_list = list(contexts)
            context1 = graph.contexts[context_list[0]]
            context2 = graph.contexts[context_list[1]]
            
            if (context1.parent_context == context_list[1] or 
                context2.parent_context == context_list[0]):
                return CrossCutType.NESTED_CROSS
            else:
                return CrossCutType.SIMPLE_CROSS
        else:
            return CrossCutType.MULTI_CROSS
    
    def _calculate_depth_span(self, contexts: Set[ContextId], graph: EGGraph) -> int:
        """Calculate the depth span of contexts involved in cross-cut.
        
        Args:
            contexts: Set of contexts involved.
            graph: The existential graph.
            
        Returns:
            Number of context levels spanned.
        """
        depths = []
        for context_id in contexts:
            context = graph.contexts[context_id]
            depths.append(context.depth)
        
        return max(depths) - min(depths) if depths else 0
    
    def _find_entity_ligature(self, entity_id: EntityId, graph: EGGraph) -> Optional[LigatureId]:
        """Find the ligature containing a specific entity.
        
        Args:
            entity_id: The entity to search for.
            graph: The existential graph.
            
        Returns:
            LigatureId if found, None otherwise.
        """
        for ligature_id, ligature in graph.ligatures.items():
            if entity_id in ligature.entities:
                return ligature_id
        return None
    
    def _get_predicates_for_ligature(self, ligature: Ligature, graph: EGGraph) -> Set[PredicateId]:
        """Get all predicates that involve entities in a ligature.
        
        Args:
            ligature: The ligature to analyze.
            graph: The existential graph.
            
        Returns:
            Set of predicate IDs involving ligature entities.
        """
        predicates = set()
        for predicate_id, predicate in graph.predicates.items():
            if any(entity_id in ligature.entities for entity_id in predicate.entities):
                predicates.add(predicate_id)
        return predicates
    
    def _validate_cross_cut_identity(self, cross_cut: CrossCutInfo, graph: EGGraph) -> Dict[str, List[str]]:
        """Validate identity preservation for a specific cross-cut.
        
        Args:
            cross_cut: The cross-cut to validate.
            graph: The existential graph.
            
        Returns:
            Dictionary with 'violations' and 'warnings' lists.
        """
        violations = []
        warnings = []
        
        entity = graph.entities.get(cross_cut.entity_id)
        if not entity:
            violations.append(f"Cross-cut entity {cross_cut.entity_id} not found in graph")
            return {'violations': violations, 'warnings': warnings}
        
        # Validate entity type consistency across contexts
        if entity.entity_type == 'variable':
            # Variables should maintain consistent scoping
            scoping_violations = self._validate_variable_scoping(cross_cut, graph)
            violations.extend(scoping_violations)
        elif entity.entity_type == 'constant':
            # Constants should maintain consistent interpretation
            interpretation_violations = self._validate_constant_interpretation(cross_cut, graph)
            violations.extend(interpretation_violations)
        
        # Validate ligature consistency if entity is in a ligature
        if cross_cut.ligature_id:
            ligature_violations = self._validate_ligature_cross_cut_consistency(cross_cut, graph)
            violations.extend(ligature_violations)
        
        # Check for semantic consistency across contexts
        semantic_issues = self._check_cross_cut_semantic_consistency(cross_cut, graph)
        violations.extend(semantic_issues.get('violations', []))
        warnings.extend(semantic_issues.get('warnings', []))
        
        return {'violations': violations, 'warnings': warnings}
    
    def _validate_variable_scoping(self, cross_cut: CrossCutInfo, graph: EGGraph) -> List[str]:
        """Validate proper variable scoping across contexts.
        
        Args:
            cross_cut: The cross-cut involving a variable.
            graph: The existential graph.
            
        Returns:
            List of scoping violations.
        """
        violations = []
        
        # Variables crossing context boundaries must follow proper scoping rules
        # In existential graphs, variables can cross from inner to outer contexts
        # but not from outer to inner without proper quantification
        
        contexts = list(cross_cut.contexts)
        for i, context_id in enumerate(contexts):
            context = graph.contexts[context_id]
            for j, other_context_id in enumerate(contexts[i+1:], i+1):
                other_context = graph.contexts[other_context_id]
                
                # Check if one context is parent of the other
                if context.parent_context == other_context_id:
                    # Variable crossing from inner to outer - generally allowed
                    continue
                elif other_context.parent_context == context_id:
                    # Variable crossing from outer to inner - needs validation
                    if not self._is_properly_quantified(cross_cut.entity_id, other_context_id, graph):
                        violations.append(
                            f"Variable {cross_cut.entity_id} crosses from outer context "
                            f"{context_id} to inner context {other_context_id} without proper quantification"
                        )
                else:
                    # Variables in sibling contexts - potential issue
                    violations.append(
                        f"Variable {cross_cut.entity_id} appears in sibling contexts "
                        f"{context_id} and {other_context_id} - may violate scoping rules"
                    )
        
        return violations
    
    def _validate_constant_interpretation(self, cross_cut: CrossCutInfo, graph: EGGraph) -> List[str]:
        """Validate consistent interpretation of constants across contexts.
        
        Args:
            cross_cut: The cross-cut involving a constant.
            graph: The existential graph.
            
        Returns:
            List of interpretation violations.
        """
        violations = []
        
        # Constants should maintain the same interpretation across all contexts
        entity = graph.entities[cross_cut.entity_id]
        
        # Check that the constant name is consistent
        # (This is automatically ensured by having a single Entity object)
        
        # Check for conflicting uses of the constant
        conflicting_uses = self._detect_conflicting_constant_uses(cross_cut, graph)
        violations.extend(conflicting_uses)
        
        return violations
    
    def _validate_ligature_cross_cut_consistency(self, cross_cut: CrossCutInfo, graph: EGGraph) -> List[str]:
        """Validate consistency of ligatures that cross context boundaries.
        
        Args:
            cross_cut: The cross-cut involving a ligature.
            graph: The existential graph.
            
        Returns:
            List of ligature consistency violations.
        """
        violations = []
        
        if not cross_cut.ligature_id:
            return violations
        
        ligature = graph.ligatures.get(cross_cut.ligature_id)
        if not ligature:
            violations.append(f"Ligature {cross_cut.ligature_id} not found in graph")
            return violations
        
        # All entities in the ligature should represent the same object
        # across all contexts
        entity_contexts = {}
        for entity_id in ligature.entities:
            entity_contexts[entity_id] = self._get_entity_contexts(entity_id, graph)
        
        # Check for consistency in ligature entity usage
        for entity_id, contexts in entity_contexts.items():
            if len(contexts) > 1:
                # This entity also crosses contexts - validate consistency
                consistency_issues = self._validate_ligature_entity_consistency(
                    entity_id, contexts, ligature, graph
                )
                violations.extend(consistency_issues)
        
        return violations
    
    def _check_cross_cut_semantic_consistency(self, cross_cut: CrossCutInfo, graph: EGGraph) -> Dict[str, List[str]]:
        """Check semantic consistency of cross-cut entities.
        
        Args:
            cross_cut: The cross-cut to check.
            graph: The existential graph.
            
        Returns:
            Dictionary with 'violations' and 'warnings' lists.
        """
        violations = []
        warnings = []
        
        # Check that the entity's usage is semantically consistent
        # across all contexts it appears in
        
        entity_usages = self._analyze_entity_usage_across_contexts(cross_cut, graph)
        
        # Look for semantic inconsistencies
        for context_id, usage_info in entity_usages.items():
            for other_context_id, other_usage_info in entity_usages.items():
                if context_id != other_context_id:
                    inconsistencies = self._compare_entity_usage(
                        usage_info, other_usage_info, context_id, other_context_id
                    )
                    violations.extend(inconsistencies.get('violations', []))
                    warnings.extend(inconsistencies.get('warnings', []))
        
        return {'violations': violations, 'warnings': warnings}
    
    def _validate_ligature_consistency_across_contexts(self, graph: EGGraph) -> List[str]:
        """Validate that all ligatures maintain consistency across contexts.
        
        Args:
            graph: The existential graph to validate.
            
        Returns:
            List of ligature consistency violations.
        """
        violations = []
        
        for ligature_id, ligature in graph.ligatures.items():
            # Use existing ligature boundary detection
            entity_contexts = self._build_entity_context_mapping(graph)
            boundary_entities = self.ligature_manager.find_ligature_boundaries(
                ligature, entity_contexts
            )
            
            if boundary_entities:
                # This ligature crosses context boundaries
                consistency_violations = self._validate_boundary_ligature_consistency(
                    ligature, boundary_entities, graph
                )
                violations.extend(consistency_violations)
        
        return violations
    
    def _validate_semantic_consistency(self, graph: EGGraph, cross_cuts: List[CrossCutInfo]) -> List[str]:
        """Validate overall semantic consistency of the graph with cross-cuts.
        
        Args:
            graph: The existential graph.
            cross_cuts: List of all cross-cuts in the graph.
            
        Returns:
            List of semantic consistency violations.
        """
        violations = []
        
        # Check for global semantic consistency issues
        for cross_cut in cross_cuts:
            # Ensure cross-cut doesn't create logical contradictions
            contradiction_check = self._check_for_logical_contradictions(cross_cut, graph)
            violations.extend(contradiction_check)
            
            # Ensure cross-cut preserves intended meaning
            meaning_preservation_check = self._check_meaning_preservation(cross_cut, graph)
            violations.extend(meaning_preservation_check)
        
        return violations
    
    # Helper methods for transformation constraint validation
    
    def _get_affected_cross_cuts(self, graph: EGGraph, target_items: Set[ItemId], 
                               target_context: ContextId) -> List[CrossCutInfo]:
        """Get cross-cuts that would be affected by a transformation.
        
        Args:
            graph: The current graph state.
            target_items: Items involved in the transformation.
            target_context: Context where transformation is being applied.
            
        Returns:
            List of affected CrossCutInfo objects.
        """
        affected_cross_cuts = []
        all_cross_cuts = self.analyze_cross_cuts(graph)
        
        for cross_cut in all_cross_cuts:
            # Check if this cross-cut involves the target context
            if target_context in cross_cut.contexts:
                # Check if any target items are related to this cross-cut
                if (cross_cut.entity_id in target_items or
                    any(pred_id in target_items for pred_id in cross_cut.predicates_involved) or
                    (cross_cut.ligature_id and cross_cut.ligature_id in target_items)):
                    affected_cross_cuts.append(cross_cut)
        
        return affected_cross_cuts
    
    def _validate_erasure_constraints(self, graph: EGGraph, affected_cross_cuts: List[CrossCutInfo], 
                                    target_context: ContextId) -> List[str]:
        """Validate constraints for erasure transformations.
        
        Args:
            graph: The current graph state.
            affected_cross_cuts: Cross-cuts affected by the erasure.
            target_context: Context where erasure is being applied.
            
        Returns:
            List of constraint violations.
        """
        violations = []
        
        for cross_cut in affected_cross_cuts:
            # Erasure from negative context should not break cross-cut identity
            context = graph.contexts[target_context]
            if context.context_type == 'cut':  # Negative context
                # Check if erasure would sever the cross-cut improperly
                if len(cross_cut.contexts) == 2 and target_context in cross_cut.contexts:
                    violations.append(
                        f"Erasure from negative context {target_context} would improperly "
                        f"sever cross-cut entity {cross_cut.entity_id}"
                    )
        
        return violations
    
    def _validate_insertion_constraints(self, graph: EGGraph, affected_cross_cuts: List[CrossCutInfo], 
                                      target_context: ContextId) -> List[str]:
        """Validate constraints for insertion transformations.
        
        Args:
            graph: The current graph state.
            affected_cross_cuts: Cross-cuts affected by the insertion.
            target_context: Context where insertion is being applied.
            
        Returns:
            List of constraint violations.
        """
        violations = []
        
        # Insertion into positive context is generally safe for cross-cuts
        # but we should check for potential semantic issues
        
        for cross_cut in affected_cross_cuts:
            # Check if insertion would create improper variable scoping
            if cross_cut.entity_id in graph.entities:
                entity = graph.entities[cross_cut.entity_id]
                if entity.entity_type == 'variable':
                    scoping_issues = self._check_insertion_variable_scoping(
                        cross_cut, target_context, graph
                    )
                    violations.extend(scoping_issues)
        
        return violations
    
    def _validate_iteration_constraints(self, graph: EGGraph, affected_cross_cuts: List[CrossCutInfo], 
                                      target_context: ContextId) -> List[str]:
        """Validate constraints for iteration transformations.
        
        Args:
            graph: The current graph state.
            affected_cross_cuts: Cross-cuts affected by the iteration.
            target_context: Context where iteration is being applied.
            
        Returns:
            List of constraint violations.
        """
        violations = []
        
        # Iteration should preserve cross-cut identity
        for cross_cut in affected_cross_cuts:
            # Check if iteration would create multiple instances of the same entity
            # across contexts in a way that violates identity
            identity_violations = self._check_iteration_identity_preservation(
                cross_cut, target_context, graph
            )
            violations.extend(identity_violations)
        
        return violations
    
    def _validate_deiteration_constraints(self, graph: EGGraph, affected_cross_cuts: List[CrossCutInfo], 
                                        target_context: ContextId) -> List[str]:
        """Validate constraints for deiteration transformations.
        
        Args:
            graph: The current graph state.
            affected_cross_cuts: Cross-cuts affected by the deiteration.
            target_context: Context where deiteration is being applied.
            
        Returns:
            List of constraint violations.
        """
        violations = []
        
        # Deiteration should not break necessary cross-cut connections
        for cross_cut in affected_cross_cuts:
            # Check if deiteration would remove a necessary cross-cut connection
            necessity_violations = self._check_deiteration_necessity(
                cross_cut, target_context, graph
            )
            violations.extend(necessity_violations)
        
        return violations
    
    # Additional helper methods (stubs for now - can be implemented as needed)
    
    def _is_properly_quantified(self, entity_id: EntityId, context_id: ContextId, graph: EGGraph) -> bool:
        """Check if a variable is properly quantified in a context.
        
        Args:
            entity_id: The variable entity to check.
            context_id: The context to check quantification in.
            graph: The existential graph.
            
        Returns:
            True if properly quantified, False otherwise.
        """
        context = graph.contexts[context_id]
        
        # Check if this context or any parent context has quantification for this variable
        current_context_id = context_id
        while current_context_id is not None:
            current_context = graph.contexts[current_context_id]
            
            # Check context properties for quantification information
            quantified_vars = current_context.properties.get('quantified_variables', set())
            if entity_id in quantified_vars:
                return True
            
            # Check for existential quantification patterns in context name
            context_name = current_context.properties.get('name', '')
            if 'Existential Quantification' in context_name:
                # This is an existential quantification context
                # Check if our variable is in the quantified set
                if entity_id in quantified_vars:
                    return True
            
            current_context_id = current_context.parent_context
        
        # If no explicit quantification found, check if variable appears in outer contexts
        # (which would indicate it's implicitly quantified at the sheet level)
        entity_contexts = self._get_entity_contexts(entity_id, graph)
        root_context = graph.root_context_id
        
        return root_context in entity_contexts
    
    def _detect_conflicting_constant_uses(self, cross_cut: CrossCutInfo, graph: EGGraph) -> List[str]:
        """Detect conflicting uses of a constant across contexts.
        
        Args:
            cross_cut: The cross-cut involving a constant.
            graph: The existential graph.
            
        Returns:
            List of conflicting use descriptions.
        """
        violations = []
        entity = graph.entities[cross_cut.entity_id]
        
        if entity.entity_type != 'constant':
            return violations
        
        # Analyze how the constant is used in each context
        context_uses = {}
        for context_id in cross_cut.contexts:
            uses = self._analyze_constant_usage_in_context(cross_cut.entity_id, context_id, graph)
            context_uses[context_id] = uses
        
        # Compare uses across contexts
        context_list = list(cross_cut.contexts)
        for i, context1 in enumerate(context_list):
            for context2 in context_list[i+1:]:
                conflicts = self._compare_constant_uses(
                    context_uses[context1], context_uses[context2], context1, context2
                )
                violations.extend(conflicts)
        
        return violations
    
    def _analyze_constant_usage_in_context(self, entity_id: EntityId, context_id: ContextId, graph: EGGraph) -> Dict[str, Any]:
        """Analyze how a constant is used within a specific context.
        
        Args:
            entity_id: The constant entity to analyze.
            context_id: The context to analyze.
            graph: The existential graph.
            
        Returns:
            Dictionary describing the constant's usage.
        """
        usage = {
            'predicates': [],
            'roles': [],
            'properties': []
        }
        
        # Find predicates in this context that use the constant
        context_items = graph.get_items_in_context(context_id)
        for item_id in context_items:
            if item_id in graph.predicates:
                predicate = graph.predicates[item_id]
                if entity_id in predicate.entities:
                    usage['predicates'].append(predicate.name)
                    # Determine the role of the constant in this predicate
                    entity_index = list(predicate.entities).index(entity_id)
                    usage['roles'].append(f"{predicate.name}_arg_{entity_index}")
        
        return usage
    
    def _compare_constant_uses(self, usage1: Dict[str, Any], usage2: Dict[str, Any], 
                             context1: ContextId, context2: ContextId) -> List[str]:
        """Compare constant usage between two contexts.
        
        Args:
            usage1: Usage in first context.
            usage2: Usage in second context.
            context1: First context ID.
            context2: Second context ID.
            
        Returns:
            List of conflict descriptions.
        """
        conflicts = []
        
        # Check for role conflicts
        roles1 = set(usage1['roles'])
        roles2 = set(usage2['roles'])
        
        # Constants should be used consistently across contexts
        # Different roles might indicate semantic inconsistency
        if roles1 and roles2 and roles1 != roles2:
            conflicts.append(
                f"Constant used in different roles across contexts {context1} and {context2}: "
                f"{roles1} vs {roles2}"
            )
        
        return conflicts
    
    def _get_entity_contexts(self, entity_id: EntityId, graph: EGGraph) -> Set[ContextId]:
        """Get all contexts where an entity appears.
        
        Args:
            entity_id: The entity to search for.
            graph: The existential graph.
            
        Returns:
            Set of context IDs where the entity appears.
        """
        entity_contexts = self._build_entity_context_mapping(graph)
        return entity_contexts.get(entity_id, set())
    
    def _validate_ligature_entity_consistency(self, entity_id: EntityId, contexts: Set[ContextId], 
                                            ligature: Ligature, graph: EGGraph) -> List[str]:
        """Validate consistency of a ligature entity across contexts.
        
        Args:
            entity_id: The entity in the ligature.
            contexts: Contexts where the entity appears.
            ligature: The ligature containing the entity.
            graph: The existential graph.
            
        Returns:
            List of consistency violations.
        """
        violations = []
        
        # Check that the entity maintains the same identity across all contexts
        entity = graph.entities[entity_id]
        
        # Analyze usage patterns across contexts
        usage_patterns = {}
        for context_id in contexts:
            pattern = self._analyze_entity_usage_pattern(entity_id, context_id, graph)
            usage_patterns[context_id] = pattern
        
        # Check for inconsistencies
        pattern_list = list(usage_patterns.items())
        for i, (context1, pattern1) in enumerate(pattern_list):
            for context2, pattern2 in pattern_list[i+1:]:
                inconsistencies = self._detect_usage_inconsistencies(
                    pattern1, pattern2, context1, context2, entity_id
                )
                violations.extend(inconsistencies)
        
        return violations
    
    def _analyze_entity_usage_pattern(self, entity_id: EntityId, context_id: ContextId, graph: EGGraph) -> Dict[str, Any]:
        """Analyze the usage pattern of an entity in a context.
        
        Args:
            entity_id: The entity to analyze.
            context_id: The context to analyze.
            graph: The existential graph.
            
        Returns:
            Dictionary describing the usage pattern.
        """
        pattern = {
            'predicate_roles': [],
            'ligature_connections': [],
            'semantic_properties': []
        }
        
        # Find predicates in this context involving the entity
        context_items = graph.get_items_in_context(context_id)
        for item_id in context_items:
            if item_id in graph.predicates:
                predicate = graph.predicates[item_id]
                if entity_id in predicate.entities:
                    entity_index = list(predicate.entities).index(entity_id)
                    pattern['predicate_roles'].append({
                        'predicate': predicate.name,
                        'role_index': entity_index,
                        'arity': len(predicate.entities)
                    })
        
        # Find ligature connections in this context
        for ligature_id, ligature in graph.ligatures.items():
            if entity_id in ligature.entities:
                other_entities = ligature.entities - {entity_id}
                pattern['ligature_connections'].extend(other_entities)
        
        return pattern
    
    def _detect_usage_inconsistencies(self, pattern1: Dict[str, Any], pattern2: Dict[str, Any], 
                                    context1: ContextId, context2: ContextId, entity_id: EntityId) -> List[str]:
        """Detect inconsistencies between usage patterns.
        
        Args:
            pattern1: Usage pattern in first context.
            pattern2: Usage pattern in second context.
            context1: First context ID.
            context2: Second context ID.
            entity_id: The entity being analyzed.
            
        Returns:
            List of inconsistency descriptions.
        """
        inconsistencies = []
        
        # Check for role inconsistencies
        roles1 = {(role['predicate'], role['role_index']) for role in pattern1['predicate_roles']}
        roles2 = {(role['predicate'], role['role_index']) for role in pattern2['predicate_roles']}
        
        # Same predicate with different roles indicates potential inconsistency
        predicates1 = {role[0] for role in roles1}
        predicates2 = {role[0] for role in roles2}
        common_predicates = predicates1 & predicates2
        
        for predicate in common_predicates:
            roles_in_pred1 = {role[1] for role in roles1 if role[0] == predicate}
            roles_in_pred2 = {role[1] for role in roles2 if role[0] == predicate}
            
            if roles_in_pred1 != roles_in_pred2:
                inconsistencies.append(
                    f"Entity {entity_id} has different roles in predicate {predicate} "
                    f"across contexts {context1} and {context2}: {roles_in_pred1} vs {roles_in_pred2}"
                )
        
        return inconsistencies
    
    def _analyze_entity_usage_across_contexts(self, cross_cut: CrossCutInfo, graph: EGGraph) -> Dict[ContextId, Dict]:
        """Analyze how an entity is used across different contexts.
        
        Args:
            cross_cut: The cross-cut to analyze.
            graph: The existential graph.
            
        Returns:
            Dictionary mapping context IDs to usage information.
        """
        usage_info = {}
        
        for context_id in cross_cut.contexts:
            usage_info[context_id] = self._analyze_entity_usage_pattern(
                cross_cut.entity_id, context_id, graph
            )
        
        return usage_info
    
    def _compare_entity_usage(self, usage1: Dict, usage2: Dict, context1: ContextId, context2: ContextId) -> Dict[str, List[str]]:
        """Compare entity usage between two contexts.
        
        Args:
            usage1: Usage information for first context.
            usage2: Usage information for second context.
            context1: First context ID.
            context2: Second context ID.
            
        Returns:
            Dictionary with 'violations' and 'warnings' lists.
        """
        violations = []
        warnings = []
        
        # Compare predicate roles
        roles1 = {(role['predicate'], role['role_index']) for role in usage1.get('predicate_roles', [])}
        roles2 = {(role['predicate'], role['role_index']) for role in usage2.get('predicate_roles', [])}
        
        # Check for conflicting roles
        predicates1 = {role[0] for role in roles1}
        predicates2 = {role[0] for role in roles2}
        common_predicates = predicates1 & predicates2
        
        for predicate in common_predicates:
            pred_roles1 = {role[1] for role in roles1 if role[0] == predicate}
            pred_roles2 = {role[1] for role in roles2 if role[0] == predicate}
            
            if pred_roles1 != pred_roles2:
                violations.append(
                    f"Entity has conflicting roles in predicate {predicate} "
                    f"between contexts {context1} and {context2}"
                )
        
        # Compare ligature connections
        connections1 = set(usage1.get('ligature_connections', []))
        connections2 = set(usage2.get('ligature_connections', []))
        
        if connections1 != connections2:
            warnings.append(
                f"Entity has different ligature connections between contexts {context1} and {context2}"
            )
        
        return {'violations': violations, 'warnings': warnings}
    
    def _validate_boundary_ligature_consistency(self, ligature: Ligature, boundary_entities: Set[EntityId], graph: EGGraph) -> List[str]:
        """Validate consistency of a ligature that crosses boundaries.
        
        Args:
            ligature: The ligature that crosses boundaries.
            boundary_entities: Entities in the ligature that cross boundaries.
            graph: The existential graph.
            
        Returns:
            List of consistency violations.
        """
        violations = []
        
        # Check that all boundary entities in the ligature maintain consistent identity
        for entity_id in boundary_entities:
            entity_contexts = self._get_entity_contexts(entity_id, graph)
            
            # Validate that the entity's usage is consistent across all contexts
            consistency_violations = self._validate_ligature_entity_consistency(
                entity_id, entity_contexts, ligature, graph
            )
            violations.extend(consistency_violations)
        
        # Check that the ligature as a whole maintains semantic consistency
        semantic_violations = self._validate_ligature_semantic_consistency(ligature, graph)
        violations.extend(semantic_violations)
        
        return violations
    
    def _validate_ligature_semantic_consistency(self, ligature: Ligature, graph: EGGraph) -> List[str]:
        """Validate semantic consistency of a ligature.
        
        Args:
            ligature: The ligature to validate.
            graph: The existential graph.
            
        Returns:
            List of semantic consistency violations.
        """
        violations = []
        
        # Check that all entities in the ligature can logically represent the same object
        entity_types = set()
        for entity_id in ligature.entities:
            if entity_id in graph.entities:
                entity = graph.entities[entity_id]
                entity_types.add(entity.entity_type)
        
        # Mixed entity types in a ligature may indicate semantic issues
        if len(entity_types) > 1:
            violations.append(
                f"Ligature {ligature.id} contains entities of different types: {entity_types}. "
                "This may indicate semantic inconsistency."
            )
        
        # Check for logical contradictions in the ligature's usage
        contradiction_violations = self._check_ligature_contradictions(ligature, graph)
        violations.extend(contradiction_violations)
        
        return violations
    
    def _check_ligature_contradictions(self, ligature: Ligature, graph: EGGraph) -> List[str]:
        """Check for logical contradictions in a ligature's usage.
        
        Args:
            ligature: The ligature to check.
            graph: The existential graph.
            
        Returns:
            List of contradiction descriptions.
        """
        violations = []
        
        # Collect all predicates that involve entities in this ligature
        involved_predicates = []
        for predicate_id, predicate in graph.predicates.items():
            if any(entity_id in ligature.entities for entity_id in predicate.entities):
                involved_predicates.append(predicate)
        
        # Check for contradictory predicate applications
        # (This is a simplified check - more sophisticated logic could be added)
        predicate_names = [pred.name for pred in involved_predicates]
        
        # Look for obvious contradictions (e.g., "Mortal" and "Immortal")
        contradiction_pairs = [
            ('Mortal', 'Immortal'),
            ('Finite', 'Infinite'),
            ('Human', 'NonHuman')
        ]
        
        for pred1, pred2 in contradiction_pairs:
            if pred1 in predicate_names and pred2 in predicate_names:
                violations.append(
                    f"Ligature {ligature.id} involves contradictory predicates: {pred1} and {pred2}"
                )
        
        return violations
    
    def _check_for_logical_contradictions(self, cross_cut: CrossCutInfo, graph: EGGraph) -> List[str]:
        """Check if a cross-cut creates logical contradictions.
        
        Args:
            cross_cut: The cross-cut to check.
            graph: The existential graph.
            
        Returns:
            List of contradiction descriptions.
        """
        violations = []
        
        # Check if the cross-cut creates contradictory assertions
        entity = graph.entities.get(cross_cut.entity_id)
        if not entity:
            return violations
        
        # Analyze predicates involving this entity across different contexts
        context_predicates = {}
        for context_id in cross_cut.contexts:
            predicates = []
            context_items = graph.get_items_in_context(context_id)
            for item_id in context_items:
                if item_id in graph.predicates:
                    predicate = graph.predicates[item_id]
                    if cross_cut.entity_id in predicate.entities:
                        predicates.append(predicate.name)
            context_predicates[context_id] = predicates
        
        # Check for contradictions between positive and negative contexts
        for context_id in cross_cut.contexts:
            context = graph.contexts[context_id]
            other_contexts = cross_cut.contexts - {context_id}
            
            for other_context_id in other_contexts:
                other_context = graph.contexts[other_context_id]
                
                # If one context is negative and the other positive, check for contradictions
                if (context.context_type == 'cut' and other_context.context_type == 'sheet') or \
                   (context.context_type == 'sheet' and other_context.context_type == 'cut'):
                    
                    # Same predicates in positive and negative contexts create contradictions
                    common_predicates = set(context_predicates[context_id]) & set(context_predicates[other_context_id])
                    for predicate in common_predicates:
                        violations.append(
                            f"Cross-cut entity {cross_cut.entity_id} appears in predicate {predicate} "
                            f"in both positive context {other_context_id if other_context.context_type == 'sheet' else context_id} "
                            f"and negative context {context_id if context.context_type == 'cut' else other_context_id}, "
                            "creating a logical contradiction"
                        )
        
        return violations
    
    def _check_meaning_preservation(self, cross_cut: CrossCutInfo, graph: EGGraph) -> List[str]:
        """Check if a cross-cut preserves intended meaning.
        
        Args:
            cross_cut: The cross-cut to check.
            graph: The existential graph.
            
        Returns:
            List of meaning preservation violations.
        """
        violations = []
        
        # Check that the entity's meaning is preserved across contexts
        entity = graph.entities.get(cross_cut.entity_id)
        if not entity:
            return violations
        
        # For constants, meaning should be identical across contexts
        if entity.entity_type == 'constant':
            meaning_violations = self._check_constant_meaning_preservation(cross_cut, graph)
            violations.extend(meaning_violations)
        
        # For variables, check proper scoping and quantification
        elif entity.entity_type == 'variable':
            scoping_violations = self._check_variable_meaning_preservation(cross_cut, graph)
            violations.extend(scoping_violations)
        
        return violations
    
    def _check_constant_meaning_preservation(self, cross_cut: CrossCutInfo, graph: EGGraph) -> List[str]:
        """Check meaning preservation for constant cross-cuts.
        
        Args:
            cross_cut: The cross-cut involving a constant.
            graph: The existential graph.
            
        Returns:
            List of meaning preservation violations.
        """
        violations = []
        
        # Constants should refer to the same object across all contexts
        # Check for consistent usage patterns
        usage_patterns = {}
        for context_id in cross_cut.contexts:
            pattern = self._analyze_constant_usage_in_context(cross_cut.entity_id, context_id, graph)
            usage_patterns[context_id] = pattern
        
        # Compare usage patterns for consistency
        pattern_list = list(usage_patterns.items())
        for i, (context1, pattern1) in enumerate(pattern_list):
            for context2, pattern2 in pattern_list[i+1:]:
                conflicts = self._compare_constant_uses(pattern1, pattern2, context1, context2)
                violations.extend(conflicts)
        
        return violations
    
    def _check_variable_meaning_preservation(self, cross_cut: CrossCutInfo, graph: EGGraph) -> List[str]:
        """Check meaning preservation for variable cross-cuts.
        
        Args:
            cross_cut: The cross-cut involving a variable.
            graph: The existential graph.
            
        Returns:
            List of meaning preservation violations.
        """
        violations = []
        
        # Variables crossing contexts must maintain proper scoping
        # Check that the variable is properly quantified in all relevant contexts
        for context_id in cross_cut.contexts:
            if not self._is_properly_quantified(cross_cut.entity_id, context_id, graph):
                violations.append(
                    f"Variable {cross_cut.entity_id} in context {context_id} lacks proper quantification, "
                    "potentially violating meaning preservation"
                )
        
        return violations
    
    def _check_insertion_variable_scoping(self, cross_cut: CrossCutInfo, target_context: ContextId, graph: EGGraph) -> List[str]:
        """Check variable scoping issues for insertion.
        
        Args:
            cross_cut: The cross-cut involving a variable.
            target_context: Context where insertion is being applied.
            graph: The existential graph.
            
        Returns:
            List of scoping violations.
        """
        violations = []
        
        entity = graph.entities.get(cross_cut.entity_id)
        if not entity or entity.entity_type != 'variable':
            return violations
        
        # Check if insertion would create improper variable scoping
        target_context_obj = graph.contexts[target_context]
        
        # If inserting into a context where the variable isn't properly quantified
        if not self._is_properly_quantified(cross_cut.entity_id, target_context, graph):
            violations.append(
                f"Insertion into context {target_context} would create improper scoping "
                f"for variable {cross_cut.entity_id}"
            )
        
        return violations
    
    def _check_iteration_identity_preservation(self, cross_cut: CrossCutInfo, target_context: ContextId, graph: EGGraph) -> List[str]:
        """Check identity preservation for iteration.
        
        Args:
            cross_cut: The cross-cut affected by iteration.
            target_context: Context where iteration is being applied.
            graph: The existential graph.
            
        Returns:
            List of identity preservation violations.
        """
        violations = []
        
        # Iteration should not create multiple distinct instances of the same entity
        # Check if the iteration would violate the single identity principle
        
        entity = graph.entities.get(cross_cut.entity_id)
        if not entity:
            return violations
        
        # If the entity is already in the target context and we're iterating it again,
        # this could create identity confusion
        if target_context in cross_cut.contexts:
            violations.append(
                f"Iteration of entity {cross_cut.entity_id} into context {target_context} "
                "where it already exists may violate identity preservation"
            )
        
        return violations
    
    def _check_deiteration_necessity(self, cross_cut: CrossCutInfo, target_context: ContextId, graph: EGGraph) -> List[str]:
        """Check necessity of cross-cut connections for deiteration.
        
        Args:
            cross_cut: The cross-cut affected by deiteration.
            target_context: Context where deiteration is being applied.
            graph: The existential graph.
            
        Returns:
            List of necessity violations.
        """
        violations = []
        
        # Deiteration should not remove necessary cross-cut connections
        # Check if removing the entity from the target context would break
        # necessary identity connections
        
        if target_context in cross_cut.contexts and len(cross_cut.contexts) == 2:
            # This is the only cross-cut connection for this entity
            # Removing it would eliminate the cross-cut entirely
            violations.append(
                f"Deiteration of entity {cross_cut.entity_id} from context {target_context} "
                "would eliminate necessary cross-cut identity connection"
            )
        
        return violations

