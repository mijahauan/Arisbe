"""
Comprehensive tests for EGI YAML serialization and deserialization.
"""

from egif_parser import parse_egif
from egi_yaml import serialize_egi_to_yaml, deserialize_egi_from_yaml
from egi_core import EGI


def test_basic_serialization():
    """Test basic YAML serialization and deserialization."""
    egif = "(phoenix *x)"
    egi = parse_egif(egif)
    
    # Serialize
    yaml_str = serialize_egi_to_yaml(egi)
    assert "phoenix" in yaml_str
    assert "vertices" in yaml_str
    assert "edges" in yaml_str
    
    # Deserialize
    egi2 = deserialize_egi_from_yaml(yaml_str)
    
    # Check structural equivalence
    assert len(egi.vertices) == len(egi2.vertices)
    assert len(egi.edges) == len(egi2.edges)
    assert len(egi.cuts) == len(egi2.cuts)
    
    print("✓ Basic serialization test passed")


def test_negation_serialization():
    """Test serialization with negation."""
    egif = "~[ (phoenix *x) ]"
    egi = parse_egif(egif)
    
    # Serialize
    yaml_str = serialize_egi_to_yaml(egi)
    
    # Deserialize
    egi2 = deserialize_egi_from_yaml(yaml_str)
    
    # Check structure
    assert len(egi.vertices) == len(egi2.vertices)
    assert len(egi.edges) == len(egi2.edges)
    assert len(egi.cuts) == len(egi2.cuts)
    
    # Check that cut exists and has correct properties
    cut = list(egi2.cuts.values())[0]
    assert cut.is_negative()
    assert cut.depth == 1
    
    print("✓ Negation serialization test passed")


def test_complex_structure():
    """Test serialization of complex structure."""
    egif = "(man *x) (human x) ~[ (mortal x) ]"
    egi = parse_egif(egif)
    
    # Serialize
    yaml_str = serialize_egi_to_yaml(egi)
    
    # Deserialize
    egi2 = deserialize_egi_from_yaml(yaml_str)
    
    # Check structure
    assert len(egi.vertices) == len(egi2.vertices) == 1
    assert len(egi.edges) == len(egi2.edges) == 3
    assert len(egi.cuts) == len(egi2.cuts) == 1
    
    # Check that vertex has correct degree
    vertex = list(egi2.vertices.values())[0]
    assert vertex.degree() == 3
    
    # Check relation names are preserved
    relation_names = {edge.relation_name for edge in egi2.edges.values()}
    assert relation_names == {"man", "human", "mortal"}
    
    print("✓ Complex structure test passed")


def test_constants_serialization():
    """Test serialization with constants."""
    egif = '(loves "Socrates" "Plato")'
    egi = parse_egif(egif)
    
    # Serialize
    yaml_str = serialize_egi_to_yaml(egi)
    
    # Deserialize
    egi2 = deserialize_egi_from_yaml(yaml_str)
    
    # Check structure
    assert len(egi2.vertices) == 2
    assert len(egi2.edges) == 1
    
    # Check that vertices are constants
    constant_names = {v.constant_name for v in egi2.vertices.values() if v.is_constant}
    assert constant_names == {"Socrates", "Plato"}
    
    print("✓ Constants serialization test passed")


def test_identity_edges():
    """Test serialization with identity edges."""
    egif = "[*x *y] (P x) (Q y)"
    egi = parse_egif(egif)
    
    # Serialize
    yaml_str = serialize_egi_to_yaml(egi)
    
    # Deserialize
    egi2 = deserialize_egi_from_yaml(yaml_str)
    
    # Check structure
    assert len(egi2.vertices) == 2
    assert len(egi2.edges) == 3  # P, Q, and identity edge
    
    # Check that identity edge exists
    identity_edges = [e for e in egi2.edges.values() if e.is_identity]
    assert len(identity_edges) == 1
    
    # Check ligatures are rebuilt
    assert len(egi2.ligature_manager.ligatures) > 0
    
    print("✓ Identity edges test passed")


def test_alphabet_preservation():
    """Test that alphabet is preserved."""
    egif = "(custom_relation *x *y *z)"
    egi = parse_egif(egif)
    
    # Serialize
    yaml_str = serialize_egi_to_yaml(egi)
    
    # Deserialize
    egi2 = deserialize_egi_from_yaml(yaml_str)
    
    # Check alphabet
    assert "custom_relation" in egi2.alphabet.relations
    assert egi2.alphabet.get_arity("custom_relation") == 3
    
    print("✓ Alphabet preservation test passed")


def test_context_hierarchy():
    """Test that context hierarchy is preserved."""
    egif = "~[ (A *x) ~[ (B x) ] ]"
    egi = parse_egif(egif)
    
    # Serialize
    yaml_str = serialize_egi_to_yaml(egi)
    
    # Deserialize
    egi2 = deserialize_egi_from_yaml(yaml_str)
    
    # Check context hierarchy
    assert len(egi2.cuts) == 2
    
    # Find cuts by depth
    depth1_cuts = [c for c in egi2.cuts.values() if c.depth == 1]
    depth2_cuts = [c for c in egi2.cuts.values() if c.depth == 2]
    
    assert len(depth1_cuts) == 1
    assert len(depth2_cuts) == 1
    
    # Check parent-child relationship
    depth1_cut = depth1_cuts[0]
    depth2_cut = depth2_cuts[0]
    
    assert depth2_cut.parent == depth1_cut
    assert depth2_cut.id in depth1_cut.children
    
    print("✓ Context hierarchy test passed")


def test_yaml_format():
    """Test that YAML format is well-formed and readable."""
    egif = "(test *x)"
    egi = parse_egif(egif)
    
    yaml_str = serialize_egi_to_yaml(egi)
    
    # Check that YAML contains expected sections
    assert "egi:" in yaml_str
    assert "metadata:" in yaml_str
    assert "alphabet:" in yaml_str
    assert "vertices:" in yaml_str
    assert "edges:" in yaml_str
    assert "sheet:" in yaml_str
    
    # Check metadata
    assert "version: '1.0'" in yaml_str
    assert "type: existential_graph_instance" in yaml_str
    
    print("✓ YAML format test passed")


def run_all_tests():
    """Run all YAML serialization tests."""
    print("Running EGI YAML serialization tests...\n")
    
    test_basic_serialization()
    test_negation_serialization()
    test_complex_structure()
    test_constants_serialization()
    test_identity_edges()
    test_alphabet_preservation()
    test_context_hierarchy()
    test_yaml_format()
    
    print("\n🎉 All YAML serialization tests passed!")


if __name__ == "__main__":
    run_all_tests()

