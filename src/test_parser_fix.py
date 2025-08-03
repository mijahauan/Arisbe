#!/usr/bin/env python3
"""
Test script to identify and fix the EGIF parser area assignment bug.
"""

import sys
sys.path.append('.')

from egif_parser_dau import EGIFParser

def test_parser_integrity():
    """Test parser integrity and identify the exact bug."""
    
    print("=== EGIF Parser Integrity Test ===")
    
    # Test the problematic EGIF
    egif = '*x (Human x) ~[ (Mortal x) (Wise x) ]'
    print(f"Testing EGIF: {egif}")
    
    # Parse the graph
    parser = EGIFParser(egif)
    graph = parser.parse()
    
    print(f"\nGraph structure:")
    print(f"  V (vertices): {len(graph.V)}")
    print(f"  E (edges): {len(graph.E)}")
    print(f"  Cut (cuts): {len(graph.Cut)}")
    print(f"  Total elements: {len(graph.V) + len(graph.E) + len(graph.Cut)}")
    
    # Check area assignments
    print(f"\nArea assignments:")
    total_assigned = 0
    for area_id, elements in graph.area.items():
        print(f"  {area_id[-8:]}: {len(elements)} elements")
        total_assigned += len(elements)
    
    print(f"  Total assigned to areas: {total_assigned}")
    
    # Check for orphaned elements (FIXED: compare IDs, not objects)
    all_element_ids = {elem.id for elem in (graph.V | graph.E | graph.Cut)}
    elements_in_areas = set()
    for elements in graph.area.values():
        elements_in_areas.update(elements)
    
    orphaned = all_element_ids - elements_in_areas
    print(f"  Orphaned elements: {len(orphaned)}")
    
    if orphaned:
        print("  ❌ PARSER BUG CONFIRMED: Elements are not being assigned to areas!")
        print("  The parser is using with_vertex() instead of with_vertex_in_context()")
        return False
    else:
        print("  ✅ Parser integrity OK: All elements properly assigned to areas")
        return True

def show_fix_locations():
    """Show the exact locations that need to be fixed in the parser."""
    
    print("\n=== Fix Required in egif_parser_dau.py ===")
    print("The following lines need to be changed:")
    print("  Line 364: self.graph.with_vertex(vertex) → self.graph.with_vertex_in_context(vertex, context_id)")
    print("  Line 390: self.graph.with_vertex(vertex) → self.graph.with_vertex_in_context(vertex, context_id)")  
    print("  Line 431: self.graph.with_vertex(vertex) → self.graph.with_vertex_in_context(vertex, context_id)")
    print("\nThese are in the _parse_argument() and _parse_isolated_vertex() methods.")

if __name__ == "__main__":
    integrity_ok = test_parser_integrity()
    if not integrity_ok:
        show_fix_locations()
        print("\n🔧 Fix these 3 lines to resolve the structural corruption issue!")
