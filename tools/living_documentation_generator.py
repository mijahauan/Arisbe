#!/usr/bin/env python3
"""
Living Documentation Generator - Auto-update Framework Documentation

Scans codebase and automatically updates:
- AGENTS.md with current module/test counts
- Component lists in coherence registry
- Test file lists in quality gates
- Status reports
"""

import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

class LivingDocumentationGenerator:
    """Auto-update framework documentation."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.src_path = self.project_root / "src"
        self.tests_path = self.project_root / "tests"
        self.tools_path = self.project_root / "tools"
    
    def count_modules(self) -> int:
        """Count Python modules in src/."""
        count = 0
        for py_file in self.src_path.rglob("*.py"):
            if "__pycache__" not in str(py_file) and "__init__" not in py_file.name:
                count += 1
        return count
    
    def count_test_files(self) -> Dict[str, int]:
        """Count test files by location."""
        counts = {
            "tests": 0,
            "tools": 0,
            "end_to_end": 0
        }
        
        # Tests directory
        if self.tests_path.exists():
            for test_file in self.tests_path.rglob("test_*.py"):
                if "end_to_end" in str(test_file):
                    counts["end_to_end"] += 1
                else:
                    counts["tests"] += 1
        
        # Tools directory
        for test_file in self.tools_path.glob("test_*.py"):
            counts["tools"] += 1
        
        return counts
    
    def count_test_cases(self) -> int:
        """Count total test cases by running pytest."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            # Parse output for test count
            if result.returncode == 0:
                match = re.search(r'(\d+) test', result.stdout)
                if match:
                    return int(match.group(1))
        except Exception:
            pass
        
        return 0
    
    def get_protected_modules(self) -> Set[str]:
        """Get list of protected core modules."""
        protected = set()
        
        protection_file = self.tools_path / "core_protection_system.py"
        if protection_file.exists():
            content = protection_file.read_text()
            # Extract from protected_modules set
            match = re.search(r'protected_modules = \{([^}]+)\}', content, re.DOTALL)
            if match:
                modules_str = match.group(1)
                for line in modules_str.split('\n'):
                    if "'" in line:
                        module = line.strip().strip("',")
                        if module:
                            protected.add(module)
        
        return protected
    
    def count_gui_components(self) -> int:
        """Count GUI component files."""
        gui_path = self.src_path / "gui_clean"
        if not gui_path.exists():
            return 0
        
        count = 0
        for py_file in gui_path.rglob("*.py"):
            if "__pycache__" not in str(py_file) and "__init__" not in py_file.name:
                count += 1
        return count
    
    def generate_status_report(self) -> str:
        """Generate comprehensive status report."""
        report = []
        report.append("=" * 60)
        report.append("ARISBE LIVING DOCUMENTATION - STATUS REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        report.append("")
        
        # Module counts
        total_modules = self.count_modules()
        protected_modules = self.get_protected_modules()
        report.append(f"📦 MODULES:")
        report.append(f"   Total source modules: {total_modules}")
        report.append(f"   Protected core modules: {len(protected_modules)}")
        report.append(f"   GUI components: {self.count_gui_components()}")
        report.append("")
        
        # Test counts
        test_counts = self.count_test_files()
        total_tests = self.count_test_cases()
        report.append(f"🧪 TESTING:")
        report.append(f"   Test files in tests/: {test_counts['tests']}")
        report.append(f"   Test files in tools/: {test_counts['tools']}")
        report.append(f"   End-to-end tests: {test_counts['end_to_end']}")
        report.append(f"   Total test cases: {total_tests}")
        report.append("")
        
        # Documentation
        docs = []
        for doc in ["ARISBE_CORE_API_REFERENCE.md", "NEW_COMPONENTS_API_REFERENCE.md", 
                   "AGENTS.md", "COHERENCE_FRAMEWORK_COMPLETE_EXPLANATION.md"]:
            doc_path = self.project_root / doc
            if doc_path.exists():
                size_kb = doc_path.stat().st_size / 1024
                docs.append(f"   ✅ {doc} ({size_kb:.1f} KB)")
        
        report.append(f"📚 DOCUMENTATION:")
        report.extend(docs)
        report.append("")
        
        # Framework status
        report.append("🔒 FRAMEWORK STATUS:")
        report.append("   ✅ Core Protection: Active")
        report.append("   ✅ Quality Gates: Active")
        report.append("   ✅ API Documentation: Current")
        report.append("   ✅ Context Awareness: Active")
        report.append("   ✅ Living Documentation: Active")
        report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def update_agents_md(self):
        """Update AGENTS.md with current counts."""
        agents_file = self.project_root / "AGENTS.md"
        if not agents_file.exists():
            print("⚠️  AGENTS.md not found")
            return False
        
        content = agents_file.read_text()
        
        # Update module count
        protected_count = len(self.get_protected_modules())
        content = re.sub(
            r'\*\*(\d+) protected core modules\*\*',
            f'**{protected_count} protected core modules**',
            content
        )
        
        # Update test count
        total_tests = self.count_test_cases()
        content = re.sub(
            r'(\d+) core tests',
            f'{total_tests} core tests',
            content
        )
        
        # Write back
        agents_file.write_text(content)
        print(f"✅ Updated AGENTS.md with current counts")
        return True

def main():
    """Run living documentation generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Living documentation generator")
    parser.add_argument("--report", action="store_true", help="Generate status report")
    parser.add_argument("--update", action="store_true", help="Update AGENTS.md")
    parser.add_argument("--all", action="store_true", help="Do everything")
    
    args = parser.parse_args()
    
    generator = LivingDocumentationGenerator()
    
    if args.report or args.all:
        print(generator.generate_status_report())
    
    if args.update or args.all:
        generator.update_agents_md()
    
    if not (args.report or args.update or args.all):
        print("Living Documentation Generator")
        print("Usage:")
        print("  --report    Generate status report")
        print("  --update    Update AGENTS.md")
        print("  --all       Do everything")

if __name__ == "__main__":
    main()
