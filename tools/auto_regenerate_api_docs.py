#!/usr/bin/env python3
"""
Auto-Regenerate API Documentation

Detects changes to core modules and automatically regenerates API documentation.
Prevents documentation lag by keeping API docs synchronized with code.

USAGE:
    python tools/auto_regenerate_api_docs.py
    python tools/auto_regenerate_api_docs.py --check-only
    
Called by git pre-commit hook when core modules change.
"""

import ast
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
import argparse


class APIDocGenerator:
    """Automatically regenerates API documentation when modules change."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.src_path = self.project_root / "src"
        self.state_file = self.project_root / ".coherence_session_state.json"
        
        # Load protected modules from session state
        self.protected_modules = self._load_protected_modules()
        
        # API doc output file
        self.api_doc_file = self.project_root / "ARISBE_CORE_API_REFERENCE.md"
        
    def _load_protected_modules(self) -> Set[str]:
        """Load list of protected core modules from session state."""
        if not self.state_file.exists():
            return set()
        
        with open(self.state_file, 'r') as f:
            state = json.load(f)
        
        protected = set()
        components = state.get("active_components", {})
        tier1 = components.get("production_tier1", {}).get("modules", [])
        
        for module_desc in tier1:
            if "PROTECTED" in module_desc or ".py" in module_desc:
                # Extract filename from "src/filename.py - Description (PROTECTED)"
                parts = module_desc.split()
                if parts:
                    filename = parts[0].split('/')[-1]
                    if filename.endswith('.py'):
                        protected.add(filename)
        
        return protected
    
    def get_modified_core_modules(self) -> List[str]:
        """Get list of modified core modules in current commit."""
        try:
            # Get staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                return []
            
            modified_files = result.stdout.strip().split('\n')
            
            # Filter for protected core modules
            core_modified = []
            for file_path in modified_files:
                if file_path.startswith('src/') and file_path.endswith('.py'):
                    filename = Path(file_path).name
                    if filename in self.protected_modules:
                        core_modified.append(file_path)
            
            return core_modified
            
        except Exception as e:
            print(f"⚠️  Could not check modified files: {e}")
            return []
    
    def extract_api_from_module(self, module_path: Path) -> Dict[str, Any]:
        """Extract API information from a Python module."""
        if not module_path.exists():
            return {}
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(module_path))
            
            api_info = {
                "module": module_path.stem,
                "path": str(module_path.relative_to(self.project_root)),
                "classes": [],
                "functions": [],
                "docstring": ast.get_docstring(tree) or ""
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "docstring": ast.get_docstring(node) or "",
                        "methods": []
                    }
                    
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                "name": item.name,
                                "args": [arg.arg for arg in item.args.args],
                                "docstring": ast.get_docstring(item) or ""
                            }
                            class_info["methods"].append(method_info)
                    
                    api_info["classes"].append(class_info)
                
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    # Top-level functions only
                    func_info = {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node) or ""
                    }
                    api_info["functions"].append(func_info)
            
            return api_info
            
        except Exception as e:
            print(f"⚠️  Could not parse {module_path}: {e}")
            return {}
    
    def generate_api_documentation(self, modules_to_document: List[Path]) -> str:
        """Generate markdown API documentation."""
        lines = [
            "# Arisbe Core API Reference",
            "",
            f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            "**Auto-Generated**: This file is automatically regenerated when core modules change",
            "",
            "---",
            "",
            "## Overview",
            "",
            "This document provides complete API documentation for Arisbe's protected core modules.",
            "These modules form the mathematical foundation validated by 90 core tests.",
            "",
            "**Protected Modules**: Changes require explicit authorization (`export ARISBE_CORE_OVERRIDE=true`)",
            "",
            "---",
            "",
        ]
        
        # Generate documentation for each module
        for module_path in sorted(modules_to_document):
            api_info = self.extract_api_from_module(module_path)
            
            if not api_info:
                continue
            
            lines.extend([
                f"## {api_info['module']}.py",
                "",
                f"**Path**: `{api_info['path']}`  ",
                f"**Status**: Protected Core Module",
                "",
            ])
            
            if api_info['docstring']:
                lines.extend([
                    "### Module Description",
                    "",
                    api_info['docstring'],
                    "",
                ])
            
            # Document classes
            if api_info['classes']:
                lines.extend([
                    "### Classes",
                    "",
                ])
                
                for cls in api_info['classes']:
                    lines.extend([
                        f"#### `{cls['name']}`",
                        "",
                    ])
                    
                    if cls['docstring']:
                        lines.extend([
                            cls['docstring'],
                            "",
                        ])
                    
                    if cls['methods']:
                        lines.append("**Methods**:")
                        lines.append("")
                        
                        for method in cls['methods']:
                            args_str = ', '.join(method['args'])
                            lines.append(f"- `{method['name']}({args_str})`")
                            
                            if method['docstring']:
                                # Indent docstring
                                doc_lines = method['docstring'].split('\n')
                                for doc_line in doc_lines:
                                    lines.append(f"  {doc_line}")
                            
                            lines.append("")
                    
                    lines.append("")
            
            # Document functions
            if api_info['functions']:
                lines.extend([
                    "### Functions",
                    "",
                ])
                
                for func in api_info['functions']:
                    args_str = ', '.join(func['args'])
                    lines.extend([
                        f"#### `{func['name']}({args_str})`",
                        "",
                    ])
                    
                    if func['docstring']:
                        lines.extend([
                            func['docstring'],
                            "",
                        ])
                    
                    lines.append("")
            
            lines.extend([
                "---",
                "",
            ])
        
        # Footer
        lines.extend([
            "## Usage Notes",
            "",
            "### Import Patterns",
            "```python",
            "# Recommended import style",
            "from module_name import function_name",
            "from module_name import ClassName",
            "",
            "# Not: from src.module_name import ...",
            "```",
            "",
            "### Immutability",
            "EGI model is immutable. Use `.with_*()` methods:",
            "```python",
            "# Correct",
            "new_egi = egi.with_vertex(vertex)",
            "",
            "# Incorrect",
            "egi.add_vertex(vertex)  # No such method",
            "```",
            "",
            "### Error Handling",
            "Always check return values and handle None cases:",
            "```python",
            "result = transform_egi(egi, rule)",
            "if result is None:",
            "    # Handle transformation failure",
            "    pass",
            "```",
            "",
            "---",
            "",
            "*For usage examples, see `CORE_API_USAGE_GUIDE.md`*",
            "",
        ])
        
        return '\n'.join(lines)
    
    def regenerate_api_docs(self, force: bool = False) -> bool:
        """Regenerate API documentation if needed."""
        # Check if core modules were modified
        if not force:
            modified = self.get_modified_core_modules()
            
            if not modified:
                print("ℹ️  No core modules modified - API docs unchanged")
                return True
            
            print(f"📝 Core modules modified: {len(modified)}")
            for mod in modified:
                print(f"   - {mod}")
        
        print("📚 Regenerating API documentation...")
        
        # Get all protected module paths
        protected_paths = []
        for protected_file in self.protected_modules:
            module_path = self.src_path / protected_file
            if module_path.exists():
                protected_paths.append(module_path)
        
        if not protected_paths:
            print("⚠️  No protected modules found")
            return False
        
        # Generate documentation
        api_docs = self.generate_api_documentation(protected_paths)
        
        # Write to file
        with open(self.api_doc_file, 'w') as f:
            f.write(api_docs)
        
        print(f"✅ API documentation regenerated: {self.api_doc_file}")
        print(f"   Documented {len(protected_paths)} protected modules")
        
        return True
    
    def check_only(self) -> bool:
        """Check if API docs need regeneration without regenerating."""
        modified = self.get_modified_core_modules()
        
        if modified:
            print(f"⚠️  {len(modified)} core module(s) modified:")
            for mod in modified:
                print(f"   - {mod}")
            print("   API docs should be regenerated")
            return False
        else:
            print("✅ No core modules modified")
            return True
    
    def run(self, check_only: bool = False, force: bool = False) -> bool:
        """Run API doc regeneration."""
        if check_only:
            return self.check_only()
        else:
            return self.regenerate_api_docs(force=force)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Auto-regenerate API documentation when core modules change"
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Check if regeneration needed without regenerating'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regeneration even if no changes detected'
    )
    
    args = parser.parse_args()
    
    generator = APIDocGenerator()
    success = generator.run(check_only=args.check_only, force=args.force)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
