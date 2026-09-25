"""legal() against hand-built cases, each cited to Dau (2006), book pages.

These cases fix what the suite means by "legal" before it is compared with
the engine: a disagreement later is then a question about the engine or about
this reading of Dau, never about an unstated assumption.
"""
import pytest

from calculus_rules import DAU_RULES, UNIMPLEMENTED, Move, legal
from egif_parser_dau import parse_egif


def _edge(g, rel):
    return next(e for e in sorted(g.nu) if g.rel[e] == rel)


def _cuts_by_depth(g):
    from calculus_enum import ancestors
    return sorted((c.id for c in g.Cut), key=lambda c: len(ancestors(g, c)))


def _vertex(g):
    return sorted(v.id for v in g.V)[0]


def ok(g, m):
    return legal(g, m)[0]


# ERA — Def 15.2, p.164-165
def test_era_single_edge_needs_no_closure():            # p.165, the edge rule
    g = parse_egif("(P *x) (Q x)")
    assert ok(g, Move("ERA", (_edge(g, "Q"),))) is True


def test_era_vertex_alone_would_dangle():
    g = parse_egif("(P *x) (Q x)")
    assert ok(g, Move("ERA", (_vertex(g),))) is False


def test_era_refused_in_a_negative_context():
    g = parse_egif("~[ (P *x) ]")
    assert ok(g, Move("ERA", (_edge(g, "P"),))) is False


def test_era_of_a_cut_on_an_outer_line():               # p.166-167, Dau's own remark
    g = parse_egif("(P *x) ~[ (Q x) ]")
    assert ok(g, Move("ERA", (_cuts_by_depth(g)[0],))) is True


# INS — Def 15.2, p.164-165
def test_ins_into_a_negative_context_only():
    g = parse_egif("~[ ]")
    c = _cuts_by_depth(g)[0]
    assert ok(g, Move("INS", (), c, "(P *x)")) is True
    assert ok(g, Move("INS", (), g.sheet, "(P *x)")) is False


def test_ins_edge_is_legal_onto_an_existing_line_in_a_negative_context():
    """Dau p.165: erasing an edge keeps its vertices (V^(e) := V), and insertion
    is its inverse, so `*x ~[ ]` may become `*x ~[ (P x) ]`."""
    g = parse_egif("*x ~[ ]")
    c = _cuts_by_depth(g)[0]
    v = _vertex(g)
    assert ok(g, Move("INS_EDGE", (v,), c, "(P x)")) is True
    assert ok(g, Move("INS_EDGE", (v,), g.sheet, "(P x)")) is False   # positive context


# DC+ / DC- — Def 15.2, p.164
def test_dc_plus_empty_anywhere():
    g = parse_egif("~[ ]")
    assert ok(g, Move("DC+", (), g.sheet)) is True
    assert ok(g, Move("DC+", (), _cuts_by_depth(g)[0])) is True


def test_dc_plus_moves_a_vertex_inward_only_with_its_edges():   # Def 12.5 on the result
    g = parse_egif("(P *x) (Q x)")
    v = _vertex(g)
    assert ok(g, Move("DC+", (v,), g.sheet)) is False
    assert ok(g, Move("DC+", (v, _edge(g, "P"), _edge(g, "Q")), g.sheet)) is True


def test_dc_plus_a_cut_named_with_its_contents_is_the_cut():   # Def 12.10, p.134
    # A subgraph holding a cut holds its whole area, so {c, e in c} is the
    # subgraph {c}: its top element is directly in the sheet.
    g = parse_egif("~[ (P *x) ]")
    c = _cuts_by_depth(g)[0]
    assert ok(g, Move("DC+", (c, _edge(g, "P")), g.sheet)) is True
    assert ok(g, Move("DC+", (c, _edge(g, "P")), c)) is False


def test_dc_minus_needs_exactly_one_inner_cut():
    g = parse_egif("~[ ~[ (P *x) ] ]")
    assert ok(g, Move("DC-", (_cuts_by_depth(g)[0],))) is True
    h = parse_egif("~[ (Q *y) ~[ (P *x) ] ]")
    assert ok(h, Move("DC-", (_cuts_by_depth(h)[0],))) is False


# IT+ / IT- — Def 15.2, p.164, 166
def test_it_plus_into_the_same_or_a_nested_context():   # c <= ctx(G0) includes equality
    g = parse_egif("(P *x) ~[ ]")
    p = _edge(g, "P")
    assert ok(g, Move("IT+", (p,), _cuts_by_depth(g)[0])) is True
    assert ok(g, Move("IT+", (p,), g.sheet)) is True


def test_it_plus_never_outward():
    g = parse_egif("~[ (P *x) ]")
    assert ok(g, Move("IT+", (_edge(g, "P"),), g.sheet)) is False


def test_it_minus_finds_the_source_it_was_copied_from():
    g = parse_egif("(P *x) ~[ (P x) ]")
    inner = next(e for e in g.nu if g.get_context(e) != g.sheet)
    assert ok(g, Move("IT-", (inner,))) is True
    h = parse_egif("(P *x) ~[ (Q x) ]")
    assert ok(h, Move("IT-", (_edge(h, "Q"),))) is False


def test_it_minus_in_the_same_context():
    g = parse_egif("(P *x) (P x)")
    assert ok(g, Move("IT-", (sorted(g.nu)[0],))) is True


# Isolated vertices — Def 15.2, p.164, 166: ANY context
def test_vertex_rules_ignore_polarity():
    g = parse_egif("~[ [*x] ]")
    assert ok(g, Move("VERTEX_ERA", (_vertex(g),))) is True
    assert ok(g, Move("VERTEX_INS", (), g.sheet)) is True
    assert ok(g, Move("VERTEX_INS", (), _cuts_by_depth(g)[0])) is True
    h = parse_egif("(P *x)")
    assert ok(h, Move("VERTEX_ERA", (_vertex(h),))) is False


# The ligature and vertex rules — Lemmas 16.2-16.3, Defs 16.4/16.6
#
# These five were `judged=False` until 2026-09-20, and this test recorded that
# gap. It now records its closing: every IMPLEMENTED rule is judged, so the
# refusal layer scores its moves instead of parking them in a `not judged`
# bucket. Only the five rules with no entry point at all remain unjudged, and
# they are named exactly.

def test_every_implemented_rule_is_judged():
    """The blind spot MOVE_BRANCHES hid an unsound move in, closed as a class.

    A rule `legal()` abstains on is scored by no refusal layer and checked by
    the structure layer only for EGI-hood, so nothing but soundness judges it —
    which is how an unsound MOVE_BRANCHES survived a whole fix arc.
    """
    unjudged = sorted(r.name for r in DAU_RULES if r.engine and not r.judged)
    assert unjudged == [], (
        f"{unjudged} are implemented but unjudged — write the oracle, or say "
        f"in the rule table why Dau's parameters cannot decide it")


def test_only_the_entry_point_less_rules_are_unjudged():
    assert sorted(r.name for r in DAU_RULES if not r.judged) == sorted(UNIMPLEMENTED)


# Lemma 16.2, p.172 — extension needs only a vertex; Dau requires no existing
# ligature ("Let a EGI be given with a vertex v"), a lone vertex being one.
def test_extend_wants_exactly_one_vertex():
    g = parse_egif("(P *x)")
    assert ok(g, Move("EXTEND_LIGATURE", (_vertex(g),), g.sheet)) is True
    assert ok(g, Move("EXTEND_LIGATURE", (sorted(g.nu)[0],), g.sheet)) is False


# Lemma 16.3, p.173 — "ctx(w) = c = ctx(f) for all w in W and f in F"
def test_retract_wants_a_connected_ligature_in_one_context():
    g = parse_egif('*x *y (= x y) (P x) (Q y)')
    W = tuple(sorted(v.id for v in g.V))
    assert ok(g, Move("RETRACT_LIGATURE", W, g.sheet)) is True
    # one vertex is not a ligature to retract
    assert ok(g, Move("RETRACT_LIGATURE", W[:1], g.sheet)) is False
    # two vertices with no identity edge between them are not connected
    h = parse_egif("(P *x) (Q *y)")
    assert ok(h, Move("RETRACT_LIGATURE", tuple(sorted(v.id for v in h.V)), h.sheet)) is False


def test_retract_refuses_when_the_identity_edge_is_deeper_than_its_vertices():
    """The clause an earlier arc found the engine ignoring (p.173)."""
    g = parse_egif('*x *y (P x) (Q y) ~[ (= x y) ]')
    W = tuple(sorted(v.id for v in g.V))
    assert ok(g, Move("RETRACT_LIGATURE", W, g.sheet)) is False


# Def 16.6 merging, p.176 — "ctx(v1) >= ctx(e) = ctx(v2)"
def test_merge_wants_the_edge_in_the_merged_vertex_context():
    g = parse_egif('*x *y (= x y) (P x) (Q y)')
    e = next(x for x in g.nu if g.rel.get(x) == "=")
    v1, v2 = g.nu[e]
    assert ok(g, Move("MERGE_VERTICES", (v1, v2, e))) is True
    h = parse_egif('*x *y (P x) (Q y) ~[ (= x y) ]')
    he = next(x for x in h.nu if h.rel.get(x) == "=")
    hv1, hv2 = h.nu[he]
    assert ok(h, Move("MERGE_VERTICES", (hv1, hv2, he))) is False


# MOVE_BRANCHES — Lemma 16.1, p.169-171; Theta is Def 15.1, p.163
def _two_vertices(g):
    return tuple(sorted(v.id for v in g.V))


def test_move_branches_wants_two_vertices():            # p.169, "two vertices va, vb"
    g = parse_egif("*x *y (= x y) (P x) (Q y)")
    assert ok(g, Move("MOVE_BRANCHES", (_vertex(g),), g.sheet)) is False
    assert ok(g, Move("MOVE_BRANCHES", (_edge(g, "="), _vertex(g)), g.sheet)) is False


def test_move_branches_wants_one_context():             # p.169, "c := ctx(va) = ctx(vb)"
    g = parse_egif("*x (P x) ~[ *y (= x y) (Q y) ]")
    assert ok(g, Move("MOVE_BRANCHES", _two_vertices(g), g.sheet)) is False


def test_move_branches_theta_holds_in_one_context():    # p.163 clause 3, satisfied
    g = parse_egif("*x *y (= x y) (P x) (Q y)")
    assert ok(g, Move("MOVE_BRANCHES", _two_vertices(g), g.sheet)) is True


def test_move_branches_theta_fails_when_the_join_is_deeper():
    """Def 15.1 clause 3 (p.163): ctx(e_i) = ctx(v_i+1). An identity edge may
    lawfully sit deeper than the vertices it joins (Def 12.5, p.125), but
    under a cut it ASSERTS an identity rather than wiring a ligature, so Theta
    fails and Lemma 16.1 licenses nothing. `*x *y (P x) (Q y) ~[ (= x y) ]` is
    the shape: moving (P x)'s hook to y turns a true graph false."""
    g = parse_egif("*x *y (P x) (Q y) ~[ (= x y) ]")
    verdict, why = legal(g, Move("MOVE_BRANCHES", _two_vertices(g), g.sheet))
    assert verdict is False and "Def 15.1" in why


def test_move_branches_theta_is_not_transitive():
    """Dau, p.163: the vertex in the cut is in Theta-relation with each of the
    two vertices on the sheet, but those two are not in Theta-relation."""
    g = parse_egif('(P "a") (Q "b") ~[ *z (= "a" z) (= "b" z) ]')
    by_name = {v.label: v.id for v in g.V if not v.is_generic}
    a, b = by_name["a"], by_name["b"]
    z = next(v.id for v in g.V if v.is_generic)
    assert ok(g, Move("MOVE_BRANCHES", (a, b), g.sheet)) is False   # not transitive
    for outer in (a, b):
        # ...and each outer vertex is not in ONE context with z either, so
        # Lemma 16.1 is out of reach from both directions (p.169).
        assert ok(g, Move("MOVE_BRANCHES", (outer, z), g.sheet)) is False


def test_move_branches_needs_a_hook_that_is_not_the_only_witness():
    """Lemma 16.1's proof (p.170-171) deiterates a copy of vb against a
    vaTHETAvb that must survive the move, so the hook moved may not sit on the
    join's only witness. Two vertices joined by nothing but their identity
    edge carry no other hook."""
    g = parse_egif("*x *y (= x y)")
    verdict, why = legal(g, Move("MOVE_BRANCHES", _two_vertices(g), g.sheet))
    assert verdict is False and "p.170-171" in why


def test_a_non_egi_source_cannot_be_built():
    """Dau Def 12.5 (p.125): ctx(e) ≤ ctx(v). Task 10 enforces it at
    construction, so a non-EGI source never reaches legal(): the core refuses
    to build one. (Before, legal() was shown to abstain on it.)"""
    from frozendict import frozendict
    from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex
    with pytest.raises(ValueError, match=r"Dominating nodes violated \(Def 12\.5\)"):
        RelationalGraphWithCuts(
            V=frozenset({Vertex("v1")}), E=frozenset({Edge("e1")}), nu=frozendict({"e1": ("v1",)}),
            sheet="S", Cut=frozenset({Cut("c1")}),
            area=frozendict({"S": frozenset({"e1", "c1"}), "c1": frozenset({"v1"})}),
            rel=frozendict({"e1": "P"}))


def test_unknown_ids_are_illegal():
    g = parse_egif("(P *x)")
    assert ok(g, Move("ERA", ("nope",))) is False
    assert ok(g, Move("VERTEX_INS", (), "nope")) is False


# Quotation opacity (B-min is Arisbe's, not Dau's) — fix round 1, Finding 1
def test_it_rules_not_judged_on_a_quotation_bearing_graph():
    from egi_core_dau import SORT_PROPOSITION

    g = parse_egif("~[ (P *y) ] ~[ (P *w) ] [*z]")
    cuts = _cuts_by_depth(g)
    z = next(v.id for v in g.V if all(v.id not in seq for seq in g.nu.values()))
    g = g.with_quotation_binding(z, cuts[1], sort_name=SORT_PROPOSITION)
    plain_cut = cuts[0]
    for verdict, why in (legal(g, Move("IT-", (plain_cut,))),
                         legal(g, Move("IT+", (plain_cut,), g.sheet))):
        assert verdict is None and why.startswith("not judged: IT")


def test_era_of_a_plain_cut_containing_an_oval_is_not_judged():
    from egi_core_dau import SORT_PROPOSITION

    g = parse_egif("~[ [*z] ~[ (P *w) ] ]")
    outer = next(c.id for c in g.Cut if g.get_context(c.id) == g.sheet)
    inner = next(c.id for c in g.Cut if g.get_context(c.id) == outer)
    z = next(v.id for v in g.V if all(v.id not in seq for seq in g.nu.values()))
    g = g.with_quotation_binding(z, inner, sort_name=SORT_PROPOSITION)
    verdict, why = legal(g, Move("ERA", (outer,)))
    assert verdict is None and "quotation" in why


# The Θ clause (p.166) is not modelled — fix round 1, Finding 2
def test_it_minus_identity_edge_reaching_outside_the_copy_is_not_judged():
    g = parse_egif("(P *x) (P *y) (= x y)")
    eq = next(e for e in g.nu if g.rel[e] == "=")
    xv, yv = g.nu[eq]
    p_of_y = next(e for e in g.nu if g.rel[e] == "P" and g.nu[e] == (yv,))
    verdict, why = legal(g, Move("IT-", (yv, p_of_y, eq)))
    assert verdict is None and why.startswith("not judged: an identity edge")


def test_legal_never_consults_the_engine():
    import calculus_rules
    src = open(calculus_rules.__file__).read()
    for forbidden in ("formal_transformation_rules", "subgraph_closure_validator",
                      "rule_interaction", "vertex_splitting_merging_rules", "proof_authoring",
                      "ligature_manipulation_rules"):
        assert forbidden not in src, forbidden


def test_ins_refuses_a_name_at_another_arity():
    """Def 12.6 (p.126): a relation name has one arity; Def 12.7 (p.126):
    |e| = ar(κ(e)) for every edge. Inserting (R x y) where the host's own edges
    make R unary yields no EGI over one alphabet (Task 10, tier B:
    dau_2006_p112_ligature).

    The third and fourth cases used to hand a graph with NO edges a hand-built
    alphabet declaring R unary, to show legal() consulted a declaration as well
    as the ink. They cannot: since 2026-09-24 the alphabet is derived from the
    ink and a passed one is discarded, so that graph declares nothing and the
    cases tested a premise that no longer exists. They are replaced by the
    corpus graph the ledger entry was actually about, whose ink — not a
    declaration — is what makes R unary, and whose unconstrained name is P."""
    REFUSED = (False,
               "the content uses a relation name at another arity (Def 12.6-12.7, p.126)")
    g = parse_egif("~[ (R *x) ]")
    c = next(iter(g.Cut)).id
    assert legal(g, Move("INS", (), c, "(R *x *y)")) == REFUSED
    assert legal(g, Move("INS", (), c, "(R *y)"))[0] is True
    p112 = parse_egif("*x (P x) ~[ (Q x) (R x) ]")
    cut = next(iter(p112.Cut)).id
    assert legal(p112, Move("INS", (), cut, "(R *y *z)")) == REFUSED
    assert legal(p112, Move("INS", (), cut, "(S *y *z)"))[0] is True
