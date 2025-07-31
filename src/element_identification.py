"""
Element Identification Utilities for Test Framework
Maps EGIF structural descriptions to actual graph element IDs

CHANGES: Created to bridge the gap between test probe descriptions (like "(Mortal x)")
and actual graph element IDs. Provides structural matching and element resolution.
"""

from typing import Dict, List, Set, Optional, Tuple
from egi_core_dau import RelationalGraphWithCuts, ElementID
from egif_parser_dau import parse_egif


class ElementIdentifier:
    """Identifies graph elements by their structural representation."""
    
    def __init__(self, graph: RelationalGraphWithCuts):
        self.graph = graph
        self._build_structural_index()
    
    def _build_structural_index(self):
        """Build index of elements by their structural properties."""
        self.vertices_by_label = {}
        self.edges_by_relation = {}
        self.cuts_by_nesting = {}
        
        # Index vertices by label and type
        for vertex in self.graph.V:
            key = (vertex.label, vertex.is_generic)
            if key not in self.vertices_by_label:
                self.vertices_by_label[key] = []
            self.vertices_by_label[key].append(vertex.id)
        
        # Index edges by relation name and incident vertices
        for edge in self.graph.E:
            relation_name = self.graph.get_relation_name(edge.id)
            incident_vertices = self.graph.get_incident_vertices(edge.id)
            
            # Get vertex labels for matching
            vertex_labels = []
            for vertex_id in incident_vertices:
                vertex = self.graph.get_vertex(vertex_id)
                vertex_labels.append((vertex.label, vertex.is_generic))
            
            key = (relation_name, tuple(vertex_labels))
            if key not in self.edges_by_relation:
                self.edges_by_relation[key] = []
            self.edges_by_relation[key].append(edge.id)
        
        # Index cuts by nesting level and context
        for cut in self.graph.Cut:
            context = self.graph.get_context(cut.id)
            nesting_level = self._get_nesting_level(cut.id)
            key = (context, nesting_level)
            if key not in self.cuts_by_nesting:
                self.cuts_by_nesting[key] = []
            self.cuts_by_nesting[key].append(cut.id)
    
    def _get_nesting_level(self, element_id: ElementID) -> int:
        """Get nesting level of element (0 = sheet, 1 = first cut, etc.)."""
        level = 0
        current = element_id
        while current != self.graph.sheet:
            current = self.graph.get_context(current)
            level += 1
        return level
    
    def find_vertex_by_structure(self, label: str, is_generic: bool = True, 
                                context_id: Optional[ElementID] = None) -> Optional[ElementID]:
        """Find vertex by label, type, and optionally context."""
        candidates = self.vertices_by_label.get((label, is_generic), [])
        
        if context_id is None:
            return candidates[0] if candidates else None
        
        # Filter by context
        for vertex_id in candidates:
            if self.graph.get_context(vertex_id) == context_id:
                return vertex_id
        
        return None
    
    def find_edge_by_structure(self, relation_name: str, vertex_labels: List[Tuple[str, bool]], 
                              context_id: Optional[ElementID] = None) -> Optional[ElementID]:
        """Find edge by relation name and incident vertex labels."""
        key = (relation_name, tuple(vertex_labels))
        candidates = self.edges_by_relation.get(key, [])
        
        if context_id is None:
            return candidates[0] if candidates else None
        
        # Filter by context
        for edge_id in candidates:
            if self.graph.get_context(edge_id) == context_id:
                return edge_id
        
        return None
    
    def find_elements_by_egif_probe(self, probe: str, context_hint: Optional[str] = None) -> List[ElementID]:
        """
        Find elements matching an EGIF probe string.
        
        Args:
            probe: EGIF string like "(Mortal x)", "[*y]", "~[(P x)]"
            context_hint: Optional context description like "positive context", "sheet"
        
        Returns:
            List of matching element IDs
        """
        try:
            # Parse the probe to understand its structure
            if probe.startswith('[') and probe.endswith(']'):
                # Isolated vertex
                return self._find_isolated_vertex(probe, context_hint)
            elif probe.startswith('(') and probe.endswith(')'):
                # Relation/edge
                return self._find_relation(probe, context_hint)
            elif probe.startswith('~[') and probe.endswith(']'):
                # Cut or subgraph
                return self._find_cut_or_subgraph(probe, context_hint)
            else:
                return []
        except Exception:
            return []
    
    def _find_isolated_vertex(self, probe: str, context_hint: Optional[str]) -> List[ElementID]:
        """Find isolated vertex from probe like '[*x]' or '["Alice"]'."""
        content = probe[1:-1]  # Remove brackets
        
        if content.startswith('*'):
            # Generic vertex
            label = content[1:]
            is_generic = True
        elif content.startswith('"') and content.endswith('"'):
            # Constant vertex
            label = content[1:-1]
            is_generic = False
        else:
            # Simple label
            label = content
            is_generic = True
        
        # Find matching vertices
        candidates = self.vertices_by_label.get((label, is_generic), [])
        
        # Filter by isolation and context if specified
        result = []
        for vertex_id in candidates:
            if self.graph.is_vertex_isolated(vertex_id):
                if context_hint is None:
                    result.append(vertex_id)
                else:
                    # Apply context filtering
                    vertex_context = self.graph.get_context(vertex_id)
                    if self._matches_context_hint(vertex_context, context_hint):
                        result.append(vertex_id)
        
        return result
    
    def _find_relation(self, probe: str, context_hint: Optional[str]) -> List[ElementID]:
        """Find relation from probe like '(Mortal x)' or '(Human *x)'."""
        # Simple parsing - extract relation name and arguments
        content = probe[1:-1]  # Remove parentheses
        parts = content.split()
        
        if not parts:
            return []
        
        relation_name = parts[0]
        vertex_specs = parts[1:]
        
        # Convert vertex specs to (label, is_generic) tuples
        vertex_labels = []
        for spec in vertex_specs:
            if spec.startswith('*'):
                vertex_labels.append((spec[1:], True))
            elif spec.startswith('"') and spec.endswith('"'):
                vertex_labels.append((spec[1:-1], False))
            else:
                vertex_labels.append((spec, False))  # Assume bound occurrence
        
        # Find matching edges
        candidates = self.edges_by_relation.get((relation_name, tuple(vertex_labels)), [])
        
        if context_hint is None:
            return candidates
        
        # Filter by context
        result = []
        for edge_id in candidates:
            edge_context = self.graph.get_context(edge_id)
            if self._matches_context_hint(edge_context, context_hint):
                result.append(edge_id)
        
        return result
    
    def _find_cut_or_subgraph(self, probe: str, context_hint: Optional[str]) -> List[ElementID]:
        """Find cut or subgraph from probe like '~[(P x)]'."""
        # For now, simple cut matching
        # Full implementation would parse the subgraph structure
        
        if probe == "~[]":
            # Empty cut
            for cut_id in [c.id for c in self.graph.Cut]:
                if not self.graph.get_area(cut_id):  # Empty area
                    return [cut_id]
        
        # For complex subgraphs, would need more sophisticated parsing
        return []
    
    def _matches_context_hint(self, context_id: ElementID, hint: str) -> bool:
        """Check if context matches the hint description."""
        if hint == "sheet" or hint == "on sheet":
            return context_id == self.graph.sheet
        elif "positive" in hint.lower():
            return self.graph.is_positive_context(context_id)
        elif "negative" in hint.lower():
            return self.graph.is_negative_context(context_id)
        elif "double cut" in hint.lower():
            # Check if context is inside double cut (positive context that's not sheet)
            return (self.graph.is_positive_context(context_id) and 
                   context_id != self.graph.sheet)
        else:
            return True  # No specific constraint
    
    def get_context_by_description(self, description: str) -> Optional[ElementID]:
        """Get context ID from description like 'after (B *y)', 'positive context'."""
        if description == "sheet" or "sheet" in description:
            return self.graph.sheet
        elif "positive context" in description:
            # Find a positive context (even nesting level)
            for cut_id in [c.id for c in self.graph.Cut]:
                if self.graph.is_positive_context(cut_id):
                    return cut_id
            return self.graph.sheet  # Sheet is always positive
        elif "negative context" in description:
            # Find a negative context (odd nesting level)
            for cut_id in [c.id for c in self.graph.Cut]:
                if self.graph.is_negative_context(cut_id):
                    return cut_id
        elif "after" in description or "beside" in description:
            # Extract element reference and find its context
            # This is simplified - full implementation would parse the reference
            return self.graph.sheet
        
        return None


def create_element_identifier(egif: str) -> ElementIdentifier:
    """Create element identifier for an EGIF string."""
    graph = parse_egif(egif)
    return ElementIdentifier(graph)


def find_element_in_graph(graph: RelationalGraphWithCuts, probe: str, 
                         context_hint: Optional[str] = None) -> Optional[ElementID]:
    """Convenience function to find single element in graph by probe."""
    identifier = ElementIdentifier(graph)
    matches = identifier.find_elements_by_egif_probe(probe, context_hint)
    return matches[0] if matches else None


def find_all_elements_in_graph(graph: RelationalGraphWithCuts, probe: str,
                              context_hint: Optional[str] = None) -> List[ElementID]:
    """Convenience function to find all elements in graph by probe."""
    identifier = ElementIdentifier(graph)
    return identifier.find_elements_by_egif_probe(probe, context_hint)

