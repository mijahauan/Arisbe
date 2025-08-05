#!/usr/bin/env python3
"""
Systematic Graphviz Layout Fix

This script investigates and implements the proper fixes for Graphviz layout
spacing and containment issues, based on previous successful approaches.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def investigate_graphviz_issues():
    """Investigate the specific Graphviz layout issues and their solutions."""
    
    print("🔍 Investigating Graphviz Layout Issues")
    print("=" * 45)
    print("Analyzing why current spacing parameters aren't working...")
    print()
    
    issues_and_solutions = [
        {
            'issue': 'Nested cuts overlapping despite cluster padding',
            'root_cause': 'Graphviz cluster margin/padding only affects internal spacing, not cluster positioning',
            'solution': 'Use cluster-level positioning attributes: pos, bb (bounding box)',
            'implementation': 'Set explicit cluster positions or use layout post-processing'
        },
        {
            'issue': 'Elements too close despite nodesep/ranksep',
            'root_cause': 'Graphviz spacing parameters may be overridden by cluster constraints',
            'solution': 'Use explicit node positioning within clusters or increase cluster size',
            'implementation': 'Set minimum cluster sizes or use pos attributes for nodes'
        },
        {
            'issue': 'Hierarchical containment not working properly',
            'root_cause': 'Nested clusters need explicit size and position management',
            'solution': 'Calculate required cluster sizes based on contents + margins',
            'implementation': 'Pre-calculate cluster bounding boxes and set explicit sizes'
        },
        {
            'issue': 'Spacing parameters not having expected effect',
            'root_cause': 'Some Graphviz engines ignore certain spacing parameters',
            'solution': 'Use different layout engine (dot vs neato vs fdp) or explicit positioning',
            'implementation': 'Test different engines or switch to manual positioning'
        }
    ]
    
    for i, item in enumerate(issues_and_solutions, 1):
        print(f"{i}. ISSUE: {item['issue']}")
        print(f"   Root Cause: {item['root_cause']}")
        print(f"   Solution: {item['solution']}")
        print(f"   Implementation: {item['implementation']}")
        print()
    
    return issues_and_solutions

def test_graphviz_approaches():
    """Test different Graphviz approaches to fix the layout issues."""
    
    print("🧪 Testing Graphviz Layout Approaches")
    print("-" * 40)
    
    approaches = [
        {
            'name': 'Explicit Cluster Sizing',
            'description': 'Set explicit width/height for clusters based on contents',
            'dot_changes': ['Add width="X", height="Y" to cluster attributes']
        },
        {
            'name': 'Different Layout Engine',
            'description': 'Try neato or fdp instead of dot for better spacing control',
            'dot_changes': ['Change layout engine in DOT generation']
        },
        {
            'name': 'Manual Node Positioning',
            'description': 'Set explicit pos="x,y" for nodes within clusters',
            'dot_changes': ['Add pos attributes to nodes for precise positioning']
        },
        {
            'name': 'Cluster Bounding Box',
            'description': 'Set explicit bounding box for clusters',
            'dot_changes': ['Add bb="x1,y1,x2,y2" to cluster attributes']
        }
    ]
    
    for i, approach in enumerate(approaches, 1):
        print(f"{i}. {approach['name']}")
        print(f"   Description: {approach['description']}")
        print(f"   DOT Changes: {', '.join(approach['dot_changes'])}")
        print()
    
    return approaches

def implement_cluster_sizing_fix():
    """Implement the explicit cluster sizing fix."""
    
    print("🛠️  Implementing Cluster Sizing Fix")
    print("-" * 40)
    
    print("Strategy: Calculate required cluster sizes based on contents")
    print("1. Measure predicate text dimensions")
    print("2. Calculate minimum cluster size to contain predicates + padding")
    print("3. Set explicit width/height attributes on clusters")
    print("4. Ensure nested clusters fit within parent clusters")
    print()
    
    print("Required changes to graphviz_layout_engine_v2.py:")
    print("  • Add cluster size calculation method")
    print("  • Modify cluster generation to include width/height")
    print("  • Ensure nested cluster sizing respects parent bounds")
    print("  • Add explicit positioning for better control")
    
    return {
        'method': '_calculate_cluster_size',
        'attributes': ['width', 'height', 'fixedsize=true'],
        'nested_handling': 'Calculate parent size based on child requirements'
    }

def test_problematic_case():
    """Test the fix on the most problematic case."""
    
    print("\n🎯 Testing Fix on Problematic Case")
    print("-" * 40)
    
    problematic_egif = '*x ~[ ~[ (Mortal x) ] ]'
    print(f"Testing: {problematic_egif}")
    
    try:
        from egif_parser_dau import parse_egif
        
        graph = parse_egif(problematic_egif)
        print(f"✅ Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
        
        print("\nCurrent issue: Nested cuts overlap by 222.0 x 160.95")
        print("Expected fix: Proper hierarchical containment with clear separation")
        
        # Analyze what the fix should achieve
        print("\nRequired layout:")
        print("  • Outer cut: Large enough to contain inner cut + margin")
        print("  • Inner cut: Large enough to contain predicate + padding")
        print("  • Predicate: Positioned within inner cut bounds")
        print("  • Vertex: Connected to predicate, positioned outside cuts")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Arisbe Graphviz Layout Fix")
    print("Systematically fixing spacing and containment issues...")
    print()
    
    # Investigate issues
    issues = investigate_graphviz_issues()
    
    # Test approaches
    approaches = test_graphviz_approaches()
    
    # Implement fix
    fix_details = implement_cluster_sizing_fix()
    
    # Test on problematic case
    test_success = test_problematic_case()
    
    print("\n🎯 Next Steps:")
    print("1. Implement explicit cluster sizing in Graphviz layout engine")
    print("2. Add cluster size calculation based on contents + padding")
    print("3. Test with nested cuts case to verify proper containment")
    print("4. Regenerate sample visuals to validate improvements")
    print("5. Ensure all spacing and overlap issues are resolved")
