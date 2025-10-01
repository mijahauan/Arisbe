#!/usr/bin/env python3
"""
EGIF Layout Visualizer - Shows EGIF input with authentic EG styling
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from layout_engine import LayoutEngine
from egif_parser_dau import parse_egif
import xml.etree.ElementTree as ET


def render_authentic_eg(layout, egi, egif_source):
    """Render with authentic Dau styling (white vertices, black outlines)"""
    viewport = layout.viewport_bounds
    width = viewport.max_x - viewport.min_x + 40
    height = viewport.max_y - viewport.min_y + 60
    
    svg = ET.Element("svg", {
        "width": str(int(width)), "height": str(int(height)),
        "xmlns": "http://www.w3.org/2000/svg"
    })
    
    # Show EGIF source
    ET.SubElement(svg, "text", {
        "x": "10", "y": "20", "font-family": "Arial", "font-size": "14",
        "font-weight": "bold"
    }).text = f"EGIF: {egif_source}"
    
    # White background
    ET.SubElement(svg, "rect", {
        "x": "0", "y": "30", "width": str(width), "height": str(height-30),
        "fill": "white", "stroke": "gray"
    })
    
    # Cuts - black rounded rectangles
    for bounds in layout.cut_bounds.values():
        ET.SubElement(svg, "rect", {
            "x": str(bounds.min_x), "y": str(bounds.min_y + 30),
            "width": str(bounds.max_x - bounds.min_x),
            "height": str(bounds.max_y - bounds.min_y),
            "fill": "none", "stroke": "black", "stroke-width": "2", "rx": "8"
        })
    
    # Vertices - white circles with black outline (authentic Dau style)
    for vertex_id, pos in layout.vertex_positions.items():
        ET.SubElement(svg, "circle", {
            "cx": str(pos.x), "cy": str(pos.y + 30), "r": "8",
            "fill": "white", "stroke": "black", "stroke-width": "2"
        })
        
        # Add labels
        if egi:
            for vertex in egi.V:
                if vertex.id == vertex_id and vertex.label:
                    ET.SubElement(svg, "text", {
                        "x": str(pos.x), "y": str(pos.y + 50),
                        "text-anchor": "middle", "font-size": "12"
                    }).text = vertex.label
    
    return ET.tostring(svg, encoding='unicode')


def test_egif_visualization():
    """Test with simple EGIF cases"""
    engine = LayoutEngine()
    
    test_cases = [
        ("simple", "*x (Human x)"),
        ("in_cut", "~[ *x (Human x) ]"),
        ("nested", "~[ ~[ *x (Human x) ] ]")
    ]
    
    output_dir = Path("egif_layouts")
    output_dir.mkdir(exist_ok=True)
    
    for name, egif in test_cases:
        print(f"Processing: {egif}")
        
        egi = parse_egif(egif)
        layout = engine.compute_layout(egi)
        svg = render_authentic_eg(layout, egi, egif)
        
        with open(output_dir / f"{name}.svg", 'w') as f:
            f.write(svg)
        
        print(f"  → {name}.svg (vertices: {len(layout.vertex_positions)}, cuts: {len(layout.cut_bounds)})")


if __name__ == "__main__":
    test_egif_visualization()
