"""legal() against hand-built cases, each cited to Dau (2006), book pages.

These cases fix what the suite means by "legal" before it is compared with
the engine: a disagreement later is then a question about the engine or about
this reading of Dau, never about an unstated assumption.
"""
from calculus_rules import Move, legal
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


# Not judged
def test_rules_whose_parameters_underdetermine_the_move_are_not_judged():
    g = parse_egif("(P *x)")
    verdict, why = legal(g, Move("MOVE_BRANCHES", (_vertex(g),), g.sheet))
    assert verdict is None and why.startswith("not judged")


def test_a_non_egi_source_is_not_judged():
    from frozendict import frozendict
    from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex
    bad = RelationalGraphWithCuts(
        V=frozenset({Vertex("v1")}), E=frozenset({Edge("e1")}), nu=frozendict({"e1": ("v1",)}),
        sheet="S", Cut=frozenset({Cut("c1")}),
        area=frozendict({"S": frozenset({"e1", "c1"}), "c1": frozenset({"v1"})}),
        rel=frozendict({"e1": "P"}))
    assert legal(bad, Move("ERA", ("e1",)))[0] is None


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
                      "rule_interaction", "vertex_splitting_merging_rules", "proof_authoring"):
        assert forbidden not in src, forbidden


def test_ins_refuses_a_name_at_another_arity():
    """Def 12.6 (p.126): a relation name has one arity; Def 12.7 (p.126):
    |e| = ar(κ(e)) for every edge. Inserting (R x y) where R is unary — by
    the declared alphabet, or by the graph's own edges — yields no EGI over
    one alphabet (Task 10, tier B: dau_2006_p112_ligature)."""
    from dataclasses import replace
    from frozendict import frozendict
    from egi_core_dau import AlphabetDAU
    g = parse_egif("~[ (R *x) ]")
    c = next(iter(g.Cut)).id
    assert legal(g, Move("INS", (), c, "(R *x *y)")) == (
        False, "the content uses a relation name at another arity (Def 12.6-12.7, p.126)")
    assert legal(g, Move("INS", (), c, "(R *y)"))[0] is True
    h = replace(parse_egif("~[ ]"), alphabet=AlphabetDAU(R=frozenset({"R", "="}),
                                                        ar=frozendict({"R": 1, "=": 2})))
    assert legal(h, Move("INS", (), next(iter(h.Cut)).id, "(R *x *y)"))[0] is False
    assert legal(h, Move("INS", (), next(iter(h.Cut)).id, "(P *x *y)"))[0] is True
