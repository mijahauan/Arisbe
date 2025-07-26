#!/usr/bin/env python3
"""
Direct EGGraph to EGRF v3.0 Converter

This module provides direct conversion from EGGraph objects to EGRF v3.0 format
without intermediary dictionary representations, minimizing complexity and points of failure.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from graph import EGGraph
from eg_types import Entity, Predicate, Context, Ligature

from ..logical_types import (
    create_logical_context, create_logical_predicate, create_logical_entity,
    LogicalElement, LogicalContext, LogicalPredicate, LogicalEntity,
    ContainmentRelationship
)
from ..containment_hierarchy import ContainmentHierarchyManager


class DirectGraphToEgrfConverter:
    """
    Direct converter from EGGraph to EGRF v3.0 format.
    
    This converter works directly with EGGraph objects, eliminating the need
    for intermediary dictionary representations and reducing complexity.
    """
    
    def __init__(self):
        """Initialize the converter."""
        self._egrf_data = {
            "metadata": {
                "version": "3.0.0",
                "format": "egrf",
                "id": "",
                "description": ""
            },
            "elements": {},
            "containment": {},
            "connections": [],
            "ligatures": [],
            "layout_constraints": []
        }
        self._context_map = {}  # Maps EGGraph context IDs to EGRF IDs
        self._predicate_map = {}  # Maps EGGraph predicate IDs to EGRF IDs
        self._entity_map = {}  # Maps EGGraph entity IDs to EGRF IDs
        self._hierarchy_manager = ContainmentHierarchyManager()
    
    def convert(self, graph: EGGraph, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert an EGGraph to EGRF v3.0 format using proper API.
        
        Args:
            graph: The EGGraph object to convert
            metadata: Optional metadata for the EGRF document
            
        Returns:
            Dictionary containing EGRF v3.0 data
        """
        # Reset state for new conversion
        self._reset_state()
        
        # Set metadata
        if metadata:
            self._egrf_data["metadata"]["id"] = metadata.get("id", "graph")
            self._egrf_data["metadata"]["description"] = metadata.get("description", "Existential Graph")
        
        # Process graph components using proper EG-HG API
        self._process_contexts_properly(graph)
        self._process_predicates_properly(graph)
        self._process_entities_properly(graph)
        self._process_ligatures_properly(graph)
        self._process_connections_properly(graph)
        self._generate_layout_constraints()
        
        return self._egrf_data
    
    def _reset_state(self) -> None:
        """Reset converter state for new conversion."""
        self._egrf_data = {
            "metadata": {
                "version": "3.0.0",
                "format": "egrf",
                "id": "",
                "description": ""
            },
            "elements": {},
            "containment": {},
            "connections": [],
            "ligatures": [],
            "layout_constraints": []
        }
        self._context_map = {}
        self._predicate_map = {}
        self._entity_map = {}
        self._hierarchy_manager = ContainmentHierarchyManager()
    
    def _process_contexts_properly(self, graph: EGGraph) -> None:
        """Process contexts using proper EG-HG API for hierarchy."""
        
        # Create the root sheet context first
        sheet_id = "sheet"
        root_context = graph.context_manager.root_context
        
        sheet = create_logical_context(
            id=sheet_id,
            name="Sheet of Assertion",
            container="none",
            context_type="sheet_of_assertion",
            is_root=True,
            nesting_level=0
        )
        
        self._egrf_data["elements"][sheet_id] = sheet.to_dict()
        self._context_map[root_context.id] = sheet_id
        self._hierarchy_manager.add_element(sheet)
        
        # Get all non-root contexts and sort by depth (shallowest first for proper parent mapping)
        non_root_contexts = [(context_id, context) for context_id, context in graph.contexts.items() 
                           if context_id != root_context.id]
        
        # Sort by depth to ensure parents are processed before children
        non_root_contexts.sort(key=lambda x: x[1].depth)
        
        # Process contexts in depth order
        for context_id, context in non_root_contexts:
            egrf_id = f"context_{context_id}"
            self._context_map[context_id] = egrf_id
            
            # Get parent context using EG-HG API
            parent_egrf_id = sheet_id  # Default fallback
            if context.parent_context is not None:
                parent_egrf_id = self._context_map.get(context.parent_context, sheet_id)
            
            # Use depth directly from EG-HG
            nesting_level = context.depth
            
            # Determine context name based on semantic role
            context_name = self._determine_context_name(context, nesting_level)
            
            # Create logical context
            logical_context = create_logical_context(
                id=egrf_id,
                name=context_name,
                container=parent_egrf_id,
                context_type="cut",
                is_root=False,
                nesting_level=nesting_level
            )
            
            self._egrf_data["elements"][egrf_id] = logical_context.to_dict()
            self._egrf_data["containment"][egrf_id] = parent_egrf_id
            self._hierarchy_manager.add_element(logical_context)
            
            # Add containment relationship
            relationship = ContainmentRelationship(
                container=parent_egrf_id,
                contained_elements=[egrf_id]
            )
            self._hierarchy_manager.add_relationship(relationship)
    
    def _process_predicates_properly(self, graph: EGGraph) -> None:
        """Process predicates using proper EG-HG API for containment."""
        for predicate_id, predicate in graph.predicates.items():
            egrf_id = f"predicate_{predicate_id}"
            self._predicate_map[predicate_id] = egrf_id
            
            # Find containing context using EG-HG API
            containing_context = self._find_containing_context_properly(graph, predicate_id)
            
            # Create logical predicate
            logical_predicate = create_logical_predicate(
                id=egrf_id,
                name=predicate.name,
                container=containing_context,
                arity=predicate.arity
            )
            
            self._egrf_data["elements"][egrf_id] = logical_predicate.to_dict()
            self._egrf_data["containment"][egrf_id] = containing_context
            self._hierarchy_manager.add_element(logical_predicate)
            
            # Add containment relationship
            relationship = ContainmentRelationship(
                container=containing_context,
                contained_elements=[egrf_id]
            )
            self._hierarchy_manager.add_relationship(relationship)
    
    def _process_entities_properly(self, graph: EGGraph) -> None:
        """Process entities using proper EG-HG API for containment."""
        for entity_id, entity in graph.entities.items():
            egrf_id = f"entity_{entity_id}"
            self._entity_map[entity_id] = egrf_id
            
            # Find containing context using EG-HG API
            containing_context = self._find_containing_context_properly(graph, entity_id)
            
            # Determine entity type and name
            entity_name = getattr(entity, 'name', f"Entity {entity_id}")
            entity_type = getattr(entity, 'entity_type', 'constant')
            
            # Get connected predicates for this entity
            connected_predicates = []
            try:
                # Use the EG-HG method to find connected predicates
                for predicate_id, predicate in graph.predicates.items():
                    if entity_id in predicate.entities:
                        egrf_predicate_id = self._predicate_map.get(predicate_id)
                        if egrf_predicate_id:
                            connected_predicates.append(egrf_predicate_id)
            except Exception:
                connected_predicates = []
            
            # Create logical entity
            logical_entity = create_logical_entity(
                id=egrf_id,
                name=entity_name,
                connected_predicates=connected_predicates,
                entity_type=entity_type
            )
            
            self._egrf_data["elements"][egrf_id] = logical_entity.to_dict()
            self._egrf_data["containment"][egrf_id] = containing_context
            self._hierarchy_manager.add_element(logical_entity)
            
            # Add containment relationship
            relationship = ContainmentRelationship(
                container=containing_context,
                contained_elements=[egrf_id]
            )
            self._hierarchy_manager.add_relationship(relationship)
    
    def _process_ligatures_properly(self, graph: EGGraph) -> None:
        """Process ligatures using proper EG-HG API."""
        for ligature_id, ligature in graph.ligatures.items():
            # Map entity IDs to EGRF IDs
            egrf_entity1_id = self._entity_map.get(ligature.entity1_id)
            egrf_entity2_id = self._entity_map.get(ligature.entity2_id)
            
            if egrf_entity1_id and egrf_entity2_id:
                ligature_data = {
                    "id": f"ligature_{ligature_id}",
                    "entity1": egrf_entity1_id,
                    "entity2": egrf_entity2_id,
                    "type": "identity"
                }
                self._egrf_data["ligatures"].append(ligature_data)
    
    def _process_connections_properly(self, graph: EGGraph) -> None:
        """Process connections using proper EG-HG API."""
        for predicate_id, predicate in graph.predicates.items():
            egrf_predicate_id = self._predicate_map.get(predicate_id)
            if not egrf_predicate_id:
                continue
            
            # Get entities connected to this predicate using EG-HG API
            for i, entity_id in enumerate(predicate.entities):
                egrf_entity_id = self._entity_map.get(entity_id)
                if egrf_entity_id:
                    connection = {
                        "predicate": egrf_predicate_id,
                        "entity": egrf_entity_id,
                        "role": i,
                        "type": "argument"
                    }
                    self._egrf_data["connections"].append(connection)
    
    def _find_containing_context_properly(self, graph: EGGraph, item_id: str) -> str:
        """Find the context that contains an item using proper EG-HG API."""
        # Check each context to see if it contains this item
        for context_id, context in graph.contexts.items():
            if item_id in context.contained_items:
                # Found the containing context, map to EGRF ID
                return self._context_map.get(context_id, "sheet")
        
        # If not found in any context, default to sheet
        return "sheet"
    
    def _determine_context_name(self, context: Context, nesting_level: int) -> str:
        """Determine appropriate name for context based on its role and properties."""
        # Check if context has a name property
        if 'name' in context.properties:
            return context.properties['name']
        
        # Use context type if available
        if hasattr(context, 'context_type') and context.context_type != 'cut':
            return context.context_type.replace('_', ' ').title()
        
        # Default naming based on nesting level
        if nesting_level == 1:
            return "Outer Cut"
        elif nesting_level == 2:
            return "Inner Cut"
        else:
            return f"Cut Level {nesting_level}"
    
    def _generate_layout_constraints(self) -> None:
        """Generate basic layout constraints for the EGRF data."""
        # Add basic spacing constraints
        self._egrf_data["layout_constraints"].append({
            "type": "spacing",
            "elements": "all",
            "minimum_distance": 20
        })
        
        # Add containment constraints
        for element_id, container in self._egrf_data["containment"].items():
            if container != "none":
                self._egrf_data["layout_constraints"].append({
                    "type": "containment",
                    "element": element_id,
                    "container": container,
                    "margin": 10
                })


def convert_graph_to_egrf_direct(graph: EGGraph, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to convert an EGGraph directly to EGRF v3.0 format.
    
    Args:
        graph: The EGGraph object to convert
        metadata: Optional metadata for the EGRF document
        
    Returns:
        Dictionary containing EGRF v3.0 data
    """
    converter = DirectGraphToEgrfConverter()
    return converter.convert(graph, metadata)

