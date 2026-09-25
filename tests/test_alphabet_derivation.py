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
        """Since the alphabet is derived at construction, the refusal happens
        as the graph is built — the earliest point at which it is true."""
        with pytest.raises(ValueError, match=r"(?i)aritie?s?.*'P'|'P'.*aritie?s?"):
            parse_egif("(P *x) (P x *y)")

    def test_the_refusal_names_both_arities_it_saw(self):
        with pytest.raises(ValueError) as exc:
            parse_egif("(P *x) (P x *y)")
        assert "1" in str(exc.value) and "2" in str(exc.value)

    def test_one_name_at_one_arity_is_fine_however_often_used(self):
        g = parse_egif("(P *x) (P *y) (P *z)")
        assert derive_alphabet(g).ar["P"] == 1


class TestTheAlphabetIsDerivedNotStored:
    """The author's ruling, 2026-09-24: derive on demand from the ink.

    It supersedes Decision 6A ("the builders extend the alphabet"), which
    answered a question we now think was mis-framed. `alphabet` and `rho` were
    being kept in fields whose Dau meaning is *the alphabet this graph is over*
    (Def 23.1; being "over A" is a **relation**, and any superset serves), while
    what they actually held was a **summary of the names the graph uses**. Two
    copies of one fact drift, and every alphabet failure in this arc was that
    drift: 31 `not in Alphabet` and 13 `rho refers to unknown vertex`.

    The criterion the ruling generalizes to, worth applying to the next field
    someone proposes: **store what the ink cannot tell you; derive what it can.**
    `sort` and `quotation` pass — a sort and a quotation binding are choices,
    unreadable from the ink. `alphabet` and `rho` fail.

    Measured before ruling, so that "loses nothing" is a reading and not a hope:
    of 15 corpus graphs carrying an alphabet, **0 declare a name they do not
    use**; of 11 carrying a rho, **0 disagree with their own vertices**.
    """

    def test_a_graph_always_has_the_alphabet_its_ink_implies(self):
        g = parse_egif('(Loves *x *y) ~[ (Happy x) ]')
        assert g.alphabet is not None
        assert g.alphabet.R == frozenset({"Loves", "Happy"})
        assert g.alphabet.ar["Loves"] == 2

    def test_a_wrong_alphabet_handed_in_is_replaced_not_honoured(self):
        """A stored summary that disagrees with the ink is the defect itself."""
        from egi_core_dau import AlphabetDAU, RelationalGraphWithCuts
        from frozendict import frozendict as fd

        g = parse_egif("(P *x)")
        lying = AlphabetDAU(R=frozenset({"NotUsedAnywhere"}), ar=fd({"NotUsedAnywhere": 9}))
        rebuilt = RelationalGraphWithCuts(
            V=g.V, E=g.E, nu=g.nu, sheet=g.sheet, Cut=g.Cut,
            area=g.area, rel=g.rel, alphabet=lying, rho=g.rho,
        )
        assert rebuilt.alphabet.R == frozenset({"P"})
        assert "NotUsedAnywhere" not in rebuilt.alphabet.R

    def test_rho_is_derived_too(self):
        from egi_core_dau import RelationalGraphWithCuts
        from frozendict import frozendict as fd

        g = parse_egif('(Human "Socrates")')
        stale = RelationalGraphWithCuts(
            V=g.V, E=g.E, nu=g.nu, sheet=g.sheet, Cut=g.Cut,
            area=g.area, rel=g.rel, rho=fd({"a-vertex-that-does-not-exist": "Ghost"}),
        )
        assert "a-vertex-that-does-not-exist" not in stale.rho
        assert "Socrates" in set(stale.rho.values())

    def test_drift_is_unconstructible_across_a_builder(self):
        """`with_edge` needed no growth logic once nothing was stored to grow."""
        from egi_core_dau import create_edge, create_vertex

        g = parse_egif("(P *x)")
        v = create_vertex(is_generic=True)
        grown = g.with_vertex(v).with_edge(create_edge(), (v.id,), "white")
        assert "white" in grown.alphabet.R
        assert grown.alphabet.ar["white"] == 1

    def test_the_arity_discipline_now_reaches_every_graph(self):
        """Def 12.6's `ar` is a *function*, so one name has one arity. This used
        to bite only on graphs that happened to carry an alphabet."""
        with pytest.raises(ValueError, match=r"(?i)two arities"):
            parse_egif("(P *x) (P x *y)")

    def test_what_the_ink_cannot_tell_you_is_still_stored(self):
        """The criterion's other half: `sort` and `quotation` must survive."""
        g = parse_egif("(P *x)")
        vid = next(iter(g.V)).id
        sorted_graph = g.with_sort(vid, "proposition")
        assert sorted_graph.sort[vid] == "proposition"
