#!/usr/bin/env python3
"""
Automated Function Index Generator for Arisbe Codebase

Scans the codebase to build a searchable index of functions, classes, and their purposes.
This helps avoid reinventing solutions that already exist in the codebase.
"""

import ast
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class FunctionInfo:
    """Information about a function or method."""

    name: str
    file_path: str
    line_number: int
    class_name: Optional[str]
    docstring: Optional[str]
    parameters: List[str]
    return_annotation: Optional[str]
    purpose_keywords: Set[str]
    complexity_indicators: List[str]


@dataclass
class ClassInfo:
    """Information about a class."""

    name: str
    file_path: str
    line_number: int
    docstring: Optional[str]
    methods: List[str]
    purpose_keywords: Set[str]
    inheritance: List[str]


class CodeIndexer(ast.NodeVisitor):
    """AST visitor to extract function and class information."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.current_class = None

    def visit_ClassDef(self, node):
        """Visit class definition."""
        docstring = ast.get_docstring(node)
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        inheritance = [
            base.id if isinstance(base, ast.Name) else str(base) for base in node.bases
        ]

        purpose_keywords = self._extract_purpose_keywords(node.name, docstring)

        class_info = ClassInfo(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            docstring=docstring,
            methods=methods,
            purpose_keywords=purpose_keywords,
            inheritance=inheritance,
        )

        self.classes.append(class_info)
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        """Visit function definition."""
        docstring = ast.get_docstring(node)
        parameters = [arg.arg for arg in node.args.args]
        return_annotation = None

        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_annotation = node.returns.id
            else:
                return_annotation = ast.unparse(node.returns)

        purpose_keywords = self._extract_purpose_keywords(node.name, docstring)
        complexity_indicators = self._analyze_complexity(node)

        function_info = FunctionInfo(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            class_name=self.current_class,
            docstring=docstring,
            parameters=parameters,
            return_annotation=return_annotation,
            purpose_keywords=purpose_keywords,
            complexity_indicators=complexity_indicators,
        )

        self.functions.append(function_info)
        self.generic_visit(node)

    def _extract_purpose_keywords(
        self, name: str, docstring: Optional[str]
    ) -> Set[str]:
        """Extract keywords that indicate the function's purpose."""
        keywords = set()

        # Extract from function name
        name_parts = re.findall(r"[A-Z][a-z]*|[a-z]+", name)
        keywords.update(word.lower() for word in name_parts)

        # Extract from docstring
        if docstring:
            # Common purpose indicators
            purpose_patterns = [
                r"calculate\w*\s+(\w+)",
                r"compute\w*\s+(\w+)",
                r"find\w*\s+(\w+)",
                r"get\w*\s+(\w+)",
                r"build\w*\s+(\w+)",
                r"create\w*\s+(\w+)",
                r"generate\w*\s+(\w+)",
                r"transform\w*\s+(\w+)",
                r"validate\w*\s+(\w+)",
                r"check\w*\s+(\w+)",
            ]

            for pattern in purpose_patterns:
                matches = re.findall(pattern, docstring.lower())
                keywords.update(matches)

            # Domain-specific keywords
            domain_keywords = [
                "polarity",
                "nesting",
                "hierarchy",
                "containment",
                "area",
                "cut",
                "vertex",
                "edge",
                "transformation",
                "rule",
                "egi",
                "spatial",
                "index",
                "tree",
                "graph",
                "logic",
                "semantic",
            ]

            for keyword in domain_keywords:
                if keyword in docstring.lower():
                    keywords.add(keyword)

        return keywords

    def _analyze_complexity(self, node: ast.FunctionDef) -> List[str]:
        """Analyze function complexity indicators."""
        indicators = []

        # Count nested loops
        loop_count = sum(
            1 for n in ast.walk(node) if isinstance(n, (ast.For, ast.While))
        )
        if loop_count > 1:
            indicators.append(f"nested_loops_{loop_count}")

        # Count recursive calls
        recursive_calls = sum(
            1
            for n in ast.walk(node)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == node.name
        )
        if recursive_calls > 0:
            indicators.append("recursive")

        # Check for O(1) indicators
        if any(
            keyword in (node.name + (ast.get_docstring(node) or "")).lower()
            for keyword in ["o(1)", "constant", "lookup", "index", "hash"]
        ):
            indicators.append("o1_complexity")

        return indicators


class FunctionIndexGenerator:
    """Generates and maintains a searchable index of code functions."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []

    def scan_codebase(self, extensions: List[str] = [".py"]) -> None:
        """Scan the codebase and build the index."""
        for ext in extensions:
            for file_path in self.root_path.rglob(f"*{ext}"):
                if self._should_skip_file(file_path):
                    continue

                try:
                    self._index_file(file_path)
                except Exception as e:
                    print(f"Error indexing {file_path}: {e}")

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            "__pycache__",
            ".git",
            "test_",
            "debug_",
            ".backup",
            "legacy",  # Skip legacy code for now
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _index_file(self, file_path: Path) -> None:
        """Index a single Python file."""
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())
                indexer = CodeIndexer(str(file_path))
                indexer.visit(tree)

                self.functions.extend(indexer.functions)
                self.classes.extend(indexer.classes)
            except SyntaxError:
                print(f"Syntax error in {file_path}, skipping")

    def search_functions(self, query: str) -> List[FunctionInfo]:
        """Search for functions by purpose keywords."""
        query_words = set(query.lower().split())
        results = []

        for func in self.functions:
            # Check name match
            if query.lower() in func.name.lower():
                results.append(func)
                continue

            # Check keyword match
            if query_words & func.purpose_keywords:
                results.append(func)
                continue

            # Check docstring match
            if func.docstring and query.lower() in func.docstring.lower():
                results.append(func)

        return results

    def find_o1_solutions(self) -> List[FunctionInfo]:
        """Find functions that provide O(1) complexity solutions."""
        return [
            func
            for func in self.functions
            if "o1_complexity" in func.complexity_indicators
        ]

    def find_polarity_functions(self) -> List[FunctionInfo]:
        """Find functions related to polarity calculation."""
        return self.search_functions("polarity")

    def find_hierarchy_functions(self) -> List[FunctionInfo]:
        """Find functions related to hierarchical operations."""
        return self.search_functions("hierarchy nesting containment")

    def export_index(self, output_path: str) -> None:
        """Export the index to JSON for persistence."""
        index_data = {
            "functions": [asdict(func) for func in self.functions],
            "classes": [asdict(cls) for cls in self.classes],
            "metadata": {
                "total_functions": len(self.functions),
                "total_classes": len(self.classes),
                "root_path": str(self.root_path),
            },
        }

        # Convert sets to lists for JSON serialization
        for func_data in index_data["functions"]:
            func_data["purpose_keywords"] = list(func_data["purpose_keywords"])

        for class_data in index_data["classes"]:
            class_data["purpose_keywords"] = list(class_data["purpose_keywords"])

        with open(output_path, "w") as f:
            json.dump(index_data, f, indent=2)

    def generate_report(self) -> str:
        """Generate a human-readable report of the index."""
        report = []
        report.append("# Arisbe Function Index Report\n")

        # O(1) Solutions
        o1_funcs = self.find_o1_solutions()
        if o1_funcs:
            report.append("## O(1) Complexity Solutions")
            for func in o1_funcs:
                report.append(
                    f"- **{func.name}** ({func.file_path}:{func.line_number})"
                )
                if func.docstring:
                    report.append(f"  {func.docstring.split('.')[0]}")
            report.append("")

        # Polarity Functions
        polarity_funcs = self.find_polarity_functions()
        if polarity_funcs:
            report.append("## Polarity Calculation Functions")
            for func in polarity_funcs:
                report.append(
                    f"- **{func.name}** ({func.file_path}:{func.line_number})"
                )
                if func.docstring:
                    report.append(f"  {func.docstring.split('.')[0]}")
            report.append("")

        # Hierarchy Functions
        hierarchy_funcs = self.find_hierarchy_functions()
        if hierarchy_funcs:
            report.append("## Hierarchical/Nesting Functions")
            for func in hierarchy_funcs:
                report.append(
                    f"- **{func.name}** ({func.file_path}:{func.line_number})"
                )
                if func.docstring:
                    report.append(f"  {func.docstring.split('.')[0]}")
            report.append("")

        return "\n".join(report)


def main():
    """Generate function index for Arisbe codebase."""
    generator = FunctionIndexGenerator("/Users/mjh/Sync/GitHub/Arisbe/src")

    print("Scanning codebase...")
    generator.scan_codebase()

    print(
        f"Found {len(generator.functions)} functions and {len(generator.classes)} classes"
    )

    # Export index
    generator.export_index("/Users/mjh/Sync/GitHub/Arisbe/function_index.json")

    # Generate report
    report = generator.generate_report()
    with open("/Users/mjh/Sync/GitHub/Arisbe/FUNCTION_INDEX_REPORT.md", "w") as f:
        f.write(report)

    print("Function index generated:")
    print("- function_index.json (machine-readable)")
    print("- FUNCTION_INDEX_REPORT.md (human-readable)")

    # Show polarity functions as example
    polarity_funcs = generator.find_polarity_functions()
    if polarity_funcs:
        print(f"\nFound {len(polarity_funcs)} polarity-related functions:")
        for func in polarity_funcs[:5]:  # Show first 5
            print(f"  {func.name} - {func.file_path}:{func.line_number}")


if __name__ == "__main__":
    main()
