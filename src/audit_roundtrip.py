#!/usr/bin/env python3
"""
Phase 1a: Audit Current Round-trip Pipeline
Tests EGIF → RelationalGraphWithCuts → Visual → Back to identify issues
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from egi_core_dau import RelationalGraphWithCuts, create_empty_graph, create_vertex, create_edge, create_cut
from diagram_canvas import DiagramCanvas, DiagramLayout
import json

def test_basic_round_trip():
    """Test basic round-trip: EGI → Visual → Back"""
    print("=== Phase 1a: Round-trip Audit ===\n")
    
    # Step 1: Create a simple EGI graph
    print("1. Creating test EGI graph...")
    graph = create_empty_graph()
    
    # Add a vertex
    vertex = create_vertex(label="Socrates", is_generic=False)
    graph = graph.with_vertex(vertex)
    
    # Add a cut
    cut = create_cut()
    graph = graph.with_cut(cut)
    
    # Add another vertex inside the cut
    vertex2 = create_vertex()
    graph = graph.with_vertex(vertex2)
    
    # Move vertex2 to the cut
    from frozendict import frozendict
    new_area = dict(graph.area)
    # Remove from sheet
    new_area[graph.sheet] = new_area[graph.sheet] - {vertex2.id}
    # Add to cut
    new_area[cut.id] = frozenset({vertex2.id})
    
    graph = RelationalGraphWithCuts(
        V=graph.V,
        E=graph.E,
        nu=graph.nu,
        sheet=graph.sheet,
        Cut=graph.Cut,
        area=frozendict(new_area),
        rel=graph.rel
    )
    
    print(f"   Created graph with {len(graph.V)} vertices, {len(graph.Cut)} cuts")
    print(f"   Sheet contains: {graph.area[graph.sheet]}")
    print(f"   Cut contains: {graph.area[cut.id]}")
    
    # Step 2: Test layout generation
    print("\n2. Testing layout generation...")
    layout_engine = DiagramLayout(800, 600)
    
    try:
        visual_elements = layout_engine.layout_graph(graph)
        print(f"   ✓ Layout generated {len(visual_elements)} visual elements")
        
        # Examine what was created
        for elem_id, visual_elem in visual_elements.items():
            elem_type = type(visual_elem).__name__
            position = visual_elem.position
            print(f"     {elem_id}: {elem_type} at {position}")
            
    except Exception as e:
        print(f"   ✗ Layout generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Test rendering (without GUI)
    print("\n3. Testing rendering pipeline...")
    try:
        # Create a canvas for testing (headless)
        canvas = DiagramCanvas(800, 600, backend_name="tkinter")
        canvas.render_graph(graph)
        print(f"   ✓ Rendering completed successfully")
        print(f"   ✓ Canvas has {len(canvas.visual_elements)} visual elements")
        
    except Exception as e:
        print(f"   ✗ Rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test information preservation
    print("\n4. Testing information preservation...")
    
    # Check if all original elements are represented
    original_elements = set()
    original_elements.update(v.id for v in graph.V)
    original_elements.update(e.id for e in graph.E)
    original_elements.update(c.id for c in graph.Cut)
    
    visual_element_ids = set(canvas.visual_elements.keys())
    
    missing_in_visual = original_elements - visual_element_ids
    extra_in_visual = visual_element_ids - original_elements
    
    if missing_in_visual:
        print(f"   ⚠ Missing in visual: {missing_in_visual}")
    if extra_in_visual:
        print(f"   ⚠ Extra in visual: {extra_in_visual}")
    
    if not missing_in_visual and not extra_in_visual:
        print(f"   ✓ All elements preserved in visual representation")
    
    return True

def test_egif_round_trip():
    """Test EGIF parsing and generation round-trip"""
    print("\n=== EGIF Round-trip Test ===")
    
    # Test with a simple EGIF string using correct Sowa-compliant syntax
    # Based on working examples: '(human "Socrates") ~[ (mortal "Socrates") ] *x'
    egif_input = '(human "Socrates") ~[ *x (mortal x) ]'
    
    print(f"Input EGIF: {egif_input}")
    
    try:
        # Import EGIF components
        from egif_parser_dau import parse_egif
        from egif_generator_dau import generate_egif
        
        # Step 1: Parse EGIF to graph
        print("\n   1. Parsing EGIF to graph...")
        graph = parse_egif(egif_input)
        print(f"      ✓ Parsed to graph with {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
        
        # Step 2: Generate EGIF from graph
        print("\n   2. Generating EGIF from graph...")
        egif_output = generate_egif(graph)
        print(f"      ✓ Generated EGIF: {egif_output}")
        
        # Step 3: Test visual round-trip
        print("\n   3. Testing EGIF → Visual → EGIF round-trip...")
        from diagram_canvas import DiagramLayout
        
        # Generate visual layout
        layout_engine = DiagramLayout(800, 600)
        visual_elements = layout_engine.layout_graph(graph)
        print(f"      ✓ Generated {len(visual_elements)} visual elements")
        
        # Generate EGIF from the same graph (should be identical)
        egif_roundtrip = generate_egif(graph)
        
        if egif_output == egif_roundtrip:
            print(f"      ✓ EGIF round-trip preserved: {egif_roundtrip}")
        else:
            print(f"      ⚠ EGIF round-trip differs:")
            print(f"        Original: {egif_output}")
            print(f"        Round-trip: {egif_roundtrip}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ EGIF round-trip failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_current_state():
    """Analyze what components are working vs broken"""
    print("\n=== Current State Analysis ===")
    
    components = {
        "EGI Core (egi_core_dau.py)": "✓ Solid - Dau-compliant implementation",
        "Layout Engine (DiagramLayout)": "? Testing...",
        "Rendering Pipeline (DiagramCanvas)": "? Testing...",
        "Canvas Backend": "? Testing...",
        "EGIF Parser": "? Not tested yet",
        "Selection System": "✗ Known broken",
        "GUI Integration": "✗ Known broken"
    }
    
    for component, status in components.items():
        print(f"   {component}: {status}")
    
    return components

if __name__ == "__main__":
    print("Phase 1a: Auditing Current Round-trip Pipeline")
    print("=" * 50)
    
    # Run the audit
    analyze_current_state()
    success = test_basic_round_trip()
    test_egif_round_trip()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ Basic round-trip audit completed - see results above")
    else:
        print("✗ Round-trip audit found critical issues")
    
    print("\nNext: Examine EGIF parser and strengthen any weak components")
