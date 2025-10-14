"""
QtDiagramCanvas - Interactive canvas using QGraphicsView for Ergasterion.

Uses QtDiagramRenderer to display LayoutDTO as native Qt graphics items.
Provides full interactivity: selection, dragging, hover effects.
"""

from typing import Optional, Set, List, Tuple
from PySide6.QtCore import Qt, Signal, QPointF, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unified_d3_engine import LayoutDTO
from egi_core_dau import RelationalGraphWithCuts
from qt_diagram_renderer import QtDiagramRenderer, InteractiveGraphicsItem
from PySide6.QtWidgets import QGraphicsItem


class QtDiagramCanvas(QWidget):
    """
    Interactive canvas for Ergasterion using QGraphicsView.
    
    Displays LayoutDTO as native Qt graphics items for full interactivity.
    
    Signals:
        element_selected(element_id: str) - Single element selected
        elements_selected(element_ids: List[str]) - Multiple selection
        element_moved(element_id: str, new_pos: Tuple[float, float]) - Element dragged
        selection_cleared() - Selection cleared
    """
    
    # Signals
    element_selected = Signal(str)
    elements_selected = Signal(list)
    element_moved = Signal(str, tuple)
    selection_cleared = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Renderer
        self.renderer = QtDiagramRenderer()
        
        # Graphics view setup
        self.view = QGraphicsView()
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)  # Let items handle their own dragging
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        
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
        
        # Track previous positions for drag detection
        self._element_positions: dict = {}
    
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
        
        # Store positions for drag detection
        self._element_positions.clear()
        for item in scene.items():
            if isinstance(item, InteractiveGraphicsItem):
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
                self._element_positions[item.element_id] = (item.pos().x(), item.pos().y())
        
        # Only fit in view if explicitly requested (e.g., initial load)
        # This preserves user's zoom/pan state during interactive edits
        if fit_to_view:
            self.view.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            print("Fitted diagram to view")
        else:
            print("Preserved current zoom/pan (not fitting to view)")
        
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
        
        if not self._current_scene:
            return
        
        moved_elements = []
        for item in self._current_scene.items():
            if isinstance(item, InteractiveGraphicsItem):
                current_pos = (item.pos().x(), item.pos().y())
                old_pos = self._element_positions.get(item.element_id)
                
                print(f"  {item.element_id}: old={old_pos}, current={current_pos}")
                
                if old_pos and old_pos != current_pos:
                    print(f"  -> MOVED!")
                    moved_elements.append((item.element_id, current_pos))
        
        print(f"=== Found {len(moved_elements)} moved elements ===")
        
        # Emit signals for all moved elements
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
