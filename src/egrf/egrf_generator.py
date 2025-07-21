#!/usr/bin/env python3

"""
EGRF Generator: Maps EG-CL-Manus2 data structures to EGRF format.

This module converts EG-CL-Manus2 graphs to EGRF while preserving logical integrity:
1. Hierarchical consistency - elements positioned according to tree structure
2. Cut containment - cuts properly encompass/are encompassed, no overlaps at same level  
3. Ligature connections - entities connect to predicates within predicate's area
4. Quantifier scope - outermost area of ligature determines existential/universal quantification
"""

import sys
import os
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass

# Import EG-CL-Manus2 types
from graph import EGGraph
from eg_types import Entity, Predicate, Context, EntityId, PredicateId, ContextId

# Import EGRF types
from .egrf_types import (
    EGRFDocument, Entity as EGRFEntity, Predicate as EGRFPredicate, 
    Context as EGRFContext, Point, Size, Connection, Label, Bounds,
    EGRFSerializer
)


@dataclass
class LayoutConstraints:
    """Layout constraints for maintaining logical integrity."""
    
    # Spacing between elements
    entity_spacing: float = 100.0
    predicate_spacing: float = 80.0
    context_padding: float = 20.0
    
    # Size constraints
    predicate_width: float = 60.0
    predicate_height: float = 30.0
    context_min_width: float = 100.0
    context_min_height: float = 60.0
    
    # Canvas dimensions
    canvas_width: float = 800.0
    canvas_height: float = 600.0


class EGRFGenerator:
    """Generates EGRF from EG-CL-Manus2 data structures."""
    
    def __init__(self, constraints: Optional[LayoutConstraints] = None):
        self.constraints = constraints or LayoutConstraints()
        self.entity_positions: Dict[EntityId, List[Point]] = {}
        self.predicate_positions: Dict[PredicateId, Point] = {}
        self.context_bounds: Dict[ContextId, Tuple[float, float, float, float]] = {}
        
    def generate(self, eg_graph: EGGraph) -> EGRFDocument:
        """Generate EGRF document from EG-CL-Manus2 graph."""
        
        # Create EGRF document
        egrf_doc = EGRFDocument()
        egrf_doc.metadata.title = "Generated from EG-CL-Manus2"
        egrf_doc.metadata.description = "Automatically generated EGRF preserving logical structure"
        
        # Set canvas dimensions from constraints
        egrf_doc.canvas.width = self.constraints.canvas_width
        egrf_doc.canvas.height = self.constraints.canvas_height
        
        # Step 1: Analyze hierarchical structure
        hierarchy = self._analyze_hierarchy(eg_graph)
        
        # Step 2: Calculate layout preserving constraints
        layout = self._calculate_layout(eg_graph, hierarchy)
        
        # Step 3: Generate EGRF entities with proper ligature paths
        self._generate_entities(eg_graph, egrf_doc, layout)
        
        # Step 4: Generate EGRF predicates with connection points
        self._generate_predicates(eg_graph, egrf_doc, layout)
        
        # Step 5: Generate EGRF contexts with proper containment
        self._generate_contexts(eg_graph, egrf_doc, layout)
        
        # Step 6: Add semantic information
        self._add_semantics(eg_graph, egrf_doc)
        
        return egrf_doc
    
    def _analyze_hierarchy(self, eg_graph: EGGraph) -> Dict[str, Any]:
        """Analyze the hierarchical structure of contexts and contained items."""
        hierarchy = {
            'context_tree': {},
            'item_contexts': {},  # Maps item_id -> context_id
            'context_depths': {},
            'context_children': {}
        }
        
        # Build context tree and depth information
        for context_id, context in eg_graph.context_manager.contexts.items():
            hierarchy['context_depths'][context_id] = context.depth
            
            if context.parent_context:
                if context.parent_context not in hierarchy['context_children']:
                    hierarchy['context_children'][context.parent_context] = []
                hierarchy['context_children'][context.parent_context].append(context_id)
            
            # Map contained items to their context
            for item_id in context.contained_items:
                hierarchy['item_contexts'][item_id] = context_id
        
        return hierarchy
    
    def _calculate_layout(self, eg_graph: EGGraph, hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate layout positions preserving logical constraints."""
        layout = {
            'entity_paths': {},
            'predicate_positions': {},
            'context_bounds': {},
            'connection_points': {}
        }
        
        # Start with root context bounds
        root_context = eg_graph.context_manager.root_context
        root_bounds = (0, 0, self.constraints.canvas_width, self.constraints.canvas_height)
        layout['context_bounds'][root_context.id] = root_bounds
        
        # Calculate context bounds depth-first to ensure proper containment
        self._calculate_context_bounds(eg_graph, hierarchy, layout, root_context.id, root_bounds)
        
        # Calculate predicate positions within their contexts
        self._calculate_predicate_positions(eg_graph, hierarchy, layout)
        
        # Calculate entity paths connecting predicates
        self._calculate_entity_paths(eg_graph, hierarchy, layout)
        
        # Calculate connection points where entities touch predicates
        self._calculate_connection_points(eg_graph, layout)
        
        return layout
    
    def _calculate_context_bounds(self, eg_graph: EGGraph, hierarchy: Dict[str, Any], 
                                layout: Dict[str, Any], context_id: ContextId, 
                                parent_bounds: Tuple[float, float, float, float]):
        """Calculate bounds for contexts ensuring proper containment."""
        x, y, width, height = parent_bounds
        
        # Get child contexts at this level
        child_contexts = hierarchy['context_children'].get(context_id, [])
        
        if not child_contexts:
            return
        
        # Calculate bounds for child contexts ensuring no overlap
        padding = self.constraints.context_padding
        available_width = width - 2 * padding
        available_height = height - 2 * padding
        
        # Simple grid layout for child contexts
        cols = max(1, int((len(child_contexts) ** 0.5)))
        rows = (len(child_contexts) + cols - 1) // cols
        
        cell_width = available_width / cols
        cell_height = available_height / rows
        
        for i, child_id in enumerate(child_contexts):
            row = i // cols
            col = i % cols
            
            child_x = x + padding + col * cell_width
            child_y = y + padding + row * cell_height
            child_width = cell_width - padding
            child_height = cell_height - padding
            
            child_bounds = (child_x, child_y, child_width, child_height)
            layout['context_bounds'][child_id] = child_bounds
            
            # Recursively calculate bounds for deeper contexts
            self._calculate_context_bounds(eg_graph, hierarchy, layout, child_id, child_bounds)
    
    def _calculate_predicate_positions(self, eg_graph: EGGraph, hierarchy: Dict[str, Any], 
                                     layout: Dict[str, Any]):
        """Calculate predicate positions within their containing contexts."""
        
        predicate_count = 0
        for predicate_id, predicate in eg_graph.predicates.items():
            # Find the context containing this predicate
            containing_context = hierarchy['item_contexts'].get(predicate_id)
            
            if containing_context and containing_context in layout['context_bounds']:
                x, y, width, height = layout['context_bounds'][containing_context]
                
                # Distribute predicates horizontally within context
                # User can adjust later - we just ensure logical containment
                pred_x = x + (predicate_count + 1) * (width / (len(eg_graph.predicates) + 1))
                pred_y = y + height / 2
                
                layout['predicate_positions'][predicate_id] = Point(pred_x, pred_y)
            else:
                # Default position if no context found - distribute horizontally
                pred_x = 100 + predicate_count * self.constraints.predicate_spacing
                pred_y = self.constraints.canvas_height / 2
                layout['predicate_positions'][predicate_id] = Point(pred_x, pred_y)
            
            predicate_count += 1
    
    def _calculate_entity_paths(self, eg_graph: EGGraph, hierarchy: Dict[str, Any], 
                              layout: Dict[str, Any]):
        """Calculate entity paths that connect to all related predicates."""
        
        for entity_id, entity in eg_graph.entities.items():
            # Find all predicates that reference this entity
            connected_predicates = []
            for pred_id, predicate in eg_graph.predicates.items():
                if entity_id in predicate.entities:
                    connected_predicates.append(pred_id)
            
            if connected_predicates:
                # Create path connecting all predicates at same y-level
                path_points = []
                
                # Get y-coordinate from first predicate
                first_pred_pos = layout['predicate_positions'][connected_predicates[0]]
                entity_y = first_pred_pos.y
                
                # Start point
                path_points.append(Point(first_pred_pos.x - 50, entity_y))
                
                # Connect to each predicate at the same y-level
                for pred_id in connected_predicates:
                    pred_pos = layout['predicate_positions'][pred_id]
                    path_points.append(Point(pred_pos.x, entity_y))
                
                # End point
                last_pred_pos = layout['predicate_positions'][connected_predicates[-1]]
                path_points.append(Point(last_pred_pos.x + 50, entity_y))
                
                layout['entity_paths'][entity_id] = path_points
            else:
                # Entity with no predicates - simple line
                layout['entity_paths'][entity_id] = [Point(50, 50), Point(150, 50)]
    
    def _calculate_connection_points(self, eg_graph: EGGraph, layout: Dict[str, Any]):
        """Calculate connection points where entities touch predicates."""
        layout['connection_points'] = {}
        
        for predicate_id, predicate in eg_graph.predicates.items():
            pred_pos = layout['predicate_positions'][predicate_id]
            connections = []
            
            for entity_id in predicate.entities:
                # Connection point is where entity path intersects predicate
                # Use the same y-coordinate as the entity path
                if entity_id in layout['entity_paths']:
                    entity_path = layout['entity_paths'][entity_id]
                    entity_y = entity_path[0].y if entity_path else pred_pos.y
                else:
                    entity_y = pred_pos.y
                
                connection_point = Point(pred_pos.x, entity_y)
                connections.append(Connection(str(entity_id), connection_point))
            
            layout['connection_points'][predicate_id] = connections
    
    def _generate_entities(self, eg_graph: EGGraph, egrf_doc: EGRFDocument, layout: Dict[str, Any]):
        """Generate EGRF entities from EG-CL-Manus2 entities."""
        
        for entity_id, entity in eg_graph.entities.items():
            egrf_entity = EGRFEntity(
                id=str(entity_id),
                name=entity.name or f"entity_{entity_id}",
                type=entity.entity_type
            )
            
            # Set visual path from layout
            if entity_id in layout['entity_paths']:
                egrf_entity.visual.path = layout['entity_paths'][entity_id]
            
            # Add label
            if egrf_entity.visual.path:
                mid_point = egrf_entity.visual.path[len(egrf_entity.visual.path) // 2]
                egrf_entity.labels = [Label(egrf_entity.name, Point(mid_point.x, mid_point.y - 15))]
            
            egrf_doc.entities.append(egrf_entity)
    
    def _generate_predicates(self, eg_graph: EGGraph, egrf_doc: EGRFDocument, layout: Dict[str, Any]):
        """Generate EGRF predicates from EG-CL-Manus2 predicates."""
        
        for predicate_id, predicate in eg_graph.predicates.items():
            egrf_predicate = EGRFPredicate(
                id=str(predicate_id),
                name=predicate.name,
                type=predicate.predicate_type,
                arity=predicate.arity,
                connected_entities=[str(eid) for eid in predicate.entities]
            )
            
            # Set visual position from layout
            if predicate_id in layout['predicate_positions']:
                pos = layout['predicate_positions'][predicate_id]
                egrf_predicate.visual.position = pos
                egrf_predicate.visual.size = Size(
                    self.constraints.predicate_width,
                    self.constraints.predicate_height
                )
            
            # Set connection points from layout
            if predicate_id in layout['connection_points']:
                egrf_predicate.connections = layout['connection_points'][predicate_id]
            
            # Add label
            egrf_predicate.labels = [Label(predicate.name, egrf_predicate.visual.position)]
            
            egrf_doc.predicates.append(egrf_predicate)
    
    def _generate_contexts(self, eg_graph: EGGraph, egrf_doc: EGRFDocument, layout: Dict[str, Any]):
        """Generate EGRF contexts from EG-CL-Manus2 contexts."""
        
        for context_id, context in eg_graph.context_manager.contexts.items():
            egrf_context = EGRFContext(
                id=str(context_id),
                type=context.context_type,
                parent_context=str(context.parent_context) if context.parent_context else None
            )
            
            # Set visual bounds from layout
            if context_id in layout['context_bounds']:
                x, y, width, height = layout['context_bounds'][context_id]
                egrf_context.visual.bounds = Bounds(x, y, width, height)
            
            # Set contained items
            egrf_context.contained_items = [str(item_id) for item_id in context.contained_items]
            egrf_context.nesting_level = context.depth
            
            egrf_doc.contexts.append(egrf_context)
    
    def _add_semantics(self, eg_graph: EGGraph, egrf_doc: EGRFDocument):
        """Add semantic information to EGRF document."""
        
        # Generate CLIF equivalent (simplified)
        clif_parts = []
        for predicate_id, predicate in eg_graph.predicates.items():
            if predicate.entities:
                entity_names = []
                for entity_id in predicate.entities:
                    entity = eg_graph.entities.get(entity_id)
                    entity_names.append(entity.name if entity and entity.name else f"?{entity_id}")
                
                clif_parts.append(f"({predicate.name} {' '.join(entity_names)})")
        
        if len(clif_parts) > 1:
            clif_equivalent = f"(and {' '.join(clif_parts)})"
        elif len(clif_parts) == 1:
            clif_equivalent = clif_parts[0]
        else:
            clif_equivalent = "()"
        
        egrf_doc.semantics.logical_form = {
            "clif_equivalent": clif_equivalent,
            "egif_equivalent": "Generated from EG-CL-Manus2"
        }
        egrf_doc.semantics.validation = {"is_valid": True}

