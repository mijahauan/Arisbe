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
        Convert an EGGraph directly to EGRF v3.0 format.
        
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
        
        # Process graph components directly
        self._process_contexts_direct(graph)
        self._process_predicates_direct(graph)
        self._process_entities_direct(graph)
        self._process_ligatures_direct(graph)
        self._process_connections_direct(graph)
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
    
    def _process_contexts_direct(self, graph: EGGraph) -> None:
        """Process contexts directly from EGGraph."""
        # Always create the root sheet context
        sheet_id = "sheet"
        sheet = create_logical_context(
            id=sheet_id,
            name="Sheet of Assertion",
            container="none",
            context_type="sheet_of_assertion",
            is_root=True,
            nesting_level=0
        )
        
        self._egrf_data["elements"][sheet_id] = sheet.to_dict()
        self._context_map[graph.root_context_id] = sheet_id
        self._hierarchy_manager.add_element(sheet)
        
        # Process other contexts (cuts)
        for context_id, context in graph.contexts.items():
            if context_id != graph.root_context_id:
                egrf_id = f"context_{context_id}"
                self._context_map[context_id] = egrf_id
                
                # Determine parent context
                parent_egrf_id = sheet_id  # Default to sheet
                if hasattr(context, 'parent_id') and context.parent_id:
                    parent_egrf_id = self._context_map.get(context.parent_id, sheet_id)
                
                # Calculate nesting level
                nesting_level = self._calculate_nesting_level(graph, context_id)
                
                # Create logical context
                logical_context = create_logical_context(
                    id=egrf_id,
                    name=f"Cut {context_id}",
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
    
    def _process_predicates_direct(self, graph: EGGraph) -> None:
        """Process predicates directly from EGGraph."""
        for predicate_id, predicate in graph.predicates.items():
            egrf_id = f"predicate_{predicate_id}"
            self._predicate_map[predicate_id] = egrf_id
            
            # Find containing context
            containing_context = self._find_containing_context(graph, predicate_id, 'predicate')
            
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
    
    def _process_entities_direct(self, graph: EGGraph) -> None:
        """Process entities directly from EGGraph."""
        for entity_id, entity in graph.entities.items():
            egrf_id = f"entity_{entity_id}"
            self._entity_map[entity_id] = egrf_id
            
            # Find containing context
            containing_context = self._find_containing_context(graph, entity_id, 'entity')
            
            # Determine entity type and name
            entity_name = getattr(entity, 'name', f"Entity {entity_id}")
            entity_type = getattr(entity, 'entity_type', 'constant')
            
            # Get connected predicates for this entity
            connected_predicates = []
            try:
                connected_predicates = [self._predicate_map.get(pred_id, pred_id) 
                                      for pred_id in graph.find_predicates_for_entity(entity_id)]
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
    
    def _process_ligatures_direct(self, graph: EGGraph) -> None:
        """Process ligatures directly from EGGraph."""
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
    
    def _process_connections_direct(self, graph: EGGraph) -> None:
        """Process connections between predicates and entities directly from EGGraph."""
        for predicate_id, predicate in graph.predicates.items():
            egrf_predicate_id = self._predicate_map.get(predicate_id)
            if not egrf_predicate_id:
                continue
            
            # Get entities connected to this predicate
            try:
                connected_entities = graph.get_entities_in_predicate(predicate_id)
                
                for i, entity_id in enumerate(connected_entities):
                    egrf_entity_id = self._entity_map.get(entity_id)
                    if egrf_entity_id:
                        connection = {
                            "predicate": egrf_predicate_id,
                            "entity": egrf_entity_id,
                            "role": i,
                            "type": "argument"
                        }
                        self._egrf_data["connections"].append(connection)
                        
            except Exception:
                # If we can't get entities for this predicate, skip it
                continue
    
    def _find_containing_context(self, graph: EGGraph, item_id: str, item_type: str) -> str:
        """Find the context that contains a given item."""
        try:
            if item_type == 'predicate':
                # Find contexts containing this predicate
                for context_id in graph.contexts.keys():
                    try:
                        predicates_in_context = graph.get_predicates_in_context(context_id)
                        if item_id in predicates_in_context:
                            return self._context_map.get(context_id, "sheet")
                    except Exception:
                        continue
                        
            elif item_type == 'entity':
                # Find contexts containing this entity
                for context_id in graph.contexts.keys():
                    try:
                        entities_in_context = graph.get_entities_in_context(context_id)
                        if item_id in entities_in_context:
                            return self._context_map.get(context_id, "sheet")
                    except Exception:
                        continue
            
            # Fallback to sheet
            return "sheet"
            
        except Exception:
            # Ultimate fallback
            return "sheet"
    
    def _calculate_nesting_level(self, graph: EGGraph, context_id: str) -> int:
        """Calculate the nesting level of a context."""
        if context_id == graph.root_context_id:
            return 0
        
        # Simple implementation - could be enhanced based on actual hierarchy
        try:
            context = graph.contexts.get(context_id)
            if hasattr(context, 'parent_id') and context.parent_id:
                if context.parent_id == graph.root_context_id:
                    return 1
                else:
                    return 1 + self._calculate_nesting_level(graph, context.parent_id)
            else:
                return 1
        except Exception:
            return 1
    
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

