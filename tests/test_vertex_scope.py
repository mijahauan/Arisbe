"""Where a line of identity sits, and how many lines one constant gets.

``hoist_vertices_to_lca`` had no test file of its own; it was exercised only
through the three parsers that call it. ``normalize_constants`` is new, and it
carries a ruling: **a constant appearing in several spots is one line of
identity.** The ruling is a normal form rather than a well-formedness law —
the two-line graph is not malformed, it says the same thing — so what is tested
here is that normalizing preserves meaning while giving the linear forms
something they can write down.

The distinction is constant-specific and the tests say so: for a *generic*
line, multiplicity and placement are meaning, and normalizing must leave
generic lines completely alone.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import eg_navigation as nav
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from proof_authoring import apply_rule
from vertex_scope import constants_normalized, normalize_constants


def _rex_lines(egi, label="Rex"):
    return [v for v in egi.V if v.label == label]


def _two_rex_graph():
    """A graph carrying two lines for one constant, built the way the calculus
    builds one: INS of fresh ink naming an individual already standing."""
    seed = parse_egif('~[ (dog "Rex") ]')
    cut = [c.id for c in seed.Cut][0]
    grown = apply_rule("INS", seed, egif='(mammal "Rex")', target=cut)
    assert len(_rex_lines(grown)) == 2, "fixture no longer reproduces the split line"
    return grown


class TestNormalizeConstants:
    def test_two_lines_for_one_constant_become_one(self):
        normalized = normalize_constants(_two_rex_graph())
        assert len(_rex_lines(normalized)) == 1

    def test_every_edge_survives_the_merge(self):
        grown = _two_rex_graph()
        normalized = normalize_constants(grown)
        assert len(normalized.E) == len(grown.E)
        assert sorted(normalized.rel.values()) == sorted(grown.rel.values())

    def test_the_surviving_line_carries_both_edges(self):
        normalized = normalize_constants(_two_rex_graph())
        (rex,) = _rex_lines(normalized)
        reached = [e for e, args in normalized.nu.items() if rex.id in args]
        assert len(reached) == 2

    def test_normalizing_is_what_makes_the_graph_writable(self):
        """The point of the normal form: no linear syntax distinguishes one
        line for a constant from two, so the unnormalized graph cannot survive
        its own EGIF and the normalized one can."""
        grown = _two_rex_graph()
        assert not nav.same_graph(grown, parse_egif(generate_egif(grown)))

        normalized = normalize_constants(grown)
        assert nav.same_graph(normalized, parse_egif(generate_egif(normalized)))

    def test_a_graph_already_in_normal_form_is_returned_unchanged(self):
        egi = parse_egif('~[ (dog "Rex") (mammal "Rex") ]')
        assert normalize_constants(egi) is egi

    def test_generic_lines_are_never_merged(self):
        """Two generic lines are two possibly-different individuals. Merging
        them would change what the graph says, so normalization must not."""
        egi = parse_egif("(dog *x) (mammal *y)")
        normalized = normalize_constants(egi)
        assert len([v for v in normalized.V if v.is_generic]) == 2

    def test_distinct_constants_are_left_distinct(self):
        egi = parse_egif('(dog "Rex") (cat "Tom")')
        normalized = normalize_constants(egi)
        assert {v.label for v in normalized.V} == {"Rex", "Tom"}


class TestConstantsNormalized:
    def test_reports_true_on_a_parsed_graph(self):
        assert constants_normalized(parse_egif('(dog "Rex") (mammal "Rex")'))

    def test_reports_false_on_a_split_line(self):
        assert not constants_normalized(_two_rex_graph())

    def test_reports_true_after_normalizing(self):
        assert constants_normalized(normalize_constants(_two_rex_graph()))

    def test_a_graph_with_no_constants_at_all_is_normal(self):
        assert constants_normalized(parse_egif("(dog *x) ~[ (mammal x) ]"))


class TestTheCorpusBoundaryRefuses:
    """Nothing unnormalized enters the record.

    The guard refuses rather than quietly rewriting, for the same reason §3.3
    refuses: a UoD carries its transformation chain's own per-state EGIs beside
    ``current.egi``, and silently rewriting one of them would let the two drift
    apart. A refusal also names the producer that minted the second line, which
    a silent repair would hide.
    """

    @staticmethod
    def _uod(uod_id, egi):
        from datetime import datetime, timezone

        from universe_of_discourse import (
            UniverseOfDiscourse,
            UoDCategory,
            UoDMetadata,
            UoDType,
        )

        now = datetime.now(timezone.utc)
        return UniverseOfDiscourse(
            metadata=UoDMetadata(
                uod_id=uod_id,
                uod_type=UoDType.HISTORICAL,
                name="constant normal form",
                description="Synthesised in test for the save-boundary guard.",
                category=UoDCategory.PRACTICE_SESSION,
                created=now,
                last_modified=now,
            ),
            current_egi=egi,
        )

    def test_a_split_line_is_refused_before_anything_is_written(self, tmp_path):
        from tomos_service import ConstantNormalFormViolation, TomosService

        service = TomosService(tmp_path)
        with pytest.raises(ConstantNormalFormViolation) as caught:
            service.save_uod(self._uod("split_line", _two_rex_graph()))

        assert "Rex" in str(caught.value)
        assert not list(tmp_path.rglob("current.egi.json")), (
            "the refusal must abort before any disk write"
        )

    def test_a_normalized_graph_saves(self, tmp_path):
        from tomos_service import TomosService

        service = TomosService(tmp_path)
        service.save_uod(
            self._uod("one_line", normalize_constants(_two_rex_graph()))
        )
        assert list(tmp_path.rglob("current.egi.json"))


class TestAConstantsPositionIsWritable:
    """EGIF *can* say where a constant's line sits, and the generator must.

    A generic line marks its position with its defining occurrence, ``*x``. A
    constant has no defining occurrence — but a bare mention serves as one, and
    the parser honours it, so ``"Rex" ~[ (dog "Rex") ]`` puts Rex on the sheet
    while ``~[ (dog "Rex") ]`` puts it in the cut. The format was never the
    limit here.

    What the generator did was omit the mention, so a constant seated above the
    least common area of its uses came back re-interned at that area. Erasure
    is what exposes this: erase the edge that was holding a constant deep, and
    the line is left above its remaining uses.
    """

    @staticmethod
    def _depth(egi, element_id):
        depth, area = 0, egi.get_context(element_id)
        while area != egi.sheet:
            depth += 1
            area = egi.get_context(area)
        return depth

    def test_a_bare_mention_makes_one_line_not_two(self):
        egi = parse_egif('"Rex" ~[ (dog "Rex") ] ~[ (mammal "Rex") ]')
        assert len(_rex_lines(egi)) == 1
        assert constants_normalized(egi)

    def test_a_bare_mention_pins_the_line_where_it_is_written(self):
        egi = parse_egif('"Rex" ~[ (dog "Rex") ] ~[ (mammal "Rex") ]')
        (rex,) = _rex_lines(egi)
        assert self._depth(egi, rex.id) == 0

    def test_without_the_mention_the_line_sits_at_the_least_common_area(self):
        egi = parse_egif('~[ (dog "Rex") ~[ (mammal "Rex") ] ]')
        (rex,) = _rex_lines(egi)
        assert self._depth(egi, rex.id) == 1

    def test_a_constant_above_its_uses_survives_the_round_trip(self):
        """The case erasure produces, and the one the generator was losing."""
        egi = parse_egif('~[ (dog "Rex") ~[ (mammal "Rex") ] ]')
        (rex,) = _rex_lines(egi)
        hoisted = egi.with_vertex_moved_to_context(rex.id, egi.sheet)
        assert self._depth(hoisted, rex.id) == 0

        emitted = generate_egif(hoisted)
        assert nav.same_graph(hoisted, parse_egif(emitted)), (
            f"a constant seated above its uses was lost: {emitted!r}"
        )

    def test_erasing_the_edge_that_held_a_constant_out_still_round_trips(self):
        """Erasure is what strands a line above its uses.

        Rex sits on the sheet, the least common area of ``(dog "Rex")`` there
        and ``(mammal "Rex")`` in the cut. Erase the sheet-level relation — a
        positive area, so ERA is licensed — and Rex is left on the sheet with
        its only remaining use one cut down.
        """
        egi = parse_egif('(dog "Rex") ~[ (mammal "Rex") ]')
        (edge,) = [
            e for e in nav.child_edges(egi, egi.sheet) if egi.rel[e] == "dog"
        ]
        erased = apply_rule("ERA", egi, selection=[edge])
        (rex,) = _rex_lines(erased)
        assert self._depth(erased, rex.id) == 0, "fixture no longer strands the line"

        emitted = generate_egif(erased)
        assert nav.same_graph(erased, parse_egif(emitted)), (
            f"a stranded constant was lost on the way out: {emitted!r}"
        )
