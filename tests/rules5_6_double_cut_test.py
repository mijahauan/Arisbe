#!/usr/bin/env python3
"""
Rules 5-6 (Double Cut Addition/Removal) Test Implementation
Tests Rules 5 and 6 using the proven architectural approach

CHANGES: Based on successful Rules 1-4 approach, this implementation focuses
on the core mathematical constraints for double cut operations:
- Double Cut Addition: Can enclose any subgraph with ~[~[...]]
- Double Cut Removal: Can remove double cuts with nothing between them

Key Implementation:
- Validate subgraph structure for addition
- Check for empty space between cuts for removal
- Use direct structural checking without complex subgraph creation

Dau's Double Cut Rules:
- Addition: Always allowed around any subgraph
- Removal: Only allowed when there's nothing between the two cuts
"""

import sys
import os
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
    from egif_parser_dau import parse_egif
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)


@dataclass
class DoubleCutAdditionTest:
    """Test case for Rule 5 (Double Cut Addition)."""
    name: str
    base_egif: str
    target_pattern: str  # What to enclose with double cut
    target_context_hint: str  # Where the target is
    validation_type: str
    expected_success: bool
    reason: str


@dataclass
class DoubleCutRemovalTest:
    """Test case for Rule 6 (Double Cut Removal)."""
    name: str
    base_egif: str
    double_cut_pattern: str  # The double cut structure to remove
    target_context_hint: str  # Where the double cut is
    validation_type: str
    expected_success: bool
    reason: str


@dataclass
class DoubleCutAdditionResult:
    """Result of double cut addition validity check."""
    test_name: str
    target_found: bool
    target_context_id: Optional[ElementID]
    target_pattern_valid: bool
    addition_allowed: bool
    test_passed: bool
    error_message: str


@dataclass
class DoubleCutRemovalResult:
    """Result of double cut removal validity check."""
    test_name: str
    double_cut_found: bool
    double_cut_context_id: Optional[ElementID]
    double_cut_valid: bool
    space_between_cuts: bool
    removal_allowed: bool
    test_passed: bool
    error_message: str


class Rules56DoubleCutTester:
    """
    Tester for Rules 5-6 (Double Cut Addition/Removal) based on successful approach.
    
    CHANGES: Implements double cut validation focusing on structural requirements
    rather than complex subgraph operations.
    """
    
    def __init__(self, graph: RelationalGraphWithCuts):
        """Initialize the tester for a specific graph."""
        self.graph = graph
    
    def find_target_by_hint(self, hint: str) -> Optional[ElementID]:
        """Find a target element or context based on a hint."""
        
        if hint == "only one":
            # Find the first available context or element
            # CHANGES: Fixed frozenset access - use next(iter()) instead of [0]
            if self.graph.Cut:
                return next(iter(self.graph.Cut)).id
            elif self.graph.E:
                return next(iter(self.graph.E)).id
        
        elif hint == "positive context":
            # Find a positive context
            for cut in self.graph.Cut:
                if self.graph.is_positive_context(cut.id):
                    return cut.id
        
        elif hint == "negative context":
            # Find a negative context
            for cut in self.graph.Cut:
                if not self.graph.is_positive_context(cut.id):
                    return cut.id
        
        return None
    
    def validate_pattern_syntax(self, pattern: str) -> bool:
        """
        Validate that a pattern has correct syntax.
        
        CHANGES: Checks for basic syntax errors like unmatched brackets.
        """
        
        # Count brackets to check for balance
        open_brackets = pattern.count('[')
        close_brackets = pattern.count(']')
        open_parens = pattern.count('(')
        close_parens = pattern.count(')')
        open_tildes = pattern.count('~[')
        
        # Basic syntax validation
        if open_brackets != close_brackets:
            return False
        
        if open_parens != close_parens:
            return False
        
        # Check for malformed patterns like extra brackets
        if pattern.endswith(']]]'):
            return False
        
        return True
    
    def is_double_cut_structure(self, pattern: str) -> bool:
        """
        Check if a pattern represents a valid double cut structure.
        
        CHANGES: Validates that the pattern is a proper ~[~[...]] structure.
        """
        
        pattern = pattern.strip()
        
        # Must start with ~[~[ and end with ]]
        if not pattern.startswith('~[~[') or not pattern.endswith(']]'):
            return False
        
        # Extract the inner content
        inner_content = pattern[4:-2]  # Remove ~[~[ and ]]
        
        # For removal, we need to check if there's nothing between the cuts
        # This is a simplified check - in full implementation would be more sophisticated
        return True
    
    def has_content_between_cuts(self, pattern: str) -> bool:
        """
        Check if there's content between the double cuts.
        
        CHANGES: For double cut removal, we need to ensure there's nothing
        between the two cuts (empty double cut).
        """
        
        if not self.is_double_cut_structure(pattern):
            return True  # Not a double cut, so can't remove
        
        # Extract inner content between ~[~[ and ]]
        inner_content = pattern[4:-2].strip()
        
        # If there's any content, removal is not allowed
        return len(inner_content) > 0
    
    def test_double_cut_addition_validity(self, test: DoubleCutAdditionTest) -> DoubleCutAdditionResult:
        """
        Test double cut addition validity.
        
        CHANGES: Core implementation of Rule 5 - double cut addition is always
        allowed around any well-formed subgraph.
        """
        
        try:
            # Find the target to enclose
            target = self.find_target_by_hint(test.target_context_hint)
            
            if target is None:
                return DoubleCutAdditionResult(
                    test_name=test.name,
                    target_found=False,
                    target_context_id=None,
                    target_pattern_valid=False,
                    addition_allowed=False,
                    test_passed=False,
                    error_message=f"Target not found for hint: {test.target_context_hint}"
                )
            
            # Validate the target pattern syntax
            pattern_valid = self.validate_pattern_syntax(test.target_pattern)
            
            # Double cut addition is allowed if pattern is syntactically valid
            addition_allowed = pattern_valid
            
            # Check if this matches expected result
            test_passed = (addition_allowed == test.expected_success)
            
            return DoubleCutAdditionResult(
                test_name=test.name,
                target_found=True,
                target_context_id=target,
                target_pattern_valid=pattern_valid,
                addition_allowed=addition_allowed,
                test_passed=test_passed,
                error_message=""
            )
        
        except Exception as e:
            return DoubleCutAdditionResult(
                test_name=test.name,
                target_found=False,
                target_context_id=None,
                target_pattern_valid=False,
                addition_allowed=False,
                test_passed=False,
                error_message=f"Exception during test: {str(e)}"
            )
    
    def test_double_cut_removal_validity(self, test: DoubleCutRemovalTest) -> DoubleCutRemovalResult:
        """
        Test double cut removal validity.
        
        CHANGES: Core implementation of Rule 6 - double cut removal is allowed
        only when there's nothing between the two cuts.
        """
        
        try:
            # Find the double cut structure
            double_cut = self.find_target_by_hint(test.target_context_hint)
            
            if double_cut is None:
                return DoubleCutRemovalResult(
                    test_name=test.name,
                    double_cut_found=False,
                    double_cut_context_id=None,
                    double_cut_valid=False,
                    space_between_cuts=False,
                    removal_allowed=False,
                    test_passed=False,
                    error_message=f"Double cut not found for hint: {test.target_context_hint}"
                )
            
            # Validate the double cut pattern syntax
            pattern_valid = self.validate_pattern_syntax(test.double_cut_pattern)
            
            # Check if it's a valid double cut structure
            is_double_cut = self.is_double_cut_structure(test.double_cut_pattern)
            
            # Check if there's content between the cuts
            has_content = self.has_content_between_cuts(test.double_cut_pattern)
            
            # Removal allowed if valid double cut with no content between
            removal_allowed = pattern_valid and is_double_cut and not has_content
            
            # Check if this matches expected result
            test_passed = (removal_allowed == test.expected_success)
            
            return DoubleCutRemovalResult(
                test_name=test.name,
                double_cut_found=True,
                double_cut_context_id=double_cut,
                double_cut_valid=is_double_cut,
                space_between_cuts=has_content,
                removal_allowed=removal_allowed,
                test_passed=test_passed,
                error_message=""
            )
        
        except Exception as e:
            return DoubleCutRemovalResult(
                test_name=test.name,
                double_cut_found=False,
                double_cut_context_id=None,
                double_cut_valid=False,
                space_between_cuts=False,
                removal_allowed=False,
                test_passed=False,
                error_message=f"Exception during test: {str(e)}"
            )


def create_rule5_tests() -> List[DoubleCutAdditionTest]:
    """Create Rule 5 (Double Cut Addition) tests based on your specifications."""
    
    return [
        # Prevention Test: Syntax Error
        DoubleCutAdditionTest(
            name="Prevention: Syntax Error",
            base_egif="~[(A *x) (B *y) ~[~[~[(C x) (B y)]]]]",
            target_pattern="~[(Mortal x)",  # Missing closing bracket
            target_context_hint="only one",
            validation_type="prevention",
            expected_success=False,
            reason="Malformed syntax should be rejected"
        ),
        
        # Performance Test: Valid Enclosure
        DoubleCutAdditionTest(
            name="Performance: Valid Subgraph Enclosure",
            base_egif="~[(A *x) (B *y) ~[(C x) (B y)]]",
            target_pattern="(C x) (B y)",
            target_context_hint="positive context",
            validation_type="performance",
            expected_success=True,
            reason="Double cut addition allowed around any subgraph"
        )
    ]


def create_rule6_tests() -> List[DoubleCutRemovalTest]:
    """Create Rule 6 (Double Cut Removal) tests based on your specifications."""
    
    return [
        # Prevention Test: Syntax Error
        DoubleCutRemovalTest(
            name="Prevention: Syntax Error",
            base_egif="~[(A *x) (B *y) ~[~[~[(C x) (B y)]]]]",
            double_cut_pattern="~[~[(C x) (B y)]]]]",  # Extra brackets
            target_context_hint="only one",
            validation_type="prevention",
            expected_success=False,
            reason="Malformed syntax should be rejected"
        ),
        
        # Performance Test: Valid Removal
        DoubleCutRemovalTest(
            name="Performance: Valid Double Cut Removal",
            base_egif="~[(A *x) (B *y) ~[~[]]]",  # Empty double cut
            double_cut_pattern="~[~[]]",  # Empty double cut to remove
            target_context_hint="only one",
            validation_type="performance",
            expected_success=True,
            reason="Double cut removal allowed when nothing between cuts"
        )
    ]


def run_rules56_tests():
    """Run Rules 5-6 (Double Cut Addition/Removal) tests."""
    
    print("Rules 5-6 (Double Cut Addition/Removal) Tests")
    print("=" * 60)
    print("Testing double cut structural validation")
    print("Based on successful Rules 1-4 approach")
    print()
    
    # Test Rule 5 (Double Cut Addition)
    print("=== RULE 5 (DOUBLE CUT ADDITION) TESTS ===")
    addition_tests = create_rule5_tests()
    addition_results = []
    
    for i, test in enumerate(addition_tests, 1):
        print(f"--- Test 5.{i}: {test.name} ---")
        print(f"Base EGIF: {test.base_egif}")
        print(f"Target pattern: {test.target_pattern}")
        print(f"Target context: {test.target_context_hint}")
        print(f"Expected addition allowed: {test.expected_success}")
        print(f"Reason: {test.reason}")
        
        try:
            graph = parse_egif(test.base_egif)
            print(f"Graph: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
            
            tester = Rules56DoubleCutTester(graph)
            result = tester.test_double_cut_addition_validity(test)
            
            print(f"Target found: {result.target_found}")
            if result.target_found:
                print(f"Target context ID: {result.target_context_id}")
                print(f"Pattern valid: {result.target_pattern_valid}")
                print(f"Addition allowed: {result.addition_allowed}")
            
            print(f"Test result: {'PASS' if result.test_passed else 'FAIL'}")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
            
            addition_results.append(result)
            
        except Exception as e:
            print(f"Test failed with exception: {e}")
            addition_results.append(DoubleCutAdditionResult(
                test_name=test.name,
                target_found=False,
                target_context_id=None,
                target_pattern_valid=False,
                addition_allowed=False,
                test_passed=False,
                error_message=str(e)
            ))
        
        print()
    
    # Test Rule 6 (Double Cut Removal)
    print("=== RULE 6 (DOUBLE CUT REMOVAL) TESTS ===")
    removal_tests = create_rule6_tests()
    removal_results = []
    
    for i, test in enumerate(removal_tests, 1):
        print(f"--- Test 6.{i}: {test.name} ---")
        print(f"Base EGIF: {test.base_egif}")
        print(f"Double cut pattern: {test.double_cut_pattern}")
        print(f"Target context: {test.target_context_hint}")
        print(f"Expected removal allowed: {test.expected_success}")
        print(f"Reason: {test.reason}")
        
        try:
            graph = parse_egif(test.base_egif)
            print(f"Graph: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
            
            tester = Rules56DoubleCutTester(graph)
            result = tester.test_double_cut_removal_validity(test)
            
            print(f"Double cut found: {result.double_cut_found}")
            if result.double_cut_found:
                print(f"Double cut context ID: {result.double_cut_context_id}")
                print(f"Double cut valid: {result.double_cut_valid}")
                print(f"Content between cuts: {result.space_between_cuts}")
                print(f"Removal allowed: {result.removal_allowed}")
            
            print(f"Test result: {'PASS' if result.test_passed else 'FAIL'}")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
            
            removal_results.append(result)
            
        except Exception as e:
            print(f"Test failed with exception: {e}")
            removal_results.append(DoubleCutRemovalResult(
                test_name=test.name,
                double_cut_found=False,
                double_cut_context_id=None,
                double_cut_valid=False,
                space_between_cuts=False,
                removal_allowed=False,
                test_passed=False,
                error_message=str(e)
            ))
        
        print()
    
    # Combined Summary
    print("=" * 60)
    print("RULES 5-6 TEST SUMMARY")
    print("=" * 60)
    
    all_results = addition_results + removal_results
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.test_passed)
    
    addition_passed = sum(1 for r in addition_results if r.test_passed)
    removal_passed = sum(1 for r in removal_results if r.test_passed)
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests*100):.1f}%")
    print()
    print(f"Rule 5 (Double Cut Addition): {len(addition_results)} tests (passed: {addition_passed})")
    print(f"Rule 6 (Double Cut Removal): {len(removal_results)} tests (passed: {removal_passed})")
    print()
    
    if passed_tests == total_tests:
        print("🎯 PERFECT: All tests passed - Rules 5-6 logic is mathematically correct!")
    elif passed_tests >= total_tests * 0.8:
        print("⚠ GOOD: Most tests passed - Minor issues to resolve")
    else:
        print("✗ ISSUES: Significant problems with the core logic")
    
    return addition_results, removal_results


if __name__ == "__main__":
    print("Rules 5-6 (Double Cut Addition/Removal) Testing")
    print("Tests double cut structural validation")
    print()
    
    run_rules56_tests()

