"""
Dynamic View Generator for Existential Graphs

Implements Peirce-Dau 2D visualization conventions with:
- Readability-based page sizing
- Pan/zoom controls with text readability thresholds
- Context collapse/expansion (pseudo-zoom)
- Multi-modal navigation (cuts, semantic, ligature)
- Separation of visualization from EGI logical structure
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from enum import Enum
import math
from abc import ABC, abstractmethod

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from subgraph_extractor import SubgraphExtractor, SelectionCriteria, BoundaryHandling


class NavigationMode(Enum):
    """Different ways to navigate through the graph structure."""
    CUT_TREE = "cut_tree"           # Hierarchical navigation through cut nesting
    SEMANTIC = "semantic"           # Navigate by semantic similarity
    LIGATURE = "ligature"          # Follow edge connections between vertices
    SPATIAL = "spatial"            # Navigate by spatial proximity


class DetailLevel(Enum):
    """Level of detail for rendering at different zoom levels."""
    OVERVIEW = "overview"          # Show only major cuts and structure
    INTERMEDIATE = "intermediate"   # Show cuts, edge labels, simplified vertices
    DETAILED = "detailed"          # Show all elements with full detail
    MICRO = "micro"               # Show individual character-level detail


@dataclass
class ViewportBounds:
    """Defines the visible area and zoom level for a view."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    zoom_level: float = 1.0
    
    @property
    def width(self) -> float:
        return self.x_max - self.x_min
    
    @property
    def height(self) -> float:
        return self.y_max - self.y_min
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)


@dataclass
class RenderingHints:
    """Hints for how to render elements at current detail level."""
    min_text_size: float = 8.0      # Minimum readable text size in points
    max_text_size: float = 72.0     # Maximum text size before becoming unwieldy
    cut_line_width: float = 1.0     # Width of cut boundary lines
    vertex_radius: float = 3.0      # Radius of vertex spots
    ligature_width: float = 1.5     # Width of ligature lines
    
    # Detail level thresholds
    overview_threshold: float = 0.1    # Below this zoom, show overview
    intermediate_threshold: float = 0.5 # Below this, show intermediate
    detailed_threshold: float = 2.0    # Above this, show detailed
    
    def get_detail_level(self, zoom: float) -> DetailLevel:
        """Determine appropriate detail level for zoom level."""
        if zoom < self.overview_threshold:
            return DetailLevel.OVERVIEW
        elif zoom < self.intermediate_threshold:
            return DetailLevel.INTERMEDIATE
        elif zoom < self.detailed_threshold:
            return DetailLevel.DETAILED
        else:
            return DetailLevel.MICRO


@dataclass
class ContextState:
    """State of a context (cut) - expanded or collapsed."""
    cut_id: ElementID
    is_expanded: bool = True
    expansion_level: int = 0  # How many levels deep to show when expanded
    
    def toggle(self):
        """Toggle expansion state."""
        self.is_expanded = not self.is_expanded


@dataclass
class NavigationState:
    """Current navigation state and history."""
    current_focus: Optional[ElementID] = None  # Currently focused element
    focus_history: List[ElementID] = field(default_factory=list)
    navigation_mode: NavigationMode = NavigationMode.CUT_TREE
    breadcrumbs: List[ElementID] = field(default_factory=list)  # Path to current focus
    
    def navigate_to(self, element_id: ElementID):
        """Navigate to a new element, updating history."""
        if self.current_focus:
            self.focus_history.append(self.current_focus)
        self.current_focus = element_id
    
    def navigate_back(self) -> Optional[ElementID]:
        """Navigate back in history."""
        if self.focus_history:
            previous = self.focus_history.pop()
            self.current_focus = previous
            return previous
        return None


class ViewGenerator(ABC):
    """Abstract base for different view generation strategies."""
    
    @abstractmethod
    def generate_view(self, egi: RelationalGraphWithCuts, 
                     viewport: ViewportBounds,
                     context_states: Dict[ElementID, ContextState],
                     rendering_hints: RenderingHints) -> 'GraphView':
        """Generate a view of the graph for the given viewport."""
        pass


@dataclass
class RenderedElement:
    """A rendered element with its visual properties."""
    element_id: ElementID
    element_type: str  # 'vertex', 'edge', 'cut'
    x: float
    y: float
    width: float = 0.0
    height: float = 0.0
    text: str = ""
    font_size: float = 12.0
    visible: bool = True
    detail_level: DetailLevel = DetailLevel.DETAILED
    
    # Visual properties
    color: str = "black"
    background_color: str = "white"
    border_color: str = "black"
    border_width: float = 1.0
    
    # For cuts - path coordinates
    path_points: List[Tuple[float, float]] = field(default_factory=list)
    
    # For edges - ligature connection points
    ligature_points: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class GraphView:
    """A rendered view of a graph with all visual elements."""
    viewport: ViewportBounds
    elements: List[RenderedElement]
    detail_level: DetailLevel
    context_states: Dict[ElementID, ContextState]
    navigation_state: NavigationState
    
    # Metadata
    total_elements: int = 0
    visible_elements: int = 0
    rendering_time: float = 0.0
    
    def get_elements_by_type(self, element_type: str) -> List[RenderedElement]:
        """Get all rendered elements of a specific type."""
        return [e for e in self.elements if e.element_type == element_type]
    
    def get_element_at_point(self, x: float, y: float) -> Optional[RenderedElement]:
        """Find the element at a given point (for click handling)."""
        for element in reversed(self.elements):  # Check top elements first
            if not element.visible:
                continue
            
            if (element.x <= x <= element.x + element.width and
                element.y <= y <= element.y + element.height):
                return element
        return None


class PeirceDauViewGenerator(ViewGenerator):
    """Generates views using traditional Peirce-Dau 2D conventions."""
    
    def __init__(self):
        self.subgraph_extractor = SubgraphExtractor()
    
    def generate_view(self, egi: RelationalGraphWithCuts,
                     viewport: ViewportBounds,
                     context_states: Dict[ElementID, ContextState],
                     rendering_hints: RenderingHints) -> GraphView:
        """Generate a Peirce-Dau style 2D view."""
        
        detail_level = rendering_hints.get_detail_level(viewport.zoom_level)
        elements = []
        
        # Determine which elements to render based on viewport and context states
        visible_elements = self._determine_visible_elements(
            egi, viewport, context_states, detail_level
        )
        
        # Render cuts first (background)
        for cut_id in visible_elements.get('cuts', []):
            if cut_id in egi._cut_map:
                cut_element = self._render_cut(
                    egi._cut_map[cut_id], egi, viewport, rendering_hints, detail_level
                )
                if cut_element:
                    elements.append(cut_element)
        
        # Render edges
        for edge_id in visible_elements.get('edges', []):
            if edge_id in egi._edge_map:
                edge_element = self._render_edge(
                    egi._edge_map[edge_id], egi, viewport, rendering_hints, detail_level
                )
                if edge_element:
                    elements.append(edge_element)
        
        # Render vertices (foreground)
        for vertex_id in visible_elements.get('vertices', []):
            if vertex_id in egi._vertex_map:
                vertex_element = self._render_vertex(
                    egi._vertex_map[vertex_id], egi, viewport, rendering_hints, detail_level
                )
                if vertex_element:
                    elements.append(vertex_element)
        
        return GraphView(
            viewport=viewport,
            elements=elements,
            detail_level=detail_level,
            context_states=context_states,
            navigation_state=NavigationState(),
            total_elements=len(egi.V) + len(egi.E) + len(egi.Cut),
            visible_elements=len(elements)
        )
    
    def _determine_visible_elements(self, egi: RelationalGraphWithCuts,
                                  viewport: ViewportBounds,
                                  context_states: Dict[ElementID, ContextState],
                                  detail_level: DetailLevel) -> Dict[str, List[ElementID]]:
        """Determine which elements should be visible in the current view."""
        
        visible = {'vertices': [], 'edges': [], 'cuts': []}
        
        # Start with all elements in viewport bounds
        # (In a real implementation, this would use spatial indexing)
        
        for vertex in egi.V:
            # Check if vertex is in collapsed context
            if self._is_in_collapsed_context(vertex.id, egi, context_states):
                continue
            
            # Check detail level visibility
            if detail_level == DetailLevel.OVERVIEW:
                # Only show vertices in top-level contexts
                if self._get_nesting_depth(vertex.id, egi) <= 1:
                    visible['vertices'].append(vertex.id)
            else:
                visible['vertices'].append(vertex.id)
        
        for edge in egi.E:
            if self._is_in_collapsed_context(edge.id, egi, context_states):
                continue
            
            if detail_level == DetailLevel.OVERVIEW:
                if self._get_nesting_depth(edge.id, egi) <= 1:
                    visible['edges'].append(edge.id)
            else:
                visible['edges'].append(edge.id)
        
        for cut in egi.Cut:
            # Cuts are always visible unless their parent is collapsed
            parent_collapsed = False
            for parent_cut in egi.Cut:
                if (cut.id in egi.area.get(parent_cut.id, set()) and
                    context_states.get(parent_cut.id, ContextState(parent_cut.id)).is_expanded == False):
                    parent_collapsed = True
                    break
            
            if not parent_collapsed:
                visible['cuts'].append(cut.id)
        
        return visible
    
    def _render_cut(self, cut: Cut, egi: RelationalGraphWithCuts,
                   viewport: ViewportBounds, hints: RenderingHints,
                   detail_level: DetailLevel) -> Optional[RenderedElement]:
        """Render a cut as a closed boundary line."""
        
        # Get elements enclosed by this cut
        enclosed_elements = egi.area.get(cut.id, set())
        
        if not enclosed_elements and detail_level == DetailLevel.OVERVIEW:
            return None  # Don't show empty cuts in overview
        
        # Calculate bounding box of enclosed elements
        # (In real implementation, would use actual spatial coordinates)
        min_x, min_y = 100, 100  # Placeholder coordinates
        max_x, max_y = 200, 150
        
        # Create closed path around enclosed elements
        margin = 10
        path_points = [
            (min_x - margin, min_y - margin),
            (max_x + margin, min_y - margin),
            (max_x + margin, max_y + margin),
            (min_x - margin, max_y + margin),
            (min_x - margin, min_y - margin)  # Close the path
        ]
        
        return RenderedElement(
            element_id=cut.id,
            element_type="cut",
            x=min_x - margin,
            y=min_y - margin,
            width=(max_x - min_x) + 2 * margin,
            height=(max_y - min_y) + 2 * margin,
            path_points=path_points,
            border_width=hints.cut_line_width,
            detail_level=detail_level
        )
    
    def _render_vertex(self, vertex: Vertex, egi: RelationalGraphWithCuts,
                      viewport: ViewportBounds, hints: RenderingHints,
                      detail_level: DetailLevel) -> Optional[RenderedElement]:
        """Render a vertex as a spot with optional constant label."""
        
        # Calculate position (placeholder - would use actual spatial data)
        x, y = 150, 125
        
        # Determine if vertex has a constant (rho mapping)
        constant_name = egi.rho.get(vertex.id, "")
        
        # Calculate parity for quantification visualization
        nesting_depth = self._get_nesting_depth(vertex.id, egi)
        is_universal = (nesting_depth % 2) == 1
        
        # Adjust rendering based on detail level
        if detail_level == DetailLevel.OVERVIEW:
            if not constant_name:  # Don't show unlabeled vertices in overview
                return None
        
        font_size = max(hints.min_text_size, 
                       min(hints.max_text_size, 12 * viewport.zoom_level))
        
        return RenderedElement(
            element_id=vertex.id,
            element_type="vertex",
            x=x - hints.vertex_radius,
            y=y - hints.vertex_radius,
            width=hints.vertex_radius * 2,
            height=hints.vertex_radius * 2,
            text=constant_name,
            font_size=font_size,
            color="blue" if is_universal else "black",
            detail_level=detail_level
        )
    
    def _render_edge(self, edge: Edge, egi: RelationalGraphWithCuts,
                    viewport: ViewportBounds, hints: RenderingHints,
                    detail_level: DetailLevel) -> Optional[RenderedElement]:
        """Render an edge as text with ligature connections."""
        
        # Get relation name
        relation_name = egi.rel.get(edge.id, f"R{edge.id}")
        
        # Get connected vertices for ligature positioning
        connected_vertices = egi.nu.get(edge.id, [])
        
        if detail_level == DetailLevel.OVERVIEW and len(connected_vertices) > 2:
            # In overview, only show simple relations
            return None
        
        # Calculate position (placeholder)
        x, y = 175, 100
        
        font_size = max(hints.min_text_size,
                       min(hints.max_text_size, 14 * viewport.zoom_level))
        
        # Calculate ligature connection points
        ligature_points = []
        for vertex_id in connected_vertices:
            # Would calculate actual vertex positions
            ligature_points.append((x + len(ligature_points) * 10, y))
        
        return RenderedElement(
            element_id=edge.id,
            element_type="edge",
            x=x,
            y=y,
            width=len(relation_name) * font_size * 0.6,
            height=font_size,
            text=relation_name,
            font_size=font_size,
            ligature_points=ligature_points,
            detail_level=detail_level
        )
    
    def _is_in_collapsed_context(self, element_id: ElementID,
                               egi: RelationalGraphWithCuts,
                               context_states: Dict[ElementID, ContextState]) -> bool:
        """Check if element is inside a collapsed cut context."""
        
        for cut_id, state in context_states.items():
            if not state.is_expanded:
                if element_id in egi.area.get(cut_id, set()):
                    return True
        return False
    
    def _get_nesting_depth(self, element_id: ElementID,
                          egi: RelationalGraphWithCuts) -> int:
        """Calculate nesting depth of element for parity determination."""
        
        depth = 0
        for cut in egi.Cut:
            if element_id in egi.area.get(cut.id, set()):
                depth += 1
        return depth


class DynamicViewManager:
    """Manages dynamic view generation with navigation and interaction."""
    
    def __init__(self, view_generator: ViewGenerator = None):
        self.view_generator = view_generator or PeirceDauViewGenerator()
        self.rendering_hints = RenderingHints()
        self.context_states: Dict[ElementID, ContextState] = {}
        self.navigation_state = NavigationState()
        
        # Current view state
        self.current_viewport = ViewportBounds(0, 0, 800, 600)
        self.current_view: Optional[GraphView] = None
    
    def generate_view(self, egi: RelationalGraphWithCuts,
                     viewport: Optional[ViewportBounds] = None) -> GraphView:
        """Generate a view of the graph."""
        
        if viewport:
            self.current_viewport = viewport
        
        view = self.view_generator.generate_view(
            egi, self.current_viewport, self.context_states, self.rendering_hints
        )
        
        self.current_view = view
        return view
    
    def pan(self, dx: float, dy: float):
        """Pan the viewport by the given deltas."""
        self.current_viewport.x_min += dx
        self.current_viewport.x_max += dx
        self.current_viewport.y_min += dy
        self.current_viewport.y_max += dy
    
    def zoom(self, factor: float, center_x: float = None, center_y: float = None):
        """Zoom the viewport by the given factor."""
        if center_x is None:
            center_x, center_y = self.current_viewport.center
        
        # Calculate new bounds
        width = self.current_viewport.width / factor
        height = self.current_viewport.height / factor
        
        self.current_viewport.x_min = center_x - width / 2
        self.current_viewport.x_max = center_x + width / 2
        self.current_viewport.y_min = center_y - height / 2
        self.current_viewport.y_max = center_y + height / 2
        self.current_viewport.zoom_level *= factor
    
    def toggle_context(self, cut_id: ElementID):
        """Toggle expansion/collapse of a cut context."""
        if cut_id not in self.context_states:
            self.context_states[cut_id] = ContextState(cut_id)
        
        self.context_states[cut_id].toggle()
    
    def navigate_to_element(self, element_id: ElementID, egi: RelationalGraphWithCuts):
        """Navigate to focus on a specific element."""
        self.navigation_state.navigate_to(element_id)
        
        # Center viewport on element (would use actual spatial coordinates)
        center_x, center_y = 150, 125  # Placeholder
        self.current_viewport.x_min = center_x - self.current_viewport.width / 2
        self.current_viewport.x_max = center_x + self.current_viewport.width / 2
        self.current_viewport.y_min = center_y - self.current_viewport.height / 2
        self.current_viewport.y_max = center_y + self.current_viewport.height / 2
    
    def get_navigation_options(self, egi: RelationalGraphWithCuts,
                             current_element: ElementID) -> Dict[NavigationMode, List[ElementID]]:
        """Get available navigation options from current element."""
        
        options = {mode: [] for mode in NavigationMode}
        
        if current_element in egi._vertex_map:
            # Ligature navigation - follow connected edges
            for edge_id, vertices in egi.nu.items():
                if current_element in vertices:
                    options[NavigationMode.LIGATURE].extend([v for v in vertices if v != current_element])
        
        elif current_element in egi._cut_map:
            # Cut tree navigation - parent/child cuts
            # Parent cuts (containing this cut)
            for cut in egi.Cut:
                if current_element in egi.area.get(cut.id, set()):
                    options[NavigationMode.CUT_TREE].append(cut.id)
            
            # Child cuts (contained by this cut)
            enclosed = egi.area.get(current_element, set())
            for cut in egi.Cut:
                if cut.id in enclosed:
                    options[NavigationMode.CUT_TREE].append(cut.id)
        
        # Semantic navigation would require semantic analysis
        # Spatial navigation would use spatial proximity
        
        return options
    
    def is_text_readable(self, font_size: float) -> bool:
        """Check if text at given size is readable at current zoom."""
        effective_size = font_size * self.current_viewport.zoom_level
        return effective_size >= self.rendering_hints.min_text_size
    
    def should_extend_page(self, egi: RelationalGraphWithCuts) -> bool:
        """Determine if page should extend beyond current viewport due to readability."""
        
        if not self.current_view:
            return False
        
        # Check if any text elements are below readability threshold
        for element in self.current_view.elements:
            if element.text and element.font_size > 0:
                if not self.is_text_readable(element.font_size):
                    return True
        
        return False


# Integration with existing subgraph selection system
class ViewBasedSubgraphSelector:
    """Integrates view generation with subgraph selection."""
    
    def __init__(self, view_manager: DynamicViewManager):
        self.view_manager = view_manager
        self.subgraph_extractor = SubgraphExtractor()
    
    def select_visible_subgraph(self, egi: RelationalGraphWithCuts,
                              selection_criteria: SelectionCriteria) -> 'SubgraphExtractionResult':
        """Select subgraph from currently visible elements."""
        
        if not self.view_manager.current_view:
            raise ValueError("No current view available for selection")
        
        # Filter selection to only visible elements
        visible_elements = {e.element_id for e in self.view_manager.current_view.elements 
                          if e.visible}
        
        # Modify selection criteria to respect visibility
        filtered_criteria = SelectionCriteria(
            selection_type=selection_criteria.selection_type,
            seed_elements=selection_criteria.seed_elements.intersection(visible_elements),
            spatial_bounds=selection_criteria.spatial_bounds,
            semantic_criteria=selection_criteria.semantic_criteria,
            depth_limit=selection_criteria.depth_limit,
            custom_predicate=selection_criteria.custom_predicate
        )
        
        return self.subgraph_extractor.extract_subgraph(
            egi, filtered_criteria, BoundaryHandling.INCLUDE_DEPENDENCIES
        )
    
    def focus_on_subgraph(self, egi: RelationalGraphWithCuts,
                         subgraph_elements: Set[ElementID]):
        """Adjust view to focus on a selected subgraph."""
        
        if not subgraph_elements:
            return
        
        # Calculate bounding box of subgraph elements
        # (Would use actual spatial coordinates)
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        
        # Placeholder calculation
        min_x, min_y, max_x, max_y = 50, 50, 300, 200
        
        # Add margin
        margin = 50
        self.view_manager.current_viewport = ViewportBounds(
            min_x - margin, min_y - margin,
            max_x + margin, max_y + margin
        )
