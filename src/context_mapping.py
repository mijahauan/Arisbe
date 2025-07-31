"""
Context Mapping Utilities for Test Framework
Maps position descriptions to actual graph context IDs

CHANGES: Created to map test position descriptions (like "after (B *y)", "positive context")
to actual graph context IDs. Handles context hierarchy and polarity determination.
"""

from typing import Dict, List, Set, Optional, Tuple
from egi_core_dau import RelationalGraphWithCuts, ElementID
from element_identification import ElementIdentifier


class ContextMapper:
    """Maps position descriptions to graph context IDs."""
    
    def __init__(self, graph: RelationalGraphWithCuts):
        self.graph = graph
        self.identifier = ElementIdentifier(graph)
        self._build_context_index()
    
    def _build_context_index(self):
        """Build index of contexts by their properties."""
        self.contexts_by_polarity = {"positive": [], "negative": []}
        self.contexts_by_nesting = {}
        
        # Always include sheet as positive context
        self.contexts_by_polarity["positive"].append(self.graph.sheet)
        self.contexts_by_nesting[0] = [self.graph.sheet]
        
        # Index cuts by polarity and nesting level
        for cut in self.graph.Cut:
            nesting_level = self._get_nesting_level(cut.id)
            
            # Determine polarity (even = positive, odd = negative)
            if nesting_level % 2 == 0:
                polarity = "positive"
            else:
                polarity = "negative"
            
            self.contexts_by_polarity[polarity].append(cut.id)
            
            if nesting_level not in self.contexts_by_nesting:
                self.contexts_by_nesting[nesting_level] = []
            self.contexts_by_nesting[nesting_level].append(cut.id)
    
    def _get_nesting_level(self, context_id: ElementID) -> int:
        """Get nesting level of context (0 = sheet, 1 = first cut, etc.)."""
        if context_id == self.graph.sheet:
            return 0
        
        level = 0
        current = context_id
        while current != self.graph.sheet:
            current = self.graph.get_context(current)
            level += 1
        return level
    
    def get_context_by_position_description(self, position: str, 
                                          base_egif: Optional[str] = None) -> Optional[ElementID]:
        """
        Map position description to context ID.
        
        Args:
            position: Description like "after (B *y)", "positive context", "sheet"
            base_egif: Base EGIF for element reference resolution
            
        Returns:
            Context ID or None if not found
        """
        position_lower = position.lower()
        
        # Direct context references
        if "sheet" in position_lower or position_lower == "on sheet":
            return self.graph.sheet
        
        if "positive context" in position_lower:
            return self._find_suitable_positive_context()
        
        if "negative context" in position_lower:
            return self._find_suitable_negative_context()
        
        if "double cut" in position_lower:
            return self._find_double_cut_context()
        
        # Relative position references
        if "after" in position_lower or "beside" in position_lower:
            return self._resolve_relative_position(position, base_egif)
        
        # Specific context descriptions
        if "inner context" in position_lower:
            return self._find_innermost_context()
        
        if "outer context" in position_lower or "outermost" in position_lower:
            return self._find_outermost_context()
        
        # Nesting level references
        if "first cut" in position_lower:
            contexts = self.contexts_by_nesting.get(1, [])
            return contexts[0] if contexts else None
        
        if "second cut" in position_lower:
            contexts = self.contexts_by_nesting.get(2, [])
            return contexts[0] if contexts else None
        
        # Default to sheet
        return self.graph.sheet
    
    def _find_suitable_positive_context(self) -> Optional[ElementID]:
        """Find a suitable positive context (even nesting level)."""
        positive_contexts = self.contexts_by_polarity["positive"]
        
        # Prefer non-sheet positive contexts if available
        non_sheet = [ctx for ctx in positive_contexts if ctx != self.graph.sheet]
        if non_sheet:
            return non_sheet[0]
        
        return self.graph.sheet
    
    def _find_suitable_negative_context(self) -> Optional[ElementID]:
        """Find a suitable negative context (odd nesting level)."""
        negative_contexts = self.contexts_by_polarity["negative"]
        return negative_contexts[0] if negative_contexts else None
    
    def _find_double_cut_context(self) -> Optional[ElementID]:
        """Find context inside a double cut (positive context that's not sheet)."""
        for context_id in self.contexts_by_polarity["positive"]:
            if context_id != self.graph.sheet:
                # Check if it's inside a double cut structure
                parent = self.graph.get_context(context_id)
                if parent in self.contexts_by_polarity["negative"]:
                    return context_id
        return None
    
    def _find_innermost_context(self) -> Optional[ElementID]:
        """Find the most deeply nested context."""
        max_level = max(self.contexts_by_nesting.keys()) if self.contexts_by_nesting else 0
        contexts = self.contexts_by_nesting.get(max_level, [])
        return contexts[0] if contexts else self.graph.sheet
    
    def _find_outermost_context(self) -> Optional[ElementID]:
        """Find the outermost context (sheet or first level cut)."""
        if 1 in self.contexts_by_nesting:
            return self.contexts_by_nesting[1][0]
        return self.graph.sheet
    
    def _resolve_relative_position(self, position: str, base_egif: Optional[str]) -> Optional[ElementID]:
        """Resolve relative position like 'after (B *y)' or 'beside (Human *x)'."""
        if not base_egif:
            return self.graph.sheet
        
        # Extract element reference from position
        element_ref = self._extract_element_reference(position)
        if not element_ref:
            return self.graph.sheet
        
        # Find the referenced element
        element_ids = self.identifier.find_elements_by_egif_probe(element_ref)
        if not element_ids:
            return self.graph.sheet
        
        # Return the context of the referenced element
        return self.graph.get_context(element_ids[0])
    
    def _extract_element_reference(self, position: str) -> Optional[str]:
        """Extract element reference from position description."""
        # Look for patterns like "after (B *y)" or "beside [*x]"
        import re
        
        # Match parentheses content
        paren_match = re.search(r'\(([^)]+)\)', position)
        if paren_match:
            return f"({paren_match.group(1)})"
        
        # Match bracket content
        bracket_match = re.search(r'\[([^\]]+)\]', position)
        if bracket_match:
            return f"[{bracket_match.group(1)}]"
        
        return None
    
    def get_context_for_transformation(self, rule_name: str, position: str, 
                                     base_egif: Optional[str] = None) -> Optional[ElementID]:
        """
        Get appropriate context for a specific transformation rule.
        
        Args:
            rule_name: Name of transformation rule (e.g., "erasure", "insertion")
            position: Position description
            base_egif: Base EGIF for context
            
        Returns:
            Context ID appropriate for the transformation
        """
        context_id = self.get_context_by_position_description(position, base_egif)
        
        if context_id is None:
            return self.graph.sheet
        
        # Apply rule-specific context requirements
        if rule_name.lower() == "insertion":
            # Insertion requires negative context
            if not self.graph.is_negative_context(context_id):
                # Find a negative context
                return self._find_suitable_negative_context() or self.graph.sheet
        
        elif rule_name.lower() == "erasure":
            # Erasure requires positive context
            if not self.graph.is_positive_context(context_id):
                # Find a positive context
                return self._find_suitable_positive_context() or self.graph.sheet
        
        return context_id
    
    def validate_context_for_rule(self, context_id: ElementID, rule_name: str) -> bool:
        """Validate that context is appropriate for transformation rule."""
        if rule_name.lower() == "insertion":
            return self.graph.is_negative_context(context_id)
        elif rule_name.lower() == "erasure":
            return self.graph.is_positive_context(context_id)
        elif rule_name.lower() in ["iteration", "de_iteration"]:
            # Iteration rules have more complex context requirements
            return True  # Simplified for now
        else:
            # Other rules (double cut, isolated vertex) can work in any context
            return True
    
    def get_context_hierarchy(self) -> Dict[int, List[ElementID]]:
        """Get context hierarchy organized by nesting level."""
        return dict(self.contexts_by_nesting)
    
    def get_context_polarity_map(self) -> Dict[str, List[ElementID]]:
        """Get contexts organized by polarity."""
        return dict(self.contexts_by_polarity)
    
    def find_context_containing_elements(self, element_ids: List[ElementID]) -> Optional[ElementID]:
        """Find the most specific context that contains all given elements."""
        if not element_ids:
            return None
        
        # Get contexts of all elements
        element_contexts = [self.graph.get_context(eid) for eid in element_ids]
        
        # Find common ancestor context
        common_context = element_contexts[0]
        for context in element_contexts[1:]:
            common_context = self._find_common_ancestor(common_context, context)
        
        return common_context
    
    def _find_common_ancestor(self, context1: ElementID, context2: ElementID) -> ElementID:
        """Find common ancestor context of two contexts."""
        if context1 == context2:
            return context1
        
        # Get paths to sheet
        path1 = self._get_path_to_sheet(context1)
        path2 = self._get_path_to_sheet(context2)
        
        # Find common ancestor
        for ctx in path1:
            if ctx in path2:
                return ctx
        
        return self.graph.sheet
    
    def _get_path_to_sheet(self, context_id: ElementID) -> List[ElementID]:
        """Get path from context to sheet."""
        path = []
        current = context_id
        while current != self.graph.sheet:
            path.append(current)
            current = self.graph.get_context(current)
        path.append(self.graph.sheet)
        return path


def create_context_mapper(egif: str) -> ContextMapper:
    """Create context mapper for an EGIF string."""
    from egif_parser_dau import parse_egif
    graph = parse_egif(egif)
    return ContextMapper(graph)


def get_context_for_position(graph: RelationalGraphWithCuts, position: str, 
                           base_egif: Optional[str] = None) -> Optional[ElementID]:
    """Convenience function to get context ID for position description."""
    mapper = ContextMapper(graph)
    return mapper.get_context_by_position_description(position, base_egif)

