#!/usr/bin/env python3
"""
Test harness for the interactive EGI viewer.

Loads corpus examples and tests multi-style rendering functionality.
"""

import sys
import os
import json
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from egi_core_dau import RelationalGraphWithCuts
from gui.interactive_egi_viewer import InteractiveEGIViewer
from gui.style_manager import STYLE_MANAGER
from gui.styles.dau_compliant_style import DauCompliantStyle
from gui.styles.peirce_authentic_style import PeirceAuthenticStyle
from gui.styles.peirce_latex_inspired_style import PeirceLatexInspiredStyle
from gui.styles.peirce_handwritten_style import PeirceHandwrittenStyle


class TestMainWindow(QMainWindow):
    """Main window for testing the interactive viewer."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe Interactive EGI Viewer - Test Harness")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Test controls
        controls_layout = QHBoxLayout()
        
        self.load_simple_btn = QPushButton("Load Simple Example")
        self.load_complex_btn = QPushButton("Load Complex Example")
        self.load_peirce_btn = QPushButton("Load Peirce Example")
        self.test_styles_btn = QPushButton("Test All Styles")
        
        controls_layout.addWidget(self.load_simple_btn)
        controls_layout.addWidget(self.load_complex_btn)
        controls_layout.addWidget(self.load_peirce_btn)
        controls_layout.addWidget(self.test_styles_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Status label
        self.status_label = QLabel("Ready to test interactive viewer")
        layout.addWidget(self.status_label)
        
        # Interactive viewer
        self.viewer = InteractiveEGIViewer()
        layout.addWidget(self.viewer)
        
        # Connect signals
        self.load_simple_btn.clicked.connect(self.load_simple_example)
        self.load_complex_btn.clicked.connect(self.load_complex_example)
        self.load_peirce_btn.clicked.connect(self.load_peirce_example)
        self.test_styles_btn.clicked.connect(self.test_all_styles)
        
        self.viewer.egi_loaded.connect(self.on_egi_loaded)
        self.viewer.selection_changed.connect(self.on_selection_changed)
        
        # Initialize styles
        self.initialize_styles()
        
    def initialize_styles(self):
        """Initialize and register all styles."""
        try:
            # Register styles with the style manager
            STYLE_MANAGER.register_style(DauCompliantStyle())
            STYLE_MANAGER.register_style(PeirceAuthenticStyle())
            STYLE_MANAGER.register_style(PeirceLatexInspiredStyle())
            STYLE_MANAGER.register_style(PeirceHandwrittenStyle())
            
            self.status_label.setText("Styles initialized successfully")
        except Exception as e:
            self.status_label.setText(f"Style initialization error: {e}")
            
    def load_simple_example(self):
        """Load a simple EGI example for testing."""
        try:
            # Create a simple test EGI
            egi = self.create_simple_test_egi()
            self.viewer.load_egi(egi)
            self.status_label.setText("Simple example loaded")
        except Exception as e:
            self.status_label.setText(f"Error loading simple example: {e}")
            
    def load_complex_example(self):
        """Load a complex corpus example."""
        try:
            corpus_file = "/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs/mixed_quantifier_complex/mixed_quantifier_complex.egi.json"
            egi = self.load_egi_from_file(corpus_file)
            if egi:
                self.viewer.load_egi(egi)
                self.status_label.setText(f"Complex example loaded from corpus")
            else:
                self.status_label.setText("Failed to load complex example")
        except Exception as e:
            self.status_label.setText(f"Error loading complex example: {e}")
            
    def load_peirce_example(self):
        """Load a Peirce-specific example."""
        try:
            corpus_file = "/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs/peirce_modus_ponens/peirce_modus_ponens.egi.json"
            egi = self.load_egi_from_file(corpus_file)
            if egi:
                self.viewer.load_egi(egi)
                self.status_label.setText("Peirce example loaded")
            else:
                self.status_label.setText("Failed to load Peirce example")
        except Exception as e:
            self.status_label.setText(f"Error loading Peirce example: {e}")
            
    def test_all_styles(self):
        """Test switching between all available styles."""
        try:
            styles = ["Dau Compliant", "Peirce Authentic", "Peirce LaTeX-Inspired", "Peirce Handwritten"]
            current_index = self.viewer.style_combo.currentIndex()
            next_index = (current_index + 1) % len(styles)
            
            self.viewer.style_combo.setCurrentIndex(next_index)
            style_name = styles[next_index]
            self.status_label.setText(f"Switched to {style_name} style")
        except Exception as e:
            self.status_label.setText(f"Error testing styles: {e}")
            
    def create_simple_test_egi(self) -> RelationalGraphWithCuts:
        """Create a simple EGI for testing purposes."""
        from egi_core_dau import Vertex, Edge, Cut, ElementID
        from frozendict import frozendict
        
        # Create vertices
        v1 = ElementID("v1")
        v2 = ElementID("v2")
        v3 = ElementID("v3")
        
        vertices = frozenset([
            Vertex(id=v1, label="A", is_generic=False),
            Vertex(id=v2, label="B", is_generic=False),
            Vertex(id=v3, label="C", is_generic=False)
        ])
        
        # Create edges
        e1 = ElementID("e1")
        e2 = ElementID("e2")
        
        edges = frozenset([
            Edge(id=e1),
            Edge(id=e2)
        ])
        
        # Create nu mapping
        nu_mapping = frozendict({
            e1: (v1, v2),
            e2: (v2, v3)
        })
        
        # Create cuts
        c1 = ElementID("c1")
        cuts = frozenset([Cut(id=c1)])
        
        # Create area mapping
        sheet_id = "test_sheet"
        area_mapping = frozendict({
            sheet_id: frozenset([v1, v2, e1, c1]),
            c1: frozenset([v3, e2])
        })
        
        # Create relation mapping
        rel_mapping = frozendict({
            e1: "loves",
            e2: "knows"
        })
        
        # Create EGI
        egi = RelationalGraphWithCuts(
            V=vertices,
            E=edges,
            nu=nu_mapping,
            sheet=sheet_id,
            Cut=cuts,
            area=area_mapping,
            rel=rel_mapping
        )
        
        return egi
        
    def load_egi_from_file(self, file_path: str) -> Optional[RelationalGraphWithCuts]:
        """Load EGI from JSON file."""
        try:
            from egi_loader import load_egi_from_json
            return load_egi_from_json(file_path)
        except Exception as e:
            print(f"Error loading EGI from {file_path}: {e}")
            return None
            
    def json_to_egi(self, data: dict) -> RelationalGraphWithCuts:
        """Convert JSON data to EGI structure."""
        from egi_core_dau import Vertex, Edge, Cut, ElementID
        
        egi = RelationalGraphWithCuts()
        
        # Load vertices
        if 'vertices' in data:
            for v_id, v_data in data['vertices'].items():
                egi.V[ElementID(v_id)] = Vertex(
                    label=v_data.get('label', ''),
                    individual=v_data.get('individual')
                )
                
        # Load edges
        if 'edges' in data:
            for e_id, e_data in data['edges'].items():
                egi.E[ElementID(e_id)] = Edge(
                    relation=e_data.get('relation', ''),
                    arity=e_data.get('arity', 2)
                )
                
        # Load cuts
        if 'cuts' in data:
            for c_id, c_data in data['cuts'].items():
                egi.Cut[ElementID(c_id)] = Cut()
                
        # Load nu mapping
        if 'nu' in data:
            for e_id, vertex_list in data['nu'].items():
                egi.nu[ElementID(e_id)] = frozenset(ElementID(v) for v in vertex_list)
                
        # Load area mapping
        if 'area_mapping' in data:
            for c_id, element_list in data['area_mapping'].items():
                egi.area_mapping[ElementID(c_id)] = frozenset(ElementID(e) for e in element_list)
                
        return egi
        
    def on_egi_loaded(self, egi: RelationalGraphWithCuts):
        """Handle EGI loaded signal."""
        vertex_count = len(egi.V)
        edge_count = len(egi.E)
        cut_count = len(egi.Cut)
        self.status_label.setText(f"EGI loaded: {vertex_count}V, {edge_count}E, {cut_count}C")
        
    def on_selection_changed(self, selected_elements):
        """Handle selection change signal."""
        if selected_elements:
            self.status_label.setText(f"Selected {len(selected_elements)} elements")
        else:
            self.status_label.setText("No elements selected")


def main():
    """Main test function."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Arisbe Interactive Viewer Test")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = TestMainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
