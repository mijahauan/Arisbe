"""
Comprehensive tests for the EGIF generator.
"""

from egif_parser import parse_egif
from egif_generator import generate_egif


def test_basic_generation():
    """Test basic EGIF generation."""
    egif = "(phoenix *x)"
    egi = parse_egif(egif)
    generated = generate_egif(egi)
    
    assert "phoenix" in generated
    assert "x" in generated
    print("✓ Basic generation test passed")


def test_negation_generation():
    """Test generation with negation."""
    egif = "~[ (phoenix *x) ]"
    egi = parse_egif(egif)
    generated = generate_egif(egi)
    
    assert "~[" in generated
    assert "phoenix" in generated
    print("✓ Negation generation test passed")


def test_multiple_relations():
    """Test generation with multiple relations."""
    egif = "(man *x) (human x) (African x)"
    egi = parse_egif(egif)
    generated = generate_egif(egi)
    
    assert "man" in generated
    assert "human" in generated
    assert "African" in generated
    print("✓ Multiple relations test passed")


def test_constants_generation():
    """Test generation with constants."""
    egif = '(loves "Socrates" "Plato")'
    egi = parse_egif(egif)
    generated = generate_egif(egi)
    
    assert "Socrates" in generated
    assert "Plato" in generated
    assert "loves" in generated
    print("✓ Constants generation test passed")


def test_identity_generation():
    """Test generation with identity edges."""
    egif = "[*x *y] (P x) (Q y)"
    egi = parse_egif(egif)
    generated = generate_egif(egi)
    
    # Should have P, Q relations and some form of identity
    assert "P" in generated
    assert "Q" in generated
    print("✓ Identity generation test passed")


def test_scroll_generation():
    """Test generation of scroll patterns."""
    egif = '[If (thunder *x) [Then (lightning *y) ] ]'
    egi = parse_egif(egif)
    generated = generate_egif(egi)
    
    assert "If" in generated
    assert "Then" in generated
    assert "thunder" in generated
    assert "lightning" in generated
    print("✓ Scroll generation test passed")


def test_round_trip_simple():
    """Test round-trip conversion for simple cases."""
    test_cases = [
        "(phoenix *x)",
        "~[ (phoenix *x) ]",
        '(loves "Socrates" "Plato")',
        '[If (thunder *x) [Then (lightning *y) ] ]'
    ]
    
    for egif in test_cases:
        egi = parse_egif(egif)
        generated = generate_egif(egi)
        egi2 = parse_egif(generated)
        
        # Check structural equivalence
        assert len(egi.vertices) == len(egi2.vertices)
        assert len(egi.edges) == len(egi2.edges)
        assert len(egi.cuts) == len(egi2.cuts)
    
    print("✓ Round-trip simple test passed")


def test_semantic_equivalence():
    """Test that generated EGIF is semantically equivalent."""
    egif = "(man *x) (human x)"
    egi = parse_egif(egif)
    generated = generate_egif(egi)
    egi2 = parse_egif(generated)
    
    # Check that both EGIs have same structure
    assert len(egi.vertices) == len(egi2.vertices) == 1
    assert len(egi.edges) == len(egi2.edges) == 2
    
    # Check that relations are preserved
    relation_names1 = {e.relation_name for e in egi.edges.values()}
    relation_names2 = {e.relation_name for e in egi2.edges.values()}
    assert relation_names1 == relation_names2 == {"man", "human"}
    
    print("✓ Semantic equivalence test passed")


def test_complex_nesting():
    """Test generation with complex nesting."""
    egif = "~[ (A *x) ~[ (B x) ] ]"
    egi = parse_egif(egif)
    generated = generate_egif(egi)
    egi2 = parse_egif(generated)
    
    # Check structure is preserved
    assert len(egi.cuts) == len(egi2.cuts) == 2
    assert len(egi.vertices) == len(egi2.vertices) == 1
    assert len(egi.edges) == len(egi2.edges) == 2
    
    print("✓ Complex nesting test passed")


def run_all_tests():
    """Run all EGIF generator tests."""
    print("Running EGIF generator tests...\n")
    
    test_basic_generation()
    test_negation_generation()
    test_multiple_relations()
    test_constants_generation()
    test_identity_generation()
    test_scroll_generation()
    test_round_trip_simple()
    test_semantic_equivalence()
    test_complex_nesting()
    
    print("\n🎉 All EGIF generator tests passed!")


if __name__ == "__main__":
    run_all_tests()

