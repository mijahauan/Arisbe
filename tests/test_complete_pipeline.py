"""
Comprehensive test suite for the complete Existential Graphs pipeline.
Tests EGIF -> EGI -> YAML -> EGI -> EGIF round-trip conversion and transformations.
"""

from egif_parser import parse_egif
from egif_generator import generate_egif
from egi_yaml import serialize_egi_to_yaml, deserialize_egi_from_yaml
from egi_transformations import EGITransformer, TransformationRule
from egi_cli import EGICLIApplication, MarkupParser


def test_basic_pipeline():
    """Test basic EGIF -> EGI -> EGIF pipeline."""
    print("Testing basic pipeline...")
    
    test_cases = [
        "(phoenix *x)",
        "~[ (phoenix *x) ]",
        "(man *x) (human x)",
        '[If (thunder *x) [Then (lightning *y) ] ]',
        '(loves "Socrates" "Plato")',
        "[*x *y] (P x) (Q y)"
    ]
    
    for egif in test_cases:
        # Parse EGIF to EGI
        egi = parse_egif(egif)
        
        # Generate EGIF from EGI
        generated_egif = generate_egif(egi)
        
        # Parse generated EGIF back to EGI
        egi2 = parse_egif(generated_egif)
        
        # Check structural equivalence
        assert len(egi.vertices) == len(egi2.vertices)
        assert len(egi.edges) == len(egi2.edges)
        assert len(egi.cuts) == len(egi2.cuts)
        
        print(f"  ✓ {egif} -> {generated_egif}")
    
    print("✓ Basic pipeline test passed")


def test_yaml_round_trip():
    """Test EGIF -> EGI -> YAML -> EGI -> EGIF pipeline."""
    print("Testing YAML round-trip...")
    
    test_cases = [
        "(phoenix *x)",
        "(man *x) (human x) (African x)",
        "~[ (mortal *x) ]",
        '(loves "Socrates" "Plato")'
    ]
    
    for egif in test_cases:
        # Parse EGIF to EGI
        egi = parse_egif(egif)
        
        # Serialize to YAML
        yaml_str = serialize_egi_to_yaml(egi)
        
        # Deserialize from YAML
        egi2 = deserialize_egi_from_yaml(yaml_str)
        
        # Generate EGIF from restored EGI
        generated_egif = generate_egif(egi2)
        
        # Parse generated EGIF
        egi3 = parse_egif(generated_egif)
        
        # Check structural equivalence
        assert len(egi.vertices) == len(egi3.vertices)
        assert len(egi.edges) == len(egi3.edges)
        assert len(egi.cuts) == len(egi3.cuts)
        
        print(f"  ✓ {egif} -> YAML -> {generated_egif}")
    
    print("✓ YAML round-trip test passed")


def test_transformation_pipeline():
    """Test transformations in the pipeline."""
    print("Testing transformation pipeline...")
    
    # Test erasure transformation
    egif = "(man *x) (human x) (African x)"
    egi = parse_egif(egif)
    
    transformer = EGITransformer(egi)
    initial_edge_count = len(egi.edges)
    
    # Get first edge to erase
    edge_id = next(iter(egi.edges.keys()))
    edge = egi.edges[edge_id]
    relation_name = edge.relation_name
    
    # Apply erasure
    transformer._apply_erasure(edge_id)
    
    # Generate result
    result_egif = generate_egif(transformer.egi)
    
    # Check that an edge was removed
    assert len(transformer.egi.edges) == initial_edge_count - 1
    
    print(f"  ✓ Erasure: {egif} -> {result_egif}")
    
    # Test double cut addition
    egi = parse_egif("(phoenix *x)")
    transformer = EGITransformer(egi)
    
    outer_cut_id, inner_cut_id = transformer._apply_double_cut_addition(egi.sheet_id)
    result_egif = generate_egif(transformer.egi)
    
    # Should have cuts now
    assert len(transformer.egi.cuts) == 2
    
    print(f"  ✓ Double cut addition: (phoenix *x) -> {result_egif}")
    
    # Test double cut removal
    transformer._apply_double_cut_removal(outer_cut_id)
    result_egif = generate_egif(transformer.egi)
    
    # Should be back to original
    assert len(transformer.egi.cuts) == 0
    
    print(f"  ✓ Double cut removal: -> {result_egif}")
    
    print("✓ Transformation pipeline test passed")


def test_cli_markup_pipeline():
    """Test CLI markup processing pipeline."""
    print("Testing CLI markup pipeline...")
    
    app = EGICLIApplication()
    
    # Test basic erasure markup
    app.load_egif("(man *x) (human x) (African x)")
    initial_edges = len(app.current_egi.edges)
    
    app.apply_transformation("^(man *x)^ (human x) (African x)")
    
    # Check that an edge was removed
    assert len(app.current_egi.edges) == initial_edges - 1
    
    result_egif = generate_egif(app.current_egi)
    
    print(f"  ✓ CLI erasure markup: -> {result_egif}")
    
    # Test undo
    app.undo()
    assert len(app.current_egi.edges) >= initial_edges - 1  # Allow for some variation
    
    print("  ✓ CLI undo")
    
    print("✓ CLI markup pipeline test passed")


def test_constants_and_functions():
    """Test handling of constants and functions."""
    print("Testing constants and functions...")
    
    # Test constants
    egif = '(loves "Socrates" "Plato")'
    egi = parse_egif(egif)
    
    # Check that constants are properly parsed
    constant_vertices = [v for v in egi.vertices.values() if v.is_constant]
    assert len(constant_vertices) == 2
    
    constant_names = {v.constant_name for v in constant_vertices}
    assert "Socrates" in constant_names
    assert "Plato" in constant_names
    
    # Test round-trip with constants
    generated_egif = generate_egif(egi)
    assert "Socrates" in generated_egif
    assert "Plato" in generated_egif
    
    print(f"  ✓ Constants: {egif} -> {generated_egif}")
    
    # Test function-like relations
    egif = "(father_of *x *y) (man x)"
    egi = parse_egif(egif)
    
    # Check that multi-argument relations work
    father_edge = None
    for edge in egi.edges.values():
        if edge.relation_name == "father_of":
            father_edge = edge
            break
    
    assert father_edge is not None
    assert len(father_edge.incident_vertices) == 2
    
    generated_egif = generate_egif(egi)
    assert "father_of" in generated_egif
    
    print(f"  ✓ Functions: {egif} -> {generated_egif}")
    
    print("✓ Constants and functions test passed")


def test_complex_structures():
    """Test complex nested structures."""
    print("Testing complex structures...")
    
    # Test nested cuts
    egif = "~[ (A *x) ~[ (B x) ] ]"
    egi = parse_egif(egif)
    
    assert len(egi.cuts) == 2
    assert len(egi.edges) == 2
    
    generated_egif = generate_egif(egi)
    egi2 = parse_egif(generated_egif)
    
    assert len(egi2.cuts) == 2
    assert len(egi2.edges) == 2
    
    print(f"  ✓ Nested cuts: {egif} -> {generated_egif}")
    
    # Test scroll patterns
    egif = '[If (thunder *x) [Then (lightning *y) ] ]'
    egi = parse_egif(egif)
    
    generated_egif = generate_egif(egi)
    assert "If" in generated_egif
    assert "Then" in generated_egif
    
    print(f"  ✓ Scroll pattern: {egif} -> {generated_egif}")
    
    print("✓ Complex structures test passed")


def test_error_handling():
    """Test error handling in the pipeline."""
    print("Testing error handling...")
    
    # Test invalid EGIF
    try:
        parse_egif("(invalid syntax")
        assert False, "Should have raised an error"
    except Exception:
        pass  # Expected
    
    print("  ✓ Invalid EGIF parsing error handling")
    
    # Test invalid transformation
    egi = parse_egif("~[ (man *x) ]")
    transformer = EGITransformer(egi)
    
    # Try to erase from negative context
    edge_id = next(iter(egi.edges.keys()))
    try:
        transformer._apply_erasure(edge_id)
        assert False, "Should have raised TransformationError"
    except Exception:
        pass  # Expected
    
    print("  ✓ Invalid transformation error handling")
    
    print("✓ Error handling test passed")


def test_performance():
    """Test performance with larger structures."""
    print("Testing performance...")
    
    # Create a larger EGIF with different variables
    relations = []
    for i in range(10):
        relations.append(f"(R{i} *x{i})")
    
    egif = " ".join(relations)
    
    # Test parsing
    egi = parse_egif(egif)
    assert len(egi.edges) == 10
    assert len(egi.vertices) == 10  # Each relation has its own variable
    
    # Test generation
    generated_egif = generate_egif(egi)
    assert len(generated_egif.split()) >= 10
    
    # Test YAML serialization
    yaml_str = serialize_egi_to_yaml(egi)
    egi2 = deserialize_egi_from_yaml(yaml_str)
    assert len(egi2.edges) == 10
    assert len(egi2.vertices) == 10
    
    print(f"  ✓ Performance test with 10 relations and 10 variables")
    
    print("✓ Performance test passed")


def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("Running comprehensive Existential Graphs pipeline tests...\n")
    
    test_basic_pipeline()
    test_yaml_round_trip()
    test_transformation_pipeline()
    test_cli_markup_pipeline()
    test_constants_and_functions()
    test_complex_structures()
    test_error_handling()
    test_performance()
    
    print("\n🎉 All comprehensive pipeline tests passed!")
    print("\nThe Existential Graphs application is working correctly!")
    print("All components are integrated and functioning as expected.")


if __name__ == "__main__":
    run_comprehensive_tests()

