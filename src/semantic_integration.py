"""
Unified semantic integration module for existential graphs.

This module provides a comprehensive semantic framework that integrates
function symbols, cross-cut validation, and semantic interpretation to
deliver complete Dau compliance for existential graph operations.
"""

from typing import Dict, Set, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from eg_types import (
    Entity, Predicate, Context, Ligature,
    EntityId, PredicateId, ContextId, LigatureId,
    pmap, pset, pvector
)
from graph import EGGraph
from semantic_interpreter import SemanticModel, SemanticInterpreter, create_finite_model
from semantic_evaluator import SemanticEvaluator, TruthEvaluationResult
from semantic_validator import SemanticValidator, SemanticValidationResult
from cross_cut_validator import CrossCutValidator
from transformations import TransformationEngine, TransformationType


@dataclass
class SemanticConfiguration:
    """Configuration for the semantic integration system."""
    
    enable_function_symbols: bool = True
    enable_cross_cut_validation: bool = True
    enable_semantic_validation: bool = True
    enable_transformation_semantics: bool = True
    strict_mode: bool = False  # If True, all semantic violations are errors
    
    # Model configuration
    default_domain_size: int = 10
    auto_generate_interpretations: bool = True
    require_complete_interpretations: bool = False


@dataclass
class SemanticAnalysisResult:
    """Complete semantic analysis result for an existential graph."""
    
    graph: EGGraph
    is_semantically_valid: bool
    truth_evaluation: TruthEvaluationResult
    validation_result: SemanticValidationResult
    cross_cut_analysis: Dict[str, Any]
    function_analysis: Dict[str, Any]
    recommendations: List[str]
    model_adequacy: Dict[str, Any]
    
    # Summary statistics
    entity_count: int
    predicate_count: int
    context_count: int
    function_count: int
    cross_cut_count: int
    violation_count: int
    warning_count: int


class SemanticFramework:
    """Unified semantic framework for existential graphs.
    
    Provides complete semantic analysis, validation, and transformation
    support with full Dau compliance.
    """
    
    def __init__(self, config: Optional[SemanticConfiguration] = None,
                 model: Optional[SemanticModel] = None):
        """Initialize the semantic framework.
        
        Args:
            config: Configuration for semantic analysis
            model: Semantic model for interpretation (optional)
        """
        self.config = config or SemanticConfiguration()
        
        # Initialize semantic components
        self.model = model or self._create_default_model()
        self.interpreter = SemanticInterpreter(self.model)
        self.evaluator = SemanticEvaluator(self.interpreter)
        self.validator = SemanticValidator(self.model)
        self.cross_cut_validator = CrossCutValidator()
        
        # Initialize transformation engine with semantic validation
        self.transformation_engine = TransformationEngine(
            semantic_validator=self.validator if self.config.enable_transformation_semantics else None
        )
        
        # Analysis cache
        self.analysis_cache = {}
    
    def set_model(self, model: SemanticModel) -> None:
        """Set the semantic model for the framework."""
        self.model = model
        self.interpreter.set_model(model)
        self.validator.set_model(model)
        self.analysis_cache.clear()
    
    def analyze_graph(self, graph: EGGraph) -> SemanticAnalysisResult:
        """Perform comprehensive semantic analysis of a graph.
        
        Args:
            graph: The existential graph to analyze
            
        Returns:
            SemanticAnalysisResult with complete analysis
        """
        # Check cache
        graph_hash = self._compute_graph_hash(graph)
        if graph_hash in self.analysis_cache:
            return self.analysis_cache[graph_hash]
        
        try:
            # 1. Truth evaluation
            truth_result = self.evaluator.evaluate_truth(graph)
            
            # 2. Semantic validation
            validation_result = self.validator.validate_semantic_consistency(graph)
            
            # 3. Cross-cut analysis (if enabled)
            cross_cut_analysis = {}
            if self.config.enable_cross_cut_validation:
                cross_cut_analysis = self._analyze_cross_cuts(graph)
            
            # 4. Function symbol analysis (if enabled)
            function_analysis = {}
            if self.config.enable_function_symbols:
                function_analysis = self._analyze_function_symbols(graph)
            
            # 5. Generate comprehensive recommendations
            recommendations = self._generate_comprehensive_recommendations(
                graph, truth_result, validation_result, cross_cut_analysis, function_analysis
            )
            
            # 6. Model adequacy assessment
            model_adequacy = self._assess_model_adequacy(graph)
            
            # 7. Determine overall semantic validity
            is_valid = self._determine_overall_validity(
                truth_result, validation_result, cross_cut_analysis, function_analysis
            )
            
            # Create result
            result = SemanticAnalysisResult(
                graph=graph,
                is_semantically_valid=is_valid,
                truth_evaluation=truth_result,
                validation_result=validation_result,
                cross_cut_analysis=cross_cut_analysis,
                function_analysis=function_analysis,
                recommendations=recommendations,
                model_adequacy=model_adequacy,
                entity_count=len(graph.entities),
                predicate_count=len(graph.predicates),
                context_count=len(graph.context_manager.contexts),
                function_count=function_analysis.get('function_count', 0),
                cross_cut_count=cross_cut_analysis.get('cross_cut_count', 0),
                violation_count=len([v for v in validation_result.violations if v.severity == 'error']),
                warning_count=len([v for v in validation_result.violations if v.severity == 'warning'])
            )
            
            # Cache result
            self.analysis_cache[graph_hash] = result
            
            return result
            
        except Exception as e:
            # Return error result
            return self._create_error_result(graph, str(e))
    
    def validate_transformation(self, original_graph: EGGraph, transformed_graph: EGGraph,
                              transformation_type: str) -> Dict[str, Any]:
        """Validate semantic consistency of a transformation.
        
        Args:
            original_graph: Original graph before transformation
            transformed_graph: Graph after transformation
            transformation_type: Type of transformation applied
            
        Returns:
            Dictionary with validation results
        """
        # Analyze both graphs
        original_analysis = self.analyze_graph(original_graph)
        transformed_analysis = self.analyze_graph(transformed_graph)
        
        # Semantic equivalence check
        equivalence_result = self.evaluator.evaluate_semantic_equivalence(
            original_graph, transformed_graph
        )
        
        # Transformation-specific validation
        transformation_validation = self.validator.validate_transformation_semantics(
            original_graph, transformed_graph, transformation_type
        )
        
        return {
            'original_analysis': original_analysis,
            'transformed_analysis': transformed_analysis,
            'semantic_equivalence': equivalence_result,
            'transformation_validation': transformation_validation,
            'semantics_preserved': transformation_validation['semantics_preserved'],
            'overall_valid': (
                transformation_validation['semantics_preserved'] and
                transformed_analysis.is_semantically_valid
            ),
            'changes': self._analyze_transformation_changes(original_analysis, transformed_analysis),
            'recommendations': self._generate_transformation_recommendations(
                original_analysis, transformed_analysis, transformation_validation
            )
        }
    
    def enhance_graph_semantics(self, graph: EGGraph) -> Tuple[EGGraph, Dict[str, Any]]:
        """Enhance a graph's semantic clarity and consistency.
        
        Args:
            graph: The graph to enhance
            
        Returns:
            Tuple of (enhanced_graph, enhancement_report)
        """
        enhancement_report = {
            'enhancements_applied': [],
            'issues_resolved': [],
            'remaining_issues': [],
            'recommendations': []
        }
        
        enhanced_graph = graph
        
        # Analyze current state
        analysis = self.analyze_graph(graph)
        
        # Apply automatic enhancements if configured
        if self.config.auto_generate_interpretations:
            enhanced_graph, interpretation_report = self._auto_generate_interpretations(enhanced_graph)
            enhancement_report['enhancements_applied'].extend(interpretation_report['added'])
            enhancement_report['issues_resolved'].extend(interpretation_report['resolved'])
        
        # Re-analyze after enhancements
        final_analysis = self.analyze_graph(enhanced_graph)
        
        # Generate recommendations for remaining issues
        enhancement_report['remaining_issues'] = [
            v.description for v in final_analysis.validation_result.violations
            if v.severity == 'error'
        ]
        enhancement_report['recommendations'] = final_analysis.recommendations
        
        return enhanced_graph, enhancement_report
    
    def generate_semantic_report(self, graph: EGGraph) -> Dict[str, Any]:
        """Generate a comprehensive semantic report for a graph.
        
        Args:
            graph: The graph to analyze
            
        Returns:
            Dictionary with complete semantic report
        """
        analysis = self.analyze_graph(graph)
        
        return {
            'summary': {
                'semantically_valid': analysis.is_semantically_valid,
                'truth_value': analysis.truth_evaluation.truth_value,
                'entity_count': analysis.entity_count,
                'predicate_count': analysis.predicate_count,
                'function_count': analysis.function_count,
                'cross_cut_count': analysis.cross_cut_count,
                'violation_count': analysis.violation_count,
                'warning_count': analysis.warning_count
            },
            'truth_evaluation': {
                'is_true': analysis.truth_evaluation.is_true,
                'truth_value': analysis.truth_evaluation.truth_value,
                'satisfying_assignments': len(analysis.truth_evaluation.satisfying_assignments),
                'quantification_scopes': len(analysis.truth_evaluation.quantification_analysis),
                'evaluation_steps': analysis.truth_evaluation.evaluation_steps
            },
            'validation': {
                'is_valid': analysis.validation_result.is_semantically_valid,
                'violations': [
                    {
                        'type': v.violation_type.value,
                        'description': v.description,
                        'severity': v.severity,
                        'suggested_fix': v.suggested_fix
                    }
                    for v in analysis.validation_result.violations
                ],
                'warnings': analysis.validation_result.warnings
            },
            'cross_cut_analysis': analysis.cross_cut_analysis,
            'function_analysis': analysis.function_analysis,
            'model_adequacy': analysis.model_adequacy,
            'recommendations': analysis.recommendations,
            'configuration': {
                'function_symbols_enabled': self.config.enable_function_symbols,
                'cross_cut_validation_enabled': self.config.enable_cross_cut_validation,
                'semantic_validation_enabled': self.config.enable_semantic_validation,
                'strict_mode': self.config.strict_mode
            }
        }
    
    # Private helper methods
    
    def _create_default_model(self) -> SemanticModel:
        """Create a default semantic model."""
        individuals = list(range(self.config.default_domain_size))
        return create_finite_model(individuals)
    
    def _compute_graph_hash(self, graph: EGGraph) -> str:
        """Compute a hash for the graph for caching purposes."""
        # Simple hash based on entity and predicate counts
        # In practice, this should be more sophisticated
        return f"{len(graph.entities)}_{len(graph.predicates)}_{len(graph.context_manager.contexts)}"
    
    def _analyze_cross_cuts(self, graph: EGGraph) -> Dict[str, Any]:
        """Analyze cross-cut ligatures in the graph."""
        cross_cuts = self.cross_cut_validator.analyze_cross_cuts(graph)
        identity_result = self.cross_cut_validator.validate_identity_preservation(graph)
        
        return {
            'cross_cuts': cross_cuts,
            'cross_cut_count': len(cross_cuts),
            'identity_preserved': identity_result.is_preserved,
            'violations': identity_result.violations,
            'warnings': identity_result.warnings
        }
    
    def _analyze_function_symbols(self, graph: EGGraph) -> Dict[str, Any]:
        """Analyze function symbols in the graph."""
        function_predicates = [
            p for p in graph.predicates.values()
            if hasattr(p, 'predicate_type') and p.predicate_type == 'function'
        ]
        
        function_analysis = {
            'function_count': len(function_predicates),
            'functions': [],
            'issues': []
        }
        
        for predicate in function_predicates:
            function_info = {
                'name': predicate.name,
                'arity': predicate.arity,
                'has_interpretation': bool(self.model.domain.get_function(predicate.name)),
                'return_entity': getattr(predicate, 'return_entity', None)
            }
            
            if not function_info['has_interpretation']:
                function_analysis['issues'].append(f"Function '{predicate.name}' has no interpretation")
            
            function_analysis['functions'].append(function_info)
        
        return function_analysis
    
    def _generate_comprehensive_recommendations(self, graph: EGGraph, truth_result: TruthEvaluationResult,
                                              validation_result: SemanticValidationResult,
                                              cross_cut_analysis: Dict[str, Any],
                                              function_analysis: Dict[str, Any]) -> List[str]:
        """Generate comprehensive recommendations for improving the graph."""
        recommendations = []
        
        # From validation result
        recommendations.extend(validation_result.recommendations)
        
        # From truth evaluation
        if not truth_result.is_true:
            recommendations.append("Graph is not true in current model - consider revising")
        
        # From cross-cut analysis
        if cross_cut_analysis and not cross_cut_analysis.get('identity_preserved', True):
            recommendations.append("Cross-cut identity violations detected - review ligature structure")
        
        # From function analysis
        if function_analysis and function_analysis.get('issues'):
            recommendations.append("Function symbol issues detected - add missing interpretations")
        
        # General recommendations
        if len(graph.entities) == 0:
            recommendations.append("Add entities to make the graph meaningful")
        
        if len(graph.predicates) == 0:
            recommendations.append("Add predicates to express relationships")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _assess_model_adequacy(self, graph: EGGraph) -> Dict[str, Any]:
        """Assess whether the current model is adequate for the graph."""
        return self.validator._analyze_model_adequacy(graph)
    
    def _determine_overall_validity(self, truth_result: TruthEvaluationResult,
                                  validation_result: SemanticValidationResult,
                                  cross_cut_analysis: Dict[str, Any],
                                  function_analysis: Dict[str, Any]) -> bool:
        """Determine overall semantic validity."""
        # In strict mode, any error makes the graph invalid
        if self.config.strict_mode:
            has_errors = any(v.severity == 'error' for v in validation_result.violations)
            return not has_errors and validation_result.is_semantically_valid
        
        # In normal mode, focus on critical errors
        critical_errors = [
            v for v in validation_result.violations
            if v.severity == 'error' and v.violation_type.value in [
                'logical_contradiction', 'domain_violation', 'function_arity_error'
            ]
        ]
        
        return len(critical_errors) == 0 and validation_result.is_semantically_valid
    
    def _create_error_result(self, graph: EGGraph, error_message: str) -> SemanticAnalysisResult:
        """Create an error result for failed analysis."""
        from semantic_evaluator import TruthEvaluationResult
        from semantic_validator import SemanticValidationResult, SemanticViolation, SemanticViolationType
        
        error_violation = SemanticViolation(
            violation_type=SemanticViolationType.DOMAIN_VIOLATION,
            description=f"Analysis error: {error_message}",
            affected_elements=set(),
            severity='error'
        )
        
        return SemanticAnalysisResult(
            graph=graph,
            is_semantically_valid=False,
            truth_evaluation=TruthEvaluationResult(
                is_true=False, truth_value=None, satisfying_assignments=[],
                quantification_analysis=[], evaluation_steps=[],
                semantic_errors=[error_message], warnings=[], model_dependencies=set()
            ),
            validation_result=SemanticValidationResult(
                is_semantically_valid=False, violations=[error_violation],
                warnings=[], recommendations=[], truth_evaluation=None,
                cross_cut_analysis=None, model_adequacy={'adequate': False},
                validation_summary={'status': 'error'}
            ),
            cross_cut_analysis={},
            function_analysis={},
            recommendations=[f"Fix analysis error: {error_message}"],
            model_adequacy={'adequate': False},
            entity_count=len(graph.entities),
            predicate_count=len(graph.predicates),
            context_count=len(graph.context_manager.contexts),
            function_count=0,
            cross_cut_count=0,
            violation_count=1,
            warning_count=0
        )
    
    def _analyze_transformation_changes(self, original: SemanticAnalysisResult,
                                      transformed: SemanticAnalysisResult) -> Dict[str, Any]:
        """Analyze changes between original and transformed graphs."""
        return {
            'entity_count_change': transformed.entity_count - original.entity_count,
            'predicate_count_change': transformed.predicate_count - original.predicate_count,
            'context_count_change': transformed.context_count - original.context_count,
            'function_count_change': transformed.function_count - original.function_count,
            'truth_value_change': (
                original.truth_evaluation.truth_value,
                transformed.truth_evaluation.truth_value
            ),
            'validity_change': (
                original.is_semantically_valid,
                transformed.is_semantically_valid
            )
        }
    
    def _generate_transformation_recommendations(self, original: SemanticAnalysisResult,
                                               transformed: SemanticAnalysisResult,
                                               transformation_validation: Dict[str, Any]) -> List[str]:
        """Generate recommendations for transformation results."""
        recommendations = []
        
        if not transformation_validation['semantics_preserved']:
            recommendations.append("Transformation did not preserve semantics - review transformation rules")
        
        if not transformed.is_semantically_valid:
            recommendations.append("Transformed graph is not semantically valid - address violations")
        
        if transformed.violation_count > original.violation_count:
            recommendations.append("Transformation introduced new semantic violations")
        
        return recommendations
    
    def _auto_generate_interpretations(self, graph: EGGraph) -> Tuple[EGGraph, Dict[str, Any]]:
        """Automatically generate interpretations for uninterpreted symbols."""
        report = {
            'added': [],
            'resolved': []
        }
        
        # For now, return the graph unchanged
        # In a full implementation, this would add interpretations to the model
        return graph, report


# Convenience functions for common use cases

def create_semantic_framework(domain_individuals: List[Any] = None,
                            enable_functions: bool = True,
                            enable_cross_cuts: bool = True) -> SemanticFramework:
    """Create a semantic framework with common configuration.
    
    Args:
        domain_individuals: List of individuals for the domain
        enable_functions: Whether to enable function symbol support
        enable_cross_cuts: Whether to enable cross-cut validation
        
    Returns:
        Configured SemanticFramework
    """
    config = SemanticConfiguration(
        enable_function_symbols=enable_functions,
        enable_cross_cut_validation=enable_cross_cuts,
        enable_semantic_validation=True,
        enable_transformation_semantics=True
    )
    
    if domain_individuals:
        model = create_finite_model(domain_individuals)
    else:
        model = None
    
    return SemanticFramework(config, model)


def analyze_graph_semantics(graph: EGGraph, model: SemanticModel = None) -> SemanticAnalysisResult:
    """Quick semantic analysis of a graph.
    
    Args:
        graph: The graph to analyze
        model: Optional semantic model
        
    Returns:
        SemanticAnalysisResult
    """
    framework = SemanticFramework(model=model)
    return framework.analyze_graph(graph)


def validate_graph_transformation(original: EGGraph, transformed: EGGraph,
                                transformation_type: str,
                                model: SemanticModel = None) -> Dict[str, Any]:
    """Quick validation of a graph transformation.
    
    Args:
        original: Original graph
        transformed: Transformed graph
        transformation_type: Type of transformation
        model: Optional semantic model
        
    Returns:
        Validation results
    """
    framework = SemanticFramework(model=model)
    return framework.validate_transformation(original, transformed, transformation_type)

