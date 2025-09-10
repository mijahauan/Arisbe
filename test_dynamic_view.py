#!/usr/bin/env python3
"""
Simple test harness for dynamic view generation system.
Generates actual visual output to verify the system works with real graphs.
"""

import sys
import os
sys.path.append('src')

from typing import List, Tuple
import xml.etree.ElementTree as ET

# Import our systems
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
from dynamic_view_generator import (
    DynamicViewManager, PeirceDauViewGenerator, ViewportBounds, 
    RenderedElement, GraphView, DetailLevel
)
from universal_composition import UniversalComposer


class SimpleSVGRenderer:
    """Renders a GraphView to SVG for immediate visual feedback."""
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
    
    def render_to_svg(self, view: GraphView, filename: str = "test_graph.svg"):
        """Render a GraphView to an SVG file."""
        
        # Create SVG root element
        svg = ET.Element("svg", {
            "width": str(self.width),
            "height": str(self.height),
            "xmlns": "http://www.w3.org/2000/svg",
            "viewBox": f"0 0 {self.width} {self.height}"
        })
        
        # Add background
        background = ET.SubElement(svg, "rect", {
            "width": "100%",
            "height": "100%",
            "fill": "white",
            "stroke": "lightgray",
            "stroke-width": "1"
        })
        
        # Add title
        title_text = ET.SubElement(svg, "text", {
            "x": "10",
            "y": "25",
            "font-family": "Arial, sans-serif",
            "font-size": "16",
            "fill": "black"
        })
        title_text.text = f"EG View - {view.visible_elements}/{view.total_elements} elements visible"
        
        # Render elements by type (cuts first, then edges, then vertices)
        cuts = view.get_elements_by_type("cut")
        edges = view.get_elements_by_type("edge")
        vertices = view.get_elements_by_type("vertex")
        
        # Render cuts (background)
        for cut in cuts:
            self._render_cut_svg(svg, cut)
        
        # Render edges
        for edge in edges:
            self._render_edge_svg(svg, edge)
        
        # Render vertices (foreground)
        for vertex in vertices:
            self._render_vertex_svg(svg, vertex)
        
        # Add viewport info
        viewport_info = ET.SubElement(svg, "text", {
            "x": "10",
            "y": str(self.height - 10),
            "font-family": "Arial, sans-serif",
            "font-size": "12",
            "fill": "gray"
        })
        viewport_info.text = f"Viewport: ({view.viewport.x_min:.1f}, {view.viewport.y_min:.1f}) to ({view.viewport.x_max:.1f}, {view.viewport.y_max:.1f}) | Zoom: {view.viewport.zoom_level:.2f}"
        
        # Write to file
        tree = ET.ElementTree(svg)
        ET.indent(tree, space="  ", level=0)
        tree.write(filename, encoding="utf-8", xml_declaration=True)
        
        print(f"✅ Rendered graph to {filename}")
        return filename
    
    def _render_cut_svg(self, parent: ET.Element, cut: RenderedElement):
        """Render a cut as a closed path."""
        if not cut.path_points:
            # Fallback to rectangle if no path points
            rect = ET.SubElement(parent, "rect", {
                "x": str(cut.x),
                "y": str(cut.y),
                "width": str(cut.width),
                "height": str(cut.height),
                "fill": "none",
                "stroke": cut.border_color,
                "stroke-width": str(cut.border_width),
                "stroke-dasharray": "5,5"
            })
        else:
            # Render as path
            path_data = "M " + " L ".join([f"{x},{y}" for x, y in cut.path_points]) + " Z"
            path = ET.SubElement(parent, "path", {
                "d": path_data,
                "fill": "none",
                "stroke": cut.border_color,
                "stroke-width": str(cut.border_width)
            })
        
        # Add cut label
        if cut.text:
            text = ET.SubElement(parent, "text", {
                "x": str(cut.x + 5),
                "y": str(cut.y + 15),
                "font-family": "Arial, sans-serif",
                "font-size": "10",
                "fill": "blue"
            })
            text.text = f"Cut {cut.element_id}"
    
    def _render_vertex_svg(self, parent: ET.Element, vertex: RenderedElement):
        """Render a vertex as a circle with optional label."""
        
        # Vertex circle
        circle = ET.SubElement(parent, "circle", {
            "cx": str(vertex.x + vertex.width / 2),
            "cy": str(vertex.y + vertex.height / 2),
            "r": str(vertex.width / 2),
            "fill": vertex.color,
            "stroke": vertex.border_color,
            "stroke-width": str(vertex.border_width)
        })
        
        # Vertex label (constant name if any)
        if vertex.text:
            text = ET.SubElement(parent, "text", {
                "x": str(vertex.x + vertex.width / 2),
                "y": str(vertex.y + vertex.height + 15),
                "font-family": "Arial, sans-serif",
                "font-size": str(vertex.font_size),
                "fill": vertex.color,
                "text-anchor": "middle"
            })
            text.text = vertex.text
        
        # Vertex ID (for debugging)
        id_text = ET.SubElement(parent, "text", {
            "x": str(vertex.x + vertex.width + 5),
            "y": str(vertex.y + vertex.height / 2),
            "font-family": "Arial, sans-serif",
            "font-size": "8",
            "fill": "gray"
        })
        id_text.text = f"v{vertex.element_id}"
    
    def _render_edge_svg(self, parent: ET.Element, edge: RenderedElement):
        """Render an edge as text with ligature lines."""
        
        # Edge text (relation name)
        text = ET.SubElement(parent, "text", {
            "x": str(edge.x),
            "y": str(edge.y + edge.height),
            "font-family": "Arial, sans-serif",
            "font-size": str(edge.font_size),
            "fill": edge.color
        })
        text.text = edge.text or f"R{edge.element_id}"
        
        # Ligature lines (connections to vertices)
        for i, (lx, ly) in enumerate(edge.ligature_points):
            line = ET.SubElement(parent, "line", {
                "x1": str(edge.x + edge.width / 2),
                "y1": str(edge.y + edge.height / 2),
                "x2": str(lx),
                "y2": str(ly),
                "stroke": "black",
                "stroke-width": "1"
            })


def create_simple_test_graph() -> RelationalGraphWithCuts:
    """Create a simple test graph for visualization testing."""
    
    # Create vertices
    v1 = Vertex(id="v1")
    v2 = Vertex(id="v2")
    v3 = Vertex(id="v3")
    
    # Create edges
    e1 = Edge(id="e1")  # Connects v1 and v2
    e2 = Edge(id="e2")  # Connects v2 and v3
    
    # Create a cut
    c1 = Cut(id="c1")
    
    # Create the graph
    from frozendict import frozendict
    
    egi = RelationalGraphWithCuts(
        V=frozenset([v1, v2, v3]),
        E=frozenset([e1, e2]),
        nu=frozendict({
            "e1": ["v1", "v2"],
            "e2": ["v2", "v3"]
        }),
        sheet="sheet1",
        Cut=frozenset([c1]),
        area=frozendict({
            "c1": frozenset(["v2", "e2"]),  # Cut contains v2 and e2
            "sheet1": frozenset(["v1", "v3", "e1", "c1"])  # Sheet contains everything else
        }),
        rel=frozendict({
            "e1": "Loves",
            "e2": "Knows"
        }),
        rho=frozendict({
            "v1": "Alice",
            "v2": "",  # No constant
            "v3": "Bob"
        })
    )
    
    return egi


def create_corpus_test_graph() -> RelationalGraphWithCuts:
    """Try to load a graph from the corpus for testing."""
    try:
        composer = UniversalComposer()
        
        # Try to find a simple graph in the corpus
        corpus_path = "corpus/graphs"
        if os.path.exists(corpus_path):
            # Look for JSON files
            for root, dirs, files in os.walk(corpus_path):
                for file in files:
                    if file.endswith('.json'):
                        filepath = os.path.join(root, file)
                        try:
                            print(f"🔍 Trying to load {filepath}")
                            historical_graph = composer.import_from_file(filepath)
                            if historical_graph and historical_graph.current_graph:
                                print(f"✅ Loaded graph from {filepath}")
                                return historical_graph.current_graph
                        except Exception as e:
                            print(f"❌ Failed to load {filepath}: {e}")
                            continue
        
        print("📝 No corpus graphs found, using simple test graph")
        return create_simple_test_graph()
        
    except Exception as e:
        print(f"❌ Error loading corpus graph: {e}")
        print("📝 Falling back to simple test graph")
        return create_simple_test_graph()


def test_basic_rendering():
    """Test basic rendering functionality."""
    print("🧪 Testing Basic Rendering")
    print("=" * 50)
    
    # Create test graph
    egi = create_simple_test_graph()
    print(f"📊 Created test graph: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
    
    # Create view manager
    view_manager = DynamicViewManager()
    
    # Generate view
    viewport = ViewportBounds(0, 0, 400, 300, zoom_level=1.0)
    view = view_manager.generate_view(egi, viewport)
    
    print(f"👁️  Generated view: {view.visible_elements}/{view.total_elements} elements visible")
    print(f"📏 Detail level: {view.detail_level}")
    
    # Render to SVG
    renderer = SimpleSVGRenderer()
    svg_file = renderer.render_to_svg(view, "test_basic_rendering.svg")
    
    return svg_file


def test_zoom_levels():
    """Test different zoom levels and detail transitions."""
    print("\n🔍 Testing Zoom Levels")
    print("=" * 50)
    
    egi = create_simple_test_graph()
    view_manager = DynamicViewManager()
    renderer = SimpleSVGRenderer()
    
    zoom_levels = [0.05, 0.3, 1.0, 3.0]  # Overview, Intermediate, Detailed, Micro
    
    for i, zoom in enumerate(zoom_levels):
        viewport = ViewportBounds(0, 0, 400, 300, zoom_level=zoom)
        view = view_manager.generate_view(egi, viewport)
        
        filename = f"test_zoom_{i+1}_{view.detail_level.value}.svg"
        renderer.render_to_svg(view, filename)
        
        print(f"🔍 Zoom {zoom:4.2f} -> {view.detail_level.value:12s} -> {filename}")


def test_context_collapse():
    """Test context collapse/expansion functionality."""
    print("\n📁 Testing Context Collapse/Expansion")
    print("=" * 50)
    
    egi = create_simple_test_graph()
    view_manager = DynamicViewManager()
    renderer = SimpleSVGRenderer()
    
    # Test with expanded context
    viewport = ViewportBounds(0, 0, 400, 300, zoom_level=1.0)
    view_expanded = view_manager.generate_view(egi, viewport)
    renderer.render_to_svg(view_expanded, "test_context_expanded.svg")
    print(f"📂 Expanded: {view_expanded.visible_elements} elements visible")
    
    # Test with collapsed context
    view_manager.toggle_context("c1")  # Collapse cut c1
    view_collapsed = view_manager.generate_view(egi, viewport)
    renderer.render_to_svg(view_collapsed, "test_context_collapsed.svg")
    print(f"📁 Collapsed: {view_collapsed.visible_elements} elements visible")


def test_corpus_graph():
    """Test with a real corpus graph if available."""
    print("\n📚 Testing with Corpus Graph")
    print("=" * 50)
    
    egi = create_corpus_test_graph()
    print(f"📊 Corpus graph: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
    
    view_manager = DynamicViewManager()
    renderer = SimpleSVGRenderer(width=1000, height=800)  # Larger canvas for corpus graphs
    
    viewport = ViewportBounds(0, 0, 500, 400, zoom_level=1.0)
    view = view_manager.generate_view(egi, viewport)
    
    renderer.render_to_svg(view, "test_corpus_graph.svg")
    print(f"👁️  Rendered corpus graph: {view.visible_elements}/{view.total_elements} elements visible")


def main():
    """Run all tests and generate visual output."""
    print("🚀 Dynamic View Generator Test Suite")
    print("=" * 50)
    
    try:
        # Basic functionality test
        svg_file = test_basic_rendering()
        
        # Zoom level tests
        test_zoom_levels()
        
        # Context collapse tests
        test_context_collapse()
        
        # Corpus graph test
        test_corpus_graph()
        
        print("\n✅ All tests completed!")
        print("📁 Generated SVG files:")
        for filename in [
            "test_basic_rendering.svg",
            "test_zoom_1_overview.svg",
            "test_zoom_2_intermediate.svg", 
            "test_zoom_3_detailed.svg",
            "test_zoom_4_micro.svg",
            "test_context_expanded.svg",
            "test_context_collapsed.svg",
            "test_corpus_graph.svg"
        ]:
            if os.path.exists(filename):
                print(f"  📄 {filename}")
        
        print(f"\n🎯 Open {svg_file} in your browser to see the basic rendering!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
