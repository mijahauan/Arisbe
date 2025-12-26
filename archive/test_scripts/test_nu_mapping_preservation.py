#!/usr/bin/env python3
"""
Test script to verify ν mapping order preservation in transformations.
This ensures semantic correctness per Dau's Definition 12.1 Component 3.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dataclasses import dataclass
from frozendict import frozendict

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, ElementID
from formal_iteration_rule import FormalIterationEngine, IterationContext


def test_nu_mapping_preservation():
    """Test that ν mapping order is preserved during formal iteration."""
    print("🔍 TESTING ν MAPPING ORDER PRESERVATION")
    print("=" * 60)
    
    # Create test EGI with specific ν mapping order
    v1 = Vertex(ElementID("v1"))
    v2 = Vertex(ElementID("v2"))
    v3 = Vertex(ElementID("v3"))
    e1 = Edge(ElementID("e1"))
    e2 = Edge(ElementID("e2"))
    sheet = ElementID("sheet")
    
    # CRITICAL: Define specific ν mapping order for semantic correctness
    # e1: Man(v1, v2) - v1 is subject, v2 is object
    # e2: Loves(v2, v3) - v2 is subject, v3 is object
    original_nu = frozendict({
        e1.id: (v1.id, v2.id),  # Order: subject, object
        e2.id: (v2.id, v3.id)   # Order: subject, object
    })
    
    test_egi = RelationalGraphWithCuts(
        V=frozenset([v1, v2, v3]),
        E=frozenset([e1, e2]),
        nu=original_nu,
        sheet=sheet,
        Cut=frozenset(),
        area=frozendict({
            sheet: frozenset([v1.id, v2.id, v3.id, e1.id, e2.id])
        }),
        rel=frozendict({
            e1.id: "Man",
            e2.id: "Loves"
        })
    )
    
    print("Original ν mappings:")
    for edge_id, vertex_seq in original_nu.items():
        print(f"  {edge_id}: {vertex_seq}")
    
    # Apply formal iteration to subgraph containing e1
    iteration_engine = FormalIterationEngine()
    subgraph_elements = frozenset([v1.id, v2.id, e1.id])
    
    print(f"\nApplying formal iteration to subgraph: {subgraph_elements}")
    
    result = iteration_engine.apply_formal_iteration(test_egi, subgraph_elements, sheet)
    
    if result.success:
        print("✅ Formal iteration successful")
        
        # Verify ν mapping preservation
        result_nu = result.result_egi.nu
        print(f"\nResult ν mappings ({len(result_nu)} total):")
        
        # Check original edges (index 1)
        original_preserved = True
        for edge_id, vertex_seq in original_nu.items():
            tagged_edge_id = ElementID(f"{edge_id}×1")
            if tagged_edge_id in result_nu:
                result_seq = result_nu[tagged_edge_id]
                expected_seq = tuple(ElementID(f"{v_id}×1") for v_id in vertex_seq)
                print(f"  {tagged_edge_id}: {result_seq}")
                if result_seq != expected_seq:
                    print(f"    ❌ Expected: {expected_seq}")
                    original_preserved = False
                else:
                    print(f"    ✅ Order preserved from original")
            else:
                print(f"  ❌ Missing: {tagged_edge_id}")
                original_preserved = False
        
        # Check iterated edges (index 2)
        iterated_preserved = True
        for edge_id, vertex_seq in original_nu.items():
            if edge_id in subgraph_elements:
                tagged_edge_id = ElementID(f"{edge_id}×2")
                if tagged_edge_id in result_nu:
                    result_seq = result_nu[tagged_edge_id]
                    expected_seq = tuple(ElementID(f"{v_id}×2") for v_id in vertex_seq)
                    print(f"  {tagged_edge_id}: {result_seq}")
                    if result_seq != expected_seq:
                        print(f"    ❌ Expected: {expected_seq}")
                        iterated_preserved = False
                    else:
                        print(f"    ✅ Order preserved in iteration")
        
        # Check fresh identity edges
        fresh_preserved = True
        for edge_id, vertex_seq in result_nu.items():
            if str(edge_id).startswith("e_"):
                print(f"  {edge_id}: {vertex_seq} (fresh identity ligature)")
                # Fresh edges should connect Θ-related vertices: (w×1, v×2)
                if len(vertex_seq) == 2:
                    w_tagged, v_tagged = vertex_seq
                    if str(w_tagged).endswith("×1") and str(v_tagged).endswith("×2"):
                        print(f"    ✅ Fresh edge connects Θ-related vertices correctly")
                    else:
                        print(f"    ❌ Fresh edge has incorrect vertex tagging")
                        fresh_preserved = False
        
        print(f"\n🎯 ν MAPPING PRESERVATION VERIFICATION")
        print("=" * 60)
        print(f"✅ Original edge ν mappings preserved: {original_preserved}")
        print(f"✅ Iterated edge ν mappings preserved: {iterated_preserved}")
        print(f"✅ Fresh identity edge ν mappings correct: {fresh_preserved}")
        
        if original_preserved and iterated_preserved and fresh_preserved:
            print("\n✅ ALL ν MAPPING ORDER PRESERVED - SEMANTIC CORRECTNESS MAINTAINED")
            print("✅ COMPLIANT WITH DAU'S DEFINITION 12.1 COMPONENT 3")
            print("✅ ARGUMENT ORDER PRESERVED FOR RELATION SEMANTICS")
        else:
            print("\n❌ ν MAPPING ORDER ISSUES DETECTED")
            
    else:
        print(f"❌ Formal iteration failed: {result.error_message}")


if __name__ == "__main__":
    test_nu_mapping_preservation()
