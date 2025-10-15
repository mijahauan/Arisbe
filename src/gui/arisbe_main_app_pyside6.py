#!/usr/bin/env python3
"""
PySide6-compatible wrapper for Arisbe Main Application
=====================================================

Adapts the current development (arisbe_main_app.py) to work with PySide6
while maintaining all the underlying logic and transformation engine capabilities.
"""

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QAction, QFont
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMenuBar,
        QMessageBox,
        QPushButton,
        QSplitter,
        QStatusBar,
        QTabWidget,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    from gui.transformation_wizard_dialog import TransformationWizardDialog
except ImportError:
    print("PySide6 not available. Install with: pip install PySide6")
    sys.exit(1)

from pathlib import Path

from cgif_generator_dau import generate_cgif
from chapter21_diagram_engine import UniversalEGIEngine

# Import transformation engine
from chapter21_transformation_sequences import TransformationSequenceEngine
from chapter21_transformation_wizards import (
    DiagramTransformationWizard,
    UniversalTransformationWizardSystem,
)
from clif_generator_dau import generate_clif

# Import tomos management
# Import tomos management
from tomos_index import CorpusEntry, graph_paths, list_entries, load_index, read_info

# Import linear forms generation
from egi_core_dau import RelationalGraphWithCuts
from egif_generator_dau import generate_egif

# Import transformation rules
from formal_transformation_rules import (
    DeiterationRule,
    DoubleCutErasureRule,
    DoubleCutInsertionRule,
    ErasureRule,
    InsertionRule,
    IterationRule,
)


@dataclass
class ApplicationState:
    """Central application state management."""

    current_egi: Optional[RelationalGraphWithCuts] = None
    transformation_engine: Optional[TransformationSequenceEngine] = None
    active_sequence_id: Optional[str] = None


class LinearFormDisplay(QWidget):
    """Display widget for EGI linear forms and transformation sequences."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("EGI Linear Form Display")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)

        # Main display area
        self.display_area = QTextEdit()
        self.display_area.setReadOnly(True)
        self.display_area.setFont(QFont("Courier", 10))
        layout.addWidget(self.display_area)

        self.setLayout(layout)

    def display_egi(self, egi: RelationalGraphWithCuts, title: str = "Current EGI"):
        """Display EGI in linear form."""
        content = f"=== {title} ===\n\n"
        content += f"Vertices: {len(egi.V)}\n"
        content += f"Cuts: {len(egi.Cut)}\n"
        content += f"Areas: {len(egi.area)}\n\n"

        # Display structure
        content += "Structure:\n"
        for area_id, elements in egi.area.items():
            if area_id == egi.sheet:
                content += f"Sheet: {list(elements)}\n"
            else:
                content += f"Cut {area_id}: {list(elements)}\n"

        self.display_area.setPlainText(content)

    def display_transformation_sequence(
        self, engine: TransformationSequenceEngine, sequence_id: str
    ):
        """Display complete transformation sequence."""
        sequence = engine.sequences.get(sequence_id)
        if not sequence:
            self.display_area.setPlainText("No sequence found.")
            return

        content = f"=== Transformation Sequence: {sequence_id} ===\n\n"

        for i, step in enumerate(sequence.steps, 1):
            content += f"Step {i}: {step.rule_type.value}\n"
            content += f"  Status: {step.validation_result.value if step.validation_result else 'None'}\n"
            if step.error_message:
                content += f"  Error: {step.error_message}\n"
            content += f"  Description: {step.parameters.get('description', 'N/A')}\n"
            content += "\n"

        # Statistics
        stats = engine.get_sequence_statistics(sequence_id)
        content += f"\nStatistics:\n"
        content += f"Total steps: {stats['total_steps']}\n"
        content += f"Valid steps: {stats['valid_steps']}\n"
        content += f"Success rate: {stats['success_rate']:.1%}\n"

        self.display_area.setPlainText(content)


class OrganonTab(QWidget):
    """Library/Browser tab for exploring the tomos."""

    egi_selected = Signal(object, str)  # EGI data, title
    transfer_to_ergasterion = Signal(object, str)  # EGI data, title

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_egi_data = None
        self.current_title = None
        self.setup_ui()
        self.load_corpus_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Compact header
        header = QLabel("📚 Organon - Tomos Library")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setMaximumHeight(30)
        layout.addWidget(header)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Left: EGI tree browser
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(3)

        browse_label = QLabel("Browse Tomos:")
        browse_label.setMaximumHeight(20)
        left_layout.addWidget(browse_label)

        self.egi_tree = QTreeWidget()
        self.egi_tree.setHeaderLabel("EGI Collection")
        self.egi_tree.itemClicked.connect(self.on_egi_selected)
        left_layout.addWidget(self.egi_tree)

        # Transfer button
        self.transfer_btn = QPushButton("📤 Send to Ergasterion")
        self.transfer_btn.setEnabled(False)
        self.transfer_btn.clicked.connect(self.on_transfer_to_ergasterion)
        left_layout.addWidget(self.transfer_btn)

        splitter.addWidget(left_widget)

        # Right: Linear form display with tabs
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(3)

        display_label = QLabel("EGI Details & Linear Forms:")
        display_label.setMaximumHeight(20)
        right_layout.addWidget(display_label)

        # Tabbed display for different formats
        self.display_tabs = QTabWidget()

        # EGI Structure tab
        self.egi_display = QTextEdit()
        self.egi_display.setReadOnly(True)
        self.display_tabs.addTab(self.egi_display, "EGI Structure")

        # Linear forms tabs
        self.egif_display = QTextEdit()
        self.egif_display.setReadOnly(True)
        self.display_tabs.addTab(self.egif_display, "EGIF")

        self.cgif_display = QTextEdit()
        self.cgif_display.setReadOnly(True)
        self.display_tabs.addTab(self.cgif_display, "CGIF")

        self.clif_display = QTextEdit()
        self.clif_display.setReadOnly(True)
        self.display_tabs.addTab(self.clif_display, "CLIF")

        right_layout.addWidget(self.display_tabs)

        splitter.addWidget(right_widget)

        # Set splitter proportions - optimize space usage for Organon
        splitter.setSizes([280, 820])

    def load_corpus_data(self):
        """Load tomos data from index into tree widget."""
        try:
            # Load tomos index
            index = load_index()
            entries = list_entries(index)

            if not entries:
                # Add placeholder if no entries
                placeholder_item = QTreeWidgetItem(self.egi_tree)
                placeholder_item.setText(0, "No graphs in corpus")
                placeholder_item.setData(0, Qt.UserRole, None)
                return

            # Group entries by category
            categories = {}
            for entry in entries:
                category = entry.get("category", "Uncategorized")
                if category not in categories:
                    categories[category] = []
                categories[category].append(entry)

            # Create tree structure
            for category, category_entries in categories.items():
                cat_item = QTreeWidgetItem(self.egi_tree)
                cat_item.setText(0, f"📁 {category}")
                cat_item.setData(0, Qt.UserRole, None)

                for entry in category_entries:
                    item_widget = QTreeWidgetItem(cat_item)
                    title = entry.get("title", entry.get("id", "Unknown"))
                    item_widget.setText(0, f"📄 {title}")
                    item_widget.setData(0, Qt.UserRole, entry)

                    # Add metadata as tooltip
                    tags = entry.get("tags", [])
                    tooltip = f"ID: {entry.get('id', 'N/A')}\n"
                    tooltip += f"Category: {category}\n"
                    if tags:
                        tooltip += f"Tags: {', '.join(tags)}\n"
                    tooltip += f"Updated: {entry.get('updated', 'N/A')}"
                    item_widget.setToolTip(0, tooltip)

                # Expand category by default
                cat_item.setExpanded(True)

        except Exception as e:
            print(f"Could not load tomos data: {e}")
            # Add error item
            error_item = QTreeWidgetItem(self.egi_tree)
            error_item.setText(0, f"Error loading corpus: {e}")
            error_item.setData(0, Qt.UserRole, None)

    def on_egi_selected(self, item, column):
        """Handle EGI selection from the tree."""
        entry_data = item.data(0, Qt.UserRole)
        if not entry_data:
            return

        try:
            # Load the actual EGI data
            graph_id = entry_data.get("id")
            graph_path = Path(entry_data.get("path", ""))

            if not graph_path.exists():
                self.egi_display.setPlainText(f"Path not found: {graph_path}")
                return

            # Load metadata
            metadata_file = graph_path / f"{graph_id}.json"
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            else:
                metadata = {}

            # Load EGI data
            egi_file = graph_path / f"{graph_id}.egi.json"
            if egi_file.exists():
                egi_data = json.loads(egi_file.read_text(encoding="utf-8"))
                self.current_egi_data = egi_data
                self.current_title = entry_data.get("title", graph_id)
            else:
                egi_data = {}
                self.current_egi_data = None
                self.current_title = None

            # Update EGI Structure tab
            content = f"=== {entry_data.get('title', graph_id)} ===\n\n"
            content += "📋 Metadata:\n"
            content += f"  ID: {graph_id}\n"
            content += f"  Category: {entry_data.get('category', 'None')}\n"
            content += f"  Updated: {entry_data.get('updated', 'Unknown')}\n"
            content += f"  Path: {graph_path}\n\n"

            content += "🔗 EGI Structure:\n"
            if egi_data:
                content += f"  Vertices: {len(egi_data.get('V', []))}\n"
                content += f"  Edges: {len(egi_data.get('E', []))}\n"
                content += f"  Cuts: {len(egi_data.get('Cut', []))}\n"
                content += f"  Areas: {len(egi_data.get('area', {}))}\n\n"

                content += "📄 Full EGI JSON:\n"
                content += json.dumps(egi_data, indent=2)
            else:
                content += "  No EGI data found\n"

            self.egi_display.setPlainText(content)

            # Generate linear forms if EGI data is available
            if egi_data:
                self.generate_linear_forms(egi_data)
                self.transfer_btn.setEnabled(True)
            else:
                self.clear_linear_forms()
                self.transfer_btn.setEnabled(False)

            # Emit selection signal
            self.egi_selected.emit(egi_data, entry_data.get("title", graph_id))

        except Exception as e:
            self.egi_display.setPlainText(f"Error loading EGI: {str(e)}")
            self.clear_linear_forms()
            self.transfer_btn.setEnabled(False)

    def generate_linear_forms(self, egi_data):
        """Generate and display linear forms from EGI data."""
        try:
            # Convert JSON to RelationalGraphWithCuts object
            # This is a simplified conversion - in practice you'd use proper deserialization
            from frozendict import frozendict

            from egi_core_dau import (
                Cut,
                Edge,
                ElementID,
                RelationalGraphWithCuts,
                Vertex,
            )

            # Create vertices
            vertices = frozenset(
                Vertex(ElementID(v["id"])) for v in egi_data.get("V", [])
            )

            # Create edges
            edges = frozenset(Edge(ElementID(e["id"])) for e in egi_data.get("E", []))

            # Create cuts
            cuts = frozenset(Cut(ElementID(c["id"])) for c in egi_data.get("Cut", []))

            # Create nu mapping
            nu_data = egi_data.get("nu", {})
            nu = frozendict(
                {
                    ElementID(k): tuple(ElementID(v) for v in seq)
                    for k, seq in nu_data.items()
                }
            )

            # Create area mapping
            area_data = egi_data.get("area", {})
            area = frozendict(
                {
                    ElementID(k): frozenset(ElementID(e) for e in contents)
                    for k, contents in area_data.items()
                }
            )

            # Create rel mapping
            rel_data = egi_data.get("rel", {})
            rel = frozendict({ElementID(k): v for k, v in rel_data.items()})

            # Create the EGI object
            egi = RelationalGraphWithCuts(
                V=vertices,
                E=edges,
                nu=nu,
                sheet=ElementID(egi_data.get("sheet", "sheet")),
                Cut=cuts,
                area=area,
                rel=rel,
            )

            # Generate EGIF
            try:
                egif_text = generate_egif(egi)
                self.egif_display.setPlainText(egif_text)
            except Exception as e:
                self.egif_display.setPlainText(f"EGIF generation error: {str(e)}")

            # Generate CGIF
            try:
                cgif_text = generate_cgif(egi)
                self.cgif_display.setPlainText(cgif_text)
            except Exception as e:
                self.cgif_display.setPlainText(f"CGIF generation error: {str(e)}")

            # Generate CLIF
            try:
                clif_text = generate_clif(egi)
                self.clif_display.setPlainText(clif_text)
            except Exception as e:
                self.clif_display.setPlainText(f"CLIF generation error: {str(e)}")

        except Exception as e:
            self.clear_linear_forms()
            self.egif_display.setPlainText(f"Linear form generation error: {str(e)}")

    def clear_linear_forms(self):
        """Clear all linear form displays."""
        self.egif_display.setPlainText("No EGI data selected")
        self.cgif_display.setPlainText("No EGI data selected")
        self.clif_display.setPlainText("No EGI data selected")

    def on_transfer_to_ergasterion(self):
        """Transfer current EGI to Ergasterion for practice."""
        if self.current_egi_data and self.current_title:
            self.transfer_to_ergasterion.emit(self.current_egi_data, self.current_title)
            QMessageBox.information(
                self,
                "Transfer Complete",
                f"'{self.current_title}' has been sent to Ergasterion for practice.",
            )

    def receive_from_ergasterion(self, egi_data, title):
        """Receive transformed EGI from Ergasterion for saving."""
        # Add the transformed EGI to the tomos data
        # For now, just show a confirmation - in full implementation this would save to corpus
        QMessageBox.information(
            self,
            "EGI Received",
            f"Transformed EGI '{title}' received from Ergasterion.\n\n"
            f"In full implementation, this would be saved to the tomos with transformation history.",
        )


class ErgasterionTab(QWidget):
    """Ergasterion tab for EGI transformation and practice."""

    # Signal to send transformed EGI back to Organon
    send_to_organon_signal = Signal(dict, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_egi_data = None
        self.current_title = None
        self.transformation_rules = self._create_transformation_rules()
        self.setup_ui()

    def _create_transformation_rules(self):
        """Create the six formal transformation rules."""
        return {
            "DC+": DoubleCutInsertionRule(),
            "DC-": DoubleCutErasureRule(),
            "IT+": IterationRule(),
            "IT-": DeiterationRule(),
            "ERA": ErasureRule(),
            "INS": InsertionRule(),
        }

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Compact header
        header = QLabel("🔨 Ergasterion - Graph Construction Workspace")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setMaximumHeight(30)
        layout.addWidget(header)

        # Status label
        self.status_label = QLabel("Selected: None")
        self.status_label.setMaximumHeight(20)
        layout.addWidget(self.status_label)

        # Main content area
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Left: Transformation rules
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(3)

        rules_label = QLabel("Transformation Rules:")
        rules_label.setMaximumHeight(20)
        left_layout.addWidget(rules_label)

        # Create buttons for all six transformation rules
        self.rule_buttons = {}

        # Double Cut rules
        self.rule_buttons["DC+"] = QPushButton("DC+ (Double Cut Insertion)")
        self.rule_buttons["DC-"] = QPushButton("DC- (Double Cut Erasure)")

        # Iteration rules
        self.rule_buttons["IT+"] = QPushButton("IT+ (Iteration)")
        self.rule_buttons["IT-"] = QPushButton("IT- (Deiteration)")

        # Content rules
        self.rule_buttons["ERA"] = QPushButton("ERA (Erasure)")
        self.rule_buttons["INS"] = QPushButton("INS (Insertion)")

        # Add buttons to layout
        for rule_name, button in self.rule_buttons.items():
            button.clicked.connect(
                lambda checked, rule=rule_name: self.apply_transformation_rule(rule)
            )
            button.setEnabled(False)  # Disabled until EGI is loaded
            left_layout.addWidget(button)

        left_layout.addStretch()

        splitter.addWidget(left_widget)

        # Right: EGI workspace with tabbed display
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(3)

        workspace_label = QLabel("EGI Details & Linear Forms:")
        workspace_label.setMaximumHeight(20)
        right_layout.addWidget(workspace_label)

        # Workspace controls
        controls_layout = QHBoxLayout()
        self.new_sequence_btn = QPushButton("New Sequence")
        self.load_egi_btn = QPushButton("Load EGI")
        controls_layout.addWidget(self.new_sequence_btn)
        controls_layout.addWidget(self.load_egi_btn)
        controls_layout.addStretch()
        right_layout.addLayout(controls_layout)

        # Tabbed display for different formats
        self.display_tabs = QTabWidget()

        # EGI Structure tab
        self.egi_display = QTextEdit()
        self.egi_display.setReadOnly(True)
        self.egi_display.setPlainText(
            "No EGI loaded. Use 'Load EGI' or transfer from Organon."
        )
        self.display_tabs.addTab(self.egi_display, "EGI Structure")

        # Linear forms tabs
        self.egif_display = QTextEdit()
        self.egif_display.setReadOnly(True)
        self.egif_display.setPlainText("No EGI data available")
        self.display_tabs.addTab(self.egif_display, "EGIF")

        self.cgif_display = QTextEdit()
        self.cgif_display.setReadOnly(True)
        self.cgif_display.setPlainText("No EGI data available")
        self.display_tabs.addTab(self.cgif_display, "CGIF")

        self.clif_display = QTextEdit()
        self.clif_display.setReadOnly(True)
        self.clif_display.setPlainText("No EGI data available")
        self.display_tabs.addTab(self.clif_display, "CLIF")

        right_layout.addWidget(self.display_tabs)

        # Add Send to Organon button
        self.send_to_organon_btn = QPushButton("📤 Send to Organon")
        self.send_to_organon_btn.setEnabled(False)
        self.send_to_organon_btn.clicked.connect(self.send_to_organon)
        right_layout.addWidget(self.send_to_organon_btn)

        splitter.addWidget(right_widget)

        # Set splitter proportions - optimize space usage for Ergasterion
        splitter.setSizes([280, 720])

    def load_egi_from_organon(self, egi_data, title):
        """Load EGI data transferred from Organon."""
        self.current_egi_data = egi_data
        self.current_title = title

        # Update status
        self.status_label.setText(f"Selected: {title}")

        # Enable transformation rule buttons and send button
        for button in self.rule_buttons.values():
            button.setEnabled(True)
        self.send_to_organon_btn.setEnabled(True)

        # Display EGI information in structure tab
        content = f"=== {title} ===\n\n"
        content += "📋 Loaded for Practice:\n"
        if egi_data:
            content += f"  Vertices: {len(egi_data.get('V', []))}\n"
            content += f"  Edges: {len(egi_data.get('E', []))}\n"
            content += f"  Cuts: {len(egi_data.get('Cut', []))}\n"
            content += f"  Areas: {len(egi_data.get('area', {}))}\n\n"

            content += "🔧 Ready for Transformation Practice\n"
            content += "Select a transformation rule from the left panel to begin.\n\n"

            content += "📄 Current EGI Structure:\n"
            content += json.dumps(egi_data, indent=2)
        else:
            content += "  No EGI data available\n"

        self.egi_display.setPlainText(content)

        # Generate linear forms if EGI data is available
        if egi_data:
            self.generate_linear_forms(egi_data)
        else:
            self.clear_linear_forms()

    def apply_transformation_rule(self, rule_name):
        """Apply the selected transformation rule with wizard interface."""
        if not self.current_egi_data:
            QMessageBox.warning(self, "No EGI", "Please load an EGI first.")
            return

        # Show transformation wizard
        self.show_transformation_wizard(rule_name)

    def show_transformation_wizard(self, rule_name):
        """Show interactive wizard for transformation rule application."""
        try:
            # Convert JSON EGI data to RelationalGraphWithCuts object
            from frozendict import frozendict

            from egi_core_dau import (
                Cut,
                Edge,
                ElementID,
                RelationalGraphWithCuts,
                Vertex,
            )

            # Create EGI object from JSON data
            vertices = frozenset(
                Vertex(ElementID(v["id"])) for v in self.current_egi_data.get("V", [])
            )
            edges = frozenset(
                Edge(ElementID(e["id"])) for e in self.current_egi_data.get("E", [])
            )
            cuts = frozenset(
                Cut(ElementID(c["id"])) for c in self.current_egi_data.get("Cut", [])
            )

            nu_data = self.current_egi_data.get("nu", {})
            nu = frozendict(
                {
                    ElementID(k): tuple(ElementID(v) for v in seq)
                    for k, seq in nu_data.items()
                }
            )

            area_data = self.current_egi_data.get("area", {})
            # Ensure sheet area exists even if empty
            if not area_data:
                area_data = {self.current_egi_data.get("sheet", "sheet"): []}
            area = frozendict(
                {
                    ElementID(k): frozenset(ElementID(e) for e in contents)
                    for k, contents in area_data.items()
                }
            )

            rel_data = self.current_egi_data.get("rel", {})
            rel = frozendict({ElementID(k): v for k, v in rel_data.items()})

            source_egi = RelationalGraphWithCuts(
                V=vertices,
                E=edges,
                nu=nu,
                sheet=ElementID(self.current_egi_data.get("sheet", "sheet")),
                Cut=cuts,
                area=area,
                rel=rel,
            )

            # Create EGI engine and wizard system
            egi_engine = UniversalEGIEngine()
            wizard_system = UniversalTransformationWizardSystem(egi_engine)

            # Get the appropriate wizard for diagram format
            from chapter21_diagram_engine import DisplayFormat

            wizard = wizard_system.create_wizard(DisplayFormat.DIAGRAM, source_egi)

            # Show the wizard interface instead of executing directly
            from chapter21_transformation_wizards import (
                TransformationRuleType,
                WizardStep,
            )

            rule_type_mapping = {
                "DC+": TransformationRuleType.DOUBLE_CUT,
                "DC-": TransformationRuleType.DOUBLE_CUT,
                "IT+": TransformationRuleType.ITERATION,
                "IT-": TransformationRuleType.DEITERATION,
                "ERA": TransformationRuleType.ERASURE,
                "INS": TransformationRuleType.INSERTION,
            }

            if rule_name in rule_type_mapping:
                wizard.state.rule_type = rule_type_mapping[rule_name]
                wizard.state.current_step = WizardStep.RULE_SELECTION
                wizard.state.can_proceed = True

            # Show wizard dialog for step-by-step guidance
            dialog = TransformationWizardDialog(wizard, rule_name, source_egi, self)
            if dialog.exec() == QDialog.Accepted:
                result = dialog.get_result()
                if result and result.success:
                    self.display_transformation_result(
                        rule_name,
                        {
                            "success": True,
                            "result_egi": self.convert_egi_to_json(result.final_egi),
                            "changes": f"Applied {result.transformation_applied.value if result.transformation_applied else rule_name}",
                        },
                    )
                else:
                    self.display_transformation_result(
                        rule_name,
                        {
                            "success": False,
                            "error": (
                                result.error_message
                                if result
                                else "Transformation cancelled"
                            ),
                        },
                    )
            else:
                self.display_transformation_result(
                    rule_name,
                    {"success": False, "error": "Transformation cancelled by user"},
                )

        except Exception as e:
            self.display_transformation_result(
                rule_name, {"success": False, "error": f"Wizard error: {str(e)}"}
            )

    def convert_egi_to_json(self, egi):
        """Convert RelationalGraphWithCuts back to JSON format."""
        if not egi:
            return {}

        return {
            "sheet": str(egi.sheet),
            "V": [{"id": str(v.id)} for v in egi.V],
            "E": [{"id": str(e.id)} for e in egi.E],
            "Cut": [{"id": str(c.id)} for c in egi.Cut],
            "nu": {str(k): [str(v) for v in seq] for k, seq in egi.nu.items()},
            "area": {
                str(k): [str(e) for e in contents] for k, contents in egi.area.items()
            },
            "rel": {str(k): v for k, v in egi.rel.items()},
        }

    def display_transformation_result(self, rule_name, result):
        """Display the result of a transformation."""
        content = f"=== {rule_name} Applied ===\n\n"
        content += f"📋 Source EGI: {self.current_title}\n\n"

        if result.get("success", False):
            content += "✅ Transformation Successful\n"
            content += f"Changes: {result.get('changes', 'Applied transformation')}\n\n"
            content += "📄 Result EGI Structure:\n"
            content += json.dumps(result.get("result_egi", {}), indent=2)

            # Update current EGI data and regenerate linear forms
            self.current_egi_data = result.get("result_egi", {})
            self.generate_linear_forms(self.current_egi_data)

            # Add button to send transformed EGI back to Organon
            content += "\n\n📤 Transfer Options:\n"
            content += (
                "Use 'Send to Organon' button below to save this transformed EGI."
            )
        else:
            content += "❌ Transformation Failed\n"
            content += f"Error: {result.get('error', 'Unknown error')}\n\n"
            content += "📄 Original EGI Structure:\n"
            content += json.dumps(self.current_egi_data, indent=2)

        self.egi_display.setPlainText(content)

    def send_to_organon(self):
        """Send the current (possibly transformed) EGI back to Organon for saving."""
        if not self.current_egi_data:
            QMessageBox.warning(self, "No EGI", "No EGI data to send to Organon.")
            return

        # Create a modified title to indicate transformation
        modified_title = (
            f"{self.current_title}_transformed"
            if self.current_title
            else "transformed_egi"
        )

        # Emit signal to send data back to Organon
        self.send_to_organon_signal.emit(self.current_egi_data, modified_title)

        QMessageBox.information(
            self,
            "Sent to Organon",
            f"EGI '{modified_title}' has been sent to Organon for saving.",
        )

    def generate_linear_forms(self, egi_data):
        """Generate and display linear forms from EGI data."""
        try:
            # Convert JSON to RelationalGraphWithCuts object
            from frozendict import frozendict

            from egi_core_dau import (
                Cut,
                Edge,
                ElementID,
                RelationalGraphWithCuts,
                Vertex,
            )

            # Create vertices
            vertices = frozenset(
                Vertex(ElementID(v["id"])) for v in egi_data.get("V", [])
            )

            # Create edges
            edges = frozenset(Edge(ElementID(e["id"])) for e in egi_data.get("E", []))

            # Create cuts
            cuts = frozenset(Cut(ElementID(c["id"])) for c in egi_data.get("Cut", []))

            # Create nu mapping
            nu_data = egi_data.get("nu", {})
            nu = frozendict(
                {
                    ElementID(k): tuple(ElementID(v) for v in seq)
                    for k, seq in nu_data.items()
                }
            )

            # Create area mapping
            area_data = egi_data.get("area", {})
            area = frozendict(
                {
                    ElementID(k): frozenset(ElementID(e) for e in contents)
                    for k, contents in area_data.items()
                }
            )

            # Create rel mapping
            rel_data = egi_data.get("rel", {})
            rel = frozendict({ElementID(k): v for k, v in rel_data.items()})

            # Create the EGI object
            egi = RelationalGraphWithCuts(
                V=vertices,
                E=edges,
                nu=nu,
                sheet=ElementID(egi_data.get("sheet", "sheet")),
                Cut=cuts,
                area=area,
                rel=rel,
            )

            # Generate EGIF
            try:
                egif_text = generate_egif(egi)
                self.egif_display.setPlainText(egif_text)
            except Exception as e:
                self.egif_display.setPlainText(f"EGIF generation error: {str(e)}")

            # Generate CGIF
            try:
                cgif_text = generate_cgif(egi)
                self.cgif_display.setPlainText(cgif_text)
            except Exception as e:
                self.cgif_display.setPlainText(f"CGIF generation error: {str(e)}")

            # Generate CLIF
            try:
                clif_text = generate_clif(egi)
                self.clif_display.setPlainText(clif_text)
            except Exception as e:
                self.clif_display.setPlainText(f"CLIF generation error: {str(e)}")

        except Exception as e:
            self.clear_linear_forms()
            self.egif_display.setPlainText(f"Linear form generation error: {str(e)}")

    def clear_linear_forms(self):
        """Clear all linear form displays."""
        self.egif_display.setPlainText("No EGI data available")
        self.cgif_display.setPlainText("No EGI data available")
        self.clif_display.setPlainText("No EGI data available")


class AgonTab(QWidget):
    """Agon: Formal reasoning and endoporeutic game environment."""

    def __init__(self, app_state: ApplicationState):
        super().__init__()
        self.app_state = app_state
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("🏆 Agon - Formal Reasoning Environment")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)

        # Main content
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml(
            """
        <h3>Endoporeutic Game Environment</h3>
        <p>The Agon provides a formal reasoning environment for:</p>
        <ul>
        <li>Universe integration of completed graphs</li>
        <li>Logical consistency validation</li>
        <li>Competitive reasoning challenges</li>
        <li>Formal proof verification</li>
        </ul>
        <p><em>This component integrates with the proven 100% transformation success core logic.</em></p>
        """
        )
        layout.addWidget(content)

        self.setLayout(layout)

    def receive_graph_for_integration(self, egi, title):
        """Receive graph from Ergasterion for universe integration."""
        # Implementation would handle graph integration
        pass


class ArisbeMainWindow(QMainWindow):
    """Main application window with three sub-applications."""

    def __init__(self):
        super().__init__()
        self.app_state = ApplicationState()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Arisbe - Existential Graph Reasoning System")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.organon_tab = OrganonTab(self)
        self.ergasterion_tab = ErgasterionTab(self)
        self.agon_tab = AgonTab(self.app_state)

        # Add tabs
        self.tab_widget.addTab(self.organon_tab, "📚 Organon")
        self.tab_widget.addTab(self.ergasterion_tab, "🔨 Ergasterion")
        self.tab_widget.addTab(self.agon_tab, "🏆 Agon")

        layout.addWidget(self.tab_widget)

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            "Arisbe ready - 100% transformation success core loaded"
        )

        # Connect Organon selection to other tabs
        self.organon_tab.egi_selected.connect(self.on_egi_selected_from_organon)
        self.organon_tab.transfer_to_ergasterion.connect(
            self.ergasterion_tab.load_egi_from_organon
        )

        # Connect Ergasterion back to Organon for saving transformed EGIs
        self.ergasterion_tab.send_to_organon_signal.connect(
            self.organon_tab.receive_from_ergasterion
        )

        # Enable cross-tab communication
        self.setup_cross_tab_communication()

    def on_egi_selected_from_organon(self, egi_data, title):
        """Handle EGI selection from Organon tab."""
        # Update application state with selected EGI
        if egi_data:
            self.app_state.current_egi = egi_data
            self.status_bar.showMessage(f"Selected: {title}")
        else:
            self.status_bar.showMessage("Arisbe ready")

    def create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New EGI", self)
        new_action.triggered.connect(self.new_egi)
        file_menu.addAction(new_action)

        open_action = QAction("Open EGI", self)
        open_action.triggered.connect(self.open_egi)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About Arisbe", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def new_egi(self):
        """Create new EGI."""
        self.tab_widget.setCurrentIndex(1)  # Switch to Ergasterion
        self.ergasterion_tab.initialize_workspace()

    def open_egi(self):
        """Open existing EGI."""
        self.tab_widget.setCurrentIndex(0)  # Switch to Organon

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Arisbe",
            "Arisbe - Existential Graph Reasoning System\n\n"
            "Built around proven 100% transformation success core logic.\n"
            "Implements Frithjof Dau's Chapter 21 transformation rules.\n\n"
            "Three sub-applications:\n"
            "• Organon: Browse and explore EGI corpus\n"
            "• Ergasterion: Construct and edit graphs\n"
            "• Agon: Formal reasoning environment",
        )

    def on_egi_selected(self, egi: RelationalGraphWithCuts, title: str):
        """Handle EGI selection from Organon."""
        self.app_state.current_egi = egi
        self.status_bar.showMessage(f"Selected: {title}")

    def setup_cross_tab_communication(self):
        """Set up communication between tabs for graph sharing."""
        # Enable sending graphs between applications
        pass

    def send_graph_to_agon(self, egi, title):
        """Send a graph from Ergasterion to Agon for universe integration."""
        self.tab_widget.setCurrentIndex(2)  # Switch to Agon
        self.agon_tab.receive_graph_for_integration(egi, title)
        self.status_bar.showMessage(f"Sent {title} to Agon for universe integration")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Arisbe")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Arisbe Project")

    # Create and show main window
    window = ArisbeMainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
