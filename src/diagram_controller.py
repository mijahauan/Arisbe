"""
Diagram Controller for Existential Graph Visualization
Coordinates the clean Data ↔ Layout ↔ Rendering pipeline.
Handles events, selection integration, and layer coordination.
"""

from typing import Dict, List, Optional, Set, Callable, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid

# Handle imports for both module and script execution
try:
    from .egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
    from .layout_engine import LayoutEngine, LayoutResult, LayoutElement, Coordinate
    from .diagram_renderer import DiagramRenderer, RenderingContext, RenderingMode, VisualTheme
    from .canvas_backend import Canvas, CanvasEvent, EventType
    from .selection_system import SelectionManager, SelectionContext, SelectionMode
except ImportError:
    from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
    from layout_engine import LayoutEngine, LayoutResult, LayoutElement, Coordinate
    from diagram_renderer import DiagramRenderer, RenderingContext, RenderingMode, VisualTheme
    from canvas_backend import Canvas, CanvasEvent, EventType
    from selection_system import SelectionManager, SelectionContext, SelectionMode


class InteractionMode(Enum):
    """Different interaction modes for the diagram"""
    VIEW = "view"                        # Read-only viewing
    SELECT = "select"                    # Selection operations
    EDIT = "edit"                        # Editing operations
    ADD_ELEMENT = "add_element"          # Adding new elements
    TRANSFORM = "transform"              # Applying transformations


@dataclass
class DiagramState:
    """Current state of the diagram system"""
    graph: RelationalGraphWithCuts
    layout_result: Optional[LayoutResult] = None
    interaction_mode: InteractionMode = InteractionMode.VIEW
    
    # Selection state
    selected_elements: Set[ElementID] = None
    highlighted_elements: Set[ElementID] = None
    
    # Interaction state
    drag_start: Optional[Coordinate] = None
    drag_current: Optional[Coordinate] = None
    is_dragging: bool = False
    
    # Pending operations
    pending_element_type: Optional[str] = None
    pending_placement_mode: Optional[str] = None
    
    def __post_init__(self):
        if self.selected_elements is None:
            object.__setattr__(self, 'selected_elements', set())
        if self.highlighted_elements is None:
            object.__setattr__(self, 'highlighted_elements', set())


class DiagramController:
    """
    Main controller coordinating the clean Data ↔ Layout ↔ Rendering pipeline.
    Handles events, selection, and maintains separation of concerns.
    """
    
    def __init__(self, canvas: Canvas, 
                 canvas_width: int = 800, canvas_height: int = 600,
                 theme: VisualTheme = VisualTheme.DAU_STANDARD):
        
        # Core components (clean separation)
        self.canvas = canvas
        self.layout_engine = LayoutEngine(canvas_width, canvas_height)
        self.renderer = DiagramRenderer(canvas, theme)
        
        # State management
        self.state = DiagramState(
            graph=RelationalGraphWithCuts.create_empty_graph()
        )
        
        # Selection system integration
        self.selection_manager: Optional[SelectionManager] = None
        
        # Event callbacks
        self.on_element_selected: Optional[Callable[[ElementID], None]] = None
        self.on_element_added: Optional[Callable[[ElementID], None]] = None
        self.on_graph_changed: Optional[Callable[[RelationalGraphWithCuts], None]] = None
        
        # Setup event handling
        self._setup_event_handlers()
        
        # Performance optimization
        self._layout_cache: Dict[str, LayoutResult] = {}
        self._needs_relayout = True
        self._needs_rerender = True
    
    def set_graph(self, graph: RelationalGraphWithCuts) -> None:
        """
        Set new graph data and trigger clean pipeline: Data → Layout → Rendering
        """
        self.state = DiagramState(graph=graph)
        
        # Update selection manager
        self.selection_manager = SelectionManager(graph)
        self._setup_selection_integration()
        
        # Trigger clean pipeline
        self._needs_relayout = True
        self._needs_rerender = True
        self._update_diagram()
        
        # Notify listeners
        if self.on_graph_changed:
            self.on_graph_changed(graph)
    
    def get_graph(self) -> RelationalGraphWithCuts:
        """Get current graph data"""
        return self.state.graph
    
    def set_interaction_mode(self, mode: InteractionMode) -> None:
        """Change interaction mode"""
        self.state.interaction_mode = mode
        self._needs_rerender = True
        self._update_rendering()
    
    def select_element(self, element_id: ElementID) -> None:
        """Select an element through the clean pipeline"""
        if self.selection_manager:
            changed = self.selection_manager.select_element(element_id)
            if changed:
                self.state.selected_elements = self.selection_manager.state.selected_elements.copy()
                self._needs_rerender = True
                self._update_rendering()
                
                if self.on_element_selected:
                    self.on_element_selected(element_id)
    
    def clear_selection(self) -> None:
        """Clear all selections"""
        if self.selection_manager:
            self.selection_manager.clear_selection()
            self.state.selected_elements.clear()
            self.state.highlighted_elements.clear()
            self._needs_rerender = True
            self._update_rendering()
    
    def add_element(self, element_type: str, position: Coordinate, 
                   placement_mode: str = "nested") -> Optional[ElementID]:
        """
        Add new element through clean pipeline: Data → Layout → Rendering
        """
        try:
            # Create new element based on type
            new_graph = None
            new_element_id = None
            
            if element_type == "vertex":
                from .egi_core_dau import create_vertex
                vertex = create_vertex(label=None, is_generic=True)
                
                # Find containing area at position
                containing_area = self._find_area_at_position(position)
                new_graph = self.state.graph.with_vertex_in_context(vertex, containing_area)
                new_element_id = vertex.id
                
            elif element_type == "cut":
                from .egi_core_dau import create_cut
                cut = create_cut()
                
                # Determine parent area
                parent_area = self._find_area_at_position(position)
                new_graph = self.state.graph.with_cut(cut, parent_area)
                new_element_id = cut.id
                
            elif element_type == "edge":
                # Edge creation requires vertex selection
                if len(self.state.selected_elements) >= 2:
                    from .egi_core_dau import create_edge
                    selected_vertices = list(self.state.selected_elements)[:2]
                    edge = create_edge(relation="connects")
                    
                    new_graph = self.state.graph.with_edge(edge, selected_vertices)
                    new_element_id = edge.id
            
            if new_graph and new_element_id:
                # Update through clean pipeline
                self.set_graph(new_graph)
                
                # Select new element
                self.select_element(new_element_id)
                
                if self.on_element_added:
                    self.on_element_added(new_element_id)
                
                return new_element_id
                
        except Exception as e:
            print(f"Error adding element: {e}")
        
        return None
    
    def delete_selected_elements(self) -> None:
        """Delete selected elements through clean pipeline"""
        if not self.state.selected_elements:
            return
        
        try:
            new_graph = self.state.graph
            
            # Remove elements from graph (order matters)
            for element_id in self.state.selected_elements:
                # Find element type and remove appropriately
                if any(v.id == element_id for v in new_graph.V):
                    new_graph = new_graph.without_vertex(element_id)
                elif any(e.id == element_id for e in new_graph.E):
                    new_graph = new_graph.without_edge(element_id)
                elif any(c.id == element_id for c in new_graph.Cut):
                    new_graph = new_graph.without_cut(element_id)
            
            # Update through clean pipeline
            self.clear_selection()
            self.set_graph(new_graph)
            
        except Exception as e:
            print(f"Error deleting elements: {e}")
    
    def save_diagram(self, filename: str, format: str = "png") -> None:
        """Save current diagram"""
        self.renderer.save_diagram(filename, format)
    
    def refresh_diagram(self) -> None:
        """Force complete refresh of the diagram"""
        self._needs_relayout = True
        self._needs_rerender = True
        self._layout_cache.clear()
        self._update_diagram()
    
    def get_element_at_point(self, point: Coordinate) -> Optional[ElementID]:
        """Find element at point using current layout"""
        if self.state.layout_result:
            return self.state.layout_result.find_element_at_point(point)
        return None
    
    # Private methods for clean pipeline coordination
    
    def _update_diagram(self) -> None:
        """Update diagram through clean Data → Layout → Rendering pipeline"""
        if self._needs_relayout:
            self._update_layout()
        
        if self._needs_rerender:
            self._update_rendering()
    
    def _update_layout(self) -> None:
        """Update layout layer (pure spatial calculations)"""
        if not self._needs_relayout:
            return
        
        # Check cache first
        graph_hash = self._hash_graph(self.state.graph)
        if graph_hash in self._layout_cache:
            self.state.layout_result = self._layout_cache[graph_hash]
        else:
            # Generate new layout
            self.state.layout_result = self.layout_engine.layout_graph(self.state.graph)
            self._layout_cache[graph_hash] = self.state.layout_result
        
        self._needs_relayout = False
        self._needs_rerender = True  # Layout change requires rerender
    
    def _update_rendering(self) -> None:
        """Update rendering layer (pure visual presentation)"""
        if not self._needs_rerender or not self.state.layout_result:
            return
        
        # Create rendering context
        rendering_mode = RenderingMode.NORMAL
        if self.state.interaction_mode == InteractionMode.SELECT:
            rendering_mode = RenderingMode.SELECTION_OVERLAY
        elif self.state.interaction_mode == InteractionMode.EDIT:
            rendering_mode = RenderingMode.EDITING
        
        context = RenderingContext(
            mode=rendering_mode,
            selected_elements=self.state.selected_elements.copy(),
            highlighted_elements=self.state.highlighted_elements.copy()
        )
        
        # Render through pure rendering layer
        self.renderer.render_diagram(self.state.layout_result, self.state.graph, context)
        
        self._needs_rerender = False
    
    def _setup_event_handlers(self) -> None:
        """Setup canvas event handlers"""
        self.canvas.add_event_handler(EventType.MOUSE_CLICK, self._on_mouse_click)
        self.canvas.add_event_handler(EventType.MOUSE_DRAG, self._on_mouse_drag)
        self.canvas.add_event_handler(EventType.MOUSE_RELEASE, self._on_mouse_release)
        self.canvas.add_event_handler(EventType.KEY_PRESS, self._on_key_press)
    
    def _setup_selection_integration(self) -> None:
        """Integrate selection manager with controller"""
        if self.selection_manager:
            self.selection_manager.on_selection_changed = self._on_selection_changed
    
    def _on_mouse_click(self, event: CanvasEvent) -> None:
        """Handle mouse click events"""
        element_id = self.get_element_at_point(event.position)
        
        if self.state.interaction_mode == InteractionMode.SELECT:
            if element_id:
                self.select_element(element_id)
            else:
                # Start drag selection
                self.state.drag_start = event.position
                self.state.is_dragging = True
        
        elif self.state.interaction_mode == InteractionMode.ADD_ELEMENT:
            if self.state.pending_element_type:
                self.add_element(self.state.pending_element_type, event.position)
                self.state.pending_element_type = None
                self.set_interaction_mode(InteractionMode.VIEW)
    
    def _on_mouse_drag(self, event: CanvasEvent) -> None:
        """Handle mouse drag events"""
        if self.state.is_dragging and self.state.drag_start:
            self.state.drag_current = event.position
            
            # Render selection rectangle
            self.renderer.render_selection_rectangle(
                self.state.drag_start, self.state.drag_current
            )
    
    def _on_mouse_release(self, event: CanvasEvent) -> None:
        """Handle mouse release events"""
        if self.state.is_dragging and self.state.drag_start and self.state.drag_current:
            # Complete drag selection
            self._complete_drag_selection(self.state.drag_start, self.state.drag_current)
        
        # Reset drag state
        self.state.drag_start = None
        self.state.drag_current = None
        self.state.is_dragging = False
        
        # Refresh rendering
        self._needs_rerender = True
        self._update_rendering()
    
    def _on_key_press(self, event: CanvasEvent) -> None:
        """Handle key press events"""
        if hasattr(event, 'key'):
            if event.key == 'Delete' or event.key == 'BackSpace':
                self.delete_selected_elements()
            elif event.key == 'Escape':
                self.clear_selection()
                self.set_interaction_mode(InteractionMode.VIEW)
    
    def _on_selection_changed(self, selection_state) -> None:
        """Handle selection manager state changes"""
        self.state.selected_elements = selection_state.selected_elements.copy()
        self._needs_rerender = True
        self._update_rendering()
    
    def _complete_drag_selection(self, start: Coordinate, end: Coordinate) -> None:
        """Complete drag-to-select operation"""
        if not self.state.layout_result:
            return
        
        # Find elements within selection rectangle
        x1, y1 = start
        x2, y2 = end
        
        # Normalize coordinates
        left, right = min(x1, x2), max(x1, x2)
        top, bottom = min(y1, y2), max(y1, y2)
        
        selected_elements = set()
        for element_id, layout_element in self.state.layout_result.elements.items():
            element_center = layout_element.get_center()
            if (left <= element_center[0] <= right and 
                top <= element_center[1] <= bottom):
                selected_elements.add(element_id)
        
        # Update selection
        if self.selection_manager:
            self.selection_manager.clear_selection()
            for element_id in selected_elements:
                self.selection_manager.select_element(element_id)
    
    def _find_area_at_position(self, position: Coordinate) -> ElementID:
        """Find the area (cut or sheet) at the given position"""
        if not self.state.layout_result:
            return self.state.graph.sheet
        
        # Find innermost cut containing the position
        innermost_cut = None
        for element_id, layout_element in self.state.layout_result.elements.items():
            if (layout_element.element_type == 'cut' and 
                layout_element.contains_point(position)):
                if (innermost_cut is None or 
                    self._is_more_nested(element_id, innermost_cut)):
                    innermost_cut = element_id
        
        return innermost_cut or self.state.graph.sheet
    
    def _is_more_nested(self, cut1: ElementID, cut2: ElementID) -> bool:
        """Check if cut1 is more nested than cut2"""
        if not self.state.layout_result:
            return False
        
        # Simple heuristic: smaller area is more nested
        layout1 = self.state.layout_result.elements.get(cut1)
        layout2 = self.state.layout_result.elements.get(cut2)
        
        if layout1 and layout2:
            area1 = (layout1.bounds[2] - layout1.bounds[0]) * (layout1.bounds[3] - layout1.bounds[1])
            area2 = (layout2.bounds[2] - layout2.bounds[0]) * (layout2.bounds[3] - layout2.bounds[1])
            return area1 < area2
        
        return False
    
    def _hash_graph(self, graph: RelationalGraphWithCuts) -> str:
        """Create hash of graph for layout caching"""
        # Simple hash based on element counts and structure
        vertex_count = len(graph.V)
        edge_count = len(graph.E)
        cut_count = len(graph.Cut)
        area_count = len(graph.area)
        
        return f"{vertex_count}_{edge_count}_{cut_count}_{area_count}_{hash(str(graph.area))}"


# Factory functions for easy integration

def create_diagram_controller(canvas: Canvas, 
                            canvas_width: int = 800, canvas_height: int = 600,
                            theme: VisualTheme = VisualTheme.DAU_STANDARD) -> DiagramController:
    """Factory function to create diagram controller"""
    return DiagramController(canvas, canvas_width, canvas_height, theme)


def create_controller_with_graph(canvas: Canvas, graph: RelationalGraphWithCuts,
                               canvas_width: int = 800, canvas_height: int = 600) -> DiagramController:
    """Factory function to create controller with initial graph"""
    controller = create_diagram_controller(canvas, canvas_width, canvas_height)
    controller.set_graph(graph)
    return controller
