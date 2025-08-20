#!/usr/bin/env python
"""
Simple Integrity Validator for Cleaned Arisbe Codebase

This replaces the complex continuous monitoring with a simple pre-commit validator
that ensures we don't reintroduce deprecated dependencies.
"""

import os
import re
import sys
from pathlib import Path

def validate_imports():
    """Validate that no deprecated imports are used."""
    violations = []
    
    # Deprecated import patterns to detect
    deprecated_patterns = [
        r'from layout_engine import',
        r'from inside_out_layout_engine import',
        r'from pipeline_layout_engine import',
        r'from layout_pipeline_design import',
        r'from networkx_qt_layout_engine import',
        r'from qt_native_layout_engine import',
        r'from spatial_layout_controller import'
    ]
    
    # Scan all Python files
    for py_file in Path('.').rglob('*.py'):
        if 'attic' in str(py_file) or '__pycache__' in str(py_file):
            continue
            
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                
            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern in forbidden_patterns:
                    if re.search(pattern, line):
                        violations.append(f'{py_file}:{line_num}: {line.strip()}')
        except:
            continue
    
    return violations

def main():
    print('🔍 Validating codebase integrity...')
    violations = validate_imports()
    
    if violations:
        print(f'❌ Found {len(violations)} violations:')
        for violation in violations:
            print(f'  {violation}')
        return 1
    else:
        print('✅ No integrity violations found')
        return 0

if __name__ == '__main__':
    sys.exit(main())
