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


def test_the_kernel_does_not_yet_let_a_named_vertex_be_merged_into_its_namesake():
    """What Phase 3 item 1 changes. The author ruled on 2026-11-25 that Def
    16.6's merge covers two vertices carrying the same constant; the kernel's
    judge still refuses any named v₂. Pinned as it stands, so that the change is
    made on purpose: this test is the one to turn over."""
    g = parse_egif("~[ ]")
    cut = next(iter(g.Cut)).id
    g = g.with_vertex_in_context(_constant("a1"), g.sheet).with_vertex_in_context(_constant("a2"), cut)
    g = g.with_edge(Edge("id"), ("a1", "a2"), "=", cut)
    verdict, why = dau_kernel.legal(g, Move("MERGE_VERTICES", ("a1", "a2", "id")))
    assert verdict is False and "carries a name" in why


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
