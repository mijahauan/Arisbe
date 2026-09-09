"""
Property-based tests for CGIF and CLIF parse → generate → parse round-trip.

Strategy: reuse the EGIF strategy from ``test_properties_round_trip.py`` to
produce well-formed EGIs (by parsing valid EGIF), then test each non-EGIF
format's round-trip on those EGIs. This lets us probe the CGIF and CLIF
parser/generator surfaces without designing separate strategies for their
syntax.

A failing example shrinks to a minimal EGIF input that exposes a structural
discrepancy somewhere in the CGIF or CLIF path. Companion to issue #4.
"""

import sys
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cgif_generator_dau import generate_cgif
from cgif_parser_dau import parse_cgif
from clif_generator_dau import generate_clif
from clif_parser_dau import parse_clif
from egif_parser_dau import parse_egif


# --------------------------------------------------------------------------- #
# Strategy (copied from test_properties_round_trip.py — kept inline because  #
# cross-test imports don't resolve under the current pythonpath layout)      #
# --------------------------------------------------------------------------- #

RELATIONS_BY_ARITY: dict[int, list[str]] = {
    1: ["P", "Q", "Sees"],
    2: ["Loves", "Likes", "Knows"],
}
VAR_NAMES = ["x", "y", "z", "u", "v", "w"]


@st.composite
def atomic_relation(draw, available_vars: list[str]):
    arity = draw(st.sampled_from(list(RELATIONS_BY_ARITY.keys())))
    relation = draw(st.sampled_from(RELATIONS_BY_ARITY[arity]))
    args = []
    unused = [v for v in VAR_NAMES if v not in available_vars]
    for _ in range(arity):
        kind = draw(
            st.sampled_from(["defining", "bound"])
            if available_vars and unused
            else st.just("defining" if unused else "bound")
        )
        if kind == "defining" and unused:
            v = draw(st.sampled_from(unused))
            args.append(f"*{v}")
            available_vars.append(v)
            unused.remove(v)
        elif available_vars:
            args.append(draw(st.sampled_from(available_vars)))
        else:
            assume(False)
    return f"({relation} {' '.join(args)})"


@st.composite
def egif_sheet(draw, max_atoms: int = 3, max_cut_depth: int = 1):
    scope_vars: list[str] = []
    n_atoms = draw(st.integers(min_value=1, max_value=max_atoms))
    parts = [draw(atomic_relation(scope_vars)) for _ in range(n_atoms)]
    if max_cut_depth > 0 and draw(st.booleans()):
        cut_vars = list(scope_vars)
        n_cut_atoms = draw(st.integers(min_value=1, max_value=2))
        cut_parts = [draw(atomic_relation(cut_vars)) for _ in range(n_cut_atoms)]
        parts.append(f"~[ {' '.join(cut_parts)} ]")
    return " ".join(parts)


# --------------------------------------------------------------------------- #
# CGIF round-trip                                                             #
# --------------------------------------------------------------------------- #


@settings(
    max_examples=120,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(egif_sheet(max_atoms=3, max_cut_depth=1))
def test_cgif_round_trip_preserves_v_e_cut_counts(text):
    """parse_egif → generate_cgif → parse_cgif preserves |V|, |E|, |Cut|.

    This is the EGIF round-trip property applied through the CGIF surface.
    If CGIF generation drops or duplicates vertices/edges/cuts, this fires."""
    try:
        egi1 = parse_egif(text)
    except Exception:
        assume(False)
        return

    try:
        cgif_text = generate_cgif(egi1)
    except Exception as e:
        pytest.fail(f"CGIF generation raised on EGI from {text!r}: {e}")

    try:
        egi2 = parse_cgif(cgif_text)
    except Exception as e:
        pytest.fail(
            f"CGIF re-parse failed on generator output {cgif_text!r} "
            f"(from EGIF {text!r}): {e}"
        )

    assert len(egi1.V) == len(egi2.V), (
        f"V differs: EGI={len(egi1.V)} CGI={len(egi2.V)} "
        f"on EGIF {text!r} → CGIF {cgif_text!r}"
    )
    assert len(egi1.E) == len(egi2.E), (
        f"E differs: EGI={len(egi1.E)} CGI={len(egi2.E)} "
        f"on EGIF {text!r} → CGIF {cgif_text!r}"
    )
    assert len(egi1.Cut) == len(egi2.Cut), (
        f"Cut differs: EGI={len(egi1.Cut)} CGI={len(egi2.Cut)} "
        f"on EGIF {text!r} → CGIF {cgif_text!r}"
    )


# --------------------------------------------------------------------------- #
# CLIF round-trip                                                             #
# --------------------------------------------------------------------------- #


@settings(
    max_examples=120,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(egif_sheet(max_atoms=3, max_cut_depth=1))
def test_clif_round_trip_preserves_v_e_cut_counts(text):
    """parse_egif → generate_clif → parse_clif preserves |V|, |E|, |Cut|.

    Same property as the CGIF test, applied through the CLIF surface. CLIF's
    universal-quantifier / S-expression syntax is structurally distinct from
    CGIF, so this can catch a different class of bugs."""
    try:
        egi1 = parse_egif(text)
    except Exception:
        assume(False)
        return

    try:
        clif_text = generate_clif(egi1)
    except Exception as e:
        pytest.fail(f"CLIF generation raised on EGI from {text!r}: {e}")

    try:
        egi2 = parse_clif(clif_text)
    except Exception as e:
        pytest.fail(
            f"CLIF re-parse failed on generator output {clif_text!r} "
            f"(from EGIF {text!r}): {e}"
        )

    assert len(egi1.V) == len(egi2.V), (
        f"V differs: EGI={len(egi1.V)} CLI={len(egi2.V)} "
        f"on EGIF {text!r} → CLIF {clif_text!r}"
    )
    assert len(egi1.E) == len(egi2.E), (
        f"E differs: EGI={len(egi1.E)} CLI={len(egi2.E)} "
        f"on EGIF {text!r} → CLIF {clif_text!r}"
    )
    assert len(egi1.Cut) == len(egi2.Cut), (
        f"Cut differs: EGI={len(egi1.Cut)} CLI={len(egi2.Cut)} "
        f"on EGIF {text!r} → CLIF {clif_text!r}"
    )


# --------------------------------------------------------------------------- #
# Generator idempotence (issue #6)                                            #
# --------------------------------------------------------------------------- #


@settings(
    max_examples=120,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(egif_sheet(max_atoms=3, max_cut_depth=1))
def test_cgif_generate_is_idempotent_on_regenerated_output(text):
    """generate_cgif(parse_cgif(generate_cgif(parse_egif(s)))) ==
    generate_cgif(parse_egif(s)).

    Issue #6 extension: CGIF generator now sorts edges, isolated vertices,
    and cuts by canonical structural signatures (Weisfeiler-Leman) rather
    than UUIDs, so two structurally equivalent EGIs emit identical CGIF."""
    try:
        egi1 = parse_egif(text)
    except Exception:
        assume(False)
        return

    first = generate_cgif(egi1)
    egi2 = parse_cgif(first)
    second = generate_cgif(egi2)
    assert first == second, (
        f"CGIF generator not idempotent on round-trip: {text!r}\n"
        f"first:  {first!r}\nsecond: {second!r}"
    )


@settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(egif_sheet(max_atoms=3, max_cut_depth=1))
def test_clif_generate_is_idempotent_on_regenerated_output(text):
    """generate_clif idempotence, checked from the second CLIF round onward.

    The first round may use the EGIF parser's preserved variable_names
    (e.g. the user's chosen ``*foo``), but the CLIF parser does not
    propagate variable_names, so from the second round on the generator
    falls into its canonical-labeling path. We assert that path is stable.

    Bumped to max_examples=200 after issue #10 was fixed (per its
    acceptance criteria) to widen coverage of the canonical-labeling
    path on automorphism-symmetric inputs."""
    try:
        egi1 = parse_egif(text)
    except Exception:
        assume(False)
        return

    first = generate_clif(egi1)
    egi2 = parse_clif(first)
    second = generate_clif(egi2)
    egi3 = parse_clif(second)
    third = generate_clif(egi3)
    assert second == third, (
        f"CLIF generator not idempotent past first round: {text!r}\n"
        f"second: {second!r}\nthird:  {third!r}"
    )


def test_clif_generator_symmetric_likes_round_trips():
    """Regression for issue #10.

    Input: ``(Loves *x *y) (Loves *z *u) ~[ (Likes *v y) (Likes *w u) ]``

    Pre-fix: the two Likes edges had structurally-equivalent canonical
    signatures (true automorphism), so ``sorted`` fell back to frozenset
    iteration order. Two re-parses produced EGIs in which ``e_Likes_2``
    and ``e_Likes_3`` had swapped ν tuples, leading the generator's
    output to differ between round 2 and round 3.

    Post-fix: the generator sorts edges by ``(edge_sig, ν tuple)``. The
    ν tuple uses CLIF's name-derived vertex IDs (``v_x``, ``v_y``, ...),
    which are stable across re-parsings, so the tiebreak is consistent.
    """
    text = "(Loves *x *y) (Loves *z *u) ~[ (Likes *v y) (Likes *w u) ]"
    egi1 = parse_egif(text)
    first = generate_clif(egi1)
    egi2 = parse_clif(first)
    second = generate_clif(egi2)
    egi3 = parse_clif(second)
    third = generate_clif(egi3)
    assert second == third, (
        f"CLIF generator not idempotent past first round.\n"
        f"second: {second!r}\nthird:  {third!r}"
    )


# --------------------------------------------------------------------------- #
# Sanity checks on the generators                                             #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "egif",
    [
        "(P *x)",
        "(Loves *x *y)",
        "(P *x) (Q x)",
        "(P *x) ~[ (Q x) ]",
        '(Loves "Socrates" *x)',
        "~[ (Cat *x) ~[ (Animal x) ] ]",
    ],
)
def test_cgif_round_trips_known_examples(egif):
    """Spot check: round-trip known EGIF examples through CGIF."""
    egi1 = parse_egif(egif)
    egi2 = parse_cgif(generate_cgif(egi1))
    assert len(egi1.V) == len(egi2.V)
    assert len(egi1.E) == len(egi2.E)
    assert len(egi1.Cut) == len(egi2.Cut)


@pytest.mark.parametrize(
    "egif",
    [
        "(P *x)",
        "(Loves *x *y)",
        "(P *x) (Q x)",
        "(P *x) ~[ (Q x) ]",
        '(Loves "Socrates" *x)',
        "~[ (Cat *x) ~[ (Animal x) ] ]",
    ],
)
def test_clif_round_trips_known_examples(egif):
    """Spot check: round-trip known EGIF examples through CLIF."""
    egi1 = parse_egif(egif)
    egi2 = parse_clif(generate_clif(egi1))
    assert len(egi1.V) == len(egi2.V)
    assert len(egi1.E) == len(egi2.E)
    assert len(egi1.Cut) == len(egi2.Cut)


# --------------------------------------------------------------------------- #
# What the strategy above cannot reach                                        #
# --------------------------------------------------------------------------- #
#
# ``RELATIONS_BY_ARITY`` offers arities 1 and 2 only, and ``egif_sheet`` never
# draws a cut with nothing in it. So the two shapes below — a cut holding
# nothing, and a relation taking nothing — were outside every generated example
# in this file, and both were silently lost on the way out. The empty cut is
# not an exotic case: it is the *hold* of the world-scroll, the standing empty
# sibling that keeps M's residence asserting nothing, so it appears in most of
# the corpus's M-bearing graphs. The zero-arity relation is how the whole
# propositional half of the corpus is written.
#
# Both parsers already read ``~[]``, ``(P)`` and ``(not (and))`` correctly.
# These are generator defects, and they are named here rather than in the
# strategy because a shrunk counterexample tells you less than a case whose
# meaning you can state.

EMPTY_CUT_SHAPES = [
    '(P "a") ~[ ]',            # the hold, beside an assertion
    "~[ ]",                    # the hold alone: a graph that denies nothing
    '~[ (P "a") ~[ ] ]',       # a hold enclosed
    '~[ ~[ (P "a") ] ~[ ] ]',  # the world-scroll: one cell and one hold
]


@pytest.mark.parametrize("egif", EMPTY_CUT_SHAPES)
def test_cgif_keeps_an_empty_cut(egif):
    """An empty cut is a cut. CGIF writes it ``~[]``."""
    egi1 = parse_egif(egif)
    egi2 = parse_cgif(generate_cgif(egi1))
    assert len(egi2.Cut) == len(egi1.Cut)
    assert len(egi2.E) == len(egi1.E)


@pytest.mark.parametrize("egif", EMPTY_CUT_SHAPES)
def test_clif_keeps_an_empty_cut(egif):
    """An empty cut is a cut. CLIF writes it ``(not (and))`` — the negation
    of the empty conjunction, which ISO/IEC 24707 gives as true."""
    egi1 = parse_egif(egif)
    egi2 = parse_clif(generate_clif(egi1))
    assert len(egi2.Cut) == len(egi1.Cut)
    assert len(egi2.E) == len(egi1.E)


ZERO_ARITY_SHAPES = [
    "(R)",                     # a bare proposition
    "(P) (Q)",                 # two of them
    "~[ ~[ (P) ] ]",           # the propositional double cut
    "~[ (P) ~[ (Q) ] ]",       # the propositional scroll
]


@pytest.mark.parametrize("egif", ZERO_ARITY_SHAPES)
def test_cgif_keeps_a_zero_arity_relation(egif):
    """A relation with no arguments still says something.

    ``generate_cgif`` returned the empty string for every graph on this list,
    so the whole propositional half of the corpus — ``de_morgan``,
    ``peirce_law``, ``theorem_praeclarum`` and the rest — was emitted as
    nothing at all and read back as the blank sheet.
    """
    egi1 = parse_egif(egif)
    text = generate_cgif(egi1)
    assert text.strip(), f"{egif} generated no CGIF at all"
    egi2 = parse_cgif(text)
    assert len(egi2.E) == len(egi1.E)
    assert len(egi2.Cut) == len(egi1.Cut)


# --------------------------------------------------------------------------- #
# Where a line of identity lives                                              #
# --------------------------------------------------------------------------- #
#
# A line's area is not decoration: its polarity is what makes the line read
# existentially or universally. Both generators decided where to write a line
# from where it is *used* — CGIF placed its defining concept at the least
# common area of the occurrences, CLIF hoisted every line into one prenex
# quantifier at the top — and neither consulted the area the graph actually
# puts the line in. So a line sitting outside all of its uses was moved inward
# on the way out, from an odd context to an even one, and came back
# existential where it had been universal. That is a change of meaning.
#
# The author's rule for the other direction of this arc applies here too:
# hoisting is **outward only**. A line is written where the graph puts it.

LINE_PLACEMENT_SHAPES = [
    "~[ *z ~[ (P z) ] ]",            # the line is one cut outside its only use
    "~[ *z ~[ *w (lt z w) ] ]",      # two lines, at two different depths
    "~[ *x (M x) ~[ (P x) ] ]",      # the subsumption scroll
    "~[ ~[ *z ~[ *w (lt z w) ] ] ]", # peirce_order_1881's shape, in miniature
]


@pytest.mark.parametrize("egif", LINE_PLACEMENT_SHAPES)
def test_cgif_writes_a_line_where_the_graph_puts_it(egif):
    egi1 = parse_egif(egif)
    egi2 = parse_cgif(generate_cgif(egi1))
    assert _depths_of_lines(egi1) == _depths_of_lines(egi2)


@pytest.mark.parametrize("egif", LINE_PLACEMENT_SHAPES)
def test_clif_writes_a_line_where_the_graph_puts_it(egif):
    egi1 = parse_egif(egif)
    egi2 = parse_clif(generate_clif(egi1))
    assert _depths_of_lines(egi1) == _depths_of_lines(egi2)


def _depths_of_lines(egi) -> list[int]:
    """The multiset of cut-depths at which this graph's lines sit, sorted.

    Compared instead of the graphs themselves so a failure says *how* they
    differ — a line one cut too deep — rather than only that they do.
    """
    def depth(element_id: str) -> int:
        d, ctx = 0, egi.get_context(element_id)
        while ctx != egi.sheet:
            d += 1
            ctx = egi.get_context(ctx)
        return d

    return sorted(depth(v.id) for v in egi.V)


def test_cgif_keeps_a_line_that_nothing_attaches_to():
    """An isolated line asserts that something exists. It is not nothing.

    ``_compute_vertex_def_contexts`` collected its areas from ν, so a vertex on
    no edge was absent from the map, got no defining context, and was written
    nowhere. No corpus UoD carries one today, which is why this went unseen.
    CLIF has no corresponding case: it offers no way to introduce an individual
    without a predicate, so there the loss is a limit of the format rather than
    a defect in the generator.
    """
    egi1 = parse_egif("(P *x) *y")
    egi2 = parse_cgif(generate_cgif(egi1))
    assert len(egi2.V) == len(egi1.V)
