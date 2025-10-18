"""
Test subgraph closure validation for INS/ERA transformations.

Tests the SubgraphClosureValidator to ensure:
1. Proper detection of non-closed subgraphs
2. Automatic expansion to achieve closure
3. Detailed violation reporting
4. Integration with transformation rules
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from frozendict import frozendict

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from subgraph_closure_validator import (
    ClosureAnalysis,
    SubgraphClosureValidator,
    create_validator,
)
from formal_transformation_rules import InsertionRule, ErasureRule, TransformationContext, AreaPolarity


class TestSubgraphClosureValidator:
    """Test cases for subgraph closure validation."""

    def test_empty_selection_is_closed(self):
        """Empty selection is trivially closed."""
        egi = self._create_simple_egi()
        validator = SubgraphClosureValidator(egi)
        
        analysis = validator.analyze_closure(frozenset(), allow_expansion=False)
        
        assert analysis.is_closed
        assert len(analysis.violations) == 0
        assert len(analysis.added_elements) == 0

    def test_edge_without_vertices_expands(self):
        """Edge selected without its vertices should expand to include vertices."""
        # Create EGI with edge connecting two vertices
        v1 = Vertex(ElementID("v1"))
        v2 = Vertex(ElementID("v2"))
        e1 = Edge(ElementID("e1"))
        
        egi = RelationalGraphWithCuts(
            V=frozenset([v1, v2]),
            E=frozenset([e1]),
            nu=frozendict({ElementID("e1"): (ElementID("v1"), ElementID("v2"))}),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({ElementID("sheet"): frozenset([ElementID("v1"), ElementID("v2"), ElementID("e1")])}),
            rel=frozendict({ElementID("e1"): "Connected"}),
        )
        
        validator = SubgraphClosureValidator(egi)
        
        # Select only the edge
        selection = frozenset([ElementID("e1")])
        analysis = validator.analyze_closure(selection, allow_expansion=True)
        
        # Should expand to include vertices
        assert analysis.is_closed
        assert ElementID("v1") in analysis.closed_subgraph
        assert ElementID("v2") in analysis.closed_subgraph
        assert ElementID("e1") in analysis.closed_subgraph
        assert len(analysis.added_elements) == 2  # Added v1 and v2

    def test_vertex_without_edge_expands(self):
        """Vertices selected without connecting edge should expand to include edge."""
        # Create EGI with edge connecting two vertices
        v1 = Vertex(ElementID("v1"))
        v2 = Vertex(ElementID("v2"))
        e1 = Edge(ElementID("e1"))
        
        egi = RelationalGraphWithCuts(
            V=frozenset([v1, v2]),
            E=frozenset([e1]),
            nu=frozendict({ElementID("e1"): (ElementID("v1"), ElementID("v2"))}),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({ElementID("sheet"): frozenset([ElementID("v1"), ElementID("v2"), ElementID("e1")])}),
            rel=frozendict({ElementID("e1"): "Connected"}),
        )
        
        validator = SubgraphClosureValidator(egi)
        
        # Select both vertices but not the edge
        selection = frozenset([ElementID("v1"), ElementID("v2")])
        analysis = validator.analyze_closure(selection, allow_expansion=True)
        
        # Should expand to include edge
        assert analysis.is_closed
        assert ElementID("v1") in analysis.closed_subgraph
        assert ElementID("v2") in analysis.closed_subgraph
        assert ElementID("e1") in analysis.closed_subgraph
        assert ElementID("e1") in analysis.added_elements

    def test_cut_without_contents_expands(self):
        """Cut selected without its contents should expand to include contents."""
        # Create EGI with cut containing a vertex
        v1 = Vertex(ElementID("v1"))
        cut1 = Cut(ElementID("cut1"))
        
        egi = RelationalGraphWithCuts(
            V=frozenset([v1]),
            E=frozenset(),
            nu=frozendict(),
            sheet=ElementID("sheet"),
            Cut=frozenset([cut1]),
            area=frozendict({
                ElementID("sheet"): frozenset([ElementID("cut1")]),
                ElementID("cut1"): frozenset([ElementID("v1")])
            }),
            rel=frozendict(),
        )
        
        validator = SubgraphClosureValidator(egi)
        
        # Select only the cut
        selection = frozenset([ElementID("cut1")])
        analysis = validator.analyze_closure(selection, allow_expansion=True)
        
        # Should expand to include cut contents
        assert analysis.is_closed
        assert ElementID("cut1") in analysis.closed_subgraph
        assert ElementID("v1") in analysis.closed_subgraph
        assert ElementID("v1") in analysis.added_elements

    def test_already_closed_subgraph(self):
        """Already closed subgraph should not expand."""
        # Create simple closed subgraph
        v1 = Vertex(ElementID("v1"))
        v2 = Vertex(ElementID("v2"))
        e1 = Edge(ElementID("e1"))
        
        egi = RelationalGraphWithCuts(
            V=frozenset([v1, v2]),
            E=frozenset([e1]),
            nu=frozendict({ElementID("e1"): (ElementID("v1"), ElementID("v2"))}),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({ElementID("sheet"): frozenset([ElementID("v1"), ElementID("v2"), ElementID("e1")])}),
            rel=frozendict({ElementID("e1"): "Connected"}),
        )
        
        validator = SubgraphClosureValidator(egi)
        
        # Select all elements (already closed)
        selection = frozenset([ElementID("v1"), ElementID("v2"), ElementID("e1")])
        analysis = validator.analyze_closure(selection, allow_expansion=True)
        
        # Should already be closed, no expansions
        assert analysis.is_closed
        assert analysis.closed_subgraph == selection
        assert len(analysis.added_elements) == 0

    def test_partial_edge_connection_does_not_force_inclusion(self):
        """Edge connecting to vertex outside subgraph should not be included."""
        # Create EGI with three vertices and two edges in a chain
        v1 = Vertex(ElementID("v1"))
        v2 = Vertex(ElementID("v2"))
        v3 = Vertex(ElementID("v3"))
        e1 = Edge(ElementID("e1"))  # v1 -> v2
        e2 = Edge(ElementID("e2"))  # v2 -> v3
        
        egi = RelationalGraphWithCuts(
            V=frozenset([v1, v2, v3]),
            E=frozenset([e1, e2]),
            nu=frozendict({
                ElementID("e1"): (ElementID("v1"), ElementID("v2")),
                ElementID("e2"): (ElementID("v2"), ElementID("v3")),
            }),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({
                ElementID("sheet"): frozenset([
                    ElementID("v1"), ElementID("v2"), ElementID("v3"),
                    ElementID("e1"), ElementID("e2")
                ])
            }),
            rel=frozendict({
                ElementID("e1"): "Connected",
                ElementID("e2"): "Connected",
            }),
        )
        
        validator = SubgraphClosureValidator(egi)
        
        # Select v1 and v2, which should include e1 but NOT e2
        selection = frozenset([ElementID("v1"), ElementID("v2")])
        analysis = validator.analyze_closure(selection, allow_expansion=True)
        
        # Should include e1 (connects v1 and v2) but not e2 or v3
        assert analysis.is_closed
        assert ElementID("v1") in analysis.closed_subgraph
        assert ElementID("v2") in analysis.closed_subgraph
        assert ElementID("e1") in analysis.closed_subgraph
        assert ElementID("e2") not in analysis.closed_subgraph
        assert ElementID("v3") not in analysis.closed_subgraph

    def test_violation_reporting(self):
        """Violations should be clearly reported."""
        # Create edge with vertices, but select edge only
        v1 = Vertex(ElementID("v1"))
        v2 = Vertex(ElementID("v2"))
        e1 = Edge(ElementID("e1"))
        
        egi = RelationalGraphWithCuts(
            V=frozenset([v1, v2]),
            E=frozenset([e1]),
            nu=frozendict({ElementID("e1"): (ElementID("v1"), ElementID("v2"))}),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({ElementID("sheet"): frozenset([ElementID("v1"), ElementID("v2"), ElementID("e1")])}),
            rel=frozendict({ElementID("e1"): "Connected"}),
        )
        
        validator = SubgraphClosureValidator(egi)
        
        # Select edge only, don't allow expansion
        selection = frozenset([ElementID("e1")])
        analysis = validator.analyze_closure(selection, allow_expansion=False)
        
        # Should have violations (edge without its vertices)
        assert not analysis.is_closed
        assert len(analysis.violations) > 0
        # Check that violation mentions missing vertices
        violation_text = str(analysis.violations[0].description).lower()
        assert "v1" in violation_text or "v2" in violation_text or "vertex" in violation_text

    def test_factory_function(self):
        """Factory function should create validator."""
        egi = self._create_simple_egi()
        validator = create_validator(egi)
        
        assert isinstance(validator, SubgraphClosureValidator)
        assert validator.egi == egi

    def test_validate_for_transformation_ins(self):
        """Test validation for INS transformation."""
        egi = self._create_simple_egi()
        validator = SubgraphClosureValidator(egi)
        
        # Valid closed subgraph
        selection = frozenset([ElementID("v1")])
        is_valid, message, expanded = validator.validate_for_transformation(selection, "INS")
        
        assert is_valid
        assert "closed" in message.lower()

    def test_validate_for_transformation_era(self):
        """Test validation for ERA transformation."""
        egi = self._create_simple_egi()
        validator = SubgraphClosureValidator(egi)
        
        # Valid closed subgraph
        selection = frozenset([ElementID("v1")])
        is_valid, message, expanded = validator.validate_for_transformation(selection, "ERA")
        
        assert is_valid
        assert "closed" in message.lower()

    def test_integration_with_insertion_rule(self):
        """Test that InsertionRule uses closure validator."""
        # Create EGI with negative area (for INS) and a vertex to insert
        v1 = Vertex(ElementID("v1"))
        cut1 = Cut(ElementID("cut1"))
        
        egi = RelationalGraphWithCuts(
            V=frozenset([v1]),
            E=frozenset(),
            nu=frozendict(),
            sheet=ElementID("sheet"),
            Cut=frozenset([cut1]),
            area=frozendict({
                ElementID("sheet"): frozenset([ElementID("v1"), ElementID("cut1")]),  # v1 in sheet
                ElementID("cut1"): frozenset()  # Empty negative area
            }),
            rel=frozendict(),
        )
        
        rule = InsertionRule()
        
        # Create context for insertion (inserting v1 from sheet into cut1)
        context = TransformationContext(
            source_egi=egi,
            target_area=ElementID("cut1"),
            selected_subgraph=frozenset([ElementID("v1")]),
            area_polarity=AreaPolarity.NEGATIVE,
            nesting_depth=1
        )
        
        # Check preconditions (should validate closure)
        is_valid, error = rule.check_preconditions(context)
        
        # Should be valid (single vertex is closed)
        assert is_valid

    def test_integration_with_erasure_rule(self):
        """Test that ErasureRule uses closure validator."""
        # Create EGI with element in positive area (for ERA)
        v1 = Vertex(ElementID("v1"))
        
        egi = RelationalGraphWithCuts(
            V=frozenset([v1]),
            E=frozenset(),
            nu=frozendict(),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({
                ElementID("sheet"): frozenset([ElementID("v1")])
            }),
            rel=frozendict(),
        )
        
        rule = ErasureRule()
        
        # Create context for erasure
        context = TransformationContext(
            source_egi=egi,
            target_area=ElementID("sheet"),
            selected_subgraph=frozenset([ElementID("v1")]),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0
        )
        
        # Check preconditions (should validate closure)
        is_valid, error = rule.check_preconditions(context)
        
        # Should be valid (single vertex is closed)
        assert is_valid

    # Helper methods
    
    def _create_simple_egi(self) -> RelationalGraphWithCuts:
        """Create a simple test EGI."""
        v1 = Vertex(ElementID("v1"))
        
        return RelationalGraphWithCuts(
            V=frozenset([v1]),
            E=frozenset(),
            nu=frozendict(),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({ElementID("sheet"): frozenset([ElementID("v1")])}),
            rel=frozendict(),
        )


def test_suite():
    """Run all subgraph closure tests."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    test_suite()
