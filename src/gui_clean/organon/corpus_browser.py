"""
Corpus Browser Widget - Navigate and select graph entities from corpus.

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

from entity_storage import EntityStorageManager
from graph_entity import EntityCategory, EntityMetadata


class CorpusBrowserWidget(QWidget):
    """
    Corpus browser for selecting graph entities.
    
    Features:
    - List all entities in corpus
    - Filter by category
    - Search by name/description
    - Show entity metadata
    - Signal when entity selected
    """
    
    # Signal emitted when user selects an entity
    entity_selected = Signal(str)  # entity_name
    
    def __init__(self, corpus_path: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.storage = EntityStorageManager(corpus_path)
        self._current_entities: list[str] = []
        
        self._setup_ui()
        self._refresh_list()
    
    def _setup_ui(self):
        """Create the browser UI."""
        layout = QVBoxLayout(self)
        
        # Top controls
        controls = QHBoxLayout()
        
        # Category filter
        controls.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("All", None)
        for category in EntityCategory:
            display_name = category.value.replace("_", " ").title()
            self.category_combo.addItem(display_name, category)
        self.category_combo.currentIndexChanged.connect(self._on_filter_changed)
        controls.addWidget(self.category_combo)
        
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
        """Refresh the entity list."""
        # Get current filter
        category = self.category_combo.currentData()
        
        # Load entities
        self._current_entities = self.storage.list_entities(category=category)
        
        # Apply search filter
        search_term = self.search_box.text().lower()
        if search_term:
            self._current_entities = [
                name for name in self._current_entities
                if search_term in name.lower()
            ]
        
        # Update list
        self.entity_list.clear()
        for entity_name in self._current_entities:
            # Load metadata (fast, cached)
            try:
                metadata = self.storage.load_entity_metadata(entity_name)
                
                # Create list item
                item = QListWidgetItem(entity_name)
                
                # Add icon based on type
                icon = "📄" if metadata.entity_type.value == "standalone" else "📚"
                item.setText(f"{icon} {entity_name}")
                
                # Store metadata for later
                item.setData(Qt.UserRole, metadata)
                
                self.entity_list.addItem(item)
            except Exception as e:
                # Skip entities that fail to load metadata
                print(f"Warning: Failed to load metadata for {entity_name}: {e}")
                continue
    
    def _on_filter_changed(self):
        """Handle category filter change."""
        self._refresh_list()
    
    def _on_search_changed(self):
        """Handle search text change."""
        self._refresh_list()
    
    def _on_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle entity selection change."""
        if current is None:
            self.info_text.clear()
            self.load_btn.setEnabled(False)
            return
        
        # Get metadata
        metadata: EntityMetadata = current.data(Qt.UserRole)
        
        # Display info
        info = self._format_entity_info(metadata)
        self.info_text.setHtml(info)
        
        self.load_btn.setEnabled(True)
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click (load immediately)."""
        metadata: EntityMetadata = item.data(Qt.UserRole)
        self.entity_selected.emit(metadata.name)
    
    def _on_load_clicked(self):
        """Handle load button click."""
        current = self.entity_list.currentItem()
        if current:
            metadata: EntityMetadata = current.data(Qt.UserRole)
            self.entity_selected.emit(metadata.name)
    
    def _format_entity_info(self, metadata: EntityMetadata) -> str:
        """Format entity metadata as HTML."""
        type_label = "Standalone" if metadata.entity_type.value == "standalone" else "Historical"
        category_label = metadata.category.value.replace("_", " ").title()
        
        html = f"""
        <p><b>Name:</b> {metadata.name}</p>
        <p><b>Type:</b> {type_label}</p>
        <p><b>Category:</b> {category_label}</p>
        """
        
        if metadata.description:
            html += f"<p><b>Description:</b> {metadata.description}</p>"
        
        if metadata.entity_type.value == "historical":
            html += f"<p><b>States:</b> {metadata.total_states} | <b>Transformations:</b> {metadata.total_transformations}</p>"
        
        if metadata.source_citation:
            html += f"<p><b>Source:</b> {metadata.source_citation}</p>"
        
        if metadata.tags:
            tags = ", ".join(sorted(metadata.tags))
            html += f"<p><b>Tags:</b> {tags}</p>"
        
        return html
    
    def get_selected_entity_name(self) -> Optional[str]:
        """Get currently selected entity name."""
        current = self.entity_list.currentItem()
        if current:
            metadata: EntityMetadata = current.data(Qt.UserRole)
            return metadata.name
        return None
