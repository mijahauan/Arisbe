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
    # Build a small graph from CLIF then alter alphabet to force arity mismatch
    clif = "(P a b)"
    g = parse_clif(clif)
    assert g.alphabet is not None

    # Original arity inferred is 2; override to 1 to force mismatch
    alph = g.alphabet
    new_ar = dict(alph.ar)
    new_ar["P"] = 1
    forced = AlphabetDAU(
        C=alph.C,
        F=alph.F,
        R=alph.R,
        ar=frozendict(new_ar),
    ).with_defaults()
    with pytest.raises(ValueError):
        _ = RelationalGraphWithCuts(
            V=g.V,
            E=g.E,
            Cut=g.Cut,
            area=g.area,
            nu=g.nu,
            rel=g.rel,
            sheet=g.sheet,
            alphabet=forced,
            rho=g.rho,
        )


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
