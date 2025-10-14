#!/usr/bin/env python3
"""
Detect Code Archaeology - Find Cleanup Candidates

Identifies code that should be reviewed for cleanup:
- Debug scripts (debug_*.py, test_debug_*.py)
- Orphaned modules (no imports found)
- Old test files (potentially obsolete)
- Files with "old", "deprecated", "legacy" in name

USAGE:
    python tools/detect_code_archaeology.py
    python tools/detect_code_archaeology.py --output CODE_CLEANUP_CANDIDATES.md
"""

import ast
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import argparse


class CodeArchaeologyDetector:
    """Detects code that may need cleanup."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.src_path = self.project_root / "src"
        self.tests_path = self.project_root / "tests"
        self.tools_path = self.project_root / "tools"
        
        # Results
        self.debug_scripts: List[Tuple[Path, int, str]] = []
        self.orphaned_modules: List[Tuple[Path, str]] = []
        self.old_tests: List[Tuple[Path, int, str]] = []
        self.deprecated_files: List[Tuple[Path, str]] = []
        
        # Import graph
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        self.imported_by: Dict[str, Set[str]] = defaultdict(set)
    
    def scan_for_imports(self) -> None:
        """Build import graph by scanning all Python files."""
        print("🔍 Scanning for imports...")
        
        for py_file in self.src_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
                
                module_name = self._path_to_module_name(py_file)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported = alias.name
                            self.imports[module_name].add(imported)
                            self.imported_by[imported].add(module_name)
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imported = node.module
                            self.imports[module_name].add(imported)
                            self.imported_by[imported].add(module_name)
            
            except Exception as e:
                # Skip files with syntax errors
                pass
        
        print(f"   Found {len(self.imports)} modules with imports")
    
    def _path_to_module_name(self, path: Path) -> str:
        """Convert file path to module name."""
        rel_path = path.relative_to(self.src_path)
        module = str(rel_path).replace('/', '.').replace('\\', '.')
        if module.endswith('.py'):
            module = module[:-3]
        return module
    
    def detect_debug_scripts(self) -> None:
        """Find debug scripts in root, tools, and tests."""
        print("🐛 Detecting debug scripts...")
        
        patterns = [
            r"^debug_.*\.py$",
            r"^test_debug_.*\.py$",
        ]
        
        search_paths = [
            self.project_root,
            self.tools_path,
            self.tests_path,
        ]
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
            
            for py_file in search_path.glob("*.py"):
                for pattern in patterns:
                    if re.match(pattern, py_file.name):
                        # Get file size and last modified
                        stat = py_file.stat()
                        size_kb = stat.st_size // 1024
                        modified = datetime.fromtimestamp(stat.st_mtime)
                        
                        self.debug_scripts.append((
                            py_file.relative_to(self.project_root),
                            size_kb,
                            modified.strftime("%Y-%m-%d")
                        ))
        
        print(f"   Found {len(self.debug_scripts)} debug scripts")
    
    def detect_orphaned_modules(self) -> None:
        """Find modules that are never imported."""
        print("👻 Detecting orphaned modules...")
        
        for py_file in self.src_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            if py_file.name == "__init__.py":
                continue
            
            module_name = self._path_to_module_name(py_file)
            
            # Check if this module is imported by anyone
            # Also check variations (with/without .py, relative imports)
            is_imported = False
            
            for imported_name in self.imported_by:
                if (module_name in imported_name or 
                    imported_name in module_name or
                    py_file.stem in imported_name):
                    is_imported = True
                    break
            
            if not is_imported:
                # Get basic info
                stat = py_file.stat()
                size_kb = stat.st_size // 1024
                
                self.orphaned_modules.append((
                    py_file.relative_to(self.project_root),
                    f"{size_kb}KB"
                ))
        
        print(f"   Found {len(self.orphaned_modules)} potentially orphaned modules")
    
    def detect_old_tests(self) -> None:
        """Find test files that might be obsolete."""
        print("🧪 Detecting old test files...")
        
        patterns = [
            r"test_old_.*\.py$",
            r"test_.*_old\.py$",
            r"test_legacy_.*\.py$",
        ]
        
        if not self.tests_path.exists():
            return
        
        for py_file in self.tests_path.rglob("*.py"):
            for pattern in patterns:
                if re.match(pattern, py_file.name):
                    stat = py_file.stat()
                    size_kb = stat.st_size // 1024
                    modified = datetime.fromtimestamp(stat.st_mtime)
                    
                    self.old_tests.append((
                        py_file.relative_to(self.project_root),
                        size_kb,
                        modified.strftime("%Y-%m-%d")
                    ))
        
        print(f"   Found {len(self.old_tests)} old test files")
    
    def detect_deprecated_files(self) -> None:
        """Find files with 'deprecated', 'legacy', 'old' in path."""
        print("📦 Detecting deprecated files...")
        
        keywords = ['deprecated', 'legacy', 'old', 'backup']
        
        for py_file in self.src_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            path_str = str(py_file).lower()
            
            for keyword in keywords:
                if keyword in path_str:
                    self.deprecated_files.append((
                        py_file.relative_to(self.project_root),
                        keyword
                    ))
                    break
        
        print(f"   Found {len(self.deprecated_files)} deprecated files")
    
    def generate_report(self) -> str:
        """Generate markdown report."""
        lines = [
            "# Code Archaeology - Cleanup Candidates",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "This report identifies code that may need cleanup or archival.",
            "",
        ]
        
        # Debug Scripts
        if self.debug_scripts:
            lines.extend([
                f"## 🐛 Debug Scripts ({len(self.debug_scripts)} found)",
                "",
                "These are one-off debugging scripts that may no longer be needed:",
                "",
            ])
            
            for path, size, modified in sorted(self.debug_scripts):
                lines.append(f"- `{path}` ({size}KB, last modified {modified})")
            
            lines.extend([
                "",
                "**Recommendation**: Review and move to `/archive/debug/` or delete if no longer needed.",
                "",
            ])
        
        # Orphaned Modules
        if self.orphaned_modules:
            lines.extend([
                f"## 👻 Orphaned Modules ({len(self.orphaned_modules)} found)",
                "",
                "These modules are never imported (may be entry points or obsolete):",
                "",
            ])
            
            for path, size in sorted(self.orphaned_modules):
                lines.append(f"- `{path}` ({size})")
            
            lines.extend([
                "",
                "**Note**: Some may be legitimate entry points (CLI scripts, etc.).",
                "Review each to determine if it's needed.",
                "",
            ])
        
        # Old Test Files
        if self.old_tests:
            lines.extend([
                f"## 🧪 Old Test Files ({len(self.old_tests)} found)",
                "",
                "Test files with 'old' or 'legacy' in name:",
                "",
            ])
            
            for path, size, modified in sorted(self.old_tests):
                lines.append(f"- `{path}` ({size}KB, last modified {modified})")
            
            lines.extend([
                "",
                "**Recommendation**: Review and either update to current tests or archive.",
                "",
            ])
        
        # Deprecated Files
        if self.deprecated_files:
            lines.extend([
                f"## 📦 Deprecated Files ({len(self.deprecated_files)} found)",
                "",
                "Files with deprecated/legacy indicators in path:",
                "",
            ])
            
            for path, keyword in sorted(self.deprecated_files):
                lines.append(f"- `{path}` (contains '{keyword}')")
            
            lines.extend([
                "",
                "**Recommendation**: Move to `/archive/` directory.",
                "",
            ])
        
        # Summary
        total = (len(self.debug_scripts) + 
                len(self.orphaned_modules) + 
                len(self.old_tests) + 
                len(self.deprecated_files))
        
        lines.extend([
            "---",
            "",
            "## Summary",
            "",
            f"**Total Cleanup Candidates**: {total}",
            "",
            "### Cleanup Actions",
            "",
            "1. **Review each file** to determine if it's still needed",
            "2. **Archive useful references** to `/archive/` directory",
            "3. **Delete obsolete code** that's no longer relevant",
            "4. **Update imports** if files are moved",
            "",
            "### Archive Structure",
            "",
            "```",
            "archive/",
            "├── debug/          # One-off debugging scripts",
            "├── deprecated/     # Superseded implementations",
            "├── experiments/    # Failed experiments (keep for reference)",
            "└── tests/          # Old test files",
            "```",
            "",
            "---",
            "",
            "*Regenerate this report: `python tools/detect_code_archaeology.py`*",
            "",
        ])
        
        return '\n'.join(lines)
    
    def run(self, output_file: Optional[Path] = None) -> None:
        """Run archaeology detection."""
        print("=" * 60)
        print("CODE ARCHAEOLOGY DETECTOR")
        print("=" * 60)
        
        self.scan_for_imports()
        self.detect_debug_scripts()
        self.detect_orphaned_modules()
        self.detect_old_tests()
        self.detect_deprecated_files()
        
        report = self.generate_report()
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"\n✅ Report written to: {output_file}")
        else:
            print("\n" + report)
        
        print("\n" + "=" * 60)
        print(f"✅ Detection complete")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Detect code archaeology and cleanup candidates"
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output file (default: print to stdout)'
    )
    
    args = parser.parse_args()
    
    detector = CodeArchaeologyDetector()
    output_path = Path(args.output) if args.output else None
    detector.run(output_path)


if __name__ == "__main__":
    main()
