#!/usr/bin/env python3
"""
Debug structural equivalence issues in EGIF round-trip
Investigates where cut nesting/area containment is being lost
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from egi_core_dau import RelationalGraphWithCuts
    from egif_parser_dau import parse_egif
    from egif_generator_dau import generate_egif
    from frozendict import frozendict
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def analyze_area_structure(graph: RelationalGraphWithCuts, label: str):
    """Analyze and display the area containment structure of a graph"""
    print(f"\n📊 {label} - Area Structure Analysis:")
    print(f"   Vertices: {len(graph.V)}")
    print(f"   Edges: {len(graph.E)}")
    print(f"   Cuts: {len(graph.Cut)}")
    print(f"   Areas: {len(graph.area)}")
    
    print(f"\n   Area Containment Structure:")
    for area_id, contents in graph.area.items():
        if area_id == graph.sheet:
            area_type = "SHEET"
        elif area_id in {c.id for c in graph.Cut}:
            area_type = "CUT"
        else:
            area_type = "UNKNOWN"
        
        print(f"     {area_id} ({area_type}): {len(contents)} elements")
        
        # Show what's contained
        for element_id in contents:
            if element_id in {v.id for v in graph.V}:
                vertex = graph.get_vertex(element_id)
                if vertex.is_generic:
                    print(f"       → Vertex {element_id} (generic)")
                else:
                    print(f"       → Vertex {element_id} (constant: \"{vertex.label}\")")
            elif element_id in {e.id for e in graph.E}:
                edge_name = graph.rel[element_id]
                print(f"       → Edge {element_id} ({edge_name})")
            elif element_id in {c.id for c in graph.Cut}:
                print(f"       → Cut {element_id}")
            else:
                print(f"       → Unknown {element_id}")

def debug_triple_nested_cuts():
    """Debug the specific triple nested cuts case"""
    egif_input = '~[ ~[ ~[ *x ] ] ]'
    print(f"🔍 Debugging structural preservation for: {egif_input}")
    print("=" * 80)
    
    # Step 1: Parse original EGIF
    print("1. Parsing original EGIF...")
    graph1 = parse_egif(egif_input)
    analyze_area_structure(graph1, "ORIGINAL")
    
    # Step 2: Generate EGIF from parsed graph
    print("\n2. Generating EGIF from parsed graph...")
    egif_output = generate_egif(graph1)
    print(f"   Generated: {egif_output}")
    
    # Step 3: Parse the generated EGIF
    print("\n3. Parsing generated EGIF...")
    graph2 = parse_egif(egif_output)
    analyze_area_structure(graph2, "ROUND-TRIP")
    
    # Step 4: Compare area structures
    print("\n4. Comparing Area Structures:")
    
    # Check if area structures are equivalent
    areas1 = {area_id: len(contents) for area_id, contents in graph1.area.items()}
    areas2 = {area_id: len(contents) for area_id, contents in graph2.area.items()}
    
    print(f"   Original areas: {len(areas1)} total")
    print(f"   Round-trip areas: {len(areas2)} total")
    
    # Check vertex containment specifically
    vertex1 = list(graph1.V)[0]  # Should be only one vertex
    vertex2 = list(graph2.V)[0]
    
    # Find which area contains each vertex
    vertex1_area = None
    vertex2_area = None
    
    for area_id, contents in graph1.area.items():
        if vertex1.id in contents:
            vertex1_area = area_id
            break
    
    for area_id, contents in graph2.area.items():
        if vertex2.id in contents:
            vertex2_area = area_id
            break
    
    print(f"\n   Vertex Containment:")
    print(f"     Original: vertex in area {vertex1_area}")
    print(f"     Round-trip: vertex in area {vertex2_area}")
    
    if vertex1_area == graph1.sheet and vertex2_area == graph2.sheet:
        print("     ✅ Both vertices at sheet level")
    elif vertex1_area != graph1.sheet and vertex2_area != graph2.sheet:
        print("     ⚠️  Both vertices in cuts (need deeper analysis)")
    else:
        print("     ❌ CRITICAL: Vertex moved between sheet and cut!")
        print("     🚨 This represents a fundamental logical change!")
    
    # Check cut nesting depth
    def get_nesting_depth(graph, vertex_id):
        """Calculate nesting depth of a vertex"""
        current_area = None
        for area_id, contents in graph.area.items():
            if vertex_id in contents:
                current_area = area_id
                break
        
        if current_area == graph.sheet:
            return 0
        
        # Count how many cuts contain this area
        depth = 1
        while current_area != graph.sheet:
            # Find parent area that contains this cut
            parent_found = False
            for area_id, contents in graph.area.items():
                if current_area in contents:
                    current_area = area_id
                    if current_area != graph.sheet:
                        depth += 1
                    parent_found = True
                    break
            if not parent_found:
                break
        
        return depth
    
    depth1 = get_nesting_depth(graph1, vertex1.id)
    depth2 = get_nesting_depth(graph2, vertex2.id)
    
    print(f"\n   Nesting Depth:")
    print(f"     Original: {depth1} levels deep")
    print(f"     Round-trip: {depth2} levels deep")
    
    if depth1 == depth2:
        print("     ✅ Nesting depth preserved")
    else:
        print("     ❌ CRITICAL: Nesting depth changed!")
        print("     🚨 This violates EG structural semantics!")

def test_other_structural_cases():
    """Test other cases that might have structural issues"""
    test_cases = [
        '~[ *x ]',
        '~[ ~[ *x ] ]',
        '~[ (loves *x *y) ]',
        '*x ~[ *y ]',
        '(loves *x *y) ~[ (mortal *x) ]'
    ]
    
    print("\n" + "=" * 80)
    print("Testing Other Structural Preservation Cases")
    print("=" * 80)
    
    for egif_input in test_cases:
        print(f"\n🧪 Testing: {egif_input}")
        try:
            graph1 = parse_egif(egif_input)
            egif_output = generate_egif(graph1)
            graph2 = parse_egif(egif_output)
            
            # Quick structural comparison
            areas1 = len(graph1.area)
            areas2 = len(graph2.area)
            
            if egif_input.strip() == egif_output.strip():
                print(f"   ✅ Perfect: {egif_output}")
            elif areas1 == areas2:
                print(f"   ⚠️  Syntax changed: {egif_output} (same structure)")
            else:
                print(f"   ❌ Structure changed: {egif_output}")
                print(f"      Areas: {areas1} → {areas2}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("Debugging Structural Equivalence in EGIF Round-trip")
    print("Investigating area containment and cut nesting preservation")
    
    debug_triple_nested_cuts()
    test_other_structural_cases()
    
    print("\n" + "=" * 80)
    print("CRITICAL FINDINGS:")
    print("- Area containment structure MUST be preserved")
    print("- Cut nesting depth MUST remain identical")
    print("- Vertex/edge placement in areas MUST be maintained")
    print("- Any structural change represents logical transformation")
    print("=" * 80)
