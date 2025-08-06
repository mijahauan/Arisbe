#!/usr/bin/env python3
"""
Test Dau-compliant variable name preservation solution.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egif_parser_dau import EGIFParser
from egif_parsing_result import EGIFParsingResult

def test_variable_name_preservation():
    """Test that variable names are preserved correctly in the Dau-compliant solution."""
    
    print("=== Testing Dau-Compliant Variable Name Preservation ===")
    
    # Test the Loves x y example
    egif = '*x *y (Loves x y) ~[ (Happy x) ]'
    print(f"Testing EGIF: {egif}")
    print()
    
    # Parse with new result structure
    parser = EGIFParser(egif)
    result = parser.parse()
    
    print(f"📊 Parsing Result Analysis:")
    print(f"  Type: {type(result)}")
    print(f"  EGI vertices: {len(result.egi.V)}")
    print(f"  Variable names preserved: {len(result.variable_names)}")
    print()
    
    print(f"🔍 Variable Name Mapping:")
    for vertex_id, var_name in result.variable_names.items():
        print(f"  {vertex_id} -> '{var_name}'")
    print()
    
    print(f"🎯 Display Name Testing:")
    for vertex in result.egi.V:
        display_name = result.get_display_name(vertex.id)
        vertex_type = "constant" if vertex.label else "generic"
        print(f"  Vertex {vertex.id} ({vertex_type}): displays as '{display_name}'")
    print()
    
    print(f"✅ Dau Compliance Check:")
    print(f"  EGI has exactly 7 components: {hasattr(result.egi, 'V') and hasattr(result.egi, 'E') and hasattr(result.egi, 'nu') and hasattr(result.egi, 'sheet') and hasattr(result.egi, 'Cut') and hasattr(result.egi, 'area') and hasattr(result.egi, 'rel')}")
    print(f"  Variable names stored separately: {hasattr(result, 'variable_names')}")
    print(f"  Formal model unpolluted: {not hasattr(result.egi, 'variable_names')}")
    print()
    
    # Test expected variable names
    expected_vars = {'x', 'y'}
    actual_vars = set(result.variable_names.values())
    
    if expected_vars == actual_vars:
        print(f"🎉 SUCCESS: Variable names correctly preserved!")
        print(f"   Expected: {expected_vars}")
        print(f"   Actual: {actual_vars}")
    else:
        print(f"❌ FAILURE: Variable names not preserved correctly")
        print(f"   Expected: {expected_vars}")
        print(f"   Actual: {actual_vars}")
    
    return result

if __name__ == "__main__":
    test_variable_name_preservation()
