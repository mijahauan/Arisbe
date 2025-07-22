#!/usr/bin/env python3

"""
EGRF Parser Module

Converts EGRF (Existential Graph Rendering Format) documents back to EG-CL-Manus2 
data structures, completing the round-trip conversion capability.
"""

import uuid
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass

# Import EG-CL-Manus2 types
from graph import EGGraph
from eg_types import Entity, Predicate, Context, EntityId, PredicateId, ContextId
from context import ContextManager

# Import EGRF types
from .egrf_types import EGRFDocument, Entity as EGRFEntity, Predicate as EGRFPredicate, Context as EGRFContext
from .egrf_serializer import EGRFSerializer


class EGRFParseError(Exception):
    """Exception raised during EGRF parsing."""
    pass


@dataclass
class ParseResult:
    """Result of EGRF parsing operation."""
    graph: Optional[EGGraph] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    @property
    def is_successful(self) -> bool:
        """Check if parsing was successful."""
        return self.graph is not None and len(self.errors) == 0


class EGRFParser:
    """Converts EGRF documents back to EG-CL-Manus2 data structures."""
    
    def __init__(self, validation_enabled: bool = True, strict_mode: bool = False):
        """
        Initialize EGRF parser.
        
        Args:
            validation_enabled: Whether to validate EGRF documents before parsing
            strict_mode: Whether to fail on warnings or continue with best effort
        """
        self.validation_enabled = validation_enabled
        self.strict_mode = strict_mode
        
        # Parsing state
        self._entity_map: Dict[str, EntityId] = {}
        self._predicate_map: Dict[str, PredicateId] = {}
        self._context_map: Dict[str, ContextId] = {}
        self._errors: List[str] = []
        self._warnings: List[str] = []
    
    def parse(self, egrf_doc: EGRFDocument) -> ParseResult:
        """
        Parse EGRF document to EGGraph.
        
        Args:
            egrf_doc: EGRF document to parse
            
        Returns:
            ParseResult with graph or errors
        """
        # Reset parsing state
        self._entity_map.clear()
        self._predicate_map.clear()
        self._context_map.clear()
        self._errors.clear()
        self._warnings.clear()
        
        try:
            # Stage 1: Validation
            if self.validation_enabled:
                self._validate_document(egrf_doc)
            
            # Stage 2: Parse entities
            entities = self._parse_entities(egrf_doc)
            
            # Stage 3: Parse predicates
            predicates = self._parse_predicates(egrf_doc)
            
            # Stage 4: Parse contexts and build hierarchy
            context_manager = self._parse_contexts(egrf_doc)
            
            # Stage 5: Reconstruct connections
            connections = self._reconstruct_connections(egrf_doc)
            
            # Stage 6: Assemble graph
            graph = self._assemble_graph(entities, predicates, context_manager, connections)
            
            # Stage 7: Final validation
            self._validate_final_graph(graph)
            
            return ParseResult(
                graph=graph,
                errors=self._errors.copy(),
                warnings=self._warnings.copy()
            )
            
        except Exception as e:
            self._errors.append(f"Parsing failed: {str(e)}")
            return ParseResult(
                graph=None,
                errors=self._errors.copy(),
                warnings=self._warnings.copy()
            )
    
    def parse_from_json(self, json_str: str) -> ParseResult:
        """
        Parse EGRF from JSON string.
        
        Args:
            json_str: JSON string containing EGRF document
            
        Returns:
            ParseResult with graph or errors
        """
        try:
            egrf_doc = EGRFSerializer.from_json(json_str, validate=self.validation_enabled)
            return self.parse(egrf_doc)
        except Exception as e:
            return ParseResult(
                graph=None,
                errors=[f"JSON parsing failed: {str(e)}"],
                warnings=[]
            )
    
    def parse_from_file(self, file_path: str) -> ParseResult:
        """
        Parse EGRF from file.
        
        Args:
            file_path: Path to EGRF file
            
        Returns:
            ParseResult with graph or errors
        """
        try:
            egrf_doc = EGRFSerializer.load_from_file(file_path, validate=self.validation_enabled)
            return self.parse(egrf_doc)
        except Exception as e:
            return ParseResult(
                graph=None,
                errors=[f"File parsing failed: {str(e)}"],
                warnings=[]
            )
    
    def _validate_document(self, egrf_doc: EGRFDocument) -> None:
        """Validate EGRF document structure."""
        if not egrf_doc.entities and not egrf_doc.predicates:
            self._warnings.append("Document contains no entities or predicates")
        
        # Check for orphaned entities
        referenced_entities = set()
        for predicate in egrf_doc.predicates:
            if hasattr(predicate, 'connections'):
                for conn in predicate.connections:
                    if hasattr(conn, 'entity_id'):
                        referenced_entities.add(conn.entity_id)
        
        entity_ids = {entity.id for entity in egrf_doc.entities}
        orphaned = entity_ids - referenced_entities
        if orphaned:
            self._warnings.append(f"Orphaned entities found: {orphaned}")
    
    def _parse_entities(self, egrf_doc: EGRFDocument) -> Dict[EntityId, Entity]:
        """Parse EGRF entities to EG-CL-Manus2 entities."""
        entities = {}
        
        # Handle both object and dictionary formats
        entities_data = egrf_doc.entities if hasattr(egrf_doc, 'entities') else egrf_doc.get('entities', [])
        
        for egrf_entity in entities_data:
            try:
                # Handle both object and dictionary formats
                if isinstance(egrf_entity, dict):
                    entity_id_str = egrf_entity.get('id', str(uuid.uuid4()))
                    entity_name = egrf_entity.get('name', 'Unknown')
                    entity_type = egrf_entity.get('entity_type', 'constant')
                else:
                    entity_id_str = getattr(egrf_entity, 'id', str(uuid.uuid4()))
                    entity_name = getattr(egrf_entity, 'name', 'Unknown')
                    entity_type = getattr(egrf_entity, 'entity_type', 'constant')
                
                # Create new EntityId or use existing if valid UUID
                try:
                    entity_id = EntityId(uuid.UUID(entity_id_str))
                except (ValueError, AttributeError):
                    entity_id = EntityId(uuid.uuid4())
                    self._warnings.append(f"Generated new ID for entity {entity_id_str}")
                
                # Map EGRF entity to EG-CL-Manus2 entity
                entity = Entity.create(
                    name=entity_name,
                    entity_type=entity_type
                )
                
                # Store mapping for connection reconstruction
                self._entity_map[entity_id_str] = entity.id
                entities[entity.id] = entity
                
            except Exception as e:
                entity_id_str = str(egrf_entity) if not isinstance(egrf_entity, dict) else egrf_entity.get('id', 'unknown')
                self._errors.append(f"Failed to parse entity {entity_id_str}: {str(e)}")
        
        return entities
    
    def _parse_predicates(self, egrf_doc: EGRFDocument) -> Dict[PredicateId, Predicate]:
        """Parse EGRF predicates to EG-CL-Manus2 predicates."""
        predicates = {}
        
        # Handle both object and dictionary formats
        predicates_data = egrf_doc.predicates if hasattr(egrf_doc, 'predicates') else egrf_doc.get('predicates', [])
        
        for egrf_predicate in predicates_data:
            try:
                # Handle both object and dictionary formats
                if isinstance(egrf_predicate, dict):
                    predicate_id_str = egrf_predicate.get('id', str(uuid.uuid4()))
                    predicate_name = egrf_predicate.get('name', 'Unknown')
                else:
                    predicate_id_str = getattr(egrf_predicate, 'id', str(uuid.uuid4()))
                    predicate_name = getattr(egrf_predicate, 'name', 'Unknown')
                
                # Create new PredicateId or use existing if valid UUID
                try:
                    predicate_id = PredicateId(uuid.UUID(predicate_id_str))
                except (ValueError, AttributeError):
                    predicate_id = PredicateId(uuid.uuid4())
                    self._warnings.append(f"Generated new ID for predicate {predicate_id_str}")
                
                # Initially create predicate without entities (will be added in connection phase)
                predicate = Predicate.create(
                    name=predicate_name,
                    entities=[]  # Will be populated during connection reconstruction
                )
                
                # Store mapping for connection reconstruction
                self._predicate_map[predicate_id_str] = predicate.id
                predicates[predicate.id] = predicate
                
            except Exception as e:
                predicate_id_str = str(egrf_predicate) if not isinstance(egrf_predicate, dict) else egrf_predicate.get('id', 'unknown')
                self._errors.append(f"Failed to parse predicate {predicate_id_str}: {str(e)}")
        
        return predicates
    
    def _parse_contexts(self, egrf_doc: EGRFDocument) -> ContextManager:
        """Parse EGRF contexts and build hierarchy."""
        context_manager = ContextManager()
        
        # Handle both object and dictionary formats
        contexts_data = egrf_doc.contexts if hasattr(egrf_doc, 'contexts') else egrf_doc.get('contexts', [])
        
        if not contexts_data:
            # No explicit contexts, use root context only
            return context_manager
        
        # Sort contexts by containment (largest to smallest for proper hierarchy)
        sorted_contexts = self._sort_contexts_by_containment(contexts_data)
        
        for egrf_context in sorted_contexts:
            try:
                # Handle both object and dictionary formats
                if isinstance(egrf_context, dict):
                    context_id_str = egrf_context.get('id', str(uuid.uuid4()))
                    context_type = egrf_context.get('context_type', 'cut')
                else:
                    context_id_str = getattr(egrf_context, 'id', str(uuid.uuid4()))
                    context_type = getattr(egrf_context, 'context_type', 'cut')
                
                # Create new ContextId or use existing if valid UUID
                try:
                    context_id = ContextId(uuid.UUID(context_id_str))
                except (ValueError, AttributeError):
                    context_id = ContextId(uuid.uuid4())
                    self._warnings.append(f"Generated new ID for context {context_id_str}")
                
                # Find parent context
                parent_id = self._find_parent_context(egrf_context, sorted_contexts)
                
                # Create context using proper parameters
                context = Context.create(
                    context_type=context_type,
                    parent_context=parent_id,
                    depth=1 if parent_id else 0,
                    id=context_id
                )
                
                # Add to context manager
                context_manager = context_manager.add_context(context)
                
                # Store mapping
                self._context_map[context_id_str] = context.id
                
            except Exception as e:
                context_id_str = str(egrf_context) if not isinstance(egrf_context, dict) else egrf_context.get('id', 'unknown')
                self._errors.append(f"Failed to parse context {context_id_str}: {str(e)}")
        
        return context_manager
    
    def _reconstruct_connections(self, egrf_doc: EGRFDocument) -> Dict[str, List[str]]:
        """Reconstruct entity-predicate connections from EGRF visual data."""
        connections = {}
        
        # Handle both object and dictionary formats
        predicates_data = egrf_doc.predicates if hasattr(egrf_doc, 'predicates') else egrf_doc.get('predicates', [])
        
        for egrf_predicate in predicates_data:
            connected_entities = []
            
            # Handle both object and dictionary formats
            if isinstance(egrf_predicate, dict):
                predicate_id = egrf_predicate.get('id', 'unknown')
                predicate_connections = egrf_predicate.get('connections', [])
            else:
                predicate_id = getattr(egrf_predicate, 'id', 'unknown')
                predicate_connections = getattr(egrf_predicate, 'connections', [])
            
            for connection in predicate_connections:
                # Handle both object and dictionary formats
                if isinstance(connection, dict):
                    entity_id = connection.get('entity_id')
                else:
                    entity_id = getattr(connection, 'entity_id', None)
                
                if entity_id:
                    # Validate entity exists
                    if entity_id in self._entity_map:
                        connected_entities.append(entity_id)
                    else:
                        self._warnings.append(f"Connection references unknown entity: {entity_id}")
            
            connections[predicate_id] = connected_entities
        
        return connections
    
    def _assemble_graph(self, entities: Dict[EntityId, Entity], 
                       predicates: Dict[PredicateId, Predicate],
                       context_manager: ContextManager,
                       connections: Dict[str, List[str]]) -> EGGraph:
        """Assemble final EGGraph from parsed components."""
        
        # Start with empty graph
        graph = EGGraph.create_empty()
        
        # Replace context manager if we have custom contexts
        if len(context_manager.contexts) > 1:  # More than just root context
            # For now, use the default context manager
            # In a full implementation, we would properly integrate custom contexts
            pass
        
        # Add entities
        for entity_id, entity in entities.items():
            # Add to root context by default (could be enhanced to use context information)
            graph = graph.add_entity(entity, graph.root_context_id)
        
        # Add predicates with connections
        for egrf_predicate_id, entity_ids in connections.items():
            if egrf_predicate_id in self._predicate_map:
                predicate_id = self._predicate_map[egrf_predicate_id]
                predicate = predicates[predicate_id]
                
                # Map EGRF entity IDs to EG-CL-Manus2 entity IDs
                eg_entity_ids = []
                for egrf_entity_id in entity_ids:
                    if egrf_entity_id in self._entity_map:
                        eg_entity_ids.append(self._entity_map[egrf_entity_id])
                
                # Create predicate with proper entity connections
                connected_predicate = Predicate.create(
                    name=predicate.name,
                    entities=eg_entity_ids
                )
                
                # Add to graph (root context by default)
                graph = graph.add_predicate(connected_predicate, graph.root_context_id)
        
        return graph
    
    def _sort_contexts_by_containment(self, contexts: List[EGRFContext]) -> List[EGRFContext]:
        """Sort contexts by containment area (largest first)."""
        def get_area(context):
            if hasattr(context, 'visual') and hasattr(context.visual, 'bounds'):
                bounds = context.visual.bounds
                return bounds.width * bounds.height
            return 0
        
        return sorted(contexts, key=get_area, reverse=True)
    
    def _find_parent_context(self, context: EGRFContext, sorted_contexts: List[EGRFContext]) -> Optional[ContextId]:
        """Find parent context based on containment."""
        # For now, return root context (could be enhanced with actual containment logic)
        return None
    
    def _validate_final_graph(self, graph: EGGraph) -> None:
        """Validate the final assembled graph."""
        try:
            # Use existing EG-CL-Manus2 validation if available
            if hasattr(graph, 'validate'):
                result = graph.validate()
                if hasattr(result, 'errors') and result.errors:
                    self._errors.extend(result.errors)
                if hasattr(result, 'warnings') and result.warnings:
                    self._warnings.extend(result.warnings)
        except Exception as e:
            self._warnings.append(f"Final validation failed: {str(e)}")


# Convenience functions
def parse_egrf(egrf_doc: EGRFDocument, validation_enabled: bool = True) -> ParseResult:
    """
    Convenience function to parse EGRF document.
    
    Args:
        egrf_doc: EGRF document to parse
        validation_enabled: Whether to validate document
        
    Returns:
        ParseResult with graph or errors
    """
    parser = EGRFParser(validation_enabled=validation_enabled)
    return parser.parse(egrf_doc)


def parse_egrf_from_json(json_str: str, validation_enabled: bool = True) -> ParseResult:
    """
    Convenience function to parse EGRF from JSON.
    
    Args:
        json_str: JSON string containing EGRF
        validation_enabled: Whether to validate document
        
    Returns:
        ParseResult with graph or errors
    """
    parser = EGRFParser(validation_enabled=validation_enabled)
    return parser.parse_from_json(json_str)


def parse_egrf_from_file(file_path: str, validation_enabled: bool = True) -> ParseResult:
    """
    Convenience function to parse EGRF from file.
    
    Args:
        file_path: Path to EGRF file
        validation_enabled: Whether to validate document
        
    Returns:
        ParseResult with graph or errors
    """
    parser = EGRFParser(validation_enabled=validation_enabled)
    return parser.parse_from_file(file_path)

