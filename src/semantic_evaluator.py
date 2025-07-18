"""
Satisfaction conditions and truth evaluation system for existential graphs.

This module implements the formal satisfaction conditions following Dau's 
model-theoretic semantics, providing complete truth evaluation for existential 
graphs with proper handling of quantification, negation, and function symbols.
"""

from typing import Dict, Set, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import itertools

from .eg_types import (
    Entity, Predicate, Context, Ligature,
    EntityId, PredicateId, ContextId, LigatureId,
    pmap, pset, pvector
)
from .graph import EGGraph
from .semantic_interpreter import (
    SemanticModel, VariableAssignment, SatisfactionResult,
    SemanticInterpreter
)


class QuantifierType(Enum):
    """Types of quantification in existential graphs."""
    EXISTENTIAL = "existential"
    UNIVERSAL = "universal"  # Represented as negated existential


@dataclass(frozen=True)
class QuantificationScope:
    """Represents a quantification scope in the graph.
    
    In existential graphs, quantification is implicit through the structure:
    - Variables in positive contexts are existentially quantified
    - Variables in negative contexts represent universal quantification
    """
    
    variables: pset  # Set of variable names
    quantifier_type: QuantifierType
    context_id: ContextId
    scope_depth: int
    
    @classmethod
    def create_existential(cls, variables: Set[str], context_id: ContextId, depth: int) -> 'QuantificationScope':
        """Create an existential quantification scope."""
        return cls(
            variables=pset(variables),
            quantifier_type=QuantifierType.EXISTENTIAL,
            context_id=context_id,
            scope_depth=depth
        )
    
    @classmethod
    def create_universal(cls, variables: Set[str], context_id: ContextId, depth: int) -> 'QuantificationScope':
        """Create a universal quantification scope."""
        return cls(
            variables=pset(variables),
            quantifier_type=QuantifierType.UNIVERSAL,
            context_id=context_id,
            scope_depth=depth
        )


@dataclass
class TruthEvaluationResult:
    """Complete result of truth evaluation for an existential graph."""
    
    is_true: bool
    truth_value: Optional[bool]
    satisfying_assignments: List[VariableAssignment]
    quantification_analysis: List[QuantificationScope]
    evaluation_steps: List[str]
    semantic_errors: List[str]
    warnings: List[str]
    model_dependencies: Set[str]  # Which model elements were used


class SemanticEvaluator:
    """Advanced semantic evaluator with formal satisfaction conditions.
    
    Implements Dau's formal semantics for existential graphs including:
    - Proper quantification handling
    - Context polarity semantics
    - Function symbol evaluation
    - Ligature identity preservation
    - Complete truth evaluation
    """
    
    def __init__(self, interpreter: SemanticInterpreter):
        """Initialize the semantic evaluator."""
        self.interpreter = interpreter
        self.evaluation_cache = {}
        self.quantification_cache = {}
    
    def evaluate_truth(self, graph: EGGraph, 
                      assignment: Optional[VariableAssignment] = None) -> TruthEvaluationResult:
        """Perform complete truth evaluation of an existential graph.
        
        Args:
            graph: The existential graph to evaluate
            assignment: Initial variable assignment (optional)
            
        Returns:
            TruthEvaluationResult with complete evaluation details
        """
        if assignment is None:
            assignment = VariableAssignment.create_empty()
        
        try:
            # Analyze quantification structure
            quantification_analysis = self._analyze_quantification_structure(graph)
            
            # Perform satisfaction evaluation
            satisfaction_result = self.interpreter.satisfies(graph, assignment)
            
            # Determine truth value based on satisfaction and quantification
            truth_result = self._determine_truth_value(
                graph, satisfaction_result, quantification_analysis
            )
            
            # Analyze model dependencies
            model_deps = self._analyze_model_dependencies(graph)
            
            return TruthEvaluationResult(
                is_true=truth_result['is_true'],
                truth_value=truth_result['truth_value'],
                satisfying_assignments=satisfaction_result.variable_assignments,
                quantification_analysis=quantification_analysis,
                evaluation_steps=satisfaction_result.evaluation_trace + truth_result['steps'],
                semantic_errors=satisfaction_result.errors,
                warnings=satisfaction_result.warnings + truth_result.get('warnings', []),
                model_dependencies=model_deps
            )
            
        except Exception as e:
            return TruthEvaluationResult(
                is_true=False,
                truth_value=None,
                satisfying_assignments=[],
                quantification_analysis=[],
                evaluation_steps=[],
                semantic_errors=[f"Evaluation error: {str(e)}"],
                warnings=[],
                model_dependencies=set()
            )
    
    def _analyze_quantification_structure(self, graph: EGGraph) -> List[QuantificationScope]:
        """Analyze the quantification structure of the graph.
        
        In existential graphs:
        - Variables in positive contexts are existentially quantified
        - Variables in negative contexts (cuts) represent universal quantification
        - Nested cuts alternate quantification types
        """
        quantification_scopes = []
        
        # Analyze each context
        for context in graph.context_manager.contexts.values():
            variables_in_context = self._get_variables_in_context(graph, context.id)
            
            if variables_in_context:
                # Determine quantification type based on context polarity
                context_polarity = self._determine_context_polarity(graph, context.id)
                
                if context_polarity == "positive":
                    scope = QuantificationScope.create_existential(
                        variables_in_context, context.id, context.depth
                    )
                else:
                    scope = QuantificationScope.create_universal(
                        variables_in_context, context.id, context.depth
                    )
                
                quantification_scopes.append(scope)
        
        # Sort by scope depth for proper nesting
        quantification_scopes.sort(key=lambda s: s.scope_depth)
        
        return quantification_scopes
    
    def _determine_context_polarity(self, graph: EGGraph, context_id: ContextId) -> str:
        """Determine the polarity (positive/negative) of a context.
        
        The polarity depends on the number of cuts (negative contexts) 
        in the path from root to this context.
        """
        cut_count = 0
        current_context = graph.context_manager.get_context(context_id)
        
        while current_context and current_context.parent_context:
            if current_context.context_type == "cut":
                cut_count += 1
            current_context = graph.context_manager.get_context(current_context.parent_context)
        
        # Even number of cuts = positive, odd number = negative
        return "positive" if cut_count % 2 == 0 else "negative"
    
    def _get_variables_in_context(self, graph: EGGraph, context_id: ContextId) -> Set[str]:
        """Get all variables that appear in a specific context."""
        variables = set()
        
        # Get predicates in this context
        context = graph.context_manager.get_context(context_id)
        if not context:
            return variables
        
        for item_id in context.contained_items:
            if item_id in graph.predicates:
                predicate = graph.predicates[item_id]
                for entity_id in predicate.entities:
                    entity = graph.entities.get(entity_id)
                    if entity and entity.entity_type == 'variable' and entity.name:
                        variables.add(entity.name)
        
        return variables
    
    def _determine_truth_value(self, graph: EGGraph, satisfaction_result: SatisfactionResult,
                              quantification_analysis: List[QuantificationScope]) -> Dict[str, Any]:
        """Determine the truth value based on satisfaction and quantification structure."""
        steps = []
        warnings = []
        
        if not satisfaction_result.is_satisfied:
            steps.append("Graph is not satisfied in the model")
            return {
                'is_true': False,
                'truth_value': False,
                'steps': steps,
                'warnings': warnings
            }
        
        # Analyze quantification requirements
        if not quantification_analysis:
            # No quantification - simple satisfaction
            steps.append("No quantification - truth value equals satisfaction")
            return {
                'is_true': satisfaction_result.is_satisfied,
                'truth_value': satisfaction_result.truth_value,
                'steps': steps,
                'warnings': warnings
            }
        
        # Check if all quantification requirements are met
        truth_value = self._evaluate_quantified_formula(
            graph, satisfaction_result, quantification_analysis, steps
        )
        
        return {
            'is_true': truth_value,
            'truth_value': truth_value,
            'steps': steps,
            'warnings': warnings
        }
    
    def _evaluate_quantified_formula(self, graph: EGGraph, satisfaction_result: SatisfactionResult,
                                   quantification_analysis: List[QuantificationScope],
                                   steps: List[str]) -> bool:
        """Evaluate a quantified formula according to existential graph semantics."""
        
        # For existential graphs, the truth conditions are:
        # - Existential quantification: ∃x φ(x) is true if there exists an assignment that satisfies φ
        # - Universal quantification: ∀x φ(x) is true if all assignments satisfy φ
        
        steps.append("Evaluating quantified formula")
        
        # Check if we have satisfying assignments
        if not satisfaction_result.variable_assignments:
            steps.append("No satisfying assignments found")
            return False
        
        # Analyze quantification requirements
        for scope in quantification_analysis:
            steps.append(f"Checking {scope.quantifier_type.value} quantification for variables {scope.variables}")
            
            if scope.quantifier_type == QuantifierType.EXISTENTIAL:
                # Existential: need at least one satisfying assignment
                has_satisfying_assignment = any(
                    all(assignment.contains(var) for var in scope.variables)
                    for assignment in satisfaction_result.variable_assignments
                )
                
                if not has_satisfying_assignment:
                    steps.append(f"Existential quantification failed for {scope.variables}")
                    return False
                else:
                    steps.append(f"Existential quantification satisfied for {scope.variables}")
            
            elif scope.quantifier_type == QuantifierType.UNIVERSAL:
                # Universal: need to check all possible assignments
                # This is more complex and requires checking against the full domain
                universal_satisfied = self._check_universal_quantification(
                    graph, scope, steps
                )
                
                if not universal_satisfied:
                    steps.append(f"Universal quantification failed for {scope.variables}")
                    return False
                else:
                    steps.append(f"Universal quantification satisfied for {scope.variables}")
        
        steps.append("All quantification requirements satisfied")
        return True
    
    def _check_universal_quantification(self, graph: EGGraph, scope: QuantificationScope,
                                      steps: List[str]) -> bool:
        """Check universal quantification by testing all domain assignments."""
        
        # Get all possible assignments for the universally quantified variables
        domain_individuals = list(self.interpreter.model.domain.individuals)
        
        if not domain_individuals:
            steps.append("Empty domain - universal quantification vacuously true")
            return True
        
        # Generate all possible assignments for the variables in scope
        variables = list(scope.variables)
        
        if not variables:
            steps.append("No variables in universal scope")
            return True
        
        # Test all possible assignments
        all_assignments_satisfy = True
        tested_count = 0
        
        for assignment_values in itertools.product(domain_individuals, repeat=len(variables)):
            # Create assignment
            test_assignment = VariableAssignment.create_empty()
            for var, value in zip(variables, assignment_values):
                test_assignment = test_assignment.assign(var, value)
            
            # Test satisfaction with this assignment
            test_result = self.interpreter.satisfies(graph, test_assignment)
            tested_count += 1
            
            if not test_result.is_satisfied:
                steps.append(f"Universal quantification failed for assignment {dict(zip(variables, assignment_values))}")
                all_assignments_satisfy = False
                break
        
        steps.append(f"Tested {tested_count} assignments for universal quantification")
        
        if all_assignments_satisfy:
            steps.append("All assignments satisfy universal quantification")
        
        return all_assignments_satisfy
    
    def _analyze_model_dependencies(self, graph: EGGraph) -> Set[str]:
        """Analyze which model elements the graph depends on."""
        dependencies = set()
        
        # Add constant interpretations
        for entity in graph.entities.values():
            if entity.entity_type == 'constant' and entity.name:
                dependencies.add(f"constant:{entity.name}")
        
        # Add predicate interpretations
        for predicate in graph.predicates.values():
            dependencies.add(f"predicate:{predicate.name}")
        
        # Add domain individuals (implicitly)
        dependencies.add("domain:individuals")
        
        return dependencies
    
    def evaluate_semantic_equivalence(self, graph1: EGGraph, graph2: EGGraph) -> Dict[str, Any]:
        """Evaluate semantic equivalence between two graphs.
        
        Two graphs are semantically equivalent if they have the same truth value
        in all possible models.
        """
        result1 = self.evaluate_truth(graph1)
        result2 = self.evaluate_truth(graph2)
        
        # Basic equivalence check (same truth value in current model)
        basic_equivalent = result1.truth_value == result2.truth_value
        
        # Analyze structural differences
        structural_analysis = self._analyze_structural_differences(graph1, graph2)
        
        return {
            'are_equivalent': basic_equivalent,
            'truth_value_1': result1.truth_value,
            'truth_value_2': result2.truth_value,
            'structural_differences': structural_analysis,
            'evaluation_1': result1,
            'evaluation_2': result2,
            'equivalence_confidence': 'high' if basic_equivalent else 'low'
        }
    
    def _analyze_structural_differences(self, graph1: EGGraph, graph2: EGGraph) -> Dict[str, Any]:
        """Analyze structural differences between two graphs."""
        differences = {
            'entity_count_diff': len(graph1.entities) - len(graph2.entities),
            'predicate_count_diff': len(graph1.predicates) - len(graph2.predicates),
            'context_count_diff': len(graph1.context_manager.contexts) - len(graph2.context_manager.contexts),
            'unique_entities_1': set(),
            'unique_entities_2': set(),
            'unique_predicates_1': set(),
            'unique_predicates_2': set()
        }
        
        # Find unique entities
        entities_1 = {(e.name, e.entity_type) for e in graph1.entities.values() if e.name}
        entities_2 = {(e.name, e.entity_type) for e in graph2.entities.values() if e.name}
        
        differences['unique_entities_1'] = entities_1 - entities_2
        differences['unique_entities_2'] = entities_2 - entities_1
        
        # Find unique predicates
        predicates_1 = {(p.name, p.arity) for p in graph1.predicates.values()}
        predicates_2 = {(p.name, p.arity) for p in graph2.predicates.values()}
        
        differences['unique_predicates_1'] = predicates_1 - predicates_2
        differences['unique_predicates_2'] = predicates_2 - predicates_1
        
        return differences
    
    def validate_transformation_semantics(self, original_graph: EGGraph, 
                                        transformed_graph: EGGraph,
                                        transformation_type: str) -> Dict[str, Any]:
        """Validate that a transformation preserves semantic meaning.
        
        Args:
            original_graph: The original graph before transformation
            transformed_graph: The graph after transformation
            transformation_type: Type of transformation applied
            
        Returns:
            Dictionary with semantic validation results
        """
        # Evaluate both graphs
        original_result = self.evaluate_truth(original_graph)
        transformed_result = self.evaluate_truth(transformed_graph)
        
        # Check semantic preservation based on transformation type
        preservation_analysis = self._analyze_semantic_preservation(
            original_result, transformed_result, transformation_type
        )
        
        return {
            'semantics_preserved': preservation_analysis['preserved'],
            'original_truth_value': original_result.truth_value,
            'transformed_truth_value': transformed_result.truth_value,
            'preservation_analysis': preservation_analysis,
            'transformation_type': transformation_type,
            'semantic_changes': preservation_analysis.get('changes', []),
            'warnings': preservation_analysis.get('warnings', [])
        }
    
    def _analyze_semantic_preservation(self, original_result: TruthEvaluationResult,
                                     transformed_result: TruthEvaluationResult,
                                     transformation_type: str) -> Dict[str, Any]:
        """Analyze whether semantic meaning is preserved across transformation."""
        
        analysis = {
            'preserved': True,
            'changes': [],
            'warnings': []
        }
        
        # Check truth value preservation
        if original_result.truth_value != transformed_result.truth_value:
            if transformation_type in ['insertion', 'erasure']:
                # These transformations can change truth values
                analysis['changes'].append(f"Truth value changed: {original_result.truth_value} -> {transformed_result.truth_value}")
            elif transformation_type in ['iteration', 'deiteration', 'double_cut']:
                # These should preserve truth values
                analysis['preserved'] = False
                analysis['changes'].append(f"Truth value incorrectly changed: {original_result.truth_value} -> {transformed_result.truth_value}")
        
        # Check quantification structure preservation
        original_quantification = {(s.quantifier_type, tuple(s.variables)) for s in original_result.quantification_analysis}
        transformed_quantification = {(s.quantifier_type, tuple(s.variables)) for s in transformed_result.quantification_analysis}
        
        if original_quantification != transformed_quantification:
            if transformation_type in ['iteration', 'deiteration']:
                # These can change quantification structure
                analysis['changes'].append("Quantification structure changed")
            else:
                analysis['warnings'].append("Unexpected quantification structure change")
        
        # Check model dependencies
        if original_result.model_dependencies != transformed_result.model_dependencies:
            analysis['changes'].append("Model dependencies changed")
        
        return analysis
    
    def generate_semantic_report(self, graph: EGGraph) -> Dict[str, Any]:
        """Generate a comprehensive semantic analysis report for a graph."""
        
        # Perform truth evaluation
        truth_result = self.evaluate_truth(graph)
        
        # Analyze semantic consistency
        consistency_result = self.interpreter.validate_semantic_consistency(graph)
        
        # Generate summary statistics
        stats = {
            'entity_count': len(graph.entities),
            'predicate_count': len(graph.predicates),
            'context_count': len(graph.context_manager.contexts),
            'variable_count': len([e for e in graph.entities.values() if e.entity_type == 'variable']),
            'constant_count': len([e for e in graph.entities.values() if e.entity_type == 'constant']),
            'quantification_scopes': len(truth_result.quantification_analysis)
        }
        
        return {
            'truth_evaluation': truth_result,
            'semantic_consistency': consistency_result,
            'statistics': stats,
            'model_coverage': {
                'interpreted_constants': len([e for e in graph.entities.values() 
                                            if e.entity_type == 'constant' and e.name and 
                                            self.interpreter.model.interpret_constant(e.name)]),
                'interpreted_predicates': len([p for p in graph.predicates.values() 
                                             if self.interpreter.model.interpret_predicate(p.name)]),
                'total_constants': len([e for e in graph.entities.values() if e.entity_type == 'constant']),
                'total_predicates': len(graph.predicates)
            },
            'recommendations': self._generate_semantic_recommendations(truth_result, consistency_result)
        }
    
    def _generate_semantic_recommendations(self, truth_result: TruthEvaluationResult,
                                         consistency_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving semantic clarity."""
        recommendations = []
        
        if not truth_result.is_true:
            recommendations.append("Graph is not true in current model - consider revising graph or model")
        
        if truth_result.semantic_errors:
            recommendations.append("Resolve semantic errors for proper evaluation")
        
        if not consistency_result['is_consistent']:
            recommendations.append("Address semantic consistency violations")
        
        if consistency_result['warnings']:
            recommendations.append("Consider adding interpretations for uninterpreted symbols")
        
        if not truth_result.quantification_analysis:
            recommendations.append("Consider adding quantified variables for more expressive power")
        
        return recommendations

