"""
Viewport-Based Interactive EGI Renderer

Unified engine that handles both rendering and interaction for large EGI structures
using viewport-based rendering with spatial indexing and level-of-detail optimization.

Based on industry best practices from interactive diagram systems like D3.js, 
Cytoscape.js, and Qt Graphics View Framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import math

from PySide6.QtCore import QObject, QPointF, QRectF, QSizeF, Signal, Qt
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem

from egi_core_dau import ElementID, RelationalGraphWithCuts
from gui.style_manager import DiagramStyle
from chapter21_diagram_engine import ViewResult, UniversalEGIEngine, ViewSpecification, InteractionMode
from gui.interaction_layer import InteractionManager
from spatial_area_manager import SpatialAreaManager
from dynamic_transformation_tracker import DynamicTransformationTracker
from rtree_spatial_index import RTreeCutTracker, SpatialBounds
from spatial_area_manager import SpatialAreaManager
from dynamic_transformation_tracker import DynamicTransformationTracker, TransformationEvent, TransformationType


class RenderingLevel(Enum):
    """Level of detail for rendering based on zoom level."""
    OVERVIEW = "overview"      # Simplified shapes, no labels
    MEDIUM = "medium"          # Standard detail
    DETAILED = "detailed"      # Full detail with all annotations
    MICROSCOPIC = "microscopic" # Debug-level detail


@dataclass
class ViewportState:
    """Current state of the viewport."""
    center: QPointF
    zoom_level: float
    visible_rect: QRectF
    rendering_level: RenderingLevel
    
    def world_to_screen(self, world_point: QPointF) -> QPointF:
        """Convert world coordinates to screen coordinates."""
        offset = world_point - self.center
        return QPointF(
            offset.x() * self.zoom_level,
            offset.y() * self.zoom_level
        )
    
    def screen_to_world(self, screen_point: QPointF) -> QPointF:
        """Convert screen coordinates to world coordinates."""
        return QPointF(
            screen_point.x() / self.zoom_level + self.center.x(),
            screen_point.y() / self.zoom_level + self.center.y()
        )


@dataclass
class RenderableElement:
    """An EGI element prepared for rendering."""
    element_id: ElementID
    element_type: str
    world_bounds: QRectF
    rendering_level: RenderingLevel
    visual_properties: Dict[str, Any]
    interaction_enabled: bool = True
    
    # Cached rendering data
    cached_item: Optional[QGraphicsItem] = None
    cache_valid: bool = False


class SpatialIndex:
    """
    Hierarchical spatial indexing for EGI containment relationships.
    Enhanced R-tree implementation with proper nesting and collision detection.
    """
    
    def __init__(self, bounds: QRectF, max_depth: int = 8):
        self.bounds = bounds
        self.max_depth = max_depth
        self.elements: Dict[ElementID, RenderableElement] = {}
        self.spatial_map: Dict[Tuple[int, int], Set[ElementID]] = {}
        self.grid_size = 64  # Grid cells for spatial partitioning
        
        # Hierarchical containment tracking
        self.area_hierarchy: Dict[ElementID, Set[ElementID]] = {}  # area_id -> child_areas
        self.element_areas: Dict[ElementID, ElementID] = {}  # element_id -> containing_area
        self.area_bounds: Dict[ElementID, QRectF] = {}  # area_id -> bounds
        self.occupied_positions: Dict[ElementID, Set[Tuple[int, int]]] = {}  # area_id -> occupied_grid_cells
        
    def register_element(self, element_id: ElementID, bounds: QRectF):
        """Register an element for spatial indexing and hit testing."""
        renderable = RenderableElement(
            element_id=element_id,
            element_type="unknown",
            world_bounds=bounds,
            rendering_level=RenderingLevel.DETAILED,
            visual_properties={},
            interaction_enabled=True
        )
        
        self.elements[element_id] = renderable
        
        # Add to spatial grid
        cells = self._get_grid_cells(bounds)
        for cell in cells:
            if cell not in self.spatial_map:
                self.spatial_map[cell] = set()
            self.spatial_map[cell].add(element_id)
    
    def insert(self, element: RenderableElement):
        """Insert element into spatial index."""
        self.elements[element.element_id] = element
        
        # Calculate grid cells this element occupies
        cells = self._get_grid_cells(element.world_bounds)
        for cell in cells:
            if cell not in self.spatial_map:
                self.spatial_map[cell] = set()
            self.spatial_map[cell].add(element.element_id)
    
    def query_region(self, region: QRectF) -> List[RenderableElement]:
        """Query elements within a region."""
        cells = self._get_grid_cells(region)
        element_ids = set()
        
        for cell in cells:
            if cell in self.spatial_map:
                element_ids.update(self.spatial_map[cell])
        
        # Filter by actual bounds intersection
        result = []
        for element_id in element_ids:
            element = self.elements[element_id]
            if element.world_bounds.intersects(region):
                result.append(element)
                
        return result
    
    def hit_test(self, point: QPointF) -> List[RenderableElement]:
        """Find elements at a specific point, respecting hierarchical containment."""
        # First, find the deepest area containing this point
        containing_area = self.get_deepest_area_at_point(point)
        
        cell = self._point_to_cell(point)
        if cell not in self.spatial_map:
            return []
            
        result = []
        for element_id in self.spatial_map[cell]:
            element = self.elements[element_id]
            # Only include elements that are in the same area or deeper
            if (element.world_bounds.contains(point) and 
                (containing_area is None or 
                 self.element_areas.get(element_id) == containing_area or
                 self._is_area_descendant(self.element_areas.get(element_id), containing_area))):
                result.append(element)
                
        # Sort by rendering order (smaller elements on top)
        # Sort by z-order (highest first) and return
        result.sort(key=lambda x: getattr(x, 'z_order', 0), reverse=True)
        return result
    
    def _get_grid_cells(self, rect: QRectF) -> List[Tuple[int, int]]:
        """Get grid cells that intersect with rectangle."""
        min_x = int(rect.left() // self.grid_size)
        max_x = int(rect.right() // self.grid_size)
        min_y = int(rect.top() // self.grid_size)
        max_y = int(rect.bottom() // self.grid_size)
        
        cells = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                cells.append((x, y))
        return cells
    
    def register_area(self, area_id: ElementID, bounds: QRectF, parent_area: Optional[ElementID] = None):
        """Register a logical area in the hierarchy."""
        self.area_bounds[area_id] = bounds
        self.occupied_positions[area_id] = set()
        
        if parent_area:
            if parent_area not in self.area_hierarchy:
                self.area_hierarchy[parent_area] = set()
            self.area_hierarchy[parent_area].add(area_id)
    
    def register_element_in_area(self, element_id: ElementID, area_id: ElementID):
        """Register which area contains an element."""
        self.element_areas[element_id] = area_id
        
        # Mark grid cells as occupied in this area
        if element_id in self.elements:
            element = self.elements[element_id]
            cells = self._get_grid_cells(element.world_bounds)
            if area_id not in self.occupied_positions:
                self.occupied_positions[area_id] = set()
            self.occupied_positions[area_id].update(cells)
    
    def get_deepest_area_at_point(self, point: QPointF) -> Optional[ElementID]:
        """Find the deepest (most nested) area containing this point."""
        deepest_area = None
        max_depth = -1
        
        for area_id, bounds in self.area_bounds.items():
            if bounds.contains(point):
                depth = self._get_area_depth(area_id)
                if depth > max_depth:
                    max_depth = depth
                    deepest_area = area_id
        
        return deepest_area
    
    def find_safe_position_in_area(self, area_id: ElementID, element_size: QRectF) -> Optional[QPointF]:
        """Find a collision-free position within the specified area."""
        if area_id not in self.area_bounds:
            return None
        
        area_bounds = self.area_bounds[area_id]
        occupied_cells = self.occupied_positions.get(area_id, set())
        
        # Try to find unoccupied grid cells
        # Search for a position where all needed cells are free
        for y in range(int(area_bounds.top()), int(area_bounds.bottom()), self.grid_size):
            for x in range(int(area_bounds.left()), int(area_bounds.right()), self.grid_size):
                test_pos = QPointF(x, y)
                test_bounds = QRectF(test_pos, element_size.size())
                
                # Check if this position is within area bounds
                if not area_bounds.contains(test_bounds):
                    continue
                
                # Check if any child areas would be overlapped
                if self._overlaps_child_areas(area_id, test_bounds):
                    continue
                
                # Check if grid cells are free
                test_cells = self._get_grid_cells(test_bounds)
                if not any(cell in occupied_cells for cell in test_cells):
                    return test_pos
        
        # If no free position found, return center as fallback
        return area_bounds.center()
    
    def _is_area_descendant(self, area_id: Optional[ElementID], ancestor_id: Optional[ElementID]) -> bool:
        """Check if area_id is a descendant of ancestor_id."""
        if not area_id or not ancestor_id:
            return False
        
        # Walk up the hierarchy
        current = area_id
        visited = set()
        
        while current and current not in visited:
            visited.add(current)
            if current == ancestor_id:
                return True
            
            # Find parent of current area
            parent = None
            for parent_id, children in self.area_hierarchy.items():
                if current in children:
                    parent = parent_id
                    break
            
            current = parent
        
        return False
    
    def _get_area_depth(self, area_id: ElementID) -> int:
        """Calculate nesting depth of an area."""
        depth = 0
        current = area_id
        visited = set()
        
        while current and current not in visited:
            visited.add(current)
            # Find parent
            parent = None
            for parent_id, children in self.area_hierarchy.items():
                if current in children:
                    parent = parent_id
                    depth += 1
                    break
            current = parent
        
        return depth
    
    def _overlaps_child_areas(self, area_id: ElementID, bounds: QRectF) -> bool:
        """Check if bounds would overlap any child areas."""
        child_areas = self.area_hierarchy.get(area_id, set())
        
        for child_id in child_areas:
            child_bounds = self.area_bounds.get(child_id)
            if child_bounds and bounds.intersects(child_bounds):
                return True
        
        return False

    def _point_to_cell(self, point: QPointF) -> Tuple[int, int]:
        """Convert point to grid cell coordinates."""
        x = int(point.x() // self.grid_size)
        y = int(point.y() // self.grid_size)
        return (x, y)


class ViewportRenderer(QObject):
    """
    Unified viewport-based renderer with integrated interaction support.
    
    This is the recommended architecture based on industry best practices:
    - Single engine handles both rendering and interaction
    - Viewport-based rendering for large data structures
    - Spatial indexing for efficient hit-testing
    - Level-of-detail rendering based on zoom
    - On-demand generation of visual elements
    """
    
    # Signals
    viewport_changed = Signal(ViewportState)
    element_selected = Signal(ElementID)
    interaction_state_changed = Signal(str)
    
    def __init__(self, engine: UniversalEGIEngine):
        super().__init__()
        self.engine = engine
        self.diagram_engine = engine  # Add alias for compatibility
        self.interaction_manager = InteractionManager()
        
        # Viewport state
        self.viewport = ViewportState(
            center=QPointF(0, 0),
            zoom_level=1.0,
            visible_rect=QRectF(-500, -500, 1000, 1000),
            rendering_level=RenderingLevel.MEDIUM
        )
        
        # Spatial area manager (will be initialized with QGraphicsScene)
        self.spatial_manager: Optional[SpatialAreaManager] = None
        
        # Dynamic transformation tracker for interactive changes
        self.transformation_tracker: Optional[DynamicTransformationTracker] = None
        
        # Current state
        self.current_egi: Optional[RelationalGraphWithCuts] = None
        self.current_style: Optional[DiagramStyle] = None
        self.current_view_result: Optional[ViewResult] = None
        self.rendered_elements: Dict[ElementID, RenderableElement] = {}
        
        # Performance settings
        self.max_elements_per_frame = 1000
        self.cache_enabled = True
        self.async_rendering = True
        
    def set_egi(self, egi: RelationalGraphWithCuts, style: DiagramStyle):
        """Set the EGI to render with specified style."""
        self.current_egi = egi
        self.current_style = style
        
        # Initialize interaction context
        self.interaction_manager.initialize_context(egi, "organon")  # Default mode
        
        # Clear existing state
        self.rendered_elements.clear()
        
        # Initialize R-tree spatial index with default bounds
        default_bounds = QRectF(-1000, -1000, 2000, 2000)
        self.spatial_index = SpatialIndex(default_bounds)
        self.rtree_tracker = RTreeCutTracker()
        
        # Trigger initial rendering
        self._invalidate_viewport()
    
    def set_viewport(self, center: QPointF, zoom: float, visible_rect: QRectF):
        """Update viewport parameters."""
        self.viewport.center = center
        self.viewport.zoom_level = zoom
        self.viewport.visible_rect = visible_rect
        
        # Update rendering level based on zoom
        if zoom < 0.25:
            self.viewport.rendering_level = RenderingLevel.OVERVIEW
        elif zoom < 1.0:
            self.viewport.rendering_level = RenderingLevel.MEDIUM
        elif zoom < 4.0:
            self.viewport.rendering_level = RenderingLevel.DETAILED
        else:
            print(f"DEBUG: Scene bounding rect: {self.viewport.visible_rect}")
        
        # Emit viewport changed signal
        self.viewport_changed.emit(self.viewport)
    
    def _verify_element_area_assignments(self, view_result: ViewResult):
        """Verify that all elements are positioned within their correct logical areas."""
        print("DEBUG: Verifying element area assignments...")
        
        for element_id, position in view_result.layout_positions.items():
            # Get expected area from EGI structure
            expected_area = None
            for area_id, contents in self.current_egi.area.items():
                if element_id in contents:
                    expected_area = area_id
                    break
            
            if expected_area is None:
                print(f"WARNING: Element {element_id} not found in any area")
                continue
            
            # Get actual area from spatial manager
            actual_area = self.spatial_manager.get_area_at_point(position)
            
            if actual_area != expected_area:
                print(f"ERROR: Element {element_id} positioned in area {actual_area} but should be in {expected_area}")
                print(f"  Position: {position}")
                if expected_area in view_result.cut_bounds:
                    print(f"  Expected area bounds: {view_result.cut_bounds[expected_area]}")
            else:
                print(f"OK: Element {element_id} correctly positioned in area {expected_area}")
        
        print("DEBUG: Area assignment verification complete")
    
    def _handle_spatial_update(self):
        """Handle request for spatial update from transformation tracker."""
        print("DEBUG: Spatial update requested - re-rendering scene")
        # Trigger re-render with updated positions
        if hasattr(self, '_last_scene'):
            self.render_to_scene(self._last_scene)
    
    def _handle_containment_violation(self, element_id: ElementID, expected_area: ElementID):
        """Handle containment violation detected by transformation tracker."""
        print(f"WARNING: Containment violation - element {element_id} not in expected area {expected_area}")
        # Could trigger automatic correction or user notification
    
    def apply_transformation(self, transformation_type: TransformationType, element_id: ElementID, 
                           target_area: Optional[ElementID] = None, new_position: Optional[QPointF] = None,
                           new_bounds: Optional[QRectF] = None) -> bool:
        """Apply an interactive transformation to the diagram."""
        if not self.transformation_tracker:
            print("ERROR: Transformation tracker not initialized")
            return False
        
        event = TransformationEvent(
            transformation_type=transformation_type,
            element_id=element_id,
            target_area=target_area,
            new_position=new_position,
            new_bounds=new_bounds
        )
        
        return self.transformation_tracker.apply_transformation(event)
    
    def insert_vertex_at_position(self, vertex_id: ElementID, position: QPointF) -> bool:
        """Insert a new vertex at the specified position."""
        # Determine target area from position
        if not self.spatial_manager:
            return False
        
        target_area = self.spatial_manager.get_area_at_point(position)
        if not target_area:
            print(f"ERROR: No area found at position {position}")
            return False
        
        return self.apply_transformation(
            TransformationType.INSERT_VERTEX,
            vertex_id,
            target_area=target_area,
            new_position=position
        )
    
    def move_element_to_position(self, element_id: ElementID, new_position: QPointF) -> bool:
        """Move an existing element to a new position."""
        return self.apply_transformation(
            TransformationType.MOVE_ELEMENT,
            element_id,
            new_position=new_position
        )
    
    def resize_cut(self, cut_id: ElementID, new_bounds: QRectF) -> bool:
        """Resize a cut to new bounds."""
        return self.apply_transformation(
            TransformationType.RESIZE_CUT,
            cut_id,
            new_bounds=new_bounds
        )
    
    def render_to_scene(self, scene: QGraphicsScene):
        """
        Render current viewport to Qt scene.
        
        This is the main rendering entry point that:
        1. Determines what needs to be rendered based on viewport
        2. Generates visual elements on-demand
        3. Updates spatial index for interaction
        4. Applies level-of-detail optimizations
        """
        print(f"DEBUG: render_to_scene called")
        print(f"DEBUG: current_egi = {self.current_egi is not None}")
        print(f"DEBUG: current_style = {self.current_style is not None}")
        
        if not self.current_egi or not self.current_style:
            print("DEBUG: Missing EGI or style, returning")
            return
            
        # Store scene reference for re-rendering
        self._last_scene = scene
        
        # Clear scene
        scene.clear()
        print(f"DEBUG: Scene cleared")
        
        # Initialize spatial area manager with the QGraphicsScene
        self.spatial_manager = SpatialAreaManager(scene)
        
        # Create view from engine
        view_spec = ViewSpecification(
            focus_elements=set(),
            context_radius=2,
            detail_level=1,
            interaction_mode=InteractionMode.ORGANON,
            viewport_bounds=self.viewport.visible_rect
        )
        
        view_result = self.engine.create_view(self.current_egi, view_spec)
        self.current_view_result = view_result  # Store for ligature rendering
        print(f"DEBUG: View result - vertices: {len(view_result.visible_vertices)}, edges: {len(view_result.visible_edges)}, cuts: {len(view_result.visible_cuts)}")
        print(f"DEBUG: Layout positions: {len(view_result.layout_positions)}")
        
        # Initialize spatial area manager with EGI structure
        self.spatial_manager.initialize_from_egi(self.current_egi, view_result.cut_bounds)
        print(f"DEBUG: Spatial area manager initialized")
        print(self.spatial_manager.debug_area_info())
        
        # Initialize dynamic transformation tracker
        self.transformation_tracker = DynamicTransformationTracker(self.spatial_manager, scene)
        self.transformation_tracker.initialize(self.current_egi, view_result.layout_positions, view_result.cut_bounds)
        
        # Connect transformation signals
        self.transformation_tracker.spatial_update_required.connect(self._handle_spatial_update)
        self.transformation_tracker.containment_violation.connect(self._handle_containment_violation)
        
        # Verify element area assignments
        self._verify_element_area_assignments(view_result)
        
        # Store layout positions for edge rendering
        self._current_layout_positions = view_result.layout_positions
        
        # Calculate area depths for z-ordering
        self._area_depths = self._calculate_area_depths(self.current_egi)
        
        # Get visible elements
        visible_elements = self._get_visible_elements(view_result)
        print(f"DEBUG: Visible elements: {len(visible_elements)}")
        
        # Separate elements by type for proper rendering order
        cuts = []
        vertices = []
        edges = []
        
        for element_data in visible_elements:
            element_id = element_data['element_id']
            if any(c.id == element_id for c in self.current_egi.Cut):
                cuts.append(element_data)
            elif any(v.id == element_id for v in self.current_egi.V):
                vertices.append(element_data)
            elif any(e.id == element_id for e in self.current_egi.E):
                edges.append(element_data)
        
        items_added = 0
        

        # Phase 1: Render cuts (background) with Peirce shading
        for element_data in cuts:
            renderable = self._create_renderable_element(element_data)
            if renderable:
                visual_item = self._get_visual_item(renderable)
                if visual_item:
                    # Check for Peirce shading convention
                    area_id = renderable.element_id
                    depth = view_result.area_depths.get(area_id, 0)
                    if depth % 2 != 0: # Oddly-enclosed areas are shaded
                        visual_item.setBrush(QBrush(QColor(220, 220, 220))) # Light gray
                    
                    scene.addItem(visual_item)
                    items_added += 1
                    self._register_element(renderable)
        
        # Phase 2: Render vertices (need positions for ligature endpoints)
        for element_data in vertices:
            renderable = self._create_renderable_element(element_data)
            if renderable:
                visual_item = self._get_visual_item(renderable)
                if visual_item:
                    scene.addItem(visual_item)
                    items_added += 1
                    self._register_element(renderable)
        
        # Phase 3: Render edges (predicate text only, no ligatures yet)
        edge_renderables = []
        for element_data in edges:
            renderable = self._create_renderable_element(element_data)
            if renderable:
                # Create edge visual item without ligatures
                visual_item = self._create_edge_visual_item(renderable, element_data, include_ligatures=False)
                if visual_item:
                    scene.addItem(visual_item)
                    items_added += 1
                    self._register_element(renderable)
                    edge_renderables.append((renderable, element_data))
        
        # Phase 4: Render ligatures (now that all endpoints are positioned)
        for renderable, element_data in edge_renderables:
            ligature_items = self._create_ligature_items(element_data)
            for ligature_item in ligature_items:
                scene.addItem(ligature_item)
                items_added += 1
        
        print(f"DEBUG: Total items added to scene: {items_added}")
        print(f"DEBUG: Scene items count: {len(scene.items())}")
        print(f"DEBUG: Scene bounding rect: {scene.itemsBoundingRect()}")
    
    def _register_element(self, renderable: RenderableElement):
        """Register element for interaction and spatial indexing."""
        # Register element with spatial index
        self.spatial_index.register_element(
            renderable.element_id,
            renderable.world_bounds
        )
        
        # Determine which area contains this element
        center_point = renderable.world_bounds.center()
        containing_area = self.spatial_index.get_deepest_area_at_point(center_point)
        
        if containing_area:
            self.spatial_index.register_element_in_area(
                renderable.element_id,
                containing_area
            )
        
        # Store renderable element
        self.rendered_elements[renderable.element_id] = renderable
    
    def _create_edge_visual_item(self, renderable: RenderableElement, element_data: Dict[str, Any], include_ligatures: bool = True):
        """Create visual item for edge (predicate text only)."""
        return self._get_visual_item(renderable)
    
    def _create_ligature_items(self, element_data: Dict[str, Any]) -> List:
        """Create ligature visual items for an edge using waypoint data."""
        from PySide6.QtWidgets import QGraphicsPathItem
        from PySide6.QtGui import QPainterPath, QPen, QColor

        ligature_items = []
        ligature_data = element_data.get('connection_points', [])

        if ligature_data and self.current_view_result:
            # The connection_points from the new engine is a list of tuples:
            # ( (list_of_waypoints, vertex_id), ... )
            for path_data, vertex_id in ligature_data:
                if not path_data or len(path_data) < 2:
                    continue

                # The path_data is now a list of QPointF waypoints
                waypoints = path_data
                
                path = QPainterPath(waypoints[0])
                for i in range(1, len(waypoints)):
                    path.lineTo(waypoints[i])

                ligature_item = QGraphicsPathItem(path)
                
                pen = QPen(QColor("black"))
                pen.setWidth(1)
                ligature_item.setPen(pen)

                # Use the z-order calculation from before
                ligature_z_order = self._calculate_ligature_z_order([(None, vertex_id)])
                ligature_item.setZValue(ligature_z_order)
                
                ligature_items.append(ligature_item)

        return ligature_items
    
    def _calculate_area_depths(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, int]:
        """Calculate nesting depth for each area in the EGI."""
        depths = {egi.sheet: 0}  # Sheet is always depth 0
        
        def calculate_depth(area_id: ElementID, current_depth: int):
            depths[area_id] = current_depth
            
            # Find cuts in this area and calculate their enclosed area depths
            if area_id in egi.area:
                for elem_id in egi.area[area_id]:
                    # If this element is a cut, its enclosed area is one level deeper
                    if any(cut.id == elem_id for cut in egi.Cut):
                        calculate_depth(elem_id, current_depth + 1)
        
        calculate_depth(egi.sheet, 0)
        return depths
    
    def _get_element_area(self, element_id: ElementID, egi: RelationalGraphWithCuts) -> ElementID:
        """Find which area contains the given element."""
        for area_id, contents in egi.area.items():
            if element_id in contents:
                return area_id
        return egi.sheet  # Fallback to sheet
    
    def _calculate_ligature_z_order(self, connection_points: List[Tuple]) -> int:
        """Calculate z-order for ligature based on max depth of connected elements."""
        max_depth = 0
        
        for hook_point, vertex_id in connection_points:
            # Find area containing this vertex
            vertex_area = self._get_element_area(vertex_id, self.current_egi)
            vertex_depth = self._area_depths.get(vertex_area, 0)
            max_depth = max(max_depth, vertex_depth)
        
        # Use proportional spacing: depth * 10 for clear separation
        return max_depth * 10 + 5  # +5 to place ligatures above elements at same depth

    def handle_mouse_event(self, event_type: str, position: QPointF, modifiers: Qt.KeyboardModifiers):
        """Handle mouse events for interaction."""
        world_pos = self.viewport.screen_to_world(position)
        
        # Hit test using R-tree spatial index
        if self.spatial_index:
            hit_elements = self.spatial_index.hit_test(world_pos)
        else:
            hit_elements = []
        
        if hit_elements:
            top_element = hit_elements[0]  # Topmost element
            
            if event_type == "press":
                self.element_selected.emit(top_element.element_id)
                
                # Delegate to interaction manager
                self.interaction_manager.handle_mouse_press(None, world_pos)
            elif event_type == "drag":
                self.interaction_manager.handle_mouse_drag(world_pos, world_pos)
    
    def get_available_transformations(self) -> List[str]:
        """Get transformations available for current selection."""
        return self.interaction_manager.get_available_transformations()
    
    def apply_transformation(self, rule_name: str):
        """Apply transformation rule to current selection."""
        self.interaction_manager.request_transformation(rule_name)
    
    def export_viewport(self, file_path: str, format: str = "svg"):
        """Export current viewport rendering to file."""
        # Implementation for saving current view
        pass
    
    def _create_view_specification(self) -> ViewSpecification:
        """Create view specification for current viewport."""
        from chapter21_diagram_engine import ViewResult
        from gui.style_manager import STYLE_MANAGER
        from spatial_area_manager import SpatialAreaManager
        
        # Convert viewport to view specification
        focus_elements = set()  # Could be current selection
        context_radius = max(
            self.viewport.visible_rect.width(),
            self.viewport.visible_rect.height()
        ) / 2
        
        detail_level = {
            RenderingLevel.OVERVIEW: 0.25,
            RenderingLevel.MEDIUM: 0.5,
            RenderingLevel.DETAILED: 1.0,
            RenderingLevel.MICROSCOPIC: 2.0
        }[self.viewport.rendering_level]
        
        return ViewSpecification(
            focus_elements=focus_elements,
            context_radius=context_radius,
            detail_level=detail_level,
            interaction_mode=InteractionMode.ORGANON,  # Could be dynamic
            show_subgraph_hints=True
        )
    
    def _get_visible_elements(self, view_result: ViewResult) -> List[Dict[str, Any]]:
        """Extract elements visible in current viewport with application-layer layout data."""
        visible = []
        
        # Process positioned elements (vertices and edges)
        for element_id, position in view_result.layout_positions.items():
            element_rect = QRectF(position.x() - 10, position.y() - 10, 20, 20)  # Approximate
            
            if self.viewport.visible_rect.intersects(element_rect):
                element_data = {
                    'element_id': element_id,
                    'position': position,
                    'bounds': element_rect,
                    'layout_position': position
                }
                
                # Add edge connection points if this is an edge
                if element_id in {e.id for e in self.current_egi.E}:
                    # Use hook-based connection points from view_result
                    if hasattr(view_result, 'connection_points') and element_id in view_result.connection_points:
                        element_data['connection_points'] = view_result.connection_points[element_id]
                
                visible.append(element_data)
        
        # Process cuts separately using cut_bounds
        if hasattr(view_result, 'cut_bounds'):
            for cut_id, cut_bounds in view_result.cut_bounds.items():
                if cut_id != self.current_egi.sheet and self.viewport.visible_rect.intersects(cut_bounds):
                    element_data = {
                        'element_id': cut_id,
                        'position': cut_bounds.center(),
                        'bounds': cut_bounds,
                        'layout_position': cut_bounds.center()
                    }
                    visible.append(element_data)
                
        return visible
    
    def _create_renderable_element(self, element_data: Dict[str, Any]) -> Optional[RenderableElement]:
        """Create renderable element from view data."""
        element_id = element_data['element_id']
        
        # Determine element type by checking element IDs
        vertex_ids = {v.id for v in self.current_egi.V}
        edge_ids = {e.id for e in self.current_egi.E}
        cut_ids = {c.id for c in self.current_egi.Cut}
        
        if element_id in vertex_ids:
            element_type = "vertex"
        elif element_id in edge_ids:
            element_type = "edge"
        elif element_id in cut_ids:
            element_type = "cut"
        else:
            return None
            
        # Create renderable with application-layer provided data
        renderable = RenderableElement(
            element_id=element_id,
            element_type=element_type,
            world_bounds=element_data['bounds'],
            rendering_level=self.viewport.rendering_level,
            visual_properties=self._get_visual_properties(element_type),
            interaction_enabled=True
        )
        
        # Add connection points for edges if provided by application layer
        if element_type == "edge" and 'connection_points' in element_data:
            renderable.connection_points = element_data['connection_points']
            
        return renderable
    
    def _get_visual_properties(self, element_type: str) -> Dict[str, Any]:
        """Get visual properties from current style."""
        if not self.current_style:
            return {}
            
        if element_type == "vertex":
            return self.current_style.get_vertex_style().__dict__
        elif element_type == "edge":
            return self.current_style.get_ligature_style().__dict__
        elif element_type == "cut":
            return self.current_style.get_cut_style().__dict__
        
        return {}
    
    def _get_visual_item(self, renderable: RenderableElement) -> Optional[QGraphicsItem]:
        """Get or create visual item for renderable element."""
        # Check cache first
        if self.cache_enabled and renderable.cached_item and renderable.cache_valid:
            return renderable.cached_item
            
        # Create new visual item based on element type and rendering level
        item = self._create_visual_item(renderable)
        
        # Cache if enabled
        if self.cache_enabled and item:
            renderable.cached_item = item
            renderable.cache_valid = True
            
        return item
    
    def _create_visual_item(self, renderable: RenderableElement) -> Optional[QGraphicsItem]:
        """Create Qt graphics item for renderable element."""
        from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsRectItem
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QBrush, QPen, QColor
        
        # Apply proper z-order and style
        z_order = self._calculate_z_order(renderable)
        
        if renderable.element_type == "vertex":
            # Dau-compliant vertex: black spot, size distinguishable from ligature width
            radius = 4.0  # Small black spot
            
            item = QGraphicsEllipseItem(-radius, -radius, radius * 2, radius * 2)
            
            # Black fill, no border for authentic Peirce style
            item.setBrush(QBrush(QColor('#000000')))
            item.setPen(QPen(QColor('#000000'), 0))  # No visible border
            item.setPos(renderable.world_bounds.center())
            item.setZValue(z_order)
            return item
            
        elif renderable.element_type == "edge":
            # Dau-compliant predicate with hook-based ligatures
            from PySide6.QtWidgets import QGraphicsItemGroup, QGraphicsTextItem
            
            group = QGraphicsItemGroup()
            
            # Add predicate text from EGI relation data
            predicate_name = self._get_predicate_for_edge(renderable.element_id)
            if predicate_name:
                text_item = QGraphicsTextItem(predicate_name)
                text_item.setDefaultTextColor(QColor('#000000'))
                text_item.setPos(-text_item.boundingRect().width()/2, -text_item.boundingRect().height()/2)
                group.addToGroup(text_item)
                
                # Note: Ligatures are now rendered separately in Phase 4
            else:
                # Fallback for edges without predicate names - simple line
                line_item = QGraphicsLineItem(-20, 0, 20, 0)
                line_item.setPos(renderable.world_bounds.center())
                line_item.setPen(QPen(QColor('#000000'), 2.0))
                group.addToGroup(line_item)
            
            group.setPos(renderable.world_bounds.center())
            group.setZValue(z_order)
            return group
            
        elif renderable.element_type == "cut":
            # Dau-compliant cut: rounded rectangle with transparent fill
            from PySide6.QtWidgets import QGraphicsPathItem
            from PySide6.QtGui import QPainterPath
            
            bounds = renderable.world_bounds
            
            # Ensure minimum size for visibility
            width = max(bounds.width(), 100.0)
            height = max(bounds.height(), 60.0)
            
            # Create rounded rectangle path
            path = QPainterPath()
            corner_radius = 15.0
            rect = QRectF(bounds.x(), bounds.y(), width, height)
            path.addRoundedRect(rect, corner_radius, corner_radius)
            
            item = QGraphicsPathItem(path)
            
            # Transparent fill with black border
            fill_color = QColor('#FFFFFF')
            fill_color.setAlpha(20)  # Very transparent
            border_color = QColor('#000000')
            border_width = 2.0
            
            item.setBrush(QBrush(fill_color))
            item.setPen(QPen(border_color, border_width))
            item.setZValue(z_order)
            return item
            
        return None
    
    def _get_predicate_for_edge(self, edge_id: ElementID) -> str:
        """Get predicate name for edge from EGI relation data."""
        if self.current_egi and hasattr(self.current_egi, 'rel') and edge_id in self.current_egi.rel:
            return self.current_egi.rel[edge_id]
        return ""
    
    def _calculate_egi_bounds(self, egi: RelationalGraphWithCuts) -> QRectF:
        """Calculate bounding rectangle for entire EGI."""
        # This would analyze the EGI structure to determine spatial bounds
        return QRectF(-1000, -1000, 2000, 2000)  # Placeholder
    
    def _world_to_screen_rect(self, world_rect: QRectF) -> QRectF:
        """Convert world rectangle to screen coordinates."""
        top_left = self.viewport.world_to_screen(world_rect.topLeft())
        bottom_right = self.viewport.world_to_screen(world_rect.bottomRight())
        return QRectF(top_left, bottom_right)
    
    def _expand_hit_region(self, bounds: QRectF) -> QRectF:
        """Expand bounds for easier hit-testing."""
        margin = 5.0 / self.viewport.zoom_level  # Larger hit area at high zoom
        return bounds.adjusted(-margin, -margin, margin, margin)
    
    def _calculate_z_order(self, renderable: RenderableElement) -> int:
        """Calculate depth-based z-order for element."""
        # Find which area contains this element
        element_area = self._get_element_area(renderable.element_id, self.current_egi)
        area_depth = self._area_depths.get(element_area, 0)
        
        # Use proportional spacing: depth * 10 for clear separation between levels
        base_z_order = area_depth * 10
        
        # Elements at same depth level have same z-order
        # (cuts, vertices, edges all render at their area's depth)
        return base_z_order
    
    def _invalidate_viewport(self):
        """Mark viewport as needing re-render."""
        # Clear cached items that are no longer valid
        for renderable in self.rendered_elements.values():
            renderable.cache_valid = False
