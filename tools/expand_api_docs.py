#!/usr/bin/env python3
"""
Expand API Documentation - Generate docs for Tier 2 (stable) modules

Extends API documentation beyond protected core to include stable modules.
Generates ARISBE_STABLE_API_REFERENCE.md covering Tier 2 components.

USAGE:
    python tools/expand_api_docs.py
    python tools/expand_api_docs.py --tier 2
    python tools/expand_api_docs.py --all-tiers
"""

import ast
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
import argparse


class APIDocExpander:
    """Expands API documentation to stable modules."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.src_path = self.project_root / "src"
        self.state_file = self.project_root / ".coherence_session_state.json"
        
        # Load tier information
        self.tier_modules = self._load_tier_modules()
        
    def _load_tier_modules(self) -> Dict[str, List[str]]:
        """Load module tier assignments from session state."""
        if not self.state_file.exists():
            return {}
        
        with open(self.state_file, 'r') as f:
            state = json.load(f)
        
        components = state.get("active_components", {})
        
        tiers = {}
        for tier_key, tier_data in components.items():
            if isinstance(tier_data, dict) and "modules" in tier_data:
                tier_name = tier_key.split('_')[0]  # Extract "production", "stable", etc.
                modules = []
                
                for module_desc in tier_data["modules"]:
                    # Extract filename from description
                    if ".py" in module_desc or "/" in module_desc:
                        parts = module_desc.split()
                        if parts:
                            path = parts[0]
                            if path.startswith("src/"):
                                modules.append(path)
                            else:
                                modules.append(f"src/{path}")
                
                tiers[tier_name] = modules
        
        return tiers
    
    def get_stable_modules(self) -> List[Path]:
        """Get list of Tier 2 (stable) module paths."""
        stable_paths = []
        
        # Get from tier assignments
        tier2_modules = self.tier_modules.get("stable", [])
        
        for module_ref in tier2_modules:
            if module_ref.startswith("src/"):
                module_path = self.project_root / module_ref
                if module_path.exists():
                    stable_paths.append(module_path)
        
        # If tier info incomplete, scan for stable modules by convention
        if not stable_paths:
            # GUI modules are typically stable
            gui_dirs = [
                self.src_path / "gui_clean" / "organon",
                self.src_path / "gui_clean" / "ergasterion",
                self.src_path / "gui_clean" / "common",
            ]
            
            for gui_dir in gui_dirs:
                if gui_dir.exists():
                    stable_paths.extend(gui_dir.glob("*.py"))
            
            # Parser/generator modules
            parser_patterns = [
                "*_parser_dau.py",
                "*_generator_dau.py",
            ]
            
            for pattern in parser_patterns:
                stable_paths.extend(self.src_path.glob(pattern))
        
        return sorted(set(stable_paths))
    
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
    
    def generate_stable_api_docs(self) -> str:
        """Generate markdown API documentation for stable modules."""
        stable_modules = self.get_stable_modules()
        
        lines = [
            "# Arisbe Stable API Reference",
            "",
            f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            "**Auto-Generated**: This file is automatically generated from Tier 2 (stable) modules",
            "",
            "---",
            "",
            "## Overview",
            "",
            "This document provides API documentation for Arisbe's stable (Tier 2) modules.",
            "These modules are production-ready but not part of the protected core.",
            "",
            f"**Documented Modules**: {len(stable_modules)}",
            "",
            "### Module Categories",
            "",
            "- **GUI Components**: Organon and Ergasterion mode implementations",
            "- **Linear Format Translation**: EGIF, CGIF, CLIF parsers and generators",
            "- **Style System**: Diagram styling and configuration",
            "- **Rendering**: SVG and Qt rendering components",
            "",
            "---",
            "",
        ]
        
        # Group modules by category
        gui_modules = [m for m in stable_modules if "gui" in str(m)]
        parser_modules = [m for m in stable_modules if "parser" in m.stem or "generator" in m.stem]
        other_modules = [m for m in stable_modules if m not in gui_modules and m not in parser_modules]
        
        # Document GUI modules
        if gui_modules:
            lines.extend([
                "## GUI Components",
                "",
            ])
            
            for module_path in sorted(gui_modules):
                api_info = self.extract_api_from_module(module_path)
                if api_info:
                    lines.extend(self._format_module_docs(api_info))
        
        # Document parser/generator modules
        if parser_modules:
            lines.extend([
                "## Linear Format Translation",
                "",
            ])
            
            for module_path in sorted(parser_modules):
                api_info = self.extract_api_from_module(module_path)
                if api_info:
                    lines.extend(self._format_module_docs(api_info))
        
        # Document other modules
        if other_modules:
            lines.extend([
                "## Other Stable Modules",
                "",
            ])
            
            for module_path in sorted(other_modules):
                api_info = self.extract_api_from_module(module_path)
                if api_info:
                    lines.extend(self._format_module_docs(api_info))
        
        # Footer
        lines.extend([
            "---",
            "",
            "## Usage Notes",
            "",
            "### Import Patterns",
            "```python",
            "# GUI components",
            "from gui_clean.organon.organon_mode import OrganonMode",
            "",
            "# Parsers/generators",
            "from egif_parser_dau import parse_egif",
            "from cgif_generator_dau import generate_cgif",
            "```",
            "",
            "### Stability",
            "Tier 2 modules are stable and safe to use. However, unlike protected core modules,",
            "they may undergo interface changes with appropriate deprecation warnings.",
            "",
            "---",
            "",
            "*For core API documentation, see `ARISBE_CORE_API_REFERENCE.md`*",
            "",
        ])
        
        return '\n'.join(lines)
    
    def _format_module_docs(self, api_info: Dict) -> List[str]:
        """Format API info as markdown."""
        lines = [
            f"### {api_info['module']}.py",
            "",
            f"**Path**: `{api_info['path']}`",
            "",
        ]
        
        if api_info['docstring']:
            lines.extend([
                api_info['docstring'],
                "",
            ])
        
        # Document classes
        if api_info['classes']:
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
                    
                    for method in cls['methods'][:5]:  # Limit to first 5 methods
                        args_str = ', '.join(method['args'])
                        lines.append(f"- `{method['name']}({args_str})`")
                    
                    if len(cls['methods']) > 5:
                        lines.append(f"- *... and {len(cls['methods']) - 5} more methods*")
                    
                    lines.append("")
        
        # Document functions
        if api_info['functions']:
            for func in api_info['functions'][:3]:  # Limit to first 3 functions
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
            
            if len(api_info['functions']) > 3:
                lines.append(f"*... and {len(api_info['functions']) - 3} more functions*")
                lines.append("")
        
        lines.append("")
        return lines
    
    def run(self) -> bool:
        """Run API documentation expansion."""
        print("=" * 60)
        print("API DOCUMENTATION EXPANDER")
        print("=" * 60)
        
        print("\n🔍 Finding Tier 2 (stable) modules...")
        stable_modules = self.get_stable_modules()
        
        print(f"   Found {len(stable_modules)} stable modules")
        
        print("\n📚 Generating expanded API documentation...")
        stable_docs = self.generate_stable_api_docs()
        
        # Write stable API docs
        output_file = self.project_root / "ARISBE_STABLE_API_REFERENCE.md"
        with open(output_file, 'w') as f:
            f.write(stable_docs)
        
        print(f"\n✅ Stable API docs generated: {output_file}")
        print(f"   Documented {len(stable_modules)} modules")
        
        print("\n" + "=" * 60)
        print("✅ Expansion complete")
        print("=" * 60)
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Expand API documentation to stable modules"
    )
    parser.add_argument(
        '--tier',
        type=int,
        default=2,
        help='Tier to document (default: 2 for stable)'
    )
    parser.add_argument(
        '--all-tiers',
        action='store_true',
        help='Document all non-core tiers'
    )
    
    args = parser.parse_args()
    
    expander = APIDocExpander()
    success = expander.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
