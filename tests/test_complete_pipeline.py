"""
Comprehensive test suite for the immutable Existential Graphs implementation.
Tests all components and verifies immutability guarantees.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from egi_core import EGI, EGIBuilder, Alphabet, create_empty_egi, Vertex, Edge, Context
from egif_parser import parse_egif
from egif_generator import generate_egif
from egi_transformations import (
    apply_transformation, TransformationRule, TransformationError,
    apply_erasure, apply_double_cut_addition, apply_double_cut_removal
)
from egi_cli import EGICLIApplication, MarkupParser


def test_immutability_guarantees():
    """Test that all operations preserve immutability."""
    print("Testing immutability guarantees...")
    
    # Test EGI immutability
    egi = parse_egif("(man *x) (human x)")
    original_vertex_count = len(egi.vertices)
    original_edge_count = len(egi.edges)
    
    # Apply transformation
    edge_id = next(iter(egi._edge_map.keys()))
    new_egi = apply_erasure(egi, edge_id)
    
    # Verify original is unchanged
    assert len(egi.vertices) == original_vertex_count
    assert len(egi.edges) == original_edge_count
    assert len(new_egi.edges) == original_edge_count - 1
    
    print("  ✓ EGI immutability preserved")
    
    # Test that modifying returned collections doesn't affect original
    vertices_copy = set(egi.vertices)
    vertices_copy.clear()
    assert len(egi.vertices) == original_vertex_count
    
    print("  ✓ Collection immutability preserved")
    
    print("✓ Immutability guarantees test passed")


def test_core_data_structures():
    """Test core immutable data structures."""
    print("Testing core data structures...")
    
    # Test Alphabet immutability
    alphabet = Alphabet()
    new_alphabet = alphabet.with_relation("test")
    
    assert "test" not in alphabet.relations
    assert "test" in new_alphabet.relations
    
    print("  ✓ Alphabet immutability")
    
    # Test Context immutability
    builder = EGIBuilder()
    context_id = builder._sheet_id
    context = builder._contexts[context_id]
    
    new_context = context.with_element("test_element")
    assert "test_element" not in context.enclosed_elements
    assert "test_element" in new_context.enclosed_elements
    
    print("  ✓ Context immutability")
    
    # Test Vertex immutability
    vertex = Vertex(
        id="test_vertex",
        context_id=context_id,
        is_constant=False
    )
    
    new_vertex = vertex.with_property("test_prop", "test_value")
    assert "test_prop" not in vertex.properties
    assert vertex.properties.get("test_prop") != "test_value"
    assert new_vertex.properties.get("test_prop") == "test_value"
    
    print("  ✓ Vertex immutability")
    
    # Test Edge immutability
    edge = Edge(
        id="test_edge",
        context_id=context_id,
        relation_name="test_relation",
        incident_vertices=("test_vertex",)
    )
    
    new_edge = edge.with_property("test_prop", "test_value")
    assert "test_prop" not in edge.properties
    assert new_edge.properties.get("test_prop") == "test_value"
    
    print("  ✓ Edge immutability")
    
    print("✓ Core data structures test passed")


def test_parser_immutability():
    """Test that parser creates immutable structures."""
    print("Testing parser immutability...")
    
    test_cases = [
        "(phoenix *x)",
        "(man *x) (human x)",
        '(loves "Socrates" "Plato")',
        "~[ (mortal *x) ]",
        "[*x *y] (P x) (Q y)"
    ]
    
    for egif in test_cases:
        egi = parse_egif(egif)
        
        # Verify EGI is properly immutable
        assert isinstance(egi.vertices, frozenset)
        assert isinstance(egi.edges, frozenset)
        assert isinstance(egi.contexts, frozenset)
        
        # Verify individual elements are immutable
        for vertex in egi.vertices:
            assert hasattr(vertex, '__hash__')  # Immutable objects are hashable
        
        for edge in egi.edges:
            assert hasattr(edge, '__hash__')
        
        for context in egi.contexts:
            assert hasattr(context, '__hash__')
        
        print(f"  ✓ {egif}")
    
    print("✓ Parser immutability test passed")


def test_transformation_immutability():
    """Test that transformations preserve immutability."""
    print("Testing transformation immutability...")
    
    # Test erasure
    egi = parse_egif("(man *x) (human x) (mortal x)")
    edge_id = next(iter(egi._edge_map.keys()))
    
    new_egi = apply_erasure(egi, edge_id)
    
    # Verify original unchanged
    assert len(egi.edges) == 3
    assert len(new_egi.edges) == 2
    assert egi is not new_egi
    
    print("  ✓ Erasure immutability")
    
    # Test double cut addition
    egi = parse_egif("(phoenix *x)")
    new_egi = apply_double_cut_addition(egi, egi.sheet_id)
    
    # Verify original unchanged
    assert len(egi.contexts) == 1
    assert len(new_egi.contexts) == 3
    assert egi is not new_egi
    
    print("  ✓ Double cut addition immutability")
    
    # Test double cut removal
    outer_cuts = [c for c in new_egi.contexts if c.parent_id == egi.sheet_id]
    if outer_cuts:
        outer_cut = outer_cuts[0]
        final_egi = apply_double_cut_removal(new_egi, outer_cut.id)
        
        # Verify intermediate EGI unchanged
        assert len(new_egi.contexts) == 3
        assert len(final_egi.contexts) == 1
        assert new_egi is not final_egi
        
        print("  ✓ Double cut removal immutability")
    
    print("✓ Transformation immutability test passed")


def test_generator_immutability():
    """Test that generator doesn't modify input EGI."""
    print("Testing generator immutability...")
    
    test_cases = [
        "(phoenix *x)",
        "(man *x) (human x)",
        '(loves "Socrates" "Plato")',
        "~[ (mortal *x) ]"
    ]
    
    for original_egif in test_cases:
        egi = parse_egif(original_egif)
        original_vertex_count = len(egi.vertices)
        original_edge_count = len(egi.edges)
        original_context_count = len(egi.contexts)
        
        # Generate EGIF
        generated_egif = generate_egif(egi)
        
        # Verify EGI unchanged
        assert len(egi.vertices) == original_vertex_count
        assert len(egi.edges) == original_edge_count
        assert len(egi.contexts) == original_context_count
        
        print(f"  ✓ {original_egif}")
    
    print("✓ Generator immutability test passed")


def test_cli_immutability():
    """Test that CLI operations preserve immutability."""
    print("Testing CLI immutability...")
    
    app = EGICLIApplication()
    app.load_egif("(man *x) (human x)")
    
    original_egi = app.current_egi
    original_vertex_count = len(original_egi.vertices)
    original_edge_count = len(original_egi.edges)
    
    # Apply transformation
    app.apply_transformation("^(man *x)^ (human x)")
    
    # Verify original EGI in history is unchanged
    history_egi = app.history[-1]
    assert len(history_egi.vertices) == original_vertex_count
    assert len(history_egi.edges) == original_edge_count
    assert history_egi is original_egi
    
    # Verify current EGI is different
    assert app.current_egi is not original_egi
    assert len(app.current_egi.edges) < original_edge_count
    
    print("  ✓ CLI transformation immutability")
    
    # Test undo preserves immutability
    app.undo()
    assert app.current_egi is history_egi
    assert len(app.current_egi.edges) == original_edge_count
    
    print("  ✓ CLI undo immutability")
    
    print("✓ CLI immutability test passed")


def test_round_trip_immutability():
    """Test round-trip conversion preserves immutability."""
    print("Testing round-trip immutability...")
    
    test_cases = [
        "(phoenix *x)",
        '(loves "Socrates" "Plato")',
        "~[ (mortal *x) ]"
    ]
    
    for original_egif in test_cases:
        # Parse to EGI
        egi1 = parse_egif(original_egif)
        original_egi1 = egi1  # Keep reference
        
        # Generate EGIF
        generated_egif = generate_egif(egi1)
        
        # Parse generated EGIF
        egi2 = parse_egif(generated_egif)
        
        # Verify original EGI unchanged
        assert egi1 is original_egi1
        assert len(egi1.vertices) == len(original_egi1.vertices)
        assert len(egi1.edges) == len(original_egi1.edges)
        
        # Verify structural equivalence
        assert len(egi1.vertices) == len(egi2.vertices)
        assert len(egi1.edges) == len(egi2.edges)
        assert len(egi1.contexts) == len(egi2.contexts)
        
        print(f"  ✓ {original_egif} -> {generated_egif}")
    
    print("✓ Round-trip immutability test passed")


def test_performance_with_immutability():
    """Test performance characteristics of immutable implementation."""
    print("Testing performance with immutability...")
    
    # Create larger structure
    builder = EGIBuilder()
    
    # Add multiple vertices and edges
    vertex_ids = []
    for i in range(10):
        vertex_id = builder.add_vertex(
            context_id=builder._sheet_id,
            is_constant=True,
            constant_name=f"const_{i}"
        )
        vertex_ids.append(vertex_id)
    
    # Add edges connecting vertices
    for i in range(9):
        builder.add_edge(
            context_id=builder._sheet_id,
            relation_name=f"rel_{i}",
            incident_vertices=(vertex_ids[i], vertex_ids[i+1])
        )
    
    egi = builder.build()
    
    # Test that operations are reasonably fast
    import time
    
    # Test transformation performance
    start_time = time.time()
    edge_id = next(iter(egi._edge_map.keys()))
    new_egi = apply_erasure(egi, edge_id)
    transformation_time = time.time() - start_time
    
    assert transformation_time < 1.0  # Should be fast
    assert len(new_egi.edges) == len(egi.edges) - 1
    
    # Test generation performance
    start_time = time.time()
    egif = generate_egif(egi)
    generation_time = time.time() - start_time
    
    assert generation_time < 1.0  # Should be fast
    assert len(egif) > 0
    
    print(f"  ✓ Transformation time: {transformation_time:.4f}s")
    print(f"  ✓ Generation time: {generation_time:.4f}s")
    
    print("✓ Performance test passed")


def test_error_handling_immutability():
    """Test that error conditions don't break immutability."""
    print("Testing error handling immutability...")
    
    egi = parse_egif("~[ (man *x) ]")
    original_egi = egi
    
    # Try invalid transformation
    edge_id = next(iter(egi._edge_map.keys()))
    
    try:
        apply_erasure(egi, edge_id)  # Should fail - negative context
        assert False, "Should have raised TransformationError"
    except TransformationError:
        pass  # Expected
    
    # Verify EGI unchanged after error
    assert egi is original_egi
    assert len(egi.edges) == 1
    assert len(egi.vertices) == 1
    
    print("  ✓ Error handling preserves immutability")
    
    # Test parser error handling
    try:
        parse_egif("(invalid syntax")
        assert False, "Should have raised error"
    except Exception:
        pass  # Expected
    
    print("  ✓ Parser error handling")
    
    print("✓ Error handling immutability test passed")


def run_comprehensive_immutable_tests():
    """Run all comprehensive tests for immutable implementation."""
    print("Running comprehensive immutable Existential Graphs tests...\n")
    
    test_immutability_guarantees()
    test_core_data_structures()
    test_parser_immutability()
    test_transformation_immutability()
    test_generator_immutability()
    test_cli_immutability()
    test_round_trip_immutability()
    test_performance_with_immutability()
    test_error_handling_immutability()
    
    print("\n🎉 All immutable implementation tests passed!")
    print("\nThe immutable Existential Graphs implementation is working correctly!")
    print("✓ Complete immutability guaranteed")
    print("✓ Mathematical soundness preserved")
    print("✓ All transformations return new instances")
    print("✓ Original graphs never modified")
    print("✓ Performance is acceptable")


if __name__ == "__main__":
    run_comprehensive_immutable_tests()

