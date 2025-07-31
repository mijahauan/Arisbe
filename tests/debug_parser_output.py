#!/usr/bin/env python3
"""
Parser Output Debugging Utility
Examines actual graph structure vs expected to fix element identification

CHANGES: Created to diagnose parser output alignment issues. Shows actual
internal graph structure to understand why element identification fails.
"""

import sys
import os
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egif_parser_dau import parse_egif
    from egi_core_dau import RelationalGraphWithCuts
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the DAU-compliant modules are available")
    sys.exit(1)


def debug_graph_structure(egif: str) -> Dict[str, Any]:
    """
    Parse EGIF and return detailed structure information.
    
    Args:
        egif: EGIF string to parse
        
    Returns:
        Dictionary with detailed graph structure
    """
    try:
        print(f"Parsing EGIF: {egif}")
        graph = parse_egif(egif)
        
        debug_info = {
            "egif": egif,
            "vertices": [],
            "edges": [],
            "cuts": [],
            "areas": {},
            "relations": {},
            "vertex_sequences": {},
            "sheet": graph.sheet,
            "context_hierarchy": {}
        }
        
        # Analyze vertices
        print(f"\nVertices ({len(graph.V)}):")
        for vertex in graph.V:
            vertex_info = {
                "id": vertex.id,
                "label": vertex.label,
                "is_generic": vertex.is_generic,
                "context": graph.get_context(vertex.id),
                "is_isolated": graph.is_vertex_isolated(vertex.id)
            }
            debug_info["vertices"].append(vertex_info)
            print(f"  {vertex.id}: label='{vertex.label}', generic={vertex.is_generic}, context={vertex_info['context']}, isolated={vertex_info['is_isolated']}")
        
        # Analyze edges
        print(f"\nEdges ({len(graph.E)}):")
        for edge in graph.E:
            relation_name = graph.get_relation_name(edge.id)
            incident_vertices = graph.get_incident_vertices(edge.id)
            context = graph.get_context(edge.id)
            
            edge_info = {
                "id": edge.id,
                "relation_name": relation_name,
                "incident_vertices": incident_vertices,
                "context": context
            }
            debug_info["edges"].append(edge_info)
            debug_info["relations"][edge.id] = relation_name
            debug_info["vertex_sequences"][edge.id] = incident_vertices
            
            print(f"  {edge.id}: {relation_name}({', '.join(incident_vertices)}), context={context}")
        
        # Analyze cuts
        print(f"\nCuts ({len(graph.Cut)}):")
        for cut in graph.Cut:
            area = graph.get_area(cut.id)
            context = graph.get_context(cut.id)
            polarity = "positive" if graph.is_positive_context(cut.id) else "negative"
            
            cut_info = {
                "id": cut.id,
                "area": list(area),
                "context": context,
                "polarity": polarity
            }
            debug_info["cuts"].append(cut_info)
            debug_info["areas"][cut.id] = list(area)
            
            print(f"  {cut.id}: area={list(area)}, context={context}, polarity={polarity}")
        
        # Analyze areas
        print(f"\nArea Mapping:")
        for context_id, area_elements in graph.area.items():
            debug_info["areas"][context_id] = list(area_elements)
            print(f"  {context_id}: {list(area_elements)}")
        
        # Build context hierarchy
        print(f"\nContext Hierarchy:")
        for element_id in [v.id for v in graph.V] + [e.id for e in graph.E] + [c.id for c in graph.Cut]:
            try:
                context = graph.get_context(element_id)
                if context not in debug_info["context_hierarchy"]:
                    debug_info["context_hierarchy"][context] = []
                debug_info["context_hierarchy"][context].append(element_id)
            except:
                pass
        
        for context_id, elements in debug_info["context_hierarchy"].items():
            print(f"  {context_id}: {elements}")
        
        return debug_info
        
    except Exception as e:
        print(f"Error parsing EGIF: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def test_element_matching(egif: str, probes: List[str]):
    """
    Test element matching for various probes.
    
    Args:
        egif: EGIF string to parse
        probes: List of probe strings to test
    """
    print(f"\n{'='*60}")
    print(f"TESTING ELEMENT MATCHING")
    print(f"{'='*60}")
    
    try:
        graph = parse_egif(egif)
        
        for probe in probes:
            print(f"\nProbe: {probe}")
            
            # Try to match manually
            if probe.startswith('(') and probe.endswith(')'):
                # Relation probe
                content = probe[1:-1]
                parts = content.split()
                if parts:
                    relation_name = parts[0]
                    vertex_specs = parts[1:]
                    
                    print(f"  Looking for relation: {relation_name}")
                    print(f"  With vertices: {vertex_specs}")
                    
                    # Find matching edges
                    matches = []
                    for edge in graph.E:
                        edge_relation = graph.get_relation_name(edge.id)
                        if edge_relation == relation_name:
                            incident_vertices = graph.get_incident_vertices(edge.id)
                            print(f"    Found edge {edge.id}: {edge_relation}({', '.join(incident_vertices)})")
                            matches.append(edge.id)
                    
                    if matches:
                        print(f"  ✓ Found {len(matches)} matches: {matches}")
                    else:
                        print(f"  ✗ No matches found")
            
            elif probe.startswith('[') and probe.endswith(']'):
                # Vertex probe
                content = probe[1:-1]
                if content.startswith('*'):
                    label = content[1:]
                    is_generic = True
                else:
                    label = content
                    is_generic = False
                
                print(f"  Looking for vertex: label='{label}', generic={is_generic}")
                
                # Find matching vertices
                matches = []
                for vertex in graph.V:
                    if vertex.label == label and vertex.is_generic == is_generic:
                        print(f"    Found vertex {vertex.id}: label='{vertex.label}', generic={vertex.is_generic}")
                        matches.append(vertex.id)
                
                if matches:
                    print(f"  ✓ Found {len(matches)} matches: {matches}")
                else:
                    print(f"  ✗ No matches found")
            
            else:
                print(f"  ? Unknown probe format")
    
    except Exception as e:
        print(f"Error testing element matching: {e}")


def main():
    """Run comprehensive parser debugging."""
    
    print("=" * 80)
    print("PARSER OUTPUT DEBUGGING UTILITY")
    print("=" * 80)
    
    # Test cases from the failing tests
    test_cases = [
        {
            "egif": "~[(Human *x) ~[(Mortal x)]]",
            "probes": ["(Human *x)", "(Mortal x)", "[*x]"]
        },
        {
            "egif": "(P *x)",
            "probes": ["(P *x)", "[*x]"]
        },
        {
            "egif": "[*x] ~[(P x)]",
            "probes": ["[*x]", "(P x)"]
        },
        {
            "egif": "~[~[(P *x)]]",
            "probes": ["(P *x)", "[*x]"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST CASE {i}: {test_case['egif']}")
        print(f"{'='*80}")
        
        # Debug graph structure
        debug_info = debug_graph_structure(test_case["egif"])
        
        # Test element matching
        if "error" not in debug_info:
            test_element_matching(test_case["egif"], test_case["probes"])
    
    print(f"\n{'='*80}")
    print("DEBUGGING COMPLETE")
    print("=" * 80)
    print("\nKey Findings:")
    print("1. Check if vertex labels match expected format")
    print("2. Verify relation names are stored correctly")
    print("3. Confirm vertex sequences match probe expectations")
    print("4. Validate context assignments")


if __name__ == "__main__":
    main()

