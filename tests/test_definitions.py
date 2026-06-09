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


# --- local, reversible fold/unfold (docs/DEFINITION_NODE.md) ----------------- #
#
# The guardrail against the Borges 1:1 map: never globally normalize for reading.
# `expand_at` unfolds ONE spot; `fold` puts it back exactly.  Definitions are a
# conservative extension, so the folded and unfolded forms carry identical
# information — you lose nothing by staying folded, and you expand locally only to
# verify a step, then refold.

from definitions import expand_at, fold  # noqa: E402


def _subset_reg():
    return DefinitionRegistry([SUBSET])


def test_expand_at_is_local_leaving_siblings_folded():
    """Unfolding one spot leaves every other defined spot folded."""
    reg = _subset_reg()
    host = parse_egif("[*p] [*q] (subset p q) ~[ (subset q p) ]")
    spots = [eid for eid, r in host.rel.items() if r == "subset"]
    assert len(spots) == 2
    g1 = expand_at(host, reg, spots[0])
    assert sum(1 for r in g1.rel.values() if r == "subset") == 1  # the other stays


def test_expand_at_then_fold_is_identity():
    """`fold(expand_at(g, e)) == g` — unfold is a local, undoable experiment."""
    reg = _subset_reg()
    host = parse_egif("[*p] [*q] (subset p q) ~[ (subset q p) ]")
    spot = next(eid for eid, r in host.rel.items() if r == "subset")
    g1, fp = expand_at(host, reg, spot, return_fold_point=True)
    assert same_graph(fold(g1, fp), host)


def test_expand_at_refuses_a_non_defined_spot():
    """Only a defined-relation spot can be unfolded."""
    reg = _subset_reg()
    host = parse_egif("[*p] [*q] (in p q)")        # `in` is primitive, not defined
    spot = next(eid for eid, r in host.rel.items() if r == "in")
    with pytest.raises(ValueError, match="not a defined-relation spot"):
        expand_at(host, reg, spot)


def test_local_expansion_reaches_the_same_territory_as_global():
    """Local unfolds compose to the global fully-expanded form (conservative):
    expanding the spots one-by-one == `expand` all at once."""
    reg = _subset_reg()
    host = parse_egif("[*p] [*q] (subset p q) ~[ (subset q p) ]")
    g = host
    while True:
        spots = [eid for eid, r in g.rel.items() if r == "subset"]
        if not spots:
            break
        g = expand_at(g, reg, spots[0])
    assert same_graph(g, expand(host, reg))
