#!/usr/bin/env python3
"""
Corpus-based EGI Drawing Test System

This system loads EGI examples from the corpus and displays them using the 
spatial correspondence engine to test various EGI drawing scenarios.
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QListWidget, QGraphicsView, 
                            QGraphicsScene, QTextEdit, QSplitter, QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from egi_graph_operations import EGISystemController
from egi_spatial_correspondence import SpatialBounds
from egif_parser_dau import parse_egif


class CorpusEGITestWindow(QMainWindow):
    """Main window for corpus-based EGI testing."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Corpus EGI Drawing Test System")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize corpus data
        self.corpus_items = []
        self.current_controller = None
        
        self.setup_ui()
        self.load_corpus_data()
        
    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Corpus selection
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Corpus list
        left_layout.addWidget(QLabel("Corpus Examples:"))
        self.corpus_list = QListWidget()
        self.corpus_list.itemClicked.connect(self.on_corpus_item_selected)
        left_layout.addWidget(self.corpus_list)
        
        # Load button
        load_button = QPushButton("Load Selected EGI")
        load_button.clicked.connect(self.load_selected_egi)
        left_layout.addWidget(load_button)
        
        # Info display
        left_layout.addWidget(QLabel("EGI Information:"))
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(200)
        self.info_text.setFont(QFont("Monaco", 10))
        left_layout.addWidget(self.info_text)
        
        splitter.addWidget(left_panel)
        
        # Right panel - EGI visualization
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        right_layout.addWidget(QLabel("EGI Visualization:"))
        
        # Graphics view for EGI display
        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        right_layout.addWidget(self.graphics_view)
        
        # Status display
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setFont(QFont("Monaco", 9))
        right_layout.addWidget(self.status_text)
        
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
    def load_corpus_data(self):
        """Load corpus data from the corpus directory."""
        corpus_path = Path(__file__).parent.parent / "corpus" / "corpus"
        
        if not corpus_path.exists():
            self.status_text.append("❌ Corpus directory not found")
            return
            
        # Load from different corpus categories
        categories = ["canonical", "peirce", "scholars", "alpha", "beta", "challenging"]
        
        for category in categories:
            category_path = corpus_path / category
            if category_path.exists():
                self.load_category_items(category, category_path)
                
        self.status_text.append(f"✅ Loaded {len(self.corpus_items)} corpus items")
        
    def load_category_items(self, category: str, category_path: Path):
        """Load items from a specific corpus category."""
        for file_path in category_path.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    item_data = json.load(f)
                    
                # Add category and file info
                item_data['category'] = category
                item_data['file_path'] = str(file_path)
                
                self.corpus_items.append(item_data)
                
                # Add to list widget
                display_name = f"[{category}] {item_data.get('title', item_data.get('id', file_path.stem))}"
                self.corpus_list.addItem(display_name)
                
            except Exception as e:
                self.status_text.append(f"⚠️ Error loading {file_path}: {e}")
                
    def on_corpus_item_selected(self, item):
        """Handle corpus item selection."""
        index = self.corpus_list.row(item)
        if 0 <= index < len(self.corpus_items):
            selected_item = self.corpus_items[index]
            self.display_corpus_info(selected_item)
            
    def display_corpus_info(self, item_data: Dict[str, Any]):
        """Display information about the selected corpus item."""
        info_text = f"ID: {item_data.get('id', 'Unknown')}\n"
        info_text += f"Title: {item_data.get('title', 'Unknown')}\n"
        info_text += f"Category: {item_data.get('category', 'Unknown')}\n"
        info_text += f"Description: {item_data.get('description', 'No description')}\n\n"
        
        if 'logical_form' in item_data:
            info_text += f"Logical Form: {item_data['logical_form']}\n\n"
            
        if 'egif_content' in item_data:
            info_text += f"EGIF Content:\n{item_data['egif_content']}\n\n"
            
        if 'notes' in item_data:
            info_text += f"Notes: {item_data['notes']}\n"
            
        self.info_text.setPlainText(info_text)
        
    def load_selected_egi(self):
        """Load and display the selected EGI."""
        current_row = self.corpus_list.currentRow()
        if current_row < 0 or current_row >= len(self.corpus_items):
            self.status_text.append("❌ No corpus item selected")
            return
            
        selected_item = self.corpus_items[current_row]
        
        try:
            # Clear previous scene
            self.scene.clear()
            
            # Get EGIF content
            egif_content = selected_item.get('egif_content')
            if not egif_content:
                self.status_text.append("❌ No EGIF content found in selected item")
                return
                
            self.status_text.append(f"🔄 Loading EGI: {selected_item.get('title', 'Unknown')}")
            
            # Parse EGIF and create EGI system
            egi = parse_egif(egif_content)
            
            # Create controller with canvas bounds using EGIF sheet id as the sheet area
            canvas_bounds = SpatialBounds(50, 50, 700, 500)
            self.current_controller = EGISystemController(egi.sheet, canvas_bounds)
            
            # Add EGI content to controller
            self.add_egi_to_controller(egi)
            
            # Generate spatial layout
            spatial_layout = self.current_controller.spatial_correspondence.generate_complete_spatial_layout()
            
            # Render the EGI
            self.render_egi_layout(spatial_layout)
            
            self.status_text.append(f"✅ Successfully loaded and rendered EGI")
            
        except Exception as e:
            self.status_text.append(f"❌ Error loading EGI: {str(e)}")
            import traceback
            self.status_text.append(f"Traceback: {traceback.format_exc()}")
            
    def add_egi_to_controller(self, egi):
        """Add parsed EGI content to the controller using correct EGIF contexts."""
        sheet_id = egi.sheet

        # 1) Create all cut areas with proper parent contexts
        created_cuts = set()
        remaining = {c.id for c in egi.Cut}
        # Iterate until all cuts are created (handles nesting)
        for _ in range(0, 10):  # safety bound for nesting depth
            progressed = False
            to_process = list(remaining)
            for cut_id in to_process:
                parent_ctx = egi.get_context(cut_id)
                # Parent exists if it's the sheet or already created cut
                if parent_ctx == sheet_id or parent_ctx in created_cuts:
                    self.current_controller.create_negation(cut_id, parent_ctx)
                    created_cuts.add(cut_id)
                    remaining.remove(cut_id)
                    progressed = True
            if not progressed:
                break

        # 2) Add vertices to their actual contexts
        for vertex in egi.V:
            v_ctx = egi.get_context(vertex.id)
            self.current_controller.add_vertex_to_area(vertex.id, v_ctx)

        # 3) Add edges (predicates) to their actual contexts
        for edge in egi.E:
            e_ctx = egi.get_context(edge.id)
            relation_name = egi.get_relation_name(edge.id) if hasattr(egi, 'get_relation_name') else egi.rel.get(edge.id, edge.id)
            self.current_controller.add_predicate_to_area(edge.id, relation_name, e_ctx)

        # 4) Bind ν mappings (ligatures) using the predicate's context
        for edge_id, vertex_sequence in egi.nu.items():
            e_ctx = egi.get_context(edge_id)
            for vertex_id in vertex_sequence:
                self.current_controller.bind_vertex_to_predicate(vertex_id, edge_id, e_ctx)
                
    def render_egi_layout(self, layout: Dict[str, Any]):
        """Render the EGI layout to the graphics scene."""
        # Process rendering commands directly
        commands = layout.get('rendering_commands', [])
        
        for command in commands:
            command_type = command.get('type')
            
            if command_type == 'render_vertex':
                self.render_egi_vertex(command)
            elif command_type == 'render_predicate':
                self.render_egi_predicate(command)
            elif command_type == 'render_cut':
                self.render_egi_cut(command)
            elif command_type == 'render_ligature':
                self.render_egi_ligature(command)
                
        # Fit view to content
        self.graphics_view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
    def render_egi_vertex(self, command):
        """Render EGI vertex as Peircean spot (no ID label)."""
        from PyQt6.QtWidgets import QGraphicsEllipseItem
        from PyQt6.QtGui import QPen, QBrush, QColor
        
        position = command.get('position', {})
        # vertex_id available in command but intentionally not displayed
        
        x = position.get('x', 100)
        y = position.get('y', 100)
        
        # Draw vertex as small black spot (8px diameter)
        spot = QGraphicsEllipseItem(x - 4, y - 4, 8, 8)
        spot.setPen(QPen(QColor(0, 0, 0), 2))
        spot.setBrush(QBrush(QColor(0, 0, 0)))
        self.scene.addItem(spot)
        
    def render_egi_predicate(self, command):
        """Render EGI predicate with Peircean styling."""
        from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
        from PyQt6.QtGui import QPen, QBrush, QColor, QFont
        
        position = command.get('position', {})
        edge_id = command.get('edge_id', 'predicate')
        
        x = position.get('x', 100)
        y = position.get('y', 100)
        
        # Get relation name from controller
        relation_name = edge_id  # Default fallback
        try:
            for area_id, area in self.current_controller.logical_system.logical_areas.items():
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
        
        # Determine background color based on Peirce shading convention
        # Even depth (sheet=0) unshaded; odd depth shaded light gray
        logical_area = command.get('logical_area', None)
        def area_depth(area_id: str) -> int:
            try:
                ls = self.current_controller.logical_system
                depth = 0
                cur = area_id
                while cur and cur in ls.logical_areas:
                    parent = ls.logical_areas[cur].parent_area
                    if not parent:
                        break
                    depth += 1
                    cur = parent
                return depth
            except Exception:
                return 0
        depth = area_depth(logical_area) if logical_area else 0
        bg_color = QColor(240, 240, 240) if (depth % 2 == 1) else QColor(255, 255, 255)
        
        # Create invisible tight boundary rectangle
        rect = QGraphicsRectItem(x - text_width/2 - 2, y - text_height/2 - 1, 
                                text_width + 4, text_height + 2)
        rect.setPen(QPen(QColor(0, 0, 0, 0), 0))  # Invisible boundary
        rect.setBrush(QBrush(bg_color))
        self.scene.addItem(rect)
        
        # Position text centered
        label.setPos(x - text_width/2, y - text_height/2)
        self.scene.addItem(label)
        
    def render_egi_cut(self, command):
        """Render EGI cut with Peircean thin solid line and rounded corners."""
        from PyQt6.QtWidgets import QGraphicsPathItem
        from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath
        from PyQt6.QtCore import QRectF
        
        bounds = command.get('bounds', {})
        cut_id = command.get('cut_id')
        
        # Draw cut boundary with thin solid line and rounded corners
        x = bounds.get('x', 0)
        y = bounds.get('y', 0)
        width = bounds.get('width', 100)
        height = bounds.get('height', 100)
        
        # Create thin solid pen for cut boundary (1px)
        pen = QPen(QColor(0, 0, 0), 1)
        
        # Create rounded rectangle path
        path = QPainterPath()
        rect_f = QRectF(x, y, width, height)
        path.addRoundedRect(rect_f, 10, 10)  # 10px corner radius
        
        # Create path item
        path_item = QGraphicsPathItem(path)
        path_item.setPen(pen)
        
        # Peirce shading: shade only odd-depth areas
        def area_depth(area_id: str) -> int:
            try:
                ls = self.current_controller.logical_system
                depth = 0
                cur = area_id
                while cur and cur in ls.logical_areas:
                    parent = ls.logical_areas[cur].parent_area
                    if not parent:
                        break
                    depth += 1
                    cur = parent
                return depth
            except Exception:
                return 0
        depth = area_depth(cut_id) if cut_id else 1
        brush_color = QColor(240, 240, 240, 100) if (depth % 2 == 1) else QColor(255, 255, 255, 0)
        path_item.setBrush(QBrush(brush_color))
        self.scene.addItem(path_item)
        
    def render_egi_ligature(self, command):
        """Render EGI ligature with Peircean heavy line styling."""
        from PyQt6.QtWidgets import QGraphicsLineItem
        from PyQt6.QtGui import QPen, QColor
        
        path_points = command.get('path_points', [])
        
        if len(path_points) < 2:
            return
        
        # Create heavy line for ligature (3px)
        pen = QPen(QColor(0, 0, 0), 3)
        
        # Draw line segments between consecutive points
        for i in range(len(path_points) - 1):
            start_point = path_points[i]
            end_point = path_points[i + 1]
            
            line = QGraphicsLineItem(start_point[0], start_point[1], 
                                   end_point[0], end_point[1])
            line.setPen(pen)
            self.scene.addItem(line)


def main():
    """Main function to run the corpus EGI test system."""
    app = QApplication(sys.argv)
    
    window = CorpusEGITestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
