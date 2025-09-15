#!/usr/bin/env python3
"""
Real-time Function Lookup Tool for Development

This tool provides quick lookup of existing functions to avoid reinventing solutions.
Can be used during development to check if a function already exists before writing new code.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


class FunctionLookup:
    """Quick lookup tool for existing functions in the codebase."""

    def __init__(
        self, index_path: str = "/Users/mjh/Sync/GitHub/Arisbe/function_index.json"
    ):
        self.index_path = index_path
        self.functions = []
        self.classes = []
        self.load_index()

    def load_index(self):
        """Load the function index from JSON."""
        try:
            with open(self.index_path, "r") as f:
                data = json.load(f)
                self.functions = data.get("functions", [])
                self.classes = data.get("classes", [])
        except FileNotFoundError:
            print(f"Index not found at {self.index_path}")
            print("Run function_index_generator.py first to create the index")

    def search(self, query: str) -> List[Dict]:
        """Search for functions matching the query."""
        query_lower = query.lower()
        results = []

        for func in self.functions:
            # Check function name
            if query_lower in func["name"].lower():
                results.append(func)
                continue

            # Check purpose keywords
            if any(
                query_lower in keyword for keyword in func.get("purpose_keywords", [])
            ):
                results.append(func)
                continue

            # Check docstring
            if func.get("docstring") and query_lower in func["docstring"].lower():
                results.append(func)

        return results

    def find_polarity_solutions(self) -> List[Dict]:
        """Find all polarity-related functions."""
        return self.search("polarity")

    def find_o1_solutions(self) -> List[Dict]:
        """Find O(1) complexity solutions."""
        return [
            func
            for func in self.functions
            if "o1_complexity" in func.get("complexity_indicators", [])
        ]

    def find_hierarchy_solutions(self) -> List[Dict]:
        """Find hierarchy/nesting related functions."""
        return self.search("hierarchy nesting containment")

    def print_results(self, results: List[Dict], title: str = "Search Results"):
        """Print search results in a readable format."""
        if not results:
            print("No functions found.")
            return

        print(f"\n{title} ({len(results)} found):")
        print("=" * 50)

        for func in results:
            class_prefix = f"{func['class_name']}." if func.get("class_name") else ""
            print(f"• {class_prefix}{func['name']}")
            print(f"  📁 {func['file_path']}:{func['line_number']}")

            if func.get("docstring"):
                # Show first sentence of docstring
                first_sentence = func["docstring"].split(".")[0]
                print(f"  📝 {first_sentence}")

            if func.get("complexity_indicators"):
                indicators = ", ".join(func["complexity_indicators"])
                print(f"  ⚡ {indicators}")

            if func.get("purpose_keywords"):
                keywords = ", ".join(list(func["purpose_keywords"])[:5])  # Show first 5
                print(f"  🏷️  {keywords}")

            print()

    def quick_lookup(self, problem_description: str):
        """Quick lookup based on problem description."""
        print(f"Looking for solutions to: '{problem_description}'")

        # Try different search strategies
        direct_results = self.search(problem_description)
        if direct_results:
            self.print_results(direct_results, "Direct Matches")
            return

        # Try common problem patterns
        problem_lower = problem_description.lower()

        if any(word in problem_lower for word in ["polarity", "positive", "negative"]):
            results = self.find_polarity_solutions()
            self.print_results(results, "Polarity Solutions")

        elif any(
            word in problem_lower
            for word in ["hierarchy", "nesting", "containment", "depth"]
        ):
            results = self.find_hierarchy_solutions()
            self.print_results(results, "Hierarchy/Nesting Solutions")

        elif any(
            word in problem_lower for word in ["fast", "efficient", "o(1)", "lookup"]
        ):
            results = self.find_o1_solutions()
            self.print_results(results, "O(1) Efficient Solutions")

        else:
            # Try word-by-word search
            words = problem_description.split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    results = self.search(word)
                    if results:
                        self.print_results(results[:5], f"Results for '{word}'")
                        break


def main():
    """Command-line interface for function lookup."""
    lookup = FunctionLookup()

    if len(sys.argv) < 2:
        print("Usage: python function_lookup.py <search_query>")
        print("\nExamples:")
        print("  python function_lookup.py 'polarity calculation'")
        print("  python function_lookup.py 'hierarchy nesting'")
        print("  python function_lookup.py 'O(1) lookup'")
        print("\nSpecial commands:")
        print("  python function_lookup.py --polarity")
        print("  python function_lookup.py --o1")
        print("  python function_lookup.py --hierarchy")
        return

    query = " ".join(sys.argv[1:])

    # Handle special commands
    if query == "--polarity":
        results = lookup.find_polarity_solutions()
        lookup.print_results(results, "Polarity Functions")
    elif query == "--o1":
        results = lookup.find_o1_solutions()
        lookup.print_results(results, "O(1) Complexity Functions")
    elif query == "--hierarchy":
        results = lookup.find_hierarchy_solutions()
        lookup.print_results(results, "Hierarchy/Nesting Functions")
    else:
        lookup.quick_lookup(query)


if __name__ == "__main__":
    main()
