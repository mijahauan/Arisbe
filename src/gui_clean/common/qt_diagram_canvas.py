"""
QtDiagramCanvas - Interactive canvas using QGraphicsView for Ergasterion.

Uses QtDiagramRenderer to display LayoutDTO as native Qt graphics items.
Provides full interactivity: selection, dragging, hover effects.
"""

from typing import Optional, Set, List, Tuple
from PySide6.QtCore import Qt, Signal, QPointF, QTimer
from PySide6.QtGui import QPainter, QWheelEvent, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unified_d3_engine import LayoutDTO
from egi_core_dau import RelationalGraphWithCuts
from qt_diagram_renderer import QtDiagramRenderer, InteractiveGraphicsItem
from PySide6.QtWidgets import QGraphicsItem


class InteractiveGraphicsView(QGraphicsView):
    """
    Enhanced QGraphicsView with mouse wheel zoom and pan controls.
    
    Features:
    - Mouse wheel zoom (Ctrl+wheel for fine control)
    - Pan with middle button drag or Space+drag
    - Reset zoom button
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Zoom state
        self._zoom_factor = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 10.0
        
        # Pan state
        self._pan_enabled = False
        self._is_panning = False
        self._pan_start_pos = None
        self._space_pressed = False
    
    def set_pan_enabled(self, enabled: bool):
        """Enable/disable panning with space+drag."""
        self._pan_enabled = enabled
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        # Get zoom factor (Ctrl for fine control)
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_factor = 1.02  # Fine zoom
        else:
            zoom_factor = 1.15  # Normal zoom
        
        # Zoom in or out based on wheel direction
        if event.angleDelta().y() > 0:
            # Zoom in
            self.scale_view(zoom_factor)
        else:
            # Zoom out
            self.scale_view(1 / zoom_factor)
        
        event.accept()
    
    def scale_view(self, factor: float):
        """Scale the view by the given factor with limits."""
        new_zoom = self._zoom_factor * factor
        
        # Clamp to limits
        if new_zoom < self._min_zoom or new_zoom > self._max_zoom:
            return
        
        self._zoom_factor = new_zoom
        self.scale(factor, factor)
    
    def reset_zoom(self):
        """Reset zoom to 1:1."""
        self.resetTransform()
        self._zoom_factor = 1.0
    
    def keyPressEvent(self, event: QKeyEvent):
        """Track space key for panning."""
        if event.key() == Qt.Key.Key_Space and self._pan_enabled:
            self._space_pressed = True
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event: QKeyEvent):
        """Track space key release."""
        if event.key() == Qt.Key.Key_Space:
            self._space_pressed = False
            if not self._is_panning:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().keyReleaseEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle pan start with middle button or space+left button."""
        if (event.button() == Qt.MouseButton.MiddleButton or
            (event.button() == Qt.MouseButton.LeftButton and self._space_pressed)):
            self._is_panning = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle panning."""
        if self._is_panning and self._pan_start_pos:
            delta = event.pos() - self._pan_start_pos
            self._pan_start_pos = event.pos()
            
            # Pan the view
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle pan end."""
        if event.button() == Qt.MouseButton.MiddleButton or self._is_panning:
            self._is_panning = False
            self._pan_start_pos = None
            if self._space_pressed:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class QtDiagramCanvas(QWidget):
    """
    Interactive canvas for Ergasterion using QGraphicsView.
    
    Displays LayoutDTO as native Qt graphics items for full interactivity.
    
    Signals:
        element_selected(element_id: str) - Single element selected
        elements_selected(element_ids: List[str]) - Multiple selection
        element_moved(element_id: str, new_pos: Tuple[float, float]) - Element dragged
        cut_moved(cut_id: str, delta: Tuple[float, float]) - Cut dragged (with delta for container movement)
        selection_cleared() - Selection cleared
    """
    
    # Signals
    element_selected = Signal(str)
    elements_selected = Signal(list)
    element_moved = Signal(str, tuple)
    cut_moved = Signal(str, tuple)  # cut_id, (dx, dy)
    cut_resized = Signal(str, tuple)  # cut_id, (new_width, new_height)
    selection_cleared = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Renderer
        self.renderer = QtDiagramRenderer()
        
        # Graphics view setup with pan/zoom
        self.view = InteractiveGraphicsView()
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)  # Let items handle their own dragging
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)  # Disable right-click menu
        
        # Enable pan with space+drag
        self.view.set_pan_enabled(True)
        
        # Install event filter on view to catch mouse releases
        self.view.viewport().installEventFilter(self)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        
        # Current state
        self._current_scene: Optional[QGraphicsScene] = None
        self._current_dto: Optional[LayoutDTO] = None
        self._current_egi: Optional[RelationalGraphWithCuts] = None
        
        # State for position tracking and move detection
        self._element_positions: Dict[str, Tuple[float, float]] = {}
        self._cut_sizes: Dict[str, Tuple[float, float]] = {}  # cut_id -> (width, height)
        self._last_display_time = 0.0
        self._fit_to_view_done_at = 0.0  # Timestamp when fit_to_view was last done
        self._updating_display: bool = False
        
        # Track when display was last updated to prevent phantom move detection
        self._last_display_update_time: float = 0.0
        self._last_fit_to_view: bool = False
    
    def display_dto(self, dto: LayoutDTO, egi: Optional[RelationalGraphWithCuts] = None, fit_to_view: bool = False):
        """
        Display a LayoutDTO as interactive Qt graphics.
        
        Args:
            dto: The layout to display
            egi: Optional EGI for labels
            fit_to_view: If True, rescale view to fit entire diagram (default: False to preserve zoom/pan)
        """
        print(f"QtDiagramCanvas.display_dto called with dto={dto is not None}, egi={egi is not None}, fit_to_view={fit_to_view}")
        
        if dto is None:
            print("ERROR: display_dto received None for dto")
            self.clear()
            return
        
        # Set flag to prevent move detection during display update
        self._updating_display = True
        
        # Record display update time to prevent phantom moves
        # If fit_to_view=True (after transformations), use longer guard period
        import time
        self._last_display_update_time = time.time()
        # Only SET the flag to True, never reset it to False
        # (it will automatically clear after threshold expires in move detection)
        if fit_to_view:
            self._last_fit_to_view = True
        
        self._current_dto = dto
        self._current_egi = egi
        
        # Render to scene
        print("Calling renderer.render_to_scene...")
        try:
            scene = self.renderer.render_to_scene(dto, egi)
            print(f"Scene created with {len(scene.items())} items")
        except Exception as e:
            print(f"ERROR rendering scene: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Connect scene signals
        scene.selectionChanged.connect(self._on_selection_changed)
        
        # Set scene
        self._current_scene = scene
        self.view.setScene(scene)
        print(f"Scene set on view. Scene rect: {scene.sceneRect()}")
        
        # Update position tracking from DTO, not from Qt scene items
        # This prevents position corruption during display refresh
        print("  Updating position tracking from DTO")
        self._element_positions.clear()
        
        # Update position tracking from Qt scene items (rendered positions)
        # This ensures tracking matches what's actually displayed
        from qt_diagram_renderer import CutRectItem
        from PySide6.QtCore import QTimer
        
        def update_position_tracking_from_scene():
            """Update position tracking after scene is stable."""
            print("  Updating position tracking from rendered scene")
            self._element_positions.clear()
            
            for item in scene.items():
                if isinstance(item, InteractiveGraphicsItem):
                    # Enable geometry change tracking
                    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
                    
                    if isinstance(item, CutRectItem):
                        # Track cut VISUAL position = pos() + rect()
                        # When dragged, Qt updates pos() while rect() stays constant
                        rect = item.rect()
                        item_pos = item.pos()
                        visual_pos = (rect.x() + item_pos.x(), rect.y() + item_pos.y())
                        self._element_positions[item.element_id] = visual_pos
                        # Also track cut size for resize detection
                        cut_size = (rect.width(), rect.height())
                        self._cut_sizes[item.element_id] = cut_size
                        print(f"    Tracking cut {item.element_id} at {visual_pos}, size {cut_size}")
                    else:
                        # Track element center position
                        if hasattr(item, 'center_position'):
                            pos = (item.center_position.x, item.center_position.y)
                        else:
                            pos = (item.pos().x(), item.pos().y())
                        self._element_positions[item.element_id] = pos
                        print(f"    Tracking element {item.element_id} at {pos}")
        
        # Update immediately for first display, then again after Qt processes events
        update_position_tracking_from_scene()
        if fit_to_view:
            # After transformations, wait a bit longer for scene to stabilize
            QTimer.singleShot(100, update_position_tracking_from_scene)
        
        # Only fit in view if explicitly requested (e.g., initial load)
        # This preserves user's zoom/pan state during interactive edits
        if fit_to_view:
            # CRITICAL: Fit to CONTENT, not huge padded scene rect
            rect = scene.itemsBoundingRect()
            
            # Add small aesthetic margin
            margin = 20.0
            rect = rect.adjusted(-margin, -margin, margin, margin)
            
            # Sanity check: don't fit to empty or tiny rects
            if rect.width() > 10 and rect.height() > 10:
                self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
                # Update zoom factor tracking
                transform = self.view.transform()
                self.view._zoom_factor = transform.m11()
                print(f"Fitted diagram to view (content): {rect}")
            else:
                print(f"WARNING: Content rect too small to fit: {rect}")
        else:
            print("Preserved current zoom/pan (not fitting to view)")
        
        # Clear flag after display is complete
        self._updating_display = False
        
        print("QtDiagramCanvas.display_dto complete")
    
    def _on_selection_changed(self):
        """Handle selection change in scene."""
        if not self._current_scene:
            return
        
        selected = self.renderer.get_selected_elements(self._current_scene)
        
        if len(selected) == 0:
            self.selection_cleared.emit()
        elif len(selected) == 1:
            self.element_selected.emit(list(selected)[0])
        else:
            self.elements_selected.emit(list(selected))
    
    def eventFilter(self, obj, event):
        """Filter events from the viewport to catch mouse releases."""
        if obj == self.view.viewport():
            if event.type() == event.Type.MouseButtonRelease:
                # Check for moved items after a short delay to ensure position is finalized
                QTimer.singleShot(10, self._check_for_moved_elements)
        return super().eventFilter(obj, event)
    
    def _check_for_moved_elements(self):
        """Check if any elements moved and emit signals."""
        print(f"=== Checking for moved elements ===")
        
        # Skip move detection if we're currently updating the display
        if self._updating_display:
            print("  Skipping move detection (display update in progress)")
            return
        
        # Skip move detection if display was updated very recently
        import time
        time_since_update = time.time() - self._last_display_update_time
        threshold = 1.0 if self._last_fit_to_view else 0.5
        print(f"  Time since last display update: {time_since_update*1000:.1f}ms (threshold: {threshold*1000:.0f}ms, fit_to_view={self._last_fit_to_view})")
        
        # Store if we should skip cut detection (BEFORE clearing flag)
        skip_cut_detection_this_check = self._last_fit_to_view
        
        if time_since_update < threshold:
            print(f"  → Skipping move detection (too soon after display refresh)")
            return
        
        # Clear the fit_to_view flag after threshold check but before processing items
        if self._last_fit_to_view:
            self._last_fit_to_view = False
            print(f"  Cleared fit_to_view flag (threshold expired)")
        
        if not self._current_scene:
            return
        
        from qt_diagram_renderer import CutRectItem
        
        moved_elements = []
        moved_cuts = []
        
        for item in self._current_scene.items():
            if isinstance(item, InteractiveGraphicsItem):
                # Check if this is a cut (container movement)
                if isinstance(item, CutRectItem):
                    # SKIP cut movement detection if we recently did a fit_to_view (transformation)
                    if skip_cut_detection_this_check:
                        print(f"  Skipping cut {item.element_id} move detection (post-transformation layout)")
                        continue
                    
                    # Get VISUAL position = pos() + rect()
                    # When user drags, Qt updates pos() while rect() stays constant
                    rect = item.rect()
                    item_pos = item.pos()
                    current_pos = (rect.x() + item_pos.x(), rect.y() + item_pos.y())
                    old_pos = self._element_positions.get(item.element_id)
                    
                    if old_pos and old_pos != current_pos:
                        # Add tolerance check to avoid minor floating point noise
                        tolerance_sq = 0.1 * 0.1  # Allow 0.1 pixel difference
                        dx = current_pos[0] - old_pos[0]
                        dy = current_pos[1] - old_pos[1]
                        if (dx*dx + dy*dy) > tolerance_sq:
                            print(f"  Cut {item.element_id} moved by ({dx}, {dy})")
                            moved_cuts.append((item.element_id, (dx, dy)))
                        else:
                            print(f"  Cut {item.element_id} position difference within tolerance ({dx:.3f}, {dy:.3f}) - ignoring")
                    
                    # Check for resize
                    current_size = (rect.width(), rect.height())
                    old_size = self._cut_sizes.get(item.element_id)
                    
                    if old_size and old_size != current_size:
                        size_tolerance = 0.1
                        dw = abs(current_size[0] - old_size[0])
                        dh = abs(current_size[1] - old_size[1])
                        if dw > size_tolerance or dh > size_tolerance:
                            print(f"  Cut {item.element_id} resized from {old_size} to {current_size}")
                            # Emit resize signal
                            self.cut_resized.emit(item.element_id, current_size)
                            # Update tracked size
                            self._cut_sizes[item.element_id] = current_size
                    
                    continue
                
                # Regular elements (vertices, predicates)
                # Calculate current center position
                if hasattr(item, 'center_position'):
                    # Predicate: calculate center from current top-left pos
                    bounds = item.boundingRect()
                    current_pos = (
                        item.pos().x() + bounds.width()/2,
                        item.pos().y() + bounds.height()/2
                    )
                else:
                    # Vertex: pos() is already the center
                    current_pos = (item.pos().x(), item.pos().y())
                
                old_pos = self._element_positions.get(item.element_id)
                
                print(f"  {item.element_id}: old={old_pos}, current={current_pos}")
                
                if old_pos and old_pos != current_pos:
                    # Add tolerance check to avoid floating point noise
                    tolerance_sq = 0.1 * 0.1
                    dx = current_pos[0] - old_pos[0]
                    dy = current_pos[1] - old_pos[1]
                    if (dx*dx + dy*dy) > tolerance_sq:
                        print(f"  -> MOVED!")
                        moved_elements.append((item.element_id, current_pos))
                    else:
                        print(f"  -> Position difference within tolerance ({dx:.3f}, {dy:.3f}) - ignoring")
        
        print(f"=== Found {len(moved_elements)} moved elements, {len(moved_cuts)} moved cuts ===")
        
        # Emit signals for moved cuts (container movement)
        for cut_id, delta in moved_cuts:
            print(f"Cut {cut_id} dragged by delta {delta}")
            self.cut_moved.emit(cut_id, delta)
        
        # Emit signals for moved elements
        for element_id, new_pos in moved_elements:
            print(f"Element {element_id} dragged to {new_pos}")
            self.element_moved.emit(element_id, new_pos)
    
    def clear(self):
        """Clear the canvas."""
        self._current_dto = None
        self._current_egi = None
        self._current_scene = None
        self._element_positions.clear()
        self.view.setScene(QGraphicsScene())
    
    def get_current_dto(self) -> Optional[LayoutDTO]:
        """Get the currently displayed LayoutDTO."""
        return self._current_dto
    
    def get_current_egi(self) -> Optional[RelationalGraphWithCuts]:
        """Get the currently displayed EGI."""
        return self._current_egi
    
    def get_selected_elements(self) -> List[str]:
        """Get list of currently selected element IDs."""
        if self._current_scene:
            return list(self.renderer.get_selected_elements(self._current_scene))
        return []
    
    def clear_selection(self):
        """Clear current selection."""
        if self._current_scene:
            self.renderer.clear_selection(self._current_scene)
    
    def set_selection(self, element_ids: List[str]):
        """Set selection to specific elements."""
        if self._current_scene:
            self.renderer.select_elements(self._current_scene, set(element_ids))
    
    def zoom_in(self):
        """Zoom in by 20%."""
        self.view.scale_view(1.2)
    
    def zoom_out(self):
        """Zoom out by 20%."""
        self.view.scale_view(1 / 1.2)
    
    def reset_zoom(self):
        """Reset zoom to fit entire diagram (actual content, not padding)."""
        if self._current_scene:
            # First reset transform to identity
            self.view.reset_zoom()
            
            # CRITICAL: Fit to ACTUAL CONTENT, not padded scene rect
            # This ensures diagram fills viewport nicely
            rect = self._current_scene.itemsBoundingRect()
            
            # Add small margin for aesthetics (20px around content)
            margin = 20.0
            rect = rect.adjusted(-margin, -margin, margin, margin)
            
            if rect.width() > 10 and rect.height() > 10:
                self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
                # Update internal zoom factor
                transform = self.view.transform()
                self.view._zoom_factor = transform.m11()  # Get current scale
                print(f"Zoom reset to fit content: {rect}")
            else:
                print(f"ERROR: Cannot reset zoom - invalid rect: {rect}")
    
    def wheelEvent(self, event):
        """Zoom with mouse wheel."""
        # Zoom factor
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        # Get zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        
        # Apply zoom
        self.view.scale(zoom_factor, zoom_factor)
