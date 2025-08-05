#!/usr/bin/env python3
"""
Solidify Graphviz Modeling and Output

Comprehensive analysis and validation of Graphviz DOT generation,
cluster hierarchy, and coordinate extraction for EG diagrams.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def analyze_dot_cluster_hierarchy():
    """Analyze DOT cluster hierarchy generation for nested cuts."""
    
    print("🔍 Analyzing DOT Cluster Hierarchy")
    print("=" * 40)
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        # Test cases for different nesting scenarios
        test_cases = [
            ("Simple nested", '*x ~[ ~[ (Mortal x) ] ]'),
            ("Sibling cuts", '*x ~[ (P x) ] ~[ (Q x) ]'),
            ("Triple nested", '*x ~[ ~[ ~[ (Deep x) ] ] ]'),
            ("Mixed sheet/cut", '(Human "Socrates") ~[ (Mortal "Socrates") ]'),
        ]
        
        layout_engine = GraphvizLayoutEngine()
        
        for test_name, egif in test_cases:
            print(f"\n📋 Test Case: {test_name}")
            print(f"   EGIF: {egif}")
            
            graph = parse_egif(egif)
            
            # Analyze EGI structure
            print(f"   EGI Structure:")
            print(f"     Sheet: {graph.sheet}")
            print(f"     Cuts: {[cut.id[:8] for cut in graph.Cut]}")
            print(f"     Areas: {[(area_id[:8], len(contents)) for area_id, contents in graph.area.items()]}")
            
            # Generate DOT and analyze structure
            dot_content = layout_engine._generate_dot_from_egi(graph)
            
            # Extract cluster nesting structure
            lines = dot_content.split('\n')
            cluster_structure = []
            indent_level = 0
            
            for line in lines:
                stripped = line.strip()
                if 'subgraph cluster_' in stripped:
                    cluster_structure.append(f"{'  ' * indent_level}{stripped}")
                    indent_level += 1
                elif stripped == '}' and indent_level > 0:
                    indent_level -= 1
                    cluster_structure.append(f"{'  ' * indent_level}{stripped}")
                elif '[label=' in stripped and ('shape=box' in stripped or 'shape=circle' in stripped):
                    cluster_structure.append(f"{'  ' * indent_level}CONTENT: {stripped}")
            
            print(f"   DOT Cluster Structure:")
            for structure_line in cluster_structure:
                print(f"     {structure_line}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_graphviz_cluster_containment():
    """Test if Graphviz actually produces proper cluster containment."""
    
    print(f"\n🎯 Testing Graphviz Cluster Containment")
    print("-" * 45)
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        # Focus on the problematic nested case
        test_egif = '*x ~[ ~[ (Mortal x) ] ]'
        print(f"Testing: {test_egif}")
        
        graph = parse_egif(test_egif)
        layout_engine = GraphvizLayoutEngine()
        
        # Generate layout and extract coordinates
        layout_result = layout_engine.create_layout_from_graph(graph)
        
        print(f"\n📊 Coordinate Analysis:")
        cuts = [(elem_id, primitive) for elem_id, primitive in layout_result.primitives.items() 
                if primitive.element_type == 'cut']
        
        if len(cuts) >= 2:
            # Sort cuts by area (smaller area = inner cut)
            cuts.sort(key=lambda x: (x[1].bounds[2] - x[1].bounds[0]) * (x[1].bounds[3] - x[1].bounds[1]))
            
            inner_cut_id, inner_cut = cuts[0]
            outer_cut_id, outer_cut = cuts[1]
            
            print(f"   Inner cut {inner_cut_id[:8]}: bounds={inner_cut.bounds}")
            print(f"   Outer cut {outer_cut_id[:8]}: bounds={outer_cut.bounds}")
            
            # Check if inner cut is properly contained within outer cut
            inner_x1, inner_y1, inner_x2, inner_y2 = inner_cut.bounds
            outer_x1, outer_y1, outer_x2, outer_y2 = outer_cut.bounds
            
            properly_contained = (
                outer_x1 < inner_x1 and
                outer_y1 < inner_y1 and
                outer_x2 > inner_x2 and
                outer_y2 > inner_y2
            )
            
            if properly_contained:
                print(f"   ✅ PROPER CONTAINMENT: Inner cut is fully within outer cut")
            else:
                print(f"   ❌ IMPROPER CONTAINMENT: Cuts are overlapping or misaligned")
                
                # Calculate overlap
                overlap_x = max(0, min(inner_x2, outer_x2) - max(inner_x1, outer_x1))
                overlap_y = max(0, min(inner_y2, outer_y2) - max(inner_y1, outer_y1))
                print(f"      Overlap area: {overlap_x} x {overlap_y}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_graphviz_attributes():
    """Analyze which Graphviz attributes affect cluster containment."""
    
    print(f"\n🔧 Analyzing Graphviz Attributes for Cluster Containment")
    print("-" * 55)
    
    print("Current Graphviz attributes in use:")
    print("  • clusterrank=local    - Layout each cluster separately then integrate")
    print("  • compound=true        - Allow edges between clusters")
    print("  • newrank=true         - Use improved ranking algorithm")
    print("  • rankdir=TB           - Top-to-bottom layout")
    print("  • overlap=false        - Prevent node overlaps")
    print("  • margin=50.0          - Cluster padding")
    print()
    
    print("Potential issues and solutions:")
    print("1. CLUSTER POSITIONING:")
    print("   Issue: Graphviz may position nested clusters as siblings")
    print("   Solution: Ensure DOT structure has true nesting, not just naming")
    print()
    print("2. CLUSTER SIZING:")
    print("   Issue: Parent clusters may not auto-size to contain children")
    print("   Solution: Use 'packmode' or explicit size constraints")
    print()
    print("3. LAYOUT ALGORITHM:")
    print("   Issue: 'dot' engine may not handle nested clusters optimally")
    print("   Solution: Test 'neato', 'fdp', or 'osage' engines")
    print()
    print("4. CLUSTER ATTRIBUTES:")
    print("   Issue: Missing attributes for proper containment")
    print("   Solution: Add 'pack=true', 'packmode=clust', or 'mode=hier'")

def test_alternative_graphviz_engines():
    """Test different Graphviz layout engines for cluster containment."""
    
    print(f"\n🚀 Testing Alternative Graphviz Engines")
    print("-" * 40)
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        test_egif = '*x ~[ ~[ (Mortal x) ] ]'
        graph = parse_egif(test_egif)
        
        # Test different engines
        engines = ['dot', 'neato', 'fdp', 'osage']
        
        for engine in engines:
            print(f"\n🔍 Testing {engine} engine:")
            
            layout_engine = GraphvizLayoutEngine()
            # Temporarily modify the engine (would need to add this capability)
            print(f"   Engine: {engine}")
            print(f"   Status: Would need to modify GraphvizLayoutEngine to test different engines")
            print(f"   Expected: Different cluster positioning behavior")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def generate_dot_validation_report():
    """Generate a comprehensive validation report for DOT generation."""
    
    print(f"\n📋 DOT Generation Validation Report")
    print("=" * 40)
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        test_egif = '*x ~[ ~[ (Mortal x) ] ]'
        graph = parse_egif(test_egif)
        layout_engine = GraphvizLayoutEngine()
        
        dot_content = layout_engine._generate_dot_from_egi(graph)
        
        print("✅ DOT Generation Checklist:")
        
        # Check hierarchical attributes
        hierarchical_attrs = [
            ('clusterrank=local', 'Cluster-local ranking'),
            ('compound=true', 'Inter-cluster edges'),
            ('newrank=true', 'Improved ranking'),
            ('rankdir=TB', 'Top-bottom layout'),
        ]
        
        for attr, description in hierarchical_attrs:
            if attr in dot_content:
                print(f"   ✅ {attr:<20} - {description}")
            else:
                print(f"   ❌ {attr:<20} - {description} (MISSING)")
        
        # Check cluster nesting
        cluster_count = dot_content.count('subgraph cluster_')
        cluster_end_count = dot_content.count('}')
        
        print(f"\n📊 Cluster Structure:")
        print(f"   Cluster declarations: {cluster_count}")
        print(f"   Closing braces: {cluster_end_count}")
        
        # Check content placement
        content_in_clusters = 0
        lines = dot_content.split('\n')
        in_cluster = False
        
        for line in lines:
            if 'subgraph cluster_' in line:
                in_cluster = True
            elif line.strip() == '}' and in_cluster:
                in_cluster = False
            elif in_cluster and '[label=' in line and 'shape=' in line:
                content_in_clusters += 1
        
        print(f"   Content elements in clusters: {content_in_clusters}")
        
        print(f"\n📄 Complete DOT Content:")
        print("-" * 25)
        print(dot_content)
        print("-" * 25)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Arisbe Graphviz Modeling Solidification")
    print("Comprehensive analysis of DOT generation and cluster hierarchy...")
    print()
    
    # Run all analyses
    success1 = analyze_dot_cluster_hierarchy()
    
    if success1:
        success2 = test_graphviz_cluster_containment()
        
        if success2:
            analyze_graphviz_attributes()
            test_alternative_graphviz_engines()
            success3 = generate_dot_validation_report()
            
            if success1 and success2 and success3:
                print(f"\n🎉 GRAPHVIZ MODELING ANALYSIS COMPLETE")
                print("=" * 45)
                print("Key findings will guide solidification of Graphviz output.")
            else:
                print(f"\n❌ Some analyses failed - review errors above")
        else:
            print(f"\n❌ Cluster containment test failed")
    else:
        print(f"\n❌ DOT hierarchy analysis failed")
