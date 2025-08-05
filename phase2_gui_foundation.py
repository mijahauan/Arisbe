#!/usr/bin/env python3
"""
Phase 2 GUI Foundation - Working EGI Rendering for Parallel Development

This creates a functioning GUI that renders EGI diagrams, providing the foundation
for Phase 2 selection overlays and context-sensitive actions development.

Uses the completed Phase 1d pipeline: EGIF → EGI → Layout → Visual Rendering
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Set
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Phase 1d Foundation - Complete pipeline
from egif_parser_dau import EGIFParser
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from layout_engine_clean import SpatialPrimitive, LayoutResult
from egdf_parser import EGDFParser

# GUI Components
try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                   QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                                   QSplitter, QFrame, QComboBox, QStatusBar)
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
    from PySide6.QtCore import Qt, QPointF, QRectF, QTimer
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    print("PySide6 not available - install with: pip install PySide6")

class EGDiagramWidget(QWidget):
    """Widget for rendering EG diagrams with interaction support."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        # Current diagram state
        self.egi: Optional[RelationalGraphWithCuts] = None
        self.layout_result = None
        self.spatial_primitives: List[SpatialPrimitive] = []
        
        # Selection state for Phase 2 development
        self.selected_elements: Set[str] = set()
        self.hover_element: Optional[str] = None
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
    def set_diagram(self, egi: RelationalGraphWithCuts, spatial_primitives: List[SpatialPrimitive]):
        """Set the diagram to render."""
        self.egi = egi
        self.spatial_primitives = spatial_primitives
        self.update()  # Trigger repaint
        
    def clear_diagram(self):
        """Clear the current diagram."""
        self.egi = None
        self.spatial_primitives = []
        self.selected_elements.clear()
        self.hover_element = None
        self.update()
        
    def paintEvent(self, event):
        """Render the EG diagram using Dau's conventions."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.egi or not self.spatial_primitives:
            # Draw placeholder text
            painter.setPen(QColor(150, 150, 150))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "Enter EGIF above to render diagram")
            return
            
        # Render spatial primitives following Dau's conventions
        for primitive in self.spatial_primitives:
            self._render_primitive(painter, primitive)
            
        # Render selection overlays (Phase 2 foundation)
        self._render_selection_overlays(painter)
            
    def _render_primitive(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render a single spatial primitive following Dau's conventions."""
        element_id = primitive.element_id
        element_type = primitive.element_type
        position = primitive.position
        bounds = primitive.bounds
        
        # Check if element is selected or hovered
        is_selected = element_id in self.selected_elements
        is_hovered = element_id == self.hover_element
        
        if element_type == "vertex":
            self._render_vertex(painter, element_id, position, is_selected, is_hovered)
        elif element_type == "predicate":
            self._render_edge(painter, element_id, position, bounds, is_selected, is_hovered)
        elif element_type == "edge":
            self._render_identity_line(painter, element_id, position, bounds, is_selected, is_hovered)
        elif element_type == "cut":
            self._render_cut(painter, element_id, bounds, is_selected, is_hovered)
            
    def _render_vertex(self, painter: QPainter, element_id: str, position: Tuple[float, float], 
                      is_selected: bool, is_hovered: bool):
        """Render vertex as heavy identity spot with constant name (Dau's convention)."""
        x, y = position
        
        # Heavy identity spot - prominent and dark
        radius = 4.0 if not is_hovered else 5.0
        color = QColor(0, 0, 0) if not is_selected else QColor(0, 100, 200)
        
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(x, y), radius, radius)
        
        # FIX 1: Render constant name at vertex if it exists
        if self.egi:
            vertex = next((v for v in self.egi.V if v.id == element_id), None)
            if vertex and vertex.label and not vertex.is_generic:
                # Render constant name below the vertex spot
                painter.setPen(QPen(color, 1))
                painter.setFont(QFont("Times", 10))
                text_rect = painter.fontMetrics().boundingRect(vertex.label)
                text_x = x - text_rect.width() / 2
                text_y = y + radius + text_rect.height() + 2
                painter.drawText(QPointF(text_x, text_y), vertex.label)
        
    def _render_edge(self, painter: QPainter, element_id: str, position: Tuple[float, float],
                    bounds: Tuple[float, float, float, float], is_selected: bool, is_hovered: bool):
        """Render edge as predicate following Dau's conventions."""
        if not self.egi:
            return
            
        x, y = position
        x1, y1, x2, y2 = bounds
        
        # Get relation name
        relation_name = self.egi.rel.get(element_id, f"R{element_id[:4]}")
        
        # Predicate text rendering
        color = QColor(0, 0, 0) if not is_selected else QColor(0, 100, 200)
        painter.setFont(QFont("Times", 11))
        text_rect = painter.fontMetrics().boundingRect(relation_name)
        
        # Minimal padding - ONLY to prevent cuts from running through text
        text_padding = 2  # Minimal padding for cut avoidance only
        
        # Draw predicate text (no decorative background)
        painter.setPen(QPen(color, 1))
        painter.setBrush(QBrush(Qt.NoBrush))
        text_x = x - text_rect.width() / 2
        text_y = y + text_rect.height() / 4  # Adjust for baseline
        painter.drawText(QPointF(text_x, text_y), relation_name)
        
        # Draw connection lines to vertices (heavy identity lines)
        if element_id in self.egi.nu:
            vertex_sequence = self.egi.nu[element_id]
            for i, vertex_id in enumerate(vertex_sequence):
                # Find vertex position
                vertex_primitive = next((p for p in self.spatial_primitives 
                                       if p.element_id == vertex_id), None)
                if vertex_primitive:
                    vx, vy = vertex_primitive.position
                    
                    # Find the closest point on predicate boundary to minimize line length
                    pred_center_x, pred_center_y = x, y
                    
                    # Calculate direction from predicate center to vertex
                    dx = vx - pred_center_x
                    dy = vy - pred_center_y
                    distance = (dx*dx + dy*dy)**0.5
                    
                    if distance > 0:
                        # Normalize direction
                        dx_norm = dx / distance
                        dy_norm = dy / distance
                        
                        # Find closest boundary point on predicate text boundary
                        # Use text dimensions + minimal padding for boundary calculation
                        text_half_width = text_rect.width() / 2 + text_padding
                        text_half_height = text_rect.height() / 2 + text_padding
                        
                        # Calculate intersection with rectangular boundary
                        # Find which edge of the rectangle the line intersects
                        if abs(dx_norm) > abs(dy_norm):
                            # Line is more horizontal - intersect with left/right edge
                            hook_x = pred_center_x + (text_half_width if dx_norm > 0 else -text_half_width)
                            hook_y = pred_center_y + dy_norm * text_half_width / abs(dx_norm)
                        else:
                            # Line is more vertical - intersect with top/bottom edge
                            hook_x = pred_center_x + dx_norm * text_half_height / abs(dy_norm)
                            hook_y = pred_center_y + (text_half_height if dy_norm > 0 else -text_half_height)
                        
                        # Heavy line of identity (Dau's convention)
                        line_width = 3.0 if not is_selected else 4.0
                        painter.setPen(QPen(color, line_width))
                        painter.drawLine(QPointF(hook_x, hook_y), QPointF(vx, vy))
                    
    def _render_identity_line(self, painter: QPainter, element_id: str, position: Tuple[float, float],
                             bounds: Tuple[float, float, float, float], is_selected: bool, is_hovered: bool):
        """Render heavy identity line connecting vertices to predicates (Dau's convention).
        
        NOTE: Currently disabled to prevent duplicate line rendering.
        Heavy identity lines are drawn by _render_edge() method when rendering predicates.
        """
        # DISABLED: Lines are already drawn by _render_edge() method
        # This prevents the double-line rendering issue
        return
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                    
    def _render_cut(self, painter: QPainter, element_id: str, 
                   bounds: Tuple[float, float, float, float], is_selected: bool, is_hovered: bool):
        """Render cut as fine-drawn closed curve (Dau's convention)."""
        x1, y1, x2, y2 = bounds
        
        # Fine cut boundary
        color = QColor(0, 0, 0) if not is_selected else QColor(0, 100, 200)
        line_width = 1.0 if not is_hovered else 1.5
        painter.setPen(QPen(color, line_width))
        painter.setBrush(QBrush(Qt.NoBrush))
        
        # Draw as oval (fine-drawn closed curve)
        painter.drawEllipse(QRectF(x1, y1, x2 - x1, y2 - y1))
        
    def _render_selection_overlays(self, painter: QPainter):
        """Render selection overlays - foundation for Phase 2."""
        if not self.selected_elements:
            return
            
        # Simple selection highlight for now
        painter.setPen(QPen(QColor(0, 100, 200, 100), 2, Qt.DashLine))
        painter.setBrush(QBrush(Qt.NoBrush))
        
        for element_id in self.selected_elements:
            primitive = next((p for p in self.spatial_primitives 
                            if p.element_id == element_id), None)
            if primitive:
                x1, y1, x2, y2 = primitive.bounds
                painter.drawRect(QRectF(x1 - 5, y1 - 5, x2 - x1 + 10, y2 - y1 + 10))
                
    def mousePressEvent(self, event):
        """Handle mouse clicks for selection (Phase 2 foundation)."""
        if event.button() == Qt.LeftButton:
            # Find element at click position
            clicked_element = self._find_element_at_position(event.position().x(), event.position().y())
            
            if clicked_element:
                if event.modifiers() & Qt.ControlModifier:
                    # Multi-select with Ctrl
                    if clicked_element in self.selected_elements:
                        self.selected_elements.remove(clicked_element)
                    else:
                        self.selected_elements.add(clicked_element)
                else:
                    # Single select
                    self.selected_elements = {clicked_element}
            else:
                # Click on empty area - clear selection
                self.selected_elements.clear()
                
            self.update()
            
    def mouseMoveEvent(self, event):
        """Handle mouse movement for hover effects."""
        hover_element = self._find_element_at_position(event.position().x(), event.position().y())
        
        if hover_element != self.hover_element:
            self.hover_element = hover_element
            self.update()
            
    def _find_element_at_position(self, x: float, y: float) -> Optional[str]:
        """Find element at given position - foundation for Phase 2 interaction."""
        for primitive in self.spatial_primitives:
            x1, y1, x2, y2 = primitive.bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                return primitive.element_id
        return None

class Phase2GUIFoundation(QMainWindow):
    """Main window for Phase 2 GUI foundation with working EGI rendering."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe Phase 2 GUI Foundation - EGI Rendering")
        self.setGeometry(100, 100, 1000, 700)
        
        # Initialize components
        self.layout_engine = GraphvizLayoutEngine()
        self.egdf_parser = EGDFParser()
        
        # Initialize corpus loader
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
            from corpus_loader import get_corpus_loader
            self.corpus_loader = get_corpus_loader()
            print(f"✓ Corpus loaded with {len(self.corpus_loader.examples)} examples")
        except Exception as e:
            print(f"Warning: Could not load corpus: {e}")
            self.corpus_loader = None
        
        # Sample EGIF expressions for testing
        self.sample_egifs = [
            '(Human "Socrates")',
            '(Human "Socrates") (Mortal "Socrates")',
            '*x (Human x) ~[ (Mortal x) ]',
            '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            '*x *y (Loves x y) ~[ (Happy x) ]',
            '*x ~[ ~[ (P x) ] ]',  # Double cut
        ]
        
        self.setup_ui()
        self.load_sample_diagram()
        
    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Top controls
        controls_layout = QHBoxLayout()
        
        # Corpus browser section
        if self.corpus_loader:
            controls_layout.addWidget(QLabel("Corpus:"))
            self.corpus_combo = QComboBox()
            self.corpus_combo.addItem("Select from corpus...")
            self._populate_corpus_dropdown()
            controls_layout.addWidget(self.corpus_combo)
            
            import_btn = QPushButton("Import")
            import_btn.clicked.connect(self.import_corpus_example)
            controls_layout.addWidget(import_btn)
            
            # Separator
            controls_layout.addWidget(QLabel("|"))
        
        # Manual EGIF input
        controls_layout.addWidget(QLabel("EGIF:"))
        self.egif_combo = QComboBox()
        self.egif_combo.setEditable(True)
        self.egif_combo.addItems(self.sample_egifs)
        self.egif_combo.currentTextChanged.connect(self.on_egif_changed)
        controls_layout.addWidget(self.egif_combo)
        
        # Render button
        render_btn = QPushButton("Render Diagram")
        render_btn.clicked.connect(self.render_diagram)
        controls_layout.addWidget(render_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_diagram)
        controls_layout.addWidget(clear_btn)
        
        main_layout.addLayout(controls_layout)
        
        # Splitter for diagram and info
        splitter = QSplitter(Qt.Horizontal)
        
        # Diagram widget
        self.diagram_widget = EGDiagramWidget()
        splitter.addWidget(self.diagram_widget)
        
        # Info panel
        info_frame = QFrame()
        info_frame.setMaximumWidth(300)
        info_layout = QVBoxLayout(info_frame)
        
        info_layout.addWidget(QLabel("EGI Structure:"))
        self.egi_info = QTextEdit()
        self.egi_info.setMaximumHeight(150)
        self.egi_info.setReadOnly(True)
        info_layout.addWidget(self.egi_info)
        
        info_layout.addWidget(QLabel("Selection Info:"))
        self.selection_info = QTextEdit()
        self.selection_info.setMaximumHeight(100)
        self.selection_info.setReadOnly(True)
        info_layout.addWidget(self.selection_info)
        
        info_layout.addWidget(QLabel("Phase 2 Development:"))
        phase2_info = QTextEdit()
        phase2_info.setPlainText(
            "Foundation Ready:\n"
            "✓ EGI → Visual rendering\n"
            "✓ Basic selection system\n"
            "✓ Hover effects\n"
            "✓ Mouse interaction\n\n"
            "Next: Selection overlays\n"
            "Context-sensitive actions\n"
            "Dynamic effects"
        )
        phase2_info.setReadOnly(True)
        info_layout.addWidget(phase2_info)
        
        splitter.addWidget(info_frame)
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Phase 2 GUI Foundation Ready")
        
        # Timer for updating selection info
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_selection_info)
        self.update_timer.start(500)  # Update every 500ms
        
    def on_egif_changed(self, text):
        """Handle EGIF input change."""
        if text.strip():
            self.render_diagram()
            
    def render_diagram(self):
        """Render diagram from current EGIF using Phase 1d pipeline."""
        egif_text = self.egif_combo.currentText().strip()
        
        if not egif_text:
            self.status_bar.showMessage("Enter EGIF to render")
            return
            
        try:
            # Phase 1d Pipeline: EGIF → EGI → Layout → Visual
            
            # 1. Parse EGIF to EGI
            egif_parser = EGIFParser(egif_text)
            egi = egif_parser.parse()
            
            # 2. Generate layout using the proper layout engine
            layout_result = self.layout_engine.create_layout_from_graph(egi)
            print(f"DEBUG: Layout result type: {type(layout_result)}")
            print(f"DEBUG: Layout result attributes: {dir(layout_result)}")
            
            # 3. Convert layout result to spatial primitives list
            # GraphvizLayoutEngine returns LayoutResult with primitives dict
            if hasattr(layout_result, 'primitives'):
                spatial_primitives = list(layout_result.primitives.values())
                print(f"DEBUG: Found {len(spatial_primitives)} spatial primitives")
                for i, prim in enumerate(spatial_primitives[:3]):  # Show first 3
                    print(f"DEBUG: Primitive {i}: {prim.element_id} ({prim.element_type}) at {prim.position}")
            else:
                print(f"DEBUG: No 'primitives' attribute found in layout_result")
                spatial_primitives = []
            
            # 4. Render in GUI
            self.diagram_widget.set_diagram(egi, spatial_primitives)
            
            # Update info panel
            self.update_egi_info(egi)
            
            self.status_bar.showMessage(f"Rendered: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
            
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
            print(f"Rendering error: {e}")
            
    def clear_diagram(self):
        """Clear the current diagram."""
        self.diagram_widget.clear_diagram()
        self.egi_info.clear()
        self.selection_info.clear()
        self.status_bar.showMessage("Diagram cleared")
        
    def update_egi_info(self, egi: RelationalGraphWithCuts):
        """Update EGI structure information."""
        info_text = f"Vertices: {len(egi.V)}\n"
        info_text += f"Edges: {len(egi.E)}\n"
        info_text += f"Cuts: {len(egi.Cut)}\n\n"
        
        info_text += "Relations:\n"
        for edge_id, relation_name in egi.rel.items():
            vertex_seq = egi.nu.get(edge_id, ())
            info_text += f"  {relation_name}: {vertex_seq}\n"
            
        self.egi_info.setPlainText(info_text)
        
    def update_selection_info(self):
        """Update selection information."""
        selected = self.diagram_widget.selected_elements
        hover = self.diagram_widget.hover_element
        
        info_text = f"Selected: {len(selected)} elements\n"
        if selected:
            info_text += f"  {', '.join(list(selected)[:3])}\n"
            if len(selected) > 3:
                info_text += f"  ... and {len(selected) - 3} more\n"
                
        if hover:
            info_text += f"\nHover: {hover}"
            
        self.selection_info.setPlainText(info_text)
        
    def _populate_corpus_dropdown(self):
        """Populate the corpus dropdown with available examples."""
        if not self.corpus_loader:
            return
        
        # Group examples by category
        categories = {}
        for example in self.corpus_loader.examples.values():
            category = example.category
            if category not in categories:
                categories[category] = []
            categories[category].append(example)
        
        # Add examples organized by category
        for category, examples in sorted(categories.items()):
            for example in examples:
                display_text = f"[{category}] {example.title}"
                self.corpus_combo.addItem(display_text, example.id)
    
    def import_corpus_example(self):
        """Import the selected corpus example into the EGIF input."""
        if not self.corpus_loader or self.corpus_combo.currentIndex() == 0:
            return
        
        example_id = self.corpus_combo.currentData()
        if not example_id:
            return
        
        example = self.corpus_loader.get_example(example_id)
        if example and example.egif_content:
            self.egif_combo.setCurrentText(example.egif_content)
            # Auto-render the imported example
            self.render_diagram()
            
            print(f"✓ Imported corpus example: {example.title}")
            print(f"  EGIF: {example.egif_content}")
            print(f"  Description: {example.description}")
        else:
            print(f"Warning: No EGIF content found for {example_id}")
    
    def load_sample_diagram(self):
        """Load the first sample diagram on startup."""
        if self.sample_egifs:
            self.egif_combo.setCurrentText(self.sample_egifs[0])
            self.render_diagram()

def main():
    """Run the Phase 2 GUI foundation."""
    if not PYSIDE6_AVAILABLE:
        print("PySide6 is required for the GUI. Install with: pip install PySide6")
        return
        
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = Phase2GUIFoundation()
    window.show()
    
    print("Phase 2 GUI Foundation Running:")
    print("✓ EGI → Visual rendering pipeline working")
    print("✓ Basic selection and interaction implemented")
    print("✓ Foundation ready for Phase 2 development")
    print("✓ Try different EGIF expressions from the dropdown")
    print("✓ Corpus integration with import functionality")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
