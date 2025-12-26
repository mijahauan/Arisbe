#!/usr/bin/env python3
"""
Simplified test for the interactive EGI viewer without complex dependencies.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
    from PySide6.QtCore import Qt
    
    from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
    
    class SimpleTestWindow(QMainWindow):
        """Simplified test window."""
        
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Arisbe Style System Test")
            self.setGeometry(100, 100, 600, 400)
            
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            
            # Test button
            self.test_btn = QPushButton("Test Style System")
            layout.addWidget(self.test_btn)
            
            # Status label
            self.status_label = QLabel("Ready to test")
            layout.addWidget(self.status_label)
            
            # Connect
            self.test_btn.clicked.connect(self.test_styles)
            
        def test_styles(self):
            """Test the style system."""
            try:
                # Test basic imports
                from gui.simple_style_system import CutStyle, LigatureStyle, VertexStyle, SimpleStyle
                
                # Create style instances
                cut_style = CutStyle()
                ligature_style = LigatureStyle()
                vertex_style = VertexStyle()
                
                # Test complete style
                test_style = SimpleStyle("Test Style")
                
                self.status_label.setText("Style system working!")
                
                # Test EGI creation
                egi = RelationalGraphWithCuts()
                v1 = ElementID("v1")
                egi.V[v1] = Vertex(label="Test")
                
                self.status_label.setText(f"EGI created with {len(egi.V)} vertices")
                
            except Exception as e:
                self.status_label.setText(f"Error: {e}")
                print(f"Full error: {e}")
                import traceback
                traceback.print_exc()
    
    def main():
        app = QApplication(sys.argv)
        window = SimpleTestWindow()
        window.show()
        sys.exit(app.exec())
    
    if __name__ == "__main__":
        main()
        
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
