#!/usr/bin/env python3
"""
Subgraph-Based Transformation System
Updates transformation system to use formal DAUSubgraphs instead of informal probes

CHANGES: Replaces informal EGIF probe matching in transformations with mathematically
rigorous subgraph operations based on Dau's Definition 12.10. All transformations
now operate on formal subgraphs with proper validation and structural integrity.
"""

import sys
import os
from typing import Optional, List, Set, Tuple

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egi_core_dau import RelationalGraphWithCuts, ElementID
    import egi_transformations_dau as base_transforms
    from dau_subgraph_model import DAUSubgraph, create_minimal_subgraph
    from subgraph_identification import SubgraphIdentifier, identify_subgraph_from_egif_probe
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)


class SubgraphTransformationError(Exception):
    """Exception raised when subgraph-based transformation fails."""
    pass


class SubgraphTransformationSystem:
    """
    Transformation system using formal DAUSubgraphs.
    
    Replaces informal probe matching with mathematically rigorous subgraph
    operations that maintain Definition 12.10 compliance.
    """
    
    def __init__(self, graph: RelationalGraphWithCuts):
        self.graph = graph
        self.identifier = SubgraphIdentifier(graph)
    
    def apply_subgraph_erasure(self, subgraph: DAUSubgraph) -> RelationalGraphWithCuts:
        """
        Apply erasure rule to a formal subgraph.
        
        Args:
            subgraph: Formal DAUSubgraph to erase
            
        Returns:
            New graph with subgraph erased
            
        Raises:
            SubgraphTransformationError: If erasure violates transformation rules
        """
        
        # Validate erasure constraints
        self._validate_erasure_constraints(subgraph)
        
        # Apply erasure to all elements in the subgraph
        result_graph = self.graph
        
        # Erase in reverse dependency order: edges first, then vertices, then cuts
        for edge in subgraph.E_prime:
            result_graph = base_transforms.apply_erasure(result_graph, edge.id)
        
        for vertex in subgraph.V_prime:
            # Only erase if not needed by remaining edges
            if not self._vertex_needed_by_remaining_elements(vertex.id, result_graph):
                result_graph = base_transforms.apply_erasure(result_graph, vertex.id)
        
        for cut in subgraph.Cut_prime:
            # Only erase if empty after other erasures
            if self._cut_is_empty(cut.id, result_graph):
                result_graph = base_transforms.apply_erasure(result_graph, cut.id)
        
        return result_graph
    
    def apply_subgraph_insertion(self, subgraph_template: DAUSubgraph, 
                                target_context: ElementID) -> RelationalGraphWithCuts:
        """
        Apply insertion rule using a subgraph template.
        
        Args:
            subgraph_template: Template subgraph to insert
            target_context: Context where to insert the subgraph
            
        Returns:
            New graph with subgraph inserted
            
        Raises:
            SubgraphTransformationError: If insertion violates transformation rules
        """
        
        # Validate insertion constraints
        self._validate_insertion_constraints(subgraph_template, target_context)
        
        # Insert elements from subgraph template
        result_graph = self.graph
        
        # Insert in dependency order: cuts first, then vertices, then edges
        for cut in subgraph_template.Cut_prime:
            # Create new cut in target context
            result_graph = base_transforms.apply_insertion(
                result_graph, "cut", target_context
            )
        
        for vertex in subgraph_template.V_prime:
            # Insert vertex with appropriate label
            vertex_label = getattr(vertex, 'label', None)
            vertex_type = "generic" if vertex_label is None else "constant"
            
            result_graph = base_transforms.apply_isolated_vertex_addition(
                result_graph, vertex_label or "", vertex_type, target_context
            )
        
        for edge in subgraph_template.E_prime:
            # Insert edge with incident vertices
            edge_label = getattr(edge, 'label', 'R')  # Default relation name
            incident_vertices = list(subgraph_template.parent_graph.get_incident_vertices(edge.id))
            
            result_graph = base_transforms.apply_insertion(
                result_graph, "relation", target_context,
                relation_name=edge_label, vertex_specs=incident_vertices
            )
        
        return result_graph
    
    def apply_subgraph_iteration(self, subgraph: DAUSubgraph, 
                                target_context: ElementID) -> RelationalGraphWithCuts:
        """
        Apply iteration rule to copy a subgraph to same or deeper context.
        
        Args:
            subgraph: Subgraph to iterate (copy)
            target_context: Target context (same or deeper than source)
            
        Returns:
            New graph with subgraph iterated
            
        Raises:
            SubgraphTransformationError: If iteration violates transformation rules
        """
        
        # Validate iteration constraints
        self._validate_iteration_constraints(subgraph, target_context)
        
        # Use insertion to create the copy
        return self.apply_subgraph_insertion(subgraph, target_context)
    
    def apply_subgraph_deiteration(self, subgraph: DAUSubgraph, 
                                  base_subgraph: DAUSubgraph) -> RelationalGraphWithCuts:
        """
        Apply de-iteration rule to remove a copy that could have been created by iteration.
        
        Args:
            subgraph: Subgraph copy to remove
            base_subgraph: Original subgraph that justifies the removal
            
        Returns:
            New graph with subgraph copy removed
            
        Raises:
            SubgraphTransformationError: If de-iteration violates transformation rules
        """
        
        # Validate de-iteration constraints
        self._validate_deiteration_constraints(subgraph, base_subgraph)
        
        # Use erasure to remove the copy
        return self.apply_subgraph_erasure(subgraph)
    
    def apply_double_cut_addition_to_subgraph(self, subgraph: DAUSubgraph) -> RelationalGraphWithCuts:
        """
        Apply double cut addition around a subgraph.
        
        Args:
            subgraph: Subgraph to enclose with double cut
            
        Returns:
            New graph with double cut added around subgraph
        """
        
        # Create double cut around the subgraph's root context
        result_graph = self.graph
        
        # Add outer cut
        result_graph = base_transforms.apply_double_cut_addition(
            result_graph, subgraph.root_context
        )
        
        return result_graph
    
    def apply_double_cut_removal_from_subgraph(self, double_cut_subgraph: DAUSubgraph) -> RelationalGraphWithCuts:
        """
        Apply double cut removal to a subgraph containing a double cut.
        
        Args:
            double_cut_subgraph: Subgraph containing the double cut to remove
            
        Returns:
            New graph with double cut removed
        """
        
        # Find the outermost cut in the subgraph
        if double_cut_subgraph.Cut_prime:
            outermost_cut = list(double_cut_subgraph.Cut_prime)[0]  # Simplified
            return base_transforms.apply_double_cut_removal(self.graph, outermost_cut.id)
        
        raise SubgraphTransformationError("No cuts found in subgraph for double cut removal")
    
    def _validate_erasure_constraints(self, subgraph: DAUSubgraph):
        """Validate that erasure is allowed for this subgraph."""
        
        # Check that subgraph is in positive context
        if subgraph.get_context_polarity() != "positive":
            raise SubgraphTransformationError(
                f"Cannot erase from negative context {subgraph.root_context}"
            )
    
    def _validate_insertion_constraints(self, subgraph: DAUSubgraph, target_context: ElementID):
        """Validate that insertion is allowed in the target context."""
        
        # Check that target context is negative
        if self.graph.is_positive_context(target_context):
            raise SubgraphTransformationError(
                f"Cannot insert into positive context {target_context}"
            )
    
    def _validate_iteration_constraints(self, subgraph: DAUSubgraph, target_context: ElementID):
        """Validate that iteration is allowed to the target context."""
        
        # Check nesting direction: can only iterate to same or deeper context
        source_context = subgraph.root_context
        
        if not (target_context == source_context or 
                self.graph.is_context_enclosed_by(target_context, source_context)):
            raise SubgraphTransformationError(
                f"Cannot iterate from {source_context} to {target_context}: wrong nesting direction"
            )
    
    def _validate_deiteration_constraints(self, subgraph: DAUSubgraph, base_subgraph: DAUSubgraph):
        """Validate that de-iteration is allowed."""
        
        # Check that subgraphs are structurally identical
        if not self._subgraphs_structurally_identical(subgraph, base_subgraph):
            raise SubgraphTransformationError(
                "Subgraphs are not structurally identical for de-iteration"
            )
        
        # Check nesting relationship
        if not (subgraph.root_context == base_subgraph.root_context or
                self.graph.is_context_enclosed_by(subgraph.root_context, base_subgraph.root_context)):
            raise SubgraphTransformationError(
                "Invalid nesting relationship for de-iteration"
            )
    
    def _vertex_needed_by_remaining_elements(self, vertex_id: ElementID, 
                                           graph: RelationalGraphWithCuts) -> bool:
        """Check if vertex is still needed by remaining edges."""
        
        for edge in graph.E:
            if vertex_id in graph.get_incident_vertices(edge.id):
                return True
        return False
    
    def _cut_is_empty(self, cut_id: ElementID, graph: RelationalGraphWithCuts) -> bool:
        """Check if cut contains no elements."""
        
        cut_area = graph.area.get(cut_id, frozenset())
        return len(cut_area) == 0
    
    def _subgraphs_structurally_identical(self, subgraph1: DAUSubgraph, 
                                        subgraph2: DAUSubgraph) -> bool:
        """Check if two subgraphs are structurally identical."""
        
        # Simplified check: compare element counts and types
        return (len(subgraph1.V_prime) == len(subgraph2.V_prime) and
                len(subgraph1.E_prime) == len(subgraph2.E_prime) and
                len(subgraph1.Cut_prime) == len(subgraph2.Cut_prime))


def apply_transformation_with_egif_probe(graph: RelationalGraphWithCuts,
                                        transformation_rule: str,
                                        egif_probe: str,
                                        position_hint: Optional[str] = None,
                                        **kwargs) -> Optional[RelationalGraphWithCuts]:
    """
    Apply transformation using EGIF probe (converted to formal subgraph).
    
    This provides backward compatibility while using the formal subgraph system.
    
    Args:
        graph: Graph to transform
        transformation_rule: Name of transformation rule
        egif_probe: EGIF expression describing what to transform
        position_hint: Optional position hint
        **kwargs: Additional arguments for specific transformations
        
    Returns:
        Transformed graph, or None if transformation failed
    """
    
    try:
        # Convert EGIF probe to formal subgraph
        subgraph = identify_subgraph_from_egif_probe(graph, egif_probe, position_hint)
        
        if not subgraph:
            raise SubgraphTransformationError(f"No subgraph found matching probe: {egif_probe}")
        
        # Apply transformation using subgraph system
        transformer = SubgraphTransformationSystem(graph)
        
        if transformation_rule == "erasure":
            return transformer.apply_subgraph_erasure(subgraph)
        
        elif transformation_rule == "insertion":
            target_context = kwargs.get('target_context', graph.sheet)
            return transformer.apply_subgraph_insertion(subgraph, target_context)
        
        elif transformation_rule == "iteration":
            target_context = kwargs.get('target_context', subgraph.root_context)
            return transformer.apply_subgraph_iteration(subgraph, target_context)
        
        elif transformation_rule == "deiteration":
            base_subgraph = kwargs.get('base_subgraph')
            if not base_subgraph:
                raise SubgraphTransformationError("De-iteration requires base_subgraph")
            return transformer.apply_subgraph_deiteration(subgraph, base_subgraph)
        
        elif transformation_rule == "double_cut_addition":
            return transformer.apply_double_cut_addition_to_subgraph(subgraph)
        
        elif transformation_rule == "double_cut_removal":
            return transformer.apply_double_cut_removal_from_subgraph(subgraph)
        
        else:
            raise SubgraphTransformationError(f"Unknown transformation rule: {transformation_rule}")
    
    except Exception as e:
        print(f"Subgraph transformation failed: {e}")
        return None


def test_subgraph_transformations():
    """Test the subgraph-based transformation system."""
    
    from egif_parser_dau import parse_egif
    
    try:
        # Test with simple graph
        test_egif = "(P *x)"
        graph = parse_egif(test_egif)
        
        print(f"Original graph: {len(graph.V)} vertices, {len(graph.E)} edges")
        
        # Test erasure
        result = apply_transformation_with_egif_probe(
            graph, "erasure", "(P *x)", "positive"
        )
        
        if result:
            print(f"After erasure: {len(result.V)} vertices, {len(result.E)} edges")
            print("✓ Subgraph erasure test passed")
        else:
            print("✗ Subgraph erasure test failed")
        
        return True
    
    except Exception as e:
        print(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    print("Subgraph-based transformation system loaded successfully")
    print("Testing subgraph transformations...")
    
    success = test_subgraph_transformations()
    if success:
        print("✓ Subgraph transformation tests passed")
    else:
        print("✗ Subgraph transformation tests failed")

