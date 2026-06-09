"""The definition layer (``src/definitions.py``).

The keystone validation: the *defined-relation* short forms of Power Set and
Infinity, once expanded, are full-isomorphism equal to the **already-validated
raw fixtures** (``tests/test_math_fixtures.py``).  The collapsed `(subset …)` /
`(succ …)` form provably *is* the verified axiom — the new layer is tied directly
to the passing gate.
"""

import pytest

from definitions import Definition, DefinitionRegistry, expand
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from clif_generator_dau import generate_clif
from eg_navigation import same_graph


# --- the math definitions (non-recursive named graphs) ---------------------- #

SUBSET = Definition("subset", ("z", "x"), "[*z] [*x] ~[ [*w] (in w z) ~[ (in w x) ] ]")
EMPTY = Definition("empty", ("e",), "[*e] ~[ [*z] (in z e) ]")
SUCC = Definition(
    "succ",
    ("x", "s"),
    "[*x] [*s] ~[ [*w] ~[ ~[ (in w s) ~[ ~[ ~[ (in w x) ] ~[ (= w x) ] ] ] ] "
    "                     ~[ ~[ ~[ (in w x) ] ~[ (= w x) ] ] ~[ (in w s) ] ] ] ]",
)

# --- the validated raw fixtures (mirror tests/test_math_fixtures.py) --------- #

POWER_SET_RAW = (
    "~[ [*x] ~[ [*y] "
    "   ~[ [*z] ~[ [*w] (in w z) ~[ (in w x) ] ] "
    "            ~[ (in z y) ] ] ] ]"
)
INFINITY_RAW = (
    "[*I] "
    "  [*e] (in e I) ~[ [*z] (in z e) ] "
    "  ~[ [*x] (in x I) "
    "     ~[ [*s] (in s I) "
    "        ~[ [*w] ~[ ~[ (in w s) ~[ ~[ ~[ (in w x) ] ~[ (= w x) ] ] ] ] "
    "                   ~[ ~[ ~[ (in w x) ] ~[ (= w x) ] ] ~[ (in w s) ] ] ] ] ] ]"
)


def counts(g):
    return (len(g.V), len(g.E), len(g.Cut))


def test_empty_expands_to_its_body():
    reg = DefinitionRegistry([EMPTY])
    defined = parse_egif("[*e] (empty e)")
    expanded = expand(defined, reg)
    assert "empty" not in set(expanded.rel.values())
    assert same_graph(expanded, parse_egif("[*e] ~[ [*z] (in z e) ]"))


def test_defined_power_set_expands_to_raw_fixture():
    """(subset z x) collapses Power Set; expanding it recovers the raw axiom."""
    reg = DefinitionRegistry([SUBSET])
    defined = parse_egif("~[ [*x] ~[ [*y] ~[ [*z] (subset z x) ~[ (in z y) ] ] ] ]")
    expanded = expand(defined, reg)
    assert "subset" not in set(expanded.rel.values())
    assert same_graph(expanded, parse_egif(POWER_SET_RAW))


def test_defined_infinity_expands_to_raw_fixture():
    """empty + succ collapse the Infinity monster; expansion recovers it."""
    reg = DefinitionRegistry([EMPTY, SUCC])
    defined = parse_egif(
        "[*I] [*e] (empty e) (in e I) "
        "~[ [*x] (in x I) ~[ [*s] (in s I) (succ x s) ] ]"
    )
    expanded = expand(defined, reg)
    assert not ({"empty", "succ"} & set(expanded.rel.values()))
    assert same_graph(expanded, parse_egif(INFINITY_RAW))


def test_expanded_form_round_trips_egif_and_clif():
    """Rule-1 of the consistency contract: the expanded form is an ordinary
    Dau-Beta graph, so it round-trips EGIF and exports to CLIF."""
    reg = DefinitionRegistry([SUBSET])
    defined = parse_egif("~[ [*x] ~[ [*y] ~[ [*z] (subset z x) ~[ (in z y) ] ] ] ]")
    expanded = expand(defined, reg)

    reparsed = parse_egif(generate_egif(expanded))
    assert counts(reparsed) == counts(expanded)
    assert same_graph(reparsed, expanded)

    clif = generate_clif(expanded)  # the defined relation never reaches CLIF
    assert "subset" not in clif


def test_use_with_wrong_arity_raises():
    reg = DefinitionRegistry([SUBSET])  # subset/2
    defined = parse_egif("[*z] (subset z)")  # used at arity 1
    with pytest.raises(ValueError, match="arity"):
        expand(defined, reg)


def test_recursive_definition_is_refused_not_looped():
    """A self-referential definition must raise, not expand forever."""
    loop = Definition("loopy", ("a",), "[*a] (loopy a)")
    reg = DefinitionRegistry([loop])
    with pytest.raises(ValueError, match="recursive|terminate"):
        expand(parse_egif("[*a] (loopy a)"), reg)


def test_unknown_port_in_definition_raises():
    with pytest.raises(ValueError, match="ports"):
        Definition("bad", ("missing",), "[*a] (in a a)")
