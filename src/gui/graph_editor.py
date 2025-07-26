#!/usr/bin/env python3
"""
Existential Graph Editor - GUI only handles EGRF rendering.
Backend handles CLIF → EG-HG → EGRF conversion.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QTabWidget, QGraphicsView,
    QGraphicsScene, QGraphicsItem, QComboBox, QSplitter, QFrame,
    QGroupBox, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Backend API imports
from clif_parser import CLIFParser
from egrf_from_graph import convert_graph_to_egrf

# GUI imports
from gui.peirce_layout_engine import PeirceLayoutEngine
from gui.peirce_graphics_adapter import PeirceGraphicsAdapter
from gui.layout_calculator import LayoutCalculator  # Fallback for when Peirce engine fails
from gui.graphics_items import ContextItem, PredicateItem, EntityItem, ConnectionManager


class GraphCanvas(QGraphicsView):
    """Canvas for displaying existential graphs from EGRF."""
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        # Initialize Peirce layout engine with fallback
        self.layout_engine = PeirceLayoutEngine(1200, 800)
        self.graphics_adapter = PeirceGraphicsAdapter(self.scene)
        self.fallback_calculator = LayoutCalculator(1200, 800)  # Fallback when Peirce engine fails
        
        # Connection manager for lines of identity
        self.connection_manager = ConnectionManager()
        
        # Current EGRF data
        self.current_egrf = None
        
        # Set scene size
        self.scene.setSceneRect(0, 0, 1200, 800)
    
    def load_egrf_graph(self, egrf_doc):
        """Load and display an EGRF document."""
        try:
            print(f"DEBUG: Loading EGRF graph with {len(egrf_doc.logical_elements) if egrf_doc else 0} elements")
            
            # Clear existing scene
            self.scene.clear()
            
            # Store current EGRF
            self.current_egrf = egrf_doc
            
            if not egrf_doc or not egrf_doc.logical_elements:
                print("Warning: No EGRF elements to display")
                return
            
            # Calculate layout using Peirce engine with fallback
            rendering_instructions = None
            try:
                rendering_instructions = self.layout_engine.calculate_layout(egrf_doc)
                print(f"DEBUG: Peirce layout engine generated rendering instructions")
                print(f"  Elements: {len(rendering_instructions.get('elements', []))}")
                print(f"  Ligatures: {len(rendering_instructions.get('ligatures', []))}")
            except Exception as layout_error:
                print(f"DEBUG: Peirce layout engine failed ({layout_error}), falling back to original layout")
                try:
                    layout_data = self.fallback_calculator.calculate_layout(egrf_doc)
                    print(f"DEBUG: Fallback layout calculated for {len(layout_data)} elements")
                    # Convert fallback layout to rendering instructions format
                    rendering_instructions = self._convert_fallback_to_instructions(layout_data)
                except Exception as fallback_error:
                    print(f"ERROR: Both layout engines failed: {fallback_error}")
                    return
            
            if not rendering_instructions:
                print("Warning: Layout calculation failed")
                return
            
            # Create graphics items using Peirce adapter
            if 'elements' in rendering_instructions:
                # Use Peirce graphics adapter
                graphics_items = self.graphics_adapter.create_graphics_from_instructions(rendering_instructions)
                
                # Update predicate names from EGRF data
                self.graphics_adapter.update_element_names(egrf_doc)
                
                print(f"DEBUG: Created {len(graphics_items)} graphics items using Peirce adapter")
            else:
                # Fallback: use old graphics items system
                graphics_items = self._create_fallback_graphics_items(rendering_instructions)
                print(f"DEBUG: Created {len(graphics_items)} graphics items using fallback system")
            
            # Update the view to fit content
            self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
        except Exception as e:
            print(f"Error loading EGRF graph: {e}")
            import traceback
            traceback.print_exc()


class BackendAPI:
    """API for backend CLIF processing."""
    
    def __init__(self):
        self.parser = CLIFParser()
    
    def clif_to_egrf(self, clif_text: str, metadata: Dict = None) -> Any:
        """Convert CLIF to EGRF using backend pipeline."""
        try:
            # Step 1: Parse CLIF to EG-HG
            parse_result = self.parser.parse(clif_text)
            
            if parse_result.errors:
                raise Exception(f"CLIF parse errors: {[e.message for e in parse_result.errors]}")
            
            if not parse_result.graph:
                raise Exception("No graph produced from CLIF parsing")
            
            # Step 2: Convert EG-HG to EGRF
            egrf_doc = convert_graph_to_egrf(parse_result.graph, metadata or {})
            
            if not egrf_doc:
                raise Exception("EGRF conversion failed")
            
            return egrf_doc
            
        except Exception as e:
            print(f"Backend API error: {e}")
            raise


class GraphEditor(QMainWindow):
    """Main graph editor application - GUI only."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe - Existential Graphs Editor")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize backend API
        self.backend = BackendAPI()
        
        # Current graph data
        self.current_clif = ""
        self.current_egrf = None
        
        # Corpus data
        self.corpus_examples = {}
        self.load_corpus_examples()
        
        # Setup UI
        self.setup_ui()
        
        # Load default example
        if self.corpus_examples:
            first_example = list(self.corpus_examples.keys())[0]
            self.corpus_combo.setCurrentText(first_example)
            self.load_corpus_example()
    
    def setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 1000])
    
    def create_left_panel(self):
        """Create the left control panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(400)
        
        layout = QVBoxLayout(panel)
        
        # Graph Input section
        input_group = QGroupBox("Graph Input")
        input_layout = QVBoxLayout(input_group)
        
        # CLIF Statement
        clif_label = QLabel("CLIF Statement")
        input_layout.addWidget(clif_label)
        
        self.clif_input = QTextEdit()
        self.clif_input.setMaximumHeight(100)
        self.clif_input.setPlaceholderText("Enter CLIF statement here...")
        input_layout.addWidget(self.clif_input)
        
        # Parse button
        parse_button = QPushButton("Parse CLIF")
        parse_button.clicked.connect(self.parse_clif)
        input_layout.addWidget(parse_button)
        
        layout.addWidget(input_group)
        
        # Corpus Examples section
        corpus_group = QGroupBox("Corpus Examples")
        corpus_layout = QVBoxLayout(corpus_group)
        
        self.corpus_combo = QComboBox()
        self.populate_corpus_dropdown()
        corpus_layout.addWidget(self.corpus_combo)
        
        load_example_button = QPushButton("Load Example")
        load_example_button.clicked.connect(self.load_corpus_example)
        corpus_layout.addWidget(load_example_button)
        
        layout.addWidget(corpus_group)
        
        # Create Empty Graph button
        empty_button = QPushButton("Create Empty Graph")
        empty_button.clicked.connect(self.create_empty_graph)
        layout.addWidget(empty_button)
        
        # Export/Save section
        export_group = QGroupBox("Export / Save")
        export_layout = QVBoxLayout(export_group)
        
        save_button = QPushButton("Save Graph")
        save_button.clicked.connect(self.save_graph)
        export_layout.addWidget(save_button)
        
        export_pdf_button = QPushButton("Export PDF")
        export_pdf_button.clicked.connect(self.export_pdf)
        export_layout.addWidget(export_pdf_button)
        
        export_png_button = QPushButton("Export PNG")
        export_png_button.clicked.connect(self.export_png)
        export_layout.addWidget(export_png_button)
        
        export_latex_button = QPushButton("Export LaTeX")
        export_latex_button.clicked.connect(self.export_latex)
        export_layout.addWidget(export_latex_button)
        
        propose_epg_button = QPushButton("Propose to EPG")
        propose_epg_button.clicked.connect(self.propose_to_epg)
        export_layout.addWidget(propose_epg_button)
        
        layout.addWidget(export_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self):
        """Create the right panel with tabs and status."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        
        # Diagram Form tab
        self.graph_canvas = GraphCanvas()
        self.tab_widget.addTab(self.graph_canvas, "Diagram Form")
        
        # Linear Form (CLIF) tab
        self.linear_form = QTextEdit()
        self.linear_form.setReadOnly(True)
        self.linear_form.setFont(QFont("Courier", 10))
        self.tab_widget.addTab(self.linear_form, "Linear Form (CLIF)")
        
        layout.addWidget(self.tab_widget)
        
        # Bottom status area
        bottom_layout = QHBoxLayout()
        
        # Validation Status
        validation_group = QGroupBox("Validation Status")
        validation_layout = QVBoxLayout(validation_group)
        
        self.validation_label = QLabel("✓ Valid")
        self.validation_label.setStyleSheet("color: green; font-weight: bold;")
        validation_layout.addWidget(self.validation_label)
        
        self.validation_details = QLabel("Graph structure appears valid\nContains 0 elements\nDiagram rendering: INACTIVE")
        self.validation_details.setWordWrap(True)
        validation_layout.addWidget(self.validation_details)
        
        bottom_layout.addWidget(validation_group)
        
        # Graph Statistics
        stats_group = QGroupBox("Graph Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("Elements: 0\nContexts: 0\nPredicates: 0\nEntities: 0")
        stats_layout.addWidget(self.stats_label)
        
        bottom_layout.addWidget(stats_group)
        
        # Peircean Rules
        rules_group = QGroupBox("Peircean Rules")
        rules_layout = QVBoxLayout(rules_group)
        
        insertion_button = QPushButton("Insertion")
        deletion_button = QPushButton("Deletion")
        erasure_button = QPushButton("Erasure")
        double_cut_button = QPushButton("Double Cut")
        iteration_button = QPushButton("Iteration")
        
        rules_layout.addWidget(insertion_button)
        rules_layout.addWidget(deletion_button)
        rules_layout.addWidget(erasure_button)
        rules_layout.addWidget(double_cut_button)
        rules_layout.addWidget(iteration_button)
        
        bottom_layout.addWidget(rules_group)
        
        # Quick Add
        quick_group = QGroupBox("Quick Add")
        quick_layout = QVBoxLayout(quick_group)
        
        add_cut_button = QPushButton("Add Cut")
        add_predicate_button = QPushButton("Add Predicate")
        add_line_button = QPushButton("Add Line of Identity")
        
        quick_layout.addWidget(add_cut_button)
        quick_layout.addWidget(add_predicate_button)
        quick_layout.addWidget(add_line_button)
        
        bottom_layout.addWidget(quick_group)
        
        layout.addLayout(bottom_layout)
        
        return panel
    
    def load_corpus_examples(self):
        """Load corpus examples from the corpus directory."""
        try:
            corpus_dir = Path(__file__).parent.parent.parent / "corpus" / "corpus"
            
            if not corpus_dir.exists():
                print(f"Warning: Corpus directory not found at {corpus_dir}")
                return
            
            # Find all .clif files in corpus subdirectories
            for clif_file in corpus_dir.rglob("*.clif"):
                try:
                    # Read the CLIF content
                    with open(clif_file, 'r', encoding='utf-8') as f:
                        clif_content = f.read().strip()
                    
                    # Create a display name from the file path
                    relative_path = clif_file.relative_to(corpus_dir)
                    category = relative_path.parts[0] if len(relative_path.parts) > 1 else "misc"
                    filename = clif_file.stem
                    
                    display_name = f"{category}: {filename}"
                    
                    self.corpus_examples[display_name] = {
                        'clif': clif_content,
                        'file_path': str(clif_file),
                        'category': category,
                        'filename': filename
                    }
                    
                except Exception as e:
                    print(f"Warning: Could not load {clif_file}: {e}")
            
            print(f"Loaded {len(self.corpus_examples)} corpus examples")
            
        except Exception as e:
            print(f"Error loading corpus examples: {e}")
    
    def populate_corpus_dropdown(self):
        """Populate the corpus dropdown with available examples."""
        self.corpus_combo.clear()
        
        if not self.corpus_examples:
            self.corpus_combo.addItem("No corpus examples found")
            return
        
        # Sort examples by category and name
        sorted_examples = sorted(self.corpus_examples.keys())
        
        for example_name in sorted_examples:
            self.corpus_combo.addItem(example_name)
    
    def parse_clif(self):
        """Parse the CLIF input using backend API."""
        clif_text = self.clif_input.toPlainText().strip()
        
        if not clif_text:
            QMessageBox.warning(self, "Warning", "Please enter a CLIF statement to parse.")
            return
        
        try:
            # Use backend API to convert CLIF to EGRF
            egrf_doc = self.backend.clif_to_egrf(clif_text, {
                'title': 'User Input Graph',
                'description': f'Graph from CLIF: {clif_text}'
            })
            
            # Update displays
            self.current_clif = clif_text
            self.current_egrf = egrf_doc
            
            self.update_displays()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error parsing CLIF: {str(e)}")
    
    def load_corpus_example(self):
        """Load the selected corpus example using backend API."""
        selected_example = self.corpus_combo.currentText()
        print(f"DEBUG: Loading corpus example: {selected_example}")
        
        if selected_example not in self.corpus_examples:
            print(f"DEBUG: Example not found: {selected_example}")
            return
        
        example_data = self.corpus_examples[selected_example]
        clif_text = example_data['clif']
        print(f"DEBUG: CLIF text: {clif_text}")
        
        try:
            # Set the CLIF input
            self.clif_input.setPlainText(clif_text)
            
            # Use backend API to convert CLIF to EGRF
            egrf_doc = self.backend.clif_to_egrf(clif_text, {
                'title': example_data['filename'],
                'description': f"Corpus example from {example_data['category']}"
            })
            
            print(f"DEBUG: EGRF doc created with {len(egrf_doc.logical_elements)} elements")
            
            # Store and display
            self.current_clif = clif_text
            self.current_egrf = egrf_doc
            
            self.update_displays()
            
        except Exception as e:
            error_msg = str(e)
            print(f"DEBUG: Error loading corpus example: {error_msg}")
            
            # Check if it's a parsing error for unsupported syntax
            if "CLIF parse errors" in error_msg and any(unsupported in clif_text for unsupported in ["(or P Q)", "(or ", "bare predicate"]):
                QMessageBox.warning(self, "Unsupported CLIF Syntax", 
                    f"The corpus example '{selected_example}' uses CLIF syntax that is not yet supported by the parser.\n\n"
                    f"CLIF: {clif_text}\n\n"
                    f"This example will be skipped. Please select a different corpus example.")
                print(f"DEBUG: Skipping unsupported CLIF syntax: {clif_text}")
                
                # Try to load a different example
                self.load_next_supported_example()
            else:
                QMessageBox.critical(self, "Error", f"Error loading corpus example: {error_msg}")
                import traceback
                traceback.print_exc()
    
    def load_next_supported_example(self):
        """Load the next supported corpus example."""
        current_index = self.corpus_combo.currentIndex()
        total_examples = self.corpus_combo.count()
        
        # Try the next few examples to find a supported one
        for i in range(1, min(5, total_examples)):
            next_index = (current_index + i) % total_examples
            self.corpus_combo.setCurrentIndex(next_index)
            
            example_name = self.corpus_combo.currentText()
            if example_name in self.corpus_examples:
                example_data = self.corpus_examples[example_name]
                clif_text = example_data['clif']
                
                # Skip known unsupported patterns
                if not any(unsupported in clif_text for unsupported in ["(or P Q)", "(or Q P)"]):
                    print(f"DEBUG: Trying supported example: {example_name}")
                    try:
                        self.load_corpus_example()
                        return  # Success, stop trying
                    except:
                        continue  # Try next example
        
        print("DEBUG: No supported examples found, staying with current selection")
    
    def update_displays(self):
        """Update all displays with current graph data."""
        try:
            # Update linear form
            self.linear_form.setPlainText(self.current_clif)
            
            # Update diagram form
            if self.current_egrf:
                self.graph_canvas.load_egrf_graph(self.current_egrf)
            
            # Update statistics
            self.update_statistics()
            
            # Update validation status
            self.update_validation_status()
            
        except Exception as e:
            print(f"Error updating displays: {e}")
            import traceback
            traceback.print_exc()
    
    def update_statistics(self):
        """Update the statistics display."""
        if not self.current_egrf:
            self.stats_label.setText("Elements: 0\nContexts: 0\nPredicates: 0\nEntities: 0")
            return
        
        try:
            # Count elements by type
            contexts = 0
            predicates = 0
            entities = 0
            
            for element in self.current_egrf.logical_elements:
                if element.logical_type in ['sheet', 'cut']:
                    contexts += 1
                elif element.logical_type == 'relation':
                    predicates += 1
                elif element.logical_type in ['individual', 'line_of_identity']:
                    entities += 1
            
            total_elements = len(self.current_egrf.logical_elements)
            
            self.stats_label.setText(
                f"Elements: {total_elements}\n"
                f"Contexts: {contexts}\n"
                f"Predicates: {predicates}\n"
                f"Entities: {entities}"
            )
            
        except Exception as e:
            print(f"Error updating statistics: {e}")
            self.stats_label.setText("Elements: Error\nContexts: Error\nPredicates: Error\nEntities: Error")
    
    def update_validation_status(self):
        """Update the validation status display."""
        if not self.current_egrf:
            self.validation_label.setText("No Graph")
            self.validation_label.setStyleSheet("color: gray; font-weight: bold;")
            self.validation_details.setText("No graph loaded\nDiagram rendering: INACTIVE")
            return
        
        try:
            # Basic validation
            element_count = len(self.current_egrf.logical_elements)
            
            self.validation_label.setText("✓ Valid")
            self.validation_label.setStyleSheet("color: green; font-weight: bold;")
            self.validation_details.setText(
                f"Graph structure appears valid\n"
                f"Contains {element_count} elements\n"
                f"Diagram rendering: ACTIVE"
            )
            
        except Exception as e:
            print(f"Error updating validation status: {e}")
            self.validation_label.setText("❌ Error")
            self.validation_label.setStyleSheet("color: red; font-weight: bold;")
            self.validation_details.setText("Error validating graph\nDiagram rendering: ERROR")
    
    def create_empty_graph(self):
        """Create an empty graph."""
        # For now, just clear everything
        self.clif_input.clear()
        self.current_clif = ""
        self.current_egrf = None
        self.graph_canvas.scene.clear()
        self.linear_form.clear()
        self.update_statistics()
        self.update_validation_status()
    
    def save_graph(self):
        """Save the current graph."""
        QMessageBox.information(self, "Info", "Save functionality not yet implemented.")
    
    def export_pdf(self):
        """Export graph as PDF."""
        QMessageBox.information(self, "Info", "PDF export functionality not yet implemented.")
    
    def export_png(self):
        """Export graph as PNG."""
        QMessageBox.information(self, "Info", "PNG export functionality not yet implemented.")
    
    def export_latex(self):
        """Export graph as LaTeX."""
        QMessageBox.information(self, "Info", "LaTeX export functionality not yet implemented.")
    
    def propose_to_epg(self):
        """Propose graph to Endoporeutic Game."""
        QMessageBox.information(self, "Info", "EPG proposal functionality not yet implemented.")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Arisbe Existential Graphs Editor")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Arisbe Project")
    
    # Create and show main window
    window = GraphEditor()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

