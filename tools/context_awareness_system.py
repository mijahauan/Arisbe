#!/usr/bin/env python3
"""
Context Awareness System - Prevent Reinvention

Scans codebase to detect existing solutions and prevent duplicate implementations.
Provides discovery hints when similar functionality already exists.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class ContextAwarenessSystem:
    """Detect existing solutions and prevent reinvention."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.src_path = self.project_root / "src"
        
        # Cache of discovered functions and classes
        self.functions_cache: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        self.classes_cache: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        
    def scan_codebase(self):
        """Scan codebase for functions and classes."""
        print("🔍 Scanning codebase for existing solutions...")
        
        for py_file in self.src_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                self._scan_file(py_file)
            except Exception as e:
                print(f"⚠️  Could not scan {py_file}: {e}")
        
        print(f"   Found {len(self.functions_cache)} unique function names")
        print(f"   Found {len(self.classes_cache)} unique class names")
    
    def _scan_file(self, filepath: Path):
        """Scan a single Python file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(filepath))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self.functions_cache[node.name].append((str(filepath), node.lineno))
                elif isinstance(node, ast.ClassDef):
                    self.classes_cache[node.name].append((str(filepath), node.lineno))
        except SyntaxError:
            pass  # Skip files with syntax errors
    
    def check_for_duplicates(self, name: str, type: str = "function") -> List[str]:
        """
        Check if a function/class name already exists.
        
        Args:
            name: Name to check
            type: "function" or "class"
            
        Returns:
            List of files where name exists
        """
        cache = self.functions_cache if type == "function" else self.classes_cache
        
        if name in cache:
            return [f"{filepath}:{lineno}" for filepath, lineno in cache[name]]
        return []
    
    def find_similar(self, name: str, type: str = "function", threshold: int = 3) -> List[str]:
        """Find similar names (fuzzy match)."""
        cache = self.functions_cache if type == "function" else self.classes_cache
        
        similar = []
        name_lower = name.lower()
        
        for existing_name in cache.keys():
            existing_lower = existing_name.lower()
            # Simple similarity: check if substantial overlap
            if (len(set(name_lower) & set(existing_lower)) >= threshold or
                name_lower in existing_lower or existing_lower in name_lower):
                similar.append(existing_name)
        
        return similar
    
    def suggest_existing_solution(self, task_description: str):
        """Suggest existing solutions based on task description."""
        print(f"\n🔍 Checking for existing solutions for: '{task_description}'")
        
        # Simple keyword matching
        keywords = task_description.lower().split()
        suggestions = []
        
        for keyword in keywords:
            if len(keyword) < 4:  # Skip short words
                continue
            
            # Check functions
            for func_name in self.functions_cache.keys():
                if keyword in func_name.lower():
                    locations = self.functions_cache[func_name]
                    suggestions.append(f"   📌 Function: {func_name} in {locations[0][0]}")
            
            # Check classes
            for class_name in self.classes_cache.keys():
                if keyword in class_name.lower():
                    locations = self.classes_cache[class_name]
                    suggestions.append(f"   📌 Class: {class_name} in {locations[0][0]}")
        
        if suggestions:
            print("   Existing solutions found:")
            for suggestion in set(suggestions[:10]):  # Limit to 10
                print(suggestion)
        else:
            print("   ℹ️  No obvious existing solutions found.")
    
    def check_api_documentation(self, name: str):
        """Check if name is documented in API reference."""
        api_ref = self.project_root / "ARISBE_CORE_API_REFERENCE.md"
        new_api_ref = self.project_root / "NEW_COMPONENTS_API_REFERENCE.md"
        
        found_in = []
        
        for doc in [api_ref, new_api_ref]:
            if doc.exists():
                content = doc.read_text()
                if name in content:
                    found_in.append(doc.name)
        
        if found_in:
            print(f"   📚 '{name}' is documented in: {', '.join(found_in)}")
            return True
        else:
            print(f"   ⚠️  '{name}' not found in API documentation")
            return False

def main():
    """Run context awareness check."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Context awareness system")
    parser.add_argument("--check", help="Check if functionality exists")
    parser.add_argument("--scan", action="store_true", help="Scan codebase")
    parser.add_argument("--suggest", help="Get suggestions for task")
    
    args = parser.parse_args()
    
    system = ContextAwarenessSystem()
    
    if args.scan or args.check or args.suggest:
        system.scan_codebase()
    
    if args.check:
        print(f"\n🔍 Checking for '{args.check}'...")
        
        # Check functions
        func_locations = system.check_for_duplicates(args.check, "function")
        if func_locations:
            print(f"   ⚠️  Function '{args.check}' already exists:")
            for loc in func_locations:
                print(f"      {loc}")
        
        # Check classes
        class_locations = system.check_for_duplicates(args.check, "class")
        if class_locations:
            print(f"   ⚠️  Class '{args.check}' already exists:")
            for loc in class_locations:
                print(f"      {loc}")
        
        # Check API docs
        system.check_api_documentation(args.check)
        
        # Find similar
        similar_funcs = system.find_similar(args.check, "function")
        if similar_funcs:
            print(f"   💡 Similar functions found: {', '.join(similar_funcs[:5])}")
    
    if args.suggest:
        system.suggest_existing_solution(args.suggest)
    
    if not (args.check or args.suggest or args.scan):
        print("Context Awareness System")
        print("Usage:")
        print("  --scan              Scan codebase")
        print("  --check NAME        Check if NAME exists")
        print("  --suggest 'task'    Suggest existing solutions")

if __name__ == "__main__":
    main()
