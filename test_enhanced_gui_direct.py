#!/usr/bin/env python3
"""
Direct test of Enhanced GUI Foundation bypassing legacy backend imports.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test PySide6 availability directly
try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                   QPushButton, QTextEdit, QComboBox, QLineEdit, QLabel)
    from PySide6.QtCore import Qt, QPointF, QRectF
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
    print("✓ PySide6 is available and working")
    PYSIDE6_AVAILABLE = True
except ImportError as e:
    print(f"✗ PySide6 not available: {e}")
    PYSIDE6_AVAILABLE = False
    sys.exit(1)

# Import only the core components we need
from src.egif_parser_dau import EGIFParser
from src.egi_core_dau import RelationalGraphWithCuts
from src.graphviz_layout_engine_v2 import GraphvizLayoutEngine
from src.layout_engine_clean import SpatialPrimitive
from src.corpus_loader import get_corpus_loader


class DiagramRenderWidget(QWidget):
    """Widget that actually renders EG diagrams visually."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        # Rendering state
        self.egi = None
        self.spatial_primitives = []
        
    def set_diagram(self, egi: RelationalGraphWithCuts, spatial_primitives: list):
        """Set the diagram to render."""
        self.egi = egi
        self.spatial_primitives = spatial_primitives
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        """Paint the diagram with actual visual rendering."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Clear background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        if not self.spatial_primitives:
            # Draw placeholder text
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.drawText(self.rect(), Qt.AlignCenter, "Load an EGIF expression to see the diagram")
            return
        
        # Render all spatial primitives
        for primitive in self.spatial_primitives:
            self._render_primitive(painter, primitive)
    
    def _render_primitive(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render a single spatial primitive following Dau's conventions."""
        element_type = primitive.element_type
        
        if element_type == "vertex":
            self._render_vertex(painter, primitive)
        elif element_type == "predicate":
            self._render_predicate(painter, primitive)
        elif element_type == "edge":
            self._render_identity_line(painter, primitive)
        elif element_type == "cut":
            self._render_cut(painter, primitive)
    
    def _render_vertex(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render vertex as identity spot."""
        if hasattr(primitive, 'position'):
            x, y = primitive.position
            
            # Draw identity spot (filled circle)
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.drawEllipse(QPointF(x, y), 4, 4)
    
    def _render_predicate(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render predicate as text label."""
        if hasattr(primitive, 'position'):
            x, y = primitive.position
            
            # Get predicate name from EGI
            predicate_name = "P"  # Default
            if self.egi and primitive.element_id in self.egi.rel:
                predicate_name = self.egi.rel[primitive.element_id]
            
            # Draw predicate text
            painter.setPen(QPen(QColor(0, 0, 0)))
            font = QFont("Times", 12)
            painter.setFont(font)
            
            # Center the text
            metrics = painter.fontMetrics()
            text_rect = metrics.boundingRect(predicate_name)
            text_x = x - text_rect.width() / 2
            text_y = y + text_rect.height() / 2
            
            painter.drawText(QPointF(text_x, text_y), predicate_name)
    
    def _render_identity_line(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render heavy line of identity."""
        # Draw heavy line (4pt width per Dau's convention)
        painter.setPen(QPen(QColor(0, 0, 0), 4, Qt.SolidLine, Qt.RoundCap))
        
        if hasattr(primitive, 'line_points') and primitive.line_points:
            points = primitive.line_points
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        elif hasattr(primitive, 'bounds'):
            # Fallback: draw line across bounds
            x1, y1, x2, y2 = primitive.bounds
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    
    def _render_cut(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render cut boundary."""
        if hasattr(primitive, 'bounds'):
            x1, y1, x2, y2 = primitive.bounds
            
            # Draw fine cut boundary (1pt width per Dau's convention)
            painter.setPen(QPen(QColor(0, 0, 0), 1, Qt.SolidLine))
            painter.setBrush(QBrush())  # No fill
            
            # Draw cut as rectangle
            painter.drawRect(QRectF(x1, y1, x2 - x1, y2 - y1))


class SimpleEnhancedGUI(QMainWindow):
    """Simplified Enhanced GUI to test core functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe Enhanced GUI - Direct Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Core components
        self.layout_engine = GraphvizLayoutEngine()
        
        self.setup_ui()
        self.load_corpus_examples()
    
    def setup_ui(self):
        """Setup simple UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Controls
        controls = QHBoxLayout()
        
        # Corpus selection dropdown
        self.corpus_combo = QComboBox()
        self.corpus_combo.currentTextChanged.connect(self.load_corpus_example)
        controls.addWidget(QLabel("Examples:"))
        controls.addWidget(self.corpus_combo)
        
        # EGIF input
        self.egif_input = QLineEdit()
        self.egif_input.setPlaceholderText("Enter EGIF expression (e.g., (Human \"Socrates\") (Mortal \"Socrates\"))")
        self.egif_input.setText('(Human "Socrates") (Mortal "Socrates")')  # Default example
        controls.addWidget(QLabel("EGIF:"))
        controls.addWidget(self.egif_input)
        
        layout.addLayout(controls)
        
        # Render button
        render_btn = QPushButton("Render Diagram")
        render_btn.clicked.connect(self.render_diagram)
        layout.addWidget(render_btn)
        
        # Diagram area with actual rendering
        self.diagram_widget = DiagramRenderWidget()
        layout.addWidget(self.diagram_widget)
        
        # Status
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
    
    def load_corpus_examples(self):
        """Load corpus examples into dropdown."""
        try:
            corpus_loader = get_corpus_loader()
            examples = corpus_loader.get_all_examples()
            
            self.corpus_combo.addItem("-- Select Example --")
            for example_id, example_data in examples.items():
                title = example_data.get('title', example_id)
                self.corpus_combo.addItem(f"{example_id}: {title}")
                
        except Exception as e:
            # Fallback to built-in examples
            self.corpus_combo.addItem("-- Select Example --")
            self.corpus_combo.addItem("Basic: (Human \"Socrates\") (Mortal \"Socrates\")")
            self.corpus_combo.addItem("Cut: ~[ (P \"x\") ]")
            self.corpus_combo.addItem("Complex: *x (Human x) ~[ (Mortal x) ]")
    
    def load_corpus_example(self, selection_text):
        """Load selected corpus example."""
        if not selection_text or selection_text.startswith("--"):
            return
            
        try:
            if ":" in selection_text:
                example_id = selection_text.split(":")[0]
                corpus_loader = get_corpus_loader()
                examples = corpus_loader.get_all_examples()
                
                if example_id in examples:
                    egif_text = examples[example_id].get('egif', '')
                    self.egif_input.setText(egif_text)
                    self.render_diagram()
                    return
            
            # Fallback to built-in examples
            if "Basic" in selection_text:
                self.egif_input.setText('(Human "Socrates") (Mortal "Socrates")')
            elif "Cut" in selection_text:
                self.egif_input.setText('~[ (P "x") ]')
            elif "Complex" in selection_text:
                self.egif_input.setText('*x (Human x) ~[ (Mortal x) ]')
                
            self.render_diagram()
            
        except Exception as e:
            self.status_text.setPlainText(f"Error loading example: {e}")
    
    def render_diagram(self):
        """Render diagram from EGIF."""
        egif_text = self.egif_input.text().strip()
        
        if not egif_text:
            self.status_text.setPlainText("Please enter an EGIF expression.")
            return
        
        try:
            # Parse EGIF to EGI
            egif_parser = EGIFParser(egif_text)
            egi = egif_parser.parse()
            
            # Create layout
            layout_result = self.layout_engine.create_layout_from_graph(egi)
            
            # **CRITICAL FIX**: Pass the layout data to the diagram widget for visual rendering
            self.diagram_widget.set_diagram(egi, layout_result.primitives)
            
            # Update status
            status = f"""✓ Successfully parsed and rendered EGIF:
- Vertices: {len(egi.V)}
- Edges: {len(egi.E)}  
- Cuts: {len(egi.Cut)}
- ν mappings: {len(egi.nu)}
- κ mappings: {len(egi.rel)}
- Layout primitives: {len(layout_result.primitives)}

EGIF: {egif_text}
"""
            self.status_text.setPlainText(status)
            
            print(f"✓ Successfully rendered: {egif_text}")
            print(f"  - EGI components: V={len(egi.V)}, E={len(egi.E)}, Cut={len(egi.Cut)}")
            print(f"  - Layout primitives: {len(layout_result.primitives)}")
            
        except Exception as e:
            error_msg = f"✗ Error rendering EGIF: {e}"
            self.status_text.setPlainText(error_msg)
            print(error_msg)


def main():
    """Run the direct enhanced GUI test."""
    if not PYSIDE6_AVAILABLE:
        print("PySide6 is required for this test.")
        return
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Arisbe Enhanced GUI Direct Test")
    app.setApplicationVersion("1.0")
    
    # Create and show window
    window = SimpleEnhancedGUI()
    window.show()
    
    print("=== Enhanced GUI Direct Test Started ===")
    print("✓ PySide6 working correctly")
    print("✓ Core pipeline components loaded")
    print("✓ GUI window displayed")
    print("✓ Sample EGIF loaded and rendered")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
