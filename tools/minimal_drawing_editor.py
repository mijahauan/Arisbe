#!/usr/bin/env python3
"""
Minimal Drawing Editor - Clean, Simple, Working
Just Qt graphics with direct element creation.
"""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView, 
                               QMenu, QInputDialog, QGraphicsEllipseItem, QGraphicsTextItem, 
                               QGraphicsRectItem, QLabel)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QFont


class MinimalDrawingEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal Drawing Editor")
        self.setGeometry(100, 100, 800, 600)
        
        # Create scene and view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        
        # Enable context menu
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)
        
        # Status bar
        self.statusBar().addWidget(QLabel("Right-click to add elements"))
        
        print("Minimal drawing editor initialized")
    
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
            print(f"Added predicate '{text}' at ({pos.x():.1f}, {pos.y():.1f})")
    
    def add_cut(self, pos):
        """Add a cut at the specified position."""
        width, height = 120, 80
        cut = QGraphicsRectItem(QRectF(0, 0, width, height))
        cut.setPos(pos.x() - width/2, pos.y() - height/2)
        cut.setPen(QPen(QColor("#000000"), 2))
        cut.setBrush(QBrush(QColor("#e8e8e8", 100)))
        cut.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        cut.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        self.scene.addItem(cut)
        print(f"Added cut at ({pos.x():.1f}, {pos.y():.1f})")


def main():
    app = QApplication(sys.argv)
    editor = MinimalDrawingEditor()
    editor.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
