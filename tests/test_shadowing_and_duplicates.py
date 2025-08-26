import pytest

from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from cgif_generator_dau import generate_cgif
from clif_generator_dau import generate_clif


def test_shadowing_allows_inner_redefinition():
    # Outer x, inner x shadowing is legal per Sowa
    egif = "[*x] ~[ (P *x) (Q x) ] (R x)"
    graph = parse_egif(egif)

    # Generators should succeed without raising
    egif_out = generate_egif(graph)
    cgif_out = generate_cgif(graph)
    clif_out = generate_clif(graph)

    assert isinstance(egif_out, str) and egif_out
    assert isinstance(cgif_out, str) and cgif_out
    assert isinstance(clif_out, str) and clif_out


def test_duplicate_in_same_area_rejected_isolated_defs():
    # Two [*x] in the same area is illegal
    with pytest.raises(ValueError):
        parse_egif("[*x] [*x]")


def test_duplicate_in_same_area_rejected_inline_defs():
    # Two *x in same relation area (sheet) is illegal as two definitions in same area
    with pytest.raises(ValueError):
        parse_egif("(P *x) (Q *x)")
