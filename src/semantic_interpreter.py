"""
Comprehensive semantic interpretation layer for existential graphs.

This module implements model-theoretic semantics following Dau's formal framework,
providing domain structures, interpretation mappings, and satisfaction conditions
for complete semantic validation of existential graphs.
"""

from typing import Dict, Set, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import uuid

from eg_types import (
    Entity, Predicate, Context, Ligature,
    EntityId, PredicateId, ContextId, LigatureId,
    pmap, pset, pvector
)
from graph import EGGraph


class SemanticValueType(Enum):
    """Types of semantic values in the domain."""
    INDIVIDUAL = "individual"
    RELATION = "relation"
    FUNCTION = "function"
    PROPOSITION = "proposition"


@dataclass(frozen=True)
class SemanticDomain:
    """Represents a semantic domain for interpretation.
    
    A domain consists of:
    - A set of individuals (domain objects)
    - Relations over the domain
    - Functions from domain tuples to domain objects
    - Truth values for propositions
    """
    
    individuals: pset  # Set of domain objects
    relations: pmap    # Dict[str, Set[Tuple]] - relation name to extension
    functions: pmap    # Dict[str, Callable] - function name to implementation
    propositions: pmap # Dict[str, bool] - proposition name to truth value
    
    @classmethod
    def create_empty(cls) -> 'SemanticDomain':
        """Create an empty semantic domain."""
        return cls(
            individuals=pset(),
            relations=pmap(),
            functions=pmap(),
            propositions=pmap()
        )
    
    @classmethod
    def create_standard(cls, individuals: Set[Any]) -> 'SemanticDomain':
        """Create a standard domain with basic relations."""
        return cls(
            individuals=pset(individuals),
            relations=pmap({
                'identity': {(x, x) for x in individuals},
                'distinct': {(x, y) for x in individuals for y in individuals if x != y}
            }),
            functions=pmap(),
            propositions=pmap()
        )
    
    def add_individual(self, individual: Any) -> 'SemanticDomain':
        """Add an individual to the domain."""
        new_individuals = self.individuals.add(individual)
        return self.set('individuals', new_individuals)
    
    def add_relation(self, name: str, extension: Set[Tuple]) -> 'SemanticDomain':
        """Add a relation to the domain."""
        new_relations = self.relations.set(name, extension)
        return self.set('relations', new_relations)
    
    def add_function(self, name: str, implementation: Callable) -> 'SemanticDomain':
        """Add a function to the domain."""
        new_functions = self.functions.set(name, implementation)
        return self.set('functions', new_functions)
    
    def add_proposition(self, name: str, truth_value: bool) -> 'SemanticDomain':
        """Add a proposition to the domain."""
        new_propositions = self.propositions.set(name, truth_value)
        return self.set('propositions', new_propositions)
    
    def set(self, field_name: str, value: Any) -> 'SemanticDomain':
        """Return a new domain with the specified field updated."""
        if field_name == 'individuals':
            return SemanticDomain(value, self.relations, self.functions, self.propositions)
        elif field_name == 'relations':
            return SemanticDomain(self.individuals, value, self.functions, self.propositions)
        elif field_name == 'functions':
            return SemanticDomain(self.individuals, self.relations, value, self.propositions)
        elif field_name == 'propositions':
            return SemanticDomain(self.individuals, self.relations, self.functions, value)
        else:
            raise ValueError(f"Unknown field: {field_name}")
    
    def get_relation_extension(self, name: str) -> Set[Tuple]:
        """Get the extension of a relation."""
        return self.relations.get(name, set())
    
    def get_function(self, name: str) -> Optional[Callable]:
        """Get a function implementation."""
        return self.functions.get(name)
    
    def get_proposition_value(self, name: str) -> Optional[bool]:
        """Get the truth value of a proposition."""
        return self.propositions.get(name)
    
    def contains_individual(self, individual: Any) -> bool:
        """Check if an individual is in the domain."""
        return individual in self.individuals


@dataclass(frozen=True)
class VariableAssignment:
    """Represents a variable assignment for semantic evaluation.
    
    Maps variable names to domain individuals.
    """
    
    assignment: pmap  # Dict[str, Any] - variable name to domain individual
    
    @classmethod
    def create_empty(cls) -> 'VariableAssignment':
        """Create an empty variable assignment."""
        return cls(assignment=pmap())
    
    def assign(self, variable: str, individual: Any) -> 'VariableAssignment':
        """Return a new assignment with the variable bound to the individual."""
        new_assignment = self.assignment.set(variable, individual)
        return VariableAssignment(new_assignment)
    
    def get(self, variable: str) -> Optional[Any]:
        """Get the assignment for a variable."""
        return self.assignment.get(variable)
    
    def contains(self, variable: str) -> bool:
        """Check if a variable is assigned."""
        return variable in self.assignment
    
    def extend(self, other: 'VariableAssignment') -> 'VariableAssignment':
        """Extend this assignment with another assignment."""
        new_assignment = self.assignment.update(other.assignment)
        return VariableAssignment(new_assignment)


@dataclass(frozen=True)
class SemanticModel:
    """Complete semantic model for existential graph interpretation.
    
    Combines a domain with interpretation mappings for predicates and constants.
    """
    
    domain: SemanticDomain
    constant_interpretation: pmap  # Dict[str, Any] - constant name to domain individual
    predicate_interpretation: pmap # Dict[str, str] - predicate name to relation/function name
    
    @classmethod
    def create_empty(cls) -> 'SemanticModel':
        """Create an empty semantic model."""
        return cls(
            domain=SemanticDomain.create_empty(),
            constant_interpretation=pmap(),
            predicate_interpretation=pmap()
        )
    
    @classmethod
    def create_standard(cls, individuals: Set[Any]) -> 'SemanticModel':
        """Create a standard model with basic interpretations."""
        domain = SemanticDomain.create_standard(individuals)
        return cls(
            domain=domain,
            constant_interpretation=pmap(),
            predicate_interpretation=pmap({
                '=': 'identity',
                '≠': 'distinct'
            })
        )
    
    def interpret_constant(self, constant_name: str) -> Optional[Any]:
        """Get the interpretation of a constant."""
        return self.constant_interpretation.get(constant_name)
    
    def interpret_predicate(self, predicate_name: str) -> Optional[str]:
        """Get the domain relation/function name for a predicate."""
        return self.predicate_interpretation.get(predicate_name)
    
    def add_constant_interpretation(self, constant_name: str, individual: Any) -> 'SemanticModel':
        """Add an interpretation for a constant."""
        if not self.domain.contains_individual(individual):
            raise ValueError(f"Individual {individual} not in domain")
        
        new_constants = self.constant_interpretation.set(constant_name, individual)
        return SemanticModel(self.domain, new_constants, self.predicate_interpretation)
    
    def add_predicate_interpretation(self, predicate_name: str, domain_relation: str) -> 'SemanticModel':
        """Add an interpretation for a predicate."""
        new_predicates = self.predicate_interpretation.set(predicate_name, domain_relation)
        return SemanticModel(self.domain, self.constant_interpretation, new_predicates)
    
    def extend_domain(self, new_domain: SemanticDomain) -> 'SemanticModel':
        """Return a model with an extended domain."""
        return SemanticModel(new_domain, self.constant_interpretation, self.predicate_interpretation)


@dataclass
class SatisfactionResult:
    """Result of semantic satisfaction evaluation."""
    is_satisfied: bool
    truth_value: Optional[bool]
    variable_assignments: List[VariableAssignment]
    evaluation_trace: List[str]
    errors: List[str]
    warnings: List[str]


class SemanticInterpreter:
    """Main semantic interpreter for existential graphs.
    
    Provides model-theoretic semantics following Dau's framework.
    """
    
    def __init__(self, model: Optional[SemanticModel] = None):
        """Initialize the semantic interpreter."""
        self.model = model or SemanticModel.create_empty()
        self.evaluation_cache = {}
    
    def set_model(self, model: SemanticModel) -> None:
        """Set the semantic model for interpretation."""
        self.model = model
        self.evaluation_cache.clear()
    
    def satisfies(self, graph: EGGraph, assignment: Optional[VariableAssignment] = None) -> SatisfactionResult:
        """Check if the graph is satisfied in the current model.
        
        Args:
            graph: The existential graph to evaluate
            assignment: Variable assignment (optional)
            
        Returns:
            SatisfactionResult with satisfaction status and details
        """
        if assignment is None:
            assignment = VariableAssignment.create_empty()
        
        try:
            # Evaluate the root context (sheet of assertion)
            root_context = graph.context_manager.root_context
            result = self._evaluate_context(graph, root_context.id, assignment)
            
            return SatisfactionResult(
                is_satisfied=result['satisfied'],
                truth_value=result['truth_value'],
                variable_assignments=result['assignments'],
                evaluation_trace=result['trace'],
                errors=[],
                warnings=result.get('warnings', [])
            )
            
        except Exception as e:
            return SatisfactionResult(
                is_satisfied=False,
                truth_value=None,
                variable_assignments=[],
                evaluation_trace=[],
                errors=[f"Evaluation error: {str(e)}"],
                warnings=[]
            )
    
    def _evaluate_context(self, graph: EGGraph, context_id: ContextId, 
                         assignment: VariableAssignment) -> Dict[str, Any]:
        """Evaluate a context in the graph.
        
        Args:
            graph: The existential graph
            context_id: ID of the context to evaluate
            assignment: Current variable assignment
            
        Returns:
            Dictionary with evaluation results
        """
        context = graph.context_manager.get_context(context_id)
        if not context:
            raise ValueError(f"Context {context_id} not found")
        
        trace = [f"Evaluating context {context_id} (type: {context.context_type})"]
        
        # Get predicates in this context
        predicates_in_context = self._get_predicates_in_context(graph, context_id)
        
        # Evaluate based on context type
        if context.context_type == "cut":
            # Negative context - evaluate as negation
            return self._evaluate_negative_context(graph, context_id, assignment, trace)
        else:
            # Positive context - evaluate as conjunction
            return self._evaluate_positive_context(graph, context_id, assignment, trace)
    
    def _evaluate_positive_context(self, graph: EGGraph, context_id: ContextId,
                                  assignment: VariableAssignment, trace: List[str]) -> Dict[str, Any]:
        """Evaluate a positive context (conjunction of contents)."""
        trace.append(f"Positive context evaluation for {context_id}")
        
        # Get all items in this context
        predicates = self._get_predicates_in_context(graph, context_id)
        child_contexts = self._get_child_contexts(graph, context_id)
        
        # All predicates must be satisfied
        all_satisfied = True
        all_assignments = [assignment]
        warnings = []
        
        # Evaluate predicates
        for predicate_id in predicates:
            predicate = graph.predicates.get(predicate_id)
            if predicate:
                pred_result = self._evaluate_predicate(graph, predicate, assignment)
                trace.extend(pred_result['trace'])
                
                if not pred_result['satisfied']:
                    all_satisfied = False
                    trace.append(f"Predicate {predicate.name} not satisfied")
                else:
                    trace.append(f"Predicate {predicate.name} satisfied")
                    all_assignments.extend(pred_result['assignments'])
                
                warnings.extend(pred_result.get('warnings', []))
        
        # Evaluate child contexts
        for child_id in child_contexts:
            child_result = self._evaluate_context(graph, child_id, assignment)
            trace.extend(child_result['trace'])
            
            if not child_result['satisfied']:
                all_satisfied = False
                trace.append(f"Child context {child_id} not satisfied")
            else:
                trace.append(f"Child context {child_id} satisfied")
                all_assignments.extend(child_result['assignments'])
            
            warnings.extend(child_result.get('warnings', []))
        
        return {
            'satisfied': all_satisfied,
            'truth_value': all_satisfied,
            'assignments': all_assignments,
            'trace': trace,
            'warnings': warnings
        }
    
    def _evaluate_negative_context(self, graph: EGGraph, context_id: ContextId,
                                  assignment: VariableAssignment, trace: List[str]) -> Dict[str, Any]:
        """Evaluate a negative context (negation of contents)."""
        trace.append(f"Negative context evaluation for {context_id}")
        
        # Evaluate the contents as if positive
        positive_result = self._evaluate_positive_context(graph, context_id, assignment, [])
        
        # Negate the result
        satisfied = not positive_result['satisfied']
        truth_value = not positive_result['truth_value'] if positive_result['truth_value'] is not None else None
        
        trace.append(f"Negating positive result: {positive_result['satisfied']} -> {satisfied}")
        trace.extend(positive_result['trace'])
        
        return {
            'satisfied': satisfied,
            'truth_value': truth_value,
            'assignments': [assignment],  # Negation doesn't add new assignments
            'trace': trace,
            'warnings': positive_result.get('warnings', [])
        }
    
    def _evaluate_predicate(self, graph: EGGraph, predicate: Predicate, 
                           assignment: VariableAssignment) -> Dict[str, Any]:
        """Evaluate a predicate in the current model.
        
        Args:
            graph: The existential graph
            predicate: The predicate to evaluate
            assignment: Current variable assignment
            
        Returns:
            Dictionary with evaluation results
        """
        trace = [f"Evaluating predicate {predicate.name} with arity {predicate.arity}"]
        
        # Handle different predicate types
        if hasattr(predicate, 'predicate_type') and predicate.predicate_type == 'function':
            return self._evaluate_function_predicate(graph, predicate, assignment, trace)
        else:
            return self._evaluate_relation_predicate(graph, predicate, assignment, trace)
    
    def _evaluate_relation_predicate(self, graph: EGGraph, predicate: Predicate,
                                   assignment: VariableAssignment, trace: List[str]) -> Dict[str, Any]:
        """Evaluate a relation predicate."""
        trace.append(f"Relation predicate: {predicate.name}")
        
        # Get domain relation name
        domain_relation = self.model.interpret_predicate(predicate.name)
        if not domain_relation:
            trace.append(f"No interpretation for predicate {predicate.name}")
            return {
                'satisfied': False,
                'assignments': [],
                'trace': trace,
                'warnings': [f"Uninterpreted predicate: {predicate.name}"]
            }
        
        # Get relation extension
        relation_extension = self.model.domain.get_relation_extension(domain_relation)
        
        # Evaluate arguments
        arg_values = []
        new_assignments = [assignment]
        
        for entity_id in predicate.entities:
            entity = graph.entities.get(entity_id)
            if not entity:
                trace.append(f"Entity {entity_id} not found")
                return {'satisfied': False, 'assignments': [], 'trace': trace, 'warnings': []}
            
            if entity.entity_type == 'constant':
                # Constant - get interpretation
                value = self.model.interpret_constant(entity.name)
                if value is None:
                    trace.append(f"No interpretation for constant {entity.name}")
                    return {
                        'satisfied': False,
                        'assignments': [],
                        'trace': trace,
                        'warnings': [f"Uninterpreted constant: {entity.name}"]
                    }
                arg_values.append(value)
                trace.append(f"Constant {entity.name} -> {value}")
                
            elif entity.entity_type == 'variable':
                # Variable - check assignment or try all domain individuals
                if assignment.contains(entity.name):
                    value = assignment.get(entity.name)
                    arg_values.append(value)
                    trace.append(f"Variable {entity.name} -> {value} (assigned)")
                else:
                    # Try all possible assignments
                    trace.append(f"Variable {entity.name} unassigned - trying all domain individuals")
                    possible_assignments = []
                    for individual in self.model.domain.individuals:
                        new_assignment = assignment.assign(entity.name, individual)
                        possible_assignments.append(new_assignment)
                    new_assignments = possible_assignments
                    arg_values = None  # Will be handled in satisfaction check
                    break
        
        # Check satisfaction
        if arg_values is not None:
            # All arguments resolved
            arg_tuple = tuple(arg_values)
            satisfied = arg_tuple in relation_extension
            trace.append(f"Checking {arg_tuple} in {domain_relation}: {satisfied}")
            
            return {
                'satisfied': satisfied,
                'assignments': new_assignments if satisfied else [],
                'trace': trace,
                'warnings': []
            }
        else:
            # Need to try variable assignments
            satisfied_assignments = []
            for test_assignment in new_assignments:
                test_values = []
                for entity_id in predicate.entities:
                    entity = graph.entities.get(entity_id)
                    if entity.entity_type == 'constant':
                        value = self.model.interpret_constant(entity.name)
                        test_values.append(value)
                    elif entity.entity_type == 'variable':
                        value = test_assignment.get(entity.name)
                        test_values.append(value)
                
                test_tuple = tuple(test_values)
                if test_tuple in relation_extension:
                    satisfied_assignments.append(test_assignment)
                    trace.append(f"Assignment satisfies: {test_tuple}")
            
            satisfied = len(satisfied_assignments) > 0
            trace.append(f"Found {len(satisfied_assignments)} satisfying assignments")
            
            return {
                'satisfied': satisfied,
                'assignments': satisfied_assignments,
                'trace': trace,
                'warnings': []
            }
    
    def _evaluate_function_predicate(self, graph: EGGraph, predicate: Predicate,
                                   assignment: VariableAssignment, trace: List[str]) -> Dict[str, Any]:
        """Evaluate a function predicate."""
        trace.append(f"Function predicate: {predicate.name}")
        
        # Get domain function
        domain_function = self.model.domain.get_function(predicate.name)
        if not domain_function:
            trace.append(f"No interpretation for function {predicate.name}")
            return {
                'satisfied': False,
                'assignments': [],
                'trace': trace,
                'warnings': [f"Uninterpreted function: {predicate.name}"]
            }
        
        # Function predicates represent equality: f(args) = result
        # The last entity is typically the result
        if len(predicate.entities) < 2:
            trace.append(f"Function predicate needs at least 2 entities")
            return {'satisfied': False, 'assignments': [], 'trace': trace, 'warnings': []}
        
        arg_entities = predicate.entities[:-1]
        result_entity_id = predicate.entities[-1]
        result_entity = graph.entities.get(result_entity_id)
        
        # Evaluate function arguments
        arg_values = []
        for entity_id in arg_entities:
            entity = graph.entities.get(entity_id)
            if entity.entity_type == 'constant':
                value = self.model.interpret_constant(entity.name)
                if value is None:
                    return {
                        'satisfied': False,
                        'assignments': [],
                        'trace': trace,
                        'warnings': [f"Uninterpreted constant: {entity.name}"]
                    }
                arg_values.append(value)
            elif entity.entity_type == 'variable':
                if assignment.contains(entity.name):
                    arg_values.append(assignment.get(entity.name))
                else:
                    trace.append(f"Unassigned variable in function: {entity.name}")
                    return {'satisfied': False, 'assignments': [], 'trace': trace, 'warnings': []}
        
        # Compute function result
        try:
            computed_result = domain_function(*arg_values)
            trace.append(f"Function {predicate.name}({arg_values}) = {computed_result}")
        except Exception as e:
            trace.append(f"Function evaluation error: {e}")
            return {'satisfied': False, 'assignments': [], 'trace': trace, 'warnings': []}
        
        # Check if result matches expected value
        if result_entity.entity_type == 'constant':
            expected_result = self.model.interpret_constant(result_entity.name)
            satisfied = computed_result == expected_result
            trace.append(f"Function result {computed_result} == expected {expected_result}: {satisfied}")
        elif result_entity.entity_type == 'variable':
            if assignment.contains(result_entity.name):
                expected_result = assignment.get(result_entity.name)
                satisfied = computed_result == expected_result
                trace.append(f"Function result {computed_result} == assigned {expected_result}: {satisfied}")
            else:
                # Assign the computed result to the variable
                new_assignment = assignment.assign(result_entity.name, computed_result)
                trace.append(f"Assigning function result {computed_result} to {result_entity.name}")
                return {
                    'satisfied': True,
                    'assignments': [new_assignment],
                    'trace': trace,
                    'warnings': []
                }
        
        return {
            'satisfied': satisfied,
            'assignments': [assignment] if satisfied else [],
            'trace': trace,
            'warnings': []
        }
    
    def _get_predicates_in_context(self, graph: EGGraph, context_id: ContextId) -> Set[PredicateId]:
        """Get all predicates in a specific context."""
        context = graph.context_manager.get_context(context_id)
        if not context:
            return set()
        
        # Filter predicates that belong to this context
        predicates_in_context = set()
        for item_id in context.contained_items:
            if item_id in graph.predicates:
                predicates_in_context.add(item_id)
        
        return predicates_in_context
    
    def _get_child_contexts(self, graph: EGGraph, context_id: ContextId) -> Set[ContextId]:
        """Get all child contexts of a specific context."""
        child_contexts = set()
        for context in graph.context_manager.contexts.values():
            if context.parent_context == context_id:
                child_contexts.add(context.id)
        return child_contexts
    
    def validate_semantic_consistency(self, graph: EGGraph) -> Dict[str, Any]:
        """Validate semantic consistency of the graph.
        
        Returns:
            Dictionary with consistency analysis results
        """
        results = {
            'is_consistent': True,
            'violations': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check for uninterpreted symbols
        uninterpreted_constants = []
        uninterpreted_predicates = []
        
        for entity in graph.entities.values():
            if entity.entity_type == 'constant' and entity.name:
                if not self.model.interpret_constant(entity.name):
                    uninterpreted_constants.append(entity.name)
        
        for predicate in graph.predicates.values():
            if not self.model.interpret_predicate(predicate.name):
                uninterpreted_predicates.append(predicate.name)
        
        if uninterpreted_constants:
            results['warnings'].append(f"Uninterpreted constants: {uninterpreted_constants}")
            results['recommendations'].append("Add interpretations for all constants")
        
        if uninterpreted_predicates:
            results['warnings'].append(f"Uninterpreted predicates: {uninterpreted_predicates}")
            results['recommendations'].append("Add interpretations for all predicates")
        
        # Check domain coverage
        if len(self.model.domain.individuals) == 0:
            results['violations'].append("Empty domain - no individuals for interpretation")
            results['is_consistent'] = False
        
        # Check for contradictions (would require full satisfaction checking)
        satisfaction_result = self.satisfies(graph)
        if not satisfaction_result.is_satisfied and not satisfaction_result.errors:
            results['warnings'].append("Graph is not satisfied in current model")
            results['recommendations'].append("Check model interpretation or graph structure")
        
        return results


# Utility functions for creating common semantic models

def create_finite_model(individuals: List[Any], relations: Dict[str, Set[Tuple]] = None,
                       constants: Dict[str, Any] = None) -> SemanticModel:
    """Create a finite semantic model with specified individuals and relations."""
    domain = SemanticDomain.create_standard(set(individuals))
    
    if relations:
        for name, extension in relations.items():
            domain = domain.add_relation(name, extension)
    
    model = SemanticModel(
        domain=domain,
        constant_interpretation=pmap(constants or {}),
        predicate_interpretation=pmap()
    )
    
    return model


def create_arithmetic_model() -> SemanticModel:
    """Create a semantic model for basic arithmetic."""
    individuals = set(range(10))  # Numbers 0-9
    
    domain = SemanticDomain.create_standard(individuals)
    
    # Add arithmetic relations
    less_than = {(i, j) for i in individuals for j in individuals if i < j}
    domain = domain.add_relation('less_than', less_than)
    
    greater_than = {(i, j) for i in individuals for j in individuals if i > j}
    domain = domain.add_relation('greater_than', greater_than)
    
    # Add arithmetic functions
    def add_function(x, y):
        result = x + y
        return result if result < 10 else result % 10  # Modular arithmetic
    
    def multiply_function(x, y):
        result = x * y
        return result if result < 10 else result % 10  # Modular arithmetic
    
    domain = domain.add_function('add', add_function)
    domain = domain.add_function('multiply', multiply_function)
    
    # Create model with standard interpretations
    model = SemanticModel(
        domain=domain,
        constant_interpretation=pmap({str(i): i for i in individuals}),
        predicate_interpretation=pmap({
            '<': 'less_than',
            '>': 'greater_than',
            '+': 'add',
            '*': 'multiply'
        })
    )
    
    return model


def create_social_model() -> SemanticModel:
    """Create a semantic model for social relationships."""
    individuals = {'alice', 'bob', 'charlie', 'diana'}
    
    domain = SemanticDomain.create_standard(individuals)
    
    # Add social relations
    friends = {('alice', 'bob'), ('bob', 'alice'), ('charlie', 'diana'), ('diana', 'charlie')}
    domain = domain.add_relation('friends', friends)
    
    parent_of = {('alice', 'charlie'), ('bob', 'diana')}
    domain = domain.add_relation('parent_of', parent_of)
    
    older_than = {('alice', 'charlie'), ('bob', 'diana'), ('alice', 'diana')}
    domain = domain.add_relation('older_than', older_than)
    
    # Create model
    model = SemanticModel(
        domain=domain,
        constant_interpretation=pmap({name: name for name in individuals}),
        predicate_interpretation=pmap({
            'Friend': 'friends',
            'Parent': 'parent_of',
            'Older': 'older_than'
        })
    )
    
    return model

