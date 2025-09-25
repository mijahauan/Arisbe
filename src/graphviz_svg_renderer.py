"""
Simple SVG Renderer for Graphviz Layout Engine Output

Renders LayoutDTO objects to SVG for visual verification.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from graphviz_layout_engine import LayoutDTO


class GraphvizSVGRenderer:
    """Renders LayoutDTO to SVG format"""
    
    def render_to_svg(self, dto: LayoutDTO, title: str, egif: str) -> str:
        """Convert LayoutDTO to SVG string"""
        
        # Calculate overall bounds
        if not dto.areas:
            svg_width, svg_height = 400, 300
        else:
            sheet = next((area for area in dto.areas if area.is_sheet), None)
            if sheet:
                svg_width = int(sheet.rect.width + 80)
                svg_height = int(sheet.rect.height + 120)
            else:
                svg_width, svg_height = 400, 300
        
        # Create SVG root
        svg = ET.Element("svg", {
            "width": str(svg_width),
            "height": str(svg_height),
            "xmlns": "http://www.w3.org/2000/svg"
        })
        
        # Background
        ET.SubElement(svg, "rect", {
            "x": "0", "y": "0",
            "width": str(svg_width), "height": str(svg_height),
            "fill": "white", "stroke": "none"
        })
        
        # Title
        ET.SubElement(svg, "text", {
            "x": "10", "y": "20",
            "font-size": "14", "font-weight": "bold",
            "fill": "black"
        }).text = title
        
        # Stats
        stats = f"Graphviz: {len(dto.vertices)}V, {len(dto.edge_labels)}E, {len([a for a in dto.areas if not a.is_sheet])}C, {len(dto.ligatures)}L"
        ET.SubElement(svg, "text", {
            "x": "10", "y": "35",
            "font-size": "10", "fill": "gray"
        }).text = stats
        
        # Offset for content
        offset_x = 40
        offset_y = 60
        
        # Render areas (cuts only, not sheet)
        for area in dto.areas:
            if not area.is_sheet:
                ET.SubElement(svg, "rect", {
                    "x": str(area.rect.x + offset_x),
                    "y": str(area.rect.y + offset_y),
                    "width": str(area.rect.width),
                    "height": str(area.rect.height),
                    "fill": "none",
                    "stroke": "black",
                    "stroke-width": "1.5",
                    "rx": "8.0",
                    "ry": "8.0"
                })
        
        # Render ligatures (behind text)
        for ligature in dto.ligatures:
            if len(ligature.path_points) >= 2:
                # Create path string
                path_parts = []
                for i, (x, y) in enumerate(ligature.path_points):
                    if i == 0:
                        path_parts.append(f"M {x + offset_x} {y + offset_y}")
                    else:
                        path_parts.append(f"L {x + offset_x} {y + offset_y}")
                
                path_d = " ".join(path_parts)
                ET.SubElement(svg, "path", {
                    "d": path_d,
                    "fill": "none",
                    "stroke": "black",
                    "stroke-width": "2.0"
                })
        
        # Render edge labels
        for edge_label in dto.edge_labels:
            ET.SubElement(svg, "text", {
                "x": str(edge_label.rect.x + edge_label.rect.width/2 + offset_x),
                "y": str(edge_label.rect.y + edge_label.rect.height/2 + offset_y),
                "text-anchor": "middle",
                "dominant-baseline": "central",
                "font-size": "12",
                "font-family": "Times New Roman",
                "fill": "black"
            }).text = edge_label.label
        
        # Render vertices
        for vertex in dto.vertices:
            ET.SubElement(svg, "circle", {
                "cx": str(vertex.pos[0] + offset_x),
                "cy": str(vertex.pos[1] + offset_y),
                "r": "3.0",
                "fill": "black",
                "stroke": "none"
            })
        
        # EGIF at bottom
        ET.SubElement(svg, "text", {
            "x": "10",
            "y": str(svg_height - 20),
            "font-size": "12",
            "font-family": "monospace",
            "fill": "black"
        }).text = f"EGIF: {egif}"
        
        # Convert to string
        return ET.tostring(svg, encoding='unicode')
    
    def save_svg(self, dto: LayoutDTO, title: str, egif: str, 
                 filename: str, output_dir: str = "test_outputs") -> Path:
        """Save LayoutDTO as SVG file"""
        
        svg_content = self.render_to_svg(dto, title, egif)
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save file
        svg_file = output_path / f"{filename}.svg"
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        return svg_file
