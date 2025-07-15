"""
Comprehensive round-trip tests for CLIF parser and generator.

These tests ensure that CLIF → EG → CLIF transformations preserve
semantic equivalence and structural integrity across all supported
logical constructs.
"""

import pytest
from hypothesis import given, strategies as st, assume

from src.clif_parser import CLIFParser
from src.clif_generator import CLIFGenerator, CLIFRoundTripValidator, CLIFGenerationOptions
from src.graph import EGGraph
from src.eg_types import Node, Edge, Ligature


class TestBasicRoundTrip:
    """Test round-trip for basic CLIF constructs."""
    
    def test_simple_predicate_roundtrip(self):
        """Test round-trip for simple predicates."""
        test_cases = [
            "(P)",
            "(P x)",
            "(P x y)",
            "(Q a b c)",
            "(loves john mary)"
        ]
        
        parser = CLIFParser()
        generator = CLIFGenerator()
        
        for clif_source in test_cases:
            # Parse CLIF to EG
            parse_result = parser.parse(clif_source)
            assert parse_result.graph is not None, f"Failed to parse: {clif_source}"
            assert len(parse_result.errors) == 0, f"Parse errors for: {clif_source}"
            
            # Generate CLIF from EG
            gen_result = generator.generate(parse_result.graph)
            
            # Parse the generated CLIF again
            reparse_result = parser.parse(gen_result.clif_text)
            assert reparse_result.graph is not None, f"Failed to reparse: {gen_result.clif_text}"
            
            # Basic structural equivalence
            original_stats = self._get_graph_stats(parse_result.graph)
            regenerated_stats = self._get_graph_stats(reparse_result.graph)
            
            # Should have same number of predicates
            assert original_stats['predicate_count'] == regenerated_stats['predicate_count'], \
                f"Predicate count mismatch for {clif_source}: {original_stats} vs {regenerated_stats}"
    
    def test_equality_roundtrip(self):
        """Test round-trip for equality statements."""
        test_cases = [
            "(= x y)",
            "(= a b)",
            "(= john mary)"
        ]
        
        parser = CLIFParser()
        generator = CLIFGenerator()
        
        for clif_source in test_cases:
            parse_result = parser.parse(clif_source)
            assert parse_result.graph is not None
            assert len(parse_result.errors) == 0
            
            # Should have created a ligature
            assert len(parse_result.graph.ligatures) == 1
            
            gen_result = generator.generate(parse_result.graph)
            reparse_result = parser.parse(gen_result.clif_text)
            
            # Should preserve ligature
            assert len(reparse_result.graph.ligatures) == 1
    
    def test_conjunction_roundtrip(self):
        """Test round-trip for conjunctions."""
        test_cases = [
            "(and (P x) (Q y))",
            "(and (P) (Q) (R))",
            "(and (loves john mary) (friend mary bob))"
        ]
        
        parser = CLIFParser()
        generator = CLIFGenerator()
        
        for clif_source in test_cases:
            parse_result = parser.parse(clif_source)
            assert parse_result.graph is not None
            assert len(parse_result.errors) == 0
            
            gen_result = generator.generate(parse_result.graph)
            reparse_result = parser.parse(gen_result.clif_text)
            assert reparse_result.graph is not None
            
            # Should preserve predicate count
            original_preds = self._count_predicates(parse_result.graph)
            regenerated_preds = self._count_predicates(reparse_result.graph)
            assert original_preds == regenerated_preds
    
    def test_disjunction_roundtrip(self):
        """Test round-trip for disjunctions."""
        test_cases = [
            "(or (P x) (Q y))",
            "(or (P) (Q) (R))"
        ]
        
        parser = CLIFParser()
        generator = CLIFGenerator()
        
        for clif_source in test_cases:
            parse_result = parser.parse(clif_source)
            assert parse_result.graph is not None
            assert len(parse_result.errors) == 0
            
            gen_result = generator.generate(parse_result.graph)
            reparse_result = parser.parse(gen_result.clif_text)
            assert reparse_result.graph is not None
    
    def test_negation_roundtrip(self):
        """Test round-trip for negations."""
        test_cases = [
            "(not (P x))",
            "(not (Q))",
            "(not (and (P) (Q)))"
        ]
        
        parser = CLIFParser()
        generator = CLIFGenerator()
        
        for clif_source in test_cases:
            parse_result = parser.parse(clif_source)
            assert parse_result.graph is not None
            assert len(parse_result.errors) == 0
            
            gen_result = generator.generate(parse_result.graph)
            reparse_result = parser.parse(gen_result.clif_text)
            assert reparse_result.graph is not None
    
    def test_implication_roundtrip(self):
        """Test round-trip for implications."""
        test_cases = [
            "(if (P x) (Q x))",
            "(if (human x) (mortal x))",
            "(if (and (P x) (Q x)) (R x))"
        ]
        
        parser = CLIFParser()
        generator = CLIFGenerator()
        
        for clif_source in test_cases:
            parse_result = parser.parse(clif_source)
            assert parse_result.graph is not None
            assert len(parse_result.errors) == 0
            
            gen_result = generator.generate(parse_result.graph)
            reparse_result = parser.parse(gen_result.clif_text)
            assert reparse_result.graph is not None


class TestQuantificationRoundTrip:
    """Test round-trip for quantified statements."""
    
    def test_universal_quantification_roundtrip(self):
        """Test round-trip for universal quantification."""
        test_cases = [
            "(forall (x) (P x))",
            "(forall (x y) (R x y))",
            "(forall (x) (if (human x) (mortal x)))"
        ]
        
        parser = CLIFParser()
        generator = CLIFGenerator(CLIFGenerationOptions(use_pattern_recognition=True))
        
        for clif_source in test_cases:
            print(f"\nTesting: {clif_source}")
            
            # Parse original
            parse_result = parser.parse(clif_source)
            assert parse_result.graph is not None, f"Failed to parse: {clif_source}"
            assert len(parse_result.errors) == 0, f"Parse errors: {parse_result.errors}"
            
            print(f"Original graph: {parse_result.graph}")
            
            # Generate CLIF with pattern recognition
            gen_result = generator.generate(parse_result.graph)
            print(f"Generated CLIF: {gen_result.clif_text}")
            print(f"Patterns used: {len(gen_result.patterns_used)}")
            
            # Check if pattern recognition worked
            if len(gen_result.patterns_used) > 0:
                # Should contain 'forall' if pattern recognition worked
                assert 'forall' in gen_result.clif_text.lower(), \
                    f"Pattern recognition failed for: {clif_source}"
            
            # Parse generated CLIF
            reparse_result = parser.parse(gen_result.clif_text)
            assert reparse_result.graph is not None, \
                f"Failed to reparse generated CLIF: {gen_result.clif_text}"
    
    def test_existential_quantification_roundtrip(self):
        """Test round-trip for existential quantification."""
        test_cases = [
            "(exists (x) (P x))",
            "(exists (x y) (R x y))",
            "(exists (x) (and (P x) (Q x)))"
        ]
        
        parser = CLIFParser()
        generator = CLIFGenerator(CLIFGenerationOptions(use_pattern_recognition=True))
        
        for clif_source in test_cases:
            parse_result = parser.parse(clif_source)
            assert parse_result.graph is not None
            assert len(parse_result.errors) == 0
            
            gen_result = generator.generate(parse_result.graph)
            reparse_result = parser.parse(gen_result.clif_text)
            assert reparse_result.graph is not None


class TestComplexRoundTrip:
    """Test round-trip for complex nested structures."""
    
    def test_nested_quantification_roundtrip(self):
        """Test round-trip for nested quantification."""
        test_cases = [
            "(forall (x) (exists (y) (R x y)))",
            "(exists (x) (forall (y) (if (P y) (Q x y))))",
            "(forall (x) (if (P x) (exists (y) (R x y))))"
        ]
        
        parser = CLIFParser()
        generator = CLIFGenerator(CLIFGenerationOptions(use_pattern_recognition=True))
        
        for clif_source in test_cases:
            parse_result = parser.parse(clif_source)
            assert parse_result.graph is not None
            assert len(parse_result.errors) == 0
            
            gen_result = generator.generate(parse_result.graph)
            reparse_result = parser.parse(gen_result.clif_text)
            assert reparse_result.graph is not None
    
    def test_complex_logical_combinations_roundtrip(self):
        """Test round-trip for complex logical combinations."""
        test_cases = [
            "(and (forall (x) (P x)) (exists (y) (Q y)))",
            "(or (not (P x)) (and (Q x) (R x)))",
            "(if (and (P x) (Q x)) (or (R x) (S x)))"
        ]
        
        parser = CLIFParser()
        generator = CLIFGenerator(CLIFGenerationOptions(use_pattern_recognition=True))
        
        for clif_source in test_cases:
            parse_result = parser.parse(clif_source)
            assert parse_result.graph is not None
            assert len(parse_result.errors) == 0
            
            gen_result = generator.generate(parse_result.graph)
            reparse_result = parser.parse(gen_result.clif_text)
            assert reparse_result.graph is not None


class TestRoundTripWithComments:
    """Test round-trip preservation of comments and metadata."""
    
    def test_comment_preservation(self):
        """Test that comments are preserved through round-trip."""
        test_cases = [
            "/* Simple predicate */ (P x)",
            "(P x) // End-of-line comment",
            """/* Multi-line
               comment */ (P x)""",
            "/* Comment 1 */ (P x) /* Comment 2 */"
        ]
        
        parser = CLIFParser()
        generator = CLIFGenerator(CLIFGenerationOptions(preserve_comments=True))
        
        for clif_source in test_cases:
            parse_result = parser.parse(clif_source)
            assert parse_result.graph is not None
            assert len(parse_result.comments) > 0, f"No comments extracted from: {clif_source}"
            
            gen_result = generator.generate(
                parse_result.graph, 
                comments=parse_result.comments
            )
            
            # Comments should be preserved in generated CLIF
            for comment in parse_result.comments:
                # Extract comment text (remove /* */ or //)
                comment_text = comment.strip()
                if comment_text.startswith('/*'):
                    comment_text = comment_text[2:-2].strip()
                elif comment_text.startswith('//'):
                    comment_text = comment_text[2:].strip()
                
                # Normalize whitespace for comparison
                normalized_comment = ' '.join(comment_text.split())
                normalized_generated = ' '.join(gen_result.clif_text.split())
                
                assert normalized_comment in normalized_generated, \
                    f"Comment not preserved: {normalized_comment}"
    
    def test_import_preservation(self):
        """Test that import statements are preserved."""
        test_cases = [
            '(cl:imports "http://example.com/ontology") (P x)',
            '(cl:imports "http://test.org/logic") (forall (x) (P x))'
        ]
        
        parser = CLIFParser()
        generator = CLIFGenerator()
        
        for clif_source in test_cases:
            parse_result = parser.parse(clif_source)
            assert parse_result.graph is not None
            assert len(parse_result.imports) > 0
            
            gen_result = generator.generate(
                parse_result.graph,
                imports=parse_result.imports
            )
            
            # Imports should be preserved
            for import_uri in parse_result.imports:
                assert import_uri in gen_result.clif_text


class TestRoundTripValidation:
    """Test the round-trip validation framework."""
    
    def test_round_trip_validator(self):
        """Test the CLIFRoundTripValidator."""
        # Create a simple graph
        graph = EGGraph.create_empty()
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        arg_node = Node.create(node_type='term', properties={'value': 'x'})
        
        graph = graph.add_node(pred_node)
        graph = graph.add_node(arg_node)
        
        edge = Edge.create(edge_type='predication', nodes={pred_node.id, arg_node.id})
        graph = graph.add_edge(edge)
        
        # Validate round-trip
        validator = CLIFRoundTripValidator()
        result = validator.validate_round_trip(graph)
        
        assert 'round_trip_successful' in result
        assert 'semantic_equivalence' in result
        assert 'original_clif' in result
        assert 'generation_metadata' in result
        
        # Should be successful for simple case
        assert result['round_trip_successful'] == True
    
    def test_semantic_equivalence_detection(self):
        """Test semantic equivalence detection."""
        # Create two equivalent graphs
        graph1 = EGGraph.create_empty()
        graph2 = EGGraph.create_empty()
        
        # Add same predicate to both
        for graph in [graph1, graph2]:
            pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
            graph = graph.add_node(pred_node)
        
        validator = CLIFRoundTripValidator()
        
        # Compare graphs
        equivalence = validator._check_semantic_equivalence(graph1, graph2)
        assert equivalence['equivalent'] == True
        assert len(equivalence['differences']) == 0


class TestRoundTripPropertyBased:
    """Property-based tests for round-trip validation."""
    
    @given(st.text(alphabet='PQRABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=3))
    def test_predicate_name_roundtrip(self, predicate_name):
        """Test that predicate names survive round-trip."""
        clif_source = f"({predicate_name} x)"
        
        parser = CLIFParser()
        generator = CLIFGenerator()
        
        parse_result = parser.parse(clif_source)
        assume(parse_result.graph is not None)
        assume(len(parse_result.errors) == 0)
        
        gen_result = generator.generate(parse_result.graph)
        
        # Predicate name should appear in generated CLIF
        assert predicate_name in gen_result.clif_text
    
    @given(st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=3), 
                   min_size=1, max_size=3))
    def test_multiple_arguments_roundtrip(self, arg_names):
        """Test predicates with multiple arguments."""
        args_str = ' '.join(arg_names)
        clif_source = f"(P {args_str})"
        
        parser = CLIFParser()
        generator = CLIFGenerator()
        
        parse_result = parser.parse(clif_source)
        assume(parse_result.graph is not None)
        assume(len(parse_result.errors) == 0)
        
        gen_result = generator.generate(parse_result.graph)
        reparse_result = parser.parse(gen_result.clif_text)
        
        # Should successfully reparse
        assert reparse_result.graph is not None
        assert len(reparse_result.errors) == 0


class TestRoundTripEdgeCases:
    """Test round-trip for edge cases and error conditions."""
    
    def test_empty_input_roundtrip(self):
        """Test round-trip for empty input."""
        parser = CLIFParser()
        generator = CLIFGenerator()
        
        parse_result = parser.parse("")
        assert parse_result.graph is not None  # Should create empty graph
        
        gen_result = generator.generate(parse_result.graph)
        # Should handle empty graph gracefully
        assert gen_result.clif_text is not None
    
    def test_malformed_input_handling(self):
        """Test handling of malformed input."""
        malformed_cases = [
            "(P x",  # Missing closing paren
            "P x)",  # Missing opening paren
            "()",    # Empty expression
            "((P x))" # Extra parens
        ]
        
        parser = CLIFParser()
        
        for clif_source in malformed_cases:
            parse_result = parser.parse(clif_source)
            # Should not crash, may have errors
            assert parse_result is not None
    
    def test_very_deep_nesting_roundtrip(self):
        """Test round-trip for deeply nested structures."""
        # Create deeply nested structure
        nested_clif = "(P x)"
        for i in range(5):
            nested_clif = f"(not {nested_clif})"
        
        parser = CLIFParser()
        generator = CLIFGenerator()
        
        parse_result = parser.parse(nested_clif)
        if parse_result.graph is not None and len(parse_result.errors) == 0:
            gen_result = generator.generate(parse_result.graph)
            reparse_result = parser.parse(gen_result.clif_text)
            assert reparse_result.graph is not None


# Helper methods
def _get_graph_stats(graph: EGGraph) -> dict:
    """Get basic statistics about a graph."""
    return {
        'node_count': len(graph.nodes),
        'edge_count': len(graph.edges),
        'ligature_count': len(graph.ligatures),
        'context_count': len(graph.context_manager.contexts),
        'predicate_count': sum(1 for node in graph.nodes.values() 
                             if node.node_type == 'predicate'),
        'term_count': sum(1 for node in graph.nodes.values() 
                        if node.node_type == 'term')
    }

def _count_predicates(graph: EGGraph) -> int:
    """Count predicate nodes in a graph."""
    return sum(1 for node in graph.nodes.values() if node.node_type == 'predicate')


# Add helper methods to test classes
TestBasicRoundTrip._get_graph_stats = staticmethod(_get_graph_stats)
TestBasicRoundTrip._count_predicates = staticmethod(_count_predicates)

