"""
Selection Highlight Controller for EGI Qt Graphics

Integrates the connected element selection system with Qt Graphics items to provide
visual feedback showing logical dependencies between predicates, vertices, and ligatures.
"""

from typing import Dict, Set, Optional, List
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtWidgets import QGraphicsItem

from connected_element_selection import ConnectedElementSelector, SelectionType, SelectionHighlight, DeletionImpactAnalyzer
from egi_core_dau import RelationalGraphWithCuts


class SelectionHighlightController(QObject):
    """
    Controls selection highlighting in the Qt Graphics scene.
    
    Manages visual feedback for element selection, showing connected elements
    and providing deletion impact previews.
    """
    
    # Signals for selection events
    selection_changed = Signal(str, str)  # element_id, selection_type
    deletion_impact_calculated = Signal(dict)  # impact analysis results
    
    def __init__(self, egi: RelationalGraphWithCuts):
        super().__init__()
        self.egi = egi
        self.selector = ConnectedElementSelector(egi)
        self.deletion_analyzer = DeletionImpactAnalyzer(egi, self.selector)
        
        # Track current selection state
        self.current_selection: Optional[SelectionHighlight] = None
        self.highlighted_items: Dict[str, QGraphicsItem] = {}
        
        # Define highlight styles
        self.highlight_styles = {
            'primary': {
                'pen': QPen(QColor(255, 0, 0, 200), 3.0),  # Red, thick border
                'brush': QBrush(QColor(255, 0, 0, 50))     # Red, transparent fill
            },
            'connected': {
                'pen': QPen(QColor(0, 150, 255, 180), 2.0),  # Blue, medium border
                'brush': QBrush(QColor(0, 150, 255, 30))     # Blue, transparent fill
            },
            'line_of_identity': {
                'pen': QPen(QColor(255, 165, 0, 160), 2.5),  # Orange, medium-thick border
                'brush': QBrush(QColor(255, 165, 0, 40))     # Orange, transparent fill
            },
            'single_object_ligature': {
                'pen': QPen(QColor(0, 255, 0, 180), 3.0),  # Green, thick border for single-object
                'brush': QBrush(QColor(0, 255, 0, 50))     # Green, transparent fill
            },
            'crossing_cut': {
                'pen': QPen(QColor(255, 255, 0, 200), 3.0),  # Yellow, thick border only
                'brush': QBrush(QColor(0, 0, 0, 0))          # Transparent fill - no area highlighting
            },
            'deletion_impact': {
                'pen': QPen(QColor(255, 100, 100, 200), 2.0),  # Light red, medium border
                'brush': QBrush(QColor(255, 100, 100, 60))      # Light red, transparent fill
            }
        }
    
    def select_element(self, element_id: str, selection_type: SelectionType, graphics_items: Dict[str, QGraphicsItem]):
        """
        Select an element and highlight all connected elements.
        
        Args:
            element_id: ID of the element to select
            selection_type: Type of element being selected
            graphics_items: Dictionary mapping element IDs to QGraphicsItem objects
        """
        # Clear previous selection
        self.clear_selection()
        
        # Get selection highlight
        self.current_selection = self.selector.get_selection_highlight(element_id, selection_type)
        self.highlighted_items = graphics_items
        
        # Debug: Print what we're trying to highlight
        print(f"🎯 Highlighting - Primary: {self.current_selection.primary_element}")
        print(f"   Connected predicates: {self.current_selection.connected_predicates}")
        print(f"   Available graphics items: {list(graphics_items.keys())}")
        
        # Apply highlighting
        self._apply_selection_highlighting()
        
        # Emit selection changed signal
        self.selection_changed.emit(element_id, selection_type.value)
    
    def clear_selection(self):
        """Clear all selection highlighting"""
        if self.current_selection and self.highlighted_items:
            self._clear_highlighting()
        
        self.current_selection = None
        self.highlighted_items = {}
    
    def preview_deletion_impact(self, element_id: str, selection_type: SelectionType, graphics_items: Dict[str, QGraphicsItem]):
        """
        Show deletion impact preview for an element.
        
        Args:
            element_id: ID of the element to analyze for deletion
            selection_type: Type of element being analyzed
            graphics_items: Dictionary mapping element IDs to QGraphicsItem objects
        """
        # Get deletion impact analysis
        if selection_type == SelectionType.VERTEX:
            impact = self.deletion_analyzer.analyze_vertex_deletion(element_id)
        elif selection_type == SelectionType.PREDICATE:
            impact = self.deletion_analyzer.analyze_predicate_deletion(element_id)
        else:
            impact = {}
        
        # Apply deletion impact highlighting
        self._apply_deletion_highlighting(impact, graphics_items)
        
        # Emit impact analysis signal
        self.deletion_impact_calculated.emit(impact)
    
    def _apply_selection_highlighting(self):
        """Apply visual highlighting to selected and connected elements"""
        if not self.current_selection or not self.highlighted_items:
            return
        
        # Highlight primary element
        primary_item = self.highlighted_items.get(self.current_selection.primary_element)
        if primary_item:
            self._apply_highlight_style(primary_item, 'primary')
        
        # Highlight connected vertices
        for vertex_id in self.current_selection.connected_vertices:
            vertex_item = self.highlighted_items.get(vertex_id)
            if vertex_item:
                self._apply_highlight_style(vertex_item, 'connected')
        
        # Highlight connected predicates
        for predicate_id in self.current_selection.connected_predicates:
            predicate_item = self.highlighted_items.get(predicate_id)
            if predicate_item:
                self._apply_highlight_style(predicate_item, 'connected')
        
        # Highlight affected lines of identity (ligatures)
        # First collect vertices that are part of single-object ligatures for special handling
        single_object_vertices = set()
        for ligature_network in self.current_selection.single_object_ligatures:
            single_object_vertices.update(ligature_network)
        
        for vertex_id, predicate_id in self.current_selection.affected_ligatures:
            ligature_key = f"{vertex_id}:{predicate_id}"
            ligature_item = self.highlighted_items.get(ligature_key)
            if ligature_item:
                # Use special highlighting for single-object ligatures
                if vertex_id in single_object_vertices:
                    self._apply_highlight_style(ligature_item, 'single_object_ligature')
                else:
                    self._apply_highlight_style(ligature_item, 'line_of_identity')
        
        # Highlight vertices that are part of single-object ligatures with special style
        for ligature_network in self.current_selection.single_object_ligatures:
            for vertex_id in ligature_network:
                vertex_item = self.highlighted_items.get(vertex_id)
                if vertex_item and vertex_id != self.current_selection.primary_element:
                    # Apply single-object ligature style if not already primary
                    self._apply_highlight_style(vertex_item, 'single_object_ligature')
        
        # Highlight crossing cuts
        for cut_id in self.current_selection.crossing_cuts:
            cut_item = self.highlighted_items.get(cut_id)
            if cut_item:
                self._apply_highlight_style(cut_item, 'crossing_cut')
    
    def _apply_deletion_highlighting(self, impact: Dict, graphics_items: Dict[str, QGraphicsItem]):
        """Apply visual highlighting for deletion impact preview"""
        # Highlight affected ligatures
        for vertex_id, predicate_id in impact.get('affected_ligatures', set()):
            ligature_key = f"{vertex_id}:{predicate_id}"
            ligature_item = graphics_items.get(ligature_key)
            if ligature_item:
                self._apply_highlight_style(ligature_item, 'deletion_impact')
        
        # Highlight orphaned elements
        for orphan_id in impact.get('orphaned_predicates', set()):
            orphan_item = graphics_items.get(orphan_id)
            if orphan_item:
                self._apply_highlight_style(orphan_item, 'deletion_impact')
        
        for orphan_id in impact.get('orphaned_vertices', set()):
            orphan_item = graphics_items.get(orphan_id)
            if orphan_item:
                self._apply_highlight_style(orphan_item, 'deletion_impact')
    
    def _apply_highlight_style(self, item: QGraphicsItem, style_name: str):
        """Apply a highlight style to a graphics item"""
        if not item or style_name not in self.highlight_styles:
            return
        
        style = self.highlight_styles[style_name]
        
        # Store original style for restoration
        if not hasattr(item, '_original_pen'):
            if hasattr(item, 'pen'):
                item._original_pen = item.pen()
            if hasattr(item, 'brush'):
                item._original_brush = item.brush()
        
        # Apply highlight style
        if hasattr(item, 'setPen') and 'pen' in style:
            item.setPen(style['pen'])
        if hasattr(item, 'setBrush') and 'brush' in style:
            item.setBrush(style['brush'])
        
        # Ensure item is visible and on top
        item.setVisible(True)
        item.setZValue(1000)  # Bring to front
    
    def _clear_highlighting(self):
        """Clear all highlighting and restore original styles"""
        for element_id, item in self.highlighted_items.items():
            if not item:
                continue
            
            # Restore original styles
            if hasattr(item, '_original_pen'):
                if hasattr(item, 'setPen'):
                    item.setPen(item._original_pen)
                delattr(item, '_original_pen')
            
            if hasattr(item, '_original_brush'):
                if hasattr(item, 'setBrush'):
                    item.setBrush(item._original_brush)
                delattr(item, '_original_brush')
            
            # Reset z-value
            item.setZValue(0)
    
    def get_selection_info(self) -> Optional[Dict]:
        """Get information about the current selection"""
        if not self.current_selection:
            return None
        
        return {
            'primary_element': self.current_selection.primary_element,
            'connected_vertices': list(self.current_selection.connected_vertices),
            'connected_predicates': list(self.current_selection.connected_predicates),
            'affected_ligatures': list(self.current_selection.affected_ligatures),
            'crossing_cuts': list(self.current_selection.crossing_cuts),
            'logical_area': self.current_selection.logical_area
        }
    
    def update_egi(self, new_egi: RelationalGraphWithCuts):
        """Update the EGI model and rebuild selection caches"""
        self.egi = new_egi
        self.selector = ConnectedElementSelector(new_egi)
        self.deletion_analyzer = DeletionImpactAnalyzer(new_egi, self.selector)
        
        # Clear current selection since EGI has changed
        self.clear_selection()


class SelectionEventHandler:
    """
    Handles selection events from Qt Graphics items and coordinates with the highlight controller.
    """
    
    def __init__(self, highlight_controller: SelectionHighlightController):
        self.highlight_controller = highlight_controller
        self.graphics_items: Dict[str, QGraphicsItem] = {}
    
    def register_graphics_item(self, element_id: str, item: QGraphicsItem, element_type: SelectionType):
        """Register a graphics item for selection handling"""
        self.graphics_items[element_id] = item
        
        # Store element info on the item
        item.element_id = element_id
        item.element_type = element_type
        
        # Enable selection and hover events
        item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        item.setAcceptHoverEvents(True)
    
    def handle_item_selection(self, item: QGraphicsItem):
        """Handle selection of a graphics item"""
        if not hasattr(item, 'element_id') or not hasattr(item, 'element_type'):
            return
        
        element_id = item.element_id
        element_type = item.element_type
        
        # Trigger selection highlighting
        self.highlight_controller.select_element(element_id, element_type, self.graphics_items)
    
    def handle_deletion_preview(self, item: QGraphicsItem):
        """Handle deletion preview for a graphics item"""
        if not hasattr(item, 'element_id') or not hasattr(item, 'element_type'):
            return
        
        element_id = item.element_id
        element_type = item.element_type
        
        # Show deletion impact
        self.highlight_controller.preview_deletion_impact(element_id, element_type, self.graphics_items)
    
    def clear_all_selections(self):
        """Clear all selections in the graphics scene"""
        self.highlight_controller.clear_selection()
        
        # Clear Qt selection state
        for item in self.graphics_items.values():
            if item:
                item.setSelected(False)
