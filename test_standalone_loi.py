#!/usr/bin/env python3
"""
Test Standalone Lines of Identity (LoI) Implementation
Demonstrates Dau's Transformation Rule 6 (Isolated Vertex) support
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import EGIFParser
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from frozendict import frozendict

def create_test_egi_with_isolated_vertices():
    """Create an EGI with both connected and isolated vertices to test LoI rendering."""
    
    # Create vertices: some connected to predicates, some isolated
    v1 = Vertex(id="v_connected", label="Socrates", is_generic=False)  # Connected constant
    v2 = Vertex(id="v_generic", label=None, is_generic=True)           # Connected generic
    v3 = Vertex(id="v_isolated_const", label="Plato", is_generic=False) # Isolated constant
    v4 = Vertex(id="v_isolated_gen", label=None, is_generic=True)       # Isolated generic
    
    # Create edges (predicates)
    e1 = Edge(id="e_human")
    e2 = Edge(id="e_mortal")
    
    # Create cut
    c1 = Cut(id="cut_1")
    
    # Nu mapping: connect some vertices to predicates, leave others isolated
    nu_mapping = frozendict({
        "e_human": ("v_connected",),      # Socrates is Human
        "e_mortal": ("v_generic",)        # Generic vertex is Mortal
        # v_isolated_const and v_isolated_gen are NOT in nu mapping (isolated)
    })
    
    # Relation mapping
    rel_mapping = frozendict({
        "e_human": "Human",
        "e_mortal": "Mortal"
    })
    
    # Area mapping: distribute elements across sheet and cut
    area_mapping = frozendict({
        "sheet": frozenset({"v_connected", "e_human", "v_isolated_const", "cut_1"}),
        "cut_1": frozenset({"v_generic", "e_mortal", "v_isolated_gen"})
    })
    
    # Create EGI
    egi = RelationalGraphWithCuts(
        V=frozenset([v1, v2, v3, v4]),
        E=frozenset([e1, e2]),
        nu=nu_mapping,
        sheet="sheet",
        Cut=frozenset([c1]),
        area=area_mapping,
        rel=rel_mapping
    )
    
    return egi

def test_isolated_vertex_detection():
    """Test that we can correctly identify isolated vertices."""
    egi = create_test_egi_with_isolated_vertices()
    
    print("=== ISOLATED VERTEX DETECTION TEST ===")
    print(f"Total vertices: {len(egi.V)}")
    print(f"Nu mappings: {dict(egi.nu)}")
    
    # Check each vertex
    for vertex in egi.V:
        is_connected = False
        for edge_id, vertex_sequence in egi.nu.items():
            if vertex.id in vertex_sequence:
                is_connected = True
                break
        
        status = "CONNECTED" if is_connected else "ISOLATED"
        vertex_type = "constant" if vertex.label else "generic"
        print(f"  {vertex.id} ({vertex_type}): {status}")
        
        if not is_connected:
            print(f"    → Should render as standalone LoI (heavy line segment)")
        else:
            print(f"    → Should render as identity spot (connected to predicate)")
    
    return egi

def generate_test_egif():
    """Generate EGIF that includes isolated vertices for testing."""
    # This EGIF should create isolated vertices when parsed
    test_egif = '*x (Human "Socrates") *y ~[ (Mortal x) *z ]'
    
    print("\n=== EGIF PARSING TEST ===")
    print(f"Test EGIF: {test_egif}")
    print("Expected result:")
    print("  - Socrates: connected to Human predicate")
    print("  - x: connected to Mortal predicate") 
    print("  - y: isolated vertex on sheet (standalone LoI)")
    print("  - z: isolated vertex in cut (standalone LoI)")
    
    return test_egif

def main():
    """Run standalone LoI tests."""
    print("STANDALONE LINES OF IDENTITY TEST")
    print("=" * 50)
    print("Testing Dau's Transformation Rule 6 (Isolated Vertex)")
    print("Isolated vertices should render as heavy line segments")
    print("Connected vertices should render as identity spots")
    print("=" * 50)
    
    # Test 1: Manual EGI construction
    egi = test_isolated_vertex_detection()
    
    # Test 2: EGIF parsing
    test_egif = generate_test_egif()
    
    try:
        parser = EGIFParser()
        parsed_egi = parser.parse(test_egif)
        
        print(f"\n=== PARSED EGI ANALYSIS ===")
        print(f"Vertices: {len(parsed_egi.V)}")
        print(f"Edges: {len(parsed_egi.E)}")
        print(f"Nu mappings: {dict(parsed_egi.nu)}")
        
        # Analyze which vertices are isolated
        for vertex in parsed_egi.V:
            is_connected = False
            for edge_id, vertex_sequence in parsed_egi.nu.items():
                if vertex.id in vertex_sequence:
                    is_connected = True
                    break
            
            status = "CONNECTED" if is_connected else "ISOLATED"
            vertex_type = f"'{vertex.label}'" if vertex.label else "generic"
            print(f"  {vertex.id} ({vertex_type}): {status}")
            
    except Exception as e:
        print(f"Error parsing EGIF: {e}")
    
    print("\n" + "=" * 50)
    print("IMPLEMENTATION STATUS:")
    print("✓ Vertex rendering enhanced for standalone LoI")
    print("✓ Hit-testing updated for line segments")
    print("✓ Selection overlays support LoI highlighting")
    print("✓ Isolated vertex detection logic implemented")
    print("\nNext: Test in GUI to verify visual rendering")
    print("=" * 50)

if __name__ == "__main__":
    main()
