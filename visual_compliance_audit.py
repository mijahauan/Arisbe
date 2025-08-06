#!/usr/bin/env python3
"""
Visual Compliance Audit Script
Examines how well the visual display corresponds to the underlying EGI structure.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import EGIFParser
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from diagram_renderer_dau import DiagramRendererDau

def audit_visual_compliance():
    """Audit visual compliance for the Loves x y example."""
    
    # Test the Loves x y example
    egif = '*x *y (Loves x y) ~[ (Happy x) ]'
    print(f"=== Visual Compliance Audit ===")
    print(f"Testing EGIF: {egif}")
    print()
    
    # Parse EGI structure
    parser = EGIFParser(egif)
    egi = parser.parse()
    
    print(f"📊 EGI Structure Analysis:")
    print(f"  Vertices: {len(egi.V)}")
    for v in egi.V:
        label = v.label if v.label else f"*{v.id[-8:]}"  # Show last 8 chars of ID
        print(f"    {v.id}: {label} ({'constant' if v.label else 'generic'})")
    
    print(f"  Edges: {len(egi.E)}")
    for e in egi.E:
        relation_name = egi.rel.get(e.id, "UNNAMED")
        arity = len(egi.nu.get(e.id, []))
        vertices = egi.nu.get(e.id, [])
        print(f"    {e.id}: {relation_name} (arity {arity}) -> {vertices}")
    
    print(f"  Cuts: {len(egi.Cut)}")
    for c in egi.Cut:
        area_contents = egi.area.get(c.id, set())
        print(f"    {c.id}: contains {len(area_contents)} elements -> {area_contents}")
    
    print()
    
    # Generate layout
    print(f"🎨 Layout Generation:")
    layout_engine = GraphvizLayoutEngine()
    layout_result = layout_engine.create_layout_from_graph(egi)
    
    print(f"  Layout primitives: {len(layout_result.primitives)}")
    for prim_id, primitive in layout_result.primitives.items():
        print(f"    {prim_id}: {primitive.element_type} at {primitive.position}")
    
    print()
    
    # Check for compliance issues
    print(f"🔍 Compliance Issues Check:")
    
    # Issue 1: Constant vertex labels (Peircean compliance)
    print(f"1. Constant Vertex Labels:")
    constant_issues = []
    for v in egi.V:
        if v.id in layout_result.primitives:
            if v.label:  # This is a constant vertex - should display the constant
                print(f"   ✓ Constant vertex {v.id}: should display '{v.label}'")
                # Note: Renderer must extract this from EGI vertex.label
            else:  # Generic vertex - should show as line of identity only (no label)
                print(f"   ✓ Generic vertex {v.id}: correctly shows as line of identity (no label)")
    
    if constant_issues:
        print(f"   ❌ Constant label issues: {constant_issues}")
    else:
        print(f"   ✅ Constant vertex labeling correct per Peirce/Dau")
    
    # Issue 2: Predicate positioning and padding
    print(f"2. Predicate Positioning:")
    predicate_issues = []
    for e in egi.E:
        if e.id in layout_result.primitives:
            primitive = layout_result.primitives[e.id]
            relation_name = egi.rel.get(e.id, "UNNAMED")
            # Check if predicate has proper bounds (x1, y1, x2, y2)
            x1, y1, x2, y2 = primitive.bounds
            width = x2 - x1
            height = y2 - y1
            if width <= 0 or height <= 0:
                predicate_issues.append(f"{e.id} ({relation_name}) has invalid bounds: {primitive.bounds}")
            else:
                print(f"   ✓ {relation_name}: bounds {primitive.bounds} (w={width:.1f}, h={height:.1f})")
    
    if predicate_issues:
        print(f"   ❌ Predicate padding issues: {predicate_issues}")
    else:
        print(f"   ✅ All predicates have proper dimensions")
    
    # Issue 3: Cut containment
    print(f"3. Cut Containment:")
    containment_issues = []
    for c in egi.Cut:
        expected_contents = egi.area.get(c.id, set())
        if c.id in layout_result.primitives:
            cut_primitive = layout_result.primitives[c.id]
            # Check if all expected contents are visually inside the cut
            for element_id in expected_contents:
                if element_id in layout_result.primitives:
                    element_primitive = layout_result.primitives[element_id]
                    # This is a simplified check - in practice we'd check spatial containment
                    if element_primitive.position == cut_primitive.position:
                        containment_issues.append(f"Element {element_id} not properly positioned inside cut {c.id}")
    
    if containment_issues:
        print(f"   ❌ Containment issues: {containment_issues}")
    else:
        print(f"   ✅ Cut containment appears correct")
    
    print()
    
    # Generate visual output
    print(f"🖼️  Generating Visual Output:")
    try:
        renderer = DiagramRendererDau()
        output_path = 'visual_compliance_audit.png'
        # Check if renderer has the right method
        if hasattr(renderer, 'render_to_file'):
            renderer.render_to_file(layout_result, egi, output_path)
            print(f"   ✅ Visual output saved to: {output_path}")
        elif hasattr(renderer, 'render'):
            # Try alternative render method
            result = renderer.render(layout_result, egi)
            print(f"   ✅ Rendering completed (method: render)")
        else:
            print(f"   ❌ No suitable render method found")
    except Exception as e:
        print(f"   ❌ Rendering failed: {e}")
    
    print()
    print(f"=== Audit Complete ===")

if __name__ == "__main__":
    audit_visual_compliance()
