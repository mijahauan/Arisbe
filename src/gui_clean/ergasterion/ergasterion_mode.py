"""
Ergasterion Mode - Interactive editing and transformation practice.

Provides interactive EGI diagram editing with:
- Interactive canvas (click, drag, select)
- Element repositioning with validation
- Transformation toolbar (DC+/-, INS, ERA, IT+/-)
- Undo/Redo controls
- Practice mode feedback
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Optional, List, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from diagram_controller import DiagramController
from egi_core_dau import RelationalGraphWithCuts
from egi_io import load_egi_json
from egif_generator_dau import generate_egif

# Import interactive canvas
from gui_clean.common.interactive_diagram_canvas import InteractiveDiagramCanvas


class ErgasterionMode(QWidget):
    """
    Ergasterion mode widget - Interactive editing and transformation practice.
    
    Layout:
    - Top: Toolbar (Load, Save, Undo, Redo, New)
    - Left: Interactive diagram canvas
    - Right: Transformation panel + Selection info + EGIF
    """
    
    # Signal when returning to Organon
    save_to_organon = Signal(object)  # Emits EGI
    
    def __init__(self, diagram_controller: DiagramController, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.controller = diagram_controller
        self._current_file: Optional[Path] = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Create the Ergasterion UI."""
        layout = QVBoxLayout(self)
        
        # Top: Action toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Main content: Canvas + Right panels
        content = QHBoxLayout()
        
        # Left: Interactive diagram canvas
        self.canvas = InteractiveDiagramCanvas()
        content.addWidget(self.canvas, stretch=3)
        
        # Right: Control panels
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        
        # Transformation panel
        transform_panel = self._create_transformation_panel()
        right_panel.addWidget(transform_panel)
        
        # Selection info panel
        selection_panel = self._create_selection_panel()
        right_panel.addWidget(selection_panel)
        
        # EGIF panel
        egif_panel = self._create_egif_panel()
        right_panel.addWidget(egif_panel)
        
        content.addLayout(right_panel, stretch=1)
        
        layout.addLayout(content)
    
    def _create_toolbar(self) -> QWidget:
        """Create the main toolbar."""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # File operations
        self.new_btn = QPushButton("📄 New")
        self.new_btn.clicked.connect(self._on_new_graph)
        self.new_btn.setToolTip("Create empty graph")
        toolbar_layout.addWidget(self.new_btn)
        
        self.load_btn = QPushButton("📂 Load...")
        self.load_btn.clicked.connect(self._on_load_egi)
        self.load_btn.setToolTip("Load EGI from file")
        toolbar_layout.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("💾 Save...")
        self.save_btn.clicked.connect(self._on_save_egi)
        self.save_btn.setEnabled(False)
        self.save_btn.setToolTip("Save EGI to file")
        toolbar_layout.addWidget(self.save_btn)
        
        toolbar_layout.addSpacing(20)
        
        # Undo/Redo
        self.undo_btn = QPushButton("↶ Undo")
        self.undo_btn.clicked.connect(self._on_undo)
        self.undo_btn.setEnabled(False)
        self.undo_btn.setToolTip("Undo last action")
        toolbar_layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("↷ Redo")
        self.redo_btn.clicked.connect(self._on_redo)
        self.redo_btn.setEnabled(False)
        self.redo_btn.setToolTip("Redo undone action")
        toolbar_layout.addWidget(self.redo_btn)
        
        toolbar_layout.addStretch()
        
        # Return to Organon
        self.return_btn = QPushButton("📚 Return to Organon")
        self.return_btn.clicked.connect(self._on_return_to_organon)
        self.return_btn.setEnabled(False)
        toolbar_layout.addWidget(self.return_btn)
        
        return toolbar
    
    def _create_transformation_panel(self) -> QWidget:
        """Create the transformation rule panel."""
        group = QGroupBox("⚙️ Transformations")
        layout = QVBoxLayout(group)
        
        info = QLabel("Select elements, then apply a transformation rule:")
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(info)
        
        # Double Cut rules
        dc_layout = QHBoxLayout()
        dc_label = QLabel("Double Cut:")
        dc_label.setStyleSheet("font-weight: bold;")
        dc_layout.addWidget(dc_label)
        
        self.dc_insert_btn = QPushButton("DC+")
        self.dc_insert_btn.clicked.connect(lambda: self._on_apply_rule("DC+"))
        self.dc_insert_btn.setEnabled(False)
        self.dc_insert_btn.setToolTip("Insert double cut around selection")
        dc_layout.addWidget(self.dc_insert_btn)
        
        self.dc_erase_btn = QPushButton("DC-")
        self.dc_erase_btn.clicked.connect(lambda: self._on_apply_rule("DC-"))
        self.dc_erase_btn.setEnabled(False)
        self.dc_erase_btn.setToolTip("Erase double cut")
        dc_layout.addWidget(self.dc_erase_btn)
        
        layout.addLayout(dc_layout)
        
        # Insertion/Erasure
        ins_era_layout = QHBoxLayout()
        
        self.ins_btn = QPushButton("INS")
        self.ins_btn.clicked.connect(lambda: self._on_apply_rule("INS"))
        self.ins_btn.setEnabled(False)
        self.ins_btn.setToolTip("Insert subgraph (even area)")
        ins_era_layout.addWidget(self.ins_btn)
        
        self.era_btn = QPushButton("ERA")
        self.era_btn.clicked.connect(lambda: self._on_apply_rule("ERA"))
        self.era_btn.setEnabled(False)
        self.era_btn.setToolTip("Erase subgraph (odd area)")
        ins_era_layout.addWidget(self.era_btn)
        
        layout.addLayout(ins_era_layout)
        
        # Iteration/Deiteration
        iter_layout = QHBoxLayout()
        
        self.iter_insert_btn = QPushButton("IT+")
        self.iter_insert_btn.clicked.connect(lambda: self._on_apply_rule("IT+"))
        self.iter_insert_btn.setEnabled(False)
        self.iter_insert_btn.setToolTip("Insert iteration (copy)")
        iter_layout.addWidget(self.iter_insert_btn)
        
        self.iter_erase_btn = QPushButton("IT-")
        self.iter_erase_btn.clicked.connect(lambda: self._on_apply_rule("IT-"))
        self.iter_erase_btn.setEnabled(False)
        self.iter_erase_btn.setToolTip("Remove iteration (delete copy)")
        iter_layout.addWidget(self.iter_erase_btn)
        
        layout.addLayout(iter_layout)
        
        # Validation message
        self.validation_label = QLabel("")
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("font-size: 10px; padding: 5px;")
        layout.addWidget(self.validation_label)
        
        layout.addStretch()
        
        return group
    
    def _create_selection_panel(self) -> QWidget:
        """Create the selection info panel."""
        group = QGroupBox("🎯 Selection")
        layout = QVBoxLayout(group)
        
        self.selection_list = QListWidget()
        self.selection_list.setMaximumHeight(100)
        layout.addWidget(self.selection_list)
        
        clear_btn = QPushButton("Clear Selection")
        clear_btn.clicked.connect(self._on_clear_selection)
        layout.addWidget(clear_btn)
        
        return group
    
    def _create_egif_panel(self) -> QWidget:
        """Create the EGIF display panel."""
        group = QGroupBox("📝 EGIF (Linear Form)")
        layout = QVBoxLayout(group)
        
        self.egif_text = QTextEdit()
        self.egif_text.setReadOnly(True)
        self.egif_text.setFont("Courier New")
        self.egif_text.setPlaceholderText("EGIF will appear here...")
        layout.addWidget(self.egif_text)
        
        return group
    
    def _connect_signals(self):
        """Connect canvas signals to handlers."""
        self.canvas.element_selected.connect(self._on_element_selected)
        self.canvas.elements_selected.connect(self._on_elements_selected)
        self.canvas.element_moved.connect(self._on_element_moved)
        self.canvas.selection_cleared.connect(self._on_selection_cleared)
    
    def _on_new_graph(self):
        """Create a new empty graph."""
        from egi_core_dau import create_empty_graph
        
        # Create empty EGI
        egi = create_empty_graph()
        
        # Load into controller
        self.controller.load_egi(egi)
        
        # Display
        self._refresh_display()
        
        self._current_file = None
        self.save_btn.setEnabled(True)
        self.return_btn.setEnabled(True)
        
        self._show_status("Created new empty graph")
    
    def _on_load_egi(self):
        """Load an EGI file for editing."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load EGI",
            str(Path.home()),
            "EGI Files (*.json *.egi.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Load EGI
            egi = load_egi_json(file_path)
            
            # Load into controller
            self.controller.load_egi(egi)
            
            # Display
            self._refresh_display()
            
            self._current_file = Path(file_path)
            self.save_btn.setEnabled(True)
            self.return_btn.setEnabled(True)
            
            self._show_status(f"Loaded: {Path(file_path).name}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading EGI",
                f"Failed to load EGI file:\n\n{str(e)}"
            )
    
    def _on_save_egi(self):
        """Save current EGI to file."""
        egi = self.controller.get_egi_model()
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
            from egi_io import save_egi_json
            save_egi_json(egi, file_path)
            
            self._current_file = Path(file_path)
            self._show_status(f"Saved: {Path(file_path).name}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving EGI",
                f"Failed to save EGI file:\n\n{str(e)}"
            )
    
    def _on_undo(self):
        """Undo last action."""
        # TODO: Implement with CommandExecutor
        self._show_status("Undo: Not yet implemented")
    
    def _on_redo(self):
        """Redo last undone action."""
        # TODO: Implement with CommandExecutor
        self._show_status("Redo: Not yet implemented")
    
    def _on_return_to_organon(self):
        """Return to Organon mode."""
        egi = self.controller.get_egi_model()
        if egi:
            self.save_to_organon.emit(egi)
            self._show_status("Switched to Organon mode")
    
    def _on_element_selected(self, element_id: str):
        """Handle single element selection."""
        self.selection_list.clear()
        self.selection_list.addItem(element_id)
        self._update_transformation_buttons()
        self._show_status(f"Selected: {element_id}")
    
    def _on_elements_selected(self, element_ids: List[str]):
        """Handle multiple element selection."""
        self.selection_list.clear()
        for element_id in element_ids:
            self.selection_list.addItem(element_id)
        self._update_transformation_buttons()
        self._show_status(f"Selected: {len(element_ids)} elements")
    
    def _on_selection_cleared(self):
        """Handle selection cleared."""
        self.selection_list.clear()
        self._update_transformation_buttons()
        self._show_status("Selection cleared")
    
    def _on_clear_selection(self):
        """Clear current selection."""
        self.canvas.clear_selection()
    
    def _on_element_moved(self, element_id: str, new_pos: Tuple[float, float]):
        """Handle element drag completed."""
        # Update position through controller (with validation)
        success = self.controller.update_element_position(element_id, new_pos)
        
        if success:
            # Refresh display
            self._refresh_display()
            self._show_status(f"Moved {element_id} to ({new_pos[0]:.1f}, {new_pos[1]:.1f})")
        else:
            # Position rejected - show error
            self._show_status(f"Invalid position for {element_id}", error=True)
            # Revert display
            self._refresh_display()
    
    def _on_apply_rule(self, rule_name: str):
        """Apply a transformation rule."""
        selection = self.canvas.get_selected_elements()
        
        if not selection:
            self.validation_label.setText("⚠️ No elements selected")
            self.validation_label.setStyleSheet("color: orange; font-size: 10px; padding: 5px;")
            return
        
        # Determine target area (sheet for now - will add area selection later)
        target_area = "sheet"  # TODO: Get from context or user selection
        
        # Apply rule through controller
        success = self.controller.apply_formal_rule(rule_name, selection, target_area)
        
        if success:
            # Refresh display
            self._refresh_display()
            self.validation_label.setText(f"✓ Applied {rule_name}")
            self.validation_label.setStyleSheet("color: green; font-size: 10px; padding: 5px;")
            self._show_status(f"Applied {rule_name}")
        else:
            # Rule rejected - show error
            self.validation_label.setText(f"✗ Cannot apply {rule_name}")
            self.validation_label.setStyleSheet("color: red; font-size: 10px; padding: 5px;")
            self._show_status(f"Cannot apply {rule_name}", error=True)
    
    def _update_transformation_buttons(self):
        """Enable/disable transformation buttons based on selection."""
        has_selection = bool(self.canvas.get_selected_elements())
        
        # Enable all buttons if there's a selection
        # (Controller will validate specific rules)
        self.dc_insert_btn.setEnabled(has_selection)
        self.dc_erase_btn.setEnabled(has_selection)
        self.ins_btn.setEnabled(has_selection)
        self.era_btn.setEnabled(has_selection)
        self.iter_insert_btn.setEnabled(has_selection)
        self.iter_erase_btn.setEnabled(has_selection)
        
        # Clear validation message when selection changes
        self.validation_label.setText("")
    
    def _refresh_display(self):
        """Refresh the diagram display."""
        dto = self.controller.get_renderable_dto()
        egi = self.controller.get_egi_model()
        
        if dto and egi:
            self.canvas.display_dto(dto, egi)
            
            # Update EGIF
            try:
                egif = generate_egif(egi)
                self.egif_text.setPlainText(egif)
            except Exception as e:
                self.egif_text.setPlainText(f"[EGIF generation failed: {e}]")
    
    def _show_status(self, message: str, error: bool = False):
        """Show status message."""
        parent = self.window()
        if hasattr(parent, 'statusBar'):
            parent.statusBar().showMessage(message, 3000 if not error else 5000)
    
    def load_egi_for_editing(self, egi: RelationalGraphWithCuts):
        """
        Load an EGI from Organon for editing.
        
        Args:
            egi: The EGI to load
        """
        self.controller.load_egi(egi)
        self._refresh_display()
        self._current_file = None
        self.save_btn.setEnabled(True)
        self.return_btn.setEnabled(True)
        self._show_status("Loaded graph from Organon")
