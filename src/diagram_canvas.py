"""
Main diagram canvas interface for Existential Graph visualization.
Connects the Dau-compliant RelationalGraphWithCuts system with canvas backends for rendering.
"""

from typing import Optional, Dict, List, Tuple, Set, Any
from dataclasses import dataclass
import math
import sys
import os
from egi_core_dau import RelationalGraphWithCuts, ElementID
import uuid
from frozendict import frozendict
import circlify

# Get absolute path to the shared directory
SHARED_DIR = os.path.join(os.path.dirname(__file__), os.pardir, 'shared')
sys.path.append(SHARED_DIR)

try:
    from .egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
    from .canvas_backend import (
        Canvas, CanvasBackend, get_optimal_backend, create_backend,
        DrawingStyle, EGDrawingStyles, CanvasEvent, EventType, Coordinate
    )
    from .selection_system import (
        SelectionManager, SelectionMode, SelectionContext, 
        integrate_with_diagram_canvas, create_selection_manager_for_context
    )
except ImportError:
    # Fallback to absolute imports when running as script
    from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
    from canvas_backend import (
        Canvas, CanvasBackend, get_optimal_backend, create_backend,
        DrawingStyle, EGDrawingStyles, CanvasEvent, EventType, Coordinate
    )
    from selection_system import (
        SelectionManager, SelectionMode, SelectionContext, 
        integrate_with_diagram_canvas, create_selection_manager_for_context
    )


@dataclass(frozen=True)
class VisualElement:
    """Base class for visual representation of Dau graph elements"""
    element_id: ElementID
    position: Coordinate
    bounds: Tuple[float, float, float, float]  # x1, y1, x2, y2
    
    def contains_point(self, point: Coordinate) -> bool:
        """Check if point is within this element's bounds"""
        x, y = point
        x1, y1, x2, y2 = self.bounds
        return x1 <= x <= x2 and y1 <= y <= y2


@dataclass(frozen=True)
class VisualVertex(VisualElement):
    """Visual representation of a Dau vertex"""
    radius: float = 5.0
    is_generic: bool = True
    label: Optional[str] = None


@dataclass(frozen=True)
class VisualEdge(VisualElement):
    """Visual representation of a Dau edge (relation)"""
    relation_name: str
    vertex_positions: List[Coordinate]


@dataclass(frozen=True)
class VisualCut(VisualElement):
    """Visual representation of a Dau cut"""
    curve_points: List[Coordinate]
    depth: int
    is_sheet: bool = False


class DiagramLayout:
    """Handles automatic layout of Dau graph elements for visualization"""
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.margin = 50
        self.vertex_radius = 5
        self.min_vertex_distance = 40
        self.cut_padding = 30
    
    def layout_graph(self, graph: RelationalGraphWithCuts) -> Dict[ElementID, VisualElement]:
        """Generate layout for all elements in a Dau graph"""
        visual_elements = {}
        
        # First, layout cuts from outermost to innermost by depth
        cuts_by_depth = self._group_cuts_by_depth(graph)
        cut_bounds = {}
        
        # Always create sheet bounds first
        sheet_bounds = (self.margin, self.margin, 
                       self.width - self.margin, self.height - self.margin)
        cut_bounds[graph.sheet] = sheet_bounds
        
        # Track cuts per context for positioning
        cuts_per_context = {}
        
        # Use simple non-overlapping layout for now (circlify was causing overlaps)
        visual_cuts = self._layout_cuts_simple(graph)
        
        # Add visual cuts to elements and bounds
        for cut_id, visual_cut in visual_cuts.items():
            visual_elements[cut_id] = visual_cut
            cut_bounds[cut_id] = visual_cut.bounds
        
        # Layout vertices within their contexts
        for vertex in graph.V:
            visual_vertex = self._layout_vertex(vertex, graph, cut_bounds)
            visual_elements[vertex.id] = visual_vertex
        
        # Layout edges connecting vertices
        for edge in graph.E:
            visual_edge = self._layout_edge(edge, graph, visual_elements)
            visual_elements[edge.id] = visual_edge
        
        return visual_elements
    
    def _group_cuts_by_depth(self, graph: RelationalGraphWithCuts) -> Dict[int, List[Cut]]:
        """Group cuts by their nesting depth"""
        cuts_by_depth = {}
        for cut in graph.Cut:
            depth = graph.get_nesting_depth(cut.id)
            if depth not in cuts_by_depth:
                cuts_by_depth[depth] = []
            cuts_by_depth[depth].append(cut)
        return cuts_by_depth
    
    def _build_cut_hierarchy(self, graph: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Build hierarchical tree structure for cuts using circlify"""
        # Find all cuts and their parent relationships
        cut_tree = {
            'id': 'sheet',
            'datum': self.width * self.height,  # Sheet area
            'children': []
        }
        
        # Build hierarchy recursively
        def add_cuts_to_parent(parent_id: str, parent_node: Dict[str, Any]):
            # Find cuts that belong to this parent
            child_cuts = []
            for cut in graph.Cut:
                # Check if this cut is directly contained in the parent
                if parent_id in graph.area and cut.id in graph.area[parent_id]:
                    child_cuts.append(cut)
            
            # Add each child cut to the parent node
            for cut in child_cuts:
                # Calculate a size value for this cut (could be based on content)
                cut_size = 100  # Default size - could be made smarter
                
                cut_node = {
                    'id': cut.id,
                    'datum': cut_size,
                    'children': []
                }
                
                # Recursively add cuts contained within this cut
                add_cuts_to_parent(cut.id, cut_node)
                
                parent_node['children'].append(cut_node)
        
        # Build the tree starting from the sheet
        add_cuts_to_parent(graph.sheet, cut_tree)
        
        return cut_tree
    
    def _convert_to_circlify_format(self, hierarchy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert our hierarchy format to circlify's expected format"""
        def convert_node(node):
            result = {
                'id': node['id'],
                'datum': node['datum']
            }
            if node['children']:
                result['children'] = [convert_node(child) for child in node['children']]
            return result
        
        # Return the children of the root (sheet) node
        return [convert_node(child) for child in hierarchy['children']]
    
    def _layout_cuts_with_circlify(self, cut_hierarchy: Dict[str, Any], graph: RelationalGraphWithCuts) -> Dict[ElementID, VisualCut]:
        """Use circlify to layout cuts with proper hierarchical containment"""
        visual_cuts = {}
        
        # If no cuts to layout, return empty
        if not cut_hierarchy['children']:
            return visual_cuts
        
        # Convert hierarchy to circlify format
        circlify_data = self._convert_to_circlify_format(cut_hierarchy)
        
        # Use circlify to compute circle positions
        circles = circlify.circlify(
            circlify_data,
            target_enclosure=circlify.Circle(x=0, y=0, r=1)
        )
        
        # Recursively process circles with proper nesting
        def process_circle_hierarchy(circle, parent_bounds=None):
            # Get the cut ID from the circle
            cut_id = getattr(circle, 'ex', {}).get('id', None)
            if not cut_id or cut_id == 'sheet':
                # Process children if this is the root
                if hasattr(circle, 'children'):
                    for child_circle in circle.children:
                        process_circle_hierarchy(child_circle, parent_bounds)
                return
            
            # Calculate canvas coordinates
            if parent_bounds is None:
                # Top-level cut - use full canvas
                canvas_x = (circle.x + 1) * self.width / 2
                canvas_y = (circle.y + 1) * self.height / 2
                canvas_r = circle.r * min(self.width, self.height) / 2
            else:
                # Nested cut - position relative to parent
                px1, py1, px2, py2 = parent_bounds
                parent_width = px2 - px1
                parent_height = py2 - py1
                parent_center_x = (px1 + px2) / 2
                parent_center_y = (py1 + py2) / 2
                
                # Scale circle position relative to parent
                canvas_x = parent_center_x + circle.x * parent_width / 2
                canvas_y = parent_center_y + circle.y * parent_height / 2
                canvas_r = circle.r * min(parent_width, parent_height) / 2
            
            # Ensure minimum size
            min_radius = 30
            if canvas_r < min_radius:
                canvas_r = min_radius
            
            # Create visual cut bounds
            x1 = canvas_x - canvas_r
            y1 = canvas_y - canvas_r
            x2 = canvas_x + canvas_r
            y2 = canvas_y + canvas_r
            
            curve_points = self._generate_oval_points(x1, y1, x2, y2)
            depth = graph.get_nesting_depth(cut_id)
            
            visual_cut = VisualCut(
                element_id=cut_id,
                position=(x1, y1),
                bounds=(x1, y1, x2, y2),
                curve_points=curve_points,
                depth=depth,
                is_sheet=False
            )
            
            visual_cuts[cut_id] = visual_cut
            
            # Process children with this cut as parent bounds
            if hasattr(circle, 'children'):
                for child_circle in circle.children:
                    process_circle_hierarchy(child_circle, (x1, y1, x2, y2))
        
        # Process the circle hierarchy starting from root
        if circles:
            # Handle both single circle and list of circles
            if isinstance(circles, list):
                for circle in circles:
                    process_circle_hierarchy(circle)
            else:
                process_circle_hierarchy(circles)
        
        return visual_cuts
    
    def _layout_cut(self, cut: Cut, graph: RelationalGraphWithCuts, 
               cut_bounds: Dict[ElementID, Tuple[float, float, float, float]], 
               sibling_cuts: List[ElementID]) -> VisualCut:
        """Layout a single cut with proper hierarchical containment (no overlapping)"""
        depth = graph.get_nesting_depth(cut.id)
        
        # Find parent context
        parent_context = None
        for context_id, area_contents in graph.area.items():
            if cut.id in area_contents:
                parent_context = context_id
                break
        
        if parent_context and parent_context in cut_bounds:
            # Nested cut - must be contained within parent bounds
            px1, py1, px2, py2 = cut_bounds[parent_context]
            
            # Calculate available space within parent
            padding = self.cut_padding
            available_width = px2 - px1 - 2 * padding
            available_height = py2 - py1 - 2 * padding
            
            # Find sibling cuts at the same nesting level
            sibling_index = sibling_cuts.index(cut.id) if cut.id in sibling_cuts else 0
            num_siblings = len(sibling_cuts)
            
            # Calculate dimensions for this cut
            if num_siblings == 1:
                # Single cut - use most of available space
                cut_width = available_width * 0.8
                cut_height = available_height * 0.8
                x1 = px1 + padding + (available_width - cut_width) / 2
                y1 = py1 + padding + (available_height - cut_height) / 2
            else:
                # Multiple sibling cuts - arrange side by side
                cut_width = available_width / num_siblings * 0.9  # Leave some spacing
                cut_height = available_height * 0.8
                
                spacing = available_width / num_siblings
                x1 = px1 + padding + sibling_index * spacing + (spacing - cut_width) / 2
                y1 = py1 + padding + (available_height - cut_height) / 2
            
            # Ensure minimum size
            min_size = 80
            if cut_width < min_size:
                cut_width = min_size
            if cut_height < min_size:
                cut_height = min_size
            
            x2 = x1 + cut_width
            y2 = y1 + cut_height
            
            # Ensure cut stays within parent bounds
            if x2 > px2 - padding:
                x2 = px2 - padding
                x1 = x2 - cut_width
            if y2 > py2 - padding:
                y2 = py2 - padding
                y1 = y2 - cut_height
            
            # Generate oval curve points
            curve_points = self._generate_oval_points(x1, y1, x2, y2)
            
            return VisualCut(
                element_id=cut.id,
                position=(x1, y1),
                bounds=(x1, y1, x2, y2),
                curve_points=curve_points,
                depth=depth,
                is_sheet=False
            )
        else:
            # Top-level cut in sheet - arrange among sheet-level siblings
            sibling_index = sibling_cuts.index(cut.id) if cut.id in sibling_cuts else 0
            num_siblings = len(sibling_cuts)
            
            # Use sheet dimensions
            sheet_width = self.width - 2 * self.cut_padding
            sheet_height = self.height - 2 * self.cut_padding
            
            if num_siblings == 1:
                # Single top-level cut
                cut_width = sheet_width * 0.6
                cut_height = sheet_height * 0.6
                x1 = self.cut_padding + (sheet_width - cut_width) / 2
                y1 = self.cut_padding + (sheet_height - cut_height) / 2
            else:
                # Multiple top-level cuts - arrange in grid
                cols = int(math.ceil(math.sqrt(num_siblings)))
                rows = int(math.ceil(num_siblings / cols))
                
                col = sibling_index % cols
                row = sibling_index // cols
                
                cut_width = sheet_width / cols * 0.9
                cut_height = sheet_height / rows * 0.9
                
                x1 = self.cut_padding + col * (sheet_width / cols) + (sheet_width / cols - cut_width) / 2
                y1 = self.cut_padding + row * (sheet_height / rows) + (sheet_height / rows - cut_height) / 2
            
            x2 = x1 + cut_width
            y2 = y1 + cut_height
            
            curve_points = self._generate_oval_points(x1, y1, x2, y2)
            
            return VisualCut(
                element_id=cut.id,
                position=(x1, y1),
                bounds=(x1, y1, x2, y2),
                curve_points=curve_points,
                depth=depth,
                is_sheet=False
            )
    
    def _layout_vertex(self, vertex: Vertex, graph: RelationalGraphWithCuts,
                      cut_bounds: Dict[ElementID, Tuple[float, float, float, float]]) -> VisualVertex:
        """Layout a single vertex"""
        # Find which context contains this vertex
        context_id = graph.get_context(vertex.id)
        if not context_id:
            context_id = graph.sheet  # Default to sheet
        
        context_bound = cut_bounds.get(context_id)
        if context_bound:
            x1, y1, x2, y2 = context_bound
            
            # Simple positioning - could be improved with force-directed layout
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            # Add some randomness to avoid overlapping
            import random
            offset_x = random.uniform(-50, 50)
            offset_y = random.uniform(-50, 50)
            
            pos_x = max(x1 + self.vertex_radius, min(x2 - self.vertex_radius, center_x + offset_x))
            pos_y = max(y1 + self.vertex_radius, min(y2 - self.vertex_radius, center_y + offset_y))
            
            bounds = (
                pos_x - self.vertex_radius,
                pos_y - self.vertex_radius,
                pos_x + self.vertex_radius,
                pos_y + self.vertex_radius
            )
            
            return VisualVertex(
                element_id=vertex.id,
                position=(pos_x, pos_y),
                bounds=bounds,
                radius=self.vertex_radius,
                is_generic=vertex.is_generic,
                label=vertex.label
            )
        else:
            # Fallback positioning
            return VisualVertex(
                element_id=vertex.id,
                position=(100, 100),
                bounds=(95, 95, 105, 105),
                radius=self.vertex_radius,
                is_generic=vertex.is_generic,
                label=vertex.label
            )
    
    def _layout_edge(self, edge: Edge, graph: RelationalGraphWithCuts,
                    visual_elements: Dict[ElementID, VisualElement]) -> VisualEdge:
        """Layout a single edge (relation)"""
        # Get incident vertices via nu mapping
        incident_vertices = graph.get_incident_vertices(edge.id)
        relation_name = graph.get_relation_name(edge.id)
        
        # Get positions of incident vertices
        vertex_positions = []
        for vertex_id in incident_vertices:
            if vertex_id in visual_elements:
                visual_vertex = visual_elements[vertex_id]
                vertex_positions.append(visual_vertex.position)
        
        if vertex_positions:
            # Position relation label at centroid of vertices
            center_x = sum(pos[0] for pos in vertex_positions) / len(vertex_positions)
            center_y = sum(pos[1] for pos in vertex_positions) / len(vertex_positions)
            
            # Estimate text bounds (simplified)
            text_width = len(relation_name) * 8
            text_height = 12
            
            bounds = (
                center_x - text_width / 2,
                center_y - text_height / 2,
                center_x + text_width / 2,
                center_y + text_height / 2
            )
            
            return VisualEdge(
                element_id=edge.id,
                position=(center_x, center_y),
                bounds=bounds,
                relation_name=relation_name,
                vertex_positions=vertex_positions
            )
        else:
            # Fallback
            return VisualEdge(
                element_id=edge.id,
                position=(200, 200),
                bounds=(190, 190, 210, 210),
                relation_name=relation_name,
                vertex_positions=[]
            )
    
    def _layout_cuts_simple(self, graph: RelationalGraphWithCuts) -> Dict[ElementID, VisualCut]:
        """Simple, reliable cut layout that ensures cuts are visible and non-overlapping"""
        visual_cuts = {}
        
        # Group cuts by their containing area
        cuts_by_area = {}
        for cut in graph.Cut:
            # Find which area contains this cut
            containing_area = None
            for area_id, area_contents in graph.area.items():
                if cut.id in area_contents:
                    containing_area = area_id
                    break
            
            if containing_area not in cuts_by_area:
                cuts_by_area[containing_area] = []
            cuts_by_area[containing_area].append(cut)
        
        # Layout cuts for each area
        for area_id, cuts in cuts_by_area.items():
            if area_id == graph.sheet:
                # Sheet-level cuts: distribute across canvas with proper spacing
                for i, cut in enumerate(cuts):
                    # Position cuts in a horizontal line with generous spacing
                    num_cuts = len(cuts)
                    if num_cuts == 1:
                        center_x = self.width / 2
                        center_y = self.height / 2
                        radius = min(self.width, self.height) / 4
                    else:
                        # Distribute horizontally with spacing
                        margin = 150  # Generous margin
                        available_width = self.width - 2 * margin
                        spacing = available_width / max(1, num_cuts - 1) if num_cuts > 1 else 0
                        
                        center_x = margin + i * spacing
                        center_y = self.height / 2
                        
                        # Calculate radius to ensure no overlap
                        max_radius = min(spacing / 2.5, 120) if num_cuts > 1 else 120
                        radius = max(60, max_radius)  # Minimum 60px radius
                    
                    x1 = center_x - radius
                    y1 = center_y - radius
                    x2 = center_x + radius
                    y2 = center_y + radius
                    
                    curve_points = self._generate_oval_points(x1, y1, x2, y2)
                    depth = graph.get_nesting_depth(cut.id)
                    
                    visual_cut = VisualCut(
                        element_id=cut.id,
                        position=(x1, y1),
                        bounds=(x1, y1, x2, y2),
                        curve_points=curve_points,
                        depth=depth,
                        is_sheet=False
                    )
                    visual_cuts[cut.id] = visual_cut
                    print(f"Positioned cut {cut.id} at ({center_x:.1f}, {center_y:.1f}) with radius {radius:.1f}")
            
            else:
                # Nested cuts: position within parent area
                # For now, use simple offset positioning
                for i, cut in enumerate(cuts):
                    # Find parent cut bounds (simplified)
                    parent_center_x = self.width / 2
                    parent_center_y = self.height / 2
                    parent_radius = min(self.width, self.height) / 4
                    
                    # Offset nested cuts
                    offset_x = (i % 2) * 100 - 50
                    offset_y = (i // 2) * 100 - 50
                    
                    center_x = parent_center_x + offset_x
                    center_y = parent_center_y + offset_y
                    radius = parent_radius * 0.6  # Smaller than parent
                    
                    x1 = center_x - radius
                    y1 = center_y - radius
                    x2 = center_x + radius
                    y2 = center_y + radius
                    
                    curve_points = self._generate_oval_points(x1, y1, x2, y2)
                    depth = graph.get_nesting_depth(cut.id)
                    
                    visual_cut = VisualCut(
                        element_id=cut.id,
                        position=(x1, y1),
                        bounds=(x1, y1, x2, y2),
                        curve_points=curve_points,
                        depth=depth,
                        is_sheet=False
                    )
                    visual_cuts[cut.id] = visual_cut
                    print(f"Positioned nested cut {cut.id} at ({center_x:.1f}, {center_y:.1f}) with radius {radius:.1f}")
        
        return visual_cuts
    
    def _generate_oval_points(self, x1: float, y1: float, x2: float, y2: float) -> List[Coordinate]:
        """Generate points for an oval curve"""
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        radius_x = (x2 - x1) / 2
        radius_y = (y2 - y1) / 2
        
        points = []
        num_points = 32
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = center_x + radius_x * math.cos(angle)
            y = center_y + radius_y * math.sin(angle)
            points.append((x, y))
        
        return points


class DiagramCanvas:
    """Main interface for rendering and interacting with Dau graph diagrams"""
    
    def __init__(self, width: int = 800, height: int = 600, 
                 backend_name: Optional[str] = None, canvas: Optional[Canvas] = None):
        self.width = width
        self.height = height
        
        # Create canvas backend
        if canvas:
            # Use provided canvas
            self.canvas = canvas
        elif backend_name:
            self.canvas = create_backend(backend_name, width=width, height=height)
        else:
            self.canvas = get_optimal_backend()
        
        # Current state
        self.graph: Optional[RelationalGraphWithCuts] = None
        self.visual_elements: Dict[ElementID, VisualElement] = {}
        self.layout_engine = DiagramLayout(width, height)
        
        # Interaction state
        self.hover_element: Optional[ElementID] = None
        self._rendering_in_progress = False  # Guard against infinite rendering loops
        
        # Robust selection system (replaces ad-hoc selection state)
        self.selection_manager: Optional[SelectionManager] = None
        
        # Legacy compatibility properties
        self.pending_cut_mode = None  # Store the cut placement mode during selection
        
        # Visual selection state for drag-to-select
        self.selection_start = None
        self.selection_current = None
        self.is_dragging_selection = False
        self.selection_rectangle = None
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def render_graph(self, graph: RelationalGraphWithCuts):
        """Render a Dau graph as a diagram"""
        self.graph = graph
        print(f"Rendering graph with {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
        self.visual_elements = self.layout_engine.layout_graph(graph)
        print(f"Created {len(self.visual_elements)} visual elements:")
        for elem_id, visual_elem in self.visual_elements.items():
            print(f"  - {elem_id}: {type(visual_elem).__name__}")
        
        # Initialize robust selection system for this graph
        self.selection_manager = create_selection_manager_for_context(graph, SelectionContext.EDITING)
        integrate_with_diagram_canvas(self, self.selection_manager)
        
        self._render_diagram()
        print("Diagram rendering complete")
    
    def _render_diagram(self):
        """Render the current diagram to canvas"""
        if not self.graph or not self.visual_elements:
            return
        
        # Guard against infinite rendering loops
        if self._rendering_in_progress:
            print("Rendering already in progress - skipping to prevent loop")
            return
        
        self._rendering_in_progress = True
        try:
            self.canvas.clear()
            
            # Render cuts first, from outermost to innermost
            cuts = [elem for elem in self.visual_elements.values() 
                   if isinstance(elem, VisualCut)]
            cuts.sort(key=lambda c: c.depth)
            
            print(f"Rendering {len(cuts)} cuts:")
            for visual_cut in cuts:
                if not visual_cut.is_sheet:  # Don't draw the sheet of assertion
                    print(f"  - Cut {visual_cut.element_id}: center=({visual_cut.position[0]:.1f}, {visual_cut.position[1]:.1f}), size=({visual_cut.bounds[2]-visual_cut.bounds[0]:.1f}, {visual_cut.bounds[3]-visual_cut.bounds[1]:.1f})")
                    style = EGDrawingStyles.CUT_LINE
                    if (self.selection_manager and 
                        visual_cut.element_id in self.selection_manager.state.selected_elements):
                        style = EGDrawingStyles.HIGHLIGHT  # SelectionManager highlighting
                        print(f"  -> HIGHLIGHTING cut {visual_cut.element_id} (SELECTED)")
                    
                    self.canvas.draw_curve(
                        visual_cut.curve_points, 
                        style, 
                        closed=True
                    )
                else:
                    print(f"  - Sheet {visual_cut.element_id}: (not drawn)")
            
            # Render edges (relations)
            edges = [elem for elem in self.visual_elements.values() 
                    if isinstance(elem, VisualEdge)]
            
            for visual_edge in edges:
                # Draw lines from relation to vertices
                for vertex_pos in visual_edge.vertex_positions:
                    style = EGDrawingStyles.EDGE_LINE
                    if (self.selection_manager and 
                        visual_edge.element_id in self.selection_manager.state.selected_elements):
                        style = EGDrawingStyles.HIGHLIGHT  # SelectionManager highlighting
                    
                    self.canvas.draw_line(
                        visual_edge.position,
                        vertex_pos,
                        style
                    )
                
                # Draw relation name
                text_style = EGDrawingStyles.RELATION_SIGN
                if (self.selection_manager and 
                    visual_edge.element_id in self.selection_manager.state.selected_elements):
                    text_style = EGDrawingStyles.HIGHLIGHT  # SelectionManager highlighting
                
                self.canvas.draw_text(
                    visual_edge.relation_name,
                    visual_edge.position,
                    text_style
                )
            
            # Render vertices
            vertices = [elem for elem in self.visual_elements.values() 
                       if isinstance(elem, VisualVertex)]
            
            for visual_vertex in vertices:
                style = EGDrawingStyles.VERTEX_SPOT
                if (self.selection_manager and 
                    visual_vertex.element_id in self.selection_manager.state.selected_elements):
                    style = EGDrawingStyles.HIGHLIGHT  # SelectionManager highlighting
                    print(f"  -> HIGHLIGHTING vertex {visual_vertex.element_id} (SELECTED)")
                
                self.canvas.draw_circle(
                    visual_vertex.position,
                    visual_vertex.radius,
                    style
                )
                
                # Draw label if vertex has one (constant)
                if visual_vertex.label:
                    label_pos = (
                        visual_vertex.position[0] + visual_vertex.radius + 5,
                        visual_vertex.position[1] - 6
                    )
                    self.canvas.draw_text(
                        visual_vertex.label,
                        label_pos,
                        EGDrawingStyles.RELATION_SIGN
                    )
            
            # Render selection rectangle if dragging
            if self.is_dragging_selection and self.selection_start and self.selection_current:
                x1, y1 = self.selection_start
                x2, y2 = self.selection_current
                
                # Draw selection rectangle with dashed line
                selection_points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
                self.canvas.draw_curve(selection_points, EGDrawingStyles.SELECTION_RECTANGLE, closed=True)
            
            # Render stored selection rectangle if exists
            if self.selection_rectangle:
                x1, y1, x2, y2 = self.selection_rectangle
                selection_points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
                self.canvas.draw_curve(selection_points, EGDrawingStyles.SELECTION_AREA, closed=True)
            
            self.canvas.update()
        finally:
            self._rendering_in_progress = False
    
    def _setup_event_handlers(self):
        """Setup canvas event handlers for interaction"""
        # Bind events
        self.canvas.add_event_handler(EventType.MOUSE_CLICK, self._on_mouse_click)
        self.canvas.add_event_handler(EventType.MOUSE_DRAG, self._on_mouse_drag)
        self.canvas.add_event_handler(EventType.MOUSE_RELEASE, self._on_mouse_release)
        self.canvas.add_event_handler(EventType.KEY_PRESS, self._on_key_press)
    
    def _on_mouse_click(self, event: CanvasEvent):
        """Handle mouse click events - start of drag-to-select or element selection"""
        clicked_element = self._find_element_at_point(event.position)
        
        # Start drag-to-select operation
        self.selection_start = event.position
        self.selection_current = event.position
        self.is_dragging_selection = False  # Will be set to True in drag event
        
        # Handle multi-select mode for enclosing cuts
        if (self.selection_manager and 
            self.selection_manager.state.context == SelectionContext.ENCLOSING):
            
            # Check for modifier keys (Cmd on Mac, Alt on others)
            has_modifier = False
            if hasattr(event, 'modifiers'):
                has_modifier = ('cmd' in event.modifiers or 'command' in event.modifiers or 'alt' in event.modifiers)
            elif hasattr(event, 'state'):
                # Tkinter state bitmask: 0x8 = Alt, 0x20000 = Cmd (Mac)
                has_modifier = (event.state & 0x8) or (event.state & 0x20000)
            
            if has_modifier:
                if clicked_element:
                    print(f"Modifier-click detected on element: {clicked_element}")
                    self.toggle_element_selection(clicked_element)
                    self._render_diagram()
                    return
            else:
                print("In selection mode: Cmd-click (Mac) or Alt-click elements to select them, Enter to confirm, Escape to cancel")
                return
        
        # Normal click handling
        if clicked_element:
            self.selected_element = clicked_element
            print(f"Selected element: {clicked_element}")
        else:
            self.selected_element = None
            print("Deselected")
        
        self.pending_cut_mode = None
        self._render_diagram()
    
    def _on_mouse_drag(self, event: CanvasEvent):
        """Handle mouse drag events - create selection rectangle"""
        if self.selection_start:
            self.is_dragging_selection = True
            self.selection_current = event.position
            self._render_diagram()  # Redraw with selection rectangle
    
    def _on_mouse_release(self, event: CanvasEvent):
        """Handle mouse release events - complete selection"""
        if self.is_dragging_selection and self.selection_start and self.selection_current:
            # Calculate selection rectangle
            x1, y1 = self.selection_start
            x2, y2 = self.selection_current
            
            # Normalize rectangle (ensure x1 < x2, y1 < y2)
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_y, max_y = min(y1, y2), max(y1, y2)
            
            # Find elements within selection rectangle
            selected_elements = []
            for element_id, visual_element in self.visual_elements.items():
                elem_x, elem_y = visual_element.position
                if min_x <= elem_x <= max_x and min_y <= elem_y <= max_y:
                    selected_elements.append(element_id)
            
            # Update selection manager
            if self.selection_manager:
                for element_id in selected_elements:
                    self.selection_manager.select_element(element_id)
                print(f"Selected {len(selected_elements)} elements via drag: {selected_elements}")
            
            # Check if selection is empty (selecting empty area)
            if not selected_elements:
                print(f"Selected empty area: ({min_x:.1f}, {min_y:.1f}) to ({max_x:.1f}, {max_y:.1f})")
                # Store the selected area for future element placement
                self.selection_rectangle = (min_x, min_y, max_x, max_y)
        
        # Reset drag state
        self.is_dragging_selection = False
        self.selection_start = None
        self.selection_current = None
        self._render_diagram()
    
    def _on_key_press(self, event: CanvasEvent):
        """Handle key press events"""
        if (self.selection_manager and 
            self.selection_manager.state.context == SelectionContext.ENCLOSING):
            if event.key == 'Return' or event.key == 'Enter':
                # Confirm selection and create enclosing cut
                if self.selection_manager.state.selected_elements:
                    # Use center of canvas as default position for the cut
                    center_position = (self.width / 2, self.height / 2)
                    self.confirm_selection_and_create_cut(center_position)
                else:
                    print("No elements selected - cannot create enclosing cut")
            elif event.key == 'Escape':
                # Cancel selection mode
                self.exit_selection_mode()
        else:
            # Normal key handling when not in selection mode
            if event.key == 'Escape':
                self.selected_element = None
                self._render_diagram()
    
    def _find_element_at_point(self, point: Coordinate) -> Optional[ElementID]:
        """Find the visual element at the given point"""
        # Check in reverse rendering order (vertices first, then edges, then cuts)
        for visual_element in self.visual_elements.values():
            if visual_element.contains_point(point):
                return visual_element.element_id
        return None
    
    def save_diagram(self, filename: str, format: str = "png"):
        """Save the current diagram to file"""
        self.canvas.save_to_file(filename, format)
    
    def run(self):
        """Start the interactive diagram viewer"""
        self.canvas.run_event_loop()
    
    def close(self):
        """Close the diagram canvas"""
        self.canvas.stop_event_loop()

    def find_area_at_position(self, position: tuple[float, float]) -> ElementID:
        """Find the innermost area (cut or sheet) at a given canvas position."""
        if not hasattr(self, 'visual_elements') or self.visual_elements is None:
            # If visual elements haven't been calculated, default to the sheet
            return self.graph.sheet

        px, py = position
        # Default to the sheet of assertion
        innermost_area_id = self.graph.sheet
        smallest_area_size = float('inf')

        # Check containment for each cut using visual elements
        for element_id, visual_element in self.visual_elements.items():
            if isinstance(visual_element, VisualCut):
                x1, y1, x2, y2 = visual_element.bounds
                if x1 <= px <= x2 and y1 <= py <= y2:
                    # The point is inside this cut's bounding box
                    cut_area_size = (x2 - x1) * (y2 - y1)
                    if cut_area_size < smallest_area_size:
                        smallest_area_size = cut_area_size
                        innermost_area_id = element_id
        
        return innermost_area_id

    def find_vertex_area(self, vertex_id: ElementID) -> ElementID:
        """Find which area (cut or sheet) contains a given vertex."""
        for area_id, vertex_set in self.graph.area.items():
            if vertex_id in vertex_set:
                return area_id
        # If not found in any area, default to sheet
        return self.graph.sheet

    def _find_parent_area(self, cut_id: ElementID) -> ElementID:
        """Find the parent area that contains the given cut."""
        for area_id, area_contents in self.graph.area.items():
            if cut_id in area_contents:
                return area_id
        # If not found, default to sheet
        return self.graph.sheet

    def _find_elements_in_area(self, center: tuple[float, float], radius: float = 100) -> Dict[str, List[ElementID]]:
        """Find all elements (vertices, edges, cuts) within a circular area."""
        cx, cy = center
        elements = {
            'vertices': [],
            'edges': [],
            'cuts': []
        }
        
        # Find vertices within the area
        for element_id, visual_element in self.visual_elements.items():
            if isinstance(visual_element, VisualVertex):
                vx, vy = visual_element.position
                distance = ((vx - cx) ** 2 + (vy - cy) ** 2) ** 0.5
                if distance <= radius:
                    elements['vertices'].append(element_id)
            
            elif isinstance(visual_element, VisualEdge):
                # Check if edge center is within area
                ex, ey = visual_element.position
                distance = ((ex - cx) ** 2 + (ey - cy) ** 2) ** 0.5
                if distance <= radius:
                    elements['edges'].append(element_id)
            
            elif isinstance(visual_element, VisualCut):
                # Check if cut center is within area
                x1, y1, x2, y2 = visual_element.bounds
                cut_cx = (x1 + x2) / 2
                cut_cy = (y1 + y2) / 2
                distance = ((cut_cx - cx) ** 2 + (cut_cy - cy) ** 2) ** 0.5
                if distance <= radius:
                    elements['cuts'].append(element_id)
        
        return elements
    
    def _reparent_elements_to_cut(self, elements_to_enclose: Dict[str, List[ElementID]], new_cut_id: ElementID) -> 'RelationalGraphWithCuts':
        """Reparent selected elements to a new cut area."""
        from frozendict import frozendict
        new_area = dict(self.graph.area)
        
        # Ensure the new cut has an area entry
        if new_cut_id not in new_area:
            new_area[new_cut_id] = frozenset()
        
        # Move vertices to new cut
        for vertex_id in elements_to_enclose['vertices']:
            # Find current area of vertex
            current_area = None
            for area_id, area_contents in new_area.items():
                if vertex_id in area_contents:
                    current_area = area_id
                    break
            
            if current_area:
                # Remove from current area
                new_area[current_area] = new_area[current_area] - {vertex_id}
                # Add to new cut area
                new_area[new_cut_id] = new_area[new_cut_id] | {vertex_id}
        
        # Move cuts to new cut (nested cuts)
        for cut_id in elements_to_enclose['cuts']:
            # Find current area of cut
            current_area = None
            for area_id, area_contents in new_area.items():
                if cut_id in area_contents:
                    current_area = area_id
                    break
            
            if current_area:
                # Remove from current area
                new_area[current_area] = new_area[current_area] - {cut_id}
                # Add to new cut area
                new_area[new_cut_id] = new_area[new_cut_id] | {cut_id}
        
        # Create new graph with updated areas
        return RelationalGraphWithCuts(
            V=self.graph.V,
            E=self.graph.E,
            nu=self.graph.nu,
            sheet=self.graph.sheet,
            Cut=self.graph.Cut,
            area=frozendict(new_area),
            rel=self.graph.rel
        )
    
    def enter_selection_mode(self, cut_placement_mode: str):
        """Enter multi-select mode for enclosing cut creation."""
        if not self.selection_manager:
            print("Error: SelectionManager not initialized")
            return
            
        # Set selection manager to enclosing context with multi-select mode
        self.selection_manager.set_context(SelectionContext.ENCLOSING, SelectionMode.MULTI)
        self.pending_cut_mode = cut_placement_mode
        print(f"Entered selection mode for {cut_placement_mode} enclosing cut")
        print("⌘-click elements to select them for enclosure. Press Enter to confirm or Escape to cancel.")
        self._render_diagram()
    
    def exit_selection_mode(self):
        """Exit selection mode without creating a cut."""
        if self.selection_manager:
            self.selection_manager.clear_selection()
            self.selection_manager.set_context(SelectionContext.EDITING, SelectionMode.SINGLE)
        self.pending_cut_mode = None
        print("Exited selection mode")
        self._render_diagram()
    
    def toggle_element_selection(self, element_id: ElementID) -> bool:
        """Toggle selection of an element. Returns True if element was added to selection."""
        if not self.selection_manager:
            print("Error: SelectionManager not initialized")
            return False
            
        # Use SelectionManager to handle selection
        was_selected = element_id in self.selection_manager.state.selected_elements
        changed = self.selection_manager.select_element(element_id)
        
        if changed:
            if was_selected:
                print(f"Deselected element: {element_id}")
                return False
            else:
                print(f"Selected element: {element_id}")
                
                # SelectionManager handles smart suggestions automatically
                if self.selection_manager.state.completion_suggestions:
                    suggestions = self.selection_manager.state.completion_suggestions[:3]
                    print(f"  Suggestion: Also consider selecting {', '.join(suggestions)}")
                
                return True
        return False
    
    def _get_logical_suggestions(self, selected_element_id: ElementID) -> List[str]:
        """Get smart suggestions for logically related elements to include in selection."""
        suggestions = []
        
        # If selecting a vertex, suggest connected edges (predicates)
        if selected_element_id in self.graph.V:
            for edge_id, edge in self.graph.E.items():
                if selected_element_id in edge.endpoints:
                    if edge_id not in self.selected_elements:
                        suggestions.append(f"predicate {edge_id}")
        
        # If selecting an edge, suggest connected vertices
        elif selected_element_id in self.graph.E:
            edge = self.graph.E[selected_element_id]
            for vertex_id in edge.endpoints:
                if vertex_id not in self.selected_elements:
                    suggestions.append(f"individual {vertex_id}")
        
        # If selecting a cut, suggest all contained elements
        elif selected_element_id in self.graph.Cut:
            if selected_element_id in self.graph.area:
                contained_elements = self.graph.area[selected_element_id]
                for element_id in contained_elements:
                    if element_id not in self.selected_elements:
                        if element_id in self.graph.V:
                            suggestions.append(f"individual {element_id}")
                        elif element_id in self.graph.E:
                            suggestions.append(f"predicate {element_id}")
                        elif element_id in self.graph.Cut:
                            suggestions.append(f"cut {element_id}")
        
        return suggestions[:3]  # Limit to 3 suggestions to avoid overwhelming
    
    def confirm_selection_and_create_cut(self, position: tuple[float, float]):
        """Create an enclosing cut around the selected elements."""
        if not self.selection_manager or not self.selection_manager.state.selected_elements:
            print("No elements selected for enclosing cut")
            return
        
        # Get selected elements from SelectionManager
        selected_elements = self.selection_manager.state.selected_elements
        
        # Convert selected elements to the format expected by _reparent_elements_to_cut
        elements_to_enclose = {
            'vertices': [eid for eid in selected_elements if eid in self.graph.V],
            'edges': [eid for eid in selected_elements if eid in self.graph.E],
            'cuts': [eid for eid in selected_elements if eid in self.graph.Cut]
        }
        
        # Create the new cut
        from egi_core_dau import create_cut
        new_cut = create_cut()
        
        # Determine parent area (where to place the enclosing cut)
        parent_area_id = self.find_area_at_position(position)
        
        # Add cut to graph
        self.graph = self.graph.with_cut(new_cut, parent_area_id)
        
        # Reparent selected elements to the new cut
        self.graph = self._reparent_elements_to_cut(elements_to_enclose, new_cut.id)
        
        enclosed_count = len(selected_elements)
        print(f"Created enclosing cut '{new_cut.id}' around {enclosed_count} selected elements")
        print(f"  Enclosed: {len(elements_to_enclose['vertices'])} individuals, {len(elements_to_enclose['edges'])} predicates, {len(elements_to_enclose['cuts'])} cuts")
        
        # Exit selection mode and redraw
        self.exit_selection_mode()
        return elements
    
    def add_enclosing_cut(self, selected_elements, bounds):
        """Add a cut that encloses the selected elements with proper bounds"""
        try:
            from egi_core_dau import RelationalGraphWithCuts
            from frozendict import frozendict
            import uuid
            
            # Create new cut ID
            cut_id = f"c_{uuid.uuid4().hex[:8]}"
            
            # Create the cut position and size based on calculated bounds
            center_x = bounds['center_x']
            center_y = bounds['center_y']
            width = bounds['width']
            height = bounds['height']
            
            print(f"Creating enclosing cut {cut_id} at ({center_x:.1f}, {center_y:.1f}) with size {width:.1f}x{height:.1f}")
            
            # Add cut to graph structure
            new_cuts = self.graph.Cut | {cut_id}
            
            # Move selected elements from their current area to the new cut
            new_area = dict(self.graph.area)
            
            # Find current areas of selected elements and move them to new cut
            cut_contents = set()
            for element_id in selected_elements:
                # Find which area currently contains this element
                for area_id, area_contents in self.graph.area.items():
                    if element_id in area_contents:
                        # Remove from current area
                        new_area[area_id] = area_contents - {element_id}
                        # Add to new cut
                        cut_contents.add(element_id)
                        break
            
            # Set the new cut's contents
            new_area[cut_id] = frozenset(cut_contents)
            
            # Create updated graph
            updated_graph = RelationalGraphWithCuts(
                V=self.graph.V,
                E=self.graph.E,
                nu=self.graph.nu,
                sheet=self.graph.sheet,
                Cut=new_cuts,
                area=frozendict(new_area),
                rel=self.graph.rel
            )
            
            # Update the graph and re-layout
            self.graph = updated_graph
            self.visual_elements = self.layout_engine.layout_graph(self.graph)
            
            # Clear selection and re-render
            if self.selection_manager:
                self.selection_manager.clear_selection()
            
            self._render_diagram()
            print(f"Successfully created enclosing cut {cut_id} around {len(selected_elements)} elements")
            
        except Exception as e:
            print(f"Error creating enclosing cut: {e}")
            import traceback
            traceback.print_exc()
    
    def delete_elements(self, element_ids):
        """Delete multiple elements from both graph data structure and visual elements"""
        try:
            from egi_core_dau import RelationalGraphWithCuts
            from frozendict import frozendict
            
            print(f"Deleting elements from graph: {element_ids}")
            
            # Update graph data structure
            new_vertices = self.graph.V - set(element_ids)
            new_edges = self.graph.E - set(element_ids)
            new_cuts = self.graph.Cut - set(element_ids)
            
            # Update areas by removing deleted elements
            new_area = {}
            for area_id, area_contents in self.graph.area.items():
                if area_id not in element_ids:  # Keep area if it's not being deleted
                    # Remove deleted elements from this area's contents
                    new_contents = area_contents - set(element_ids)
                    new_area[area_id] = new_contents
            
            # Update relations by removing edges that reference deleted elements
            new_rel = {}
            for edge_id, vertices in self.graph.rel.items():
                if edge_id not in element_ids:  # Keep edge if it's not being deleted
                    # Check if any referenced vertices are being deleted
                    if not any(v_id in element_ids for v_id in vertices):
                        new_rel[edge_id] = vertices
            
            # Create updated graph
            updated_graph = RelationalGraphWithCuts(
                V=new_vertices,
                E=new_edges,
                nu=self.graph.nu,
                sheet=self.graph.sheet,
                Cut=new_cuts,
                area=frozendict(new_area),
                rel=frozendict(new_rel)
            )
            
            # Update the graph and re-layout
            self.graph = updated_graph
            self.visual_elements = self.layout_engine.layout_graph(self.graph)
            
            # Clear selection and re-render
            if self.selection_manager:
                self.selection_manager.clear_selection()
            
            self._render_diagram()
            print(f"Successfully deleted {len(element_ids)} elements from graph")
            
        except Exception as e:
            print(f"Error deleting elements: {e}")
            import traceback
            traceback.print_exc()
    
    def delete_element(self, element_id):
        """Delete a single element from both graph data structure and visual elements"""
        self.delete_elements([element_id])
    
    def add_element(self, element_type: str, position: tuple[float, float], placement_mode: str = "nested"):
        """Adds a new element to the graph at the given position and redraws."""
        # Find which area the element was dropped in (needed for all element types)
        parent_area_id = self.find_area_at_position(position)
        
        try:
            if element_type == 'cut':
                # Handle different cut placement modes
                from egi_core_dau import create_cut
                new_cut = create_cut()
                
                if placement_mode == "nested":
                    # Nested: place inside the innermost cut at this position
                    cut_area_id = parent_area_id  # Use the already calculated area
                    self.graph = self.graph.with_cut(new_cut, cut_area_id)
                    print(f"Added nested cut '{new_cut.id}' inside area '{cut_area_id}'")
                    
                elif placement_mode == "sibling":
                    # Sibling: place at the same level as existing cuts
                    # Find the parent of the innermost cut at this position
                    if parent_area_id == self.graph.sheet:
                        # Already at sheet level
                        cut_area_id = self.graph.sheet
                    else:
                        # Find parent of the innermost cut
                        cut_area_id = self._find_parent_area(parent_area_id)
                    self.graph = self.graph.with_cut(new_cut, cut_area_id)
                    print(f"Added sibling cut '{new_cut.id}' beside existing cuts in area '{cut_area_id}'")
                    
                elif placement_mode == "enclosing":
                    # Enclosing: enter multi-select mode for precise subgraph selection
                    print("Entering multi-select mode for enclosing cut creation")
                    self.enter_selection_mode(placement_mode)
                    return  # Don't create cut yet - wait for user selection
                    
                else:
                    # Default to nested behavior
                    cut_area_id = parent_area_id
                    self.graph = self.graph.with_cut(new_cut, cut_area_id)
                    print(f"Added cut '{new_cut.id}' to area '{cut_area_id}' (default mode)")
            
            elif element_type == 'individual':
                # Create a new vertex (individual/line of identity) - same concept in Dau's formalism
                # This represents an "extant thing" that can be rendered as either a spot or line segment
                from egi_core_dau import create_vertex
                new_vertex = create_vertex()
                self.graph = self.graph.with_vertex(new_vertex)
                
                # Move the vertex to the correct area if not the sheet
                if parent_area_id != self.graph.sheet:
                    from frozendict import frozendict
                    from egi_core_dau import RelationalGraphWithCuts
                    new_area = dict(self.graph.area)
                    # Remove vertex from sheet
                    sheet_area = new_area[self.graph.sheet] - {new_vertex.id}
                    new_area[self.graph.sheet] = sheet_area
                    # Add vertex to target area
                    target_area = new_area[parent_area_id] | {new_vertex.id}
                    new_area[parent_area_id] = target_area
                    # Update graph
                    self.graph = RelationalGraphWithCuts(
                        V=self.graph.V,
                        E=self.graph.E,
                        nu=self.graph.nu,
                        sheet=self.graph.sheet,
                        Cut=self.graph.Cut,
                        area=frozendict(new_area),
                        rel=self.graph.rel
                    )
                
                print(f"Added individual '{new_vertex.id}' to area '{parent_area_id}'")

            elif element_type == 'predicate':
                # Create a new edge (predicate/relation) that attaches to individual line ends via "hooks"
                from egi_core_dau import create_edge
                
                # Find individuals (vertices) in the target area to attach the predicate to
                individuals_in_area = []
                for vertex in self.graph.V:
                    vertex_area = self.find_vertex_area(vertex.id)
                    if vertex_area == parent_area_id:
                        individuals_in_area.append(vertex.id)
                
                if len(individuals_in_area) >= 1:
                    # Create a predicate that attaches to the first individual found
                    # In Dau's formalism, predicates have "hooks" that attach to line ends
                    new_edge = create_edge()
                    vertex_tuple = (individuals_in_area[0],)  # Unary predicate
                    relation_name = "P"  # Default predicate name - could be made configurable
                    self.graph = self.graph.with_edge(new_edge, vertex_tuple, relation_name, parent_area_id)
                    print(f"Added predicate '{new_edge.id}' ({relation_name}) with hook attached to individual {vertex_tuple[0]} in area '{parent_area_id}'")
                else:
                    print(f"Cannot create predicate: need at least 1 individual in area '{parent_area_id}', found {len(individuals_in_area)}")
                    print("Note: In Dau's formalism, predicates attach to the ends of individual lines via 'hooks'")

            # Re-layout and redraw the canvas with the updated graph
            self.visual_elements = self.layout_engine.layout_graph(self.graph)
            self._render_diagram()
        except Exception as e:
            print(f"Error adding element: {e}")
            import traceback
            traceback.print_exc()
