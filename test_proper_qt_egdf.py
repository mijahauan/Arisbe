#!/usr/bin/env python3
"""
Proper Qt Integration using EGDF Canvas Renderer

This demonstrates the correct architecture:
EGIF → EGI → EGDF Document → EGDFCanvasRenderer → Qt Display
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel
from PySide6.QtCore import Qt

# Add src to path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT / 'src'))
os.chdir(REPO_ROOT)

class ProperQtEGDFWindow(QWidget):
    """Qt window that uses proper EGDF pipeline."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proper Qt EGDF Integration")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create layout
        layout = QHBoxLayout(self)
        
        # Left panel - controls
        controls = QVBoxLayout()
        
        # EGIF input
        controls.addWidget(QLabel("EGIF Input:"))
        self.egif_input = QTextEdit()
        self.egif_input.setMaximumHeight(100)
        self.egif_input.setPlainText("*x ~[ ~[ (P x) ] ]")
        controls.addWidget(self.egif_input)
        
        # Load button
        self.load_btn = QPushButton("Load EGIF")
        self.load_btn.clicked.connect(self.load_egif)
        controls.addWidget(self.load_btn)
        
        # Status
        controls.addWidget(QLabel("Status:"))
        self.status = QTextEdit()
        self.status.setMaximumHeight(200)
        controls.addWidget(self.status)
        
        # Example buttons
        controls.addWidget(QLabel("Examples:"))
        examples = [
            ("Simple", "*x (P x)"),
            ("Binary", "*x *y (Loves x y)"),
            ("Single Cut", "*x ~[ (P x) ]"),
            ("Double Cut", "*x ~[ ~[ (P x) ] ]"),
            ("Complex", "*x *y (Human x) (Loves x y) ~[ (Mortal x) (Happy y) ]")
        ]
        
        for name, egif in examples:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, e=egif: self.load_example(e))
            controls.addWidget(btn)
        
        controls.addStretch()
        
        # Right panel - EGDF canvas
        canvas_layout = QVBoxLayout()
        canvas_layout.addWidget(QLabel("EGDF Canvas Renderer:"))
        
        # Import and create EGDF canvas
        try:
            from egdf_canvas_renderer import EGDFCanvasRenderer
            self.canvas = EGDFCanvasRenderer(600, 500)
            canvas_layout.addWidget(self.canvas)
        except Exception as e:
            error_label = QLabel(f"Failed to create EGDF canvas: {e}")
            canvas_layout.addWidget(error_label)
            self.canvas = None
        
        # Add panels to main layout
        left_widget = QWidget()
        left_widget.setLayout(controls)
        left_widget.setMaximumWidth(350)
        
        right_widget = QWidget()
        right_widget.setLayout(canvas_layout)
        
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
        
        # Load default example
        self.load_egif()
    
    def load_example(self, egif_text):
        """Load an example EGIF."""
        self.egif_input.setPlainText(egif_text)
        self.load_egif()
    
    def load_egif(self):
        """Load EGIF using proper EGDF pipeline."""
        if not self.canvas:
            self.status.setPlainText("❌ EGDF Canvas not available")
            return
        
        egif_text = self.egif_input.toPlainText().strip()
        if not egif_text:
            self.status.setPlainText("❌ No EGIF input")
            return
        
        try:
            self.status.setPlainText("🔄 Processing EGIF through proper pipeline...")
            
            # Step 1: Parse EGIF to EGI
            from egif_parser_dau import EGIFParser
            parser = EGIFParser(egif_text)
            egi = parser.parse()
            
            self.status.append(f"✅ EGIF→EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
            
            # Step 2: Convert EGI to EGDF using proper translator
            from egi_to_egdf_translator import get_rock_solid_egdf_layout
            egdf_document = get_rock_solid_egdf_layout(egi)
            
            self.status.append(f"✅ EGI→EGDF: Document created with {len(egdf_document.visual_layout.get('spatial_primitives', []))} spatial primitives")
            
            # Step 3: Load EGDF into canvas renderer
            success = self.canvas.load_egdf(egdf_document, egi)
            
            if success:
                self.status.append("✅ EGDF→Qt: Canvas rendering successful")
                self.status.append(f"\n📊 Final Status:")
                self.status.append(f"  • EGIF: {egif_text}")
                self.status.append(f"  • EGI Structure: {len(egi.V)}V, {len(egi.E)}E, {len(egi.Cut)}C")
                self.status.append(f"  • EGDF Primitives: {len(egdf_document.visual_layout.get('spatial_primitives', []))}")
                self.status.append(f"  • Qt Rendering: Active")
            else:
                self.status.append("❌ EGDF→Qt: Canvas rendering failed")
                
        except Exception as e:
            self.status.append(f"❌ Pipeline failed: {e}")
            import traceback
            self.status.append(f"Traceback: {traceback.format_exc()}")

def main():
    app = QApplication(sys.argv)
    
    window = ProperQtEGDFWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    result = main()
    print(f"Proper Qt EGDF integration completed with exit code: {result}")
