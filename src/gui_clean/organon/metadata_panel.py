"""
Metadata Panel - Display entity properties and statistics.

Shows both synchronic (current state) and diachronic (history) information.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from graph_entity import GraphEntity


class MetadataPanel(QWidget):
    """
    Display entity metadata and properties.
    
    Shows:
    - Entity name, description
    - Type (standalone vs historical)
    - Category and tags
    - Authors and citation
    - Created/modified timestamps
    - History statistics (if historical)
    - Complexity metrics
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._current_entity: Optional[GraphEntity] = None
    
    def _setup_ui(self):
        """Create the metadata panel UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("📋 Entity Metadata")
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        main_layout.addWidget(title)
        
        # Scrollable area for metadata
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Container for all metadata sections
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(10)
        
        # Basic Info Section
        self.basic_group = self._create_basic_info_group()
        container_layout.addWidget(self.basic_group)
        
        # Type & Category Section
        self.type_group = self._create_type_category_group()
        container_layout.addWidget(self.type_group)
        
        # History Section (only shown for historical entities)
        self.history_group = self._create_history_group()
        container_layout.addWidget(self.history_group)
        self.history_group.setVisible(False)  # Hidden by default
        
        # Timestamps Section
        self.timestamp_group = self._create_timestamp_group()
        container_layout.addWidget(self.timestamp_group)
        
        # Authorship Section
        self.authorship_group = self._create_authorship_group()
        container_layout.addWidget(self.authorship_group)
        
        # Complexity Section
        self.complexity_group = self._create_complexity_group()
        container_layout.addWidget(self.complexity_group)
        
        container_layout.addStretch()
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
    
    def _create_basic_info_group(self) -> QGroupBox:
        """Create basic information group."""
        group = QGroupBox("Basic Information")
        layout = QFormLayout(group)
        layout.setSpacing(5)
        
        self.name_label = QLabel()
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-weight: bold;")
        layout.addRow("Name:", self.name_label)
        
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #666;")
        layout.addRow("Description:", self.description_label)
        
        return group
    
    def _create_type_category_group(self) -> QGroupBox:
        """Create type and category group."""
        group = QGroupBox("Classification")
        layout = QFormLayout(group)
        layout.setSpacing(5)
        
        self.type_label = QLabel()
        layout.addRow("Type:", self.type_label)
        
        self.category_label = QLabel()
        layout.addRow("Category:", self.category_label)
        
        self.tags_label = QLabel()
        self.tags_label.setWordWrap(True)
        layout.addRow("Tags:", self.tags_label)
        
        return group
    
    def _create_history_group(self) -> QGroupBox:
        """Create history statistics group."""
        group = QGroupBox("Transformation History")
        layout = QFormLayout(group)
        layout.setSpacing(5)
        
        self.states_label = QLabel()
        layout.addRow("Total States:", self.states_label)
        
        self.transformations_label = QLabel()
        layout.addRow("Transformations:", self.transformations_label)
        
        self.current_state_label = QLabel()
        layout.addRow("Current State:", self.current_state_label)
        
        return group
    
    def _create_timestamp_group(self) -> QGroupBox:
        """Create timestamps group."""
        group = QGroupBox("Timestamps")
        layout = QFormLayout(group)
        layout.setSpacing(5)
        
        self.created_label = QLabel()
        layout.addRow("Created:", self.created_label)
        
        self.modified_label = QLabel()
        layout.addRow("Last Modified:", self.modified_label)
        
        return group
    
    def _create_authorship_group(self) -> QGroupBox:
        """Create authorship and citation group."""
        group = QGroupBox("Authorship")
        layout = QFormLayout(group)
        layout.setSpacing(5)
        
        self.authors_label = QLabel()
        self.authors_label.setWordWrap(True)
        layout.addRow("Authors:", self.authors_label)
        
        self.citation_label = QLabel()
        self.citation_label.setWordWrap(True)
        self.citation_label.setStyleSheet("font-style: italic; color: #555;")
        layout.addRow("Citation:", self.citation_label)
        
        return group
    
    def _create_complexity_group(self) -> QGroupBox:
        """Create complexity metrics group."""
        group = QGroupBox("Graph Complexity")
        layout = QFormLayout(group)
        layout.setSpacing(5)
        
        self.vertices_label = QLabel()
        layout.addRow("Vertices:", self.vertices_label)
        
        self.edges_label = QLabel()
        layout.addRow("Edges:", self.edges_label)
        
        self.cuts_label = QLabel()
        layout.addRow("Cuts:", self.cuts_label)
        
        self.depth_label = QLabel()
        layout.addRow("Max Depth:", self.depth_label)
        
        return group
    
    def update_metadata(self, entity: GraphEntity):
        """
        Update display with entity metadata.
        
        Args:
            entity: The graph entity to display
        """
        self._current_entity = entity
        metadata = entity.metadata
        
        # Basic Info
        self.name_label.setText(metadata.name or "Untitled")
        self.description_label.setText(metadata.description or "No description")
        
        # Type & Category
        entity_type_text = self._format_entity_type(entity)
        self.type_label.setText(entity_type_text)
        
        category_text = metadata.category.value.replace("_", " ").title()
        self.category_label.setText(category_text)
        
        # Tags
        if metadata.tags:
            tags_text = ", ".join(sorted(metadata.tags))
            self.tags_label.setText(tags_text)
        else:
            self.tags_label.setText("(none)")
        
        # History (only for historical entities)
        if entity.is_historical:
            self.history_group.setVisible(True)
            self.history_group.setHidden(False)  # Explicitly unhide
            self.states_label.setText(str(metadata.total_states))
            self.transformations_label.setText(str(metadata.total_transformations))
            
            # Find current state number
            if entity.history:
                current_num = 1
                if metadata.current_state_id:
                    for i, state_id in enumerate(entity.history.state_sequence):
                        if state_id == metadata.current_state_id:
                            current_num = i + 1
                            break
                self.current_state_label.setText(f"State {current_num} of {metadata.total_states}")
            else:
                self.current_state_label.setText("N/A")
        else:
            self.history_group.setVisible(False)
            self.history_group.setHidden(True)
        
        # Timestamps
        created_text = self._format_timestamp(metadata.created)
        self.created_label.setText(created_text)
        
        modified_text = self._format_timestamp(metadata.last_modified)
        self.modified_label.setText(modified_text)
        
        # Authorship
        if metadata.authors:
            authors_text = ", ".join(metadata.authors)
            self.authors_label.setText(authors_text)
        else:
            self.authors_label.setText("(anonymous)")
        
        if metadata.source_citation:
            self.citation_label.setText(metadata.source_citation)
        else:
            self.citation_label.setText("(none)")
        
        # Complexity Metrics
        self._update_complexity_metrics(entity.current_egi)
    
    def _format_entity_type(self, entity: GraphEntity) -> str:
        """Format entity type with icon and text."""
        if entity.is_historical:
            return "📜 Historical (Transformation Sequence)"
        else:
            return "📄 Standalone (Single State)"
    
    def _format_timestamp(self, dt: datetime) -> str:
        """Format timestamp for display."""
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def _update_complexity_metrics(self, egi):
        """Update complexity metrics from current EGI."""
        # Count elements
        num_vertices = len(egi.V)
        num_edges = len(egi.E)
        num_cuts = len(egi.Cut)
        
        self.vertices_label.setText(str(num_vertices))
        self.edges_label.setText(str(num_edges))
        self.cuts_label.setText(str(num_cuts))
        
        # Calculate max depth (nesting level)
        max_depth = self._calculate_max_depth(egi)
        self.depth_label.setText(str(max_depth))
    
    def _calculate_max_depth(self, egi) -> int:
        """
        Calculate maximum nesting depth of cuts.
        
        Args:
            egi: The EGI graph
            
        Returns:
            Maximum depth (0 = sheet only, 1 = one cut level, etc.)
        """
        if not egi.Cut:
            return 0
        
        # Use hierarchical index if available
        if egi.hierarchical_index:
            max_depth = 0
            for cut in egi.Cut:
                depth = egi.hierarchical_index.get_nesting_level(cut.id)
                max_depth = max(max_depth, depth)
            return max_depth
        
        # Fallback: Build parent-child relationships from area mapping
        # Find which area contains each cut
        cut_parent = {}
        for area_id, elements in egi.area.items():
            for element_id in elements:
                # Check if element is a cut
                if any(c.id == element_id for c in egi.Cut):
                    cut_parent[element_id] = area_id
        
        # Find root cuts (contained in sheet)
        root_cuts = []
        for cut in egi.Cut:
            parent = cut_parent.get(cut.id)
            if parent == egi.sheet:
                root_cuts.append(cut.id)
        
        if not root_cuts:
            return 0
        
        # Calculate depth recursively
        def depth_from(cut_id: str, current_depth: int) -> int:
            # Find children of this cut
            children = []
            for other_cut in egi.Cut:
                parent = cut_parent.get(other_cut.id)
                if parent == cut_id:
                    children.append(other_cut.id)
            
            if not children:
                return current_depth
            return max(depth_from(child, current_depth + 1) for child in children)
        
        return max(depth_from(root, 1) for root in root_cuts)
    
    def clear(self):
        """Clear all metadata displays."""
        self._current_entity = None
        
        self.name_label.setText("(no entity loaded)")
        self.description_label.setText("")
        self.type_label.setText("")
        self.category_label.setText("")
        self.tags_label.setText("")
        self.states_label.setText("")
        self.transformations_label.setText("")
        self.current_state_label.setText("")
        self.created_label.setText("")
        self.modified_label.setText("")
        self.authors_label.setText("")
        self.citation_label.setText("")
        self.vertices_label.setText("")
        self.edges_label.setText("")
        self.cuts_label.setText("")
        self.depth_label.setText("")
        
        self.history_group.setVisible(False)
