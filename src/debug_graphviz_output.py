#!/usr/bin/env python3
"""
Debug script to see what Graphviz actually outputs for clusters.
This will help us understand what cluster information we're missing.
"""

from egif_parser_dau import parse_egif
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
import subprocess
import tempfile
import os


def debug_graphviz_cluster_output():
    """Debug what Graphviz outputs for cluster boundaries."""
    
    print("🔍 Debugging Graphviz Cluster Output")
    
    # Test case with nested cuts
    test_egif = '*x *y (Human x) (Woman y) ~[ (Loves x y) ~[ (Married x y) ] ] ~[ (Happy x) (Happy y) ]'
    print(f"📝 Test EGIF: {test_egif}")
    
    try:
        # Parse to EGI
        graph = parse_egif(test_egif)
        print(f"✅ Parsed EGI: {len(graph.Cut)} cuts, {len(graph._vertex_map)} vertices")
        
        # Create layout engine and generate DOT
        engine = GraphvizLayoutEngine()
        dot_content = engine._generate_dot_from_egi(graph)
        
        print("\n📄 Generated DOT content:")
        print("=" * 50)
        print(dot_content)
        print("=" * 50)
        
        # Execute Graphviz with plain output
        dot_file = os.path.join(tempfile.gettempdir(), "debug_cluster.dot")
        with open(dot_file, 'w') as f:
            f.write(dot_content)
        
        # Try different output formats to see cluster information
        formats = ['plain', 'plain-ext']
        
        for fmt in formats:
            print(f"\n🎯 Graphviz {fmt} output:")
            print("-" * 30)
            
            try:
                cmd = ["dot", f"-T{fmt}", dot_file]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print(result.stdout)
                else:
                    print(f"❌ Error: {result.stderr}")
            except Exception as e:
                print(f"❌ Failed: {e}")
        
        # Clean up
        os.remove(dot_file)
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_graphviz_cluster_output()
