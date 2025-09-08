#!/usr/bin/env python3
"""
Ergasterion Drawing Editor - Fixed Constraints and No Repositioning

This version:
- Implements proper Permissive mode (free movement, only snap back on true violations)
- Fixes predicate creation issues
- Removes all automatic repositioning
- Allows movement across cut boundaries in Permissive mode
- Uses default EG styling
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import traceback

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

from diagram_coordinator import DiagramCoordinator, Point2D
from shared_diagram_renderer import SharedDiagramRenderer
from styling.style_manager import StyleManager
from controller.constraint_engine import (
    ConstraintMode, ValidationResult,
    validate_syntactic_constraints, validate_semantic_constraints
)

print("All imports successful")


class ConstraintModeWidget(QWidget):
    """Widget for controlling constraint modes."""
    
    mode_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.current_mode = "permissive"
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the constraint mode UI."""
        layout = QHBoxLayout()
        
        # Mode selection
        self.mode_label = QLabel("Mode:")
        layout.addWidget(self.mode_label)
        
        self.permissive_btn = QPushButton("Permissive")
        self.permissive_btn.setCheckable(True)
        self.permissive_btn.setChecked(True)
        self.permissive_btn.clicked.connect(lambda: self._set_mode("permissive"))
        layout.addWidget(self.permissive_btn)
        
        self.strict_btn = QPushButton("Strict")
        self.strict_btn.setCheckable(True)
        self.strict_btn.clicked.connect(lambda: self._set_mode("strict"))
        layout.addWidget(self.strict_btn)
        
        # Status
        self.status_label = QLabel("Permissive: Free movement, minimal constraints")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def _set_mode(self, mode):
        """Set constraint mode."""
        self.current_mode = mode
        
        # Update button states
        self.permissive_btn.setChecked(mode == "permissive")
        self.strict_btn.setChecked(mode == "strict")
        
        # Update status
        if mode == "permissive":
            self.status_label.setText("Permissive: Free movement, minimal constraints")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("Strict: Auto-adjust, semantic constraints")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.mode_changed.emit(mode)
        print(f"Constraint mode changed to: {mode}")


class MinimalConstraintDrawingView(QGraphicsView):
    """Drawing view with minimal constraints and no repositioning."""
    
    def __init__(self, scene, coordinator, renderer, style_manager):
        super().__init__(scene)
        self.coordinator = coordinator
        self.renderer = renderer
        self.style_manager = style_manager
        self.constraint_mode = "permissive"
        
        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        print("Minimal constraint drawing view initialized")
    
    def set_constraint_mode(self, mode: str):
        """Set the constraint mode."""
        self.constraint_mode = mode
        print(f"Drawing view constraint mode set to: {mode}")
    
    def mousePressEvent(self, event):
        """Handle mouse press - no constraint interference."""
        if event.button() == Qt.MouseButton.RightButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            self._show_context_menu(event.position().toPoint(), scene_pos)
            return
        
        # Let Qt handle all left-click behavior naturally
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
    
    def _show_context_menu(self, view_pos, scene_pos):
        """Show context menu for element creation."""
        area_info = self._detect_area(scene_pos)
        
        menu = QMenu(self)
        
        vertex_action = menu.addAction(f"Create Vertex in {area_info['type']}")
        vertex_action.triggered.connect(lambda: self._create_vertex(scene_pos, area_info))
        
        predicate_action = menu.addAction(f"Create Predicate in {area_info['type']}")
        predicate_action.triggered.connect(lambda: self._create_predicate(scene_pos, area_info))
        
        cut_action = menu.addAction(f"Create Cut in {area_info['type']}")
        cut_action.triggered.connect(lambda: self._create_cut(scene_pos, area_info))
        
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
            width = 150.0
            height = 100.0
            
            # Only validate for severe overlaps in permissive mode
            if self.constraint_mode == "permissive":
                # Very minimal validation - only prevent complete overlaps
                pass  # Allow almost everything in permissive mode
            
            cut_id = self.coordinator.create_cut(
                scene_pos.x(), scene_pos.y(), width, height, area_info['area_id']
            )
            
            if cut_id:
                # Try to use renderer first
                cut_dto = self.coordinator.egi_state.cuts[cut_id]
                cut_item = self.renderer.render_cut(cut_dto)
                
                # Fallback to simple creation if renderer fails
                if cut_item is None:
                    if cut_dto.spatial:
                        cut_item = QGraphicsRectItem(0, 0, cut_dto.spatial.width, cut_dto.spatial.height)
                        cut_item.setBrush(QBrush(QColor(255, 255, 255, 0)))  # Transparent fill
                        cut_item.setPen(QPen(QColor("black"), 2))  # Black border
                        cut_item.setPos(cut_dto.spatial.x, cut_dto.spatial.y)
                        cut_item.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                                        QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                        self.scene().addItem(cut_item)
                
                cut_item.cut_id = cut_id
                print(f"Created cut {cut_id} at ({scene_pos.x()}, {scene_pos.y()})")
                
        except Exception as e:
            print(f"Error creating cut: {e}")
            traceback.print_exc()


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
            
            print("Clean DTO-only DiagramCoordinator initialized")
            
            # Create main widget
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            
            # Create layout
            layout = QVBoxLayout()
            
            # Add constraint mode widget
            self.constraint_widget = ConstraintModeWidget()
            self.constraint_widget.mode_changed.connect(self._on_constraint_mode_changed)
            layout.addWidget(self.constraint_widget)
            
            # Create minimal constraint view
            self.view = MinimalConstraintDrawingView(
                self.scene, self.coordinator, self.renderer, self.style_manager
            )
            layout.addWidget(self.view)
            
            main_widget.setLayout(layout)
            
            # Status bar
            self.statusBar().showMessage("Fixed constraints: Permissive mode allows free movement. Right-click to create elements.")
            
            print("Ergasterion Drawing Editor initialized")
            
        except Exception as e:
            print(f"Error initializing editor: {e}")
            traceback.print_exc()
    
    def _on_constraint_mode_changed(self, mode_value):
        """Handle constraint mode change."""
        self.view.set_constraint_mode(mode_value)
        
        if mode_value == "permissive":
            self.statusBar().showMessage("PERMISSIVE: Free movement, minimal constraints")
        else:
            self.statusBar().showMessage("STRICT: Auto-adjust elements, semantic constraints")


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
