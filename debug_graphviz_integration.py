#!/usr/bin/env python3
"""
Debug GraphvizLayoutEngine Integration
Test the GraphvizLayoutEngine directly to see what it returns.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import EGIFParser
from graphviz_layout_engine_v2 import GraphvizLayoutEngine

def test_graphviz_layout():
    """Test GraphvizLayoutEngine with a simple EGIF example."""
    
    # Simple test case
    egif_text = '(Human "Socrates")'
    print(f"Testing EGIF: {egif_text}")
    
    try:
        # 1. Parse EGIF to EGI
        print("1. Parsing EGIF to EGI...")
        egif_parser = EGIFParser(egif_text)
        egi = egif_parser.parse()
        print(f"   EGI parsed: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
        
        # 2. Create layout engine
        print("2. Creating GraphvizLayoutEngine...")
        layout_engine = GraphvizLayoutEngine()
        
        # 3. Generate layout
        print("3. Generating layout...")
        layout_result = layout_engine.create_layout_from_graph(egi)
        print(f"   Layout result type: {type(layout_result)}")
        print(f"   Layout result attributes: {[attr for attr in dir(layout_result) if not attr.startswith('_')]}")
        
        # 4. Check primitives
        if hasattr(layout_result, 'primitives'):
            primitives = layout_result.primitives
            print(f"   Found {len(primitives)} spatial primitives:")
            for element_id, primitive in primitives.items():
                print(f"     {element_id}: {primitive.element_type} at {primitive.position}")
                print(f"       bounds: {primitive.bounds}")
        else:
            print("   No 'primitives' attribute found!")
            
        return layout_result
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_graphviz_layout()
