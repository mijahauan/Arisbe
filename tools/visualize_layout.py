#!/usr/bin/env python3
"""
Layout Visualization Tool

Creates SVG visualizations of layout engine output for testing and validation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from layout_engine import LayoutEngine
from svg_renderer import SVGRenderer, render_layout_to_file
from egi_core_dau import create_empty_graph, create_vertex, create_cut


def create_test_cases():
    """Create various test EGIs for visualization"""
    test_cases = []
    
    # Test 1: Simple vertex
    egi1 = create_empty_graph()
    vertex1 = create_vertex(label="Human", is_generic=False)
    egi1 = egi1.with_vertex(vertex1)
    test_cases.append(("simple_vertex", egi1))
    
    # Test 2: Vertex in cut  
    egi2 = create_empty_graph()
    cut2 = create_cut()
    vertex2 = create_vertex(label="Mortal", is_generic=False)
    egi2 = egi2.with_cut(cut2)
    egi2 = egi2.with_vertex_in_context(vertex2, cut2.id)
    test_cases.append(("vertex_in_cut", egi2))
    
    # Test 3: Multiple vertices
    egi3 = create_empty_graph()
    for i in range(4):
        vertex = create_vertex(label=f"V{i}", is_generic=False)
        egi3 = egi3.with_vertex(vertex)
    test_cases.append(("multiple_vertices", egi3))
    
    # Test 4: Nested cuts
    egi4 = create_empty_graph()
    outer_cut = create_cut()
    inner_cut = create_cut()
    vertex4 = create_vertex(label="Nested", is_generic=False)
    
    egi4 = egi4.with_cut(outer_cut)
    egi4 = egi4.with_cut(inner_cut, outer_cut.id)
    egi4 = egi4.with_vertex_in_context(vertex4, inner_cut.id)
    test_cases.append(("nested_cuts", egi4))
    
    # Test 5: Complex structure
    egi5 = create_empty_graph()
    cut_a = create_cut()
    cut_b = create_cut()
    v1 = create_vertex(label="A", is_generic=False)
    v2 = create_vertex(label="B", is_generic=False)
    v3 = create_vertex(label="C", is_generic=False)
    
    egi5 = egi5.with_cut(cut_a)
    egi5 = egi5.with_cut(cut_b)
    egi5 = egi5.with_vertex_in_context(v1, cut_a.id)
    egi5 = egi5.with_vertex_in_context(v2, cut_b.id)
    egi5 = egi5.with_vertex(v3)  # On sheet
    test_cases.append(("complex_structure", egi5))
    
    return test_cases


def visualize_all_test_cases():
    """Generate SVG visualizations for all test cases"""
    engine = LayoutEngine()
    test_cases = create_test_cases()
    
    print("🎨 Generating Layout Visualizations")
    print("=" * 40)
    
    output_dir = Path("layout_visualizations")
    output_dir.mkdir(exist_ok=True)
    
    for name, egi in test_cases:
        print(f"Rendering: {name}")
        
        # Generate layout
        layout = engine.compute_layout(egi)
        
        # Render to SVG
        output_file = output_dir / f"{name}.svg"
        render_layout_to_file(layout, str(output_file), egi)
        
        # Print layout info
        print(f"  Vertices: {len(layout.vertex_positions)}")
        print(f"  Cuts: {len(layout.cut_bounds)}")
        print(f"  Viewport: {layout.viewport_bounds.min_x:.1f},{layout.viewport_bounds.min_y:.1f} to {layout.viewport_bounds.max_x:.1f},{layout.viewport_bounds.max_y:.1f}")
        print()
    
    print(f"✅ Generated {len(test_cases)} visualizations in {output_dir}/")
    print("\nOpen the SVG files in a web browser to view the layouts!")


if __name__ == "__main__":
    visualize_all_test_cases()
