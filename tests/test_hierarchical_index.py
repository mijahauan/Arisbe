"""The nesting index — the polarity oracle the whole rule engine reads.

Written 2026-09-21 to retire `hierarchical_index.py` from the calculus map's
`UNATTESTED` set. It was declared unattested rather than quietly assumed: it is
reached only transitively, so its code ran on every EGI ever constructed and its
contract was pinned by nothing.

**It is load-bearing for soundness, not a performance index.** Every EGI builds
one in `__post_init__` (`egi_core_dau.py:154-166`), before Def 12.5 validation.
`egi_core_dau.area_polarity` reads `get_nesting_level` and returns POSITIVE iff
the level is even (Dau Def 12.4, evenly/oddly enclosed) — and that is the sole
polarity oracle for `formal_transformation_rules` (INS demands NEGATIVE, ERA
demands POSITIVE), `rule_interaction` (nine sites), `endoporeutic_game`,
`eg_navigation` and `egi_diff`. `area_polarity` has no cross-check: its fallback
fires only when the level is `None`, never when it is *wrong*. Measured before
this file was written — bumping one `NestingInfo.nesting_level` by 1 on
`(P *x) ~[ (Q x) ]` turns the cut from `(NEGATIVE, 1)` into `(POSITIVE, 2)`, and
ERA and INS licensing invert in silence. A one-level error is a soundness error.

The oracle here is `tests/calculus_enum`'s `ancestors` / `all_areas`, which walk
`egi.area` directly and never consult the index — the same engine-free discipline
`calculus_rules.legal()` keeps.

What is deliberately *not* asserted: the module's dead half. `get_polarity`,
`get_parent`, `get_children`, `get_areas_at_level`, `get_positive_areas`,
`get_negative_areas`, `remove_area`, `validate_containment` and `get_statistics`
have no caller in `src/`. Three of them are known-defective (see
`TestTheDeadHalfIsRecordedNotTrusted`); they are pinned as *recorded behaviour*
so the module's state is written down rather than implied, and so that
implementing one is visible as a change.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from frozendict import frozendict

from hierarchical_index import HierarchicalIndex, NestingInfo

from calculus_enum import DEFAULT_BOUNDS, all_areas, ancestors, build, tier_a, tier_b


# --------------------------------------------------------------------------- #
# 1. The contract, against an index-free oracle                               #
# --------------------------------------------------------------------------- #


class TestTheIndexAgreesWithTheAreaMap:
    """For every area: the level is its depth, and the ancestors are its chain."""

    def test_levels_and_ancestors_on_a_hand_built_nest(self):
        g = build({"c1": "S", "c2": "c1"}, [(None, "c2")], [("P", (0,), "c2")])
        hi = g.hierarchical_index

        assert isinstance(hi, HierarchicalIndex)
        assert hi.sheet_id == g.sheet
        assert {a: hi.get_nesting_level(a) for a in all_areas(g)} == {
            "S": 0, "c1": 1, "c2": 2}
        assert hi.get_ancestors("c2") == ["c2", "c1", "S"]
        assert hi.get_ancestors(g.sheet) == ["S"]
        assert hi.max_nesting_level == 2

    def test_every_area_is_indexed_and_no_area_is_invented(self):
        """A missing area reads as `None`, which `area_polarity` silently
        treats as the sheet — so a gap here is a polarity error, not a KeyError."""
        for name, g in _all_graphs():
            assert set(g.hierarchical_index.areas) == set(all_areas(g)), name

    def test_levels_agree_with_the_area_walk_corpus_wide(self):
        checked = 0
        for name, g in _all_graphs():
            hi = g.hierarchical_index
            for area in all_areas(g):
                expected = len(ancestors(g, area)) - 1
                assert hi.get_nesting_level(area) == expected, (
                    f"{name}/{area}: index says {hi.get_nesting_level(area)}, "
                    f"the area map says {expected}")
                checked += 1
        assert checked > 1000, f"only {checked} areas checked — the tiers shrank"

    def test_ancestors_agree_with_the_area_walk_corpus_wide(self):
        for name, g in _all_graphs():
            hi = g.hierarchical_index
            for area in all_areas(g):
                assert hi.get_ancestors(area) == ancestors(g, area), f"{name}/{area}"

    def test_the_chain_is_innermost_first_and_ends_at_the_sheet(self):
        g = build({"c1": "S", "c2": "c1", "c3": "c2"}, [], [])
        chain = g.hierarchical_index.get_ancestors("c3")
        assert chain[0] == "c3" and chain[-1] == g.sheet
        assert chain == ["c3", "c2", "c1", "S"]


class TestPolarityIsDefinition124:
    """Even depth is positive, odd is negative — and the two copies agree.

    The convention is written twice: `NestingInfo.polarity` here, and
    `egi_core_dau.area_polarity` recomputing `level % 2` itself. Nothing held
    them in step until this test.
    """

    @pytest.mark.parametrize("level,expected", [(0, "positive"), (1, "negative"),
                                                (2, "positive"), (3, "negative")])
    def test_nesting_info_polarity(self, level, expected):
        assert NestingInfo("a", level, None, set()).polarity == expected

    def test_the_index_and_the_core_never_disagree_about_polarity(self):
        from egi_core_dau import AreaPolarity

        for name, g in _all_graphs():
            hi = g.hierarchical_index
            for area in all_areas(g):
                core, level = g.area_polarity(area)
                index = hi.areas[area].polarity
                assert level == hi.get_nesting_level(area), f"{name}/{area}"
                assert (core is AreaPolarity.POSITIVE) == (index == "positive"), (
                    f"{name}/{area}: core says {core}, index says {index}")


class TestAncestryQueries:
    """`is_ancestor` as the two live callers in `rule_interaction` need it."""

    def test_a_strict_ancestor_is_one_and_a_sibling_is_not(self):
        g = build({"c1": "S", "c2": "c1", "s1": "S"}, [], [])
        hi = g.hierarchical_index
        assert hi.is_ancestor("S", "c2") and hi.is_ancestor("c1", "c2")
        assert not hi.is_ancestor("c2", "c1"), "the relation is not symmetric"
        assert not hi.is_ancestor("s1", "c2") and not hi.is_ancestor("c2", "s1")

    def test_is_ancestor_is_reflexive_and_both_callers_compensate(self):
        """Pinned as-is, deliberately: the name says otherwise.

        `is_ancestor(a, a)` is True. Both live callers already work around it —
        `rule_interaction:789` guards IT+ with `source_area != area_id`, and
        `:891` filters self out of the IT- enclosing-area search. So "fixing" it
        would be a silent behaviour change under two rules. This pins the
        current reading so such a change breaks loudly and gets read first.
        """
        g = build({"c1": "S"}, [], [])
        assert g.hierarchical_index.is_ancestor("c1", "c1") is True

    def test_an_unknown_area_is_not_an_ancestor_of_anything(self):
        g = build({"c1": "S"}, [], [])
        hi = g.hierarchical_index
        assert not hi.is_ancestor("nope", "c1")
        assert not hi.is_ancestor("c1", "nope")
        assert hi.get_nesting_level("nope") is None


class TestBuilding:
    def test_a_parent_that_is_not_present_is_refused(self):
        hi = HierarchicalIndex()
        assert hi.add_area("S") is True
        assert hi.add_area("c1", "missing") is False
        assert "c1" not in hi.areas

    def test_a_duplicate_area_is_refused(self):
        hi = HierarchicalIndex()
        hi.add_area("S")
        assert hi.add_area("S") is False

    def test_the_parent_learns_its_child(self):
        hi = HierarchicalIndex()
        hi.add_area("S")
        hi.add_area("c1", "S")
        assert hi.areas["S"].child_areas == {"c1"}
        assert hi.areas["c1"].parent_area == "S"
        assert hi.max_nesting_level == 1


# --------------------------------------------------------------------------- #
# 2. Staleness — the invariant that is not obvious and is one refactor away    #
# --------------------------------------------------------------------------- #


class TestTheIndexIsRebuiltWheneverTheAreaMapMoves:
    """`hierarchical_index` is a dataclass *field*, so it can outlive its graph.

    `__post_init__` only builds one when the field is `None`. `dataclasses
    .replace(egi, area=...)` carries the **old** index forward and does not
    rebuild it, so the graph and its polarity oracle disagree — and nothing
    raises. `composition_ops.py:640` is the one place in `src/` that knows this
    and passes `hierarchical_index=None` explicitly.

    The `with_*` constructors are safe today because they call the constructor
    rather than `replace`. That is exactly the kind of fact a refactor erases,
    so it is pinned here.
    """

    def test_replace_without_clearing_the_index_keeps_a_stale_one(self):
        """The hazard itself, demonstrated — so the guard below means something."""
        g = build({"c1": "S", "c2": "c1"}, [], [])
        moved = dict(g.area)
        moved["c1"] = moved["c1"] - {"c2"}
        moved["S"] = moved["S"] | {"c2"}

        stale = dataclasses.replace(g, area=frozendict(moved))
        fresh = dataclasses.replace(g, area=frozendict(moved), hierarchical_index=None)

        assert stale.hierarchical_index.get_nesting_level("c2") == 2
        assert fresh.hierarchical_index.get_nesting_level("c2") == 1
        # c2 genuinely sits on the sheet now: depth 1, NEGATIVE. The stale index
        # says 2, POSITIVE — ERA would be licensed where it is not.
        assert ancestors(fresh, "c2") == ["c2", "S"]

    def test_with_cut_rebuilds(self):
        from egi_core_dau import Cut

        g = build({"c1": "S"}, [], [])
        extended = g.with_cut(Cut(id="c_new"), "c1")
        _assert_index_agrees(extended)
        assert extended.hierarchical_index.get_nesting_level("c_new") == 2

    def test_moving_a_vertex_between_contexts_rebuilds(self):
        g = build({"c1": "S"}, [(None, "S")], [])
        vid = next(iter(g.V)).id
        moved = g.with_vertex_moved_to_context(vid, "c1")
        _assert_index_agrees(moved)

    def test_without_element_rebuilds(self):
        g = build({"c1": "S", "c2": "c1"}, [], [])
        pruned = g.without_element("c2")
        _assert_index_agrees(pruned)
        assert "c2" not in pruned.hierarchical_index.areas


# --------------------------------------------------------------------------- #
# 3. The dead half — recorded, not trusted                                     #
# --------------------------------------------------------------------------- #


class TestTheDeadHalfRepaired:
    """Three of the nine uncalled methods were defective. Two are now fixed.

    The author's ruling (2026-09-24, Decision 3): repair per method rather than
    wholesale, because the three had different characters. What made these worth
    fixing though nothing calls them is that each would mislead the *first*
    caller — and `validate_containment` misleads by its name, which is the worst
    way for an uncalled method to be wrong.

    `remove_area` stays pinned below as a recorded defect: a correct version has
    to choose between re-parenting orphans and cascading the removal, and
    nothing in the codebase constrains that choice. Inventing a policy for a
    method with no caller is how you get a second landmine instead of none.
    """

    def test_get_children_hands_out_a_copy(self):
        g = build({"c1": "S"}, [], [])
        hi = g.hierarchical_index
        hi.get_children("S").add("not-an-area")
        assert "not-an-area" not in hi.areas["S"].child_areas, (
            "a caller must not be able to corrupt the index in place")
        assert hi.get_children("S") == {"c1"}

    def test_validate_containment_follows_ancestry_not_depth(self):
        g = build({"cA": "S", "cB": "S", "cB1": "cB"}, [], [])
        hi = g.hierarchical_index
        # cA is at level 1 and cB1 at level 2, but in *different* branches:
        # deeper is not contained.
        assert hi.validate_containment("cA", "cB1") is False
        assert hi.validate_containment("cB", "cB1") is True
        assert hi.validate_containment("S", "cB1") is True

    def test_validate_containment_agrees_with_is_ancestor(self):
        """The two answered different questions while sharing one vocabulary."""
        g = build({"cA": "S", "cB": "S", "cB1": "cB", "cB2": "cB1"}, [], [])
        hi = g.hierarchical_index
        areas = ["S", "cA", "cB", "cB1", "cB2"]
        for a in areas:
            for b in areas:
                expected = a != b and hi.is_ancestor(a, b)
                assert hi.validate_containment(a, b) is expected, (a, b)

    def test_an_area_does_not_contain_itself(self):
        """`is_ancestor` is reflexive and stays so — both live callers already
        compensate. Containment is the strict relation, so it must not be."""
        g = build({"c1": "S"}, [], [])
        hi = g.hierarchical_index
        assert hi.is_ancestor("c1", "c1") is True
        assert hi.validate_containment("c1", "c1") is False

    def test_nesting_info_is_hashable(self):
        """`frozen=True` around a mutable `set` is immutability in name only —
        the same finding `test_second_order_core` made about the EGI itself."""
        info = NestingInfo("a", 0, None, {"b"})
        assert hash(info) == hash(NestingInfo("a", 0, None, {"b"}))
        assert isinstance(info.child_areas, frozenset)


class TestTheDeadHalfIsRecordedNotTrusted:
    """What is still defective, pinned as current behaviour so it is written
    down. If it is ever fixed, this test says so by failing."""

    def test_remove_area_orphans_its_descendants(self):
        g = build({"c1": "S", "c2": "c1", "c3": "c2"}, [], [])
        hi = g.hierarchical_index
        assert hi.remove_area("c2") is True
        # c3 survives, still claiming a parent that is gone.
        assert hi.areas["c3"].parent_area == "c2"
        assert hi.get_ancestors("c3") == ["c3", "c2"], (
            "recorded defect: the chain no longer reaches the sheet")
        assert not hi.is_ancestor("S", "c3")


# --------------------------------------------------------------------------- #
# helpers                                                                     #
# --------------------------------------------------------------------------- #


def _all_graphs():
    """Tier A (enumerated) + tier B (the corpus as used), named for messages."""
    return list(tier_a(DEFAULT_BOUNDS).graphs) + list(tier_b().graphs)


def _assert_index_agrees(g):
    hi = g.hierarchical_index
    assert set(hi.areas) == set(all_areas(g))
    for area in all_areas(g):
        assert hi.get_nesting_level(area) == len(ancestors(g, area)) - 1, area
        assert hi.get_ancestors(area) == ancestors(g, area), area
