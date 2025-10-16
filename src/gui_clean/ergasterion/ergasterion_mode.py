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
from enum import Enum

from PySide6.QtCore import Qt, Signal

class WorkflowMode(Enum):
    """Ergasterion workflow modes."""
    EDIT_EXISTING = "edit"      # Editing UoD from Organon
    CREATE_NEW = "create"        # Creating new diagram
    ISOLATED_PRACTICE = "practice"  # Just practicing, no destination
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
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDMetadata,
    UoDType,
    UoDCategory,
)
from datetime import datetime

# Import Qt-based interactive canvas
from gui_clean.common.qt_diagram_canvas import QtDiagramCanvas


class ErgasterionMode(QWidget):
    """
    Ergasterion mode widget - Interactive editing and transformation practice.
    
    Layout:
    - Top: Toolbar (Load, Save, Undo, Redo, New)
    - Left: Interactive diagram canvas
    - Right: Transformation panel + Selection info + EGIF
    """
    
    # Signals
    uod_modified = Signal(object)  # Emits modified UoD to Organon (edit mode)
    new_uod_created = Signal(object)  # Emits new UoD to Organon for addition to tomos
    send_to_agon = Signal(object)  # Emits UoD to Agon for EPG
    cancelled = Signal()  # Emits when user cancels without saving
    
    def __init__(self, diagram_controller: DiagramController, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.controller = diagram_controller
        self._current_file: Optional[Path] = None
        self._current_uod: Optional[UniverseOfDiscourse] = None  # Current UoD
        self._workflow_mode: WorkflowMode = WorkflowMode.ISOLATED_PRACTICE
        self._has_unsaved_changes: bool = False
        
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
        
        # Left: Interactive diagram canvas (Qt-based)
        self.canvas = QtDiagramCanvas()
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
        self.new_btn.setToolTip("Create empty graph for practice")
        toolbar_layout.addWidget(self.new_btn)
        
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
        
        # Workflow mode indicator
        self.mode_label = QLabel()
        self.mode_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        toolbar_layout.addWidget(self.mode_label)
        
        toolbar_layout.addSpacing(10)
        
        # Destination buttons (visibility depends on workflow mode)
        self.return_to_organon_btn = QPushButton("📚 Return to Organon")
        self.return_to_organon_btn.clicked.connect(self._on_return_to_organon)
        self.return_to_organon_btn.setEnabled(False)
        self.return_to_organon_btn.setToolTip("Return modified UoD to Organon")
        self.return_to_organon_btn.setVisible(False)
        toolbar_layout.addWidget(self.return_to_organon_btn)
        
        self.send_to_organon_btn = QPushButton("📚 Send to Organon")
        self.send_to_organon_btn.clicked.connect(self._on_send_to_organon)
        self.send_to_organon_btn.setEnabled(False)
        self.send_to_organon_btn.setToolTip("Add this new diagram to the tomos")
        self.send_to_organon_btn.setVisible(False)
        toolbar_layout.addWidget(self.send_to_organon_btn)
        
        self.send_to_agon_btn = QPushButton("⚔️ Send to Agon")
        self.send_to_agon_btn.clicked.connect(self._on_send_to_agon)
        self.send_to_agon_btn.setEnabled(False)
        self.send_to_agon_btn.setToolTip("Use this diagram in the Endoporeutic Game")
        self.send_to_agon_btn.setVisible(False)
        toolbar_layout.addWidget(self.send_to_agon_btn)
        
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
    
    def _update_workflow_ui(self):
        """Update toolbar buttons based on current workflow mode."""
        # Hide all destination buttons first
        self.return_to_organon_btn.setVisible(False)
        self.send_to_organon_btn.setVisible(False)
        self.send_to_agon_btn.setVisible(False)
        
        if self._workflow_mode == WorkflowMode.EDIT_EXISTING:
            # Editing existing UoD from Organon
            self.mode_label.setText("Mode: Editing")
            self.return_to_organon_btn.setVisible(True)
            self.return_to_organon_btn.setEnabled(True)
            
        elif self._workflow_mode == WorkflowMode.CREATE_NEW:
            # Creating new diagram
            self.mode_label.setText("Mode: Creating New")
            self.send_to_organon_btn.setVisible(True)
            self.send_to_organon_btn.setEnabled(True)
            self.send_to_agon_btn.setVisible(True)
            self.send_to_agon_btn.setEnabled(True)
            
        elif self._workflow_mode == WorkflowMode.ISOLATED_PRACTICE:
            # Just practicing
            self.mode_label.setText("Mode: Practice")
            self.send_to_organon_btn.setVisible(True)
            self.send_to_organon_btn.setEnabled(True)
            self.send_to_agon_btn.setVisible(True)
            self.send_to_agon_btn.setEnabled(True)
    
    def _on_new_graph(self):
        """Create a new practice session (empty UoD)."""
        from egi_core_dau import create_empty_graph
        import uuid
        
        # Create empty EGI
        egi = create_empty_graph()
        
        # Create new practice session UoD
        metadata = UoDMetadata(
            uod_id=f"practice_{uuid.uuid4().hex[:8]}",
            uod_type=UoDType.STANDALONE,
            name=f"Practice Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description="Isolated practice session",
            category=UoDCategory.PRACTICE_SESSION,
            created=datetime.now(),
            last_modified=datetime.now(),
            authors=["Current User"],
        )
        
        self._current_uod = UniverseOfDiscourse(
            metadata=metadata,
            current_egi=egi,
            history=None
        )
        
        # Load into controller
        self.controller.load_egi(egi)
        
        # Set workflow mode
        self._workflow_mode = WorkflowMode.CREATE_NEW
        self._update_workflow_ui()
        
        # Display
        self._refresh_display()
        
        self._current_file = None
        self._has_unsaved_changes = False
        
        self._show_status("Created new diagram - ready to send to Organon or Agon")
    
    # File operations removed - Organon manages all tomos I/O
    # Ergasterion receives UoDs from Organon and returns them modified
    
    def _on_undo(self):
        """Undo last action."""
        # TODO: Implement with CommandExecutor
        self._show_status("Undo: Not yet implemented")
    
    def _on_redo(self):
        """Redo last undone action."""
        # TODO: Implement with CommandExecutor
        self._show_status("Redo: Not yet implemented")
    
    def _prepare_modified_uod(self) -> Optional[UniverseOfDiscourse]:
        """Prepare the current UoD with modifications for return to Organon."""
        if not self._current_uod:
            return None
        
        # Update UoD with current EGI
        egi = self.controller.get_egi_model()
        if egi:
            self._current_uod.current_egi = egi
            
            # Update layout deltas
            if self.controller.layout_deltas:
                deltas_dict = {}
                for element_id, delta in self.controller.layout_deltas.items():
                    deltas_dict[element_id] = {
                        'type': delta.delta_type,
                        'position': list(delta.new_position)
                    }
                self._current_uod.current_layout_deltas = deltas_dict
            
            # Update metadata
            self._current_uod.metadata.last_modified = datetime.now()
        
        return self._current_uod
    
    def _on_return_to_organon(self):
        """Return modified UoD to Organon (for EDIT_EXISTING mode)."""
        if not self._current_uod:
            self.cancelled.emit()
            return
        
        # Confirm return
        reply = QMessageBox.question(
            self,
            "Return to Organon?",
            f"Return modifications to '{self._current_uod.name}' to Organon for saving?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Prepare modified UoD
        modified_uod = self._prepare_modified_uod()
        if modified_uod:
            self.uod_modified.emit(modified_uod)
            self._has_unsaved_changes = False
            self._show_status("Returned modifications to Organon")
        else:
            self.cancelled.emit()
    
    def _on_send_to_organon(self):
        """Send new UoD to Organon for addition to tomos (for CREATE_NEW mode)."""
        if not self._current_uod:
            QMessageBox.warning(
                self,
                "No Diagram",
                "Create a diagram first before sending to Organon."
            )
            return
        
        # Prepare UoD
        uod = self._prepare_modified_uod()
        if uod:
            self.new_uod_created.emit(uod)
            self._has_unsaved_changes = False
            self._show_status("Sent new diagram to Organon for addition to tomos")
    
    def _on_send_to_agon(self):
        """Send UoD to Agon for use in Endoporeutic Game."""
        if not self._current_uod:
            QMessageBox.warning(
                self,
                "No Diagram",
                "Create a diagram first before sending to Agon."
            )
            return
        
        # Prepare UoD
        uod = self._prepare_modified_uod()
        if uod:
            self.send_to_agon.emit(uod)
            self._has_unsaved_changes = False
            self._show_status("Sent diagram to Agon for Endoporeutic Game")
    
    def _on_element_selected(self, element_id: str):
        """Handle single element selection."""
        print(f"✓ Handler received element_selected: {element_id}")
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
        """Handle element drag completed - FAST PATH."""
        # Update position through controller (with validation and DTO update)
        success = self.controller.update_element_position(element_id, new_pos)
        
        if success:
            # FAST PATH: Controller already updated DTO, just refresh display
            # No relayout needed - this is a logic-indifferent aesthetic change
            # fit_to_view=False to preserve zoom/pan and manual positioning
            dto = self.controller.current_dto
            egi = self.controller.egi_model
            if dto and egi:
                self.canvas.display_dto(dto, egi, fit_to_view=False)
            self._show_status(f"Moved {element_id} to ({new_pos[0]:.1f}, {new_pos[1]:.1f})")
        else:
            # Position rejected - revert by redisplaying current DTO
            self._show_status(f"Invalid position for {element_id}", error=True)
            dto = self.controller.current_dto
            egi = self.controller.egi_model
            if dto and egi:
                self.canvas.display_dto(dto, egi, fit_to_view=False)
    
    def _on_apply_rule(self, rule_name: str):
        """Apply a transformation rule and record in UoD history if historical."""
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
            # Mark as modified
            self._has_unsaved_changes = True
            
            # Update UoD with new EGI
            if self._current_uod:
                new_egi = self.controller.get_egi_model()
                self._current_uod.current_egi = new_egi
                self._current_uod.metadata.last_modified = datetime.now()
                
                # If historical, record transformation
                if self._current_uod.is_historical:
                    # TODO: Record transformation in history
                    # This would require TransformationContext and TransformationResult
                    pass
            
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
        print("=== _refresh_display called ===")
        dto = self.controller.get_renderable_dto()
        egi = self.controller.get_egi_model()
        
        print(f"=== dto={dto is not None}, egi={egi is not None} ===")
        if dto and egi:
            print("=== Calling canvas.display_dto ===")
            # fit_to_view=True for initial loads and full relayouts
            self.canvas.display_dto(dto, egi, fit_to_view=True)
            
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
    
    def load_egi_for_editing(self, egi: RelationalGraphWithCuts, source_uod: Optional[UniverseOfDiscourse] = None):
        """
        Load an EGI from Organon for editing.
        
        Args:
            egi: The EGI to load
            source_uod: Optional source UoD (if provided, edit it directly; otherwise create new practice session)
        """
        import uuid
        
        print(f"=== Ergasterion.load_egi_for_editing called with {len(egi.V)}V, {len(egi.E)}E ===")
        
        # If source UoD provided, edit it directly
        if source_uod:
            print(f"=== Editing existing UoD: {source_uod.uod_id} ===")
            self._current_uod = source_uod
            # Update the EGI in case it changed
            self._current_uod.current_egi = egi
            # Set EDIT mode
            self._workflow_mode = WorkflowMode.EDIT_EXISTING
        else:
            # Create new practice session (no source provided)
            print("=== Creating new practice session ===")
            name = f"Practice Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            description = "Practice session from Organon"
            
            metadata = UoDMetadata(
                uod_id=f"practice_{uuid.uuid4().hex[:8]}",
                uod_type=UoDType.STANDALONE,
                name=name,
                description=description,
                category=UoDCategory.PRACTICE_SESSION,
                created=datetime.now(),
                last_modified=datetime.now(),
                authors=["Current User"],
                related_uods=[],
            )
            
            self._current_uod = UniverseOfDiscourse(
                metadata=metadata,
                current_egi=egi,
                history=None
            )
            # Set PRACTICE mode
            self._workflow_mode = WorkflowMode.ISOLATED_PRACTICE
        
        # Update UI based on mode
        self._update_workflow_ui()
        
        self.controller.load_egi(egi)
        print("=== Calling _refresh_display ===")
        self._refresh_display()
        self._current_file = None
        self._has_unsaved_changes = False
        
        mode_name = "editing" if source_uod else "practice"
        self._show_status(f"Loaded graph from Organon for {mode_name}")
