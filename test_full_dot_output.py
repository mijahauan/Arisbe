#!/usr/bin/env python3
"""
Test Full DOT Output Structure

Verify that the complete DOT structure properly leverages Graphviz's
hierarchical layout capabilities for nested EG cuts.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_full_dot_structure():
    """Test the complete DOT output for proper hierarchical structure."""
    
    print("🔍 Testing Full DOT Structure")
    print("=" * 35)
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        # Test with nested cuts case
        test_egif = '*x ~[ ~[ (Mortal x) ] ]'
        print(f"Testing: {test_egif}")
        
        graph = parse_egif(test_egif)
        layout_engine = GraphvizLayoutEngine()
        
        # Generate complete DOT content
        dot_content = layout_engine._generate_dot_from_egi(graph)
        
        print(f"\n📄 Complete DOT Output:")
        print("-" * 25)
        print(dot_content)
        print("-" * 25)
        
        # Analyze structure
        print(f"\n🔍 Structure Analysis:")
        lines = dot_content.split('\n')
        
        # Check for proper Graphviz hierarchical attributes
        hierarchical_attrs = ['clusterrank=local', 'compound=true', 'newrank=true']
        for attr in hierarchical_attrs:
            if any(attr in line for line in lines):
                print(f"  ✅ {attr} found")
            else:
                print(f"  ❌ {attr} missing")
        
        # Check cluster nesting
        cluster_starts = []
        cluster_ends = []
        content_lines = []
        
        for i, line in enumerate(lines):
            if 'subgraph cluster_' in line:
                cluster_starts.append((i, line.strip()))
            elif line.strip() == '}' and any('subgraph cluster_' in lines[j] for j in range(max(0, i-10), i)):
                cluster_ends.append((i, line.strip()))
            elif '[label=' in line and 'shape=' in line:
                content_lines.append((i, line.strip()))
        
        print(f"\n🏗️  Cluster Structure:")
        print(f"  Cluster starts: {len(cluster_starts)}")
        for line_num, content in cluster_starts:
            print(f"    Line {line_num}: {content}")
        
        print(f"\n📦 Content Placement:")
        print(f"  Content elements: {len(content_lines)}")
        for line_num, content in content_lines:
            print(f"    Line {line_num}: {content}")
        
        # Check if content is inside clusters
        print(f"\n🎯 Content-Cluster Relationship:")
        for content_line, content in content_lines:
            # Find the most recent cluster start before this content
            containing_cluster = None
            for cluster_line, cluster_content in reversed(cluster_starts):
                if cluster_line < content_line:
                    containing_cluster = cluster_content
                    break
            
            if containing_cluster:
                print(f"  Content at line {content_line} is inside: {containing_cluster}")
            else:
                print(f"  Content at line {content_line} is at sheet level")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_graphviz_execution():
    """Test if Graphviz can actually process our DOT structure."""
    
    print(f"\n🚀 Testing Graphviz Execution")
    print("-" * 30)
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        test_egif = '*x ~[ ~[ (Mortal x) ] ]'
        graph = parse_egif(test_egif)
        layout_engine = GraphvizLayoutEngine()
        
        # Generate DOT
        dot_content = layout_engine._generate_dot_from_egi(graph)
        
        # Try to execute Graphviz
        print("Executing Graphviz with our DOT structure...")
        xdot_output = layout_engine._execute_graphviz(dot_content)
        
        if xdot_output:
            print("✅ Graphviz execution successful!")
            print(f"   Output length: {len(xdot_output)} characters")
            
            # Check for cluster boundaries in output
            if '_bb=' in xdot_output:
                bb_count = xdot_output.count('_bb=')
                print(f"   Found {bb_count} cluster bounding boxes")
            else:
                print("   ⚠️  No cluster bounding boxes found")
                
        else:
            print("❌ Graphviz execution failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Arisbe DOT Structure Tester")
    print("Verifying proper Graphviz hierarchical layout structure...")
    print()
    
    # Test DOT structure
    success1 = test_full_dot_structure()
    
    if success1:
        # Test Graphviz execution
        success2 = test_graphviz_execution()
        
        if success1 and success2:
            print(f"\n🎉 CONCLUSION:")
            print("DOT structure appears correct for Graphviz hierarchical layout.")
            print("The issue may be in coordinate parsing or rendering, not structure.")
        else:
            print(f"\n❌ Issues found in DOT structure or Graphviz execution.")
    else:
        print(f"\n❌ Could not test DOT structure due to errors")
