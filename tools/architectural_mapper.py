#!/usr/bin/env python3
"""
Architectural Mapper - Layer 2 of Layered Strategy

Maps major subsystems, their responsibilities, and interaction patterns.
Creates high-level architectural overview for quick orientation.
"""

import json
import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple


@dataclass
class Subsystem:
    """Represents a major subsystem in the codebase."""

    name: str
    path: str
    purpose: str
    key_classes: List[str]
    key_functions: List[str]
    responsibilities: List[str]
    dependencies: List[str]
    provides_to: List[str]


class ArchitecturalMapper:
    """Maps the high-level architecture of the codebase."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.subsystems: Dict[str, Subsystem] = {}

    def analyze_architecture(self):
        """Analyze and map the architectural structure."""
        # Define known subsystems based on directory structure and purpose
        subsystem_definitions = {
            "gui": {
                "purpose": "User interface and interaction management",
                "responsibilities": [
                    "PySide6 GUI components",
                    "User interaction handling",
                    "Visual representation of EGI graphs",
                    "Transformation wizard dialogs",
                ],
            },
            "linear_form_parsers": {
                "purpose": "Multi-format parsing and generation system",
                "responsibilities": [
                    "EGIF parser/generator (egif_parser_dau.py, egif_generator_dau.py)",
                    "CGIF parser/generator (cgif_parser_dau.py, cgif_generator_dau.py)",
                    "CLIF parser/generator (clif_parser_dau.py, clif_generator_dau.py)",
                    "FOPL translation and syntactic equivalence",
                    "Multi-format synchronization and consistency",
                ],
            },
            "dau_treatise_implementations": {
                "purpose": "Dau treatise chapter implementations and theoretical compliance",
                "responsibilities": [
                    "Translation consistency (Chapter 18)",
                    "Syntactic equivalence (Chapter 20)",
                    "Graph isomorphism engine",
                    "Theorem correspondence tests",
                    "Semantic evaluation engine",
                    "Soundness verification",
                    "Diagram correspondence validation",
                ],
            },
            "data_persistence_model": {
                "purpose": "Synchronic and diachronic EGI data management",
                "responsibilities": [
                    "Transformation history tracking",
                    "Branching and state snapshots",
                    "Temporal graph evolution",
                    "Persistence across sessions",
                    "Metadata and provenance tracking",
                    "Multi-format serialization",
                ],
            },
            "domain_ontology_system": {
                "purpose": "Domain knowledge and ontological reasoning",
                "responsibilities": [
                    "Concept hierarchy management",
                    "Ontological validation",
                    "Domain-specific reasoning",
                    "Knowledge graph integration",
                    "Semantic constraint enforcement",
                ],
            },
            "formal_transformation_rules": {
                "purpose": "Core transformation rule implementations",
                "responsibilities": [
                    "Peirce-Dau transformation rules",
                    "Rule validation and precondition checking",
                    "Formal logical operations",
                    "Polarity and nesting calculations",
                ],
            },
            "egi_core_dau": {
                "purpose": "Core EGI data structures and operations",
                "responsibilities": [
                    "EGI graph representation",
                    "Vertex, Edge, Cut data structures",
                    "Area mapping and containment",
                    "Graph validation and integrity",
                ],
            },
            "hierarchical_index": {
                "purpose": "Efficient hierarchical relationship management",
                "responsibilities": [
                    "O(1) polarity lookups",
                    "Nesting level calculations",
                    "Parent-child relationships",
                    "Containment queries",
                ],
            },
            "chapter21_diagram_engine": {
                "purpose": "Chapter 21 transformation coordination",
                "responsibilities": [
                    "Transformation wizard system",
                    "Multi-format synchronization",
                    "View management",
                    "Engine coordination",
                ],
            },
            "corpus_integration": {
                "purpose": "Corpus management and persistence",
                "responsibilities": [
                    "Graph storage and retrieval",
                    "Corpus indexing",
                    "File system integration",
                    "Metadata management",
                ],
            },
            "legacy": {
                "purpose": "Legacy systems and experimental features",
                "responsibilities": [
                    "R-tree spatial indexing",
                    "Experimental algorithms",
                    "Deprecated interfaces",
                    "Research prototypes",
                ],
            },
        }

        # Scan directories and build subsystem map
        for subsystem_name, definition in subsystem_definitions.items():
            self._analyze_subsystem(subsystem_name, definition)

        # Analyze cross-subsystem dependencies
        self._analyze_dependencies()

    def _analyze_subsystem(self, name: str, definition: Dict):
        """Analyze a specific subsystem."""
        # Find files for this subsystem
        key_classes = []
        key_functions = []

        # Look for main files
        patterns = [f"{name}.py", f"{name}_*.py", f"*{name}*.py"]

        subsystem_files = []
        if name == "gui":
            # GUI is a directory
            gui_path = self.root_path / "gui"
            if gui_path.exists():
                subsystem_files = list(gui_path.rglob("*.py"))
        elif name == "legacy":
            # Legacy is a directory
            legacy_path = self.root_path / "legacy"
            if legacy_path.exists():
                subsystem_files = list(legacy_path.rglob("*.py"))
        else:
            # Single file or pattern-based
            for pattern in patterns:
                subsystem_files.extend(self.root_path.glob(pattern))

        # Extract key classes and functions (simplified)
        for file_path in subsystem_files[:5]:  # Limit to first 5 files
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Simple regex-like extraction
                import re

                classes = re.findall(r"class\s+(\w+)", content)
                functions = re.findall(r"def\s+(\w+)", content)

                key_classes.extend(classes[:3])  # Top 3 classes per file
                key_functions.extend(functions[:3])  # Top 3 functions per file

            except Exception:
                continue

        subsystem = Subsystem(
            name=name,
            path=(
                str(self.root_path / name)
                if (self.root_path / name).exists()
                else str(self.root_path)
            ),
            purpose=definition["purpose"],
            key_classes=list(set(key_classes))[:10],  # Unique, max 10
            key_functions=list(set(key_functions))[:10],  # Unique, max 10
            responsibilities=definition["responsibilities"],
            dependencies=[],  # Will be filled by _analyze_dependencies
            provides_to=[],  # Will be filled by _analyze_dependencies
        )

        self.subsystems[name] = subsystem

    def _analyze_dependencies(self):
        """Analyze dependencies between subsystems."""
        # Define known dependency relationships
        dependencies = {
            "gui": [
                "formal_transformation_rules",
                "egi_core_dau",
                "chapter21_diagram_engine",
                "corpus_integration",
            ],
            "chapter21_diagram_engine": [
                "formal_transformation_rules",
                "egi_core_dau",
                "hierarchical_index",
            ],
            "formal_transformation_rules": ["egi_core_dau", "hierarchical_index"],
            "corpus_integration": ["egi_core_dau"],
            "hierarchical_index": ["egi_core_dau"],
            "legacy": ["egi_core_dau"],
        }

        # Update subsystem dependencies
        for subsystem_name, deps in dependencies.items():
            if subsystem_name in self.subsystems:
                self.subsystems[subsystem_name].dependencies = deps

                # Update "provides_to" for dependencies
                for dep in deps:
                    if dep in self.subsystems:
                        self.subsystems[dep].provides_to.append(subsystem_name)

    def get_subsystem_for_concept(self, concept: str) -> List[str]:
        """Find which subsystems handle a specific concept."""
        concept_mapping = {
            "polarity": ["formal_transformation_rules", "hierarchical_index"],
            "hierarchy": ["hierarchical_index", "egi_core_dau"],
            "transformation": [
                "formal_transformation_rules",
                "chapter21_diagram_engine",
            ],
            "gui": ["gui"],
            "spatial": ["legacy"],
            "corpus": ["corpus_integration"],
            "validation": ["formal_transformation_rules", "egi_core_dau"],
        }

        return concept_mapping.get(concept.lower(), [])

    def get_interaction_pattern(self, subsystem1: str, subsystem2: str) -> str:
        """Describe how two subsystems interact."""
        patterns = {
            (
                "gui",
                "formal_transformation_rules",
            ): "GUI invokes transformation rules via wizard system",
            (
                "gui",
                "chapter21_diagram_engine",
            ): "GUI uses engine for transformation coordination",
            (
                "chapter21_diagram_engine",
                "formal_transformation_rules",
            ): "Engine orchestrates rule application",
            (
                "formal_transformation_rules",
                "hierarchical_index",
            ): "Rules use index for O(1) polarity lookups",
            (
                "formal_transformation_rules",
                "egi_core_dau",
            ): "Rules operate on core EGI data structures",
            (
                "hierarchical_index",
                "egi_core_dau",
            ): "Index built from EGI area mappings",
        }

        return patterns.get(
            (subsystem1, subsystem2),
            f"Unknown interaction between {subsystem1} and {subsystem2}",
        )

    def export_architecture_map(self, output_path: str):
        """Export architectural map to JSON."""
        arch_data = {
            "subsystems": {
                name: asdict(subsystem) for name, subsystem in self.subsystems.items()
            },
            "metadata": {
                "total_subsystems": len(self.subsystems),
                "analysis_date": "2025-09-15",
            },
        }

        with open(output_path, "w") as f:
            json.dump(arch_data, f, indent=2)

    def generate_architecture_report(self) -> str:
        """Generate human-readable architecture report."""
        report = []
        report.append("# Arisbe Architecture Map\n")

        report.append("## Subsystem Overview")
        for name, subsystem in self.subsystems.items():
            report.append(f"### {name.title()}")
            report.append(f"**Purpose**: {subsystem.purpose}")
            report.append(f"**Key Responsibilities**:")
            for resp in subsystem.responsibilities:
                report.append(f"- {resp}")

            if subsystem.key_classes:
                report.append(
                    f"**Key Classes**: {', '.join(subsystem.key_classes[:5])}"
                )

            if subsystem.dependencies:
                report.append(f"**Dependencies**: {', '.join(subsystem.dependencies)}")

            if subsystem.provides_to:
                report.append(f"**Provides To**: {', '.join(subsystem.provides_to)}")

            report.append("")

        report.append("## Common Problem → Subsystem Mapping")
        concept_mappings = {
            "Polarity Calculation": [
                "formal_transformation_rules",
                "hierarchical_index",
            ],
            "Hierarchy/Nesting": ["hierarchical_index", "egi_core_dau"],
            "Transformation Rules": [
                "formal_transformation_rules",
                "chapter21_diagram_engine",
            ],
            "User Interface": ["gui"],
            "Spatial Operations": ["legacy"],
            "Data Persistence": ["corpus_integration"],
        }

        for problem, subsystems in concept_mappings.items():
            report.append(f"- **{problem}**: {' → '.join(subsystems)}")

        return "\n".join(report)


def main():
    """Generate architectural map for Arisbe."""
    mapper = ArchitecturalMapper("/Users/mjh/Sync/GitHub/Arisbe/src")

    print("Mapping architectural structure...")
    mapper.analyze_architecture()

    print(f"Identified {len(mapper.subsystems)} major subsystems")

    # Export architecture map
    mapper.export_architecture_map(
        "/Users/mjh/Sync/GitHub/Arisbe/architecture_map.json"
    )

    # Generate report
    report = mapper.generate_architecture_report()
    with open("/Users/mjh/Sync/GitHub/Arisbe/ARCHITECTURE_MAP.md", "w") as f:
        f.write(report)

    print("Architecture map generated:")
    print("- architecture_map.json (machine-readable)")
    print("- ARCHITECTURE_MAP.md (human-readable)")

    # Show polarity subsystems
    polarity_subsystems = mapper.get_subsystem_for_concept("polarity")
    print(f"\nPolarity is handled by: {', '.join(polarity_subsystems)}")


if __name__ == "__main__":
    main()
