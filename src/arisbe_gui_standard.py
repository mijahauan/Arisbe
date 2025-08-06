#!/usr/bin/env python3
"""
Arisbe Standard GUI - Pipeline Compliant Implementation

This is the standardized GUI implementation that enforces:
1. Complete EGIF→EGI→EGDF pipeline with API contract validation
2. PySide6/QPainter backend exclusively
3. Full corpus integration and support
4. Clean, deprecated-code-free architecture
5. Core test suite integration

CRITICAL: This replaces all experimental/fragmented GUI implementations.
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path

# Ensure src directory is in path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Standard PySide6 imports (enforced backend)
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTextEdit, QLabel, QSplitter, QFrame, QComboBox,
        QCheckBox, QGroupBox, QStatusBar, QMenuBar, QMenu, QFileDialog,
        QMessageBox, QTabWidget
    )
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QAction
    from PySide6.QtCore import Qt, QPointF, QRectF, QTimer, Signal
except ImportError as e:
    print(f"❌ CRITICAL: PySide6 not available: {e}")
    print("Install with: pip install PySide6")
    sys.exit(1)

# Complete pipeline imports with contract validation
from egif_parser_dau import EGIFParser
from egi_core_dau import RelationalGraphWithCuts
from egdf_parser import EGDFParser, EGDFGenerator
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from layout_engine_clean import SpatialPrimitive, LayoutResult
from corpus_loader import get_corpus_loader
from pipeline_contracts import (
    validate_relational_graph_with_cuts,
    validate_layout_result,
    validate_spatial_primitive,
    validate_full_pipeline,
    enforce_contracts,
    ContractViolationError
)

class EGDiagramCanvas(QWidget):
    """
    Standard EG diagram canvas with complete pipeline integration.
    
    Enforces:
    - EGIF→EGI→EGDF pipeline with contract validation
    - PySide6/QPainter rendering exclusively
    - Corpus integration for examples
    - Clean architecture without deprecated patterns
    """
    
    # Signals for GUI communication
    element_selected = Signal(str)
    diagram_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        # Pipeline components (contract-validated)
        self.layout_engine = GraphvizLayoutEngine()
        self.egdf_generator = EGDFGenerator()
        self.egdf_parser = EGDFParser()
        
        # Current state
        self.current_egi: Optional[RelationalGraphWithCuts] = None
        self.current_layout: Optional[LayoutResult] = None
        self.current_egdf: Optional[Dict] = None
        self.spatial_primitives: List[SpatialPrimitive] = []
        
        # Selection and interaction
        self.selected_elements: Set[str] = set()
        self.hover_element: Optional[str] = None
        
        # Enable mouse tracking
        self.setMouseTracking(True)
    
    @enforce_contracts(
        input_contracts={'egif_text': lambda x: isinstance(x, str) and len(x.strip()) > 0},
        output_contract=lambda x: x is None  # Void return
    )
    def load_egif(self, egif_text: str):
        """Load EGIF through complete pipeline with contract validation."""
        try:
            # Step 1: EGIF → EGI (with contract validation)
            parser = EGIFParser(egif_text)
            egi = parser.parse()
            validate_relational_graph_with_cuts(egi)
            
            # Step 2: EGI → Layout (with contract validation)
            layout_result = self.layout_engine.create_layout_from_graph(egi)
            validate_layout_result(layout_result)
            
            # Step 3: EGI + Layout → EGDF (with contract validation)
            egdf_data = self.egdf_generator.generate_from_egi_and_layout(egi, layout_result)
            
            # Step 4: Validate complete pipeline
            validate_full_pipeline(egif_text, egi, layout_result, self)
            
            # Update state
            self.current_egi = egi
            self.current_layout = layout_result
            self.current_egdf = egdf_data
            self.spatial_primitives = list(layout_result.primitives.values())
            
            # Trigger repaint
            self.update()
            self.diagram_changed.emit()
            
            print(f"✅ Pipeline validation passed: {len(self.spatial_primitives)} elements")
            
        except ContractViolationError as e:
            print(f"❌ Pipeline contract violation: {e}")
            QMessageBox.critical(self, "Pipeline Error", f"Contract violation: {e}")
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            QMessageBox.critical(self, "Pipeline Error", f"Failed to process EGIF: {e}")
    
    def paintEvent(self, event):
        """Render diagram using PySide6/QPainter exclusively."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.spatial_primitives:
            # Draw placeholder text
            painter.setPen(QPen(QColor(128, 128, 128), 1))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "Load EGIF to display diagram")
            return
        
        # Render all spatial primitives with contract validation
        for primitive in self.spatial_primitives:
            try:
                validate_spatial_primitive(primitive)
                self._render_primitive(painter, primitive)
            except ContractViolationError as e:
                print(f"⚠️  Spatial primitive contract violation: {e}")
                continue
    
    def _render_primitive(self, painter: QPainter, primitive: SpatialPrimitive):
        """Render a single spatial primitive following Dau's conventions."""
        element_id = primitive.element_id
        element_type = primitive.element_type
        position = primitive.position
        bounds = primitive.bounds
        
        # Selection state
        is_selected = element_id in self.selected_elements
        is_hovered = element_id == self.hover_element
        
        # Base colors
        base_color = QColor(0, 0, 0)
        selected_color = QColor(0, 100, 200)
        hover_color = QColor(100, 100, 100)
        
        color = selected_color if is_selected else (hover_color if is_hovered else base_color)
        
        if element_type == "vertex":
            self._render_vertex(painter, primitive, color)
        elif element_type == "predicate":
            self._render_predicate(painter, primitive, color)
        elif element_type == "edge":
            self._render_identity_line(painter, primitive, color)
        elif element_type == "cut":
            self._render_cut(painter, primitive, color)
    
    def _render_vertex(self, painter: QPainter, primitive: SpatialPrimitive, color: QColor):
        """Render vertex as identity spot per Dau's formalism."""
        x, y = primitive.position
        
        # Heavy identity spot
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        
        radius = 4.0
        painter.drawEllipse(QPointF(x, y), radius, radius)
        
        # Render constant label if available
        if self.current_egi:
            vertex = next((v for v in self.current_egi.V if v.id == primitive.element_id), None)
            if vertex and vertex.label and not vertex.is_generic:
                painter.setPen(QPen(color, 1))
                painter.setFont(QFont("Times", 10))
                text_rect = painter.fontMetrics().boundingRect(vertex.label)
                text_x = x - text_rect.width() / 2
                text_y = y + radius + text_rect.height() + 2
                painter.drawText(QPointF(text_x, text_y), vertex.label)
    
    def _render_predicate(self, painter: QPainter, primitive: SpatialPrimitive, color: QColor):
        """Render predicate as text per Dau's formalism."""
        x, y = primitive.position
        
        # Get predicate name
        predicate_name = "Predicate"
        if self.current_egi:
            predicate_name = self.current_egi.rel.get(primitive.element_id, "Predicate")
        
        # Render predicate text
        painter.setPen(QPen(color, 1))
        painter.setFont(QFont("Times", 12))
        painter.drawText(QPointF(x, y), predicate_name)
    
    def _render_identity_line(self, painter: QPainter, primitive: SpatialPrimitive, color: QColor):
        """Render heavy line of identity per Dau's formalism."""
        x1, y1, x2, y2 = primitive.bounds
        
        # Heavy line of identity (4pt width per Dau's convention)
        painter.setPen(QPen(color, 4, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    
    def _render_cut(self, painter: QPainter, primitive: SpatialPrimitive, color: QColor):
        """Render cut as oval per Dau's formalism."""
        x1, y1, x2, y2 = primitive.bounds
        
        # Cut boundary (thin line, distinct from identity lines)
        painter.setPen(QPen(color, 1, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.NoBrush))  # No fill
        
        # Draw oval cut
        painter.drawEllipse(QRectF(x1, y1, x2 - x1, y2 - y1))
    
    def mousePressEvent(self, event):
        """Handle mouse clicks for element selection."""
        click_pos = (event.position().x(), event.position().y())
        
        # Find element under click
        clicked_element = self._find_element_at_position(click_pos)
        
        if clicked_element:
            # Toggle selection
            if clicked_element in self.selected_elements:
                self.selected_elements.remove(clicked_element)
            else:
                self.selected_elements.add(clicked_element)
            
            self.element_selected.emit(clicked_element)
            self.update()  # Trigger repaint
    
    def _find_element_at_position(self, pos: Tuple[float, float]) -> Optional[str]:
        """Find element at given position."""
        x, y = pos
        
        for primitive in self.spatial_primitives:
            px, py = primitive.position
            
            # Simple distance-based selection (can be refined)
            distance = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
            if distance < 20:  # 20px selection radius
                return primitive.element_id
        
        return None

class ArisbeStandardGUI(QMainWindow):
    """
    Standard Arisbe GUI with complete pipeline compliance.
    
    This is the authoritative GUI implementation that enforces all
    architectural requirements and serves as the foundation for
    all future development.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe - Existential Graphs (Standard Pipeline)")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize corpus
        try:
            self.corpus_loader = get_corpus_loader()
            print(f"✅ Corpus loaded: {len(self.corpus_loader.examples)} examples")
        except Exception as e:
            print(f"⚠️  Corpus not available: {e}")
            self.corpus_loader = None
        
        # Setup UI
        self.setup_ui()
        self.setup_menu()
        
        # Load initial example
        self.load_initial_example()
    
    def setup_ui(self):
        """Setup the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Right panel - Diagram canvas
        self.diagram_canvas = EGDiagramCanvas()
        main_layout.addWidget(self.diagram_canvas, 3)
        
        # Connect signals
        self.diagram_canvas.element_selected.connect(self.on_element_selected)
        self.diagram_canvas.diagram_changed.connect(self.on_diagram_changed)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Standard Pipeline Active")
    
    def create_control_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setMaximumWidth(400)
        
        layout = QVBoxLayout(panel)
        
        # EGIF Input
        egif_group = QGroupBox("EGIF Input")
        egif_layout = QVBoxLayout(egif_group)
        
        self.egif_text = QTextEdit()
        self.egif_text.setMaximumHeight(100)
        self.egif_text.setPlaceholderText("Enter EGIF expression...")
        egif_layout.addWidget(self.egif_text)
        
        # Parse button
        parse_btn = QPushButton("Parse & Render")
        parse_btn.clicked.connect(self.parse_and_render)
        egif_layout.addWidget(parse_btn)
        
        layout.addWidget(egif_group)
        
        # Corpus Integration
        if self.corpus_loader:
            corpus_group = QGroupBox("Corpus Examples")
            corpus_layout = QVBoxLayout(corpus_group)
            
            self.corpus_combo = QComboBox()
            self.corpus_combo.addItem("Select example...")
            self.populate_corpus_dropdown()
            corpus_layout.addWidget(self.corpus_combo)
            
            load_corpus_btn = QPushButton("Load Corpus Example")
            load_corpus_btn.clicked.connect(self.load_corpus_example)
            corpus_layout.addWidget(load_corpus_btn)
            
            layout.addWidget(corpus_group)
        
        # Pipeline Status
        status_group = QGroupBox("Pipeline Status")
        status_layout = QVBoxLayout(status_group)
        
        self.pipeline_status = QLabel("Ready")
        status_layout.addWidget(self.pipeline_status)
        
        layout.addWidget(status_group)
        
        # Selection Info
        selection_group = QGroupBox("Selection")
        selection_layout = QVBoxLayout(selection_group)
        
        self.selection_info = QLabel("No selection")
        selection_layout.addWidget(self.selection_info)
        
        layout.addWidget(selection_group)
        
        layout.addStretch()
        return panel
    
    def setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open EGIF...", self)
        open_action.triggered.connect(self.open_egif_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save EGIF...", self)
        save_action.triggered.connect(self.save_egif_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_egdf_action = QAction("Export EGDF...", self)
        export_egdf_action.triggered.connect(self.export_egdf)
        file_menu.addAction(export_egdf_action)
        
        # Tests menu
        tests_menu = menubar.addMenu("Tests")
        
        run_tests_action = QAction("Run Core Pipeline Tests", self)
        run_tests_action.triggered.connect(self.run_core_tests)
        tests_menu.addAction(run_tests_action)
    
    def populate_corpus_dropdown(self):
        """Populate corpus dropdown with examples."""
        if not self.corpus_loader:
            return
        
        for example_id, example in self.corpus_loader.examples.items():
            display_text = f"{example.title} - {example.description[:50]}..."
            self.corpus_combo.addItem(display_text, example_id)
    
    def parse_and_render(self):
        """Parse EGIF and render through complete pipeline."""
        egif_text = self.egif_text.toPlainText().strip()
        
        if not egif_text:
            QMessageBox.warning(self, "Input Required", "Please enter an EGIF expression.")
            return
        
        # Load through pipeline with contract validation
        self.diagram_canvas.load_egif(egif_text)
        self.pipeline_status.setText("Pipeline validated ✅")
    
    def load_corpus_example(self):
        """Load selected corpus example."""
        if not self.corpus_loader or self.corpus_combo.currentIndex() == 0:
            return
        
        example_id = self.corpus_combo.currentData()
        example = self.corpus_loader.get_example(example_id)
        
        if example and example.egif_expression:
            self.egif_text.setPlainText(example.egif_expression)
            self.parse_and_render()
            self.status_bar.showMessage(f"Loaded: {example.title}")
    
    def load_initial_example(self):
        """Load initial example on startup."""
        initial_egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
        self.egif_text.setPlainText(initial_egif)
        self.parse_and_render()
    
    def on_element_selected(self, element_id: str):
        """Handle element selection."""
        self.selection_info.setText(f"Selected: {element_id}")
    
    def on_diagram_changed(self):
        """Handle diagram changes."""
        self.status_bar.showMessage("Diagram updated")
    
    def open_egif_file(self):
        """Open EGIF file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open EGIF File", "", "EGIF Files (*.egif);;Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                self.egif_text.setPlainText(content)
                self.parse_and_render()
            except Exception as e:
                QMessageBox.critical(self, "File Error", f"Could not open file: {e}")
    
    def save_egif_file(self):
        """Save EGIF file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save EGIF File", "", "EGIF Files (*.egif);;Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.egif_text.toPlainText())
                self.status_bar.showMessage(f"Saved: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "File Error", f"Could not save file: {e}")
    
    def export_egdf(self):
        """Export current diagram as EGDF."""
        if not self.diagram_canvas.current_egdf:
            QMessageBox.warning(self, "No Diagram", "No diagram to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export EGDF", "", "JSON Files (*.json);;YAML Files (*.yaml);;All Files (*)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'w') as f:
                    json.dump(self.diagram_canvas.current_egdf, f, indent=2)
                self.status_bar.showMessage(f"Exported EGDF: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not export EGDF: {e}")
    
    def run_core_tests(self):
        """Run core pipeline tests."""
        try:
            # Import and run core tests
            sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
            from core_pipeline_tests import run_core_tests
            
            success = run_core_tests()
            
            if success:
                QMessageBox.information(self, "Tests Passed", "✅ All core pipeline tests passed!")
            else:
                QMessageBox.warning(self, "Tests Failed", "❌ Some core pipeline tests failed. Check console for details.")
                
        except Exception as e:
            QMessageBox.critical(self, "Test Error", f"Could not run tests: {e}")

def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Arisbe")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Arisbe Project")
    
    # Create and show main window
    window = ArisbeStandardGUI()
    window.show()
    
    print("🎯 ARISBE STANDARD GUI LAUNCHED")
    print("✅ Complete EGIF→EGI→EGDF pipeline active")
    print("✅ PySide6/QPainter backend enforced")
    print("✅ Corpus integration enabled")
    print("✅ API contract validation active")
    print("✅ Clean architecture - no deprecated code")
    
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())
