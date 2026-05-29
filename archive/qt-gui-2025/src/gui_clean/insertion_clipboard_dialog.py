"""
Insertion Clipboard Dialog - UI for browsing and selecting subgraphs for INS.

Provides a pop-up window where users can:
- View all clipboard entries
- See preview of each subgraph
- Select an entry for insertion
- Remove unwanted entries
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Optional
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QTextEdit,
    QSplitter,
    QWidget,
    QMessageBox
)
from PySide6.QtGui import QFont

from insertion_clipboard import InsertionClipboard, ClipboardEntry, get_insertion_clipboard


class InsertionClipboardDialog(QDialog):
    """
    Dialog for browsing and selecting from the insertion clipboard.
    
    Signals:
        entry_selected: Emitted when user selects an entry for insertion
    """
    
    entry_selected = Signal(ClipboardEntry)  # Emits selected entry
    
    def __init__(self, clipboard: Optional[InsertionClipboard] = None, parent=None):
        super().__init__(parent)
        
        self.clipboard = clipboard or get_insertion_clipboard()
        self.selected_entry: Optional[ClipboardEntry] = None
        
        self.setWindowTitle("Insertion Clipboard - Select Subgraph for INS")
        self.setMinimumSize(800, 600)
        
        self._setup_ui()
        self._load_entries()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("📋 Insertion Clipboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Select a validated subgraph to insert. "
            "The subgraph will be copied into your target negative area."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        # Splitter for list and details
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: List of entries
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("Available Subgraphs:")
        list_label.setStyleSheet("font-weight: bold;")
        list_layout.addWidget(list_label)
        
        self.entry_list = QListWidget()
        self.entry_list.currentItemChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.entry_list)
        
        # Button to remove entry
        remove_btn = QPushButton("🗑️ Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        list_layout.addWidget(remove_btn)
        
        splitter.addWidget(list_widget)
        
        # Right: Details panel
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        details_label = QLabel("Details:")
        details_label.setStyleSheet("font-weight: bold;")
        details_layout.addWidget(details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        details_layout.addWidget(self.details_text)
        
        # Element list
        elements_label = QLabel("Elements in Subgraph:")
        elements_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        details_layout.addWidget(elements_label)
        
        self.elements_text = QTextEdit()
        self.elements_text.setReadOnly(True)
        self.elements_text.setStyleSheet("font-family: monospace; font-size: 10pt;")
        details_layout.addWidget(self.elements_text)
        
        splitter.addWidget(details_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter, 1)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.select_btn = QPushButton("✓ Select for Insertion")
        self.select_btn.setEnabled(False)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #228B22;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2E8B57;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self.select_btn.clicked.connect(self._on_select_clicked)
        button_layout.addWidget(self.select_btn)
        
        layout.addLayout(button_layout)
    
    def _load_entries(self):
        """Load entries from clipboard into list."""
        print(f"[Dialog] _load_entries called, clipboard instance: {id(self.clipboard)}")
        self.entry_list.clear()
        
        entries = self.clipboard.get_all_entries()
        print(f"[Dialog] Retrieved {len(entries)} entries from clipboard")
        
        if not entries:
            # Show empty state
            print("[Dialog] No entries - showing empty state")
            item = QListWidgetItem("No entries in clipboard")
            item.setFlags(Qt.NoItemFlags)  # Not selectable
            self.entry_list.addItem(item)
            self.details_text.setPlainText("The insertion clipboard is empty.\n\n"
                                          "Add subgraphs from Organon, Ergasterion, or Agon.")
            return
        
        for entry in entries:
            # Create display text
            element_count = len(entry.subgraph_elements)
            time_ago = self._format_time_ago(entry.added_timestamp)
            display_text = f"{entry.name} ({element_count} elements) - {time_ago}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, entry.id)  # Store entry ID
            self.entry_list.addItem(item)
    
    def _on_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle selection change in list."""
        if not current or not current.data(Qt.UserRole):
            self.selected_entry = None
            self.select_btn.setEnabled(False)
            self.details_text.clear()
            self.elements_text.clear()
            return
        
        # Get entry
        entry_id = current.data(Qt.UserRole)
        entry = self.clipboard.get_entry(entry_id)
        
        if not entry:
            return
        
        self.selected_entry = entry
        self.select_btn.setEnabled(True)
        
        # Show details
        details = f"Name: {entry.name}\n"
        details += f"Added: {entry.added_timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        details += f"Elements: {len(entry.subgraph_elements)}\n"
        if entry.description:
            details += f"\nDescription:\n{entry.description}"
        
        self.details_text.setPlainText(details)
        
        # Show elements
        elements_display = "Elements:\n"
        for elem_id in sorted(str(e) for e in entry.subgraph_elements):
            elements_display += f"  • {elem_id}\n"
        
        self.elements_text.setPlainText(elements_display)
    
    def _on_select_clicked(self):
        """Handle selection confirmation."""
        if self.selected_entry:
            self.entry_selected.emit(self.selected_entry)
            self.accept()
    
    def _remove_selected(self):
        """Remove the selected entry from clipboard."""
        current = self.entry_list.currentItem()
        if not current or not current.data(Qt.UserRole):
            return
        
        entry_id = current.data(Qt.UserRole)
        entry = self.clipboard.get_entry(entry_id)
        
        if not entry:
            return
        
        # Confirm removal
        reply = QMessageBox.question(
            self,
            "Remove Entry",
            f"Remove '{entry.name}' from clipboard?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.clipboard.remove_entry(entry_id)
            self._load_entries()
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format timestamp as relative time."""
        now = datetime.now()
        delta = now - timestamp
        
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "just now"
    
    def get_selected_entry(self) -> Optional[ClipboardEntry]:
        """Get the selected entry (if dialog was accepted)."""
        return self.selected_entry


# Standalone test
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create test clipboard with dummy data
    clipboard = InsertionClipboard()
    
    dialog = InsertionClipboardDialog(clipboard)
    
    def on_selected(entry):
        print(f"Selected: {entry.name}")
    
    dialog.entry_selected.connect(on_selected)
    dialog.exec()
    
    sys.exit(0)
