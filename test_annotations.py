#!/usr/bin/env python3
"""
Test script to debug annotation generation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egif_parser_dau import EGIFParser
    from egi_core_dau import RelationalGraphWithCuts
    from graphviz_layout_engine_v2 import GraphvizLayoutEngine
    from annotation_system import AnnotationManager, AnnotationType, create_arity_numbering_layer
except ImportError as e:
    print(f"Import error: {e}")
    # Try alternative import paths
    try:
        from src.egif_parser_dau import EGIFParser
        from src.egi_core_dau import RelationalGraphWithCuts
        from src.graphviz_layout_engine_v2 import GraphvizLayoutEngine
        from src.annotation_system import AnnotationManager, AnnotationType, create_arity_numbering_layer
    except ImportError as e2:
        print(f"Alternative import also failed: {e2}")
        sys.exit(1)

def test_annotation_generation():
    """Test annotation generation on the Loves x y example."""
    
    # Parse the Loves x y EGIF
    egif = '*x *y (Loves x y) ~[ (Happy x) ]'
    print(f"Testing EGIF: {egif}")
    
    try:
        parser = EGIFParser(egif)
        egi = parser.parse()
        print(f"✓ Parsed EGI successfully")
        print(f"  Vertices: {len(egi.V)}")
        print(f"  Edges: {len(egi.E)}")
        print(f"  Nu mapping: {dict(egi.nu)}")
        
        # Check arity of each edge
        for edge_id in egi.E:
            if edge_id in egi.nu:
                arity = len(egi.nu[edge_id])
                print(f"  Edge {edge_id}: arity {arity}, vertices {egi.nu[edge_id]}")
        
    except Exception as e:
        print(f"✗ Failed to parse EGIF: {e}")
        return
    
    # Generate layout
    layout_engine = GraphvizLayoutEngine()
    try:
        layout_result = layout_engine.create_layout_from_graph(egi)
        print(f"✓ Generated layout successfully")
        print(f"  Primitives: {len(layout_result.primitives)}")
        for prim_id, primitive in layout_result.primitives.items():
            print(f"    {prim_id}: {primitive.element_type} at {primitive.position}")
        
    except Exception as e:
        print(f"✗ Failed to generate layout: {e}")
        return
    
    # Test annotation generation
    annotation_manager = AnnotationManager()
    arity_layer = create_arity_numbering_layer(enabled=True)
    annotation_manager.add_layer(arity_layer)
    
    print(f"\n--- Testing Annotation Generation ---")
    try:
        annotations = annotation_manager.generate_annotations(layout_result, egi)
        print(f"✓ Generated {len(annotations)} annotations")
        
        for annotation in annotations:
            print(f"  Annotation: {annotation.content} at {annotation.position}")
            print(f"    Type: {annotation.annotation_type}")
            print(f"    Element: {annotation.element_id}")
            print(f"    Style: {annotation.style}")
        
        if len(annotations) == 0:
            print("✗ No annotations generated - debugging...")
            
            # Debug the annotation generation
            for layer in annotation_manager.annotation_layers:
                print(f"  Layer: {layer.layer_id}")
                for config in layer.annotations:
                    print(f"    Config: {config.annotation_type}, enabled: {config.enabled}")
        
    except Exception as e:
        print(f"✗ Failed to generate annotations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_annotation_generation()
