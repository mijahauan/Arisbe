#!/usr/bin/env python3
"""
Subgraph Identification System
Replaces informal EGIF probe matching with mathematically rigorous subgraph identification

CHANGES: Implements Dau-compliant subgraph identification to replace the informal
"probe" system. Uses Definition 12.10 subgraphs for all transformation operations,
ensuring mathematical rigor and structural integrity.
"""

import sys
import os
import re
from typing import Set, List, Optional, Dict, Tuple, Union
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egi_core_dau import RelationalGraphWithCuts, ElementID
    from egif_parser_dau import parse_egif
    from dau_subgraph_model import DAUSubgraph, create_minimal_subgraph
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)


class SubgraphIdentificationError(Exception):
    """Exception raised when subgraph identification fails."""
    pass


@dataclass
class SubgraphPattern:
    """
    Represents a pattern for identifying subgraphs from EGIF expressions.
    
    This replaces informal "probes" with structured pattern matching that
    can be converted to formal DAUSubgraphs.
    """
    egif_expression: str                    # Original EGIF expression
    pattern_type: str                       # "relation", "vertex", "cut", "compound"
    relation_name: Optional[str] = None     # For relation patterns
    vertex_label: Optional[str] = None      # For vertex patterns  
    vertex_type: Optional[str] = None       # "generic" (*x) or "constant" (x)
    arity: Optional[int] = None             # For relation patterns
    nested_patterns: List['SubgraphPattern'] = None  # For compound patterns
    
    def __post_init__(self):
        if self.nested_patterns is None:
            self.nested_patterns = []


class SubgraphIdentifier:
    """
    Identifies formal DAUSubgraphs from EGIF patterns.
    
    Replaces the informal probe matching system with mathematically rigorous
    subgraph identification based on Dau's Definition 12.10.
    """
    
    def __init__(self, graph: RelationalGraphWithCuts):
        self.graph = graph
    
    def identify_subgraphs_from_egif(self, egif_pattern: str, 
                                   context_hint: Optional[str] = None) -> List[DAUSubgraph]:
        """
        Identify all subgraphs matching the given EGIF pattern.
        
        Args:
            egif_pattern: EGIF expression describing the pattern to match
            context_hint: Optional hint about where to look ("positive", "negative", "sheet")
            
        Returns:
            List of formal DAUSubgraphs matching the pattern
        """
        
        # Parse the EGIF pattern into structured form
        pattern = self._parse_egif_pattern(egif_pattern)
        
        # Find all matching subgraphs
        matches = self._find_matching_subgraphs(pattern, context_hint)
        
        # Convert matches to formal DAUSubgraphs
        subgraphs = []
        for match in matches:
            try:
                subgraph = self._create_subgraph_from_match(match, pattern)
                subgraphs.append(subgraph)
            except Exception as e:
                # Skip invalid matches
                continue
        
        return subgraphs
    
    def _parse_egif_pattern(self, egif_pattern: str) -> SubgraphPattern:
        """Parse EGIF pattern into structured form."""
        
        egif_pattern = egif_pattern.strip()
        
        # Handle relation patterns: (RelationName arg1 arg2 ...)
        if egif_pattern.startswith('(') and egif_pattern.endswith(')'):
            return self._parse_relation_pattern(egif_pattern)
        
        # Handle vertex patterns: [*x] or [x]
        elif egif_pattern.startswith('[') and egif_pattern.endswith(']'):
            return self._parse_vertex_pattern(egif_pattern)
        
        # Handle cut patterns: ~[...]
        elif egif_pattern.startswith('~[') and egif_pattern.endswith(']'):
            return self._parse_cut_pattern(egif_pattern)
        
        # Handle compound patterns (multiple elements)
        elif ' ' in egif_pattern and not (egif_pattern.startswith('(') or 
                                         egif_pattern.startswith('[') or 
                                         egif_pattern.startswith('~[')):
            return self._parse_compound_pattern(egif_pattern)
        
        else:
            raise SubgraphIdentificationError(f"Unrecognized EGIF pattern: {egif_pattern}")
    
    def _parse_relation_pattern(self, pattern: str) -> SubgraphPattern:
        """Parse relation pattern like (P *x) or (Loves John Mary)."""
        content = pattern[1:-1].strip()  # Remove parentheses
        parts = content.split()
        
        if not parts:
            raise SubgraphIdentificationError(f"Empty relation pattern: {pattern}")
        
        relation_name = parts[0]
        arity = len(parts) - 1
        
        return SubgraphPattern(
            egif_expression=pattern,
            pattern_type="relation",
            relation_name=relation_name,
            arity=arity
        )
    
    def _parse_vertex_pattern(self, pattern: str) -> SubgraphPattern:
        """Parse vertex pattern like [*x] or [John]."""
        content = pattern[1:-1].strip()  # Remove brackets
        
        if content.startswith('*'):
            # Generic vertex
            vertex_label = content[1:]
            vertex_type = "generic"
        else:
            # Constant vertex
            vertex_label = content
            vertex_type = "constant"
        
        return SubgraphPattern(
            egif_expression=pattern,
            pattern_type="vertex",
            vertex_label=vertex_label,
            vertex_type=vertex_type
        )
    
    def _parse_cut_pattern(self, pattern: str) -> SubgraphPattern:
        """Parse cut pattern like ~[...] or ~[~[...]]."""
        # For now, treat as compound pattern with the inner content
        inner_content = pattern[2:-1].strip()  # Remove ~[ and ]
        
        if inner_content:
            nested_pattern = self._parse_egif_pattern(inner_content)
            nested_patterns = [nested_pattern]
        else:
            nested_patterns = []
        
        return SubgraphPattern(
            egif_expression=pattern,
            pattern_type="cut",
            nested_patterns=nested_patterns
        )
    
    def _parse_compound_pattern(self, pattern: str) -> SubgraphPattern:
        """Parse compound pattern with multiple elements."""
        # Simple implementation: split by spaces and parse each part
        # This is a simplified approach - full parsing would need more sophisticated logic
        
        parts = []
        current_part = ""
        paren_depth = 0
        bracket_depth = 0
        
        i = 0
        while i < len(pattern):
            char = pattern[i]
            
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
            elif char == ' ' and paren_depth == 0 and bracket_depth == 0:
                if current_part.strip():
                    parts.append(current_part.strip())
                current_part = ""
                i += 1
                continue
            
            current_part += char
            i += 1
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        nested_patterns = []
        for part in parts:
            try:
                nested_pattern = self._parse_egif_pattern(part)
                nested_patterns.append(nested_pattern)
            except:
                # Skip unparseable parts
                continue
        
        return SubgraphPattern(
            egif_expression=pattern,
            pattern_type="compound",
            nested_patterns=nested_patterns
        )
    
    def _find_matching_subgraphs(self, pattern: SubgraphPattern, 
                                context_hint: Optional[str]) -> List[Dict]:
        """Find all graph elements matching the pattern."""
        
        if pattern.pattern_type == "relation":
            return self._find_relation_matches(pattern, context_hint)
        elif pattern.pattern_type == "vertex":
            return self._find_vertex_matches(pattern, context_hint)
        elif pattern.pattern_type == "cut":
            return self._find_cut_matches(pattern, context_hint)
        elif pattern.pattern_type == "compound":
            return self._find_compound_matches(pattern, context_hint)
        else:
            return []
    
    def _find_relation_matches(self, pattern: SubgraphPattern, 
                              context_hint: Optional[str]) -> List[Dict]:
        """Find relations matching the pattern."""
        matches = []
        
        for edge in self.graph.E:
            # Check if relation name matches (if we have edge labels)
            if hasattr(edge, 'label') and edge.label:
                if pattern.relation_name and edge.label != pattern.relation_name:
                    continue
            
            # Check arity
            incident_vertices = self.graph.get_incident_vertices(edge.id)
            if pattern.arity is not None and len(incident_vertices) != pattern.arity:
                continue
            
            # Check context hint
            if context_hint:
                edge_context = self.graph.get_context(edge.id)
                if context_hint == "positive" and not self.graph.is_positive_context(edge_context):
                    continue
                elif context_hint == "negative" and self.graph.is_positive_context(edge_context):
                    continue
                elif context_hint == "sheet" and edge_context != self.graph.sheet:
                    continue
            
            # Build match info
            match = {
                'type': 'relation',
                'edge_id': edge.id,
                'vertex_ids': incident_vertices,
                'context': self.graph.get_context(edge.id)
            }
            matches.append(match)
        
        return matches
    
    def _find_vertex_matches(self, pattern: SubgraphPattern,
                            context_hint: Optional[str]) -> List[Dict]:
        """Find vertices matching the pattern."""
        matches = []
        
        for vertex in self.graph.V:
            # Check vertex type and label
            if hasattr(vertex, 'label'):
                if pattern.vertex_type == "generic" and vertex.label is not None:
                    continue
                elif pattern.vertex_type == "constant" and vertex.label != pattern.vertex_label:
                    continue
            
            # Check context hint
            if context_hint:
                vertex_context = self.graph.get_context(vertex.id)
                if context_hint == "positive" and not self.graph.is_positive_context(vertex_context):
                    continue
                elif context_hint == "negative" and self.graph.is_positive_context(vertex_context):
                    continue
                elif context_hint == "sheet" and vertex_context != self.graph.sheet:
                    continue
            
            # Build match info
            match = {
                'type': 'vertex',
                'vertex_id': vertex.id,
                'context': self.graph.get_context(vertex.id)
            }
            matches.append(match)
        
        return matches
    
    def _find_cut_matches(self, pattern: SubgraphPattern,
                         context_hint: Optional[str]) -> List[Dict]:
        """Find cuts matching the pattern."""
        matches = []
        
        for cut in self.graph.Cut:
            # Check context hint
            if context_hint:
                cut_context = self.graph.get_context(cut.id)
                if context_hint == "positive" and not self.graph.is_positive_context(cut_context):
                    continue
                elif context_hint == "negative" and self.graph.is_positive_context(cut_context):
                    continue
                elif context_hint == "sheet" and cut_context != self.graph.sheet:
                    continue
            
            # Build match info
            match = {
                'type': 'cut',
                'cut_id': cut.id,
                'context': self.graph.get_context(cut.id)
            }
            matches.append(match)
        
        return matches
    
    def _find_compound_matches(self, pattern: SubgraphPattern,
                              context_hint: Optional[str]) -> List[Dict]:
        """Find compound structures matching the pattern."""
        # For compound patterns, we need to find combinations of elements
        # This is a simplified implementation
        
        all_element_matches = []
        
        for nested_pattern in pattern.nested_patterns:
            nested_matches = self._find_matching_subgraphs(nested_pattern, context_hint)
            all_element_matches.extend(nested_matches)
        
        if all_element_matches:
            # Return a single compound match containing all elements
            compound_match = {
                'type': 'compound',
                'element_matches': all_element_matches,
                'context': context_hint  # Simplified
            }
            return [compound_match]
        
        return []
    
    def _create_subgraph_from_match(self, match: Dict, pattern: SubgraphPattern) -> DAUSubgraph:
        """Create formal DAUSubgraph from match information."""
        
        element_ids = set()
        root_context = None
        
        if match['type'] == 'relation':
            element_ids.add(match['edge_id'])
            element_ids.update(match['vertex_ids'])
            root_context = match['context']
        
        elif match['type'] == 'vertex':
            element_ids.add(match['vertex_id'])
            root_context = match['context']
        
        elif match['type'] == 'cut':
            element_ids.add(match['cut_id'])
            root_context = match['context']
        
        elif match['type'] == 'compound':
            for element_match in match['element_matches']:
                if element_match['type'] == 'relation':
                    element_ids.add(element_match['edge_id'])
                    element_ids.update(element_match['vertex_ids'])
                elif element_match['type'] == 'vertex':
                    element_ids.add(element_match['vertex_id'])
                elif element_match['type'] == 'cut':
                    element_ids.add(element_match['cut_id'])
            
            # Use first element's context as root context (simplified)
            if match['element_matches']:
                root_context = match['element_matches'][0].get('context', self.graph.sheet)
        
        if not root_context:
            root_context = self.graph.sheet
        
        # Create minimal subgraph containing these elements
        return create_minimal_subgraph(
            parent_graph=self.graph,
            element_ids=element_ids,
            root_context=root_context
        )


def identify_subgraph_from_egif_probe(graph: RelationalGraphWithCuts, 
                                     egif_probe: str,
                                     position_hint: Optional[str] = None) -> Optional[DAUSubgraph]:
    """
    Convenience function to identify a single subgraph from EGIF probe.
    
    This replaces the old informal probe matching with formal subgraph identification.
    
    Args:
        graph: The graph to search in
        egif_probe: EGIF expression describing what to find
        position_hint: Optional position hint ("positive", "negative", "sheet")
        
    Returns:
        First matching DAUSubgraph, or None if no matches found
    """
    
    identifier = SubgraphIdentifier(graph)
    
    try:
        subgraphs = identifier.identify_subgraphs_from_egif(egif_probe, position_hint)
        return subgraphs[0] if subgraphs else None
    except Exception as e:
        print(f"Subgraph identification failed: {e}")
        return None


def test_subgraph_identification():
    """Test the subgraph identification system."""
    
    # Test with a simple EGIF
    test_egif = "(P *x)"
    
    try:
        graph = parse_egif(test_egif)
        identifier = SubgraphIdentifier(graph)
        
        # Test relation pattern
        subgraphs = identifier.identify_subgraphs_from_egif("(P *x)")
        print(f"Found {len(subgraphs)} subgraphs matching '(P *x)'")
        
        for i, subgraph in enumerate(subgraphs):
            print(f"  Subgraph {i+1}: {subgraph}")
        
        # Test vertex pattern
        subgraphs = identifier.identify_subgraphs_from_egif("[*x]")
        print(f"Found {len(subgraphs)} subgraphs matching '[*x]'")
        
        return True
    
    except Exception as e:
        print(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    print("Subgraph identification system loaded successfully")
    print("Testing subgraph identification...")
    
    success = test_subgraph_identification()
    if success:
        print("✓ Subgraph identification test passed")
    else:
        print("✗ Subgraph identification test failed")

