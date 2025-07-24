#!/usr/bin/env python3
"""
EGRF Converter from EGGraph

This module provides conversion from EGGraph objects directly to EGRF format,
bypassing the problematic EG-HG file parsing. This creates a clean pipeline:
CLIF -> EGGraph -> EGRF

This solves the architectural inconsistency identified where EG-HG files
were being parsed separately instead of using the proven EGGraph model.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import uuid

from graph import EGGraph
from eg_types import Entity, Predicate, Context, EntityId, PredicateId, ContextId
from clif_parser import CLIFParser


@dataclass
class EGRFElement:
    """Base class for EGRF elements."""
    id: str
    type: str
    properties: Dict[str, Any]


@dataclass
class EGRFLogicalElement(EGRFElement):
    """EGRF element representing logical content."""
    logical_type: str
    containment_level: int
    parent_container: Optional[str] = None


@dataclass
class EGRFLayoutConstraint:
    """EGRF layout constraint."""
    constraint_type: str
    target_elements: List[str]
    parameters: Dict[str, Any]


@dataclass
class EGRFDocument:
    """Complete EGRF document structure."""
    metadata: Dict[str, Any]
    logical_elements: List[EGRFLogicalElement]
    layout_constraints: List[EGRFLayoutConstraint]
    platform_hints: Dict[str, Any]


class EGGraphToEGRFConverter:
    """
    Converts EGGraph objects to EGRF format.
    
    This converter creates the logical containment structure that EGRF v3.0
    uses for platform-independent representation of Existential Graphs.
    """
    
    def __init__(self):
        """Initialize the converter."""
        self.element_counter = 0
        self.id_mapping = {}  # Maps EGGraph IDs to EGRF IDs
    
    def convert_graph_to_egrf(self, graph: EGGraph, 
                             metadata: Optional[Dict[str, Any]] = None) -> EGRFDocument:
        """
        Convert an EGGraph to EGRF format.
        
        Args:
            graph: The EGGraph to convert
            metadata: Optional metadata for the EGRF document
            
        Returns:
            EGRFDocument containing the converted graph
        """
        # Reset state for new conversion
        self.element_counter = 0
        self.id_mapping = {}
        
        # Generate metadata
        if metadata is None:
            metadata = self._generate_default_metadata()
        
        # Convert logical elements
        logical_elements = []
        
        # Convert contexts first (they contain other elements)
        context_elements = self._convert_contexts(graph)
        logical_elements.extend(context_elements)
        
        # Convert entities
        entity_elements = self._convert_entities(graph)
        logical_elements.extend(entity_elements)
        
        # Convert predicates
        predicate_elements = self._convert_predicates(graph)
        logical_elements.extend(predicate_elements)
        
        # Generate layout constraints
        layout_constraints = self._generate_layout_constraints(graph, logical_elements)
        
        # Generate platform hints
        platform_hints = self._generate_platform_hints(graph)
        
        return EGRFDocument(
            metadata=metadata,
            logical_elements=logical_elements,
            layout_constraints=layout_constraints,
            platform_hints=platform_hints
        )
    
    def convert_clif_to_egrf(self, clif_text: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> EGRFDocument:
        """
        Convert CLIF text to EGRF format via EGGraph.
        
        Args:
            clif_text: CLIF text to convert
            metadata: Optional metadata for the EGRF document
            
        Returns:
            EGRFDocument containing the converted graph
            
        Raises:
            ValueError: If CLIF parsing fails
        """
        parser = CLIFParser()
        result = parser.parse(clif_text)
        
        if result.graph is None:
            error_msg = "Failed to parse CLIF text"
            if result.errors:
                error_msg += f": {'; '.join(result.errors)}"
            raise ValueError(error_msg)
        
        # Add CLIF text to metadata
        if metadata is None:
            metadata = {}
        metadata['source_clif'] = clif_text.strip()
        
        return self.convert_graph_to_egrf(result.graph, metadata)
    
    def _convert_contexts(self, graph: EGGraph) -> List[EGRFLogicalElement]:
        """Convert contexts to EGRF logical elements."""
        elements = []
        
        for context_id, context in graph.contexts.items():
            egrf_id = self._generate_egrf_id("context")
            self.id_mapping[context_id] = egrf_id
            
            # Determine logical type based on context type
            if context.context_type == 'sheet_of_assertion':
                logical_type = 'sheet'
            elif context.context_type == 'cut':
                logical_type = 'cut'
            else:
                logical_type = 'container'
            
            # Find parent container
            parent_container = None
            if context.parent_context:
                parent_container = self.id_mapping.get(context.parent_context)
            
            element = EGRFLogicalElement(
                id=egrf_id,
                type='logical_container',
                properties={
                    'original_id': str(context_id),
                    'context_type': context.context_type,
                    **dict(context.properties)
                },
                logical_type=logical_type,
                containment_level=context.depth,
                parent_container=parent_container
            )
            
            elements.append(element)
        
        return elements
    
    def _convert_entities(self, graph: EGGraph) -> List[EGRFLogicalElement]:
        """Convert entities to EGRF logical elements."""
        elements = []
        
        for entity_id, entity in graph.entities.items():
            egrf_id = self._generate_egrf_id("entity")
            self.id_mapping[entity_id] = egrf_id
            
            # Determine logical type
            if entity.entity_type == 'variable':
                logical_type = 'line_of_identity'
            elif entity.entity_type == 'constant':
                logical_type = 'individual'
            else:
                logical_type = 'line_of_identity'
            
            # Find containing context
            context_id = graph.context_manager.find_item_context(entity_id)
            parent_container = None
            containment_level = 0
            
            if context_id and context_id in self.id_mapping:
                parent_container = self.id_mapping[context_id]
                context = graph.contexts.get(context_id)
                if context:
                    containment_level = context.depth
            
            element = EGRFLogicalElement(
                id=egrf_id,
                type='logical_element',
                properties={
                    'original_id': str(entity_id),
                    'name': entity.name,
                    'entity_type': entity.entity_type,
                    **dict(entity.properties)
                },
                logical_type=logical_type,
                containment_level=containment_level,
                parent_container=parent_container
            )
            
            elements.append(element)
        
        return elements
    
    def _convert_predicates(self, graph: EGGraph) -> List[EGRFLogicalElement]:
        """Convert predicates to EGRF logical elements."""
        elements = []
        
        for predicate_id, predicate in graph.predicates.items():
            egrf_id = self._generate_egrf_id("predicate")
            self.id_mapping[predicate_id] = egrf_id
            
            # Determine logical type
            if predicate.predicate_type == 'function':
                logical_type = 'functional_relation'
            else:
                logical_type = 'relation'
            
            # Find containing context
            context_id = graph.context_manager.find_item_context(predicate_id)
            parent_container = None
            containment_level = 0
            
            if context_id and context_id in self.id_mapping:
                parent_container = self.id_mapping[context_id]
                context = graph.contexts.get(context_id)
                if context:
                    containment_level = context.depth
            
            # Map connected entities
            connected_entities = []
            for entity_id in predicate.entities:
                if entity_id in self.id_mapping:
                    connected_entities.append(self.id_mapping[entity_id])
            
            # Handle return entity for functions
            return_entity = None
            if predicate.return_entity and predicate.return_entity in self.id_mapping:
                return_entity = self.id_mapping[predicate.return_entity]
            
            element = EGRFLogicalElement(
                id=egrf_id,
                type='logical_element',
                properties={
                    'original_id': str(predicate_id),
                    'name': predicate.name,
                    'arity': predicate.arity,
                    'predicate_type': predicate.predicate_type,
                    'connected_entities': connected_entities,
                    'return_entity': return_entity,
                    **dict(predicate.properties)
                },
                logical_type=logical_type,
                containment_level=containment_level,
                parent_container=parent_container
            )
            
            elements.append(element)
        
        return elements
    
    def _generate_layout_constraints(self, graph: EGGraph, 
                                   logical_elements: List[EGRFLogicalElement]) -> List[EGRFLayoutConstraint]:
        """Generate layout constraints for the EGRF document."""
        constraints = []
        
        # Containment constraints
        for element in logical_elements:
            if element.parent_container:
                constraint = EGRFLayoutConstraint(
                    constraint_type='containment',
                    target_elements=[element.id],
                    parameters={
                        'container': element.parent_container,
                        'containment_level': element.containment_level
                    }
                )
                constraints.append(constraint)
        
        # Connection constraints for predicates
        for element in logical_elements:
            if element.logical_type in ['relation', 'functional_relation']:
                connected_entities = element.properties.get('connected_entities', [])
                if connected_entities:
                    constraint = EGRFLayoutConstraint(
                        constraint_type='connection',
                        target_elements=[element.id] + connected_entities,
                        parameters={
                            'relation': element.id,
                            'entities': connected_entities,
                            'connection_type': 'hyperedge'
                        }
                    )
                    constraints.append(constraint)
        
        # Nesting level constraints
        level_groups = {}
        for element in logical_elements:
            level = element.containment_level
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(element.id)
        
        for level, elements in level_groups.items():
            if len(elements) > 1:
                constraint = EGRFLayoutConstraint(
                    constraint_type='nesting_level',
                    target_elements=elements,
                    parameters={
                        'level': level,
                        'relative_positioning': 'same_level'
                    }
                )
                constraints.append(constraint)
        
        return constraints
    
    def _generate_platform_hints(self, graph: EGGraph) -> Dict[str, Any]:
        """Generate platform-specific hints."""
        return {
            'rendering_style': 'existential_graph',
            'default_layout': 'hierarchical',
            'entity_representation': 'line_of_identity',
            'predicate_representation': 'oval',
            'cut_representation': 'closed_curve',
            'suggested_dimensions': {
                'min_width': 400,
                'min_height': 300,
                'aspect_ratio': '4:3'
            },
            'interaction_hints': {
                'supports_editing': True,
                'supports_transformation_rules': True,
                'supports_animation': False
            }
        }
    
    def _generate_default_metadata(self) -> Dict[str, Any]:
        """Generate default metadata for EGRF document."""
        return {
            'id': f'egrf_document_{uuid.uuid4().hex[:8]}',
            'title': 'Existential Graph',
            'format': 'EGRF',
            'version': '3.0',
            'generated_by': 'EGGraphToEGRFConverter',
            'description': 'Existential Graph converted from EGGraph representation'
        }
    
    def _generate_egrf_id(self, prefix: str) -> str:
        """Generate a unique EGRF element ID."""
        self.element_counter += 1
        return f"{prefix}_{self.element_counter}"


def serialize_egrf_to_dict(egrf_doc: EGRFDocument) -> Dict[str, Any]:
    """
    Serialize an EGRFDocument to a dictionary format.
    
    Args:
        egrf_doc: The EGRF document to serialize
        
    Returns:
        Dictionary representation of the EGRF document
    """
    return {
        'metadata': egrf_doc.metadata,
        'logical_elements': [
            {
                'id': elem.id,
                'type': elem.type,
                'logical_type': elem.logical_type,
                'containment_level': elem.containment_level,
                'parent_container': elem.parent_container,
                'properties': elem.properties
            }
            for elem in egrf_doc.logical_elements
        ],
        'layout_constraints': [
            {
                'constraint_type': constraint.constraint_type,
                'target_elements': constraint.target_elements,
                'parameters': constraint.parameters
            }
            for constraint in egrf_doc.layout_constraints
        ],
        'platform_hints': egrf_doc.platform_hints
    }


def serialize_egrf_to_json(egrf_doc: EGRFDocument, indent: Optional[int] = 2) -> str:
    """
    Serialize an EGRFDocument to JSON format.
    
    Args:
        egrf_doc: The EGRF document to serialize
        indent: JSON indentation level
        
    Returns:
        JSON string representation of the EGRF document
    """
    import json
    return json.dumps(serialize_egrf_to_dict(egrf_doc), indent=indent)


# Convenience functions
def convert_clif_to_egrf(clif_text: str, metadata: Optional[Dict[str, Any]] = None) -> EGRFDocument:
    """
    Convert CLIF text directly to EGRF format.
    
    Args:
        clif_text: CLIF text to convert
        metadata: Optional metadata
        
    Returns:
        EGRFDocument
    """
    converter = EGGraphToEGRFConverter()
    return converter.convert_clif_to_egrf(clif_text, metadata)


def convert_graph_to_egrf(graph: EGGraph, metadata: Optional[Dict[str, Any]] = None) -> EGRFDocument:
    """
    Convert EGGraph to EGRF format.
    
    Args:
        graph: EGGraph to convert
        metadata: Optional metadata
        
    Returns:
        EGRFDocument
    """
    converter = EGGraphToEGRFConverter()
    return converter.convert_graph_to_egrf(graph, metadata)

