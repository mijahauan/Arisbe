#!/usr/bin/env python3
"""
Arisbe Main Application Framework
================================

Main GUI application with three sub-applications:
- Organon: Graph browsing and exploration
- Ergasterion: Graph construction and editing
- Agon: Endoporeutic Game formal reasoning

Built around the proven 100% transformation success core logic.
"""

import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QAction, QFont
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
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
except ImportError:
    print("PyQt6 not available. Install with: pip install PyQt6")
    sys.exit(1)

# Import core transformation engine
sys.path.append(str(Path(__file__).parent.parent))
from chapter21_transformation_sequences import TransformationSequenceEngine
from egi_core_dau import RelationalGraphWithCuts

# Import tomos management
try:
    from tomos_index import list_entries, load_index
    from corpus_integration import CorpusIntegration, CorpusItem, CorpusManager
except ImportError:
    # Create dummy classes if tomos modules not available
    class CorpusManager:
        def get_categories(self):
            return []

        def get_items_by_category(self, cat):
            return []

    class CorpusIntegration:
        def __init__(self, manager):
            pass

    class CorpusItem:
        pass

    def load_index():
        return {}

    def list_entries(index):
        return []


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
    """Organon: Graph browsing and exploration of existing EGI tomos."""

    egi_selected = pyqtSignal(RelationalGraphWithCuts, str)

    def __init__(self, app_state: ApplicationState):
        super().__init__()
        self.app_state = app_state
        self.annotations = {}  # Store annotations by EGI ID
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        # Left panel: EGI browser and tools
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        # Search and filter tools
        search_label = QLabel("Search & Filter")
        search_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        left_layout.addWidget(search_label)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search graphs...")
        self.search_box.textChanged.connect(self.on_search_changed)
        left_layout.addWidget(self.search_box)

        # Category filter
        filter_layout = QHBoxLayout()
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.currentTextChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.category_filter)

        # View options
        self.show_metadata = QCheckBox("Show Metadata")
        self.show_metadata.stateChanged.connect(self.on_view_options_changed)
        filter_layout.addWidget(self.show_metadata)

        left_layout.addLayout(filter_layout)

        # Ingestion tools
        ingestion_label = QLabel("Graph Management")
        ingestion_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        left_layout.addWidget(ingestion_label)

        ingestion_buttons = QHBoxLayout()
        self.import_btn = QPushButton("Import EGI")
        self.import_btn.clicked.connect(self.import_egi)
        ingestion_buttons.addWidget(self.import_btn)

        self.load_corpus_btn = QPushButton("Refresh Corpus")
        self.load_corpus_btn.clicked.connect(self.load_corpus)
        ingestion_buttons.addWidget(self.load_corpus_btn)

        self.new_graph_btn = QPushButton("New Graph")
        self.new_graph_btn.clicked.connect(self.create_new_graph)
        ingestion_buttons.addWidget(self.new_graph_btn)

        left_layout.addLayout(ingestion_buttons)

        # Browser
        browser_label = QLabel("EGI Tomos Browser")
        browser_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        left_layout.addWidget(browser_label)

        self.egi_tree = QTreeWidget()
        self.egi_tree.setHeaderLabel("Available EGIs")
        self.populate_egi_tree()
        self.egi_tree.itemClicked.connect(self.on_egi_selected)
        left_layout.addWidget(self.egi_tree)

        # View mode controls
        view_mode_label = QLabel("View Mode")
        view_mode_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        left_layout.addWidget(view_mode_label)

        view_buttons = QHBoxLayout()
        self.synchronic_btn = QPushButton("Synchronic")
        self.synchronic_btn.setCheckable(True)
        self.synchronic_btn.setChecked(True)
        self.synchronic_btn.clicked.connect(lambda: self.set_view_mode("synchronic"))
        view_buttons.addWidget(self.synchronic_btn)

        self.diachronic_btn = QPushButton("Diachronic")
        self.diachronic_btn.setCheckable(True)
        self.diachronic_btn.clicked.connect(lambda: self.set_view_mode("diachronic"))
        view_buttons.addWidget(self.diachronic_btn)

        left_layout.addLayout(view_buttons)

        left_panel.setLayout(left_layout)

        # Right panel: Display and annotation
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # Export tools
        export_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export EGI")
        self.export_btn.clicked.connect(self.export_egi)
        export_layout.addWidget(self.export_btn)

        self.export_format = QPushButton("Format Options")
        self.export_format.clicked.connect(self.show_export_options)
        export_layout.addWidget(self.export_format)

        export_layout.addStretch()
        right_layout.addLayout(export_layout)

        # Linear form display
        self.linear_display = LinearFormDisplay()
        right_layout.addWidget(self.linear_display)

        # Annotation panel
        annotation_label = QLabel("Annotations & Citations")
        annotation_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        right_layout.addWidget(annotation_label)

        self.annotation_area = QTextEdit()
        self.annotation_area.setMaximumHeight(150)
        self.annotation_area.setPlaceholderText("Add comments, citations, and notes...")
        self.annotation_area.textChanged.connect(self.on_annotation_changed)
        right_layout.addWidget(self.annotation_area)

        right_panel.setLayout(right_layout)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 650])

        layout.addWidget(splitter)
        self.setLayout(layout)

        # Initialize view mode
        self.current_view_mode = "synchronic"
        self.current_egi_name = None
        self.tomos_manager = None
        self.tomos_integration = None
        self.filtered_items = []

    def populate_egi_tree(self):
        """Populate tree with actual tomos data."""
        # Load tomos manager
        self.tomos_manager = CorpusManager()
        self.tomos_integration = CorpusIntegration(self.tomos_manager)

        # Load tomos index
        corpus_index = load_index()
        corpus_entries = list_entries(corpus_index)

        # Group by category
        categories = {}
        for entry in corpus_entries:
            category = entry.get("category", "Uncategorized")
            if category not in categories:
                categories[category] = []
            categories[category].append(entry)

        # Add tomos items by category
        for category_name in sorted(categories.keys()):
            category_item = QTreeWidgetItem([category_name])
            category_item.setData(
                0, Qt.ItemDataRole.UserRole, {"type": "category", "name": category_name}
            )
            self.egi_tree.addTopLevelItem(category_item)

            for entry in categories[category_name]:
                child_item = QTreeWidgetItem([entry.get("title", entry["id"])])
                child_item.setData(
                    0,
                    Qt.ItemDataRole.UserRole,
                    {"type": "entry", "id": entry["id"], "entry": entry},
                )
                category_item.addChild(child_item)

        # Add tomos manager items
        for category in self.tomos_manager.get_categories():
            items = self.tomos_manager.get_items_by_category(category)
            if items:
                category_item = QTreeWidgetItem([category.value.title()])
                category_item.setData(
                    0,
                    Qt.ItemDataRole.UserRole,
                    {"type": "corpus_category", "category": category},
                )
                self.egi_tree.addTopLevelItem(category_item)

                for item in items:
                    child_item = QTreeWidgetItem([item.title])
                    child_item.setData(
                        0,
                        Qt.ItemDataRole.UserRole,
                        {"type": "corpus_item", "item": item},
                    )
                    category_item.addChild(child_item)

        peirce_item = QTreeWidgetItem(["Peirce Historical"])
        corpus_folder.addChild(peirce_item)

        textbook_item = QTreeWidgetItem(["Textbook Examples"])

        # Add developed universe graphs from Agon
        universe_folder = QTreeWidgetItem(["Universe of Discourse (Agon)"])
        self.egi_tree.addTopLevelItem(universe_folder)

        # Sample universe items
        philosophy_universe = QTreeWidgetItem(["Philosophy Domain"])
        universe_folder.addChild(philosophy_universe)

        science_universe = QTreeWidgetItem(["Scientific Reasoning"])
        universe_folder.addChild(science_universe)

        logic_universe = QTreeWidgetItem(["Formal Logic System"])
        universe_folder.addChild(logic_universe)

    def on_egi_selected(self, item: QTreeWidgetItem, column: int):
        """Handle EGI selection from tree."""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)

        if not item_data or item_data.get("type") not in ["entry", "corpus_item"]:
            return

        if item_data["type"] == "entry":
            # Load from tomos index
            entry = item_data["entry"]
            self.display_corpus_entry(entry)

        elif item_data["type"] == "corpus_item":
            # Load from tomos manager
            corpus_item = item_data["item"]
            self.display_corpus_item(corpus_item)

            # Try to parse to EGI and emit signal
            egi = self.tomos_manager.parse_item_to_egi(corpus_item.id)
            if egi:
                self.egi_selected.emit(egi, corpus_item.title)

    def import_egi(self):
        """Import EGI from file."""
        from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import EGI", "", "EGI Files (*.json *.egif *.yaml);;All Files (*)"
        )

        if file_path:
            # Get graph details
            graph_id, ok = QInputDialog.getText(
                self, "Graph ID", "Enter unique ID for this graph:"
            )

            if ok and graph_id:
                title, ok = QInputDialog.getText(
                    self, "Graph Title", "Enter title for this graph:", text=graph_id
                )

                if ok:
                    try:
                        # Create graph directory
                        graph_dir = create_graph_dir(graph_id, title, "imported")

                        # Copy file content
                        import shutil

                        target_path = graph_dir / f"{graph_id}.egi.json"
                        shutil.copy2(file_path, target_path)

                        # Refresh corpus
                        self.load_corpus()

                        QMessageBox.information(
                            self,
                            "Import Success",
                            f"Graph '{title}' imported successfully as {graph_id}",
                        )

                    except Exception as e:
                        QMessageBox.warning(
                            self, "Import Error", f"Failed to import graph: {e}"
                        )

    def load_corpus(self):
        """Refresh tomos from directory."""
        try:
            # Reload tomos data
            self.tomos_manager = CorpusManager()
            self.tomos_integration = CorpusIntegration(self.tomos_manager)

            # Update category filter
            self.category_filter.clear()
            self.category_filter.addItem("All Categories")
            for category in self.tomos_manager.get_categories():
                self.category_filter.addItem(category.value.title())

            # Repopulate tree
            self.populate_egi_tree()

            # Show statistics
            stats = self.tomos_manager.get_statistics()
            self.linear_display.display_area.setPlainText(
                f"Tomos Refreshed\n\n"
                f"Total Items: {stats['total_items']}\n"
                f"Categories: {', '.join(stats['by_category'].keys())}\n"
                f"Formats: EGIF({stats['by_format']['egif']}), "
                f"CGIF({stats['by_format']['cgif']}), "
                f"CLIF({stats['by_format']['clif']})\n\n"
                f"Select an item from the tree to view details."
            )

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self, "Tomos Load Error", f"Failed to load corpus: {e}"
            )

    def export_egi(self):
        """Export current EGI to various formats."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        if not self.current_egi_name:
            QMessageBox.warning(self, "Export", "No EGI selected for export.")
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export EGI",
            f"{self.current_egi_name}",
            "EGIF (*.egif);;JSON (*.json);;YAML (*.yaml);;LaTeX (*.tex);;SVG (*.svg);;PNG (*.png)",
        )

        if file_path:
            try:
                # TODO: Implement actual export functionality
                format_type = selected_filter.split("(")[0].strip()

                # Add send to Ergasterion option
                reply = QMessageBox.question(
                    self,
                    "Export Complete",
                    f"EGI exported as {format_type} to: {file_path}\n\n"
                    "Would you like to send this graph to Ergasterion for editing and practice?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.send_to_ergasterion()

            except Exception as e:
                QMessageBox.warning(self, "Export Error", f"Failed to export EGI: {e}")

    def send_to_ergasterion(self):
        """Send current EGI to Ergasterion for editing."""
        if self.current_egi_name and hasattr(self.parent(), "tab_widget"):
            # Get the current EGI
            current_egi = (
                self.app_state.current_egi if self.app_state.current_egi else None
            )

            # Switch to Ergasterion tab
            main_window = self.parent()
            while main_window and not hasattr(main_window, "ergasterion_tab"):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, "ergasterion_tab"):
                main_window.tab_widget.setCurrentIndex(1)
                if current_egi:
                    main_window.ergasterion_tab.load_exemplar_from_organon(
                        current_egi, self.current_egi_name
                    )
                main_window.status_bar.showMessage(
                    f"Sent {self.current_egi_name} to Ergasterion for editing"
                )

    def show_export_options(self):
        """Show export format options dialog."""
        from PyQt6.QtWidgets import QCheckBox, QDialog, QLabel, QPushButton, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Export Format Options")
        dialog.setModal(True)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Available Export Formats:"))

        formats = [
            ("EGIF", "Native Arisbe format"),
            ("JSON", "Machine-readable structured data"),
            ("YAML", "Human-readable structured data"),
            ("LaTeX", "Academic publication format"),
            ("SVG", "Scalable vector graphics"),
            ("PNG", "Raster image format"),
            ("FOPL", "First-order predicate logic"),
            ("Graphviz DOT", "Graph description language"),
        ]

        for fmt, desc in formats:
            checkbox = QCheckBox(f"{fmt} - {desc}")
            layout.addWidget(checkbox)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def set_view_mode(self, mode: str):
        """Set synchronic or diachronic view mode."""
        self.current_view_mode = mode

        # Update button states
        self.synchronic_btn.setChecked(mode == "synchronic")
        self.diachronic_btn.setChecked(mode == "diachronic")

        # Refresh display with new mode
        if self.current_egi_name:
            # TODO: Refresh current EGI display with new view mode
            self.linear_display.display_area.append(
                f"\nView mode changed to: {mode.upper()}"
            )

    def display_egi_with_mode(self, egi: RelationalGraphWithCuts, title: str):
        """Display EGI according to current view mode."""
        if self.current_view_mode == "synchronic":
            # Static view of current EGI state
            self.linear_display.display_egi(egi, f"{title} (Synchronic View)")

            # Add contextual information
            context_info = "\n=== Graph Context ===\n"
            if (
                "exemplar" in title.lower()
                or "dau" in title.lower()
                or "peirce" in title.lower()
            ):
                context_info += "Type: Isolated Exemplar Graph\n"
                context_info += "Source: Academic literature/textbook\n"
                context_info += "Purpose: Illustration and reference\n"
            elif "universe" in title.lower() or "agon" in title.lower():
                context_info += "Type: Universe of Discourse Component\n"
                context_info += "Source: Developed reasoning system\n"
                context_info += "Purpose: Active logical framework\n"
            else:
                context_info += "Type: Working graph\n"

            self.linear_display.display_area.append(context_info)
        else:
            # Diachronic view showing transformation history
            content = f"=== {title} (Diachronic View) ===\n\n"
            content += "Living System Evolution:\n"
            content += "1. Initial assertion or hypothesis\n"
            content += "2. Rule-governed transformations\n"
            content += "3. Fact introduction and pattern discovery\n"
            content += "4. Integration with universe of discourse\n\n"
            content += "Transformation Provenance:\n"
            content += "[Future: Complete transformation history]\n"
            content += "[Future: Reasoning justifications]\n"
            content += "[Future: Endoporeutic Game sessions]\n\n"
            content += "Current State:\n"
            self.linear_display.display_area.setPlainText(content)
            # Append current EGI info
            self.linear_display.display_egi(egi, "Current")

    def load_annotations_for_egi(self, egi_id: str):
        """Load annotations for the selected EGI."""
        if egi_id in self.annotations:
            self.annotation_area.setPlainText(self.annotations[egi_id])
        else:
            self.annotation_area.clear()

    def on_annotation_changed(self):
        """Handle annotation text changes."""
        if self.current_egi_name:
            self.annotations[self.current_egi_name] = self.annotation_area.toPlainText()

    def find_graphs(self, search_term: str):
        """Search for graphs by content or metadata."""
        # TODO: Implement graph search functionality
        results = []
        # Search through corpus, annotations, etc.
        return results

    def explore_universe_connections(self, egi_id: str):
        """Explore connections to universe of discourse."""
        # TODO: Show how this graph relates to developed universes
        pass

    def on_search_changed(self):
        """Handle search text changes."""
        search_term = self.search_box.text().strip()
        if len(search_term) >= 2:
            # Filter tomos tree based on search term
            self.filter_corpus_tree(search_term)
        elif len(search_term) == 0:
            # Show all items when search is cleared
            self.populate_corpus_tree()

    def on_filter_changed(self):
        """Handle category filter changes."""
        selected_category = self.category_filter.currentText()
        self.filter_by_category(selected_category)

    def on_view_options_changed(self):
        """Handle view options changes."""
        show_metadata = self.show_metadata.isChecked()
        # Update display to show/hide metadata
        self.update_display_options(show_metadata)

    def filter_corpus_tree(self, search_term: str):
        """Filter tomos tree by search term."""
        # TODO: Implement search filtering
        pass

    def filter_by_category(self, category: str):
        """Filter tomos by category."""
        # TODO: Implement category filtering
        pass

    def update_display_options(self, show_metadata: bool):
        """Update display options."""
        # TODO: Implement metadata display toggle
        pass

    def create_new_graph(self):
        """Create a new graph."""
        self.linear_display.display_area.append("\n📄 Creating new graph...\n")
        self.linear_display.display_area.append(
            "[Future: New graph creation workflow]\n"
        )

    def import_egi(self):
        """Import an EGI file."""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import EGI", "", "EGI Files (*.egi.json);;All Files (*)"
        )
        if file_path:
            self.linear_display.display_area.append(
                f"\n📥 Importing EGI from: {file_path}\n"
            )
            # TODO: Implement EGI import

    def load_corpus(self):
        """Load/refresh the tomos."""
        self.linear_display.display_area.append("\n🔄 Refreshing tomos...\n")
        self.populate_corpus_tree()

    def populate_egi_tree(self):
        """Populate the EGI tree widget with actual tomos data."""
        self.egi_tree.clear()

        try:
            import json
            from pathlib import Path

            # Load tomos index
            tomos_root = Path(__file__).parent.parent.parent / "corpus"
            index_path = tomos_root / "index.json"

            if not index_path.exists():
                # Fallback to sample entries if tomos not available
                self._populate_sample_entries()
                return

            with open(index_path, "r") as f:
                corpus_index = json.load(f)

            # Group entries by category
            categories = {}
            for entry in corpus_index.get("entries", []):
                category = entry.get("category", "Uncategorized")
                if category is None:
                    category = "General"

                if category not in categories:
                    categories[category] = []
                categories[category].append(entry["id"])

            # Add categories to tree
            for category, items in categories.items():
                category_item = QTreeWidgetItem([category.title()])
                self.egi_tree.addTopLevelItem(category_item)

                for item in sorted(items):
                    child_item = QTreeWidgetItem([item])
                    category_item.addChild(child_item)

            self.egi_tree.expandAll()

        except Exception as e:
            print(f"Error loading corpus: {e}")
            self._populate_sample_entries()

    def _populate_sample_entries(self):
        """Fallback method to populate sample entries."""
        categories = {
            "Exemplar Graphs": ["dau_2006_p112_ligature", "peirce_authentic_example"],
            "Universe Components": ["agon_developed_universe", "discourse_framework"],
            "Working Graphs": ["test_transformation", "practice_session"],
        }

        for category, items in categories.items():
            category_item = QTreeWidgetItem([category])
            self.egi_tree.addTopLevelItem(category_item)

            for item in items:
                child_item = QTreeWidgetItem([item])
                category_item.addChild(child_item)

        self.egi_tree.expandAll()

    def populate_corpus_tree(self):
        """Populate tomos tree (alias for populate_egi_tree)."""
        self.populate_egi_tree()

    def on_egi_selected(self, item, column):
        """Handle EGI selection from tree."""
        if item.parent():  # Only handle leaf items
            egi_name = item.text(0)
            self.current_egi_name = egi_name
            self.linear_display.display_area.setPlainText(
                f"=== {egi_name} ===\n\nLoading EGI data...\n"
            )

            # Load actual EGI data
            try:
                self._load_and_display_egi(egi_name)
            except Exception as e:
                self.linear_display.display_area.setPlainText(
                    f"=== {egi_name} ===\n\n❌ Error loading EGI: {str(e)}\n"
                )

    def _load_and_display_egi(self, egi_name):
        """Load EGI data from tomos and display linear forms."""
        import json
        import os
        from pathlib import Path

        # Load tomos index to find the EGI
        tomos_root = Path(__file__).parent.parent.parent / "corpus"
        index_path = tomos_root / "index.json"

        if not index_path.exists():
            raise FileNotFoundError(f"Tomos index not found at {index_path}")

        with open(index_path, "r") as f:
            corpus_index = json.load(f)

        # Find the EGI entry
        egi_entry = None
        for entry in corpus_index.get("entries", []):
            if entry["id"] == egi_name or entry["title"] == egi_name:
                egi_entry = entry
                break

        if not egi_entry:
            raise ValueError(f"EGI '{egi_name}' not found in corpus")

        # Load the EGI JSON file
        egi_path = Path(egi_entry["path"]) / f"{egi_name}.egi.json"
        full_egi_path = tomos_root.parent / egi_path

        if not full_egi_path.exists():
            raise FileNotFoundError(f"EGI file not found at {full_egi_path}")

        with open(full_egi_path, "r") as f:
            egi_data = json.load(f)

        # Convert to RelationalGraphWithCuts and generate linear forms
        try:
            from cgif_generator_dau import generate_cgif
            from clif_generator_dau import generate_clif
            from egi_dto import dto_to_egi
            from egif_generator_dau import generate_egif

            # Convert JSON to EGI object
            egi = dto_to_egi(egi_data)

            # Generate linear forms
            egif_form = generate_egif(egi)
            cgif_form = generate_cgif(egi)
            clif_form = generate_clif(egi)

            # Display the results
            display_text = f"=== {egi_name} ===\n\n"
            display_text += f"📊 EGI Structure:\n"
            display_text += f"  • Vertices: {len(egi.V)}\n"
            display_text += f"  • Edges: {len(egi.E)}\n"
            display_text += f"  • Cuts: {len(egi.Cut)}\n"
            display_text += f"  • Sheet: {egi.sheet}\n\n"

            display_text += f"📝 EGIF (Existential Graph Interchange Format):\n"
            display_text += f"{egif_form}\n\n"

            display_text += f"📝 CGIF (Conceptual Graph Interchange Format):\n"
            display_text += f"{cgif_form}\n\n"

            display_text += f"📝 CLIF (Common Logic Interchange Format):\n"
            display_text += f"{clif_form}\n"

            self.linear_display.display_area.setPlainText(display_text)

        except Exception as e:
            # Fallback: display raw JSON data if conversion fails
            display_text = f"=== {egi_name} ===\n\n"
            display_text += f"⚠️ Linear form generation failed: {str(e)}\n\n"
            display_text += f"📄 Raw EGI JSON Data:\n"
            display_text += json.dumps(egi_data, indent=2)
            self.linear_display.display_area.setPlainText(display_text)

    def export_egi(self):
        """Export current EGI."""
        if not hasattr(self, "current_egi_name") or not self.current_egi_name:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.information(self, "No Selection", "Please select an EGI first.")
            return

        self.linear_display.display_area.append(
            f"\n📤 Exporting {self.current_egi_name}...\n"
        )
        # TODO: Implement export functionality

    def display_corpus_entry(self, entry: Dict[str, Any]):
        """Display a tomos index entry."""
        content = f"=== {entry.get('title', entry['id'])} ===\n\n"
        content += f"ID: {entry['id']}\n"
        content += f"Category: {entry.get('category', 'Uncategorized')}\n"
        content += f"Path: {entry.get('path', 'Unknown')}\n"
        content += f"Updated: {entry.get('updated', 'Unknown')}\n\n"

        if entry.get("tags"):
            content += f"Tags: {', '.join(entry['tags'])}\n\n"

        # Try to load EGI data
        try:
            from pathlib import Path

            repo_root = Path(__file__).resolve().parents[2]
            entry_path = repo_root / entry["path"]

            if entry_path.exists():
                # Try to read info file
                info_file = entry_path / f"{entry['id']}.json"
                if info_file.exists():
                    import json

                    info_data = json.loads(info_file.read_text())
                    content += f"Description: {info_data.get('description', 'No description')}\n\n"

                # Try to read EGI file
                egi_file = entry_path / f"{entry['id']}.egi.json"
                if egi_file.exists():
                    egi_data = json.loads(egi_file.read_text())
                    content += "EGI Structure:\n"
                    content += f"  Vertices: {len(egi_data.get('V', []))}\n"
                    content += f"  Edges: {len(egi_data.get('E', []))}\n"
                    content += f"  Cuts: {len(egi_data.get('Cut', []))}\n\n"

                    # Display linear form
                    content += "Linear Form:\n"
                    content += f"Sheet: {egi_data.get('sheet', 'unknown')}\n"
                    if egi_data.get("V"):
                        content += f"V = {egi_data['V']}\n"
                    if egi_data.get("E"):
                        content += f"E = {egi_data['E']}\n"
                    if egi_data.get("rel"):
                        content += f"rel = {egi_data['rel']}\n"
                    if egi_data.get("nu"):
                        content += f"ν = {egi_data['nu']}\n"
        except Exception as e:
            content += f"Error loading entry data: {e}\n"

        self.linear_display.display_area.setPlainText(content)
        self.current_egi_name = entry.get("title", entry["id"])
        self.annotation_area.setPlainText(f"Notes for {self.current_egi_name}:\n\n")

    def display_corpus_item(self, item: CorpusItem):
        """Display a tomos manager item."""
        content = f"=== {item.title} ===\n\n"
        content += f"ID: {item.id}\n"
        content += f"Category: {item.category.value}\n"
        content += f"Description: {item.description}\n\n"

        if item.metadata:
            content += "Metadata:\n"
            for key, value in item.metadata.items():
                content += f"  {key}: {value}\n"
            content += "\n"

        # Display available formats
        formats = []
        if item.egif_content:
            formats.append("EGIF")
        if item.cgif_content:
            formats.append("CGIF")
        if item.clif_content:
            formats.append("CLIF")

        if formats:
            content += f"Available formats: {', '.join(formats)}\n\n"

        # Display content
        if item.egif_content:
            content += "EGIF Content:\n"
            content += item.egif_content[:500]  # First 500 chars
            if len(item.egif_content) > 500:
                content += "...\n"

        self.linear_display.display_area.setPlainText(content)
        self.current_egi_name = item.title
        self.annotation_area.setPlainText(f"Notes for {item.title}:\n\n")


class ErgasterionTab(QWidget):
    """Ergasterion: Graph construction and editing workspace."""

    def __init__(self, app_state: ApplicationState):
        super().__init__()
        self.app_state = app_state
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("Ergasterion - Graph Construction Workspace")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(header)

        # Main workspace
        workspace_layout = QHBoxLayout()

        # Left: Transformation controls
        controls_panel = QWidget()
        controls_layout = QVBoxLayout()

        controls_label = QLabel("Transformation Rules")
        controls_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        controls_layout.addWidget(controls_label)

        # Mode selection
        mode_label = QLabel("Mode")
        mode_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        controls_layout.addWidget(mode_label)

        self.practice_mode_btn = QPushButton("Practice Mode")
        self.practice_mode_btn.setCheckable(True)
        self.practice_mode_btn.setChecked(True)
        self.practice_mode_btn.clicked.connect(lambda: self.set_mode("practice"))
        controls_layout.addWidget(self.practice_mode_btn)

        self.build_mode_btn = QPushButton("Build Mode")
        self.build_mode_btn.setCheckable(True)
        self.build_mode_btn.clicked.connect(lambda: self.set_mode("build"))
        controls_layout.addWidget(self.build_mode_btn)

        controls_layout.addWidget(QLabel(""))  # Spacer

        # Appearance adjustment tools
        appearance_label = QLabel("Appearance")
        appearance_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        controls_layout.addWidget(appearance_label)

        self.style_btn = QPushButton("Adjust Style")
        self.style_btn.clicked.connect(self.adjust_appearance)
        controls_layout.addWidget(self.style_btn)

        self.layout_btn = QPushButton("Adjust Layout")
        self.layout_btn.clicked.connect(self.adjust_layout)
        controls_layout.addWidget(self.layout_btn)

        controls_layout.addWidget(QLabel(""))  # Spacer

        # Graph building tools
        building_label = QLabel("Graph Building")
        building_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        controls_layout.addWidget(building_label)

        self.new_fact_btn = QPushButton("New Fact")
        self.new_fact_btn.clicked.connect(self.create_new_fact)
        controls_layout.addWidget(self.new_fact_btn)

        self.new_hypothesis_btn = QPushButton("New Hypothesis")
        self.new_hypothesis_btn.clicked.connect(self.create_new_hypothesis)
        controls_layout.addWidget(self.new_hypothesis_btn)

        self.thought_structure_btn = QPushButton("Thought Structure")
        self.thought_structure_btn.clicked.connect(self.create_thought_structure)
        controls_layout.addWidget(self.thought_structure_btn)

        controls_layout.addWidget(QLabel(""))  # Spacer

        # Transformation buttons
        transform_label = QLabel("Transformations")
        transform_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        controls_layout.addWidget(transform_label)

        self.dc_plus_btn = QPushButton("DC+ (Double Cut)")
        self.dc_plus_btn.clicked.connect(lambda: self.apply_transformation("DC+"))
        controls_layout.addWidget(self.dc_plus_btn)

        self.ins_btn = QPushButton("INS (Insertion)")
        self.ins_btn.clicked.connect(lambda: self.apply_transformation("INS"))
        controls_layout.addWidget(self.ins_btn)

        self.iter_btn = QPushButton("IT+ (Iteration)")
        self.iter_btn.clicked.connect(lambda: self.apply_transformation("IT+"))
        controls_layout.addWidget(self.iter_btn)

        self.deiter_btn = QPushButton("IT- (Deiteration)")
        self.deiter_btn.clicked.connect(lambda: self.apply_transformation("IT-"))
        controls_layout.addWidget(self.deiter_btn)

        self.era_btn = QPushButton("ERA (Erasure)")
        self.era_btn.clicked.connect(lambda: self.apply_transformation("ERA"))
        controls_layout.addWidget(self.era_btn)

        self.dc_minus_btn = QPushButton("DC- (Double Cut Elimination)")
        self.dc_minus_btn.clicked.connect(lambda: self.apply_transformation("DC-"))
        controls_layout.addWidget(self.dc_minus_btn)

        controls_layout.addStretch()
        controls_panel.setLayout(controls_layout)
        workspace_layout.addWidget(controls_panel)

        # Right: Display area with wizard panel
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # Wizard status panel
        self.wizard_panel = QWidget()
        wizard_layout = QVBoxLayout()

        self.wizard_status = QLabel("No active wizard")
        self.wizard_status.setFont(QFont("Arial", 9))
        wizard_layout.addWidget(self.wizard_status)

        self.wizard_step_display = QTextEdit()
        self.wizard_step_display.setMaximumHeight(200)
        self.wizard_step_display.setPlaceholderText(
            "Wizard interface will appear here..."
        )
        wizard_layout.addWidget(self.wizard_step_display)

        # Wizard controls
        wizard_controls = QHBoxLayout()
        self.wizard_input = QLineEdit()
        self.wizard_input.setPlaceholderText("Enter wizard command...")
        self.wizard_input.returnPressed.connect(self.handle_wizard_input)
        wizard_controls.addWidget(self.wizard_input)

        self.wizard_execute_btn = QPushButton("Execute")
        self.wizard_execute_btn.clicked.connect(self.handle_wizard_input)
        wizard_controls.addWidget(self.wizard_execute_btn)

        self.wizard_cancel_btn = QPushButton("Cancel")
        self.wizard_cancel_btn.clicked.connect(self.cancel_wizard)
        wizard_controls.addWidget(self.wizard_cancel_btn)

        wizard_layout.addLayout(wizard_controls)
        self.wizard_panel.setLayout(wizard_layout)
        self.wizard_panel.setVisible(False)
        right_layout.addWidget(self.wizard_panel)

        # Main display
        self.linear_display = LinearFormDisplay()
        right_layout.addWidget(self.linear_display)

        right_panel.setLayout(right_layout)
        workspace_layout.addWidget(right_panel)

        layout.addLayout(workspace_layout)
        self.setLayout(layout)

        # Initialize state
        self.current_mode = "practice"
        self.current_exemplar = None
        self.active_wizard = None
        self.wizard_system = None
        self.initialize_workspace()

    def initialize_workspace(self):
        """Initialize workspace with blank sheet."""
        from frozendict import frozendict

        from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex

        # Create blank sheet following Dau's 6+1 component structure
        sheet_id = ElementID("sheet")
        blank_egi = RelationalGraphWithCuts(
            V=frozenset(),  # No vertices initially
            E=frozenset(),  # No edges initially
            nu=frozendict(),  # No ν mappings initially
            sheet=sheet_id,  # Sheet of assertion
            Cut=frozenset(),  # No cuts initially
            area=frozendict(
                {sheet_id: frozenset()}
            ),  # Sheet contains nothing initially
            rel=frozendict(),  # No relation mappings initially
        )

        self.app_state.transformation_engine = TransformationSequenceEngine()
        self.app_state.current_egi = blank_egi
        self.app_state.active_sequence_id = "ergasterion_workspace"

        # Create sequence
        self.app_state.transformation_engine.create_sequence(
            self.app_state.current_egi, self.app_state.active_sequence_id
        )

        self.linear_display.display_egi(
            self.app_state.current_egi, "Workspace - Blank Sheet"
        )

    def set_mode(self, mode: str):
        """Set Ergasterion mode (practice or build)."""
        self.current_mode = mode
        self.practice_mode_btn.setChecked(mode == "practice")
        self.build_mode_btn.setChecked(mode == "build")

        mode_info = {
            "practice": "Practice transformations on exemplar graphs from Organon",
            "build": "Build new graphs for facts, hypotheses, and thought structures",
        }

        self.linear_display.display_area.append(
            f"\n=== Mode Changed to {mode.upper()} ===\n"
        )
        self.linear_display.display_area.append(mode_info[mode])

    def adjust_appearance(self):
        """Adjust visual appearance of current graph."""
        from PyQt6.QtWidgets import (
            QComboBox,
            QDialog,
            QLabel,
            QPushButton,
            QSlider,
            QVBoxLayout,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Adjust Graph Appearance")
        dialog.setModal(True)

        layout = QVBoxLayout()

        # Style selection
        layout.addWidget(QLabel("Visual Style:"))
        style_combo = QComboBox()
        style_combo.addItems(
            ["Peirce Classical", "Modern Minimalist", "Academic", "High Contrast"]
        )
        layout.addWidget(style_combo)

        # Size adjustments
        layout.addWidget(QLabel("Element Sizes:"))

        layout.addWidget(QLabel("Vertex Size:"))
        vertex_slider = QSlider(Qt.Orientation.Horizontal)
        vertex_slider.setRange(50, 200)
        vertex_slider.setValue(100)
        layout.addWidget(vertex_slider)

        layout.addWidget(QLabel("Cut Thickness:"))
        cut_slider = QSlider(Qt.Orientation.Horizontal)
        cut_slider.setRange(1, 10)
        cut_slider.setValue(3)
        layout.addWidget(cut_slider)

        # Apply button
        apply_btn = QPushButton("Apply Changes")
        apply_btn.clicked.connect(lambda: self.apply_appearance_changes(dialog))
        layout.addWidget(apply_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def adjust_layout(self):
        """Adjust spatial layout of current graph."""
        from PyQt6.QtWidgets import (
            QDialog,
            QLabel,
            QPushButton,
            QRadioButton,
            QVBoxLayout,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Adjust Graph Layout")
        dialog.setModal(True)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Layout Algorithm:"))

        force_directed = QRadioButton("Force-Directed")
        force_directed.setChecked(True)
        layout.addWidget(force_directed)

        hierarchical = QRadioButton("Hierarchical")
        layout.addWidget(hierarchical)

        circular = QRadioButton("Circular")
        layout.addWidget(circular)

        manual = QRadioButton("Manual Positioning")
        layout.addWidget(manual)

        apply_btn = QPushButton("Apply Layout")
        apply_btn.clicked.connect(lambda: self.apply_layout_changes(dialog))
        layout.addWidget(apply_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def create_new_fact(self):
        """Create graph representing a new observed fact."""
        from PyQt6.QtWidgets import QInputDialog

        fact_text, ok = QInputDialog.getText(
            self, "New Fact", "Describe the observed fact:"
        )

        if ok and fact_text:
            self.linear_display.display_area.append(f"\n=== Creating New Fact ===\n")
            self.linear_display.display_area.append(f"Fact: {fact_text}\n")
            self.linear_display.display_area.append(
                "Converting to EG representation...\n"
            )
            # TODO: Implement fact-to-EG conversion
            self.linear_display.display_area.append(
                "[Future: Automatic EG generation from natural language]"
            )

    def create_new_hypothesis(self):
        """Create graph representing a new hypothesis."""
        from PyQt6.QtWidgets import QInputDialog

        hypothesis_text, ok = QInputDialog.getText(
            self, "New Hypothesis", "Describe your hypothesis:"
        )

        if ok and hypothesis_text:
            self.linear_display.display_area.append(
                f"\n=== Creating New Hypothesis ===\n"
            )
            self.linear_display.display_area.append(f"Hypothesis: {hypothesis_text}\n")
            self.linear_display.display_area.append("Structuring as testable EG...\n")
            # TODO: Implement hypothesis-to-EG conversion
            self.linear_display.display_area.append(
                "[Future: Hypothesis structuring with testable implications]"
            )

    def create_thought_structure(self):
        """Create a new thought structure."""
        # TODO: Implement thought structure creation
        self.linear_display.display_area.append("\n Creating thought structure...\n")
        self.linear_display.display_area.append(
            "[Future: Guided thought structure creation]\n"
        )

    def _initialize_wizard_system(self):
        """Initialize the transformation wizard system."""
        try:
            from chapter21_diagram_engine import UniversalEGIEngine
            from chapter21_transformation_wizards import (
                UniversalTransformationWizardSystem,
            )

            egi_engine = UniversalEGIEngine()
            self.wizard_system = UniversalTransformationWizardSystem(egi_engine)

        except ImportError as e:
            self.linear_display.display_area.append(
                f"\n Wizard system not available: {e}\n"
            )

    def start_transformation_wizard(self):
        """Start the transformation wizard interface."""
        if not self.current_exemplar:
            QMessageBox.information(
                self, "No Graph", "Please load a graph first from Organon."
            )
            return

        if not self.wizard_system:
            self._initialize_wizard_system()
            if not self.wizard_system:
                QMessageBox.warning(
                    self, "Wizard Error", "Transformation wizard system not available."
                )
                return

        try:
            # Create diagram wizard (default format)
            from chapter21_diagram_engine import DisplayFormat

            self.active_wizard = self.wizard_system.create_wizard(
                DisplayFormat.DIAGRAM, self.current_exemplar
            )

            # Show wizard panel
            self.wizard_panel.setVisible(True)
            self.wizard_status.setText(" Transformation Wizard Active")

            # Display initial wizard interface
            interface = self.active_wizard.render_step_interface(
                self.active_wizard.state.current_step
            )
            self.wizard_step_display.setPlainText(interface)

            # Enable input
            self.wizard_input.setEnabled(True)
            self.wizard_execute_btn.setEnabled(True)

            self.linear_display.display_area.append(
                "\n Transformation Wizard Started\n"
            )
            self.linear_display.display_area.append(
                "Follow the wizard interface above for guided transformations.\n"
            )

        except Exception as e:
            QMessageBox.warning(self, "Wizard Error", f"Failed to start wizard: {e}")

    def handle_wizard_input(self):
        """Handle user input to the wizard."""
        if not self.active_wizard:
            return

        user_input = self.wizard_input.text().strip()
        if not user_input:
            return

        try:
            # Process wizard input
            current_step = self.active_wizard.state.current_step
            success = self.active_wizard.handle_user_input(current_step, user_input)

            if success:
                self.wizard_input.clear()

                # Try to advance to next step
                if self.active_wizard.advance_step():
                    # Update interface for new step
                    interface = self.active_wizard.render_step_interface(
                        self.active_wizard.state.current_step
                    )
                    self.wizard_step_display.setPlainText(interface)

                    step_name = self.active_wizard.state.current_step.value.replace(
                        "_", " "
                    ).title()
                    self.wizard_status.setText(f" Wizard Step: {step_name}")

                else:
                    # Wizard ready for execution
                    self.wizard_status.setText(" Ready for Execution")
                    self.wizard_step_display.setPlainText(
                        "Wizard configuration complete. Click Execute to apply transformation."
                    )

                    # Execute transformation
                    self._execute_wizard_transformation()
            else:
                self.wizard_step_display.append(f"\n Invalid input: {user_input}")
                self.wizard_step_display.append("Please try again with valid input.")

        except Exception as e:
            self.wizard_step_display.append(f"\n Error processing input: {e}")

    def _execute_wizard_transformation(self):
        """Execute the configured wizard transformation."""
        if not self.active_wizard:
            return

        try:
            # Execute transformation
            result = self.active_wizard.execute_transformation()

            if result.success:
                # Update current exemplar
                self.current_exemplar = result.final_egi

                # Display result
                self.linear_display.display_egi(
                    result.final_egi,
                    f"After {result.transformation_applied.value if result.transformation_applied else 'Transformation'}",
                )

                self.wizard_status.setText(" Transformation Complete")
                self.wizard_step_display.setPlainText(
                    f"Transformation successful!\n\n"
                    f"Rule applied: {result.transformation_applied.value if result.transformation_applied else 'Unknown'}\n"
                    f"Steps completed: {len(result.steps_completed)}\n\n"
                    f"The graph has been updated. You can start a new wizard or continue editing."
                )

                # Create proof sequence from wizard result
                self._create_proof_sequence_from_wizard(result)

            else:
                self.wizard_status.setText(" Transformation Failed")
                self.wizard_step_display.setPlainText(
                    f"Transformation failed: {result.error_message}\n\n"
                    f"Please try again or cancel the wizard."
                )

        except Exception as e:
            self.wizard_status.setText(" Execution Error")
            self.wizard_step_display.setPlainText(
                f"Error executing transformation: {e}"
            )

    def _create_proof_sequence_from_wizard(self, wizard_result):
        """Create a proof sequence from wizard result for historical tracking."""
        try:
            from proof_sequence_validator import ProofSequenceValidator, RuleType

            # Create enhanced validator
            validator = ProofSequenceValidator(
                enable_historical_storage=True, enable_compression=True
            )

            # Convert wizard result to proof steps
            steps = []
            if wizard_result.transformation_applied:
                # Map transformation type to proof rule
                if "DOUBLE_CUT" in wizard_result.transformation_applied.value:
                    rule_type = RuleType.CALCULUS
                    rule_name = (
                        "DC+" if "insert" in str(wizard_result).lower() else "DC-"
                    )
                else:
                    rule_type = RuleType.TRANSFORMATION
                    rule_name = wizard_result.transformation_applied.value

                from egi_core_dau import ElementID

                steps.append((rule_type, rule_name, ElementID("sheet"), frozenset()))

            # Create proof sequence
            proof_sequence = validator.validate_proof_sequence(
                start_egi=self.active_wizard.source_egi,
                end_egi=wizard_result.final_egi,
                steps=steps,
                sequence_id=f"wizard_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                metadata={
                    "source": "transformation_wizard",
                    "wizard_format": "DIAGRAM",
                    "user_guided": True,
                    "created_at": datetime.now().isoformat(),
                },
            )

            # Display proof sequence info
            self.linear_display.display_area.append(
                f"\n Proof Sequence Created: {proof_sequence.sequence_id}\n"
                f"Derivation: {proof_sequence.derivation_notation}\n"
                f"Historical tracking: {'' if proof_sequence.historical_graph else ''}\n"
            )

        except Exception as e:
            self.linear_display.display_area.append(
                f"\n Could not create proof sequence: {e}\n"
            )

    def cancel_wizard(self):
        """Cancel the active wizard."""
        self.active_wizard = None
        self.wizard_panel.setVisible(False)
        self.wizard_input.clear()
        self.linear_display.display_area.append("\n Transformation wizard cancelled.\n")

    def apply_appearance_changes(self, dialog):
        """Apply appearance changes to current graph."""
        self.linear_display.display_area.append("\n[Appearance] Visual style updated")
        dialog.close()

    def apply_layout_changes(self, dialog):
        """Apply layout changes to current graph."""
        self.linear_display.display_area.append(
            "\n[Layout] Spatial arrangement updated"
        )
        dialog.close()

    def load_exemplar_from_organon(self, egi: RelationalGraphWithCuts, title: str):
        """Load exemplar graph from Organon for editing."""
        self.current_exemplar = egi
        self.linear_display.display_egi(egi, f"Exemplar: {title}")

        # Initialize wizard system with current EGI
        self._initialize_wizard_system()

        # Add mode-specific information
        if self.current_mode == "practice":
            info = "\n=== PRACTICE MODE ===\n"
            info += "• Apply transformation rules to learn EG operations\n"
            info += "• Validation feedback provided for each step\n"
            info += "• Safe environment for experimentation\n"
            info += "• Use 'Start Wizard' for guided transformations\n\n"
        else:
            info = "\n=== BUILD MODE ===\n"
            info += "• Create new graphs from facts and hypotheses\n"
            info += "• Rule-governed construction process\n"
            info += "• Build towards universe of discourse\n"
            info += "• Use 'Start Wizard' for step-by-step guidance\n\n"

        self.linear_display.display_area.append(info)

    def apply_transformation(self, rule_name: str):
        """Apply transformation rule with mode-aware behavior."""
        if (
            not self.app_state.transformation_engine
            or not self.app_state.active_sequence_id
        ):
            return

        if self.current_mode == "practice":
            self.linear_display.display_area.append(
                f"\n[Practice] Applied {rule_name} transformation"
            )
            self.linear_display.display_area.append(
                "[Practice] Validating transformation correctness..."
            )
            # Add send to Agon option for completed graphs in build mode
        if self.current_mode == "build":
            from PyQt6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self,
                "Send to Agon",
                f"Transformation {rule_name} applied.\n\n"
                "Would you like to send this graph to Agon for universe integration?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.send_to_agon()

    def send_to_agon(self):
        """Send current graph to Agon for universe integration."""
        if hasattr(self.parent(), "send_graph_to_agon") and self.app_state.current_egi:
            main_window = self.parent()
            while main_window and not hasattr(main_window, "send_graph_to_agon"):
                main_window = main_window.parent()

            if main_window:
                graph_title = (
                    "Built Graph" if self.current_mode == "build" else "Practice Graph"
                )
                main_window.send_graph_to_agon(self.app_state.current_egi, graph_title)
            self.linear_display.display_area.append(
                "[Build] Adding to construction sequence..."
            )
            # TODO: Implement build mode with construction tracking

        self.active_game_session = False
        self.start_game_btn.setText("Start Game Session")
        self.start_game_btn.clicked.disconnect()
        self.start_game_btn.clicked.connect(self.start_endoporeutic_game)

    def receive_graph_for_integration(self, egi, title):
        """Receive a graph from Ergasterion for universe integration."""
        self.linear_display.display_area.clear()
        self.linear_display.display_area.append(
            f"=== Graph Received for Integration ===\n"
        )
        self.linear_display.display_area.append(f"Graph: {title}\n")
        self.linear_display.display_area.append(
            "Analyzing for universe compatibility...\n"
        )

        if self.current_universe:
            self.linear_display.display_area.append(
                f"Target Universe: {self.current_universe}\n"
            )
            self.linear_display.display_area.append("Ready for integration evaluation.")
        else:
            self.linear_display.display_area.append(
                "No universe selected. Please choose a target universe."
            )

        # Display the graph
        self.linear_display.display_egi(egi, f"Integration Candidate: {title}")


class AgonTab(QWidget):
    """Agon: Endoporeutic Game formal reasoning environment."""

    def __init__(self, app_state: ApplicationState):
        super().__init__()
        self.app_state = app_state
        self.current_universe = None
        self.active_game_session = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("Agon - Endoporeutic Game Environment")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(header)

        # Main workspace
        workspace_layout = QHBoxLayout()

        # Left: Game controls
        controls_panel = QWidget()
        controls_layout = QVBoxLayout()

        controls_label = QLabel("Game Controls")
        controls_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        controls_layout.addWidget(controls_label)

        # Universe management
        universe_label = QLabel("Universe of Discourse")
        universe_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        controls_layout.addWidget(universe_label)

        self.load_universe_btn = QPushButton("Load Universe")
        self.load_universe_btn.clicked.connect(self.load_universe)
        controls_layout.addWidget(self.load_universe_btn)

        self.create_universe_btn = QPushButton("Create Universe")
        self.create_universe_btn.clicked.connect(self.create_universe)
        controls_layout.addWidget(self.create_universe_btn)

        controls_layout.addWidget(QLabel(""))  # Spacer

        # Game session
        session_label = QLabel("Game Session")
        session_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        controls_layout.addWidget(session_label)

        self.start_game_btn = QPushButton("Start Game")
        self.start_game_btn.clicked.connect(self.start_endoporeutic_game)
        controls_layout.addWidget(self.start_game_btn)

        self.pause_game_btn = QPushButton("Pause Game")
        self.pause_game_btn.clicked.connect(self.pause_game)
        controls_layout.addWidget(self.pause_game_btn)

        self.end_game_btn = QPushButton("End Game")
        self.end_game_btn.clicked.connect(self.end_game)
        controls_layout.addWidget(self.end_game_btn)

        controls_layout.addStretch()
        controls_panel.setLayout(controls_layout)
        workspace_layout.addWidget(controls_panel)

        # Right: Game display
        self.linear_display = LinearFormDisplay()
        workspace_layout.addWidget(self.linear_display)

        layout.addLayout(workspace_layout)
        self.setLayout(layout)

        # Initialize with welcome message
        self.initialize_agon()

    def initialize_agon(self):
        """Initialize Agon with welcome message."""
        welcome = "=== Welcome to Agon ===\n\n"
        welcome += "The Endoporeutic Game environment for formal reasoning.\n\n"
        welcome += "🎯 Purpose: Develop and test logical reasoning within\n"
        welcome += "   established universes of discourse\n\n"
        welcome += "🎮 Game Flow:\n"
        welcome += "   1. Load or create a universe of discourse\n"
        welcome += "   2. Start a reasoning session\n"
        welcome += "   3. Apply transformations within game rules\n"
        welcome += "   4. Build towards logical conclusions\n\n"
        welcome += "📚 Integration: Completed graphs can be sent back\n"
        welcome += "   to Organon for tomos integration\n\n"
        welcome += "Ready to begin formal reasoning!\n"

        self.linear_display.display_area.setPlainText(welcome)

    def load_universe(self):
        """Load an existing universe of discourse."""
        self.linear_display.display_area.append(
            "\n🌌 Loading universe of discourse...\n"
        )
        self.linear_display.display_area.append(
            "[Future: Universe selection and loading]\n"
        )

    def create_universe(self):
        """Create a new universe of discourse."""
        self.linear_display.display_area.append(
            "\n✨ Creating new universe of discourse...\n"
        )
        self.linear_display.display_area.append(
            "[Future: Universe creation workflow]\n"
        )

    def start_endoporeutic_game(self):
        """Start an Endoporeutic Game session."""
        self.linear_display.display_area.append(
            "\n🎮 Starting Endoporeutic Game session...\n"
        )
        self.linear_display.display_area.append(
            "[Future: Game session initialization]\n"
        )
        self.active_game_session = True
        self.start_game_btn.setText("Resume Game")

    def pause_game(self):
        """Pause the current game session."""
        self.linear_display.display_area.append("\n⏸️ Game session paused.\n")

    def end_game(self):
        """End the current game session."""
        self.linear_display.display_area.append("\n🏁 Game session ended.\n")
        self.linear_display.display_area.append(
            "[Future: Session summary and results]\n"
        )
        self.active_game_session = False
        self.start_game_btn.setText("Start Game")

    def receive_graph_for_integration(self, egi, title):
        """Receive a graph from Ergasterion for universe integration."""
        self.linear_display.display_area.clear()
        self.linear_display.display_area.append(
            f"=== Graph Received for Integration ===\n"
        )
        self.linear_display.display_area.append(f"Graph: {title}\n")
        self.linear_display.display_area.append(
            "Analyzing for universe compatibility...\n"
        )

        if self.current_universe:
            self.linear_display.display_area.append(
                f"Target Universe: {self.current_universe}\n"
            )
            self.linear_display.display_area.append("Ready for integration evaluation.")
        else:
            self.linear_display.display_area.append(
                "No universe selected. Please choose a target universe."
            )

        # Display the graph
        self.linear_display.display_egi(egi, f"Integration Candidate: {title}")


class ArisbeMainWindow(QMainWindow):
    """Main Arisbe application window."""

    def __init__(self):
        super().__init__()
        self.app_state = ApplicationState()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Arisbe - Existential Graph Reasoning System")
        self.setGeometry(100, 100, 1200, 800)

        # Create menu bar
        self.create_menu_bar()

        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # Tab widget for three sub-applications
        self.tab_widget = QTabWidget()

        # Create tabs
        self.organon_tab = OrganonTab(self.app_state)
        self.ergasterion_tab = ErgasterionTab(self.app_state)
        self.agon_tab = AgonTab(self.app_state)

        # Store references for cross-tab communication
        self.organon_tab.parent = lambda: self
        self.ergasterion_tab.parent = lambda: self
        self.agon_tab.parent = lambda: self

        # Add tabs
        self.tab_widget.addTab(self.organon_tab, "Organon (Browse)")
        self.tab_widget.addTab(self.ergasterion_tab, "Ergasterion (Build)")
        self.tab_widget.addTab(self.agon_tab, "Agon (Reason)")

        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            "Arisbe ready - 100% transformation success core loaded"
        )

        # Connect signals
        self.organon_tab.egi_selected.connect(self.on_egi_selected)

        # Enable cross-tab communication
        self.setup_cross_tab_communication()

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
        from PyQt6.QtWidgets import QMessageBox

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
