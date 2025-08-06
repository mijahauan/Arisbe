#!/usr/bin/env python3
"""
Mode-aware selection system for Existential Graphs GUI.
Implements different selection behaviors for Warmup vs Practice modes.
"""

from dataclasses import dataclass
from typing import Set, Optional, List, Dict, Any
from enum import Enum
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from egi_core_dau import RelationalGraphWithCuts, ElementID


class Mode(Enum):
    """GUI interaction modes."""
    WARMUP = "warmup"    # EGI construction/composition
    PRACTICE = "practice"  # EGI transformation/preservation


class SelectionType(Enum):
    """Types of selections."""
    SINGLE_ELEMENT = "single_element"
    MULTI_ELEMENT = "multi_element"
    SUBGRAPH = "subgraph"
    EMPTY_AREA = "empty_area"


class ActionType(Enum):
    """Available actions on selections."""
    # Compositional actions (Warmup mode)
    ADD_VERTEX = "add_vertex"
    ADD_PREDICATE = "add_predicate"
    ADD_CUT = "add_cut"
    DELETE_ELEMENT = "delete_element"
    CONNECT_ELEMENTS = "connect_elements"
    DISCONNECT_ELEMENTS = "disconnect_elements"
    MOVE_ELEMENT = "move_element"
    EDIT_PROPERTIES = "edit_properties"
    
    # Transformation actions (Practice mode)
    APPLY_ERASURE = "apply_erasure"
    APPLY_INSERTION = "apply_insertion"
    APPLY_ITERATION = "apply_iteration"
    APPLY_DE_ITERATION = "apply_de_iteration"
    APPLY_DOUBLE_CUT_ADDITION = "apply_double_cut_addition"
    APPLY_DOUBLE_CUT_REMOVAL = "apply_double_cut_removal"
    APPLY_ISOLATED_VERTEX_ADDITION = "apply_isolated_vertex_addition"
    APPLY_ISOLATED_VERTEX_REMOVAL = "apply_isolated_vertex_removal"
    
    # Layout-only actions (both modes)
    LAYOUT_MOVE = "layout_move"
    LAYOUT_RESIZE = "layout_resize"


@dataclass
class ValidationResult:
    """Result of selection/action validation."""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class SelectionState:
    """Current selection state."""
    selected_elements: Set[ElementID]
    selected_context: Optional[ElementID]  # For area selections
    selection_type: SelectionType
    hover_element: Optional[ElementID] = None
    
    def clear(self):
        """Clear all selections."""
        self.selected_elements.clear()
        self.selected_context = None
        self.selection_type = SelectionType.SINGLE_ELEMENT
        self.hover_element = None
    
    def is_empty(self) -> bool:
        """Check if selection is empty."""
        return len(self.selected_elements) == 0 and self.selected_context is None


class SelectionValidator:
    """Base class for selection validation."""
    
    def __init__(self, graph: RelationalGraphWithCuts):
        self.graph = graph
    
    def validate_selection(self, selection: SelectionState) -> ValidationResult:
        """Validate current selection state."""
        raise NotImplementedError
    
    def validate_action(self, action: ActionType, selection: SelectionState) -> ValidationResult:
        """Validate action on current selection."""
        raise NotImplementedError
    
    def get_available_actions(self, selection: SelectionState) -> Set[ActionType]:
        """Get available actions for current selection."""
        raise NotImplementedError


class WarmupSelectionValidator(SelectionValidator):
    """Selection validator for Warmup mode (EGI construction)."""
    
    def validate_selection(self, selection: SelectionState) -> ValidationResult:
        """Validate selection - only syntactic constraints in Warmup mode."""
        # In Warmup mode, most selections are valid as we're building the EGI
        if selection.is_empty():
            return ValidationResult(True)
        
        # Check that selected elements exist in the graph
        for element_id in selection.selected_elements:
            if not self._element_exists(element_id):
                return ValidationResult(False, f"Element {element_id} not found in graph")
        
        return ValidationResult(True)
    
    def validate_action(self, action: ActionType, selection: SelectionState) -> ValidationResult:
        """Validate action - compositional freedom in Warmup mode."""
        if action in [ActionType.ADD_VERTEX, ActionType.ADD_PREDICATE, ActionType.ADD_CUT]:
            # Can add elements anywhere syntactically valid
            return ValidationResult(True)
        
        if action == ActionType.DELETE_ELEMENT:
            # Can delete any element (with cascade validation)
            if selection.is_empty():
                return ValidationResult(False, "No elements selected for deletion")
            return ValidationResult(True)
        
        if action in [ActionType.CONNECT_ELEMENTS, ActionType.DISCONNECT_ELEMENTS]:
            # Can modify connections freely
            if len(selection.selected_elements) < 2:
                return ValidationResult(False, "Need at least 2 elements for connection operations")
            return ValidationResult(True)
        
        if action in [ActionType.MOVE_ELEMENT, ActionType.LAYOUT_MOVE]:
            # Can move elements within syntactic constraints
            if selection.is_empty():
                return ValidationResult(False, "No elements selected for moving")
            return ValidationResult(True)
        
        return ValidationResult(True)  # Default to permissive in Warmup mode
    
    def get_available_actions(self, selection: SelectionState) -> Set[ActionType]:
        """Get available actions - broad set for compositional work."""
        if selection.is_empty():
            return {ActionType.ADD_VERTEX, ActionType.ADD_PREDICATE, ActionType.ADD_CUT}
        
        actions = {ActionType.DELETE_ELEMENT, ActionType.MOVE_ELEMENT, ActionType.EDIT_PROPERTIES}
        
        if len(selection.selected_elements) >= 2:
            actions.update({ActionType.CONNECT_ELEMENTS, ActionType.DISCONNECT_ELEMENTS})
        
        return actions
    
    def _element_exists(self, element_id: ElementID) -> bool:
        """Check if element exists in graph."""
        return (element_id in {v.id for v in self.graph.V} or
                element_id in {e.id for e in self.graph.E} or
                element_id in {c.id for c in self.graph.Cut} or
                element_id == self.graph.sheet)


class PracticeSelectionValidator(SelectionValidator):
    """Selection validator for Practice mode (EGI preservation)."""
    
    def validate_selection(self, selection: SelectionState) -> ValidationResult:
        """Validate selection - full rule constraints in Practice mode."""
        if selection.is_empty():
            return ValidationResult(True)
        
        # Check element existence
        for element_id in selection.selected_elements:
            if not self._element_exists(element_id):
                return ValidationResult(False, f"Element {element_id} not found in graph")
        
        # Check logical completeness for subgraph selections
        if selection.selection_type == SelectionType.SUBGRAPH:
            completeness_result = self._check_logical_completeness(selection.selected_elements)
            if not completeness_result.is_valid:
                return completeness_result
        
        return ValidationResult(True)
    
    def validate_action(self, action: ActionType, selection: SelectionState) -> ValidationResult:
        """Validate action - transformation rule constraints in Practice mode."""
        if action == ActionType.APPLY_ERASURE:
            return self._validate_erasure(selection)
        
        if action == ActionType.APPLY_INSERTION:
            return self._validate_insertion(selection)
        
        if action == ActionType.APPLY_ITERATION:
            return self._validate_iteration(selection)
        
        if action in [ActionType.APPLY_DOUBLE_CUT_ADDITION, ActionType.APPLY_DOUBLE_CUT_REMOVAL]:
            return self._validate_double_cut_operation(selection)
        
        if action in [ActionType.LAYOUT_MOVE, ActionType.LAYOUT_RESIZE]:
            # Layout-only operations are generally allowed
            return ValidationResult(True)
        
        return ValidationResult(False, f"Action {action} not available in Practice mode")
    
    def get_available_actions(self, selection: SelectionState) -> Set[ActionType]:
        """Get available actions - transformation rules only."""
        if selection.is_empty():
            return {ActionType.APPLY_INSERTION, ActionType.APPLY_ISOLATED_VERTEX_ADDITION}
        
        actions = set()
        
        # Check context polarity for each selected element
        for element_id in selection.selected_elements:
            context = self.graph.get_context(element_id)
            if self.graph.is_positive_context(context):
                actions.add(ActionType.APPLY_ERASURE)
            if self.graph.is_negative_context(context):
                actions.add(ActionType.APPLY_INSERTION)
        
        # Always available for valid selections
        actions.update({
            ActionType.APPLY_ITERATION,
            ActionType.LAYOUT_MOVE,
            ActionType.LAYOUT_RESIZE
        })
        
        return actions
    
    def _validate_erasure(self, selection: SelectionState) -> ValidationResult:
        """Validate erasure operation."""
        if selection.is_empty():
            return ValidationResult(False, "No elements selected for erasure")
        
        for element_id in selection.selected_elements:
            context = self.graph.get_context(element_id)
            if not self.graph.is_positive_context(context):
                return ValidationResult(False, f"Cannot erase from negative context {context}")
        
        return ValidationResult(True)
    
    def _validate_insertion(self, selection: SelectionState) -> ValidationResult:
        """Validate insertion operation."""
        if selection.selected_context is None:
            return ValidationResult(False, "No context selected for insertion")
        
        if not self.graph.is_negative_context(selection.selected_context):
            return ValidationResult(False, f"Cannot insert into positive context {selection.selected_context}")
        
        return ValidationResult(True)
    
    def _validate_iteration(self, selection: SelectionState) -> ValidationResult:
        """Validate iteration operation."""
        if selection.is_empty():
            return ValidationResult(False, "No elements selected for iteration")
        
        # Additional iteration constraints would be checked here
        # (target context dominance, etc.)
        return ValidationResult(True)
    
    def _validate_double_cut_operation(self, selection: SelectionState) -> ValidationResult:
        """Validate double cut operations."""
        if selection.is_empty():
            return ValidationResult(False, "No elements selected for double cut operation")
        
        # Check that elements are in same context for enclosure
        contexts = {self.graph.get_context(elem_id) for elem_id in selection.selected_elements}
        if len(contexts) > 1:
            return ValidationResult(False, "Elements must be in same context for double cut operations")
        
        return ValidationResult(True)
    
    def _check_logical_completeness(self, selected_elements: Set[ElementID]) -> ValidationResult:
        """Check if selection forms a logically complete subgraph."""
        # For now, assume selections are complete
        # Full implementation would check vertex-edge connectivity
        return ValidationResult(True)
    
    def _element_exists(self, element_id: ElementID) -> bool:
        """Check if element exists in graph."""
        return (element_id in {v.id for v in self.graph.V} or
                element_id in {e.id for e in self.graph.E} or
                element_id in {c.id for c in self.graph.Cut} or
                element_id == self.graph.sheet)


class ModeAwareSelectionSystem:
    """Main selection system that adapts behavior based on mode."""
    
    def __init__(self, initial_mode: Mode = Mode.WARMUP):
        self.mode = initial_mode
        self.selection_state = SelectionState(
            selected_elements=set(),
            selected_context=None,
            selection_type=SelectionType.SINGLE_ELEMENT
        )
        self.validator: Optional[SelectionValidator] = None
        self.graph: Optional[RelationalGraphWithCuts] = None
    
    def set_graph(self, graph: RelationalGraphWithCuts):
        """Set the current graph and update validator."""
        self.graph = graph
        self._update_validator()
    
    def switch_mode(self, new_mode: Mode):
        """Switch between Warmup and Practice modes."""
        if new_mode != self.mode:
            self.mode = new_mode
            self.selection_state.clear()  # Clear selections on mode switch
            self._update_validator()
    
    def select_element(self, element_id: ElementID, multi_select: bool = False) -> ValidationResult:
        """Select an element."""
        if not multi_select:
            self.selection_state.selected_elements.clear()
            self.selection_state.selected_context = None
        
        if element_id in self.selection_state.selected_elements:
            self.selection_state.selected_elements.remove(element_id)
        else:
            self.selection_state.selected_elements.add(element_id)
        
        # Update selection type
        if len(self.selection_state.selected_elements) == 0:
            self.selection_state.selection_type = SelectionType.SINGLE_ELEMENT
        elif len(self.selection_state.selected_elements) == 1:
            self.selection_state.selection_type = SelectionType.SINGLE_ELEMENT
        else:
            self.selection_state.selection_type = SelectionType.MULTI_ELEMENT
        
        return self._validate_current_selection()
    
    def select_area(self, context_id: ElementID) -> ValidationResult:
        """Select an empty area/context."""
        self.selection_state.clear()
        self.selection_state.selected_context = context_id
        self.selection_state.selection_type = SelectionType.EMPTY_AREA
        
        return self._validate_current_selection()
    
    def clear_selection(self):
        """Clear all selections."""
        self.selection_state.clear()
    
    def get_available_actions(self) -> Set[ActionType]:
        """Get available actions for current selection."""
        if self.validator is None:
            return set()
        return self.validator.get_available_actions(self.selection_state)
    
    def validate_action(self, action: ActionType) -> ValidationResult:
        """Validate an action on current selection."""
        if self.validator is None:
            return ValidationResult(False, "No validator available")
        return self.validator.validate_action(action, self.selection_state)
    
    def _update_validator(self):
        """Update validator based on current mode and graph."""
        if self.graph is None:
            self.validator = None
            return
        
        if self.mode == Mode.WARMUP:
            self.validator = WarmupSelectionValidator(self.graph)
        else:
            self.validator = PracticeSelectionValidator(self.graph)
    
    def _validate_current_selection(self) -> ValidationResult:
        """Validate current selection state."""
        if self.validator is None:
            return ValidationResult(False, "No validator available")
        return self.validator.validate_selection(self.selection_state)


if __name__ == "__main__":
    # Test the mode-aware selection system
    print("=== Testing Mode-Aware Selection System ===")
    
    from egi_core_dau import create_empty_graph, create_vertex, create_edge, create_cut
    
    # Create test graph
    graph = create_empty_graph()
    vertex = create_vertex()  # Generic vertex with no label
    graph = graph.with_vertex(vertex)
    
    # Test Warmup mode
    selection_system = ModeAwareSelectionSystem(Mode.WARMUP)
    selection_system.set_graph(graph)
    
    print(f"Mode: {selection_system.mode}")
    print(f"Available actions (empty selection): {selection_system.get_available_actions()}")
    
    # Select vertex
    result = selection_system.select_element(vertex.id)
    print(f"Selection result: {result}")
    print(f"Available actions (vertex selected): {selection_system.get_available_actions()}")
    
    # Switch to Practice mode
    selection_system.switch_mode(Mode.PRACTICE)
    print(f"\\nSwitched to mode: {selection_system.mode}")
    print(f"Available actions (empty after switch): {selection_system.get_available_actions()}")
    
    print("\\n=== Mode-Aware Selection System Test Complete ===")
