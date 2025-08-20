"""
Qt Graphics Scene-based renderer for Existential Graphs.

This module replaces all custom hit detection, coordinate tracking, and selection
overlays with Qt's proven QGraphicsScene/QGraphicsView architecture.
"""

from typing import Dict, Any, List, Optional, Set
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QColor, QPainter

from eg_graphics_items import (
    PredicateGraphicsItem, VertexGraphicsItem, 
    CutGraphicsItem, LigatureGraphicsItem, EGSelectionOverlay
)
from connected_element_selection import ConnectedElementSelector, SelectionType, DeletionImpactAnalyzer
from selection_highlight_controller import SelectionHighlightController, SelectionEventHandler


class EGGraphicsSceneRenderer(QGraphicsView):
    """
    QGraphicsView-based renderer for Existential Graphs.
    
    Replaces custom canvas with Qt's scene-graph architecture:
    - Automatic hit detection via QGraphicsItem
    - Built-in selection overlays
    - Native drag-and-drop support
    - Hierarchical containment via item parenting
    - Group operations for connected elements
    """
    
    # Signals for EGI synchronization
    element_moved = Signal(str, float, float)  # element_id, delta_x, delta_y
    element_selected = Signal(str)  # element_id
    
    def __init__(self):
        super().__init__()
        
        # Create Qt Graphics Scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Configure view
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Element tracking for EGI integration
        self.element_to_item: Dict[str, Any] = {}
        self.item_to_element: Dict[Any, str] = {}
        self.egi_graph = None
        
        # Connected element selection system
        self.selection_controller: Optional[SelectionHighlightController] = None
        self.selection_handler: Optional[SelectionEventHandler] = None
        
        # EG-specific selection system (legacy)
        self.selection_overlay = EGSelectionOverlay()
        self.scene.addItem(self.selection_overlay)
        self.selection_overlay.setVisible(False)
        
        # Track current selection for constraint validation
        self.current_selection: Set[str] = set()
        self.containment_hierarchy: Dict[str, List[str]] = {}  # cut_id -> [contained_element_ids]
        self.connected_groups: Dict[str, Set[str]] = {}  # element_id -> connected_element_ids
        
        print("🎨 Created EGGraphicsSceneRenderer with Qt scene-graph architecture")
    
    def validate_selection(self, element_ids: Set[str]) -> bool:
        """
        Validate that the proposed selection conforms to EG constraints.
        
        EG-specific rules:
        1. Selection must form a valid subgraph or be within the same logical area
        2. Cannot select elements across cut boundaries that would violate semantics
        3. Connected elements (predicates + ligatures) should be selected as groups
        """
        if not element_ids:
            return True
            
        # TODO: Implement full EG constraint validation
        # For now, allow all selections (will be enhanced with area constraints)
        return True
    
    def get_connected_group(self, element_id: str) -> Set[str]:
        """
        Get all elements that should be selected/moved together with the given element.
        
        This implements group-aware selection where predicates move with their
        connected ligatures, and vertices move with their identity lines.
        """
        if element_id in self.selection_groups:
            return self.selection_groups[element_id]
        
        # Find connected elements based on EGI relationships
        connected = {element_id}
        
        # TODO: Implement logic to find connected ligatures for predicates/vertices
        # This will use the EGI nu mapping to determine connections
        
        return connected
    
    def update_selection_overlay(self, selected_elements: Set[str]):
        """Update the visual selection overlay based on current selection."""
        if not selected_elements:
            self.selection_overlay.clear_selection()
            return
        
        # Calculate bounding box of all selected elements
        bounds = QRectF()
        for element_id in selected_elements:
            if element_id in self.element_to_item:
                item = self.element_to_item[element_id]
                item_bounds = item.boundingRect()
                item_bounds.translate(item.pos())
                bounds = bounds.united(item_bounds)
        
        # Determine selection type
        selection_type = "single" if len(selected_elements) == 1 else "subgraph"
        self.selection_overlay.selection_type = selection_type
        
        # Update overlay
        self.selection_overlay.update_selection(selected_elements, bounds)
    
    def clear_scene(self):
        """Clear all graphics items and reset mappings."""
        self.scene.clear()
        self.element_to_item.clear()
        self.item_to_element.clear()
        self.containment_hierarchy.clear()
        self.connected_groups.clear()
        print("🧹 Cleared graphics scene and mappings")
    
    def load_from_egdf_primitives(self, spatial_primitives: List[Dict[str, Any]], egi_graph=None):
        """
        Load EGDF spatial primitives into Qt Graphics Scene.
        
        This replaces all custom coordinate conversion and hit detection
        with Qt's native scene-graph architecture.
        """
        print(f"🎨 Loading {len(spatial_primitives)} EGDF primitives into Qt Graphics Scene")
        
        # Clear existing scene
        self.clear_scene()
        
        # Store EGI reference
        self.egi_graph = egi_graph
        
        # Initialize connected element selection system
        if egi_graph:
            self.selection_controller = SelectionHighlightController(egi_graph)
            self.selection_handler = SelectionEventHandler(self.selection_controller)
            
            # Connect selection signals
            self.selection_controller.selection_changed.connect(self._on_selection_changed)
            self.selection_controller.deletion_impact_calculated.connect(self._on_deletion_impact)
        
        # Phase 1: Create all graphics items
        cuts = []  # Process cuts first for containment hierarchy
        other_items = []
        
        for primitive in spatial_primitives:
            if not isinstance(primitive, dict):
                continue
                
            element_type = primitive.get('element_type')
            element_id = primitive.get('element_id')
            
            if not element_id:
                continue
            
            if element_type == 'cut':
                cuts.append(primitive)
            else:
                other_items.append(primitive)
        
        # Create cut items first (containers)
        for primitive in cuts:
            self._create_cut_item(primitive)
        
        # Create other items
        for primitive in other_items:
            element_type = primitive.get('element_type')
            
            if element_type == 'predicate':
                self._create_predicate_item(primitive)
            elif element_type == 'vertex':
                self._create_vertex_item(primitive)
            elif element_type == 'identity_line':
                self._create_ligature_item(primitive)
            elif element_type == 'text':
                self._create_text_annotation_item(primitive)
        
        # Phase 2: Establish containment hierarchy
        self._establish_containment_hierarchy()
        
        # Phase 3: Create connected groups for identity lines
        self._create_connected_groups()
        
        # Fit scene to view
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        print(f"✅ Loaded {len(self.element_to_item)} graphics items with Qt scene-graph")
    
    def _create_predicate_item(self, primitive: Dict[str, Any]):
        """Create a PredicateGraphicsItem from EGDF primitive."""
        element_id = primitive.get('element_id')
        position = primitive.get('position')
        
        if not position:
            return
        
        # Get predicate name from EGDF primitive (already extracted from EGI.rel)
        predicate_name = primitive.get('display_name')
        if not predicate_name:
            predicate_name = element_id  # Fallback
        
        # Create graphics item
        item = PredicateGraphicsItem(element_id, primitive, predicate_name, position)
        
        # Store parent area for containment hierarchy
        item._parent_area = primitive.get('parent_area')
        
        # Set Z-value based on cut nesting depth
        cut_depth = self._get_element_cut_depth(element_id)
        item.setZValue(100 + (cut_depth * 10))
        
        # Add to scene and track mapping
        self.scene.addItem(item)
        self.element_to_item[element_id] = item
        self.item_to_element[item] = element_id
        
        # Register with selection handler
        if self.selection_handler:
            self.selection_handler.register_graphics_item(element_id, item, SelectionType.PREDICATE)
    
    def _create_vertex_item(self, primitive: Dict[str, Any]):
        """Create a VertexGraphicsItem from EGDF primitive."""
        element_id = primitive.get('element_id')
        position = primitive.get('position')
        
        if not position:
            return
        
        # Get vertex constant name from EGDF primitive (like "Socrates")
        vertex_name = primitive.get('display_name')
        print(f"🔍 DEBUG: Vertex {element_id} display_name = '{vertex_name}'")
        
        # Create graphics item with vertex name
        item = VertexGraphicsItem(element_id, primitive, position, vertex_name)
        
        # Store parent area for containment hierarchy
        item._parent_area = primitive.get('parent_area')
        
        # Set Z-value based on cut nesting depth
        cut_depth = self._get_element_cut_depth(element_id)
        item.setZValue(100 + (cut_depth * 10))
        
        # Add to scene and track mapping
        self.scene.addItem(item)
        self.element_to_item[element_id] = item
        self.item_to_element[item] = element_id
        
        # Register with selection handler
        if self.selection_handler:
            self.selection_handler.register_graphics_item(element_id, item, SelectionType.VERTEX)
    
    def _create_cut_item(self, primitive: Dict[str, Any]):
        """Create a CutGraphicsItem from EGDF primitive."""
        element_id = primitive.get('element_id')
        bounds = primitive.get('bounds')
        
        if not bounds:
            return
        
        # Create graphics item
        item = CutGraphicsItem(element_id, primitive, bounds)
        
        # Add to scene and track mapping
        self.scene.addItem(item)
        self.element_to_item[element_id] = item
        self.item_to_element[item] = element_id
        
        # Register with selection handler
        if self.selection_handler:
            self.selection_handler.register_graphics_item(element_id, item, SelectionType.CUT)
    
    def _create_ligature_item(self, primitive: Dict[str, Any]):
        """Create a LigatureGraphicsItem from EGDF primitive."""
        element_id = primitive.get('element_id')
        curve_points = primitive.get('curve_points')
        
        if not curve_points or len(curve_points) < 2:
            return
        
        # Create graphics item with full rectilinear path
        item = LigatureGraphicsItem(element_id, primitive, curve_points)
        
        # Ligatures transcend all cut boundaries - highest z-order
        item.setZValue(1000)
        
        # Add to scene and track mapping
        self.scene.addItem(item)
        self.element_to_item[element_id] = item
        self.item_to_element[item] = element_id
        
        # Register with selection handler
        if self.selection_handler:
            self.selection_handler.register_graphics_item(element_id, item, SelectionType.LIGATURE)
    
    def _create_text_annotation_item(self, primitive: Dict[str, Any]):
        """Create a text annotation item for arity numbers or identity markers."""
        element_id = primitive.get('element_id')
        position = primitive.get('position')
        text = primitive.get('text', '')
        font_size = primitive.get('font_size', 10)
        color = primitive.get('color', '#000000')
        
        if not position or not text:
            return
        
        # Create QGraphicsTextItem for annotation
        from PySide6.QtWidgets import QGraphicsTextItem
        from PySide6.QtGui import QFont, QColor
        
        item = QGraphicsTextItem(text)
        item.setPos(position[0], position[1])
        
        # Set font and color
        font = QFont("Arial", font_size)
        item.setFont(font)
        item.setDefaultTextColor(QColor(color))
        
        # Annotations have same z-order as their parent element
        parent_element_id = primitive.get('parent_element_id')
        if parent_element_id:
            parent_cut_depth = self._get_element_cut_depth(parent_element_id)
            item.setZValue(100 + (parent_cut_depth * 10))
        else:
            item.setZValue(primitive.get('z_index', 103))  # Default annotation level
        
        # Add to scene and track mapping
        self.scene.addItem(item)
        self.element_to_item[element_id] = item
        self.item_to_element[item] = element_id
        
        # Annotations don't need selection registration
    
    def _get_element_cut_depth(self, element_id: str) -> int:
        """Calculate the nesting depth of an element based on cut containment."""
        if not self.egi_graph:
            return 0
        
        depth = 0
        # Find which cuts contain this element
        for cut_id, area_contents in self.egi_graph.area.items():
            if element_id in area_contents:
                # This element is in this cut, so depth increases
                depth += 1
                # Recursively check if this cut is nested in other cuts
                depth += self._get_element_cut_depth(cut_id)
                break
        
        return depth
    
    def _create_cut_item(self, primitive: Dict[str, Any]):
        """Create a CutGraphicsItem from EGDF primitive."""
        element_id = primitive.get('element_id')
        bounds = primitive.get('bounds')
        
        if not bounds:
            return
        
        # Create graphics item
        item = CutGraphicsItem(element_id, primitive, bounds)
        
        # Cut boundaries render behind their contents
        cut_depth = self._get_element_cut_depth(element_id)
        item.setZValue((cut_depth * 10) - 1)  # Just behind contents at this level
        
        # Add to scene and track mapping
        self.scene.addItem(item)
        self.element_to_item[element_id] = item
        self.item_to_element[item] = element_id
        
        # Register with selection handler
        if self.selection_handler:
            self.selection_handler.register_graphics_item(element_id, item, SelectionType.CUT)
    
    def _establish_containment_hierarchy(self):
        """Establish parent-child relationships for cuts and contained elements using layout parent_area information."""
        # Use parent_area from layout result instead of EGI area mapping
        cuts = [item for item in self.element_to_item.values() 
                if isinstance(item, CutGraphicsItem)]
        
        # Build mapping of cut_id -> cut_item for quick lookup
        cut_items = {}
        for cut_item in cuts:
            cut_id = self.item_to_element[cut_item]
            cut_items[cut_id] = cut_item
        
        # Establish parent-child relationships based on parent_area from primitives
        for element_id, item in self.element_to_item.items():
            # Skip cuts themselves - they don't have parents in this context
            if isinstance(item, CutGraphicsItem):
                continue
                
            # CRITICAL: Never make ligatures children of cuts - they transcend boundaries
            if isinstance(item, LigatureGraphicsItem):
                continue  # Ligatures must remain scene children, never cut children
            
            # Find parent area from the primitive data stored during creation
            parent_area = getattr(item, '_parent_area', None)
            if parent_area and parent_area != 'sheet' and parent_area in cut_items:
                parent_cut_item = cut_items[parent_area]
                
                # Set parent-child relationship in Qt graphics scene
                item.setParentItem(parent_cut_item)
                
                # Track containment
                if parent_area not in self.containment_hierarchy:
                    self.containment_hierarchy[parent_area] = []
                self.containment_hierarchy[parent_area].append(element_id)
        
        # Report containment results
        for cut_id, contained_elements in self.containment_hierarchy.items():
            print(f"📦 Cut {cut_id} contains: {contained_elements}")
    
    def _create_connected_groups(self):
        """Create groups for elements connected by identity lines."""
        # Group predicates and vertices connected by ligatures
        ligatures = [item for item in self.element_to_item.values() 
                    if isinstance(item, LigatureGraphicsItem)]
        
        # This will be enhanced to use actual EGI connectivity information
        print(f"🔗 Found {len(ligatures)} ligatures for connected groups")
    
    def _get_predicate_name(self, element_id: str) -> Optional[str]:
        """Get predicate name from EGI graph."""
        if not self.egi_graph:
            return None
        
        # In Dau's EGI formalism, predicate names are stored in the rel mapping
        if hasattr(self.egi_graph, 'rel') and element_id in self.egi_graph.rel:
            return self.egi_graph.rel[element_id]
        
        # Fallback: try edge attributes (for compatibility)
        for edge in self.egi_graph.E:
            if edge.id == element_id:
                # Try different possible attribute names for predicate
                if hasattr(edge, 'predicate'):
                    return edge.predicate
                elif hasattr(edge, 'name'):
                    return edge.name
                elif hasattr(edge, 'label'):
                    return edge.label
        
        # Final fallback: use element_id as predicate name
        return element_id
    
    def _get_vertex_name(self, element_id: str) -> Optional[str]:
        """Get vertex constant name from EGI graph."""
        if not self.egi_graph:
            return None
        
        # Find vertex in EGI and get its label (constant name like "Socrates")
        for vertex in self.egi_graph.V:
            if vertex.id == element_id:
                if hasattr(vertex, 'label') and vertex.label:
                    return vertex.label
                elif hasattr(vertex, 'name') and vertex.name:
                    return vertex.name
        
        # No constant name found
        return None
    
    def get_selected_elements(self) -> List[str]:
        """Get list of currently selected element IDs."""
        selected_items = self.scene.selectedItems()
        return [self.item_to_element.get(item) for item in selected_items 
                if item in self.item_to_element]
    
    def select_element(self, element_id: str):
        """Select an element by its EGI ID."""
        if element_id in self.element_to_item:
            item = self.element_to_item[element_id]
            item.setSelected(True)
            self.element_selected.emit(element_id)
    
    def _on_selection_changed(self, element_id: str, selection_type: str):
        """Handle selection change from connected element selection system."""
        print(f"🎯 Selection changed: {element_id} ({selection_type})")
        
        # Get selection info for debugging
        if self.selection_controller:
            selection_info = self.selection_controller.get_selection_info()
            if selection_info:
                print(f"   Connected vertices: {selection_info['connected_vertices']}")
                print(f"   Connected predicates: {selection_info['connected_predicates']}")
                print(f"   Affected ligatures: {selection_info['affected_ligatures']}")
                print(f"   Crossing cuts: {selection_info['crossing_cuts']}")
    
    def _on_deletion_impact(self, impact: dict):
        """Handle deletion impact analysis from connected element selection system."""
        print(f"💥 Deletion impact analysis:")
        print(f"   Affected ligatures: {impact.get('affected_ligatures', set())}")
        print(f"   Orphaned predicates: {impact.get('orphaned_predicates', set())}")
        print(f"   Orphaned vertices: {impact.get('orphaned_vertices', set())}")
        print(f"   Cut crossing impact: {impact.get('cut_crossing_impact', set())}")
    
    def handle_item_click(self, item):
        """Handle click on a graphics item to trigger selection highlighting."""
        if self.selection_handler and hasattr(item, 'element_id'):
            self.selection_handler.handle_item_selection(item)
    
    def handle_item_right_click(self, item):
        """Handle right-click on a graphics item to show deletion preview."""
        if self.selection_handler and hasattr(item, 'element_id'):
            self.selection_handler.handle_deletion_preview(item)
