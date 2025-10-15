"""
Coherence Maintenance System for Arisbe Codebase

This system provides automated monitoring and enforcement of codebase coherence
to prevent the accumulation of orphaned code and interface inconsistencies.
"""

import ast
import importlib.util
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from .coherence_analyzer import CoherenceAnalyzer
from function_index_generator import FunctionIndexGenerator
from semantic_code_analyzer import SemanticCodeAnalyzer


@dataclass
class CoherenceMetrics:
    """Metrics for tracking codebase coherence over time."""

    timestamp: str
    total_functions: int
    orphaned_functions: int
    interface_inconsistencies: int
    naming_inconsistencies: int
    import_inconsistencies: int
    coherence_score: float  # 0-100, higher is better

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class IntegrationRule:
    """Rule for maintaining integration between subsystems."""

    name: str
    description: str
    source_pattern: str  # File pattern or function pattern
    target_pattern: str  # What it should connect to
    validation_function: str  # Function to validate the connection
    severity: str  # 'error', 'warning', 'info'


class CoherenceMaintenanceSystem:
    """System for maintaining codebase coherence through automated monitoring."""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.coherence_history: List[CoherenceMetrics] = []
        self.integration_rules: List[IntegrationRule] = []
        self.load_integration_rules()

    def load_integration_rules(self):
        """Load integration rules that define expected connections."""
        self.integration_rules = [
            IntegrationRule(
                name="polarity_standardization",
                description="All polarity calculations should use HierarchicalIndex",
                source_pattern="*polarity*",
                target_pattern="HierarchicalIndex.get_polarity",
                validation_function="validate_polarity_usage",
                severity="error",
            ),
            IntegrationRule(
                name="transformation_interface",
                description="All transformation functions should use TransformationContext",
                source_pattern="*transformation*",
                target_pattern="TransformationContext",
                validation_function="validate_transformation_interface",
                severity="error",
            ),
            IntegrationRule(
                name="dau_theorem_integration",
                description="Dau theorem tests should be connected to validation pipeline",
                source_pattern="dau_theorem_correspondence_tests.py",
                target_pattern="formal_transformation_rules.py",
                validation_function="validate_theorem_integration",
                severity="warning",
            ),
            IntegrationRule(
                name="corpus_manager_integration",
                description="CorpusManager should be connected to GUI",
                source_pattern="corpus_integration.py",
                target_pattern="*gui*",
                validation_function="validate_corpus_integration",
                severity="warning",
            ),
            IntegrationRule(
                name="history_unification",
                description="All history systems should use unified HistoryTracker",
                source_pattern="*history*",
                target_pattern="HistoryTracker",
                validation_function="validate_history_unification",
                severity="error",
            ),
        ]

    def analyze_current_coherence(self) -> CoherenceMetrics:
        """Analyze current codebase coherence and return metrics."""
        print("Analyzing current codebase coherence...")

        # Run coherence analyzer
        analyzer = CoherenceAnalyzer(self.project_root)
        analyzer.run_full_analysis()
        analysis_result = {
            "naming_inconsistencies": analyzer.inconsistencies,
            "interface_incompatibilities": [
                inc
                for inc in analyzer.inconsistencies
                if inc.type == "interface_incompatibility"
            ],
            "orphaned_code": analyzer.orphans,
            "import_inconsistencies": [
                inc
                for inc in analyzer.inconsistencies
                if inc.type == "import_inconsistency"
            ],
        }

        # Calculate coherence score
        total_issues = (
            len(analysis_result.get("naming_inconsistencies", []))
            + len(analysis_result.get("interface_incompatibilities", []))
            + len(analysis_result.get("orphaned_code", []))
            + len(analysis_result.get("import_inconsistencies", []))
        )

        # Generate function index for total function count
        function_indexer = FunctionIndexGenerator(self.project_root)
        function_index = function_indexer.generate_index()
        total_functions = len(function_index.get("functions", []))

        # Calculate coherence score (100 - percentage of problematic functions)
        if total_functions > 0:
            coherence_score = max(0, 100 - (total_issues / total_functions * 100))
        else:
            coherence_score = 100

        metrics = CoherenceMetrics(
            timestamp=datetime.now().isoformat(),
            total_functions=total_functions,
            orphaned_functions=len(analysis_result.get("orphaned_code", [])),
            interface_inconsistencies=len(
                analysis_result.get("interface_incompatibilities", [])
            ),
            naming_inconsistencies=len(
                analysis_result.get("naming_inconsistencies", [])
            ),
            import_inconsistencies=len(
                analysis_result.get("import_inconsistencies", [])
            ),
            coherence_score=coherence_score,
        )

        self.coherence_history.append(metrics)
        return metrics

    def validate_integration_rules(self) -> Dict[str, List[str]]:
        """Validate all integration rules and return violations."""
        violations = {}

        for rule in self.integration_rules:
            rule_violations = self._validate_single_rule(rule)
            if rule_violations:
                violations[rule.name] = rule_violations

        return violations

    def _validate_single_rule(self, rule: IntegrationRule) -> List[str]:
        """Validate a single integration rule."""
        violations = []

        try:
            # Use the validation function specified in the rule
            if hasattr(self, rule.validation_function):
                validation_func = getattr(self, rule.validation_function)
                rule_violations = validation_func(rule)
                violations.extend(rule_violations)
        except Exception as e:
            violations.append(f"Error validating rule {rule.name}: {str(e)}")

        return violations

    def validate_polarity_usage(self, rule: IntegrationRule) -> List[str]:
        """Validate that polarity calculations use HierarchicalIndex."""
        violations = []

        # Search for polarity-related functions
        analyzer = SemanticCodeAnalyzer(self.project_root)
        graph = analyzer.build_knowledge_graph()

        polarity_functions = [
            node
            for node in graph.nodes()
            if "polarity" in node.lower()
            and "function" in graph.nodes[node].get("type", "")
        ]

        for func in polarity_functions:
            # Check if function uses HierarchicalIndex
            if not self._function_uses_hierarchical_index(func):
                violations.append(
                    f"Function {func} calculates polarity without using HierarchicalIndex"
                )

        return violations

    def validate_transformation_interface(self, rule: IntegrationRule) -> List[str]:
        """Validate transformation interface standardization."""
        violations = []

        # Find transformation functions
        function_indexer = FunctionIndexGenerator(self.project_root)
        function_index = function_indexer.generate_index()

        transformation_functions = [
            func
            for func in function_index.get("functions", [])
            if "transformation" in func.get("name", "").lower()
        ]

        for func in transformation_functions:
            # Check if function uses TransformationContext
            if not self._function_uses_transformation_context(func):
                violations.append(
                    f"Function {func.get('name')} doesn't use TransformationContext interface"
                )

        return violations

    def validate_theorem_integration(self, rule: IntegrationRule) -> List[str]:
        """Validate Dau theorem integration."""
        violations = []

        # Check if DauTheoremCorrespondenceTests is connected to validation pipeline
        theorem_file = os.path.join(
            self.project_root, "src", "dau_theorem_correspondence_tests.py"
        )
        formal_rules_file = os.path.join(
            self.project_root, "src", "formal_transformation_rules.py"
        )

        if os.path.exists(theorem_file) and os.path.exists(formal_rules_file):
            # Check for imports or references
            if not self._files_are_connected(theorem_file, formal_rules_file):
                violations.append(
                    "DauTheoremCorrespondenceTests not integrated with formal transformation rules"
                )

        return violations

    def validate_corpus_integration(self, rule: IntegrationRule) -> List[str]:
        """Validate tomos manager integration."""
        violations = []

        corpus_file = os.path.join(self.project_root, "src", "corpus_integration.py")
        gui_files = self._find_gui_files()

        if os.path.exists(corpus_file) and gui_files:
            # Check if tomos manager is used in any GUI file
            connected = False
            for gui_file in gui_files:
                if self._files_are_connected(corpus_file, gui_file):
                    connected = True
                    break

            if not connected:
                violations.append("CorpusManager not integrated with GUI components")

        return violations

    def validate_history_unification(self, rule: IntegrationRule) -> List[str]:
        """Validate history system unification."""
        violations = []

        # Find all history-related files
        history_files = []
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                if "history" in file.lower() and file.endswith(".py"):
                    history_files.append(os.path.join(root, file))

        if len(history_files) > 1:
            # Check if they use a unified interface
            unified_interface_usage = 0
            for history_file in history_files:
                if self._file_uses_history_tracker(history_file):
                    unified_interface_usage += 1

            if unified_interface_usage < len(history_files):
                violations.append(
                    f"Found {len(history_files)} history files but only {unified_interface_usage} use unified HistoryTracker interface"
                )

        return violations

    def _function_uses_hierarchical_index(self, function_name: str) -> bool:
        """Check if a function uses HierarchicalIndex."""
        # This would need to analyze the function's AST or source code
        # Simplified implementation for now
        return "hierarchical_index" in function_name.lower()

    def _function_uses_transformation_context(self, func_info: Dict) -> bool:
        """Check if a function uses TransformationContext."""
        # Check function signature or imports
        return "TransformationContext" in str(func_info.get("signature", ""))

    def _files_are_connected(self, file1: str, file2: str) -> bool:
        """Check if two files are connected through imports or references."""
        try:
            with open(file1, "r") as f:
                content1 = f.read()
            with open(file2, "r") as f:
                content2 = f.read()

            # Check for imports or references
            file1_name = os.path.basename(file1).replace(".py", "")
            file2_name = os.path.basename(file2).replace(".py", "")

            return file1_name in content2 or file2_name in content1
        except Exception:
            return False

    def _find_gui_files(self) -> List[str]:
        """Find all GUI-related files."""
        gui_files = []
        gui_dirs = ["gui", "interface", "ui"]

        for root, dirs, files in os.walk(self.project_root):
            if any(gui_dir in root.lower() for gui_dir in gui_dirs):
                for file in files:
                    if file.endswith(".py"):
                        gui_files.append(os.path.join(root, file))

        return gui_files

    def _file_uses_history_tracker(self, file_path: str) -> bool:
        """Check if a file uses the unified HistoryTracker interface."""
        try:
            with open(file_path, "r") as f:
                content = f.read()
            return "HistoryTracker" in content
        except Exception:
            return False

    def generate_coherence_report(self) -> str:
        """Generate a comprehensive coherence report."""
        current_metrics = self.analyze_current_coherence()
        rule_violations = self.validate_integration_rules()

        report = f"""
# Arisbe Codebase Coherence Report
Generated: {current_metrics.timestamp}

## Current Coherence Metrics
- **Coherence Score**: {current_metrics.coherence_score:.1f}/100
- **Total Functions**: {current_metrics.total_functions}
- **Orphaned Functions**: {current_metrics.orphaned_functions}
- **Interface Inconsistencies**: {current_metrics.interface_inconsistencies}
- **Naming Inconsistencies**: {current_metrics.naming_inconsistencies}
- **Import Inconsistencies**: {current_metrics.import_inconsistencies}

## Integration Rule Violations
"""

        if rule_violations:
            for rule_name, violations in rule_violations.items():
                report += f"\n### {rule_name}\n"
                for violation in violations:
                    report += f"- {violation}\n"
        else:
            report += "\n✅ No integration rule violations detected!\n"

        # Add trend analysis if we have history
        if len(self.coherence_history) > 1:
            previous = self.coherence_history[-2]
            current = self.coherence_history[-1]

            score_change = current.coherence_score - previous.coherence_score
            orphan_change = current.orphaned_functions - previous.orphaned_functions

            report += f"""
## Trend Analysis
- **Coherence Score Change**: {score_change:+.1f}
- **Orphaned Functions Change**: {orphan_change:+d}
"""

        return report

    def save_coherence_metrics(self, filename: str = "coherence_metrics.json"):
        """Save coherence metrics to file."""
        metrics_data = [metrics.to_dict() for metrics in self.coherence_history]

        with open(os.path.join(self.project_root, filename), "w") as f:
            json.dump(metrics_data, f, indent=2)

    def create_pre_commit_hook(self):
        """Create a pre-commit hook to check coherence before commits."""
        hook_content = """#!/bin/bash
# Arisbe Coherence Pre-commit Hook

echo "Checking codebase coherence..."
python tools/coherence_maintenance_system.py --check

if [ $? -ne 0 ]; then
    echo "❌ Coherence check failed. Please address issues before committing."
    exit 1
fi

echo "✅ Coherence check passed."
exit 0
"""

        hooks_dir = os.path.join(self.project_root, ".git", "hooks")
        if os.path.exists(hooks_dir):
            hook_path = os.path.join(hooks_dir, "pre-commit")
            with open(hook_path, "w") as f:
                f.write(hook_content)
            os.chmod(hook_path, 0o755)
            print(f"Created pre-commit hook at {hook_path}")


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Arisbe Coherence Maintenance System")
    parser.add_argument("--check", action="store_true", help="Check current coherence")
    parser.add_argument(
        "--report", action="store_true", help="Generate coherence report"
    )
    parser.add_argument(
        "--install-hook", action="store_true", help="Install pre-commit hook"
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()

    system = CoherenceMaintenanceSystem(args.project_root)

    if args.check:
        metrics = system.analyze_current_coherence()
        violations = system.validate_integration_rules()

        print(f"Coherence Score: {metrics.coherence_score:.1f}/100")
        print(
            f"Issues Found: {metrics.orphaned_functions + metrics.interface_inconsistencies}"
        )

        if violations:
            print("Integration rule violations detected:")
            for rule, rule_violations in violations.items():
                print(f"  {rule}: {len(rule_violations)} violations")
            exit(1)
        else:
            print("✅ All integration rules satisfied")
            exit(0)

    elif args.report:
        report = system.generate_coherence_report()
        print(report)

        # Save report to file
        with open("COHERENCE_REPORT.md", "w") as f:
            f.write(report)
        print("\nReport saved to COHERENCE_REPORT.md")

    elif args.install_hook:
        system.create_pre_commit_hook()
        print("Pre-commit hook installed successfully")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
