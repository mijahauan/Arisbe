"""
Metadata Panel - Display entity properties and statistics.

Shows both synchronic (current state) and diachronic (history) information.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from universe_of_discourse import UniverseOfDiscourse


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
    - Visual style selector
    """
    
    # Signals
    style_changed = Signal(str)  # Emits new style name when user changes style
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._current_uod: Optional[UniverseOfDiscourse] = None
    
    def _setup_ui(self):
        """Create the metadata panel UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("📋 Universe of Discourse Metadata")
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
        
        # Visual Style Section
        self.style_group = self._create_style_group()
        container_layout.addWidget(self.style_group)
        
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
    
    def _create_style_group(self) -> QGroupBox:
        """Create visual style selector group."""
        group = QGroupBox("🎨 Visual Style")
        layout = QVBoxLayout(group)
        layout.setSpacing(5)
        
        # Style selector combo box
        self.style_combo = QComboBox()
        self.style_combo.setToolTip("Select rendering style for this diagram")
        
        # Populate with available styles
        try:
            from style_loader import StyleLoader
            loader = StyleLoader()
            available_styles = loader.list_available_styles()
            
            # Add styles with friendly display names
            for style_file in available_styles:
                # Remove .json extension if present
                style_name = style_file.replace('.json', '')
                
                # Create friendly display name
                if 'dau' in style_name.lower():
                    display_name = f"📐 {style_name} (Mathematical)"
                elif 'peirce' in style_name.lower():
                    display_name = f"✍️ {style_name} (Peirce)"
                elif 'sowa' in style_name.lower():
                    display_name = f"🔷 {style_name} (Sowa CG)"
                else:
                    display_name = style_name
                
                self.style_combo.addItem(display_name, style_name)
        except Exception as e:
            # Fallback if style loader fails
            self.style_combo.addItem("dau-compliant@1.0", "dau-compliant@1.0")
            self.style_combo.addItem("peirce-authentic@1.0", "peirce-authentic@1.0")
            self.style_combo.addItem("sowa-compliant@1.0", "sowa-compliant@1.0")
            print(f"Warning: Could not load styles dynamically: {e}")
        
        # Connect signal
        self.style_combo.currentIndexChanged.connect(self._on_style_combo_changed)
        
        layout.addWidget(self.style_combo)
        
        # Add help text
        help_label = QLabel("Changes how the diagram is rendered")
        help_label.setStyleSheet("color: #888; font-size: 9px; font-style: italic;")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
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
    
    def update_metadata(self, uod: UniverseOfDiscourse):
        """
        Update display with UoD metadata.
        
        Args:
            uod: The Universe of Discourse to display
        """
        self._current_uod = uod
        metadata = uod.metadata
        
        # Basic Info
        self.name_label.setText(metadata.name or "Untitled")
        self.description_label.setText(metadata.description or "No description")
        
        # Type & Category
        uod_type_text = self._format_uod_type(uod)
        self.type_label.setText(uod_type_text)
        
        category_text = metadata.category.value.replace("_", " ").title()
        self.category_label.setText(category_text)
        
        # Tags
        if metadata.tags:
            tags_text = ", ".join(sorted(metadata.tags))
            self.tags_label.setText(tags_text)
        else:
            self.tags_label.setText("(none)")
        
        # History (only for historical UoDs)
        if uod.is_historical:
            self.history_group.setVisible(True)
            self.history_group.setHidden(False)  # Explicitly unhide
            self.states_label.setText(str(metadata.total_states))
            self.transformations_label.setText(str(metadata.total_transformations))
            
            # Find current state number
            if uod.history:
                current_num = 1
                if metadata.current_state_id:
                    for i, state_id in enumerate(uod.history.state_sequence):
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
        self._update_complexity_metrics(uod.current_egi)
        
        # Set current style in combo box
        self._set_current_style(metadata.style_name)
    
    def _format_uod_type(self, uod: UniverseOfDiscourse) -> str:
        """Format UoD type with icon and text."""
        if uod.is_static:
            return "📚 Static (Literature Import)"
        elif uod.is_dynamic and uod.is_historical:
            return "🔬 Dynamic (Active Reasoning with History)"
        elif uod.is_dynamic:
            return "🔬 Dynamic (Active Reasoning)"
        else:
            return "📄 Standalone"
    
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
    
    def _on_style_combo_changed(self, index: int):
        """Handle style selection change."""
        if index < 0:
            return
        
        # Get actual style name from combo box data
        new_style = self.style_combo.itemData(index)
        
        if new_style and self._current_uod:
            # Emit signal (organon_mode will handle reload)
            self.style_changed.emit(new_style)
    
    def _set_current_style(self, style_name: str):
        """Set the current style in the combo box without triggering signal."""
        # Block signals temporarily to avoid triggering reload
        self.style_combo.blockSignals(True)
        
        # Find matching style in combo box
        for i in range(self.style_combo.count()):
            if self.style_combo.itemData(i) == style_name:
                self.style_combo.setCurrentIndex(i)
                break
        
        # Re-enable signals
        self.style_combo.blockSignals(False)
    
    def clear(self):
        """Clear all metadata displays."""
        self._current_uod = None
        
        self.name_label.setText("(no UoD loaded)")
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
        
        # Reset style combo to default
        self.style_combo.blockSignals(True)
        self.style_combo.setCurrentIndex(0)  # Default to first style
        self.style_combo.blockSignals(False)
        
        self.history_group.setVisible(False)
