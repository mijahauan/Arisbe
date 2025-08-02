"""
Robust Selection System for Existential Graphs
Provides standardized subgraph selection capabilities across all EG operations.
"""

from typing import Set, List, Dict, Optional, Tuple, Callable, Any
from dataclasses import dataclass
from enum import Enum
import uuid

# Handle imports for both module and script execution
try:
    from .egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
except ImportError:
    try:
        from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
    except ImportError:
        # Fallback for testing - create minimal types
        RelationalGraphWithCuts = object
        ElementID = str
        Vertex = object
        Edge = object
        Cut = object


class SelectionMode(Enum):
    """Different modes of selection behavior"""
    SINGLE = "single"           # Single element selection
    MULTI = "multi"             # Multi-element selection
    LOGICAL_COMPLETE = "logical_complete"  # Auto-complete logical subgraphs
    SPATIAL = "spatial"         # Spatial boundary selection
    CONNECTED = "connected"     # Connected component selection


class SelectionContext(Enum):
    """Context in which selection is being used"""
    EDITING = "editing"         # Visual editing/rearrangement
    COMPOSITION = "composition" # Graph composition (pre-validation)
    TRANSFORMATION = "transformation"  # Formal EG transformations
    ENCLOSING = "enclosing"     # Creating enclosing cuts
    DELETION = "deletion"       # Deleting elements
    MOVEMENT = "movement"       # Moving elements between areas


@dataclass
class SelectionState:
    """Current state of the selection system"""
    selected_elements: Set[ElementID]
    mode: SelectionMode
    context: SelectionContext
    is_valid_subgraph: bool
    suggestions: List[ElementID]
    completion_suggestions: List[ElementID]


@dataclass
class LogicalSuggestion:
    """A suggestion for logical completeness"""
    element_id: ElementID
    reason: str
    priority: int  # 1=high, 2=medium, 3=low


class SelectionManager:
    """
    Core selection system for Existential Graphs.
    Provides robust, reusable selection capabilities across all EG operations.
    """
    
    def __init__(self, graph: RelationalGraphWithCuts):
        self.graph = graph
        self.state = SelectionState(
            selected_elements=set(),
            mode=SelectionMode.SINGLE,
            context=SelectionContext.EDITING,
            is_valid_subgraph=False,
            suggestions=[],
            completion_suggestions=[]
        )
        
        # Event callbacks
        self.on_selection_changed: Optional[Callable[[SelectionState], None]] = None
        self.on_suggestion_generated: Optional[Callable[[List[LogicalSuggestion]], None]] = None
        
    def set_context(self, context: SelectionContext, mode: SelectionMode = None):
        """Set the selection context and optionally mode"""
        self.state.context = context
        if mode:
            self.state.mode = mode
        self._update_suggestions()
        self._notify_selection_changed()
    
    def select_element(self, element_id: ElementID) -> bool:
        """Select an element. Returns True if selection changed."""
        if self.state.mode == SelectionMode.SINGLE:
            if element_id in self.state.selected_elements:
                return False  # Already selected
            self.state.selected_elements = {element_id}
        else:
            # Multi-select modes
            if element_id in self.state.selected_elements:
                self.state.selected_elements.remove(element_id)
            else:
                self.state.selected_elements.add(element_id)
        
        self._update_validation()
        self._update_suggestions()
        self._notify_selection_changed()
        return True
    
    def deselect_element(self, element_id: ElementID) -> bool:
        """Deselect an element. Returns True if selection changed."""
        if element_id in self.state.selected_elements:
            self.state.selected_elements.remove(element_id)
            self._update_validation()
            self._update_suggestions()
            self._notify_selection_changed()
            return True
        return False
    
    def clear_selection(self):
        """Clear all selected elements"""
        if self.state.selected_elements:
            self.state.selected_elements.clear()
            self._update_validation()
            self._update_suggestions()
            self._notify_selection_changed()
    
    def select_spatial_area(self, center: Tuple[float, float], radius: float, 
                           visual_elements: Dict[ElementID, Any]) -> List[ElementID]:
        """Select elements within a spatial area"""
        cx, cy = center
        newly_selected = []
        
        for element_id, visual_element in visual_elements.items():
            # Check if element is within radius (implementation depends on visual element type)
            if hasattr(visual_element, 'position'):
                ex, ey = visual_element.position
                distance = ((ex - cx) ** 2 + (ey - cy) ** 2) ** 0.5
                if distance <= radius:
                    if self.select_element(element_id):
                        newly_selected.append(element_id)
        
        return newly_selected
    
    def auto_complete_logical_subgraph(self) -> List[ElementID]:
        """Automatically complete the selection to form a proper logical subgraph"""
        added_elements = []
        
        # Keep adding suggested elements until no more suggestions
        while True:
            suggestions = self._generate_completion_suggestions()
            if not suggestions:
                break
            
            # Add highest priority suggestions
            high_priority = [s for s in suggestions if s.priority == 1]
            if not high_priority:
                break
            
            for suggestion in high_priority:
                if self.select_element(suggestion.element_id):
                    added_elements.append(suggestion.element_id)
        
        return added_elements
    
    def get_selected_subgraph_info(self) -> Dict[str, Any]:
        """Get detailed information about the selected subgraph"""
        vertices = [eid for eid in self.state.selected_elements if eid in self.graph.V]
        edges = [eid for eid in self.state.selected_elements if eid in self.graph.E]
        cuts = [eid for eid in self.state.selected_elements if eid in self.graph.Cut]
        
        return {
            'vertices': vertices,
            'edges': edges,
            'cuts': cuts,
            'total_count': len(self.state.selected_elements),
            'is_valid_subgraph': self.state.is_valid_subgraph,
            'missing_for_completion': self.state.completion_suggestions,
            'context': self.state.context.value,
            'mode': self.state.mode.value
        }
    
    def validate_subgraph_completeness(self) -> Tuple[bool, List[str]]:
        """Validate if selected elements form a complete logical subgraph"""
        issues = []
        
        # Check for orphaned edges (edges without all their vertices selected)
        for edge_id in [eid for eid in self.state.selected_elements if eid in self.graph.E]:
            edge = self.graph.E[edge_id]
            for vertex_id in edge.endpoints:
                if vertex_id not in self.state.selected_elements:
                    issues.append(f"Edge {edge_id} requires vertex {vertex_id}")
        
        # Check for orphaned vertices in certain contexts
        if self.state.context in [SelectionContext.TRANSFORMATION, SelectionContext.ENCLOSING]:
            for vertex_id in [eid for eid in self.state.selected_elements if eid in self.graph.V]:
                # Find edges connected to this vertex
                connected_edges = [eid for eid, edge in self.graph.E.items() 
                                 if vertex_id in edge.endpoints]
                # If vertex has connected edges, they should be selected too
                for edge_id in connected_edges:
                    if edge_id not in self.state.selected_elements:
                        issues.append(f"Vertex {vertex_id} is connected to unselected edge {edge_id}")
        
        # Check for cut containment consistency
        for cut_id in [eid for eid in self.state.selected_elements if eid in self.graph.Cut]:
            if cut_id in self.graph.area:
                contained_elements = self.graph.area[cut_id]
                for element_id in contained_elements:
                    if element_id not in self.state.selected_elements:
                        issues.append(f"Cut {cut_id} contains unselected element {element_id}")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def _update_validation(self):
        """Update the validation state of the current selection"""
        is_valid, _ = self.validate_subgraph_completeness()
        self.state.is_valid_subgraph = is_valid
    
    def _update_suggestions(self):
        """Update suggestions based on current selection and context"""
        self.state.suggestions = []
        self.state.completion_suggestions = []
        
        if not self.state.selected_elements:
            return
        
        # Generate logical completion suggestions
        completion_suggestions = self._generate_completion_suggestions()
        self.state.completion_suggestions = [s.element_id for s in completion_suggestions]
        
        # Generate context-specific suggestions
        if self.state.context == SelectionContext.EDITING:
            self.state.suggestions = self._generate_editing_suggestions()
        elif self.state.context == SelectionContext.TRANSFORMATION:
            self.state.suggestions = self._generate_transformation_suggestions()
        
        # Notify about suggestions
        if self.on_suggestion_generated and completion_suggestions:
            self.on_suggestion_generated(completion_suggestions)
    
    def _generate_completion_suggestions(self) -> List[LogicalSuggestion]:
        """Generate suggestions for logical subgraph completion"""
        suggestions = []
        
        # Suggest vertices for selected edges
        for edge_id in [eid for eid in self.state.selected_elements if eid in self.graph.E]:
            edge = self.graph.E[edge_id]
            for vertex_id in edge.endpoints:
                if vertex_id not in self.state.selected_elements:
                    suggestions.append(LogicalSuggestion(
                        element_id=vertex_id,
                        reason=f"Required vertex for selected edge {edge_id}",
                        priority=1
                    ))
        
        # Suggest edges for selected vertices (in certain contexts)
        if self.state.context in [SelectionContext.TRANSFORMATION, SelectionContext.ENCLOSING]:
            for vertex_id in [eid for eid in self.state.selected_elements if eid in self.graph.V]:
                connected_edges = [eid for eid, edge in self.graph.E.items() 
                                 if vertex_id in edge.endpoints]
                for edge_id in connected_edges:
                    if edge_id not in self.state.selected_elements:
                        suggestions.append(LogicalSuggestion(
                            element_id=edge_id,
                            reason=f"Connected edge to selected vertex {vertex_id}",
                            priority=2
                        ))
        
        # Suggest contained elements for selected cuts
        for cut_id in [eid for eid in self.state.selected_elements if eid in self.graph.Cut]:
            if cut_id in self.graph.area:
                contained_elements = self.graph.area[cut_id]
                for element_id in contained_elements:
                    if element_id not in self.state.selected_elements:
                        suggestions.append(LogicalSuggestion(
                            element_id=element_id,
                            reason=f"Contained in selected cut {cut_id}",
                            priority=1
                        ))
        
        return suggestions
    
    def _generate_editing_suggestions(self) -> List[ElementID]:
        """Generate suggestions for editing context"""
        # In editing context, suggest spatially related elements
        return []
    
    def _generate_transformation_suggestions(self) -> List[ElementID]:
        """Generate suggestions for transformation context"""
        # In transformation context, suggest logically related elements
        return []
    
    def _notify_selection_changed(self):
        """Notify listeners that selection has changed"""
        if self.on_selection_changed:
            self.on_selection_changed(self.state)


# Utility functions for integration with existing systems

def integrate_with_diagram_canvas(canvas, selection_manager: SelectionManager):
    """Integrate SelectionManager with DiagramCanvas"""
    # Store reference
    canvas.selection_manager = selection_manager
    
    # Set up callbacks
    def on_selection_changed(state: SelectionState):
        # Update canvas visual feedback
        canvas.selected_elements = state.selected_elements
        canvas.selection_mode = state.mode != SelectionMode.SINGLE
        canvas._render_diagram()
    
    selection_manager.on_selection_changed = on_selection_changed
    
    # Update canvas methods to use SelectionManager
    original_toggle = getattr(canvas, 'toggle_element_selection', None)
    if original_toggle:
        def new_toggle(element_id):
            return selection_manager.select_element(element_id)
        canvas.toggle_element_selection = new_toggle


def create_selection_manager_for_context(graph: RelationalGraphWithCuts, 
                                       context: SelectionContext) -> SelectionManager:
    """Factory function to create SelectionManager for specific contexts"""
    manager = SelectionManager(graph)
    
    # Set appropriate mode based on context
    if context == SelectionContext.TRANSFORMATION:
        manager.set_context(context, SelectionMode.LOGICAL_COMPLETE)
    elif context == SelectionContext.ENCLOSING:
        manager.set_context(context, SelectionMode.MULTI)
    elif context == SelectionContext.EDITING:
        manager.set_context(context, SelectionMode.SINGLE)
    else:
        manager.set_context(context, SelectionMode.MULTI)
    
    return manager
