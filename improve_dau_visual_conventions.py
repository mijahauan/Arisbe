#!/usr/bin/env python3
"""
Improve Dau Visual Conventions

Focus on graphical/visual polish to ensure full compliance with Dau's
formalization of Peircean conventions. Structural EGI consistency is already
validated and working.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def analyze_visual_convention_improvements():
    """Analyze specific visual improvements needed for Dau conventions."""
    
    print("🎨 Analyzing Visual Convention Improvements")
    print("=" * 50)
    
    print("✅ STRUCTURAL FOUNDATION (Already Working):")
    print("   • Cut containment - elements properly contained in cuts")
    print("   • Nested cuts - hierarchical containment working")
    print("   • Sibling cuts - spatially separated")
    print("   • Element positioning - matches logical EGI areas")
    print("   • Identity line consistency - maintained")
    print()
    
    print("🎯 VISUAL IMPROVEMENTS NEEDED:")
    
    # 1. Line Weight and Style Distinctions
    print("\n1. LINE WEIGHT AND STYLE DISTINCTIONS:")
    print("   Issue: Lines of identity should be visually distinct from cut boundaries")
    print("   Dau Convention: Lines of identity = heavy/bold, Cuts = fine-drawn")
    print("   Current Status: Need to ensure clear visual distinction")
    print("   Priority: HIGH - Core Peircean convention")
    
    # 2. Predicate-Line Connection Points
    print("\n2. PREDICATE-LINE CONNECTION POINTS:")
    print("   Issue: Predicates should attach to line ends via clear 'hooks'")
    print("   Dau Convention: Predicates connect at line endpoints, not midpoints")
    print("   Current Status: Need to verify connection points are at line ends")
    print("   Priority: HIGH - Essential for n-ary predicate clarity")
    
    # 3. Cut Boundary Clarity
    print("\n3. CUT BOUNDARY CLARITY:")
    print("   Issue: Cut boundaries should be clearly closed curves")
    print("   Dau Convention: Fine-drawn, closed, double-point-free curves")
    print("   Current Status: Need to ensure oval/circular rendering is clean")
    print("   Priority: MEDIUM - Visual clarity")
    
    # 4. Spacing and Margins
    print("\n4. SPACING AND MARGINS:")
    print("   Issue: Adequate spacing between elements for readability")
    print("   Dau Convention: No overlap, clear visual separation")
    print("   Current Status: Need to optimize spacing parameters")
    print("   Priority: MEDIUM - Professional appearance")
    
    # 5. Identity Line Branching
    print("\n5. IDENTITY LINE BRANCHING:")
    print("   Issue: Single identity should branch to multiple predicates")
    print("   Dau Convention: Lines can branch at any point")
    print("   Current Status: Need to implement proper branching visualization")
    print("   Priority: MEDIUM - Complex identity relationships")
    
    # 6. Vertex Spot Visibility
    print("\n6. VERTEX SPOT VISIBILITY:")
    print("   Issue: Identity spots should be clearly visible")
    print("   Dau Convention: Vertices as visible 'identity spots'")
    print("   Current Status: Need to ensure vertex rendering is prominent")
    print("   Priority: LOW - Already working but could be enhanced")

def create_visual_improvement_implementation():
    """Create implementation plan for visual improvements."""
    
    print("\n🔧 IMPLEMENTATION PLAN:")
    print("=" * 30)
    
    print("\nPhase 1: Line Weight and Style (HIGH PRIORITY)")
    print("   • Update renderer to use distinct line weights")
    print("   • Lines of identity: bold/heavy (penwidth=3)")
    print("   • Cut boundaries: fine (penwidth=1)")
    print("   • Ensure consistent styling across all backends")
    
    print("\nPhase 2: Connection Point Accuracy (HIGH PRIORITY)")
    print("   • Verify predicate attachment points are at line ends")
    print("   • Implement proper 'hook' visualization")
    print("   • Ensure n-ary predicates have numbered connection points")
    
    print("\nPhase 3: Spacing Optimization (MEDIUM PRIORITY)")
    print("   • Optimize Graphviz spacing parameters")
    print("   • Increase margins around predicates and cuts")
    print("   • Ensure no visual overlap between elements")
    
    print("\nPhase 4: Advanced Features (LOWER PRIORITY)")
    print("   • Implement identity line branching")
    print("   • Enhance vertex spot visibility")
    print("   • Add visual polish and refinements")

def test_specific_visual_improvements():
    """Test specific visual improvements against key cases."""
    
    print("\n🧪 TESTING VISUAL IMPROVEMENTS:")
    print("=" * 35)
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        # Focus on the most critical visual test cases
        critical_cases = [
            ("Line Weight Test", '*x (Human x)', "Heavy identity line vs fine elements"),
            ("Connection Test", '*x (Human x) (Mortal x)', "Predicates at line ends"),
            ("Cut Clarity Test", '~[ (Human "Socrates") ]', "Fine-drawn cut boundary"),
            ("Spacing Test", '*x ~[ (P x) ] ~[ (Q x) ]', "Adequate spacing between cuts"),
        ]
        
        layout_engine = GraphvizLayoutEngine()
        
        for test_name, egif, focus in critical_cases:
            print(f"\n   {test_name}: {egif}")
            print(f"   Focus: {focus}")
            
            try:
                graph = parse_egif(egif)
                layout_result = layout_engine.create_layout_from_graph(graph)
                
                # Analyze layout for visual improvements
                analyze_layout_for_visual_issues(layout_result, focus)
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def analyze_layout_for_visual_issues(layout_result, focus):
    """Analyze a specific layout for visual improvement opportunities."""
    
    print(f"      Elements: {len(layout_result.primitives)}")
    
    # Check for line weight distinctions
    line_elements = [p for p in layout_result.primitives.values() 
                    if p.element_type in ['vertex', 'edge']]
    cut_elements = [p for p in layout_result.primitives.values() 
                   if p.element_type == 'cut']
    
    if line_elements and cut_elements:
        print(f"      ✅ Has both line elements ({len(line_elements)}) and cuts ({len(cut_elements)})")
        print(f"      🎯 Need distinct visual styling between them")
    
    # Check spacing
    if len(layout_result.primitives) >= 2:
        primitives = list(layout_result.primitives.values())
        min_distance = float('inf')
        
        for i, p1 in enumerate(primitives):
            for j, p2 in enumerate(primitives):
                if i < j:
                    # Calculate distance between centers
                    dx = p1.position[0] - p2.position[0]
                    dy = p1.position[1] - p2.position[1]
                    distance = (dx*dx + dy*dy)**0.5
                    min_distance = min(min_distance, distance)
        
        print(f"      📏 Minimum element distance: {min_distance:.1f}")
        if min_distance < 50:
            print(f"      ⚠️  Elements may be too close for optimal readability")
        else:
            print(f"      ✅ Element spacing appears adequate")

if __name__ == "__main__":
    print("Arisbe Visual Convention Improvement Analysis")
    print("Focusing on graphical polish for Dau/Peircean conventions...")
    print()
    
    # Analyze what visual improvements are needed
    analyze_visual_convention_improvements()
    
    # Create implementation plan
    create_visual_improvement_implementation()
    
    # Test current state against critical visual cases
    test_specific_visual_improvements()
    
    print(f"\n🎯 NEXT STEPS:")
    print("=" * 15)
    print("1. Implement line weight distinctions (heavy identity lines, fine cuts)")
    print("2. Verify predicate connection points are at line ends")
    print("3. Optimize spacing parameters for better visual clarity")
    print("4. Test visual improvements against all Dau convention cases")
    print()
    print("✅ Structural EGI consistency is solid - focus on visual polish!")
