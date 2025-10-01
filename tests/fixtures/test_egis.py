"""
Shared EGI fixtures for testing.

Provides pre-built EGI instances for various test scenarios.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from egi_core_dau import (
    create_empty_graph, create_vertex, create_edge, create_cut,
    RelationalGraphWithCuts
)
from egif_parser_dau import parse_egif


def create_simple_vertex_egi() -> RelationalGraphWithCuts:
    """Create EGI with single vertex: [*x] (P x)"""
    return parse_egif("[*x] (P x)")


def create_simple_two_vertex_egi() -> RelationalGraphWithCuts:
    """Create EGI with two vertices: [*x] [*y] (Loves x y)"""
    return parse_egif("[*x] [*y] (Loves x y)")


def create_nested_cuts_egi() -> RelationalGraphWithCuts:
    """Create EGI with nested double cut: [*x] ~[ ~[ (P x) ] ]"""
    return parse_egif("[*x] ~[ ~[ (P x) ] ]")


def create_complex_nested_egi() -> RelationalGraphWithCuts:
    """Create EGI with multiple levels of nesting."""
    return parse_egif("[*x] ~[ (P x) ~[ (Q x) ] ]")


def create_multiple_predicates_egi() -> RelationalGraphWithCuts:
    """Create EGI with multiple predicates on same vertex."""
    return parse_egif("[*s] (Human s) (Mortal s)")


def create_empty_egi() -> RelationalGraphWithCuts:
    """Create completely empty EGI."""
    return create_empty_graph()


def create_single_cut_egi() -> RelationalGraphWithCuts:
    """Create EGI with single cut containing vertex: ~[ [*x] (P x) ]"""
    return parse_egif("~[ [*x] (P x) ]")


# Test data catalog for systematic testing
TEST_EGIS = {
    'empty': create_empty_egi,
    'simple_vertex': create_simple_vertex_egi,
    'two_vertices': create_simple_two_vertex_egi,
    'nested_cuts': create_nested_cuts_egi,
    'complex_nested': create_complex_nested_egi,
    'multiple_predicates': create_multiple_predicates_egi,
    'single_cut': create_single_cut_egi,
}


def get_test_egi(name: str) -> RelationalGraphWithCuts:
    """
    Get a test EGI by name.
    
    Args:
        name: One of the keys in TEST_EGIS
        
    Returns:
        RelationalGraphWithCuts instance
    """
    if name not in TEST_EGIS:
        raise ValueError(f"Unknown test EGI: {name}. Available: {list(TEST_EGIS.keys())}")
    return TEST_EGIS[name]()
