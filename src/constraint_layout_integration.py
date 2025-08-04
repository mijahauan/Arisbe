#!/usr/bin/env python3
"""
Constraint-Based Layout Integration for Main Application

This module provides a drop-in replacement for ContentDrivenLayoutEngine
using our validated constraint-based approach with Cassowary solver and Cairo rendering.

Key Features:
- Enforces strict hierarchical containment for cuts
- Prevents overlapping cuts (non-overlapping siblings)
- Maintains clean Data ↔ Layout ↔ Rendering separation
- Compatible with existing application architecture
"""

import math
from typing import Dict, Set, List, Tuple, Optional
from dataclasses import dataclass

from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_engine_clean import SpatialPrimitive, LayoutResult, Bounds, Coordinate
from constraint_layout_engine import ConstraintBasedLayoutEngine

class ConstraintLayoutIntegration:
    """
    Drop-in replacement for ContentDrivenLayoutEngine using constraint-based approach.
    
    This class provides the same interface as ContentDrivenLayoutEngine but uses
    our validated constraint-based layout engine internally.
    """
    
    def __init__(self, canvas_width: float = 800, canvas_height: float = 600):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # Initialize constraint-based layout engine
        self.constraint_engine = ConstraintBasedLayoutEngine(canvas_width, canvas_height)
        
        # Layout parameters (compatible with existing system)
        self.margin = 50.0
        self.vertex_radius = 6.0
        self.min_vertex_spacing = 80.0
        self.cut_padding = 50.0
        self.predicate_spacing = 90.0
        
        # Z-index layers
        self.z_cuts = 0
        self.z_vertices = 1
        self.z_edges = 2
    
    def layout_graph(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        Main entry point: Constraint-based hierarchical layout.
        
        This method provides the same interface as ContentDrivenLayoutEngine.layout_graph()
        but uses our validated constraint-based approach internally.
        
        Args:
            graph: The EGI graph to layout
            
        Returns:
            LayoutResult compatible with existing rendering pipeline
        """
        try:
            # Use the validated constraint-based layout engine directly
            print(f"🔧 Using constraint-based layout for graph with {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
            
            # The constraint engine handles all the complex logic internally
            layout_result = self.constraint_engine.create_layout_from_graph(graph)
            
            print(f"✅ Constraint-based layout completed successfully")
            return layout_result
            
        except Exception as e:
            print(f"❌ Constraint layout failed: {e}")
            import traceback
            traceback.print_exc()
            # Return minimal fallback layout
            return self._create_fallback_layout(graph)
    
    # All complex layout logic is handled by the constraint engine internally
    
    def _create_fallback_layout(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """Create minimal fallback layout if constraint solving fails."""
        primitives = {}
        
        # Simple grid layout as fallback
        x, y = 100, 100
        spacing = 150
        
        # Layout vertices
        for i, vertex in enumerate(graph.V):
            primitives[vertex.id] = SpatialPrimitive(
                element_id=vertex.id,
                element_type='vertex',
                position=(x + i * spacing, y),
                bounds=(x + i * spacing - 5, y - 5, x + i * spacing + 5, y + 5),
                z_index=self.z_vertices
            )
        
        # Layout edges
        for i, edge in enumerate(graph.E):
            primitives[edge.id] = SpatialPrimitive(
                element_id=edge.id,
                element_type='edge',
                position=(x + i * spacing, y + 50),
                bounds=(x + i * spacing - 30, y + 40, x + i * spacing + 30, y + 60),
                z_index=self.z_edges
            )
        
        # Layout cuts
        for i, cut in enumerate(graph.Cut):
            cut_x = x + i * spacing
            cut_y = y + 100
            # Generate simple circular curve points for fallback
            curve_points = []
            center_x, center_y = cut_x, cut_y
            radius_x, radius_y = 75, 50
            num_points = 32
            for i in range(num_points):
                angle = 2 * math.pi * i / num_points
                x = center_x + radius_x * math.cos(angle)
                y = center_y + radius_y * math.sin(angle)
                curve_points.append((x, y))
            
            primitives[cut.id] = SpatialPrimitive(
                element_id=cut.id,
                element_type='cut',
                position=(cut_x, cut_y),
                bounds=(cut_x - 75, cut_y - 50, cut_x + 75, cut_y + 50),
                curve_points=curve_points,
                z_index=self.z_cuts
            )
        
        return LayoutResult(
            primitives=primitives,
            canvas_bounds=(0, 0, self.canvas_width, self.canvas_height),
            containment_hierarchy=self._build_containment_hierarchy(graph)
        )


def test_constraint_integration():
    """Test the constraint-based layout integration."""
    print("🧪 Testing Constraint-Based Layout Integration")
    print("=" * 60)
    
    # Import required modules
    import sys
    sys.path.append('.')
    from egif_parser_dau import parse_egif
    
    # Test cases
    test_cases = [
        ("Mixed Cut and Sheet", '(Human "Socrates") ~[ (Mortal "Socrates") ]'),
        ("Nested Cuts", '~[ ~[ (P "x") ] ]'),
        ("Sibling Cuts", '~[ (P "x") ] ~[ (Q "x") ]'),
    ]
    
    integration = ConstraintLayoutIntegration()
    
    for test_name, egif in test_cases:
        print(f"\n📋 Test: {test_name}")
        print(f"EGIF: {egif}")
        print("-" * 40)
        
        try:
            # Parse EGIF
            graph = parse_egif(egif)
            print(f"✅ Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
            
            # Test constraint-based layout
            result = integration.layout_graph(graph)
            print(f"✅ Layout completed: {len(result.primitives)} primitives")
            print(f"   Canvas bounds: {result.canvas_bounds}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Constraint-based layout integration testing complete!")


if __name__ == "__main__":
    test_constraint_integration()
