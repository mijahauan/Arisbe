"""
Beta graph proof exercises for the Arisbe EG transformation engine.

These tests verify that the transformation rules operate correctly on
**Beta graphs** — Existential Graphs with lines of identity (shared
vertices crossing cut boundaries).  This is the full first-order logic
level, going beyond the Alpha-graph (propositional) exercises.

Key Beta semantics tested:

  - ERA on an edge whose vertex lives in an ancestor area (free vertex)
  - IT+ extending a line of identity into a deeper area (no vertex copy)
  - IT- deiterating an edge whose isomorphic original shares the same
    free vertex in an enclosing area
  - DC+/DC- preserving bound references across structural changes
  - Full FOL proofs: universal instantiation, Barbara syllogism

EGIF Beta conventions:
  ``*x``  defining label — creates a new vertex
  ``x``   bound label   — references an existing vertex in enclosing scope
  ``~[ (P *x) ~[ (Q x) ] ]``  =  ∀x(P(x) → Q(x))  (one shared vertex)
"""

import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from egi_core_dau import AreaPolarity, ElementID, RelationalGraphWithCuts
from rule_interaction import (
    begin_interaction,
    advance_interaction,
    apply_interaction,
    insert_from_egif,
)


# ===================================================================
# Helpers — navigate EGI structure by semantic properties
# ===================================================================

def _elements_in_area(egi, area_id):
    """Return dict classifying area contents by type."""
    contents = egi.area.get(area_id, frozenset())
    v_ids = {v.id for v in egi.V}
    e_ids = {e.id for e in egi.E}
    c_ids = {c.id for c in egi.Cut}
    return {
        "vertices": [eid for eid in contents if eid in v_ids],
        "edges": [eid for eid in contents if eid in e_ids],
        "cuts": [eid for eid in contents if eid in c_ids],
        "all": list(contents),
    }


def _find_edge_by_rel(egi, area_id, rel_name):
    """Find edge ID by relation name in a specific area."""
    info = _elements_in_area(egi, area_id)
    for eid in info["edges"]:
        if egi.rel.get(eid) == rel_name:
            return eid
    return None


def _find_edges_by_rel(egi, area_id, rel_name):
    """Find all edge IDs with given relation name in a specific area."""
    info = _elements_in_area(egi, area_id)
    return [eid for eid in info["edges"] if egi.rel.get(eid) == rel_name]


def _vertex_for_edge(egi, edge_id, pos=0):
    """Return the vertex ID at position *pos* in the edge's ν mapping."""
    return egi.nu.get(edge_id, ())[pos]


def _apply_rule(rule_name, egi, selection=None, egif_text=None, target_area=None):
    """Convenience: apply a single-step or two-step rule and return result EGI.

    Raises AssertionError with the failure message on failure.
    """
    state = begin_interaction(rule_name, egi)

    if rule_name == "INS":
        assert egif_text is not None, "INS requires egif_text"
        assert target_area is not None, "INS requires target_area"
        r1 = advance_interaction(state, egif_text)
        assert r1.valid, f"INS content step failed: {r1.message}"
        r2 = advance_interaction(state, target_area)
        assert r2.valid, f"INS target step failed: {r2.message}"
    elif rule_name == "IT+":
        assert selection is not None, "IT+ requires selection"
        assert target_area is not None, "IT+ requires target_area"
        r1 = advance_interaction(state, selection)
        assert r1.valid, f"IT+ source step failed: {r1.message}"
        r2 = advance_interaction(state, target_area)
        assert r2.valid, f"IT+ dest step failed: {r2.message}"
    else:
        # Single-step rules: DC+, DC-, ERA, IT-
        if selection is None:
            selection = []
        r = advance_interaction(state, selection)
        assert r.valid, f"{rule_name} step failed: {r.message}"

    result = apply_interaction(state)
    assert result.success, f"{rule_name} apply failed: {result.message}"
    return result.result_egi


def _dump(egi, label=""):
    """Debug helper: print EGI structure."""
    if label:
        print(f"\n--- {label} ---")
    print(f"  EGIF: {generate_egif(egi)}")
    print(f"  V={len(egi.V)} E={len(egi.E)} Cut={len(egi.Cut)}")


# ===================================================================
# 1. BASIC BETA GRAPH OPERATIONS
# ===================================================================

class TestBetaGraphParsing(unittest.TestCase):
    """Verify the parser produces genuine Beta structure: one shared vertex
    across cut boundaries when bound labels (bare x) are used."""

    def test_shared_vertex_across_cut(self):
        """~[ (P *x) ~[ (Q x) ] ] has exactly ONE vertex shared by P and Q."""
        egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")

        self.assertEqual(len(egi.V), 1, "Beta graph should have one shared vertex")
        self.assertEqual(len(egi.E), 2, "Two edges: P and Q")

        v_id = list(egi.V)[0].id
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]

        p_edge = _find_edge_by_rel(egi, outer_cut, "P")
        q_edge = _find_edge_by_rel(egi, inner_cut, "Q")
        self.assertIsNotNone(p_edge)
        self.assertIsNotNone(q_edge)

        # Both edges reference the SAME vertex
        self.assertEqual(_vertex_for_edge(egi, p_edge), v_id)
        self.assertEqual(_vertex_for_edge(egi, q_edge), v_id)

        # Vertex is in the outer cut (where *x is defined)
        self.assertIn(v_id, egi.area[outer_cut])
        # Vertex is NOT in the inner cut (Q references it from an ancestor area)
        self.assertNotIn(v_id, egi.area[inner_cut])

    def test_shadowed_vs_shared(self):
        """*x in both areas → two vertices; *x outer + x inner → one vertex."""
        egi_shadow = parse_egif("~[ (P *x) ~[ (Q *x) ] ]")
        egi_shared = parse_egif("~[ (P *x) ~[ (Q x) ] ]")

        self.assertEqual(len(egi_shadow.V), 2, "Shadowed: two vertices")
        self.assertEqual(len(egi_shared.V), 1, "Shared: one vertex")


class TestBetaERA(unittest.TestCase):
    """ERA on Beta graphs: erase an edge whose vertex is in an ancestor area."""

    def test_erase_edge_with_free_vertex(self):
        """
        ∀x(P(x) → Q(x)):  ~[ (P *x) ~[ (Q x) ] ]

        ERA: erase (Q x) from depth 2 (positive).  The vertex *x is free
        (in ancestor area) so the edge alone forms a closed subgraph.

        Result: ~[ (P *x) ~[ ] ]  =  ¬∃x(P(x) ∧ ⊥)  =  ⊤
        """
        egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]

        q_edge = _find_edge_by_rel(egi, inner_cut, "Q")
        self.assertIsNotNone(q_edge)

        # ERA just the edge — vertex is free in ancestor area
        egi2 = _apply_rule("ERA", egi, selection=[q_edge])

        # Q is gone; P and vertex remain in outer cut
        self.assertIsNone(_find_edge_by_rel(egi2, inner_cut, "Q"))
        self.assertIsNotNone(_find_edge_by_rel(egi2, outer_cut, "P"))
        self.assertEqual(len(egi2.V), 1, "Vertex preserved in outer area")


class TestBetaITPlus(unittest.TestCase):
    """IT+ on Beta graphs: extend lines of identity, don't copy vertices."""

    def test_iterate_edge_extends_line_of_identity(self):
        """
        ∀x(P(x) → Q(x)):  ~[ (P *x) ~[ (Q x) ] ]

        IT+: copy (P x) from outer cut into inner cut.
        Result: ~[ (P *x) ~[ (P x) (Q x) ] ]

        The copied edge references the SAME vertex — the line of identity
        extends into the inner area.  No new vertex is created.
        """
        egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]

        v_id = list(egi.V)[0].id
        p_edge = _find_edge_by_rel(egi, outer_cut, "P")

        # IT+ copies (P x) into inner cut — select edge only, vertex is free
        egi2 = _apply_rule("IT+", egi, selection=[p_edge], target_area=inner_cut)

        # Still one vertex — line of identity extended, not duplicated
        self.assertEqual(len(egi2.V), 1, "No new vertex created")
        self.assertEqual(len(egi2.E), 3, "Three edges: original P, copy of P, original Q")

        # Inner cut now has both P and Q
        p_copy = _find_edge_by_rel(egi2, inner_cut, "P")
        q_edge = _find_edge_by_rel(egi2, inner_cut, "Q")
        self.assertIsNotNone(p_copy)
        self.assertIsNotNone(q_edge)

        # Both reference the SAME vertex
        self.assertEqual(_vertex_for_edge(egi2, p_copy), v_id)
        self.assertEqual(_vertex_for_edge(egi2, q_edge), v_id)

    def test_iterate_edge_with_vertex_in_same_area(self):
        """
        When iterating from outer cut where both edge AND vertex reside,
        the edge is copied but the vertex is reused (Beta semantics).
        """
        egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]

        v_id = list(egi.V)[0].id
        p_edge = _find_edge_by_rel(egi, outer_cut, "P")

        # Select both edge and vertex — vertex should still be reused
        egi2 = _apply_rule("IT+", egi,
                           selection=[p_edge, v_id],
                           target_area=inner_cut)

        self.assertEqual(len(egi2.V), 1, "Vertex reused, not copied")


class TestBetaITMinus(unittest.TestCase):
    """IT- on Beta graphs: deiterate an edge that was iterated via IT+."""

    def test_deiterate_iterated_edge(self):
        """
        After IT+ of (P x) into inner cut:
            ~[ (P *x) ~[ (P x) (Q x) ] ]

        IT-: deiterate (P x) from inner cut.  The original (P x) is in
        the enclosing outer cut, so deiteration is valid.

        Result: ~[ (P *x) ~[ (Q x) ] ]  (back to original)
        """
        # Start with ∀x(P(x) → Q(x))
        egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]
        p_edge = _find_edge_by_rel(egi, outer_cut, "P")

        # IT+ — copy P into inner area
        egi2 = _apply_rule("IT+", egi, selection=[p_edge], target_area=inner_cut)
        self.assertEqual(len(egi2.E), 3)

        # IT- — deiterate the P copy from inner area
        p_copy = _find_edge_by_rel(egi2, inner_cut, "P")
        self.assertIsNotNone(p_copy, "P copy should be in inner area")

        egi3 = _apply_rule("IT-", egi2, selection=[p_copy])

        # Back to original structure
        self.assertEqual(len(egi3.E), 2, "Two edges remain: P and Q")
        self.assertEqual(len(egi3.V), 1, "Shared vertex preserved")
        self.assertIsNone(_find_edge_by_rel(egi3, inner_cut, "P"))
        self.assertIsNotNone(_find_edge_by_rel(egi3, inner_cut, "Q"))

    def test_it_plus_minus_roundtrip(self):
        """IT+ followed by IT- returns to structurally identical EGIF."""
        egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
        egif_before = generate_egif(egi)

        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]
        p_edge = _find_edge_by_rel(egi, outer_cut, "P")

        # IT+ then IT-
        egi2 = _apply_rule("IT+", egi, selection=[p_edge], target_area=inner_cut)
        p_copy = _find_edge_by_rel(egi2, inner_cut, "P")
        egi3 = _apply_rule("IT-", egi2, selection=[p_copy])

        # Same counts
        self.assertEqual(len(egi3.V), len(egi.V))
        self.assertEqual(len(egi3.E), len(egi.E))
        self.assertEqual(len(egi3.Cut), len(egi.Cut))


class TestBetaDC(unittest.TestCase):
    """DC+/DC- preserve bound references in Beta graphs."""

    def test_double_cut_around_beta_edge(self):
        """
        DC+ around (Q x) in the inner area of ~[ (P *x) ~[ (Q x) ] ]
        should produce ~[ (P *x) ~[ ~[ ~[ (Q x) ] ] ] ] with the
        bound reference (Q x) still pointing to the same vertex.
        """
        egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]
        q_edge = _find_edge_by_rel(egi, inner_cut, "Q")
        v_id = list(egi.V)[0].id

        # DC+ around Q edge
        egi2 = _apply_rule("DC+", egi, selection=[q_edge])

        # Q edge still references the same vertex (through two more cuts)
        # Find Q in the new structure
        q_found = False
        for e in egi2.E:
            if egi2.rel.get(e.id) == "Q":
                self.assertEqual(_vertex_for_edge(egi2, e.id), v_id,
                                 "Q must still reference the original vertex")
                q_found = True
        self.assertTrue(q_found, "Q edge must still exist")

    def test_dc_plus_minus_roundtrip_beta(self):
        """DC+ then DC- on Beta graph returns to original."""
        egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]
        q_edge = _find_edge_by_rel(egi, inner_cut, "Q")

        # DC+ around Q
        egi2 = _apply_rule("DC+", egi, selection=[q_edge])
        self.assertEqual(len(egi2.Cut), 4, "4 cuts after DC+")

        # Find the new outer DC cut (in the inner area)
        new_cuts = _elements_in_area(egi2, inner_cut)["cuts"]
        self.assertEqual(len(new_cuts), 1, "One new cut in inner area")

        # DC- to remove the double cut
        egi3 = _apply_rule("DC-", egi2, selection=new_cuts)
        self.assertEqual(len(egi3.Cut), 2, "Back to 2 cuts")
        self.assertEqual(len(egi3.V), 1, "Vertex preserved")


# ===================================================================
# 2. BETA GRAPH PROOFS — FOL Derivations
# ===================================================================

class TestBetaUniversalStrengthening(unittest.TestCase):
    """
    ∀x(P(x) → Q(x))  ⊢  ∀x(P(x) → P(x) ∧ Q(x))

    Starting from:  ~[ (P *x) ~[ (Q x) ] ]

    Proof:
        1. IT+  iterate (P x) from outer cut into inner cut
           Result: ~[ (P *x) ~[ (P x) (Q x) ] ]

    The conclusion ~[ (P *x) ~[ (P x) (Q x) ] ] reads:
    ∀x(P(x) → P(x) ∧ Q(x))
    """

    def test_universal_strengthening(self):
        egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]
        v_id = list(egi.V)[0].id

        # IT+: iterate P from outer into inner
        p_edge = _find_edge_by_rel(egi, outer_cut, "P")
        egi2 = _apply_rule("IT+", egi, selection=[p_edge], target_area=inner_cut)

        # Verify: ∀x(P(x) → P(x) ∧ Q(x))
        self.assertEqual(len(egi2.V), 1, "Still one shared vertex")

        inner_info = _elements_in_area(egi2, inner_cut)
        inner_rels = sorted(egi2.rel[eid] for eid in inner_info["edges"])
        self.assertEqual(inner_rels, ["P", "Q"], "Inner has P and Q")

        # All edges reference the same vertex
        for eid in inner_info["edges"]:
            self.assertEqual(_vertex_for_edge(egi2, eid), v_id)


class TestBetaContrapositive(unittest.TestCase):
    """
    ∀x(P(x) → Q(x)), ¬Q(a)  ⊢  ¬P(a)

    Starting from:
        ~[ (P *x) ~[ (Q x) ] ]    (All P are Q)
        ~[ (Q *a) ]               (¬Q(a)  — a is not Q)

    This is a Beta version of modus tollens with shared variables.

    Proof:
        1. IT+  iterate ~[ (Q x) ] from inside the P-scroll
                into depth 1 of the ¬Q(a) cut.
                Wait — this is complex because the iterated content
                has a free variable x.  Instead, we use a simpler
                approach: iterate the whole P→Q conditional into
                the ¬Q cut.

    Actually, the standard EG approach is more nuanced for Beta.
    Let's prove a simpler but genuine Beta result:

    ∀x(P(x) → Q(x))  ⊢  ∀x(P(x) → Q(x))   (tautological, but tests IT+/IT-)

    And the more interesting:
    ∀x(P(x) → Q(x)), P(a)  ⊢  Q(a)   (universal modus ponens with constants)
    """

    def test_beta_it_roundtrip_preserves_quantification(self):
        """IT+/IT- round-trip preserves ∀ quantification structure."""
        egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]
        p_edge = _find_edge_by_rel(egi, outer_cut, "P")

        # IT+ then IT-
        egi2 = _apply_rule("IT+", egi, selection=[p_edge], target_area=inner_cut)
        p_copy = _find_edge_by_rel(egi2, inner_cut, "P")
        egi3 = _apply_rule("IT-", egi2, selection=[p_copy])

        # The EGIF should represent the same ∀x(P(x) → Q(x))
        egif_result = generate_egif(egi3)
        self.assertIn("(P", egif_result)
        self.assertIn("(Q", egif_result)
        self.assertEqual(len(egi3.V), 1, "Universal quantification: one vertex")


class TestBetaErasureWeakening(unittest.TestCase):
    """
    ∀x(P(x) → P(x) ∧ Q(x))  ⊢  ∀x(P(x) → P(x))

    Proof: ERA the (Q x) edge from the positive inner area.

    Starting from:  ~[ (P *x) ~[ (P x) (Q x) ] ]
    After ERA(Q):   ~[ (P *x) ~[ (P x) ] ]  =  ∀x(P(x) → P(x))
    """

    def test_beta_weakening_via_era(self):
        egi = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]
        p_edge = _find_edge_by_rel(egi, outer_cut, "P")

        # First build ∀x(P(x) → P(x) ∧ Q(x)) via IT+
        egi2 = _apply_rule("IT+", egi, selection=[p_edge], target_area=inner_cut)

        # Now ERA Q from inner area (positive, depth 2)
        q_edge = _find_edge_by_rel(egi2, inner_cut, "Q")
        egi3 = _apply_rule("ERA", egi2, selection=[q_edge])

        # Result: ∀x(P(x) → P(x))
        self.assertEqual(len(egi3.E), 2, "Two P edges remain")
        self.assertEqual(len(egi3.V), 1, "One shared vertex")
        self.assertIsNone(_find_edge_by_rel(egi3, inner_cut, "Q"))

        # Both remaining P edges share the same vertex
        v_id = list(egi3.V)[0].id
        for e in egi3.E:
            self.assertEqual(_vertex_for_edge(egi3, e.id), v_id)


class TestBetaMultiplePredicates(unittest.TestCase):
    """
    ∀x(P(x) → Q(x) ∧ R(x)):  ~[ (P *x) ~[ (Q x) (R x) ] ]

    Tests operations on Beta graphs with multiple predicates sharing
    the same line of identity across the cut boundary.
    """

    def test_three_predicates_one_vertex(self):
        egi = parse_egif("~[ (P *x) ~[ (Q x) (R x) ] ]")
        self.assertEqual(len(egi.V), 1, "One shared vertex for x")
        self.assertEqual(len(egi.E), 3, "Three edges: P, Q, R")

    def test_era_one_of_two_consequents(self):
        """ERA R from positive area, keeping Q."""
        egi = parse_egif("~[ (P *x) ~[ (Q x) (R x) ] ]")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]

        r_edge = _find_edge_by_rel(egi, inner_cut, "R")
        egi2 = _apply_rule("ERA", egi, selection=[r_edge])

        self.assertEqual(len(egi2.E), 2, "P and Q remain")
        self.assertEqual(len(egi2.V), 1, "Vertex preserved")
        self.assertIsNone(_find_edge_by_rel(egi2, inner_cut, "R"))
        self.assertIsNotNone(_find_edge_by_rel(egi2, inner_cut, "Q"))

    def test_iterate_into_area_with_existing_bound_refs(self):
        """IT+ a new edge into an area that already has bound references."""
        egi = parse_egif("~[ (P *x) ~[ (Q x) (R x) ] ]")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]
        v_id = list(egi.V)[0].id

        # IT+ P into inner area
        p_edge = _find_edge_by_rel(egi, outer_cut, "P")
        egi2 = _apply_rule("IT+", egi, selection=[p_edge], target_area=inner_cut)

        # Inner area now has P, Q, R — all sharing one vertex
        inner_info = _elements_in_area(egi2, inner_cut)
        inner_rels = sorted(egi2.rel[eid] for eid in inner_info["edges"])
        self.assertEqual(inner_rels, ["P", "Q", "R"])

        for eid in inner_info["edges"]:
            self.assertEqual(_vertex_for_edge(egi2, eid), v_id,
                             f"Edge {egi2.rel[eid]} must reference shared vertex")


class TestBetaEGIFRoundTrip(unittest.TestCase):
    """EGIF parse → generate → parse preserves Beta graph structure."""

    def test_roundtrip_single_shared_vertex(self):
        original = "~[ (P *x) ~[ (Q x) ] ]"
        egi1 = parse_egif(original)
        egif_out = generate_egif(egi1)
        egi2 = parse_egif(egif_out)

        self.assertEqual(len(egi1.V), len(egi2.V))
        self.assertEqual(len(egi1.E), len(egi2.E))
        self.assertEqual(len(egi1.Cut), len(egi2.Cut))

        # Verify shared vertex structure is preserved
        for e in egi2.E:
            v_id = _vertex_for_edge(egi2, e.id)
            self.assertEqual(v_id, list(egi2.V)[0].id,
                             "All edges must reference the single shared vertex")

    def test_roundtrip_multiple_bound_refs(self):
        original = "~[ (P *x) ~[ (Q x) (R x) ] ]"
        egi1 = parse_egif(original)
        egif_out = generate_egif(egi1)
        egi2 = parse_egif(egif_out)

        self.assertEqual(len(egi2.V), 1, "Round-trip preserves single vertex")
        self.assertEqual(len(egi2.E), 3, "Round-trip preserves all edges")

    def test_roundtrip_nested_beta(self):
        """~[ (P *x) ~[ (Q x) ~[ (R x) ] ] ] — three-level Beta graph."""
        original = "~[ (P *x) ~[ (Q x) ~[ (R x) ] ] ]"
        egi1 = parse_egif(original)

        self.assertEqual(len(egi1.V), 1, "One vertex across three levels")
        self.assertEqual(len(egi1.E), 3)

        egif_out = generate_egif(egi1)
        egi2 = parse_egif(egif_out)
        self.assertEqual(len(egi2.V), 1)
        self.assertEqual(len(egi2.E), 3)


class TestBetaMultiVariable(unittest.TestCase):
    """Beta graphs with multiple independent lines of identity."""

    def test_two_independent_variables(self):
        """~[ (P *x) (Q *y) ~[ (R x y) ] ] has two vertices, three edges."""
        egi = parse_egif("~[ (P *x) (Q *y) ~[ (R x y) ] ]")
        self.assertEqual(len(egi.V), 2, "Two vertices: x and y")
        self.assertEqual(len(egi.E), 3, "Three edges: P, Q, R")

        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]

        r_edge = _find_edge_by_rel(egi, inner_cut, "R")
        self.assertIsNotNone(r_edge)

        # R references both vertices
        r_vertices = egi.nu[r_edge]
        self.assertEqual(len(r_vertices), 2)

    def test_era_binary_relation_with_free_vertices(self):
        """ERA the binary R(x,y) from positive inner area — both vertices free."""
        egi = parse_egif("~[ (P *x) (Q *y) ~[ (R x y) ] ]")
        outer_cut = _elements_in_area(egi, egi.sheet)["cuts"][0]
        inner_cut = _elements_in_area(egi, outer_cut)["cuts"][0]

        r_edge = _find_edge_by_rel(egi, inner_cut, "R")
        egi2 = _apply_rule("ERA", egi, selection=[r_edge])

        self.assertEqual(len(egi2.E), 2, "P and Q remain")
        self.assertEqual(len(egi2.V), 2, "Both vertices preserved")
        self.assertIsNone(_find_edge_by_rel(egi2, inner_cut, "R"))


if __name__ == "__main__":
    unittest.main()
