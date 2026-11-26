"""Erasing a vertex, and the two constant rules, as worked cases.

The hand-built complement to the enumerated calculus suite for the three rules
that gained an entry point on 2026-11-26 (the conformance arc's Phase 3, item
1), as ``test_chapter15_formal_calculus`` is for Chapter 15. Each case goes
through the door, so the kernel judges what the engine did.

- **Erasing a vertex**, Def 15.2 (p.164, 166): "An isolated vertex may be
  erased from arbitrary contexts."
- **Existence of Constants**, Def 24.10 (p.271): "In each context c, we may add
  a fresh vertex v with ρ(v) = C. Vice versa, if v is an isolated vertex with
  ρ(v) = C v may be erased from c."
- **Constant Identity**, Def 24.10 (p.271), with the text the author ruled on
  2026-11-25: vertices v, w with ρ(v) = ρ(w) = C, a context c ≤ ctx(v), ctx(w);
  an identity link (v, w) may be inserted into c or erased from c.

The first three tests are also the hand reproductions of the ledger entries the
change retired: ``vertex-era-erases-a-line-with-its-edges`` (the engine erased
a vertex's edges with it), ``vertex-era-positive-only`` (it refused a negative
context) and ``vertex-era-erases-a-line-not-an-equivalence``.
"""
import pytest

import dau_kernel
import tarski
from calculus_certify import Act, EngineRefusal, certify, name_move
from dau_kernel import ACCEPTED, Move
from egi_core_dau import Edge, Vertex
from egif_parser_dau import parse_egif


def _apply(g, rule, selection=(), target=None, content=None):
    h, certificate = certify(g, Act("engine", rule, tuple(selection), target, content))
    assert certificate.status == ACCEPTED, certificate.why
    return h, certificate


def _refused(g, rule, selection=(), target=None, content=None) -> str:
    with pytest.raises(EngineRefusal) as refusal:
        certify(g, Act("engine", rule, tuple(selection), target, content))
    return str(refusal.value)


def _equivalent(g, h) -> bool:
    relations, constants = tarski.vocabulary(g, h)
    for size in (1, 2):
        structures, _ = tarski.universe(relations, constants, size, cap=12, sample_n=64, seed=1)
        if tarski.model_set(g, structures) != tarski.model_set(h, structures):
            return False
    return True


def _constant(vid, name="a"):
    return Vertex(vid, label=name, is_generic=False)


def _isolated(g, area):
    return next(v.id for v in g.V
                if g.get_context(v.id) == area and not dau_kernel.edges_on(g, v.id))


# -- erasing a vertex (Def 15.2, p.164, 166) ----------------------------------

def test_a_vertex_with_edges_is_refused_and_the_refusal_names_the_edges():
    """Was SEVERE: offered ``x`` of ``(P x)``, ERA — the only road — erased the
    edge too and reported a vertex erasure. E_v = ∅ is the rule's condition."""
    g = parse_egif("(P *x)")
    (edge,) = g.nu
    (x,) = g.nu[edge]
    why = _refused(g, "VERTEX_ERA", [x])
    assert "not isolated" in why and edge in why
    assert dau_kernel.legal(g, Move("VERTEX_ERA", (x,)))[0] is False


def test_an_isolated_vertex_is_erased_from_a_negative_context():
    """Was INCOMPLETE: ERA refuses every negative context, and Dau's vertex
    rule has no polarity condition ("arbitrary contexts")."""
    g = parse_egif("[*x] ~[ [*y] ]")
    cut = next(iter(g.Cut)).id
    h, certificate = _apply(g, "VERTEX_ERA", [_isolated(g, cut)])
    assert certificate.steps == (Move("VERTEX_ERA", (_isolated(g, cut),)),)
    assert dau_kernel.same_graph(h, parse_egif("[*x] ~[ ]"))


@pytest.mark.parametrize("text", ["[*x] ~[ [*y] ]", "[*x] (P *z)", "~[ [*x] ~[ [*y] ] ]"])
def test_erasing_an_isolated_vertex_is_an_equivalence_wherever_it_stands(text):
    """Was NOT AN EQUIVALENCE, because what was erased was a line with its
    edges. Dau's structures have non-empty universes, so "something exists"
    is true at any depth and its erasure changes no model set."""
    g = parse_egif(text)
    for v in sorted(x.id for x in g.V if not dau_kernel.edges_on(g, x.id)):
        h, _ = _apply(g, "VERTEX_ERA", [v])
        assert _equivalent(g, h)


def test_the_vertex_rule_names_exactly_one_vertex():
    g = parse_egif("[*x] [*y] (P *z)")
    x, y = sorted(v.id for v in g.V if not dau_kernel.edges_on(g, v.id))
    (edge,) = g.nu
    assert "exactly one vertex" in _refused(g, "VERTEX_ERA", [x, y])
    assert "exactly one vertex" in _refused(g, "VERTEX_ERA", [edge])
    assert "exactly one vertex" in _refused(g, "VERTEX_ERA", [])


# -- existence of constants (Def 24.10, p.271) --------------------------------

def test_a_constant_may_be_added_in_any_context_and_erased_again():
    g = parse_egif("~[ (P *x) ~[ ] ]")
    outer = next(c for c in g.area[g.sheet] if c in {k.id for k in g.Cut})
    inner = next(c for c in g.area[outer] if c in {k.id for k in g.Cut})
    for area in (g.sheet, outer, inner):                      # positive, negative, positive
        h, certificate = _apply(g, "CONSTANT_EXISTENCE", (), area, "Rex")
        assert certificate.steps == (Move("CONSTANT_EXISTENCE", (), area, "Rex"),)
        (rex,) = [v for v in h.V if v.label == "Rex"]
        assert not rex.is_generic and h.get_context(rex.id) == area
        assert _equivalent(g, h)
        back, certificate = _apply(h, "CONSTANT_EXISTENCE", [rex.id])
        assert certificate.steps == (Move("CONSTANT_EXISTENCE", (rex.id,)),)
        assert dau_kernel.same_graph(back, g)


def test_the_two_vertex_rules_do_not_take_each_other_s_vertices():
    """A vertex "with ρ(v) = C" goes by the constant rule; a generic one by
    Def 15.2. The kernel's vertex judge passed both until 2026-11-26, against
    its own docstring."""
    g = parse_egif("[*x]")
    g = g.with_vertex_in_context(_constant("rex", "Rex"), g.sheet)
    x = next(v.id for v in g.V if v.is_generic)
    assert "CONSTANT_EXISTENCE" in _refused(g, "VERTEX_ERA", ["rex"])
    assert "VERTEX_ERA" in _refused(g, "CONSTANT_EXISTENCE", [x])
    assert dau_kernel.legal(g, Move("VERTEX_ERA", ("rex",)))[0] is False
    assert dau_kernel.legal(g, Move("CONSTANT_EXISTENCE", (x,)))[0] is False
    # and the protocol's ERA of each, in a positive context, is named for the rule it is
    assert name_move(g, "ERA", [x]) == Move("VERTEX_ERA", (x,))
    assert name_move(g, "ERA", ["rex"]) == Move("CONSTANT_EXISTENCE", ("rex",))


def test_a_constant_with_edges_is_not_erased_and_one_with_no_name_is_not_added():
    g = parse_egif('(P "Rex")')
    (edge,) = g.nu
    (rex,) = g.nu[edge]
    why = _refused(g, "CONSTANT_EXISTENCE", [rex])
    assert "not isolated" in why and edge in why
    assert "names the constant" in _refused(g, "CONSTANT_EXISTENCE", (), g.sheet, None)
    assert "does not exist" in _refused(g, "CONSTANT_EXISTENCE", (), "no-such-area", "Rex")


def test_adding_a_constant_twice_mints_two_vertices():
    """A fixed id for the fresh vertex would make the second application a
    silent no-op reported as a success."""
    g = parse_egif("~[ ]")
    h, _ = _apply(g, "CONSTANT_EXISTENCE", (), g.sheet, "Rex")
    h, _ = _apply(h, "CONSTANT_EXISTENCE", (), g.sheet, "Rex")
    assert len([v for v in h.V if v.label == "Rex"]) == 2


# -- constant identity (Def 24.10, p.271) -------------------------------------

def _two_mentions():
    """"a" on the sheet under P; "a" again in a cut under Q; "b" beside it."""
    g = parse_egif("~[ ] ~[ ]")
    c1, c2 = sorted(c.id for c in g.Cut)
    g = g.with_vertex_in_context(_constant("a1"), g.sheet).with_edge(Edge("p"), ("a1",), "P", g.sheet)
    g = g.with_vertex_in_context(_constant("a2"), c1).with_edge(Edge("q"), ("a2",), "Q", c1)
    g = g.with_vertex_in_context(_constant("b1", "b"), c1)
    return g, c1, c2


def test_two_vertices_of_one_name_are_linked_in_a_context_both_enclose():
    g, c1, _c2 = _two_mentions()
    h, certificate = _apply(g, "CONSTANT_IDENTITY", ["a1", "a2"], c1)
    assert certificate.steps == (Move("CONSTANT_IDENTITY", ("a1", "a2"), c1),)
    (link,) = set(h.nu) - set(g.nu)
    assert h.rel[link] == "=" and set(h.nu[link]) == {"a1", "a2"} and h.get_context(link) == c1
    assert _equivalent(g, h)
    back, certificate = _apply(h, "CONSTANT_IDENTITY", [link])
    assert certificate.steps == (Move("CONSTANT_IDENTITY", (link,)),)
    assert dau_kernel.same_graph(back, g)


def test_the_link_goes_nowhere_one_of_the_two_does_not_enclose():
    """c ≤ ctx(v) and c ≤ ctx(w). a2 sits in the first cut, so neither the
    sheet nor the sibling cut will do — which is why two mentions in sibling
    cuts cannot be linked directly (specification §4.4)."""
    g, _c1, c2 = _two_mentions()
    for area in (g.sheet, c2):
        assert "not enclosed by the context of a2" in _refused(
            g, "CONSTANT_IDENTITY", ["a1", "a2"], area)
        assert dau_kernel.legal(g, Move("CONSTANT_IDENTITY", ("a1", "a2"), area))[0] is False


def test_the_link_joins_one_name_only():
    g, c1, _c2 = _two_mentions()
    assert "same constant name" in _refused(g, "CONSTANT_IDENTITY", ["a1", "b1"], c1)
    line = parse_egif("[*x] [*y]")
    x, y = sorted(v.id for v in line.V)
    assert "same constant name" in _refused(line, "CONSTANT_IDENTITY", [x, y], line.sheet)
    # and an identity link between two generic lines is not this rule's to erase
    joined = line.with_edge(Edge("id"), (x, y), "=", line.sheet)
    assert "same constant name" in _refused(joined, "CONSTANT_IDENTITY", ["id"])
    assert dau_kernel.legal(joined, Move("CONSTANT_IDENTITY", ("id",)))[0] is False


def test_the_kernel_accepts_the_link_scribed_either_way_round():
    """The rule's hypothesis is symmetric in v and w."""
    g, c1, _c2 = _two_mentions()
    move = Move("CONSTANT_IDENTITY", ("a1", "a2"), c1)
    for ends in (("a1", "a2"), ("a2", "a1")):
        h = g.with_edge(Edge("id"), ends, "=", c1)
        assert dau_kernel.check_step(g, move, h).status == ACCEPTED


# -- merging a constant into its namesake (Def 16.6, p.176; ruled 2026-11-25) --

def test_a_linked_namesake_is_merged_and_any_other_named_vertex_is_not():
    g, c1, _c2 = _two_mentions()
    linked, _ = _apply(g, "CONSTANT_IDENTITY", ["a1", "a2"], c1)
    (link,) = set(linked.nu) - set(g.nu)
    merged, certificate = certify(linked, Act("merge-checked", "MERGE_VERTICES", ("a1", "a2", link)))
    assert certificate.status == ACCEPTED
    assert [v.id for v in merged.V if v.label == "a"] == ["a1"]
    assert merged.nu["q"] == ("a1",) and _equivalent(g, merged)

    other = g.with_edge(Edge("id"), ("a1", "b1"), "=", c1)      # a = b, asserted in the cut
    with pytest.raises(EngineRefusal) as refusal:
        certify(other, Act("merge-checked", "MERGE_VERTICES", ("a1", "b1", "id")))
    assert "carries a constant name" in str(refusal.value)


# -- the drawing keeps up (the correspondence check, §3.3) --------------------
#
# The conformance arc's gate for a family includes the picture: what these
# rules produce must draw, attest, and read back as the graph it is. They
# leave shapes the six older rules seldom did — a constant standing on the
# sheet with no edge on it, two vertices of one name joined by an identity
# link inside a cut, a cut emptied of its last vertex.

def _draws_and_reads_back(egi) -> bool:
    from correspondence_attestation import attest_correspondence
    from eg_reader import read_drawing, reading_matches_egi
    from elk_layout_engine import ELKLayoutEngine
    from style_loader import load_default_style

    dto = ELKLayoutEngine().generate_layout(egi, load_default_style())
    attest_correspondence(egi, dto)                       # raises on a violation
    return reading_matches_egi(read_drawing(dto), egi, ordered=False)


def test_what_the_three_rules_produce_draws_and_reads_back():
    g = parse_egif('(P "Rex") ~[ [*y] (Q *z) ]')
    cut = next(iter(g.Cut)).id
    erased, _ = _apply(g, "VERTEX_ERA", [_isolated(g, cut)])
    on_sheet, _ = _apply(g, "CONSTANT_EXISTENCE", (), g.sheet, "Rex")
    in_cut, _ = _apply(g, "CONSTANT_EXISTENCE", (), cut, "Rex")
    standing = next(v.id for v in g.V if v.label == "Rex")
    fresh = next(v.id for v in in_cut.V if v.label == "Rex" and v.id != standing)
    linked, _ = _apply(in_cut, "CONSTANT_IDENTITY", [standing, fresh], cut)
    (link,) = set(linked.nu) - set(in_cut.nu)
    merged, _ = certify(linked, Act("merge-checked", "MERGE_VERTICES", (standing, fresh, link)))
    for name, egi in [("vertex erased", erased), ("constant on the sheet", on_sheet),
                      ("constant in a cut", in_cut), ("two of one name linked", linked),
                      ("merged back", merged)]:
        assert _draws_and_reads_back(egi), name
