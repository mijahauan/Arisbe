"""
Test variable name consistency across linear formats.

This test ensures that variable names are preserved consistently
across EGIF, CGIF, and CLIF translations, maintaining semantic
meaning and user expectations.
"""

import pytest
from src.egif_parser_dau import parse_egif
from src.egif_generator_dau import generate_egif
from src.cgif_generator_dau import generate_cgif
from src.clif_generator_dau import generate_clif


def test_simple_variable_name_preservation():
    """Test that simple variable names are preserved across formats."""
    egif_in = "*x (Human x)"
    graph = parse_egif(egif_in)
    
    egif_out = generate_egif(graph)
    cgif_out = generate_cgif(graph)
    clif_out = generate_clif(graph)
    
    # All formats should use 'x' as the variable name
    assert 'x' in egif_out
    assert 'x' in cgif_out or '?x' in cgif_out  # CGIF uses ?x for bound variables
    assert 'x' in clif_out  # CLIF should preserve semantic name
    
    # CLIF should not use generated IDs like v_abc123
    assert not any(token.startswith('v_') and len(token) > 3 for token in clif_out.split())


def test_multiple_variable_name_preservation():
    """Test that multiple variable names are preserved in order."""
    egif_in = "*x *y *z (Relation x y z)"
    graph = parse_egif(egif_in)
    
    egif_out = generate_egif(graph)
    cgif_out = generate_cgif(graph)
    clif_out = generate_clif(graph)
    
    # Extract variable names from each format
    egif_vars = extract_variables_from_egif(egif_out)
    cgif_vars = extract_variables_from_cgif(cgif_out)
    clif_vars = extract_variables_from_clif(clif_out)
    
    # All should preserve the same semantic names
    assert egif_vars == ['x', 'y', 'z']
    assert cgif_vars == ['x', 'y', 'z']
    assert clif_vars == ['x', 'y', 'z']


def test_nested_cut_variable_preservation():
    """Test variable name preservation in nested cuts."""
    egif_in = "~[ ~[ *x *y *z (Relation x y z) ] ]"
    graph = parse_egif(egif_in)
    
    egif_out = generate_egif(graph)
    cgif_out = generate_cgif(graph)
    clif_out = generate_clif(graph)
    
    # Extract relation arguments from each format
    egif_args = extract_relation_args_from_egif(egif_out)
    cgif_args = extract_relation_args_from_cgif(cgif_out)
    clif_args = extract_relation_args_from_clif(clif_out)
    
    # All should preserve the same argument order and names
    assert egif_args == ['x', 'y', 'z']
    assert cgif_args == ['x', 'y', 'z']  
    assert clif_args == ['x', 'y', 'z']  # This is currently failing


def test_mixed_constants_variables_preservation():
    """Test preservation with mixed constants and variables."""
    egif_in = '*x (Human x) (Mortal "Socrates")'
    graph = parse_egif(egif_in)
    
    clif_out = generate_clif(graph)
    
    # Should preserve variable name 'x' and constant "Socrates"
    assert 'x' in clif_out
    assert 'Socrates' in clif_out or '"Socrates"' in clif_out
    # Should not use generated vertex IDs
    assert not any(token.startswith('v_') and len(token) > 3 for token in clif_out.split())


# Helper functions for extracting variables/arguments

def extract_variables_from_egif(egif_text):
    """Extract variable names from EGIF text."""
    import re
    # Find all *variable patterns
    matches = re.findall(r'\*([a-zA-Z_][a-zA-Z0-9_]*)', egif_text)
    return matches


def extract_variables_from_cgif(cgif_text):
    """Extract variable names from CGIF text."""
    import re
    # Find all [*var] or ?var patterns
    star_matches = re.findall(r'\[\*\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\]', cgif_text)
    question_matches = re.findall(r'\?([a-zA-Z_][a-zA-Z0-9_]*)', cgif_text)
    # Return unique variables in order
    seen = set()
    result = []
    for var in star_matches + question_matches:
        if var not in seen:
            result.append(var)
            seen.add(var)
    return result


def extract_variables_from_clif(clif_text):
    """Extract variable names from CLIF text."""
    import re
    # Find all unquoted identifiers that are not predicates
    # This is a simplified extraction - in practice would need proper parsing
    tokens = clif_text.replace('(', ' ').replace(')', ' ').split()
    variables = []
    predicates = {'Human', 'Mortal', 'Relation', 'not', 'and', 'or', 'exists', 'forall'}
    
    for token in tokens:
        if (token.isalpha() and 
            token not in predicates and 
            not token.startswith('"') and
            token.islower()):  # Variables typically lowercase
            if token not in variables:
                variables.append(token)
    
    return variables


def extract_relation_args_from_egif(egif_text):
    """Extract relation arguments from EGIF text."""
    import re
    # Find relation pattern like (Relation x y z)
    match = re.search(r'\(Relation\s+([^)]+)\)', egif_text)
    if match:
        args = match.group(1).split()
        return args
    return []


def extract_relation_args_from_cgif(cgif_text):
    """Extract relation arguments from CGIF text."""
    import re
    # Find relation pattern like (Relation ?x ?y ?z)
    match = re.search(r'\(Relation\s+([^)]+)\)', cgif_text)
    if match:
        args = match.group(1).split()
        # Remove ? prefix from variables
        return [arg.lstrip('?') for arg in args]
    return []


def extract_relation_args_from_clif(clif_text):
    """Extract relation arguments from CLIF text."""
    import re
    # Find relation pattern like (Relation x y z) or (Relation v_123 v_456 v_789)
    match = re.search(r'\(Relation\s+([^)]+)\)', clif_text)
    if match:
        args = match.group(1).split()
        return args
    return []


if __name__ == "__main__":
    # Run the failing test to see current behavior
    test_nested_cut_variable_preservation()
