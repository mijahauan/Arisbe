#!/usr/bin/env python3
"""
Visual Rendering Test for Arisbe EG Implementation

Tests the complete pipeline: EGIF → EGI → Layout → Visual Rendering
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import GraphvizLayoutEngine, create_canonical_layout
from pyside6_backend import PySide6Canvas, PySide6Backend
from canvas_backend import EGDrawingStyles
from diagram_renderer_dau import DiagramRendererDau


def test_egif_visual_rendering():
    """Test visual rendering of various EGIF expressions."""
    
    # Test cases with different EG structures
    test_cases = [
        {
            'name': 'Simple Relation',
            'egif': '(Human "Socrates")',
            'description': 'Basic unary relation with constant'
        },
        {
            'name': 'Sibling Cuts',
            'egif': '*x ~[ (Human x) ] ~[ (Mortal x) ]',
            'description': 'Two sibling cuts with shared variable'
        },
        {
            'name': 'Nested Cuts',
            'egif': '*x (Human x) ~[ (Mortal x) ~[ (Wise x) ] ]',
            'description': 'Nested cuts with proper containment'
        },
        {
            'name': 'Binary Relation',
            'egif': '*x *y (Loves x y)',
            'description': 'Binary relation with two variables'
        }
    ]
    
    print("🎨 Testing Visual EG Rendering Pipeline")
    print("=" * 50)
    
    # Initialize layout engine (non-canonical baseline)
    layout_engine = GraphvizLayoutEngine()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}: {test_case['egif']}")
        print(f"   {test_case['description']}")
        
        try:
            # Step 1: Parse EGIF → EGI
            graph = parse_egif(test_case['egif'])
            print(f"   ✅ Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
            
            # Step 2: Create Layout (canonical)
            layout = create_canonical_layout(graph)
            print(f"   ✅ Layout: {len(layout.primitives)} elements positioned")
            
            # Step 3: Render to PNG (Dau-compliant renderer)
            output_file = f"test_render_{i}_{test_case['name'].lower().replace(' ', '_')}.png"
            render_layout_to_file(graph, layout, output_file, test_case['name'])
            print(f"   ✅ Rendered: {output_file}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n🎯 Visual rendering test complete!")
    print(f"Check generated PNG files to verify EG diagram correctness.")


def _layout_hash(layout) -> str:
    """Compute a stable, order-independent hash of a LayoutResult."""
    import hashlib
    items = []
    for eid, prim in sorted(layout.primitives.items(), key=lambda kv: str(kv[0])):
        et = getattr(prim, 'element_type', '')
        pos = getattr(prim, 'position', None)
        b = getattr(prim, 'bounds', None)
        z = getattr(prim, 'z_index', 0)
        items.append((str(eid), et, pos, b, z))
    m = hashlib.sha256()
    for rec in items:
        m.update(str(rec).encode('utf-8'))
    # include coarse canvas bounds to catch size drift
    cb = getattr(layout, 'canvas_bounds', None)
    m.update(str(cb).encode('utf-8'))
    return m.hexdigest()


def test_canonical_layout_determinism():
    """Canonical layout must be deterministic for a fixed EGI."""
    cases = [
        '(Human "Socrates")',
        '*x ~[ (Human x) ]',
        '*x ~[ (P x) ] ~[ (Q x) ]',
        '*x *y (Loves x y)',
    ]
    for egif in cases:
        g = parse_egif(egif)
        a = create_canonical_layout(g)
        b = create_canonical_layout(g)
        ha = _layout_hash(a)
        hb = _layout_hash(b)
        assert ha == hb, f"Canonical layout nondeterministic for: {egif} (\n{ha}\n!=\n{hb}\n)"


def render_layout_to_file(egi, layout, filename, title):
    """Render a layout to PNG file using the Dau-compliant renderer."""
    canvas = PySide6Canvas(1000, 800, title=f"Arisbe EG: {title}")
    DiagramRendererDau().render_diagram(canvas, egi, layout, selected_ids=None)
    canvas.save_to_file(filename)
    print(f"   💾 Saved diagram to: {filename}")


def quick_visual_test():
    """Quick test to verify the rendering pipeline is working."""
    
    print("🚀 Quick Visual Test")
    print("-" * 20)
    
    # Simple test case
    egif = '*x (Human x) ~[ (Mortal x) ]'
    print(f"Testing: {egif}")
    
    try:
        # Parse
        graph = parse_egif(egif)
        print("✅ EGIF parsing successful")
        
        # Layout
        engine = GraphvizLayoutEngine()
        layout = engine.create_layout_from_graph(graph)
        print("✅ Layout generation successful")
        
        # Show layout details
        print(f"📊 Layout contains {len(layout.primitives)} elements:")
        for elem_id, primitive in layout.primitives.items():
            print(f"   {elem_id}: {primitive.element_type} at {primitive.position}")
        
        print("🎯 Rendering pipeline is functional!")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return False


if __name__ == "__main__":
    print("Arisbe Visual Rendering Test")
    print("=" * 40)
    
    # First do a quick test
    if quick_visual_test():
        print("\n" + "=" * 40)
        # If quick test passes, run full visual tests
        test_egif_visual_rendering()
    else:
        print("❌ Quick test failed - check pipeline components")
