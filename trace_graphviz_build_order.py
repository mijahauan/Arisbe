#!/usr/bin/env python3
"""
Trace Graphviz Build Order

This script traces whether Graphviz is building from components up,
which should guarantee proper relative sizes for EG diagrams.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def trace_graphviz_build_order():
    """Trace the order in which Graphviz builds DOT components."""
    
    print("🔍 Tracing Graphviz Build Order")
    print("=" * 35)
    print("Examining whether DOT generation builds from components up...")
    print()
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        # Test with nested cuts case
        test_egif = '*x ~[ ~[ (Mortal x) ] ]'
        print(f"Testing: {test_egif}")
        
        graph = parse_egif(test_egif)
        layout_engine = GraphvizLayoutEngine()
        
        # Generate DOT and trace the build order
        dot_content = layout_engine._generate_dot_from_egi(graph)
        
        print("\n📋 DOT Generation Order Analysis:")
        print("-" * 40)
        
        lines = dot_content.split('\n')
        
        # Trace the order of component generation
        component_order = []
        in_cluster = False
        cluster_depth = 0
        
        for i, line in enumerate(lines, 1):
            line_clean = line.strip()
            
            if 'subgraph cluster_' in line_clean:
                cluster_depth += 1
                component_order.append(f"Line {i}: START CLUSTER (depth {cluster_depth}) - {line_clean}")
                in_cluster = True
            elif line_clean == '}' and in_cluster:
                component_order.append(f"Line {i}: END CLUSTER (depth {cluster_depth}) - {line_clean}")
                cluster_depth -= 1
                if cluster_depth == 0:
                    in_cluster = False
            elif '[label=' in line_clean and 'shape=box' in line_clean:
                component_order.append(f"Line {i}: PREDICATE - {line_clean}")
            elif '[label=' in line_clean and 'shape=circle' in line_clean:
                component_order.append(f"Line {i}: VERTEX - {line_clean}")
            elif '--' in line_clean and '[' in line_clean:
                component_order.append(f"Line {i}: EDGE - {line_clean}")
        
        print("Component generation order:")
        for order_item in component_order:
            print(f"  {order_item}")
        
        print("\n🔍 Build Order Analysis:")
        print("-" * 25)
        
        # Check if it's building from inside out (components first, then containers)
        predicate_lines = [i for i, item in enumerate(component_order) if 'PREDICATE' in item]
        cluster_start_lines = [i for i, item in enumerate(component_order) if 'START CLUSTER' in item]
        cluster_end_lines = [i for i, item in enumerate(component_order) if 'END CLUSTER' in item]
        
        if predicate_lines and cluster_start_lines:
            if min(predicate_lines) > min(cluster_start_lines):
                print("✅ CORRECT: Clusters defined first, then contents added inside")
                print("   This should allow Graphviz to size clusters based on contents")
            else:
                print("❌ ISSUE: Contents defined before clusters")
                print("   This could cause sizing problems")
        
        # Check nesting order
        if len(cluster_start_lines) >= 2:
            print(f"\n🏗️  Cluster Nesting Order:")
            print(f"   Outer cluster starts at position {cluster_start_lines[0]}")
            print(f"   Inner cluster starts at position {cluster_start_lines[1]}")
            if cluster_start_lines[1] > cluster_start_lines[0]:
                print("   ✅ Correct nesting: Outer cluster first, then inner cluster")
            else:
                print("   ❌ Incorrect nesting order")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_cluster_sizing_approach():
    """Analyze how Graphviz should handle cluster sizing."""
    
    print("\n📐 Cluster Sizing Analysis")
    print("-" * 30)
    
    print("Expected Graphviz behavior for proper component-up building:")
    print("1. Define cluster boundaries")
    print("2. Add contents (predicates, vertices) inside clusters")
    print("3. Graphviz automatically sizes clusters to fit contents + margin")
    print("4. Position clusters to avoid overlaps")
    print()
    
    print("Current issues suggest:")
    print("• Clusters may not be auto-sizing based on contents")
    print("• Manual cluster sizing might be needed")
    print("• Margin/padding parameters might not be working as expected")
    print()
    
    print("Potential fixes:")
    print("1. Ensure contents are properly assigned to clusters")
    print("2. Add explicit cluster sizing based on content dimensions")
    print("3. Verify margin/padding parameters are being applied")
    print("4. Check if cluster positioning respects spacing parameters")

if __name__ == "__main__":
    print("Arisbe Graphviz Build Order Tracer")
    print("Investigating component-up building for proper sizing...")
    print()
    
    # Trace build order
    success = trace_graphviz_build_order()
    
    if success:
        # Analyze sizing approach
        analyze_cluster_sizing_approach()
        
        print("\n🎯 Key Question:")
        print("Is Graphviz actually auto-sizing clusters based on their contents,")
        print("or do we need to explicitly calculate and set cluster dimensions?")
    else:
        print("\n❌ Could not trace build order due to errors")
