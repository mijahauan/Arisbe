#!/usr/bin/env python3
"""
Test script to verify baseline GUI rendering functionality.
Tests the Phase 2 GUI with corpus examples to ensure Dau-compliant rendering.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import EGIFParser
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from corpus_loader import CorpusLoader

def test_baseline_rendering():
    """Test that the GUI pipeline can render corpus examples correctly."""
    print("=== Testing Baseline GUI Rendering ===")
    
    # Initialize components
    layout_engine = GraphvizLayoutEngine()
    corpus_loader = CorpusLoader()
    
    # Test with a few key corpus examples
    test_cases = [
        "canonical_implication",
        "dau_2006_p112_ligature", 
        "peirce_cp_4_394_man_mortal",
        "sowa_2011_p356_quantification"
    ]
    
    for case_name in test_cases:
        print(f"\n--- Testing: {case_name} ---")
        
        try:
            # Get EGIF from corpus
            example = corpus_loader.get_example(case_name)
            if not example or not example.egif_content:
                print(f"❌ No EGIF found for {case_name}")
                continue
                
            egif_text = example.egif_content
            print(f"EGIF: {egif_text}")
            
            # Parse EGIF to EGI
            parser = EGIFParser(egif_text)
            egi = parser.parse()
            print(f"✅ Parsed EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
            
            # Generate layout
            layout_result = layout_engine.create_layout_from_graph(egi)
            print(f"✅ Generated layout: {len(layout_result.primitives)} primitives")
            
            # Check for essential elements
            primitive_types = {p.element_type for p in layout_result.primitives.values()}
            print(f"✅ Primitive types: {primitive_types}")
            
            # Verify Dau compliance basics
            has_vertices = any(p.element_type == 'vertex' for p in layout_result.primitives.values())
            has_predicates = any(p.element_type == 'predicate' for p in layout_result.primitives.values())
            has_cuts = any(p.element_type == 'cut' for p in layout_result.primitives.values())
            
            print(f"✅ Has vertices: {has_vertices}, predicates: {has_predicates}, cuts: {has_cuts}")
            
        except Exception as e:
            print(f"❌ Error with {case_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== Baseline Test Complete ===")

if __name__ == "__main__":
    test_baseline_rendering()
