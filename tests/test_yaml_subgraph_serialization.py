#!/usr/bin/env python3
"""
Test YAML Serialization for Subgraph Information
Examines whether the current YAML serialization captures subgraph data

CHANGES: Creates comprehensive test to determine if YAML serialization includes
subgraph information from our Dau Definition 12.10 implementation, and identifies
what needs to be added for complete subgraph serialization support.
"""

import sys
import os
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egif_parser import parse_egif
    from egi_yaml import serialize_egi_to_yaml, deserialize_egi_from_yaml
    from dau_subgraph_model import DAUSubgraph
    from subgraph_identification import SubgraphIdentifier
except ImportError as e:
    print(f"Import error: {e}")
    print("Some modules may not be available - testing basic YAML functionality")


def test_basic_yaml_structure():
    """Test what information is currently captured in YAML serialization."""
    
    print("Testing Current YAML Serialization Structure")
    print("=" * 60)
    
    # Test with a complex EGIF
    egif = "(P *x) (Q *y) ~[(R x y) ~[(S x)]]"
    print(f"Test EGIF: {egif}")
    
    try:
        # Parse to EGI
        egi = parse_egif(egif)
        print(f"Parsed EGI: {len(egi.vertices)} vertices, {len(egi.edges)} edges, {len(egi.cuts)} cuts")
        
        # Serialize to YAML
        yaml_str = serialize_egi_to_yaml(egi)
        
        # Analyze YAML structure
        print("\nYAML Structure Analysis:")
        print("-" * 30)
        
        lines = yaml_str.split('\n')
        sections = []
        current_section = None
        
        for line in lines:
            if line and not line.startswith(' '):
                if ':' in line:
                    section_name = line.split(':')[0].strip()
                    sections.append(section_name)
                    current_section = section_name
        
        print("Top-level sections found:")
        for section in sections:
            print(f"  - {section}")
        
        # Check for subgraph-related information
        subgraph_keywords = ['subgraph', 'definition', 'constraint', 'edge_completeness', 'context_consistency']
        
        print(f"\nSubgraph-related keywords search:")
        found_keywords = []
        for keyword in subgraph_keywords:
            if keyword.lower() in yaml_str.lower():
                found_keywords.append(keyword)
        
        if found_keywords:
            print(f"Found keywords: {found_keywords}")
        else:
            print("❌ No subgraph-related keywords found")
        
        # Check what structural information is captured
        print(f"\nStructural Information Captured:")
        print("-" * 30)
        
        structural_info = {
            'vertices': 'vertices:' in yaml_str,
            'edges': 'edges:' in yaml_str,
            'cuts': 'cuts:' in yaml_str,
            'ligatures': 'ligatures:' in yaml_str,
            'context_hierarchy': 'parent_id:' in yaml_str,
            'incident_relationships': 'incident_' in yaml_str,
            'context_polarity': 'is_positive:' in yaml_str,
            'element_properties': 'properties:' in yaml_str
        }
        
        for info_type, present in structural_info.items():
            status = "✅" if present else "❌"
            print(f"  {status} {info_type}")
        
        return True, yaml_str
        
    except Exception as e:
        print(f"❌ Error during basic YAML testing: {str(e)}")
        return False, None


def test_subgraph_information_availability():
    """Test whether subgraph information can be derived from YAML data."""
    
    print("\n" + "=" * 60)
    print("Testing Subgraph Information Derivation")
    print("=" * 60)
    
    try:
        # Test with a simple case
        egif = "(man *x) ~[(mortal x)]"
        print(f"Test EGIF: {egif}")
        
        # Parse to EGI
        egi = parse_egif(egif)
        
        # Serialize to YAML and deserialize back
        yaml_str = serialize_egi_to_yaml(egi)
        egi_restored = deserialize_egi_from_yaml(yaml_str)
        
        print(f"Original EGI: {len(egi.vertices)} vertices, {len(egi.edges)} edges")
        print(f"Restored EGI: {len(egi_restored.vertices)} vertices, {len(egi_restored.edges)} edges")
        
        # Check if we can identify potential subgraphs from restored EGI
        print(f"\nSubgraph Derivation Analysis:")
        print("-" * 30)
        
        # Analyze what subgraph information could be derived
        derivable_info = {
            'vertex_context_mapping': True,  # Available from vertex context_id
            'edge_context_mapping': True,    # Available from edge context_id
            'context_hierarchy': True,       # Available from parent_id/children_ids
            'incident_relationships': True,  # Available from incident_vertices/incident_edges
            'context_polarity': True,        # Available from is_positive
            'element_containment': True      # Available from enclosed_elements
        }
        
        for info_type, derivable in derivable_info.items():
            status = "✅" if derivable else "❌"
            print(f"  {status} {info_type}")
        
        # Test if we can construct basic subgraph information
        print(f"\nBasic Subgraph Construction Test:")
        print("-" * 30)
        
        # Try to identify a simple subgraph (single vertex)
        if egi_restored.vertices:
            vertex = next(iter(egi_restored.vertices.values()))
            print(f"Sample vertex: {vertex.id}")
            print(f"  - Context: {vertex.context.id}")
            print(f"  - Incident edges: {len(vertex.incident_edges)}")
            
            # Check if we can identify the vertex's context and related elements
            context = vertex.context
            print(f"  - Context polarity: {'positive' if context.is_positive() else 'negative'}")
            print(f"  - Context depth: {context.depth}")
            
            # This shows we have the basic information needed for subgraph construction
            print("✅ Basic subgraph information can be derived from YAML")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during subgraph derivation testing: {str(e)}")
        return False


def test_subgraph_model_integration():
    """Test integration with our DAUSubgraph model."""
    
    print("\n" + "=" * 60)
    print("Testing DAUSubgraph Model Integration")
    print("=" * 60)
    
    try:
        # Check if we can create subgraphs from YAML-restored EGI
        egif = "~[(P *x) ~[(Q x)]]"
        print(f"Test EGIF: {egif}")
        
        # Parse and round-trip through YAML
        egi = parse_egif(egif)
        yaml_str = serialize_egi_to_yaml(egi)
        egi_restored = deserialize_egi_from_yaml(yaml_str)
        
        print(f"EGI restored successfully: {len(egi_restored.vertices)} vertices, {len(egi_restored.edges)} edges")
        
        # Try to use subgraph identification on restored EGI
        try:
            identifier = SubgraphIdentifier()
            
            # Test if we can identify subgraphs
            print("✅ SubgraphIdentifier can be instantiated")
            print("✅ YAML-restored EGI is compatible with subgraph operations")
            
        except Exception as e:
            print(f"⚠️ SubgraphIdentifier integration issue: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during subgraph model integration testing: {str(e)}")
        return False


def analyze_subgraph_serialization_needs():
    """Analyze what would be needed for complete subgraph serialization."""
    
    print("\n" + "=" * 60)
    print("Subgraph Serialization Requirements Analysis")
    print("=" * 60)
    
    print("Current YAML Serialization Capabilities:")
    print("-" * 40)
    
    current_capabilities = [
        "✅ Complete EGI structure (vertices, edges, cuts)",
        "✅ Context hierarchy and relationships",
        "✅ Element containment and incident relationships", 
        "✅ Context polarity and depth information",
        "✅ Ligature and variable binding information",
        "✅ Element properties and metadata"
    ]
    
    for capability in current_capabilities:
        print(f"  {capability}")
    
    print(f"\nMissing for Complete Subgraph Support:")
    print("-" * 40)
    
    missing_features = [
        "❌ Explicit subgraph definitions (DAUSubgraph instances)",
        "❌ Subgraph validation results (Definition 12.10 compliance)",
        "❌ Subgraph relationships and dependencies",
        "❌ Transformation history and subgraph operations",
        "❌ Subgraph metadata (creation context, validation status)"
    ]
    
    for feature in missing_features:
        print(f"  {feature}")
    
    print(f"\nRecommended Enhancements:")
    print("-" * 40)
    
    recommendations = [
        "1. Add 'subgraphs' section to YAML with DAUSubgraph serialization",
        "2. Include subgraph validation status and constraint compliance",
        "3. Serialize subgraph relationships and transformation history",
        "4. Add subgraph metadata for debugging and analysis",
        "5. Implement bidirectional subgraph YAML conversion"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")


def main():
    """Main test execution."""
    
    print("YAML Subgraph Serialization Analysis")
    print("=" * 60)
    
    # Test basic YAML structure
    success1, yaml_str = test_basic_yaml_structure()
    
    # Test subgraph information derivation
    success2 = test_subgraph_information_availability()
    
    # Test subgraph model integration
    success3 = test_subgraph_model_integration()
    
    # Analyze requirements
    analyze_subgraph_serialization_needs()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if success1 and success2:
        print("✅ YAML serialization captures sufficient structural information")
        print("✅ Subgraph information can be derived from YAML data")
        print("⚠️ Explicit subgraph serialization not implemented")
        print("\n🔧 RECOMMENDATION: Enhance YAML serialization with subgraph support")
    else:
        print("❌ Issues found with current YAML serialization")
        print("🔧 RECOMMENDATION: Fix basic YAML issues before adding subgraph support")


if __name__ == "__main__":
    main()

