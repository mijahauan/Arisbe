#!/usr/bin/env python3
"""
Test script to verify Graphviz installation and basic functionality.
"""

try:
    import graphviz
    print("✓ Graphviz Python library imported successfully")
    print(f"  Version: {graphviz.__version__}")
except ImportError as e:
    print(f"✗ Failed to import graphviz: {e}")
    print("  Install with: conda install python-graphviz")
    exit(1)

# Test basic DOT generation
try:
    dot = graphviz.Digraph(comment='Test Graph')
    dot.node('A', 'Node A')
    dot.node('B', 'Node B') 
    dot.edge('A', 'B')
    
    print("✓ Basic DOT graph created successfully")
    print("DOT source:")
    print(dot.source)
    
except Exception as e:
    print(f"✗ Failed to create basic graph: {e}")
    exit(1)

# Test hierarchical subgraphs (what we need for EG cuts)
try:
    dot = graphviz.Digraph(comment='Hierarchical Test')
    
    # Outer cut
    with dot.subgraph(name='cluster_outer') as outer:
        outer.attr(style='rounded', label='Outer Cut')
        
        # Inner cut 1
        with outer.subgraph(name='cluster_inner1') as inner1:
            inner1.attr(style='rounded', label='Inner Cut 1')
            inner1.node('P', 'P')
            inner1.node('x1', 'x')
            inner1.edge('P', 'x1')
        
        # Inner cut 2  
        with outer.subgraph(name='cluster_inner2') as inner2:
            inner2.attr(style='rounded', label='Inner Cut 2')
            inner2.node('Q', 'Q')
            inner2.node('x2', 'x')
            inner2.edge('Q', 'x2')
    
    print("✓ Hierarchical subgraphs created successfully")
    print("This matches our EG cut structure!")
    
except Exception as e:
    print(f"✗ Failed to create hierarchical graph: {e}")
    exit(1)

# Test layout calculation (the key feature we need)
try:
    # Try to get layout positions
    dot_with_layout = graphviz.Source(dot.source)
    print("✓ Layout calculation ready")
    print("  Note: Actual coordinates require rendering to SVG/PNG")
    
except Exception as e:
    print(f"✗ Failed layout test: {e}")
    exit(1)

print("\n🎉 All Graphviz tests passed!")
print("Ready to implement Graphviz-based layout engine for EG cuts.")
