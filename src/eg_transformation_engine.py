#!/usr/bin/env python3
"""
Existential Graph Transformation Engine

Implements formal EG transformation rules with validation:
- Erasure: Remove elements from positive contexts
- Insertion: Add elements to negative contexts  
- Iteration: Copy elements across cut boundaries
- Deiteration: Remove duplicate elements
- Double Cut: Add/remove double cuts (logical equivalence)
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from dataclasses import dataclass, replace
from enum import Enum
from copy import deepcopy

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from mode_aware_selection import Mode, ActionType


class TransformationRule(Enum):
    """Formal EG transformation rules."""
    ERASURE = "erasure"                    # Remove from positive context
    INSERTION = "insertion"                # Add to negative context
    ITERATION = "iteration"                # Copy across cut boundary
    DEITERATION = "deiteration"           # Remove duplicate
    DOUBLE_CUT_ADDITION = "double_cut_addition"      # Add double cut
    DOUBLE_CUT_REMOVAL = "double_cut_removal"        # Remove double cut
    ISOLATED_VERTEX_ADDITION = "isolated_vertex_addition"  # Add isolated vertex


@dataclass
class TransformationContext:
    """Context information for transformation validation."""
    element_id: ElementID
    containing_cuts: List[ElementID]  # Cuts containing this element
    context_polarity: str            # "positive" or "negative"
    nesting_level: int               # Depth of nesting


@dataclass
class TransformationResult:
    """Result of a transformation operation."""
    success: bool
    new_egi: Optional[RelationalGraphWithCuts] = None
    error_message: Optional[str] = None
    warnings: List[str] = None
    applied_rule: Optional[TransformationRule] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ContextAnalyzer:
    """Analyzes EGI context and polarity for transformation validation."""
    
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        self._context_cache: Dict[ElementID, TransformationContext] = {}
    
    def get_context(self, element_id: ElementID) -> TransformationContext:
        """Get transformation context for an element."""
        if element_id in self._context_cache:
            return self._context_cache[element_id]
        
        context = self._analyze_element_context(element_id)
        self._context_cache[element_id] = context
        return context
    
    def _analyze_element_context(self, element_id: ElementID) -> TransformationContext:
        """Analyze the context of a specific element."""
        containing_cuts = self._find_containing_cuts(element_id)
        nesting_level = len(containing_cuts)
        
        # Determine polarity: even nesting = positive, odd nesting = negative
        context_polarity = "positive" if nesting_level % 2 == 0 else "negative"
        
        return TransformationContext(
            element_id=element_id,
            containing_cuts=containing_cuts,
            context_polarity=context_polarity,
            nesting_level=nesting_level
        )
    
    def _find_containing_cuts(self, element_id: ElementID) -> List[ElementID]:
        """Find all cuts that contain the given element."""
        containing_cuts = []
        
        # Check each cut to see if it contains the element
        for cut in self.egi.Cut:
            if self._element_in_cut(element_id, cut.id):
                containing_cuts.append(cut.id)
        
        # Sort by nesting level (innermost first)
        containing_cuts.sort(key=lambda cut_id: self._get_cut_nesting_level(cut_id), reverse=True)
        
        return containing_cuts
    
    def _element_in_cut(self, element_id: ElementID, cut_id: ElementID) -> bool:
        """Check if an element is contained within a cut."""
        # This is a simplified implementation
        # In a full implementation, this would use the area mapping
        # For now, we'll use a heuristic based on the area mapping if available
        
        if hasattr(self.egi, 'area') and cut_id in self.egi.area:
            return element_id in self.egi.area[cut_id]
        
        # Fallback: assume no containment for now
        return False
    
    def _get_cut_nesting_level(self, cut_id: ElementID) -> int:
        """Get the nesting level of a cut."""
        # Count how many cuts contain this cut
        level = 0
        for other_cut in self.egi.Cut:
            if other_cut.id != cut_id and self._element_in_cut(cut_id, other_cut.id):
                level += 1
        return level
    
    def is_positive_context(self, element_id: ElementID) -> bool:
        """Check if element is in positive context."""
        return self.get_context(element_id).context_polarity == "positive"
    
    def is_negative_context(self, element_id: ElementID) -> bool:
        """Check if element is in negative context."""
        return self.get_context(element_id).context_polarity == "negative"


class TransformationValidator:
    """Validates transformation operations against EG rules."""
    
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        self.context_analyzer = ContextAnalyzer(egi)
    
    def validate_erasure(self, element_id: ElementID) -> TransformationResult:
        """Validate erasure operation (remove from positive context)."""
        context = self.context_analyzer.get_context(element_id)
        
        if context.context_polarity != "positive":
            return TransformationResult(
                success=False,
                error_message=f"Erasure rule violation: Element {element_id} is not in positive context"
            )
        
        # Check if element exists
        if not self._element_exists(element_id):
            return TransformationResult(
                success=False,
                error_message=f"Element {element_id} does not exist"
            )
        
        return TransformationResult(success=True, applied_rule=TransformationRule.ERASURE)
    
    def validate_insertion(self, element_type: str, target_context: ElementID) -> TransformationResult:
        """Validate insertion operation (add to negative context)."""
        if target_context:
            context = self.context_analyzer.get_context(target_context)
            if context.context_polarity != "negative":
                return TransformationResult(
                    success=False,
                    error_message=f"Insertion rule violation: Target context is not negative"
                )
        
        return TransformationResult(success=True, applied_rule=TransformationRule.INSERTION)
    
    def validate_iteration(self, element_id: ElementID, target_context: ElementID) -> TransformationResult:
        """Validate iteration operation (copy across cut boundary)."""
        source_context = self.context_analyzer.get_context(element_id)
        target_context_info = self.context_analyzer.get_context(target_context)
        
        # Check if contexts are adjacent (differ by one nesting level)
        level_diff = abs(source_context.nesting_level - target_context_info.nesting_level)
        if level_diff != 1:
            return TransformationResult(
                success=False,
                error_message="Iteration rule violation: Contexts must be adjacent"
            )
        
        return TransformationResult(success=True, applied_rule=TransformationRule.ITERATION)
    
    def validate_deiteration(self, element_id: ElementID) -> TransformationResult:
        """Validate deiteration operation (remove duplicate)."""
        # Check if element has duplicates in the same context
        context = self.context_analyzer.get_context(element_id)
        
        # This would need more sophisticated duplicate detection
        # For now, assume it's valid
        return TransformationResult(success=True, applied_rule=TransformationRule.DEITERATION)
    
    def validate_double_cut_addition(self, target_area: ElementID) -> TransformationResult:
        """Validate double cut addition (logically neutral)."""
        # Double cut addition is always valid as it preserves meaning
        return TransformationResult(success=True, applied_rule=TransformationRule.DOUBLE_CUT_ADDITION)
    
    def validate_double_cut_removal(self, outer_cut_id: ElementID, inner_cut_id: ElementID) -> TransformationResult:
        """Validate double cut removal."""
        # Check if cuts are actually nested
        outer_context = self.context_analyzer.get_context(outer_cut_id)
        inner_context = self.context_analyzer.get_context(inner_cut_id)
        
        if inner_context.nesting_level != outer_context.nesting_level + 1:
            return TransformationResult(
                success=False,
                error_message="Double cut removal violation: Cuts are not properly nested"
            )
        
        return TransformationResult(success=True, applied_rule=TransformationRule.DOUBLE_CUT_REMOVAL)
    
    def _element_exists(self, element_id: ElementID) -> bool:
        """Check if element exists in the EGI."""
        # Check vertices
        for vertex in self.egi.V:
            if vertex.id == element_id:
                return True
        
        # Check edges
        for edge in self.egi.E:
            if edge.id == element_id:
                return True
        
        # Check cuts
        for cut in self.egi.Cut:
            if cut.id == element_id:
                return True
        
        return False


class EGTransformationEngine:
    """Main transformation engine for Existential Graphs."""
    
    def __init__(self):
        self.transformation_history: List[Tuple[TransformationRule, RelationalGraphWithCuts]] = []
        self.max_history_size: int = 100
    
    def apply_transformation(self, egi: RelationalGraphWithCuts, rule: TransformationRule,
                           **kwargs) -> TransformationResult:
        """Apply a transformation rule to an EGI."""
        validator = TransformationValidator(egi)
        
        # Validate the transformation
        if rule == TransformationRule.ERASURE:
            element_id = kwargs.get('element_id')
            if not element_id:
                return TransformationResult(success=False, error_message="Missing element_id for erasure")
            
            validation = validator.validate_erasure(element_id)
            if not validation.success:
                return validation
            
            return self._apply_erasure(egi, element_id)
        
        elif rule == TransformationRule.INSERTION:
            element_type = kwargs.get('element_type')
            target_context = kwargs.get('target_context')
            
            validation = validator.validate_insertion(element_type, target_context)
            if not validation.success:
                return validation
            
            return self._apply_insertion(egi, element_type, target_context, **kwargs)
        
        elif rule == TransformationRule.ITERATION:
            element_id = kwargs.get('element_id')
            target_context = kwargs.get('target_context')
            
            validation = validator.validate_iteration(element_id, target_context)
            if not validation.success:
                return validation
            
            return self._apply_iteration(egi, element_id, target_context)
        
        elif rule == TransformationRule.DEITERATION:
            element_id = kwargs.get('element_id')
            
            validation = validator.validate_deiteration(element_id)
            if not validation.success:
                return validation
            
            return self._apply_deiteration(egi, element_id)
        
        elif rule == TransformationRule.DOUBLE_CUT_ADDITION:
            target_area = kwargs.get('target_area')
            
            validation = validator.validate_double_cut_addition(target_area)
            if not validation.success:
                return validation
            
            return self._apply_double_cut_addition(egi, target_area)
        
        elif rule == TransformationRule.DOUBLE_CUT_REMOVAL:
            outer_cut_id = kwargs.get('outer_cut_id')
            inner_cut_id = kwargs.get('inner_cut_id')
            
            validation = validator.validate_double_cut_removal(outer_cut_id, inner_cut_id)
            if not validation.success:
                return validation
            
            return self._apply_double_cut_removal(egi, outer_cut_id, inner_cut_id)
        
        else:
            return TransformationResult(
                success=False,
                error_message=f"Unknown transformation rule: {rule}"
            )
    
    def _apply_erasure(self, egi: RelationalGraphWithCuts, element_id: ElementID) -> TransformationResult:
        """Apply erasure transformation."""
        new_egi = deepcopy(egi)
        
        # Remove element from all collections
        new_egi.V = [v for v in new_egi.V if v.id != element_id]
        new_egi.E = [e for e in new_egi.E if e.id != element_id]
        new_egi.Cut = [c for c in new_egi.Cut if c.id != element_id]
        
        # Update mappings
        if element_id in new_egi.nu:
            del new_egi.nu[element_id]
        if element_id in new_egi.rel:
            del new_egi.rel[element_id]
        
        # Remove from area mappings
        if hasattr(new_egi, 'area'):
            for cut_id in list(new_egi.area.keys()):
                if element_id in new_egi.area[cut_id]:
                    new_area = [e for e in new_egi.area[cut_id] if e != element_id]
                    new_egi.area[cut_id] = new_area
        
        self._add_to_history(TransformationRule.ERASURE, egi)
        
        return TransformationResult(
            success=True,
            new_egi=new_egi,
            applied_rule=TransformationRule.ERASURE
        )
    
    def _apply_insertion(self, egi: RelationalGraphWithCuts, element_type: str,
                        target_context: ElementID, **kwargs) -> TransformationResult:
        """Apply insertion transformation."""
        new_egi = deepcopy(egi)
        
        # Generate new element ID
        new_id = self._generate_element_id(new_egi, element_type)
        
        if element_type == "vertex":
            new_vertex = Vertex(id=new_id)
            new_egi.V.append(new_vertex)
        
        elif element_type == "predicate":
            predicate_name = kwargs.get('predicate_name', 'P')
            vertex_ids = kwargs.get('vertex_ids', [])
            
            new_edge = Edge(id=new_id)
            new_egi.E.append(new_edge)
            
            # Update mappings
            new_egi.rel[new_id] = predicate_name
            if vertex_ids:
                new_egi.nu[new_id] = vertex_ids
        
        elif element_type == "cut":
            new_cut = Cut(id=new_id)
            new_egi.Cut.append(new_cut)
        
        self._add_to_history(TransformationRule.INSERTION, egi)
        
        return TransformationResult(
            success=True,
            new_egi=new_egi,
            applied_rule=TransformationRule.INSERTION
        )
    
    def _apply_iteration(self, egi: RelationalGraphWithCuts, element_id: ElementID,
                        target_context: ElementID) -> TransformationResult:
        """Apply iteration transformation."""
        new_egi = deepcopy(egi)
        
        # Find the element to iterate
        element_to_copy = None
        element_type = None
        
        for vertex in egi.V:
            if vertex.id == element_id:
                element_to_copy = vertex
                element_type = "vertex"
                break
        
        if not element_to_copy:
            for edge in egi.E:
                if edge.id == element_id:
                    element_to_copy = edge
                    element_type = "edge"
                    break
        
        if not element_to_copy:
            return TransformationResult(
                success=False,
                error_message=f"Element {element_id} not found for iteration"
            )
        
        # Create copy with new ID
        new_id = self._generate_element_id(new_egi, element_type)
        
        if element_type == "vertex":
            new_vertex = Vertex(id=new_id)
            new_egi.V.append(new_vertex)
        
        elif element_type == "edge":
            new_edge = Edge(id=new_id)
            new_egi.E.append(new_edge)
            
            # Copy mappings
            if element_id in egi.rel:
                new_egi.rel[new_id] = egi.rel[element_id]
            if element_id in egi.nu:
                new_egi.nu[new_id] = egi.nu[element_id]
        
        self._add_to_history(TransformationRule.ITERATION, egi)
        
        return TransformationResult(
            success=True,
            new_egi=new_egi,
            applied_rule=TransformationRule.ITERATION
        )
    
    def _apply_deiteration(self, egi: RelationalGraphWithCuts, element_id: ElementID) -> TransformationResult:
        """Apply deiteration transformation."""
        # For now, deiteration is implemented as erasure
        # A full implementation would identify and remove true duplicates
        return self._apply_erasure(egi, element_id)
    
    def _apply_double_cut_addition(self, egi: RelationalGraphWithCuts, target_area: ElementID) -> TransformationResult:
        """Apply double cut addition transformation."""
        new_egi = deepcopy(egi)
        
        # Create outer cut
        outer_id = self._generate_element_id(new_egi, "cut")
        outer_cut = Cut(id=outer_id)
        new_egi.Cut.append(outer_cut)
        
        # Create inner cut
        inner_id = self._generate_element_id(new_egi, "cut")
        inner_cut = Cut(id=inner_id)
        new_egi.Cut.append(inner_cut)
        
        self._add_to_history(TransformationRule.DOUBLE_CUT_ADDITION, egi)
        
        return TransformationResult(
            success=True,
            new_egi=new_egi,
            applied_rule=TransformationRule.DOUBLE_CUT_ADDITION
        )
    
    def _apply_double_cut_removal(self, egi: RelationalGraphWithCuts,
                                 outer_cut_id: ElementID, inner_cut_id: ElementID) -> TransformationResult:
        """Apply double cut removal transformation."""
        new_egi = deepcopy(egi)
        
        # Remove both cuts
        new_egi.Cut = [c for c in new_egi.Cut if c.id not in [outer_cut_id, inner_cut_id]]
        
        # Update area mappings if they exist
        if hasattr(new_egi, 'area'):
            if outer_cut_id in new_egi.area:
                del new_egi.area[outer_cut_id]
            if inner_cut_id in new_egi.area:
                del new_egi.area[inner_cut_id]
        
        self._add_to_history(TransformationRule.DOUBLE_CUT_REMOVAL, egi)
        
        return TransformationResult(
            success=True,
            new_egi=new_egi,
            applied_rule=TransformationRule.DOUBLE_CUT_REMOVAL
        )
    
    def _generate_element_id(self, egi: RelationalGraphWithCuts, element_type: str) -> ElementID:
        """Generate a unique element ID."""
        existing_ids = set()
        
        # Collect all existing IDs
        for vertex in egi.V:
            existing_ids.add(vertex.id)
        for edge in egi.E:
            existing_ids.add(edge.id)
        for cut in egi.Cut:
            existing_ids.add(cut.id)
        
        # Generate unique ID
        counter = 1
        while True:
            new_id = f"{element_type}_{counter}"
            if new_id not in existing_ids:
                return new_id
            counter += 1
    
    def _add_to_history(self, rule: TransformationRule, egi: RelationalGraphWithCuts):
        """Add transformation to history."""
        self.transformation_history.append((rule, deepcopy(egi)))
        
        # Limit history size
        if len(self.transformation_history) > self.max_history_size:
            self.transformation_history.pop(0)
    
    def get_transformation_history(self) -> List[Tuple[TransformationRule, RelationalGraphWithCuts]]:
        """Get transformation history."""
        return self.transformation_history.copy()
    
    def undo_last_transformation(self) -> Optional[RelationalGraphWithCuts]:
        """Undo the last transformation."""
        if self.transformation_history:
            _, previous_egi = self.transformation_history.pop()
            return previous_egi
        return None


if __name__ == "__main__":
    print("=== EG Transformation Engine ===")
    print("Formal transformation rules with validation")
    
    # Test the transformation engine
    engine = EGTransformationEngine()
    print(f"Transformation engine initialized")
    print(f"Available rules: {[rule.value for rule in TransformationRule]}")
