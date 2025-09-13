#!/usr/bin/env python3
"""
Minimal Qt test to verify basic functionality.
"""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QGraphicsView, QGraphicsScene, 
                            QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem,
                            QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QBrush, QColor, QFont


class MinimalEGIWindow(QMainWindow):
    """Minimal EGI window for testing."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal EGI Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Create graphics view and scene
        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        layout.addWidget(self.graphics_view)
        
        # Create control panel
        control_panel = QWidget()
        control_panel.setFixedWidth(200)
        control_layout = QVBoxLayout(control_panel)
        
        # Add buttons
        add_circle_btn = QPushButton("Add Circle")
        add_circle_btn.clicked.connect(self.add_circle)
        control_layout.addWidget(add_circle_btn)
        
        add_rect_btn = QPushButton("Add Rectangle")
        add_rect_btn.clicked.connect(self.add_rectangle)
        control_layout.addWidget(add_rect_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_scene)
        control_layout.addWidget(clear_btn)
        
        self.status_label = QLabel("Ready")
        control_layout.addWidget(self.status_label)
        
        control_layout.addStretch()
        layout.addWidget(control_panel)
        
        # Set scene bounds
        self.scene.setSceneRect(0, 0, 600, 400)
        
        # Add initial test items
        self.add_test_items()
    
    def add_test_items(self):
        """Add EGI graph elements using the new system."""
        try:
            # Import the graph-based system
            import sys
            sys.path.append('/Users/mjh/Sync/GitHub/Arisbe/src')
            from egi_graph_operations import EGISystemController
            from egi_spatial_correspondence import SpatialBounds
            
            # Create controller
            canvas_bounds = SpatialBounds(50, 50, 500, 300)
            self.controller = EGISystemController("sheet_main", canvas_bounds)
            
            # Multi-step EGI construction - flexible ordering
            
            # Step 1: Add vertex graph for Tom (quantifies existence)
            self.controller.add_vertex_to_area("Tom", "sheet_main")
            
            # Step 2a: Add predicate graphs (without vertices initially)
            self.controller.add_predicate_to_area("e1", "Person", "sheet_main")
            self.controller.add_predicate_to_area("e2", "Happy", "sheet_main")
            
            # Step 3a: Bind vertex to predicates with ligatures
            self.controller.bind_vertex_to_predicate("Tom", "e1", "sheet_main")
            self.controller.bind_vertex_to_predicate("Tom", "e2", "sheet_main")
            
            # Create negation area
            self.controller.create_negation("cut_1", "sheet_main")
            
            # Alternative ordering: predicate first, then bind
            # Step 2b: Add predicate in cut
            self.controller.add_predicate_to_area("e3", "Sad", "cut_1")
            # Step 3b: Bind same Tom vertex to Sad predicate (ligatures can cross cuts)
            self.controller.bind_vertex_to_predicate("Tom", "e3", "cut_1")
            
            print("DEBUG: Multi-step EGI construction:")
            print("- Step 1: Add Tom vertex to sheet_main")
            print("- Step 2: Add Person, Happy predicates to sheet_main")
            print("- Step 3: Bind Tom to Person and Happy via ligatures")
            print("- Step 2b: Add Sad predicate to ~[cut_1]")
            print("- Step 3b: Bind Tom to Sad via ligature (cross-cut binding)")
            
            # Get layout and render
            layout = self.controller.get_complete_layout()
            self.render_egi_layout(layout)
            
            # Display linear replica for debugging
            if 'linear_replica' in layout:
                print(f"\nLINEAR GRAPH REPLICA: {layout['linear_replica']}")
                self.status_label.setText(f"EGI Graph: {layout['linear_replica']} ({len(self.scene.items())} items)")
            else:
                self.status_label.setText(f"EGI Graph Loaded: {len(self.scene.items())} items")
            
        except Exception as e:
            print(f"Error loading EGI system: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to simple test items
            circle = QGraphicsEllipseItem(50, 50, 60, 60)
            circle.setPen(QPen(QColor(0, 0, 255), 3))
            circle.setBrush(QBrush(QColor(100, 150, 255)))
            self.scene.addItem(circle)
            
            text = QGraphicsTextItem("EGI System Error")
            text.setPos(50, 150)
            text.setFont(QFont("Arial", 16))
            self.scene.addItem(text)
            
            self.status_label.setText(f"Error: {str(e)[:50]}")
    
    def render_egi_layout(self, layout):
        """Render EGI layout using the working Qt framework."""
        commands = layout.get('rendering_commands', [])
        print(f"Rendering {len(commands)} EGI commands")
        
        for command in commands:
            cmd_type = command.get('type')
            
            if cmd_type == 'render_vertex':
                self.render_egi_vertex(command)
            elif cmd_type == 'render_predicate':
                self.render_egi_predicate(command)
            elif cmd_type == 'render_cut':
                self.render_egi_cut(command)
            elif cmd_type == 'render_ligature':
                self.render_egi_ligature(command)
    
    def render_egi_vertex(self, command):
        """Render EGI vertex as Peircean spot."""
        position = command.get('position', {})
        vertex_id = command.get('vertex_id', 'vertex')
        
        x = position.get('x', 100)
        y = position.get('y', 100)
        
        # Draw vertex as black spot (slightly thicker than ligature line)
        circle = QGraphicsEllipseItem(x - 4, y - 4, 8, 8)
        circle.setPen(QPen(QColor(0, 0, 0), 1))
        circle.setBrush(QBrush(QColor(0, 0, 0)))
        self.scene.addItem(circle)
        
        # Add label
        label = QGraphicsTextItem(vertex_id)
        label.setPos(x + 8, y - 8)
        label.setFont(QFont("Arial", 9))
        self.scene.addItem(label)
    
    def render_egi_predicate(self, command):
        """Render EGI predicate with Peircean styling."""
        position = command.get('position', {})
        edge_id = command.get('edge_id', 'predicate')
        logical_area = command.get('logical_area', 'sheet_main')
        
        x = position.get('x', 100)
        y = position.get('y', 100)
        
        # Get relation name from controller
        relation_name = edge_id  # Default fallback
        try:
            for area_id, area in self.controller.logical_system.logical_areas.items():
                for graph in area.contained_graphs:
                    if edge_id in graph.relation_mapping:
                        relation_name = graph.relation_mapping[edge_id]
                        break
        except:
            pass
        
        # Create text item with tight bounds
        label = QGraphicsTextItem(relation_name)
        label.setFont(QFont("Arial", 10))
        
        # Get text bounds for tight boundary
        text_rect = label.boundingRect()
        text_width = text_rect.width()
        text_height = text_rect.height()
        
        # Determine background color based on area nesting (Peirce convention)
        bg_color = QColor(255, 255, 255)  # Even-enclosed (unshaded)
        if logical_area != 'sheet_main':  # Odd-enclosed (light gray)
            bg_color = QColor(240, 240, 240)
        
        # Create invisible tight boundary rectangle
        rect = QGraphicsRectItem(x - text_width/2 - 2, y - text_height/2 - 1, 
                                text_width + 4, text_height + 2)
        rect.setPen(QPen(QColor(0, 0, 0, 0), 0))  # Invisible boundary
        rect.setBrush(QBrush(bg_color))
        self.scene.addItem(rect)
        
        # Position text centered on the rectangle
        label.setPos(x - text_width/2, y - text_height/2)
        self.scene.addItem(label)
        
        # Store predicate bounds for ligature attachment
        command['predicate_bounds'] = {
            'x': x - text_width/2 - 2,
            'y': y - text_height/2 - 1,
            'width': text_width + 4,
            'height': text_height + 2
        }
    
    def render_egi_cut(self, command):
        """Render EGI cut with Peircean thin solid line and rounded corners."""
        bounds = command.get('bounds', {})
        cut_id = command.get('cut_id', 'cut')
        
        # Draw cut boundary with thin solid line and rounded corners
        from PySide6.QtWidgets import QGraphicsRectItem
        rect = QGraphicsRectItem(
            bounds.get('x', 0), bounds.get('y', 0),
            bounds.get('width', 100), bounds.get('height', 100)
        )
        
        pen = QPen(QColor(0, 0, 0), 1)  # Thin black solid line
        pen.setStyle(Qt.PenStyle.SolidLine)
        rect.setPen(pen)
        
        # Add rounded corners
        from PySide6.QtCore import QRectF
        from PySide6.QtWidgets import QGraphicsPathItem
        from PySide6.QtGui import QPainterPath
        
        # Create rounded rectangle path
        path = QPainterPath()
        rect_f = QRectF(
            bounds.get('x', 0), bounds.get('y', 0),
            bounds.get('width', 100), bounds.get('height', 100)
        )
        path.addRoundedRect(rect_f, 10, 10)  # 10px corner radius
        
        # Create path item instead of rect item
        path_item = QGraphicsPathItem(path)
        path_item.setPen(pen)
        
        # Light gray background for odd-enclosed areas (Peirce convention)
        path_item.setBrush(QBrush(QColor(240, 240, 240, 100)))
        self.scene.addItem(path_item)
        
        # Cut label suppressed - cuts should only show boundaries, not IDs
    
    def render_egi_ligature(self, command):
        """Render EGI ligature with Peircean heavy line styling."""
        path_points = command.get('path_points', [])
        
        if len(path_points) < 2:
            return
        
        from PySide6.QtWidgets import QGraphicsLineItem
        
        # Draw heavy lines for ligatures (Peirce convention)
        start_point = path_points[0]
        for i in range(1, len(path_points)):
            end_point = path_points[i]
            line = QGraphicsLineItem(
                start_point[0], start_point[1],
                end_point[0], end_point[1]
            )
            # Heavy line for ligatures (thicker than cuts)
            line.setPen(QPen(QColor(0, 0, 0), 3))
            self.scene.addItem(line)
    
    def add_circle(self):
        """Add a circle at random position."""
        import random
        x = random.randint(50, 500)
        y = random.randint(50, 300)
        
        circle = QGraphicsEllipseItem(x, y, 40, 40)
        circle.setPen(QPen(QColor(0, 255, 0), 2))
        circle.setBrush(QBrush(QColor(200, 255, 200)))
        self.scene.addItem(circle)
        
        self.status_label.setText(f"Items: {len(self.scene.items())}")
    
    def add_rectangle(self):
        """Add a rectangle at random position."""
        import random
        x = random.randint(50, 500)
        y = random.randint(50, 300)
        
        rect = QGraphicsRectItem(x, y, 60, 30)
        rect.setPen(QPen(QColor(255, 0, 255), 2))
        rect.setBrush(QBrush(QColor(255, 200, 255)))
        self.scene.addItem(rect)
        
        self.status_label.setText(f"Items: {len(self.scene.items())}")
    
    def clear_scene(self):
        """Clear all items from scene."""
        self.scene.clear()
        self.status_label.setText("Cleared")


def main():
    """Temporarily disabled GUI demo."""
    print("qt_test_minimal.py is temporarily disabled while the headless EGI↔spatial adapter is stabilized."
          " Run the headless tests (pytest) instead.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
