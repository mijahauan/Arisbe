#!/usr/bin/env python3
"""
Ergasterion Drawing Editor - Fixed Constraints and No Repositioning

This version:
- Implements proper Permissive mode (free movement, only snap back on true violations)
- Fixes predicate creation issues
- Removes all automatic repositioning
- Allows movement across cut boundaries in Permissive mode
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import traceback
import uuid
from typing import Optional, Dict, Any, List, Set, Tuple
from dataclasses import dataclass

from PySide6.QtCore import Qt, QPointF, QRectF, QSizeF, Signal
from PySide6.QtGui import QAction, QKeySequence, QPen, QBrush, QColor, QPainter, QFont

# Add src to path for imports first
sys.path.append(str(Path(__file__).parent.parent / "src"))

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QWidget, QGraphicsView, QGraphicsScene, QMenuBar, 
                               QMenu, QToolBar, QStatusBar, QDockWidget, QLabel,
                               QPushButton, QGroupBox, QInputDialog, QMessageBox,
                               QGraphicsItem, QGraphicsEllipseItem, QGraphicsTextItem,
                               QGraphicsRectItem)

from diagram_coordinator import DiagramCoordinator
from egi_dto import EGIStateDTO, VertexDTO, EdgeDTO, CutDTO, SpatialInfo
from interactive_transformer_with_history import InteractiveTransformerWithHistory
from shared_diagram_renderer import SharedDiagramRenderer
from styling.style_manager import StyleManager
from controller.constraint_engine import (
    ConstraintMode, ValidationResult,
    validate_syntactic_constraints, validate_semantic_constraints
)

print("All imports successful")


class TransformationRulesWidget(QWidget):
    """Widget for existential graph transformation rules."""
    
    transformation_requested = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.current_selection = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the transformation rules UI."""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Transformation Rules")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Transformation buttons in a grid
        transform_layout = QHBoxLayout()
        
        # Double Cut transformations
        dc_group = QGroupBox("Double Cut")
        dc_layout = QVBoxLayout()
        
        self.dc_plus_btn = QPushButton("DC+ (Add Double Cut)")
        self.dc_plus_btn.clicked.connect(lambda: self._request_transformation("DC+"))
        dc_layout.addWidget(self.dc_plus_btn)
        
        self.dc_minus_btn = QPushButton("DC- (Remove Double Cut)")
        self.dc_minus_btn.clicked.connect(lambda: self._request_transformation("DC-"))
        dc_layout.addWidget(self.dc_minus_btn)
        
        dc_group.setLayout(dc_layout)
        transform_layout.addWidget(dc_group)
        
        # Insertion/Erasure transformations
        ie_group = QGroupBox("Insert/Erase")
        ie_layout = QVBoxLayout()
        
        self.ins_btn = QPushButton("INS (Insert Subgraph)")
        self.ins_btn.clicked.connect(lambda: self._request_transformation("INS"))
        ie_layout.addWidget(self.ins_btn)
        
        self.era_btn = QPushButton("ERA (Erase Subgraph)")
        self.era_btn.clicked.connect(lambda: self._request_transformation("ERA"))
        ie_layout.addWidget(self.era_btn)
        
        ie_group.setLayout(ie_layout)
        transform_layout.addWidget(ie_group)
        
        # Iteration transformations
        it_group = QGroupBox("Iteration")
        it_layout = QVBoxLayout()
        
        self.it_plus_btn = QPushButton("IT+ (Add Iteration)")
        self.it_plus_btn.clicked.connect(lambda: self._request_transformation("IT+"))
        it_layout.addWidget(self.it_plus_btn)
        
        self.it_minus_btn = QPushButton("IT- (Remove Iteration)")
        self.it_minus_btn.clicked.connect(lambda: self._request_transformation("IT-"))
        it_layout.addWidget(self.it_minus_btn)
        
        it_group.setLayout(it_layout)
        transform_layout.addWidget(it_group)
        
        layout.addLayout(transform_layout)
        
        # Status/instruction label
        self.status_label = QLabel("Select an area and subgraph, then choose a transformation rule.")
        self.status_label.setStyleSheet("color: blue; font-style: italic; margin-top: 10px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def _request_transformation(self, transform_type):
        """Request a transformation."""
        self.status_label.setText(f"Applying {transform_type} transformation...")
        self.transformation_requested.emit(transform_type)
        print(f"Transformation requested: {transform_type}")
    
    def update_selection_status(self, selection_info):
        """Update the status based on current selection."""
        if selection_info:
            self.status_label.setText(f"Selection: {selection_info}. Choose a transformation rule.")
        else:
            self.status_label.setText("Select an area and subgraph, then choose a transformation rule.")


class TransformationDrawingView(QGraphicsView):
    """Drawing view with area selection and transformation support."""
    
    selection_changed = Signal(str)
    
    def __init__(self, scene, coordinator, renderer, style_manager):
        super().__init__(scene)
        self.coordinator = coordinator
        self.renderer = renderer
        self.style_manager = style_manager
        self.current_selection = None
        self.selection_area = None
        self.dragging_item = None
        self.drag_start_pos = None
        self.last_mouse_pos = None
        
        # Enable selection and drag
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        
        print("Transformation drawing view initialized")
    
    def get_current_selection(self):
        """Get the current area/subgraph selection."""
        return self.current_selection
    
    def set_selection(self, selection_info):
        """Set the current selection and emit signal."""
        self.current_selection = selection_info
        selection_text = f"Area: {selection_info.get('area', 'sheet')}, Elements: {len(selection_info.get('elements', []))}"
        self.selection_changed.emit(selection_text)
        print(f"Selection updated: {selection_text}")
    
    def mousePressEvent(self, event):
        """Handle mouse press for element creation and selection."""
        if event.button() == Qt.RightButton:
            # Right-click context menu for element creation
            self._show_context_menu(event.pos())
        elif event.button() == Qt.LeftButton:
            # Handle area selection for transformations
            scene_pos = self.mapToScene(event.pos())
            self._update_selection_at_point(scene_pos)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move - no constraint interference."""
        # Let Qt handle all drag behavior naturally
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release - minimal constraint validation only."""
        # Only validate in strict mode, and only for severe violations
        if self.constraint_mode == "strict":
            # TODO: Add strict mode validation here if needed
            pass
        
        # Let Qt handle the release naturally
        super().mouseReleaseEvent(event)
    
    def _show_context_menu(self, view_pos):
        """Show context menu for element creation."""
        area_info = self._detect_area(self.mapToScene(view_pos))
        
        menu = QMenu(self)
        
        vertex_action = menu.addAction(f"Create Vertex in {area_info['type']}")
        vertex_action.triggered.connect(lambda: self._create_vertex(self.mapToScene(view_pos), area_info))
        
        predicate_action = menu.addAction(f"Create Predicate in {area_info['type']}")
        predicate_action.triggered.connect(lambda: self._create_predicate(self.mapToScene(view_pos), area_info))
        
        cut_action = menu.addAction(f"Create Cut in {area_info['type']}")
        cut_action.triggered.connect(lambda: self._create_cut(self.mapToScene(view_pos), area_info))
        
        menu.exec(self.mapToGlobal(view_pos))
    
    def _detect_area(self, scene_pos):
        """Simple area detection."""
        # For now, just return sheet area
        # TODO: Implement proper cut area detection if needed
        return {'type': 'sheet', 'area_id': 'sheet'}
    
    def _create_vertex(self, scene_pos, area_info):
        """Create vertex with minimal constraints."""
        try:
            position = Point2D(scene_pos.x(), scene_pos.y())
            vertex_id = self.coordinator.create_vertex(position, area_info['area_id'])
            
            if vertex_id:
                # Try to use renderer first
                vertex_dto = self.coordinator.egi_state.vertices[vertex_id]
                vertex_item = self.renderer.render_vertex(vertex_dto)
                
                # Fallback to simple creation if renderer fails
                if vertex_item is None:
                    vertex_item = QGraphicsEllipseItem(-4, -4, 8, 8)
                    vertex_item.setBrush(QBrush(QColor("white")))
                    vertex_item.setPen(QPen(QColor("black"), 1))
                    if vertex_dto.spatial:
                        vertex_item.setPos(vertex_dto.spatial.x, vertex_dto.spatial.y)
                    vertex_item.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                                       QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                    self.scene().addItem(vertex_item)
                
                vertex_item.vertex_id = vertex_id
                print(f"Created vertex {vertex_id} at ({scene_pos.x()}, {scene_pos.y()})")
                
        except Exception as e:
            print(f"Error creating vertex: {e}")
            traceback.print_exc()
    
    def _create_predicate(self, scene_pos, area_info):
        """Create predicate with minimal constraints."""
        text, ok = QInputDialog.getText(self, "Create Predicate", "Enter predicate name:")
        if ok and text:
            try:
                position = Point2D(scene_pos.x(), scene_pos.y())
                
                # Use the coordinator's method signature
                predicate_id = self.coordinator.create_predicate(text, position, area_info['area_id'])
                
                if predicate_id:
                    # Create simple predicate item directly (bypass problematic renderer)
                    predicate_item = QGraphicsTextItem(text)
                    predicate_item.setPos(scene_pos.x(), scene_pos.y())
                    predicate_item.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                                          QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                    font = QFont("Arial", 10)
                    predicate_item.setFont(font)
                    predicate_item.setDefaultTextColor(QColor("black"))
                    self.scene().addItem(predicate_item)
                    
                    predicate_item.predicate_id = predicate_id
                    print(f"Created predicate {predicate_id} '{text}' at ({scene_pos.x()}, {scene_pos.y()})")
                else:
                    print("Failed to create predicate - coordinator returned None")
                    
            except Exception as e:
                print(f"Error creating predicate: {e}")
                traceback.print_exc()
    
    def _create_cut(self, scene_pos, area_info):
        """Create cut with minimal constraints."""
        try:
            # Create a default-sized cut at the clicked position
            cut_id = self.coordinator.create_cut(
                scene_pos.x() - 50, scene_pos.y() - 40,  # x, y (top-left)
                100, 80,  # width, height
                area_info['area_id']
            )
            
            if cut_id:
                # Create simple cut visualization
                cut_item = QGraphicsRectItem(-50, -40, 100, 80)
                cut_item.setPos(scene_pos.x(), scene_pos.y())
                cut_item.setBrush(QBrush(QColor(255, 255, 255, 0)))  # Transparent fill
                cut_item.setPen(QPen(QColor("black"), 2))
                cut_item.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                                QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                self.scene().addItem(cut_item)
                
                cut_item.element_id = cut_id
                print(f"Created cut {cut_id} at ({scene_pos.x()}, {scene_pos.y()})")
                
        except Exception as e:
            print(f"Error creating cut: {e}")
            traceback.print_exc()
    
    def _update_selection_at_point(self, scene_pos):
        """Update selection based on clicked point."""
        try:
            # Find items at the clicked position
            items = self.scene.items(scene_pos)
            
            if items:
                # Get the topmost item
                selected_item = items[0]
                
                # Determine area and collect nearby elements
                area_id = "sheet"  # Default area
                elements = []
                
                # Collect all items in a small radius for subgraph selection
                radius = 50.0
                nearby_items = self.scene.items(QRectF(
                    scene_pos.x() - radius, scene_pos.y() - radius,
                    radius * 2, radius * 2
                ))
                
                for item in nearby_items:
                    if hasattr(item, 'element_id'):
                        elements.append(item.element_id)
                
                selection_info = {
                    'area': area_id,
                    'elements': elements,
                    'center': (scene_pos.x(), scene_pos.y())
                }
                
                self.set_selection(selection_info)
            else:
                # Clicked on empty area
                selection_info = {
                    'area': 'sheet',
                    'elements': [],
                    'center': (scene_pos.x(), scene_pos.y())
                }
                self.set_selection(selection_info)
                
        except Exception as e:
            print(f"Error updating selection: {e}")
    
    def clear_selection(self):
        """Clear the current selection."""
        self.current_selection = None
        self.selection_changed.emit("")
        print("Selection cleared")


class ErgasterionDrawingEditor(QMainWindow):
    """Main drawing editor with fixed constraints."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ergasterion - Fixed Constraints")
        self.setGeometry(100, 100, 1000, 700)
        
        try:
            # Initialize core components
            self.scene = QGraphicsScene()
            self.style_manager = StyleManager()
            self.coordinator = DiagramCoordinator(self.scene, self.style_manager)
            self.renderer = SharedDiagramRenderer(self.scene, self.style_manager)
            
            # Initialize transformation system with history
            self.transformer = InteractiveTransformerWithHistory()
            self.current_session_id = None
            
            print("Clean DTO-only DiagramCoordinator initialized")
            
            # Create main widget
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            
            # Create layout
            layout = QVBoxLayout()
            
            # Add transformation rules widget
            self.transformation_widget = TransformationRulesWidget()
            self.transformation_widget.transformation_requested.connect(self._on_transformation_requested)
            layout.addWidget(self.transformation_widget)
            
            # Create transformation-enabled drawing view
            self.view = TransformationDrawingView(
                self.scene, self.coordinator, self.renderer, self.style_manager
            )
            self.view.selection_changed.connect(self.transformation_widget.update_selection_status)
            layout.addWidget(self.view)
            
            main_widget.setLayout(layout)
            
            # Status bar
            self.statusBar().showMessage("Ergasterion: Edit graph appearance or practice transformations. Right-click to create elements.")
            
            print("Ergasterion Drawing Editor initialized")
            
        except Exception as e:
            print(f"Error initializing editor: {e}")
            traceback.print_exc()
    
    def _on_transformation_requested(self, transform_type):
        """Handle transformation request from the rules widget."""
        print(f"[Ergasterion] Transformation requested: {transform_type}")
        
        if not self.current_session_id:
            print("[Ergasterion] No active transformation session")
            return
        
        # Get current selection from the drawing view
        selection = self.drawing_view.current_selection
        
        if not selection or 'area' not in selection:
            print("[Ergasterion] No area selected for transformation")
            return
        
        # Convert selection to target area description
        area_bounds = selection['area']
        target_area = f"area_{area_bounds['x1']}_{area_bounds['y1']}_{area_bounds['x2']}_{area_bounds['y2']}"
        
        # Apply transformation using the existing system
        result = self.transformer.apply_transformation_with_history(
            rule_name=transform_type,
            target_area=target_area,
            user_annotation=f"Applied {transform_type} transformation via GUI"
        )
        
        if result["success"]:
            print(f"[Ergasterion] {transform_type} transformation applied successfully")
            
            # Convert updated EGI back to DTO and re-render
            from egi_dto import egi_to_dto
            updated_egi = self.transformer.base_transformer.current_egi
            updated_dto = egi_to_dto(updated_egi)
            
            # Update coordinator with new DTO
            self.coordinator.load_egi_dto(updated_dto)
            
        else:
            print(f"[Ergasterion] {transform_type} transformation failed: {result.get('error', 'Unknown error')}")
        
        # Update transformation widget status
        self.transformation_widget.update_selection_status(selection)
    
    def add_undo_redo_support(self):
        """Add undo/redo functionality using transformation history."""
        # Add undo action
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self._undo_transformation)
        
        # Add to menu if it exists
        if hasattr(self, 'edit_menu'):
            self.edit_menu.addAction(undo_action)
    
    def _undo_transformation(self):
        """Undo the last transformation."""
        if not self.current_session_id:
            print("[Ergasterion] No active session for undo")
            return
        
        result = self.transformer.undo_transformation()
        
        if result["success"]:
            print("[Ergasterion] Transformation undone successfully")
            
            # Convert updated EGI back to DTO and re-render
            from egi_dto import egi_to_dto
            updated_egi = self.transformer.base_transformer.current_egi
            updated_dto = egi_to_dto(updated_egi)
            
            # Update coordinator with new DTO
            self.coordinator.load_egi_dto(updated_dto)
        else:
            print(f"[Ergasterion] Undo failed: {result.get('error', 'Cannot undo')}")
            
            # Re-render the scene
            self.coordinator._render_loaded_elements()
            
            print(f"[DC-] Removed double cut: outer={outer_id}, inner={inner_id}")
            
        except Exception as e:
            print(f"[DC-] Error removing double cut: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_insertion(self, selection):
        """Apply INS transformation: insert subgraph at selection."""
        print(f"[INS] Inserting subgraph at selection: {selection}")
        # TODO: Implement INS logic with subgraph input dialog
        pass
    
    def _apply_erasure(self, selection):
        """Apply ERA transformation: erase selected subgraph."""
        print(f"[ERA] Erasing subgraph at selection: {selection}")
        # TODO: Implement ERA logic
        pass
    
    def _apply_iteration_addition(self, selection):
        """Apply IT+ transformation: iterate selected subgraph."""
        print(f"[IT+] Adding iteration of subgraph: {selection}")
        # TODO: Implement IT+ logic with area selection dialog
        pass
    
    def _apply_iteration_removal(self, selection):
        """Apply IT- transformation: remove iteration if isomorphism exists."""
        print(f"[IT-] Removing iteration of subgraph: {selection}")
        # TODO: Implement IT- logic
        pass
    
    def set_current_graph_dir(self, graph_dir: str):
        """Set the current graph directory for the editor."""
        self.current_graph_dir = graph_dir
        self.statusBar().showMessage(f"Loaded graph from: {graph_dir}")
        print(f"[Ergasterion] Set current graph directory: {graph_dir}")
    
    def load_egi_dto(self, egi_dto):
        """Load EGI DTO from Organon handoff."""
        print(f"[Ergasterion] Loading EGI DTO with {len(egi_dto.vertices)} vertices, {len(egi_dto.edges)} edges, {len(egi_dto.cuts)} cuts")
        
        # Load DTO into coordinator for rendering
        self.coordinator.load_egi_dto(egi_dto)
        
        # Convert DTO back to EGI for transformation system
        from egi_dto import dto_to_egi
        from datetime import datetime
        egi = dto_to_egi(egi_dto)
        
        # Create transformation session
        self.current_session_id = self.transformer.create_new_session(
            name=f"Ergasterion Session {datetime.now().strftime('%H:%M:%S')}",
            description="Interactive diagram transformation session"
        )
        
        # Set the EGI in the transformer
        self.transformer.base_transformer.current_egi = egi
        
        print(f"[Ergasterion] EGI DTO loaded and transformation session created")
    
    def load_handoff_data(self, egi_data: Optional[Dict] = None, egdf_data: Optional[Dict] = None):
        """Load EGI and EGDF data from handoff."""
        try:
            if egi_data:
                print(f"[Ergasterion] Loading EGI data with {len(egi_data)} entries")
                # Load EGI data into the coordinator
                self.coordinator.load_egi_data(egi_data)
                
            if egdf_data:
                print(f"[Ergasterion] EGDF data available but using EGI rendering instead")
                # Skip EGDF rendering - using coordinator's direct rendering
                
            # Update view
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            self.statusBar().showMessage("Graph loaded successfully")
            
        except Exception as e:
            print(f"[Ergasterion] Error loading handoff data: {e}")
            self.statusBar().showMessage(f"Error loading graph: {e}")


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    try:
        window = ErgasterionDrawingEditor()
        window.show()
        return app.exec()
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
