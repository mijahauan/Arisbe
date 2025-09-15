"""
Comprehensive Test Specifications for Dau-based EGI System
Organized by Dau's formalism chapters 11-21

This module contains concrete test specifications covering:
a) EGI logical equivalence in transformation sequences
b) Transformation rule soundness 
c) Round-trip translation fidelity (EGIF/CGIF/CLIF/FOPL)
d) Dau formalism compliance (chapters 11-21)
"""

from .test_framework_schema import (
    TestSpecification, TestCategory, TestType, DauReference
)


# =============================================================================
# A) LOGICAL EQUIVALENCE TESTS
# =============================================================================

LOGICAL_EQUIVALENCE_SPECS = [
    TestSpecification(
        test_id="LE001_transformation_sequence_equivalence",
        title="Transformation Sequence Preserves Logical Equivalence",
        category=TestCategory.LOGICAL_EQUIVALENCE,
        test_type=TestType.EQUIVALENCE_CHECK,
        rationale="Any sequence of valid transformations must preserve the logical meaning of the original EGI",
        dau_reference=DauReference(chapter=13, theorem="13.7", page=312),
        description="Apply a sequence of transformations (IT+, IT-, INS, DNE) to an EGI and verify the result is logically equivalent to the original",
        expected_result="All EGIs in the transformation sequence are logically equivalent",
        input_data={
            "initial_egi": "placeholder_for_test_egi",
            "transformation_sequence": ["iteration", "deiteration", "insertion", "double_negation"]
        },
        priority="high",
        complexity="complex"
    ),
    
    TestSpecification(
        test_id="LE002_cut_polarity_equivalence",
        title="Even/Odd Cut Nesting Preserves Logical Meaning",
        category=TestCategory.LOGICAL_EQUIVALENCE,
        test_type=TestType.EQUIVALENCE_CHECK,
        rationale="Dau's polarity principle: even nesting depth = positive, odd = negative context",
        dau_reference=DauReference(chapter=11, section="11.2", page=245),
        description="Create EGIs with identical content at different nesting depths and verify logical equivalence based on polarity",
        expected_result="EGIs with same polarity (both even or both odd nesting) are equivalent; different polarity are negations",
        input_data={
            "base_formula": "Human(Socrates)",
            "even_nesting_depths": [0, 2, 4],
            "odd_nesting_depths": [1, 3, 5]
        },
        priority="high",
        complexity="moderate"
    ),
    
    TestSpecification(
        test_id="LE003_variable_shadowing_equivalence",
        title="Variable Shadowing Preserves Logical Scope",
        category=TestCategory.LOGICAL_EQUIVALENCE,
        test_type=TestType.EQUIVALENCE_CHECK,
        rationale="Variable shadowing in nested contexts must preserve logical meaning per Dau's scoping rules",
        dau_reference=DauReference(chapter=12, section="12.3", page=278),
        description="Test EGIs with variable shadowing across cut boundaries maintain logical equivalence",
        expected_result="Shadowed variables maintain proper scope and logical equivalence",
        input_data={
            "outer_variable": "x",
            "inner_variable": "x",  # Same name, different scope
            "predicate": "Human"
        },
        priority="medium",
        complexity="moderate"
    )
]


# =============================================================================
# B) TRANSFORMATION RULE SOUNDNESS TESTS
# =============================================================================

TRANSFORMATION_SOUNDNESS_SPECS = [
    TestSpecification(
        test_id="TR001_iteration_rule_soundness",
        title="IT+ (Iteration) Rule Preserves Semantic Equivalence",
        category=TestCategory.TRANSFORMATION_SOUNDNESS,
        test_type=TestType.SUCCESS_VALIDATION,
        rationale="Iteration rule must create semantically equivalent EGI by duplicating subgraphs",
        dau_reference=DauReference(chapter=15, definition="15.1", page=356),
        description="Apply IT+ rule to duplicate a subgraph and verify semantic equivalence",
        expected_result="Input EGI and output EGI are semantically equivalent",
        input_data={
            "rule_type": "iteration",
            "source_subgraph": "Human(Socrates)",
            "target_area": "positive_context"
        },
        priority="high",
        complexity="moderate"
    ),
    
    TestSpecification(
        test_id="TR002_deiteration_rule_soundness",
        title="IT- (Deiteration) Rule Preserves Semantic Equivalence",
        category=TestCategory.TRANSFORMATION_SOUNDNESS,
        test_type=TestType.SUCCESS_VALIDATION,
        rationale="Deiteration rule must preserve semantics when removing duplicate subgraphs",
        dau_reference=DauReference(chapter=15, definition="15.2", page=358),
        description="Apply IT- rule to remove duplicate subgraph and verify semantic equivalence",
        expected_result="Input EGI and output EGI are semantically equivalent",
        input_data={
            "rule_type": "deiteration",
            "duplicate_subgraphs": ["Human(Socrates)", "Human(Socrates)"],
            "removal_target": "deeper_nesting"
        },
        priority="high",
        complexity="moderate"
    ),
    
    TestSpecification(
        test_id="TR003_insertion_rule_soundness",
        title="INS (Insertion) Rule Preserves Semantic Equivalence",
        category=TestCategory.TRANSFORMATION_SOUNDNESS,
        test_type=TestType.SUCCESS_VALIDATION,
        rationale="Insertion rule must preserve semantics when moving subgraphs between contexts",
        dau_reference=DauReference(chapter=16, definition="16.1", page=378),
        description="Apply INS rule to move subgraph to different context and verify semantic equivalence",
        expected_result="Input EGI and output EGI are semantically equivalent",
        input_data={
            "rule_type": "insertion",
            "source_context": "positive_area",
            "target_context": "negative_area",
            "subgraph": "Mortal(x)"
        },
        priority="high",
        complexity="complex"
    ),
    
    TestSpecification(
        test_id="TR004_double_negation_soundness",
        title="DNE (Double Negation Elimination) Rule Soundness",
        category=TestCategory.TRANSFORMATION_SOUNDNESS,
        test_type=TestType.SUCCESS_VALIDATION,
        rationale="Double negation elimination must preserve logical equivalence",
        dau_reference=DauReference(chapter=17, theorem="17.3", page=402),
        description="Apply DNE rule to eliminate double cuts and verify semantic equivalence",
        expected_result="Input EGI and output EGI are semantically equivalent",
        input_data={
            "rule_type": "double_negation_elimination",
            "nested_cuts": 2,
            "inner_content": "Human(Socrates)"
        },
        priority="medium",
        complexity="simple"
    ),
    
    TestSpecification(
        test_id="TR005_invalid_transformation_detection",
        title="Invalid Transformation Rule Application Detection",
        category=TestCategory.TRANSFORMATION_SOUNDNESS,
        test_type=TestType.ERROR_DETECTION,
        rationale="System must reject invalid transformation attempts per Dau's preconditions",
        dau_reference=DauReference(chapter=15, section="15.3", page=362),
        description="Attempt invalid transformations and verify they are properly rejected",
        expected_result="Invalid transformations are detected and rejected with appropriate error messages",
        input_data={
            "invalid_cases": [
                {"rule": "deiteration", "error": "no_duplicate_found"},
                {"rule": "insertion", "error": "violates_nesting_constraint"},
                {"rule": "iteration", "error": "creates_inconsistency"}
            ]
        },
        priority="high",
        complexity="moderate"
    )
]


# =============================================================================
# C) ROUND-TRIP TRANSLATION FIDELITY TESTS
# =============================================================================

TRANSLATION_FIDELITY_SPECS = [
    TestSpecification(
        test_id="RT001_egif_cgif_roundtrip",
        title="EGIF ↔ CGIF Round-trip Translation Fidelity",
        category=TestCategory.TRANSLATION_FIDELITY,
        test_type=TestType.EQUIVALENCE_CHECK,
        rationale="EGIF and CGIF must be perfectly interconvertible without loss of information",
        dau_reference=DauReference(chapter=18, section="18.1", page=425),
        description="Convert EGIF to EGI to CGIF and back, verifying structural preservation",
        expected_result="Original and round-trip EGIF are structurally equivalent",
        input_data={
            "source_format": "EGIF",
            "target_format": "CGIF",
            "test_expressions": [
                "[Human: Socrates]",
                "~[[Mortal: *x] [Human: *x]]",
                "[Human: *x] ~[~[Mortal: *x]]"
            ]
        },
        priority="high",
        complexity="moderate"
    ),
    
    TestSpecification(
        test_id="RT002_clif_fopl_roundtrip",
        title="CLIF ↔ FOPL Round-trip Translation Fidelity",
        category=TestCategory.TRANSLATION_FIDELITY,
        test_type=TestType.EQUIVALENCE_CHECK,
        rationale="CLIF and FOPL must preserve logical meaning through EGI intermediate form",
        dau_reference=DauReference(chapter=18, section="18.2", page=430),
        description="Convert CLIF to EGI to FOPL and verify logical equivalence",
        expected_result="CLIF and FOPL expressions are logically equivalent",
        input_data={
            "source_format": "CLIF",
            "target_format": "FOPL",
            "test_expressions": [
                "(Human Socrates)",
                "(not (and (Mortal ?x) (Human ?x)))",
                "(exists (?x) (and (Human ?x) (Mortal ?x)))"
            ]
        },
        priority="high",
        complexity="complex"
    ),
    
    TestSpecification(
        test_id="RT003_all_formats_consistency",
        title="Four-way Translation Consistency (EGIF/CGIF/CLIF/FOPL)",
        category=TestCategory.TRANSLATION_FIDELITY,
        test_type=TestType.EQUIVALENCE_CHECK,
        rationale="All linear forms must be mutually consistent through EGI representation",
        dau_reference=DauReference(chapter=18, theorem="18.5", page=445),
        description="Convert same logical content through all four linear forms and verify equivalence",
        expected_result="All four linear representations are logically equivalent",
        input_data={
            "base_logic": "∃x(Human(x) ∧ Mortal(x))",
            "formats": ["EGIF", "CGIF", "CLIF", "FOPL"]
        },
        priority="high",
        complexity="complex"
    ),
    
    TestSpecification(
        test_id="RT004_complex_nesting_preservation",
        title="Complex Nested Structure Preservation in Translation",
        category=TestCategory.TRANSLATION_FIDELITY,
        test_type=TestType.EQUIVALENCE_CHECK,
        rationale="Deep nesting and complex structures must be preserved across translations",
        dau_reference=DauReference(chapter=19, section="19.2", page=465),
        description="Test translation fidelity for deeply nested cuts and complex variable scoping",
        expected_result="Complex nested structures maintain fidelity across all translations",
        input_data={
            "complex_structures": [
                "Triple nested cuts with variable shadowing",
                "Multiple quantifier scopes",
                "Mixed positive/negative contexts"
            ]
        },
        priority="medium",
        complexity="complex"
    )
]


# =============================================================================
# D) DAU FORMALISM COMPLIANCE TESTS (Chapters 11-21)
# =============================================================================

DAU_COMPLIANCE_SPECS = [
    TestSpecification(
        test_id="DC001_six_component_structure",
        title="Dau's 6+1 Component EGI Structure Validation",
        category=TestCategory.DAU_COMPLIANCE,
        test_type=TestType.SUCCESS_VALIDATION,
        rationale="EGI must conform to Dau's formal definition: (V, E, ν, ⊤, Cut, area) + rel",
        dau_reference=DauReference(chapter=11, definition="11.1", page=240),
        description="Validate that all EGIs conform to the formal 6+1 component structure",
        expected_result="EGI structure matches Dau's formal definition exactly",
        input_data={
            "test_function": "validate_egi_structure",
            "validation_criteria": {
                "components": ["V", "E", "nu", "top", "Cut", "area", "rel"],
                "type_check": "RelationalGraphWithCuts"
            }
        },
        priority="high",
        complexity="simple"
    ),
    
    TestSpecification(
        test_id="DC002_cut_nesting_hierarchy",
        title="Cut Nesting Hierarchy Validation (Chapter 11)",
        category=TestCategory.DAU_COMPLIANCE,
        test_type=TestType.SUCCESS_VALIDATION,
        rationale="Cut nesting must form proper hierarchy with no overlaps per Dau's constraints",
        dau_reference=DauReference(chapter=11, section="11.3", page=250),
        description="Validate cut nesting forms proper tree structure without overlaps",
        expected_result="Cut hierarchy is valid tree structure",
        input_data={
            "test_function": "validate_cut_hierarchy",
            "validation_criteria": {"tree_structure": True, "no_overlaps": True}
        },
        priority="high",
        complexity="moderate"
    ),
    
    TestSpecification(
        test_id="DC003_variable_scoping_rules",
        title="Variable Scoping Rules Compliance (Chapter 12)",
        category=TestCategory.DAU_COMPLIANCE,
        test_type=TestType.SUCCESS_VALIDATION,
        rationale="Variable scoping must follow Dau's rules for cut boundaries and shadowing",
        dau_reference=DauReference(chapter=12, theorem="12.4", page=285),
        description="Validate variable scoping across cut boundaries follows Dau's rules",
        expected_result="Variable scoping is compliant with Dau's rules",
        input_data={
            "test_function": "validate_variable_scoping",
            "test_cases": [
                "simple_shadowing",
                "nested_quantification", 
                "cross_cut_references"
            ]
        },
        priority="high",
        complexity="moderate"
    ),
    
    TestSpecification(
        test_id="DC004_semantic_evaluation_correctness",
        title="Semantic Evaluation Correctness (Chapter 13)",
        category=TestCategory.DAU_COMPLIANCE,
        test_type=TestType.SUCCESS_VALIDATION,
        rationale="Semantic evaluation must follow Dau's truth conditions exactly",
        dau_reference=DauReference(chapter=13, definition="13.3", page=305),
        description="Validate semantic evaluation produces correct truth values per Dau's semantics",
        expected_result="Semantic evaluation matches Dau's truth conditions",
        input_data={
            "test_function": "validate_semantic_evaluation",
            "test_models": ["simple_universe", "complex_relations", "empty_domain"]
        },
        priority="high",
        complexity="complex"
    ),
    
    TestSpecification(
        test_id="DC005_transformation_preconditions",
        title="Transformation Rule Precondition Validation (Chapters 15-17)",
        category=TestCategory.DAU_COMPLIANCE,
        test_type=TestType.ERROR_DETECTION,
        rationale="All transformation rules must enforce Dau's preconditions strictly",
        dau_reference=DauReference(chapter=15, section="15.4", page=365),
        description="Validate that transformation rules properly check and enforce preconditions",
        expected_result="Invalid transformations are rejected with appropriate error messages",
        input_data={
            "transformation_rules": ["iteration", "deiteration", "insertion", "double_negation"],
            "invalid_cases": "generate_invalid_precondition_cases"
        },
        priority="high",
        complexity="moderate"
    ),
    
    TestSpecification(
        test_id="DC006_proof_sequence_validation",
        title="Proof Sequence Validation (Chapter 21)",
        category=TestCategory.DAU_COMPLIANCE,
        test_type=TestType.SUCCESS_VALIDATION,
        rationale="Proof sequences must follow Dau's rules for valid transformation chains",
        dau_reference=DauReference(chapter=21, theorem="21.2", page=510),
        description="Validate that proof sequences are well-formed per Dau's requirements",
        expected_result="Proof sequences are valid and maintain logical consistency",
        input_data={
            "test_function": "validate_proof_sequence",
            "proof_examples": [
                "simple_syllogism",
                "complex_nested_proof",
                "contradiction_derivation"
            ]
        },
        priority="medium",
        complexity="complex"
    )
]


# =============================================================================
# COMPREHENSIVE TEST REGISTRY
# =============================================================================

ALL_TEST_SPECIFICATIONS = (
    LOGICAL_EQUIVALENCE_SPECS +
    TRANSFORMATION_SOUNDNESS_SPECS +
    TRANSLATION_FIDELITY_SPECS +
    DAU_COMPLIANCE_SPECS
)


def get_tests_by_category(category: TestCategory) -> list:
    """Get all test specifications for a given category."""
    return [spec for spec in ALL_TEST_SPECIFICATIONS if spec.category == category]


def get_tests_by_priority(priority: str) -> list:
    """Get all test specifications for a given priority level."""
    return [spec for spec in ALL_TEST_SPECIFICATIONS if spec.priority == priority]


def get_tests_by_complexity(complexity: str) -> list:
    """Get all test specifications for a given complexity level."""
    return [spec for spec in ALL_TEST_SPECIFICATIONS if spec.complexity == complexity]


def get_test_by_id(test_id: str) -> TestSpecification:
    """Get specific test specification by ID."""
    for spec in ALL_TEST_SPECIFICATIONS:
        if spec.test_id == test_id:
            return spec
    raise ValueError(f"Test specification not found: {test_id}")


# Test Statistics
TOTAL_TESTS = len(ALL_TEST_SPECIFICATIONS)
HIGH_PRIORITY_TESTS = len(get_tests_by_priority("high"))
COMPLEX_TESTS = len(get_tests_by_complexity("complex"))

print(f"Comprehensive EGI Test Suite: {TOTAL_TESTS} total tests")
print(f"High Priority: {HIGH_PRIORITY_TESTS}, Complex: {COMPLEX_TESTS}")
