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

from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from PySide6.QtCore import Qt, Signal

class WorkflowMode(Enum):
    """Ergasterion workflow modes."""
    EDIT_EXISTING = "edit"      # Editing UoD from Organon
    CREATE_NEW = "create"        # Creating new diagram
    ISOLATED_PRACTICE = "practice"  # Just practicing, no destination
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QRadioButton,
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


class StartingContextDialog(QDialog):
    """Dialog for selecting starting context when creating new diagrams."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Diagram")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Choose Starting Context:")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Radio button group
        self.button_group = QButtonGroup(self)
        
        # Option 1: Empty Sheet
        self.empty_radio = QRadioButton("Empty Sheet")
        self.button_group.addButton(self.empty_radio)
        layout.addWidget(self.empty_radio)
        
        empty_desc = QLabel(
            "   Start with bare sheet of assertion.\n"
            "   Apply DC+ to create context, or assert vertex."
        )
        empty_desc.setStyleSheet("color: #666; font-size: 11px; padding-left: 20px;")
        layout.addWidget(empty_desc)
        
        layout.addSpacing(10)
        
        # Option 2: Double Cut (Recommended)
        self.double_cut_radio = QRadioButton("Double Cut (Recommended)")
        self.double_cut_radio.setChecked(True)  # Default
        self.button_group.addButton(self.double_cut_radio)
        layout.addWidget(self.double_cut_radio)
        
        dc_desc = QLabel(
            "   Sheet with double cut already in place.\n"
            "   Standard starting point for composition.\n"
            "   Inner area is negative context (INS enabled)."
        )
        dc_desc.setStyleSheet("color: #666; font-size: 11px; padding-left: 20px;")
        layout.addWidget(dc_desc)
        
        layout.addSpacing(10)
        
        # Option 3: Composition Context (Future)
        self.composition_radio = QRadioButton("Composition Context")
        self.composition_radio.setEnabled(False)  # Not yet implemented
        self.button_group.addButton(self.composition_radio)
        layout.addWidget(self.composition_radio)
        
        comp_desc = QLabel(
            "   Select from predefined composition contexts.\n"
            "   (Coming soon - requires context selection workflow)"
        )
        comp_desc.setStyleSheet("color: #999; font-size: 11px; padding-left: 20px; font-style: italic;")
        layout.addWidget(comp_desc)
        
        layout.addSpacing(20)
        
        # Info about formal rules
        info = QLabel(
            "ℹ️  All actions follow formal transformation rules.\n"
            "   Sheet allows: DC+ (double cut) and adding vertices.\n"
            "   Negative contexts (inside cuts) allow: INS (insertion)."
        )
        info.setStyleSheet(
            "background-color: #f0f8ff; "
            "border: 1px solid #b0d4f1; "
            "border-radius: 4px; "
            "padding: 10px; "
            "font-size: 10px; "
            "color: #333;"
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create")
        create_btn.setDefault(True)
        create_btn.clicked.connect(self.accept)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
    
    def get_selected_context(self) -> str:
        """Get the selected context type."""
        if self.empty_radio.isChecked():
            return "empty"
        elif self.double_cut_radio.isChecked():
            return "double_cut"
        elif self.composition_radio.isChecked():
            return "composition"
        else:
            return "double_cut"  # Default


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
        
        toolbar_layout.addSpacing(20)
        
        # View controls
        self.zoom_in_btn = QPushButton("🔍+")
        self.zoom_in_btn.clicked.connect(self._on_zoom_in)
        self.zoom_in_btn.setToolTip("Zoom in (or use mouse wheel)")
        self.zoom_in_btn.setMaximumWidth(45)
        toolbar_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = QPushButton("🔍−")
        self.zoom_out_btn.clicked.connect(self._on_zoom_out)
        self.zoom_out_btn.setToolTip("Zoom out (or use mouse wheel)")
        self.zoom_out_btn.setMaximumWidth(45)
        toolbar_layout.addWidget(self.zoom_out_btn)
        
        self.reset_zoom_btn = QPushButton("⟲ Fit")
        self.reset_zoom_btn.clicked.connect(self._on_reset_zoom)
        self.reset_zoom_btn.setToolTip("Reset zoom to fit entire diagram")
        self.reset_zoom_btn.setMaximumWidth(55)
        toolbar_layout.addWidget(self.reset_zoom_btn)
        
        # Add help text for pan
        pan_label = QLabel("Pan: Space+Drag")
        pan_label.setStyleSheet("color: #888; font-size: 9px; padding: 0px 10px;")
        pan_label.setToolTip("Hold Space and drag to pan the view, or use middle mouse button")
        toolbar_layout.addWidget(pan_label)
        
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
        
        # Clipboard section
        clipboard_label = QLabel("Insertion Clipboard:")
        clipboard_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(clipboard_label)
        
        clipboard_layout = QHBoxLayout()
        
        self.add_to_clipboard_btn = QPushButton("📋 Add to Clipboard")
        self.add_to_clipboard_btn.clicked.connect(self._on_add_to_clipboard)
        self.add_to_clipboard_btn.setEnabled(False)
        self.add_to_clipboard_btn.setToolTip("Add selected closed subgraph to insertion clipboard")
        clipboard_layout.addWidget(self.add_to_clipboard_btn)
        
        self.browse_clipboard_btn = QPushButton("🔍 Browse")
        self.browse_clipboard_btn.clicked.connect(self._on_browse_clipboard)
        self.browse_clipboard_btn.setToolTip("Browse insertion clipboard")
        self.browse_clipboard_btn.setMaximumWidth(80)
        clipboard_layout.addWidget(self.browse_clipboard_btn)
        
        layout.addLayout(clipboard_layout)
        
        # Insertion/Erasure
        ins_era_label = QLabel("Formal Rules:")
        ins_era_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(ins_era_label)
        
        ins_era_layout = QHBoxLayout()
        
        self.ins_btn = QPushButton("INS")
        self.ins_btn.clicked.connect(self._on_start_ins_workflow)
        self.ins_btn.setEnabled(False)
        self.ins_btn.setToolTip("Insert subgraph from clipboard (negative area)")
        ins_era_layout.addWidget(self.ins_btn)
        
        self.era_btn = QPushButton("ERA")
        self.era_btn.clicked.connect(lambda: self._on_apply_rule("ERA"))
        self.era_btn.setEnabled(False)
        self.era_btn.setToolTip("Erase subgraph (positive area)")
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
        self.canvas.cut_moved.connect(self._on_cut_moved)
        self.canvas.cut_resized.connect(self._on_cut_resized)
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
        """Create a new diagram with user-selected starting context."""
        # Show context selection dialog
        dialog = StartingContextDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            context_type = dialog.get_selected_context()
            self._create_new_graph_with_context(context_type)
    
    def _create_new_graph_with_context(self, context_type: str):
        """Create a new graph with the specified starting context."""
        from egi_core_dau import RelationalGraphWithCuts
        import uuid
        
        # Build EGI based on context type
        if context_type == "empty":
            # Empty sheet - user applies DC+ or adds vertex manually
            egi = self._create_empty_sheet()
            description = "Empty sheet of assertion"
            
        elif context_type == "double_cut":
            # Sheet with one double cut (standard starting point)
            egi = self._create_with_double_cut()
            description = "Sheet with double cut for composition"
            
        elif context_type == "composition":
            # Future: Let user select from composition contexts
            # For now, same as double cut
            egi = self._create_with_double_cut()
            description = "Composition context (double cut)"
            
        else:
            self._show_status(f"Unknown context type: {context_type}", error=True)
            return
        
        # Create new practice session UoD
        metadata = UoDMetadata(
            uod_id=f"new_{uuid.uuid4().hex[:8]}",
            uod_type=UoDType.STANDALONE,
            name=f"New Diagram {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description=description,
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
        if not self.controller.load_egi(egi):
            # Load failed - show error to user
            error_msg = self.controller.last_error or "Unknown validation error"
            QMessageBox.critical(
                self,
                "Cannot Create Diagram",
                f"Failed to create new diagram:\n\n{error_msg}"
            )
            self._show_status(f"Failed to create diagram", error=True)
            return
        
        # Set workflow mode
        self._workflow_mode = WorkflowMode.CREATE_NEW
        self._update_workflow_ui()
        
        # Display
        self._refresh_display()
        
        self._current_file = None
        self._has_unsaved_changes = False
        
        self._show_status(f"Created new diagram: {description}")
    
    def _create_empty_sheet(self) -> RelationalGraphWithCuts:
        """Create empty sheet of assertion."""
        from egi_core_dau import create_empty_graph
        return create_empty_graph()
    
    def _create_with_double_cut(self) -> RelationalGraphWithCuts:
        """Create sheet with double cut (negative context for composition)."""
        from egi_core_dau import RelationalGraphWithCuts, Cut as EGICut
        from frozendict import frozendict
        import uuid
        
        sheet_id = f"sheet_{uuid.uuid4().hex[:8]}"
        outer_cut_id = f"cut_{uuid.uuid4().hex[:8]}"
        inner_cut_id = f"cut_{uuid.uuid4().hex[:8]}"
        
        outer_cut = EGICut(id=outer_cut_id)
        inner_cut = EGICut(id=inner_cut_id)
        
        return RelationalGraphWithCuts(
            V=frozenset(),
            E=frozenset(),
            nu=frozendict(),
            sheet=sheet_id,
            Cut=frozenset([outer_cut, inner_cut]),
            area=frozendict({
                sheet_id: frozenset([outer_cut_id]),
                outer_cut_id: frozenset([inner_cut_id]),
                inner_cut_id: frozenset()
            }),
            rel=frozendict(),
            alphabet=None,
            rho=frozendict()
        )
    
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
    
    def _on_zoom_in(self):
        """Zoom in."""
        self.canvas.zoom_in()
    
    def _on_zoom_out(self):
        """Zoom out."""
        self.canvas.zoom_out()
    
    def _on_reset_zoom(self):
        """Reset zoom to fit entire diagram."""
        self.canvas.reset_zoom()
        self._show_status("Zoom reset")
    
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
        print(f"=== _on_element_moved: {element_id} to {new_pos} ===")
        
        # Update position through controller (with validation and DTO update)
        success = self.controller.update_element_position(element_id, new_pos)
        
        if success:
            print(f"✓ Position update accepted")
            # FAST PATH: Controller already updated DTO, just refresh display
            # No relayout needed - this is a logic-indifferent aesthetic change
            # fit_to_view=False to preserve zoom/pan and manual positioning
            dto = self.controller.current_dto
            egi = self.controller.egi_model
            
            # Verify the DTO was actually updated
            if element_id in dto.vertex_positions:
                dto_pos = dto.vertex_positions[element_id]
                print(f"  DTO vertex position: ({dto_pos.x}, {dto_pos.y})")
            elif element_id in dto.predicate_positions:
                dto_pos = dto.predicate_positions[element_id]
                print(f"  DTO predicate position: ({dto_pos.x}, {dto_pos.y})")
            
            if dto and egi:
                self.canvas.display_dto(dto, egi, fit_to_view=False)
            self._show_status(f"Moved {element_id} to ({new_pos[0]:.1f}, {new_pos[1]:.1f})")
        else:
            print(f"✗ Position update REJECTED")
            # Position rejected - revert by redisplaying current DTO
            self._show_status(f"Invalid position for {element_id}", error=True)
            dto = self.controller.current_dto
            egi = self.controller.egi_model
            if dto and egi:
                self.canvas.display_dto(dto, egi, fit_to_view=False)
    
    def _on_cut_moved(self, cut_id: str, delta: Tuple[float, float]):
        """Handle cut drag - move all contents with the cut (container movement)."""
        print(f"=== _on_cut_moved: {cut_id} by delta {delta} ===")
        
        # Update cut position through controller
        success = self.controller.update_cut_position(cut_id, delta)
        
        if success:
            print(f"✓ Cut movement applied")
            # Refresh display
            dto = self.controller.current_dto
            egi = self.controller.egi_model
            if dto and egi:
                self.canvas.display_dto(dto, egi, fit_to_view=False)
            
            dx, dy = delta
            self._show_status(f"Moved cut {cut_id} by ({dx:.1f}, {dy:.1f})")
        else:
            print(f"✗ Cut movement FAILED")
            self._show_status(f"Failed to move cut {cut_id}", error=True)
    
    def _on_cut_resized(self, cut_id: str, new_size: Tuple[float, float]):
        """Handle cut resize - update cut bounds."""
        print(f"=== _on_cut_resized: {cut_id} to size {new_size} ===")
        
        # Update cut size through controller
        success = self.controller.update_cut_size(cut_id, new_size)
        
        if success:
            print(f"✓ Cut resize applied")
            # Refresh display
            dto = self.controller.current_dto
            egi = self.controller.egi_model
            if dto and egi:
                self.canvas.display_dto(dto, egi, fit_to_view=False)
            
            w, h = new_size
            self._show_status(f"Resized cut {cut_id} to ({w:.1f} × {h:.1f})")
        else:
            print(f"✗ Cut resize FAILED")
            self._show_status(f"Failed to resize cut {cut_id}", error=True)
    
    def _on_apply_rule(self, rule_name: str):
        """Apply a transformation rule and record in UoD history if historical."""
        selection = self.canvas.get_selected_elements()
        
        if not selection:
            self.validation_label.setText("⚠️ No elements selected")
            self.validation_label.setStyleSheet("color: orange; font-size: 10px; padding: 5px;")
            return
        
        # Determine target area from selection
        target_area, polarity = self._get_target_area_from_selection(selection)
        
        print(f"Applying {rule_name} to selection {selection} in area {target_area} ({polarity})")
        
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
    
    def _check_selection_closure(self, selection: List[str], polarity: str) -> Dict[str, Any]:
        """
        Check if selection forms a closed subgraph for INS/ERA.
        
        Returns:
            Dict with keys: is_valid, message, added_count
        """
        from subgraph_closure_validator import SubgraphClosureValidator
        
        egi = self.controller.get_egi_model()
        if not egi or not selection:
            return {'is_valid': True, 'message': '', 'added_count': 0}
        
        # Only validate for INS/ERA contexts
        if polarity not in ["positive", "negative"]:
            return {'is_valid': True, 'message': '', 'added_count': 0}
        
        try:
            validator = SubgraphClosureValidator(egi)
            analysis = validator.analyze_closure(frozenset(selection), allow_expansion=True)
            
            if analysis.is_closed:
                if analysis.added_elements:
                    count = len(analysis.added_elements)
                    return {
                        'is_valid': True,
                        'message': f'✓ Closure (+{count})',
                        'added_count': count
                    }
                else:
                    return {
                        'is_valid': True,
                        'message': '✓ Closed',
                        'added_count': 0
                    }
            else:
                return {
                    'is_valid': False,
                    'message': '✗ Not closed',
                    'added_count': 0
                }
        except Exception as e:
            # If validation fails, be conservative
            return {
                'is_valid': False,
                'message': f'✗ Validation error',
                'added_count': 0
            }
    
    def _get_target_area_from_selection(self, selection: List[str]) -> Tuple[str, str]:
        """
        Determine target area and polarity from selection.
        
        Returns:
            Tuple of (area_id, polarity) where polarity is "positive" or "negative"
        """
        if not selection:
            return None, "positive"
        
        egi = self.controller.get_egi_model()
        if not egi:
            return None, "positive"
        
        # If a cut is selected, use that cut as the target area
        for elem_id in selection:
            if elem_id.startswith('cut_'):
                polarity, _ = self.controller._calculate_area_polarity(elem_id)
                polarity_str = "positive" if polarity.value == "positive" else "negative"
                return elem_id, polarity_str
        
        # Otherwise, find which area contains the selected elements
        for elem_id in selection:
            # Check which area this element belongs to
            for area_id, contents in egi.area.items():
                if elem_id in contents:
                    polarity, _ = self.controller._calculate_area_polarity(area_id)
                    polarity_str = "positive" if polarity.value == "positive" else "negative"
                    return area_id, polarity_str
        
        # Default to sheet (positive)
        return egi.sheet, "positive"
    
    def _update_transformation_buttons(self):
        """Enable/disable transformation buttons based on selection and area polarity."""
        selection = self.canvas.get_selected_elements()
        has_selection = bool(selection)
        
        if not has_selection:
            # No selection - disable all transformation buttons
            self.dc_insert_btn.setEnabled(False)
            self.dc_erase_btn.setEnabled(False)
            self.add_to_clipboard_btn.setEnabled(False)
            self.ins_btn.setEnabled(False)
            self.era_btn.setEnabled(False)
            self.iter_insert_btn.setEnabled(False)
            self.iter_erase_btn.setEnabled(False)
            self.validation_label.setText("")
            return
        
        # Determine target area from selection
        target_area, polarity = self._get_target_area_from_selection(selection)
        
        # Enable buttons based on area polarity and selection
        # DC+ always available (can wrap anything)
        self.dc_insert_btn.setEnabled(True)
        
        # DC- requires selecting a cut (specifically double cut in practice)
        has_cut_selected = any(elem_id.startswith('cut_') for elem_id in selection)
        self.dc_erase_btn.setEnabled(has_cut_selected)
        
        # Check closure for INS/ERA and clipboard
        closure_status = self._check_selection_closure(selection, polarity)
        
        # Clipboard button: enabled if selection forms closed subgraph (any polarity)
        self.add_to_clipboard_btn.setEnabled(closure_status['is_valid'])
        
        # INS: now starts workflow (always enabled when something selected)
        # Actual insertion happens after clipboard selection + target selection
        self.ins_btn.setEnabled(True)  # Changed: always enabled with selection
        
        # ERA only in positive areas (even polarity) with closed subgraph
        self.era_btn.setEnabled(polarity == "positive" and closure_status['is_valid'])
        
        # IT+/IT- available with selection (controller will validate isomorphism)
        self.iter_insert_btn.setEnabled(has_selection)
        self.iter_erase_btn.setEnabled(has_selection)
        
        # Show context info with closure status
        area_name = "sheet" if target_area == self.controller.get_egi_model().sheet else target_area
        status_text = f"ℹ️ Context: {area_name} ({polarity})"
        
        if closure_status['message']:
            status_text += f" | {closure_status['message']}"
            
        self.validation_label.setText(status_text)
        
        # Color code based on closure status
        if closure_status['added_count'] > 0:
            # Expanded to closure
            self.validation_label.setStyleSheet("color: #0066cc; font-size: 10px; padding: 5px;")
        elif not closure_status['is_valid']:
            # Invalid closure
            self.validation_label.setStyleSheet("color: #cc6600; font-size: 10px; padding: 5px;")
        else:
            # Normal
            self.validation_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
    
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
    
    def _on_add_to_clipboard(self):
        """Add current selection to insertion clipboard."""
        from insertion_clipboard import get_insertion_clipboard
        from PySide6.QtWidgets import QInputDialog
        
        selection = self.canvas.get_selected_elements()
        if not selection:
            self._show_status("No elements selected", error=True)
            return
        
        egi = self.controller.get_egi_model()
        if not egi:
            self._show_status("No graph loaded", error=True)
            return
        
        # Get clipboard
        clipboard = get_insertion_clipboard()
        
        # Ask for name (optional)
        name, ok = QInputDialog.getText(
            self,
            "Add to Insertion Clipboard",
            "Enter a name for this subgraph (optional):",
            text=f"Subgraph {len(clipboard.get_all_entries()) + 1}"
        )
        
        if not ok:
            return  # User cancelled
        
        # Add to clipboard (will validate automatically)
        success, message, entry = clipboard.add_entry(
            subgraph_elements=frozenset(selection),
            source_egi=egi,
            name=name or None,
            description=""
        )
        
        if success:
            self.validation_label.setText(message)
            self.validation_label.setStyleSheet("color: green; font-size: 10px; padding: 5px;")
            self._show_status(message)
        else:
            self.validation_label.setText(f"✗ {message}")
            self.validation_label.setStyleSheet("color: red; font-size: 10px; padding: 5px;")
            self._show_status(f"Cannot add to clipboard: {message}", error=True)
    
    def _on_browse_clipboard(self):
        """Browse insertion clipboard."""
        from gui_clean.insertion_clipboard_dialog import InsertionClipboardDialog
        from insertion_clipboard import get_insertion_clipboard
        
        clipboard = get_insertion_clipboard()
        dialog = InsertionClipboardDialog(clipboard, parent=self)
        
        # Just show for browsing (user can remove entries)
        dialog.exec()
        
        # No action needed - user browses only
        # Actual insertion happens via INS button workflow
    
    def _on_start_ins_workflow(self):
        """Start the INS workflow: select from clipboard, then select target."""
        from gui_clean.insertion_clipboard_dialog import InsertionClipboardDialog
        from insertion_clipboard import get_insertion_clipboard
        from PySide6.QtWidgets import QMessageBox
        
        # Step 1: User selects from clipboard
        clipboard = get_insertion_clipboard()
        
        if not clipboard.get_all_entries():
            QMessageBox.information(
                self,
                "Insertion Clipboard Empty",
                "The insertion clipboard is empty.\n\n"
                "Please add a closed subgraph to the clipboard first using "
                "'📋 Add to Clipboard'."
            )
            return
        
        dialog = InsertionClipboardDialog(clipboard, parent=self)
        result = dialog.exec()
        
        if result != QDialog.Accepted:
            return  # User cancelled
        
        selected_entry = dialog.get_selected_entry()
        if not selected_entry:
            return
        
        # Store selected entry for step 2
        self._pending_ins_entry = selected_entry
        
        # Step 2: Indicate that user should select target
        self.validation_label.setText(
            f"📋 Selected: {selected_entry.name}\n"
            f"👉 Now click on a CUT (negative area) to select insertion target"
        )
        self.validation_label.setStyleSheet("color: blue; font-size: 10px; padding: 5px;")
        
        # Enable special mode where clicking on cut finalizes INS
        self._awaiting_ins_target = True
        self.canvas.setCursor(Qt.CrossCursor)
        
        # TODO: Connect to canvas click event to detect cut selection
        # For now, show message that this is pending implementation
        QMessageBox.information(
            self,
            "Select Target Cut",
            f"Selected subgraph: {selected_entry.name}\n\n"
            f"Next: Click on a cut (negative area) to complete insertion.\n\n"
            f"Note: Target selection UI pending implementation."
        )
    
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
        
        # Load into controller
        if not self.controller.load_egi(egi):
            # Load failed - show error to user
            error_msg = self.controller.last_error or "Unknown validation error"
            QMessageBox.critical(
                self,
                "Cannot Load Diagram",
                f"Failed to load diagram from Organon:\n\n{error_msg}"
            )
            self._show_status(f"Failed to load diagram", error=True)
            return
        
        print("=== Calling _refresh_display ===")
        self._refresh_display()
        self._current_file = None
        self._has_unsaved_changes = False
        
        mode_name = "editing" if source_uod else "practice"
        self._show_status(f"Loaded graph from Organon for {mode_name}")
