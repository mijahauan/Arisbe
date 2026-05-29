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
sys.path.insert(0, str(Path(__file__).parent))  # for shared strategy imports

import pytest
from frozendict import frozendict
from hypothesis import HealthCheck, assume, given, settings, strategies as st

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from egif_parser_dau import parse_egif
from subgraph_closure_validator import (
    ClosureAnalysis,
    SubgraphClosureValidator,
    create_validator,
)
from formal_transformation_rules import InsertionRule, ErasureRule, TransformationContext, AreaPolarity

# Reuse the well-formed EGIF strategy from the round-trip property tests.
# Importing across test modules is safe: pytest collects each file
# independently, and `egif_sheet` is a strategy factory, not a test.
from test_properties_round_trip import egif_sheet


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

    def test_edge_without_vertices_expands_when_isolated(self):
        """Edge whose vertices have no other connections expands to include them.

        When v1 and v2 connect ONLY to e1, erasing e1 alone would leave them
        as isolated vertices.  The closure pulls them in so they are co-erased.
        """
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
        selection = frozenset([ElementID("e1")])
        analysis = validator.analyze_closure(selection, allow_expansion=True)

        assert analysis.is_closed
        assert ElementID("v1") in analysis.closed_subgraph
        assert ElementID("v2") in analysis.closed_subgraph
        assert len(analysis.added_elements) == 2

    def test_edge_without_vertices_is_closed_when_vertex_shared(self):
        """Edge is closed alone when its vertex connects to OTHER predicates.

        The vertex is "semi-free": it has external connections and will remain
        connected after the edge is erased.  This is the ERA "Cat on Mat" fix:
        erasing Cat leaves the shared vertex still connected to On.
        """
        v1 = Vertex(ElementID("v1"))
        e1 = Edge(ElementID("e1"))  # Cat — v1
        e2 = Edge(ElementID("e2"))  # On  — v1

        egi = RelationalGraphWithCuts(
            V=frozenset([v1]),
            E=frozenset([e1, e2]),
            nu=frozendict({
                ElementID("e1"): (ElementID("v1"),),
                ElementID("e2"): (ElementID("v1"),),
            }),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({ElementID("sheet"): frozenset([ElementID("v1"), ElementID("e1"), ElementID("e2")])}),
            rel=frozendict({ElementID("e1"): "Cat", ElementID("e2"): "On"}),
        )

        validator = SubgraphClosureValidator(egi)
        selection = frozenset([ElementID("e1")])
        analysis = validator.analyze_closure(selection, allow_expansion=True)

        # Cat alone is closed — v1 is semi-free (stays connected to On)
        assert analysis.is_closed
        assert ElementID("e1") in analysis.closed_subgraph
        assert ElementID("v1") not in analysis.closed_subgraph
        assert len(analysis.added_elements) == 0

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

    def test_vertex_selection_forces_all_connecting_edges(self):
        """Selecting vertices forces all connecting edges to be included.

        When a vertex is erased, every edge referencing it would become a
        dangling reference.  The closure must therefore include all edges
        that touch any selected vertex.  In a chain v1-e1-v2-e2-v3, selecting
        {v1, v2} forces both e1 and e2 (because v2 connects to e2).  Since
        v3 connects only to e2 (which is now in the subgraph), v3 is also
        pulled in to avoid leaving an isolated vertex.
        """
        v1 = Vertex(ElementID("v1"))
        v2 = Vertex(ElementID("v2"))
        v3 = Vertex(ElementID("v3"))
        e1 = Edge(ElementID("e1"))  # v1 — v2
        e2 = Edge(ElementID("e2"))  # v2 — v3

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

        # Select v1 and v2 — forces e1 and e2 (connecting edges)
        # v3 is isolated after e2 is added, so it is co-erased
        selection = frozenset([ElementID("v1"), ElementID("v2")])
        analysis = validator.analyze_closure(selection, allow_expansion=True)

        assert analysis.is_closed
        assert ElementID("v1") in analysis.closed_subgraph
        assert ElementID("v2") in analysis.closed_subgraph
        assert ElementID("e1") in analysis.closed_subgraph
        assert ElementID("e2") in analysis.closed_subgraph   # forced by v2
        # v3 connects only to e2, so it is co-erased to avoid leaving an isolated vertex
        assert ElementID("v3") in analysis.closed_subgraph

    def test_violation_reporting(self):
        """Violations should be reported for vertex with missing connecting edges."""
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

        # Select only a vertex (without its connecting edge), no expansion allowed
        selection = frozenset([ElementID("v1")])
        analysis = validator.analyze_closure(selection, allow_expansion=False)

        # Should have violations (vertex without its connecting edge)
        assert not analysis.is_closed
        assert len(analysis.violations) > 0
        violation_text = str(analysis.violations[0].description).lower()
        assert "e1" in violation_text or "edge" in violation_text

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


# --------------------------------------------------------------------------- #
# Property tests: closure idempotence (issue #8)                              #
# --------------------------------------------------------------------------- #


@st.composite
def egi_with_selection(draw):
    """Generate a parseable EGIF, parse it to an EGI, and draw a random
    subset of its element IDs as the selection.

    Selection may include any mix of vertex / edge / cut IDs, including
    the empty set (trivially closed) and the full element set (already
    closed by construction).
    """
    text = draw(egif_sheet(max_atoms=3, max_cut_depth=1))
    try:
        egi = parse_egif(text)
    except Exception:
        assume(False)
        return None  # unreachable; assume(False) aborts

    all_ids = (
        [v.id for v in egi.V]
        + [e.id for e in egi.E]
        + [c.id for c in egi.Cut]
    )
    if not all_ids:
        assume(False)

    selection = draw(st.sets(st.sampled_from(all_ids)))
    return egi, frozenset(selection)


class TestClosureIdempotence:
    """Issue #8: compute_closure(compute_closure(g)) == compute_closure(g).

    The expansion in ``analyze_closure`` already iterates to a fixed point
    internally (up to 100 passes). Idempotence is the external guarantee:
    feeding the result back in does no further work and yields the same
    closed subgraph.
    """

    @settings(
        max_examples=120,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    )
    @given(egi_with_selection())
    def test_closure_is_a_fixed_point(self, egi_and_selection):
        egi, selection = egi_and_selection
        validator = SubgraphClosureValidator(egi)

        first = validator.analyze_closure(selection, allow_expansion=True)
        second = validator.analyze_closure(first.closed_subgraph, allow_expansion=True)

        # The closed subgraph itself is stable.
        assert first.closed_subgraph == second.closed_subgraph, (
            f"closure not idempotent: first={set(first.closed_subgraph)} "
            f"second={set(second.closed_subgraph)}"
        )
        # The second pass adds nothing.
        assert second.added_elements == set(), (
            f"second pass added elements: {second.added_elements}"
        )
        # The second pass classifies as closed (the strict check passes).
        assert second.is_closed, (
            f"second pass not closed; violations={[v.description for v in second.violations]}"
        )

    @settings(
        max_examples=120,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    )
    @given(egi_with_selection())
    def test_closure_is_a_superset_of_input(self, egi_and_selection):
        """Closure never removes elements from the selection — it only adds.

        This is a sanity check on the expansion: when ``allow_expansion=True``
        the returned ``closed_subgraph`` must contain every element of the
        original selection.
        """
        egi, selection = egi_and_selection
        validator = SubgraphClosureValidator(egi)

        result = validator.analyze_closure(selection, allow_expansion=True)

        assert selection <= result.closed_subgraph, (
            f"closure dropped elements: missing={selection - result.closed_subgraph}"
        )


def test_suite():
    """Run all subgraph closure tests."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    test_suite()
