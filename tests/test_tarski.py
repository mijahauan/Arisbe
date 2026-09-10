"""The fresh Dau-faithful evaluator (spec 2026-09-10 §4, §1a.5).

Validated on pairs whose answer is known before anything is trusted to it:
constant multiplicity/placement is inert (names always denote), generic
placement is not. These pairs are built fresh; the 8/8 and 3/8 pairs of the
2026-09-09 ruling were measured ad hoc and never kept.
"""
import pytest
from frozendict import frozendict

from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex
from egif_parser_dau import parse_egif
from tarski import (
    NotAnEGI, Structure, dominating_nodes, model_set, satisfies,
    sheet_components, universe, vocabulary,
)

G = RelationalGraphWithCuts


def g_(V, E, nu, area, rel, cuts=()):
    return G(V=frozenset(V), E=frozenset(Edge(e) for e in E), nu=frozendict(nu), sheet="S",
             Cut=frozenset(Cut(c) for c in cuts),
             area=frozendict({k: frozenset(v) for k, v in area.items()}), rel=frozendict(rel))


def equivalent(a, b, sizes=(1, 2, 3)):
    rels, consts = vocabulary(a, b)
    for n in sizes:
        us, _ = universe(rels, consts, n, cap=12, sample_n=512, seed=1)
        if model_set(a, us) != model_set(b, us):
            return False
    return True


S1 = Structure(2, {"a": 0}, {"P": {(0,)}, "Q": set(), "p": {()}})


def test_atoms_constants_and_zero_arity():
    assert satisfies(parse_egif('(P "a")'), S1)
    assert not satisfies(parse_egif('(Q "a")'), S1)
    zero = g_([], ["e1"], {"e1": ()}, {"S": {"e1"}}, {"e1": "p"})
    assert satisfies(zero, S1)  # 0-ary read as a truth value: a declared extension


def test_generic_line_is_quantified_where_it_is_placed():
    above = parse_egif("[*x] ~[ (Q x) ]")   # ∃x ¬Q(x)
    inside = parse_egif("~[ (Q *x) ]")      # ¬∃x Q(x)
    s = Structure(2, {}, {"Q": {(0,)}})
    assert satisfies(above, s) and not satisfies(inside, s)


def test_identity_is_equality():
    eq = g_([Vertex("v1"), Vertex("v2")], ["e1"], {"e1": ("v1", "v2")},
            {"S": {"v1", "v2", "e1"}}, {"e1": "="})
    assert satisfies(eq, Structure(1, {}, {}))
    neq = g_([Vertex("v1"), Vertex("v2")], ["e1"], {"e1": ("v1", "v2")},
             {"S": {"v1", "v2", "c1"}, "c1": {"e1"}}, {"e1": "="}, cuts=["c1"])
    assert satisfies(neq, Structure(2, {}, {})) and not satisfies(neq, Structure(1, {}, {}))


def test_constants_may_codenote():
    g = parse_egif('(P "a") ~[ (P "b") ]')
    assert not satisfies(g, Structure(1, {"a": 0, "b": 0}, {"P": {(0,)}}))
    assert satisfies(g, Structure(2, {"a": 0, "b": 1}, {"P": {(0,)}}))


# -- validation pairs ---------------------------------------------------------

def _constant_pair_one_vs_two_spots():
    one = g_([Vertex("a1", label="a", is_generic=False)], ["e1", "e2"],
             {"e1": ("a1",), "e2": ("a1",)}, {"S": {"a1", "e1", "c1"}, "c1": {"e2"}},
             {"e1": "P", "e2": "Q"}, cuts=["c1"])
    two = g_([Vertex("a1", label="a", is_generic=False), Vertex("a2", label="a", is_generic=False)],
             ["e1", "e2"], {"e1": ("a1",), "e2": ("a2",)},
             {"S": {"a1", "e1", "c1"}, "c1": {"a2", "e2"}}, {"e1": "P", "e2": "Q"}, cuts=["c1"])
    return one, two


def _constant_pair_placement():
    out = g_([Vertex("a1", label="a", is_generic=False)], ["e1"], {"e1": ("a1",)},
             {"S": {"a1", "c1"}, "c1": {"e1"}}, {"e1": "Q"}, cuts=["c1"])
    inn = g_([Vertex("a1", label="a", is_generic=False)], ["e1"], {"e1": ("a1",)},
             {"S": {"c1"}, "c1": {"a1", "e1"}}, {"e1": "Q"}, cuts=["c1"])
    return out, inn


def _generic_pair_placement():
    return parse_egif("[*x] ~[ (Q x) ]"), parse_egif("~[ (Q *x) ]")


def _generic_pair_one_vs_two_lines():
    one = parse_egif("(P *x) ~[ (Q x) ]")
    two = parse_egif("(P *x) ~[ (Q *y) ]")
    return one, two


@pytest.mark.parametrize("pair", [_constant_pair_one_vs_two_spots, _constant_pair_placement])
def test_constant_multiplicity_and_placement_are_inert(pair):
    assert equivalent(*pair())


@pytest.mark.parametrize("pair", [_generic_pair_placement, _generic_pair_one_vs_two_lines])
def test_generic_multiplicity_and_placement_are_meaning(pair):
    assert not equivalent(*pair())


# -- guards -------------------------------------------------------------------

def test_a_non_egi_is_refused_not_evaluated():
    bad = g_([Vertex("v1")], ["e1"], {"e1": ("v1",)}, {"S": {"e1", "c1"}, "c1": {"v1"}},
             {"e1": "P"}, cuts=["c1"])
    assert not dominating_nodes(bad)
    assert dominating_nodes(parse_egif("(P *x) ~[ (Q x) ]"))
    with pytest.raises(NotAnEGI):
        satisfies(bad, S1)


def test_universe_is_exhaustive_under_the_cap_and_says_so():
    us, exhaustive = universe((("P", 1),), ("a",), 2, cap=12, sample_n=10, seed=1)
    assert exhaustive and len(us) == 2 * 2 ** 2
    us, exhaustive = universe((("T", 3),), (), 3, cap=12, sample_n=10, seed=1)
    assert not exhaustive and len(us) == 10


def test_una_universe_assigns_names_injectively():
    us, _ = universe((), ("a", "b"), 2, cap=12, sample_n=10, seed=1, una=True)
    assert all(s.value("a") != s.value("b") for s in us) and len(us) == 2


def test_sheet_components_split_on_shared_lines_only():
    g = parse_egif("(P *x) ~[ (Q x) ] (R *y *z) ~[ (P *w) ]")
    assert len(sheet_components(g)) == 3
