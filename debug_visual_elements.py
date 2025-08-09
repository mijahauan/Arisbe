#!/usr/bin/env python3
"""
Debug Visual Elements - Diagnose why vertices and lines aren't rendering
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.egif_parser_dau import EGIFParser
from src.graphviz_layout_engine_v2 import GraphvizLayoutEngine

def debug_visual_elements():
    """Debug what's happening with visual element generation."""
    
    # Test simple EGIF
    egif_text = '(Human "Socrates") (Mortal "Socrates")'
    print(f"🔍 Debugging EGIF: {egif_text}")
    print("=" * 50)
    
    try:
        # Parse EGIF to EGI
        print("1. Parsing EGIF to EGI...")
        egif_parser = EGIFParser(egif_text)
        egi = egif_parser.parse()
        
        print(f"   ✓ EGI Components:")
        print(f"     - Vertices (V): {len(egi.V)} -> {list(egi.V)}")
        print(f"     - Edges (E): {len(egi.E)} -> {list(egi.E)}")
        print(f"     - Cuts: {len(egi.Cut)} -> {list(egi.Cut)}")
        print(f"     - ν mappings: {len(egi.nu)} -> {dict(egi.nu)}")
        print(f"     - κ mappings: {len(egi.rel)} -> {dict(egi.rel)}")
        
        # Create layout
        print("\n2. Creating layout...")
        layout_engine = GraphvizLayoutEngine()
        layout_result = layout_engine.create_layout_from_graph(egi)
        
        print(f"   ✓ Layout primitives: {len(layout_result.primitives)}")
        
        # Examine each primitive
        print("\n3. Examining spatial primitives:")
        for i, primitive in enumerate(layout_result.primitives):
            print(f"   Primitive {i}:")
            print(f"     - element_id: {primitive.element_id}")
            print(f"     - element_type: {primitive.element_type}")
            
            # Check attributes
            attrs = []
            if hasattr(primitive, 'position'):
                attrs.append(f"position={primitive.position}")
            if hasattr(primitive, 'bounds'):
                attrs.append(f"bounds={primitive.bounds}")
            if hasattr(primitive, 'line_points'):
                attrs.append(f"line_points={primitive.line_points}")
            
            print(f"     - attributes: {', '.join(attrs) if attrs else 'NONE'}")
            
            # This is critical - check if vertices and edges have the right attributes
            if primitive.element_type == "vertex" and not hasattr(primitive, 'position'):
                print(f"     ⚠️  PROBLEM: Vertex missing position attribute!")
            if primitive.element_type == "edge" and not (hasattr(primitive, 'line_points') or hasattr(primitive, 'bounds')):
                print(f"     ⚠️  PROBLEM: Edge missing line_points/bounds attributes!")
        
        print("\n4. Summary:")
        vertex_count = sum(1 for p in layout_result.primitives if p.element_type == "vertex")
        edge_count = sum(1 for p in layout_result.primitives if p.element_type == "edge")
        predicate_count = sum(1 for p in layout_result.primitives if p.element_type == "predicate")
        cut_count = sum(1 for p in layout_result.primitives if p.element_type == "cut")
        
        print(f"   - Vertices: {vertex_count}")
        print(f"   - Edges: {edge_count}")
        print(f"   - Predicates: {predicate_count}")
        print(f"   - Cuts: {cut_count}")
        
        if vertex_count == 0:
            print("   ⚠️  NO VERTICES GENERATED - This explains missing vertex rendering!")
        if edge_count == 0:
            print("   ⚠️  NO EDGES GENERATED - This explains missing line of identity rendering!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_visual_elements()
