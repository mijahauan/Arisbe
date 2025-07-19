"""
Fixed CLIF generator with correct Entity-Predicate hypergraph architecture.

This module provides CLIF generation that correctly maps:
- Entities (Lines of Identity) → CLIF terms (variables, constants)
- Predicates (hyperedges connecting entities) → CLIF predicates
- Entity scoping in contexts → CLIF quantifiers

Fixed to work with the corrected graph API.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from collections import defaultdict
import uuid

from eg_types import (
    Entity, Predicate, Context,
    EntityId, PredicateId, ContextId,
    ValidationError, pmap, pset
)
from graph import EGGraph


@dataclass
class CLIFGenerationResult:
    """Result of CLIF generation operation."""
    clif_text: Optional[str]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class CLIFGenerator:
    """Generator for CLIF (Common Logic Interchange Format) from Entity-Predicate graphs."""
    
    def __init__(self):
        """Initialize the generator."""
        self.errors = []
        self.warnings = []
        self.metadata = {}
        
        # Entity name mapping for generation
        self.entity_names = {}  # Dict[EntityId, str]
        self.variable_counter = 0
    
    def generate(self, graph: EGGraph) -> CLIFGenerationResult:
        """Generate CLIF from an existential graph."""
        try:
            # Initialize generator state
            self.errors = []
            self.warnings = []
            self.metadata = {}
            self.entity_names = {}
            self.variable_counter = 0
            
            # Build entity name mapping
            self._build_entity_names(graph)
            
            # Generate CLIF content
            clif_content = self._generate_clif_from_graph(graph)
            
            return CLIFGenerationResult(
                clif_text=clif_content,
                errors=self.errors,
                warnings=self.warnings,
                metadata=self.metadata
            )
        
        except Exception as e:
            self._add_error(f"Generation failed: {str(e)}")
            return CLIFGenerationResult(
                clif_text=None,
                errors=self.errors,
                warnings=self.warnings,
                metadata=self.metadata
            )
    
    def _add_error(self, message: str):
        """Add an error to the error list."""
        self.errors.append(message)
    
    def _add_warning(self, message: str):
        """Add a warning to the warning list."""
        self.warnings.append(message)
    
    def _build_entity_names(self, graph: EGGraph):
        """Build mapping from entity IDs to names."""
        for entity in graph.entities.values():
            self.entity_names[entity.id] = entity.name
    
    def _generate_clif_from_graph(self, graph: EGGraph) -> str:
        """Generate CLIF content from the graph."""
        # Start with the root context
        root_content = self._generate_context_content(graph, graph.root_context_id)
        
        if root_content.strip():
            return root_content
        else:
            return "(cl:text)"  # Empty CLIF module
    
    def _generate_context_content(self, graph: EGGraph, context_id: ContextId) -> str:
        """Generate CLIF content for a specific context."""
        context = graph.contexts.get(context_id)
        if context is None:
            return ""
        
        # Get entities and predicates in this context
        context_entities = self._get_entities_in_context(graph, context_id)
        context_predicates = self._get_predicates_in_context(graph, context_id)
        
        # Get child contexts
        child_contexts = self._get_child_contexts(graph, context_id)
        
        # Generate content based on context type
        if context.context_type == 'sheet_of_assertion':
            return self._generate_sheet_content(graph, context_entities, context_predicates, child_contexts)
        elif context.context_type == 'cut':
            return self._generate_cut_content(graph, context_id, context_entities, context_predicates, child_contexts)
        else:
            # Default: treat as conjunction
            return self._generate_conjunction_content(graph, context_entities, context_predicates, child_contexts)
    
    def _get_entities_in_context(self, graph: EGGraph, context_id: ContextId) -> Set[EntityId]:
        """Get entities directly in a specific context."""
        entities = set()
        
        # Get all items in context
        items = graph.get_items_in_context(context_id)
        
        # Filter for entities
        for item_id in items:
            if item_id in graph.entities:
                entities.add(item_id)
        
        return entities
    
    def _get_predicates_in_context(self, graph: EGGraph, context_id: ContextId) -> Set[PredicateId]:
        """Get predicates directly in a specific context."""
        predicates = set()
        
        # Get all items in context
        items = graph.get_items_in_context(context_id)
        
        # Filter for predicates
        for item_id in items:
            if item_id in graph.predicates:
                predicates.add(item_id)
        
        return predicates
    
    def _get_child_contexts(self, graph: EGGraph, parent_id: ContextId) -> List[ContextId]:
        """Get direct child contexts of a parent context."""
        children = []
        
        for context_id, context in graph.contexts.items():
            if context.parent_context == parent_id:
                children.append(context_id)
        
        return children
    
    def _generate_sheet_content(self, graph: EGGraph, entities: Set[EntityId], 
                               predicates: Set[PredicateId], child_contexts: List[ContextId]) -> str:
        """Generate content for the sheet of assertion (root context)."""
        statements = []
        
        # Generate predicates in root context (skip function predicates)
        for predicate_id in predicates:
            predicate = graph.predicates[predicate_id]
            
            # Skip function predicates - they should only appear as functional terms
            if hasattr(predicate, 'predicate_type') and predicate.predicate_type == 'function':
                continue
                
            statement = self._generate_predicate_statement(graph, predicate)
            if statement:
                statements.append(statement)
        
        # Generate child contexts
        for child_id in child_contexts:
            child_content = self._generate_context_content(graph, child_id)
            if child_content:
                statements.append(child_content)
        
        # Combine statements
        if len(statements) == 0:
            return ""
        elif len(statements) == 1:
            return statements[0]
        else:
            # Multiple statements - wrap in conjunction if needed
            return self._combine_statements(statements)
    
    def _generate_cut_content(self, graph: EGGraph, context_id: ContextId, entities: Set[EntityId], 
                             predicates: Set[PredicateId], child_contexts: List[ContextId]) -> str:
        """Generate content for a cut context (negation)."""
        # Check if this is part of a quantification pattern
        context = graph.contexts[context_id]
        context_name = context.properties.get("name", "")
        
        if "Universal Quantification" in context_name:
            return self._generate_universal_quantification(graph, context_id, entities, predicates, child_contexts)
        elif "Existential Quantification" in context_name:
            return self._generate_existential_quantification(graph, context_id, entities, predicates, child_contexts)
        else:
            # Simple negation
            inner_content = self._generate_conjunction_content(graph, entities, predicates, child_contexts)
            if inner_content:
                return f"(not {inner_content})"
            else:
                return "(not)"
    
    def _generate_universal_quantification(self, graph: EGGraph, context_id: ContextId, 
                                         entities: Set[EntityId], predicates: Set[PredicateId], 
                                         child_contexts: List[ContextId]) -> str:
        """Generate universal quantification."""
        # Find variables in this context
        variables = []
        for entity_id in entities:
            entity = graph.entities[entity_id]
            if entity.entity_type == 'variable':
                variables.append(entity.name)
        
        # Generate body content
        body_content = self._generate_conjunction_content(graph, entities, predicates, child_contexts)
        
        if variables and body_content:
            var_list = " ".join(variables)
            return f"(forall ({var_list}) {body_content})"
        else:
            return body_content or ""
    
    def _generate_existential_quantification(self, graph: EGGraph, context_id: ContextId, 
                                           entities: Set[EntityId], predicates: Set[PredicateId], 
                                           child_contexts: List[ContextId]) -> str:
        """Generate existential quantification."""
        # Find variables in this context
        variables = []
        for entity_id in entities:
            entity = graph.entities[entity_id]
            if entity.entity_type == 'variable':
                variables.append(entity.name)
        
        # Generate body content
        body_content = self._generate_conjunction_content(graph, entities, predicates, child_contexts)
        
        if variables and body_content:
            var_list = " ".join(variables)
            return f"(exists ({var_list}) {body_content})"
        else:
            return body_content or ""
    
    def _generate_conjunction_content(self, graph: EGGraph, entities: Set[EntityId], 
                                    predicates: Set[PredicateId], child_contexts: List[ContextId]) -> str:
        """Generate conjunction content."""
        statements = []
        
        # Generate predicates (skip function predicates)
        for predicate_id in predicates:
            predicate = graph.predicates[predicate_id]
            
            # Skip function predicates - they should only appear as functional terms
            if hasattr(predicate, 'predicate_type') and predicate.predicate_type == 'function':
                continue
                
            statement = self._generate_predicate_statement(graph, predicate)
            if statement:
                statements.append(statement)
        
        # Generate child contexts
        for child_id in child_contexts:
            child_content = self._generate_context_content(graph, child_id)
            if child_content:
                statements.append(child_content)
        
        return self._combine_statements(statements)
    
    def _generate_predicate_statement(self, graph: EGGraph, predicate: Predicate) -> str:
        """Generate a CLIF statement for a predicate."""
        
        # Handle function predicates specially
        if hasattr(predicate, 'predicate_type') and predicate.predicate_type == 'function':
            return self._generate_function_term(graph, predicate)
        
        # Handle regular relation predicates
        if predicate.arity == 0:
            # Zero-arity predicate
            return f"({predicate.name})"
        
        # Get entity names
        entity_names = []
        for entity_id in predicate.entities:
            entity_name = self._get_entity_name_for_clif(graph, entity_id)
            entity_names.append(entity_name)
        
        if entity_names:
            args = " ".join(entity_names)
            return f"({predicate.name} {args})"
        else:
            return f"({predicate.name})"
    
    def _generate_function_term(self, graph: EGGraph, function_predicate: Predicate) -> str:
        """Generate a functional term from a function predicate."""
        # For function predicates, the last entity is the return entity
        # The other entities are the arguments
        
        if not hasattr(function_predicate, 'return_entity') or function_predicate.return_entity is None:
            # Fallback: treat as regular predicate if no return entity specified
            return self._generate_regular_predicate_statement(graph, function_predicate)
        
        # Get argument entities (all except the return entity)
        arg_entities = []
        return_entity_id = function_predicate.return_entity
        
        for entity_id in function_predicate.entities:
            if entity_id != return_entity_id:
                arg_entities.append(entity_id)
        
        # Generate the functional term
        if len(arg_entities) == 0:
            # Zero-arity function
            return f"({function_predicate.name})"
        else:
            # Function with arguments
            arg_names = []
            for entity_id in arg_entities:
                arg_name = self._get_entity_name_for_clif(graph, entity_id)
                arg_names.append(arg_name)
            
            args = " ".join(arg_names)
            return f"({function_predicate.name} {args})"
    
    def _generate_regular_predicate_statement(self, graph: EGGraph, predicate: Predicate) -> str:
        """Generate a regular predicate statement (fallback method)."""
        if predicate.arity == 0:
            return f"({predicate.name})"
        
        entity_names = []
        for entity_id in predicate.entities:
            entity_name = self._get_entity_name_for_clif(graph, entity_id)
            entity_names.append(entity_name)
        
        if entity_names:
            args = " ".join(entity_names)
            return f"({predicate.name} {args})"
        else:
            return f"({predicate.name})"
    
    def _get_entity_name_for_clif(self, graph: EGGraph, entity_id: EntityId) -> str:
        """Get the appropriate CLIF representation for an entity."""
        entity = graph.entities.get(entity_id)
        if entity is None:
            return f"entity_{entity_id}"
        
        # Check if this entity is the result of a function
        if hasattr(entity, 'entity_type') and entity.entity_type == 'functional_term':
            # This entity represents the result of a function call
            # We need to find the function predicate that produces this entity
            function_term = self._reconstruct_function_term(graph, entity_id)
            if function_term:
                return function_term
        
        # Use the entity's name or generate one
        if entity.name:
            return entity.name
        else:
            return f"entity_{entity_id}"
    
    def _reconstruct_function_term(self, graph: EGGraph, result_entity_id: EntityId) -> Optional[str]:
        """Reconstruct a functional term from its result entity."""
        # Find the function predicate that has this entity as its return entity
        for predicate in graph.predicates.values():
            if (hasattr(predicate, 'predicate_type') and 
                predicate.predicate_type == 'function' and
                hasattr(predicate, 'return_entity') and
                predicate.return_entity == result_entity_id):
                
                # Found the function predicate, reconstruct the term
                arg_entities = []
                for entity_id in predicate.entities:
                    if entity_id != result_entity_id:
                        arg_entities.append(entity_id)
                
                if len(arg_entities) == 0:
                    # Zero-arity function
                    return f"({predicate.name})"
                else:
                    # Function with arguments
                    arg_names = []
                    for entity_id in arg_entities:
                        # Recursively get names for arguments (handles nested functions)
                        arg_name = self._get_entity_name_for_clif(graph, entity_id)
                        arg_names.append(arg_name)
                    
                    args = " ".join(arg_names)
                    return f"({predicate.name} {args})"
        
        return None
    
    def _combine_statements(self, statements: List[str]) -> str:
        """Combine multiple statements appropriately."""
        if len(statements) == 0:
            return ""
        elif len(statements) == 1:
            return statements[0]
        else:
            # Multiple statements - use conjunction
            combined = " ".join(statements)
            return f"(and {combined})"


class CLIFRoundTripValidator:
    """Validator for CLIF round-trip conversion."""
    
    def __init__(self):
        """Initialize the validator."""
        pass
    
    def validate_round_trip(self, original_graph: EGGraph, roundtrip_graph: EGGraph) -> Dict[str, Any]:
        """Validate that a round-trip conversion preserves graph structure."""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        # Compare entity counts
        orig_entity_count = len(original_graph.entities)
        rt_entity_count = len(roundtrip_graph.entities)
        
        if orig_entity_count != rt_entity_count:
            results['errors'].append(f"Entity count mismatch: {orig_entity_count} vs {rt_entity_count}")
            results['valid'] = False
        
        # Compare predicate counts
        orig_predicate_count = len(original_graph.predicates)
        rt_predicate_count = len(roundtrip_graph.predicates)
        
        if orig_predicate_count != rt_predicate_count:
            results['errors'].append(f"Predicate count mismatch: {orig_predicate_count} vs {rt_predicate_count}")
            results['valid'] = False
        
        # Compare context counts
        orig_context_count = len(original_graph.contexts)
        rt_context_count = len(roundtrip_graph.contexts)
        
        if orig_context_count != rt_context_count:
            results['warnings'].append(f"Context count difference: {orig_context_count} vs {rt_context_count}")
        
        # Store statistics
        results['statistics'] = {
            'original_entities': orig_entity_count,
            'roundtrip_entities': rt_entity_count,
            'original_predicates': orig_predicate_count,
            'roundtrip_predicates': rt_predicate_count,
            'original_contexts': orig_context_count,
            'roundtrip_contexts': rt_context_count
        }
        
        return results

