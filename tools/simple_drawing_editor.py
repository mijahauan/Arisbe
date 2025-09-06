#!/usr/bin/env python3
"""
Simple Drawing Editor - Clean slate implementation
Focus: Working diagram creation without complex architecture
"""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView, 
                               QMenu, QInputDialog, QGraphicsEllipseItem, QGraphicsTextItem, 
                               QGraphicsRectItem, QLabel, QToolBar, QVBoxLayout, QWidget)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QAction


class SimpleDrawingEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Drawing Editor")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create scene and view
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-500, -350, 1000, 700)
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        
        # Enable context menu
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)
        
        # Create toolbar
        self.create_toolbar()
        
        # Status bar
        self.statusBar().addWidget(QLabel("Right-click to add elements | Drag to move | Select and press Delete to remove"))
        
        # Track elements for deletion
        self.elements = []
        
        print("Simple drawing editor initialized")
    
    def create_toolbar(self):
        """Create a simple toolbar."""
        toolbar = self.addToolBar("Main")
        
        clear_action = QAction("Clear All", self)
        clear_action.triggered.connect(self.clear_all)
        toolbar.addAction(clear_action)
        
        toolbar.addSeparator()
        
        info_action = QAction("Info", self)
        info_action.triggered.connect(self.show_info)
        toolbar.addAction(info_action)
    
    def show_context_menu(self, position):
        """Show context menu at right-click position."""
        scene_pos = self.view.mapToScene(position)
        global_pos = self.view.mapToGlobal(position)
        
        menu = QMenu("Add Element", self)
        
        vertex_action = menu.addAction("Add Vertex")
        vertex_action.triggered.connect(lambda: self.add_vertex(scene_pos))
        
        predicate_action = menu.addAction("Add Predicate")
        predicate_action.triggered.connect(lambda: self.add_predicate(scene_pos))
        
        cut_action = menu.addAction("Add Cut")
        cut_action.triggered.connect(lambda: self.add_cut(scene_pos))
        
        menu.popup(global_pos)
    
    def add_vertex(self, pos):
        """Add a vertex at the specified position."""
        radius = 8
        vertex = QGraphicsEllipseItem(pos.x() - radius, pos.y() - radius, 2 * radius, 2 * radius)
        vertex.setPen(QPen(QColor("#000000"), 2))
        vertex.setBrush(QBrush(QColor("#ff6b6b")))
        vertex.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
        vertex.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        self.scene.addItem(vertex)
        self.elements.append(vertex)
        print(f"Added vertex at ({pos.x():.1f}, {pos.y():.1f})")
    
    def add_predicate(self, pos):
        """Add a predicate at the specified position."""
        text, ok = QInputDialog.getText(self, "Add Predicate", "Enter predicate text:")
        if ok and text:
            predicate = QGraphicsTextItem(text)
            predicate.setPos(pos.x(), pos.y())
            predicate.setFont(QFont("Arial", 12))
            predicate.setDefaultTextColor(QColor("#000000"))
            predicate.setFlag(QGraphicsTextItem.GraphicsItemFlag.ItemIsMovable, True)
            predicate.setFlag(QGraphicsTextItem.GraphicsItemFlag.ItemIsSelectable, True)
            
            self.scene.addItem(predicate)
            self.elements.append(predicate)
            print(f"Added predicate '{text}' at ({pos.x():.1f}, {pos.y():.1f})")
    
    def add_cut(self, pos):
        """Add a cut at the specified position."""
        width, height = 120, 80
        cut = QGraphicsRectItem(QRectF(0, 0, width, height))
        cut.setPos(pos.x() - width/2, pos.y() - height/2)
        cut.setPen(QPen(QColor("#000000"), 2))
        cut.setBrush(QBrush(QColor(220, 220, 220, 100)))
        cut.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        cut.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        self.scene.addItem(cut)
        self.elements.append(cut)
        print(f"Added cut at ({pos.x():.1f}, {pos.y():.1f})")
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Delete:
            # Delete selected items
            selected_items = self.scene.selectedItems()
            for item in selected_items:
                self.scene.removeItem(item)
                if item in self.elements:
                    self.elements.remove(item)
            if selected_items:
                print(f"Deleted {len(selected_items)} item(s)")
        else:
            super().keyPressEvent(event)
    
    def clear_all(self):
        """Clear all elements from the scene."""
        self.scene.clear()
        self.elements.clear()
        print("Cleared all elements")
    
    def show_info(self):
        """Show information about current elements."""
        vertex_count = sum(1 for item in self.elements if isinstance(item, QGraphicsEllipseItem))
        predicate_count = sum(1 for item in self.elements if isinstance(item, QGraphicsTextItem))
        cut_count = sum(1 for item in self.elements if isinstance(item, QGraphicsRectItem))
        
        info = f"Elements: {vertex_count} vertices, {predicate_count} predicates, {cut_count} cuts"
        self.statusBar().showMessage(info, 3000)
        print(info)


def main():
    app = QApplication(sys.argv)
    editor = SimpleDrawingEditor()
    editor.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
