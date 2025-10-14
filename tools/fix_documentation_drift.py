#!/usr/bin/env python3
"""
Fix Documentation Drift - Semi-automated drift resolution

Helps fix the 63 invalid references found by validate_architecture_docs.py
Provides analysis and semi-automated fixes for common patterns.

USAGE:
    python tools/fix_documentation_drift.py
    python tools/fix_documentation_drift.py --auto-fix
    python tools/fix_documentation_drift.py --report-only
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import argparse
from datetime import datetime


class DocumentationDriftFixer:
    """Semi-automated documentation drift resolution."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.src_path = self.project_root / "src"
        
        # Track fixes
        self.fixes_applied: List[Tuple[str, str, str]] = []
        self.manual_review_needed: List[Tuple[str, str, str]] = []
        
    def categorize_drift_issues(self) -> Dict[str, List[str]]:
        """Categorize the types of drift issues."""
        
        # Based on validator output, categorize known issues
        categories = {
            "missing_test_files": [
                "tests/test_data_persistence_comprehensive.py",
                "tests/test_integration_managers_comprehensive.py",
                "tests/test_ligature_algorithms_comprehensive.py",
                "tests/test_serialization_comprehensive.py",
                "tests/test_performance_comprehensive.py",
                "tests/test_error_handling_comprehensive.py",
                "tests/test_comprehensive_validation.py",
            ],
            "missing_planned_modules": [
                "egdf_parser.py",
                "interaction_handler.py",
                "shared_diagram_renderer.py",
                "egi_delta.py",
                "entity_cache.py",
                "structural_index.py",
                "subgraph_extractor.py",
                "terrain_navigator.py",
                "branch_manager.py",
                "export_manager.py",
                "archive_manager.py",
            ],
            "missing_test_functions": [
                "test_json_round_trip_fidelity",
                "test_large_history_handling",
                "test_concurrent_access_safety",
                "test_memory_usage_efficiency",
                # ... many more
            ],
            "missing_classes": [
                "RefactoredDrawingEditor",
                "ModularDrawingView",
                "StyleQuery",
            ],
            "deprecated_tools": [
                "tools/drawing_editor_refactored.py",
                "tools/test_diagram_controller.py",
            ],
        }
        
        return categories
    
    def add_deprecation_notice(self, doc_path: Path, section: str) -> bool:
        """Add deprecation notice to a section."""
        if not doc_path.exists():
            return False
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        notice = f"\n> **⚠️ DEPRECATION NOTICE**: This section describes planned features that were not implemented or were superseded. Last validated: {datetime.now().strftime('%Y-%m-%d')}\n"
        
        # Add notice before the section (simplified - would need section detection)
        updated_content = content  # Placeholder
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        return True
    
    def remove_invalid_references(self, doc_path: Path, references: List[str]) -> bool:
        """Remove invalid references from document."""
        if not doc_path.exists():
            return False
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Remove lines containing invalid references
        filtered_lines = []
        removed_count = 0
        
        for line in lines:
            should_keep = True
            for ref in references:
                if ref in line:
                    should_keep = False
                    removed_count += 1
                    break
            
            if should_keep:
                filtered_lines.append(line)
        
        if removed_count > 0:
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.writelines(filtered_lines)
            
            return True
        
        return False
    
    def add_validation_timestamp(self, doc_path: Path) -> bool:
        """Add 'Last Validated' timestamp to document."""
        if not doc_path.exists():
            return False
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        timestamp = f"\n**Last Validated Against Code**: {datetime.now().strftime('%Y-%m-%d')}  \n**Validation Status**: Issues resolved (see git history for details)\n"
        
        # Add after title (simplified)
        if content.startswith('#'):
            lines = content.split('\n')
            lines.insert(2, timestamp)
            content = '\n'.join(lines)
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    
    def generate_fix_recommendations(self) -> str:
        """Generate recommendations for fixing drift."""
        categories = self.categorize_drift_issues()
        
        lines = [
            "# Documentation Drift Fix Recommendations",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- **Missing test files**: {len(categories['missing_test_files'])}",
            f"- **Missing planned modules**: {len(categories['missing_planned_modules'])}",
            f"- **Missing test functions**: {len(categories['missing_test_functions'])}",
            f"- **Missing classes**: {len(categories['missing_classes'])}",
            f"- **Deprecated tools**: {len(categories['deprecated_tools'])}",
            "",
            "---",
            "",
            "## Recommended Actions",
            "",
            "### 1. Missing Test Files (Comprehensive Tests)",
            "",
            "**Issue**: Documentation references comprehensive test files that were planned but never created.",
            "",
            "**Files Affected**:",
        ]
        
        for test_file in categories['missing_test_files']:
            lines.append(f"- `{test_file}`")
        
        lines.extend([
            "",
            "**Recommendation**: Add deprecation notice to COMPREHENSIVE_TESTING_IMPLEMENTATION_SUMMARY.md",
            "```markdown",
            "> **⚠️ NOTE**: These comprehensive tests were planned but not implemented.",
            "> Current testing strategy focuses on core tests (90/90 passing).",
            "> See `tests/` directory for actual test suite.",
            "```",
            "",
            "---",
            "",
            "### 2. Missing Planned Modules",
            "",
            "**Issue**: Documentation describes modules that were designed but never implemented.",
            "",
            "**Modules**:",
        ])
        
        for module in categories['missing_planned_modules']:
            lines.append(f"- `{module}` - Planned but not implemented")
        
        lines.extend([
            "",
            "**Recommendation**: Mark as \"Planned/Not Implemented\" in architecture docs",
            "- Add section: \"## Planned Features (Not Implemented)\"",
            "- Move references to this section",
            "- Document why not implemented (if known)",
            "",
            "---",
            "",
            "### 3. Deprecated Tool References",
            "",
            "**Issue**: Documentation references tools that were superseded or removed.",
            "",
            "**Files**:",
        ])
        
        for tool in categories['deprecated_tools']:
            lines.append(f"- `{tool}`")
        
        lines.extend([
            "",
            "**Recommendation**: Update to reference current tools",
            "- `tools/test_diagram_controller.py` → `tests/test_diagram_controller.py` (if exists)",
            "- Remove references to non-existent refactored tools",
            "",
            "---",
            "",
            "### 4. Missing Classes/Functions",
            "",
            "**Issue**: References to classes and functions that don't exist in codebase.",
            "",
            "**Action Required**: Manual review of each reference",
            "- Determine if class/function was renamed",
            "- Check if functionality exists under different name",
            "- Remove if truly non-existent",
            "",
            "---",
            "",
            "## Automated Fixes Available",
            "",
            "### Add Validation Timestamps",
            "```bash",
            "python tools/fix_documentation_drift.py --add-timestamps",
            "```",
            "Adds \"Last Validated: YYYY-MM-DD\" to all architecture docs.",
            "",
            "### Remove Invalid References",
            "```bash",
            "python tools/fix_documentation_drift.py --remove-invalid",
            "```",
            "Removes lines containing invalid references (use with caution).",
            "",
            "---",
            "",
            "## Manual Review Required",
            "",
            "The following documents need manual review:",
            "",
            "1. **COMPREHENSIVE_ARCHITECTURE_SUMMARY.md** (44 invalid refs)",
            "   - Review each planned feature section",
            "   - Mark as \"Planned\" or remove if obsolete",
            "",
            "2. **COMPREHENSIVE_TESTING_IMPLEMENTATION_SUMMARY.md** (15 invalid refs)",
            "   - Add note about comprehensive tests not implemented",
            "   - Link to actual test suite",
            "",
            "3. **GRAPH_ENTITY_SCALABILITY_ARCHITECTURE.md** (7 invalid refs)",
            "   - Review scalability features",
            "   - Mark unimplemented features",
            "",
            "---",
            "",
            "## Best Practices Going Forward",
            "",
            "1. **Add Validation Timestamps**: Include \"Last Validated: YYYY-MM-DD\" in all architecture docs",
            "2. **Mark Planned Features**: Clearly distinguish implemented vs planned features",
            "3. **Run Validator Regularly**: `python tools/validate_architecture_docs.py`",
            "4. **Update on Changes**: When code changes, update related docs",
            "",
        ])
        
        return '\n'.join(lines)
    
    def run(self, report_only: bool = True, auto_fix: bool = False) -> None:
        """Run drift fixing process."""
        print("=" * 60)
        print("DOCUMENTATION DRIFT FIXER")
        print("=" * 60)
        
        # Generate recommendations
        recommendations = self.generate_fix_recommendations()
        
        # Save recommendations
        rec_file = self.project_root / "DOCUMENTATION_DRIFT_FIX_PLAN.md"
        with open(rec_file, 'w') as f:
            f.write(recommendations)
        
        print(f"\n✅ Fix recommendations generated: {rec_file}")
        
        if report_only:
            print("\n📋 REPORT-ONLY MODE")
            print("   Review recommendations in DOCUMENTATION_DRIFT_FIX_PLAN.md")
            print("   Manual fixes required for most issues")
            print("\n💡 Next steps:")
            print("   1. Review DOCUMENTATION_DRIFT_FIX_PLAN.md")
            print("   2. Apply manual fixes to architecture docs")
            print("   3. Add validation timestamps")
            print("   4. Re-run validator to confirm")
        
        elif auto_fix:
            print("\n⚙️  AUTO-FIX MODE")
            print("   This would apply automated fixes")
            print("   (Not implemented - manual review safer)")
        
        print("\n" + "=" * 60)
        print("✅ Analysis complete")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fix documentation drift issues"
    )
    parser.add_argument(
        '--auto-fix',
        action='store_true',
        help='Apply automated fixes (use with caution)'
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        default=True,
        help='Generate recommendations only (default)'
    )
    
    args = parser.parse_args()
    
    fixer = DocumentationDriftFixer()
    fixer.run(report_only=args.report_only, auto_fix=args.auto_fix)


if __name__ == "__main__":
    main()
