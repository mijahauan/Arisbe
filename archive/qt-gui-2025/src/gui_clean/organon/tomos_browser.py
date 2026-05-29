"""
Tomos Browser Widget - Navigate and select graph entities from tomos.

Displays available entities with metadata, category filtering, and search.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tomos_service import TomosService
from universe_of_discourse import UoDCategory, UoDMetadata, UniverseOfDiscourse


class TomosBrowserWidget(QWidget):
    """
    Tomos browser for selecting Universes of Discourse.
    
    Features:
    - List all UoDs in tomos
    - Filter by category (static/dynamic)
    - Search by name/description
    - Show UoD metadata
    - Signal when UoD selected
    """
    
    # Signal emitted when user selects a UoD
    entity_selected = Signal(str)  # uod_id
    
    def __init__(self, corpus_path: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.tomos = TomosService(corpus_path)
        self._current_uods: list[dict] = []
        
        self._setup_ui()
        self._refresh_list()
    
    def _setup_ui(self):
        """Create the browser UI."""
        layout = QVBoxLayout(self)
        
        # Top controls
        controls = QHBoxLayout()
        
        # Type filter
        controls.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("All", None)
        self.type_combo.addItem("📚 Static (Literature)", "static")
        self.type_combo.addItem("🔬 Dynamic (Reasoning)", "dynamic")
        self.type_combo.currentIndexChanged.connect(self._on_filter_changed)
        controls.addWidget(self.type_combo)
        
        # Search box
        controls.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search entities...")
        self.search_box.textChanged.connect(self._on_search_changed)
        controls.addWidget(self.search_box, stretch=1)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh list")
        self.refresh_btn.clicked.connect(self._refresh_list)
        controls.addWidget(self.refresh_btn)
        
        layout.addLayout(controls)
        
        # Entity list
        self.entity_list = QListWidget()
        self.entity_list.setAlternatingRowColors(True)
        self.entity_list.currentItemChanged.connect(self._on_selection_changed)
        self.entity_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.entity_list, stretch=2)
        
        # Entity info panel
        info_label = QLabel("Entity Information:")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(120)
        layout.addWidget(self.info_text)
        
        # Load button
        self.load_btn = QPushButton("📂 Load Selected Entity")
        self.load_btn.clicked.connect(self._on_load_clicked)
        self.load_btn.setEnabled(False)
        layout.addWidget(self.load_btn)
    
    def _refresh_list(self):
        """Refresh the UoD list."""
        # Get current filter
        type_filter = self.type_combo.currentData()
        
        # Build filter kwargs
        kwargs = {}
        if type_filter == "static":
            kwargs["is_static"] = True
        elif type_filter == "dynamic":
            kwargs["is_dynamic"] = True
        
        # Load UoDs from index (fast, no full loading)
        self._current_uods = self.tomos.list_uods(**kwargs)
        
        # Apply search filter
        search_term = self.search_box.text().lower()
        if search_term:
            self._current_uods = [
                uod for uod in self._current_uods
                if search_term in uod.get("name", "").lower()
            ]
        
        # Update list
        self.entity_list.clear()
        for uod_metadata in self._current_uods:
            try:
                uod_id = uod_metadata.get("uod_id")
                name = uod_metadata.get("name", uod_id)
                
                # Create list item
                item = QListWidgetItem(name)
                
                # Add icon based on type
                is_static = uod_metadata.get("is_static", False)
                icon = "📚" if is_static else "🔬"
                item.setText(f"{icon} {name}")
                
                # Store full metadata for later
                item.setData(Qt.UserRole, uod_metadata)
                
                self.entity_list.addItem(item)
            except Exception as e:
                print(f"Warning: Failed to display UoD: {e}")
                continue
    
    def _on_filter_changed(self):
        """Handle category filter change."""
        self._refresh_list()
    
    def _on_search_changed(self):
        """Handle search text change."""
        self._refresh_list()
    
    def _on_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle UoD selection change."""
        if current is None:
            self.info_text.clear()
            self.load_btn.setEnabled(False)
            return
        
        # Get metadata dict
        metadata: dict = current.data(Qt.UserRole)
        
        # Display info
        info = self._format_uod_info(metadata)
        self.info_text.setHtml(info)
        
        self.load_btn.setEnabled(True)
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click (load immediately)."""
        metadata: dict = item.data(Qt.UserRole)
        self.entity_selected.emit(metadata.get("uod_id"))
    
    def _on_load_clicked(self):
        """Handle load button click."""
        current = self.entity_list.currentItem()
        if current:
            metadata: dict = current.data(Qt.UserRole)
            self.entity_selected.emit(metadata.get("uod_id"))
    
    def _format_uod_info(self, metadata: dict) -> str:
        """Format UoD metadata as HTML."""
        name = metadata.get("name", "Unnamed")
        is_static = metadata.get("is_static", False)
        is_dynamic = metadata.get("is_dynamic", False)
        category = metadata.get("category", "unknown").replace("_", " ").title()
        
        type_label = "Static (Literature)" if is_static else "Dynamic (Reasoning)"
        
        html = f"""
        <p><b>Name:</b> {name}</p>
        <p><b>Type:</b> {type_label}</p>
        <p><b>Category:</b> {category}</p>
        """
        
        if is_dynamic:
            total_states = metadata.get("total_states", 0)
            total_transformations = metadata.get("total_transformations", 0)
            html += f"<p><b>States:</b> {total_states} | <b>Transformations:</b> {total_transformations}</p>"
        
        if metadata.get("tags"):
            tags = ", ".join(sorted(metadata.get("tags", [])))
            html += f"<p><b>Tags:</b> {tags}</p>"
        
        if metadata.get("authors"):
            authors = ", ".join(metadata.get("authors", []))
            html += f"<p><b>Authors:</b> {authors}</p>"
        
        return html
    
    def get_selected_uod_id(self) -> Optional[str]:
        """Get currently selected UoD ID."""
        current = self.entity_list.currentItem()
        if current:
            metadata: dict = current.data(Qt.UserRole)
            return metadata.get("uod_id")
        return None
