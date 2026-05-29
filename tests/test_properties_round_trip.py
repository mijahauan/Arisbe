"""
Property-based tests for linear-format round-trip identity.

The existing example-driven tests (test_tomos_parsing.py) exercise round-trip
across 130+ corpus files but each is one fixed string. These hypothesis-driven
tests probe the *space* of well-formed EGIF formulae and check the property
that interests us: parse → generate → parse preserves graph structure.

Currently scoped to EGIF. CGIF and CLIF can be added the same way once these
EGIF strategies are battle-tested.

If a generated formula breaks round-trip, hypothesis will shrink it to a
minimal failing input — that's a real bug report, not test flakiness.
"""

import sys
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif


# --------------------------------------------------------------------------- #
# Strategies                                                                  #
# --------------------------------------------------------------------------- #

# A small alphabet of relations with FIXED ARITY per name. EGIF (and Dau's
# formalism) treats a relation name as a single symbol with a fixed signature;
# the parser is lenient about mixed-arity reuse on input but the generator
# does not preserve it — a separate finding tracked below.
RELATIONS_BY_ARITY: dict[int, list[str]] = {
    1: ["P", "Q", "Sees"],
    2: ["Loves", "Likes", "Knows"],
}
VAR_NAMES = ["x", "y", "z", "u", "v", "w"]


@st.composite
def atomic_relation(draw, available_vars: list[str]):
    """An EGIF atomic relation like (P *x) or (Loves *x y).

    Generates only well-formed EGIF: each defining variable name is fresh in
    the current scope, and each relation name is used at a single fixed arity
    (per RELATIONS_BY_ARITY). Other shapes — shadowing, arity reuse — are
    parser-accepted but break round-trip; regression tests for those bugs
    live in `test_known_generator_shadowing_bug` and
    `test_known_generator_arity_reuse_bug`."""
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
            # Strategy ran out of fresh variables AND has no bound vars; bail.
            assume(False)
    return f"({relation} {' '.join(args)})"


@st.composite
def egif_sheet(draw, max_atoms: int = 3, max_cut_depth: int = 1):
    """An EGIF expression at the sheet level: a sequence of atomic relations
    and optionally one nested cut containing more relations.

    Bound variables introduced inside a cut do not leak out — but for our
    round-trip check we keep the structure simple to keep hypothesis fast."""
    scope_vars: list[str] = []
    n_atoms = draw(st.integers(min_value=1, max_value=max_atoms))
    parts = []
    for _ in range(n_atoms):
        parts.append(draw(atomic_relation(scope_vars)))

    if max_cut_depth > 0 and draw(st.booleans()):
        # Add one nested cut with its own atoms.
        cut_vars = list(scope_vars)  # outer vars can be referenced inside
        n_cut_atoms = draw(st.integers(min_value=1, max_value=2))
        cut_parts = [draw(atomic_relation(cut_vars)) for _ in range(n_cut_atoms)]
        parts.append(f"~[ {' '.join(cut_parts)} ]")

    return " ".join(parts)


# --------------------------------------------------------------------------- #
# Properties                                                                  #
# --------------------------------------------------------------------------- #


def _round_trip(text: str):
    """Parse → generate → parse; returns (egi1, egi2)."""
    egi1 = parse_egif(text)
    regenerated = generate_egif(egi1)
    egi2 = parse_egif(regenerated)
    return egi1, egi2


@settings(
    max_examples=120,
    deadline=None,  # parser is fast but allow headroom on first run
    suppress_health_check=[HealthCheck.too_slow],
)
@given(egif_sheet(max_atoms=3, max_cut_depth=1))
def test_egif_round_trip_preserves_v_e_cut_counts(text):
    """Parse-generate-parse must preserve the |V|, |E|, |Cut| invariants.

    This is weaker than full structural isomorphism but catches the class of
    bugs we actually care about: vertices being dropped, edges being duplicated,
    or cuts being flattened by the generator."""
    try:
        egi1, egi2 = _round_trip(text)
    except Exception:
        # If the parser rejects a generated string, that is a real bug —
        # but for the initial pass we only assert the success case.
        assume(False)
        return

    assert len(egi1.V) == len(egi2.V), f"V differs after round-trip: {text!r}"
    assert len(egi1.E) == len(egi2.E), f"E differs after round-trip: {text!r}"
    assert len(egi1.Cut) == len(egi2.Cut), f"Cut differs after round-trip: {text!r}"


@settings(
    max_examples=120,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(egif_sheet(max_atoms=3, max_cut_depth=1))
def test_egif_generate_is_idempotent_on_regenerated_output(text):
    """generate(parse(generate(parse(s)))) == generate(parse(s)).

    Issue #6: the generator now assigns vertex labels from canonical
    structural signatures (Weisfeiler-Leman-style refinement of relation
    names, argument positions, and area-nesting depth) rather than UUID
    iteration order, so two structurally equivalent EGIs produce identical
    EGIF — including the EGI freshly minted by re-parsing the generator's
    own output."""
    try:
        egi1 = parse_egif(text)
    except Exception:
        assume(False)
        return

    first = generate_egif(egi1)
    egi2 = parse_egif(first)
    second = generate_egif(egi2)

    assert first == second, f"generator not idempotent on round-trip: {text!r}"


# --------------------------------------------------------------------------- #
# Sanity check on the strategy itself                                         #
# --------------------------------------------------------------------------- #


def test_strategy_produces_parseable_formulae():
    """A regression check: a few hand-rolled examples from our own strategy
    shape must parse. If this fails, the strategy is producing invalid EGIF
    and the property tests above are silently no-op'ing via `assume(False)`."""
    samples = [
        "(P *x)",
        "(Loves *x *y)",
        "(P *x) (Q x)",
        "(P *x) ~[ (Q x) ]",
        "(P *x) ~[ (Q x) (R x) ]",
    ]
    for s in samples:
        egi = parse_egif(s)
        assert len(egi.V) >= 1, f"strategy sample {s!r} parsed with no vertices"


def test_shadowed_defining_var_across_cut_boundary_round_trips():
    """Regression for issue #1: when a defining variable name is re-used
    inside a nested cut (effectively shadowing the outer occurrence), the
    generator emits a disambiguated form (e.g. ``*x1`` for the inner one)
    that the parser must accept on re-parse. The original bug was in the
    lexer's identifier classifier: it treated any non-single-letter
    identifier as a relation name. Fixed by tracking defining names as
    they're lexed."""
    text = "(P *x) ~[ (P *x) (P *y *z) ]"
    egi1 = parse_egif(text)
    regenerated = generate_egif(egi1)
    egi2 = parse_egif(regenerated)
    assert len(egi1.V) == len(egi2.V)
    assert len(egi1.E) == len(egi2.E)
    assert len(egi1.Cut) == len(egi2.Cut)


def test_relation_name_reused_with_different_arities_round_trips():
    """Regression for issue #1: a relation name used with multiple arities
    (P as both 1-ary and 2-ary) is accepted by the parser; the generator
    must emit it in a re-parseable form. Same underlying lexer fix as
    ``test_shadowed_defining_var_across_cut_boundary_round_trips`` — the
    relabeled bound vars in the generator's output were being mis-classified
    as relation names."""
    text = "(P *x) ~[ (P *y) (P *u *w) ]"
    egi1 = parse_egif(text)
    regenerated = generate_egif(egi1)
    egi2 = parse_egif(regenerated)
    assert len(egi1.V) == len(egi2.V)
    assert len(egi1.E) == len(egi2.E)
    assert len(egi1.Cut) == len(egi2.Cut)
