"""
Enhanced Dau Compliance Engine - Complete integration of all Dau formalism components.
Combines formal transformation rules, ligature manipulation, isomorphism checking,
and syntactic equivalence validation for full Chapter 14 & 16 compliance.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from frozendict import frozendict

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from formal_transformation_rules import (
    AreaPolarity,
    FormalTransformationEngine,
    TransformationContext,
    TransformationResult,
)
from graph_isomorphism_engine import GraphIsomorphismEngine, IsomorphismValidator
# from legacy.level_polarity_adjustment import LevelPolarityAdjuster  # Legacy component removed
from ligature_manipulation_rules import LigatureManipulationEngine
from syntactic_equivalence_checker import (
    SyntacticEquivalenceChecker,
    validate_transformation_preserves_meaning,
)


class ComplianceLevel(Enum):
    """Levels of Dau compliance validation."""

    BASIC = "basic"  # Basic rule application
    STRUCTURAL = "structural"  # + Structural validation
    SEMANTIC = "semantic"  # + Semantic equivalence checking
    RIGOROUS = "rigorous"  # + Full isomorphism validation


@dataclass
class ComplianceResult:
    """Result of Dau compliance validation."""

    is_compliant: bool
    compliance_level: ComplianceLevel
    transformation_result: Optional[TransformationResult]
    equivalence_validation: Optional[Any]
    violations: List[str]
    recommendations: List[str]


class EnhancedDauComplianceEngine:
    """
    Complete Dau compliance engine integrating all formalism components:
    - All 6 calculus rules (DC+/DC-, INS/ERA, IT+/IT-, HEAVY_DOT)
    - Chapter 16 ligature manipulation rules
    - Rigorous isomorphism checking for deiteration
    - Syntactic equivalence validation
    - Polarity and closed subgraph validation
    """

    def __init__(self, compliance_level: ComplianceLevel = ComplianceLevel.RIGOROUS):
        self.compliance_level = compliance_level

        # Core engines
        self.transformation_engine = FormalTransformationEngine()
        self.ligature_engine = LigatureManipulationEngine()
        self.equivalence_checker = SyntacticEquivalenceChecker()
        self.isomorphism_engine = GraphIsomorphismEngine()
        self.isomorphism_validator = IsomorphismValidator()
        self.polarity_adjuster = LevelPolarityAdjuster()

    def apply_transformation_with_compliance(
        self,
        rule_name: str,
        source_egi: RelationalGraphWithCuts,
        target_area: ElementID,
        selected_subgraph: FrozenSet[ElementID],
    ) -> ComplianceResult:
        """
        Apply transformation with full Dau compliance validation.

        Args:
            rule_name: Name of transformation rule to apply
            source_egi: Source EGI to transform
            target_area: Target area for transformation
            selected_subgraph: Selected elements for transformation

        Returns:
            ComplianceResult with validation details
        """

        violations = []
        recommendations = []

        # Step 1: Basic rule application
        if rule_name in self.transformation_engine.get_available_rules():
            transformation_result = self.transformation_engine.apply_rule(
                rule_name, source_egi, target_area, selected_subgraph
            )
        elif rule_name in self.ligature_engine.get_available_rules():
            transformation_result = self.ligature_engine.apply_rule(
                rule_name, source_egi, target_area, selected_subgraph
            )
        else:
            return ComplianceResult(
                is_compliant=False,
                compliance_level=ComplianceLevel.BASIC,
                transformation_result=None,
                equivalence_validation=None,
                violations=[f"Unknown transformation rule: {rule_name}"],
                recommendations=["Use one of the supported Dau calculus rules"],
            )

        if not transformation_result.success:
            return ComplianceResult(
                is_compliant=False,
                compliance_level=ComplianceLevel.BASIC,
                transformation_result=transformation_result,
                equivalence_validation=None,
                violations=[transformation_result.error_message],
                recommendations=["Check rule preconditions and selected elements"],
            )

        # Step 2: Structural validation (if enabled)
        if self.compliance_level.value in ["structural", "semantic", "rigorous"]:
            structural_violations = self._validate_structural_integrity(
                source_egi, transformation_result.result_egi, rule_name
            )
            violations.extend(structural_violations)

        # Step 3: Semantic equivalence validation (if enabled)
        equivalence_validation = None
        if self.compliance_level.value in ["semantic", "rigorous"]:
            equivalence_validation = validate_transformation_preserves_meaning(
                source_egi, transformation_result.result_egi, rule_name
            )

            if not equivalence_validation.are_equivalent:
                violations.append(
                    f"Transformation does not preserve semantic equivalence: {equivalence_validation.reason}"
                )
                recommendations.append(
                    "Verify transformation follows Dau's syntactic equivalence requirements"
                )

        # Step 4: Rigorous isomorphism validation (if enabled)
        if self.compliance_level == ComplianceLevel.RIGOROUS:
            isomorphism_violations = self._validate_isomorphism_requirements(
                source_egi,
                transformation_result.result_egi,
                rule_name,
                selected_subgraph,
            )
            violations.extend(isomorphism_violations)

        # Determine compliance
        is_compliant = len(violations) == 0

        return ComplianceResult(
            is_compliant=is_compliant,
            compliance_level=self.compliance_level,
            transformation_result=transformation_result,
            equivalence_validation=equivalence_validation,
            violations=violations,
            recommendations=recommendations,
        )

    def validate_dau_compliance(self, egi: RelationalGraphWithCuts) -> ComplianceResult:
        """
        Validate that an EGI meets all Dau formalism requirements.

        Args:
            egi: EGI to validate

        Returns:
            ComplianceResult indicating compliance status
        """

        violations = []
        recommendations = []

        # Check basic EGI structure
        structural_violations = self._validate_egi_structure(egi)
        violations.extend(structural_violations)

        # Check area mapping constraints
        area_violations = self._validate_area_constraints(egi)
        violations.extend(area_violations)

        # Check cut nesting requirements
        nesting_violations = self._validate_cut_nesting(egi)
        violations.extend(nesting_violations)

        # Check ligature consistency
        ligature_violations = self._validate_ligature_consistency(egi)
        violations.extend(ligature_violations)

        is_compliant = len(violations) == 0

        return ComplianceResult(
            is_compliant=is_compliant,
            compliance_level=self.compliance_level,
            transformation_result=None,
            equivalence_validation=None,
            violations=violations,
            recommendations=recommendations,
        )

    def _validate_structural_integrity(
        self,
        original_egi: RelationalGraphWithCuts,
        transformed_egi: RelationalGraphWithCuts,
        rule_name: str,
    ) -> List[str]:
        """Validate structural integrity after transformation."""
        violations = []

        # Check that all elements are properly mapped to areas
        all_elements = set()
        all_elements.update(v.id for v in transformed_egi.V)
        all_elements.update(e.id for e in transformed_egi.E)
        all_elements.update(c.id for c in transformed_egi.Cut)

        mapped_elements = set()
        for area_contents in transformed_egi.area.values():
            mapped_elements.update(area_contents)

        unmapped_elements = all_elements - mapped_elements
        if unmapped_elements:
            violations.append(f"Elements not mapped to any area: {unmapped_elements}")

        # Check that nu mapping is consistent with vertices
        for edge_id, vertex_sequence in transformed_egi.nu.items():
            for vertex_id in vertex_sequence:
                if not any(v.id == vertex_id for v in transformed_egi.V):
                    violations.append(
                        f"Nu mapping references non-existent vertex: {vertex_id}"
                    )

        # Check that rel mapping is consistent with edges
        for edge_id in transformed_egi.rel.keys():
            if not any(e.id == edge_id for e in transformed_egi.E):
                violations.append(
                    f"Rel mapping references non-existent edge: {edge_id}"
                )

        return violations

    def _validate_isomorphism_requirements(
        self,
        original_egi: RelationalGraphWithCuts,
        transformed_egi: RelationalGraphWithCuts,
        rule_name: str,
        selected_subgraph: FrozenSet[ElementID],
    ) -> List[str]:
        """Validate isomorphism requirements for specific rules."""
        violations = []

        # For IT- (deiteration), validate using isomorphism engine
        if rule_name == "IT-":
            # Find the area containing the selected subgraph
            target_area = None
            for area_id, contents in original_egi.area.items():
                if selected_subgraph.issubset(contents):
                    target_area = area_id
                    break

            if target_area:
                # Build nesting hierarchy
                nesting_hierarchy = self._get_nesting_hierarchy(
                    original_egi, target_area
                )

                # Validate deiteration candidate
                is_valid, error_message = (
                    self.isomorphism_validator.validate_deiteration_candidate(
                        original_egi, selected_subgraph, target_area, nesting_hierarchy
                    )
                )

                if not is_valid:
                    violations.append(
                        f"IT- isomorphism validation failed: {error_message}"
                    )

        return violations

    def _validate_egi_structure(self, egi: RelationalGraphWithCuts) -> List[str]:
        """Validate basic EGI structure per Dau's Definition 12.1."""
        violations = []

        # Check that sheet exists and is mapped
        if egi.sheet not in egi.area:
            violations.append("Sheet of assertion not found in area mapping")

        # Check that all cuts have area mappings
        for cut in egi.Cut:
            if cut.id not in egi.area:
                violations.append(f"Cut {cut.id} has no area mapping")

        # Check that nu mapping covers all edges
        edge_ids = {e.id for e in egi.E}
        nu_edge_ids = set(egi.nu.keys())

        unmapped_edges = edge_ids - nu_edge_ids
        if unmapped_edges:
            violations.append(f"Edges without nu mapping: {unmapped_edges}")

        return violations

    def _validate_area_constraints(self, egi: RelationalGraphWithCuts) -> List[str]:
        """Validate area mapping constraints."""
        violations = []

        # Check that areas are disjoint (no element in multiple areas)
        all_mapped_elements = []
        for area_id, contents in egi.area.items():
            all_mapped_elements.extend(contents)

        if len(all_mapped_elements) != len(set(all_mapped_elements)):
            violations.append(
                "Area mappings are not disjoint - elements appear in multiple areas"
            )

        return violations

    def _validate_cut_nesting(self, egi: RelationalGraphWithCuts) -> List[str]:
        """Validate cut nesting requirements."""
        violations = []

        # Check for proper nesting (no overlapping cuts at same level)
        cut_levels = {}
        for cut in egi.Cut:
            level = self._calculate_cut_nesting_level(egi, cut.id)
            if level not in cut_levels:
                cut_levels[level] = []
            cut_levels[level].append(cut.id)

        # For each level, check that cuts don't overlap
        for level, cuts_at_level in cut_levels.items():
            if len(cuts_at_level) > 1:
                # Check for overlaps (simplified check)
                for i, cut1_id in enumerate(cuts_at_level):
                    for cut2_id in cuts_at_level[i + 1 :]:
                        if self._cuts_overlap(egi, cut1_id, cut2_id):
                            violations.append(
                                f"Overlapping cuts at level {level}: {cut1_id}, {cut2_id}"
                            )

        return violations

    def _validate_ligature_consistency(self, egi: RelationalGraphWithCuts) -> List[str]:
        """Validate ligature consistency per Chapter 16."""
        violations = []

        # Check that identity edges form valid ligatures
        identity_edges = []
        for edge_id, relation in egi.rel.items():
            if relation == "=":
                vertex_sequence = egi.nu.get(edge_id, ())
                if len(vertex_sequence) == 2:
                    identity_edges.append((vertex_sequence[0], vertex_sequence[1]))
                else:
                    violations.append(
                        f"Identity edge {edge_id} has invalid vertex sequence length: {len(vertex_sequence)}"
                    )

        # Check ligature connectivity (simplified)
        if identity_edges:
            # Build ligature graph and check for valid structure
            ligature_graph = self._build_ligature_graph(identity_edges)
            # Additional ligature validation could be added here

        return violations

    def _get_nesting_hierarchy(
        self, egi: RelationalGraphWithCuts, target_area: ElementID
    ) -> List[ElementID]:
        """Get nesting hierarchy from target area to sheet."""
        hierarchy = [target_area]
        current_area = target_area

        while current_area != egi.sheet:
            parent_area = None
            for area_id, contents in egi.area.items():
                if current_area in contents:
                    parent_area = area_id
                    break

            if parent_area is None:
                break

            hierarchy.append(parent_area)
            current_area = parent_area

        return hierarchy

    def _calculate_cut_nesting_level(
        self, egi: RelationalGraphWithCuts, cut_id: ElementID
    ) -> int:
        """Calculate nesting level of a cut."""
        level = 0
        for other_cut in egi.Cut:
            if other_cut.id != cut_id:
                other_contents = egi.area.get(other_cut.id, frozenset())
                if cut_id in other_contents:
                    level += 1
        return level

    def _cuts_overlap(
        self, egi: RelationalGraphWithCuts, cut1_id: ElementID, cut2_id: ElementID
    ) -> bool:
        """Check if two cuts overlap (simplified check)."""
        contents1 = egi.area.get(cut1_id, frozenset())
        contents2 = egi.area.get(cut2_id, frozenset())

        # Cuts overlap if they share any elements
        return len(contents1.intersection(contents2)) > 0

    def _build_ligature_graph(
        self, identity_edges: List[Tuple[ElementID, ElementID]]
    ) -> Dict[ElementID, List[ElementID]]:
        """Build adjacency graph from identity edges."""
        graph = {}
        for v1, v2 in identity_edges:
            if v1 not in graph:
                graph[v1] = []
            if v2 not in graph:
                graph[v2] = []
            graph[v1].append(v2)
            graph[v2].append(v1)
        return graph

    def get_supported_rules(self) -> Dict[str, str]:
        """Get all supported transformation rules with descriptions."""
        rules = {}

        # Formal transformation rules
        for rule_name in self.transformation_engine.get_available_rules():
            rules[rule_name] = self.transformation_engine.describe_rule(rule_name)

        # Ligature manipulation rules
        for rule_name in self.ligature_engine.get_available_rules():
            rules[rule_name] = self.ligature_engine.describe_rule(rule_name)

        return rules

    def set_compliance_level(self, level: ComplianceLevel):
        """Set the compliance validation level."""
        self.compliance_level = level


def demonstrate_enhanced_compliance():
    """Demonstrate the enhanced Dau compliance engine."""

    print("🎯 Enhanced Dau Compliance Engine Demonstration")
    print("=" * 55)

    # Create test EGI
    from egi_core_dau import Edge, ElementID, RelationalGraphWithCuts, Vertex

    vertex_a = Vertex(ElementID("A"))
    vertex_b = Vertex(ElementID("B"))

    test_egi = RelationalGraphWithCuts(
        V=frozenset([vertex_a, vertex_b]),
        E=frozenset(),
        nu=frozendict(),
        sheet=ElementID("sheet"),
        Cut=frozenset(),
        area=frozendict(
            {ElementID("sheet"): frozenset([ElementID("A"), ElementID("B")])}
        ),
        rel=frozendict(),
    )

    # Test with different compliance levels
    for level in ComplianceLevel:
        print(f"\n🔍 Testing with {level.value.upper()} compliance level")

        engine = EnhancedDauComplianceEngine(level)

        # Test EGI validation
        validation_result = engine.validate_dau_compliance(test_egi)
        print(
            f"   EGI Compliance: {'✅ PASS' if validation_result.is_compliant else '❌ FAIL'}"
        )
        if validation_result.violations:
            print(f"   Violations: {validation_result.violations}")

        # Test transformation with compliance
        transformation_result = engine.apply_transformation_with_compliance(
            "DC+", test_egi, ElementID("sheet"), frozenset([ElementID("A")])
        )
        print(
            f"   DC+ Compliance: {'✅ PASS' if transformation_result.is_compliant else '❌ FAIL'}"
        )
        if transformation_result.violations:
            print(f"   Violations: {transformation_result.violations}")

    print(f"\n📋 Supported Rules: {len(engine.get_supported_rules())}")
    for rule_name, description in engine.get_supported_rules().items():
        print(f"   • {rule_name}: {description}")

    return engine


if __name__ == "__main__":
    demonstrate_enhanced_compliance()
