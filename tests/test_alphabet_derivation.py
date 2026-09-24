"""One alphabet finaliser, field-preserving, refusing what Dau forbids (9e-0).

Dau's formal model wants an explicit alphabet Σ = (C, F, R, ar) — Def 12.6-12.7,
p.126 — where each name has **one** arity. Three parsers needed one, so three
parsers grew one: `_finalize_alphabet_and_rho` existed in three copies, in
`egif_parser_dau`, `cgif_parser_dau` and `clif_parser_dau`. That is the shape
the INS defect taught this project to distrust — one rule with several
implementations, which drift apart in the dark.

They had already drifted into a shared defect. Each rebuilt
`RelationalGraphWithCuts` from an **explicit field list**, so every field the
list forgot was silently dropped: `variable_names`, `sort`, `quotation`.
Measured before the change: a CGIF- or CLIF-parsed graph carried an alphabet and
an **empty** `variable_names`; an EGIF-parsed graph carried names and **no**
alphabet, because EGIF alone never called its copy.

Nothing was broken by that, for the thin reason that CGIF and CLIF never set the
dropped fields. It would have broken the moment EGIF was wired up — which is
exactly what 9e-2 does — and it would have taken the CLIF tie-break with it,
since that reads `variable_names`.

So the helper moves to `egi_core_dau`, which owns `AlphabetDAU`, and preserves
whatever it was handed.
"""

from __future__ import annotations

import pytest

from egi_core_dau import derive_alphabet, with_alphabet_and_rho
from egif_parser_dau import parse_egif


class TestWhatItDerives:
    def test_relation_names_and_arities(self):
        g = parse_egif('(Loves *x *y) (Happy x)')
        alph = derive_alphabet(g)
        assert {"Loves", "Happy"} <= alph.R
        assert alph.ar["Loves"] == 2
        assert alph.ar["Happy"] == 1

    def test_constants_become_C_and_rho(self):
        g = with_alphabet_and_rho(parse_egif('(Human "Socrates")'))
        assert "Socrates" in g.alphabet.C
        assert "Socrates" in set(g.rho.values())

    def test_a_generic_line_maps_to_None_in_rho(self):
        g = with_alphabet_and_rho(parse_egif("(P *x)"))
        assert None in g.rho.values()


class TestItPreservesWhatItWasHanded:
    """The defect that made this a prerequisite rather than a tidy-up."""

    def test_variable_names_survive(self):
        parsed = parse_egif("(Loves *x *y)")
        assert dict(parsed.variable_names), "the fixture must carry names to lose"
        finalized = with_alphabet_and_rho(parsed)
        assert dict(finalized.variable_names) == dict(parsed.variable_names)

    def test_the_second_order_maps_survive(self):
        parsed = parse_egif("(P *x)")
        vid = next(iter(parsed.V)).id
        sorted_graph = parsed.with_sort(vid, "proposition")
        finalized = with_alphabet_and_rho(sorted_graph)
        assert dict(finalized.sort) == dict(sorted_graph.sort)
        assert dict(finalized.quotation) == dict(sorted_graph.quotation)

    def test_the_graph_is_otherwise_unchanged(self):
        from eg_navigation import same_graph

        parsed = parse_egif('(Loves *x *y) ~[ (Happy x) ]')
        assert same_graph(with_alphabet_and_rho(parsed), parsed)


class TestItRefusesWhatDauForbids:
    """Def 12.6 (p.126) gives each name **one** arity.

    Measured before ruling: **0 of 133 corpus graphs** use one name at two
    arities, so refusing costs the corpus nothing. (Seven names are used at
    different arities in *different* graphs, which violates nothing — an
    alphabet is per-graph.)
    """

    def test_a_name_at_two_arities_is_refused_by_name(self):
        g = parse_egif("(P *x) (P x *y)")
        with pytest.raises(ValueError, match=r"(?i)aritie?s?.*'P'|'P'.*aritie?s?"):
            derive_alphabet(g)

    def test_the_refusal_names_both_arities_it_saw(self):
        g = parse_egif("(P *x) (P x *y)")
        with pytest.raises(ValueError) as exc:
            derive_alphabet(g)
        assert "1" in str(exc.value) and "2" in str(exc.value)

    def test_one_name_at_one_arity_is_fine_however_often_used(self):
        g = parse_egif("(P *x) (P *y) (P *z)")
        assert derive_alphabet(g).ar["P"] == 1
