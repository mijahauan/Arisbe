#!/usr/bin/env python3
"""
Test dual JSON/YAML format support in EGDF parser.
"""

import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egdf_parser import EGDFParser, EGDFDocument, EGDFMetadata
from egi_core_dau import RelationalGraphWithCuts

def test_dual_format_support():
    """Test that EGDF parser can handle both JSON and YAML formats."""
    
    parser = EGDFParser()
    
    # Create test EGI
    test_egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    
    # Create a minimal EGDF document for testing format support
    from egdf_parser import EGDFMetadata, EGDFDocument
    
    # Create test metadata
    metadata = EGDFMetadata(
        title="Dual Format Test",
        description="Testing JSON/YAML format support",
        author="Test Suite",
        created=datetime.now().isoformat()
    )
    
    # Create minimal test document
    egdf_doc = EGDFDocument(
        metadata=metadata,
        canonical_egi={
            "vertices": [{"id": "v1", "label": "Socrates"}],
            "edges": [{"id": "e1", "relation": "Human", "args": ["v1"]}],
            "cuts": [],
            "areas": {"sheet": ["v1", "e1"]}
        },
        visual_layout={
            "spatial_primitives": [
                {"element_id": "v1", "type": "vertex", "position": {"x": 100, "y": 100}},
                {"element_id": "e1", "type": "edge", "position": {"x": 150, "y": 100}}
            ]
        }
    )
    
    print("=== Testing Dual Format Support ===\n")
    
    # Test JSON export
    print("1. JSON Export:")
    json_output = parser.egdf_to_json(egdf_doc, indent=2)
    print(f"JSON length: {len(json_output)} characters")
    print("JSON preview:")
    print(json_output[:200] + "..." if len(json_output) > 200 else json_output)
    print()
    
    # Test YAML export (if available)
    print("2. YAML Export:")
    try:
        yaml_output = parser.egdf_to_yaml(egdf_doc)
        print(f"YAML length: {len(yaml_output)} characters")
        print("YAML preview:")
        print(yaml_output[:300] + "..." if len(yaml_output) > 300 else yaml_output)
        print()
        
        # Test YAML parsing
        print("3. YAML Round-trip Test:")
        parsed_from_yaml = parser.parse_egdf(yaml_output, format_hint="yaml")
        print(f"✓ YAML parsing successful")
        print(f"  Original metadata title: {egdf_doc.metadata.title}")
        print(f"  Parsed metadata title: {parsed_from_yaml.metadata.title}")
        print()
        
    except ValueError as e:
        if "PyYAML not available" in str(e):
            print("YAML support not available (PyYAML not installed)")
            print("Install with: pip install PyYAML")
        else:
            print(f"YAML error: {e}")
        print()
    
    # Test JSON parsing
    print("4. JSON Round-trip Test:")
    parsed_from_json = parser.parse_egdf(json_output, format_hint="json")
    print(f"✓ JSON parsing successful")
    print(f"  Original metadata title: {egdf_doc.metadata.title}")
    print(f"  Parsed metadata title: {parsed_from_json.metadata.title}")
    print()
    
    # Test auto-detection
    print("5. Format Auto-detection Test:")
    json_detected = parser._detect_format(json_output)
    print(f"  JSON auto-detected as: {json_detected}")
    
    try:
        yaml_detected = parser._detect_format(yaml_output)
        print(f"  YAML auto-detected as: {yaml_detected}")
    except NameError:
        print("  YAML not available for auto-detection test")
    print()
    
    # Test export method
    print("6. Unified Export Method Test:")
    json_via_export = parser.export_egdf(egdf_doc, format_type="json")
    print(f"✓ JSON export via unified method: {len(json_via_export)} characters")
    
    try:
        yaml_via_export = parser.export_egdf(egdf_doc, format_type="yaml")
        print(f"✓ YAML export via unified method: {len(yaml_via_export)} characters")
    except ValueError as e:
        print(f"YAML export via unified method: {e}")
    
    print("\n=== Dual Format Support Test Complete ===")

if __name__ == "__main__":
    test_dual_format_support()
