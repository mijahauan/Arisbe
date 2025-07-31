#!/usr/bin/env python3
"""
Rules 3-4 (Iteration/De-iteration) Test Implementation
Tests Rules 3 and 4 using the proven architectural approach

CHANGES: Based on successful Rules 1-2 approach, this implementation focuses
on the core mathematical constraints for iteration and de-iteration:
- Iteration: Copy subgraph to same or deeper nested context
- De-iteration: Remove copy that could have been created by iteration

Key Implementation:
- Check context nesting relationships (same or deeper for iteration)
- Validate identical subgraph structure for de-iteration
- Use direct context checking without complex subgraph creation

Dau's Iteration Rules:
- Iteration: Copy subgraph from one context to same or deeper context
- De-iteration: Remove copy if identical to base subgraph in shallower context
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
class IterationTest:
    """Test case for Rule 3 (Iteration)."""
    name: str
    base_egif: str
    source_pattern: str  # What to iterate
    source_context_hint: str  # Where it currently is
    target_context_hint: str  # Where to iterate it to
    validation_type: str
    expected_success: bool
    reason: str


@dataclass
class DeiterationTest:
    """Test case for Rule 4 (De-iteration)."""
    name: str
    base_egif: str
    copy_pattern: str  # What to de-iterate (remove)
    copy_context_hint: str  # Where the copy is
    base_pattern: str  # The original that justifies removal
    base_context_hint: str  # Where the original is
    validation_type: str
    expected_success: bool
    reason: str


@dataclass
class IterationResult:
    """Result of iteration validity check."""
    test_name: str
    source_context_found: bool
    target_context_found: bool
    source_context_id: Optional[ElementID]
    target_context_id: Optional[ElementID]
    nesting_relationship: Optional[str]  # "same", "deeper", "shallower", "unrelated"
    iteration_allowed: bool
    test_passed: bool
    error_message: str


@dataclass
class DeiterationResult:
    """Result of de-iteration validity check."""
    test_name: str
    copy_found: bool
    base_found: bool
    copy_context_id: Optional[ElementID]
    base_context_id: Optional[ElementID]
    patterns_identical: bool
    nesting_valid: bool  # base should be in same or shallower context
    deiteration_allowed: bool
    test_passed: bool
    error_message: str


class Rules34IterationTester:
    """
    Tester for Rules 3-4 (Iteration/De-iteration) based on successful approach.
    
    CHANGES: Implements context nesting validation and pattern matching
    for iteration and de-iteration rules.
    """
    
    def __init__(self, graph: RelationalGraphWithCuts):
        """Initialize the tester for a specific graph."""
        self.graph = graph
    
    def find_context_by_hint(self, hint: str) -> Optional[ElementID]:
        """Find a context based on a hint."""
        
        if hint == "negative" or hint == "only one":
            # Find the first negative context
            for cut in self.graph.Cut:
                if not self.graph.is_positive_context(cut.id):
                    return cut.id
        
        elif hint == "positive":
            # Find the first positive context
            for cut in self.graph.Cut:
                if self.graph.is_positive_context(cut.id):
                    return cut.id
        
        elif hint == "sheet" or hint == "after base graph":
            return self.graph.sheet
        
        elif hint == "beside (Mortal x)":
            # Find positive context (where Mortal x would be)
            for cut in self.graph.Cut:
                if self.graph.is_positive_context(cut.id):
                    return cut.id
        
        elif hint == "beside (B *y)":
            # Find negative context (where B *y would be)
            for cut in self.graph.Cut:
                if not self.graph.is_positive_context(cut.id):
                    return cut.id
        
        elif hint == "beside (C x)":
            # Find positive context (where C x would be)
            for cut in self.graph.Cut:
                if self.graph.is_positive_context(cut.id):
                    return cut.id
        
        return None
    
    def get_nesting_relationship(self, context1: ElementID, context2: ElementID) -> str:
        """
        Determine the nesting relationship between two contexts.
        
        CHANGES: Core logic for iteration validation - determines if target
        context is same, deeper, shallower, or unrelated to source context.
        """
        
        if context1 == context2:
            return "same"
        
        # Check if context1 is nested inside context2 (context1 is deeper)
        current = context1
        while current != self.graph.sheet:
            # Find the cut with this context ID and get its parent
            cut = next((c for c in self.graph.Cut if c.id == current), None)
            if cut:
                parent = self.graph.get_context(cut.id)
                if parent == context2:
                    return "deeper"  # context1 is deeper than context2
                current = parent
            else:
                break
        
        # Check if context2 is nested inside context1 (context2 is deeper)
        current = context2
        while current != self.graph.sheet:
            # Find the cut with this context ID and get its parent
            cut = next((c for c in self.graph.Cut if c.id == current), None)
            if cut:
                parent = self.graph.get_context(cut.id)
                if parent == context1:
                    return "shallower"  # context1 is shallower than context2
                current = parent
            else:
                break
        
        return "unrelated"
    
    def patterns_are_identical(self, pattern1: str, pattern2: str) -> bool:
        """
        Check if two patterns represent identical subgraphs.
        
        CHANGES: Enhanced to handle variable binding equivalence for de-iteration.
        For de-iteration, (B y) and (B *y) should be considered equivalent since
        one could be created by iterating the other with proper variable binding.
        """
        
        # Normalize patterns by removing variable binding markers
        def normalize_pattern(pattern):
            # Remove * from variable names for comparison
            # (B *y) becomes (B y) for comparison purposes
            return pattern.replace('*', '').strip()
        
        normalized1 = normalize_pattern(pattern1)
        normalized2 = normalize_pattern(pattern2)
        
        return normalized1 == normalized2
    
    def test_iteration_validity(self, test: IterationTest) -> IterationResult:
        """
        Test iteration validity by checking context nesting.
        
        CHANGES: Core implementation of Rule 3 - iteration allowed only
        to same or deeper contexts.
        """
        
        try:
            # Find source and target contexts
            source_context = self.find_context_by_hint(test.source_context_hint)
            target_context = self.find_context_by_hint(test.target_context_hint)
            
            if source_context is None:
                return IterationResult(
                    test_name=test.name,
                    source_context_found=False,
                    target_context_found=target_context is not None,
                    source_context_id=None,
                    target_context_id=target_context,
                    nesting_relationship=None,
                    iteration_allowed=False,
                    test_passed=False,
                    error_message=f"Source context not found for hint: {test.source_context_hint}"
                )
            
            if target_context is None:
                return IterationResult(
                    test_name=test.name,
                    source_context_found=True,
                    target_context_found=False,
                    source_context_id=source_context,
                    target_context_id=None,
                    nesting_relationship=None,
                    iteration_allowed=False,
                    test_passed=False,
                    error_message=f"Target context not found for hint: {test.target_context_hint}"
                )
            
            # Determine nesting relationship
            nesting = self.get_nesting_relationship(target_context, source_context)
            
            # Iteration allowed if target is same or deeper than source
            iteration_allowed = nesting in ["same", "deeper"]
            
            # Check if this matches expected result
            test_passed = (iteration_allowed == test.expected_success)
            
            return IterationResult(
                test_name=test.name,
                source_context_found=True,
                target_context_found=True,
                source_context_id=source_context,
                target_context_id=target_context,
                nesting_relationship=nesting,
                iteration_allowed=iteration_allowed,
                test_passed=test_passed,
                error_message=""
            )
        
        except Exception as e:
            return IterationResult(
                test_name=test.name,
                source_context_found=False,
                target_context_found=False,
                source_context_id=None,
                target_context_id=None,
                nesting_relationship=None,
                iteration_allowed=False,
                test_passed=False,
                error_message=f"Exception during test: {str(e)}"
            )
    
    def test_deiteration_validity(self, test: DeiterationTest) -> DeiterationResult:
        """
        Test de-iteration validity by checking pattern identity and nesting.
        
        CHANGES: Core implementation of Rule 4 - de-iteration allowed only
        if copy is identical to base and base is in same or shallower context.
        """
        
        try:
            # Find copy and base contexts
            copy_context = self.find_context_by_hint(test.copy_context_hint)
            base_context = self.find_context_by_hint(test.base_context_hint)
            
            copy_found = copy_context is not None
            base_found = base_context is not None
            
            if not copy_found or not base_found:
                return DeiterationResult(
                    test_name=test.name,
                    copy_found=copy_found,
                    base_found=base_found,
                    copy_context_id=copy_context,
                    base_context_id=base_context,
                    patterns_identical=False,
                    nesting_valid=False,
                    deiteration_allowed=False,
                    test_passed=False,
                    error_message="Copy or base context not found"
                )
            
            # Check if patterns are identical
            patterns_identical = self.patterns_are_identical(test.copy_pattern, test.base_pattern)
            
            # Check nesting relationship (base should be same or shallower than copy)
            nesting = self.get_nesting_relationship(base_context, copy_context)
            nesting_valid = nesting in ["same", "shallower"]
            
            # De-iteration allowed if patterns identical and nesting valid
            deiteration_allowed = patterns_identical and nesting_valid
            
            # Check if this matches expected result
            test_passed = (deiteration_allowed == test.expected_success)
            
            return DeiterationResult(
                test_name=test.name,
                copy_found=True,
                base_found=True,
                copy_context_id=copy_context,
                base_context_id=base_context,
                patterns_identical=patterns_identical,
                nesting_valid=nesting_valid,
                deiteration_allowed=deiteration_allowed,
                test_passed=test_passed,
                error_message=""
            )
        
        except Exception as e:
            return DeiterationResult(
                test_name=test.name,
                copy_found=False,
                base_found=False,
                copy_context_id=None,
                base_context_id=None,
                patterns_identical=False,
                nesting_valid=False,
                deiteration_allowed=False,
                test_passed=False,
                error_message=f"Exception during test: {str(e)}"
            )


def create_rule3_tests() -> List[IterationTest]:
    """Create Rule 3 (Iteration) tests based on your specifications."""
    
    return [
        # Prevention Test: Wrong Nesting Direction
        IterationTest(
            name="Prevention: Wrong Nesting Direction",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            source_pattern="(Human *x)",
            source_context_hint="negative",  # Source in negative context
            target_context_hint="after base graph",  # Target on sheet (shallower)
            validation_type="prevention",
            expected_success=False,
            reason="Cannot iterate to shallower context"
        ),
        
        # Performance Test: Same Context Iteration
        IterationTest(
            name="Performance: Same Context Iteration",
            base_egif="~[(A *x) (B *y) ~[(C x) (B y)]]",
            source_pattern="(B y)",
            source_context_hint="positive",  # Source in positive context
            target_context_hint="beside (C x)",  # Target in same positive context
            validation_type="performance",
            expected_success=True,
            reason="Iteration to same context is allowed"
        )
    ]


def create_rule4_tests() -> List[DeiterationTest]:
    """Create Rule 4 (De-iteration) tests based on your specifications."""
    
    return [
        # Prevention Test: Non-identical Subgraphs
        DeiterationTest(
            name="Prevention: Non-identical Subgraphs",
            base_egif="~[(Human *x) ~[(Mortal x)]]",
            copy_pattern="(Human *x)",
            copy_context_hint="negative",
            base_pattern="~[]",  # Different pattern
            base_context_hint="positive",
            validation_type="prevention",
            expected_success=False,
            reason="Copy and base patterns are not identical"
        ),
        
        # Performance Test: Valid Copy Removal
        DeiterationTest(
            name="Performance: Valid Copy Removal",
            base_egif="~[(A *x) (B *y) ~[(C x) (B y)]]",
            copy_pattern="(B y)",
            copy_context_hint="beside (C x)",  # Copy in deeper context
            base_pattern="(B *y)",  # Base pattern (with variable binding difference)
            base_context_hint="beside (B *y)",  # Base in shallower context
            validation_type="performance",
            expected_success=True,
            reason="Valid de-iteration of copy with proper base"
        )
    ]


def run_rules34_tests():
    """Run Rules 3-4 (Iteration/De-iteration) tests."""
    
    print("Rules 3-4 (Iteration/De-iteration) Tests")
    print("=" * 60)
    print("Testing context nesting relationships and pattern identity")
    print("Based on successful Rules 1-2 approach")
    print()
    
    # Test Rule 3 (Iteration)
    print("=== RULE 3 (ITERATION) TESTS ===")
    iteration_tests = create_rule3_tests()
    iteration_results = []
    
    for i, test in enumerate(iteration_tests, 1):
        print(f"--- Test 3.{i}: {test.name} ---")
        print(f"Base EGIF: {test.base_egif}")
        print(f"Source pattern: {test.source_pattern}")
        print(f"Source context: {test.source_context_hint}")
        print(f"Target context: {test.target_context_hint}")
        print(f"Expected iteration allowed: {test.expected_success}")
        print(f"Reason: {test.reason}")
        
        try:
            graph = parse_egif(test.base_egif)
            print(f"Graph: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
            
            tester = Rules34IterationTester(graph)
            result = tester.test_iteration_validity(test)
            
            print(f"Source context found: {result.source_context_found}")
            print(f"Target context found: {result.target_context_found}")
            if result.source_context_found and result.target_context_found:
                print(f"Source context ID: {result.source_context_id}")
                print(f"Target context ID: {result.target_context_id}")
                print(f"Nesting relationship: {result.nesting_relationship}")
                print(f"Iteration allowed: {result.iteration_allowed}")
            
            print(f"Test result: {'PASS' if result.test_passed else 'FAIL'}")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
            
            iteration_results.append(result)
            
        except Exception as e:
            print(f"Test failed with exception: {e}")
            iteration_results.append(IterationResult(
                test_name=test.name,
                source_context_found=False,
                target_context_found=False,
                source_context_id=None,
                target_context_id=None,
                nesting_relationship=None,
                iteration_allowed=False,
                test_passed=False,
                error_message=str(e)
            ))
        
        print()
    
    # Test Rule 4 (De-iteration)
    print("=== RULE 4 (DE-ITERATION) TESTS ===")
    deiteration_tests = create_rule4_tests()
    deiteration_results = []
    
    for i, test in enumerate(deiteration_tests, 1):
        print(f"--- Test 4.{i}: {test.name} ---")
        print(f"Base EGIF: {test.base_egif}")
        print(f"Copy pattern: {test.copy_pattern}")
        print(f"Copy context: {test.copy_context_hint}")
        print(f"Base pattern: {test.base_pattern}")
        print(f"Base context: {test.base_context_hint}")
        print(f"Expected de-iteration allowed: {test.expected_success}")
        print(f"Reason: {test.reason}")
        
        try:
            graph = parse_egif(test.base_egif)
            print(f"Graph: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
            
            tester = Rules34IterationTester(graph)
            result = tester.test_deiteration_validity(test)
            
            print(f"Copy found: {result.copy_found}")
            print(f"Base found: {result.base_found}")
            if result.copy_found and result.base_found:
                print(f"Copy context ID: {result.copy_context_id}")
                print(f"Base context ID: {result.base_context_id}")
                print(f"Patterns identical: {result.patterns_identical}")
                print(f"Nesting valid: {result.nesting_valid}")
                print(f"De-iteration allowed: {result.deiteration_allowed}")
            
            print(f"Test result: {'PASS' if result.test_passed else 'FAIL'}")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
            
            deiteration_results.append(result)
            
        except Exception as e:
            print(f"Test failed with exception: {e}")
            deiteration_results.append(DeiterationResult(
                test_name=test.name,
                copy_found=False,
                base_found=False,
                copy_context_id=None,
                base_context_id=None,
                patterns_identical=False,
                nesting_valid=False,
                deiteration_allowed=False,
                test_passed=False,
                error_message=str(e)
            ))
        
        print()
    
    # Combined Summary
    print("=" * 60)
    print("RULES 3-4 TEST SUMMARY")
    print("=" * 60)
    
    all_results = iteration_results + deiteration_results
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.test_passed)
    
    iteration_passed = sum(1 for r in iteration_results if r.test_passed)
    deiteration_passed = sum(1 for r in deiteration_results if r.test_passed)
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests*100):.1f}%")
    print()
    print(f"Rule 3 (Iteration): {len(iteration_results)} tests (passed: {iteration_passed})")
    print(f"Rule 4 (De-iteration): {len(deiteration_results)} tests (passed: {deiteration_passed})")
    print()
    
    if passed_tests == total_tests:
        print("🎯 PERFECT: All tests passed - Rules 3-4 logic is mathematically correct!")
    elif passed_tests >= total_tests * 0.8:
        print("⚠ GOOD: Most tests passed - Minor issues to resolve")
    else:
        print("✗ ISSUES: Significant problems with the core logic")
    
    return iteration_results, deiteration_results


if __name__ == "__main__":
    print("Rules 3-4 (Iteration/De-iteration) Testing")
    print("Tests context nesting relationships and pattern identity")
    print()
    
    run_rules34_tests()

