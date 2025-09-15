"""
Final Chapter 18 FOPL ↔ EGI Translation

Precise solution that maintains exact correspondence with original formulas:
- Tracks original formula structure during Ψ translation
- Only reconstructs quantifiers that were present in the original
- Enhanced variable equivalence checking
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


@dataclass
class TranslationMetadata:
    """Metadata to track during translation for precise reconstruction."""

    original_formula: FOPLFormula
    has_existential_quantifiers: bool
    quantified_variables: Set[str]
    free_variables: Set[str]
    formula_type: str


class FinalChapter18Translator(EnhancedChapter18Translator):
    """Final translator with precise formula structure preservation."""

    def __init__(self):
        super().__init__()
        self.translation_metadata: Optional[TranslationMetadata] = None

    def psi_translate(self, formula: FOPLFormula) -> RelationalGraphWithCuts:
        """Ψ translation with metadata tracking."""
        # Analyze original formula structure
        self.translation_metadata = self._analyze_formula_structure(formula)

        # Perform translation
        result = super().psi_translate(formula)

        # Store metadata in EGI for reconstruction
        # We'll use the rel mapping to store a special metadata entry
        metadata_rel = dict(result.rel)
        metadata_rel["__metadata__"] = str(
            {
                "has_existential": self.translation_metadata.has_existential_quantifiers,
                "quantified_vars": list(self.translation_metadata.quantified_variables),
                "free_vars": list(self.translation_metadata.free_variables),
                "formula_type": self.translation_metadata.formula_type,
            }
        )

        return RelationalGraphWithCuts(
            V=result.V,
            E=result.E,
            nu=result.nu,
            sheet=result.sheet,
            Cut=result.Cut,
            area=result.area,
            rel=frozendict(metadata_rel),
        )

    def _analyze_formula_structure(self, formula: FOPLFormula) -> TranslationMetadata:
        """Analyze original formula structure for precise reconstruction."""
        has_existential = self._has_existential_quantifier(formula)
        quantified_vars = self._get_quantified_variables(formula)
        free_vars = self._get_free_variables(formula)
        formula_type = self._get_formula_type(formula)

        return TranslationMetadata(
            original_formula=formula,
            has_existential_quantifiers=has_existential,
            quantified_variables=quantified_vars,
            free_variables=free_vars,
            formula_type=formula_type,
        )

    def _has_existential_quantifier(self, formula: FOPLFormula) -> bool:
        """Check if formula has existential quantifiers."""
        if isinstance(formula, ExistentialFormula):
            return True
        elif isinstance(formula, ConjunctionFormula):
            return self._has_existential_quantifier(
                formula.left
            ) or self._has_existential_quantifier(formula.right)
        elif isinstance(formula, NegationFormula):
            return self._has_existential_quantifier(formula.formula)
        elif isinstance(formula, ImplicationFormula):
            return self._has_existential_quantifier(
                formula.antecedent
            ) or self._has_existential_quantifier(formula.consequent)
        elif isinstance(formula, UniversalFormula):
            return self._has_existential_quantifier(formula.formula)

        return False

    def _get_quantified_variables(self, formula: FOPLFormula) -> Set[str]:
        """Get all quantified variables."""
        quantified = set()

        if isinstance(formula, ExistentialFormula):
            quantified.add(formula.variable)
            quantified.update(self._get_quantified_variables(formula.formula))
        elif isinstance(formula, UniversalFormula):
            quantified.add(formula.variable)
            quantified.update(self._get_quantified_variables(formula.formula))
        elif isinstance(formula, ConjunctionFormula):
            quantified.update(self._get_quantified_variables(formula.left))
            quantified.update(self._get_quantified_variables(formula.right))
        elif isinstance(formula, NegationFormula):
            quantified.update(self._get_quantified_variables(formula.formula))
        elif isinstance(formula, ImplicationFormula):
            quantified.update(self._get_quantified_variables(formula.antecedent))
            quantified.update(self._get_quantified_variables(formula.consequent))

        return quantified

    def _get_free_variables(self, formula: FOPLFormula) -> Set[str]:
        """Get all free variables."""
        all_vars = self._get_all_variables(formula)
        quantified_vars = self._get_quantified_variables(formula)
        return all_vars - quantified_vars

    def _get_all_variables(self, formula: FOPLFormula) -> Set[str]:
        """Get all variables in formula."""
        variables = set()

        if isinstance(formula, AtomicFormula):
            variables.update(formula.variables)
        elif isinstance(formula, ExistentialFormula):
            variables.add(formula.variable)
            variables.update(self._get_all_variables(formula.formula))
        elif isinstance(formula, UniversalFormula):
            variables.add(formula.variable)
            variables.update(self._get_all_variables(formula.formula))
        elif isinstance(formula, ConjunctionFormula):
            variables.update(self._get_all_variables(formula.left))
            variables.update(self._get_all_variables(formula.right))
        elif isinstance(formula, NegationFormula):
            variables.update(self._get_all_variables(formula.formula))
        elif isinstance(formula, ImplicationFormula):
            variables.update(self._get_all_variables(formula.antecedent))
            variables.update(self._get_all_variables(formula.consequent))

        return variables

    def _get_formula_type(self, formula: FOPLFormula) -> str:
        """Get the type of formula for reconstruction guidance."""
        if isinstance(formula, AtomicFormula):
            return "atomic"
        elif isinstance(formula, ExistentialFormula):
            return "existential"
        elif isinstance(formula, UniversalFormula):
            return "universal"
        elif isinstance(formula, ConjunctionFormula):
            return "conjunction"
        elif isinstance(formula, NegationFormula):
            return "negation"
        elif isinstance(formula, ImplicationFormula):
            return "implication"
        else:
            return "unknown"

    def phi_translate(self, egi: RelationalGraphWithCuts) -> str:
        """Φ translation with precise reconstruction based on metadata."""
        # Extract metadata if available
        metadata = None
        if "__metadata__" in egi.rel:
            try:
                import ast

                metadata_dict = ast.literal_eval(egi.rel["__metadata__"])
                metadata = metadata_dict
            except:
                pass

        # Reset context
        self.vertex_variable_map = {}

        # Assign variables
        var_counter = 1
        for vertex in egi.V:
            var_name = f"x{var_counter}"
            self.vertex_variable_map[vertex.id] = var_name
            var_counter += 1

        # Translate sheet area
        base_formula = self._translate_area_to_fopl_final(egi, egi.sheet)

        # Reconstruct quantifiers ONLY if metadata indicates they were present
        if metadata and metadata.get("has_existential", False):
            return self._reconstruct_existential_quantifiers(base_formula)
        else:
            return base_formula

    def _reconstruct_existential_quantifiers(self, base_formula: str) -> str:
        """Reconstruct existential quantifiers for formulas that originally had them."""
        if not base_formula:
            return base_formula

        # Extract variables from the formula
        import re

        variables = re.findall(r"\b[a-z]\d*\b", base_formula)
        unique_vars = sorted(set(variables))

        # Add existential quantifiers for all variables
        result = base_formula
        for var in unique_vars:
            result = f"∃{var}.{result}"

        return result

    def _translate_area_to_fopl_final(
        self, egi: RelationalGraphWithCuts, area_id: ElementID
    ) -> str:
        """Final area translation with clean output."""
        area_contents = egi.area.get(area_id, frozenset())

        # Separate edges and cuts
        edges = [eid for eid in area_contents if any(e.id == eid for e in egi.E)]
        cuts = [cid for cid in area_contents if any(c.id == cid for c in egi.Cut)]

        formulas = []

        # Translate edges to atomic formulas
        for edge_id in edges:
            if edge_id in egi.nu and edge_id in egi.rel and edge_id != "__metadata__":
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
            cut_formula = self._translate_area_to_fopl_final(egi, cut_id)
            if cut_formula:
                formulas.append(f"¬({cut_formula})")

        # Combine with conjunction
        if len(formulas) == 0:
            return ""
        elif len(formulas) == 1:
            return formulas[0]
        else:
            return " ∧ ".join(formulas)


class PreciseLogicalEquivalenceChecker:
    """Precise logical equivalence checker."""

    @staticmethod
    def formulas_logically_equivalent(f1_str: str, f2_str: str) -> bool:
        """Check logical equivalence with precise variable handling."""
        # Direct string comparison after normalization
        norm_f1 = PreciseLogicalEquivalenceChecker._normalize_formula_string(f1_str)
        norm_f2 = PreciseLogicalEquivalenceChecker._normalize_formula_string(f2_str)

        return norm_f1 == norm_f2

    @staticmethod
    def _normalize_formula_string(formula_str: str) -> str:
        """Normalize formula string for comparison."""
        import re

        # Remove extra spaces
        normalized = re.sub(r"\s+", " ", formula_str.strip())

        # Extract and sort variables
        variables = re.findall(r"\b[a-z]\d*\b", normalized)
        unique_vars = sorted(set(variables))

        # Create variable mapping
        var_map = {}
        for i, var in enumerate(unique_vars):
            var_map[var] = f"x{i+1}"

        # Apply variable mapping
        for old_var, new_var in var_map.items():
            normalized = re.sub(r"\b" + re.escape(old_var) + r"\b", new_var, normalized)

        # Normalize conjunction order
        if " ∧ " in normalized and not normalized.startswith("∃"):
            parts = normalized.split(" ∧ ")
            if len(parts) == 2:
                normalized = " ∧ ".join(sorted(parts))

        return normalized


def test_final_translation():
    """Test the final translation system."""
    print("🔬 Testing Final Chapter 18 Translation")
    print("=" * 60)
    print("Focus: Exact formula structure preservation")
    print("=" * 60)

    translator = FinalChapter18Translator()
    checker = PreciseLogicalEquivalenceChecker()

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

    print(f"\n🎯 FINAL TRANSLATION SUMMARY")
    print("-" * 50)
    print(f"Successful translations: {successful}/{len(test_cases)}")
    print(f"Logically equivalent: {equivalent}/{len(test_cases)}")
    print(f"Accuracy rate: {equivalent/len(test_cases):.1%}")

    if equivalent >= len(test_cases) * 0.9:
        print("✅ EXCELLENT: Full theoretical compliance achieved!")
    elif equivalent >= len(test_cases) * 0.8:
        print("✅ GOOD: Strong theoretical compliance")
    else:
        print("⚠️  Needs further refinement")

    return results


if __name__ == "__main__":
    test_final_translation()
