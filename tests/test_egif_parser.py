"""
Comprehensive tests for the EGIF parser.
"""

from egif_parser import parse_egif
from egi_core import EGI


def test_basic_relation():
    """Test parsing a basic relation."""
    egif = "(phoenix *x)"
    egi = parse_egif(egif)
    
    assert len(egi.vertices) == 1
    assert len(egi.edges) == 1
    
    edge = list(egi.edges.values())[0]
    assert edge.relation_name == "phoenix"
    assert edge.arity == 1
    print("✓ Basic relation test passed")


def test_negation():
    """Test parsing negation."""
    egif = "~[ (phoenix *x) ]"
    egi = parse_egif(egif)
    
    assert len(egi.vertices) == 1
    assert len(egi.edges) == 1
    assert len(egi.cuts) == 1
    
    # Vertex should be in the cut context
    vertex = list(egi.vertices.values())[0]
    cut = list(egi.cuts.values())[0]
    assert vertex.context == cut
    print("✓ Negation test passed")


def test_multiple_relations():
    """Test parsing multiple relations with shared variables."""
    egif = "(male *x) (human x) (African x)"
    egi = parse_egif(egif)
    
    assert len(egi.vertices) == 1  # All relations share the same vertex
    assert len(egi.edges) == 3
    
    # All edges should connect to the same vertex
    vertex_id = list(egi.vertices.keys())[0]
    for edge in egi.edges.values():
        assert vertex_id in edge.incident_vertices
    print("✓ Multiple relations test passed")


def test_coreference_node():
    """Test parsing coreference nodes (identity)."""
    egif = "[*x *y] (P x) (Q y)"
    egi = parse_egif(egif)
    
    assert len(egi.vertices) == 2
    assert len(egi.edges) == 3  # 2 relations + 1 identity edge
    
    # Should have one identity edge
    identity_edges = [e for e in egi.edges.values() if e.is_identity]
    assert len(identity_edges) == 1
    print("✓ Coreference node test passed")


def test_scroll():
    """Test parsing scroll notation."""
    egif = "[If (thunder *x) [Then (lightning *y) ] ]"
    egi = parse_egif(egif)
    
    assert len(egi.vertices) == 2  # x and y are different vertices
    assert len(egi.edges) == 2
    assert len(egi.cuts) == 2  # If and Then cuts
    
    # Check nesting structure
    if_cut = None
    then_cut = None
    for cut in egi.cuts.values():
        if cut.parent == egi.sheet:
            if_cut = cut
        else:
            then_cut = cut
    
    assert if_cut is not None
    assert then_cut is not None
    assert then_cut.parent == if_cut
    print("✓ Scroll test passed")


def test_constants():
    """Test parsing constants."""
    egif = '(loves "Socrates" "Plato")'
    egi = parse_egif(egif)
    
    assert len(egi.vertices) == 2
    assert len(egi.edges) == 1
    
    # Both vertices should be constants
    for vertex in egi.vertices.values():
        assert vertex.is_constant
        assert vertex.constant_name in ["Socrates", "Plato"]
    print("✓ Constants test passed")


def test_complex_example():
    """Test a complex EGIF expression."""
    egif = "(man *x) ~[ (mortal x) ]"
    egi = parse_egif(egif)
    
    assert len(egi.vertices) == 1
    assert len(egi.edges) == 2
    assert len(egi.cuts) == 1
    
    # One edge should be in sheet, one in cut
    sheet_edges = [e for e in egi.edges.values() if e.context == egi.sheet]
    cut_edges = [e for e in egi.edges.values() if e.context != egi.sheet]
    
    assert len(sheet_edges) == 1
    assert len(cut_edges) == 1
    assert sheet_edges[0].relation_name == "man"
    assert cut_edges[0].relation_name == "mortal"
    print("✓ Complex example test passed")


def test_error_handling():
    """Test error handling for invalid EGIF."""
    try:
        parse_egif("(invalid")
        assert False, "Should have raised an error"
    except ValueError:
        print("✓ Error handling test passed")


def run_all_tests():
    """Run all tests."""
    print("Running EGIF parser tests...\n")
    
    test_basic_relation()
    test_negation()
    test_multiple_relations()
    test_coreference_node()
    test_scroll()
    test_constants()
    test_complex_example()
    test_error_handling()
    
    print("\n🎉 All tests passed!")


if __name__ == "__main__":
    run_all_tests()

