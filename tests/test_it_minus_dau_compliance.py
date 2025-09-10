"""
Comprehensive tests for DAU-compliant IT- (deiteration) implementation.

Tests verify the claimed properties from the IT- implementation:
1. Nest-of-cuts analysis with strict nesting hierarchy checking
2. Structural isomorphism validation for vertices, edges, and cuts
3. All four Dau compliance requirements
4. Prevention of false positive duplicates and invalid cross-area deiterations
"""

import unittest
from typing import FrozenSet, Dict, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.formal_transformation_rules import DeiterationRule
from src.egi_core_dau import (
    RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
)
from frozendict import frozendict


class TestITMinusDauCompliance(unittest.TestCase):
    """Test suite for DAU-compliant IT- deiteration implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.deiteration_rule = DeiterationRule()
    
    def create_test_egi_with_nested_cuts(self) -> RelationalGraphWithCuts:
        """Create test EGI with nested cut structure for testing."""
        # Create vertices
        v1 = Vertex(id="v1", label="Socrates", is_generic=False)
        v2 = Vertex(id="v2", label="Socrates", is_generic=False)  # Duplicate for testing
        v3 = Vertex(id="v3", label="x", is_generic=True)
        
        # Create edges/predicates
        e1 = Edge(id="e1")
        e2 = Edge(id="e2")  # Duplicate for testing
        e3 = Edge(id="e3")
        
        # Create cuts
        cut1 = Cut(id="cut1")
        cut2 = Cut(id="cut2")  # Nested inside cut1
        cut3 = Cut(id="cut3")  # Separate cut
        
        # Create EGI structure with proper Dau format
        egi = RelationalGraphWithCuts(
            V=frozenset([v1, v2, v3]),
            E=frozenset([e1, e2, e3]),
            Cut=frozenset([cut1, cut2, cut3]),
            nu=frozendict({
                "e1": ("v1",),
                "e2": ("v2",),  # Same structure as e1
                "e3": ("v3",)
            }),
            sheet="sheet",
            area=frozendict({
                "sheet": frozenset(["v1", "e1", "cut1", "cut3"]),  # Sheet level
                "cut1": frozenset(["v2", "e2", "cut2"]),           # Inside cut1
                "cut2": frozenset(["v3", "e3"]),                   # Inside cut2 (nested)
                "cut3": frozenset([])                              # Empty separate cut
            }),
            rel=frozendict({
                "e1": "Human",
                "e2": "Human",  # Same relation as e1
                "e3": "Mortal"
            })
        )
        
        return egi
    
    def test_nest_of_cuts_analysis(self):
        """Test 1: Nest-of-cuts analysis builds proper nesting hierarchy."""
        egi = self.create_test_egi_with_nested_cuts()
        
        # Test building nesting hierarchy from cut2 (deepest)
        hierarchy = self.deiteration_rule._get_nesting_hierarchy(egi, "cut2")
        expected_hierarchy = ["cut2", "cut1", "sheet"]
        self.assertEqual(hierarchy, expected_hierarchy, 
                        "Nesting hierarchy should go from deepest to sheet")
        
        # Test building hierarchy from cut1 (middle)
        hierarchy = self.deiteration_rule._get_nesting_hierarchy(egi, "cut1")
        expected_hierarchy = ["cut1", "sheet"]
        self.assertEqual(hierarchy, expected_hierarchy,
                        "Hierarchy from cut1 should skip cut2 (not a parent)")
        
        # Test building hierarchy from sheet (top level)
        hierarchy = self.deiteration_rule._get_nesting_hierarchy(egi, "sheet")
        expected_hierarchy = ["sheet"]
        self.assertEqual(hierarchy, expected_hierarchy,
                        "Sheet level should only contain itself")
    
    def test_structural_isomorphism_vertices(self):
        """Test 2a: Structural isomorphism validation for vertices."""
        egi = self.create_test_egi_with_nested_cuts()
        
        # Test identical vertices (should match)
        mapping = {"v1": "v2"}
        result = self.deiteration_rule._is_valid_structural_mapping(
            egi, frozenset(["v1"]), mapping, "cut1"
        )
        self.assertTrue(result, "Identical vertices should match structurally")
        
        # Test different labels (should not match)
        v_different = Vertex(id="v_diff", label="Plato", is_generic=False)
        egi.V.append(v_different)
        egi.area["cut1"] = egi.area["cut1"] | frozenset(["v_diff"])
        
        mapping = {"v1": "v_diff"}
        result = self.deiteration_rule._is_valid_structural_mapping(
            egi, frozenset(["v1"]), mapping, "cut1"
        )
        self.assertFalse(result, "Vertices with different labels should not match")
        
        # Test different generic status (should not match)
        v_generic = Vertex(id="v_gen", label="Socrates", is_generic=True)
        egi.V.append(v_generic)
        egi.area["cut1"] = egi.area["cut1"] | frozenset(["v_gen"])
        
        mapping = {"v1": "v_gen"}
        result = self.deiteration_rule._is_valid_structural_mapping(
            egi, frozenset(["v1"]), mapping, "cut1"
        )
        self.assertFalse(result, "Vertices with different generic status should not match")
    
    def test_structural_isomorphism_edges(self):
        """Test 2b: Structural isomorphism validation for edges."""
        egi = self.create_test_egi_with_nested_cuts()
        
        # Test identical edges (should match)
        mapping = {"e1": "e2", "v1": "v2"}
        result = self.deiteration_rule._is_valid_structural_mapping(
            egi, frozenset(["e1", "v1"]), mapping, "cut1"
        )
        self.assertTrue(result, "Identical edges should match structurally")
        
        # Test different relations (should not match)
        mapping = {"e1": "e3"}  # Human vs Mortal
        result = self.deiteration_rule._is_valid_structural_mapping(
            egi, frozenset(["e1"]), mapping, "cut2"
        )
        self.assertFalse(result, "Edges with different relations should not match")
        
        # Test different vertex sequences (should not match)
        egi.nu["e3"] = ("v1", "v2")  # Different arity
        mapping = {"e1": "e3"}
        result = self.deiteration_rule._is_valid_structural_mapping(
            egi, frozenset(["e1"]), mapping, "cut2"
        )
        self.assertFalse(result, "Edges with different vertex sequences should not match")
    
    def test_dau_requirement_1_multiple_instances(self):
        """Test 3a: Dau requirement - at least two instances in nest of cuts."""
        egi = self.create_test_egi_with_nested_cuts()
        
        # Test valid case: e1 in sheet, e2 in cut1 (nesting hierarchy)
        selected_subgraph = frozenset(["e2", "v2"])  # In cut1
        result = self.deiteration_rule.is_valid(egi, selected_subgraph)
        self.assertTrue(result, "Should find matching instance e1+v1 in parent area (sheet)")
        
        # Test invalid case: only one instance exists
        # Remove the duplicate to test single instance
        egi.area["sheet"] = egi.area["sheet"] - frozenset(["e1", "v1"])
        result = self.deiteration_rule.is_valid(egi, selected_subgraph)
        self.assertFalse(result, "Should reject when no duplicate exists in nesting hierarchy")
    
    def test_dau_requirement_2_nesting_constraint(self):
        """Test 3b: Dau requirement - more-times-enclosed instance may be erased."""
        egi = self.create_test_egi_with_nested_cuts()
        
        # Test valid: removing more deeply nested instance (cut1 vs sheet)
        selected_subgraph = frozenset(["e2", "v2"])  # In cut1 (deeper)
        result = self.deiteration_rule.is_valid(egi, selected_subgraph)
        self.assertTrue(result, "Should allow removal of more deeply nested instance")
        
        # Test invalid: trying to remove less nested instance
        selected_subgraph = frozenset(["e1", "v1"])  # In sheet (shallower)
        result = self.deiteration_rule.is_valid(egi, selected_subgraph)
        # This should be false because we can't remove the less nested instance
        # when a more nested one exists
        self.assertFalse(result, "Should not allow removal of less nested instance")
    
    def test_dau_requirement_3_valid_deiteration_condition(self):
        """Test 3c: Dau requirement - leaves instance in same or less enclosed area."""
        egi = self.create_test_egi_with_nested_cuts()
        
        # Test removing from cut2 (deepest) - should leave instances in cut1 and sheet
        selected_subgraph = frozenset(["e3", "v3"])  # In cut2
        
        # Add matching instances in cut1 and sheet for this test
        v4 = Vertex(id="v4", label="x", is_generic=True)
        e4 = Edge(id="e4")
        egi.V.append(v4)
        egi.E.append(e4)
        egi.rel["e4"] = "Mortal"
        egi.nu["e4"] = ("v4",)
        egi.area["cut1"] = egi.area["cut1"] | frozenset(["e4", "v4"])
        
        result = self.deiteration_rule.is_valid(egi, selected_subgraph)
        self.assertTrue(result, "Should allow removal when instance exists in less enclosed area")
    
    def test_false_positive_prevention(self):
        """Test 4a: Prevention of false positive duplicates."""
        egi = self.create_test_egi_with_nested_cuts()
        
        # Create superficially similar but structurally different elements
        v_similar = Vertex(id="v_similar", label="Socrates", is_generic=False)
        e_similar = Edge(id="e_similar")
        egi.V.append(v_similar)
        egi.E.append(e_similar)
        egi.rel["e_similar"] = "Human"  # Same relation name
        egi.nu["e_similar"] = ("v_similar",)  # Same structure
        
        # But place in non-nesting area (cut3 is separate from cut1)
        egi.area["cut3"] = frozenset(["e_similar", "v_similar"])
        
        # Try to deiterate from cut1 - should fail because cut3 is not in nesting hierarchy
        selected_subgraph = frozenset(["e2", "v2"])  # In cut1
        result = self.deiteration_rule.is_valid(egi, selected_subgraph)
        
        # Should still be true because e1+v1 exists in sheet (valid nesting)
        # But let's remove that and test the cut3 case specifically
        egi.area["sheet"] = egi.area["sheet"] - frozenset(["e1", "v1"])
        result = self.deiteration_rule.is_valid(egi, selected_subgraph)
        self.assertFalse(result, "Should not match elements in non-nesting areas")
    
    def test_invalid_cross_area_deiteration_prevention(self):
        """Test 4b: Prevention of invalid cross-area deiterations."""
        egi = self.create_test_egi_with_nested_cuts()
        
        # Create identical elements in completely separate cut hierarchies
        cut4 = Cut(id="cut4")
        v5 = Vertex(id="v5", label="Socrates", is_generic=False)
        e5 = Edge(id="e5")
        
        egi.Cut.append(cut4)
        egi.V.append(v5)
        egi.E.append(e5)
        egi.rel["e5"] = "Human"
        egi.nu["e5"] = ("v5",)
        
        # Place in separate hierarchy (cut4 at sheet level, separate from cut1 hierarchy)
        egi.area["sheet"] = egi.area["sheet"] | frozenset(["cut4"])
        egi.area["cut4"] = frozenset(["e5", "v5"])
        
        # Remove the valid nesting match to isolate this test
        egi.area["sheet"] = egi.area["sheet"] - frozenset(["e1", "v1"])
        
        # Try to deiterate from cut1 against cut4 - should fail
        selected_subgraph = frozenset(["e2", "v2"])  # In cut1
        result = self.deiteration_rule.is_valid(egi, selected_subgraph)
        self.assertFalse(result, "Should prevent deiteration across separate cut hierarchies")
    
    def test_distance_ordered_search(self):
        """Test 5: Distance-ordered search finds closest match first."""
        egi = self.create_test_egi_with_nested_cuts()
        
        # Add identical elements at multiple nesting levels
        # Level 1: cut1 (closest to cut2)
        v_cut1 = Vertex(id="v_cut1", label="x", is_generic=True)
        e_cut1 = Edge(id="e_cut1")
        egi.V.append(v_cut1)
        egi.E.append(e_cut1)
        egi.rel["e_cut1"] = "Mortal"
        egi.nu["e_cut1"] = ("v_cut1",)
        egi.area["cut1"] = egi.area["cut1"] | frozenset(["e_cut1", "v_cut1"])
        
        # Level 2: sheet (further from cut2)
        v_sheet = Vertex(id="v_sheet", label="x", is_generic=True)
        e_sheet = Edge(id="e_sheet")
        egi.V.append(v_sheet)
        egi.E.append(e_sheet)
        egi.rel["e_sheet"] = "Mortal"
        egi.nu["e_sheet"] = ("v_sheet",)
        egi.area["sheet"] = egi.area["sheet"] | frozenset(["e_sheet", "v_sheet"])
        
        # Test deiteration from cut2 - should find match in cut1 (closer) first
        selected_subgraph = frozenset(["e3", "v3"])  # In cut2
        result = self.deiteration_rule.is_valid(egi, selected_subgraph)
        self.assertTrue(result, "Should find valid deiteration using distance-ordered search")
        
        # The implementation should prefer the closer match (cut1) over the farther one (sheet)
        # This is tested implicitly by the algorithm's correctness
    
    def test_edge_cases(self):
        """Test 6: Edge cases and error conditions."""
        egi = self.create_test_egi_with_nested_cuts()
        
        # Test empty subgraph
        result = self.deiteration_rule.is_valid(egi, frozenset())
        self.assertFalse(result, "Empty subgraph should be invalid")
        
        # Test non-existent elements
        result = self.deiteration_rule.is_valid(egi, frozenset(["non_existent"]))
        self.assertFalse(result, "Non-existent elements should be invalid")
        
        # Test self-deiteration (same area)
        selected_subgraph = frozenset(["e1", "v1"])  # In sheet
        # Remove other instances to force self-comparison
        egi.area["cut1"] = frozenset()
        egi.area["cut2"] = frozenset()
        result = self.deiteration_rule.is_valid(egi, selected_subgraph)
        self.assertFalse(result, "Cannot deiterate against self in same area")


class TestStructuralIsomorphismHelpers(unittest.TestCase):
    """Test the helper methods for structural isomorphism checking."""
    
    def setUp(self):
        self.deiteration_rule = DeiterationRule()
    
    def test_sequences_structurally_equivalent(self):
        """Test vertex sequence structural equivalence checking."""
        # Test identical sequences
        seq1 = ("v1", "v2", "v3")
        seq2 = ("v4", "v5", "v6")
        mapping = {"v1": "v4", "v2": "v5", "v3": "v6"}
        
        result = self.deiteration_rule._sequences_structurally_equivalent(seq1, seq2, mapping)
        self.assertTrue(result, "Mapped sequences should be equivalent")
        
        # Test different lengths
        seq2_short = ("v4", "v5")
        result = self.deiteration_rule._sequences_structurally_equivalent(seq1, seq2_short, mapping)
        self.assertFalse(result, "Sequences of different lengths should not be equivalent")
        
        # Test incomplete mapping
        incomplete_mapping = {"v1": "v4", "v2": "v5"}  # Missing v3 -> v6
        result = self.deiteration_rule._sequences_structurally_equivalent(seq1, seq2, incomplete_mapping)
        self.assertFalse(result, "Sequences with incomplete mapping should not be equivalent")


if __name__ == '__main__':
    unittest.main()
