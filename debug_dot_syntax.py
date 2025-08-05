#!/usr/bin/env python3
"""
Debug DOT Syntax Error

This script debugs the DOT syntax error that's causing Graphviz to fail
with "syntax error in line X near '--'" for non-cut EGIF cases.

The error suggests there's an issue with edge syntax generation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_dot_syntax():
    """Debug the DOT syntax error by examining generated DOT content."""
    
    print("🐛 Debugging DOT Syntax Error")
    print("=" * 40)
    print("Investigating 'syntax error near --' in Graphviz DOT generation...")
    print()
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        # Test cases that are failing with DOT syntax errors
        failing_cases = [
            '(Human "Socrates")',  # Simple constant
            '*x (Human x)',        # Variable predicate  
            '*x *y (Loves x y)',   # Binary relation
        ]
        
        layout_engine = GraphvizLayoutEngine()
        
        for i, egif in enumerate(failing_cases, 1):
            print(f"{i}. Testing EGIF: {egif}")
            
            try:
                # Parse EGIF to EGI
                graph = parse_egif(egif)
                print(f"   ✅ Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
                
                # Generate DOT content (this is where the error occurs)
                dot_content = layout_engine._generate_dot_from_egi(graph)
                
                print(f"   ✅ DOT generation successful")
                print(f"   📄 DOT content ({len(dot_content)} chars):")
                print("   " + "-" * 50)
                
                # Print DOT content with line numbers for debugging
                lines = dot_content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    print(f"   {line_num:2d}: {line}")
                
                print("   " + "-" * 50)
                
                # Save DOT file for manual inspection
                dot_filename = f"debug_dot_{i}.dot"
                with open(dot_filename, 'w') as f:
                    f.write(dot_content)
                print(f"   💾 Saved DOT file: {dot_filename}")
                
            except Exception as e:
                print(f"   ❌ Error generating DOT: {e}")
                import traceback
                traceback.print_exc()
            
            print()
        
        print("🔍 DOT Syntax Analysis")
        print("-" * 25)
        print("Look for these common DOT syntax issues:")
        print("  • Invalid edge syntax (should be 'node1 -> node2' or 'node1 -- node2')")
        print("  • Missing semicolons")
        print("  • Invalid node/edge identifiers")
        print("  • Incorrect attribute syntax")
        print("  • Mixed directed/undirected graph syntax")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")

def test_minimal_dot():
    """Test with a minimal DOT file to isolate the syntax issue."""
    
    print("\n🧪 Testing Minimal DOT Syntax")
    print("-" * 35)
    
    # Create a minimal DOT file that should work
    minimal_dot = """digraph test {
    rankdir=TB;
    node [shape=circle];
    edge [arrowhead=none];
    
    v1 [label="x"];
    p1 [label="Human", shape=box];
    
    v1 -> p1;
}"""
    
    print("Testing minimal DOT syntax:")
    print(minimal_dot)
    
    # Save and test
    with open("minimal_test.dot", 'w') as f:
        f.write(minimal_dot)
    
    print("💾 Saved minimal_test.dot")
    print("You can test this manually with: dot -Tpng minimal_test.dot -o minimal_test.png")

if __name__ == "__main__":
    print("Arisbe DOT Syntax Debugger")
    print("Investigating Graphviz syntax errors...")
    print()
    
    # Debug the DOT syntax
    debug_dot_syntax()
    
    # Test minimal DOT
    test_minimal_dot()
    
    print("\n🎯 Next Steps:")
    print("1. Examine generated DOT files for syntax issues")
    print("2. Look for invalid edge syntax around line numbers mentioned in errors")
    print("3. Fix DOT generation method to produce valid syntax")
    print("4. Test with manual Graphviz execution")
