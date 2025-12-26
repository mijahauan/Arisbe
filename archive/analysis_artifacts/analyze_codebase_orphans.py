#!/usr/bin/env python3
"""
Codebase Orphan Analysis Tool

Analyzes the Arisbe codebase to identify:
- Orphaned functions (defined but never called)
- Unreferenced classes
- Unused imports
- Dead code
- Duplicate functionality
"""

import ast
import os
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze Python code structure."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.functions_defined = set()
        self.classes_defined = set()
        self.functions_called = set()
        self.classes_used = set()
        self.imports = set()
        self.from_imports = defaultdict(set)
        
    def visit_FunctionDef(self, node):
        """Record function definitions."""
        self.functions_defined.add(node.name)
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        """Record async function definitions."""
        self.functions_defined.add(node.name)
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        """Record class definitions."""
        self.classes_defined.add(node.name)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Record function calls."""
        if isinstance(node.func, ast.Name):
            self.functions_called.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.functions_called.add(node.func.attr)
            if isinstance(node.func.value, ast.Name):
                self.classes_used.add(node.func.value.id)
        self.generic_visit(node)
        
    def visit_Name(self, node):
        """Record name usage (for classes used as types, etc.)."""
        if isinstance(node.ctx, ast.Load):
            self.classes_used.add(node.id)
        self.generic_visit(node)
        
    def visit_Import(self, node):
        """Record imports."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Record from imports."""
        module = node.module or ""
        for alias in node.names:
            self.from_imports[module].add(alias.name)
        self.generic_visit(node)

def analyze_file(filepath: Path) -> CodeAnalyzer:
    """Analyze a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        analyzer = CodeAnalyzer(str(filepath))
        analyzer.visit(tree)
        return analyzer
        
    except Exception as e:
        logger.warning(f"Could not analyze {filepath}: {e}")
        return None

def find_python_files(src_dir: Path) -> List[Path]:
    """Find all Python files in the source directory."""
    python_files = []
    
    for root, dirs, files in os.walk(src_dir):
        # Skip certain directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py') and not file.startswith('.'):
                python_files.append(Path(root) / file)
    
    return python_files

def analyze_codebase(src_dir: Path) -> Dict:
    """Analyze the entire codebase."""
    logger.info(f"Analyzing codebase in {src_dir}")
    
    python_files = find_python_files(src_dir)
    logger.info(f"Found {len(python_files)} Python files")
    
    # Analyze all files
    analyzers = {}
    all_functions_defined = set()
    all_classes_defined = set()
    all_functions_called = set()
    all_classes_used = set()
    all_imports = Counter()
    all_from_imports = defaultdict(Counter)
    
    for filepath in python_files:
        analyzer = analyze_file(filepath)
        if analyzer:
            analyzers[str(filepath)] = analyzer
            all_functions_defined.update(analyzer.functions_defined)
            all_classes_defined.update(analyzer.classes_defined)
            all_functions_called.update(analyzer.functions_called)
            all_classes_used.update(analyzer.classes_used)
            
            for imp in analyzer.imports:
                all_imports[imp] += 1
            
            for module, names in analyzer.from_imports.items():
                for name in names:
                    all_from_imports[module][name] += 1
    
    # Find orphans
    orphaned_functions = all_functions_defined - all_functions_called
    orphaned_classes = all_classes_defined - all_classes_used
    
    # Remove common patterns that aren't actually orphans
    common_patterns = {
        'main', '__init__', '__str__', '__repr__', '__eq__', '__hash__',
        'setUp', 'tearDown', 'test_', 'run', 'execute', 'handle',
        'get', 'set', 'create', 'update', 'delete', 'validate'
    }
    
    # Filter out test functions and common patterns
    orphaned_functions = {f for f in orphaned_functions 
                         if not any(pattern in f for pattern in common_patterns)}
    
    return {
        'analyzers': analyzers,
        'total_files': len(python_files),
        'functions_defined': len(all_functions_defined),
        'classes_defined': len(all_classes_defined),
        'functions_called': len(all_functions_called),
        'classes_used': len(all_classes_used),
        'orphaned_functions': orphaned_functions,
        'orphaned_classes': orphaned_classes,
        'imports': all_imports,
        'from_imports': all_from_imports
    }

def identify_legacy_components(src_dir: Path) -> List[str]:
    """Identify components that appear to be legacy."""
    legacy_indicators = [
        'legacy/', 'old_', 'deprecated_', 'unused_', 'backup_',
        'test_minimal', 'demo_', 'example_', 'prototype_'
    ]
    
    legacy_files = []
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = str(Path(root) / file)
                if any(indicator in filepath.lower() for indicator in legacy_indicators):
                    legacy_files.append(filepath)
    
    return legacy_files

def find_duplicate_functionality(analyzers: Dict) -> List[Tuple[str, str, str]]:
    """Find potential duplicate functionality."""
    function_locations = defaultdict(list)
    
    for filepath, analyzer in analyzers.items():
        for func in analyzer.functions_defined:
            function_locations[func].append(filepath)
    
    # Find functions defined in multiple files (potential duplicates)
    duplicates = []
    for func_name, locations in function_locations.items():
        if len(locations) > 1:
            # Filter out common names like __init__, main, etc.
            if func_name not in {'__init__', 'main', 'run', 'test', 'setup'}:
                duplicates.append((func_name, len(locations), locations))
    
    return duplicates

def generate_report(analysis: Dict, src_dir: Path):
    """Generate comprehensive analysis report."""
    logger.info("\n" + "="*80)
    logger.info("ARISBE CODEBASE ORPHAN ANALYSIS REPORT")
    logger.info("="*80)
    
    # Overview
    logger.info(f"\n📊 OVERVIEW:")
    logger.info(f"  Total Python files analyzed: {analysis['total_files']}")
    logger.info(f"  Functions defined: {analysis['functions_defined']}")
    logger.info(f"  Classes defined: {analysis['classes_defined']}")
    logger.info(f"  Functions called: {analysis['functions_called']}")
    logger.info(f"  Classes used: {analysis['classes_used']}")
    
    # Orphaned functions
    logger.info(f"\n🔍 ORPHANED FUNCTIONS ({len(analysis['orphaned_functions'])}):")
    if analysis['orphaned_functions']:
        for func in sorted(analysis['orphaned_functions'])[:20]:  # Show top 20
            # Find where it's defined
            for filepath, analyzer in analysis['analyzers'].items():
                if func in analyzer.functions_defined:
                    rel_path = Path(filepath).relative_to(src_dir)
                    logger.info(f"  • {func} in {rel_path}")
                    break
        if len(analysis['orphaned_functions']) > 20:
            logger.info(f"  ... and {len(analysis['orphaned_functions']) - 20} more")
    else:
        logger.info("  ✅ No orphaned functions found!")
    
    # Orphaned classes
    logger.info(f"\n🏗️  ORPHANED CLASSES ({len(analysis['orphaned_classes'])}):")
    if analysis['orphaned_classes']:
        for cls in sorted(analysis['orphaned_classes'])[:15]:  # Show top 15
            # Find where it's defined
            for filepath, analyzer in analysis['analyzers'].items():
                if cls in analyzer.classes_defined:
                    rel_path = Path(filepath).relative_to(src_dir)
                    logger.info(f"  • {cls} in {rel_path}")
                    break
        if len(analysis['orphaned_classes']) > 15:
            logger.info(f"  ... and {len(analysis['orphaned_classes']) - 15} more")
    else:
        logger.info("  ✅ No orphaned classes found!")
    
    # Legacy components
    legacy_files = identify_legacy_components(src_dir)
    logger.info(f"\n📁 LEGACY COMPONENTS ({len(legacy_files)}):")
    for legacy_file in sorted(legacy_files)[:10]:
        rel_path = Path(legacy_file).relative_to(src_dir)
        logger.info(f"  • {rel_path}")
    if len(legacy_files) > 10:
        logger.info(f"  ... and {len(legacy_files) - 10} more")
    
    # Duplicate functionality
    duplicates = find_duplicate_functionality(analysis['analyzers'])
    logger.info(f"\n🔄 POTENTIAL DUPLICATES ({len(duplicates)}):")
    for func_name, count, locations in sorted(duplicates, key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"  • {func_name} ({count} locations):")
        for loc in locations[:3]:  # Show first 3 locations
            rel_path = Path(loc).relative_to(src_dir)
            logger.info(f"    - {rel_path}")
        if len(locations) > 3:
            logger.info(f"    ... and {len(locations) - 3} more")
    
    # Most imported modules
    logger.info(f"\n📦 MOST IMPORTED MODULES:")
    for module, count in analysis['imports'].most_common(10):
        logger.info(f"  • {module}: {count} times")
    
    # Cleanup recommendations
    logger.info(f"\n🧹 CLEANUP RECOMMENDATIONS:")
    
    total_orphans = len(analysis['orphaned_functions']) + len(analysis['orphaned_classes'])
    if total_orphans > 0:
        logger.info(f"  1. Review {total_orphans} orphaned functions/classes for removal")
    
    if legacy_files:
        logger.info(f"  2. Archive {len(legacy_files)} legacy files to reduce codebase size")
    
    if duplicates:
        logger.info(f"  3. Consolidate {len(duplicates)} potentially duplicate functions")
    
    # Calculate cleanup potential
    cleanup_score = max(0, 100 - (total_orphans + len(legacy_files) + len(duplicates)))
    logger.info(f"\n📈 CODEBASE HEALTH SCORE: {cleanup_score}/100")
    
    if cleanup_score >= 80:
        logger.info("  🎉 Excellent! Codebase is well-maintained")
    elif cleanup_score >= 60:
        logger.info("  ✅ Good! Minor cleanup recommended")
    elif cleanup_score >= 40:
        logger.info("  ⚠️  Fair - Some cleanup needed")
    else:
        logger.info("  🚨 Poor - Significant cleanup recommended")

def main():
    """Run the orphan analysis."""
    src_dir = Path(__file__).parent / "src"
    
    if not src_dir.exists():
        logger.error(f"Source directory not found: {src_dir}")
        return 1
    
    try:
        analysis = analyze_codebase(src_dir)
        generate_report(analysis, src_dir)
        
        return 0
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
