"""
Simple SVG Renderer for Graphviz Layout Engine Output

Renders LayoutDTO objects to SVG for visual verification.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from definitive_egi_layout_engine import LayoutDTO


class GraphvizSVGRenderer:
    """Renders LayoutDTO to SVG format"""
    
    def render_to_svg(self, dto: LayoutDTO, title: str, egif: str, style: Optional[dict] = None) -> str:
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
        
        # Render areas (cuts only, not sheet) with styling
        for area in dto.areas:
            if not area.is_sheet:
                # Get styling from area or use defaults
                fill = area.style.get('fill', 'none')
                stroke_width = str(area.style.get('stroke_width', 1.5))
                shape = area.style.get('shape', 'rounded_rectangle')
                
                # DEBUG: Print fill value
                print(f"DEBUG SVG Renderer: Area {area.id} fill='{fill}'")
                
                # Apply shape-specific attributes
                rect_attrs = {
                    "x": str(area.rect.x + offset_x),
                    "y": str(area.rect.y + offset_y),
                    "width": str(area.rect.width),
                    "height": str(area.rect.height),
                    "fill": fill,
                    "stroke": "black",
                    "stroke-width": stroke_width
                }
                
                if shape == 'rounded_rectangle':
                    rect_attrs.update({"rx": "8.0", "ry": "8.0"})
                
                ET.SubElement(svg, "rect", rect_attrs)
        
        # Render ligatures (behind text) with styling
        for ligature in dto.ligatures:
            if len(ligature.path_points) >= 2:
                # Get styling from ligature or use defaults
                stroke_color = ligature.style.get('color', 'black')
                stroke_width = str(ligature.style.get('stroke_width', 2.0))
                
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
                    "stroke": stroke_color,
                    "stroke-width": stroke_width
                })
        
        # Render edge labels with styling
        for edge_label in dto.edge_labels:
            # Get styling from label or use defaults
            font_color = edge_label.style.get('font_color', 'black')
            
            ET.SubElement(svg, "text", {
                "x": str(edge_label.rect.x + edge_label.rect.width/2 + offset_x),
                "y": str(edge_label.rect.y + edge_label.rect.height/2 + offset_y),
                "text-anchor": "middle",
                "dominant-baseline": "central",
                "font-size": "12",
                "font-family": "Times New Roman",
                "fill": font_color
            }).text = edge_label.label
            
            # Render connection ports if enabled in style
            show_ports = style and style.get('annotations', {}).get('show_connection_ports', False)
            if show_ports:
                for port in edge_label.connection_ports:
                    ET.SubElement(svg, "circle", {
                        "cx": str(port.position[0] + offset_x),
                        "cy": str(port.position[1] + offset_y),
                        "r": "2.0",
                        "fill": "red",
                        "stroke": "darkred",
                        "stroke-width": "0.5"
                    })
                    
                    # Add port number label
                    ET.SubElement(svg, "text", {
                        "x": str(port.position[0] + offset_x + 5),
                        "y": str(port.position[1] + offset_y - 5),
                        "font-size": "8",
                        "fill": "darkred",
                        "font-weight": "bold"
                    }).text = str(port.port_id)
        
        # Render vertices
        for vertex in dto.vertices:
            ET.SubElement(svg, "circle", {
                "cx": str(vertex.pos[0] + offset_x),
                "cy": str(vertex.pos[1] + offset_y),
                "r": "3.0",
                "fill": "black",
                "stroke": "none"
            })
        
        # Render annotations
        for annotation in dto.annotations:
            if annotation.text:
                # Get styling from annotation or use defaults
                font_size = str(annotation.style.get('font_size', 10))
                font_color = annotation.style.get('font_color', 'blue')
                font_weight = annotation.style.get('font_weight', 'normal')
                
                text_attrs = {
                    "x": str(annotation.position[0] + offset_x),
                    "y": str(annotation.position[1] + offset_y),
                    "font-size": font_size,
                    "fill": font_color,
                    "font-weight": font_weight
                }
                
                ET.SubElement(svg, "text", text_attrs).text = annotation.text
        
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
                 filename: str, output_dir: str = "test_outputs", style: Optional[dict] = None) -> Path:
        """Save LayoutDTO as SVG file"""
        
        svg_content = self.render_to_svg(dto, title, egif, style)
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save file
        svg_file = output_path / f"{filename}.svg"
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        return svg_file
