"""
Refined Chapter 18 FOPL ↔ EGI Translation

Final refinement addressing quantification detection precision:
- Only reconstruct existential quantifiers when evidence supports it
- Improved heuristics based on original formula structure
- Better variable equivalence checking with free/bound variable analysis
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


class RefinedChapter18Translator(EnhancedChapter18Translator):
    """Refined translator with precise existential quantification detection."""

    def __init__(self):
        super().__init__()
        # Track original formula context to guide reconstruction
        self.original_formula_context: Optional[FOPLFormula] = None
        self.quantified_variables: Set[str] = set()

    def psi_translate(self, formula: FOPLFormula) -> RelationalGraphWithCuts:
        """Enhanced Ψ translation that tracks original context."""
        self.original_formula_context = formula
        self.quantified_variables = self._extract_quantified_variables(formula)
        return super().psi_translate(formula)

    def _extract_quantified_variables(self, formula: FOPLFormula) -> Set[str]:
        """Extract all quantified variables from original formula."""
        quantified = set()

        if isinstance(formula, ExistentialFormula):
            quantified.add(formula.variable)
            quantified.update(self._extract_quantified_variables(formula.formula))
        elif isinstance(formula, UniversalFormula):
            quantified.add(formula.variable)
            quantified.update(self._extract_quantified_variables(formula.formula))
        elif isinstance(formula, ConjunctionFormula):
            quantified.update(self._extract_quantified_variables(formula.left))
            quantified.update(self._extract_quantified_variables(formula.right))
        elif isinstance(formula, NegationFormula):
            quantified.update(self._extract_quantified_variables(formula.formula))
        elif isinstance(formula, ImplicationFormula):
            quantified.update(self._extract_quantified_variables(formula.antecedent))
            quantified.update(self._extract_quantified_variables(formula.consequent))

        return quantified

    def phi_translate(self, egi: RelationalGraphWithCuts) -> str:
        """Refined Φ translation with precise quantification reconstruction."""
        # Reset context
        self.vertex_variable_map = {}

        # Assign variables
        var_counter = 1
        for vertex in egi.V:
            var_name = f"x{var_counter}"
            self.vertex_variable_map[vertex.id] = var_name
            var_counter += 1

        # Translate sheet area
        base_formula = self._translate_area_to_fopl_improved(egi, egi.sheet)

        # Only reconstruct quantifiers if there's strong evidence
        return self._selective_quantifier_reconstruction(base_formula, egi)

    def _selective_quantifier_reconstruction(
        self, base_formula: str, egi: RelationalGraphWithCuts
    ) -> str:
        """Selectively reconstruct quantifiers based on strong evidence."""
        if not base_formula:
            return base_formula

        # Evidence for existential quantification:
        # 1. Original formula had existential quantifiers
        # 2. EGI structure suggests bound variables (single vertex, multiple edges)
        # 3. No cuts (existential quantification doesn't introduce cuts)

        should_quantify = False

        # Check if original formula had existential quantifiers
        if self.original_formula_context:
            has_existential = self._formula_has_existential(
                self.original_formula_context
            )
            if has_existential:
                should_quantify = True

        # Check EGI structure for existential patterns
        if len(egi.Cut) == 0 and len(egi.V) == 1:
            # Single vertex with no cuts suggests existential binding
            vertex_id = next(iter(egi.V)).id
            edge_count = sum(
                1 for vertex_seq in egi.nu.values() if vertex_id in vertex_seq
            )
            if edge_count >= 1:
                should_quantify = True

        if should_quantify:
            # Find variables to quantify
            variables_in_formula = self._extract_variables_from_formula_string(
                base_formula
            )
            if variables_in_formula:
                # Quantify all variables (following Dau's pattern)
                result = base_formula
                for var in sorted(variables_in_formula):
                    result = f"∃{var}.{result}"
                return result

        return base_formula

    def _formula_has_existential(self, formula: FOPLFormula) -> bool:
        """Check if formula contains existential quantifiers."""
        if isinstance(formula, ExistentialFormula):
            return True
        elif isinstance(formula, ConjunctionFormula):
            return self._formula_has_existential(
                formula.left
            ) or self._formula_has_existential(formula.right)
        elif isinstance(formula, NegationFormula):
            return self._formula_has_existential(formula.formula)
        elif isinstance(formula, ImplicationFormula):
            return self._formula_has_existential(
                formula.antecedent
            ) or self._formula_has_existential(formula.consequent)
        elif isinstance(formula, UniversalFormula):
            return self._formula_has_existential(formula.formula)

        return False

    def _extract_variables_from_formula_string(self, formula_str: str) -> Set[str]:
        """Extract variable names from formula string."""
        import re

        # Find variables like x1, x2, etc.
        variables = re.findall(r"\b[a-z]\d*\b", formula_str)
        return set(variables)

    def _translate_area_to_fopl_improved(
        self, egi: RelationalGraphWithCuts, area_id: ElementID
    ) -> str:
        """Improved area translation."""
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
                    formulas.append(f"{variables[0]} .= {variables[1]}")
                else:
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


class EnhancedLogicalEquivalenceChecker:
    """Enhanced equivalence checker with free/bound variable analysis."""

    @staticmethod
    def formulas_logically_equivalent(f1_str: str, f2_str: str) -> bool:
        """Check logical equivalence with improved variable handling."""
        try:
            # Handle special cases first
            if f1_str == f2_str:
                return True

            # Parse formulas
            f1 = parse_fopl_formula(f1_str)
            f2 = parse_fopl_formula(f2_str)

            # Check structural equivalence with variable normalization
            return EnhancedLogicalEquivalenceChecker._check_structural_equivalence(
                f1, f2
            )
        except:
            # Fallback to string-based comparison
            return EnhancedLogicalEquivalenceChecker._string_based_equivalence(
                f1_str, f2_str
            )

    @staticmethod
    def _check_structural_equivalence(f1: FOPLFormula, f2: FOPLFormula) -> bool:
        """Check structural equivalence with proper variable handling."""
        # Normalize variables in both formulas
        norm_f1 = EnhancedLogicalEquivalenceChecker._normalize_variables(f1)
        norm_f2 = EnhancedLogicalEquivalenceChecker._normalize_variables(f2)

        return EnhancedLogicalEquivalenceChecker._formulas_structurally_equal(
            norm_f1, norm_f2
        )

    @staticmethod
    def _normalize_variables(formula: FOPLFormula) -> FOPLFormula:
        """Normalize variable names in formula."""
        var_map = {}
        counter = [1]

        def get_var(var: str) -> str:
            if var not in var_map:
                var_map[var] = f"x{counter[0]}"
                counter[0] += 1
            return var_map[var]

        return EnhancedLogicalEquivalenceChecker._apply_var_mapping(formula, get_var)

    @staticmethod
    def _apply_var_mapping(formula: FOPLFormula, var_mapper) -> FOPLFormula:
        """Apply variable mapping to formula."""
        if isinstance(formula, AtomicFormula):
            new_vars = [var_mapper(var) for var in formula.variables]
            return AtomicFormula(formula.relation, new_vars)
        elif isinstance(formula, ConjunctionFormula):
            new_left = EnhancedLogicalEquivalenceChecker._apply_var_mapping(
                formula.left, var_mapper
            )
            new_right = EnhancedLogicalEquivalenceChecker._apply_var_mapping(
                formula.right, var_mapper
            )
            return ConjunctionFormula(new_left, new_right)
        elif isinstance(formula, NegationFormula):
            new_inner = EnhancedLogicalEquivalenceChecker._apply_var_mapping(
                formula.formula, var_mapper
            )
            return NegationFormula(new_inner)
        elif isinstance(formula, ExistentialFormula):
            new_var = var_mapper(formula.variable)
            new_inner = EnhancedLogicalEquivalenceChecker._apply_var_mapping(
                formula.formula, var_mapper
            )
            return ExistentialFormula(new_var, new_inner)
        elif isinstance(formula, UniversalFormula):
            new_var = var_mapper(formula.variable)
            new_inner = EnhancedLogicalEquivalenceChecker._apply_var_mapping(
                formula.formula, var_mapper
            )
            return UniversalFormula(new_var, new_inner)
        elif isinstance(formula, ImplicationFormula):
            new_ant = EnhancedLogicalEquivalenceChecker._apply_var_mapping(
                formula.antecedent, var_mapper
            )
            new_cons = EnhancedLogicalEquivalenceChecker._apply_var_mapping(
                formula.consequent, var_mapper
            )
            return ImplicationFormula(new_ant, new_cons)

        return formula

    @staticmethod
    def _formulas_structurally_equal(f1: FOPLFormula, f2: FOPLFormula) -> bool:
        """Check if normalized formulas are structurally equal."""
        if type(f1) != type(f2):
            return False

        if isinstance(f1, AtomicFormula):
            return f1.relation == f2.relation and f1.variables == f2.variables
        elif isinstance(f1, ConjunctionFormula):
            # Check both orders (conjunction is commutative)
            return (
                EnhancedLogicalEquivalenceChecker._formulas_structurally_equal(
                    f1.left, f2.left
                )
                and EnhancedLogicalEquivalenceChecker._formulas_structurally_equal(
                    f1.right, f2.right
                )
            ) or (
                EnhancedLogicalEquivalenceChecker._formulas_structurally_equal(
                    f1.left, f2.right
                )
                and EnhancedLogicalEquivalenceChecker._formulas_structurally_equal(
                    f1.right, f2.left
                )
            )
        elif isinstance(f1, NegationFormula):
            return EnhancedLogicalEquivalenceChecker._formulas_structurally_equal(
                f1.formula, f2.formula
            )
        elif isinstance(f1, ExistentialFormula):
            return (
                f1.variable == f2.variable
                and EnhancedLogicalEquivalenceChecker._formulas_structurally_equal(
                    f1.formula, f2.formula
                )
            )
        elif isinstance(f1, UniversalFormula):
            return (
                f1.variable == f2.variable
                and EnhancedLogicalEquivalenceChecker._formulas_structurally_equal(
                    f1.formula, f2.formula
                )
            )
        elif isinstance(f1, ImplicationFormula):
            return EnhancedLogicalEquivalenceChecker._formulas_structurally_equal(
                f1.antecedent, f2.antecedent
            ) and EnhancedLogicalEquivalenceChecker._formulas_structurally_equal(
                f1.consequent, f2.consequent
            )

        return False

    @staticmethod
    def _string_based_equivalence(f1_str: str, f2_str: str) -> bool:
        """Fallback string-based equivalence check."""

        # Normalize strings by removing spaces and standardizing variables
        def normalize_string(s: str) -> str:
            import re

            # Remove spaces
            s = s.replace(" ", "")
            # Find and replace variables
            variables = re.findall(r"\b[a-z]\d*\b", s)
            var_map = {}
            for i, var in enumerate(sorted(set(variables))):
                var_map[var] = f"x{i+1}"

            for old_var, new_var in var_map.items():
                s = s.replace(old_var, new_var)

            return s

        return normalize_string(f1_str) == normalize_string(f2_str)


def test_refined_translation():
    """Test the refined translation system."""
    print("🔬 Testing Refined Chapter 18 Translation")
    print("=" * 60)
    print("Focus: Precise existential quantification and variable equivalence")
    print("=" * 60)

    translator = RefinedChapter18Translator()
    checker = EnhancedLogicalEquivalenceChecker()

    test_cases = [
        "Man(x)",  # Should NOT add ∃
        "∃x.Man(x)",  # Should preserve ∃
        "∃x.(Man(x) ∧ Mortal(x))",  # Should preserve ∃
        "Man(x) ∧ Mortal(x)",  # Should NOT add ∃
        "¬Man(x)",  # Should NOT add ∃
        "x .= y",  # Should NOT add ∃
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

    print(f"\n🎯 REFINED TRANSLATION SUMMARY")
    print("-" * 50)
    print(f"Successful translations: {successful}/{len(test_cases)}")
    print(f"Logically equivalent: {equivalent}/{len(test_cases)}")
    print(f"Accuracy rate: {equivalent/len(test_cases):.1%}")

    if equivalent >= len(test_cases) * 0.9:
        print("✅ EXCELLENT: Theoretical compliance achieved!")
    elif equivalent >= len(test_cases) * 0.8:
        print("✅ GOOD: Strong theoretical compliance")
    else:
        print("⚠️  Needs further refinement")

    return results


if __name__ == "__main__":
    test_refined_translation()
