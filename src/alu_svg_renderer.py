"""
ALU to SVG Renderer

Converts Abstract Layout Unit (ALU) data structures to SVG format
for visual verification of the layout engine results.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from abstract_layout_engine import AbstractLayoutUnit


class ALUSVGRenderer:
    """Renders ALU data structures to SVG format"""
    
    def render_to_svg(self, alu: AbstractLayoutUnit, title: str, egif: str) -> str:
        """Convert ALU to SVG string"""
        
        # Calculate SVG dimensions with margins
        margin = 40
        svg_width = int(alu.total_width + 2 * margin)
        svg_height = int(alu.total_height + 2 * margin + 60)  # Extra for title and EGIF
        
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
        stats = f"ALU: {len(alu.vertices)}V, {len(alu.edge_labels)}E, {len(alu.areas)-1}C, {len(alu.ligatures)}L"
        ET.SubElement(svg, "text", {
            "x": "10", "y": "35",
            "font-size": "10", "fill": "gray"
        }).text = stats
        
        # Render areas (cuts only, not sheet)
        for area in alu.areas:
            if area.type == 'cut':
                ET.SubElement(svg, "rect", {
                    "x": str(area.x + margin),
                    "y": str(area.y + margin + 50),  # +50 for title space
                    "width": str(area.width),
                    "height": str(area.height),
                    "fill": "none",
                    "stroke": "black",
                    "stroke-width": "1.5",
                    "rx": "8.0",
                    "ry": "8.0"
                })
        
        # Render ligatures (behind text)
        for ligature in alu.ligatures:
            if len(ligature.path) >= 2:
                start = ligature.path[0]
                end = ligature.path[-1]
                ET.SubElement(svg, "path", {
                    "d": f"M {start.x + margin} {start.y + margin + 50} L {end.x + margin} {end.y + margin + 50}",
                    "fill": "none",
                    "stroke": "black",
                    "stroke-width": "2.0"
                })
        
        # Render edge labels
        for edge in alu.edge_labels:
            ET.SubElement(svg, "text", {
                "x": str(edge.x + margin),
                "y": str(edge.y + margin + 50),
                "text-anchor": "middle",
                "font-size": "12",
                "font-family": "Times New Roman",
                "fill": "black"
            }).text = edge.text
        
        # Render vertices
        for vertex in alu.vertices:
            ET.SubElement(svg, "circle", {
                "cx": str(vertex.x + margin),
                "cy": str(vertex.y + margin + 50),
                "r": str(vertex.radius),
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
    
    def save_svg(self, alu: AbstractLayoutUnit, title: str, egif: str, 
                 filename: str, output_dir: str = "test_outputs") -> Path:
        """Save ALU as SVG file"""
        
        svg_content = self.render_to_svg(alu, title, egif)
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save file
        svg_file = output_path / f"{filename}.svg"
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        return svg_file
