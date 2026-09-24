"""Canonical ordering, and the tie-break that makes generation deterministic.

`canonical_signature` computes a Weisfeiler-Leman refinement so the three linear
generators can order elements without consulting minted UUIDs. Its own docstring
is careful about the limit: *"True graph symmetries collapse to equal signatures
— that's intrinsic ambiguity, not a bug."* That is the right answer to "are
these two interchangeable?", and `graph_isomorphism_engine`, `world_scroll` and
`ligature_manipulation_rules` all depend on it.

But a **generator** must still choose one of the interchangeable orderings, and
`sorted(key=sig)` is stable, so equal keys fall back to the input list order —
which comes from iterating a `frozenset` of `uuid4` ids. Measured on
`(P *u) (P *v) ~[ (Loves v *y) (Loves u *x) ]`: 200 parses, two texts, roughly
half and half. Both texts were *correct* — `same_graph` says they denote one
graph and each matches the input — so this was never a soundness defect, only a
determinism one. It is the root of the text-equality flakes two arcs chased.

Fixed 2026-09-24 under the author's ruling (Decision 7(ii)) by
**individualization**: try each assignment of distinct ranks within a tied class,
score each candidate by a structural certificate that names no id, keep the
lexicographic minimum. Opt-in via `break_ties=True` so that every existing
consumer keeps the semantics it relies on.

Why (ii) and not "mint deterministic ids at parse": deterministic ids would make
*re-parses of one text* agree, which is all the failing property asked for. This
makes any two **differently constructed** copies of one graph agree, which is
what a canonical form means and what the round-trip guarantee has implicitly
claimed all along. `test_two_differently_built_copies_order_identically` is the
test that tells those two fixes apart.
"""

from __future__ import annotations

import collections

from canonical_signature import TIE_BREAK_BUDGET, compute_canonical_signatures
from cgif_generator_dau import generate_cgif
from clif_generator_dau import generate_clif
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif

SYMMETRIC = "(P *u) (P *v) ~[ (Loves v *y) (Loves u *x) ]"
PLAIN = '(Human "Socrates") ~[ (Mortal "Socrates") ]'


def _tied_classes(graph, **kw):
    vsig, _, _ = compute_canonical_signatures(graph, **kw)
    return [n for n in collections.Counter(vsig.values()).values() if n > 1]


class TestTheDefaultIsUnchanged:
    """Equal colours for symmetric elements is a feature, and three modules
    read it that way. The tie-break must not reach them."""

    def test_symmetric_lines_still_share_a_colour_by_default(self):
        assert _tied_classes(parse_egif(SYMMETRIC)) == [2, 2]

    def test_an_asymmetric_graph_has_no_ties_either_way(self):
        g = parse_egif(PLAIN)
        assert _tied_classes(g) == []
        assert _tied_classes(g, break_ties=True) == []


class TestTheTieBreak:
    def test_it_gives_every_vertex_a_distinct_rank(self):
        assert _tied_classes(parse_egif(SYMMETRIC), break_ties=True) == []

    def test_one_input_now_yields_one_text_in_every_form(self):
        for generate in (generate_egif, generate_cgif, generate_clif):
            texts = {generate(parse_egif(SYMMETRIC)) for _ in range(40)}
            assert len(texts) == 1, (
                f"{generate.__name__} produced {len(texts)} texts: {sorted(texts)}"
            )

    def test_two_differently_built_copies_order_identically(self):
        """The claim that distinguishes a canonical form from a reproducible one.

        The same graph reached by two different routes — parsed from the
        original text, and parsed from what the generator emitted — must order
        the same. Deterministic ids would not deliver this; a canonical
        tie-break does.
        """
        first = parse_egif(SYMMETRIC)
        second = parse_egif(generate_egif(first))
        assert generate_egif(first) == generate_egif(second)

    def test_the_emitted_name_settles_a_structural_stalemate(self):
        """Structure alone cannot order two interchangeable lines that carry
        different *emitted* names, which is why the certificate carries them.

        Without this, CLIF — which preserves the parser's variable names —
        still emitted two texts after the structural tie was settled. Names stay
        out of the colours, where the isomorphism engine would see them.
        """
        assert _tied_classes(parse_egif(SYMMETRIC), break_ties=True) == []
        texts = {generate_clif(parse_egif(SYMMETRIC)) for _ in range(40)}
        assert len(texts) == 1


class TestTheBudgetIsHonest:
    """A pathologically symmetric graph must degrade visibly, not hang.

    Measured 2026-09-24 over 341 graphs (tier A + the corpus as used): ten tie
    at all, every one a single class of two, so the real work is two
    permutations. The budget guards a case that does not occur here rather than
    one that does.
    """

    def test_the_budget_exists_and_is_a_real_number(self):
        assert isinstance(TIE_BREAK_BUDGET, int) and TIE_BREAK_BUDGET > 1

    def test_over_budget_leaves_the_ties_in_place_rather_than_hanging(self, monkeypatch):
        import canonical_signature

        monkeypatch.setattr(canonical_signature, "TIE_BREAK_BUDGET", 1)
        # Two permutations needed, budget of one: it declines and says so by
        # leaving the classes tied, exactly as break_ties=False would.
        assert _tied_classes(parse_egif(SYMMETRIC), break_ties=True) == [2, 2]
