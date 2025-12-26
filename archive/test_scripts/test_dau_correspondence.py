#!/usr/bin/env python3
"""
Test the Dau-compliant diagram correspondence engine with corpus examples.
Validates that the correspondence correctly implements Dau's Chapter 12 requirements.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dau_diagram_correspondence import (
    DauDiagramCorrespondence, DiagramRepresentation, VertexSpot, RelationSign, 
    EdgeLine, CutLine, ConstraintViolation
)
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from frozendict import frozendict
import json


def test_simple_diagram_validation():
    """Test basic diagram constraint validation."""
    print("=== Testing Diagram Constraint Validation ===\n")
    
    correspondence = DauDiagramCorrespondence()
    
    # Test 1: Valid binary relation diagram
    print("1. Testing valid binary relation...")
    
    # Create a simple "Socrates is mortal" diagram
    vertex_spots = {
        "socrates": VertexSpot(
            element_id="socrates",
            label="Socrates",
            is_generic=False,
            containing_cut=None
        ),
        "mortal_property": VertexSpot(
            element_id="mortal_property", 
            label="Mortal",
            is_generic=False,
            containing_cut=None
        )
    }
    
    relation_signs = {
        "is_relation": RelationSign(
            element_id="is_relation",
            relation_name="is",
            arity=2,
            containing_cut=None
        )
    }
    
    edge_lines = {
        "line1": EdgeLine(
            element_id="line1",
            relation_sign_id="is_relation",
            vertex_spot_id="socrates",
            position_number=1
        ),
        "line2": EdgeLine(
            element_id="line2", 
            relation_sign_id="is_relation",
            vertex_spot_id="mortal_property",
            position_number=2
        )
    }
    
    diagram = DiagramRepresentation(
        sheet_id="sheet",
        vertex_spots=vertex_spots,
        relation_signs=relation_signs,
        edge_lines=edge_lines,
        cut_lines={},
        containment={"sheet": {"socrates", "mortal_property", "is_relation"}}
    )
    
    try:
        result = correspondence.validate_diagram_constraints(diagram)
        print("   ✓ Valid binary relation diagram passed validation")
    except ConstraintViolation as e:
        print(f"   ✗ Unexpected validation failure: {e}")
    
    # Test 2: Invalid arity mismatch
    print("\n2. Testing invalid arity mismatch...")
    
    # Create relation with arity 3 but only 2 edge-lines
    invalid_relation_signs = {
        "bad_relation": RelationSign(
            element_id="bad_relation",
            relation_name="triple",
            arity=3,  # Claims arity 3
            containing_cut=None
        )
    }
    
    invalid_edge_lines = {
        "line1": EdgeLine(
            element_id="line1",
            relation_sign_id="bad_relation", 
            vertex_spot_id="socrates",
            position_number=1
        ),
        "line2": EdgeLine(
            element_id="line2",
            relation_sign_id="bad_relation",
            vertex_spot_id="mortal_property", 
            position_number=2
        )
        # Missing position 3!
    }
    
    invalid_diagram = DiagramRepresentation(
        sheet_id="sheet",
        vertex_spots=vertex_spots,
        relation_signs=invalid_relation_signs,
        edge_lines=invalid_edge_lines,
        cut_lines={},
        containment={"sheet": {"socrates", "mortal_property", "bad_relation"}}
    )
    
    try:
        correspondence.validate_diagram_constraints(invalid_diagram)
        print("   ✗ Should have failed validation")
    except ConstraintViolation as e:
        print(f"   ✓ Correctly caught arity violation: {e}")


def test_dominating_nodes_constraint():
    """Test the dominating nodes constraint."""
    print("\n=== Testing Dominating Nodes Constraint ===\n")
    
    correspondence = DauDiagramCorrespondence()
    
    # Test 3: Valid dominating nodes (relation in same cut as vertex)
    print("3. Testing valid dominating nodes...")
    
    vertex_spots = {
        "x": VertexSpot(
            element_id="x",
            is_generic=True,
            containing_cut="cut1"  # Vertex in cut
        )
    }
    
    relation_signs = {
        "mortal": RelationSign(
            element_id="mortal",
            relation_name="Mortal",
            arity=1,
            containing_cut="cut1"  # Relation in same cut - valid
        )
    }
    
    edge_lines = {
        "line1": EdgeLine(
            element_id="line1",
            relation_sign_id="mortal",
            vertex_spot_id="x", 
            position_number=1
        )
    }
    
    cut_lines = {
        "cut1": CutLine(element_id="cut1")
    }
    
    valid_diagram = DiagramRepresentation(
        sheet_id="sheet",
        vertex_spots=vertex_spots,
        relation_signs=relation_signs,
        edge_lines=edge_lines,
        cut_lines=cut_lines,
        containment={
            "sheet": {"cut1"},
            "cut1": {"x", "mortal"}
        }
    )
    
    try:
        correspondence.validate_diagram_constraints(valid_diagram)
        print("   ✓ Valid dominating nodes passed validation")
    except ConstraintViolation as e:
        print(f"   ✗ Unexpected validation failure: {e}")
    
    # Test 4: Invalid dominating nodes (vertex in cut, relation on sheet)
    print("\n4. Testing invalid dominating nodes...")
    
    invalid_relation_signs = {
        "mortal": RelationSign(
            element_id="mortal",
            relation_name="Mortal", 
            arity=1,
            containing_cut=None  # Relation on sheet, but vertex in cut - invalid!
        )
    }
    
    invalid_diagram = DiagramRepresentation(
        sheet_id="sheet",
        vertex_spots=vertex_spots,  # x still in cut1
        relation_signs=invalid_relation_signs,
        edge_lines=edge_lines,
        cut_lines=cut_lines,
        containment={
            "sheet": {"cut1", "mortal"},  # Relation on sheet
            "cut1": {"x"}  # Vertex in cut
        }
    )
    
    try:
        correspondence.validate_diagram_constraints(invalid_diagram)
        print("   ✗ Should have failed dominating nodes validation")
        print("   DEBUG: Checking domination logic...")
        print(f"   Vertex 'x' in cut: {vertex_spots['x'].containing_cut}")
        print(f"   Relation 'mortal' in cut: {invalid_relation_signs['mortal'].containing_cut}")
    except ConstraintViolation as e:
        print(f"   ✓ Correctly caught dominating nodes violation: {e}")


def test_bidirectional_reconstruction():
    """Test bidirectional EGI ↔ diagram reconstruction."""
    print("\n=== Testing Bidirectional Reconstruction ===\n")
    
    correspondence = DauDiagramCorrespondence()
    
    # Test 5: EGI → Diagram → EGI round-trip
    print("5. Testing EGI → Diagram → EGI round-trip...")
    
    # Create a simple EGI
    vertices = frozenset([
        Vertex(id="socrates", label="Socrates", is_generic=False),
        Vertex(id="x", is_generic=True)
    ])
    
    edges = frozenset([
        Edge(id="mortal_rel")
    ])
    
    nu_mapping = frozendict({
        "mortal_rel": ("socrates", "x")  # Binary relation
    })
    
    rel_mapping = frozendict({
        "mortal_rel": "Mortal"
    })
    
    area_mapping = frozendict({
        "sheet": frozenset({"socrates", "x", "mortal_rel"})
    })
    
    original_egi = RelationalGraphWithCuts(
        V=vertices,
        E=edges,
        nu=nu_mapping,
        sheet="sheet",
        Cut=frozenset(),
        area=area_mapping,
        rel=rel_mapping
    )
    
    # Convert to diagram
    diagram = correspondence.egi_to_diagram(original_egi)
    print("   ✓ EGI → Diagram conversion completed")
    
    # Validate diagram
    try:
        correspondence.validate_diagram_constraints(diagram)
        print("   ✓ Generated diagram passes validation")
    except ConstraintViolation as e:
        print(f"   ✗ Generated diagram failed validation: {e}")
        return
    
    # Convert back to EGI
    reconstructed_egi = correspondence.diagram_to_egi(diagram)
    print("   ✓ Diagram → EGI conversion completed")
    
    # Compare key properties (structural equivalence)
    if (len(original_egi.V) == len(reconstructed_egi.V) and
        len(original_egi.E) == len(reconstructed_egi.E) and
        original_egi.nu == reconstructed_egi.nu and
        original_egi.rel == reconstructed_egi.rel):
        print("   ✓ Round-trip reconstruction preserves EGI structure")
    else:
        print("   ✗ Round-trip reconstruction failed")
        print(f"      Original vertices: {len(original_egi.V)}, Reconstructed: {len(reconstructed_egi.V)}")
        print(f"      Original edges: {len(original_egi.E)}, Reconstructed: {len(reconstructed_egi.E)}")


def test_with_corpus_example():
    """Test with actual corpus example."""
    print("\n=== Testing with Corpus Example ===\n")
    
    # Load Peirce man-mortal example
    corpus_path = "corpus/graphs/peirce_cp_4_394_man_mortal/peirce_cp_4_394_man_mortal.json"
    
    if not os.path.exists(corpus_path):
        print("6. Corpus example not found, skipping...")
        return
    
    print("6. Testing with Peirce man-mortal corpus example...")
    
    try:
        with open(corpus_path, 'r') as f:
            corpus_data = json.load(f)
        
        # Parse EGIF to EGI (using existing parser)
        from egif_parser_dau import parse_egif
        egi = parse_egif(corpus_data.get('egif', ''))
        
        correspondence = DauDiagramCorrespondence()
        
        # Convert to diagram
        diagram = correspondence.egi_to_diagram(egi)
        print("   ✓ Corpus EGI → Diagram conversion completed")
        
        # Validate diagram
        correspondence.validate_diagram_constraints(diagram)
        print("   ✓ Corpus-generated diagram passes validation")
        
        # Convert back
        reconstructed_egi = correspondence.diagram_to_egi(diagram)
        print("   ✓ Corpus Diagram → EGI conversion completed")
        
        print(f"   ✓ Corpus example processed successfully")
        print(f"      Vertices: {len(egi.V)}, Edges: {len(egi.E)}, Cuts: {len(egi.Cut)}")
        
    except Exception as e:
        print(f"   ⚠ Corpus example test failed: {e}")
        print("   (This may indicate corpus format differences)")


def main():
    """Run all correspondence tests."""
    print("🎯 Testing Dau-Compliant Diagram Correspondence Engine")
    print("=" * 60)
    
    test_simple_diagram_validation()
    test_dominating_nodes_constraint()
    test_bidirectional_reconstruction()
    test_with_corpus_example()
    
    print("\n" + "=" * 60)
    print("✅ Correspondence Engine Testing Complete")
    print("\nKey Validations:")
    print("• Dau's n-ary relation constraint")
    print("• Dau's dominating nodes constraint") 
    print("• Bidirectional EGI ↔ Diagram reconstruction")
    print("• Corpus example compatibility")


if __name__ == "__main__":
    main()
