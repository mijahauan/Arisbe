"""
Corpus Panel for Organon - provides browsing interface for graph collections.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QLineEdit, QSplitter, QTextEdit, QGroupBox,
    QListWidget, QListWidgetItem, QMessageBox
)


class CorpusPanel(QWidget):
    """
    Panel for browsing and managing graph corpus.
    Provides tree view of collections and individual graphs.
    """
    
    # Signals for Organon main_window compatibility
    entry_selected = Signal(dict)  # entry data
    refresh_requested = Signal()
    new_requested = Signal()
    
    # Signals for launching Ergasterion with different handoff types  
    new_graph_requested = Signal(dict)  # metadata
    edit_graph_requested = Signal(str)  # graph_id
    practice_graph_requested = Signal(str)  # graph_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.corpus_path = "corpus"
        self.index_path = "corpus/index.json"
        self.current_graphs = {}
        
        self._setup_ui()
        self._load_corpus()
    
    def _setup_ui(self):
        """Set up the corpus browsing interface."""
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._filter_graphs)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel: Graph tree
        left_panel = QGroupBox("Corpus Browser")
        left_layout = QVBoxLayout(left_panel)
        
        self.graph_tree = QTreeWidget()
        self.graph_tree.setHeaderLabels(["Title", "Type", "Status"])
        self.graph_tree.itemClicked.connect(self._on_graph_selected)
        left_layout.addWidget(self.graph_tree)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.new_button = QPushButton("New Graph")
        self.new_button.clicked.connect(self._new_graph)
        button_layout.addWidget(self.new_button)
        
        self.edit_button = QPushButton("Edit Diagram")
        self.edit_button.clicked.connect(self._edit_graph)
        self.edit_button.setEnabled(False)
        button_layout.addWidget(self.edit_button)
        
        self.practice_button = QPushButton("Practice Mode")
        self.practice_button.clicked.connect(self._practice_graph)
        self.practice_button.setEnabled(False)
        button_layout.addWidget(self.practice_button)
        
        left_layout.addLayout(button_layout)
        splitter.addWidget(left_panel)
        
        # Right panel: Graph details
        right_panel = QGroupBox("Graph Details")
        right_layout = QVBoxLayout(right_panel)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        right_layout.addWidget(self.details_text)
        
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 300])
    
    def _load_corpus(self):
        """Load corpus from index.json file."""
        self.graph_tree.clear()
        self.current_graphs.clear()
        
        import os
        if not os.path.exists(self.index_path):
            print(f"Corpus index not found at {self.index_path}")
            return
        
        try:
            # Simple direct file read without any complex operations
            with open(self.index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            index_data = json.loads(content)
            entries = index_data.get("entries", [])
            
            for entry in entries:
                graph_id = entry.get("id")
                if not graph_id:
                    continue
                
                # Store entry data for later use
                self.current_graphs[graph_id] = entry
                
                # Add to tree
                item = QTreeWidgetItem()
                item.setText(0, entry.get("title", graph_id))
                item.setText(1, self._get_graph_type_from_entry(entry))
                item.setText(2, self._get_graph_status_from_entry(entry))
                item.setData(0, Qt.UserRole, graph_id)
                
                self.graph_tree.addTopLevelItem(item)
                
        except Exception as e:
            print(f"Failed to load corpus index: {e}")
    
    def _get_graph_type_from_entry(self, entry: Dict[str, Any]) -> str:
        """Determine graph type from index entry."""
        has_diagram = entry.get("has_egdf", False)
        has_exports = entry.get("has_exports", False)
        
        # Assume logic exists if the entry is in the index
        # (since graphs without logic wouldn't be meaningful)
        has_logic = True
        
        if has_logic and has_diagram:
            return "Complete"
        elif has_logic:
            return "Logic Only"
        elif has_diagram:
            return "Diagram Only"
        else:
            return "Draft"
    
    def _get_graph_status_from_entry(self, entry: Dict[str, Any]) -> str:
        """Determine graph status from index entry."""
        category = entry.get("category")
        if category == "peirce":
            return "Historical"
        elif category:
            return category.title()
        else:
            return "Active"
    
    def _get_graph_type(self, graph_data: Dict[str, Any]) -> str:
        """Determine graph type from data."""
        has_egi = "egi_ref" in graph_data
        has_egdf = "layout" in graph_data
        
        if has_egi and has_egdf:
            return "Complete"
        elif has_egi:
            return "Logic Only"
        else:
            return "Empty"
    
    def _get_graph_status(self, graph_data: Dict[str, Any]) -> str:
        """Determine graph status."""
        # Could be enhanced with more sophisticated status tracking
        return "Ready"
    
    def _filter_graphs(self, text: str):
        """Filter graphs based on search text."""
        for i in range(self.graph_tree.topLevelItemCount()):
            item = self.graph_tree.topLevelItem(i)
            title = item.text(0).lower()
            visible = text.lower() in title if text else True
            item.setHidden(not visible)
    
    def _on_graph_selected(self, item: QTreeWidgetItem):
        """Handle graph selection."""
        graph_id = item.data(0, Qt.UserRole)
        if graph_id in self.current_graphs:
            graph_data = self.current_graphs[graph_id]
            self._show_graph_details(graph_data)
            
            # Enable appropriate buttons
            graph_type = self._get_graph_type(graph_data)
            self.edit_button.setEnabled(True)
            self.practice_button.setEnabled(graph_type == "Complete")
            
            # Emit entry_selected signal for Organon main_window compatibility
            entry_data = {
                "id": graph_id,
                "path": graph_data.get("path", f"corpus/graphs/{graph_id}"),  
                "title": graph_data.get("title", graph_id)
            }
            self.entry_selected.emit(entry_data)
    
    def _show_graph_details(self, graph_data: Dict[str, Any]):
        """Show detailed information about selected graph."""
        details = []
        
        # Basic metadata
        metadata = graph_data.get("metadata", {})
        details.append(f"Title: {metadata.get('title', 'Untitled')}")
        details.append(f"Created: {metadata.get('created', 'Unknown')}")
        details.append(f"Type: {self._get_graph_type(graph_data)}")
        details.append("")
        
        # EGI information
        if "egi_ref" in graph_data:
            egi = graph_data["egi_ref"].get("inline", {})
            details.append("Logical Structure (EGI):")
            details.append(f"  Vertices: {len(egi.get('V', []))}")
            details.append(f"  Edges: {len(egi.get('E', []))}")
            details.append(f"  Cuts: {len(egi.get('Cut', []))}")
            details.append("")
        
        # Layout information
        if "layout" in graph_data:
            layout = graph_data["layout"]
            details.append("Spatial Layout (EGDF):")
            details.append(f"  Predicates: {len(layout.get('predicates', {}))}")
            details.append(f"  Vertices: {len(layout.get('vertices', {}))}")
            details.append("")
        
        self.details_text.setPlainText("\n".join(details))
    
    def _new_graph(self):
        """Request creation of new graph."""
        import uuid
        graph_id = f"graph_{uuid.uuid4().hex[:8]}"
        metadata = {
            "title": f"New Graph {len(self.current_graphs) + 1}",
            "created": "now",
            "source": "organon_new"
        }
        self.new_graph_requested.emit({"id": graph_id, "metadata": metadata})
        # Also emit new_requested for Organon main_window compatibility
        self.new_requested.emit()
    
    def _edit_graph(self):
        """Request editing of selected graph."""
        current_item = self.graph_tree.currentItem()
        if current_item:
            graph_id = current_item.data(0, Qt.UserRole)
            self.edit_graph_requested.emit(graph_id)
    
    def _practice_graph(self):
        """Request practice mode for selected graph."""
        current_item = self.graph_tree.currentItem()
        if current_item:
            graph_id = current_item.data(0, Qt.UserRole)
            graph_data = self.current_graphs.get(graph_id)
            if graph_data and self._get_graph_type(graph_data) == "Complete":
                self.practice_graph_requested.emit(graph_id)
            else:
                QMessageBox.warning(self, "Practice Mode", 
                                  "Practice mode requires a complete graph with both logic and layout.")
    
    def get_graph_data(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Get graph data by ID."""
        return self.current_graphs.get(graph_id)
    
    def refresh_corpus(self):
        """Refresh the corpus display."""
        self._load_corpus()
    
    def add_graph_to_index(self, graph_id: str, title: str, path: str):
        """Add a new graph entry to the corpus index."""
        try:
            # Load current index
            import os
            if os.path.exists(self.index_path):
                with open(self.index_path, 'r') as f:
                    index_data = json.load(f)
            else:
                index_data = {"name": "Arisbe Corpus", "version": "0.1", "entries": []}
            
            # Check if entry already exists
            entries = index_data.get("entries", [])
            existing_entry = next((e for e in entries if e.get("id") == graph_id), None)
            
            if existing_entry:
                # Update existing entry
                existing_entry["title"] = title
                existing_entry["path"] = path
                existing_entry["updated"] = datetime.now().isoformat()
            else:
                # Add new entry
                from datetime import datetime
                new_entry = {
                    "id": graph_id,
                    "title": title,
                    "category": None,
                    "tags": [],
                    "path": path,
                    "updated": datetime.now().isoformat(),
                    "has_egdf": False,
                    "has_exports": False
                }
                entries.append(new_entry)
            
            # Save updated index
            with open(self.index_path, 'w') as f:
                json.dump(index_data, f, indent=2)
            
            # Refresh display without emitting signals to avoid recursion
            self._load_corpus()
            
        except Exception as e:
            print(f"Failed to update corpus index: {e}")
    
    def populate(self, entries: List[Dict[str, Any]]):
        """Populate corpus panel with entries (for Organon main_window compatibility)."""
        self.graph_tree.clear()
        self.current_graphs.clear()
        
        for entry in entries:
            graph_id = entry.get("id", "unknown")
            self.current_graphs[graph_id] = entry
            
            # Add to tree
            item = QTreeWidgetItem()
            item.setText(0, entry.get("title", graph_id))
            item.setText(1, "Complete" if entry.get("has_egdf") else "Logic Only")
            item.setText(2, "Ready")
            item.setData(0, Qt.UserRole, graph_id)
            
            self.graph_tree.addTopLevelItem(item)
