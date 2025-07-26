"""
EGIF Integration with EG-HG Architecture

This module provides the integration layer between EGIF parsing and the existing
EG-HG (Existential Graph - Hypergraph) architecture. It converts EGIF parse results
into the canonical EGGraph representation used throughout the Arisbe system.

The integration maintains the educational focus by providing detailed feedback about
how EGIF constructs map to the EG-HG representation.

Author: Manus AI
Date: January 2025
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
import uuid

from egif_parser import EGIFParseResult, parse_egif
from egif_error_handler import (
    EGIFErrorHandler, EGIFErrorReport, EGIFErrorSeverity, 
    EGIFErrorCategory, EGIFErrorContext
)
from eg_types import (
    Entity, Predicate, Context, EntityId, PredicateId, ContextId,
    new_entity_id, new_predicate_id, new_context_id,
    ValidationError, pmap, pset
)
from graph import EGGraph
from context import ContextManager


@dataclass
class EGIFIntegrationResult:
    """Result of integrating EGIF with EG-HG architecture."""
    graph: Optional[EGGraph]
    success: bool
    errors: List[EGIFErrorReport]
    educational_trace: List[str]
    entity_mapping: Dict[str, EntityId]  # Maps EGIF labels to entity IDs
    context_mapping: Dict[str, ContextId]  # Maps EGIF contexts to context IDs
    
    def get_summary(self) -> str:
        """Get a summary of the integration result."""
        if self.success:
            entity_count = len(self.entity_mapping)
            predicate_count = len(self.graph.predicates) if self.graph else 0
            context_count = len(self.context_mapping)
            
            return (f"EGIF integration successful: "
                   f"{entity_count} entities, {predicate_count} predicates, "
                   f"{context_count} contexts created")
        else:
            error_count = len(self.errors)
            return f"EGIF integration failed with {error_count} error(s)"


class EGIFIntegrator:
    """
    Integrates EGIF parsing results with the EG-HG architecture.
    
    This class provides the bridge between EGIF's linear representation
    and the canonical EGGraph representation used throughout the system.
    It maintains educational feedback about the integration process.
    """
    
    def __init__(self, educational_mode: bool = True):
        """
        Initialize the EGIF integrator.
        
        Args:
            educational_mode: Whether to provide educational feedback
        """
        self.educational_mode = educational_mode
        self.error_handler = EGIFErrorHandler(educational_mode)
        self.integration_trace = []
    
    def integrate_egif(self, source: str) -> EGIFIntegrationResult:
        """
        Parse EGIF source and integrate with EG-HG architecture.
        
        Args:
            source: EGIF source code to parse and integrate
            
        Returns:
            EGIFIntegrationResult containing the integrated graph and metadata
        """
        self._reset_state()
        
        # Parse EGIF
        self._trace("Starting EGIF parsing and integration")
        parse_result = parse_egif(source, self.educational_mode)
        
        # Handle parse errors
        source_lines = source.split('\n')
        error_reports = []
        for parse_error in parse_result.errors:
            error_report = self.error_handler.handle_parse_error(parse_error, source_lines)
            error_reports.append(error_report)
        
        if error_reports:
            self._trace(f"Parse errors found: {len(error_reports)}")
            return EGIFIntegrationResult(
                graph=None,
                success=False,
                errors=error_reports,
                educational_trace=self.integration_trace,
                entity_mapping={},
                context_mapping={}
            )
        
        # Integrate with EG-HG
        try:
            integration_result = self._integrate_parse_result(parse_result)
            self._trace("EGIF integration completed successfully")
            return integration_result
            
        except Exception as e:
            self._trace(f"Integration error: {str(e)}")
            error_report = EGIFErrorReport(
                severity=EGIFErrorSeverity.CRITICAL,
                category=EGIFErrorCategory.SYSTEM,
                message=f"Integration failed: {str(e)}",
                error_code="INTEGRATION_ERROR",
                context=EGIFErrorContext(),
                suggestions=["Check EGIF syntax and try again", "Report this error if it persists"]
            )
            
            return EGIFIntegrationResult(
                graph=None,
                success=False,
                errors=[error_report],
                educational_trace=self.integration_trace,
                entity_mapping={},
                context_mapping={}
            )
    
    def _reset_state(self):
        """Reset integrator state for a new integration."""
        self.integration_trace = []
        self.error_handler.clear_history()
    
    def _trace(self, message: str):
        """Add a message to the integration trace."""
        if self.educational_mode:
            self.integration_trace.append(message)
    
    def _integrate_parse_result(self, parse_result: EGIFParseResult) -> EGIFIntegrationResult:
        """Integrate a successful parse result with EG-HG architecture."""
        # Create empty graph
        graph = EGGraph.create_empty()
        
        # Track mappings for educational feedback
        entity_mapping = {}
        context_mapping = {"root": graph.root_context_id}
        
        self._trace(f"Created empty EG graph with root context: {graph.root_context_id}")
        
        # Add entities to graph
        self._trace(f"Integrating {len(parse_result.entities)} entities")
        for entity in parse_result.entities:
            graph = self._add_entity_to_graph(graph, entity)
            if entity.name:
                entity_mapping[entity.name] = entity.id
                self._trace(f"Mapped entity '{entity.name}' -> {entity.id}")
        
        # Add predicates to graph
        self._trace(f"Integrating {len(parse_result.predicates)} predicates")
        for predicate in parse_result.predicates:
            graph = self._add_predicate_to_graph(graph, predicate)
            self._trace(f"Added predicate '{predicate.name}' with {predicate.arity} arguments")
        
        # Handle contexts (for negations and scrolls)
        self._trace("Processing contexts from parse result")
        for context_id in self._extract_contexts_from_parse_result(parse_result):
            if context_id != parse_result.root_context_id:
                # Create context in graph if it doesn't exist
                context_name = f"context_{context_id}"
                context_mapping[context_name] = context_id
                self._trace(f"Mapped context '{context_name}' -> {context_id}")
        
        # Validate the integrated graph
        self._trace("Validating integrated graph")
        validation_errors = self._validate_integrated_graph(graph)
        
        if validation_errors:
            self._trace(f"Validation errors found: {len(validation_errors)}")
            return EGIFIntegrationResult(
                graph=None,
                success=False,
                errors=validation_errors,
                educational_trace=self.integration_trace,
                entity_mapping=entity_mapping,
                context_mapping=context_mapping
            )
        
        return EGIFIntegrationResult(
            graph=graph,
            success=True,
            errors=[],
            educational_trace=self.integration_trace,
            entity_mapping=entity_mapping,
            context_mapping=context_mapping
        )
    
    def _add_entity_to_graph(self, graph: EGGraph, entity: Entity) -> EGGraph:
        """Add an entity to the EG graph."""
        # Get the context ID from entity properties
        context_id = entity.properties.get("context_id", graph.root_context_id)
        
        # Add entity to graph
        new_entities = graph.entities.set(entity.id, entity)
        
        # Create updated graph with new entities
        from dataclasses import replace
        updated_graph = replace(graph, entities=new_entities)
        
        # Add entity to context
        updated_context_manager = updated_graph.context_manager.add_item_to_context(
            context_id, entity.id
        )
        
        return replace(updated_graph, context_manager=updated_context_manager)
    
    def _add_predicate_to_graph(self, graph: EGGraph, predicate: Predicate) -> EGGraph:
        """Add a predicate to the EG graph."""
        # Get the context ID from predicate properties
        context_id = predicate.properties.get("context_id", graph.root_context_id)
        
        # Add predicate to graph
        new_predicates = graph.predicates.set(predicate.id, predicate)
        
        # Create updated graph with new predicates
        from dataclasses import replace
        updated_graph = replace(graph, predicates=new_predicates)
        
        # Add predicate to context
        updated_context_manager = updated_graph.context_manager.add_item_to_context(
            context_id, predicate.id
        )
        
        return replace(updated_graph, context_manager=updated_context_manager)
    
    def _extract_contexts_from_parse_result(self, parse_result: EGIFParseResult) -> Set[ContextId]:
        """Extract all context IDs from the parse result."""
        contexts = {parse_result.root_context_id}
        
        # Extract contexts from entities
        for entity in parse_result.entities:
            context_id = entity.properties.get("context_id")
            if context_id:
                contexts.add(context_id)
        
        # Extract contexts from predicates
        for predicate in parse_result.predicates:
            context_id = predicate.properties.get("context_id")
            if context_id:
                contexts.add(context_id)
        
        return contexts
    
    def _validate_integrated_graph(self, graph: EGGraph) -> List[EGIFErrorReport]:
        """Validate the integrated graph for consistency."""
        errors = []
        
        # Check that all entities referenced by predicates exist
        for predicate in graph.predicates.values():
            for entity_id in predicate.entities:
                if entity_id not in graph.entities:
                    error = EGIFErrorReport(
                        severity=EGIFErrorSeverity.ERROR,
                        category=EGIFErrorCategory.SEMANTIC,
                        message=f"Predicate '{predicate.name}' references non-existent entity {entity_id}",
                        error_code="MISSING_ENTITY_REFERENCE",
                        context=EGIFErrorContext(),
                        suggestions=["Check entity creation logic", "Verify entity ID mapping"]
                    )
                    errors.append(error)
        
        # Check that all items are in valid contexts
        for entity in graph.entities.values():
            context_id = entity.properties.get("context_id")
            if context_id and context_id not in graph.contexts:
                error = EGIFErrorReport(
                    severity=EGIFErrorSeverity.WARNING,
                    category=EGIFErrorCategory.CONTEXT,
                    message=f"Entity '{entity.name}' references non-existent context {context_id}",
                    error_code="MISSING_CONTEXT_REFERENCE",
                    context=EGIFErrorContext(),
                    suggestions=["Check context creation logic", "Verify context ID mapping"]
                )
                errors.append(error)
        
        return errors
    
    def generate_integration_report(self, result: EGIFIntegrationResult) -> str:
        """Generate a comprehensive report of the integration process."""
        lines = []
        lines.append("EGIF Integration Report")
        lines.append("=" * 30)
        
        # Summary
        lines.append(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
        lines.append(result.get_summary())
        
        # Entity mapping
        if result.entity_mapping:
            lines.append("\nEntity Mapping:")
            for label, entity_id in result.entity_mapping.items():
                lines.append(f"  {label} -> {entity_id}")
        
        # Context mapping
        if result.context_mapping:
            lines.append("\nContext Mapping:")
            for context_name, context_id in result.context_mapping.items():
                lines.append(f"  {context_name} -> {context_id}")
        
        # Graph statistics
        if result.graph:
            lines.append("\nGraph Statistics:")
            lines.append(f"  Entities: {len(result.graph.entities)}")
            lines.append(f"  Predicates: {len(result.graph.predicates)}")
            lines.append(f"  Contexts: {len(result.graph.contexts)}")
        
        # Educational trace
        if self.educational_mode and result.educational_trace:
            lines.append("\nIntegration Trace:")
            for trace_line in result.educational_trace:
                lines.append(f"  {trace_line}")
        
        # Errors
        if result.errors:
            lines.append(f"\nErrors ({len(result.errors)}):")
            for i, error in enumerate(result.errors, 1):
                lines.append(f"  {i}. {error.message}")
                if error.suggestions:
                    lines.append(f"     Suggestion: {error.suggestions[0]}")
        
        return "\n".join(lines)


# Convenience functions for common operations
def egif_to_graph(source: str, educational_mode: bool = True) -> EGIFIntegrationResult:
    """
    Convert EGIF source code directly to an EGGraph.
    
    Args:
        source: EGIF source code
        educational_mode: Whether to include educational feedback
        
    Returns:
        EGIFIntegrationResult containing the integrated graph
    """
    integrator = EGIFIntegrator(educational_mode)
    return integrator.integrate_egif(source)


def validate_egif_syntax(source: str) -> Tuple[bool, List[str]]:
    """
    Validate EGIF syntax without full integration.
    
    Args:
        source: EGIF source code to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    result = egif_to_graph(source, educational_mode=False)
    error_messages = [error.message for error in result.errors]
    return result.success, error_messages


# Example usage and testing
if __name__ == "__main__":
    # Test cases for integration
    test_cases = [
        # Simple relation
        "(Person *x)",
        
        # Multiple relations with shared entity
        "(Person *x) (Mortal x)",
        
        # Negation
        "~[(Person x)]",
        
        # Complex example
        "(Person *x) ~[(Mortal x)]",
        
        # Error case
        "(Person *x) (Mortal y)",  # Undefined label
    ]
    
    integrator = EGIFIntegrator(educational_mode=True)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case}")
        print("=" * 50)
        
        result = integrator.integrate_egif(test_case)
        
        print(integrator.generate_integration_report(result))
        
        if result.success and result.graph:
            print(f"\nGraph Details:")
            print(f"  Root context: {result.graph.root_context_id}")
            
            # Show entities
            for entity in result.graph.entities.values():
                context_id = entity.properties.get("context_id", "unknown")
                print(f"  Entity: {entity.name} ({entity.entity_type}) in context {context_id}")
            
            # Show predicates
            for predicate in result.graph.predicates.values():
                context_id = predicate.properties.get("context_id", "unknown")
                entity_names = []
                for entity_id in predicate.entities:
                    if entity_id in result.graph.entities:
                        entity_names.append(result.graph.entities[entity_id].name or str(entity_id))
                    else:
                        entity_names.append(str(entity_id))
                print(f"  Predicate: {predicate.name}({', '.join(entity_names)}) in context {context_id}")
        
        print("\n" + "-" * 50)

