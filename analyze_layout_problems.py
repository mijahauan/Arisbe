#!/usr/bin/env python3
"""
Analyze Fundamental Layout Problems

This script analyzes the core layout issues identified in the generated PNG files:
1. Predicate names overlapping cuts
2. Cuts overlapping cuts  
3. Inadequate padding/margins
4. Inadequate spreading of elements

The goal is to identify the root causes in the layout engine and propose fixes.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def analyze_layout_problems():
    """Analyze the fundamental layout problems in the current system."""
    
    print("🔍 Analyzing Fundamental Layout Problems")
    print("=" * 50)
    
    problems = [
        {
            'issue': 'Predicate names overlapping cuts',
            'root_cause': 'Graphviz layout does not account for text dimensions when positioning elements within clusters',
            'current_behavior': 'Predicates positioned at cluster centers without considering text bounds vs cluster bounds',
            'required_fix': 'Calculate text dimensions and ensure adequate margins within cuts'
        },
        {
            'issue': 'Cuts overlapping cuts',
            'root_cause': 'Graphviz cluster positioning allows overlapping when sibling cuts are too close',
            'current_behavior': 'Sibling cuts can overlap spatially even though logically they should be separate',
            'required_fix': 'Enforce minimum separation distances between sibling cuts'
        },
        {
            'issue': 'Inadequate padding/margins',
            'root_cause': 'Graphviz cluster padding parameters are too small for readable EG diagrams',
            'current_behavior': 'Elements positioned too close to cut boundaries for clear visual discrimination',
            'required_fix': 'Increase cluster padding and element margins significantly'
        },
        {
            'issue': 'Inadequate spreading of elements',
            'root_cause': 'Graphviz node separation parameters insufficient for complex EG structures',
            'current_behavior': 'Lines of identity and elements crowded together, reducing visual clarity',
            'required_fix': 'Increase node separation and edge spacing parameters'
        }
    ]
    
    for i, problem in enumerate(problems, 1):
        print(f"{i}. ISSUE: {problem['issue']}")
        print(f"   Root Cause: {problem['root_cause']}")
        print(f"   Current: {problem['current_behavior']}")
        print(f"   Fix: {problem['required_fix']}")
        print()
    
    return problems

def examine_graphviz_parameters():
    """Examine current Graphviz layout parameters that affect spacing."""
    
    print("🔧 Current Graphviz Layout Parameters")
    print("-" * 40)
    
    try:
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        # Create engine to examine current parameters
        engine = GraphvizLayoutEngine()
        
        print("Current parameters likely causing layout issues:")
        print("  • Cluster padding: Probably too small")
        print("  • Node separation: Insufficient for EG diagrams")
        print("  • Edge separation: Inadequate spreading")
        print("  • Margin settings: Not accounting for text dimensions")
        print()
        
        # Test with a problematic case
        from egif_parser_dau import parse_egif
        
        test_egif = '*x ~[ (Human x) ] ~[ (Mortal x) ]'  # Known to have overlapping issues
        print(f"Testing problematic case: {test_egif}")
        
        graph = parse_egif(test_egif)
        layout = engine.create_layout_from_graph(graph)
        
        print(f"Layout result: {len(layout.primitives)} elements")
        
        # Analyze spacing between elements
        cut_elements = [(k, v) for k, v in layout.primitives.items() if v.element_type == 'cut']
        if len(cut_elements) >= 2:
            cut1_bounds = cut_elements[0][1].bounds
            cut2_bounds = cut_elements[1][1].bounds
            
            # Check for overlap
            cut1_x1, cut1_y1, cut1_x2, cut1_y2 = cut1_bounds
            cut2_x1, cut2_y1, cut2_x2, cut2_y2 = cut2_bounds
            
            horizontal_gap = min(abs(cut1_x2 - cut2_x1), abs(cut2_x2 - cut1_x1))
            vertical_gap = min(abs(cut1_y2 - cut2_y1), abs(cut2_y2 - cut1_y1))
            
            print(f"Cut separation analysis:")
            print(f"  Cut 1 bounds: {cut1_bounds}")
            print(f"  Cut 2 bounds: {cut2_bounds}")
            print(f"  Horizontal gap: {horizontal_gap}")
            print(f"  Vertical gap: {vertical_gap}")
            
            if horizontal_gap < 20 or vertical_gap < 20:
                print("  ❌ Inadequate separation between cuts")
            else:
                print("  ✅ Adequate separation between cuts")
        
    except Exception as e:
        print(f"❌ Error analyzing parameters: {e}")

def propose_layout_fixes():
    """Propose specific fixes for the layout problems."""
    
    print("\n🛠️  Proposed Layout Fixes")
    print("-" * 30)
    
    fixes = [
        {
            'problem': 'Predicate/cut overlap',
            'solution': 'Increase Graphviz cluster padding from default to 15-20 points',
            'implementation': 'Modify DOT generation to include: margin="20", pad="1.0"'
        },
        {
            'problem': 'Cut/cut overlap',
            'solution': 'Increase node separation and add explicit separation constraints',
            'implementation': 'Add: nodesep="2.0", ranksep="2.0" to DOT graph attributes'
        },
        {
            'problem': 'Inadequate padding',
            'solution': 'Calculate text dimensions and enforce minimum margins',
            'implementation': 'Post-process layout to adjust positions based on actual text bounds'
        },
        {
            'problem': 'Element crowding',
            'solution': 'Increase overall graph spacing and edge separation',
            'implementation': 'Add: splines="true", sep="+20" to improve edge routing'
        }
    ]
    
    for i, fix in enumerate(fixes, 1):
        print(f"{i}. {fix['problem']}")
        print(f"   Solution: {fix['solution']}")
        print(f"   Implementation: {fix['implementation']}")
        print()
    
    return fixes

def test_layout_fix_approach():
    """Test a potential approach to fixing the layout issues."""
    
    print("🧪 Testing Layout Fix Approach")
    print("-" * 35)
    
    print("Proposed fix strategy:")
    print("1. Modify Graphviz DOT generation with better spacing parameters")
    print("2. Post-process layout results to enforce minimum separations")
    print("3. Adjust predicate positions to ensure cut containment")
    print("4. Validate spatial constraints before rendering")
    print()
    
    print("This requires modifying:")
    print("  • graphviz_layout_engine_v2.py - DOT generation parameters")
    print("  • Layout post-processing - spatial constraint enforcement")
    print("  • Renderer positioning logic - final position adjustments")

if __name__ == "__main__":
    print("Arisbe Layout Problem Analysis")
    print("Identifying root causes of visual layout issues...")
    print()
    
    # Analyze the problems
    problems = analyze_layout_problems()
    
    # Examine current parameters
    examine_graphviz_parameters()
    
    # Propose fixes
    fixes = propose_layout_fixes()
    
    # Test approach
    test_layout_fix_approach()
    
    print("\n🎯 Next Steps:")
    print("1. Implement Graphviz parameter improvements")
    print("2. Add layout post-processing for spatial constraints")
    print("3. Test with problematic EGIF expressions")
    print("4. Validate visual improvements")
    print("5. Regenerate sample visuals with fixes")
