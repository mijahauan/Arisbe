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
``<phi: ...>`` and are NOT ordinary EGIF — they await the graph-with-holes node
(Part III of the doc) and are deliberately not exercised here.
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
