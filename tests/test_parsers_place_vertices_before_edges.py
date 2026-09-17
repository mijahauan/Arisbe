"""A parser builds only EGIs on its way to one (Dau Def 12.5, p.125).

All three linear-form parsers used to scribe each edge the moment they met it,
with its vertex still where it was first mentioned, and place the vertex at the
least common area of its uses only after the walk. They returned EGIs, but a
constant mentioned in two cuts that do not nest put an edge outside its own
vertex's area, and every graph built between that edge and the final hoist was
not an EGI: Def 12.5 requires ctx(e) ≤ ctx(v) for every edge e and every vertex
v that e hooks. Ψ (p.207) places a line's vertex where it encloses every hook
before anything hooks it; the parsers now do the same, placing vertices on a
graph with no edges and scribing the edges afterwards.

The instrument here checks Def 12.5 itself on every graph a parse constructs,
without relying on the core's own enforcement, so it bites whether or not that
enforcement is on.
"""

import pytest

import egi_core_dau as core
from cgif_parser_dau import parse_cgif
from clif_parser_dau import parse_clif
from egif_parser_dau import parse_egif

PARSE = {"EGIF": parse_egif, "CLIF": parse_clif, "CGIF": parse_cgif}


def _encloses(g, outer, inner):
    """``inner ≤ outer`` (Def 12.2, p.125): ``outer`` is ``inner`` or encloses it."""
    current = inner
    while True:
        if current == outer:
            return True
        if current == g.sheet:
            return False
        current = g.get_context(current)


def _not_dominating(g):
    return [
        (edge_id, vertex_id)
        for edge_id, sequence in g.nu.items()
        for vertex_id in sequence
        if not _encloses(g, g.get_context(vertex_id), g.get_context(edge_id))
    ]


@pytest.fixture
def constructed(monkeypatch):
    """Every graph built while the test runs, with its Def 12.5 violations."""
    seen = []
    validate = core.RelationalGraphWithCuts._validate_dau_constraints

    def recording(self):
        seen.append(_not_dominating(self))
        return validate(self)

    monkeypatch.setattr(core.RelationalGraphWithCuts, "_validate_dau_constraints", recording)
    return seen


def _depth(g, element_id):
    depth, current = 0, g.get_context(element_id)
    while current != g.sheet:
        depth, current = depth + 1, g.get_context(current)
    return depth


# A constant used in two areas that do not nest: outward (a cut and the sheet)
# and across siblings (two cuts in one cut). Its line runs through their least
# common area, at depth 0 and depth 1 respectively.
CASES = [
    ("EGIF", '~[ (P "a") ] (Q "a")', "a", 0),
    ("EGIF", '~[ ~[ (P "a") ] ~[ (Q "a") ] ]', "a", 1),
    ("CLIF", "(and (not (P A)) (Q A))", "A", 0),
    ("CLIF", "(not (and (not (P A)) (not (Q A))))", "A", 1),
    ("CGIF", "~[(P a)] (Q a)", "a", 0),
    ("CGIF", "~[ ~[ (P a) ] ~[ (Q a) ] ]", "a", 1),
]


@pytest.mark.parametrize("form,text,constant,depth", CASES)
def test_every_graph_a_parse_builds_is_an_egi(constructed, form, text, constant, depth):
    g = PARSE[form](text)
    violations = [v for v in constructed if v]
    assert not violations, (
        f"{form} built {len(violations)} non-EGI(s) parsing {text!r}; "
        f"first: ctx(edge) ≰ ctx(vertex) for {violations[0]}"
    )
    (vertex,) = [v for v in g.V if v.label == constant]
    assert _depth(g, vertex.id) == depth


@pytest.mark.parametrize("text", ["(P ?x) [*x]", "[T: ?x] [*x]", "[*x] (P ?x ?y) [*y]"])
def test_cgif_refuses_an_unbound_label_where_it_is_written(text):
    """Deferring the edge must not defer its refusal: a ``?x`` with no ``*x``
    before it is refused, even though a later ``[*x]`` would supply a vertex by
    the time the edges are scribed."""
    with pytest.raises(ValueError, match="not found"):
        parse_cgif(text)
