#!/usr/bin/env python3
"""
Graph Construction Debugging Utility
Diagnoses area mapping and graph construction validation issues

CHANGES: Created to debug graph construction failures, particularly area
mapping validation errors that prevent transformations from completing.
"""

import sys
import os
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egif_parser_dau import parse_egif
    from egi_core_dau import RelationalGraphWithCuts, create_vertex, create_edge, create_cut
    import egi_transformations_dau as transforms
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the DAU-compliant modules are available")
    sys.exit(1)


def debug_area_mapping(graph: RelationalGraphWithCuts):
    """Debug area mapping structure."""
    
    print("AREA MAPPING ANALYSIS")
    print("-" * 40)
    
    print(f"Sheet: {graph.sheet}")
    
    # Show all areas
    for context_id, area_elements in graph.area.items():
        context_type = "sheet" if context_id == graph.sheet else "cut"
        polarity = ""
        if context_id != graph.sheet:
            polarity = f" ({('positive' if graph.is_positive_context(context_id) else 'negative')})"
        
        print(f"{context_id} ({context_type}{polarity}): {list(area_elements)}")
    
    # Validate area constraints
    print("\nAREA CONSTRAINT VALIDATION")
    print("-" * 40)
    
    all_elements = {v.id for v in graph.V} | {e.id for e in graph.E} | {c.id for c in graph.Cut}
    print(f"All elements: {all_elements}")
    
    # Check coverage
    covered_elements = set()
    for area_elements in graph.area.values():
        covered_elements |= area_elements
    
    print(f"Covered elements: {covered_elements}")
    
    missing = all_elements - covered_elements
    extra = covered_elements - all_elements
    
    if missing:
        print(f"❌ Missing elements: {missing}")
    if extra:
        print(f"❌ Extra elements: {extra}")
    if not missing and not extra:
        print("✅ Area coverage is correct")
    
    # Check disjointness
    context_ids = list(graph.area.keys())
    overlaps = []
    for i, c1 in enumerate(context_ids):
        for c2 in context_ids[i+1:]:
            area1 = graph.area[c1]
            area2 = graph.area[c2]
            overlap = area1 & area2
            if overlap:
                overlaps.append((c1, c2, overlap))
    
    if overlaps:
        print("❌ Area overlaps found:")
        for c1, c2, overlap in overlaps:
            print(f"  {c1} ∩ {c2} = {overlap}")
    else:
        print("✅ Areas are disjoint")


def test_simple_transformation():
    """Test a simple transformation to see where it fails."""
    
    print("\n" + "=" * 60)
    print("TESTING SIMPLE TRANSFORMATION")
    print("=" * 60)
    
    # Start with simple graph
    egif = "(P *x)"
    print(f"Base EGIF: {egif}")
    
    try:
        graph = parse_egif(egif)
        print("✅ Parsing successful")
        
        debug_area_mapping(graph)
        
        # Try to add an isolated vertex
        print(f"\nTesting isolated vertex addition...")
        
        new_vertex = create_vertex(label="y", is_generic=True)
        print(f"Created vertex: {new_vertex.id}, label='{new_vertex.label}', generic={new_vertex.is_generic}")
        
        try:
            result_graph = transforms.apply_isolated_vertex_addition(
                graph, "y", "generic", graph.sheet
            )
            print("✅ Isolated vertex addition successful")
            
            print("\nResult graph area mapping:")
            debug_area_mapping(result_graph)
            
        except Exception as e:
            print(f"❌ Isolated vertex addition failed: {e}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Parsing failed: {e}")


def test_area_mapping_construction():
    """Test manual area mapping construction."""
    
    print("\n" + "=" * 60)
    print("TESTING MANUAL AREA MAPPING CONSTRUCTION")
    print("=" * 60)
    
    try:
        # Create a simple graph manually
        from frozendict import frozendict
        
        # Create components
        vertex = create_vertex(label="x", is_generic=True)
        edge = create_edge()
        sheet_id = "sheet_test"
        
        print(f"Created vertex: {vertex.id}")
        print(f"Created edge: {edge.id}")
        print(f"Sheet ID: {sheet_id}")
        
        # Build area mapping
        area_mapping = {
            sheet_id: frozenset([vertex.id, edge.id])
        }
        
        # Build other mappings
        nu_mapping = {edge.id: (vertex.id,)}
        rel_mapping = {edge.id: "P"}
        
        print(f"Area mapping: {area_mapping}")
        print(f"Nu mapping: {nu_mapping}")
        print(f"Rel mapping: {rel_mapping}")
        
        # Create graph
        graph = RelationalGraphWithCuts(
            V=frozenset([vertex]),
            E=frozenset([edge]),
            nu=frozendict(nu_mapping),
            sheet=sheet_id,
            Cut=frozenset(),
            area=frozendict(area_mapping),
            rel=frozendict(rel_mapping)
        )
        
        print("✅ Manual graph construction successful")
        debug_area_mapping(graph)
        
        # Test adding another vertex
        print(f"\nTesting vertex addition to manual graph...")
        
        new_vertex = create_vertex(label="y", is_generic=True)
        print(f"New vertex: {new_vertex.id}")
        
        # Update area mapping
        new_area = dict(area_mapping)
        sheet_area = new_area[sheet_id]
        new_area[sheet_id] = sheet_area | {new_vertex.id}
        
        print(f"Updated area mapping: {new_area}")
        
        # Create updated graph
        updated_graph = RelationalGraphWithCuts(
            V=graph.V | {new_vertex},
            E=graph.E,
            nu=graph.nu,
            sheet=graph.sheet,
            Cut=graph.Cut,
            area=frozendict(new_area),
            rel=graph.rel
        )
        
        print("✅ Manual vertex addition successful")
        debug_area_mapping(updated_graph)
        
    except Exception as e:
        print(f"❌ Manual construction failed: {e}")
        import traceback
        traceback.print_exc()


def debug_transformation_failure():
    """Debug specific transformation failure."""
    
    print("\n" + "=" * 60)
    print("DEBUGGING TRANSFORMATION FAILURE")
    print("=" * 60)
    
    # Use the exact case that's failing
    egif = "~[(A *x) (B *y) ~[~[~[(C x) (B y)]]]]"
    print(f"Base EGIF: {egif}")
    
    try:
        graph = parse_egif(egif)
        print("✅ Parsing successful")
        
        debug_area_mapping(graph)
        
        # Try the failing transformation
        print(f"\nTesting isolated vertex addition that fails...")
        
        try:
            result_graph = transforms.apply_isolated_vertex_addition(
                graph, "z", "generic", graph.sheet
            )
            print("✅ Transformation successful")
            debug_area_mapping(result_graph)
            
        except Exception as e:
            print(f"❌ Transformation failed: {e}")
            
            # Debug the specific error
            if "Area coverage mismatch" in str(e):
                print("\nDebugging area coverage mismatch...")
                
                # Try to understand what's happening in the transformation
                new_vertex = create_vertex(label="z", is_generic=True)
                print(f"New vertex would be: {new_vertex.id}")
                
                # Show what the area mapping would look like
                new_area = dict(graph.area)
                sheet_area = new_area.get(graph.sheet, frozenset())
                new_area[graph.sheet] = sheet_area | {new_vertex.id}
                
                print(f"Proposed new area mapping:")
                for context_id, area_elements in new_area.items():
                    print(f"  {context_id}: {list(area_elements)}")
                
                # Check what elements would exist
                all_elements = {v.id for v in graph.V} | {e.id for e in graph.E} | {c.id for c in graph.Cut} | {new_vertex.id}
                covered_elements = set()
                for area_elements in new_area.values():
                    covered_elements |= area_elements
                
                print(f"All elements (with new): {all_elements}")
                print(f"Covered elements: {covered_elements}")
                print(f"Missing: {all_elements - covered_elements}")
                print(f"Extra: {covered_elements - all_elements}")
    
    except Exception as e:
        print(f"❌ Parsing failed: {e}")


def main():
    """Run comprehensive graph construction debugging."""
    
    print("=" * 80)
    print("GRAPH CONSTRUCTION DEBUGGING UTILITY")
    print("=" * 80)
    
    test_simple_transformation()
    test_area_mapping_construction()
    debug_transformation_failure()


if __name__ == "__main__":
    main()

