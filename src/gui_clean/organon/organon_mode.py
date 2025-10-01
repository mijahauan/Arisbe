"""
Organon Mode - Exploration and corpus management.

Provides read-only visualization of EGI diagrams with:
- Corpus browser (file tree)
- Diagram viewer (SVG display)
- EGIF panel (linear form)
- Metadata panel (properties)
- Export capabilities
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from diagram_controller import DiagramController
from egi_core_dau import RelationalGraphWithCuts
from egi_io import load_egi_json
from egif_generator_dau import generate_egif

# Import our canvas
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from common.diagram_canvas import DiagramCanvas


class OrganonMode(QWidget):
    """
    Organon mode widget - Exploration and corpus management.
    
    Layout:
    - Top: Action buttons (Load, Export, etc.)
    - Left: Diagram canvas (main display)
    - Right: EGIF panel (linear form)
    """
    
    # Signal when user wants to edit in Ergasterion
    edit_in_ergasterion = Signal(object)  # Emits EGI
    
    def __init__(self, diagram_controller: DiagramController, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.controller = diagram_controller
        self._current_file: Optional[Path] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the Organon UI."""
        layout = QVBoxLayout(self)
        
        # Top: Action bar
        action_bar = QHBoxLayout()
        
        self.load_btn = QPushButton("📂 Load EGI...")
        self.load_btn.clicked.connect(self._on_load_egi)
        action_bar.addWidget(self.load_btn)
        
        self.export_btn = QPushButton("💾 Export SVG...")
        self.export_btn.clicked.connect(self._on_export_svg)
        self.export_btn.setEnabled(False)
        action_bar.addWidget(self.export_btn)
        
        action_bar.addStretch()
        
        self.edit_btn = QPushButton("🔨 Edit in Ergasterion")
        self.edit_btn.clicked.connect(self._on_edit_in_ergasterion)
        self.edit_btn.setEnabled(False)
        action_bar.addWidget(self.edit_btn)
        
        layout.addLayout(action_bar)
        
        # Main content: Canvas + EGIF panel
        content = QHBoxLayout()
        
        # Left: Diagram canvas
        self.canvas = DiagramCanvas()
        content.addWidget(self.canvas, stretch=3)
        
        # Right: EGIF panel
        egif_panel = QVBoxLayout()
        egif_label = QLabel("📝 EGIF (Linear Form)")
        egif_label.setStyleSheet("font-weight: bold; padding: 5px;")
        egif_panel.addWidget(egif_label)
        
        self.egif_text = QTextEdit()
        self.egif_text.setReadOnly(True)
        self.egif_text.setFont("Courier New")
        self.egif_text.setPlaceholderText("EGIF will appear here when a graph is loaded...")
        egif_panel.addWidget(self.egif_text)
        
        content.addLayout(egif_panel, stretch=1)
        
        layout.addLayout(content)
    
    def _on_load_egi(self):
        """Load an EGI file."""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load EGI",
            str(Path.home()),
            "EGI Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Load EGI
            egi = load_egi_json(file_path)
            
            # Load into controller
            self.controller.load_egi(egi)
            
            # Get renderable DTO
            dto = self.controller.get_renderable_dto()
            
            # Display
            self.canvas.display_dto(dto, egi)
            
            # Generate and display EGIF
            try:
                egif = generate_egif(egi)
                self.egif_text.setPlainText(egif)
            except Exception as e:
                self.egif_text.setPlainText(f"[EGIF generation failed: {e}]")
            
            # Update state
            self._current_file = Path(file_path)
            self.export_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            
            # Show success
            file_name = Path(file_path).name
            QMessageBox.information(self, "Success", f"Loaded: {file_name}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading EGI",
                f"Failed to load EGI file:\n\n{str(e)}"
            )
    
    def _on_export_svg(self):
        """Export current diagram as SVG."""
        if not self._current_file:
            return
        
        # Get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export SVG",
            str(self._current_file.with_suffix('.svg')),
            "SVG Files (*.svg);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Get current DTO
            dto = self.controller.get_renderable_dto()
            egi = self.controller.get_egi_model()
            
            if not dto or not egi:
                QMessageBox.warning(self, "Warning", "No diagram to export")
                return
            
            # Render to SVG
            from graphviz_svg_renderer import GraphvizSVGRenderer
            renderer = GraphvizSVGRenderer()
            
            egif = generate_egif(egi)
            svg_content = renderer.render_to_svg(
                dto,
                title=self._current_file.stem,
                egif=egif
            )
            
            # Save
            Path(file_path).write_text(svg_content, encoding='utf-8')
            
            QMessageBox.information(
                self,
                "Success",
                f"Exported to:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export SVG:\n\n{str(e)}"
            )
    
    def _on_edit_in_ergasterion(self):
        """Signal that user wants to edit in Ergasterion."""
        egi = self.controller.get_egi_model()
        if egi:
            self.edit_in_ergasterion.emit(egi)
            QMessageBox.information(
                self,
                "Ergasterion",
                "Ergasterion mode will be implemented in Phase 3.\n\n"
                "This will allow interactive editing of the diagram."
            )
