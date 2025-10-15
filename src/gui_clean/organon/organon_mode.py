"""
Organon Mode - Exploration and tomos management.

Provides read-only visualization of EGI diagrams with:
- Tomos browser (file tree)
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
    Organon mode widget - Exploration and tomos management.
    
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
        self._current_uod: Optional['UniverseOfDiscourse'] = None  # Track loaded UoD
        
        # Initialize TomosService
        from tomos_service import TomosService
        tomos_root = Path(__file__).parent.parent.parent.parent / "tomos"
        self.tomos = TomosService(tomos_root)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the Organon UI."""
        layout = QHBoxLayout(self)  # Changed to horizontal for sidebar
        
        # Left: Tomos browser sidebar
        from organon.corpus_browser import TomosBrowserWidget
        
        # Use tomos root directory
        tomos_root = Path(__file__).parent.parent.parent.parent / "tomos"
        
        self.tomos_browser = TomosBrowserWidget(tomos_root)
        self.tomos_browser.entity_selected.connect(self._on_load_from_corpus)
        self.tomos_browser.setMaximumWidth(300)
        layout.addWidget(self.tomos_browser)
        
        # Right: Main viewing area
        main_area = QVBoxLayout()
        
        # Top: Action bar
        action_bar = QHBoxLayout()
        
        self.load_btn = QPushButton("📂 Load File...")
        self.load_btn.clicked.connect(self._on_load_egi)
        self.load_btn.setToolTip("Load EGI from any file")
        action_bar.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("💾 Save EGI...")
        self.save_btn.clicked.connect(self._on_save_egi)
        self.save_btn.setEnabled(False)
        self.save_btn.setToolTip("Save EGI with layout customizations")
        action_bar.addWidget(self.save_btn)
        
        self.export_btn = QPushButton("📤 Export SVG...")
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
    
    def _on_load_from_corpus(self, uod_id: str):
        """Load UoD from tomos."""
        try:
            # Load UoD
            uod = self.tomos.load_uod(uod_id, load_history=True)
            
            if uod is None:
                raise Exception(f"UoD not found: {uod_id}")
            
            # Load into controller
            print(f"Loading EGI into controller: {len(uod.current_egi.V)}V, {len(uod.current_egi.E)}E")
            success = self.controller.load_egi(uod.current_egi)
            
            if not success:
                raise Exception("Controller failed to load EGI")
            
            # Restore layout deltas if present
            if uod.current_layout_deltas:
                print(f"=== Restoring layout deltas from UoD (Organon) ===")
                from definitive_egi_layout_engine import LayoutDelta
                for element_id, delta_data in uod.current_layout_deltas.items():
                    if isinstance(delta_data, dict) and 'type' in delta_data and 'position' in delta_data:
                        delta = LayoutDelta(
                            element_id=element_id,
                            delta_type=delta_data['type'],
                            new_position=tuple(delta_data['position'])
                        )
                        self.controller.layout_deltas[element_id] = delta
                self.controller._trigger_fast_update()
            
            # Get renderable DTO
            dto = self.controller.get_renderable_dto()
            print(f"Got DTO from controller: {dto}")
            
            if dto is None:
                raise Exception("Controller returned None for DTO")
            
            # Display (fit_to_view=True for initial load)
            self.canvas.display_dto(dto, uod.current_egi, fit_to_view=True)
            
            # Display EGIF
            egif = uod.get_current_egif()
            self.egif_text.setPlainText(egif)
            
            # Update metadata panel
            self.metadata_panel.update_metadata(uod)
            
            # Update history timeline
            self.history_timeline.update_history(uod)
            
            # Update state
            self._current_file = None  # Loaded from tomos, not file
            self._current_uod = uod  # Store UoD for history navigation
            self.save_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            
            # Show success
            parent = self.window()
            if hasattr(parent, 'statusBar'):
                status = "Historical" if uod.is_historical else "Standalone"
                type_label = "Static" if uod.is_static else "Dynamic"
                parent.statusBar().showMessage(f"Loaded {type_label} {status}: {uod.name}", 3000)
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading UoD",
                f"Failed to load UoD from tomos:\n\n{str(e)}"
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
            import json
            from definitive_egi_layout_engine import LayoutDelta
            
            # Load JSON file
            file_content = Path(file_path).read_text(encoding="utf-8")
            data = json.loads(file_content)
            
            # Load EGI (handles both standalone and entity formats)
            egi = load_egi_json(file_path)
            
            # Load into controller
            self.controller.load_egi(egi)
            
            # Restore layout deltas if present
            if 'layout_deltas' in data:
                print(f"=== Restoring layout deltas from file (Organon) ===")
                deltas_dict = data['layout_deltas']
                print(f"  Found {len(deltas_dict)} deltas in file")
                
                for element_id, delta_data in deltas_dict.items():
                    delta = LayoutDelta(
                        element_id=element_id,
                        delta_type=delta_data['type'],
                        new_position=tuple(delta_data['position'])
                    )
                    self.controller.layout_deltas[element_id] = delta
                    print(f"  Restored delta: {element_id} -> {delta.new_position}")
                
                print(f"=== Deltas restored, triggering fast update ===")
                # Trigger fast update to apply deltas
                self.controller._trigger_fast_update()
            else:
                print("=== No layout_deltas found in file (Organon) ===")
            
            # Get renderable DTO
            dto = self.controller.get_renderable_dto()
            
            # Display (fit_to_view=True for new file load)
            self.canvas.display_dto(dto, egi, fit_to_view=True)
            
            # Generate and display EGIF
            try:
                egif = generate_egif(egi)
                self.egif_text.setPlainText(egif)
            except Exception as e:
                self.egif_text.setPlainText(f"[EGIF generation failed: {e}]")
            
            # Clear metadata panel and timeline (file load has no UoD metadata)
            self.metadata_panel.clear()
            self.history_timeline.hide()
            
            # Update state
            self._current_file = Path(file_path)
            self._current_uod = None  # No UoD for file loads
            self.save_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            
            # Show success (shorter message)
            file_name = Path(file_path).name
            status_msg = f"Loaded: {file_name}"
            if 'layout_deltas' in data and data['layout_deltas']:
                delta_count = len(data['layout_deltas'])
                status_msg += f" ({delta_count} position overrides)"
            parent = self.window()
            if hasattr(parent, 'statusBar'):
                parent.statusBar().showMessage(status_msg, 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading EGI",
                f"Failed to load EGI file:\n\n{str(e)}"
            )
    
    def _on_save_egi(self):
        """Save current EGI with layout deltas."""
        egi = self.controller.egi_model
        if not egi:
            return
        
        # Get save location
        default_path = str(self._current_file) if self._current_file else str(Path.home() / "untitled.egi.json")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save EGI",
            default_path,
            "EGI Files (*.json *.egi.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            import json
            from egi_io import to_dict
            
            # Build payload with EGI and layout deltas
            payload = to_dict(egi)
            
            print(f"=== Saving EGI with layout deltas (Organon) ===")
            print(f"  Current layout_deltas: {len(self.controller.layout_deltas)}")
            
            # Add layout deltas (user position overrides)
            if self.controller.layout_deltas:
                deltas_dict = {}
                for element_id, delta in self.controller.layout_deltas.items():
                    deltas_dict[element_id] = {
                        'type': delta.delta_type,
                        'position': list(delta.new_position)
                    }
                    print(f"  Saving delta: {element_id} -> {delta.new_position}")
                payload['layout_deltas'] = deltas_dict
                print(f"  Total deltas saved: {len(deltas_dict)}")
            else:
                print("  No layout deltas to save")
            
            # Save to file
            Path(file_path).write_text(
                json.dumps(payload, indent=2, sort_keys=True),
                encoding="utf-8"
            )
            
            self._current_file = Path(file_path)
            delta_count = len(self.controller.layout_deltas)
            status_msg = f"Saved: {Path(file_path).name}"
            if delta_count > 0:
                status_msg += f" ({delta_count} position overrides)"
            
            parent = self.window()
            if hasattr(parent, 'statusBar'):
                parent.statusBar().showMessage(status_msg, 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving EGI",
                f"Failed to save EGI file:\n\n{str(e)}"
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
        if not self._current_uod or not self._current_uod.is_historical:
            return
        
        try:
            # Get state snapshot
            state = self._current_uod.get_state(state_id)
            
            # Load state's EGI into controller
            self.controller.load_egi(state.egi)
            
            # Restore layout deltas from this state if present
            if state.diagram_metadata and 'layout_deltas' in state.diagram_metadata:
                from definitive_egi_layout_engine import LayoutDelta
                for element_id, delta_data in state.diagram_metadata['layout_deltas'].items():
                    if isinstance(delta_data, dict) and 'type' in delta_data and 'position' in delta_data:
                        delta = LayoutDelta(
                            element_id=element_id,
                            delta_type=delta_data['type'],
                            new_position=tuple(delta_data['position'])
                        )
                        self.controller.layout_deltas[element_id] = delta
                self.controller._trigger_fast_update()
            
            # Get renderable DTO
            dto = self.controller.get_renderable_dto()
            
            # Display (fit_to_view=True for state navigation)
            self.canvas.display_dto(dto, state.egi, fit_to_view=True)
            
            # Update EGIF (use cached if available)
            egif = state.linear_forms.get("egif")
            if not egif:
                egif = generate_egif(state.egi)
            self.egif_text.setPlainText(egif)
            
            # Update history timeline to highlight new current state
            # (This will re-render with the selected state as current)
            self._current_uod.history.current_state_id = state_id
            self.history_timeline.update_history(self._current_uod)
            
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
        if egi and self._current_uod:
            # Emit tuple of (EGI, source UoD)
            self.edit_in_ergasterion.emit((egi, self._current_uod))
    
    def handle_modified_uod_from_ergasterion(self, modified_uod):
        """
        Handle modified UoD returned from Ergasterion.
        
        Prompts user to save changes to tomos.
        """
        from tomos_service import TomosService
        from datetime import datetime
        
        reply = QMessageBox.question(
            self,
            "Save Modifications?",
            f"Save modifications to '{modified_uod.name}' to the tomos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Initialize tomos service
                tomos_root = Path(__file__).parent.parent.parent.parent / "tomos"
                tomos = TomosService(tomos_root)
                
                # Update last modified time
                modified_uod.metadata.last_modified = datetime.now()
                
                # Save to tomos
                tomos.save_uod(modified_uod)
                
                # Reload the UoD to see changes
                self._current_uod = tomos.load_uod(modified_uod.uod_id)
                if self._current_uod:
                    # Reload in display
                    self.controller.load_egi(self._current_uod.current_egi)
                    
                    # Restore layout deltas if present
                    if self._current_uod.current_layout_deltas:
                        from definitive_egi_layout_engine import LayoutDelta
                        for element_id, delta_data in self._current_uod.current_layout_deltas.items():
                            if isinstance(delta_data, dict) and 'type' in delta_data and 'position' in delta_data:
                                delta = LayoutDelta(
                                    element_id=element_id,
                                    delta_type=delta_data['type'],
                                    new_position=tuple(delta_data['position'])
                                )
                                self.controller.layout_deltas[element_id] = delta
                        self.controller._trigger_fast_update()
                    
                    dto = self.controller.get_renderable_dto()
                    self.canvas.display_dto(dto, self._current_uod.current_egi, fit_to_view=True)
                    
                    # Update panels
                    egif = generate_egif(self._current_uod.current_egi)
                    self.egif_text.setPlainText(egif)
                    self.metadata_panel.update_metadata(self._current_uod)
                    self.history_timeline.update_history(self._current_uod)
                
                QMessageBox.information(
                    self,
                    "Saved",
                    f"Successfully saved modifications to '{modified_uod.name}'"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Saving",
                    f"Failed to save modifications:\n\n{str(e)}"
                )
