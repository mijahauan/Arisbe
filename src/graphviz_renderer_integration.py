#!/usr/bin/env python3
"""
Integration between Graphviz layout and existing rendering pipeline.
This bridges the Graphviz spatial primitives to the CleanDiagramRenderer format.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_engine_clean import SpatialPrimitive, LayoutResult, Coordinate
from graphviz_layout_integration import GraphvizLayoutIntegration, GraphvizLayoutResult


def convert_graphviz_to_layout_result(graphviz_result: GraphvizLayoutResult, 
                                    graph: RelationalGraphWithCuts) -> LayoutResult:
    """
    Convert Graphviz layout result to the format expected by CleanDiagramRenderer.
    
    This bridges the gap between Graphviz spatial primitives and the existing
    rendering pipeline that expects LayoutResult objects.
    """
    
    # Convert Graphviz primitives to SpatialPrimitive objects
    spatial_primitives = {}
    
    for primitive in graphviz_result.primitives:
        element_id = primitive.get('element_id')
        if not element_id:
            continue
            
        ptype = primitive['type']
        
        if ptype == 'vertex':
            pos = (primitive['x'], primitive['y'])
            radius = primitive['radius']
            spatial_primitives[element_id] = SpatialPrimitive(
                element_id=element_id,
                element_type='vertex',
                position=pos,
                bounds=(pos[0]-radius, pos[1]-radius, pos[0]+radius, pos[1]+radius),
                z_index=1
            )
            
        elif ptype == 'predicate':
            pos = (primitive['x'], primitive['y'])
            width = primitive['width']
            height = primitive['height']
            spatial_primitives[element_id] = SpatialPrimitive(
                element_id=element_id,
                element_type='edge',  # Note: predicates are edges in EGI
                position=pos,
                bounds=(pos[0]-width/2, pos[1]-height/2, pos[0]+width/2, pos[1]+height/2),
                z_index=2
            )
            
        elif ptype == 'cut':
            # Convert polygon points to center and radius (approximation)
            points = primitive.get('points', [])
            if points:
                # Calculate center
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                center_x = sum(xs) / len(xs)
                center_y = sum(ys) / len(ys)
                
                # Approximate radius as distance to furthest point
                radius = max(((x - center_x)**2 + (y - center_y)**2)**0.5 
                           for x, y in points) if points else 50
                
                pos = (center_x, center_y)
                spatial_primitives[element_id] = SpatialPrimitive(
                    element_id=element_id,
                    element_type='cut',
                    position=pos,
                    bounds=(pos[0]-radius, pos[1]-radius, pos[0]+radius, pos[1]+radius),
                    z_index=0,
                    curve_points=points
                )
    
    # Create LayoutResult
    return LayoutResult(
        primitives=spatial_primitives,
        canvas_bounds=(0, 0, 800, 600),  # (x1, y1, x2, y2)
        containment_hierarchy={}  # Simplified for now
    )


class GraphvizRendererIntegration:
    """
    Complete integration: EGI → Graphviz Layout → Existing Renderer
    
    This class provides a drop-in replacement for the old layout engine
    while maintaining compatibility with the existing rendering pipeline.
    """
    
    def __init__(self):
        self.graphviz_engine = GraphvizLayoutIntegration()
    
    def render_graph(self, graph: RelationalGraphWithCuts, canvas) -> bool:
        """
        Complete pipeline: EGI → Graphviz Layout → Rendering
        
        Args:
            graph: EGI graph structure
            canvas: Canvas backend (TkinterCanvas, etc.)
            
        Returns:
            True if rendering succeeded, False otherwise
        """
        
        try:
            # Step 1: Calculate Graphviz layout
            graphviz_result = self.graphviz_engine.calculate_layout(graph)
            
            # Step 2: Convert to existing format
            layout_result = convert_graphviz_to_layout_result(graphviz_result, graph)
            
            # Step 3: Render with existing pipeline
            from diagram_renderer_clean import CleanDiagramRenderer
            renderer = CleanDiagramRenderer(canvas)
            renderer.render_diagram(layout_result, graph)
            
            return True
            
        except Exception as e:
            print(f"Rendering failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_layout_info(self, graph: RelationalGraphWithCuts) -> Dict:
        """Get layout information for debugging/analysis."""
        
        graphviz_result = self.graphviz_engine.calculate_layout(graph)
        
        return {
            'primitives_count': len(graphviz_result.primitives),
            'node_positions_count': len(graphviz_result.node_positions),
            'cluster_bounds_count': len(graphviz_result.cluster_bounds),
            'dot_source': graphviz_result.dot_source,
            'primitive_types': {
                ptype: len([p for p in graphviz_result.primitives if p['type'] == ptype])
                for ptype in set(p['type'] for p in graphviz_result.primitives)
            }
        }


def test_integration():
    """Test the complete Graphviz → Renderer integration."""
    
    print("=== Testing Complete Graphviz → Renderer Integration ===")
    
    # Create test EGI: ~[ ~[ (P "x") ] ~[ (Q "x") ] ]
    from egi_core_dau import create_empty_graph, create_vertex, create_edge, create_cut
    
    graph = create_empty_graph()
    
    # Add outer cut
    outer_cut = create_cut()
    graph = graph.with_cut(outer_cut)
    
    # Add first inner cut with P(x)
    inner_cut1 = create_cut()
    graph = graph.with_cut(inner_cut1, outer_cut.id)
    
    x_vertex1 = create_vertex("x", is_generic=False)
    graph = graph.with_vertex_in_context(x_vertex1, inner_cut1.id)
    
    p_edge = create_edge()
    graph = graph.with_edge(p_edge, (x_vertex1.id,), "P", inner_cut1.id)
    
    # Add second inner cut with Q(x)
    inner_cut2 = create_cut()
    graph = graph.with_cut(inner_cut2, outer_cut.id)
    
    x_vertex2 = create_vertex("x", is_generic=False)
    graph = graph.with_vertex_in_context(x_vertex2, inner_cut2.id)
    
    q_edge = create_edge()
    graph = graph.with_edge(q_edge, (x_vertex2.id,), "Q", inner_cut2.id)
    
    print(f"✓ Created test EGI with {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
    
    # Test the integration
    integration = GraphvizRendererIntegration()
    
    # Get layout info
    layout_info = integration.get_layout_info(graph)
    print(f"✓ Layout analysis:")
    for key, value in layout_info.items():
        if key != 'dot_source':
            print(f"  {key}: {value}")
    
    print(f"\n✓ DOT source generated:")
    print(layout_info['dot_source'])
    
    # Test rendering (without GUI)
    print(f"\n✓ Testing rendering pipeline...")
    
    # Create mock canvas for testing
    class MockCanvas:
        def __init__(self):
            self.operations = []
        
        def draw_line(self, start, end, width, color):
            self.operations.append(f"line: {start} → {end}")
        
        def draw_circle(self, center, radius, fill_color, outline_color, outline_width):
            self.operations.append(f"circle: center={center}, radius={radius}")
        
        def draw_curve(self, points, width, color, fill=False):
            self.operations.append(f"curve: {len(points)} points")
        
        def draw_text(self, position, text, font_size, color):
            self.operations.append(f"text: '{text}' at {position}")
        
        def clear(self):
            self.operations = []
    
    mock_canvas = MockCanvas()
    success = integration.render_graph(graph, mock_canvas)
    
    if success:
        print(f"✓ Rendering succeeded!")
        print(f"  Generated {len(mock_canvas.operations)} drawing operations")
        for op in mock_canvas.operations[:5]:  # Show first 5 operations
            print(f"    {op}")
        if len(mock_canvas.operations) > 5:
            print(f"    ... and {len(mock_canvas.operations) - 5} more")
    else:
        print(f"✗ Rendering failed")
        return False
    
    print(f"\n🎉 Complete integration test successful!")
    print(f"Ready to replace old layout engine in main application.")
    
    return True


if __name__ == "__main__":
    test_integration()
