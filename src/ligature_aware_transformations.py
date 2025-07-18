"""
Ligature-aware transformation utilities for enhanced cross-cut validation.

This module provides specialized transformation utilities that are specifically
designed to work with cross-cut ligatures and ensure identity preservation
during all graph transformations.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from eg_types import (
    Entity, Predicate, Context, Ligature,
    EntityId, PredicateId, ContextId, LigatureId, ItemId,
    ValidationError, pmap, pset
)
from graph import EGGraph
from cross_cut_validator import CrossCutValidator, CrossCutInfo, IdentityPreservationResult


@dataclass
class LigatureTransformationResult:
    """Result of a ligature-aware transformation."""
    success: bool
    result_graph: Optional[EGGraph]
    cross_cuts_preserved: bool
    identity_violations: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class LigatureAwareTransformationEngine:
    """Specialized transformation engine with enhanced ligature awareness."""
    
    def __init__(self):
        """Initialize the ligature-aware transformation engine."""
        self.cross_cut_validator = CrossCutValidator()
    
    def safe_entity_join(self, graph: EGGraph, entity_ids: Set[EntityId]) -> LigatureTransformationResult:
        """Safely join entities while preserving cross-cut ligature integrity.
        
        Args:
            graph: The source graph.
            entity_ids: Set of entity IDs to join.
            
        Returns:
            LigatureTransformationResult with the outcome.
        """
        # Analyze cross-cuts before transformation
        pre_cross_cuts = self.cross_cut_validator.analyze_cross_cuts(graph)
        affected_cross_cuts = [cc for cc in pre_cross_cuts if cc.entity_id in entity_ids]
        
        # Check if joining these entities would violate cross-cut constraints
        violations = []
        warnings = []
        
        # Validate that all entities can be safely joined
        entity_types = set()
        for entity_id in entity_ids:
            if entity_id in graph.entities:
                entity = graph.entities[entity_id]
                entity_types.add(entity.entity_type)
        
        # Mixed entity types cannot be joined
        if len(entity_types) > 1:
            violations.append(f"Cannot join entities of different types: {entity_types}")
        
        # Check cross-cut compatibility
        for cross_cut in affected_cross_cuts:
            if cross_cut.cross_cut_type.value in ['multi_cross', 'nested_cross']:
                warnings.append(
                    f"Joining entity {cross_cut.entity_id} may affect complex cross-cut pattern"
                )
        
        if violations:
            return LigatureTransformationResult(
                success=False,
                result_graph=None,
                cross_cuts_preserved=False,
                identity_violations=violations,
                warnings=warnings,
                metadata={'affected_cross_cuts': len(affected_cross_cuts)}
            )
        
        # Perform the join operation
        try:
            # Create new ligature connecting all entities
            from ligature import LigatureManager
            ligature_manager = LigatureManager()
            
            new_ligature = ligature_manager.create_ligature_from_entities(entity_ids)
            result_graph = graph.add_ligature(new_ligature)
            
            # Validate post-transformation state
            post_validation = self.cross_cut_validator.validate_identity_preservation(result_graph)
            
            return LigatureTransformationResult(
                success=True,
                result_graph=result_graph,
                cross_cuts_preserved=post_validation.is_preserved,
                identity_violations=post_validation.violations,
                warnings=warnings + post_validation.warnings,
                metadata={
                    'affected_cross_cuts': len(affected_cross_cuts),
                    'new_ligature_id': new_ligature.id,
                    'entities_joined': len(entity_ids)
                }
            )
            
        except Exception as e:
            return LigatureTransformationResult(
                success=False,
                result_graph=None,
                cross_cuts_preserved=False,
                identity_violations=[f"Join operation failed: {str(e)}"],
                warnings=warnings,
                metadata={'affected_cross_cuts': len(affected_cross_cuts)}
            )
    
    def safe_entity_sever(self, graph: EGGraph, entity_id: EntityId, 
                         target_contexts: Set[ContextId]) -> LigatureTransformationResult:
        """Safely sever an entity's connections while preserving cross-cut integrity.
        
        Args:
            graph: The source graph.
            entity_id: The entity to sever.
            target_contexts: Contexts where the entity should be severed.
            
        Returns:
            LigatureTransformationResult with the outcome.
        """
        # Analyze current cross-cuts
        pre_cross_cuts = self.cross_cut_validator.analyze_cross_cuts(graph)
        affected_cross_cuts = [cc for cc in pre_cross_cuts if cc.entity_id == entity_id]
        
        violations = []
        warnings = []
        
        # Check if severing would break necessary cross-cut connections
        for cross_cut in affected_cross_cuts:
            if len(cross_cut.contexts & target_contexts) > 0:
                if len(cross_cut.contexts) == 2:
                    # This would completely eliminate the cross-cut
                    violations.append(
                        f"Severing entity {entity_id} would eliminate necessary cross-cut connection"
                    )
                else:
                    warnings.append(
                        f"Severing entity {entity_id} will reduce cross-cut complexity"
                    )
        
        if violations:
            return LigatureTransformationResult(
                success=False,
                result_graph=None,
                cross_cuts_preserved=False,
                identity_violations=violations,
                warnings=warnings,
                metadata={'affected_cross_cuts': len(affected_cross_cuts)}
            )
        
        # Perform the sever operation
        try:
            # Implementation would depend on specific severing logic
            # For now, return a placeholder result
            result_graph = graph  # Placeholder - actual severing logic would go here
            
            # Validate post-transformation state
            post_validation = self.cross_cut_validator.validate_identity_preservation(result_graph)
            
            return LigatureTransformationResult(
                success=True,
                result_graph=result_graph,
                cross_cuts_preserved=post_validation.is_preserved,
                identity_violations=post_validation.violations,
                warnings=warnings + post_validation.warnings,
                metadata={
                    'affected_cross_cuts': len(affected_cross_cuts),
                    'contexts_severed': len(target_contexts)
                }
            )
            
        except Exception as e:
            return LigatureTransformationResult(
                success=False,
                result_graph=None,
                cross_cuts_preserved=False,
                identity_violations=[f"Sever operation failed: {str(e)}"],
                warnings=warnings,
                metadata={'affected_cross_cuts': len(affected_cross_cuts)}
            )
    
    def validate_transformation_safety(self, graph: EGGraph, transformation_type: str,
                                     target_items: Set[ItemId], target_context: ContextId) -> Dict[str, Any]:
        """Validate the safety of a proposed transformation with respect to cross-cut ligatures.
        
        Args:
            graph: The source graph.
            transformation_type: Type of transformation being proposed.
            target_items: Items involved in the transformation.
            target_context: Context where transformation would be applied.
            
        Returns:
            Dictionary with safety analysis results.
        """
        # Get current cross-cut state
        current_cross_cuts = self.cross_cut_validator.analyze_cross_cuts(graph)
        
        # Validate transformation constraints
        violations = self.cross_cut_validator.validate_transformation_constraints(
            graph, transformation_type, target_items, target_context
        )
        
        # Analyze affected cross-cuts
        affected_cross_cuts = []
        for cross_cut in current_cross_cuts:
            if (cross_cut.entity_id in target_items or
                target_context in cross_cut.contexts or
                any(pred_id in target_items for pred_id in cross_cut.predicates_involved)):
                affected_cross_cuts.append(cross_cut)
        
        # Assess risk level
        risk_level = "low"
        if violations:
            risk_level = "high"
        elif len(affected_cross_cuts) > 2:
            risk_level = "medium"
        elif any(cc.cross_cut_type.value == 'nested_cross' for cc in affected_cross_cuts):
            risk_level = "medium"
        
        return {
            'safe': len(violations) == 0,
            'risk_level': risk_level,
            'violations': violations,
            'affected_cross_cuts': len(affected_cross_cuts),
            'cross_cut_details': [
                {
                    'entity_id': cc.entity_id,
                    'type': cc.cross_cut_type.value,
                    'contexts': list(cc.contexts),
                    'depth_span': cc.depth_span
                }
                for cc in affected_cross_cuts
            ],
            'recommendations': self._generate_safety_recommendations(
                transformation_type, affected_cross_cuts, violations
            )
        }
    
    def _generate_safety_recommendations(self, transformation_type: str, 
                                       affected_cross_cuts: List[CrossCutInfo],
                                       violations: List[str]) -> List[str]:
        """Generate safety recommendations for a transformation.
        
        Args:
            transformation_type: Type of transformation.
            affected_cross_cuts: Cross-cuts that would be affected.
            violations: Current constraint violations.
            
        Returns:
            List of safety recommendations.
        """
        recommendations = []
        
        if violations:
            recommendations.append("Address constraint violations before proceeding")
            for violation in violations:
                recommendations.append(f"- {violation}")
        
        if len(affected_cross_cuts) > 2:
            recommendations.append("Consider breaking down transformation into smaller steps")
        
        for cross_cut in affected_cross_cuts:
            if cross_cut.cross_cut_type.value == 'nested_cross':
                recommendations.append(
                    f"Exercise caution with entity {cross_cut.entity_id} - "
                    "it crosses nested context boundaries"
                )
            elif cross_cut.cross_cut_type.value == 'multi_cross':
                recommendations.append(
                    f"Entity {cross_cut.entity_id} crosses multiple contexts - "
                    "verify identity preservation"
                )
        
        if transformation_type == "erasure" and affected_cross_cuts:
            recommendations.append("Ensure erasure does not sever necessary identity connections")
        
        if transformation_type == "iteration" and affected_cross_cuts:
            recommendations.append("Verify that iteration preserves unique entity identity")
        
        return recommendations
    
    def analyze_ligature_health(self, graph: EGGraph) -> Dict[str, Any]:
        """Analyze the overall health of ligatures and cross-cuts in the graph.
        
        Args:
            graph: The graph to analyze.
            
        Returns:
            Dictionary with ligature health analysis.
        """
        # Get identity preservation analysis
        identity_result = self.cross_cut_validator.validate_identity_preservation(graph)
        
        # Analyze cross-cuts
        cross_cuts = self.cross_cut_validator.analyze_cross_cuts(graph)
        
        # Categorize cross-cuts by type
        cross_cut_types = {}
        for cross_cut in cross_cuts:
            cut_type = cross_cut.cross_cut_type.value
            if cut_type not in cross_cut_types:
                cross_cut_types[cut_type] = 0
            cross_cut_types[cut_type] += 1
        
        # Calculate health score
        health_score = 100
        health_score -= len(identity_result.violations) * 10  # Major penalty for violations
        health_score -= len(identity_result.warnings) * 2    # Minor penalty for warnings
        health_score = max(0, health_score)  # Don't go below 0
        
        # Determine overall health status
        if health_score >= 90:
            health_status = "excellent"
        elif health_score >= 70:
            health_status = "good"
        elif health_score >= 50:
            health_status = "fair"
        else:
            health_status = "poor"
        
        return {
            'health_score': health_score,
            'health_status': health_status,
            'identity_preserved': identity_result.is_preserved,
            'total_cross_cuts': len(cross_cuts),
            'cross_cut_types': cross_cut_types,
            'violations': identity_result.violations,
            'warnings': identity_result.warnings,
            'recommendations': self._generate_health_recommendations(
                identity_result, cross_cuts, health_score
            )
        }
    
    def _generate_health_recommendations(self, identity_result: IdentityPreservationResult,
                                       cross_cuts: List[CrossCutInfo], health_score: int) -> List[str]:
        """Generate recommendations for improving ligature health.
        
        Args:
            identity_result: Identity preservation analysis result.
            cross_cuts: List of cross-cuts in the graph.
            health_score: Current health score.
            
        Returns:
            List of health improvement recommendations.
        """
        recommendations = []
        
        if health_score < 50:
            recommendations.append("Graph has significant ligature integrity issues")
        
        if identity_result.violations:
            recommendations.append("Address identity preservation violations:")
            for violation in identity_result.violations[:3]:  # Show first 3
                recommendations.append(f"- {violation}")
        
        if len(cross_cuts) > 10:
            recommendations.append("Consider simplifying graph structure - many cross-cuts detected")
        
        nested_cross_cuts = [cc for cc in cross_cuts if cc.cross_cut_type.value == 'nested_cross']
        if len(nested_cross_cuts) > 3:
            recommendations.append("Multiple nested cross-cuts may indicate overly complex structure")
        
        if identity_result.warnings:
            recommendations.append("Review warnings for potential improvements:")
            for warning in identity_result.warnings[:2]:  # Show first 2
                recommendations.append(f"- {warning}")
        
        return recommendations

