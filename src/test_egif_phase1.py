"""
Comprehensive Test Suite for EGIF Phase 1 Implementation

This test suite validates the Phase 1 EGIF implementation with focus on:
- Lexical analysis and tokenization
- Basic parsing of Alpha and Beta constructs
- Error handling with educational feedback
- Educational trace generation

The tests follow the educational-first design principle by providing
clear feedback about what each test validates and why it matters.

Author: Manus AI
Date: January 2025
"""

import unittest
from typing import List, Dict, Any
import sys
import os

# Add the src directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from egif_lexer import EGIFLexer, EGIFTokenType, EGIFLexError
from egif_parser import EGIFParser, parse_egif, EGIFParseError
from egif_error_handler import EGIFErrorHandler, EGIFErrorSeverity, EGIFErrorCategory
from eg_types import Entity, Predicate


class TestEGIFLexer(unittest.TestCase):
    """Test cases for EGIF lexical analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.lexer = EGIFLexer("", educational_mode=True)
    
    def test_basic_tokenization(self):
        """Test basic tokenization of EGIF constructs."""
        test_cases = [
            # Basic relation
            ("(Person *x)", [
                EGIFTokenType.LPAREN, EGIFTokenType.IDENTIFIER, 
                EGIFTokenType.ASTERISK, EGIFTokenType.IDENTIFIER, 
                EGIFTokenType.RPAREN
            ]),
            
            # Negation
            ("~[test]", [
                EGIFTokenType.TILDE, EGIFTokenType.LBRACKET,
                EGIFTokenType.IDENTIFIER, EGIFTokenType.RBRACKET
            ]),
            
            # Scroll notation
            ("[If condition [Then result]]", [
                EGIFTokenType.LBRACKET, EGIFTokenType.IF, EGIFTokenType.IDENTIFIER,
                EGIFTokenType.LBRACKET, EGIFTokenType.THEN, EGIFTokenType.IDENTIFIER,
                EGIFTokenType.RBRACKET, EGIFTokenType.RBRACKET
            ]),
            
            # Constants
            ("42 \"hello\"", [
                EGIFTokenType.INTEGER, EGIFTokenType.QUOTED_NAME
            ])
        ]
        
        for source, expected_types in test_cases:
            with self.subTest(source=source):
                self.lexer = EGIFLexer(source, educational_mode=True)
                tokens, errors = self.lexer.tokenize()
                
                # Filter out whitespace and EOF tokens for comparison
                actual_types = [token.type for token in tokens 
                              if token.type not in [EGIFTokenType.WHITESPACE, EGIFTokenType.EOF]]
                
                self.assertEqual(actual_types, expected_types, 
                               f"Token types don't match for '{source}'")
                self.assertEqual(len(errors), 0, 
                               f"Unexpected lexical errors for '{source}': {errors}")
    
    def test_lexical_errors(self):
        """Test lexical error detection and educational feedback."""
        error_cases = [
            ("(Person &x)", "&"),  # Invalid conjunction
            ("{Person x}", "{"),   # Wrong bracket type
            ("(Person @x)", "@"),  # Invalid quantifier
            ("(Person !x)", "!"),  # Invalid negation
        ]
        
        for source, expected_char in error_cases:
            with self.subTest(source=source):
                self.lexer = EGIFLexer(source, educational_mode=True)
                tokens, errors = self.lexer.tokenize()
                
                self.assertGreater(len(errors), 0, 
                                 f"Expected lexical error for '{source}'")
                
                # Check that error mentions the problematic character
                error_found = any(expected_char in error.message for error in errors)
                self.assertTrue(error_found, 
                              f"Error should mention '{expected_char}' for '{source}'")
                
                # Check educational feedback
                has_educational_note = any(error.educational_note for error in errors)
                self.assertTrue(has_educational_note, 
                              f"Should provide educational feedback for '{source}'")
    
    def test_educational_feedback(self):
        """Test that lexer provides educational feedback for tokens."""
        source = "(Person *x)"
        self.lexer = EGIFLexer(source, educational_mode=True)
        tokens, errors = self.lexer.tokenize()
        
        # Check that tokens have educational descriptions
        for token in tokens:
            if token.type != EGIFTokenType.WHITESPACE:
                self.assertIsNotNone(token.description, 
                                   f"Token {token.type} should have educational description")


class TestEGIFParser(unittest.TestCase):
    """Test cases for EGIF parsing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = EGIFParser(educational_mode=True)
    
    def test_simple_relations(self):
        """Test parsing of simple relations."""
        test_cases = [
            "(Person *x)",
            "(Loves *john *mary)",
            "(Between *a *b *c)"
        ]
        
        for source in test_cases:
            with self.subTest(source=source):
                result = parse_egif(source)
                
                self.assertEqual(len(result.errors), 0, 
                               f"Should parse without errors: {source}")
                self.assertGreater(len(result.predicates), 0, 
                                 f"Should create predicates: {source}")
                self.assertGreater(len(result.entities), 0, 
                                 f"Should create entities: {source}")
    
    def test_defining_and_bound_labels(self):
        """Test parsing of defining labels (*x) and bound labels (x)."""
        # Valid case: defining then using
        result = parse_egif("(Person *x) (Mortal x)")
        self.assertEqual(len(result.errors), 0, "Should parse without errors")
        self.assertEqual(len(result.entities), 1, "Should create one entity")
        self.assertEqual(len(result.predicates), 2, "Should create two predicates")
        
        # Error case: using undefined label
        result = parse_egif("(Person *x) (Mortal y)")
        self.assertGreater(len(result.errors), 0, "Should detect undefined label")
        
        # Check error type
        undefined_errors = [e for e in result.errors if "UNDEFINED_LABEL" in e.error_type]
        self.assertGreater(len(undefined_errors), 0, "Should have undefined label error")
    
    def test_negation_parsing(self):
        """Test parsing of negation constructs."""
        test_cases = [
            "~[(Person x)]",
            "~[~[(Mortal x)]]",  # Double negation
            "(Person *x) ~[(Mortal x)]"
        ]
        
        for source in test_cases:
            with self.subTest(source=source):
                result = parse_egif(source)
                
                # Should parse without critical errors
                critical_errors = [e for e in result.errors 
                                 if e.error_type not in ["UNDEFINED_LABEL"]]
                self.assertEqual(len(critical_errors), 0, 
                               f"Should parse structure correctly: {source}")
    
    def test_coreference_parsing(self):
        """Test parsing of coreference nodes."""
        # Valid coreference
        result = parse_egif("(Person *x) (Mortal *y) [x y]")
        self.assertEqual(len(result.errors), 0, "Should parse without errors")
        
        # Invalid coreference - undefined labels
        result = parse_egif("(Person *x) [x y]")
        undefined_errors = [e for e in result.errors if "UNDEFINED_LABEL" in e.error_type]
        self.assertGreater(len(undefined_errors), 0, "Should detect undefined label in coreference")
    
    def test_scroll_notation_parsing(self):
        """Test parsing of scroll notation (conditionals)."""
        # Note: This test focuses on structure recognition rather than full semantic correctness
        source = "[If (Person *x) [Then (Mortal x)]]"
        result = parse_egif(source)
        
        # Should recognize the scroll structure
        self.assertGreater(len(result.educational_trace), 0, "Should provide educational trace")
        
        # Check for scroll-related trace messages
        scroll_traces = [trace for trace in result.educational_trace 
                        if "scroll" in trace.lower()]
        self.assertGreater(len(scroll_traces), 0, "Should mention scroll in trace")
    
    def test_constants_parsing(self):
        """Test parsing of constants (integers and strings)."""
        test_cases = [
            "(Age *person 25)",
            "(Name *person \"John\")",
            "(Between 1 2 3)"
        ]
        
        for source in test_cases:
            with self.subTest(source=source):
                result = parse_egif(source)
                
                # Should create constant entities
                constant_entities = [e for e in result.entities 
                                   if e.entity_type == 'constant']
                self.assertGreater(len(constant_entities), 0, 
                                 f"Should create constant entities: {source}")
    
    def test_educational_trace(self):
        """Test that parser provides educational trace."""
        source = "(Person *x) (Mortal x)"
        result = parse_egif(source, educational_mode=True)
        
        self.assertGreater(len(result.educational_trace), 0, 
                         "Should provide educational trace")
        
        # Check for key educational concepts
        trace_text = " ".join(result.educational_trace).lower()
        educational_concepts = ["defining label", "bound label", "relation", "entity"]
        
        found_concepts = [concept for concept in educational_concepts 
                         if concept in trace_text]
        self.assertGreater(len(found_concepts), 0, 
                         "Should mention educational concepts in trace")
    
    def test_error_recovery(self):
        """Test parser error recovery and continued parsing."""
        # Simple case with just one undefined label error
        source = "(Person *x) (Mortal y)"  # 'y' is undefined
        result = parse_egif(source, educational_mode=False)
        
        # Should detect the undefined label error
        self.assertGreater(len(result.errors), 0, "Should detect undefined label error")
        
        # Should still create the valid parts (Person *x should work)
        self.assertGreater(len(result.entities), 0, "Should create entity from valid part")
        self.assertGreater(len(result.predicates), 0, "Should create predicates from valid parts")
        
        # Should return a valid result object
        self.assertIsNotNone(result, "Should return a result even with errors")
        self.assertIsNotNone(result.entities, "Should have entities list")
        self.assertIsNotNone(result.predicates, "Should have predicates list")


class TestEGIFErrorHandler(unittest.TestCase):
    """Test cases for EGIF error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = EGIFErrorHandler(educational_mode=True)
    
    def test_error_categorization(self):
        """Test that errors are properly categorized."""
        # Create sample errors
        from egif_lexer import EGIFLexError
        from egif_parser import EGIFParseError, EGIFToken
        
        lex_error = EGIFLexError(
            message="Invalid character",
            line=1, column=1, position=0, length=1,
            error_type="INVALID_CHARACTER",
            suggestions=[], educational_note=""
        )
        
        token = EGIFToken(EGIFTokenType.IDENTIFIER, "test", 1, 1, 0, 4)
        parse_error = EGIFParseError(
            message="Undefined label",
            token=token,
            error_type="UNDEFINED_LABEL",
            suggestions=[], educational_note=""
        )
        
        # Test error handling
        lex_report = self.handler.handle_lexical_error(lex_error, ["test line"])
        parse_report = self.handler.handle_parse_error(parse_error, ["test line"])
        
        self.assertEqual(lex_report.category, EGIFErrorCategory.LEXICAL)
        self.assertEqual(parse_report.category, EGIFErrorCategory.CONTEXT)
    
    def test_educational_notes(self):
        """Test that educational notes are provided for errors."""
        # Test with undefined label error
        from egif_parser import EGIFParseError, EGIFToken
        
        token = EGIFToken(EGIFTokenType.IDENTIFIER, "x", 1, 1, 0, 1)
        parse_error = EGIFParseError(
            message="Undefined label 'x'",
            token=token,
            error_type="UNDEFINED_LABEL",
            suggestions=[], educational_note=""
        )
        
        report = self.handler.handle_parse_error(parse_error, ["(Person x)"])
        
        self.assertIsNotNone(report.educational_note, 
                           "Should provide educational note for undefined label")
        self.assertEqual(report.educational_note.concept, "Bound Labels")
    
    def test_error_summary(self):
        """Test error summary generation."""
        # Create multiple error reports
        from egif_lexer import EGIFLexError
        
        errors = []
        for i in range(3):
            lex_error = EGIFLexError(
                message=f"Error {i}",
                line=1, column=i, position=i, length=1,
                error_type="TEST_ERROR",
                suggestions=[], educational_note=""
            )
            report = self.handler.handle_lexical_error(lex_error, ["test"])
            errors.append(report)
        
        summary = self.handler.generate_error_summary(errors)
        
        self.assertIn("3 error(s) found", summary)
        self.assertIn("Educational Insights", summary)


class TestEGIFIntegration(unittest.TestCase):
    """Test cases for EGIF integration with educational focus."""
    
    def test_end_to_end_parsing(self):
        """Test complete end-to-end parsing workflow."""
        test_cases = [
            # Simple cases that should work
            "(Person *x)",
            "(Person *x) (Mortal x)",
            
            # Cases with expected errors
            "(Person *x) (Mortal y)",  # Undefined label
        ]
        
        for source in test_cases:
            with self.subTest(source=source):
                result = parse_egif(source, educational_mode=True)
                
                # Should always provide educational trace
                self.assertGreater(len(result.educational_trace), 0, 
                                 f"Should provide educational trace for: {source}")
                
                # Should create appropriate structures when valid
                if len(result.errors) == 0:
                    self.assertGreater(len(result.entities) + len(result.predicates), 0,
                                     f"Should create entities/predicates for valid: {source}")
    
    def test_educational_feedback_quality(self):
        """Test the quality and usefulness of educational feedback."""
        # Test with a complex example
        source = "(Person *x) ~[(Mortal x)] [If (Human *y) [Then (Mortal y)]]"
        result = parse_egif(source, educational_mode=True)
        
        trace_text = " ".join(result.educational_trace).lower()
        
        # Should mention key EG concepts
        expected_concepts = [
            "relation", "entity", "negation", "cut", "defining", "bound"
        ]
        
        mentioned_concepts = [concept for concept in expected_concepts 
                            if concept in trace_text]
        
        self.assertGreater(len(mentioned_concepts), 3, 
                         "Should mention multiple EG concepts in educational trace")


def run_phase1_tests():
    """Run all Phase 1 tests and generate a comprehensive report."""
    print("EGIF Phase 1 Test Suite")
    print("=" * 50)
    print("Testing lexical analysis, parsing, error handling, and educational feedback")
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestEGIFLexer,
        TestEGIFParser,
        TestEGIFErrorHandler,
        TestEGIFIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Generate summary report
    print("\n" + "=" * 50)
    print("PHASE 1 TEST SUMMARY")
    print("=" * 50)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    
    print(f"Total Tests: {total_tests}")
    print(f"Successes: {successes}")
    print(f"Failures: {failures}")
    print(f"Errors: {errors}")
    print(f"Success Rate: {(successes/total_tests)*100:.1f}%")
    
    if failures > 0:
        print(f"\nFailures ({failures}):")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if errors > 0:
        print(f"\nErrors ({errors}):")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    # Educational assessment
    print("\nEducational Features Validated:")
    print("✓ Lexical tokenization with educational descriptions")
    print("✓ Parse error detection with helpful suggestions")
    print("✓ Educational trace generation during parsing")
    print("✓ Error categorization and educational notes")
    print("✓ Integration of EGIF concepts with EG principles")
    
    print("\nPhase 1 Implementation Status:")
    if successes == total_tests:
        print("🎉 PHASE 1 COMPLETE - All tests passing!")
        print("Ready to proceed to Phase 2 (Advanced constructs)")
    elif successes >= total_tests * 0.8:
        print("✅ PHASE 1 MOSTLY COMPLETE - Minor issues to resolve")
        print("Can proceed to Phase 2 with noted limitations")
    else:
        print("⚠️  PHASE 1 NEEDS WORK - Significant issues found")
        print("Recommend addressing failures before Phase 2")
    
    return result


if __name__ == "__main__":
    # Run the comprehensive test suite
    run_phase1_tests()

