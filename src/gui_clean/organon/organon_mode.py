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

# Import organon components
from organon.metadata_panel import MetadataPanel
from organon.history_timeline import HistoryTimeline


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
        self._current_entity: Optional['GraphEntity'] = None  # Track loaded entity
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the Organon UI."""
        layout = QHBoxLayout(self)  # Changed to horizontal for sidebar
        
        # Left: Corpus browser sidebar
        from organon.corpus_browser import CorpusBrowserWidget
        
        # Use corpus directory if it exists
        corpus_path = Path(__file__).parent.parent.parent.parent / "corpus" / "graphs"
        if not corpus_path.exists():
            corpus_path.mkdir(parents=True, exist_ok=True)
        
        self.corpus_browser = CorpusBrowserWidget(corpus_path)
        self.corpus_browser.entity_selected.connect(self._on_load_from_corpus)
        self.corpus_browser.setMaximumWidth(300)
        layout.addWidget(self.corpus_browser)
        
        # Right: Main viewing area
        main_area = QVBoxLayout()
        
        # Top: Action bar
        action_bar = QHBoxLayout()
        
        self.load_btn = QPushButton("📂 Load File...")
        self.load_btn.clicked.connect(self._on_load_egi)
        self.load_btn.setToolTip("Load EGI from any file")
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
        
        main_area.addLayout(action_bar)
        
        # History Timeline (shown only for historical entities)
        self.history_timeline = HistoryTimeline()
        self.history_timeline.state_selected.connect(self._on_state_selected)
        main_area.addWidget(self.history_timeline)
        
        # Main content: Canvas + Right Sidebar
        content = QHBoxLayout()
        
        # Center: Diagram canvas
        self.canvas = DiagramCanvas()
        content.addWidget(self.canvas, stretch=3)
        
        # Right Sidebar: Metadata + EGIF panels
        right_sidebar = QVBoxLayout()
        right_sidebar.setSpacing(10)
        
        # Metadata Panel
        self.metadata_panel = MetadataPanel()
        self.metadata_panel.setMaximumWidth(350)
        right_sidebar.addWidget(self.metadata_panel, stretch=1)
        
        # EGIF Panel
        egif_panel = QVBoxLayout()
        egif_label = QLabel("📝 EGIF (Linear Form)")
        egif_label.setStyleSheet("font-weight: bold; padding: 5px;")
        egif_panel.addWidget(egif_label)
        
        self.egif_text = QTextEdit()
        self.egif_text.setReadOnly(True)
        self.egif_text.setFont("Courier New")
        self.egif_text.setPlaceholderText("EGIF will appear here when a graph is loaded...")
        egif_panel.addWidget(self.egif_text)
        
        right_sidebar.addLayout(egif_panel, stretch=1)
        
        content.addLayout(right_sidebar, stretch=1)
        
        main_area.addLayout(content)
        layout.addLayout(main_area)
    
    def _on_load_from_corpus(self, entity_name: str):
        """Load entity from corpus."""
        try:
            from entity_storage import EntityStorageManager
            
            # Get corpus path (same as browser)
            corpus_path = Path(__file__).parent.parent.parent.parent / "corpus" / "graphs"
            storage = EntityStorageManager(corpus_path)
            
            # Load entity
            entity = storage.load_entity(entity_name)
            
            # Load into controller
            print(f"Loading EGI into controller: {len(entity.current_egi.V)}V, {len(entity.current_egi.E)}E")
            success = self.controller.load_egi(entity.current_egi)
            
            if not success:
                raise Exception("Controller failed to load EGI")
            
            # Get renderable DTO
            dto = self.controller.get_renderable_dto()
            print(f"Got DTO from controller: {dto}")
            
            if dto is None:
                raise Exception("Controller returned None for DTO")
            
            # Display
            self.canvas.display_dto(dto, entity.current_egi)
            
            # Display EGIF
            egif = entity.get_current_egif()
            self.egif_text.setPlainText(egif)
            
            # Update metadata panel
            self.metadata_panel.update_metadata(entity)
            
            # Update history timeline
            self.history_timeline.update_history(entity)
            
            # Update state
            self._current_file = None  # Loaded from corpus, not file
            self._current_entity = entity  # Store entity for history navigation
            self.export_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            
            # Show success
            parent = self.window()
            if hasattr(parent, 'statusBar'):
                status = "Historical" if entity.is_historical else "Standalone"
                parent.statusBar().showMessage(f"Loaded {status}: {entity.name}", 3000)
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Entity",
                f"Failed to load entity from corpus:\n\n{str(e)}"
            )
    
    def _on_load_egi(self):
        """Load an EGI file."""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load EGI",
            str(Path.home()),
            "EGI Files (*.json *.egi.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Load EGI (handles both standalone and entity formats)
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
            
            # Clear metadata panel and timeline (file load has no entity metadata)
            self.metadata_panel.clear()
            self.history_timeline.hide()
            
            # Update state
            self._current_file = Path(file_path)
            self._current_entity = None  # No entity for file loads
            self.export_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            
            # Show success (shorter message)
            file_name = Path(file_path).name
            parent = self.window()
            if hasattr(parent, 'statusBar'):
                parent.statusBar().showMessage(f"Loaded: {file_name}", 3000)
            
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
    
    def _on_state_selected(self, state_id: str):
        """
        Navigate to selected historical state.
        
        Args:
            state_id: The state ID to navigate to
        """
        if not self._current_entity or not self._current_entity.is_historical:
            return
        
        try:
            # Get state snapshot
            state = self._current_entity.get_state(state_id)
            
            # Load state's EGI into controller
            self.controller.load_egi(state.egi)
            
            # Get renderable DTO
            dto = self.controller.get_renderable_dto()
            
            # Display
            self.canvas.display_dto(dto, state.egi)
            
            # Update EGIF (use cached if available)
            egif = state.linear_forms.get("egif")
            if not egif:
                egif = generate_egif(state.egi)
            self.egif_text.setPlainText(egif)
            
            # Update history timeline to highlight new current state
            # (This will re-render with the selected state as current)
            self._current_entity.history.current_state_id = state_id
            self.history_timeline.update_history(self._current_entity)
            
            # Show state info
            parent = self.window()
            if hasattr(parent, 'statusBar'):
                parent.statusBar().showMessage(
                    f"Viewing State {state.step_number + 1}: {state.description}",
                    5000
                )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Navigating State",
                f"Failed to navigate to state:\n\n{str(e)}"
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
