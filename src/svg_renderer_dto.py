"""
SVG Renderer for New Layout Engine DTO
"""

import xml.etree.ElementTree as ET
from layout_engine import LayoutDTO, Point, BoundingBox
from egi_core_dau import RelationalGraphWithCuts
from pathlib import Path


class SVGRendererDTO:
    """Renders LayoutDTO to SVG"""
    
    def render_to_svg(self, layout: LayoutDTO, egi: RelationalGraphWithCuts, title: str = "EG Diagram", egif: str = "") -> str:
        """Convert LayoutDTO to SVG string"""
        
        # Create SVG with viewport bounds + space for EGIF at bottom
        viewport = layout.viewport_bounds
        diagram_width = max(400, viewport.width + 80)
        diagram_height = max(300, viewport.height + 80)
        egif_height = 40  # Space for EGIF at bottom
        total_height = diagram_height + egif_height
        
        svg = ET.Element("svg", {
            "width": str(int(diagram_width)),
            "height": str(int(total_height)),
            "xmlns": "http://www.w3.org/2000/svg"
        })
        
        # Background
        ET.SubElement(svg, "rect", {
            "x": "0", "y": "0",
            "width": str(int(diagram_width)), "height": str(int(total_height)),
            "fill": "white", "stroke": "none"
        })
        
        # Calculate centering offset for diagram
        center_x = (diagram_width - viewport.width) / 2 - viewport.min_x
        center_y = (diagram_height - viewport.height) / 2 - viewport.min_y + 30  # +30 for title space
        
        # Title
        ET.SubElement(svg, "text", {
            "x": "10", "y": "20",
            "font-size": "14", "font-weight": "bold",
            "fill": "black"
        }).text = title
        
        # Style info
        style_info = f"Elements: V={len(layout.vertex_positions)}, E={len(layout.predicate_positions)}, C={len(layout.cut_bounds)}"
        ET.SubElement(svg, "text", {
            "x": "10", "y": "35",
            "font-size": "10", "fill": "gray"
        }).text = style_info
        
        # Render cuts first (background) - thinner lines than ligatures
        for cut_id, bounds in layout.cut_bounds.items():
            ET.SubElement(svg, "rect", {
                "x": str(bounds.min_x + center_x), "y": str(bounds.min_y + center_y),
                "width": str(bounds.width), "height": str(bounds.height),
                "fill": "none", "stroke": "black", "stroke-width": "1.5",  # Thinner than ligatures
                "rx": "8.0", "ry": "8.0"
            })
        
        # Render ligature paths - thicker than cuts
        for path in layout.ligature_paths:
            if len(path.points) >= 2:
                start = path.points[0]
                end = path.points[-1]
                ET.SubElement(svg, "path", {
                    "d": f"M {start.x + center_x} {start.y + center_y} L {end.x + center_x} {end.y + center_y}",
                    "fill": "none", "stroke": "black", "stroke-width": "2.0"  # Thicker than cuts
                })
        
        # Render predicates (edges)
        for pred_id, pos in layout.predicate_positions.items():
            relation_name = egi.rel.get(pred_id, "?")
            ET.SubElement(svg, "text", {
                "x": str(pos.x + center_x), "y": str(pos.y + center_y),
                "text-anchor": "middle", "font-size": "12",
                "font-family": "Arial", "fill": "black"
            }).text = relation_name
        
        # Render vertices
        for vertex_id, pos in layout.vertex_positions.items():
            # Find vertex info
            vertex = next((v for v in egi.V if v.id == vertex_id), None)
            if vertex:
                if vertex.is_generic:
                    # Generic vertex - small black dot (just noticeably larger than ligature)
                    ET.SubElement(svg, "circle", {
                        "cx": str(pos.x + center_x), "cy": str(pos.y + center_y),
                        "r": "3.0", "fill": "black", "stroke": "none"  # Smaller radius
                    })
                else:
                    # Constant vertex - label
                    ET.SubElement(svg, "text", {
                        "x": str(pos.x + center_x), "y": str(pos.y + center_y + 4),
                        "text-anchor": "middle", "font-size": "10",
                        "font-family": "Arial", "fill": "blue"
                    }).text = vertex.label or "?"
        
        # Add EGIF at bottom
        if egif:
            egif_y = diagram_height + 20
            ET.SubElement(svg, "text", {
                "x": "10", "y": str(egif_y),
                "font-size": "12", "font-family": "monospace",
                "fill": "black"
            }).text = f"EGIF: {egif}"
        
        return ET.tostring(svg, encoding='unicode')
    
    def save_svg(self, layout: LayoutDTO, egi: RelationalGraphWithCuts, 
                 filename: str, title: str = "EG Diagram", egif: str = "", output_dir: str = "test_outputs/new_layouts"):
        """Save LayoutDTO as SVG file"""
        svg_content = self.render_to_svg(layout, egi, title, egif)
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save file
        svg_file = output_path / f"{filename}.svg"
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        return str(svg_file)
