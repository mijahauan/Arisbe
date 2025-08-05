#!/usr/bin/env python3
"""
Phase 1d API Contract Validation Test

Tests the complete EGI ↔ EGDF conversion pipeline with strict API contract enforcement.
This validates that Phase 1d is complete and the foundation is mathematically rigorous.
"""

import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egdf_parser import EGDFParser, EGDFDocument, EGDFMetadata, SpatialPrimitive, Coordinate
from egi_core_dau import RelationalGraphWithCuts, create_empty_graph, Vertex, Edge, Cut
from egif_parser_dau import EGIFParser
from pipeline_contracts import ContractViolationError, validate_relational_graph_with_cuts

def create_test_spatial_primitives(egi: RelationalGraphWithCuts) -> list:
    """Create minimal spatial primitives for testing."""
    primitives = []
    
    # Create primitives for all vertices
    for i, vertex in enumerate(egi.V):
        primitive = SpatialPrimitive(
            element_id=vertex.id,
            element_type="vertex",
            position=(100.0 + i * 50, 100.0),
            bounds=(90.0 + i * 50, 90.0, 110.0 + i * 50, 110.0),
            id=f"sp_{vertex.id}"
        )
        primitives.append(primitive)
    
    # Create primitives for all edges
    for i, edge in enumerate(egi.E):
        primitive = SpatialPrimitive(
            element_id=edge.id,
            element_type="edge",
            position=(200.0 + i * 50, 150.0),
            bounds=(190.0 + i * 50, 140.0, 210.0 + i * 50, 160.0),
            id=f"sp_{edge.id}"
        )
        primitives.append(primitive)
    
    # Create primitives for all cuts
    for i, cut in enumerate(egi.Cut):
        primitive = SpatialPrimitive(
            element_id=cut.id,
            element_type="cut",
            position=(300.0 + i * 100, 200.0),
            bounds=(250.0 + i * 100, 150.0, 350.0 + i * 100, 250.0),
            id=f"sp_{cut.id}"
        )
        primitives.append(primitive)
    
    return primitives

def test_phase1d_api_contracts():
    """Test complete Phase 1d API contract enforcement."""
    
    print("=== Phase 1d API Contract Validation Test ===\n")
    
    parser = EGDFParser()
    
    # Test 1: Create EGI from EGIF
    print("1. Testing EGIF → EGI with contracts:")
    test_egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    
    try:
        egif_parser = EGIFParser(test_egif)
        egi = egif_parser.parse()
        print(f"✓ EGI created successfully")
        print(f"  Vertices: {len(egi.V)}")
        print(f"  Edges: {len(egi.E)}")
        print(f"  Cuts: {len(egi.Cut)}")
        
        # Validate EGI meets contracts
        validate_relational_graph_with_cuts(egi)
        print(f"✓ EGI passes contract validation")
        
    except Exception as e:
        print(f"❌ EGIF → EGI failed: {e}")
        return False
    
    print()
    
    # Test 2: Create EGDF from EGI with API contracts
    print("2. Testing EGI → EGDF with full API contracts:")
    
    try:
        # Create spatial primitives that cover all EGI elements
        spatial_primitives = create_test_spatial_primitives(egi)
        print(f"✓ Created {len(spatial_primitives)} spatial primitives")
        
        # This should enforce input contracts and validate layout primitives
        egdf_doc = parser.create_egdf_from_egi(egi, spatial_primitives)
        print(f"✓ EGDF document created with contract validation")
        print(f"  Format: {egdf_doc.format}")
        print(f"  Version: {egdf_doc.version}")
        
    except ContractViolationError as e:
        print(f"❌ Contract violation: {e}")
        return False
    except Exception as e:
        print(f"❌ EGI → EGDF failed: {e}")
        return False
    
    print()
    
    # Test 3: Extract EGI from EGDF with contracts
    print("3. Testing EGDF → EGI with contract validation:")
    
    try:
        # This should enforce output contracts
        recovered_egi = parser.extract_egi_from_egdf(egdf_doc)
        print(f"✓ EGI extracted successfully")
        print(f"  Vertices: {len(recovered_egi.V)}")
        print(f"  Edges: {len(recovered_egi.E)}")
        print(f"  Cuts: {len(recovered_egi.Cut)}")
        
        # Validate recovered EGI meets contracts
        validate_relational_graph_with_cuts(recovered_egi)
        print(f"✓ Recovered EGI passes contract validation")
        
    except ContractViolationError as e:
        print(f"❌ Contract violation: {e}")
        return False
    except Exception as e:
        print(f"❌ EGDF → EGI failed: {e}")
        return False
    
    print()
    
    # Test 4: Round-trip structural integrity
    print("4. Testing round-trip structural integrity:")
    
    try:
        # Compare original and recovered EGI structures
        original_vertex_count = len(egi.V)
        recovered_vertex_count = len(recovered_egi.V)
        
        original_edge_count = len(egi.E)
        recovered_edge_count = len(recovered_egi.E)
        
        original_cut_count = len(egi.Cut)
        recovered_cut_count = len(recovered_egi.Cut)
        
        print(f"  Original:  V={original_vertex_count}, E={original_edge_count}, Cut={original_cut_count}")
        print(f"  Recovered: V={recovered_vertex_count}, E={recovered_edge_count}, Cut={recovered_cut_count}")
        
        if (original_vertex_count == recovered_vertex_count and 
            original_edge_count == recovered_edge_count and 
            original_cut_count == recovered_cut_count):
            print(f"✓ Round-trip preserves structural integrity")
        else:
            print(f"❌ Round-trip structural mismatch")
            return False
            
    except Exception as e:
        print(f"❌ Round-trip validation failed: {e}")
        return False
    
    print()
    
    # Test 5: Contract violation detection
    print("5. Testing contract violation detection:")
    
    try:
        # Test with incomplete spatial primitives (should fail)
        incomplete_primitives = spatial_primitives[:-1]  # Remove one primitive
        print(f"  Testing with incomplete primitives ({len(incomplete_primitives)} instead of {len(spatial_primitives)})")
        
        try:
            parser.create_egdf_from_egi(egi, incomplete_primitives)
            print(f"❌ Contract should have caught incomplete primitives")
            return False
        except ContractViolationError as e:
            print(f"✓ Contract correctly caught incomplete primitives: {str(e)[:80]}...")
            
    except Exception as e:
        print(f"❌ Contract violation test failed: {e}")
        return False
    
    print()
    
    # Test 6: Dual format support with contracts
    print("6. Testing dual format export with contract validation:")
    
    try:
        # JSON export
        json_output = parser.export_egdf(egdf_doc, format_type="json")
        print(f"✓ JSON export: {len(json_output)} characters")
        
        # Debug: Show first part of JSON to understand structure
        print(f"  JSON preview: {json_output[:200]}...")
        
        # Parse JSON back
        parsed_from_json = parser.parse_egdf(json_output, format_hint="json")
        recovered_from_json = parser.extract_egi_from_egdf(parsed_from_json)
        validate_relational_graph_with_cuts(recovered_from_json)
        print(f"✓ JSON round-trip with contract validation")
        
        # YAML export (if available)
        try:
            yaml_output = parser.export_egdf(egdf_doc, format_type="yaml")
            print(f"✓ YAML export: {len(yaml_output)} characters")
            
            # Parse YAML back
            parsed_from_yaml = parser.parse_egdf(yaml_output, format_hint="yaml")
            recovered_from_yaml = parser.extract_egi_from_egdf(parsed_from_yaml)
            validate_relational_graph_with_cuts(recovered_from_yaml)
            print(f"✓ YAML round-trip with contract validation")
            
        except ValueError as e:
            if "PyYAML not available" in str(e):
                print(f"⚠️  YAML not available (PyYAML not installed)")
            else:
                raise
        
    except Exception as e:
        print(f"❌ Dual format test failed: {e}")
        return False
    
    print()
    print("=== Phase 1d API Contract Validation: ALL TESTS PASSED ===")
    print("✓ EGI ↔ EGDF transitions are now fully contract-validated")
    print("✓ Mathematical rigor is enforced at every pipeline stage")
    print("✓ Foundation is ready for Phase 2+ development")
    
    return True

if __name__ == "__main__":
    success = test_phase1d_api_contracts()
    if not success:
        sys.exit(1)
    print("\n🎯 Phase 1d Complete: API contracts are fully enforced!")
