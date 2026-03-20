"""
Simple SVG Renderer for Layout Engine DTO
"""

import xml.etree.ElementTree as ET
from layout_engine import LayoutResult
from egi_core_dau import RelationalGraphWithCuts


class SVGRenderer:
    """Renders LayoutResult DTO to SVG"""
    
    def render_to_svg(self, layout: LayoutResult, egi=None) -> str:
        """Convert layout DTO to SVG string"""
        
        # Create SVG with viewport bounds
        viewport = layout.viewport_bounds
        width = viewport.max_x - viewport.min_x
        height = viewport.max_y - viewport.min_y
        
        svg = ET.Element("svg", {
            "width": str(int(width + 20)),
            "height": str(int(height + 20)),
            "viewBox": f"{viewport.min_x-10} {viewport.min_y-10} {width+20} {height+20}",
            "xmlns": "http://www.w3.org/2000/svg"
        })
        
        # Background
        ET.SubElement(svg, "rect", {
            "x": str(viewport.min_x-10), "y": str(viewport.min_y-10),
            "width": str(width+20), "height": str(height+20),
            "fill": "white", "stroke": "none"
        })
        
        # Render cuts first (background)
        for cut_id, bounds in layout.cut_bounds.items():
            cut_width = bounds.max_x - bounds.min_x
            cut_height = bounds.max_y - bounds.min_y
            ET.SubElement(svg, "rect", {
                "x": str(bounds.min_x), "y": str(bounds.min_y),
                "width": str(cut_width), "height": str(cut_height),
                "fill": "none", "stroke": "#333", "stroke-width": "2", "rx": "8"
            })
        
        # Render vertices (foreground)
        for vertex_id, pos in layout.vertex_positions.items():
            ET.SubElement(svg, "circle", {
                "cx": str(pos.x), "cy": str(pos.y), "r": "10",
                "fill": "#4A90E2", "stroke": "#2E5C8A", "stroke-width": "2"
            })
        
        # Render edges
        for edge_id, path in layout.edge_paths.items():
            if len(path.points) >= 2:
                path_data = f"M {path.points[0].x} {path.points[0].y}"
                for point in path.points[1:]:
                    path_data += f" L {point.x} {point.y}"
                
                ET.SubElement(svg, "path", {
                    "d": path_data, "fill": "none", 
                    "stroke": "#666", "stroke-width": "1.5"
                })
        
        return ET.tostring(svg, encoding='unicode')


def render_layout_to_file(layout: LayoutResult, filename: str, egi=None):
    """Render layout to SVG file"""
    renderer = SVGRenderer()
    svg_content = renderer.render_to_svg(layout, egi)
    
    with open(filename, 'w') as f:
        f.write(svg_content)
    
    print(f"SVG rendered to {filename}")


# Test function
def test_svg_rendering():
    """Test SVG rendering with simple EGI"""
    from layout_engine import LayoutEngine
    from egi_core_dau import create_empty_graph, create_vertex, create_cut
    
    # Create test EGI
    egi = create_empty_graph()
    vertex = create_vertex(label="Human", is_generic=False)
    cut = create_cut()
    
    egi = egi.with_cut(cut)
    egi = egi.with_vertex_in_context(vertex, cut.id)
    
    # Generate layout
    engine = LayoutEngine()
    layout = engine.compute_layout(egi)
    
    # Render to SVG
    render_layout_to_file(layout, "test_layout.svg", egi)


if __name__ == "__main__":
    test_svg_rendering()
