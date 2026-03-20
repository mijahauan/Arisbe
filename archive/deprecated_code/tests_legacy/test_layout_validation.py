"""Layout Engine Validation Tests"""

import pytest
from src.layout_engine import LayoutEngine, LayoutResult
from src.egi_core_dau import create_empty_graph, create_vertex, create_cut


def validate_layout(egi, layout):
    """Validate layout output"""
    violations = []
    
    # Check cut overlaps
    cuts = list(layout.cut_bounds.keys())
    for i, c1 in enumerate(cuts):
        for c2 in cuts[i+1:]:
            if layout.cut_bounds[c1].overlaps_with(layout.cut_bounds[c2]):
                violations.append(f"Cuts {c1} and {c2} overlap")
    
    # Check containment
    for area_id, elements in egi.area.items():
        if area_id == egi.sheet:
            continue
        if area_id not in layout.cut_bounds:
            violations.append(f"Area {area_id} missing bounds")
            continue
        
        bounds = layout.cut_bounds[area_id]
        for elem_id in elements:
            if elem_id in layout.vertex_positions:
                pos = layout.vertex_positions[elem_id]
                if not bounds.contains_point(pos):
                    violations.append(f"Vertex {elem_id} not in area {area_id}")
    
    # Check DTO completeness
    for vertex in egi.V:
        if vertex.id not in layout.vertex_positions:
            violations.append(f"Vertex {vertex.id} missing position")
    
    return violations


def test_layout_validation():
    """Test layout validation"""
    engine = LayoutEngine()
    
    # Create test EGI
    egi = create_empty_graph()
    vertex = create_vertex(label="Human", is_generic=False)
    egi = egi.with_vertex(vertex)
    
    # Compute layout
    layout = engine.compute_layout(egi)
    
    # Validate
    violations = validate_layout(egi, layout)
    
    # Should have no violations
    assert len(violations) == 0, f"Layout violations: {violations}"


def test_cut_containment():
    """Test cut containment validation"""
    engine = LayoutEngine()
    
    # Create EGI with cut
    egi = create_empty_graph()
    cut = create_cut()
    vertex = create_vertex(label="Human", is_generic=False)
    
    egi = egi.with_cut(cut)
    egi = egi.with_vertex_in_context(vertex, cut.id)
    
    layout = engine.compute_layout(egi)
    violations = validate_layout(egi, layout)
    
    assert len(violations) == 0, f"Containment violations: {violations}"


def test_layout_visual_sanity_check():
    """Visual sanity check - generates SVG for manual inspection"""
    from pathlib import Path
    import xml.etree.ElementTree as ET
    
    engine = LayoutEngine()
    
    # Test with simple EGIF
    from egif_parser_dau import parse_egif
    egi = parse_egif('~[ *x (Human x) ]')
    layout = engine.compute_layout(egi)
    
    # Generate Dau-compliant SVG
    svg = ET.Element("svg", {
        "width": "250", "height": "200", 
        "xmlns": "http://www.w3.org/2000/svg"
    })
    
    # White background
    ET.SubElement(svg, "rect", {
        "x": "0", "y": "0", "width": "250", "height": "200",
        "fill": "white"
    })
    
    # Cuts - thin black lines with rounded corners (Dau style)
    for bounds in layout.cut_bounds.values():
        ET.SubElement(svg, "rect", {
            "x": str(bounds.min_x + 20), "y": str(bounds.min_y + 30),
            "width": str(bounds.max_x - bounds.min_x),
            "height": str(bounds.max_y - bounds.min_y),
            "fill": "none", "stroke": "black", "stroke-width": "1",
            "rx": "8", "ry": "8"  # Rounded corners per Dau specification
        })
    
    # Vertices - black spots
    for pos in layout.vertex_positions.values():
        ET.SubElement(svg, "circle", {
            "cx": str(pos.x + 20), "cy": str(pos.y + 30), "r": "2",
            "fill": "black", "stroke": "none"
        })
    
    # EGIF at bottom
    from egif_generator_dau import EGIFGenerator
    egif_gen = EGIFGenerator()
    egif_text = egif_gen.generate_egif(egi)
    ET.SubElement(svg, "text", {
        "x": "10", "y": "190", "font-family": "monospace", "font-size": "12"
    }).text = f"EGIF: {egif_text}"
    
    # Save for inspection
    output_dir = Path("test_outputs")
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "layout_sanity_check.svg", 'w') as f:
        f.write(ET.tostring(svg, encoding='unicode'))
    
    # Basic assertions
    assert len(layout.vertex_positions) == 1
    assert len(layout.cut_bounds) == 1
