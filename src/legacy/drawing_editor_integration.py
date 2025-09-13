"""
Integration module for enhancing the existing drawing_editor.py with
corpus browsing and improved export functionality.

This module provides mixins and utilities that can be integrated into
the existing drawing editor without requiring a complete rewrite.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QListWidget, QListWidgetItem,
    QTextEdit, QGroupBox, QMessageBox, QFileDialog, QTabWidget
)

# Import our new modules
try:
    sys.path.append(str(Path(__file__).parent))
    from corpus_integration import get_corpus_integration, CorpusCategory
    from egi_export import get_export_manager, ExportFormat
except ImportError as e:
    print(f"Warning: Could not import integration modules: {e}")
    # Provide fallback implementations
    def get_corpus_integration():
        return None
    def get_export_manager():
        return None


class CorpusDockWidget(QDockWidget):
    """Dock widget for corpus browsing functionality."""
    
    corpus_item_selected = Signal(str, dict)  # item_id, metadata
    
    def __init__(self, parent=None):
        super().__init__("Corpus Browser", parent)
        self.corpus_integration = get_corpus_integration()
        self.setup_ui()
        self.load_corpus_items()
    
    def setup_ui(self):
        """Set up the corpus browser UI."""
        widget = QWidget()
        self.setWidget(widget)
        
        layout = QVBoxLayout(widget)
        
        # Category filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Category:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All")
        if self.corpus_integration:
            for category in self.corpus_integration.corpus_manager.get_categories():
                self.category_combo.addItem(category.value.title())
        self.category_combo.currentTextChanged.connect(self.filter_items)
        filter_layout.addWidget(self.category_combo)
        
        layout.addLayout(filter_layout)
        
        # Corpus list
        self.corpus_list = QListWidget()
        self.corpus_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.corpus_list)
        
        # Load button
        load_btn = QPushButton("Load Selected")
        load_btn.clicked.connect(self.load_selected_item)
        layout.addWidget(load_btn)
        
        # Info display
        info_group = QGroupBox("Item Info")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(100)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        layout.addWidget(info_group)
    
    def load_corpus_items(self):
        """Load corpus items into the list."""
        if not self.corpus_integration:
            return
        
        try:
            items = self.corpus_integration.get_corpus_list_for_ui()
            self.all_items = items
            self.filter_items()
        except Exception as e:
            print(f"Error loading corpus items: {e}")
    
    def filter_items(self):
        """Filter items based on selected category."""
        self.corpus_list.clear()
        
        if not hasattr(self, 'all_items'):
            return
        
        selected_category = self.category_combo.currentText().lower()
        
        for item in self.all_items:
            if selected_category == "all" or item["category"] == selected_category:
                list_item = QListWidgetItem(item["title"])
                list_item.setData(Qt.UserRole, item)
                list_item.setToolTip(item["description"])
                self.corpus_list.addItem(list_item)
    
    def on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on corpus item."""
        self.load_selected_item()
    
    def load_selected_item(self):
        """Load the selected corpus item."""
        current_item = self.corpus_list.currentItem()
        if not current_item:
            return
        
        item_data = current_item.data(Qt.UserRole)
        if item_data:
            self.show_item_info(item_data)
            self.corpus_item_selected.emit(item_data["id"], item_data)
    
    def show_item_info(self, item_data: dict):
        """Show information about the selected item."""
        info_lines = [
            f"Title: {item_data['title']}",
            f"Category: {item_data['category'].title()}",
            f"Description: {item_data['description']}",
            ""
        ]
        
        formats = []
        if item_data.get("has_egif"):
            formats.append("EGIF")
        if item_data.get("has_cgif"):
            formats.append("CGIF")
        if item_data.get("has_clif"):
            formats.append("CLIF")
        
        if formats:
            info_lines.append(f"Available formats: {', '.join(formats)}")
        
        self.info_text.setText("\n".join(info_lines))


class ExportDockWidget(QDockWidget):
    """Dock widget for export functionality."""
    
    def __init__(self, parent=None):
        super().__init__("Export", parent)
        self.export_manager = get_export_manager()
        self.drawing_editor = parent  # Reference to main editor
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the export UI."""
        widget = QWidget()
        self.setWidget(widget)
        
        layout = QVBoxLayout(widget)
        
        # Export format selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["EGIF", "EGI JSON", "Drawing Schema"])
        format_layout.addWidget(self.format_combo)
        
        layout.addWidget(format_group)
        
        # Export buttons
        button_group = QGroupBox("Export Actions")
        button_layout = QVBoxLayout(button_group)
        
        # Quick export to clipboard
        clipboard_btn = QPushButton("Copy to Clipboard")
        clipboard_btn.clicked.connect(self.export_to_clipboard)
        button_layout.addWidget(clipboard_btn)
        
        # Export to file
        file_btn = QPushButton("Export to File...")
        file_btn.clicked.connect(self.export_to_file)
        button_layout.addWidget(file_btn)
        
        # Quick EGIF export
        quick_btn = QPushButton("Quick EGIF Export")
        quick_btn.clicked.connect(self.quick_egif_export)
        button_layout.addWidget(quick_btn)
        
        layout.addWidget(button_group)
        
        # Export preview
        preview_group = QGroupBox("Export Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        preview_btn = QPushButton("Generate Preview")
        preview_btn.clicked.connect(self.generate_preview)
        preview_layout.addWidget(preview_btn)
        
        layout.addWidget(preview_group)
    
    def get_drawing_schema(self) -> Optional[Dict]:
        """Get the current drawing schema from the editor."""
        if hasattr(self.drawing_editor, 'model'):
            return self.drawing_editor.model.to_schema()
        return None
    
    def export_to_clipboard(self):
        """Export to clipboard."""
        schema = self.get_drawing_schema()
        if not schema:
            QMessageBox.warning(self, "Export Error", "No drawing data available")
            return
        
        if not self.export_manager:
            QMessageBox.warning(self, "Export Error", "Export manager not available")
            return
        
        try:
            format_name = self.format_combo.currentText()
            export_format = self._get_export_format(format_name)
            
            result = self.export_manager.export_to_string(schema, export_format)
            
            if result.success:
                # Copy to clipboard
                from PySide6.QtGui import QGuiApplication
                clipboard = QGuiApplication.clipboard()
                clipboard.setText(result.content)
                
                QMessageBox.information(self, "Export Success", 
                                      f"Exported to clipboard as {format_name}")
            else:
                error_msg = "\n".join(result.errors) if result.errors else "Unknown error"
                QMessageBox.warning(self, "Export Error", f"Export failed:\n{error_msg}")
        
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Export failed: {str(e)}")
    
    def export_to_file(self):
        """Export to file with dialog."""
        schema = self.get_drawing_schema()
        if not schema:
            QMessageBox.warning(self, "Export Error", "No drawing data available")
            return
        
        format_name = self.format_combo.currentText()
        
        # Get file extension
        extensions = {
            "EGIF": "egif",
            "EGI JSON": "json",
            "Drawing Schema": "json"
        }
        ext = extensions.get(format_name, "txt")
        
        # File dialog
        filename, _ = QFileDialog.getSaveFileName(
            self, f"Export {format_name}", f"graph.{ext}",
            f"{format_name} Files (*.{ext});;All Files (*)")
        
        if not filename:
            return
        
        if not self.export_manager:
            QMessageBox.warning(self, "Export Error", "Export manager not available")
            return
        
        try:
            export_format = self._get_export_format(format_name)
            result = self.export_manager.exporter.export_drawing_schema(
                schema, export_format, Path(filename))
            
            if result.success:
                QMessageBox.information(self, "Export Success", 
                                      f"Exported to {filename}")
            else:
                error_msg = "\n".join(result.errors) if result.errors else "Unknown error"
                QMessageBox.warning(self, "Export Error", f"Export failed:\n{error_msg}")
        
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Export failed: {str(e)}")
    
    def quick_egif_export(self):
        """Quick export to EGIF in default location."""
        schema = self.get_drawing_schema()
        if not schema:
            QMessageBox.warning(self, "Export Error", "No drawing data available")
            return
        
        if not self.export_manager:
            QMessageBox.warning(self, "Export Error", "Export manager not available")
            return
        
        try:
            result = self.export_manager.quick_export_egif(schema)
            
            if result.success:
                QMessageBox.information(self, "Export Success", 
                                      f"Quick exported to {result.file_path}")
            else:
                error_msg = "\n".join(result.errors) if result.errors else "Unknown error"
                QMessageBox.warning(self, "Export Error", f"Export failed:\n{error_msg}")
        
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Export failed: {str(e)}")
    
    def generate_preview(self):
        """Generate export preview."""
        schema = self.get_drawing_schema()
        if not schema:
            self.preview_text.setText("No drawing data available")
            return
        
        if not self.export_manager:
            self.preview_text.setText("Export manager not available")
            return
        
        try:
            format_name = self.format_combo.currentText()
            export_format = self._get_export_format(format_name)
            
            result = self.export_manager.export_to_string(schema, export_format)
            
            if result.success:
                # Show first 500 characters
                preview = result.content[:500]
                if len(result.content) > 500:
                    preview += "\n... (truncated)"
                self.preview_text.setText(preview)
            else:
                error_msg = "\n".join(result.errors) if result.errors else "Unknown error"
                self.preview_text.setText(f"Preview failed:\n{error_msg}")
        
        except Exception as e:
            self.preview_text.setText(f"Preview failed: {str(e)}")
    
    def _get_export_format(self, format_name: str) -> 'ExportFormat':
        """Convert format name to ExportFormat enum."""
        format_map = {
            "EGIF": ExportFormat.EGIF,
            "EGI JSON": ExportFormat.EGI_JSON,
            "Drawing Schema": ExportFormat.DRAWING_SCHEMA
        }
        return format_map.get(format_name, ExportFormat.EGIF)


class DrawingEditorIntegration:
    """Integration helper for adding corpus and export functionality to drawing editor."""
    
    def __init__(self, drawing_editor):
        self.drawing_editor = drawing_editor
        self.corpus_dock = None
        self.export_dock = None
    
    def add_corpus_browser(self):
        """Add corpus browser dock widget to the drawing editor."""
        self.corpus_dock = CorpusDockWidget(self.drawing_editor)
        self.corpus_dock.corpus_item_selected.connect(self.on_corpus_item_selected)
        
        self.drawing_editor.addDockWidget(Qt.LeftDockWidgetArea, self.corpus_dock)
        
        # Add menu action to show/hide
        if hasattr(self.drawing_editor, 'menuBar'):
            view_menu = self.drawing_editor.menuBar().addMenu("View")
            corpus_action = self.corpus_dock.toggleViewAction()
            corpus_action.setText("Corpus Browser")
            view_menu.addAction(corpus_action)
    
    def add_export_panel(self):
        """Add export panel dock widget to the drawing editor."""
        self.export_dock = ExportDockWidget(self.drawing_editor)
        
        self.drawing_editor.addDockWidget(Qt.RightDockWidgetArea, self.export_dock)
        
        # Add menu action to show/hide
        if hasattr(self.drawing_editor, 'menuBar'):
            view_menu = None
            # Find existing View menu or create it
            for action in self.drawing_editor.menuBar().actions():
                if action.text() == "View":
                    view_menu = action.menu()
                    break
            
            if not view_menu:
                view_menu = self.drawing_editor.menuBar().addMenu("View")
            
            export_action = self.export_dock.toggleViewAction()
            export_action.setText("Export Panel")
            view_menu.addAction(export_action)
    
    def on_corpus_item_selected(self, item_id: str, metadata: dict):
        """Handle corpus item selection."""
        try:
            corpus_integration = get_corpus_integration()
            if not corpus_integration:
                QMessageBox.warning(self.drawing_editor, "Error", 
                                  "Corpus integration not available")
                return
            
            # Load the corpus item
            schema = corpus_integration.load_item_for_editor(item_id)
            if schema:
                self.load_schema_into_editor(schema)
                
                # Update status
                if hasattr(self.drawing_editor, 'statusBar'):
                    self.drawing_editor.statusBar().showMessage(
                        f"Loaded corpus item: {metadata.get('title', item_id)}")
            else:
                QMessageBox.warning(self.drawing_editor, "Load Error", 
                                  f"Could not load corpus item: {item_id}")
        
        except Exception as e:
            QMessageBox.critical(self.drawing_editor, "Load Error", 
                               f"Failed to load corpus item: {str(e)}")
    
    def load_schema_into_editor(self, schema: dict):
        """Load a schema into the drawing editor."""
        try:
            # Clear current content
            if hasattr(self.drawing_editor, 'scene'):
                self.drawing_editor.scene.clear()
            
            # Reset model
            if hasattr(self.drawing_editor, 'model'):
                # Use the existing model's from_schema method if available
                if hasattr(self.drawing_editor.model, 'from_schema'):
                    self.drawing_editor.model = self.drawing_editor.model.from_schema(
                        self.drawing_editor.scene, schema)
                else:
                    # Fallback: manually populate the model
                    self._populate_model_from_schema(schema)
            
            # Update any preview or status displays
            if hasattr(self.drawing_editor, '_update_preview'):
                self.drawing_editor._update_preview()
            
            if hasattr(self.drawing_editor, '_schedule_ligature_refresh'):
                self.drawing_editor._schedule_ligature_refresh()
        
        except Exception as e:
            raise Exception(f"Failed to load schema into editor: {str(e)}")
    
    def _populate_model_from_schema(self, schema: dict):
        """Manually populate model from schema (fallback method)."""
        # This would implement manual population if the model doesn't have from_schema
        # For now, just log that we received the schema
        print(f"Received schema with {len(schema.get('vertices', []))} vertices, "
              f"{len(schema.get('predicates', []))} predicates, "
              f"{len(schema.get('cuts', []))} cuts")


def integrate_drawing_editor(drawing_editor):
    """Integrate corpus and export functionality into an existing drawing editor."""
    integration = DrawingEditorIntegration(drawing_editor)
    
    # Add corpus browser
    integration.add_corpus_browser()
    
    # Add export panel
    integration.add_export_panel()
    
    return integration

