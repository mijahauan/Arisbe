"""
Subgraph closure validation for INS/ERA transformations.

Per Dau's formalism, INS and ERA only apply to CLOSED subgraphs - subgraphs with
no connections to elements outside the subgraph. This module provides:

1. Validation: Check if a selection forms a closed subgraph
2. Expansion: Automatically expand incomplete selections to achieve closure
3. Feedback: Detailed information about missing elements and closure violations

Beta graph support
------------------
In Beta graphs, lines of identity (vertices) can cross cut boundaries.  An edge
in area B may reference a vertex defined in an ancestor area A.  When computing
closure *relative to area B*, such vertices are **free** — they need not be
included in the subgraph.  Pass ``context_area`` to ``analyze_closure`` to
enable this Beta-aware behaviour.
"""

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts


@dataclass
class ClosureViolation:
    """Describes why a subgraph is not closed."""
    
    element_id: ElementID
    violation_type: str  # "edge_external_vertex", "vertex_external_edge", "cut_partial_contents"
    missing_elements: Set[ElementID]
    description: str


@dataclass
class ClosureAnalysis:
    """Result of analyzing subgraph closure."""
    
    is_closed: bool
    original_selection: FrozenSet[ElementID]
    closed_subgraph: FrozenSet[ElementID]  # Expanded to closure
    violations: List[ClosureViolation]
    added_elements: Set[ElementID]  # Elements added to achieve closure
    
    def get_summary(self) -> str:
        """Get human-readable summary of closure analysis."""
        if self.is_closed and not self.added_elements:
            return "✓ Selection forms a closed subgraph"
        elif self.is_closed and self.added_elements:
            count = len(self.added_elements)
            return f"✓ Selection expanded to closure (+{count} elements)"
        else:
            violation_count = len(self.violations)
            return f"✗ Selection cannot form closed subgraph ({violation_count} violations)"


class SubgraphClosureValidator:
    """
    Validates and expands subgraphs to ensure closure per Dau's requirements.
    
    A closed subgraph must satisfy:
    1. All edges in subgraph connect only to vertices in subgraph
       (Beta: vertices in ancestor areas of context_area are free)
    2. All vertices in subgraph that have edges in the SAME area
       must have those edges in subgraph
    3. All cuts in subgraph must have their full contents in subgraph
    4. Ligatures connecting vertices must be fully contained
    """
    
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        self._edge_ids = {e.id for e in egi.E}
        self._vertex_ids = {v.id for v in egi.V}
        self._cut_ids = {c.id for c in egi.Cut}
        # Pre-compute element-to-area mapping for Beta checks
        self._elem_area: Dict[ElementID, ElementID] = {}
        for area_id, contents in egi.area.items():
            for eid in contents:
                self._elem_area[eid] = area_id
    
    def _is_ancestor_area(self, ancestor: ElementID, descendant: ElementID) -> bool:
        """Return True if *ancestor* is the same as or encloses *descendant*."""
        current = descendant
        seen: Set[ElementID] = set()
        while current is not None and current not in seen:
            if current == ancestor:
                return True
            seen.add(current)
            if current == self.egi.sheet:
                return current == ancestor
            current = self._elem_area.get(current)
        return False

    def _vertex_is_free(self, vertex_id: ElementID,
                        context_area: Optional[ElementID]) -> bool:
        """Return True if *vertex_id* is in a strict ancestor of *context_area*.

        Free vertices live in an enclosing scope — they need not be included
        in the subgraph when computing closure relative to *context_area*.
        """
        if context_area is None:
            return False  # No Beta context — all vertices required
        v_area = self._elem_area.get(vertex_id)
        if v_area is None:
            return False
        if v_area == context_area:
            return False  # Same area — not free
        return self._is_ancestor_area(v_area, context_area)

    def analyze_closure(self, selection: FrozenSet[ElementID],
                       allow_expansion: bool = True,
                       context_area: Optional[ElementID] = None) -> ClosureAnalysis:
        """
        Analyze if selection forms a closed subgraph.
        
        Args:
            selection: Selected element IDs
            allow_expansion: If True, automatically expand to achieve closure
            context_area: (Beta) The area in which the subgraph resides.
                When provided, vertices in strict ancestor areas are treated
                as free and need not be included in the subgraph.
            
        Returns:
            ClosureAnalysis with validation results and expansion details
        """
        if not selection:
            return ClosureAnalysis(
                is_closed=True,
                original_selection=selection,
                closed_subgraph=selection,
                violations=[],
                added_elements=set()
            )
        
        # Start with original selection
        current_subgraph = set(selection)
        violations = []
        added_in_pass = set()
        
        # Iteratively expand until closure or no more expansions possible
        max_iterations = 100  # Prevent infinite loops
        for iteration in range(max_iterations):
            violations_this_pass = []
            added_in_pass = set()
            
            # Check each element for closure violations
            for elem_id in list(current_subgraph):
                if elem_id in self._edge_ids:
                    # Edge closure: all vertices in ν mapping must be included
                    # (Beta: vertices in ancestor areas are free)
                    edge_violations = self._check_edge_closure(
                        elem_id, current_subgraph, context_area)
                    if edge_violations:
                        violations_this_pass.extend(edge_violations)
                        if allow_expansion:
                            # Add missing vertices
                            for v in edge_violations:
                                added_in_pass.update(v.missing_elements)
                
                elif elem_id in self._vertex_ids:
                    # Vertex closure: all connecting edges must be included
                    # (Beta: only edges in the same area)
                    vertex_violations = self._check_vertex_closure(
                        elem_id, current_subgraph, context_area)
                    if vertex_violations:
                        violations_this_pass.extend(vertex_violations)
                        if allow_expansion:
                            # Add missing edges
                            for v in vertex_violations:
                                added_in_pass.update(v.missing_elements)
                
                elif elem_id in self._cut_ids:
                    # Cut closure: all contents must be included
                    cut_violations = self._check_cut_closure(elem_id, current_subgraph)
                    if cut_violations:
                        violations_this_pass.extend(cut_violations)
                        if allow_expansion:
                            # Add missing contents
                            for v in cut_violations:
                                added_in_pass.update(v.missing_elements)
            
            # Check for ligatures (identity connections between vertices)
            ligature_violations = self._check_ligature_closure(current_subgraph)
            if ligature_violations:
                violations_this_pass.extend(ligature_violations)
                # Note: Ligatures are edges, already handled by edge/vertex checks
            
            violations.extend(violations_this_pass)
            
            # If no expansions needed, we're done
            if not added_in_pass:
                break
            
            # Expand subgraph with added elements
            current_subgraph.update(added_in_pass)
        
        # Final validation
        is_closed = self._is_truly_closed(
            frozenset(current_subgraph), context_area)
        
        total_added = current_subgraph - set(selection)
        
        return ClosureAnalysis(
            is_closed=is_closed,
            original_selection=selection,
            closed_subgraph=frozenset(current_subgraph),
            violations=violations if not is_closed else [],
            added_elements=total_added
        )
    
    def _check_edge_closure(self, edge_id: ElementID,
                           current_subgraph: Set[ElementID],
                           context_area: Optional[ElementID] = None
                           ) -> List[ClosureViolation]:
        """Check if edge has all its vertices in subgraph.

        Beta: vertices in ancestor areas of *context_area* are free.
        """
        violations = []
        vertex_sequence = self.egi.nu.get(edge_id, ())
        
        missing_vertices = set()
        for vertex_id in vertex_sequence:
            if vertex_id not in current_subgraph:
                # Beta: skip free vertices (in ancestor area)
                if self._vertex_is_free(vertex_id, context_area):
                    continue
                missing_vertices.add(vertex_id)
        
        if missing_vertices:
            relation = self.egi.rel.get(edge_id, "?")
            violations.append(ClosureViolation(
                element_id=edge_id,
                violation_type="edge_external_vertex",
                missing_elements=missing_vertices,
                description=f"Edge {relation}({edge_id}) connects to vertices outside subgraph: {missing_vertices}"
            ))
        
        return violations
    
    def _check_vertex_closure(self, vertex_id: ElementID,
                             current_subgraph: Set[ElementID],
                             context_area: Optional[ElementID] = None
                             ) -> List[ClosureViolation]:
        """Check if vertex has all its connecting edges in subgraph.

        Beta: only edges in the same area as the vertex (or the context_area)
        are required.  Edges in descendant or sibling areas are independent.
        """
        violations = []
        missing_edges = set()
        v_area = self._elem_area.get(vertex_id)
        
        # Find all edges that connect to this vertex
        for edge in self.egi.E:
            vertex_sequence = self.egi.nu.get(edge.id, ())
            if vertex_id in vertex_sequence:
                # Beta: only require edges in the same area as the vertex
                if context_area is not None:
                    e_area = self._elem_area.get(edge.id)
                    if e_area != v_area:
                        continue  # Edge in a different area — independent

                # This edge connects to our vertex
                if edge.id not in current_subgraph:
                    # Check if the other end of the edge is in subgraph
                    other_vertices_in_subgraph = [
                        v for v in vertex_sequence 
                        if v != vertex_id and v in current_subgraph
                    ]
                    
                    if other_vertices_in_subgraph:
                        # Edge connects two vertices in subgraph but edge itself not included
                        missing_edges.add(edge.id)
        
        if missing_edges:
            violations.append(ClosureViolation(
                element_id=vertex_id,
                violation_type="vertex_external_edge",
                missing_elements=missing_edges,
                description=f"Vertex {vertex_id} has connecting edges outside subgraph: {missing_edges}"
            ))
        
        return violations
    
    def _check_cut_closure(self, cut_id: ElementID,
                          current_subgraph: Set[ElementID]) -> List[ClosureViolation]:
        """Check if cut has all its contents in subgraph."""
        violations = []
        cut_contents = self.egi.area.get(cut_id, frozenset())
        
        missing_contents = set()
        for content_id in cut_contents:
            if content_id not in current_subgraph:
                missing_contents.add(content_id)
        
        if missing_contents:
            violations.append(ClosureViolation(
                element_id=cut_id,
                violation_type="cut_partial_contents",
                missing_elements=missing_contents,
                description=f"Cut {cut_id} has contents outside subgraph: {missing_contents}"
            ))
        
        return violations
    
    def _check_ligature_closure(self, current_subgraph: Set[ElementID]) -> List[ClosureViolation]:
        """
        Check ligature closure.
        
        Ligatures are special identity edges connecting vertices. If vertices are
        connected by a ligature (identity relation), the ligature edge must be
        in the subgraph if both vertices are.
        """
        violations = []
        
        # Find all identity edges (ligatures)
        for edge in self.egi.E:
            relation = self.egi.rel.get(edge.id)
            if relation == "=" or str(relation).lower() == "identity":
                vertex_sequence = self.egi.nu.get(edge.id, ())
                
                # Check if both ends are in subgraph
                vertices_in_subgraph = [v for v in vertex_sequence if v in current_subgraph]
                
                if len(vertices_in_subgraph) == len(vertex_sequence) and len(vertices_in_subgraph) > 1:
                    # All vertices of ligature are in subgraph
                    if edge.id not in current_subgraph:
                        violations.append(ClosureViolation(
                            element_id=edge.id,
                            violation_type="ligature_external",
                            missing_elements={edge.id},
                            description=f"Ligature {edge.id} connects vertices in subgraph but is not included"
                        ))
        
        return violations
    
    def _is_truly_closed(self, subgraph: FrozenSet[ElementID],
                         context_area: Optional[ElementID] = None) -> bool:
        """Final strict validation that subgraph is closed.

        Beta: when *context_area* is set, vertices in ancestor areas are
        considered free and edges in other areas are independent.
        """
        subgraph_edges = {e_id for e_id in subgraph if e_id in self._edge_ids}
        
        for edge_id in subgraph_edges:
            vertex_sequence = self.egi.nu.get(edge_id, ())
            for vertex_id in vertex_sequence:
                if vertex_id not in subgraph:
                    # Beta: free vertex in ancestor area is OK
                    if self._vertex_is_free(vertex_id, context_area):
                        continue
                    return False
        
        # Check cuts have full contents
        subgraph_cuts = {c_id for c_id in subgraph if c_id in self._cut_ids}
        for cut_id in subgraph_cuts:
            cut_contents = self.egi.area.get(cut_id, frozenset())
            for content_id in cut_contents:
                if content_id not in subgraph:
                    return False
        
        # Check vertices have all connecting edges (if other end is in subgraph)
        subgraph_vertices = {v_id for v_id in subgraph if v_id in self._vertex_ids}
        for vertex_id in subgraph_vertices:
            v_area = self._elem_area.get(vertex_id)
            for edge in self.egi.E:
                vertex_sequence = self.egi.nu.get(edge.id, ())
                if vertex_id in vertex_sequence:
                    # Beta: only require edges in the same area as the vertex
                    if context_area is not None:
                        e_area = self._elem_area.get(edge.id)
                        if e_area != v_area:
                            continue
                    # Check if all vertices of this edge are in subgraph
                    all_vertices_in = all(
                        v in subgraph or self._vertex_is_free(v, context_area)
                        for v in vertex_sequence
                    )
                    if all_vertices_in and edge.id not in subgraph:
                        return False
        
        return True
    
    def get_expansion_description(self, analysis: ClosureAnalysis) -> str:
        """Get detailed description of what was added to achieve closure."""
        if not analysis.added_elements:
            return "No expansion needed - selection is already closed"
        
        lines = ["Elements added to achieve closure:"]
        
        for elem_id in sorted(analysis.added_elements, key=str):
            if elem_id in self._edge_ids:
                relation = self.egi.rel.get(elem_id, "?")
                vertex_seq = self.egi.nu.get(elem_id, ())
                lines.append(f"  • Edge: {relation}({elem_id}) connecting {list(vertex_seq)}")
            elif elem_id in self._vertex_ids:
                lines.append(f"  • Vertex: {elem_id}")
            elif elem_id in self._cut_ids:
                lines.append(f"  • Cut: {elem_id}")
            else:
                lines.append(f"  • Element: {elem_id}")
        
        return "\n".join(lines)
    
    def validate_for_transformation(self, selection: FrozenSet[ElementID],
                                   rule_name: str,
                                   context_area: Optional[ElementID] = None
                                   ) -> Tuple[bool, str, FrozenSet[ElementID]]:
        """
        Validate selection for INS/ERA transformation.
        
        Args:
            selection: Selected elements
            rule_name: Transformation rule (INS or ERA)
            context_area: (Beta) The operating area; vertices in ancestor
                areas are treated as free.
            
        Returns:
            (is_valid, message, expanded_selection)
        """
        if rule_name not in ["INS", "ERA"]:
            return True, "Not an INS/ERA rule", selection
        
        if not selection:
            return False, "No elements selected", selection
        
        # Analyze closure
        analysis = self.analyze_closure(selection, allow_expansion=True,
                                        context_area=context_area)
        
        if analysis.is_closed:
            if analysis.added_elements:
                count = len(analysis.added_elements)
                expansion_desc = self.get_expansion_description(analysis)
                message = f"✓ Selection expanded to closure (+{count} elements)\n{expansion_desc}"
                return True, message, analysis.closed_subgraph
            else:
                return True, "✓ Selection forms a closed subgraph", selection
        else:
            # Could not achieve closure
            violation_desc = "\n".join(v.description for v in analysis.violations[:3])
            message = f"✗ Selection cannot form closed subgraph:\n{violation_desc}"
            return False, message, selection


def create_validator(egi: RelationalGraphWithCuts) -> SubgraphClosureValidator:
    """Factory function to create a closure validator."""
    return SubgraphClosureValidator(egi)
