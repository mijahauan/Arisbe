#!/usr/bin/env python3
"""
Test with corrected EGIF syntax to demonstrate non-overlapping cuts properly.
"""

from egif_parser_dau import EGIFParser
from graphviz_layout_integration import GraphvizLayoutIntegration

def test_egif_options():
    """Test different EGIF syntactic options."""
    
    print("=== Testing EGIF Syntactic Options ===")
    
    test_cases = [
        {
            'name': 'Original (Same Constant)',
            'egif': '~[ ~[ (P "x") ] ~[ (Q "x") ] ]',
            'expected': 'One vertex "x" shared by both predicates'
        },
        {
            'name': 'Shared Variable',
            'egif': '*x ~[ ~[ (P x) ] ~[ (Q x) ] ]',
            'expected': 'One variable vertex shared by both predicates'
        },
        {
            'name': 'Different Variables',
            'egif': '~[ *x ~[ (P x) ] ] ~[ *y ~[ (Q y) ] ]',
            'expected': 'Two separate variable vertices'
        },
        {
            'name': 'Different Constants',
            'egif': '~[ ~[ (P "Socrates") ] ~[ (Q "Plato") ] ]',
            'expected': 'Two separate constant vertices'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        print(f"EGIF: {test_case['egif']}")
        print(f"Expected: {test_case['expected']}")
        
        try:
            # Parse EGIF
            parser = EGIFParser(test_case['egif'])
            graph = parser.parse()
            
            print(f"✓ Parsed successfully:")
            print(f"  Vertices: {len(graph.V)} - {[(v.id, v.label, v.is_generic) for v in graph.V]}")
            print(f"  Edges: {len(graph.E)} - {[(e.id, graph.get_relation_name(e.id)) for e in graph.E]}")
            print(f"  Cuts: {len(graph.Cut)}")
            
            # Test Graphviz layout
            integration = GraphvizLayoutIntegration()
            result = integration.calculate_layout(graph)
            
            print(f"  Layout primitives: {len(result.primitives)}")
            print(f"  Primitive types: {set(p['type'] for p in result.primitives)}")
            
            # Show DOT structure (first few lines)
            dot_lines = result.dot_source.split('\n')
            relevant_lines = [line.strip() for line in dot_lines if 'subgraph' in line or '[label=' in line]
            print(f"  DOT structure: {relevant_lines}")
            
        except Exception as e:
            print(f"✗ Failed: {e}")

def test_best_demo_case():
    """Test the best case for demonstrating non-overlapping cuts."""
    
    print(f"\n=== Best Demo Case for Non-overlapping Cuts ===")
    
    # Use different constants to get clear visual separation
    egif_text = '~[ ~[ (Human "Socrates") ] ~[ (Mortal "Plato") ] ]'
    
    print(f"Demo EGIF: {egif_text}")
    print("This should produce 2 vertices, 2 predicates, 3 cuts - perfect for showing non-overlapping layout")
    
    try:
        parser = EGIFParser(egif_text)
        graph = parser.parse()
        
        print(f"✓ Demo EGI structure:")
        print(f"  Vertices: {[(v.id, v.label) for v in graph.V]}")
        print(f"  Edges: {[(e.id, graph.get_relation_name(e.id)) for e in graph.E]}")
        print(f"  Cuts: {len(graph.Cut)}")
        print(f"  Area mapping: {dict(graph.area)}")
        
        # Test layout
        integration = GraphvizLayoutIntegration()
        result = integration.calculate_layout(graph)
        
        print(f"\n✓ Demo layout results:")
        print(f"  Primitives: {len(result.primitives)}")
        print(f"  Types: {[p['type'] for p in result.primitives]}")
        
        print(f"\n✓ Demo DOT source:")
        print(result.dot_source)
        
        return egif_text, graph, result
        
    except Exception as e:
        print(f"✗ Demo failed: {e}")
        return None, None, None

if __name__ == "__main__":
    # Test all options
    test_egif_options()
    
    # Find best demo case
    demo_egif, demo_graph, demo_result = test_best_demo_case()
    
    if demo_result:
        print(f"\n🎉 Found perfect demo case: {demo_egif}")
        print(f"This will clearly show non-overlapping sibling cuts with distinct visual elements.")
    else:
        print(f"\n❌ Could not find suitable demo case.")
