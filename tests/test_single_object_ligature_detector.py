"""Single-object ligatures — Dau Definition 16.8 (p.180), pinned.

Written 2026-09-21 to retire `single_object_ligature_detector.py` from the
calculus map's `UNATTESTED` set. Like `hierarchical_index.py` it was declared
unattested rather than quietly assumed: reached only transitively, so its code
ran and its contract was pinned by nothing.

**Definition 16.8, verbatim (p.180).** Let (W, F) be a ligature of the EGI
G := (V, E, ν, ⊤, Cut, area, κ). It is a *single-object ligature* iff

  1. there are no (not necessarily different) w₁, w₂ ∈ W and an identity-link
     f ∈ F with w₁ f w₂, f < w₁ and f < w₂;
  2. there are no w₁, w₂, w ∈ W and f₁, f₂ ∈ F with w₁ ≠ w₂, w₁ f₁ w f₂ w₂,
     w < w₁ and w < w₂; and
  3. there are no w₁, w₂ ∈ W which are part of a cycle in (W, F) and for which
     we have w₂ < w₁.

Dau's gloss, same page: "this network crosses each cut-line almost once if and
only if the ligature is a single-object ligature", and on the third condition —
"A single-object ligature still may contain cycles, as long as all vertices and
edges of a cycle are placed in the area of a single context." That sentence is
why `test_a_cycle_inside_one_context_is_accepted` exists: the naive reading
("no cycles") is wrong, and is what a reimplementation would most likely get
wrong.

**`<` is the context tree's partial order, not a depth comparison.** Two areas in
different branches are *incomparable*, not ordered by which is deeper. The
implementation gets this right (`_is_context_deeper` walks parents); the test
that would catch someone "simplifying" it into `level_a > level_b` is
`test_incomparable_contexts_are_not_ordered`.

**Scope, stated honestly.** This module is *not* load-bearing, unlike
`hierarchical_index`. Its one caller is `chapter17_soundness_evaluation
._all_ligatures_single_object`, and nothing in the production path constructs a
`Chapter17SoundnessEvaluator`. A wrong answer here does not corrupt a graph; it
makes one evaluator layer report the wrong verdict, and nothing acts on it. That
is the reason its known defects below are *recorded* rather than repaired — but
it is not a reason to leave the definition unpinned, because the day something
reads this layer, Def 16.8 is what it will be trusting.

**Assertion style, and why.** `violation_reasons` and `cycles` are built by
iterating a `set` of vertex ids, so their order — and on some fixtures their
length — follows Python's per-process string hashing. The verdict is what this
module is *for*; the message list is diagnostics. So these tests assert the
boolean and `any("condition N" in …)`, never a count, never exact text, never
`cycles`. A test that pinned those would flake across processes, and a flaky
test gets deleted rather than read.

A separate file from `test_chapter16_17_ligature_soundness_simplified.py`
deliberately: eight of that file's tests are in `tests/admission_ledger.json`
(they cannot fail), and `test_calculus_map.test_no_attesting_suite_is_itself
_inadmissible` matches on file name, so naming it as an attestation would — and
should — fail the gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from single_object_ligature_detector import (
    LigatureAnalysis,
    SingleObjectLigatureDetector,
)

from calculus_enum import build


def _verdict(graph, vertices):
    return SingleObjectLigatureDetector(egi=graph).is_single_object_ligature(list(vertices))


def _cites(violations, condition: str) -> bool:
    return any(condition in v.lower() for v in violations)


# --------------------------------------------------------------------------- #
# The three conditions                                                        #
# --------------------------------------------------------------------------- #


class TestDefinition168:
    def test_a_flat_ligature_is_a_single_object_ligature(self):
        """Two vertices joined by an identity edge, all in one area."""
        g = build({}, [(None, "S"), (None, "S")], [("=", (0, 1), "S")])
        assert _verdict(g, ["v1", "v2"]) == (True, [])

    def test_condition_1_an_identity_edge_deeper_than_both_endpoints(self):
        """Dau p.180, the left graph: f < w₁ and f < w₂."""
        g = build({"c": "S"}, [(None, "S"), (None, "S")], [("=", (0, 1), "c")])
        ok, violations = _verdict(g, ["v1", "v2"])
        assert ok is False
        assert _cites(violations, "condition 1")

    def test_condition_2_an_intermediate_vertex_deeper_than_its_neighbours(self):
        """Dau p.180, the right graph: w₁ f₁ w f₂ w₂ with w < w₁ and w < w₂.

        Def 12.5 forces the two identity edges into the cut as well: an edge may
        be deeper than its vertices, never shallower.
        """
        g = build({"c": "S"},
                  [(None, "S"), (None, "S"), (None, "c")],
                  [("=", (0, 2), "c"), ("=", (2, 1), "c")])
        ok, violations = _verdict(g, ["v1", "v2", "v3"])
        assert ok is False
        assert _cites(violations, "condition 2")

    @pytest.mark.parametrize("n", [3, 4])
    def test_a_cycle_inside_one_context_is_accepted(self, n):
        """Dau's G₁: a cycle is fine while it lives in one context.

        The condition is about context ordering around the cycle, not about
        acyclicity. Reading condition 3 as "no cycles" is the likely error, and
        this is what catches it.
        """
        verts = [(None, "S")] * n
        edges = [("=", (i, (i + 1) % n), "S") for i in range(n)]
        g = build({}, verts, edges)
        assert _verdict(g, [f"v{i + 1}" for i in range(n)]) == (True, [])

    def test_condition_3_a_cycle_with_a_vertex_strictly_deeper(self):
        """Dau's G₂: two cycle vertices ordered by `<`.

        Not isolable — this shape also trips conditions 1 and 2 — so the
        assertion is that condition 3 is *among* the reasons, not that it is
        the only one.
        """
        g = build({"c": "S"},
                  [(None, "S"), (None, "S"), (None, "c")],
                  [("=", (0, 1), "S"), ("=", (1, 2), "c"), ("=", (2, 0), "c")])
        ok, violations = _verdict(g, ["v1", "v2", "v3"])
        assert ok is False
        assert _cites(violations, "condition 3")

    def test_incomparable_contexts_are_not_ordered(self):
        """`<` is the context tree, not the depth number.

        `v3` sits in `cA` (level 1) and `v4` in `cB1` (level 2), in different
        branches — neither encloses the other, so no condition-3 violation may
        name that pair, however different their depths. A `_is_context_deeper`
        rewritten as `level(a) > level(b)` would report one, and this is the
        only test in the repository that would notice.

        Deliberately no assertion on how many messages there are or which other
        pairs appear: those follow set-iteration order. The *absence* of this
        pair is a correctness property and is stable.
        """
        g = build({"cA": "S", "cB": "S", "cB1": "cB"},
                  [(None, "S"), (None, "S"), (None, "cA"), (None, "cB1")],
                  [("=", (0, 2), "cA"), ("=", (2, 1), "cA"),
                   ("=", (1, 3), "cB1"), ("=", (3, 0), "cB1")])
        analysis = SingleObjectLigatureDetector(egi=g)._analyze_ligature_impl(
            g, {"v1", "v2", "v3", "v4"})

        assert isinstance(analysis, LigatureAnalysis)
        assert analysis.is_single_object is False
        reasons = [r for r in analysis.violation_reasons if "condition 3" in r]
        assert reasons, "expected at least one condition-3 reason on this cycle"
        assert not any("v3, v4" in r or "v4, v3" in r for r in reasons), (
            "v3 (in cA) and v4 (in cB1) are in different branches and are "
            f"incomparable; neither is `<` the other. Got: {reasons}")


class TestWhatCountsAsAnIdentityLink:
    """F is the identity links — `rel[e] == "=" ` and binary. Nothing else."""

    def test_an_ordinary_relation_is_not_an_identity_link(self):
        g = build({}, [(None, "S"), (None, "S")], [("Loves", (0, 1), "S")])
        analysis = SingleObjectLigatureDetector(egi=g)._analyze_ligature_impl(
            g, {"v1", "v2"})
        assert analysis.identity_edges == set()
        assert analysis.is_single_object is True

    def test_an_ordinary_relation_deeper_than_its_vertices_is_not_a_violation(self):
        """The condition-1 shape, with a non-identity edge: must be accepted.

        Guards against a rewrite that checks edge depth before checking κ.
        """
        g = build({"c": "S"}, [(None, "S"), (None, "S")], [("Loves", (0, 1), "c")])
        assert _verdict(g, ["v1", "v2"]) == (True, [])


class TestRefusals:
    def test_analysis_without_an_egi_is_refused(self):
        detector = SingleObjectLigatureDetector()
        with pytest.raises(ValueError, match="EGI must be set"):
            detector.is_single_object_ligature(["v1"])
        with pytest.raises(ValueError, match="EGI must be set"):
            detector.separate_into_single_object_components(["v1"])


# --------------------------------------------------------------------------- #
# Recorded, not repaired                                                      #
# --------------------------------------------------------------------------- #


class TestKnownGapsAreRecorded:
    """Three gaps, pinned as current behaviour so they are written down.

    None is repaired here. This module is consulted by one evaluator layer that
    no production path calls, so a fix has no beneficiary today and some risk;
    what costs nothing is saying exactly what it does. Each of these is a real
    departure from Def 16.8 or from ordinary robustness, and each is queued in
    `tasks/todo.md`. If one is fixed, the test says so by failing.
    """

    def test_parallel_identity_edges_are_invisible_to_cycle_detection(self):
        """Two distinct `=` edges between one pair *are* a cycle in (W, F).

        `_find_ligature_cycles` builds adjacency as a `set`, so the second edge
        collapses onto the first and the `neighbor == parent` guard skips it.
        """
        g = build({}, [(None, "S"), (None, "S")],
                  [("=", (0, 1), "S"), ("=", (0, 1), "S")])
        analysis = SingleObjectLigatureDetector(egi=g)._analyze_ligature_impl(
            g, {"v1", "v2"})
        assert len(analysis.identity_edges) == 2, "both edges are identity links"
        assert analysis.cycles == [], (
            "recorded gap: adjacency is a set, so parallel identity edges do "
            "not read as a cycle")

    def test_an_unknown_vertex_id_passes_silently(self):
        """No check that W ⊆ V. An empty ligature passes too."""
        g = build({}, [(None, "S"), (None, "S")], [("=", (0, 1), "S")])
        assert _verdict(g, ["not-a-vertex"]) == (True, [])
        assert _verdict(g, []) == (True, [])

    def test_separating_into_components_is_still_a_stub(self):
        """`separate_into_single_object_components` returns one singleton per
        vertex whatever the graph — the source says `# For now`. It has no
        caller in `src/`. Pinned as a stub so implementing it is visible.
        """
        g = build({}, [(None, "S")] * 3,
                  [("=", (0, 1), "S"), ("=", (1, 2), "S")])
        detector = SingleObjectLigatureDetector(egi=g)
        assert detector.separate_into_single_object_components(
            ["v1", "v2", "v3"]) == [["v1"], ["v2"], ["v3"]]
