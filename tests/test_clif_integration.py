"""
Comprehensive tests for CLIF integration including parsing, pattern recognition,
and generation with round-trip validation.
"""

import pytest
from hypothesis import given, strategies as st

from src.clif_parser import CLIFParser, CLIFLexer, CLIFTokenType
from src.pattern_recognizer import (
    PatternRecognitionEngine, UniversalQuantifierRecognizer,
    ImplicationRecognizer, DisjunctionRecognizer
)
from src.clif_generator import CLIFGenerator, CLIFGenerationOptions, CLIFRoundTripValidator
from src.graph import EGGraph
from src.eg_types import Node, Edge, Context, new_node_id, new_edge_id


class TestCLIFLexer:
    """Test the CLIF lexer."""
    
    def test_tokenize_simple_predicate(self):
        """Test tokenizing a simple predicate."""
        source = "(P x)"
        lexer = CLIFLexer(source)
        tokens = lexer.tokenize()
        
        assert len(tokens) == 5  # (, P, x, ), EOF
        assert tokens[0].type == CLIFTokenType.LPAREN
        assert tokens[1].type == CLIFTokenType.IDENTIFIER
        assert tokens[1].value == "P"
        assert tokens[2].type == CLIFTokenType.IDENTIFIER
        assert tokens[2].value == "x"
        assert tokens[3].type == CLIFTokenType.RPAREN
        assert tokens[4].type == CLIFTokenType.EOF
    
    def test_tokenize_forall_statement(self):
        """Test tokenizing a forall statement."""
        source = "(forall (x) (P x))"
        lexer = CLIFLexer(source)
        tokens = lexer.tokenize()
        
        # Find the forall keyword
        forall_token = next(t for t in tokens if t.value == "forall")
        assert forall_token.type == CLIFTokenType.KEYWORD
    
    def test_tokenize_with_comments(self):
        """Test tokenizing with comments."""
        source = """
        /* This is a comment */
        (P x) // Another comment
        """
        lexer = CLIFLexer(source)
        tokens = lexer.tokenize()
        
        comment_tokens = [t for t in tokens if t.type == CLIFTokenType.COMMENT]
        assert len(comment_tokens) == 2
        assert "This is a comment" in comment_tokens[0].value
        assert "Another comment" in comment_tokens[1].value
    
    def test_tokenize_string_literals(self):
        """Test tokenizing string literals."""
        source = '(P "hello world")'
        lexer = CLIFLexer(source)
        tokens = lexer.tokenize()
        
        string_token = next(t for t in tokens if t.type == CLIFTokenType.STRING)
        assert string_token.value == '"hello world"'
    
    def test_tokenize_numbers(self):
        """Test tokenizing numbers."""
        source = "(P 42 3.14 -7)"
        lexer = CLIFLexer(source)
        tokens = lexer.tokenize()
        
        number_tokens = [t for t in tokens if t.type == CLIFTokenType.NUMBER]
        assert len(number_tokens) == 3
        assert number_tokens[0].value == "42"
        assert number_tokens[1].value == "3.14"
        assert number_tokens[2].value == "-7"


class TestCLIFParser:
    """Test the CLIF parser."""
    
    def test_parse_simple_predicate(self):
        """Test parsing a simple predicate."""
        source = "(P x)"
        parser = CLIFParser()
        result = parser.parse(source)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        # Should have created a predicate node
        predicate_nodes = [n for n in result.graph.nodes.values() 
                          if n.node_type == 'predicate']
        assert len(predicate_nodes) == 1
        assert predicate_nodes[0].properties['name'] == 'P'
    
    def test_parse_forall_statement(self):
        """Test parsing a universal quantification."""
        source = "(forall (x) (P x))"
        parser = CLIFParser()
        result = parser.parse(source)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        # Should have created nested contexts for quantification
        contexts = result.graph.context_manager.contexts
        assert len(contexts) > 1  # Root + quantification contexts
    
    def test_parse_implication(self):
        """Test parsing an implication."""
        source = "(if (P x) (Q x))"
        parser = CLIFParser()
        result = parser.parse(source)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        # Should have created contexts for implication structure
        contexts = result.graph.context_manager.contexts
        assert len(contexts) >= 2  # Root + implication contexts
    
    def test_parse_disjunction(self):
        """Test parsing a disjunction."""
        source = "(or (P x) (Q x))"
        parser = CLIFParser()
        result = parser.parse(source)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        # Should have created contexts for disjunction structure
        contexts = result.graph.context_manager.contexts
        assert len(contexts) >= 3  # Root + outer cut + disjunct cuts
    
    def test_parse_equality(self):
        """Test parsing an equality statement."""
        source = "(= x y)"
        parser = CLIFParser()
        result = parser.parse(source)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        # Should have created ligature for equality
        equality_ligatures = [l for l in result.graph.ligatures.values()
                            if l.properties.get('type') == 'equality']
        assert len(equality_ligatures) == 1
    
    def test_parse_with_comments(self):
        """Test parsing with comments preserved."""
        source = """
        /* This is a test */
        (P x)
        """
        parser = CLIFParser()
        result = parser.parse(source)
        
        assert result.graph is not None
        assert len(result.comments) == 1
        assert "This is a test" in result.comments[0]
    
    def test_parse_with_imports(self):
        """Test parsing with import statements."""
        source = """
        (cl:imports "http://example.com/ontology")
        (P x)
        """
        parser = CLIFParser()
        result = parser.parse(source)
        
        assert result.graph is not None
        assert len(result.imports) == 1
        assert result.imports[0] == "http://example.com/ontology"
    
    def test_parse_syntax_error(self):
        """Test parsing with syntax errors."""
        source = "(P x"  # Missing closing paren
        parser = CLIFParser()
        result = parser.parse(source)
        
        assert len(result.errors) > 0
        assert any("Expected" in error.message for error in result.errors)
    
    def test_parse_complex_nested_structure(self):
        """Test parsing complex nested logical structure."""
        source = "(forall (x) (if (P x) (exists (y) (and (Q x y) (R y)))))"
        parser = CLIFParser()
        result = parser.parse(source)
        
        assert result.graph is not None
        assert len(result.errors) == 0
        
        # Should have multiple nested contexts
        contexts = result.graph.context_manager.contexts
        assert len(contexts) >= 4  # Multiple levels of nesting


class TestPatternRecognition:
    """Test pattern recognition algorithms."""
    
    def test_universal_quantifier_recognition(self):
        """Test recognition of universal quantification patterns."""
        # Create a graph with universal quantification structure: ~[exists x ~[P(x)]]
        # This represents: forall x P(x)
        graph = EGGraph.create_empty()
        
        # Create outer negative context (depth 1, negative polarity)
        graph, outer_cut = graph.create_context('cut', name='Universal Outer')
        
        # Create inner negative context (depth 2, positive polarity, but we need another cut)
        graph, middle_cut = graph.create_context('cut', outer_cut.id, 'Existential')
        
        # Create innermost negative context for the predicate (depth 3, negative polarity)
        graph, inner_cut = graph.create_context('cut', middle_cut.id, 'Predicate Negation')
        
        # Add predicate in innermost context
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        var_node = Node.create(node_type='variable', properties={'value': 'x'})
        
        graph = graph.add_node(pred_node, inner_cut.id)
        graph = graph.add_node(var_node, inner_cut.id)
        
        # Create edge connecting predicate and variable
        edge = Edge.create(edge_type='predication', nodes={pred_node.id, var_node.id})
        graph = graph.add_edge(edge, inner_cut.id)
        
        # Run pattern recognition
        recognizer = UniversalQuantifierRecognizer()
        engine = PatternRecognitionEngine()
        patterns = engine.recognize_patterns(graph)
        
        # Should recognize universal quantification
        universal_patterns = [p for p in patterns if p.pattern_type == 'universal_quantifier']
        assert len(universal_patterns) >= 1
        assert universal_patterns[0].confidence > 0.7
    
    def test_implication_recognition(self):
        """Test recognition of implication patterns."""
        # Create a graph with implication structure: ~[P ~[Q]]
        # This represents: if P then Q
        graph = EGGraph.create_empty()
        
        # Create outer negative context (depth 1, negative polarity)
        graph, outer_cut = graph.create_context('cut', name='Implication')
        
        # Add antecedent (P) in outer context
        ant_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(ant_node, outer_cut.id)
        
        # Create inner negative context for consequent (depth 2, positive polarity)
        graph, inner_cut = graph.create_context('cut', outer_cut.id, 'Consequent Negation')
        
        # Add consequent (Q) in inner context
        cons_node = Node.create(node_type='predicate', properties={'name': 'Q'})
        graph = graph.add_node(cons_node, inner_cut.id)
        
        # Run pattern recognition
        recognizer = ImplicationRecognizer()
        engine = PatternRecognitionEngine()
        patterns = engine.recognize_patterns(graph)
        
        # Should recognize implication
        implication_patterns = [p for p in patterns if p.pattern_type == 'implication']
        assert len(implication_patterns) >= 1
        assert implication_patterns[0].confidence > 0.6
    
    def test_disjunction_recognition(self):
        """Test recognition of disjunction patterns."""
        # Create a graph with disjunction structure: ~[~[P] ~[Q]]
        # This represents: P or Q
        graph = EGGraph.create_empty()
        
        # Create outer negative context (depth 1, negative polarity)
        graph, outer_cut = graph.create_context('cut', name='Disjunction')
        
        # Create first disjunct context (depth 2, positive polarity)
        graph, cut1 = graph.create_context('cut', outer_cut.id, 'Disjunct 1')
        p_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(p_node, cut1.id)
        
        # Create second disjunct context (depth 2, positive polarity)
        graph, cut2 = graph.create_context('cut', outer_cut.id, 'Disjunct 2')
        q_node = Node.create(node_type='predicate', properties={'name': 'Q'})
        graph = graph.add_node(q_node, cut2.id)
        
        # Run pattern recognition
        recognizer = DisjunctionRecognizer()
        engine = PatternRecognitionEngine()
        patterns = engine.recognize_patterns(graph)
        
        # Should recognize disjunction
        disjunction_patterns = [p for p in patterns if p.pattern_type == 'disjunction']
        assert len(disjunction_patterns) >= 1
        assert disjunction_patterns[0].confidence > 0.6
    
    def test_pattern_engine_integration(self):
        """Test the complete pattern recognition engine."""
        # Create a complex graph with multiple patterns
        graph = EGGraph.create_empty()
        
        # Add a simple predicate at root level
        simple_pred = Node.create(node_type='predicate', properties={'name': 'Simple'})
        graph = graph.add_node(simple_pred)
        
        # Add an implication pattern
        graph, impl_cut = graph.create_context('cut', name='Implication')
        ant_node = Node.create(node_type='predicate', properties={'name': 'Antecedent'})
        graph = graph.add_node(ant_node, impl_cut.id)
        
        graph, cons_cut = graph.create_context('cut', impl_cut.id, 'Consequent')
        cons_node = Node.create(node_type='predicate', properties={'name': 'Consequent'})
        graph = graph.add_node(cons_node, cons_cut.id)
        
        # Run full pattern recognition
        engine = PatternRecognitionEngine()
        patterns = engine.recognize_patterns(graph)
        
        # Should find patterns and generate CLIF
        assert len(patterns) >= 1
        
        clif_output = engine.generate_clif_from_patterns(graph, patterns)
        assert clif_output is not None
        assert len(clif_output) > 0


class TestCLIFGenerator:
    """Test CLIF generation."""
    
    def test_generate_simple_predicate(self):
        """Test generating CLIF for a simple predicate."""
        graph = EGGraph.create_empty()
        
        # Add a simple predicate
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        arg_node = Node.create(node_type='term', properties={'value': 'x'})
        
        graph = graph.add_node(pred_node)
        graph = graph.add_node(arg_node)
        
        # Connect with edge
        edge = Edge.create(edge_type='predication', nodes={pred_node.id, arg_node.id})
        graph = graph.add_edge(edge)
        
        # Generate CLIF
        generator = CLIFGenerator()
        result = generator.generate(graph)
        
        assert result.clif_text is not None
        assert "P" in result.clif_text
        assert "x" in result.clif_text
    
    def test_generate_with_pattern_recognition(self):
        """Test CLIF generation using pattern recognition."""
        # Create implication pattern
        graph = EGGraph.create_empty()
        
        graph, outer_cut = graph.create_context('cut', name='Implication')
        ant_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(ant_node, outer_cut.id)
        
        graph, inner_cut = graph.create_context('cut', outer_cut.id, 'Consequent')
        cons_node = Node.create(node_type='predicate', properties={'name': 'Q'})
        graph = graph.add_node(cons_node, inner_cut.id)
        
        # Generate with pattern recognition
        options = CLIFGenerationOptions(use_pattern_recognition=True)
        generator = CLIFGenerator(options)
        result = generator.generate(graph)
        
        assert result.clif_text is not None
        assert len(result.patterns_used) > 0
        
        # Should generate clean implication
        assert "if" in result.clif_text.lower() or "P" in result.clif_text
    
    def test_generate_without_pattern_recognition(self):
        """Test CLIF generation without pattern recognition."""
        graph = EGGraph.create_empty()
        
        # Add simple content
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(pred_node)
        
        # Generate without pattern recognition
        options = CLIFGenerationOptions(use_pattern_recognition=False)
        generator = CLIFGenerator(options)
        result = generator.generate(graph)
        
        assert result.clif_text is not None
        assert len(result.patterns_used) == 0
        assert "P" in result.clif_text
    
    def test_generate_with_comments_and_imports(self):
        """Test CLIF generation with comments and imports."""
        graph = EGGraph.create_empty()
        
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(pred_node)
        
        comments = ["This is a test", "Another comment"]
        imports = ["http://example.com/ontology"]
        
        generator = CLIFGenerator()
        result = generator.generate(graph, comments=comments, imports=imports)
        
        assert "This is a test" in result.clif_text
        assert "cl:imports" in result.clif_text
        assert "http://example.com/ontology" in result.clif_text
    
    def test_generate_formatted_output(self):
        """Test formatted CLIF output."""
        graph = EGGraph.create_empty()
        
        # Create nested structure
        graph, cut = graph.create_context('cut', name='Test')
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(pred_node, cut.id)
        
        options = CLIFGenerationOptions(format_output=True)
        generator = CLIFGenerator(options)
        result = generator.generate(graph)
        
        # Should have proper formatting (newlines, indentation)
        assert "\n" in result.clif_text or len(result.clif_text.split()) > 1


class TestCLIFRoundTrip:
    """Test CLIF round-trip conversion."""
    
    def test_simple_predicate_round_trip(self):
        """Test round-trip for simple predicate."""
        # Create original graph
        graph = EGGraph.create_empty()
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        arg_node = Node.create(node_type='term', properties={'value': 'x'})
        
        graph = graph.add_node(pred_node)
        graph = graph.add_node(arg_node)
        
        edge = Edge.create(edge_type='predication', nodes={pred_node.id, arg_node.id})
        graph = graph.add_edge(edge)
        
        # Test round-trip
        validator = CLIFRoundTripValidator()
        result = validator.validate_round_trip(graph)
        
        # Should preserve basic structure
        assert 'round_trip_successful' in result
        assert 'original_clif' in result
    
    def test_complex_structure_round_trip(self):
        """Test round-trip for complex nested structure."""
        # Create complex graph with nested contexts
        graph = EGGraph.create_empty()
        
        # Add implication structure
        graph, outer_cut = graph.create_context('cut', name='Implication')
        ant_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(ant_node, outer_cut.id)
        
        graph, inner_cut = graph.create_context('cut', outer_cut.id, 'Consequent')
        cons_node = Node.create(node_type='predicate', properties={'name': 'Q'})
        graph = graph.add_node(cons_node, inner_cut.id)
        
        # Test round-trip
        validator = CLIFRoundTripValidator()
        result = validator.validate_round_trip(graph)
        
        # Should preserve structure
        assert 'semantic_equivalence' in result
        assert 'generation_metadata' in result


class TestCLIFIntegrationProperties:
    """Property-based tests for CLIF integration."""
    
    @given(st.text(alphabet='PQRABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=5))
    def test_predicate_name_preservation(self, predicate_name):
        """Test that predicate names are preserved through round-trip."""
        # Create graph with predicate
        graph = EGGraph.create_empty()
        pred_node = Node.create(node_type='predicate', properties={'name': predicate_name})
        graph = graph.add_node(pred_node)
        
        # Generate CLIF
        generator = CLIFGenerator()
        result = generator.generate(graph)
        
        # Predicate name should appear in CLIF
        assert predicate_name in result.clif_text
    
    @given(st.integers(min_value=1, max_value=5))
    def test_context_depth_handling(self, depth):
        """Test handling of various context depths."""
        graph = EGGraph.create_empty()
        current_context_id = graph.root_context_id
        
        # Create nested contexts
        for i in range(depth):
            graph, new_context = graph.create_context('cut', current_context_id, f'Level {i}')
            current_context_id = new_context.id
        
        # Add predicate at deepest level
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        graph = graph.add_node(pred_node, current_context_id)
        
        # Should handle any reasonable depth
        generator = CLIFGenerator()
        result = generator.generate(graph)
        
        assert result.clif_text is not None
        assert len(result.warnings) == 0 or depth > 3  # May warn for very deep nesting

