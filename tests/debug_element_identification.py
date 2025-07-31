#!/usr/bin/env python3
"""
Element Identification Debugging Utility
Traces element matching process to fix identification issues

CHANGES: Created to diagnose element identification failures. Shows step-by-step
matching process and reveals why probes don't find expected elements.
"""

import sys
import os
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egif_parser_dau import parse_egif
    from egi_core_dau import RelationalGraphWithCuts
    from element_identification import ElementIdentifier
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the DAU-compliant modules are available")
    sys.exit(1)


def debug_element_identification_process(egif: str, probe: str, context_hint: Optional[str] = None):
    """
    Debug the element identification process step by step.
    
    Args:
        egif: EGIF string to parse
        probe: Probe string to match
        context_hint: Optional context hint
    """
    print(f"\n{'='*60}")
    print(f"DEBUGGING ELEMENT IDENTIFICATION")
    print(f"{'='*60}")
    print(f"EGIF: {egif}")
    print(f"Probe: {probe}")
    print(f"Context Hint: {context_hint}")
    print()
    
    try:
        # Parse the graph
        graph = parse_egif(egif)
        identifier = ElementIdentifier(graph)
        
        print("STEP 1: Graph Structure Analysis")
        print("-" * 40)
        
        # Show actual graph structure
        print(f"Vertices ({len(graph.V)}):")
        for vertex in graph.V:
            print(f"  {vertex.id}: label='{vertex.label}', generic={vertex.is_generic}")
        
        print(f"\nEdges ({len(graph.E)}):")
        for edge in graph.E:
            relation_name = graph.get_relation_name(edge.id)
            incident_vertices = graph.get_incident_vertices(edge.id)
            print(f"  {edge.id}: {relation_name}({', '.join(incident_vertices)})")
        
        print(f"\nCuts ({len(graph.Cut)}):")
        for cut in graph.Cut:
            area = graph.get_area(cut.id)
            print(f"  {cut.id}: area={list(area)}")
        
        print("\nSTEP 2: Probe Analysis")
        print("-" * 40)
        
        # Analyze the probe
        if probe.startswith('(') and probe.endswith(')'):
            print("Probe Type: Relation/Edge")
            content = probe[1:-1]
            parts = content.split()
            if parts:
                relation_name = parts[0]
                vertex_specs = parts[1:]
                print(f"Relation Name: {relation_name}")
                print(f"Vertex Specs: {vertex_specs}")
                
                # Convert vertex specs to expected format
                expected_vertex_labels = []
                for spec in vertex_specs:
                    if spec.startswith('*'):
                        expected_vertex_labels.append((spec[1:], True))  # Generic
                    elif spec.startswith('"') and spec.endswith('"'):
                        expected_vertex_labels.append((spec[1:-1], False))  # Constant
                    else:
                        expected_vertex_labels.append((spec, False))  # Bound occurrence
                
                print(f"Expected Vertex Labels: {expected_vertex_labels}")
                
                print("\nSTEP 3: Edge Matching Process")
                print("-" * 40)
                
                # Check identifier's edge index
                print("Identifier's Edge Index:")
                for key, edge_ids in identifier.edges_by_relation.items():
                    print(f"  {key}: {edge_ids}")
                
                # Try to find matching edges
                search_key = (relation_name, tuple(expected_vertex_labels))
                print(f"\nSearching for key: {search_key}")
                
                if search_key in identifier.edges_by_relation:
                    matches = identifier.edges_by_relation[search_key]
                    print(f"✓ Found matches: {matches}")
                else:
                    print("✗ No exact matches found")
                    
                    # Try to find partial matches
                    print("\nPartial matches:")
                    for key, edge_ids in identifier.edges_by_relation.items():
                        if key[0] == relation_name:  # Same relation name
                            print(f"  Same relation '{relation_name}': {key} -> {edge_ids}")
        
        elif probe.startswith('[') and probe.endswith(']'):
            print("Probe Type: Isolated Vertex")
            content = probe[1:-1]
            
            if content.startswith('*'):
                label = content[1:]
                is_generic = True
            elif content.startswith('"') and content.endswith('"'):
                label = content[1:-1]
                is_generic = False
            else:
                label = content
                is_generic = True
            
            print(f"Expected Label: '{label}'")
            print(f"Expected Generic: {is_generic}")
            
            print("\nSTEP 3: Vertex Matching Process")
            print("-" * 40)
            
            # Check identifier's vertex index
            print("Identifier's Vertex Index:")
            for key, vertex_ids in identifier.vertices_by_label.items():
                print(f"  {key}: {vertex_ids}")
            
            # Try to find matching vertices
            search_key = (label, is_generic)
            print(f"\nSearching for key: {search_key}")
            
            if search_key in identifier.vertices_by_label:
                matches = identifier.vertices_by_label[search_key]
                print(f"✓ Found matches: {matches}")
                
                # Check isolation
                for vertex_id in matches:
                    is_isolated = graph.is_vertex_isolated(vertex_id)
                    print(f"  {vertex_id}: isolated={is_isolated}")
            else:
                print("✗ No exact matches found")
                
                # Show what vertices actually exist
                print("\nActual vertices:")
                for vertex in graph.V:
                    print(f"  {vertex.id}: label='{vertex.label}', generic={vertex.is_generic}")
        
        print("\nSTEP 4: Using ElementIdentifier")
        print("-" * 40)
        
        # Try the actual element identification
        matches = identifier.find_elements_by_egif_probe(probe, context_hint)
        print(f"ElementIdentifier result: {matches}")
        
        if not matches:
            print("\nDiagnosing why no matches found...")
            
            # Check if it's a parsing issue
            if probe.startswith('(') and probe.endswith(')'):
                # Try manual edge search
                content = probe[1:-1]
                parts = content.split()
                if parts:
                    relation_name = parts[0]
                    print(f"Manual search for relation '{relation_name}':")
                    
                    for edge in graph.E:
                        edge_relation = graph.get_relation_name(edge.id)
                        if edge_relation == relation_name:
                            incident_vertices = graph.get_incident_vertices(edge.id)
                            print(f"  Found: {edge.id} -> {edge_relation}({', '.join(incident_vertices)})")
                            
                            # Check vertex labels
                            vertex_labels = []
                            for vertex_id in incident_vertices:
                                vertex = graph.get_vertex(vertex_id)
                                vertex_labels.append((vertex.label, vertex.is_generic))
                            print(f"    Vertex labels: {vertex_labels}")
        
        print(f"\n{'='*60}")
        
    except Exception as e:
        print(f"Error during debugging: {e}")
        import traceback
        traceback.print_exc()


def analyze_parser_vertex_labeling():
    """Analyze how the parser handles vertex labeling."""
    
    print(f"\n{'='*80}")
    print("ANALYZING PARSER VERTEX LABELING")
    print(f"{'='*80}")
    
    test_cases = [
        "(P *x)",           # Generic vertex
        "(P \"Alice\")",    # Constant vertex  
        "[*x]",            # Isolated generic vertex
        "[\"Bob\"]",       # Isolated constant vertex
        "(P *x) (Q x)",    # Generic + bound occurrence
    ]
    
    for egif in test_cases:
        print(f"\nTesting: {egif}")
        try:
            graph = parse_egif(egif)
            
            print("Vertices:")
            for vertex in graph.V:
                print(f"  {vertex.id}: label='{vertex.label}', generic={vertex.is_generic}")
            
            print("Edges:")
            for edge in graph.E:
                relation_name = graph.get_relation_name(edge.id)
                incident_vertices = graph.get_incident_vertices(edge.id)
                print(f"  {edge.id}: {relation_name}({', '.join(incident_vertices)})")
        
        except Exception as e:
            print(f"  Error: {e}")


def main():
    """Run comprehensive element identification debugging."""
    
    print("=" * 80)
    print("ELEMENT IDENTIFICATION DEBUGGING UTILITY")
    print("=" * 80)
    
    # Analyze parser vertex labeling first
    analyze_parser_vertex_labeling()
    
    # Test specific failing cases
    failing_cases = [
        {
            "egif": "~[(Human *x) ~[(Mortal x)]]",
            "probe": "(Mortal x)",
            "context_hint": "positive context"
        },
        {
            "egif": "(P *x)",
            "probe": "(P *x)",
            "context_hint": None
        },
        {
            "egif": "[*x] ~[(P x)]",
            "probe": "[*x]",
            "context_hint": "sheet"
        },
        {
            "egif": "~[~[(P *x)]]",
            "probe": "(P *x)",
            "context_hint": "positive context"
        }
    ]
    
    for case in failing_cases:
        debug_element_identification_process(
            case["egif"], 
            case["probe"], 
            case["context_hint"]
        )


if __name__ == "__main__":
    main()

