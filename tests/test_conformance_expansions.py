"""The expansions Phase 3 builds, reproduced by hand before they are built.

The specification says of each: "a reading, not yet reproduced on a graph; to
be reproduced before it is built." They are reproduced here with the data
model's own constructors — no rule engine performs a step — and each is held to
two things: its result is ``same_graph`` to what the engine's fused move
produces today, and every step in it is an equivalence over small structures.

So when Phase 3 replaces a fused move with its recorded expansion, the graph
that comes out is already known, and so is each step on the way.
"""
import dau_kernel
import tarski
from dau_kernel import Move
from egi_core_dau import Edge, Vertex
from egif_parser_dau import parse_egif
from proof_authoring import apply_rule
from vertex_scope import normalize_constants
from vertex_splitting_merging_rules import VertexMergingRule


def _merge(g, v1, v2, edge):
    """Def 16.6 merging (p.176), performed with no check: v2 into v1 along ``edge``."""
    return VertexMergingRule()._apply_vertex_merge(g, v1_id=v1, v2_id=v2, identity_edge_id=edge)


def _equivalent(g, h) -> bool:
    relations, constants = tarski.vocabulary(g, h)
    for size in (1, 2):
        structures, _ = tarski.universe(relations, constants, size, cap=12, sample_n=64, seed=1)
        if tarski.model_set(g, structures) != tarski.model_set(h, structures):
            return False
    return True


def _every_step_is_an_equivalence(chain) -> bool:
    return all(_equivalent(a, b) for a, b in zip(chain, chain[1:]))


def _constant(vid):
    return Vertex(vid, label="a", is_generic=False)


def test_normalising_a_constant_whose_survivor_dominates_its_twin():
    """CONSTANT_IDENTITY, then a merge (specification §4.4; Def 24.10 p.271,
    Def 16.6 p.176). "a" on the sheet under P, and a second "a" in a cut under Q."""
    g = parse_egif("~[ ]")
    cut = next(iter(g.Cut)).id
    g = g.with_vertex_in_context(_constant("a1"), g.sheet).with_edge(Edge("p"), ("a1",), "P", g.sheet)
    g = g.with_vertex_in_context(_constant("a2"), cut).with_edge(Edge("q"), ("a2",), "Q", cut)
    linked = g.with_edge(Edge("id"), ("a1", "a2"), "=", cut)     # c = ctx(a2) ≤ ctx(a1), ctx(a2)
    merged = _merge(linked, "a1", "a2", "id")                    # ctx(a1) ≥ ctx(id) = ctx(a2)
    assert dau_kernel.same_graph(merged, normalize_constants(g))
    assert _every_step_is_an_equivalence([g, linked, merged])


def test_normalising_a_constant_whose_twins_sit_in_sibling_cuts():
    """The link must lie in a context enclosed by both vertices, and two sibling
    cuts have none. So CONSTANT_EXISTENCE puts a fresh vertex at their least
    common area first, and each twin is linked to it and merged into it."""
    g = parse_egif("~[ ] ~[ ]")
    c1, c2 = sorted(c.id for c in g.Cut)
    g = g.with_vertex_in_context(_constant("a1"), c1).with_edge(Edge("p"), ("a1",), "P", c1)
    g = g.with_vertex_in_context(_constant("a2"), c2).with_edge(Edge("q"), ("a2",), "Q", c2)
    s0 = g.with_vertex_in_context(_constant("u"), g.sheet)       # CONSTANT_EXISTENCE
    s1 = s0.with_edge(Edge("i1"), ("u", "a1"), "=", c1)          # CONSTANT_IDENTITY, c = c1
    s2 = _merge(s1, "u", "a1", "i1")
    s3 = s2.with_edge(Edge("i2"), ("u", "a2"), "=", c2)          # CONSTANT_IDENTITY, c = c2
    s4 = _merge(s3, "u", "a2", "i2")
    assert dau_kernel.same_graph(s4, normalize_constants(g))
    assert _every_step_is_an_equivalence([g, s0, s1, s2, s3, s4])


def test_the_kernel_lets_a_named_vertex_be_merged_into_its_namesake_and_no_other():
    """What Phase 3 item 1 changed. The author ruled on 2026-11-25 that Def
    16.6's merge covers two vertices carrying the same constant. Until
    2026-11-26 the kernel's judge refused any named v₂, and this test pinned
    that refusal so the change would be made on purpose. Turned over: the
    namesake is accepted; a name that would be lost is still refused."""
    g = parse_egif("~[ ]")
    cut = next(iter(g.Cut)).id
    g = g.with_vertex_in_context(_constant("a1"), g.sheet).with_vertex_in_context(_constant("a2"), cut)
    g = g.with_edge(Edge("id"), ("a1", "a2"), "=", cut)
    assert dau_kernel.legal(g, Move("MERGE_VERTICES", ("a1", "a2", "id")))[0] is True

    other = parse_egif("~[ ]")
    other = (other.with_vertex_in_context(Vertex("b1", label="b", is_generic=False), other.sheet)
             .with_vertex_in_context(_constant("a2"), cut_of(other)))
    other = other.with_edge(Edge("id"), ("b1", "a2"), "=", cut_of(other))
    verdict, why = dau_kernel.legal(other, Move("MERGE_VERTICES", ("b1", "a2", "id")))
    assert verdict is False and "carries a name v₁ does not" in why
    line = parse_egif("~[ ]")
    line = (line.with_vertex_in_context(Vertex("x"), line.sheet)
            .with_vertex_in_context(_constant("a2"), cut_of(line)))
    line = line.with_edge(Edge("id"), ("x", "a2"), "=", cut_of(line))
    assert dau_kernel.legal(line, Move("MERGE_VERTICES", ("x", "a2", "id")))[0] is False


def cut_of(g):
    return next(iter(g.Cut)).id


def test_the_engine_reaches_both_normalisations_by_the_rules_reproduced_above():
    """The two hand-built expansions, now performed: ``join_constant_lines``
    applies the same rules in the same order, every step certified, and
    reaches the graph the old normaliser did."""
    from derived_rules import join_constant_lines

    g = parse_egif("~[ ]")
    cut = cut_of(g)
    g = g.with_vertex_in_context(_constant("a1"), g.sheet).with_edge(Edge("p"), ("a1",), "P", g.sheet)
    g = g.with_vertex_in_context(_constant("a2"), cut).with_edge(Edge("q"), ("a2",), "Q", cut)
    joined, steps, survivor = join_constant_lines(g, ["a1", "a2"])
    assert steps == ["CONSTANT_IDENTITY", "MERGE_VERTICES"] and survivor == "a1"
    assert dau_kernel.same_graph(joined, normalize_constants(g))

    g = parse_egif("~[ ] ~[ ]")
    c1, c2 = sorted(c.id for c in g.Cut)
    g = g.with_vertex_in_context(_constant("a1"), c1).with_edge(Edge("p"), ("a1",), "P", c1)
    g = g.with_vertex_in_context(_constant("a2"), c2).with_edge(Edge("q"), ("a2",), "Q", c2)
    joined, steps, survivor = join_constant_lines(g, ["a1", "a2"])
    assert steps == ["CONSTANT_EXISTENCE", "CONSTANT_IDENTITY", "MERGE_VERTICES",
                     "CONSTANT_IDENTITY", "MERGE_VERTICES"]
    assert survivor not in ("a1", "a2") and joined.get_context(survivor) == joined.sheet
    assert dau_kernel.same_graph(joined, normalize_constants(g))


def test_iterating_with_a_reused_vertex_is_four_of_dau_s_steps():
    """R2, option A. The engine iterates ``(P x)`` into a deeper cut and hangs
    the copy on x itself. Dau copies every vertex (p.166). The engine's graph
    is reached by: the second iteration clause (p.164) — a new vertex w in the
    cut, joined to x; iteration proper, the copy x′ linked to w, which is in the
    target and Θ-related to x; then two merges (Def 16.6)."""
    g = parse_egif("(P *x) ~[ (Q *y) ]")
    cut = next(iter(g.Cut)).id
    p = next(e for e in g.nu if g.rel[e] == "P")
    x = g.nu[p][0]
    engine = apply_rule("IT+", g, selection=[p, x], target=cut)

    extended = g.with_vertex_in_context(Vertex("w"), cut).with_edge(Edge("xw"), (x, "w"), "=", cut)
    assert dau_kernel.theta(extended, "w", x)
    iterated = (extended.with_vertex_in_context(Vertex("x2"), cut)
                .with_edge(Edge("p2"), ("x2",), "P", cut)
                .with_edge(Edge("wx2"), ("w", "x2"), "=", cut))
    assert dau_kernel.legal(iterated, Move("MERGE_VERTICES", ("w", "x2", "wx2")))[0] is True
    once = _merge(iterated, "w", "x2", "wx2")
    assert dau_kernel.legal(once, Move("MERGE_VERTICES", (x, "w", "xw")))[0] is True
    twice = _merge(once, x, "w", "xw")

    assert dau_kernel.same_graph(twice, engine)
    assert _every_step_is_an_equivalence([g, extended, iterated, once, twice])
    # And the kernel rejects the fused move today, which is the ledger's entry.
    assert dau_kernel.check_step(g, Move("IT+", (p, x), cut), engine).status == dau_kernel.REJECTED
