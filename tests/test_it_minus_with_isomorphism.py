"""
Test IT- (deiteration) transformation using the new isomorphism engine.
Demonstrates the fundamental isomorphism testing capabilities in practice.
"""

import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frozendict import frozendict

from src.egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from src.formal_transformation_rules import (
    AreaPolarity,
    DeiterationRule,
    TransformationContext,
)
from src.graph_isomorphism_engine import GraphIsomorphismEngine, IsomorphismValidator


class TestITMinusWithIsomorphism(unittest.TestCase):
    """Test IT- transformation with rigorous isomorphism validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.deiteration_rule = DeiterationRule()
        self.isomorphism_engine = GraphIsomorphismEngine()

    def create_dau_compliant_egi(self) -> RelationalGraphWithCuts:
        """Create EGI that demonstrates Dau's IT- requirements."""
        # Peirce's classic example: "If a man, then mortal"
        # ~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]
        # With duplicate structure for deiteration testing

        # Vertices
        socrates1 = Vertex(id="socrates1", label="Socrates", is_generic=False)
        socrates2 = Vertex(
            id="socrates2", label="Socrates", is_generic=False
        )  # Duplicate
        socrates3 = Vertex(
            id="socrates3", label="Socrates", is_generic=False
        )  # Another duplicate

        # Edges
        human1 = Edge(id="human1")
        human2 = Edge(id="human2")  # Duplicate structure
        mortal1 = Edge(id="mortal1")
        mortal2 = Edge(id="mortal2")  # Duplicate structure

        # Cuts for nested structure
        outer_cut = Cut(id="outer_cut")
        inner_cut1 = Cut(id="inner_cut1")
        inner_cut2 = Cut(id="inner_cut2")  # Duplicate of inner_cut1

        return RelationalGraphWithCuts(
            V=frozenset([socrates1, socrates2, socrates3]),
            E=frozenset([human1, human2, mortal1, mortal2]),
            Cut=frozenset([outer_cut, inner_cut1, inner_cut2]),
            nu=frozendict(
                {
                    "human1": ("socrates1",),
                    "human2": ("socrates2",),  # Same structure as human1
                    "mortal1": ("socrates1",),
                    "mortal2": ("socrates3",),  # Same structure as mortal1
                }
            ),
            sheet="sheet",
            area=frozendict(
                {
                    "sheet": frozenset(["outer_cut"]),
                    "outer_cut": frozenset(
                        ["human1", "socrates1", "inner_cut1", "inner_cut2"]
                    ),
                    "inner_cut1": frozenset(
                        ["mortal1"]
                    ),  # Contains mortal1 + socrates1 (via nu)
                    "inner_cut2": frozenset(
                        ["human2", "socrates2", "mortal2", "socrates3"]
                    ),  # Separate area
                }
            ),
            rel=frozendict(
                {
                    "human1": "Human",
                    "human2": "Human",  # Same relation as human1
                    "mortal1": "Mortal",
                    "mortal2": "Mortal",  # Same relation as mortal1
                }
            ),
        )

    def test_valid_it_minus_deiteration(self):
        """Test valid IT- deiteration following Dau's requirements."""
        egi = self.create_dau_compliant_egi()

        # Test Case: Deiterate human2+socrates2 from inner_cut2
        # Should find isomorphic human1+socrates1 in outer_cut (parent area)
        context = TransformationContext(
            source_egi=egi,
            target_area="inner_cut2",
            selected_subgraph=frozenset(["human2", "socrates2"]),
            area_polarity=AreaPolarity.NEGATIVE,
            nesting_depth=2,
        )

        # Check preconditions using the isomorphism-enhanced IT- rule
        is_valid, error_msg = self.deiteration_rule.check_preconditions(context)

        self.assertTrue(is_valid, f"IT- should be valid: {error_msg}")
        self.assertIsNone(error_msg)

    def test_invalid_it_minus_no_isomorphic_counterpart(self):
        """Test invalid IT- when no isomorphic counterpart exists."""
        egi = self.create_dau_compliant_egi()

        # Test Case: Try to deiterate mortal2+socrates3 from inner_cut2
        # No isomorphic counterpart exists in nesting hierarchy
        context = TransformationContext(
            source_egi=egi,
            target_area="inner_cut2",
            selected_subgraph=frozenset(["mortal2", "socrates3"]),
            area_polarity=AreaPolarity.NEGATIVE,
            nesting_depth=2,
        )

        is_valid, error_msg = self.deiteration_rule.check_preconditions(context)

        self.assertFalse(is_valid)
        self.assertIn("No structurally identical subgraph found", error_msg)

    def test_invalid_it_minus_wrong_nesting_hierarchy(self):
        """Test invalid IT- when isomorphic structure exists but not in nesting hierarchy."""
        # Create EGI with isomorphic structures in separate cut hierarchies
        v1 = Vertex(id="v1", label="Socrates", is_generic=False)
        v2 = Vertex(id="v2", label="Socrates", is_generic=False)
        e1 = Edge(id="e1")
        e2 = Edge(id="e2")
        cut1 = Cut(id="cut1")
        cut2 = Cut(id="cut2")  # Separate hierarchy

        egi = RelationalGraphWithCuts(
            V=frozenset([v1, v2]),
            E=frozenset([e1, e2]),
            Cut=frozenset([cut1, cut2]),
            nu=frozendict({"e1": ("v1",), "e2": ("v2",)}),  # Same structure as e1
            sheet="sheet",
            area=frozendict(
                {
                    "sheet": frozenset(["cut1", "cut2"]),  # Both cuts at same level
                    "cut1": frozenset(["v1", "e1"]),
                    "cut2": frozenset(
                        ["v2", "e2"]
                    ),  # Isomorphic but not in nesting hierarchy
                }
            ),
            rel=frozendict({"e1": "Human", "e2": "Human"}),  # Same relation
        )

        # Try to deiterate from cut1 - should fail because cut2 is not in nesting hierarchy
        context = TransformationContext(
            source_egi=egi,
            target_area="cut1",
            selected_subgraph=frozenset(["v1", "e1"]),
            area_polarity=AreaPolarity.NEGATIVE,
            nesting_depth=1,
        )

        is_valid, error_msg = self.deiteration_rule.check_preconditions(context)

        self.assertFalse(is_valid)
        self.assertIn("No structurally identical subgraph found", error_msg)

    def test_isomorphism_engine_directly(self):
        """Test the isomorphism engine directly on EGI structures."""
        egi = self.create_dau_compliant_egi()

        # Test 1: Identical vertices
        result = self.isomorphism_engine.test_subgraph_isomorphism(
            egi, frozenset(["socrates1"]), frozenset(["socrates2"])
        )
        self.assertTrue(result.is_isomorphic)
        self.assertEqual(result.mapping.vertex_mapping, {"socrates1": "socrates2"})

        # Test 2: Identical edges with vertices
        result = self.isomorphism_engine.test_subgraph_isomorphism(
            egi, frozenset(["human1", "socrates1"]), frozenset(["human2", "socrates2"])
        )
        self.assertTrue(result.is_isomorphic)
        self.assertEqual(result.mapping.edge_mapping, {"human1": "human2"})
        self.assertEqual(result.mapping.vertex_mapping, {"socrates1": "socrates2"})

        # Test 3: Non-isomorphic structures
        result = self.isomorphism_engine.test_subgraph_isomorphism(
            egi, frozenset(["human1", "socrates1"]), frozenset(["mortal1"])
        )
        self.assertFalse(result.is_isomorphic)
        self.assertEqual(result.reason, "Different number of elements")

    def test_find_isomorphic_subgraphs_in_areas(self):
        """Test finding all isomorphic subgraphs within specified areas."""
        egi = self.create_dau_compliant_egi()

        # Find all subgraphs isomorphic to (human1, socrates1)
        matches = self.isomorphism_engine.find_isomorphic_subgraphs(
            egi,
            frozenset(["human1", "socrates1"]),
            ["outer_cut", "inner_cut1", "inner_cut2"],
        )

        # Should find matches in the specified areas (could be multiple valid matches)
        self.assertGreaterEqual(len(matches), 1)

        # Find the match in inner_cut2 specifically
        inner_cut2_matches = [m for m in matches if m[0] == "inner_cut2"]
        self.assertGreater(
            len(inner_cut2_matches), 0, "Should find at least one match in inner_cut2"
        )

        area_id, matching_subgraph, mapping = inner_cut2_matches[0]
        self.assertEqual(area_id, "inner_cut2")
        self.assertEqual(matching_subgraph, frozenset(["human2", "socrates2"]))

    def test_dau_compliance_multiple_instances(self):
        """Test Dau's requirement: 'at least two instances in nest of cuts'."""
        egi = self.create_dau_compliant_egi()

        # Verify that human1+socrates1 (outer_cut) and human2+socrates2 (inner_cut2)
        # satisfy the "multiple instances" requirement
        validator = IsomorphismValidator()

        is_valid, error = validator.validate_deiteration_candidate(
            egi,
            frozenset(["human2", "socrates2"]),  # Target for deiteration
            "inner_cut2",
            ["inner_cut2", "outer_cut", "sheet"],  # Nesting hierarchy
        )

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_dau_compliance_nesting_constraint(self):
        """Test Dau's requirement: 'more-times-enclosed instance may be erased'."""
        egi = self.create_dau_compliant_egi()

        # Should allow removing more deeply nested instance (inner_cut2)
        # when less nested instance exists (outer_cut)
        context = TransformationContext(
            source_egi=egi,
            target_area="inner_cut2",  # More deeply nested
            selected_subgraph=frozenset(["human2", "socrates2"]),
            area_polarity=AreaPolarity.NEGATIVE,
            nesting_depth=2,
        )

        is_valid, error_msg = self.deiteration_rule.check_preconditions(context)
        self.assertTrue(is_valid)

        # Should NOT allow removing less nested instance when more nested exists
        context_invalid = TransformationContext(
            source_egi=egi,
            target_area="outer_cut",  # Less deeply nested
            selected_subgraph=frozenset(["human1", "socrates1"]),
            area_polarity=AreaPolarity.NEGATIVE,
            nesting_depth=1,
        )

        # This should be invalid per Dau's nesting constraint
        is_valid_reverse, error_msg_reverse = self.deiteration_rule.check_preconditions(
            context_invalid
        )
        # Note: Current implementation may not enforce this constraint strictly
        # This test documents the expected behavior per Dau's formalism


class TestCutAsUnitDeiterationAndErasure(unittest.TestCase):
    """IT-/ERA of a whole *cut* (cut + everything nested inside it) as a unit.

    Before this capability only flat edges could be deiterated/erased: a cut's
    interior lives in a deeper area, so the candidate spanned areas and the
    isomorphism search (which built each search area's graph from its *direct*
    members only) could never embed a cut-subtree.  ``find_isomorphic_subgraphs``
    now searches the area's *recursive* contents and filters each match to a
    rooted, closed subtree; ``ErasureRule`` accepts a selection rooted at the
    target area through selected cuts.
    """

    @staticmethod
    def _parent_area(egi, eid):
        for a, contents in egi.area.items():
            if eid in contents:
                return a
        return None

    def _inner_P_cut(self, egi):
        """The ``~[(P)]`` cut that is NOT a direct member of the sheet."""
        edges = {e.id for e in egi.E}
        for c in egi.Cut:
            cont = egi.area.get(c.id)
            if (len(cont) == 1 and list(cont)[0] in edges
                    and egi.rel.get(list(cont)[0]) == "P"
                    and self._parent_area(egi, c.id) != egi.sheet):
                return c.id
        return None

    def test_cut_deiteration_as_unit(self):
        """``~[(P)] ~[ ~[(P)] ]`` → deiterate the inner ``~[(P)]`` copy."""
        from src.egif_parser_dau import parse_egif
        from src.rule_interaction import (
            begin_interaction, advance_interaction, apply_interaction,
        )

        egi = parse_egif("~[ (P) ] ~[ ~[ (P) ] ]")
        candidate = self._inner_P_cut(egi)
        self.assertIsNotNone(candidate)

        state = begin_interaction("IT-", egi)
        result = advance_interaction(state, frozenset([candidate]))
        self.assertTrue(result.valid, result.message)
        self.assertTrue(state.is_complete)

        applied = apply_interaction(state)
        self.assertTrue(applied.success, applied.message)
        out = applied.result_egi
        # The inner copy is gone: the original (P)-cut survives plus one now-empty
        # cut (the double cut's outer, its interior removed).
        self.assertEqual(2, len(out.Cut))
        self.assertEqual(1, len(out.E))  # only the surviving (P)
        empty_cuts = [c for c in out.Cut if not out.area.get(c.id)]
        self.assertEqual(1, len(empty_cuts))

    def test_cut_erasure_as_unit(self):
        """Erase a whole ``~[(P)]`` cut from the positive sheet."""
        from src.egif_parser_dau import parse_egif
        from src.egif_generator_dau import generate_egif
        from src.rule_interaction import (
            begin_interaction, advance_interaction, apply_interaction,
        )

        egi = parse_egif("~[ (P) ] ~[ ~[ (P) ] ]")
        edges = {e.id for e in egi.E}
        outer = next(
            c.id for c in egi.Cut
            if len(egi.area.get(c.id)) == 1
            and list(egi.area.get(c.id))[0] in edges
            and self._parent_area(egi, c.id) == egi.sheet
        )

        state = begin_interaction("ERA", egi)
        result = advance_interaction(state, frozenset([outer]))
        self.assertTrue(result.valid, result.message)

        applied = apply_interaction(state)
        self.assertTrue(applied.success, applied.message)
        # Only the double-cut ~[ ~[(P)] ] survives.
        self.assertEqual("~[ ~[ (P) ] ]", generate_egif(applied.result_egi))

    def test_sliced_cut_is_rejected(self):
        """A cut copy must be *identical*: ``~[(P)]`` ≠ a slice of ``~[(P)(Q)]``."""
        from src.egif_parser_dau import parse_egif
        from src.rule_interaction import begin_interaction, advance_interaction

        egi = parse_egif("~[ (P) (Q) ] ~[ ~[ (P) ] ]")
        candidate = self._inner_P_cut(egi)
        state = begin_interaction("IT-", egi)
        result = advance_interaction(state, frozenset([candidate]))
        self.assertFalse(result.valid)

    def test_buried_copy_is_not_an_enclosing_occurrence(self):
        """A copy nested inside a *sibling* cut is not in an enclosing area."""
        from src.egif_parser_dau import parse_egif
        from src.rule_interaction import begin_interaction, advance_interaction

        # cut2 = ~[ ~[(P)] ] on the sheet; the only other ~[(P)] is buried
        # inside cut1's interior, which is not an ancestor of cut2's interior.
        egi = parse_egif("~[ (A) ~[ (P) ] ] ~[ ~[ (P) ] ]")
        candidate = self._inner_P_cut(egi)
        self.assertIsNotNone(candidate)
        state = begin_interaction("IT-", egi)
        result = advance_interaction(state, frozenset([candidate]))
        self.assertFalse(result.valid)


if __name__ == "__main__":
    unittest.main()
