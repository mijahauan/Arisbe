#!/usr/bin/env python3
"""
Refactored DrawingEditor - Thin wiring layer using modular architecture.

This version delegates all business logic to DiagramCoordinator and InteractionHandler,
serving only as a Qt UI wiring layer. The original functionality is preserved while
establishing clear separation of concerns.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QMainWindow,
    QMessageBox, QFileDialog, QToolBar, QLabel, QDockWidget,
    QTabWidget, QTextEdit, QWidget, QInputDialog, QVBoxLayout, QHBoxLayout, QStatusBar, QMenu
)
from PySide6.QtGui import QActionGroup

# Import new modular components
sys.path.append(str(Path(__file__).parent.parent / "src"))
from diagram_coordinator import DiagramCoordinator, Point2D, ValidationMode
from interaction_handler import InteractionHandler, InteractionMode
from organon_ergasterion_protocol import ErgasterionWorkflowManager, GraphHandoffPackage, GraphHandoffType
from egdf_parser import EGDFDocument


class ModularDrawingView(QGraphicsView):
    """Graphics view that delegates all interactions to InteractionHandler."""
    
    def __init__(self, scene: QGraphicsScene, interaction_handler: InteractionHandler, coordinator: DiagramCoordinator):
        super().__init__(scene)
        self.interaction_handler = interaction_handler
        self.coordinator = coordinator
        self.setDragMode(QGraphicsView.RubberBandDrag)
    
    def mousePressEvent(self, event):
        """Delegate mouse press to interaction handler."""
        scene_pos = self.mapToScene(event.pos())
        item = self.scene().itemAt(scene_pos, self.transform())
        
        # Handle right-click context menus for existing items
        if event.button() == Qt.MouseButton.RightButton:
            if item:
                self._show_context_menu(event.globalPosition().toPoint(), item)
                return
        
        # Handle left-click for element creation (empty canvas or inside cuts)
        if event.button() == Qt.LeftButton:
            print(f"DEBUG: Left click detected at scene_pos={scene_pos}, item={item}")
            # Check if we're in ligature drawing mode
            if hasattr(self.parent(), 'ligature_drawing_mode') and self.parent().ligature_drawing_mode:
                self._handle_ligature_click(item, scene_pos)
                return
            
            if item is None:
                print(f"DEBUG: No item at click position, showing context menu")
                # Show context menu for empty canvas on left-click
                self.parent()._show_canvas_context_menu_wrapper(event.pos())
            else:
                print(f"DEBUG: Item found at click position: {item}, type: {type(item)}")
            return
        
        handled = self.interaction_handler.handle_mouse_press(event, scene_pos, item)
        if not handled:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Delegate mouse move to interaction handler."""
        scene_pos = self.mapToScene(event.pos())
        
        handled = self.interaction_handler.handle_mouse_move(event, scene_pos)
        if not handled:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Delegate mouse release to interaction handler."""
        scene_pos = self.mapToScene(event.pos())
        
        handled = self.interaction_handler.handle_mouse_release(event, scene_pos)
        if not handled:
            super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        """Delegate key press to interaction handler."""
        handled = self.interaction_handler.handle_key_press(event)
        if not handled:
            super().keyPressEvent(event)
    
    def _show_context_menu(self, global_pos, item):
        """Show context menu for graphics items."""
        from shared_diagram_renderer import InteractiveVertex, InteractivePredicate, StyledCutItem
        
        menu = QMenu()
        
        print(f"Context menu for item type: {type(item).__name__}")
        print(f"Is InteractiveVertex: {isinstance(item, InteractiveVertex)}")
        
        if isinstance(item, InteractiveVertex) or hasattr(item, 'vertex_id'):
            menu.addAction("Delete Vertex", lambda: self._delete_vertex(item))
            menu.addAction("Edit Vertex Name", lambda: self._edit_vertex(item))
            menu.addAction("Extend Ligature from Vertex", lambda: self._start_ligature_from_vertex(item))
        # Handle predicate context menu
        if hasattr(item, 'predicate_id'):
            menu.addAction("Delete Predicate", lambda: self._delete_predicate(item))
            menu.addAction("Edit Text", lambda: self._edit_predicate(item))
            menu.addAction("Specify Arity", lambda: self._specify_predicate_arity(item))
            menu.addAction("Draw Ligature to Vertex", lambda: self._start_ligature_from_predicate(item))
        elif isinstance(item, StyledCutItem) or hasattr(item, 'cut_id'):
            menu.addAction("Delete Cut", lambda: self._delete_cut(item))
            menu.addAction("Edit Cut Properties", lambda: self._edit_cut(item))
            menu.addAction("Resize Cut", lambda: self._resize_cut(item))
        else:
            menu.addAction("Properties", lambda: self._show_properties(item))
        
        menu.exec(global_pos)
    
    def _delete_vertex(self, vertex_item):
        """Delete a vertex."""
        reply = QMessageBox.question(self, "Delete Vertex", 
                                   f"Delete vertex {vertex_item.vertex_id}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.scene().removeItem(vertex_item)
            print(f"Deleted vertex {vertex_item.vertex_id}")
    
    def _edit_vertex(self, vertex_item):
        """Edit vertex properties including name."""
        current_name = getattr(vertex_item, '_vertex_name', '')
        new_name, ok = QInputDialog.getText(self, "Edit Vertex", 
                                          "Enter vertex name (leave empty for anonymous):", 
                                          text=current_name)
        if ok:
            # Update the visual display
            vertex_item._vertex_name = new_name
            
            # Update the underlying EGI data through coordinator
            if hasattr(self, 'coordinator') and self.coordinator:
                success = self.coordinator.update_vertex_name(vertex_item.vertex_id, new_name)
                if success:
                    print(f"Changed vertex {vertex_item.vertex_id} name to '{new_name}'")
                    # Mark as modified for save prompt
                    self.setWindowTitle(f"Ergasterion - {self.current_file or 'Untitled'}*")
                else:
                    print(f"Failed to update vertex {vertex_item.vertex_id} name")
            else:
                print("No coordinator available for vertex name update")
    
    def _delete_predicate(self, predicate_item):
        """Delete a predicate."""
        reply = QMessageBox.question(self, "Delete Predicate", 
                                   f"Delete predicate '{predicate_item.toPlainText()}'?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.scene().removeItem(predicate_item)
            print(f"Deleted predicate {predicate_item.predicate_id}")
    
    def _edit_predicate(self, predicate_item):
        """Edit predicate text."""
        current_text = predicate_item.toPlainText()
        new_text, ok = QInputDialog.getText(self, "Edit Predicate", 
                                          "Enter new text:", text=current_text)
        if ok and new_text:
            # Update the visual display
            predicate_item.setPlainText(new_text)
            
            # Update the underlying EGI data through coordinator
            if hasattr(self, 'coordinator') and self.coordinator:
                success = self.coordinator.update_predicate_text(predicate_item.predicate_id, new_text)
                if success:
                    print(f"Changed predicate {predicate_item.predicate_id} to '{new_text}'")
                    # Mark as modified for save prompt
                    self.setWindowTitle(f"Ergasterion - {self.current_file or 'Untitled'}*")
                else:
                    QMessageBox.warning(self, "Update Failed", 
                                      f"Failed to update predicate text in EGI data.\n"
                                      f"The visual change will not persist when saved.")
            else:
                print(f"Updated predicate text to '{new_text}' for {predicate_item.predicate_id}")
    
    def _is_cut_item(self, item):
        """Check if the item is a cut (allows clicking inside cuts for element creation)."""
        if not item:
            return False
        # Check for cut-related class names or attributes
        class_name = item.__class__.__name__
        return 'Cut' in class_name or hasattr(item, 'cut_id')
    
    def _show_canvas_context_menu(self, scene_pos, global_pos):
        """Show context menu for canvas (empty area) to add elements."""
        print(f"DEBUG: _show_canvas_context_menu called at scene_pos={scene_pos}, global_pos={global_pos}")
        
        # Create menu with proper parent
        menu = QMenu("Add Element", self)
        
        # Connect actions directly to methods with scene_pos captured
        add_vertex_action = menu.addAction("Add Vertex here")
        add_vertex_action.triggered.connect(lambda: self._add_vertex_at_position(scene_pos))
        
        add_predicate_action = menu.addAction("Add Predicate here")
        add_predicate_action.triggered.connect(lambda: self._add_predicate_at_position(scene_pos))
        
        add_cut_action = menu.addAction("Add Cut here")
        add_cut_action.triggered.connect(lambda: self._add_cut_at_position(scene_pos))
        
        print(f"DEBUG: About to show context menu at {global_pos}")
        # Use popup instead of exec for better reliability
        menu.popup(global_pos)
        print(f"DEBUG: Context menu popup called")
    
    def _add_vertex_at_position(self, scene_pos):
        """Add a vertex directly at click position."""
        from PySide6.QtWidgets import QGraphicsEllipseItem
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QPen, QBrush, QColor
        
        print(f"Creating vertex at scene coordinates: ({scene_pos.x()}, {scene_pos.y()})")
        print(f"Scene object: {self.scene}")
        print(f"View object: {getattr(self, 'view', 'NO VIEW')}")
        
        # Create vertex with absolute coordinates (not relative to position)
        radius = 8
        vertex = QGraphicsEllipseItem(scene_pos.x() - radius, scene_pos.y() - radius, 2 * radius, 2 * radius)
        vertex.setPen(QPen(QColor("#000000"), 2))
        vertex.setBrush(QBrush(QColor("#ff0000")))  # Red for visibility
        vertex.setFlag(vertex.GraphicsItemFlag.ItemIsMovable, True)
        vertex.setFlag(vertex.GraphicsItemFlag.ItemIsSelectable, True)
        
        # Add to scene
        self.scene.addItem(vertex)
        print(f"Added vertex to scene. Scene has {len(self.scene.items())} items")
        print(f"Scene rect: {self.scene.sceneRect()}")
        
        # Force updates
        self.scene.update()
        if hasattr(self, 'view') and self.view:
            self.view.update()
            self.view.viewport().update()
            print("Forced all updates")
    
    def _add_predicate_at_position(self, scene_pos):
        """Add a predicate directly at click position."""
        from PySide6.QtWidgets import QInputDialog, QGraphicsTextItem
        from PySide6.QtGui import QFont, QColor
        
        text, ok = QInputDialog.getText(self, "Add Predicate", "Enter predicate text:")
        if ok and text:
            print(f"Creating predicate '{text}' at scene coordinates: ({scene_pos.x()}, {scene_pos.y()})")
            
            # Create predicate directly at click coordinates
            predicate = QGraphicsTextItem(text)
            predicate.setPos(scene_pos.x(), scene_pos.y())
            predicate.setFont(QFont("Arial", 12))
            predicate.setDefaultTextColor(QColor("#000000"))
            predicate.setFlag(predicate.GraphicsItemFlag.ItemIsMovable, True)
            predicate.setFlag(predicate.GraphicsItemFlag.ItemIsSelectable, True)
            
            # Ensure scene exists and add predicate
            if hasattr(self, 'scene') and self.scene:
                self.scene.addItem(predicate)
                print(f"Added predicate to scene. Scene has {len(self.scene.items())} items")
            else:
                print("ERROR: No scene available")
            
            # Force view update
            if hasattr(self, 'view') and self.view:
                self.view.update()
                print("Forced view update")
    
    def _add_cut_at_position(self, scene_pos):
        """Add a cut directly at click position."""
        from PySide6.QtWidgets import QGraphicsRectItem
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QPen, QBrush, QColor
        
        print(f"Creating cut at scene coordinates: ({scene_pos.x()}, {scene_pos.y()})")
        
        # Create cut directly at click coordinates
        width, height = 150, 100
        rect = QRectF(0, 0, width, height)
        cut = QGraphicsRectItem(rect)
        cut.setPos(scene_pos.x() - width/2, scene_pos.y() - height/2)  # Center on click
        cut.setPen(QPen(QColor("#000000"), 2))
        cut.setBrush(QBrush(QColor("#f0f0f0", 50)))  # Light gray, semi-transparent
        cut.setFlag(cut.GraphicsItemFlag.ItemIsMovable, True)
        cut.setFlag(cut.GraphicsItemFlag.ItemIsSelectable, True)
        
        # Ensure scene exists and add cut
        if hasattr(self, 'scene') and self.scene:
            self.scene.addItem(cut)
            print(f"Added cut to scene. Scene has {len(self.scene.items())} items")
        else:
            print("ERROR: No scene available")
        
        # Force view update
        if hasattr(self, 'view') and self.view:
            self.view.update()
            print("Forced view update")

    def _detect_containing_area(self, scene_pos):
        """Detect which area/cut contains the given position using correct coordinate mapping."""
        print(f"DEBUG: Area detection for position {scene_pos}")
        
        # Check cuts in the coordinator's drawing schema for accurate positions
        if hasattr(self, 'coordinator') and self.coordinator:
            print(f"DEBUG: Found coordinator with {len(self.coordinator.current_drawing_schema.get('cuts', []))} cuts")
            
            for cut_data in self.coordinator.current_drawing_schema.get("cuts", []):
                cut_id = cut_data.get("id")
                cut_pos = cut_data.get("pos")
                cut_width = cut_data.get("width", 100)
                cut_height = cut_data.get("height", 100)
                
                print(f"DEBUG: Checking cut {cut_id} at pos {cut_pos}, size {cut_width}x{cut_height}")
                
                if cut_pos:
                    # Create bounding rectangle from cut data
                    cut_left = cut_pos.x - cut_width/2
                    cut_right = cut_pos.x + cut_width/2
                    cut_top = cut_pos.y - cut_height/2
                    cut_bottom = cut_pos.y + cut_height/2
                    
                    print(f"DEBUG: Cut {cut_id} bounds: left={cut_left}, right={cut_right}, top={cut_top}, bottom={cut_bottom}")
                    print(f"DEBUG: Click at x={scene_pos.x()}, y={scene_pos.y()}")
                    
                    # Check if scene position is inside cut bounds
                    if (cut_left <= scene_pos.x() <= cut_right and 
                        cut_top <= scene_pos.y() <= cut_bottom):
                        print(f"DEBUG: Position {scene_pos} IS INSIDE cut {cut_id}")
                        return cut_id
                    else:
                        print(f"DEBUG: Position {scene_pos} is outside cut {cut_id}")
        else:
            print(f"DEBUG: No coordinator found")
        
        print(f"DEBUG: Position {scene_pos} not inside any cut, returning 'sheet'")
        return "sheet"

    def _delete_cut(self, cut_item):
        """Delete a cut."""
        cut_id = getattr(cut_item, 'cut_id', 'unknown')
        reply = QMessageBox.question(self, "Delete Cut", 
                                   f"Delete cut {cut_id}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from scene
            self.scene().removeItem(cut_item)
            
            # Remove from coordinator's drawing schema
            if hasattr(self, 'coordinator') and self.coordinator:
                # Remove from current_drawing_schema
                self.coordinator.current_drawing_schema["cuts"] = [
                    cut for cut in self.coordinator.current_drawing_schema["cuts"] 
                    if cut.get("id") != cut_id
                ]
                
                # Update EGI structure
                if self.coordinator.egi and self.coordinator.correspondence_engine:
                    self.coordinator._sync_drawing_to_egi()
            
            # DISABLED: EGIF update causes element repositioning
            # if hasattr(self.parent(), '_update_current_egif_display'):
            #     self.parent()._update_current_egif_display()
            
            print(f"Deleted cut {cut_id}")
    
    def _edit_cut(self, cut_item):
        """Edit cut properties."""
        QMessageBox.information(self, "Edit Cut", 
                              f"Editing properties for cut {getattr(cut_item, 'cut_id', 'unknown')}\n(Not yet implemented)")
    
    def _resize_cut(self, cut_item):
        """Enable cut resizing mode."""
        # Get current dimensions
        current_rect = cut_item.rect()
        current_width = current_rect.width()
        current_height = current_rect.height()
        
        # Ask user for new dimensions
        new_width, ok1 = QInputDialog.getDouble(self, "Resize Cut", 
                                               f"Enter new width (current: {current_width}):", 
                                               current_width, 10, 1000, 1)
        if not ok1:
            return
            
        new_height, ok2 = QInputDialog.getDouble(self, "Resize Cut", 
                                                f"Enter new height (current: {current_height}):", 
                                                current_height, 10, 1000, 1)
        if not ok2:
            return
        
        # Update the cut size
        cut_item.setRect(0, 0, new_width, new_height)
        
        # Update coordinator if available
        if hasattr(self, 'coordinator') and self.coordinator and hasattr(cut_item, 'cut_id'):
            pos = cut_item.pos()
            success = self.coordinator.update_cut_size(cut_item.cut_id, new_width, new_height)
            if success:
                print(f"Resized cut {cut_item.cut_id} to {new_width}x{new_height}")
            else:
                print(f"Failed to update cut {cut_item.cut_id} size in coordinator")

    def _start_ligature_from_predicate(self, predicate_item):
        """Start drawing a ligature from a predicate to a vertex."""
        if not hasattr(predicate_item, 'predicate_id'):
            QMessageBox.warning(self, "Error", "Cannot determine predicate ID")
            return
        
        # Enter ligature drawing mode
        self.ligature_drawing_mode = True
        self.ligature_source = predicate_item
        self.ligature_source_type = "predicate"
        
        # Change cursor to indicate drawing mode
        self.setCursor(Qt.CrossCursor)
        
        # Show instruction
        QMessageBox.information(self, "Draw Ligature", 
                              "Click on a vertex to connect the ligature.\nPress Escape to cancel.")
    
    def _start_ligature_from_vertex(self, vertex_item):
        """Start extending a ligature from a vertex."""
        if not hasattr(vertex_item, 'vertex_id'):
            QMessageBox.warning(self, "Error", "Cannot determine vertex ID")
            return
        
        # Enter ligature drawing mode
        self.ligature_drawing_mode = True
        self.ligature_source = vertex_item
        self.ligature_source_type = "vertex"
        
        # Change cursor to indicate drawing mode
        self.setCursor(Qt.CrossCursor)
        
        # Show instruction
        QMessageBox.information(self, "Extend Ligature", 
                              "Click on a predicate or vertex to extend the ligature.\nPress Escape to cancel.")

    def _handle_ligature_click(self, item, scene_pos):
        """Handle click during ligature drawing mode."""
        from shared_diagram_renderer import InteractiveVertex, InteractivePredicate
        
        if item is None:
            # Clicked on empty space - cancel ligature drawing
            self._cancel_ligature_drawing()
            return
        
        # Check if clicked item is valid target
        target_type = None
        target_id = None
        
        if isinstance(item, InteractiveVertex) or hasattr(item, 'vertex_id'):
            target_type = "vertex"
            target_id = getattr(item, 'vertex_id', None)
        elif isinstance(item, InteractivePredicate) or hasattr(item, 'predicate_id'):
            target_type = "predicate"  
            target_id = getattr(item, 'predicate_id', None)
        
        if target_type and target_id:
            # Valid target found - create ligature
            self._create_ligature_connection(target_type, target_id, item)
        else:
            QMessageBox.warning(self, "Invalid Target", 
                              "Please click on a vertex or predicate to connect the ligature.")
    
    def _create_ligature_connection(self, target_type, target_id, target_item):
        """Create a ligature connection between source and target."""
        if not self.ligature_source or not hasattr(self, 'coordinator'):
            self._cancel_ligature_drawing()
            return
        
        source_id = None
        if self.ligature_source_type == "predicate":
            source_id = getattr(self.ligature_source, 'predicate_id', None)
        elif self.ligature_source_type == "vertex":
            source_id = getattr(self.ligature_source, 'vertex_id', None)
        
        if source_id and self.coordinator:
            # Create ligature through coordinator
            success = self.coordinator.create_ligature(
                self.ligature_source_type, source_id,
                target_type, target_id
            )
            
            if success:
                print(f"Created ligature from {self.ligature_source_type} {source_id} to {target_type} {target_id}")
                QMessageBox.information(self, "Ligature Created", 
                                      f"Connected {self.ligature_source_type} to {target_type}")
            else:
                QMessageBox.warning(self, "Connection Failed", 
                                  "Failed to create ligature connection. Check semantic constraints.")
        
        # Reset ligature drawing mode
        self._cancel_ligature_drawing()
    
    def _cancel_ligature_drawing(self):
        """Cancel ligature drawing mode."""
        self.ligature_drawing_mode = False
        self.ligature_source = None
        self.ligature_source_type = None
        self.setCursor(Qt.ArrowCursor)
        print("Cancelled ligature drawing mode")
    
    def keyPressEvent(self, event):
        """Handle key press events including Escape to cancel ligature drawing."""
        if event.key() == Qt.Key_Escape and self.ligature_drawing_mode:
            self._cancel_ligature_drawing()
            return
        super().keyPressEvent(event)

    def _specify_predicate_arity(self, predicate_item):
        """Specify the arity and vertex ordering for a predicate."""
        if not hasattr(predicate_item, 'predicate_id'):
            QMessageBox.warning(self, "Error", "Cannot determine predicate ID")
            return
        
        predicate_id = predicate_item.predicate_id
        predicate_text = predicate_item.toPlainText()
        
        # Get current nu mapping if available
        current_vertices = []
        if hasattr(self, 'coordinator') and self.coordinator:
            current_vertices = self.coordinator.get_predicate_vertices(predicate_id)
        
        # Show dialog for arity specification
        arity, ok = QInputDialog.getInt(self, "Specify Predicate Arity", 
                                       f"Enter arity for predicate '{predicate_text}':\n"
                                       f"(Currently connected to {len(current_vertices)} vertices)",
                                       value=len(current_vertices), min=0, max=10)
        
        if ok:
            if hasattr(self, 'coordinator') and self.coordinator:
                success = self.coordinator.set_predicate_arity(predicate_id, arity)
                if success:
                    QMessageBox.information(self, "Arity Set", 
                                          f"Set arity of '{predicate_text}' to {arity}")
                    # Mark as modified for save prompt
                    self.setWindowTitle(f"Ergasterion - {self.current_file or 'Untitled'}*")
                else:
                    QMessageBox.warning(self, "Update Failed", 
                                      "Failed to update predicate arity")
            else:
                QMessageBox.warning(self, "No Coordinator", 
                                  "Cannot set arity - no coordinator available")

    def _show_properties(self, item):
        """Show item properties."""
        item_type = type(item).__name__
        QMessageBox.information(self, "Properties", 
                              f"Item type: {item_type}\nPosition: {item.pos()}")


class RefactoredDrawingEditor(QMainWindow):
    """
    Refactored DrawingEditor using modular architecture.
    
    This serves as a thin UI wiring layer that coordinates between:
    - DiagramCoordinator (business logic)
    - InteractionHandler (user input)
    - Qt UI components (presentation)
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize Qt components FIRST
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        
        # Initialize the proper architecture
        from styling.style_manager import StyleManager
        self.style_manager = StyleManager()
        self._setup_coordinator()
        self._setup_interaction_handler()
        
        # Set up the full UI
        self._setup_toolbar()
        self._setup_dock_widgets()
        
        # Status bar
        self.status_label = QLabel("Ready - Right-click to add elements")
        self.statusBar().addWidget(self.status_label)
        
        print(f"Initialized with DiagramCoordinator and InteractionHandler")
    
    def _setup_interaction_handler(self):
        """Set up interaction handler."""
        self.interaction_handler = InteractionHandler(self.coordinator)
        
        # Replace the view with ModularDrawingView that uses the interaction handler
        self.view = ModularDrawingView(self.scene, self.interaction_handler, self.coordinator)
        self.setCentralWidget(self.view)
    
    def _show_canvas_context_menu_wrapper(self, position):
        """Wrapper to handle context menu with proper coordinate conversion."""
        print(f"DEBUG: Context menu requested at view position {position}")
        
        # Convert view position to scene position
        scene_pos = self.view.mapToScene(position)
        global_pos = self.view.mapToGlobal(position)
        
        print(f"DEBUG: Scene position: {scene_pos}, Global position: {global_pos}")
        
        # Use coordinator methods instead of direct Qt creation
        menu = QMenu("Add Element", self)
        
        add_vertex_action = menu.addAction("Add Vertex here")
        add_vertex_action.triggered.connect(lambda: self._create_vertex_via_coordinator(scene_pos))
        
        add_predicate_action = menu.addAction("Add Predicate here")
        add_predicate_action.triggered.connect(lambda: self._create_predicate_via_coordinator(scene_pos))
        
        add_cut_action = menu.addAction("Add Cut here")
        add_cut_action.triggered.connect(lambda: self._create_cut_via_coordinator(scene_pos))
        
        menu.popup(global_pos)
    
    def _create_vertex_via_coordinator(self, scene_pos):
        """Create vertex using DiagramCoordinator."""
        position = Point2D(scene_pos.x(), scene_pos.y())
        vertex_id = self.coordinator.create_vertex(position)
        if vertex_id:
            print(f"Created vertex {vertex_id} via coordinator at ({scene_pos.x()}, {scene_pos.y()})")
            # Trigger rendering update - use existing render method
            # Note: SharedDiagramRenderer doesn't have render_current_state, skip for now
        else:
            print(f"Failed to create vertex at ({scene_pos.x()}, {scene_pos.y()})")
    
    def _create_predicate_via_coordinator(self, scene_pos):
        """Create predicate using DiagramCoordinator."""
        from PySide6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(self, "Add Predicate", "Enter predicate text:")
        if ok and text:
            position = Point2D(scene_pos.x(), scene_pos.y())
            predicate_id = self.coordinator.create_predicate(text, position)
            if predicate_id:
                print(f"Created predicate {predicate_id} via coordinator at ({scene_pos.x()}, {scene_pos.y()})")
                # Trigger rendering update
                self.coordinator.renderer.render_current_state()
            else:
                print(f"Failed to create predicate at ({scene_pos.x()}, {scene_pos.y()})")
    
    def _create_cut_via_coordinator(self, scene_pos):
        """Create cut using DiagramCoordinator."""
        position = Point2D(scene_pos.x(), scene_pos.y())
        cut_id = self.coordinator.create_cut(position, width=150, height=100)
        if cut_id:
            print(f"Created cut {cut_id} via coordinator at ({scene_pos.x()}, {scene_pos.y()})")
            # Trigger rendering update - use existing render method
            # Note: SharedDiagramRenderer doesn't have render_current_state, skip for now
        else:
            print(f"Failed to create cut at ({scene_pos.x()}, {scene_pos.y()})")
    
    def _setup_ui(self):
        """Set up main UI components."""
        # Create graphics view with interaction handler and coordinator
        
        # Set up UI
        
        # Set up UI callbacks
        
        # Initialize UI
        
        # Status bar
        
        # Load default or sample content (unless launched with handoff)
        if not hasattr(self, '_launched_with_handoff'):
            self._load_default_content()
    
    def _setup_coordinator(self):
        """Set up coordinator."""
        # Initialize coordinator with validation mode
        self.coordinator = DiagramCoordinator(self.scene, self.style_manager)
        # Set syntactic constraints ON, semantic constraints OFF by default
        self.coordinator.set_validation_mode(ValidationMode.COMPOSITION)
    
    def _setup_toolbar(self):
        """Set up toolbar with mode controls."""
        self._create_main_toolbar()
        self._create_annotation_toolbar()
    
    def _create_main_toolbar(self):
        """Create main toolbar with mode and file controls."""
        toolbar = self.addToolBar("Main")
        
        # Mode action group
        mode_group = QActionGroup(self)
        
        # Selection mode
        select_action = QAction("Select (Esc)", self)
        select_action.setCheckable(True)
        select_action.setChecked(True)
        select_action.triggered.connect(lambda: self._set_mode(InteractionMode.SELECT))
        mode_group.addAction(select_action)
        toolbar.addAction(select_action)
        
        # Note: Element creation now handled via left-click context menu
        # No toolbar buttons for creating elements
        
        toolbar.addSeparator()
        
        # Validation mode toggle
        validation_group = QActionGroup(self)
        
        composition_action = QAction("Composition Mode", self)
        composition_action.setCheckable(True)
        composition_action.setChecked(True)
        composition_action.triggered.connect(lambda: self._set_validation_mode(ValidationMode.COMPOSITION))
        validation_group.addAction(composition_action)
        toolbar.addAction(composition_action)
        
        practice_action = QAction("Practice Mode", self)
        practice_action.setCheckable(True)
        practice_action.triggered.connect(lambda: self._set_validation_mode(ValidationMode.PRACTICE))
        validation_group.addAction(practice_action)
        toolbar.addAction(practice_action)
        
        toolbar.addSeparator()
        
        # File operations removed - all file management handled by Organon via corpus index
        
        toolbar.addSeparator()
        
        # Add return to Organon action
        self.return_action = QAction("Return to Organon", self)
        self.return_action.triggered.connect(self._return_to_organon)
        self.return_action.setEnabled(False)  # Only enabled during handoff
        toolbar.addAction(self.return_action)
        
        # Store actions for mode updates (only SELECT mode since creation is via context menu)
        self.mode_actions = {
            InteractionMode.SELECT: select_action
        }
    
    def _create_annotation_toolbar(self):
        """Create annotation control toolbar."""
        annotation_toolbar = self.addToolBar("Annotations")
        
        # Double cut annotation toggle
        double_cut_action = QAction("Double Cuts", self)
        double_cut_action.setCheckable(True)
        double_cut_action.setToolTip("Highlight double cuts in red")
        double_cut_action.triggered.connect(lambda checked: self._toggle_annotation('double_cuts', checked))
        annotation_toolbar.addAction(double_cut_action)
        
        # Predicate arity annotation toggle
        arity_action = QAction("Arity", self)
        arity_action.setCheckable(True)
        arity_action.setToolTip("Show predicate arity numbers")
        arity_action.triggered.connect(lambda checked: self._toggle_annotation('predicate_arity', checked))
        annotation_toolbar.addAction(arity_action)
        
        # Vertex variable annotation toggle
        variables_action = QAction("Variables", self)
        variables_action.setCheckable(True)
        variables_action.setToolTip("Show vertex variable names")
        variables_action.triggered.connect(lambda checked: self._toggle_annotation('vertex_variables', checked))
        annotation_toolbar.addAction(variables_action)
    
    def _toggle_annotation(self, annotation_type: str, enabled: bool):
        """Toggle annotation display."""
        if hasattr(self.coordinator, 'renderer') and self.coordinator.renderer:
            self.coordinator.renderer.toggle_annotation(annotation_type, enabled)
            self.status_label.setText(f"{'Enabled' if enabled else 'Disabled'} {annotation_type.replace('_', ' ')} annotations")
    
    def _setup_dock_widgets(self):
        """Set up dock widgets for additional information."""
        # Target EGIF dock (for EGI-only mode)
        target_dock = QDockWidget("Target EGIF", self)
        self.target_egif_text = QTextEdit()
        self.target_egif_text.setReadOnly(True)
        self.target_egif_text.setFont(self._get_monospace_font())
        target_dock.setWidget(self.target_egif_text)
        self.addDockWidget(Qt.RightDockWidgetArea, target_dock)
        
        # Current EGIF dock (for comparison)
        current_dock = QDockWidget("Current EGIF", self)
        self.current_egif_text = QTextEdit()
        self.current_egif_text.setReadOnly(True)
        self.current_egif_text.setFont(self._get_monospace_font())
        current_dock.setWidget(self.current_egif_text)
        self.addDockWidget(Qt.RightDockWidgetArea, current_dock)
        
        # Missing elements dock (for EGI-only mode guidance)
        missing_dock = QDockWidget("Missing Elements", self)
        self.missing_elements_text = QTextEdit()
        self.missing_elements_text.setReadOnly(True)
        missing_dock.setWidget(self.missing_elements_text)
        self.addDockWidget(Qt.RightDockWidgetArea, missing_dock)
        
        # EGI info dock
        egi_dock = QDockWidget("EGI Information", self)
        self.egi_text = QTextEdit()
        self.egi_text.setReadOnly(True)
        egi_dock.setWidget(self.egi_text)
        self.addDockWidget(Qt.RightDockWidgetArea, egi_dock)
        
        # Debug info dock
        debug_dock = QDockWidget("Debug Information", self)
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        debug_dock.setWidget(self.debug_text)
        self.addDockWidget(Qt.RightDockWidgetArea, debug_dock)
        
        # Ligature suggestions dock
        suggestions_dock = QDockWidget("Ligature Suggestions", self)
        self.suggestions_text = QTextEdit()
        self.suggestions_text.setReadOnly(True)
        suggestions_dock.setWidget(self.suggestions_text)
        self.addDockWidget(Qt.RightDockWidgetArea, suggestions_dock)
    
    def _get_monospace_font(self):
        """Get monospace font for EGIF display."""
        from PySide6.QtGui import QFont
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.Monospace)
        return font
    
    def _load_default_content(self):
        """Load default EGDF content."""
        # Try to load the same sample file as before
        sample_file = Path(__file__).parent.parent / "corpus/graphs/sowa_cat_on_mat/EGDF/diagram_20250902_202811.egdf.json"
        
        if sample_file.exists():
            try:
                with open(sample_file, 'r') as f:
                    egdf_data = json.load(f)
                
                success = self.coordinator.load_from_egdf(egdf_data)
                if success:
                    self._update_egi_display()
                    self._update_ligature_suggestions()
                    self._log_debug(f"Loaded default EGDF: {sample_file}")
                else:
                    self._log_debug("Failed to load default EGDF")
            except Exception as e:
                self._log_debug(f"Error loading default EGDF: {e}")
        else:
            self._log_debug("No default EGDF file found")
    
    # --- Mode Management ---
    
    def _set_mode(self, mode: str):
        """Set interaction mode."""
        self.interaction_handler.set_interaction_mode(mode)
    
    def _set_validation_mode(self, mode: str):
        """Set validation mode."""
        self.interaction_handler.set_validation_mode(mode)
    
    def _on_mode_change(self, mode):
        """Handle mode changes from interaction handler."""
        # Update UI to reflect current mode
        for action_mode, action in self.mode_actions.items():
            action.setChecked(action_mode == mode)
    
    def _on_status_update(self, message: str):
        """Handle status updates."""
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(message)
        print(f"Status: {message}")  # Fallback for testing
    
    def _return_to_organon(self):
        """Return completed work to Organon."""
        if not self.workflow_manager or not self.workflow_manager.current_package:
            QMessageBox.warning(self, "No Active Session", 
                              "No active handoff session to return.")
            return
        
        try:
            # Create return package
            return_package = self.workflow_manager.create_return_package()
            
            # Signal return to Arisbe main window
            if hasattr(self, 'parent') and hasattr(self.parent, 'receive_ergasterion_return'):
                self.parent.receive_ergasterion_return(return_package)
            
            # Close this Ergasterion instance
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Return Error", f"Failed to return to Organon: {e}")
    
    def _save_egdf(self):
        """Save current diagram as EGDF with unique identifier and generate EGI."""
        if hasattr(self, 'current_graph_dir') and self.current_graph_dir:
            # Save to corpus structure with unique identifier
            self._save_to_corpus()
        else:
            # Fallback to file dialog for standalone use
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save EGDF File", "", "EGDF Files (*.egdf.json);;JSON Files (*.json)"
            )
            
            if file_path:
                try:
                    egdf_data = self.coordinator.save_to_egdf()
                    if egdf_data:
                        with open(file_path, 'w') as f:
                            json.dump(egdf_data, f, indent=2)
                        self.status_label.setText(f"EGDF saved to {file_path}")
                    else:
                        QMessageBox.warning(self, "Save Warning", "No diagram data to save.")
                except Exception as e:
                    QMessageBox.critical(self, "Save Error", f"Failed to save EGDF: {e}")
    
    def _save_to_corpus(self):
        """Save EGDF to corpus structure and generate EGI."""
        egdf_data = self.coordinator.save_to_egdf()
        if not egdf_data:
            QMessageBox.warning(self, "Save Warning", "No diagram data to save.")
            return
        
        # Generate unique identifier for this EGDF
        try:
            unique_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            egdf_filename = f"{timestamp}_{unique_id}.egdf.json"
            
            # Save EGDF to corpus structure
            egdf_dir = self.current_graph_dir / "EGDF"
            egdf_dir.mkdir(exist_ok=True)
            egdf_path = egdf_dir / egdf_filename
            
            with open(egdf_path, 'w') as f:
                json.dump(egdf_data, f, indent=2)
            
            # Generate EGI from EGDF
            egi_data = self._generate_egi_from_egdf(egdf_data)
            if egi_data:
                # Save EGI to corpus structure
                graph_name = self.current_graph_dir.name
                egi_path = self.current_graph_dir / f"{graph_name}.egi.json"
                
                with open(egi_path, 'w') as f:
                    json.dump(egi_data, f, indent=2)
                
                # Update metadata with linear forms
                self._update_metadata_with_linear_forms(egi_data)
                
                self.status_label.setText(f"Saved EGDF and generated EGI for {graph_name}")
                
                # Show confirmation dialog
                reply = QMessageBox.question(
                    self, 
                    "Graph Saved", 
                    f"Diagram saved successfully!\n\n"
                    f"EGDF: {egdf_filename}\n"
                    f"EGI: {graph_name}.egi.json\n\n"
                    f"Return to Organon to view the completed graph?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self._return_to_organon()
            else:
                QMessageBox.warning(self, "EGI Generation", "Could not generate EGI from diagram.")
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save to corpus: {e}")
    
    def _generate_egi_from_egdf(self, egdf_data):
        """Generate EGI structure from EGDF diagram data."""
        try:
            # This is a simplified EGI generation - in practice this would be more sophisticated
            # For now, create a basic EGI structure that can be enhanced later
            
            vertices = []
            edges = []
            cuts = []
            nu_mapping = {}
            area_mapping = {"sheet": []}
            rel_mapping = {}
            
            # Extract elements from EGDF
            elements = egdf_data.get("elements", {})
            
            vertex_count = 0
            edge_count = 0
            cut_count = 0
            
            for elem_id, elem_data in elements.items():
                elem_type = elem_data.get("type")
                
                if elem_type == "vertex":
                    vertex_id = f"v_{vertex_count}"
                    vertices.append({
                        "id": vertex_id,
                        "is_generic": elem_data.get("label") is None,
                        "label": elem_data.get("label")
                    })
                    area_mapping["sheet"].append(vertex_id)
                    vertex_count += 1
                    
                elif elem_type == "predicate":
                    edge_id = f"e_{edge_count}"
                    edges.append({"id": edge_id})
                    rel_mapping[edge_id] = elem_data.get("text", "P")
                    area_mapping["sheet"].append(edge_id)
                    # For now, connect to first vertex (this would be more sophisticated)
                    if vertices:
                        nu_mapping[edge_id] = [vertices[0]["id"]]
                    edge_count += 1
                    
                elif elem_type == "cut":
                    cut_id = f"c_{cut_count}"
                    cuts.append({"id": cut_id})
                    area_mapping[cut_id] = []  # Would contain elements inside the cut
                    cut_count += 1
            
            # Build EGI structure
            egi_data = {
                "V": vertices,
                "E": edges,
                "Cut": cuts,
                "nu": nu_mapping,
                "area": area_mapping,
                "rel": rel_mapping,
                "sheet": "sheet",
                "alphabet": {
                    "C": [],
                    "F": [],
                    "R": list(set(rel_mapping.values())),
                    "ar": {rel: 1 for rel in set(rel_mapping.values())}
                },
                "rho": {}
            }
            
            return egi_data
            
        except Exception as e:
            print(f"Error generating EGI from EGDF: {e}")
            return None
    
    def _update_metadata_with_linear_forms(self, egi_data):
        """Update graph metadata with generated linear forms."""
        try:
            graph_name = self.current_graph_dir.name
            metadata_path = self.current_graph_dir / f"{graph_name}.json"
            
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Generate basic linear forms (simplified for now)
                predicates = [rel for rel in egi_data.get("rel", {}).values()]
                vertices = [v.get("label", "x") for v in egi_data.get("V", [])]
                
                if predicates and vertices:
                    # Simple EGIF form
                    egif_form = f"{predicates[0]}({vertices[0]})" if len(predicates) == 1 else " ".join(f"{p}(x)" for p in predicates)
                    
                    metadata["linear_forms"] = {
                        "egif": {
                            "content": egif_form,
                            "source": "generated_from_egdf"
                        }
                    }
                    
                    metadata["updated"] = datetime.now().isoformat()
                    metadata["status"] = "completed"
                    
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                        
        except Exception as e:
            print(f"Error updating metadata: {e}")
    
    def set_current_graph_dir(self, graph_dir):
        """Set the current graph directory for corpus-aware saving."""
        self.current_graph_dir = Path(graph_dir) if graph_dir else None
    
    def load_handoff_data(self, egi_data, egdf_data):
        """Load EGI and EGDF data from Organon handoff."""
        try:
            print(f"[Ergasterion] Handoff data received - EGI: {bool(egi_data)}, EGDF: {bool(egdf_data)}")
            
            # Load EGDF data if available (preferred for visual representation)
            if egdf_data:
                print("[Ergasterion] Loading EGDF data")
                success = self.coordinator.load_from_egdf(egdf_data)
                if success:
                    print("[Ergasterion] EGDF data loaded successfully - canvas left empty for user drawing")
                    return
                else:
                    print("[Ergasterion] Failed to load EGDF data, trying EGI fallback")
            
            # Fallback to EGI data if EGDF not available or failed
            if egi_data:
                print(f"[Ergasterion] Loading EGI data with {len(egi_data.get('V', []))} vertices")
                success = self._load_egi_from_dict(egi_data)
                if success:
                    print("[Ergasterion] EGI data loaded successfully - canvas left empty for user drawing")
                else:
                    print("[Ergasterion] Failed to load EGI data")
            
            if not egi_data and not egdf_data:
                print("[Ergasterion] No handoff data provided")
            
        except Exception as e:
            print(f"[Ergasterion] Error loading handoff data: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_egi_from_dict(self, egi_dict):
        """Convert EGI dictionary to RelationalGraphWithCuts and load into coordinator."""
        try:
            from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, AlphabetDAU
            from frozendict import frozendict
            
            # Convert vertices
            vertices = frozenset(
                Vertex(
                    id=v["id"], 
                    label=v.get("label"), 
                    is_generic=v.get("is_generic", True)
                ) 
                for v in egi_dict.get("V", [])
            )
            
            # Convert edges
            edges = frozenset(Edge(id=e["id"]) for e in egi_dict.get("E", []))
            
            # Convert cuts
            cuts = frozenset(Cut(id=c["id"]) for c in egi_dict.get("Cut", []))
            
            # Convert mappings
            nu_mapping = frozendict({
                eid: tuple(seq) for eid, seq in egi_dict.get("nu", {}).items()
            })
            
            rel_mapping = frozendict(egi_dict.get("rel", {}))
            
            area_mapping = frozendict({
                area_id: frozenset(contents) 
                for area_id, contents in egi_dict.get("area", {}).items()
            })
            
            # Convert alphabet if present
            alphabet = None
            alphabet_data = egi_dict.get("alphabet")
            if alphabet_data:
                alphabet = AlphabetDAU(
                    C=frozenset(alphabet_data.get("C", [])),
                    F=frozenset(alphabet_data.get("F", [])),
                    R=frozenset(alphabet_data.get("R", [])),
                    ar=frozendict(alphabet_data.get("ar", {}))
                )
            
            rho_mapping = frozendict(egi_dict.get("rho", {}))
            
            # Create RelationalGraphWithCuts
            egi = RelationalGraphWithCuts(
                V=vertices,
                E=edges,
                nu=nu_mapping,
                sheet=egi_dict.get("sheet", "sheet"),
                Cut=cuts,
                area=area_mapping,
                rel=rel_mapping,
                alphabet=alphabet,
                rho=rho_mapping
            )
            
            # Set the EGI as target for EGI-only mode (but don't render it)
            self.coordinator.target_egi = egi
            self.coordinator.is_egi_only_mode = True
            
            # Clear the scene to ensure it's empty for user drawing
            self.coordinator.scene.clear()
            
            # Generate target EGIF display
            self._update_target_egif_display(egi)
            
            # DO NOT call initialize_empty_scene or any render methods
            # Leave canvas completely empty for user drawing
            
            print(f"[Ergasterion] Set target EGI with {len(vertices)} vertices, {len(edges)} edges, {len(cuts)} cuts")
            print("[Ergasterion] Initialized empty diagram for EGI-only mode")
            return True
            
        except Exception as e:
            print(f"[Ergasterion] Error converting EGI dict: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _update_target_egif_display(self, target_egi):
        """Generate and display target EGIF from the loaded EGI."""
        try:
            from egif_generator_dau import EGIFGenerator
            
            # Generate EGIF from target EGI
            generator = EGIFGenerator()
            target_egif = generator.generate_egif(target_egi)
            
            # Update the target EGIF display in the UI
            if hasattr(self, 'target_egif_text'):
                self.target_egif_text.setText(target_egif)
            else:
                print(f"[Ergasterion] Target EGIF: {target_egif}")
            
            # DISABLED: EGIF update causes element repositioning
            # self._update_current_egif_display()
            
        except Exception as e:
            print(f"[Ergasterion] Error generating target EGIF: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_current_egif_display(self):
        """Update current EGIF display based on current diagram state."""
        try:
            # Convert current diagram state to EGI and generate EGIF
            current_egi = self._convert_current_diagram_to_egi()
            if current_egi:
                from egif_generator_dau import EGIFGenerator
                generator = EGIFGenerator()
                current_egif = generator.generate_egif(current_egi)
                
                if hasattr(self, 'current_egif_text'):
                    self.current_egif_text.setText(current_egif)
                else:
                    print(f"[Ergasterion] Current EGIF: {current_egif}")
            else:
                # Empty diagram
                if hasattr(self, 'current_egif_text'):
                    self.current_egif_text.setText("(empty)")
                else:
                    print("[Ergasterion] Current EGIF: (empty)")
                    
        except Exception as e:
            print(f"[Ergasterion] Error updating current EGIF: {e}")
    
    def _convert_current_diagram_to_egi(self):
        """Convert current diagram state to EGI for EGIF generation."""
        try:
            # Get current drawing schema from coordinator
            if hasattr(self.coordinator, 'current_drawing_schema'):
                drawing_schema = self.coordinator.current_drawing_schema
                
                # Convert drawing schema to EGI using the drawing_to_egi_adapter
                from drawing_to_egi_adapter import drawing_to_relational_graph
                current_egi = drawing_to_relational_graph(drawing_schema)
                return current_egi
            
            # Fallback: create empty EGI if no drawing schema
            from egi_core_dau import create_empty_graph
            return create_empty_graph()
            
        except Exception as e:
            print(f"[Ergasterion] Error converting diagram to EGI: {e}")
            # Return empty EGI on error
            from egi_core_dau import create_empty_graph
            return create_empty_graph()
    
    def _return_to_organon(self):
        """Signal to return to Organon after saving."""
        # Emit signal to parent Arisbe home to navigate back to Organon
        from PySide6.QtCore import QTimer
        
        # Use a timer to allow the dialog to close first
        QTimer.singleShot(100, self._navigate_to_organon)
    
    def _navigate_to_organon(self):
        """Navigate back to Organon room."""
        # Find the parent Arisbe home window and navigate to Organon
        parent = self.parent()
        while parent and not hasattr(parent, '_enter_library'):
            parent = parent.parent()
        
        if parent and hasattr(parent, '_enter_library'):
            parent._enter_library({"refresh_graph": True})
        else:
            print("Could not find Arisbe home to navigate back to Organon")
    
    def _load_egdf(self):
        """Load EGDF file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load EGDF File", "", "EGDF Files (*.egdf.json);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    egdf_data = json.load(f)
                
                # Load into coordinator
                success = self.coordinator.load_from_egdf(egdf_data)
                if success:
                    self._on_status_update(f"Loaded: {Path(file_path).name}")
                else:
                    QMessageBox.warning(self, "Load Error", "Failed to load EGDF data")
                    
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load file: {e}")
    
    def _load_default_content(self):
        """Load default content when not launched with handoff."""
        # For testing, just initialize empty
        pass
    
    def launch_with_handoff(self, package: GraphHandoffPackage) -> bool:
        """Launch Ergasterion with a handoff package from Organon."""
        self._launched_with_handoff = True
        
        # Receive handoff
        success = self.workflow_manager.receive_handoff(package)
        if not success:
            return False
        
        # Handle EGI-only mode setup
        if package.handoff_type == GraphHandoffType.EGI_ONLY and package.egi:
            self.coordinator.set_target_egi(package.egi)
            self._log_debug("EGI-only mode activated - target EGI set for comparison")
        elif package.handoff_type == GraphHandoffType.EGI_PLUS_EGDF:
            # Enable semantic constraints for EGI+EGDF mode
            self.coordinator.set_validation_mode("practice")
            self._log_debug("EGI+EGDF mode - semantic constraints enabled")
        
        # Update UI for handoff workflow
        self.setWindowTitle(f"Ergasterion - {package.handoff_type.value.title()} - {package.graph_id}")
        self.return_action.setEnabled(True)
        
        # Update displays
        self._update_egi_display()
        self._update_ligature_suggestions()
        
        # Show workflow status
        workflow_descriptions = {
            GraphHandoffType.BRAND_NEW: "Create new diagram from scratch (syntactic constraints only)",
            GraphHandoffType.EGI_ONLY: "Draw diagram to match existing logic (syntactic until matched, then semantic)",
            GraphHandoffType.EGI_PLUS_EGDF: "Adjust appearance or practice transformations (full constraints)"
        }
        
        description = workflow_descriptions.get(package.handoff_type, "Unknown workflow")
        self._log_debug(f"Handoff received: {description}")
        
        return True
    
    def _show_egi_match_confirmation(self):
        """Show confirmation dialog when EGI matches target."""
        reply = QMessageBox.question(
            self, 
            "EGI Match Detected",
            "Your diagram now matches the target EGI structure!\n\n"
            "Would you like to confirm this match?\n\n"
            "Confirming will:\n"
            "• Replace your drawing element IDs with the target EGI IDs\n"
            "• Enable semantic constraints (Practice Mode)\n"
            "• Allow saving the EGDF with consistent IDs",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.workflow_manager.confirm_egi_match()
            if success:
                QMessageBox.information(
                    self,
                    "Match Confirmed",
                    "EGI match confirmed! Your diagram now uses the target EGI IDs.\n\n"
                    "You can now practice transformations or save the EGDF."
                )
                # Update displays to reflect the ID changes
                self._update_egi_display()
                self._update_egif_displays()
            else:
                QMessageBox.warning(
                    self,
                    "Confirmation Failed", 
                    "Failed to confirm EGI match. Please try again."
                )
    
    # --- Display Updates ---
    
    def _update_egi_display(self):
        """Update EGI information display."""
        if self.coordinator.egi:
            egi_info = f"EGI Structure:\n"
            egi_info += f"Vertices: {len(self.coordinator.egi.V)}\n"
            egi_info += f"Edges: {len(self.coordinator.egi.E)}\n"
            egi_info += f"Cuts: {len(self.coordinator.egi.Cut)}\n"
            egi_info += f"Sheet: {self.coordinator.egi.sheet}\n"
            
            # Add vertex details
            if self.coordinator.egi.V:
                egi_info += "\nVertices:\n"
                for vertex in self.coordinator.egi.V:
                    label = self.coordinator.egi.rho.get(vertex.id, "unlabeled")
                    egi_info += f"  {vertex.id}: {label}\n"
            
            # Add edge details
            if self.coordinator.egi.E:
                egi_info += "\nEdges:\n"
                for edge in self.coordinator.egi.E:
                    relation = self.coordinator.egi.rho.get(edge.id, "unknown")
                    egi_info += f"  {edge.id}: {relation}\n"
            
            self.egi_text.setPlainText(egi_info)
        else:
            self.egi_text.setPlainText("No EGI loaded")
        
        # Update EGIF displays for EGI-only mode
        if self.coordinator.is_egi_only_mode:
            self._update_egif_displays()
            self._update_missing_elements_display()
    
    def _update_egif_displays(self):
        """Update target and current EGIF displays."""
        # Update target EGIF
        target_egif = self.coordinator.get_target_egif()
        self.target_egif_text.setPlainText(target_egif)
        
        # Update current EGIF
        current_egif = self.coordinator.get_current_egif()
        self.current_egif_text.setPlainText(current_egif)
        
        # Check for EGI match confirmation needed
        if self.workflow_manager and self.workflow_manager.is_egi_match_pending_confirmation():
            self._show_egi_match_confirmation()
    
    def _update_missing_elements_display(self):
        """Update missing elements display for EGI-only mode."""
        missing = self.coordinator.analyze_missing_elements()
        
        display_text = "Elements to Add:\n\n"
        
        if missing["vertices"]:
            display_text += "VERTICES:\n"
            for vertex in missing["vertices"]:
                display_text += f"  • {vertex}\n"
            display_text += "\n"
        
        if missing["predicates"]:
            display_text += "PREDICATES:\n"
            for predicate in missing["predicates"]:
                display_text += f"  • {predicate}\n"
            display_text += "\n"
        
        if missing["cuts"]:
            display_text += "CUTS:\n"
            for cut in missing["cuts"]:
                display_text += f"  • {cut}\n"
            display_text += "\n"
        
        if not any(missing.values()):
            display_text += "✅ All target elements present!\n"
        
        self.missing_elements_text.setPlainText(display_text)
    
    def _update_ligature_suggestions(self):
        """Update ligature suggestions display."""
        if not self.coordinator.egi or not self.coordinator.correspondence_engine:
            self.suggestions_text.setPlainText("No ligature data available")
            return
        
        try:
            suggestions_text = "Ligature Improvement Suggestions:\n\n"
            
            # Get all ligatures from current drawing schema
            ligature_count = 0
            for ligature in self.coordinator.current_drawing_schema["ligatures"]:
                predicate_id = ligature["edge_id"]
                suggestions = self.coordinator.suggest_ligature_improvements(predicate_id)
                
                if suggestions:
                    ligature_count += 1
                    suggestions_text += f"Predicate {predicate_id}:\n"
                    
                    for suggestion in suggestions:
                        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(suggestion["priority"], "⚪")
                        suggestions_text += f"  {priority_icon} {suggestion['description']}\n"
                    
                    suggestions_text += "\n"
            
            if ligature_count == 0:
                suggestions_text += "No improvement suggestions available.\n"
                suggestions_text += "All ligatures are optimally positioned."
            
            self.suggestions_text.setPlainText(suggestions_text)
            
        except Exception as e:
            self.suggestions_text.setPlainText(f"Error generating suggestions: {e}")
    
    def _setup_coordinate_negotiation(self):
        """Set up coordinate negotiation between Qt GUI and logical workspace."""
        # Use default GUI viewport bounds for Qt Graphics View
        # This will be called after the view is created
        gui_viewport_bounds = (-500, -500, 1000, 1000)  # Standard Qt scene bounds
        logical_workspace_bounds = (-250, -250, 500, 500)  # Centered logical workspace
        
        print(f"DRAWING_EDITOR: Setting up coordinate negotiation")
        print(f"DRAWING_EDITOR: GUI bounds: {gui_viewport_bounds}")
        print(f"DRAWING_EDITOR: Logical bounds: {logical_workspace_bounds}")
        
        # Negotiate mapping between GUI and logical coordinates
        self.coordinator.coordinate_negotiator.negotiate_coordinate_mapping(
            gui_viewport_bounds=gui_viewport_bounds,
            logical_workspace_bounds=logical_workspace_bounds
        )
        
        print(f"DRAWING_EDITOR: Coordinate negotiation complete")
    
    def _log_debug(self, message: str):
        """Log debug message."""
        current_text = self.debug_text.toPlainText()
        new_text = f"{current_text}\n{message}" if current_text else message
        self.debug_text.setPlainText(new_text)
        
        # Auto-scroll to bottom
        cursor = self.debug_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.debug_text.setTextCursor(cursor)


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    editor = RefactoredDrawingEditor()
    editor.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
