#!/usr/bin/env python3
"""
EG-HG YAML Serialization Module

This module provides canonical YAML serialization for EGGraph objects,
creating a human-readable, version-control-friendly format for storing
and exchanging Existential Graph hypergraph data.

The YAML format preserves all EG semantic information while being
suitable for scholarly workflows, corpus management, and collaborative development.
"""

import yaml
import uuid
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import asdict, replace
from pathlib import Path

from eg_types import (
    Entity, Predicate, Context, Ligature,
    EntityId, PredicateId, ContextId, LigatureId,
    new_entity_id, new_predicate_id, new_context_id, new_ligature_id,
    ValidationError, pmap, pset, pvector
)
from graph import EGGraph
from context import ContextManager


class EGYAMLError(Exception):
    """Exception raised for YAML serialization/deserialization errors."""
    pass


class EGGraphYAMLSerializer:
    """
    Serializer for converting EGGraph objects to/from canonical YAML format.
    
    The YAML format is designed to be:
    - Human-readable and editable
    - Version control friendly
    - Schema-validatable
    - Preserving all EG semantic information
    """
    
    def __init__(self):
        """Initialize the serializer."""
        self.id_mapping = {}  # Maps UUIDs to human-readable names
        self.reverse_mapping = {}  # Maps names back to UUIDs
        self.counter = 0
    
    def serialize_to_yaml(self, graph: EGGraph, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Convert an EGGraph to canonical YAML format.
        
        Args:
            graph: The EGGraph to serialize
            metadata: Optional metadata to include in the YAML
            
        Returns:
            YAML string representation of the graph
        """
        # Reset mappings for each serialization
        self.id_mapping = {}
        self.reverse_mapping = {}
        self.counter = 0
        
        # Build the YAML structure
        yaml_data = {
            'metadata': metadata or {
                'id': f'eg_graph_{uuid.uuid4().hex[:8]}',
                'title': 'Existential Graph',
                'description': 'Generated from EGGraph',
                'format_version': '1.0'
            },
            'entities': self._serialize_entities(graph),
            'predicates': self._serialize_predicates(graph),
            'contexts': self._serialize_contexts(graph),
            'ligatures': self._serialize_ligatures(graph)
        }
        
        # Convert to YAML with custom formatting
        return yaml.dump(
            yaml_data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
            indent=2
        )
    
    def deserialize_from_yaml(self, yaml_content: str) -> EGGraph:
        """
        Convert YAML content to an EGGraph.
        
        Args:
            yaml_content: YAML string to deserialize
            
        Returns:
            EGGraph object
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise EGYAMLError(f"Invalid YAML format: {e}")
        
        # Validate required sections
        required_sections = ['entities', 'predicates', 'contexts']
        for section in required_sections:
            if section not in data:
                raise EGYAMLError(f"Missing required section: {section}")
        
        # Reset mappings for deserialization
        self.id_mapping = {}
        self.reverse_mapping = {}
        
        # Check if we have contexts in the YAML
        contexts_data = data.get('contexts', {})
        
        if contexts_data:
            # Start with completely empty graph (no default root context)
            from context import ContextManager
            
            # Create a truly empty context manager by bypassing __post_init__
            # We'll manually set the contexts after deserializing from YAML
            empty_context_manager = object.__new__(ContextManager)
            object.__setattr__(empty_context_manager, 'contexts', pmap())
            object.__setattr__(empty_context_manager, 'root_context', None)
            
            graph = EGGraph(
                context_manager=empty_context_manager,
                nodes=pmap(),
                edges=pmap(),
                ligatures=pmap(),
                entities=pmap(),
                predicates=pmap()
            )
            
            # Deserialize contexts from YAML - this will create the proper contexts
            graph = self._deserialize_contexts(graph, contexts_data)
            
            # Find and set the root context (depth 0, no parent) BEFORE deserializing entities
            root_context = None
            for ctx_id, ctx in graph.contexts.items():
                if ctx.depth == 0 and ctx.parent_context is None:
                    root_context = ctx
                    break
            
            if root_context:
                # Update the context manager to use this as root
                graph = replace(graph, 
                              context_manager=replace(graph.context_manager, 
                                                    root_context=root_context))
            else:
                # If no root context found, create one from the first context
                if graph.contexts:
                    first_context = next(iter(graph.contexts.values()))
                    graph = replace(graph, 
                                  context_manager=replace(graph.context_manager, 
                                                        root_context=first_context))
        else:
            # No contexts in YAML, start with default empty graph
            graph = EGGraph.create_empty()
        
        # Deserialize other components
        graph = self._deserialize_entities(graph, data['entities'])
        graph = self._deserialize_predicates(graph, data['predicates'])
        graph = self._deserialize_ligatures(graph, data.get('ligatures', []))
        
        return graph
    
    def _serialize_entities(self, graph: EGGraph) -> Dict[str, Any]:
        """Serialize entities to YAML format."""
        entities = {}
        
        for entity_id, entity in graph.entities.items():
            # Generate human-readable name
            name = self._get_readable_name(entity_id, 'entity', entity.name)
            
            entities[name] = {
                'name': entity.name,
                'type': entity.entity_type,
                'properties': dict(entity.properties) if entity.properties else {}
            }
            
            # Add context information
            context_id = graph.context_manager.find_item_context(entity_id)
            if context_id:
                context_name = self._get_readable_name(context_id, 'context')
                entities[name]['context'] = context_name
        
        return entities
    
    def _serialize_predicates(self, graph: EGGraph) -> Dict[str, Any]:
        """Serialize predicates to YAML format."""
        predicates = {}
        
        for predicate_id, predicate in graph.predicates.items():
            # Generate human-readable name
            name = self._get_readable_name(predicate_id, 'predicate', predicate.name)
            
            # Map entity IDs to readable names
            entity_names = []
            for entity_id in predicate.entities:
                entity_name = self._get_readable_name(entity_id, 'entity')
                entity_names.append(entity_name)
            
            predicates[name] = {
                'name': predicate.name,
                'arity': predicate.arity,
                'entities': entity_names,
                'type': getattr(predicate, 'predicate_type', 'relation'),
                'properties': dict(predicate.properties) if predicate.properties else {}
            }
            
            # Add return entity for functions
            if hasattr(predicate, 'return_entity') and predicate.return_entity:
                return_name = self._get_readable_name(predicate.return_entity, 'entity')
                predicates[name]['return_entity'] = return_name
            
            # Add context information
            context_id = graph.context_manager.find_item_context(predicate_id)
            if context_id:
                context_name = self._get_readable_name(context_id, 'context')
                predicates[name]['context'] = context_name
        
        return predicates
    
    def _serialize_contexts(self, graph: EGGraph) -> Dict[str, Any]:
        """Serialize contexts to YAML format."""
        contexts = {}
        
        for context_id, context in graph.contexts.items():
            # Generate human-readable name
            name = self._get_readable_name(context_id, 'context', context.context_type)
            
            context_data = {
                'type': context.context_type,
                'nesting_level': context.depth,
                'properties': dict(context.properties) if context.properties else {}
            }
            
            # Add parent context
            if context.parent_context:
                parent_name = self._get_readable_name(context.parent_context, 'context')
                context_data['parent'] = parent_name
            
            # Add contained items
            contained_items = []
            for item_id in context.contained_items:
                if item_id in graph.entities:
                    item_name = self._get_readable_name(item_id, 'entity')
                elif item_id in graph.predicates:
                    item_name = self._get_readable_name(item_id, 'predicate')
                elif item_id in graph.contexts:
                    item_name = self._get_readable_name(item_id, 'context')
                else:
                    continue  # Skip unknown items
                contained_items.append(item_name)
            
            if contained_items:
                context_data['contains'] = contained_items
            
            contexts[name] = context_data
        
        return contexts
    
    def _serialize_ligatures(self, graph: EGGraph) -> List[Dict[str, Any]]:
        """Serialize ligatures to YAML format."""
        ligatures = []
        
        for ligature_id, ligature in graph.ligatures.items():
            # Map node and edge IDs to readable names
            entity_names = []
            for node_id in ligature.nodes:
                if node_id in graph.entities:
                    entity_name = self._get_readable_name(node_id, 'entity')
                    entity_names.append(entity_name)
            
            predicate_names = []
            for edge_id in ligature.edges:
                if edge_id in graph.predicates:
                    predicate_name = self._get_readable_name(edge_id, 'predicate')
                    predicate_names.append(predicate_name)
            
            ligature_data = {
                'type': 'identity',
                'properties': dict(ligature.properties) if ligature.properties else {}
            }
            
            if entity_names:
                ligature_data['entities'] = entity_names
            if predicate_names:
                ligature_data['predicates'] = predicate_names
            
            ligatures.append(ligature_data)
        
        return ligatures
    
    def _deserialize_contexts(self, graph: EGGraph, contexts_data: Dict[str, Any]) -> EGGraph:
        """Deserialize contexts from YAML data."""
        # Start with empty context manager
        context_manager = graph.context_manager
        
        # First pass: create all contexts
        for context_name, context_data in contexts_data.items():
            context_id = new_context_id()
            self.reverse_mapping[context_name] = context_id
            
            # Create context (parent will be set in second pass)
            context = Context.create(
                context_type=context_data['type'],
                depth=context_data.get('nesting_level', 0),
                properties=context_data.get('properties', {}),
                id=context_id
            )
            
            # Add context to manager
            context_manager = context_manager.add_context(context)
        
        # Update graph with new context manager
        graph = replace(graph, context_manager=context_manager)
        
        # Second pass: establish parent relationships
        for context_name, context_data in contexts_data.items():
            if 'parent' in context_data:
                context_id = self.reverse_mapping[context_name]
                parent_id = self.reverse_mapping[context_data['parent']]
                
                # Update context with parent
                context = graph.contexts[context_id]
                updated_context = replace(context, parent_context=parent_id)
                context_manager = graph.context_manager.add_context(updated_context)
                graph = replace(graph, context_manager=context_manager)
        
        return graph
    
    def _deserialize_entities(self, graph: EGGraph, entities_data: Dict[str, Any]) -> EGGraph:
        """Deserialize entities from YAML data."""
        for entity_name, entity_data in entities_data.items():
            entity_id = new_entity_id()
            self.reverse_mapping[entity_name] = entity_id
            
            # Create entity
            entity = Entity.create(
                name=entity_data.get('name'),
                entity_type=entity_data.get('type', 'anonymous'),
                properties=entity_data.get('properties', {}),
                id=entity_id
            )
            
            # Determine context - use the first available context if root_context_id is None
            context_id = graph.root_context_id
            if context_id is None and graph.contexts:
                # Use the first context as fallback
                context_id = next(iter(graph.contexts.keys()))
            
            if 'context' in entity_data:
                mapped_context_id = self.reverse_mapping.get(entity_data['context'])
                if mapped_context_id and mapped_context_id in graph.contexts:
                    context_id = mapped_context_id
            
            # Ensure we have a valid context
            if context_id is None or context_id not in graph.contexts:
                raise EGYAMLError(f"No valid context found for entity {entity_name}")
            
            # Add to graph
            graph = graph.add_entity(entity, context_id)
        
        return graph
    
    def _deserialize_predicates(self, graph: EGGraph, predicates_data: Dict[str, Any]) -> EGGraph:
        """Deserialize predicates from YAML data."""
        for predicate_name, predicate_data in predicates_data.items():
            predicate_id = new_predicate_id()
            self.reverse_mapping[predicate_name] = predicate_id
            
            # Map entity names to IDs
            entity_ids = []
            for entity_name in predicate_data.get('entities', []):
                if entity_name in self.reverse_mapping:
                    entity_ids.append(self.reverse_mapping[entity_name])
            
            # Handle return entity for functions
            return_entity = None
            if 'return_entity' in predicate_data:
                return_entity = self.reverse_mapping.get(predicate_data['return_entity'])
            
            # Create predicate
            predicate = Predicate.create(
                name=predicate_data['name'],
                entities=entity_ids,
                arity=predicate_data.get('arity', len(entity_ids)),
                predicate_type=predicate_data.get('type', 'relation'),
                return_entity=return_entity,
                properties=predicate_data.get('properties', {}),
                id=predicate_id
            )
            
            # Determine context - use the first available context if root_context_id is None
            context_id = graph.root_context_id
            if context_id is None and graph.contexts:
                # Use the first context as fallback
                context_id = next(iter(graph.contexts.keys()))
            
            if 'context' in predicate_data:
                mapped_context_id = self.reverse_mapping.get(predicate_data['context'])
                if mapped_context_id and mapped_context_id in graph.contexts:
                    context_id = mapped_context_id
            
            # Ensure we have a valid context
            if context_id is None or context_id not in graph.contexts:
                raise EGYAMLError(f"No valid context found for predicate {predicate_name}")
            
            # Add to graph
            graph = graph.add_predicate(predicate, context_id)
        
        return graph
    
    def _deserialize_ligatures(self, graph: EGGraph, ligatures_data: List[Dict[str, Any]]) -> EGGraph:
        """Deserialize ligatures from YAML data."""
        for ligature_data in ligatures_data:
            ligature_id = new_ligature_id()
            
            # Map entity and predicate names to IDs
            entity_ids = set()
            for entity_name in ligature_data.get('entities', []):
                if entity_name in self.reverse_mapping:
                    entity_ids.add(self.reverse_mapping[entity_name])
            
            predicate_ids = set()
            for predicate_name in ligature_data.get('predicates', []):
                if predicate_name in self.reverse_mapping:
                    predicate_ids.add(self.reverse_mapping[predicate_name])
            
            # Create ligature
            ligature = Ligature.create(
                nodes=entity_ids,
                edges=predicate_ids,
                properties=ligature_data.get('properties', {}),
                id=ligature_id
            )
            
            # Add to graph
            graph = graph.add_ligature(ligature)
        
        return graph
    
    def _get_readable_name(self, item_id: Union[EntityId, PredicateId, ContextId], 
                          item_type: str, base_name: Optional[str] = None) -> str:
        """Generate a human-readable name for an item ID."""
        if item_id in self.id_mapping:
            return self.id_mapping[item_id]
        
        # Generate name based on type and base name
        if base_name and base_name.strip():
            # Clean the name to make it a valid identifier
            clean_name = self._clean_identifier(base_name)
            candidate = f"{clean_name}_{item_type}"
        else:
            # Generate generic name
            candidate = f"{item_type}_{self.counter}"
            self.counter += 1
        
        # Ensure uniqueness
        original_candidate = candidate
        counter = 1
        while candidate in self.reverse_mapping:
            candidate = f"{original_candidate}_{counter}"
            counter += 1
        
        # Store mapping
        self.id_mapping[item_id] = candidate
        self.reverse_mapping[candidate] = item_id
        
        return candidate
    
    def _clean_identifier(self, name: str) -> str:
        """Clean a name to make it a valid identifier."""
        import re
        
        # Remove namespace prefixes like "cl:"
        if ':' in name:
            name = name.split(':')[-1]
        
        # Remove parentheses and their contents
        name = re.sub(r'\([^)]*\)', '', name)
        
        # Replace invalid characters with underscores
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        # Remove multiple consecutive underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        # Ensure it starts with a letter or underscore
        if name and name[0].isdigit():
            name = f"_{name}"
        
        # Fallback if empty
        if not name:
            name = "item"
        
        return name.lower()


# Convenience functions
def serialize_graph_to_yaml(graph: EGGraph, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Serialize an EGGraph to YAML format.
    
    Args:
        graph: The EGGraph to serialize
        metadata: Optional metadata to include
        
    Returns:
        YAML string representation
    """
    serializer = EGGraphYAMLSerializer()
    return serializer.serialize_to_yaml(graph, metadata)


def deserialize_graph_from_yaml(yaml_content: str) -> EGGraph:
    """
    Deserialize an EGGraph from YAML format.
    
    Args:
        yaml_content: YAML string to deserialize
        
    Returns:
        EGGraph object
    """
    serializer = EGGraphYAMLSerializer()
    return serializer.deserialize_from_yaml(yaml_content)


def save_graph_to_file(graph: EGGraph, filepath: Union[str, Path], 
                      metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Save an EGGraph to a YAML file.
    
    Args:
        graph: The EGGraph to save
        filepath: Path to save the file
        metadata: Optional metadata to include
    """
    yaml_content = serialize_graph_to_yaml(graph, metadata)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(yaml_content)


def load_graph_from_file(filepath: Union[str, Path]) -> EGGraph:
    """
    Load an EGGraph from a YAML file.
    
    Args:
        filepath: Path to the YAML file
        
    Returns:
        EGGraph object
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        yaml_content = f.read()
    
    return deserialize_graph_from_yaml(yaml_content)


# Add methods to EGGraph class
def _add_yaml_methods_to_egraph():
    """Add YAML serialization methods to EGGraph class."""
    
    def to_yaml(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Convert this graph to YAML format."""
        return serialize_graph_to_yaml(self, metadata)
    
    def save_yaml(self, filepath: Union[str, Path], 
                  metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save this graph to a YAML file."""
        save_graph_to_file(self, filepath, metadata)
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'EGGraph':
        """Create an EGGraph from YAML content."""
        return deserialize_graph_from_yaml(yaml_content)
    
    @classmethod
    def load_yaml(cls, filepath: Union[str, Path]) -> 'EGGraph':
        """Load an EGGraph from a YAML file."""
        return load_graph_from_file(filepath)
    
    # Add methods to EGGraph class
    EGGraph.to_yaml = to_yaml
    EGGraph.save_yaml = save_yaml
    EGGraph.from_yaml = from_yaml
    EGGraph.load_yaml = load_yaml


# Initialize the methods when module is imported
_add_yaml_methods_to_egraph()

