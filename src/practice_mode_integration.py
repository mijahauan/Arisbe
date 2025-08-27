"""
Practice mode integration for Ergasterion drawing editor.

Provides transformation rule practice functionality that can be integrated
into the existing drawing editor for educational and research purposes.
"""

import json
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QListWidget, QListWidgetItem,
    QTextEdit, QGroupBox, QMessageBox, QCheckBox, QSpinBox,
    QTabWidget, QScrollArea, QFrame, QSplitter, QProgressBar
)
from PySide6.QtGui import QFont, QColor, QPalette

try:
    from transformation_rules import (
        get_transformation_engine, TransformationRuleType, 
        TransformationContext, ValidationResult, TransformationResult
    )
    from egi_export import get_export_manager
except ImportError as e:
    print(f"Warning: Could not import transformation modules: {e}")
    # Provide fallback
    def get_transformation_engine():
        return None


class PracticeModeState(Enum):
    """States of practice mode."""
    INACTIVE = "inactive"
    SELECTING = "selecting"
    RULE_CHOSEN = "rule_chosen"
    VALIDATING = "validating"
    APPLYING = "applying"


@dataclass
class PracticeSession:
    """Represents a practice session."""
    session_id: str
    start_time: str
    transformations_attempted: int = 0
    transformations_successful: int = 0
    current_rule: Optional[TransformationRuleType] = None
    selected_elements: List[str] = None
    
    def __post_init__(self):
        if self.selected_elements is None:
            self.selected_elements = []


class TransformationRulePalette(QWidget):
    """Widget displaying available transformation rules."""
    
    rule_selected = Signal(object)  # TransformationRuleType
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.transformation_engine = get_transformation_engine()
        self.current_graph = None
        self.selected_elements = []
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the rule palette UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Transformation Rules")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Rule categories
        self.create_rule_category("Basic Rules", [
            (TransformationRuleType.INSERTION, "Always valid - insert any graph anywhere"),
            (TransformationRuleType.ERASURE, "Only from positive contexts"),
            (TransformationRuleType.ITERATION, "Copy within same context"),
            (TransformationRuleType.DEITERATION, "Remove duplicates in same context")
        ], layout)
        
        self.create_rule_category("Cut Rules", [
            (TransformationRuleType.DOUBLE_CUT_INSERTION, "Insert double negation"),
            (TransformationRuleType.DOUBLE_CUT_ERASURE, "Remove double negation")
        ], layout)
        
        # Status display
        status_group = QGroupBox("Rule Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
    
    def create_rule_category(self, title: str, rules: List[Tuple], layout: QVBoxLayout):
        """Create a category of rule buttons."""
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        
        for rule_type, description in rules:
            btn = QPushButton(rule_type.value.replace('_', ' ').title())
            btn.setToolTip(description)
            btn.clicked.connect(lambda checked, rt=rule_type: self.on_rule_selected(rt))
            
            # Initially disable all buttons
            btn.setEnabled(False)
            
            group_layout.addWidget(btn)
        
        layout.addWidget(group)
    
    def on_rule_selected(self, rule_type: TransformationRuleType):
        """Handle rule selection."""
        self.rule_selected.emit(rule_type)
    
    def update_for_selection(self, graph, selected_elements: List[str]):
        """Update rule availability based on current selection."""
        self.current_graph = graph
        self.selected_elements = selected_elements
        
        if not self.transformation_engine or not graph:
            self.disable_all_rules()
            return
        
        # Get applicable rules
        applicable_rules = self.transformation_engine.get_applicable_rules(
            graph, selected_elements)
        
        # Update button states
        self.update_rule_buttons(applicable_rules)
        
        # Update status
        self.update_status_display(applicable_rules)
    
    def disable_all_rules(self):
        """Disable all rule buttons."""
        for group in self.findChildren(QGroupBox):
            for btn in group.findChildren(QPushButton):
                btn.setEnabled(False)
    
    def update_rule_buttons(self, applicable_rules: List[Tuple]):
        """Update rule button states based on applicable rules."""
        applicable_types = {rule_type for rule_type, _ in applicable_rules}
        
        for group in self.findChildren(QGroupBox):
            for btn in group.findChildren(QPushButton):
                # Find corresponding rule type
                rule_name = btn.text().lower().replace(' ', '_')
                try:
                    rule_type = TransformationRuleType(rule_name)
                    btn.setEnabled(rule_type in applicable_types)
                except ValueError:
                    btn.setEnabled(False)
    
    def update_status_display(self, applicable_rules: List[Tuple]):
        """Update the status display with rule information."""
        if not applicable_rules:
            self.status_text.setText("No rules applicable to current selection.")
            return
        
        status_lines = [f"Applicable rules ({len(applicable_rules)}):"]
        
        for rule_type, validation in applicable_rules:
            rule = self.transformation_engine.get_rule(rule_type)
            line = f"• {rule.name}"
            
            if validation.suggestions:
                line += f" - {validation.suggestions[0]}"
            
            status_lines.append(line)
        
        self.status_text.setText("\n".join(status_lines))


class ValidationPanel(QWidget):
    """Panel for showing transformation validation results."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up validation panel UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Validation Results")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Status indicator
        self.status_label = QLabel("No validation performed")
        layout.addWidget(self.status_label)
        
        # Details
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(150)
        self.details_text.setReadOnly(True)
        layout.addWidget(self.details_text)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Apply Transformation")
        self.apply_btn.setEnabled(False)
        button_layout.addWidget(self.apply_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def show_validation_result(self, validation: ValidationResult, rule_name: str):
        """Display validation results."""
        if validation.is_valid:
            self.status_label.setText(f"✓ {rule_name} can be applied")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.apply_btn.setEnabled(True)
        else:
            self.status_label.setText(f"✗ {rule_name} cannot be applied")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.apply_btn.setEnabled(False)
        
        # Build details text
        details = []
        
        if validation.errors:
            details.append("Errors:")
            for error in validation.errors:
                details.append(f"  • {error}")
            details.append("")
        
        if validation.warnings:
            details.append("Warnings:")
            for warning in validation.warnings:
                details.append(f"  • {warning}")
            details.append("")
        
        if validation.suggestions:
            details.append("Suggestions:")
            for suggestion in validation.suggestions:
                details.append(f"  • {suggestion}")
        
        self.details_text.setText("\n".join(details))
    
    def clear(self):
        """Clear validation display."""
        self.status_label.setText("No validation performed")
        self.status_label.setStyleSheet("")
        self.details_text.clear()
        self.apply_btn.setEnabled(False)


class PracticeSessionPanel(QWidget):
    """Panel for managing practice sessions."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_session = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up session panel UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Practice Session")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Session controls
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Session")
        self.start_btn.clicked.connect(self.start_session)
        controls_layout.addWidget(self.start_btn)
        
        self.end_btn = QPushButton("End Session")
        self.end_btn.clicked.connect(self.end_session)
        self.end_btn.setEnabled(False)
        controls_layout.addWidget(self.end_btn)
        
        layout.addLayout(controls_layout)
        
        # Session stats
        stats_group = QGroupBox("Session Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(100)
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        
        # Progress tracking
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("No active session")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
    
    def start_session(self):
        """Start a new practice session."""
        from datetime import datetime
        import uuid
        
        self.current_session = PracticeSession(
            session_id=str(uuid.uuid4())[:8],
            start_time=datetime.now().isoformat()
        )
        
        self.start_btn.setEnabled(False)
        self.end_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_label.setText("Session active - select elements to practice transformations")
        
        self.update_stats_display()
    
    def end_session(self):
        """End the current practice session."""
        if self.current_session:
            # Could save session data here
            self.current_session = None
        
        self.start_btn.setEnabled(True)
        self.end_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("No active session")
        
        self.stats_text.clear()
    
    def record_transformation_attempt(self, success: bool):
        """Record a transformation attempt."""
        if self.current_session:
            self.current_session.transformations_attempted += 1
            if success:
                self.current_session.transformations_successful += 1
            
            self.update_stats_display()
    
    def update_stats_display(self):
        """Update the statistics display."""
        if not self.current_session:
            return
        
        session = self.current_session
        success_rate = 0
        if session.transformations_attempted > 0:
            success_rate = (session.transformations_successful / 
                          session.transformations_attempted) * 100
        
        stats = [
            f"Session ID: {session.session_id}",
            f"Attempts: {session.transformations_attempted}",
            f"Successful: {session.transformations_successful}",
            f"Success Rate: {success_rate:.1f}%"
        ]
        
        self.stats_text.setText("\n".join(stats))


class PracticeModeDockWidget(QDockWidget):
    """Main dock widget for practice mode functionality."""
    
    transformation_requested = Signal(object, object)  # rule_type, context
    
    def __init__(self, parent=None):
        super().__init__("Practice Mode", parent)
        self.drawing_editor = parent
        self.transformation_engine = get_transformation_engine()
        self.current_state = PracticeModeState.INACTIVE
        self.selected_elements = []
        self.current_rule = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the practice mode UI."""
        widget = QWidget()
        self.setWidget(widget)
        
        layout = QVBoxLayout(widget)
        
        # Mode toggle
        mode_group = QGroupBox("Practice Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_checkbox = QCheckBox("Enable Practice Mode")
        self.mode_checkbox.toggled.connect(self.toggle_practice_mode)
        mode_layout.addWidget(self.mode_checkbox)
        
        layout.addWidget(mode_group)
        
        # Tabbed interface
        self.tab_widget = QTabWidget()
        
        # Rules tab
        self.rule_palette = TransformationRulePalette()
        self.rule_palette.rule_selected.connect(self.on_rule_selected)
        self.tab_widget.addTab(self.rule_palette, "Rules")
        
        # Validation tab
        self.validation_panel = ValidationPanel()
        self.validation_panel.apply_btn.clicked.connect(self.apply_transformation)
        self.validation_panel.cancel_btn.clicked.connect(self.cancel_transformation)
        self.tab_widget.addTab(self.validation_panel, "Validation")
        
        # Session tab
        self.session_panel = PracticeSessionPanel()
        self.tab_widget.addTab(self.session_panel, "Session")
        
        layout.addWidget(self.tab_widget)
        
        # Initially disable tabs
        self.tab_widget.setEnabled(False)
    
    def toggle_practice_mode(self, enabled: bool):
        """Toggle practice mode on/off."""
        self.tab_widget.setEnabled(enabled)
        
        if enabled:
            self.current_state = PracticeModeState.SELECTING
            # Notify drawing editor to enter practice mode
            if hasattr(self.drawing_editor, 'set_practice_mode'):
                self.drawing_editor.set_practice_mode(True)
        else:
            self.current_state = PracticeModeState.INACTIVE
            self.selected_elements = []
            self.current_rule = None
            self.validation_panel.clear()
            
            # Notify drawing editor to exit practice mode
            if hasattr(self.drawing_editor, 'set_practice_mode'):
                self.drawing_editor.set_practice_mode(False)
    
    def update_selection(self, selected_elements: List[str]):
        """Update based on element selection in the drawing editor."""
        if self.current_state == PracticeModeState.INACTIVE:
            return
        
        self.selected_elements = selected_elements
        
        # Get current graph from drawing editor
        current_graph = None
        if hasattr(self.drawing_editor, 'get_current_egi'):
            current_graph = self.drawing_editor.get_current_egi()
        
        # Update rule palette
        self.rule_palette.update_for_selection(current_graph, selected_elements)
        
        # Clear validation if selection changed
        if self.current_state != PracticeModeState.SELECTING:
            self.validation_panel.clear()
            self.current_state = PracticeModeState.SELECTING
    
    def on_rule_selected(self, rule_type: TransformationRuleType):
        """Handle rule selection."""
        if not self.transformation_engine:
            QMessageBox.warning(self, "Error", "Transformation engine not available")
            return
        
        self.current_rule = rule_type
        self.current_state = PracticeModeState.RULE_CHOSEN
        
        # Get current graph
        current_graph = None
        if hasattr(self.drawing_editor, 'get_current_egi'):
            current_graph = self.drawing_editor.get_current_egi()
        
        if not current_graph:
            QMessageBox.warning(self, "Error", "No graph available for transformation")
            return
        
        # Create transformation context
        context = TransformationContext(
            rule_type=rule_type,
            source_elements=self.selected_elements.copy()
        )
        
        # Validate transformation
        validation = self.transformation_engine.validate_transformation(
            current_graph, rule_type, context)
        
        # Show validation results
        rule = self.transformation_engine.get_rule(rule_type)
        self.validation_panel.show_validation_result(validation, rule.name)
        
        # Switch to validation tab
        self.tab_widget.setCurrentIndex(1)
        
        self.current_state = PracticeModeState.VALIDATING
    
    def apply_transformation(self):
        """Apply the selected transformation."""
        if not self.current_rule or not self.transformation_engine:
            return
        
        # Get current graph
        current_graph = None
        if hasattr(self.drawing_editor, 'get_current_egi'):
            current_graph = self.drawing_editor.get_current_egi()
        
        if not current_graph:
            QMessageBox.warning(self, "Error", "No graph available for transformation")
            return
        
        # Create transformation context
        context = TransformationContext(
            rule_type=self.current_rule,
            source_elements=self.selected_elements.copy()
        )
        
        # Apply transformation
        self.current_state = PracticeModeState.APPLYING
        result = self.transformation_engine.apply_transformation(
            current_graph, self.current_rule, context)
        
        # Record attempt
        self.session_panel.record_transformation_attempt(result.success)
        
        if result.success:
            # Notify drawing editor of successful transformation
            if hasattr(self.drawing_editor, 'apply_transformation_result'):
                self.drawing_editor.apply_transformation_result(result)
            
            QMessageBox.information(self, "Success", 
                                  f"Transformation applied: {result.changes_description}")
        else:
            error_msg = "Transformation failed"
            if result.validation_result and result.validation_result.errors:
                error_msg += ":\n" + "\n".join(result.validation_result.errors)
            
            QMessageBox.warning(self, "Transformation Failed", error_msg)
        
        # Reset state
        self.cancel_transformation()
    
    def cancel_transformation(self):
        """Cancel the current transformation."""
        self.current_rule = None
        self.current_state = PracticeModeState.SELECTING
        self.validation_panel.clear()
        
        # Switch back to rules tab
        self.tab_widget.setCurrentIndex(0)


def integrate_practice_mode(drawing_editor):
    """Integrate practice mode functionality into a drawing editor."""
    practice_dock = PracticeModeDockWidget(drawing_editor)
    
    # Add dock widget
    drawing_editor.addDockWidget(Qt.RightDockWidgetArea, practice_dock)
    
    # Add menu action if menu bar exists
    if hasattr(drawing_editor, 'menuBar'):
        view_menu = None
        # Find existing View menu or create it
        for action in drawing_editor.menuBar().actions():
            if action.text() == "View":
                view_menu = action.menu()
                break
        
        if not view_menu:
            view_menu = drawing_editor.menuBar().addMenu("View")
        
        practice_action = practice_dock.toggleViewAction()
        practice_action.setText("Practice Mode")
        view_menu.addAction(practice_action)
    
    # Connect selection changes if the drawing editor supports it
    if hasattr(drawing_editor, 'selection_changed'):
        drawing_editor.selection_changed.connect(practice_dock.update_selection)
    
    return practice_dock

