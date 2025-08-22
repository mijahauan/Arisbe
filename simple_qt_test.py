#!/usr/bin/env python3
"""
Simple Qt test to verify GUI display works.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import Qt

# Add src to path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT / 'src'))

class SimpleTestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt Test - Pipeline Integration")
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Qt GUI Test - Pipeline Integration")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Status
        self.status = QTextEdit()
        self.status.setMaximumHeight(200)
        self.status.setPlainText("Qt GUI is working!\n\nThis confirms that:\n- PySide6 is installed\n- Qt can create windows\n- Ready for pipeline integration")
        layout.addWidget(self.status)
        
        # Test button
        test_btn = QPushButton("Test Pipeline Import")
        test_btn.clicked.connect(self.test_pipeline)
        layout.addWidget(test_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def test_pipeline(self):
        try:
            from egif_parser_dau import EGIFParser
            from spatial_constraint_system import SpatialConstraintSystem
            
            parser = EGIFParser('*x (P x)')
            egi = parser.parse()
            
            constraint_system = SpatialConstraintSystem()
            constraint_system.set_egi_reference(egi)
            
            self.status.setPlainText(f"✅ Pipeline test successful!\n\nParsed EGI: {len(egi.V)} vertices, {len(egi.E)} edges\nConstraint system initialized\n\nReady for full integration!")
            
        except Exception as e:
            self.status.setPlainText(f"❌ Pipeline test failed:\n{e}\n\nQt works but pipeline has issues")

def main():
    app = QApplication(sys.argv)
    
    window = SimpleTestWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    result = main()
    print(f"Qt test completed with exit code: {result}")
