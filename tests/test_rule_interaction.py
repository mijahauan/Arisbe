"""
Headless integration tests for the RuleInteraction protocol.

Tests full transform chains for all six Dau transformation rules
(DC+, DC-, ERA, INS, IT+, IT-) through the interaction protocol,
verifying that:
  1. Each rule's interaction steps validate correctly.
  2. Invalid inputs are rejected with clear messages.
  3. Applying a completed interaction produces correct EGI output.
  4. Multi-step rules (INS, IT+) enforce step ordering.
  5. Chained transformations compose correctly.
"""

import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from egi_core_dau import AreaPolarity, ElementID, RelationalGraphWithCuts
from rule_interaction import (
    ApplyResult,
    InteractionState,
    begin_interaction,
    advance_interaction,
    apply_interaction,
    get_interaction,
    insert_from_egif,
    RULE_INTERACTIONS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_areas_by_polarity(egi, polarity):
    """Return list of area IDs with the given polarity."""
    return [
        a for a in egi.area
        if egi.area_polarity(a)[0] is polarity
    ]


def _find_cuts_in_area(egi, area_id):
    """Return cut IDs that are direct contents of area_id."""
    contents = egi.area.get(area_id, frozenset())
    cut_ids = {c.id for c in egi.Cut}
    return [eid for eid in contents if eid in cut_ids]


def _find_edges_in_area(egi, area_id):
    """Return edge IDs that are direct contents of area_id."""
    contents = egi.area.get(area_id, frozenset())
    edge_ids = {e.id for e in egi.E}
    return [eid for eid in contents if eid in edge_ids]


def _elem_count(egi):
    return len(egi.V) + len(egi.E) + len(egi.Cut)


# ===================================================================
# DC+ Tests
# ===================================================================

class TestDCPlusInteraction(unittest.TestCase):
    """DC+ (Double Cut Insertion) via interaction protocol."""

    def test_empty_double_cut_on_sheet(self):
        """Insert empty double cut on empty sheet."""
        egi = parse_egif("")  # empty sheet
        state = begin_interaction("DC+", egi)
        # Advance with empty selection (optional step)
        r = advance_interaction(state, [])
        self.assertTrue(r.valid)
        self.assertTrue(state.is_complete)

        result = apply_interaction(state)
        self.assertTrue(result.success, result.message)
        # Should have 2 new cuts, nothing else
        self.assertEqual(len(result.result_egi.Cut), 2)
        self.assertEqual(len(result.result_egi.V), 0)
        self.assertEqual(len(result.result_egi.E), 0)

    def test_enclose_elements(self):
        """Enclose existing elements in a double cut."""
        egi = parse_egif("(Human *x)")
        sheet_contents = list(egi.area[egi.sheet])

        state = begin_interaction("DC+", egi)
        r = advance_interaction(state, sheet_contents)
        self.assertTrue(r.valid, r.message)

        result = apply_interaction(state)
        self.assertTrue(result.success, result.message)
        # Original elements + 2 new cuts
        self.assertEqual(len(result.result_egi.Cut), 2)
        self.assertEqual(len(result.result_egi.V), 1)
        self.assertEqual(len(result.result_egi.E), 1)
        # Sheet should now contain only the outer cut
        sheet_contents_after = result.result_egi.area[result.result_egi.sheet]
        self.assertEqual(len(sheet_contents_after), 1)

    def test_elements_in_different_areas_rejected(self):
        """Elements from different areas cannot be selected together."""
        egi = parse_egif("(Cat *x) ~[ (Dog *y) ]")
        # Get an element from the sheet and one from inside the cut
        cut_ids = {c.id for c in egi.Cut}
        sheet_elems = [e for e in egi.area[egi.sheet] if e not in cut_ids]
        inner_cut = next(c.id for c in egi.Cut)
        inner_elems = list(egi.area.get(inner_cut, frozenset()))

        if sheet_elems and inner_elems:
            mixed = [sheet_elems[0], inner_elems[0]]
            state = begin_interaction("DC+", egi)
            r = advance_interaction(state, mixed)
            self.assertFalse(r.valid)
            self.assertIn("same area", r.message)


# ===================================================================
# DC- Tests
# ===================================================================

class TestDCMinusInteraction(unittest.TestCase):
    """DC- (Double Cut Erasure) via interaction protocol."""

    def test_erase_double_cut(self):
        """Insert then erase a double cut — round trip."""
        egi = parse_egif("(Human *x)")

        # First, insert double cut
        state1 = begin_interaction("DC+", egi)
        advance_interaction(state1, list(egi.area[egi.sheet]))
        r1 = apply_interaction(state1)
        self.assertTrue(r1.success)
        egi2 = r1.result_egi

        # Find the outer cut (the one on the sheet)
        outer_cut = list(egi2.area[egi2.sheet])
        self.assertEqual(len(outer_cut), 1)
        outer_cut_id = outer_cut[0]

        # Now erase the double cut
        state2 = begin_interaction("DC-", egi2)
        r = advance_interaction(state2, [outer_cut_id])
        self.assertTrue(r.valid, r.message)

        result = apply_interaction(state2)
        self.assertTrue(result.success, result.message)
        # Should be back to original structure: no cuts
        self.assertEqual(len(result.result_egi.Cut), 0)
        self.assertEqual(len(result.result_egi.V), 1)
        self.assertEqual(len(result.result_egi.E), 1)

    def test_non_cut_rejected(self):
        """Selecting a non-cut element is rejected."""
        egi = parse_egif("(Human *x)")
        vertex_id = next(v.id for v in egi.V)

        state = begin_interaction("DC-", egi)
        r = advance_interaction(state, [vertex_id])
        self.assertFalse(r.valid)
        self.assertIn("not a cut", r.message)

    def test_single_cut_rejected(self):
        """A single cut (not a double-cut pair) is rejected."""
        egi = parse_egif("~[ (Human *x) ]")
        cut_id = next(c.id for c in egi.Cut)

        state = begin_interaction("DC-", egi)
        r = advance_interaction(state, [cut_id])
        self.assertFalse(r.valid)
        # The inner contents aren't a single cut, so validation fails

    def test_must_select_exactly_one(self):
        """Must select exactly one cut."""
        egi = parse_egif("~[ ~[ ] ]")
        state = begin_interaction("DC-", egi)
        r = advance_interaction(state, [])
        self.assertFalse(r.valid)
        self.assertIn("exactly one", r.message)


# ===================================================================
# ERA Tests
# ===================================================================

class TestERAInteraction(unittest.TestCase):
    """ERA (Erasure) via interaction protocol."""

    def test_erase_from_positive_area(self):
        """Erase element from sheet (positive area)."""
        egi = parse_egif("(Human *x) (Cat *y)")
        # Pick one edge + its vertex to erase
        # Find an edge and its connected vertex
        edge_id = next(iter(e.id for e in egi.E))
        vertex_ids = list(egi.nu[edge_id])

        state = begin_interaction("ERA", egi)
        r = advance_interaction(state, [edge_id] + vertex_ids)
        self.assertTrue(r.valid, r.message)

        result = apply_interaction(state)
        self.assertTrue(result.success, result.message)
        # One fewer edge and its vertex
        self.assertLess(_elem_count(result.result_egi), _elem_count(egi))

    def test_erase_from_negative_area_rejected(self):
        """Erasure in a negative (verso) area is rejected."""
        egi = parse_egif("~[ (Human *x) ]")
        cut_id = next(c.id for c in egi.Cut)
        inner_contents = list(egi.area[cut_id])

        state = begin_interaction("ERA", egi)
        r = advance_interaction(state, inner_contents)
        self.assertFalse(r.valid)
        self.assertIn("positive", r.message.lower())

    def test_empty_selection_rejected(self):
        """Empty selection is rejected for ERA."""
        egi = parse_egif("(Human *x)")
        state = begin_interaction("ERA", egi)
        r = advance_interaction(state, [])
        self.assertFalse(r.valid)


# ===================================================================
# INS Tests
# ===================================================================

class TestINSInteraction(unittest.TestCase):
    """INS (Insertion) via interaction protocol."""

    def test_insert_into_negative_area(self):
        """Insert content into a negative area."""
        egi = parse_egif("~[ ]")
        cut_id = next(c.id for c in egi.Cut)
        # cut is at depth 1 (negative)
        polarity, depth = egi.area_polarity(cut_id)
        self.assertEqual(polarity, AreaPolarity.NEGATIVE)

        state = begin_interaction("INS", egi)
        r1 = advance_interaction(state, "(Mortal *x)")
        self.assertTrue(r1.valid, r1.message)
        self.assertFalse(state.is_complete)

        r2 = advance_interaction(state, cut_id)
        self.assertTrue(r2.valid, r2.message)
        self.assertTrue(state.is_complete)

        result = apply_interaction(state)
        self.assertTrue(result.success, result.message)
        # Should have the new vertex and edge inside the cut
        self.assertGreater(len(result.result_egi.V), 0)
        self.assertGreater(len(result.result_egi.E), 0)

    def test_insert_into_positive_area_rejected(self):
        """Insertion into a positive area is rejected."""
        egi = parse_egif("~[ ]")
        state = begin_interaction("INS", egi)
        r1 = advance_interaction(state, "(Mortal *x)")
        self.assertTrue(r1.valid)

        r2 = advance_interaction(state, egi.sheet)
        self.assertFalse(r2.valid)
        self.assertIn("negative", r2.message.lower())

    def test_invalid_egif_rejected(self):
        """Invalid EGIF text is rejected."""
        egi = parse_egif("~[ ]")
        state = begin_interaction("INS", egi)
        r = advance_interaction(state, "((( not valid egif ]]")
        self.assertFalse(r.valid)
        self.assertIn("parse error", r.message.lower())

    def test_empty_egif_rejected(self):
        """Empty EGIF text is rejected."""
        egi = parse_egif("~[ ]")
        state = begin_interaction("INS", egi)
        r = advance_interaction(state, "")
        self.assertFalse(r.valid)

    def test_insert_complex_content(self):
        """Insert nested structure (with cut) into negative area."""
        egi = parse_egif("~[ ]")
        cut_id = next(c.id for c in egi.Cut)

        state = begin_interaction("INS", egi)
        r1 = advance_interaction(state, "~[ (Human *x) ]")
        self.assertTrue(r1.valid, r1.message)

        r2 = advance_interaction(state, cut_id)
        self.assertTrue(r2.valid, r2.message)

        result = apply_interaction(state)
        self.assertTrue(result.success, result.message)
        # Original 1 cut + 1 new cut from the inserted content
        self.assertEqual(len(result.result_egi.Cut), 2)

    def test_insert_from_egif_standalone(self):
        """Test the standalone insert_from_egif function."""
        egi = parse_egif("~[ ]")
        cut_id = next(c.id for c in egi.Cut)

        result = insert_from_egif(egi, cut_id, "(Cat *x)")
        self.assertTrue(result.success, result.error_message)
        self.assertGreater(len(result.result_egi.V), 0)

    def test_insert_from_egif_positive_area_rejected(self):
        """insert_from_egif rejects positive areas."""
        egi = parse_egif("~[ ]")
        result = insert_from_egif(egi, egi.sheet, "(Cat *x)")
        self.assertFalse(result.success)
        self.assertIn("negative", result.error_message.lower())


# ===================================================================
# IT+ Tests
# ===================================================================

class TestITPlusInteraction(unittest.TestCase):
    """IT+ (Iteration) via interaction protocol."""

    def test_iterate_into_nested_area(self):
        """Copy subgraph from sheet into a nested cut area."""
        # (Human *x) ~[ ]
        egi = parse_egif("(Human *x) ~[ ]")
        cut_id = next(c.id for c in egi.Cut)

        # Select the vertex and edge on the sheet as source
        cut_ids = {c.id for c in egi.Cut}
        sheet_elems = [e for e in egi.area[egi.sheet] if e not in cut_ids]

        state = begin_interaction("IT+", egi)
        r1 = advance_interaction(state, sheet_elems)
        self.assertTrue(r1.valid, r1.message)
        self.assertFalse(state.is_complete)

        r2 = advance_interaction(state, cut_id)
        self.assertTrue(r2.valid, r2.message)
        self.assertTrue(state.is_complete)

        result = apply_interaction(state)
        self.assertTrue(result.success, result.message)
        # The cut area should now have copies of the iterated elements
        cut_contents = result.result_egi.area.get(cut_id, frozenset())
        self.assertGreater(len(cut_contents), 0)

    def test_iterate_source_auto_closes(self):
        """Selecting just an edge auto-expands to include its vertex."""
        egi = parse_egif("(Human *x) ~[ ]")
        edge_id = next(e.id for e in egi.E)

        state = begin_interaction("IT+", egi)
        r = advance_interaction(state, [edge_id])
        # SubgraphClosureValidator auto-expands to include the vertex
        self.assertTrue(r.valid, r.message)
        # The expanded selection should include the vertex
        expanded = r.data["selection"]
        self.assertGreater(len(expanded), 1, "Selection should be expanded to include vertex")

    def test_dest_must_be_nested_inside_source(self):
        """Destination area must be nested inside source area."""
        # ~[ (Human *x) ] ~[ ]
        egi = parse_egif("~[ (Human *x) ] ~[ ]")
        cuts = list(egi.Cut)

        # Find which cut contains (Human *x)
        source_cut = None
        empty_cut = None
        for c in cuts:
            contents = egi.area.get(c.id, frozenset())
            if contents:
                source_cut = c.id
            else:
                empty_cut = c.id

        if source_cut and empty_cut:
            # Select elements inside source_cut
            source_elems = list(egi.area[source_cut])

            state = begin_interaction("IT+", egi)
            r1 = advance_interaction(state, source_elems)
            self.assertTrue(r1.valid, r1.message)

            # Try to iterate into the OTHER cut (not nested inside source)
            r2 = advance_interaction(state, empty_cut)
            self.assertFalse(r2.valid)
            self.assertIn("nested", r2.message.lower())


# ===================================================================
# IT- Tests
# ===================================================================

class TestITMinusInteraction(unittest.TestCase):
    """IT- (Deiteration) via interaction protocol."""

    def test_deiterate_iterated_copy(self):
        """Full chain: iterate, then deiterate the copy."""
        # Start with (Human *x) ~[ ]
        egi = parse_egif("(Human *x) ~[ ]")
        cut_id = next(c.id for c in egi.Cut)

        # IT+: copy sheet elements into the cut
        cut_ids_set = {c.id for c in egi.Cut}
        sheet_elems = [e for e in egi.area[egi.sheet] if e not in cut_ids_set]

        state_it = begin_interaction("IT+", egi)
        advance_interaction(state_it, sheet_elems)
        advance_interaction(state_it, cut_id)
        it_result = apply_interaction(state_it)
        self.assertTrue(it_result.success, it_result.message)
        egi2 = it_result.result_egi

        # Now the cut contains copies. Select them for IT-
        cut_contents = list(egi2.area.get(cut_id, frozenset()))
        self.assertGreater(len(cut_contents), 0, "Cut should have iterated copies")

        state_dt = begin_interaction("IT-", egi2)
        r = advance_interaction(state_dt, cut_contents)
        self.assertTrue(r.valid, r.message)
        self.assertIn("isomorphic", r.message.lower())

        result = apply_interaction(state_dt)
        self.assertTrue(result.success, result.message)
        # After deiteration, the cut should be empty again
        cut_contents_after = result.result_egi.area.get(cut_id, frozenset())
        self.assertEqual(len(cut_contents_after), 0,
                         "Cut should be empty after deiterating the copy")

    def test_non_iterated_subgraph_rejected(self):
        """A subgraph with no isomorphic original is rejected."""
        # (Human *x) ~[ (Cat *y) ] — Cat is not a copy of Human
        egi = parse_egif("(Human *x) ~[ (Cat *y) ]")
        cut_id = next(c.id for c in egi.Cut)
        cut_contents = list(egi.area[cut_id])

        state = begin_interaction("IT-", egi)
        r = advance_interaction(state, cut_contents)
        self.assertFalse(r.valid)
        self.assertIn("isomorphic", r.message.lower())

    def test_sheet_level_cannot_be_deiterated(self):
        """Elements on the sheet have no enclosing area — cannot deiterate."""
        egi = parse_egif("(Human *x)")
        sheet_elems = list(egi.area[egi.sheet])

        state = begin_interaction("IT-", egi)
        r = advance_interaction(state, sheet_elems)
        self.assertFalse(r.valid)
        self.assertIn("enclosing", r.message.lower())


# ===================================================================
# Chained transformation tests
# ===================================================================

class TestTransformationChains(unittest.TestCase):
    """Test multi-rule transformation chains."""

    def test_dc_plus_then_dc_minus_roundtrip(self):
        """DC+ followed by DC- returns to equivalent structure."""
        egi = parse_egif("(Human *x)")
        orig_v = len(egi.V)
        orig_e = len(egi.E)

        # DC+
        s1 = begin_interaction("DC+", egi)
        advance_interaction(s1, list(egi.area[egi.sheet]))
        r1 = apply_interaction(s1)
        self.assertTrue(r1.success)
        egi2 = r1.result_egi
        self.assertEqual(len(egi2.Cut), 2)

        # DC-
        outer = list(egi2.area[egi2.sheet])[0]
        s2 = begin_interaction("DC-", egi2)
        advance_interaction(s2, [outer])
        r2 = apply_interaction(s2)
        self.assertTrue(r2.success)
        egi3 = r2.result_egi

        self.assertEqual(len(egi3.Cut), 0)
        self.assertEqual(len(egi3.V), orig_v)
        self.assertEqual(len(egi3.E), orig_e)

    def test_ins_then_era_roundtrip(self):
        """INS into negative area, then ERA from positive (sheet)."""
        # Start: (Human *x) ~[ ]   — sheet is positive, cut is negative
        egi = parse_egif("(Human *x) ~[ ]")
        cut_id = next(c.id for c in egi.Cut)

        # INS: insert (Cat *y) into the cut (negative, depth 1)
        s1 = begin_interaction("INS", egi)
        advance_interaction(s1, "(Cat *y)")
        advance_interaction(s1, cut_id)
        r1 = apply_interaction(s1)
        self.assertTrue(r1.success, r1.message)
        egi2 = r1.result_egi
        self.assertGreater(len(egi2.V), len(egi.V))

        # ERA: erase (Human *x) from the sheet (positive)
        cut_ids = {c.id for c in egi2.Cut}
        sheet_non_cut = [e for e in egi2.area[egi2.sheet] if e not in cut_ids]
        s2 = begin_interaction("ERA", egi2)
        advance_interaction(s2, sheet_non_cut)
        r2 = apply_interaction(s2)
        self.assertTrue(r2.success, r2.message)
        egi3 = r2.result_egi

        # Sheet should now have only the cut
        sheet_contents = egi3.area[egi3.sheet]
        self.assertEqual(len(sheet_contents), 1)
        self.assertIn(cut_id, sheet_contents)
        # Cut still has the inserted content
        cut_contents = egi3.area.get(cut_id, frozenset())
        self.assertGreater(len(cut_contents), 0)

    def test_full_modus_ponens_chain(self):
        """
        Demonstrate modus ponens: from (Human *x) and ~[ (Human *y) ~[ (Mortal *z) ] ],
        derive (Mortal) on the sheet.

        Steps:
        1. Start with (Human *x) ~[ (Human *y) ~[ (Mortal *z) ] ]
        2. IT+: copy (Human *x) from sheet into outer cut (depth 1)
        3. DC-: The outer cut now has two (Human) and a nested ~[ (Mortal *z) ]
           — This step actually needs more work (double cut erasure on inner pattern)
           For now, verify the IT+ step works correctly.
        """
        egi = parse_egif("(Human *x) ~[ (Human *y) ~[ (Mortal *z) ] ]")

        # Verify structure
        self.assertEqual(len(egi.Cut), 2)
        self.assertEqual(len(egi.V), 3)
        self.assertEqual(len(egi.E), 3)

        # Find elements on the sheet that aren't cuts
        cut_ids = {c.id for c in egi.Cut}
        sheet_non_cut = [e for e in egi.area[egi.sheet] if e not in cut_ids]

        # IT+: copy sheet elements into the outer cut
        outer_cut = next(e for e in egi.area[egi.sheet] if e in cut_ids)
        s = begin_interaction("IT+", egi)
        r1 = advance_interaction(s, sheet_non_cut)
        self.assertTrue(r1.valid, r1.message)

        r2 = advance_interaction(s, outer_cut)
        self.assertTrue(r2.valid, r2.message)

        result = apply_interaction(s)
        self.assertTrue(result.success, result.message)

        # Outer cut should now have more elements (original + copies)
        outer_contents_before = len(egi.area.get(outer_cut, frozenset()))
        outer_contents_after = len(result.result_egi.area.get(outer_cut, frozenset()))
        self.assertGreater(outer_contents_after, outer_contents_before)


# ===================================================================
# Protocol mechanics tests
# ===================================================================

class TestProtocolMechanics(unittest.TestCase):
    """Test interaction protocol mechanics (not rule logic)."""

    def test_all_rules_registered(self):
        """All six rules have registered interactions."""
        expected = {"DC+", "DC-", "ERA", "INS", "IT+", "IT-"}
        self.assertEqual(set(RULE_INTERACTIONS.keys()), expected)

    def test_get_interaction_unknown_rule(self):
        """Unknown rule name raises ValueError."""
        with self.assertRaises(ValueError):
            get_interaction("UNKNOWN")

    def test_begin_interaction_creates_state(self):
        """begin_interaction returns a fresh InteractionState."""
        egi = parse_egif("")
        state = begin_interaction("DC+", egi)
        self.assertEqual(state.rule_name, "DC+")
        self.assertIs(state.egi, egi)
        self.assertEqual(len(state.completed_steps), 0)
        self.assertFalse(state.is_complete)

    def test_apply_without_steps_fails(self):
        """Applying before completing required steps fails."""
        egi = parse_egif("~[ ]")
        state = begin_interaction("INS", egi)
        result = apply_interaction(state)
        self.assertFalse(result.success)
        self.assertIn("Missing", result.message)

    def test_step_descriptions(self):
        """Each rule provides human-readable step descriptions."""
        for name, interaction in RULE_INTERACTIONS.items():
            steps = interaction.steps()
            self.assertGreater(len(steps), 0, f"{name} must have at least one step")
            for step in steps:
                self.assertTrue(step.prompt, f"{name}.{step.step_id} must have a prompt")
                self.assertTrue(step.step_id, f"{name} step must have an ID")


if __name__ == "__main__":
    unittest.main()
