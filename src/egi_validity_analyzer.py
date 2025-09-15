"""
EGI Validity and Consistency Analysis System.
Comprehensive validation framework for ensuring EGI structural integrity and logical consistency.
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """A single validation issue found in an EGI."""

    issue_id: str
    severity: ValidationSeverity
    category: str
    description: str
    element_ids: List[ElementID] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    suggested_fix: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report for an EGI."""

    egi_id: Optional[str]
    source_egif: Optional[str]
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_issues_by_severity(
        self, severity: ValidationSeverity
    ) -> List[ValidationIssue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]

    def get_issues_by_category(self, category: str) -> List[ValidationIssue]:
        """Get all issues in a specific category."""
        return [issue for issue in self.issues if issue.category == category]

    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return any(
            issue.severity == ValidationSeverity.CRITICAL for issue in self.issues
        )

    def has_errors(self) -> bool:
        """Check if there are any errors or critical issues."""
        return any(
            issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
            for issue in self.issues
        )


class EGIValidityAnalyzer:
    """
    Comprehensive EGI validity and consistency analyzer.

    Performs multiple types of validation:
    1. Structural integrity checks
    2. Referential consistency validation
    3. Area containment validation
    4. Cut nesting validation
    5. Edge endpoint validation
    6. Logical consistency checks
    7. EGIF round-trip validation
    """

    def __init__(self):
        self.issue_counter = 0

    def analyze_egi(
        self,
        egi: RelationalGraphWithCuts,
        source_egif: Optional[str] = None,
        egi_id: Optional[str] = None,
    ) -> ValidationReport:
        """Perform comprehensive analysis of an EGI."""

        report = ValidationReport(
            egi_id=egi_id,
            source_egif=source_egif,
            is_valid=True,
            statistics=self._calculate_statistics(egi),
            metadata={"analysis_timestamp": "now"},
        )

        # Run all validation checks
        self._check_structural_integrity(egi, report)
        self._check_referential_consistency(egi, report)
        self._check_area_containment(egi, report)
        self._check_cut_nesting(egi, report)
        self._check_edge_endpoints(egi, report)
        self._check_logical_consistency(egi, report)

        if source_egif:
            self._check_egif_round_trip(egi, source_egif, report)

        # Determine overall validity
        report.is_valid = not report.has_errors()

        return report

    def _calculate_statistics(self, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Calculate basic statistics about the EGI."""

        return {
            "vertex_count": len(egi.V),
            "edge_count": len(egi.E),
            "cut_count": len(egi.Cut),
            "area_count": len(egi.area),
            "max_nesting_depth": self._calculate_max_nesting_depth(egi),
            "connected_components": self._count_connected_components(egi),
        }

    def _calculate_max_nesting_depth(self, egi: RelationalGraphWithCuts) -> int:
        """Calculate the maximum nesting depth of cuts."""

        max_depth = 0

        def calculate_depth(area_id: ElementID, current_depth: int = 0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)

            # Find cuts in this area
            area_contents = egi.area.get(area_id, frozenset())
            for element_id in area_contents:
                if any(cut.id == element_id for cut in egi.Cut):
                    calculate_depth(element_id, current_depth + 1)

        # Start from sheet of assertion
        calculate_depth(egi.sheet)

        return max_depth

    def _count_connected_components(self, egi: RelationalGraphWithCuts) -> int:
        """Count connected components in the graph structure."""

        if not egi.V:
            return 0

        visited = set()
        components = 0

        def dfs(vertex_id: ElementID):
            if vertex_id in visited:
                return
            visited.add(vertex_id)

            # Find all edges connected to this vertex
            for edge in egi.E:
                edge_vertices = egi.nu.get(edge.id, ())
                if vertex_id in edge_vertices:
                    for other_vertex_id in edge_vertices:
                        if (
                            other_vertex_id != vertex_id
                            and other_vertex_id not in visited
                        ):
                            dfs(other_vertex_id)

        for vertex in egi.V:
            if vertex.id not in visited:
                dfs(vertex.id)
                components += 1

        return components

    def _check_structural_integrity(
        self, egi: RelationalGraphWithCuts, report: ValidationReport
    ):
        """Check basic structural integrity of the EGI."""

        # Check that sheet of assertion exists
        if not hasattr(egi, "sheet") or egi.sheet is None:
            self._add_issue(
                report,
                ValidationSeverity.CRITICAL,
                "structure",
                "Missing sheet of assertion",
                [],
            )

        # Check that all required collections exist
        required_collections = ["V", "E", "Cut", "area"]
        for collection in required_collections:
            if not hasattr(egi, collection):
                self._add_issue(
                    report,
                    ValidationSeverity.CRITICAL,
                    "structure",
                    f"Missing required collection: {collection}",
                    [],
                )

        # Check for duplicate element IDs across collections
        all_ids = set()
        duplicates = set()

        for vertex in egi.V:
            if vertex.id in all_ids:
                duplicates.add(vertex.id)
            all_ids.add(vertex.id)

        for edge in egi.E:
            if edge.id in all_ids:
                duplicates.add(edge.id)
            all_ids.add(edge.id)

        for cut in egi.Cut:
            if cut.id in all_ids:
                duplicates.add(cut.id)
            all_ids.add(cut.id)

        for duplicate_id in duplicates:
            self._add_issue(
                report,
                ValidationSeverity.CRITICAL,
                "structure",
                f"Duplicate element ID: {duplicate_id}",
                [duplicate_id],
            )

    def _check_referential_consistency(
        self, egi: RelationalGraphWithCuts, report: ValidationReport
    ):
        """Check that all references between elements are valid."""

        # Collect all valid element IDs
        valid_ids = {egi.sheet}
        valid_ids.update(vertex.id for vertex in egi.V)
        valid_ids.update(edge.id for edge in egi.E)
        valid_ids.update(cut.id for cut in egi.Cut)

        # Check edge vertex references
        for edge in egi.E:
            edge_vertices = egi.nu.get(edge.id, ())
            for vertex_id in edge_vertices:
                if vertex_id not in valid_ids:
                    self._add_issue(
                        report,
                        ValidationSeverity.ERROR,
                        "references",
                        f"Edge {edge.id} references non-existent vertex {vertex_id}",
                        [edge.id, vertex_id],
                    )
                elif not any(v.id == vertex_id for v in egi.V):
                    self._add_issue(
                        report,
                        ValidationSeverity.ERROR,
                        "references",
                        f"Edge {edge.id} references ID {vertex_id} which is not a vertex",
                        [edge.id, vertex_id],
                    )

        # Check area containment references
        for area_id, contents in egi.area.items():
            if area_id not in valid_ids:
                self._add_issue(
                    report,
                    ValidationSeverity.ERROR,
                    "references",
                    f"Area {area_id} is not a valid element ID",
                    [area_id],
                )

            for element_id in contents:
                if element_id not in valid_ids:
                    self._add_issue(
                        report,
                        ValidationSeverity.ERROR,
                        "references",
                        f"Area {area_id} contains non-existent element {element_id}",
                        [area_id, element_id],
                    )

    def _check_area_containment(
        self, egi: RelationalGraphWithCuts, report: ValidationReport
    ):
        """Check area containment rules and consistency."""

        # Check that every element is contained in exactly one area
        element_area_count = defaultdict(int)

        for area_id, contents in egi.area.items():
            for element_id in contents:
                element_area_count[element_id] += 1

        # Check for elements in multiple areas
        for element_id, count in element_area_count.items():
            if count > 1:
                self._add_issue(
                    report,
                    ValidationSeverity.ERROR,
                    "containment",
                    f"Element {element_id} appears in {count} areas (should be exactly 1)",
                    [element_id],
                )

        # Check for orphaned elements (not in any area)
        all_elements = set()
        all_elements.update(vertex.id for vertex in egi.V)
        all_elements.update(edge.id for edge in egi.E)
        all_elements.update(cut.id for cut in egi.Cut)

        contained_elements = set()
        for contents in egi.area.values():
            contained_elements.update(contents)

        orphaned = all_elements - contained_elements
        for element_id in orphaned:
            self._add_issue(
                report,
                ValidationSeverity.ERROR,
                "containment",
                f"Element {element_id} is not contained in any area",
                [element_id],
            )

        # Check that sheet of assertion has an area entry
        if egi.sheet not in egi.area:
            self._add_issue(
                report,
                ValidationSeverity.CRITICAL,
                "containment",
                "Sheet of assertion has no area entry",
                [egi.sheet],
            )

    def _check_cut_nesting(
        self, egi: RelationalGraphWithCuts, report: ValidationReport
    ):
        """Check cut nesting rules and detect cycles."""

        # Build containment graph
        containment_graph = defaultdict(set)
        for area_id, contents in egi.area.items():
            for element_id in contents:
                if any(cut.id == element_id for cut in egi.Cut):
                    containment_graph[area_id].add(element_id)

        # Check for containment cycles using DFS
        def has_cycle(
            node: ElementID, visited: Set[ElementID], rec_stack: Set[ElementID]
        ) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in containment_graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        visited = set()
        for area_id in egi.area.keys():
            if area_id not in visited:
                if has_cycle(area_id, visited, set()):
                    self._add_issue(
                        report,
                        ValidationSeverity.CRITICAL,
                        "nesting",
                        f"Containment cycle detected involving area {area_id}",
                        [area_id],
                    )

    def _check_edge_endpoints(
        self, egi: RelationalGraphWithCuts, report: ValidationReport
    ):
        """Check edge endpoint validity and consistency."""

        for edge in egi.E:
            edge_vertices = egi.nu.get(edge.id, ())

            # Check minimum vertex count
            if len(edge_vertices) < 1:
                self._add_issue(
                    report,
                    ValidationSeverity.ERROR,
                    "edges",
                    f"Edge {edge.id} has no vertices",
                    [edge.id],
                )

            # Check for self-loops in binary relations
            if len(edge_vertices) == 2 and edge_vertices[0] == edge_vertices[1]:
                self._add_issue(
                    report,
                    ValidationSeverity.WARNING,
                    "edges",
                    f"Edge {edge.id} is a self-loop",
                    [edge.id],
                )

            # Check vertex sequence consistency
            vertex_ids = set(vertex.id for vertex in egi.V)
            for vertex_id in edge_vertices:
                if vertex_id not in vertex_ids:
                    self._add_issue(
                        report,
                        ValidationSeverity.ERROR,
                        "edges",
                        f"Edge {edge.id} references non-existent vertex {vertex_id}",
                        [edge.id, vertex_id],
                    )

    def _check_logical_consistency(
        self, egi: RelationalGraphWithCuts, report: ValidationReport
    ):
        """Check logical consistency rules specific to existential graphs."""

        # Check for empty cuts (cuts with no content)
        for cut in egi.Cut:
            cut_contents = egi.area.get(cut.id, frozenset())
            if not cut_contents:
                self._add_issue(
                    report,
                    ValidationSeverity.WARNING,
                    "logic",
                    f"Cut {cut.id} is empty (may be removable by DC-)",
                    [cut.id],
                )

        # Check for double cuts (nested empty cuts)
        for cut in egi.Cut:
            cut_contents = egi.area.get(cut.id, frozenset())
            if len(cut_contents) == 1:
                inner_element = next(iter(cut_contents))
                if any(inner_cut.id == inner_element for inner_cut in egi.Cut):
                    inner_cut_contents = egi.area.get(inner_element, frozenset())
                    if not inner_cut_contents:
                        self._add_issue(
                            report,
                            ValidationSeverity.INFO,
                            "logic",
                            f"Double cut detected: {cut.id} contains empty cut {inner_element}",
                            [cut.id, inner_element],
                        )

        # Check for potential iteration opportunities
        vertex_predicates = defaultdict(list)
        for vertex in egi.V:
            if hasattr(vertex, "concept") and vertex.concept:
                vertex_predicates[vertex.concept].append(vertex.id)

        for predicate, vertex_list in vertex_predicates.items():
            if len(vertex_list) > 1:
                self._add_issue(
                    report,
                    ValidationSeverity.INFO,
                    "logic",
                    f"Multiple vertices with predicate '{predicate}' - potential iteration opportunity",
                    vertex_list,
                )

    def _check_egif_round_trip(
        self, egi: RelationalGraphWithCuts, source_egif: str, report: ValidationReport
    ):
        """Check EGIF round-trip consistency."""

        try:
            # Generate EGIF from EGI
            generated_egif = generate_egif(egi)

            # Parse both EGIFs and compare structures
            source_egi = parse_egif(source_egif)
            generated_egi = parse_egif(generated_egif)

            # Compare basic counts
            if len(source_egi.V) != len(generated_egi.V):
                self._add_issue(
                    report,
                    ValidationSeverity.WARNING,
                    "round_trip",
                    f"Vertex count mismatch: source={len(source_egi.V)}, generated={len(generated_egi.V)}",
                    [],
                )

            if len(source_egi.E) != len(generated_egi.E):
                self._add_issue(
                    report,
                    ValidationSeverity.WARNING,
                    "round_trip",
                    f"Edge count mismatch: source={len(source_egi.E)}, generated={len(generated_egi.E)}",
                    [],
                )

            if len(source_egi.Cut) != len(generated_egi.Cut):
                self._add_issue(
                    report,
                    ValidationSeverity.WARNING,
                    "round_trip",
                    f"Cut count mismatch: source={len(source_egi.Cut)}, generated={len(generated_egi.Cut)}",
                    [],
                )

            # Store generated EGIF for comparison
            report.metadata["generated_egif"] = generated_egif

        except Exception as e:
            self._add_issue(
                report,
                ValidationSeverity.ERROR,
                "round_trip",
                f"EGIF round-trip failed: {str(e)}",
                [],
            )

    def _add_issue(
        self,
        report: ValidationReport,
        severity: ValidationSeverity,
        category: str,
        description: str,
        element_ids: List[ElementID],
        details: Dict[str, Any] = None,
        suggested_fix: str = None,
    ):
        """Add a validation issue to the report."""

        self.issue_counter += 1
        issue = ValidationIssue(
            issue_id=f"issue_{self.issue_counter:04d}",
            severity=severity,
            category=category,
            description=description,
            element_ids=element_ids,
            details=details or {},
            suggested_fix=suggested_fix,
        )

        report.issues.append(issue)

    def generate_report_summary(self, report: ValidationReport) -> str:
        """Generate a human-readable summary of the validation report."""

        lines = []
        lines.append("=== EGI Validity Analysis Report ===")

        if report.egi_id:
            lines.append(f"EGI ID: {report.egi_id}")

        lines.append(f"Overall Status: {'VALID' if report.is_valid else 'INVALID'}")
        lines.append(f"Total Issues: {len(report.issues)}")

        # Statistics
        lines.append("\n--- Statistics ---")
        for key, value in report.statistics.items():
            lines.append(f"{key.replace('_', ' ').title()}: {value}")

        # Issue summary by severity
        lines.append("\n--- Issues by Severity ---")
        for severity in ValidationSeverity:
            issues = report.get_issues_by_severity(severity)
            if issues:
                lines.append(f"{severity.value.upper()}: {len(issues)}")

        # Issue summary by category
        lines.append("\n--- Issues by Category ---")
        categories = set(issue.category for issue in report.issues)
        for category in sorted(categories):
            issues = report.get_issues_by_category(category)
            lines.append(f"{category}: {len(issues)}")

        # Detailed issues
        if report.issues:
            lines.append("\n--- Detailed Issues ---")
            for issue in report.issues:
                lines.append(
                    f"[{issue.severity.value.upper()}] {issue.category}: {issue.description}"
                )
                if issue.element_ids:
                    lines.append(
                        f"  Elements: {', '.join(map(str, issue.element_ids))}"
                    )
                if issue.suggested_fix:
                    lines.append(f"  Suggested Fix: {issue.suggested_fix}")

        return "\n".join(lines)


def test_egi_validity_analyzer():
    """Test the EGI validity analyzer with various test cases."""
    print("=== Testing EGI Validity Analyzer ===")

    analyzer = EGIValidityAnalyzer()

    # Test 1: Valid simple EGI
    print("\n--- Test 1: Valid Simple EGI ---")
    try:
        valid_egif = '(Human "Socrates")'
        valid_egi = parse_egif(valid_egif)
        report = analyzer.analyze_egi(valid_egi, valid_egif, "test_valid")

        print(f"Valid EGI Status: {'VALID' if report.is_valid else 'INVALID'}")
        print(f"Issues found: {len(report.issues)}")

        if report.issues:
            for issue in report.issues:
                print(f"  - {issue.severity.value}: {issue.description}")

    except Exception as e:
        print(f"Test 1 failed: {e}")

    # Test 2: Valid complex EGI with cuts
    print("\n--- Test 2: Valid Complex EGI ---")
    try:
        complex_egif = '~[ ~[ (Human "Socrates") ] ]'
        complex_egi = parse_egif(complex_egif)
        report = analyzer.analyze_egi(complex_egi, complex_egif, "test_complex")

        print(f"Complex EGI Status: {'VALID' if report.is_valid else 'INVALID'}")
        print(f"Issues found: {len(report.issues)}")
        print(f"Max nesting depth: {report.statistics.get('max_nesting_depth', 'N/A')}")

    except Exception as e:
        print(f"Test 2 failed: {e}")

    # Test 3: Generate full report
    print("\n--- Test 3: Full Report Generation ---")
    try:
        test_egif = "*x (Human x) (Mortal x)"
        test_egi = parse_egif(test_egif)
        report = analyzer.analyze_egi(test_egi, test_egif, "test_full_report")

        summary = analyzer.generate_report_summary(report)
        print(summary)

    except Exception as e:
        print(f"Test 3 failed: {e}")

    return analyzer


if __name__ == "__main__":
    test_egi_validity_analyzer()
