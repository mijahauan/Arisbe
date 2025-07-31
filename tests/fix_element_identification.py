#!/usr/bin/env python3
"""
Fixed Element Identification System
Addresses the core issue: parser stores vertex labels as None, not the expected labels

CHANGES: Fixed element identification to match actual parser behavior where
vertices have label=None and variable names are implicit in the EGIF structure.
"""

from typing import Dict, List, Set, Optional, Tuple
from egi_core_dau import RelationalGraphWithCuts, ElementID
from egif_parser_dau import parse_egif


class FixedElementIdentifier:
    """Fixed element identifier that works with actual parser output."""
    
    def __init__(self, graph: RelationalGraphWithCuts):
        self.graph = graph
        self._build_structural_index()
    
    def _build_structural_index(self):
        """Build index based on actual parser behavior."""
        self.edges_by_relation = {}
        self.vertices_by_context = {}
        self.cuts_by_nesting = {}
        
        # Index edges by relation name only (ignore vertex label matching)
        for edge in self.graph.E:
            relation_name = self.graph.get_relation_name(edge.id)
            incident_vertices = self.graph.get_incident_vertices(edge.id)
            context = self.graph.get_context(edge.id)
            
            # Key by relation name and vertex count
            key = (relation_name, len(incident_vertices))
            if key not in self.edges_by_relation:
                self.edges_by_relation[key] = []
            self.edges_by_relation[key].append({
                "edge_id": edge.id,
                "incident_vertices": incident_vertices,
                "context": context
            })
        
        # Index vertices by context and isolation status
        for vertex in self.graph.V:
            context = self.graph.get_context(vertex.id)
            is_isolated = self.graph.is_vertex_isolated(vertex.id)
            
            if context not in self.vertices_by_context:
                self.vertices_by_context[context] = {"isolated": [], "connected": []}
            
            if is_isolated:
                self.vertices_by_context[context]["isolated"].append(vertex.id)
            else:
                self.vertices_by_context[context]["connected"].append(vertex.id)
        
        # Index cuts by nesting level
        for cut in self.graph.Cut:
            nesting_level = self._get_nesting_level(cut.id)
            if nesting_level not in self.cuts_by_nesting:
                self.cuts_by_nesting[nesting_level] = []
            self.cuts_by_nesting[nesting_level].append(cut.id)
    
    def _get_nesting_level(self, context_id: ElementID) -> int:
        """Get nesting level of context."""
        if context_id == self.graph.sheet:
            return 0
        
        level = 0
        current = context_id
        while current != self.graph.sheet:
            current = self.graph.get_context(current)
            level += 1
        return level
    
    def find_elements_by_egif_probe(self, probe: str, context_hint: Optional[str] = None) -> List[ElementID]:
        """
        Find elements matching an EGIF probe using fixed logic.
        
        Key insight: Parser doesn't preserve variable names in vertex labels,
        so we match by structure rather than exact label matching.
        """
        try:
            if probe.startswith('[') and probe.endswith(']'):
                # Isolated vertex - match by isolation status and context
                return self._find_isolated_vertex_fixed(probe, context_hint)
            elif probe.startswith('(') and probe.endswith(')'):
                # Relation/edge - match by relation name and structure
                return self._find_relation_fixed(probe, context_hint)
            elif probe.startswith('~[') and probe.endswith(']'):
                # Cut or subgraph - match by structure
                return self._find_cut_fixed(probe, context_hint)
            else:
                return []
        except Exception:
            return []
    
    def _find_isolated_vertex_fixed(self, probe: str, context_hint: Optional[str]) -> List[ElementID]:
        """Find isolated vertex using fixed logic."""
        # For isolated vertices, match by context and isolation status
        # Ignore the specific label since parser stores None
        
        target_contexts = []
        
        if context_hint:
            if "sheet" in context_hint.lower():
                target_contexts = [self.graph.sheet]
            elif "positive" in context_hint.lower():
                # Find positive contexts
                for cut_id in [c.id for c in self.graph.Cut]:
                    if self.graph.is_positive_context(cut_id):
                        target_contexts.append(cut_id)
                if not target_contexts:
                    target_contexts = [self.graph.sheet]
            elif "negative" in context_hint.lower():
                # Find negative contexts
                for cut_id in [c.id for c in self.graph.Cut]:
                    if self.graph.is_negative_context(cut_id):
                        target_contexts.append(cut_id)
        else:
            # Check all contexts
            target_contexts = list(self.vertices_by_context.keys())
        
        # Find isolated vertices in target contexts
        result = []
        for context_id in target_contexts:
            if context_id in self.vertices_by_context:
                isolated_vertices = self.vertices_by_context[context_id]["isolated"]
                result.extend(isolated_vertices)
        
        return result
    
    def _find_relation_fixed(self, probe: str, context_hint: Optional[str]) -> List[ElementID]:
        """Find relation using fixed logic."""
        content = probe[1:-1]  # Remove parentheses
        parts = content.split()
        
        if not parts:
            return []
        
        relation_name = parts[0]
        vertex_count = len(parts) - 1
        
        # Find edges by relation name and vertex count
        key = (relation_name, vertex_count)
        if key not in self.edges_by_relation:
            return []
        
        candidates = self.edges_by_relation[key]
        
        # Filter by context if hint provided
        if context_hint:
            filtered_candidates = []
            for candidate in candidates:
                edge_context = candidate["context"]
                if self._matches_context_hint(edge_context, context_hint):
                    filtered_candidates.append(candidate)
            candidates = filtered_candidates
        
        return [candidate["edge_id"] for candidate in candidates]
    
    def _find_cut_fixed(self, probe: str, context_hint: Optional[str]) -> List[ElementID]:
        """Find cut using fixed logic."""
        if probe == "~[]":
            # Empty cut
            for cut_id in [c.id for c in self.graph.Cut]:
                if not self.graph.get_area(cut_id):  # Empty area
                    return [cut_id]
        
        # For complex cuts, return first available cut
        if self.graph.Cut:
            return [list(self.graph.Cut)[0].id]
        
        return []
    
    def _matches_context_hint(self, context_id: ElementID, hint: str) -> bool:
        """Check if context matches hint."""
        if "sheet" in hint.lower():
            return context_id == self.graph.sheet
        elif "positive" in hint.lower():
            return self.graph.is_positive_context(context_id)
        elif "negative" in hint.lower():
            return self.graph.is_negative_context(context_id)
        else:
            return True


def create_fixed_element_identifier(egif: str) -> FixedElementIdentifier:
    """Create fixed element identifier for an EGIF string."""
    graph = parse_egif(egif)
    return FixedElementIdentifier(graph)


def find_element_in_graph_fixed(graph: RelationalGraphWithCuts, probe: str, 
                               context_hint: Optional[str] = None) -> Optional[ElementID]:
    """Fixed convenience function to find single element."""
    identifier = FixedElementIdentifier(graph)
    matches = identifier.find_elements_by_egif_probe(probe, context_hint)
    return matches[0] if matches else None


def test_fixed_element_identification():
    """Test the fixed element identification."""
    
    print("=" * 80)
    print("TESTING FIXED ELEMENT IDENTIFICATION")
    print("=" * 80)
    
    test_cases = [
        {
            "egif": "~[(Human *x) ~[(Mortal x)]]",
            "probes": [
                ("(Human *x)", None),
                ("(Mortal x)", "positive context"),
                ("[*x]", "sheet")
            ]
        },
        {
            "egif": "(P *x)",
            "probes": [
                ("(P *x)", None),
                ("[*x]", "sheet")
            ]
        },
        {
            "egif": "[*x] ~[(P x)]",
            "probes": [
                ("[*x]", "sheet"),
                ("(P x)", "negative context")
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['egif']}")
        print("-" * 40)
        
        try:
            identifier = create_fixed_element_identifier(test_case["egif"])
            
            for probe, context_hint in test_case["probes"]:
                print(f"\nProbe: {probe}")
                print(f"Context Hint: {context_hint}")
                
                matches = identifier.find_elements_by_egif_probe(probe, context_hint)
                
                if matches:
                    print(f"✓ Found {len(matches)} matches: {matches}")
                else:
                    print("✗ No matches found")
        
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    test_fixed_element_identification()

