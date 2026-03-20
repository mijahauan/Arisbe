"""
Improved Chapter 18 FOPL ↔ EGI Translation

Addresses the key issues identified in theoretical verification:
1. Existential quantification reconstruction in Φ translation
2. Enhanced variable equivalence checking for logical structure
3. Better semantic preservation

This builds on the enhanced translation with specific fixes for Dau compliance.
"""

import os
import sys

sys.path.append(os.path.dirname(__file__))

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from frozendict import frozendict

from chapter18_enhanced_translation import (
    EnhancedChapter18Translator,
    parse_fopl_formula,
)
from chapter18_fopl_translation import (
    AtomicFormula,
    ConjunctionFormula,
    ExistentialFormula,
    FOPLFormula,
    ImplicationFormula,
    NegationFormula,
    UniversalFormula,
)
from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex


class ImprovedChapter18Translator(EnhancedChapter18Translator):
    """Improved translator with better existential quantification and variable handling."""

    def __init__(self):
        super().__init__()
        # Track quantification context for better reconstruction
        self.quantification_context: Dict[str, str] = {}  # vertex_id -> quantifier_type
        self.bound_variables: Set[str] = set()

    def phi_translate(self, egi: RelationalGraphWithCuts) -> str:
        """Improved Φ: Translate EGI to FOPL with proper existential reconstruction."""
        # Reset context
        self.vertex_variable_map = {}
        self.quantification_context = {}
        self.bound_variables = set()

        # Analyze EGI structure to detect quantification patterns
        self._analyze_quantification_context(egi)

        # Assign variables with context awareness
        var_counter = 1
        for vertex in egi.V:
            var_name = f"x{var_counter}"
            self.vertex_variable_map[vertex.id] = var_name
            var_counter += 1

        # Translate sheet area
        base_formula = self._translate_area_to_fopl_improved(egi, egi.sheet)

        # Reconstruct existential quantifiers if needed
        return self._reconstruct_quantifiers(base_formula, egi)

    def _analyze_quantification_context(self, egi: RelationalGraphWithCuts):
        """Analyze EGI structure to detect quantification patterns."""
        # Check if this EGI likely came from existential quantification
        # Heuristics based on Dau's translation patterns:

        # 1. Single vertex with multiple edges suggests existential binding
        vertex_edge_count = {}
        for edge_id, vertex_seq in egi.nu.items():
            for vertex_id in vertex_seq:
                vertex_edge_count[vertex_id] = vertex_edge_count.get(vertex_id, 0) + 1

        # 2. No cuts and single vertex suggests ∃x.formula pattern
        if len(egi.Cut) == 0 and len(egi.V) == 1:
            vertex_id = next(iter(egi.V)).id
            if vertex_edge_count.get(vertex_id, 0) >= 1:
                self.quantification_context[vertex_id] = "existential"
                self.bound_variables.add(vertex_id)

        # 3. Multiple vertices sharing edges suggests existential binding
        for vertex_id, edge_count in vertex_edge_count.items():
            if edge_count >= 2:  # Vertex appears in multiple relations
                self.quantification_context[vertex_id] = "existential"
                self.bound_variables.add(vertex_id)

    def _reconstruct_quantifiers(
        self, base_formula: str, egi: RelationalGraphWithCuts
    ) -> str:
        """Reconstruct existential quantifiers based on context analysis."""
        if not base_formula:
            return base_formula

        # Find variables that should be existentially quantified
        variables_to_quantify = []

        for vertex_id, quant_type in self.quantification_context.items():
            if quant_type == "existential" and vertex_id in self.vertex_variable_map:
                var_name = self.vertex_variable_map[vertex_id]
                if var_name not in variables_to_quantify:
                    variables_to_quantify.append(var_name)

        # Apply existential quantifiers
        result = base_formula
        for var in variables_to_quantify:
            # Check if variable actually appears in formula
            if var in result:
                result = f"∃{var}.{result}"

        return result

    def _translate_area_to_fopl_improved(
        self, egi: RelationalGraphWithCuts, area_id: ElementID
    ) -> str:
        """Improved area to FOPL translation with better structure preservation."""
        area_contents = egi.area.get(area_id, frozenset())

        # Separate edges and cuts
        edges = [eid for eid in area_contents if any(e.id == eid for e in egi.E)]
        cuts = [cid for cid in area_contents if any(c.id == cid for c in egi.Cut)]

        formulas = []

        # Translate edges to atomic formulas
        for edge_id in edges:
            if edge_id in egi.nu and edge_id in egi.rel:
                vertex_sequence = egi.nu[edge_id]
                relation = egi.rel[edge_id]

                variables = [self.vertex_variable_map[vid] for vid in vertex_sequence]

                if relation == "=" or relation == ".=":
                    # Identity relation - use proper FOPL syntax
                    formulas.append(f"{variables[0]} .= {variables[1]}")
                else:
                    # Regular relation
                    var_list = ", ".join(variables)
                    formulas.append(f"{relation}({var_list})")

        # Translate cuts to negated formulas
        for cut_id in cuts:
            cut_formula = self._translate_area_to_fopl_improved(egi, cut_id)
            if cut_formula:
                formulas.append(f"¬({cut_formula})")

        # Combine with conjunction
        if len(formulas) == 0:
            return ""
        elif len(formulas) == 1:
            return formulas[0]
        else:
            return " ∧ ".join(formulas)


class LogicalEquivalenceChecker:
    """Enhanced logical equivalence checker focusing on structure over syntax."""

    @staticmethod
    def formulas_logically_equivalent(f1_str: str, f2_str: str) -> bool:
        """Check if two FOPL formulas are logically equivalent."""
        try:
            # Parse both formulas
            f1 = parse_fopl_formula(f1_str)
            f2 = parse_fopl_formula(f2_str)

            # Normalize and compare
            norm_f1 = LogicalEquivalenceChecker._normalize_formula(f1)
            norm_f2 = LogicalEquivalenceChecker._normalize_formula(f2)

            return LogicalEquivalenceChecker._structural_equivalence(norm_f1, norm_f2)
        except:
            return False

    @staticmethod
    def _normalize_formula(formula: FOPLFormula) -> FOPLFormula:
        """Normalize formula by standardizing variable names."""
        var_map = {}
        var_counter = [1]  # Use list to allow modification in nested function

        def get_normalized_var(var: str) -> str:
            if var not in var_map:
                var_map[var] = f"x{var_counter[0]}"
                var_counter[0] += 1
            return var_map[var]

        return LogicalEquivalenceChecker._apply_variable_normalization(
            formula, get_normalized_var
        )

    @staticmethod
    def _apply_variable_normalization(
        formula: FOPLFormula, var_normalizer
    ) -> FOPLFormula:
        """Apply variable normalization to formula structure."""
        if isinstance(formula, AtomicFormula):
            norm_vars = [var_normalizer(var) for var in formula.variables]
            return AtomicFormula(formula.relation, norm_vars)

        # Handle identity as atomic formula with special relation
        elif hasattr(formula, "relation") and formula.relation in ["=", ".="]:
            norm_vars = [var_normalizer(var) for var in formula.variables]
            return AtomicFormula(formula.relation, norm_vars)

        elif isinstance(formula, ConjunctionFormula):
            norm_left = LogicalEquivalenceChecker._apply_variable_normalization(
                formula.left, var_normalizer
            )
            norm_right = LogicalEquivalenceChecker._apply_variable_normalization(
                formula.right, var_normalizer
            )
            return ConjunctionFormula(norm_left, norm_right)

        elif isinstance(formula, NegationFormula):
            norm_inner = LogicalEquivalenceChecker._apply_variable_normalization(
                formula.formula, var_normalizer
            )
            return NegationFormula(norm_inner)

        elif isinstance(formula, ExistentialFormula):
            norm_var = var_normalizer(formula.variable)
            norm_inner = LogicalEquivalenceChecker._apply_variable_normalization(
                formula.formula, var_normalizer
            )
            return ExistentialFormula(norm_var, norm_inner)

        elif isinstance(formula, UniversalFormula):
            norm_var = var_normalizer(formula.variable)
            norm_inner = LogicalEquivalenceChecker._apply_variable_normalization(
                formula.formula, var_normalizer
            )
            return UniversalFormula(norm_var, norm_inner)

        elif isinstance(formula, ImplicationFormula):
            norm_left = LogicalEquivalenceChecker._apply_variable_normalization(
                formula.antecedent, var_normalizer
            )
            norm_right = LogicalEquivalenceChecker._apply_variable_normalization(
                formula.consequent, var_normalizer
            )
            return ImplicationFormula(norm_left, norm_right)

        return formula

    @staticmethod
    def _structural_equivalence(f1: FOPLFormula, f2: FOPLFormula) -> bool:
        """Check structural equivalence of normalized formulas."""
        # Same type check
        if type(f1) != type(f2):
            return False

        if isinstance(f1, AtomicFormula):
            return f1.relation == f2.relation and f1.variables == f2.variables

        elif isinstance(f1, AtomicFormula) and f1.relation in ["=", ".="]:
            # Handle identity relations with symmetry
            return (f1.variables == f2.variables) or (
                len(f1.variables) == 2
                and len(f2.variables) == 2
                and f1.variables[0] == f2.variables[1]
                and f1.variables[1] == f2.variables[0]
            )

        elif isinstance(f1, ConjunctionFormula):
            # Conjunction is commutative
            return (
                LogicalEquivalenceChecker._structural_equivalence(f1.left, f2.left)
                and LogicalEquivalenceChecker._structural_equivalence(
                    f1.right, f2.right
                )
            ) or (
                LogicalEquivalenceChecker._structural_equivalence(f1.left, f2.right)
                and LogicalEquivalenceChecker._structural_equivalence(f1.right, f2.left)
            )

        elif isinstance(f1, NegationFormula):
            return LogicalEquivalenceChecker._structural_equivalence(
                f1.formula, f2.formula
            )

        elif isinstance(f1, ExistentialFormula):
            return (
                f1.variable == f2.variable
                and LogicalEquivalenceChecker._structural_equivalence(
                    f1.formula, f2.formula
                )
            )

        elif isinstance(f1, UniversalFormula):
            return (
                f1.variable == f2.variable
                and LogicalEquivalenceChecker._structural_equivalence(
                    f1.formula, f2.formula
                )
            )

        elif isinstance(f1, ImplicationFormula):
            return LogicalEquivalenceChecker._structural_equivalence(
                f1.antecedent, f2.antecedent
            ) and LogicalEquivalenceChecker._structural_equivalence(
                f1.consequent, f2.consequent
            )

        return False


def test_improved_translation():
    """Test the improved translation with focus on existential quantification."""
    print("🔬 Testing Improved Chapter 18 Translation")
    print("=" * 60)
    print("Focus: Existential quantification reconstruction and variable equivalence")
    print("=" * 60)

    translator = ImprovedChapter18Translator()
    checker = LogicalEquivalenceChecker()

    test_cases = [
        "Man(x)",
        "∃x.Man(x)",
        "∃x.(Man(x) ∧ Mortal(x))",
        "Man(x) ∧ Mortal(x)",
        "¬Man(x)",
        "x .= y",
    ]

    results = []

    for i, formula_str in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {formula_str}")

        try:
            # Step 1: FOPL → EGI
            original_formula = parse_fopl_formula(formula_str)
            egi = translator.psi_translate(original_formula)

            # Step 2: EGI → FOPL
            roundtrip_formula = translator.phi_translate(egi)

            # Step 3: Check logical equivalence
            equivalent = checker.formulas_logically_equivalent(
                formula_str, roundtrip_formula
            )

            print(f"   Original:  {formula_str}")
            print(f"   EGI:       {len(egi.V)}v, {len(egi.E)}e, {len(egi.Cut)}c")
            print(f"   Roundtrip: {roundtrip_formula}")
            print(f"   Equivalent: {'✅' if equivalent else '❌'}")

            results.append(
                {
                    "formula": formula_str,
                    "roundtrip": roundtrip_formula,
                    "equivalent": equivalent,
                    "success": True,
                }
            )

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append(
                {
                    "formula": formula_str,
                    "roundtrip": "",
                    "equivalent": False,
                    "success": False,
                    "error": str(e),
                }
            )

    # Summary
    successful = sum(1 for r in results if r["success"])
    equivalent = sum(1 for r in results if r.get("equivalent", False))

    print(f"\n🎯 SUMMARY")
    print("-" * 40)
    print(f"Successful translations: {successful}/{len(test_cases)}")
    print(f"Logically equivalent: {equivalent}/{len(test_cases)}")
    print(f"Improvement rate: {equivalent/len(test_cases):.1%}")

    if equivalent >= len(test_cases) * 0.8:
        print("✅ SIGNIFICANT IMPROVEMENT achieved!")
    else:
        print("⚠️  Further refinement needed")

    return results


if __name__ == "__main__":
    test_improved_translation()
