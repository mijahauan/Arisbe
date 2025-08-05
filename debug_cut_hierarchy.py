#!/usr/bin/env python3
"""
Debug Cut Hierarchy Building

Test to verify that nested cuts are properly identified and structured
for Graphviz hierarchical layout.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_cut_hierarchy():
    """Debug the cut hierarchy building for nested cuts."""
    
    print("🔍 Debugging Cut Hierarchy Building")
    print("=" * 40)
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        # Test with nested cuts case
        test_egif = '*x ~[ ~[ (Mortal x) ] ]'
        print(f"Testing: {test_egif}")
        
        graph = parse_egif(test_egif)
        layout_engine = GraphvizLayoutEngine()
        
        print(f"\n📊 Graph Structure:")
        print(f"  Sheet: {graph.sheet}")
        print(f"  Cuts: {[cut.id for cut in graph.Cut]}")
        print(f"  Areas: {dict(graph.area)}")
        
        # Build hierarchy
        hierarchy = layout_engine._build_cut_hierarchy(graph)
        print(f"\n🏗️  Cut Hierarchy:")
        for parent, children in hierarchy.items():
            child_ids = [child.id for child in children]
            print(f"  {parent} → {child_ids}")
        
        # Check each cut's parent
        print(f"\n🔗 Parent-Child Relationships:")
        for cut in graph.Cut:
            parent = layout_engine._get_cut_parent(cut, graph)
            print(f"  Cut {cut.id[:8]} → Parent: {parent}")
        
        # Generate DOT to see structure
        print(f"\n📄 DOT Structure:")
        dot_content = layout_engine._generate_dot_from_egi(graph)
        
        # Extract cluster structure from DOT
        lines = dot_content.split('\n')
        cluster_lines = [line for line in lines if 'subgraph cluster_' in line or line.strip() == '}']
        
        print("  Cluster nesting in DOT:")
        indent_level = 0
        for line in cluster_lines:
            if 'subgraph cluster_' in line:
                print(f"    {'  ' * indent_level}{line.strip()}")
                indent_level += 1
            elif line.strip() == '}':
                indent_level -= 1
                print(f"    {'  ' * indent_level}{line.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_expected_vs_actual():
    """Analyze what the hierarchy should be vs what we're getting."""
    
    print(f"\n🎯 Expected vs Actual Analysis")
    print("-" * 35)
    
    print("For EGIF: *x ~[ ~[ (Mortal x) ] ]")
    print()
    print("EXPECTED STRUCTURE:")
    print("  Sheet")
    print("  └── Outer Cut (contains inner cut)")
    print("      └── Inner Cut (contains predicate)")
    print("          └── Predicate (Mortal x)")
    print("  └── Vertex *x (at sheet level)")
    print()
    print("EXPECTED DOT STRUCTURE:")
    print("  graph EG {")
    print("    // Sheet-level vertex")
    print("    vertex_x [...]")
    print("    ")
    print("    // Outer cut cluster")
    print("    subgraph cluster_outer {")
    print("      // Inner cut cluster (NESTED INSIDE outer)")
    print("      subgraph cluster_inner {")
    print("        // Predicate inside inner cut")
    print("        predicate_mortal [...]")
    print("      }")
    print("    }")
    print("  }")
    print()
    print("This structure should make Graphviz automatically:")
    print("1. Size inner cluster to fit predicate + margin")
    print("2. Size outer cluster to fit inner cluster + margin")
    print("3. Position clusters non-overlapping")

if __name__ == "__main__":
    print("Arisbe Cut Hierarchy Debugger")
    print("Investigating nested cut structure for Graphviz...")
    print()
    
    # Debug hierarchy
    success = debug_cut_hierarchy()
    
    if success:
        # Analyze expected vs actual
        analyze_expected_vs_actual()
    else:
        print("\n❌ Could not debug hierarchy due to errors")
