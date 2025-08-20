#!/usr/bin/env python3
"""
Architectural Integrity System - Protection against code contamination and regression

This system provides stronger protection than API contracts by enforcing architectural
principles and preventing integration of deprecated/failed code patterns.

Key Protection Mechanisms:
1. Architectural Lineage Tracking - Know what code is current vs deprecated
2. Integration Gatekeepers - Prevent linking to superseded components  
3. Regression Detection - Identify when newer code reverts to older patterns
4. Clean Architecture Enforcement - Maintain separation between layers
"""

import os
import re
import ast
import inspect
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class ArchitecturalComponent:
    """Represents a component in the architectural lineage."""
    name: str
    file_path: str
    creation_date: datetime
    status: str  # 'current', 'deprecated', 'failed', 'experimental'
    dependencies: Set[str]
    supersedes: Set[str]  # Components this replaces
    superseded_by: Optional[str] = None


@dataclass
class IntegrationViolation:
    """Represents a violation of architectural integrity."""
    violation_type: str
    component: str
    deprecated_dependency: str
    file_path: str
    line_number: int
    description: str


class ArchitecturalLineageTracker:
    """Tracks the lineage and status of architectural components."""
    
    def __init__(self):
        self.components: Dict[str, ArchitecturalComponent] = {}
        self.deprecated_patterns: Set[str] = set()
        self.failed_patterns: Set[str] = set()
        self._initialize_arisbe_lineage()
    
    def _initialize_arisbe_lineage(self):
        """Initialize the architectural lineage for Arisbe project."""
        
        # Current Architecture (Post-9-Phase Pipeline)
        self.register_component(ArchitecturalComponent(
            name="graphviz_utilities",
            file_path="src/graphviz_utilities.py", 
            creation_date=datetime.now(),
            status="current",
            dependencies={"egi_core_dau"},
            supersedes={"graphviz_layout_engine_v2"}
        ))
        
        self.register_component(ArchitecturalComponent(
            name="layout_phase_implementations", 
            file_path="src/layout_phase_implementations.py",
            creation_date=datetime.now(),
            status="current",
            dependencies={"graphviz_utilities", "egi_core_dau", "layout_engine"},
            supersedes={"legacy_layout_phases"}
        ))
        
        # Deprecated Components (Must Not Be Imported)
        self.register_component(ArchitecturalComponent(
            name="graphviz_layout_engine_v2",
            file_path="src/graphviz_layout_engine_v2.py",
            creation_date=datetime(2024, 1, 1),  # Earlier date
            status="deprecated",
            dependencies=set(),
            supersedes=set(),
            superseded_by="graphviz_utilities"
        ))
        
        # Failed Patterns (Must Be Avoided)
        self.add_failed_pattern("incremental_graphviz_wrapper")
        self.add_failed_pattern("get_graphviz_positions_for_phase")
        self.add_failed_pattern("get_graphviz_bounds_for_phase")
        
        # Deprecated Import Patterns
        self.add_deprecated_pattern("from.*graphviz_layout_engine_v2.*import")
        self.add_deprecated_pattern("from.*incremental_graphviz_wrapper.*import")
    
    def register_component(self, component: ArchitecturalComponent):
        """Register a component in the lineage."""
        self.components[component.name] = component
        
        # Mark superseded components as deprecated
        for superseded_name in component.supersedes:
            if superseded_name in self.components:
                self.components[superseded_name].status = "deprecated"
                self.components[superseded_name].superseded_by = component.name
    
    def add_deprecated_pattern(self, pattern: str):
        """Add a deprecated code pattern to avoid."""
        self.deprecated_patterns.add(pattern)
    
    def add_failed_pattern(self, pattern: str):
        """Add a failed code pattern to avoid."""
        self.failed_patterns.add(pattern)
    
    def is_deprecated(self, component_name: str) -> bool:
        """Check if a component is deprecated."""
        return (component_name in self.components and 
                self.components[component_name].status == "deprecated")
    
    def is_failed(self, pattern: str) -> bool:
        """Check if a pattern is known to be failed."""
        return any(failed in pattern for failed in self.failed_patterns)
    
    def get_current_replacement(self, deprecated_component: str) -> Optional[str]:
        """Get the current replacement for a deprecated component."""
        if deprecated_component in self.components:
            return self.components[deprecated_component].superseded_by
        return None


class IntegrationGatekeeper:
    """Prevents integration of deprecated or failed code patterns."""
    
    def __init__(self, lineage_tracker: ArchitecturalLineageTracker):
        self.lineage_tracker = lineage_tracker
        self.violations: List[IntegrationViolation] = []
    
    def scan_file_for_violations(self, file_path: str) -> List[IntegrationViolation]:
        """Scan a file for architectural violations."""
        violations = []
        
        if not os.path.exists(file_path):
            return violations
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check for deprecated imports
            violations.extend(self._check_deprecated_imports(file_path, lines))
            
            # Check for failed patterns
            violations.extend(self._check_failed_patterns(file_path, lines))
            
            # Check for superseded dependencies
            violations.extend(self._check_superseded_dependencies(file_path, lines))
            
        except Exception as e:
            print(f"⚠️  Error scanning {file_path}: {e}")
        
        return violations
    
    def _check_deprecated_imports(self, file_path: str, lines: List[str]) -> List[IntegrationViolation]:
        """Check for imports of deprecated components."""
        violations = []
        
        for line_num, line in enumerate(lines, 1):
            for pattern in self.lineage_tracker.deprecated_patterns:
                if re.search(pattern, line):
                    violations.append(IntegrationViolation(
                        violation_type="deprecated_import",
                        component=os.path.basename(file_path),
                        deprecated_dependency=pattern,
                        file_path=file_path,
                        line_number=line_num,
                        description=f"Imports deprecated pattern: {pattern}"
                    ))
        
        return violations
    
    def _check_failed_patterns(self, file_path: str, lines: List[str]) -> List[IntegrationViolation]:
        """Check for usage of known failed patterns."""
        violations = []
        
        for line_num, line in enumerate(lines, 1):
            for failed_pattern in self.lineage_tracker.failed_patterns:
                if failed_pattern in line:
                    violations.append(IntegrationViolation(
                        violation_type="failed_pattern",
                        component=os.path.basename(file_path),
                        deprecated_dependency=failed_pattern,
                        file_path=file_path,
                        line_number=line_num,
                        description=f"Uses known failed pattern: {failed_pattern}"
                    ))
        
        return violations
    
    def _check_superseded_dependencies(self, file_path: str, lines: List[str]) -> List[IntegrationViolation]:
        """Check for dependencies on superseded components."""
        violations = []
        
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith('from ') or line.strip().startswith('import '):
                for component_name, component in self.lineage_tracker.components.items():
                    if (component.status == "deprecated" and 
                        component_name in line and
                        'graphviz_layout_engine_v2' in line):
                        
                        replacement = self.lineage_tracker.get_current_replacement(component_name)
                        violations.append(IntegrationViolation(
                            violation_type="superseded_dependency",
                            component=os.path.basename(file_path),
                            deprecated_dependency=component_name,
                            file_path=file_path,
                            line_number=line_num,
                            description=f"Depends on superseded component {component_name}. Use {replacement} instead."
                        ))
        
        return violations


class RegressionDetector:
    """Detects when code reverts to older, superseded patterns."""
    
    def __init__(self, lineage_tracker: ArchitecturalLineageTracker):
        self.lineage_tracker = lineage_tracker
    
    def detect_architectural_regression(self, file_path: str) -> List[IntegrationViolation]:
        """Detect if code has regressed to older architectural patterns."""
        violations = []
        
        if not os.path.exists(file_path):
            return violations
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for regression patterns
            violations.extend(self._check_for_monolithic_regression(file_path, content))
            violations.extend(self._check_for_deprecated_api_usage(file_path, content))
            
        except Exception as e:
            print(f"⚠️  Error detecting regression in {file_path}: {e}")
        
        return violations
    
    def _check_for_monolithic_regression(self, file_path: str, content: str) -> List[IntegrationViolation]:
        """Check if code has regressed to monolithic patterns."""
        violations = []
        
        # Check for signs of monolithic code (very long files, too many responsibilities)
        lines = content.split('\n')
        if len(lines) > 1500:  # Threshold for monolithic warning
            violations.append(IntegrationViolation(
                violation_type="monolithic_regression",
                component=os.path.basename(file_path),
                deprecated_dependency="monolithic_pattern",
                file_path=file_path,
                line_number=len(lines),
                description=f"File has {len(lines)} lines - potential monolithic regression"
            ))
        
        return violations
    
    def _check_for_deprecated_api_usage(self, file_path: str, content: str) -> List[IntegrationViolation]:
        """Check for usage of deprecated API patterns."""
        violations = []
        
        # Specific patterns that indicate regression to old APIs
        deprecated_apis = [
            "graphviz_layout_engine_v2",
            "get_graphviz_positions_for_phase", 
            "get_graphviz_bounds_for_phase"
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for api in deprecated_apis:
                if api in line:
                    violations.append(IntegrationViolation(
                        violation_type="deprecated_api_regression",
                        component=os.path.basename(file_path),
                        deprecated_dependency=api,
                        file_path=file_path,
                        line_number=line_num,
                        description=f"Regressed to deprecated API: {api}"
                    ))
        
        return violations


class ArchitecturalIntegritySystem:
    """Main system for protecting architectural integrity."""
    
    def __init__(self):
        self.lineage_tracker = ArchitecturalLineageTracker()
        self.gatekeeper = IntegrationGatekeeper(self.lineage_tracker)
        self.regression_detector = RegressionDetector(self.lineage_tracker)
    
    def scan_project(self, project_root: str = "/Users/mjh/Sync/GitHub/Arisbe") -> Dict[str, List[IntegrationViolation]]:
        """Scan entire project for architectural violations."""
        all_violations = {}
        
        # Scan key files in the 9-phase pipeline
        key_files = [
            "src/layout_phase_implementations.py",
            "src/graphviz_utilities.py", 
            "src/layout_engine.py",
            "test_gui_integration.py"
        ]
        
        for file_path in key_files:
            full_path = os.path.join(project_root, file_path)
            violations = []
            
            # Check for integration violations
            violations.extend(self.gatekeeper.scan_file_for_violations(full_path))
            
            # Check for regressions
            violations.extend(self.regression_detector.detect_architectural_regression(full_path))
            
            if violations:
                all_violations[file_path] = violations
        
        return all_violations
    
    def generate_protection_report(self) -> str:
        """Generate a report on architectural protection status."""
        violations = self.scan_project()
        
        report = ["🛡️  ARCHITECTURAL INTEGRITY REPORT", "=" * 50, ""]
        
        if not violations:
            report.extend([
                "✅ NO VIOLATIONS DETECTED",
                "   All components follow current architectural patterns",
                "   No deprecated dependencies found",
                "   No regression to superseded code detected",
                ""
            ])
        else:
            report.append("⚠️  VIOLATIONS DETECTED:")
            report.append("")
            
            for file_path, file_violations in violations.items():
                report.append(f"📁 {file_path}:")
                for violation in file_violations:
                    report.append(f"   ❌ Line {violation.line_number}: {violation.description}")
                    if violation.violation_type == "superseded_dependency":
                        replacement = self.lineage_tracker.get_current_replacement(violation.deprecated_dependency)
                        if replacement:
                            report.append(f"      💡 Suggested fix: Use {replacement} instead")
                report.append("")
        
        # Add architectural lineage summary
        report.extend([
            "📋 CURRENT ARCHITECTURAL LINEAGE:",
            ""
        ])
        
        for name, component in self.lineage_tracker.components.items():
            status_emoji = {"current": "✅", "deprecated": "❌", "failed": "💥"}.get(component.status, "❓")
            report.append(f"   {status_emoji} {name} ({component.status})")
            if component.superseded_by:
                report.append(f"      ↳ Superseded by: {component.superseded_by}")
        
        return "\n".join(report)
    
    def _validate_serialization_integrity(self) -> List[Any]:
        """Validate EGDF serialization system integrity."""
        violations = []
        
        try:
            from egdf_structural_lock import EGDFStructuralProtector
            protector = EGDFStructuralProtector()
            
            is_valid, errors = protector.validate_structural_integrity()
            if not is_valid:
                for error in errors:
                    violations.append(type('Violation', (), {'description': f"Serialization integrity: {error}"})())
        except Exception as e:
            violations.append(type('Violation', (), {'description': f"Serialization validation failed: {e}"})())
        
        return violations
    
    def enforce_clean_integration(self, file_path: str) -> bool:
        violations = []
        
        # Add serialization integrity validation
        serialization_violations = self._validate_serialization_integrity()
        violations.extend(serialization_violations)
        
        violations.extend(self.gatekeeper.scan_file_for_violations(file_path))
        violations.extend(self.regression_detector.detect_architectural_regression(file_path))
        
        if violations:
            print(f"🚫 INTEGRATION BLOCKED: {file_path}")
            for violation in violations:
                print(f"   ❌ {violation.description}")
            return False
        
        print(f"✅ INTEGRATION APPROVED: {file_path}")
        return True


# Convenience function for project protection
def protect_arisbe_architecture():
    """Run architectural protection scan on Arisbe project."""
    system = ArchitecturalIntegritySystem()
    report = system.generate_protection_report()
    print(report)
    return system


if __name__ == "__main__":
    # Run architectural protection
    protection_system = protect_arisbe_architecture()
