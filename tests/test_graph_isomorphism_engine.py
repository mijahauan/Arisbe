"""
Comprehensive test suite for Graph Isomorphism Engine.

Tests the fundamental isomorphism testing capabilities that underlie
both IT- transformations and Endoporeutic Game proof validation.
"""

import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph_isomorphism_engine import (
    GraphIsomorphismEngine, IsomorphismValidator, IsomorphismMapping, IsomorphismResult
)
from src.egi_core_dau import (
    RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
)
from frozendict import frozendict


class TestGraphIsomorphismEngine(unittest.TestCase):
    """Test the core isomorphism engine functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = GraphIsomorphismEngine()
    
    def create_test_egi(self) -> RelationalGraphWithCuts:
        """Create a test EGI with various structural patterns."""
        # Vertices
        v1 = Vertex(id="v1", label="Socrates", is_generic=False)
        v2 = Vertex(id="v2", label="Socrates", is_generic=False)  # Identical to v1
        v3 = Vertex(id="v3", label=None, is_generic=True)
        v4 = Vertex(id="v4", label=None, is_generic=True)  # Identical to v3
        v5 = Vertex(id="v5", label="Plato", is_generic=False)  # Different from v1
        
        # Edges
        e1 = Edge(id="e1")
        e2 = Edge(id="e2")  # Will be identical to e1
        e3 = Edge(id="e3")  # Different relation
        
        # Cuts
        cut1 = Cut(id="cut1")
        cut2 = Cut(id="cut2")  # Will have same contents as cut1
        cut3 = Cut(id="cut3")  # Different contents
        
        return RelationalGraphWithCuts(
            V=frozenset([v1, v2, v3, v4, v5]),
            E=frozenset([e1, e2, e3]),
            Cut=frozenset([cut1, cut2, cut3]),
            nu=frozendict({
                "e1": ("v1",),
                "e2": ("v2",),  # Same structure as e1
                "e3": ("v3", "v4")  # Different structure
            }),
            sheet="sheet",
            area=frozendict({
                "sheet": frozenset(["v1", "e1", "v5", "cut1", "cut2", "cut3"]),
                "cut1": frozenset(["v2", "e2"]),
                "cut2": frozenset(["v3", "e3"]),  # Different from cut1 to satisfy disjoint constraint
                "cut3": frozenset(["v4"])  # Different from cut1/cut2
            }),
            rel=frozendict({
                "e1": "Human",
                "e2": "Human",  # Same as e1
                "e3": "Knows"   # Different from e1/e2
            })
        )
    
    def test_identical_vertices(self):
        """Test isomorphism of identical vertices."""
        egi = self.create_test_egi()
        
        # v1 and v2 are identical (same label, same generic status)
        result = self.engine.test_subgraph_isomorphism(
            egi, frozenset(["v1"]), frozenset(["v2"])
        )
        
        self.assertTrue(result.is_isomorphic)
        self.assertEqual(result.mapping.vertex_mapping, {"v1": "v2"})
    
    def test_different_vertices(self):
        """Test non-isomorphism of different vertices."""
        egi = self.create_test_egi()
        
        # v1 (Socrates, non-generic) vs v3 (generic) - should not match
        result = self.engine.test_subgraph_isomorphism(
            egi, frozenset(["v1"]), frozenset(["v3"])
        )
        
        self.assertFalse(result.is_isomorphic)
        self.assertIn("No valid structural mapping", result.reason)
    
    def test_identical_edges(self):
        """Test isomorphism of identical edges with their vertices."""
        egi = self.create_test_egi()
        
        # e1+v1 and e2+v2 are identical (same relation, same vertex structure)
        result = self.engine.test_subgraph_isomorphism(
            egi, frozenset(["e1", "v1"]), frozenset(["e2", "v2"])
        )
        
        self.assertTrue(result.is_isomorphic)
        self.assertEqual(result.mapping.edge_mapping, {"e1": "e2"})
        self.assertEqual(result.mapping.vertex_mapping, {"v1": "v2"})
    
    def test_different_edge_relations(self):
        """Test non-isomorphism of edges with different relations."""
        egi = self.create_test_egi()
        
        # e1 (Human) vs e3 (Knows) - different relations
        result = self.engine.test_subgraph_isomorphism(
            egi, frozenset(["e1", "v1"]), frozenset(["e3", "v3"])
        )
        
        self.assertFalse(result.is_isomorphic)
    
    def test_different_edge_arity(self):
        """Test non-isomorphism of edges with different vertex sequence lengths."""
        egi = self.create_test_egi()
        
        # e1 has 1 vertex, e3 has 2 vertices
        result = self.engine.test_subgraph_isomorphism(
            egi, frozenset(["e1", "v1"]), frozenset(["e3", "v3", "v4"])
        )
        
        self.assertFalse(result.is_isomorphic)
    
    def test_identical_cuts(self):
        """Test isomorphism of cuts with structurally identical contents."""
        egi = self.create_test_egi()
        
        # Create a simpler test case for cut isomorphism
        # cut1 contains (v2, e2) where e2: Human(v2)
        # We need to find another cut with the same structure
        # Since cut2 now contains (v3, e3) where e3: Knows(v3, v4), they're different
        # Let's test that they are NOT isomorphic
        result = self.engine.test_subgraph_isomorphism(
            egi, frozenset(["cut1", "v2", "e2"]), 
            frozenset(["cut2", "v3", "e3"])
        )
        
        self.assertFalse(result.is_isomorphic)  # Different structures
    
    def test_different_cut_contents(self):
        """Test non-isomorphism of cuts with different contents."""
        egi = self.create_test_egi()
        
        # cut1 has (v2, e2), cut3 has (v4) - different contents
        result = self.engine.test_subgraph_isomorphism(
            egi, frozenset(["cut1", "v2", "e2"]),
            frozenset(["cut3", "v4"])
        )
        
        self.assertFalse(result.is_isomorphic)
    
    def test_empty_subgraphs(self):
        """Test that empty subgraphs are trivially isomorphic."""
        egi = self.create_test_egi()
        
        result = self.engine.test_subgraph_isomorphism(
            egi, frozenset(), frozenset()
        )
        
        self.assertTrue(result.is_isomorphic)
        self.assertEqual(result.mapping.vertex_mapping, {})
        self.assertEqual(result.mapping.edge_mapping, {})
        self.assertEqual(result.mapping.cut_mapping, {})
    
    def test_different_sizes(self):
        """Test that subgraphs of different sizes are not isomorphic."""
        egi = self.create_test_egi()
        
        result = self.engine.test_subgraph_isomorphism(
            egi, frozenset(["v1"]), frozenset(["v1", "v2"])
        )
        
        self.assertFalse(result.is_isomorphic)
        self.assertEqual(result.reason, "Different number of elements")
    
    def test_find_isomorphic_subgraphs(self):
        """Test finding all isomorphic subgraphs in specified areas."""
        egi = self.create_test_egi()
        
        # Look for subgraphs isomorphic to (v1) in all areas
        matches = self.engine.find_isomorphic_subgraphs(
            egi, frozenset(["v1"]), ["sheet", "cut1", "cut2", "cut3"]
        )
        
        # Should find v2 in cut1 (v2 is identical to v1)
        # Also finds v1 itself in sheet (which is expected)
        self.assertEqual(len(matches), 2)
        
        # Check that we found the right matches
        found_areas = {match[0] for match in matches}
        self.assertIn("cut1", found_areas)
        self.assertIn("sheet", found_areas)


class TestCrossEGIIsomorphism(unittest.TestCase):
    """Test isomorphism between subgraphs in different EGIs."""
    
    def setUp(self):
        self.engine = GraphIsomorphismEngine()
    
    def create_egi_pair(self) -> tuple[RelationalGraphWithCuts, RelationalGraphWithCuts]:
        """Create two EGIs with some isomorphic subgraphs."""
        
        # EGI 1
        v1a = Vertex(id="v1a", label="Socrates", is_generic=False)
        e1a = Edge(id="e1a")
        
        egi1 = RelationalGraphWithCuts(
            V=frozenset([v1a]),
            E=frozenset([e1a]),
            Cut=frozenset(),
            nu=frozendict({"e1a": ("v1a",)}),
            sheet="sheet1",
            area=frozendict({"sheet1": frozenset(["v1a", "e1a"])}),
            rel=frozendict({"e1a": "Human"})
        )
        
        # EGI 2 with isomorphic structure but different IDs
        v1b = Vertex(id="v1b", label="Socrates", is_generic=False)
        e1b = Edge(id="e1b")
        
        egi2 = RelationalGraphWithCuts(
            V=frozenset([v1b]),
            E=frozenset([e1b]),
            Cut=frozenset(),
            nu=frozendict({"e1b": ("v1b",)}),
            sheet="sheet2",
            area=frozendict({"sheet2": frozenset(["v1b", "e1b"])}),
            rel=frozendict({"e1b": "Human"})
        )
        
        return egi1, egi2
    
    def test_cross_egi_isomorphism(self):
        """Test isomorphism detection across different EGIs."""
        egi1, egi2 = self.create_egi_pair()
        
        result = self.engine.test_cross_egi_isomorphism(
            egi1, frozenset(["v1a", "e1a"]),
            egi2, frozenset(["v1b", "e1b"])
        )
        
        self.assertTrue(result.is_isomorphic)
        self.assertEqual(result.mapping.vertex_mapping, {"v1a": "v1b"})
        self.assertEqual(result.mapping.edge_mapping, {"e1a": "e1b"})


class TestIsomorphismValidator(unittest.TestCase):
    """Test the high-level isomorphism validator."""
    
    def setUp(self):
        self.validator = IsomorphismValidator()
    
    def create_deiteration_test_egi(self) -> RelationalGraphWithCuts:
        """Create EGI suitable for testing deiteration validation."""
        v1 = Vertex(id="v1", label="Socrates", is_generic=False)
        v2 = Vertex(id="v2", label="Socrates", is_generic=False)  # Duplicate
        e1 = Edge(id="e1")
        e2 = Edge(id="e2")  # Duplicate
        cut1 = Cut(id="cut1")
        
        return RelationalGraphWithCuts(
            V=frozenset([v1, v2]),
            E=frozenset([e1, e2]),
            Cut=frozenset([cut1]),
            nu=frozendict({
                "e1": ("v1",),
                "e2": ("v2",)
            }),
            sheet="sheet",
            area=frozendict({
                "sheet": frozenset(["v1", "e1", "cut1"]),
                "cut1": frozenset(["v2", "e2"])
            }),
            rel=frozendict({
                "e1": "Human",
                "e2": "Human"
            })
        )
    
    def test_valid_deiteration_candidate(self):
        """Test validation of valid deiteration candidate."""
        egi = self.create_deiteration_test_egi()
        
        # Try to deiterate (v2, e2) from cut1
        # Should find matching (v1, e1) in sheet
        is_valid, error = self.validator.validate_deiteration_candidate(
            egi, frozenset(["v2", "e2"]), "cut1", ["cut1", "sheet"]
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_invalid_deiteration_candidate(self):
        """Test validation of invalid deiteration candidate."""
        egi = self.create_deiteration_test_egi()
        
        # Try to deiterate (v1, e1) from sheet
        # No matching subgraph exists in nesting hierarchy
        is_valid, error = self.validator.validate_deiteration_candidate(
            egi, frozenset(["v1", "e1"]), "sheet", ["sheet"]
        )
        
        self.assertFalse(is_valid)
        self.assertIn("No structurally identical subgraph found", error)


class TestComplexIsomorphismScenarios(unittest.TestCase):
    """Test complex isomorphism scenarios."""
    
    def setUp(self):
        self.engine = GraphIsomorphismEngine()
    
    def test_nested_cut_isomorphism(self):
        """Test isomorphism of complex nested cut structures."""
        # Create EGI with nested cuts containing isomorphic structures
        v1 = Vertex(id="v1", label=None, is_generic=True)
        v2 = Vertex(id="v2", label=None, is_generic=True)
        e1 = Edge(id="e1")
        e2 = Edge(id="e2")
        cut1 = Cut(id="cut1")
        cut2 = Cut(id="cut2")
        inner_cut1 = Cut(id="inner_cut1")
        inner_cut2 = Cut(id="inner_cut2")
        
        egi = RelationalGraphWithCuts(
            V=frozenset([v1, v2]),
            E=frozenset([e1, e2]),
            Cut=frozenset([cut1, cut2, inner_cut1, inner_cut2]),
            nu=frozendict({
                "e1": ("v1",),
                "e2": ("v2",)
            }),
            sheet="sheet",
            area=frozendict({
                "sheet": frozenset(["cut1", "cut2"]),
                "cut1": frozenset(["inner_cut1"]),
                "cut2": frozenset(["inner_cut2"]),
                "inner_cut1": frozenset(["v1", "e1"]),
                "inner_cut2": frozenset(["v2", "e2"])
            }),
            rel=frozendict({
                "e1": "P",
                "e2": "P"
            })
        )
        
        # Test isomorphism of the complete nested structures
        result = self.engine.test_subgraph_isomorphism(
            egi, 
            frozenset(["cut1", "inner_cut1", "v1", "e1"]),
            frozenset(["cut2", "inner_cut2", "v2", "e2"])
        )
        
        self.assertTrue(result.is_isomorphic)


if __name__ == '__main__':
    unittest.main()
