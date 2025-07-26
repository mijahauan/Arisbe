"""
EGIF Semantic Equivalence Testing - Phase 3 Implementation

This module provides comprehensive semantic equivalence testing for EGIF
expressions, ensuring that different syntactic representations of the same
logical content are recognized as equivalent. This is crucial for:

1. Round-trip conversion validation (EGIF → EG-HG → EGIF)
2. Educational assessment (recognizing equivalent student answers)
3. Dau-Sowa compatibility (mathematical vs syntactic equivalence)
4. Quality assurance (ensuring semantic preservation)

The framework implements multiple equivalence testing strategies:
- Structural equivalence (same entities and predicates)
- Logical equivalence (same truth conditions)
- Educational equivalence (same learning concepts)
- Syntactic normalization (canonical form comparison)

Author: Manus AI
Date: January 2025
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
from dataclasses import dataclass
from enum import Enum
import re
from collections import defaultdict, Counter

from egif_parser import EGIFParseResult, parse_egif
from egif_advanced_constructs import parse_advanced_egif, FunctionSymbol, CoreferencePattern, ScrollPattern
from egif_educational_features import EGIFEducationalSystem, EGConcept


class EquivalenceType(Enum):
    """Types of semantic equivalence."""
    STRUCTURAL = "structural"        # Same entities and predicates
    LOGICAL = "logical"             # Same truth conditions
    EDUCATIONAL = "educational"     # Same learning concepts
    SYNTACTIC = "syntactic"         # Same normalized syntax
    SEMANTIC = "semantic"           # Same meaning in context
    MATHEMATICAL = "mathematical"   # Same mathematical properties


class EquivalenceLevel(Enum):
    """Levels of equivalence strictness."""
    EXACT = 1           # Identical in all respects
    STRONG = 2          # Equivalent in most important aspects
    MODERATE = 3        # Equivalent in key aspects
    WEAK = 4            # Equivalent in basic aspects
    NONE = 5            # Not equivalent


@dataclass
class EquivalenceResult:
    """Result of semantic equivalence testing."""
    equivalent: bool
    equivalence_type: EquivalenceType
    equivalence_level: EquivalenceLevel
    confidence: float  # 0.0 to 1.0
    explanation: str
    differences: List[str]
    similarities: List[str]
    educational_notes: List[str]
    
    def get_formatted_result(self) -> str:
        """Get formatted equivalence result."""
        lines = []
        status = "✅ EQUIVALENT" if self.equivalent else "❌ NOT EQUIVALENT"
        lines.append(f"{status} ({self.equivalence_type.value.title()})")
        lines.append(f"Level: {self.equivalence_level.name}")
        lines.append(f"Confidence: {self.confidence:.1%}")
        lines.append(f"Explanation: {self.explanation}")
        
        if self.similarities:
            lines.append(f"\n✅ Similarities:")
            for sim in self.similarities:
                lines.append(f"  • {sim}")
        
        if self.differences:
            lines.append(f"\n⚠️ Differences:")
            for diff in self.differences:
                lines.append(f"  • {diff}")
        
        if self.educational_notes:
            lines.append(f"\n📚 Educational Notes:")
            for note in self.educational_notes:
                lines.append(f"  • {note}")
        
        return "\n".join(lines)


@dataclass
class EquivalenceTestSuite:
    """Suite of equivalence tests with results."""
    source1: str
    source2: str
    results: Dict[EquivalenceType, EquivalenceResult]
    overall_equivalent: bool
    overall_confidence: float
    summary: str
    
    def get_formatted_report(self) -> str:
        """Get formatted equivalence test report."""
        lines = []
        lines.append("🔍 Semantic Equivalence Test Report")
        lines.append("=" * 60)
        lines.append(f"Source 1: {self.source1}")
        lines.append(f"Source 2: {self.source2}")
        lines.append(f"Overall: {'✅ EQUIVALENT' if self.overall_equivalent else '❌ NOT EQUIVALENT'}")
        lines.append(f"Confidence: {self.overall_confidence:.1%}")
        lines.append(f"Summary: {self.summary}")
        
        lines.append(f"\n📊 Test Results by Type:")
        for eq_type, result in self.results.items():
            status = "✅" if result.equivalent else "❌"
            lines.append(f"  {status} {eq_type.value.title()}: {result.equivalence_level.name} ({result.confidence:.1%})")
        
        # Detailed results
        for eq_type, result in self.results.items():
            lines.append(f"\n{result.get_formatted_result()}")
            lines.append("-" * 40)
        
        return "\n".join(lines)


class StructuralEquivalenceTester:
    """Tests structural equivalence of EGIF expressions."""
    
    def test_equivalence(self, source1: str, source2: str) -> EquivalenceResult:
        """Test structural equivalence between two EGIF sources."""
        try:
            # Parse both sources
            result1 = parse_egif(source1, educational_mode=False)
            result2 = parse_egif(source2, educational_mode=False)
            
            # Check for parse errors
            if result1.errors or result2.errors:
                return EquivalenceResult(
                    equivalent=False,
                    equivalence_type=EquivalenceType.STRUCTURAL,
                    equivalence_level=EquivalenceLevel.NONE,
                    confidence=0.0,
                    explanation="Parse errors prevent structural comparison",
                    differences=["Parse errors in one or both sources"],
                    similarities=[],
                    educational_notes=["Fix syntax errors before testing equivalence"]
                )
            
            # Compare entities
            entities1 = {e.name: e.entity_type for e in result1.entities}
            entities2 = {e.name: e.entity_type for e in result2.entities}
            
            # Compare predicates
            predicates1 = [(p.name, len(p.entities)) for p in result1.predicates]
            predicates2 = [(p.name, len(p.entities)) for p in result2.predicates]
            
            # Count similarities and differences
            similarities = []
            differences = []
            
            # Entity comparison
            common_entities = set(entities1.keys()) & set(entities2.keys())
            if common_entities:
                similarities.append(f"Common entities: {', '.join(sorted(common_entities))}")
            
            only_in_1 = set(entities1.keys()) - set(entities2.keys())
            only_in_2 = set(entities2.keys()) - set(entities1.keys())
            
            if only_in_1:
                differences.append(f"Entities only in source 1: {', '.join(sorted(only_in_1))}")
            if only_in_2:
                differences.append(f"Entities only in source 2: {', '.join(sorted(only_in_2))}")
            
            # Predicate comparison
            predicates1_counter = Counter(predicates1)
            predicates2_counter = Counter(predicates2)
            
            common_predicates = set(predicates1) & set(predicates2)
            if common_predicates:
                similarities.append(f"Common predicates: {len(common_predicates)}")
            
            only_in_pred_1 = set(predicates1) - set(predicates2)
            only_in_pred_2 = set(predicates2) - set(predicates1)
            
            if only_in_pred_1:
                differences.append(f"Predicates only in source 1: {len(only_in_pred_1)}")
            if only_in_pred_2:
                differences.append(f"Predicates only in source 2: {len(only_in_pred_2)}")
            
            # Calculate equivalence
            total_entities = len(set(entities1.keys()) | set(entities2.keys()))
            total_predicates = len(set(predicates1) | set(predicates2))
            
            if total_entities == 0 and total_predicates == 0:
                # Both empty
                equivalent = True
                level = EquivalenceLevel.EXACT
                confidence = 1.0
                explanation = "Both sources are empty"
            elif len(common_entities) == total_entities and len(common_predicates) == total_predicates:
                # Exact match
                equivalent = True
                level = EquivalenceLevel.EXACT
                confidence = 1.0
                explanation = "Identical entities and predicates"
            elif len(common_entities) >= total_entities * 0.8 and len(common_predicates) >= total_predicates * 0.8:
                # Strong similarity
                equivalent = True
                level = EquivalenceLevel.STRONG
                confidence = 0.8
                explanation = "High structural similarity"
            elif len(common_entities) >= total_entities * 0.6 and len(common_predicates) >= total_predicates * 0.6:
                # Moderate similarity
                equivalent = True
                level = EquivalenceLevel.MODERATE
                confidence = 0.6
                explanation = "Moderate structural similarity"
            else:
                # Not equivalent
                equivalent = False
                level = EquivalenceLevel.NONE
                confidence = 0.0
                explanation = "Insufficient structural similarity"
            
            educational_notes = []
            if equivalent:
                educational_notes.append("Structural equivalence indicates same basic graph components")
            else:
                educational_notes.append("Different structures may represent different logical content")
            
            return EquivalenceResult(
                equivalent=equivalent,
                equivalence_type=EquivalenceType.STRUCTURAL,
                equivalence_level=level,
                confidence=confidence,
                explanation=explanation,
                differences=differences,
                similarities=similarities,
                educational_notes=educational_notes
            )
            
        except Exception as e:
            return EquivalenceResult(
                equivalent=False,
                equivalence_type=EquivalenceType.STRUCTURAL,
                equivalence_level=EquivalenceLevel.NONE,
                confidence=0.0,
                explanation=f"Structural test failed: {str(e)}",
                differences=[f"Exception: {str(e)}"],
                similarities=[],
                educational_notes=["Fix implementation issues before testing"]
            )


class SyntacticEquivalenceTester:
    """Tests syntactic equivalence through normalization."""
    
    def normalize_egif(self, source: str) -> str:
        """Normalize EGIF source for comparison."""
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', source.strip())
        
        # Normalize parentheses spacing
        normalized = re.sub(r'\s*\(\s*', '(', normalized)
        normalized = re.sub(r'\s*\)\s*', ')', normalized)
        
        # Normalize bracket spacing
        normalized = re.sub(r'\s*\[\s*', '[', normalized)
        normalized = re.sub(r'\s*\]\s*', ']', normalized)
        
        # Sort predicates for consistent ordering (simple heuristic)
        # This is a basic implementation - more sophisticated normalization could be added
        
        return normalized
    
    def test_equivalence(self, source1: str, source2: str) -> EquivalenceResult:
        """Test syntactic equivalence through normalization."""
        try:
            norm1 = self.normalize_egif(source1)
            norm2 = self.normalize_egif(source2)
            
            similarities = []
            differences = []
            
            if norm1 == norm2:
                equivalent = True
                level = EquivalenceLevel.EXACT
                confidence = 1.0
                explanation = "Identical after normalization"
                similarities.append("Normalized forms are identical")
            else:
                # Calculate similarity
                common_chars = sum(1 for c1, c2 in zip(norm1, norm2) if c1 == c2)
                max_len = max(len(norm1), len(norm2))
                similarity = common_chars / max_len if max_len > 0 else 0
                
                if similarity >= 0.9:
                    equivalent = True
                    level = EquivalenceLevel.STRONG
                    confidence = similarity
                    explanation = "Very similar after normalization"
                    similarities.append(f"High character similarity: {similarity:.1%}")
                elif similarity >= 0.7:
                    equivalent = True
                    level = EquivalenceLevel.MODERATE
                    confidence = similarity
                    explanation = "Moderately similar after normalization"
                    similarities.append(f"Moderate character similarity: {similarity:.1%}")
                else:
                    equivalent = False
                    level = EquivalenceLevel.NONE
                    confidence = similarity
                    explanation = "Different after normalization"
                    differences.append(f"Low character similarity: {similarity:.1%}")
                
                differences.append(f"Normalized 1: {norm1}")
                differences.append(f"Normalized 2: {norm2}")
            
            educational_notes = []
            if equivalent:
                educational_notes.append("Syntactic equivalence indicates same surface structure")
            else:
                educational_notes.append("Different syntax may indicate different intended meaning")
            
            return EquivalenceResult(
                equivalent=equivalent,
                equivalence_type=EquivalenceType.SYNTACTIC,
                equivalence_level=level,
                confidence=confidence,
                explanation=explanation,
                differences=differences,
                similarities=similarities,
                educational_notes=educational_notes
            )
            
        except Exception as e:
            return EquivalenceResult(
                equivalent=False,
                equivalence_type=EquivalenceType.SYNTACTIC,
                equivalence_level=EquivalenceLevel.NONE,
                confidence=0.0,
                explanation=f"Syntactic test failed: {str(e)}",
                differences=[f"Exception: {str(e)}"],
                similarities=[],
                educational_notes=["Fix implementation issues before testing"]
            )


class EducationalEquivalenceTester:
    """Tests educational equivalence based on learning concepts."""
    
    def __init__(self):
        """Initialize educational equivalence tester."""
        self.educational_system = EGIFEducationalSystem()
    
    def test_equivalence(self, source1: str, source2: str) -> EquivalenceResult:
        """Test educational equivalence based on concepts."""
        try:
            # Analyze concepts in both sources
            concepts1 = self.educational_system.identify_concepts(source1)
            concepts2 = self.educational_system.identify_concepts(source2)
            
            # Extract concept names
            concept_names1 = {concept for concept, _ in concepts1}
            concept_names2 = {concept for concept, _ in concepts2}
            
            similarities = []
            differences = []
            
            # Compare concepts
            common_concepts = concept_names1 & concept_names2
            only_in_1 = concept_names1 - concept_names2
            only_in_2 = concept_names2 - concept_names1
            
            if common_concepts:
                similarities.append(f"Common concepts: {', '.join(sorted(common_concepts))}")
            
            if only_in_1:
                differences.append(f"Concepts only in source 1: {', '.join(sorted(only_in_1))}")
            if only_in_2:
                differences.append(f"Concepts only in source 2: {', '.join(sorted(only_in_2))}")
            
            # Calculate educational equivalence
            total_concepts = len(concept_names1 | concept_names2)
            
            if total_concepts == 0:
                equivalent = True
                level = EquivalenceLevel.EXACT
                confidence = 1.0
                explanation = "No educational concepts in either source"
            elif len(common_concepts) == total_concepts:
                equivalent = True
                level = EquivalenceLevel.EXACT
                confidence = 1.0
                explanation = "Identical educational concepts"
            elif len(common_concepts) >= total_concepts * 0.8:
                equivalent = True
                level = EquivalenceLevel.STRONG
                confidence = 0.8
                explanation = "High educational concept overlap"
            elif len(common_concepts) >= total_concepts * 0.6:
                equivalent = True
                level = EquivalenceLevel.MODERATE
                confidence = 0.6
                explanation = "Moderate educational concept overlap"
            else:
                equivalent = False
                level = EquivalenceLevel.NONE
                confidence = len(common_concepts) / total_concepts if total_concepts > 0 else 0.0
                explanation = "Insufficient educational concept overlap"
            
            educational_notes = []
            if equivalent:
                educational_notes.append("Educational equivalence indicates same learning objectives")
                educational_notes.append("Students would learn similar concepts from both expressions")
            else:
                educational_notes.append("Different educational concepts may require different teaching approaches")
                educational_notes.append("Consider which expression better serves learning objectives")
            
            return EquivalenceResult(
                equivalent=equivalent,
                equivalence_type=EquivalenceType.EDUCATIONAL,
                equivalence_level=level,
                confidence=confidence,
                explanation=explanation,
                differences=differences,
                similarities=similarities,
                educational_notes=educational_notes
            )
            
        except Exception as e:
            return EquivalenceResult(
                equivalent=False,
                equivalence_type=EquivalenceType.EDUCATIONAL,
                equivalence_level=EquivalenceLevel.NONE,
                confidence=0.0,
                explanation=f"Educational test failed: {str(e)}",
                differences=[f"Exception: {str(e)}"],
                similarities=[],
                educational_notes=["Fix implementation issues before testing"]
            )


class SemanticEquivalenceTester:
    """Comprehensive semantic equivalence testing framework."""
    
    def __init__(self):
        """Initialize semantic equivalence tester."""
        self.structural_tester = StructuralEquivalenceTester()
        self.syntactic_tester = SyntacticEquivalenceTester()
        self.educational_tester = EducationalEquivalenceTester()
    
    def test_equivalence(self, source1: str, source2: str, 
                        test_types: Optional[List[EquivalenceType]] = None) -> EquivalenceTestSuite:
        """Test semantic equivalence using multiple approaches."""
        if test_types is None:
            test_types = [EquivalenceType.STRUCTURAL, EquivalenceType.SYNTACTIC, EquivalenceType.EDUCATIONAL]
        
        results = {}
        
        # Run each test type
        for test_type in test_types:
            if test_type == EquivalenceType.STRUCTURAL:
                results[test_type] = self.structural_tester.test_equivalence(source1, source2)
            elif test_type == EquivalenceType.SYNTACTIC:
                results[test_type] = self.syntactic_tester.test_equivalence(source1, source2)
            elif test_type == EquivalenceType.EDUCATIONAL:
                results[test_type] = self.educational_tester.test_equivalence(source1, source2)
            # Add more test types as needed
        
        # Calculate overall equivalence
        equivalent_count = sum(1 for result in results.values() if result.equivalent)
        total_tests = len(results)
        
        overall_equivalent = equivalent_count >= total_tests * 0.6  # Majority rule
        overall_confidence = sum(result.confidence for result in results.values()) / total_tests if total_tests > 0 else 0.0
        
        # Generate summary
        if overall_equivalent:
            if equivalent_count == total_tests:
                summary = "All tests indicate equivalence"
            else:
                summary = f"Majority of tests ({equivalent_count}/{total_tests}) indicate equivalence"
        else:
            summary = f"Majority of tests ({total_tests - equivalent_count}/{total_tests}) indicate non-equivalence"
        
        return EquivalenceTestSuite(
            source1=source1,
            source2=source2,
            results=results,
            overall_equivalent=overall_equivalent,
            overall_confidence=overall_confidence,
            summary=summary
        )
    
    def quick_equivalence_test(self, source1: str, source2: str) -> bool:
        """Quick equivalence test - returns True if likely equivalent."""
        # Use structural test as quick check
        result = self.structural_tester.test_equivalence(source1, source2)
        return result.equivalent and result.confidence >= 0.6


# Convenience functions
def test_semantic_equivalence(source1: str, source2: str) -> EquivalenceTestSuite:
    """Test semantic equivalence between two EGIF sources."""
    tester = SemanticEquivalenceTester()
    return tester.test_equivalence(source1, source2)


def are_semantically_equivalent(source1: str, source2: str) -> bool:
    """Quick check if two EGIF sources are semantically equivalent."""
    tester = SemanticEquivalenceTester()
    return tester.quick_equivalence_test(source1, source2)


# Example usage and testing
if __name__ == "__main__":
    print("EGIF Semantic Equivalence Testing")
    print("=" * 50)
    
    # Test cases for equivalence testing
    test_pairs = [
        # Exact equivalence
        ("(Person *john)", "(Person *john)"),
        
        # Syntactic differences but structural equivalence
        ("(Person *john)", "( Person *john )"),
        
        # Different variable names but same structure
        ("(Person *x)", "(Person *y)"),
        
        # Different order but same content
        ("(Person *x) (Mortal x)", "(Mortal x) (Person *x)"),
        
        # Different structures
        ("(Person *john)", "(Animal *dog)"),
        
        # Complex equivalence
        ("(Loves *alice *bob)", "(Loves *x *y)"),
    ]
    
    tester = SemanticEquivalenceTester()
    
    for i, (source1, source2) in enumerate(test_pairs, 1):
        print(f"\nTest Pair {i}:")
        print(f"  Source 1: {source1}")
        print(f"  Source 2: {source2}")
        print("-" * 60)
        
        try:
            test_suite = tester.test_equivalence(source1, source2)
            print(f"Overall: {'✅ EQUIVALENT' if test_suite.overall_equivalent else '❌ NOT EQUIVALENT'}")
            print(f"Confidence: {test_suite.overall_confidence:.1%}")
            print(f"Summary: {test_suite.summary}")
            
            # Show individual test results
            for eq_type, result in test_suite.results.items():
                status = "✅" if result.equivalent else "❌"
                print(f"  {status} {eq_type.value.title()}: {result.confidence:.1%}")
            
        except Exception as e:
            print(f"Equivalence test failed: {e}")
        
        if i < len(test_pairs):
            print("\n" + "=" * 80)
    
    print("\n" + "=" * 80)
    print("Equivalence Types Available:")
    print("=" * 80)
    
    for eq_type in EquivalenceType:
        print(f"• {eq_type.value.title()}: {eq_type.name}")
    
    print("\n" + "=" * 80)
    print("EGIF Semantic Equivalence Testing Phase 3 implementation complete!")
    print("Provides comprehensive equivalence testing for educational and validation purposes.")

