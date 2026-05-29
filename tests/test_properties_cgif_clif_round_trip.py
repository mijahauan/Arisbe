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
    max_examples=120,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(egif_sheet(max_atoms=3, max_cut_depth=1))
def test_clif_generate_is_idempotent_on_regenerated_output(text):
    """generate_clif idempotence, checked from the second CLIF round onward.

    The first round may use the EGIF parser's preserved variable_names
    (e.g. the user's chosen ``*foo``), but the CLIF parser does not
    propagate variable_names, so from the second round on the generator
    falls into its canonical-labeling path. We assert that path is stable."""
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


@pytest.mark.xfail(
    reason=(
        "Issue #10: CLIF generator canonical labeling is unstable when "
        "two bound variables have equivalent structural signatures "
        "(same usage pattern across the outer and inner scopes). The "
        "second→third round swaps the variable assignments. Surfaced by "
        "the closure-idempotence and rule-reversibility property tests "
        "pushing more EGIF shapes through the shared strategy. "
        "strict=False because the bug is order-dependent (cross-call "
        "state in the generator — see issue #1 bug (3) for the same "
        "pattern in EGIFGenerator): triggered reliably in isolation, "
        "sometimes masked when other CLIF calls have warmed module "
        "state. Remove the marker only after issue #10 fixes both the "
        "labeling instability and the state leakage."
    ),
    strict=False,
)
def test_known_clif_generator_canonical_labeling_swap_bug():
    """Minimal reproducer for the CLIF generator non-idempotence bug.

    Input: ``(Loves *x *y) (Loves *z *u) ~[ (Likes *v y) (Likes *w u) ]``

    Round 1 → 2 stabilizes labeling, but round 2 → 3 swaps ``y`` and
    ``u`` inside the inner ``Likes`` calls, producing a different CLIF
    string with the same logical content. Symmetry between the two
    structurally-equivalent variables defeats the canonical refinement.
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
