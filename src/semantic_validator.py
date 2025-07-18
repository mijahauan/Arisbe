"""
Semantic consistency validation framework for existential graphs.

This module provides comprehensive semantic validation that integrates with
cross-cut validation and function symbol systems to ensure complete semantic
consistency across all graph operations and transformations.
"""

from typing import Dict, Set, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .eg_types import (
    Entity, Predicate, Context, Ligature,
    EntityId, PredicateId, ContextId, LigatureId,
    pmap, pset, pvector
)
from .graph import EGGraph
from .semantic_interpreter import SemanticModel, SemanticInterpreter, VariableAssignment
from .semantic_evaluator import SemanticEvaluator, TruthEvaluationResult
from .cross_cut_validator import CrossCutValidator, CrossCutInfo
from .transformations import TransformationEngine, TransformationType


class SemanticViolationType(Enum):
    """Types of semantic violations."""
    INTERPRETATION_MISSING = "interpretation_missing"
    LOGICAL_CONTRADICTION = "logical_contradiction"
    TYPE_MISMATCH = "type_mismatch"
    QUANTIFICATION_ERROR = "quantification_error"
    FUNCTION_ARITY_ERROR = "function_arity_error"
    DOMAIN_VIOLATION = "domain_violation"
    CROSS_CUT_SEMANTIC_ERROR = "cross_cut_semantic_error"
    TRANSFORMATION_SEMANTIC_ERROR = "transformation_semantic_error"


@dataclass
class SemanticViolation:
    """Represents a semantic consistency violation."""
    violation_type: SemanticViolationType
    description: str
    affected_elements: Set[str]
    severity: str  # 'error', 'warning', 'info'
    context_id: Optional[ContextId] = None
    suggested_fix: Optional[str] = None


@dataclass
class SemanticValidationResult:
    """Result of comprehensive semantic validation."""
    is_semantically_valid: bool
    violations: List[SemanticViolation]
    warnings: List[str]
    recommendations: List[str]
    truth_evaluation: Optional[TruthEvaluationResult]
    cross_cut_analysis: Optional[Dict[str, Any]]
    model_adequacy: Dict[str, Any]
    validation_summary: Dict[str, Any]


class SemanticValidator:
    """Comprehensive semantic consistency validator.
    
    Integrates semantic interpretation with cross-cut validation and function
    symbol systems to provide complete semantic consistency checking.
    """
    
    def __init__(self, model: Optional[SemanticModel] = None):
        """Initialize the semantic validator."""
        self.interpreter = SemanticInterpreter(model)
        self.evaluator = SemanticEvaluator(self.interpreter)
        self.cross_cut_validator = CrossCutValidator()
        self.transformation_engine = TransformationEngine()
        
        # Validation caches
        self.validation_cache = {}
        self.model_adequacy_cache = {}
    
    def set_model(self, model: SemanticModel) -> None:
        """Set the semantic model for validation."""
        self.interpreter.set_model(model)
        self.validation_cache.clear()
        self.model_adequacy_cache.clear()
    
    def validate_semantic_consistency(self, graph: EGGraph) -> SemanticValidationResult:
        """Perform comprehensive semantic consistency validation.
        
        Args:
            graph: The existential graph to validate
            
        Returns:
            SemanticValidationResult with complete validation analysis
        """
        violations = []
        warnings = []
        recommendations = []
        
        try:
            # 1. Basic semantic interpretation validation
            interpretation_violations = self._validate_interpretation_completeness(graph)
            violations.extend(interpretation_violations)
            
            # 2. Truth evaluation and logical consistency
            truth_result = self.evaluator.evaluate_truth(graph)
            logical_violations = self._validate_logical_consistency(graph, truth_result)
            violations.extend(logical_violations)
            
            # 3. Cross-cut semantic validation
            cross_cut_analysis = self._validate_cross_cut_semantics(graph)
            violations.extend(cross_cut_analysis['violations'])
            warnings.extend(cross_cut_analysis['warnings'])
            
            # 4. Function symbol semantic validation
            function_violations = self._validate_function_semantics(graph)
            violations.extend(function_violations)
            
            # 5. Quantification semantic validation
            quantification_violations = self._validate_quantification_semantics(graph, truth_result)
            violations.extend(quantification_violations)
            
            # 6. Model adequacy analysis
            model_adequacy = self._analyze_model_adequacy(graph)
            
            # 7. Generate recommendations
            recommendations = self._generate_semantic_recommendations(
                graph, violations, warnings, truth_result, model_adequacy
            )
            
            # Determine overall validity
            error_violations = [v for v in violations if v.severity == 'error']
            is_valid = len(error_violations) == 0
            
            # Create validation summary
            validation_summary = self._create_validation_summary(
                graph, violations, warnings, truth_result, model_adequacy
            )
            
            return SemanticValidationResult(
                is_semantically_valid=is_valid,
                violations=violations,
                warnings=warnings,
                recommendations=recommendations,
                truth_evaluation=truth_result,
                cross_cut_analysis=cross_cut_analysis,
                model_adequacy=model_adequacy,
                validation_summary=validation_summary
            )
            
        except Exception as e:
            # Handle validation errors gracefully
            error_violation = SemanticViolation(
                violation_type=SemanticViolationType.DOMAIN_VIOLATION,
                description=f"Validation error: {str(e)}",
                affected_elements=set(),
                severity='error'
            )
            
            return SemanticValidationResult(
                is_semantically_valid=False,
                violations=[error_violation],
                warnings=[],
                recommendations=["Fix validation errors before proceeding"],
                truth_evaluation=None,
                cross_cut_analysis=None,
                model_adequacy={'adequate': False, 'issues': [str(e)]},
                validation_summary={'status': 'error', 'message': str(e)}
            )
    
    def _validate_interpretation_completeness(self, graph: EGGraph) -> List[SemanticViolation]:
        """Validate that all symbols have proper interpretations."""
        violations = []
        
        # Check constants
        for entity in graph.entities.values():
            if entity.entity_type == 'constant' and entity.name:
                if not self.interpreter.model.interpret_constant(entity.name):
                    violations.append(SemanticViolation(
                        violation_type=SemanticViolationType.INTERPRETATION_MISSING,
                        description=f"Constant '{entity.name}' has no interpretation",
                        affected_elements={entity.id},
                        severity='warning',
                        suggested_fix=f"Add interpretation for constant '{entity.name}'"
                    ))
        
        # Check predicates
        for predicate in graph.predicates.values():
            if not self.interpreter.model.interpret_predicate(predicate.name):
                violations.append(SemanticViolation(
                    violation_type=SemanticViolationType.INTERPRETATION_MISSING,
                    description=f"Predicate '{predicate.name}' has no interpretation",
                    affected_elements={predicate.id},
                    severity='warning',
                    suggested_fix=f"Add interpretation for predicate '{predicate.name}'"
                ))
        
        # Check domain adequacy
        if len(self.interpreter.model.domain.individuals) == 0:
            violations.append(SemanticViolation(
                violation_type=SemanticViolationType.DOMAIN_VIOLATION,
                description="Empty domain - no individuals for interpretation",
                affected_elements=set(),
                severity='error',
                suggested_fix="Add individuals to the semantic domain"
            ))
        
        return violations
    
    def _validate_logical_consistency(self, graph: EGGraph, 
                                    truth_result: TruthEvaluationResult) -> List[SemanticViolation]:
        """Validate logical consistency of the graph."""
        violations = []
        
        # Check for semantic errors in evaluation
        for error in truth_result.semantic_errors:
            violations.append(SemanticViolation(
                violation_type=SemanticViolationType.LOGICAL_CONTRADICTION,
                description=f"Semantic evaluation error: {error}",
                affected_elements=set(),
                severity='error'
            ))
        
        # Check for contradictory contexts
        contradictions = self._detect_logical_contradictions(graph)
        for contradiction in contradictions:
            violations.append(SemanticViolation(
                violation_type=SemanticViolationType.LOGICAL_CONTRADICTION,
                description=contradiction['description'],
                affected_elements=contradiction['elements'],
                severity='error',
                context_id=contradiction.get('context_id'),
                suggested_fix=contradiction.get('fix')
            ))
        
        return violations
    
    def _detect_logical_contradictions(self, graph: EGGraph) -> List[Dict[str, Any]]:
        """Detect logical contradictions in the graph structure."""
        contradictions = []
        
        # Check for same predicate in positive and negative contexts
        predicate_contexts = {}
        
        for predicate in graph.predicates.values():
            # Find which context this predicate is in
            context_id = self._find_predicate_context(graph, predicate.id)
            if context_id:
                polarity = self._determine_context_polarity(graph, context_id)
                
                key = (predicate.name, tuple(sorted(predicate.entities)))
                if key not in predicate_contexts:
                    predicate_contexts[key] = []
                predicate_contexts[key].append((predicate.id, polarity, context_id))
        
        # Check for contradictions
        for key, occurrences in predicate_contexts.items():
            polarities = {occ[1] for occ in occurrences}
            if 'positive' in polarities and 'negative' in polarities:
                predicate_name, entities = key
                contradictions.append({
                    'description': f"Predicate '{predicate_name}' appears in both positive and negative contexts",
                    'elements': {occ[0] for occ in occurrences},
                    'fix': "Remove contradiction or add proper quantification"
                })
        
        return contradictions
    
    def _validate_cross_cut_semantics(self, graph: EGGraph) -> Dict[str, Any]:
        """Validate semantic consistency of cross-cut ligatures."""
        violations = []
        warnings = []
        
        # Use cross-cut validator for structural analysis
        cross_cuts = self.cross_cut_validator.analyze_cross_cuts(graph)
        identity_result = self.cross_cut_validator.validate_identity_preservation(graph)
        
        # Add semantic analysis to cross-cut validation
        for cross_cut in cross_cuts:
            semantic_issues = self._analyze_cross_cut_semantics(graph, cross_cut)
            violations.extend(semantic_issues['violations'])
            warnings.extend(semantic_issues['warnings'])
        
        # Check identity preservation violations
        for violation in identity_result.violations:
            violations.append(SemanticViolation(
                violation_type=SemanticViolationType.CROSS_CUT_SEMANTIC_ERROR,
                description=f"Cross-cut identity violation: {violation}",
                affected_elements=set(),
                severity='error'
            ))
        
        return {
            'violations': violations,
            'warnings': warnings,
            'cross_cuts': cross_cuts,
            'identity_preserved': identity_result.is_preserved
        }
    
    def _analyze_cross_cut_semantics(self, graph: EGGraph, cross_cut: CrossCutInfo) -> Dict[str, Any]:
        """Analyze semantic implications of a specific cross-cut."""
        violations = []
        warnings = []
        
        entity = graph.entities.get(cross_cut.entity_id)
        if not entity:
            return {'violations': violations, 'warnings': warnings}
        
        # Check semantic consistency across contexts
        if entity.entity_type == 'constant':
            # Constants should have consistent interpretation across contexts
            interpretation = self.interpreter.model.interpret_constant(entity.name)
            if not interpretation:
                warnings.append(f"Cross-cut constant '{entity.name}' has no interpretation")
            
        elif entity.entity_type == 'variable':
            # Variables in cross-cuts affect quantification scope
            scope_issues = self._check_cross_cut_quantification(graph, cross_cut)
            violations.extend(scope_issues)
        
        return {'violations': violations, 'warnings': warnings}
    
    def _check_cross_cut_quantification(self, graph: EGGraph, cross_cut: CrossCutInfo) -> List[SemanticViolation]:
        """Check quantification issues in cross-cut scenarios."""
        violations = []
        
        entity = graph.entities.get(cross_cut.entity_id)
        if not entity or entity.entity_type != 'variable':
            return violations
        
        # Analyze quantification across the cross-cut contexts
        quantification_types = set()
        for context_id in cross_cut.contexts:
            polarity = self._determine_context_polarity(graph, context_id)
            quantification_types.add(polarity)
        
        # Check for mixed quantification (both positive and negative contexts)
        if len(quantification_types) > 1:
            violations.append(SemanticViolation(
                violation_type=SemanticViolationType.QUANTIFICATION_ERROR,
                description=f"Variable '{entity.name}' crosses both positive and negative contexts",
                affected_elements={entity.id},
                severity='warning',
                suggested_fix="Ensure proper quantification scope for cross-cut variables"
            ))
        
        return violations
    
    def _validate_function_semantics(self, graph: EGGraph) -> List[SemanticViolation]:
        """Validate semantic consistency of function symbols."""
        violations = []
        
        for predicate in graph.predicates.values():
            if hasattr(predicate, 'predicate_type') and predicate.predicate_type == 'function':
                function_issues = self._validate_function_predicate_semantics(graph, predicate)
                violations.extend(function_issues)
        
        return violations
    
    def _validate_function_predicate_semantics(self, graph: EGGraph, predicate: Predicate) -> List[SemanticViolation]:
        """Validate semantics of a specific function predicate."""
        violations = []
        
        # Check function interpretation
        domain_function = self.interpreter.model.domain.get_function(predicate.name)
        if not domain_function:
            violations.append(SemanticViolation(
                violation_type=SemanticViolationType.INTERPRETATION_MISSING,
                description=f"Function '{predicate.name}' has no domain implementation",
                affected_elements={predicate.id},
                severity='warning',
                suggested_fix=f"Add domain function for '{predicate.name}'"
            ))
            return violations
        
        # Check arity consistency
        expected_arity = predicate.arity - 1  # Subtract 1 for return value
        if expected_arity < 0:
            violations.append(SemanticViolation(
                violation_type=SemanticViolationType.FUNCTION_ARITY_ERROR,
                description=f"Function '{predicate.name}' has invalid arity {predicate.arity}",
                affected_elements={predicate.id},
                severity='error',
                suggested_fix="Functions must have at least one entity (the return value)"
            ))
        
        # Check return entity type
        if hasattr(predicate, 'return_entity') and predicate.return_entity:
            return_entity = graph.entities.get(predicate.return_entity)
            if return_entity and return_entity.entity_type == 'constant':
                # Function result should be consistent with constant interpretation
                constant_value = self.interpreter.model.interpret_constant(return_entity.name)
                if constant_value and not self.interpreter.model.domain.contains_individual(constant_value):
                    violations.append(SemanticViolation(
                        violation_type=SemanticViolationType.DOMAIN_VIOLATION,
                        description=f"Function return constant '{return_entity.name}' not in domain",
                        affected_elements={predicate.id, return_entity.id},
                        severity='error'
                    ))
        
        return violations
    
    def _validate_quantification_semantics(self, graph: EGGraph, 
                                         truth_result: TruthEvaluationResult) -> List[SemanticViolation]:
        """Validate semantic consistency of quantification structure."""
        violations = []
        
        for scope in truth_result.quantification_analysis:
            # Check for unbound variables
            for variable in scope.variables:
                if not any(assignment.contains(variable) for assignment in truth_result.satisfying_assignments):
                    violations.append(SemanticViolation(
                        violation_type=SemanticViolationType.QUANTIFICATION_ERROR,
                        description=f"Variable '{variable}' in quantification scope has no satisfying assignment",
                        affected_elements=set(),
                        severity='warning',
                        context_id=scope.context_id
                    ))
            
            # Check scope nesting consistency
            if scope.scope_depth > 5:  # Arbitrary complexity threshold
                violations.append(SemanticViolation(
                    violation_type=SemanticViolationType.QUANTIFICATION_ERROR,
                    description=f"Deep quantification nesting (depth {scope.scope_depth}) may be complex",
                    affected_elements=set(),
                    severity='info',
                    context_id=scope.context_id,
                    suggested_fix="Consider simplifying quantification structure"
                ))
        
        return violations
    
    def _analyze_model_adequacy(self, graph: EGGraph) -> Dict[str, Any]:
        """Analyze whether the current model is adequate for the graph."""
        adequacy = {
            'adequate': True,
            'issues': [],
            'coverage': {},
            'recommendations': []
        }
        
        # Check interpretation coverage
        total_constants = len([e for e in graph.entities.values() if e.entity_type == 'constant'])
        interpreted_constants = len([e for e in graph.entities.values() 
                                   if e.entity_type == 'constant' and e.name and 
                                   self.interpreter.model.interpret_constant(e.name)])
        
        total_predicates = len(graph.predicates)
        interpreted_predicates = len([p for p in graph.predicates.values() 
                                    if self.interpreter.model.interpret_predicate(p.name)])
        
        adequacy['coverage'] = {
            'constants': interpreted_constants / max(total_constants, 1),
            'predicates': interpreted_predicates / max(total_predicates, 1)
        }
        
        # Check adequacy thresholds
        if adequacy['coverage']['constants'] < 0.8:
            adequacy['adequate'] = False
            adequacy['issues'].append("Low constant interpretation coverage")
            adequacy['recommendations'].append("Add interpretations for more constants")
        
        if adequacy['coverage']['predicates'] < 0.8:
            adequacy['adequate'] = False
            adequacy['issues'].append("Low predicate interpretation coverage")
            adequacy['recommendations'].append("Add interpretations for more predicates")
        
        # Check domain size adequacy
        domain_size = len(self.interpreter.model.domain.individuals)
        variable_count = len([e for e in graph.entities.values() if e.entity_type == 'variable'])
        
        if domain_size < variable_count:
            adequacy['issues'].append("Domain may be too small for variable assignments")
            adequacy['recommendations'].append("Consider expanding the domain")
        
        return adequacy
    
    def _generate_semantic_recommendations(self, graph: EGGraph, violations: List[SemanticViolation],
                                         warnings: List[str], truth_result: TruthEvaluationResult,
                                         model_adequacy: Dict[str, Any]) -> List[str]:
        """Generate semantic improvement recommendations."""
        recommendations = []
        
        # Based on violations
        error_count = len([v for v in violations if v.severity == 'error'])
        warning_count = len([v for v in violations if v.severity == 'warning'])
        
        if error_count > 0:
            recommendations.append(f"Address {error_count} semantic errors before proceeding")
        
        if warning_count > 0:
            recommendations.append(f"Consider addressing {warning_count} semantic warnings")
        
        # Based on truth evaluation
        if not truth_result.is_true:
            recommendations.append("Graph is not true in current model - review graph structure or model")
        
        if not truth_result.satisfying_assignments:
            recommendations.append("No satisfying assignments found - check variable constraints")
        
        # Based on model adequacy
        if not model_adequacy['adequate']:
            recommendations.extend(model_adequacy['recommendations'])
        
        # General recommendations
        if len(graph.entities) == 0:
            recommendations.append("Add entities to make the graph meaningful")
        
        if len(graph.predicates) == 0:
            recommendations.append("Add predicates to express relationships")
        
        return recommendations
    
    def _create_validation_summary(self, graph: EGGraph, violations: List[SemanticViolation],
                                 warnings: List[str], truth_result: TruthEvaluationResult,
                                 model_adequacy: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the validation results."""
        error_count = len([v for v in violations if v.severity == 'error'])
        warning_count = len([v for v in violations if v.severity == 'warning'])
        
        return {
            'status': 'valid' if error_count == 0 else 'invalid',
            'error_count': error_count,
            'warning_count': warning_count,
            'truth_value': truth_result.truth_value if truth_result else None,
            'model_adequate': model_adequacy['adequate'],
            'graph_complexity': {
                'entities': len(graph.entities),
                'predicates': len(graph.predicates),
                'contexts': len(graph.context_manager.contexts),
                'quantification_scopes': len(truth_result.quantification_analysis) if truth_result else 0
            }
        }
    
    def validate_transformation_semantics(self, original_graph: EGGraph, 
                                        transformed_graph: EGGraph,
                                        transformation_type: str) -> Dict[str, Any]:
        """Validate semantic consistency of a transformation."""
        
        # Use the evaluator's transformation validation
        semantic_result = self.evaluator.validate_transformation_semantics(
            original_graph, transformed_graph, transformation_type
        )
        
        # Add additional semantic consistency checks
        additional_checks = self._additional_transformation_checks(
            original_graph, transformed_graph, transformation_type
        )
        
        return {
            **semantic_result,
            'additional_checks': additional_checks,
            'overall_valid': semantic_result['semantics_preserved'] and additional_checks['valid']
        }
    
    def _additional_transformation_checks(self, original_graph: EGGraph, 
                                        transformed_graph: EGGraph,
                                        transformation_type: str) -> Dict[str, Any]:
        """Perform additional semantic checks for transformations."""
        checks = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Check cross-cut preservation
        original_cross_cuts = self.cross_cut_validator.analyze_cross_cuts(original_graph)
        transformed_cross_cuts = self.cross_cut_validator.analyze_cross_cuts(transformed_graph)
        
        if transformation_type in ['iteration', 'deiteration', 'double_cut']:
            # These should preserve cross-cut structure
            if len(original_cross_cuts) != len(transformed_cross_cuts):
                checks['valid'] = False
                checks['issues'].append("Cross-cut structure not preserved")
        
        # Check interpretation consistency
        original_constants = {e.name for e in original_graph.entities.values() 
                            if e.entity_type == 'constant' and e.name}
        transformed_constants = {e.name for e in transformed_graph.entities.values() 
                               if e.entity_type == 'constant' and e.name}
        
        if transformation_type in ['insertion', 'erasure']:
            # New constants may be introduced or removed
            if transformed_constants - original_constants:
                checks['warnings'].append("New constants introduced - ensure proper interpretation")
        
        return checks
    
    # Helper methods
    
    def _find_predicate_context(self, graph: EGGraph, predicate_id: PredicateId) -> Optional[ContextId]:
        """Find which context contains a predicate."""
        for context in graph.context_manager.contexts.values():
            if predicate_id in context.contained_items:
                return context.id
        return None
    
    def _determine_context_polarity(self, graph: EGGraph, context_id: ContextId) -> str:
        """Determine if a context is positive or negative."""
        cut_count = 0
        current_context = graph.context_manager.get_context(context_id)
        
        while current_context and current_context.parent_context:
            if current_context.context_type == "cut":
                cut_count += 1
            current_context = graph.context_manager.get_context(current_context.parent_context)
        
        return "positive" if cut_count % 2 == 0 else "negative"

