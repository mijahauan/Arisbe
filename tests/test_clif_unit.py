import re
import pytest

from src.clif_parser_dau import parse_clif
from src.clif_generator_dau import generate_clif
from src.egi_core_dau import AlphabetDAU, RelationalGraphWithCuts
from frozendict import frozendict


def test_clif_quoted_constants_roundtrip():
    # Quoted constants in CLIF should be unquoted internally (alphabet/rho)
    # and re-quoted on generation when not simple identifiers.
    clif = '(and (Human "Socrates") (Mortal "Socrates"))'
    g = parse_clif(clif)

    assert g.alphabet is not None
    assert 'Socrates' in g.alphabet.C
    # Every rho entry is either None or 'Socrates' in this tiny example
    assert any(name == 'Socrates' for name in g.rho.values())

    out = generate_clif(g)
    # Output should contain quoted constant
    assert '(Human "Socrates")' in out or '(Mortal "Socrates")' in out


def test_clif_generator_arity_validation_raises():
    # Build a small graph from CLIF then alter alphabet to force arity mismatch
    clif = '(P a b)'
    g = parse_clif(clif)
    assert g.alphabet is not None

    # Original arity inferred is 2; override to 1 to force mismatch
    alph = g.alphabet
    new_ar = dict(alph.ar)
    new_ar['P'] = 1
    forced = AlphabetDAU(
        C=alph.C,
        F=alph.F,
        R=alph.R,
        ar=frozendict(new_ar),
    ).with_defaults()
    with pytest.raises(ValueError):
        _ = RelationalGraphWithCuts(
            V=g.V, E=g.E, Cut=g.Cut, area=g.area, nu=g.nu, rel=g.rel,
            sheet=g.sheet, alphabet=forced, rho=g.rho
        )
