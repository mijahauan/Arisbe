#!/usr/bin/env python3
"""
Debug Layout Spacing Issues

This script investigates why the improved spacing parameters aren't working
and implements more aggressive fixes for the remaining layout problems.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_layout_spacing():
    """Debug why spacing improvements aren't working effectively."""
    
    print("🔧 Debugging Layout Spacing Issues")
    print("=" * 40)
    print("Investigating why improved parameters aren't fixing spacing...")
    print()
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        # Test the most problematic case
        problematic_egif = '*x ~[ ~[ (Mortal x) ] ]'  # Nested cuts that overlap
        
        print(f"🧪 Testing problematic case: {problematic_egif}")
        
        # Parse and analyze
        graph = parse_egif(problematic_egif)
        layout_engine = GraphvizLayoutEngine()
        
        # Generate DOT to see actual parameters
        dot_content = layout_engine._generate_dot_from_egi(graph)
        
        print("📄 Generated DOT parameters:")
        lines = dot_content.split('\n')
        for line in lines[:20]:  # Show first 20 lines with parameters
            if any(param in line.lower() for param in ['nodesep', 'ranksep', 'margin', 'pad', 'sep']):
                print(f"   {line.strip()}")
        
        print()
        
        # Create layout and examine results
        layout_result = layout_engine.create_layout_from_graph(graph)
        
        print("📊 Layout Analysis:")
        print(f"   Total elements: {len(layout_result.primitives)}")
        
        # Analyze spacing between elements
        cuts = [(k, v) for k, v in layout_result.primitives.items() if v.element_type == 'cut']
        predicates = [(k, v) for k, v in layout_result.primitives.items() if v.element_type == 'predicate']
        vertices = [(k, v) for k, v in layout_result.primitives.items() if v.element_type == 'vertex']
        
        print(f"   Cuts: {len(cuts)}")
        for cut_id, cut in cuts:
            print(f"     {cut_id[:8]}: bounds={cut.bounds}")
        
        print(f"   Predicates: {len(predicates)}")
        for pred_id, pred in predicates:
            print(f"     {pred_id[:8]}: bounds={pred.bounds}")
        
        print(f"   Vertices: {len(vertices)}")
        for vert_id, vert in vertices:
            print(f"     {vert_id[:8]}: bounds={vert.bounds}")
        
        # Check actual distances
        if len(cuts) >= 2:
            cut1_bounds = cuts[0][1].bounds
            cut2_bounds = cuts[1][1].bounds
            
            if cut1_bounds and cut2_bounds:
                # Calculate overlap/distance
                x1_min, y1_min, x1_max, y1_max = cut1_bounds
                x2_min, y2_min, x2_max, y2_max = cut2_bounds
                
                print(f"\n🔍 Cut Spacing Analysis:")
                print(f"   Cut 1: ({x1_min}, {y1_min}) to ({x1_max}, {y1_max})")
                print(f"   Cut 2: ({x2_min}, {y2_min}) to ({x2_max}, {y2_max})")
                
                # Check for overlap
                overlap_x = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
                overlap_y = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
                
                if overlap_x > 0 and overlap_y > 0:
                    print(f"   ❌ OVERLAP: {overlap_x} x {overlap_y}")
                else:
                    gap_x = min(abs(x1_max - x2_min), abs(x2_max - x1_min))
                    gap_y = min(abs(y1_max - y2_min), abs(y2_max - y1_min))
                    print(f"   ✅ GAP: {max(gap_x, gap_y)}")
        
        return layout_result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def propose_aggressive_fixes():
    """Propose more aggressive fixes for the spacing issues."""
    
    print("\n🛠️  Aggressive Spacing Fixes")
    print("-" * 35)
    
    fixes = [
        {
            'issue': 'Elements too close (8.9 distance)',
            'current': 'nodesep=3.0, ranksep=2.5',
            'fix': 'nodesep=10.0, ranksep=8.0 (much more aggressive)',
            'rationale': 'Current values insufficient for visual clarity'
        },
        {
            'issue': 'Cuts overlapping in nested cases',
            'current': 'margin=25.0 cluster padding',
            'fix': 'margin=50.0 + post-processing separation enforcement',
            'rationale': 'Graphviz cluster nesting needs manual adjustment'
        },
        {
            'issue': 'Predicate text near boundaries',
            'current': 'Predicate dimensions 0.12 char width',
            'fix': 'Predicate dimensions 0.20 char width + margin enforcement',
            'rationale': 'Text needs more generous bounding boxes'
        },
        {
            'issue': 'Overall layout too compact',
            'current': 'sep="+25"',
            'fix': 'sep="+50" + minimum distance post-processing',
            'rationale': 'Professional diagrams need generous whitespace'
        }
    ]
    
    for i, fix in enumerate(fixes, 1):
        print(f"{i}. {fix['issue']}")
        print(f"   Current: {fix['current']}")
        print(f"   Fix: {fix['fix']}")
        print(f"   Rationale: {fix['rationale']}")
        print()
    
    return fixes

def implement_aggressive_spacing():
    """Implement much more aggressive spacing parameters."""
    
    print("🚀 Implementing Aggressive Spacing")
    print("-" * 40)
    
    print("Proposed changes to graphviz_layout_engine_v2.py:")
    print("  • nodesep: 3.0 → 10.0 (3.3x increase)")
    print("  • ranksep: 2.5 → 8.0 (3.2x increase)")
    print("  • cut padding: 25.0 → 50.0 (2x increase)")
    print("  • element separation: +25 → +50 (2x increase)")
    print("  • predicate char width: 0.12 → 0.20 (1.7x increase)")
    print()
    print("These changes should provide much more generous spacing")
    print("and prevent the crowding issues identified in the analysis.")

if __name__ == "__main__":
    print("Arisbe Layout Spacing Debugger")
    print("Investigating remaining spacing and overlap issues...")
    print()
    
    # Debug current spacing
    layout_result = debug_layout_spacing()
    
    # Propose fixes
    fixes = propose_aggressive_fixes()
    
    # Implementation guidance
    implement_aggressive_spacing()
    
    print("\n🎯 Next Steps:")
    print("1. Implement much more aggressive spacing parameters")
    print("2. Add post-processing to enforce minimum distances")
    print("3. Test with problematic cases")
    print("4. Regenerate sample visuals")
    print("5. Verify visual improvements")
