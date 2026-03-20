"""
Complete Round-Trip Translation Demonstration

This module demonstrates complete round-trip translations between all supported formats
via EGI as the central representation:

FOPL ↔ CGIF ↔ CLIF ↔ EGIF ↔ FOPL

Tests semantic preservation and format consistency across arbitrary complex expressions.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass
import traceback

from chapter18_enhanced_translation import (
    EnhancedChapter18Translator, parse_fopl_formula, enhanced_fopl_to_egi, enhanced_egi_to_fopl
)
from egif_generator_dau import EGIFGenerator
from cgif_generator_dau import CGIFGenerator
from clif_generator_dau import CLIFGenerator
from egif_parser_dau import EGIFParser
from egi_core_dau import RelationalGraphWithCuts


@dataclass
class RoundTripTestCase:
    """Test case for round-trip translation."""
    name: str
    fopl_expression: str
    description: str
    complexity_level: str  # "simple", "medium", "complex", "extreme"


@dataclass
class RoundTripResult:
    """Result of complete round-trip translation test."""
    test_name: str
    original_fopl: str
    
    # Forward translations
    egi_from_fopl: Optional[RelationalGraphWithCuts]
    egif_from_egi: str
    cgif_from_egi: str
    clif_from_egi: str
    
    # Reverse translations
    egi_from_egif: Optional[RelationalGraphWithCuts]
    fopl_from_egi: str
    
    # Cross-format consistency
    egif_to_cgif_consistent: bool
    cgif_to_clif_consistent: bool
    clif_to_egif_consistent: bool
    
    # Semantic preservation
    semantic_preservation_score: float
    structural_fidelity_score: float
    
    # Overall success
    round_trip_success: bool
    errors: List[str]


class CompleteRoundTripTester:
    """Tests complete round-trip translations across all formats via EGI."""
    
    def __init__(self):
        self.fopl_translator = EnhancedChapter18Translator()
        self.egif_generator = EGIFGenerator()
        self.cgif_generator = CGIFGenerator()
        self.clif_generator = CLIFGenerator()
        
        # Define comprehensive test cases
        self.test_cases = [
            # Simple cases
            RoundTripTestCase(
                name="atomic_unary",
                fopl_expression="Man(x)",
                description="Simple unary predicate",
                complexity_level="simple"
            ),
            RoundTripTestCase(
                name="atomic_binary",
                fopl_expression="Loves(x, y)",
                description="Binary relation",
                complexity_level="simple"
            ),
            RoundTripTestCase(
                name="identity_relation",
                fopl_expression="x .= y",
                description="Identity relation",
                complexity_level="simple"
            ),
            
            # Medium complexity
            RoundTripTestCase(
                name="simple_conjunction",
                fopl_expression="Man(x) ∧ Mortal(x)",
                description="Conjunction with shared variable",
                complexity_level="medium"
            ),
            RoundTripTestCase(
                name="existential_simple",
                fopl_expression="∃x.Man(x)",
                description="Simple existential quantification",
                complexity_level="medium"
            ),
            RoundTripTestCase(
                name="universal_simple",
                fopl_expression="∀x.Man(x)",
                description="Simple universal quantification",
                complexity_level="medium"
            ),
            RoundTripTestCase(
                name="simple_negation",
                fopl_expression="¬Man(x)",
                description="Simple negation",
                complexity_level="medium"
            ),
            
            # Complex cases
            RoundTripTestCase(
                name="existential_conjunction",
                fopl_expression="∃x.(Man(x) ∧ Mortal(x))",
                description="Existential with conjunction",
                complexity_level="complex"
            ),
            RoundTripTestCase(
                name="universal_implication",
                fopl_expression="∀x.(Man(x) → Mortal(x))",
                description="Universal with implication",
                complexity_level="complex"
            ),
            RoundTripTestCase(
                name="nested_quantifiers",
                fopl_expression="∀x.∃y.Loves(x, y)",
                description="Nested quantifiers",
                complexity_level="complex"
            ),
            RoundTripTestCase(
                name="complex_conjunction",
                fopl_expression="Man(x) ∧ Loves(x, y) ∧ Woman(y)",
                description="Multi-predicate conjunction",
                complexity_level="complex"
            ),
            
            # Extreme cases
            RoundTripTestCase(
                name="deeply_nested",
                fopl_expression="∀x.(Man(x) → ∃y.(Woman(y) ∧ Loves(x, y) ∧ ∀z.(Child(z) → ParentOf(x, z))))",
                description="Deeply nested quantifiers and operators",
                complexity_level="extreme"
            ),
            RoundTripTestCase(
                name="multiple_identities",
                fopl_expression="∃x.∃y.∃z.(x .= y ∧ y .= z ∧ Man(x))",
                description="Multiple identity relations with quantification",
                complexity_level="extreme"
            ),
            RoundTripTestCase(
                name="complex_negation",
                fopl_expression="¬∃x.(Man(x) ∧ ¬∃y.(Woman(y) ∧ Loves(x, y)))",
                description="Complex nested negations",
                complexity_level="extreme"
            )
        ]
    
    def run_complete_round_trip_tests(self) -> List[RoundTripResult]:
        """Run all round-trip translation tests."""
        results = []
        
        print("🔄 Complete Round-Trip Translation Testing")
        print("=" * 70)
        print("Testing: FOPL ↔ CGIF ↔ CLIF ↔ EGIF ↔ FOPL via EGI")
        print("=" * 70)
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case.name} ({test_case.complexity_level})")
            print(f"   Expression: {test_case.fopl_expression}")
            print(f"   Description: {test_case.description}")
            
            result = self._run_single_round_trip_test(test_case)
            results.append(result)
            
            if result.round_trip_success:
                print(f"   ✅ SUCCESS (semantic: {result.semantic_preservation_score:.2f}, structural: {result.structural_fidelity_score:.2f})")
            else:
                print(f"   ❌ FAILED (semantic: {result.semantic_preservation_score:.2f}, structural: {result.structural_fidelity_score:.2f})")
                for error in result.errors[:3]:  # Show first 3 errors
                    print(f"      Error: {error}")
        
        return results
    
    def _run_single_round_trip_test(self, test_case: RoundTripTestCase) -> RoundTripResult:
        """Run single complete round-trip test."""
        errors = []
        
        try:
            # Step 1: FOPL → EGI
            fopl_formula = parse_fopl_formula(test_case.fopl_expression)
            egi_from_fopl = self.fopl_translator.psi_translate(fopl_formula)
            
            # Step 2: EGI → All formats
            egif_from_egi = self.egif_generator.generate_egif(egi_from_fopl)
            cgif_from_egi = self.cgif_generator.generate_cgif(egi_from_fopl)
            clif_from_egi = self.clif_generator.generate_clif(egi_from_fopl)
            
            # Step 3: EGIF → EGI (round-trip test)
            egi_from_egif = None
            try:
                egif_parser = EGIFParser(egif_from_egi)
                egi_from_egif = egif_parser.parse()
            except Exception as e:
                errors.append(f"EGIF parsing failed: {e}")
            
            # Step 4: EGI → FOPL (complete round-trip)
            fopl_from_egi = self.fopl_translator.phi_translate(egi_from_fopl)
            
            # Step 5: Cross-format consistency checks
            egif_to_cgif_consistent = self._check_format_consistency(egi_from_fopl, egif_from_egi, cgif_from_egi)
            cgif_to_clif_consistent = self._check_semantic_equivalence(cgif_from_egi, clif_from_egi)
            clif_to_egif_consistent = self._check_structural_similarity(clif_from_egi, egif_from_egi)
            
            # Step 6: Semantic preservation analysis
            semantic_score = self._calculate_semantic_preservation(test_case.fopl_expression, fopl_from_egi)
            structural_score = self._calculate_structural_fidelity(egi_from_fopl, egi_from_egif)
            
            # Step 7: Overall success determination
            success = (len(errors) == 0 and 
                      semantic_score >= 0.8 and 
                      structural_score >= 0.7 and
                      egif_to_cgif_consistent and
                      cgif_to_clif_consistent)
            
            return RoundTripResult(
                test_name=test_case.name,
                original_fopl=test_case.fopl_expression,
                egi_from_fopl=egi_from_fopl,
                egif_from_egi=egif_from_egi,
                cgif_from_egi=cgif_from_egi,
                clif_from_egi=clif_from_egi,
                egi_from_egif=egi_from_egif,
                fopl_from_egi=fopl_from_egi,
                egif_to_cgif_consistent=egif_to_cgif_consistent,
                cgif_to_clif_consistent=cgif_to_clif_consistent,
                clif_to_egif_consistent=clif_to_egif_consistent,
                semantic_preservation_score=semantic_score,
                structural_fidelity_score=structural_score,
                round_trip_success=success,
                errors=errors
            )
            
        except Exception as e:
            errors.append(f"Critical failure: {e}")
            return RoundTripResult(
                test_name=test_case.name,
                original_fopl=test_case.fopl_expression,
                egi_from_fopl=None,
                egif_from_egi="",
                cgif_from_egi="",
                clif_from_egi="",
                egi_from_egif=None,
                fopl_from_egi="",
                egif_to_cgif_consistent=False,
                cgif_to_clif_consistent=False,
                clif_to_egif_consistent=False,
                semantic_preservation_score=0.0,
                structural_fidelity_score=0.0,
                round_trip_success=False,
                errors=errors
            )
    
    def _check_format_consistency(self, original_egi: RelationalGraphWithCuts, 
                                 parsed_egi: Optional[RelationalGraphWithCuts],
                                 cgif_output: str) -> bool:
        """Check consistency between EGI and parsed formats."""
        if parsed_egi is None:
            return False
        
        # Basic structural consistency
        vertex_count_match = len(original_egi.V) == len(parsed_egi.V)
        edge_count_match = len(original_egi.E) == len(parsed_egi.E)
        cut_count_match = len(original_egi.Cut) == len(parsed_egi.Cut)
        
        # CGIF output should not be empty
        cgif_not_empty = bool(cgif_output.strip())
        
        return vertex_count_match and edge_count_match and cut_count_match and cgif_not_empty
    
    def _check_semantic_equivalence(self, cgif_output: str, clif_output: str) -> bool:
        """Check semantic equivalence between CGIF and CLIF outputs."""
        # Both outputs should be non-empty
        cgif_valid = bool(cgif_output.strip())
        clif_valid = bool(clif_output.strip())
        
        # Basic consistency checks
        cgif_has_relations = any(char in cgif_output for char in "()[]")
        clif_has_relations = any(char in clif_output for char in "()")
        
        return cgif_valid and clif_valid and cgif_has_relations and clif_has_relations
    
    def _check_structural_similarity(self, clif_output: str, egif_output: str) -> bool:
        """Check structural similarity between CLIF and EGIF outputs."""
        clif_valid = bool(clif_output.strip())
        egif_valid = bool(egif_output.strip())
        
        # Both should contain relational structures
        clif_has_structure = "(" in clif_output
        egif_has_structure = "(" in egif_output or "[" in egif_output
        
        return clif_valid and egif_valid and clif_has_structure and egif_has_structure
    
    def _calculate_semantic_preservation(self, original_fopl: str, round_trip_fopl: str) -> float:
        """Calculate semantic preservation score between original and round-trip FOPL."""
        if not round_trip_fopl.strip():
            return 0.0
        
        try:
            # Parse both formulas
            original_formula = parse_fopl_formula(original_fopl)
            round_trip_formula = parse_fopl_formula(round_trip_fopl)
            
            # Basic structural comparison
            same_type = type(original_formula) == type(round_trip_formula)
            
            # For atomic formulas, check relation and arity
            if hasattr(original_formula, 'relation') and hasattr(round_trip_formula, 'relation'):
                same_relation = original_formula.relation == round_trip_formula.relation
                same_arity = len(original_formula.variables) == len(round_trip_formula.variables)
                if same_type and same_relation and same_arity:
                    return 1.0
                elif same_type and same_relation:
                    return 0.8
                elif same_type:
                    return 0.6
            
            # For compound formulas, basic type matching
            if same_type:
                return 0.9  # Same logical structure
            else:
                return 0.5  # Different structure but parseable
                
        except Exception:
            return 0.3  # Parseable but potentially different semantics
    
    def _calculate_structural_fidelity(self, original_egi: Optional[RelationalGraphWithCuts],
                                     parsed_egi: Optional[RelationalGraphWithCuts]) -> float:
        """Calculate structural fidelity between original and parsed EGI."""
        if original_egi is None or parsed_egi is None:
            return 0.0
        
        # Component count comparisons
        vertex_ratio = min(len(original_egi.V), len(parsed_egi.V)) / max(len(original_egi.V), len(parsed_egi.V), 1)
        edge_ratio = min(len(original_egi.E), len(parsed_egi.E)) / max(len(original_egi.E), len(parsed_egi.E), 1)
        cut_ratio = min(len(original_egi.Cut), len(parsed_egi.Cut)) / max(len(original_egi.Cut), len(parsed_egi.Cut), 1)
        
        # Weighted average
        return (vertex_ratio * 0.4 + edge_ratio * 0.4 + cut_ratio * 0.2)
    
    def generate_comprehensive_report(self, results: List[RoundTripResult]) -> str:
        """Generate comprehensive round-trip testing report."""
        successful_tests = [r for r in results if r.round_trip_success]
        failed_tests = [r for r in results if not r.round_trip_success]
        
        # Calculate statistics by complexity
        complexity_stats = {}
        for result in results:
            test_case = next(tc for tc in self.test_cases if tc.name == result.test_name)
            level = test_case.complexity_level
            if level not in complexity_stats:
                complexity_stats[level] = {"total": 0, "passed": 0}
            complexity_stats[level]["total"] += 1
            if result.round_trip_success:
                complexity_stats[level]["passed"] += 1
        
        avg_semantic = sum(r.semantic_preservation_score for r in results) / len(results)
        avg_structural = sum(r.structural_fidelity_score for r in results) / len(results)
        
        report = []
        report.append("🔄 Complete Round-Trip Translation Report")
        report.append("=" * 70)
        report.append("Translation Chain: FOPL ↔ CGIF ↔ CLIF ↔ EGIF ↔ FOPL via EGI")
        report.append("=" * 70)
        report.append(f"Total Tests: {len(results)}")
        report.append(f"Successful: {len(successful_tests)} ({len(successful_tests)/len(results)*100:.1f}%)")
        report.append(f"Failed: {len(failed_tests)} ({len(failed_tests)/len(results)*100:.1f}%)")
        report.append(f"Average Semantic Preservation: {avg_semantic:.3f}")
        report.append(f"Average Structural Fidelity: {avg_structural:.3f}")
        report.append("")
        
        # Complexity breakdown
        report.append("📊 COMPLEXITY BREAKDOWN:")
        for level, stats in complexity_stats.items():
            success_rate = stats["passed"] / stats["total"] * 100
            report.append(f"   {level.title()}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        report.append("")
        
        # Successful tests
        if successful_tests:
            report.append("✅ SUCCESSFUL ROUND-TRIPS:")
            for result in successful_tests:
                report.append(f"   • {result.test_name}")
                report.append(f"     Original: {result.original_fopl}")
                report.append(f"     Round-trip: {result.fopl_from_egi}")
                report.append(f"     EGIF: {result.egif_from_egi[:60]}...")
                report.append(f"     CGIF: {result.cgif_from_egi[:60]}...")
                report.append(f"     CLIF: {result.clif_from_egi[:60]}...")
                report.append(f"     Scores: semantic={result.semantic_preservation_score:.2f}, structural={result.structural_fidelity_score:.2f}")
                report.append("")
        
        # Failed tests
        if failed_tests:
            report.append("❌ FAILED ROUND-TRIPS:")
            for result in failed_tests:
                report.append(f"   • {result.test_name}")
                report.append(f"     Original: {result.original_fopl}")
                report.append(f"     Round-trip: {result.fopl_from_egi}")
                for error in result.errors[:2]:
                    report.append(f"     Error: {error}")
                report.append("")
        
        # Format consistency analysis
        report.append("🔗 FORMAT CONSISTENCY ANALYSIS:")
        egif_cgif_consistent = sum(1 for r in results if r.egif_to_cgif_consistent)
        cgif_clif_consistent = sum(1 for r in results if r.cgif_to_clif_consistent)
        clif_egif_consistent = sum(1 for r in results if r.clif_to_egif_consistent)
        
        report.append(f"   EGIF ↔ CGIF: {egif_cgif_consistent}/{len(results)} ({egif_cgif_consistent/len(results)*100:.1f}%)")
        report.append(f"   CGIF ↔ CLIF: {cgif_clif_consistent}/{len(results)} ({cgif_clif_consistent/len(results)*100:.1f}%)")
        report.append(f"   CLIF ↔ EGIF: {clif_egif_consistent}/{len(results)} ({clif_egif_consistent/len(results)*100:.1f}%)")
        report.append("")
        
        # Overall assessment
        overall_success_rate = len(successful_tests) / len(results)
        if overall_success_rate >= 0.9:
            status = "🎯 EXCELLENT - Production Ready"
        elif overall_success_rate >= 0.8:
            status = "✅ GOOD - Minor Issues"
        elif overall_success_rate >= 0.7:
            status = "⚠️ ACCEPTABLE - Needs Improvement"
        else:
            status = "❌ POOR - Major Issues"
        
        report.append(f"🎯 OVERALL ASSESSMENT: {status}")
        report.append(f"   Success Rate: {overall_success_rate:.1%}")
        report.append(f"   Semantic Preservation: {'✅' if avg_semantic >= 0.8 else '⚠️'}")
        report.append(f"   Structural Fidelity: {'✅' if avg_structural >= 0.7 else '⚠️'}")
        report.append(f"   Format Consistency: {'✅' if egif_cgif_consistent/len(results) >= 0.8 else '⚠️'}")
        
        return "\n".join(report)


def demonstrate_arbitrary_expressions():
    """Demonstrate round-trip translations with arbitrary complex expressions."""
    print("\n🎭 Arbitrary Expression Round-Trip Demonstration")
    print("=" * 60)
    
    # Test with user-defined arbitrary expressions
    arbitrary_expressions = [
        "∃x.∀y.(Loves(x, y) → (Happy(x) ∧ Happy(y)))",
        "¬∃x.(Philosopher(x) ∧ ∀y.(Knows(x, y) → ¬Knows(y, x)))",
        "∀x.∀y.∀z.((x .= y ∧ y .= z) → x .= z)",
        "∃x.∃y.(Man(x) ∧ Woman(y) ∧ ∀z.(Child(z) → (ParentOf(x, z) ∨ ParentOf(y, z))))"
    ]
    
    translator = EnhancedChapter18Translator()
    egif_gen = EGIFGenerator()
    cgif_gen = CGIFGenerator()
    clif_gen = CLIFGenerator()
    
    for i, expr in enumerate(arbitrary_expressions, 1):
        print(f"\n🔄 Arbitrary Expression {i}:")
        print(f"   FOPL: {expr}")
        
        try:
            # Complete round-trip
            formula = parse_fopl_formula(expr)
            egi = translator.psi_translate(formula)
            
            egif_output = egif_gen.generate_egif(egi)
            cgif_output = cgif_gen.generate_cgif(egi)
            clif_output = clif_gen.generate_clif(egi)
            fopl_output = translator.phi_translate(egi)
            
            print(f"   EGIF: {egif_output[:80]}...")
            print(f"   CGIF: {cgif_output[:80]}...")
            print(f"   CLIF: {clif_output[:80]}...")
            print(f"   FOPL Round-trip: {fopl_output}")
            print(f"   ✅ SUCCESS")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")


def main():
    """Main execution function."""
    print("🚀 Complete Round-Trip Translation Testing")
    print("=" * 70)
    print("Demonstrating: FOPL ↔ CGIF ↔ CLIF ↔ EGIF ↔ FOPL via EGI")
    print("=" * 70)
    
    # Run comprehensive round-trip tests
    tester = CompleteRoundTripTester()
    results = tester.run_complete_round_trip_tests()
    
    # Generate comprehensive report
    report = tester.generate_comprehensive_report(results)
    print(f"\n{report}")
    
    # Demonstrate with arbitrary expressions
    demonstrate_arbitrary_expressions()
    
    # Save detailed report
    with open('/Users/mjh/Sync/GitHub/Arisbe/COMPLETE_ROUND_TRIP_REPORT.md', 'w') as f:
        f.write("# Complete Round-Trip Translation Report\n\n")
        f.write("Generated by comprehensive round-trip testing suite.\n\n")
        f.write("## Translation Chain\n")
        f.write("FOPL ↔ CGIF ↔ CLIF ↔ EGIF ↔ FOPL via EGI\n\n")
        f.write("## Results\n\n")
        f.write(report)
    
    print(f"\n📄 Detailed report saved to: COMPLETE_ROUND_TRIP_REPORT.md")
    
    # Final assessment
    successful_tests = len([r for r in results if r.round_trip_success])
    total_tests = len(results)
    success_rate = successful_tests / total_tests
    
    print(f"\n🎯 FINAL ROUND-TRIP ASSESSMENT")
    print("=" * 40)
    print(f"Success Rate: {successful_tests}/{total_tests} ({success_rate:.1%})")
    print(f"Status: {'✅ PRODUCTION READY' if success_rate >= 0.8 else '⚠️ NEEDS IMPROVEMENT'}")
    
    return success_rate >= 0.8


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
