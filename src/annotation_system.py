#!/usr/bin/env python3
"""
Annotation System for Existential Graph Diagrams

This module provides the core data structures and functionality for adding
optional annotations to EG diagrams. Annotations are analysis tools that can
be toggled on/off without affecting the base diagram logic.

Design Principles:
- Default rendering is clean and uncluttered (Dau's aesthetic)
- Annotations are optional overlays for analysis
- Multiple annotation types can be layered
- Annotations preserve EGI mathematical integrity
"""

from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
import os

# Import the contract system
sys.path.insert(0, os.path.dirname(__file__))
from pipeline_contracts import AnnotationType, AnnotationConfig, AnnotationLayer

@dataclass
class AnnotationPrimitive:
    """A visual annotation element to be rendered over the base diagram."""
    annotation_id: str
    annotation_type: AnnotationType
    element_id: str  # The base element this annotates
    position: Tuple[float, float]
    content: str  # Text content (e.g., "1", "2", "input", "output")
    style: Dict[str, Any]  # Rendering style options
    
class AnnotationRenderer:
    """Renders annotation overlays on top of base EG diagrams."""
    
    def __init__(self):
        self.annotation_generators = {
            AnnotationType.ARITY_NUMBERING: self._generate_arity_annotations,
            AnnotationType.ARGUMENT_LABELS: self._generate_argument_annotations,
            AnnotationType.VARIABLE_BINDING: self._generate_binding_annotations,
            AnnotationType.LOGICAL_STRUCTURE: self._generate_structure_annotations,
            AnnotationType.CONTAINMENT_AREAS: self._generate_containment_annotations,
            AnnotationType.TRANSFORMATION_HINTS: self._generate_transformation_annotations,
        }
    
    def generate_annotation_primitives(self, 
                                     layout_result: Any,
                                     graph: Any,
                                     annotation_layers: List[AnnotationLayer]) -> List[AnnotationPrimitive]:
        """Generate annotation primitives for all active annotation layers."""
        primitives = []
        
        # Sort layers by z_order to ensure proper rendering order
        sorted_layers = sorted(annotation_layers, key=lambda l: l.z_order)
        
        for layer in sorted_layers:
            for annotation_config in layer.annotations:
                if annotation_config.enabled:
                    layer_primitives = self._generate_layer_primitives(
                        layout_result, graph, annotation_config
                    )
                    primitives.extend(layer_primitives)
        
        return primitives
    
    def _generate_layer_primitives(self, 
                                 layout_result: Any,
                                 graph: Any,
                                 annotation_config: AnnotationConfig) -> List[AnnotationPrimitive]:
        """Generate annotation primitives for a specific annotation configuration."""
        generator = self.annotation_generators.get(annotation_config.annotation_type)
        if not generator:
            return []
        
        return generator(layout_result, graph, annotation_config)
    
    def _generate_arity_annotations(self, 
                                  layout_result: Any,
                                  graph: Any,
                                  annotation_config: AnnotationConfig) -> List[AnnotationPrimitive]:
        """Generate arity numbering annotations for n-ary predicates."""
        primitives = []
        
        # Find all predicates (edges) with arity > 1
        for edge_id in graph.E:
            if edge_id in graph.nu and len(graph.nu[edge_id]) > 1:
                # Check if this element should be annotated
                if (annotation_config.target_elements is None or 
                    edge_id in annotation_config.target_elements):
                    
                    # Get predicate position from layout
                    if edge_id in layout_result.primitives:
                        predicate_primitive = layout_result.primitives[edge_id]
                        pred_x, pred_y = predicate_primitive.position
                        
                        # Generate numbered annotations for each argument
                        vertex_sequence = graph.nu[edge_id]
                        for i, vertex_id in enumerate(vertex_sequence):
                            if vertex_id in layout_result.primitives:
                                vertex_primitive = layout_result.primitives[vertex_id]
                                vx, vy = vertex_primitive.position
                                
                                # Calculate annotation position near the connection point
                                # Position number halfway between predicate and vertex
                                ann_x = (pred_x + vx) / 2
                                ann_y = (pred_y + vy) / 2 - 8  # Slightly above the line
                                
                                # Create annotation primitive
                                annotation = AnnotationPrimitive(
                                    annotation_id=f"arity_{edge_id}_{i}",
                                    annotation_type=AnnotationType.ARITY_NUMBERING,
                                    element_id=edge_id,
                                    position=(ann_x, ann_y),
                                    content=str(i + 1),  # 1-based numbering
                                    style={
                                        'font_size': 10,
                                        'color': 'blue',
                                        'background': 'white',
                                        'border': True,
                                        **annotation_config.style_options
                                    }
                                )
                                primitives.append(annotation)
        
        return primitives
    
    def _generate_argument_annotations(self, 
                                     layout_result: Any,
                                     graph: Any,
                                     annotation_config: AnnotationConfig) -> List[AnnotationPrimitive]:
        """Generate argument role labels (input/output) for functional predicates."""
        # TODO: Implement argument role annotation
        # This would require additional metadata about which predicates are functions
        # and which arguments are inputs vs outputs
        return []
    
    def _generate_binding_annotations(self, 
                                    layout_result: Any,
                                    graph: Any,
                                    annotation_config: AnnotationConfig) -> List[AnnotationPrimitive]:
        """Generate variable binding relationship annotations."""
        # TODO: Implement variable binding visualization
        # This could show which variables are bound together across different predicates
        return []
    
    def _generate_structure_annotations(self, 
                                      layout_result: Any,
                                      graph: Any,
                                      annotation_config: AnnotationConfig) -> List[AnnotationPrimitive]:
        """Generate logical structure highlighting annotations."""
        # TODO: Implement logical pattern highlighting
        # This could highlight common patterns like implications, conjunctions, etc.
        return []
    
    def _generate_containment_annotations(self, 
                                        layout_result: Any,
                                        graph: Any,
                                        annotation_config: AnnotationConfig) -> List[AnnotationPrimitive]:
        """Generate explicit area boundary annotations."""
        # TODO: Implement area boundary visualization
        # This could show dotted lines around logical areas for clarity
        return []
    
    def _generate_transformation_annotations(self, 
                                           layout_result: Any,
                                           graph: Any,
                                           annotation_config: AnnotationConfig) -> List[AnnotationPrimitive]:
        """Generate transformation rule hint annotations."""
        # TODO: Implement transformation rule suggestions
        # This could highlight where EG transformation rules can be applied
        return []

class AnnotationManager:
    """Manages annotation layers and provides high-level annotation control."""
    
    def __init__(self):
        self.annotation_layers: List[AnnotationLayer] = []
        self.renderer = AnnotationRenderer()
    
    def add_layer(self, layer: AnnotationLayer):
        """Add an annotation layer."""
        self.annotation_layers.append(layer)
        # Sort by z_order to maintain rendering order
        self.annotation_layers.sort(key=lambda l: l.z_order)
    
    def remove_layer(self, layer_id: str):
        """Remove an annotation layer by ID."""
        self.annotation_layers = [l for l in self.annotation_layers if l.layer_id != layer_id]
    
    def get_layer(self, layer_id: str) -> Optional[AnnotationLayer]:
        """Get an annotation layer by ID."""
        for layer in self.annotation_layers:
            if layer.layer_id == layer_id:
                return layer
        return None
    
    def toggle_annotation_type(self, annotation_type: AnnotationType, enabled: bool):
        """Enable or disable all annotations of a specific type across all layers."""
        for layer in self.annotation_layers:
            for annotation in layer.annotations:
                if annotation.annotation_type == annotation_type:
                    annotation.enabled = enabled
    
    def get_active_annotation_types(self) -> Set[AnnotationType]:
        """Get all currently active annotation types."""
        active_types = set()
        for layer in self.annotation_layers:
            for annotation in layer.annotations:
                if annotation.enabled:
                    active_types.add(annotation.annotation_type)
        return active_types
    
    def generate_annotations(self, layout_result: Any, graph: Any) -> List[AnnotationPrimitive]:
        """Generate all annotation primitives for the current configuration."""
        return self.renderer.generate_annotation_primitives(
            layout_result, graph, self.annotation_layers
        )

# Convenience functions for creating common annotation configurations
def create_arity_numbering_layer(enabled: bool = True, z_order: int = 10) -> AnnotationLayer:
    """Create a standard arity numbering annotation layer."""
    arity_config = AnnotationConfig(
        annotation_type=AnnotationType.ARITY_NUMBERING,
        enabled=enabled,
        style_options={
            'font_size': 10,
            'color': 'blue',
            'background': 'white',
            'border': True
        }
    )
    
    return AnnotationLayer(
        layer_id="arity_numbering",
        annotations=[arity_config],
        z_order=z_order
    )

def create_argument_labels_layer(enabled: bool = True, z_order: int = 11) -> AnnotationLayer:
    """Create a standard argument labeling annotation layer."""
    labels_config = AnnotationConfig(
        annotation_type=AnnotationType.ARGUMENT_LABELS,
        enabled=enabled,
        style_options={
            'font_size': 9,
            'color': 'green',
            'background': 'lightyellow'
        }
    )
    
    return AnnotationLayer(
        layer_id="argument_labels",
        annotations=[labels_config],
        z_order=z_order
    )

if __name__ == "__main__":
    print("Annotation System for Existential Graph Diagrams")
    print("Available annotation types:")
    for annotation_type in AnnotationType:
        print(f"  - {annotation_type.value}")
