#!/usr/bin/env python3

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPen, QBrush, QColor

class MinimalTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal Qt Graphics Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create scene and view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        
        # Add a test circle immediately
        circle = QGraphicsEllipseItem(100, 100, 50, 50)
        circle.setPen(QPen(QColor("#000000"), 2))
        circle.setBrush(QBrush(QColor("#ff0000")))
        self.scene.addItem(circle)
        
        print(f"Added circle to scene. Scene has {len(self.scene.items())} items")
        print(f"Scene rect: {self.scene.sceneRect()}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MinimalTest()
    window.show()
    sys.exit(app.exec())
