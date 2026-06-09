"""Math fixtures — ZFC + Peirce 1881 arithmetic as validated Arisbe EGIF.

These pin the *renderable* (non-schema) fixtures from
``docs/MATH_FIXTURES_ZFC_PEIRCE_1881.md`` as genuinely Arisbe-valid EGIF: every
axiom parses, and every one round-trips (parse -> generate -> parse) preserving
its (V, E, Cut) counts.

Equality is written ``(= a b)`` — Dau's special dyadic identity relation,
formalized as a 2-ary edge labeled ``=`` (Ch. 11, "the identity relation will be
captured by 2-ary edges, labeled with the special relation name ="). This is the
doc's "relational alternative" and the form the EGIF lexer now reads (the
generator already emitted it). The doc's primary ``[a b]`` coreference-bracket
notation is *not* the chosen surface: Dau explicitly refines the
"two coincident points merge into one line" reading into the ``=`` edge.

The schema fixtures (ZFC Separation/Replacement, Peirce induction P7) carry holes
``⟨phi: ...⟩`` and are NOT ordinary EGIF.  The graph-with-holes node now exists
(``src/schema.py``), so they ARE exercised here (bottom of file): each parses as a
``Schema`` with the expected hole arity and instantiates to a hole-free Beta graph
that round-trips.  The deep coverage (Replacement's per-occurrence relabeling,
shared parameters, the native-EGIF round-trip, the CLIF-export refusal) lives in
``tests/test_schema.py``.
"""

import pytest

from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif


# Each value is Arisbe EGIF: ``*x`` defining, ``x`` bound, ``~[ ... ]`` cut,
# juxtaposition = conjunction, ``(= a b)`` = Dau's identity edge.
FIXTURES = {
    # --- Part I: ZFC, the seven non-schema axioms (one graph each) ---
    # 1. Extensionality: same members => equal.
    "zfc_extensionality": (
        "~[ [*x] [*y] "
        "   ~[ [*z] ~[ ~[ (in z x) ~[ (in z y) ] ] "
        "              ~[ (in z y) ~[ (in z x) ] ] ] ] "
        "   ~[ (= x y) ] ]"
    ),
    # 2. Empty Set: a set with no members.
    "zfc_empty_set": "[*x] ~[ [*y] (in y x) ]",
    # 3. Pairing (existence form): for any x, y a set containing both.
    "zfc_pairing": "~[ [*x] [*y] ~[ [*z] (in x z) (in y z) ] ]",
    # 4. Union: a set containing every member of every member of F.
    "zfc_union": (
        "~[ [*F] ~[ [*A] "
        "   ~[ [*x] [*B] (in x B) (in B F) ~[ (in x A) ] ] ] ]"
    ),
    # 5. Power Set: a set containing every subset of x (subset inlined).
    "zfc_power_set": (
        "~[ [*x] ~[ [*y] "
        "   ~[ [*z] ~[ [*w] (in w z) ~[ (in w x) ] ] "
        "            ~[ (in z y) ] ] ] ]"
    ),
    # 6. Infinity: contains the empty set, closed under successor s = x u {x}.
    "zfc_infinity": (
        "[*I] "
        "  [*e] (in e I) ~[ [*z] (in z e) ] "
        "  ~[ [*x] (in x I) "
        "     ~[ [*s] (in s I) "
        "        ~[ [*w] ~[ ~[ (in w s) ~[ ~[ ~[ (in w x) ] ~[ (= w x) ] ] ] ] "
        "                   ~[ ~[ ~[ (in w x) ] ~[ (= w x) ] ] ~[ (in w s) ] ] ] ] ] ]"
    ),
    # 7. Foundation (Regularity): every nonempty set has an in-minimal member.
    "zfc_foundation": (
        "~[ [*x] [*y] (in y x) "
        "   ~[ [*u] (in u x) ~[ [*z] (in z u) (in z x) ] ] ]"
    ),
    # --- Part IV: Peirce 1881 arithmetic (Shields reconstruction) ---
    # P1. Irreflexivity.
    "peirce_p1_irreflexivity": "~[ [*x] (lt x x) ]",
    # P2. Transitivity.
    "peirce_p2_transitivity": (
        "~[ [*x] [*y] [*z] (lt x y) (lt y z) ~[ (lt x z) ] ]"
    ),
    # P3. Trichotomy (linearity): x<y or x=y or y<x.
    "peirce_p3_trichotomy": (
        "~[ [*x] [*y] ~[ (lt x y) ] ~[ (= x y) ] ~[ (lt y x) ] ]"
    ),
    # P4. Discreteness: an immediate successor exists.
    "peirce_p4_discreteness": (
        "~[ [*x] ~[ [*y] (lt x y) ~[ [*z] (lt x z) (lt z y) ] ] ]"
    ),
    # P5. Least element (Peirce starts the count at 1).
    "peirce_p5_least_element": "[*x] ~[ [*y] ~[ (lt x y) ] ~[ (= x y) ] ]",
    # P6. No greatest element (unboundedness).
    "peirce_p6_no_greatest": "~[ [*x] ~[ [*y] (lt x y) ] ]",
}


@pytest.mark.parametrize("name", sorted(FIXTURES))
def test_fixture_parses(name):
    """Every renderable math fixture is valid Arisbe EGIF."""
    g = parse_egif(FIXTURES[name])
    assert len(g.V) >= 1
    # the only nonlogical vocabulary is (in ...) / (lt ...) plus the = edge
    rel_names = {g.rel[e] for e in g.rel}
    assert rel_names <= {"in", "lt", "="}, f"{name}: unexpected relations {rel_names}"


@pytest.mark.parametrize("name", sorted(FIXTURES))
def test_fixture_round_trips(name):
    """parse -> generate -> parse preserves the (V, E, Cut) shape."""
    g1 = parse_egif(FIXTURES[name])
    g2 = parse_egif(generate_egif(g1))
    assert (len(g1.V), len(g1.E), len(g1.Cut)) == (
        len(g2.V),
        len(g2.E),
        len(g2.Cut),
    )


def test_equality_is_dau_identity_edge():
    """Equality is the 2-ary ``=`` edge (Dau Ch. 11), not a vertex merge.

    The two lines stay distinct vertices joined by a ``=``-labeled edge.
    """
    g = parse_egif("[*x] [*y] (= x y)")
    assert len(g.V) == 2, "x and y remain distinct vertices (no merge)"
    eq_edges = [e for e in g.rel if g.rel[e] == "="]
    assert len(eq_edges) == 1
    assert len(g.nu[eq_edges[0]]) == 2, "identity is a 2-ary edge"


# --- Part II + P7: the schema fixtures (graph-with-holes node) --------------- #
# Now buildable. ``hole_name -> (arity, occurrences)``; a parameter-free sample
# filler instantiates each to a hole-free Beta graph. Deep coverage in
# tests/test_schema.py.

SCHEMA_FIXTURES = {
    # 8. Separation (Specification) — hole arity 1, 2 occurrences.
    "zfc_separation": (
        "~[ [*p] ~[ [*A] ~[ [*B] "
        "   ~[ [*x] ~[ ~[ (in x B) ~[ (in x A) ⟨phi: x⟩ ] ] "
        "              ~[ (in x A) ⟨phi: x⟩ ~[ (in x B) ] ] ] ] "
        "] ] ]",
        ("phi", 1, 2),
        ("[*x] (red x)", ["x"]),  # φ(x) := (red x)
    ),
    # 9. Replacement — hole arity 2, 3 occurrences, per-occurrence relabeling.
    "zfc_replacement": (
        "~[ [*A] "
        "   ~[ [*x] (in x A) ~[ [*y] ⟨phi: x y⟩ "
        "                       ~[ [*y2] ⟨phi: x y2⟩ ~[ (= y y2) ] ] ] ] "
        "   ~[ [*B] "
        "      ~[ [*xi] (in xi A) ~[ [*yi] (in yi B) ⟨phi: xi yi⟩ ] ] ] ]",
        ("phi", 2, 3),
        ("[*x] [*y] (maps x y)", ["x", "y"]),  # φ(x, y) := (maps x y)
    ),
    # P7. Induction = least-number principle — hole arity 1, 3 occurrences.
    "peirce_p7_induction": (
        "~[ [*x] ⟨psi: x⟩ "
        "   ~[ [*u] ⟨psi: u⟩ "
        "      ~[ [*y] ⟨psi: y⟩ (lt y u) ] ] ]",
        ("psi", 1, 3),
        ("[*n] (even n)", ["n"]),  # ψ(n) := (even n)
    ),
}


@pytest.mark.parametrize("name", sorted(SCHEMA_FIXTURES))
def test_schema_fixture_parses_with_expected_hole(name):
    from schema import Schema

    egif, (hole, arity, n_occ), _ = SCHEMA_FIXTURES[name]
    s = Schema.from_egif(egif)
    assert s.holes == {hole: arity}
    assert len(s.occurrences(hole)) == n_occ
    assert not s.is_complete()


@pytest.mark.parametrize("name", sorted(SCHEMA_FIXTURES))
def test_schema_fixture_instantiates_hole_free_and_round_trips(name):
    from schema import Schema, instantiate

    egif, (hole, _, _), (filler, ports) = SCHEMA_FIXTURES[name]
    inst = instantiate(Schema.from_egif(egif), filler, ports=ports)
    # a single-hole schema yields a finished graph with no hole relation left
    assert hole not in set(inst.rel.values())
    g2 = parse_egif(generate_egif(inst))
    assert (len(inst.V), len(inst.E), len(inst.Cut)) == (
        len(g2.V),
        len(g2.E),
        len(g2.Cut),
    )


# --- Part IV (recursive operations): Peirce's +, × as primitive relations ---- #
# NOT eliminable definitions (a recursive body never bottoms out — that's why the
# definition layer's `expand` refuses them). They are ordinary first-order
# (Beta) AXIOMS constraining the new relation symbols `plus`/`times`, grounded in
# `succ` (immediate successor) and `zero`. Reasoning about them uses the induction
# schema (P7). Gamma is needed only for the 2nd-order recursion theorem; Peirce
# 1881 — like first-order PA — sidesteps it exactly this way. See test_induction_proofs.

RECURSION_FIXTURES = {
    # x + 0 = x
    "plus_base": "~[ [*x] [*z] (zero z) ~[ (plus x z x) ] ]",
    # x + S(y) = S(x + y)
    "plus_step": (
        "~[ [*x] [*y] [*z] [*sy] [*sz] "
        "   (plus x y z) (succ y sy) (succ z sz) ~[ (plus x sy sz) ] ]"
    ),
    # x · 0 = 0
    "times_base": "~[ [*x] [*z] (zero z) ~[ (times x z z) ] ]",
    # x · S(y) = x·y + x
    "times_step": (
        "~[ [*x] [*y] [*p] [*sy] (times x y p) (succ y sy) "
        "   ~[ [*q] (plus p x q) (times x sy q) ] ]"
    ),
}


@pytest.mark.parametrize("name", sorted(RECURSION_FIXTURES))
def test_recursion_axiom_parses(name):
    g = parse_egif(RECURSION_FIXTURES[name])
    rel_names = {g.rel[e] for e in g.rel}
    assert rel_names <= {"zero", "succ", "plus", "times"}, f"{name}: {rel_names}"


@pytest.mark.parametrize("name", sorted(RECURSION_FIXTURES))
def test_recursion_axiom_round_trips(name):
    g1 = parse_egif(RECURSION_FIXTURES[name])
    g2 = parse_egif(generate_egif(g1))
    assert (len(g1.V), len(g1.E), len(g1.Cut)) == (
        len(g2.V),
        len(g2.E),
        len(g2.Cut),
    )
