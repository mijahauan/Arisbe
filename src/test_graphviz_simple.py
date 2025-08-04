#!/usr/bin/env python3
"""
Simple Graphviz test to demonstrate hierarchical layout for EG cuts.
This creates the exact structure we need: ~[ ~[ (P "x") ] ~[ (Q "x") ] ]
"""

import graphviz

def create_test_dot():
    """Create a DOT graph showing the overlapping cuts problem and solution."""
    
    # Create the graph
    dot = graphviz.Digraph(comment='EG Hierarchical Layout Test')
    dot.attr(rankdir='TB', splines='true', overlap='false')
    
    # Outer cut containing two sibling inner cuts
    with dot.subgraph(name='cluster_outer') as outer:
        outer.attr(style='rounded', color='blue', label='Outer Cut', margin='20')
        
        # First inner cut: ~[ (P "x") ]
        with outer.subgraph(name='cluster_inner1') as inner1:
            inner1.attr(style='rounded', color='red', label='Inner Cut 1', margin='15')
            inner1.node('P1', 'P', shape='box', style='filled', fillcolor='lightyellow')
            inner1.node('x1', 'x', shape='circle', style='filled', fillcolor='lightblue')
            inner1.edge('P1', 'x1', style='dashed')
        
        # Second inner cut: ~[ (Q "x") ]  
        with outer.subgraph(name='cluster_inner2') as inner2:
            inner2.attr(style='rounded', color='red', label='Inner Cut 2', margin='15')
            inner2.node('P2', 'Q', shape='box', style='filled', fillcolor='lightyellow')
            inner2.node('x2', 'x', shape='circle', style='filled', fillcolor='lightblue')
            inner2.edge('P2', 'x2', style='dashed')
    
    return dot

def test_graphviz_hierarchical_layout():
    """Test Graphviz hierarchical layout for sibling cuts."""
    
    print("=== Testing Graphviz Hierarchical Layout ===")
    
    # Create test DOT graph
    dot = create_test_dot()
    
    print("DOT Source:")
    print(dot.source)
    print()
    
    # Generate SVG to see the layout
    try:
        svg_output = dot.pipe(format='svg', encoding='utf-8')
        print(f"✓ SVG generated successfully ({len(svg_output)} bytes)")
        
        # Save to file for inspection
        with open('/tmp/test_eg_layout.svg', 'w') as f:
            f.write(svg_output)
        print("✓ SVG saved to /tmp/test_eg_layout.svg")
        
    except Exception as e:
        print(f"✗ SVG generation failed: {e}")
        return False
    
    # Generate PNG for visual inspection
    try:
        png_output = dot.pipe(format='png')
        with open('/tmp/test_eg_layout.png', 'wb') as f:
            f.write(png_output)
        print("✓ PNG saved to /tmp/test_eg_layout.png")
        
    except Exception as e:
        print(f"✗ PNG generation failed: {e}")
    
    print("\n🎉 Graphviz hierarchical layout test completed!")
    print("Key observations:")
    print("- Sibling cuts (Inner Cut 1, Inner Cut 2) should be non-overlapping")
    print("- Both inner cuts should be contained within the outer cut")
    print("- This demonstrates the solution to our overlapping cuts problem")
    
    return True

if __name__ == "__main__":
    test_graphviz_hierarchical_layout()
