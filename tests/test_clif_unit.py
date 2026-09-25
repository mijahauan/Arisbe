import re

import pytest
from frozendict import frozendict

from src.clif_generator_dau import generate_clif
from src.clif_parser_dau import parse_clif
from src.egi_core_dau import AlphabetDAU, RelationalGraphWithCuts


def test_clif_quoted_constants_roundtrip():
    # Quoted constants in CLIF should be unquoted internally (alphabet/rho)
    # and re-quoted on generation when not simple identifiers.
    clif = '(and (Human "Socrates") (Mortal "Socrates"))'
    g = parse_clif(clif)

    assert g.alphabet is not None
    assert "Socrates" in g.alphabet.C
    # Every rho entry is either None or 'Socrates' in this tiny example
    assert any(name == "Socrates" for name in g.rho.values())

    out = generate_clif(g)
    # Output should contain quoted constant
    assert '(Human "Socrates")' in out or '(Mortal "Socrates")' in out


def test_clif_generator_arity_validation_raises():
    """One relation name, one arity (Def 12.6, p.126: ``ar`` is a function) —
    and where the violation now has to come from.

    This used to hand the constructor a graph whose *declared* alphabet said
    ``P`` was unary while its edge carried two hooks, and require a ValueError.
    Since 2026-09-24 the alphabet is DERIVED from the ink and a declared one is
    discarded, so that disagreement is **unconstructible**: the forced alphabet
    is simply replaced, and there is nothing left to raise about. (The same
    thing happened to ``has_dominating_nodes`` when Def 12.5 moved to
    construction time — a guarantee strong enough to make its own falsifier
    unbuildable, which is worth noticing rather than mourning.)

    So the test asks the two questions that remain askable: the wrong
    declaration is replaced rather than honoured, and the refusal still fires
    — now on the only thing that can still carry the violation, the ink."""
    g = parse_clif("(P a b)")
    assert g.alphabet is not None and g.alphabet.ar["P"] == 2

    forced = AlphabetDAU(
        C=g.alphabet.C, F=g.alphabet.F, R=g.alphabet.R,
        ar=frozendict({**g.alphabet.ar, "P": 1}),
    ).with_defaults()
    replaced = RelationalGraphWithCuts(
        V=g.V, E=g.E, Cut=g.Cut, area=g.area, nu=g.nu, rel=g.rel,
        sheet=g.sheet, alphabet=forced, rho=g.rho,
    )
    assert replaced.alphabet.ar["P"] == 2, "a declared alphabet is replaced, not honoured"

    # The ink itself using one name at two arities: still a ValueError, and it
    # now names the name and both arities it saw.
    with pytest.raises(ValueError, match=r"'P' is used at two arities"):
        parse_clif("(and (P a b) (P a))")


def test_clif_quoted_lowercase_constant_stays_a_constant():
    """A quoted CLIF name is a constant whatever its case.

    ``test_clif_quoted_constants_roundtrip`` above passes on ``"Socrates"``,
    but it is the capital S that carries it: the lexer discarded the quotes
    and the builder fell back to an ``isupper()`` guess. A lowercase quoted
    name — which the generator emits for any constant labelled in lower case —
    came back as an existentially bound variable, so ``(P "x")`` round-tripped
    to ``(exists (x) (P x))``. That is a change of meaning, not of surface
    form.
    """
    g = parse_clif('(P "x")')

    (vertex,) = g.V
    assert vertex.label == "x"
    assert not vertex.is_generic
    assert g.alphabet is not None and "x" in g.alphabet.C
    assert generate_clif(g) == '(P "x")'


def test_clif_unquoted_lowercase_identifier_is_still_a_variable():
    """The companion half: nothing quoted, nothing constant."""
    g = parse_clif("(P x)")

    (vertex,) = g.V
    assert vertex.is_generic
    assert vertex.label is None
