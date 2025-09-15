#!/usr/bin/env python3
"""
Pattern Catalog - Layer 3 of Layered Strategy

Documents established patterns and anti-patterns in the codebase.
Provides guidance for consistent implementation and avoiding known pitfalls.
"""

import json
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional


@dataclass
class CodePattern:
    """Represents a code pattern or anti-pattern."""

    name: str
    category: str
    description: str
    when_to_use: str
    implementation: str
    examples: List[str]
    related_patterns: List[str]
    anti_patterns: List[str]


class PatternCatalog:
    """Catalog of established patterns in the Arisbe codebase."""

    def __init__(self):
        self.patterns: Dict[str, CodePattern] = {}
        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize known patterns from the codebase."""

        # Performance Patterns
        self.patterns["hierarchical_index_lookup"] = CodePattern(
            name="Hierarchical Index O(1) Lookup",
            category="Performance",
            description="Use HierarchicalIndex for constant-time polarity and nesting queries",
            when_to_use="When you need polarity, nesting level, or containment information",
            implementation="Build HierarchicalIndex from EGI, use get_polarity() and get_nesting_level()",
            examples=[
                "hierarchical_index.py:90 - get_polarity()",
                "chapter21_diagram_engine.py:458 - _calculate_area_polarity_and_depth()",
            ],
            related_patterns=["egi_area_mapping", "spatial_indexing"],
            anti_patterns=["manual_traversal_polarity"],
        )

        self.patterns["spatial_indexing"] = CodePattern(
            name="R-Tree Spatial Indexing",
            category="Performance",
            description="Use R-tree for efficient spatial queries and containment checks",
            when_to_use="When dealing with spatial relationships, cut containment, or region queries",
            implementation="Use rtree_cut_tracker.py or hierarchical_view_system.py",
            examples=[
                "legacy/rtree_cut_tracker.py:86 - RTreeNode",
                "legacy/hierarchical_view_system.py:431 - DynamicViewManager",
            ],
            related_patterns=["hierarchical_index_lookup"],
            anti_patterns=["linear_spatial_search"],
        )

        # Transformation Patterns
        self.patterns["transformation_wizard"] = CodePattern(
            name="Step-by-Step Transformation Wizard",
            category="User Interface",
            description="Use modal wizard dialogs for complex multi-step transformations",
            when_to_use="For transformation rules requiring user input or validation",
            implementation="Create TransformationWizardDialog with step navigation and validation",
            examples=[
                "gui/transformation_wizard_dialog.py:1 - TransformationWizardDialog",
                "chapter21_diagram_engine.py:352 - UniversalEGIEngine",
            ],
            related_patterns=["formal_rule_application"],
            anti_patterns=["direct_transformation_execution"],
        )

        self.patterns["formal_rule_application"] = CodePattern(
            name="Formal Rule Application",
            category="Logic",
            description="Apply transformation rules through formal validation and context",
            when_to_use="For all Peirce-Dau transformation operations",
            implementation="Use TransformationContext with rule validation and precondition checking",
            examples=[
                "formal_transformation_rules.py:75 - calculate_area_polarity",
                "chapter21_diagram_engine.py:375 - apply_transformation",
            ],
            related_patterns=["transformation_wizard", "hierarchical_index_lookup"],
            anti_patterns=["direct_egi_manipulation"],
        )

        # Data Structure Patterns
        self.patterns["egi_area_mapping"] = CodePattern(
            name="EGI Area Mapping",
            category="Data Structure",
            description="Use frozendict area mapping for immutable containment relationships",
            when_to_use="When representing cut containment and area relationships",
            implementation="RelationalGraphWithCuts with area: frozendict[ElementID, frozenset[ElementID]]",
            examples=[
                "egi_core_dau.py:128 - _build_hierarchical_index",
                "egi_core_dau.py:349 - get_nesting_depth",
            ],
            related_patterns=["hierarchical_index_lookup"],
            anti_patterns=["mutable_area_mapping"],
        )

        self.patterns["signal_based_communication"] = CodePattern(
            name="Signal-Based Tab Communication",
            category="Architecture",
            description="Use PySide6 signals for communication between GUI tabs",
            when_to_use="For passing data between Organon, Ergasterion, and Agon tabs",
            implementation="Define custom signals and connect them in main application",
            examples=[
                "gui/arisbe_main_app_pyside6.py:170 - send_to_organon_signal",
                "gui/arisbe_main_app_pyside6.py:340 - receive_from_ergasterion",
            ],
            related_patterns=["transformation_wizard"],
            anti_patterns=["direct_tab_coupling"],
        )

        # Anti-Patterns
        self.patterns["manual_traversal_polarity"] = CodePattern(
            name="Manual Polarity Traversal (Anti-Pattern)",
            category="Anti-Pattern",
            description="Manually traversing containment hierarchy for polarity calculation",
            when_to_use="NEVER - Use HierarchicalIndex instead",
            implementation="DON'T: while current_area != egi.sheet: traverse...",
            examples=[
                "chapter21_diagram_engine.py:438 - OLD _calculate_area_polarity_and_depth (fixed)"
            ],
            related_patterns=[],
            anti_patterns=[],
        )

        self.patterns["direct_egi_manipulation"] = CodePattern(
            name="Direct EGI Manipulation (Anti-Pattern)",
            category="Anti-Pattern",
            description="Directly modifying EGI structures without formal rule validation",
            when_to_use="NEVER - Use formal transformation rules",
            implementation="DON'T: egi.area[new_area] = contents",
            examples=[],
            related_patterns=[],
            anti_patterns=[],
        )

    def find_pattern_for_problem(self, problem: str) -> List[CodePattern]:
        """Find patterns that solve a specific problem."""
        problem_lower = problem.lower()
        matching_patterns = []

        for pattern in self.patterns.values():
            if (
                problem_lower in pattern.description.lower()
                or problem_lower in pattern.when_to_use.lower()
                or any(problem_lower in example.lower() for example in pattern.examples)
            ):
                matching_patterns.append(pattern)

        return matching_patterns

    def get_patterns_by_category(self, category: str) -> List[CodePattern]:
        """Get all patterns in a specific category."""
        return [p for p in self.patterns.values() if p.category == category]

    def get_anti_patterns(self) -> List[CodePattern]:
        """Get all anti-patterns to avoid."""
        return [p for p in self.patterns.values() if p.category == "Anti-Pattern"]

    def export_catalog(self, output_path: str):
        """Export pattern catalog to JSON."""
        catalog_data = {
            "patterns": {
                name: asdict(pattern) for name, pattern in self.patterns.items()
            },
            "metadata": {
                "total_patterns": len(self.patterns),
                "categories": list(set(p.category for p in self.patterns.values())),
            },
        }

        with open(output_path, "w") as f:
            json.dump(catalog_data, f, indent=2)

    def generate_catalog_report(self) -> str:
        """Generate human-readable pattern catalog."""
        report = []
        report.append("# Arisbe Pattern Catalog\n")

        # Group by category
        categories = {}
        for pattern in self.patterns.values():
            if pattern.category not in categories:
                categories[pattern.category] = []
            categories[pattern.category].append(pattern)

        for category, patterns in categories.items():
            report.append(f"## {category} Patterns")

            for pattern in patterns:
                report.append(f"### {pattern.name}")
                report.append(f"**Description**: {pattern.description}")
                report.append(f"**When to Use**: {pattern.when_to_use}")
                report.append(f"**Implementation**: {pattern.implementation}")

                if pattern.examples:
                    report.append("**Examples**:")
                    for example in pattern.examples:
                        report.append(f"- {example}")

                if pattern.related_patterns:
                    report.append(
                        f"**Related Patterns**: {', '.join(pattern.related_patterns)}"
                    )

                if pattern.anti_patterns:
                    report.append(
                        f"**Anti-Patterns to Avoid**: {', '.join(pattern.anti_patterns)}"
                    )

                report.append("")

        return "\n".join(report)


def main():
    """Generate pattern catalog for Arisbe."""
    catalog = PatternCatalog()

    print(f"Generated pattern catalog with {len(catalog.patterns)} patterns")

    # Export catalog
    catalog.export_catalog("/Users/mjh/Sync/GitHub/Arisbe/pattern_catalog.json")

    # Generate report
    report = catalog.generate_catalog_report()
    with open("/Users/mjh/Sync/GitHub/Arisbe/PATTERN_CATALOG.md", "w") as f:
        f.write(report)

    print("Pattern catalog generated:")
    print("- pattern_catalog.json (machine-readable)")
    print("- PATTERN_CATALOG.md (human-readable)")

    # Show polarity patterns
    polarity_patterns = catalog.find_pattern_for_problem("polarity")
    print(f"\nPolarity-related patterns ({len(polarity_patterns)} found):")
    for pattern in polarity_patterns:
        print(f"- {pattern.name} ({pattern.category})")


if __name__ == "__main__":
    main()
