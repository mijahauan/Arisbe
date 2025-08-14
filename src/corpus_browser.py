#!/usr/bin/env python3
"""
Corpus Browser - Educational EG Example Explorer

A Qt component for browsing and loading examples from the Arisbe corpus.
Provides educational progression from simple to complex EG structures.

Features:
- Browse by category (Peirce, scholars, canonical, etc.)
- Filter by logical pattern (implication, quantification, etc.)
- Rich metadata display (source, description, complexity)
- One-click loading into canvas via canonical EGDF pipeline
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QPushButton, QLabel, QGroupBox, QSplitter, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


@dataclass
class CorpusExample:
    """Metadata for a corpus example."""
    id: str
    title: str
    description: str
    category: str
    logical_pattern: str
    source: Dict[str, Any]
    egif_path: Optional[Path] = None
    json_path: Optional[Path] = None


class CorpusBrowser(QWidget):
    """
    Corpus browser widget for exploring EG examples.
    
    Provides educational browsing of the corpus with rich metadata
    and one-click loading into the diagram canvas.
    """
    
    # Signal emitted when user wants to load an example
    example_selected = Signal(str, str)  # example_name, EGIF content
    
    def __init__(self, corpus_path: str = "corpus/corpus", parent=None):
        super().__init__(parent)
        
        self.corpus_path = Path(corpus_path)
        self.examples: Dict[str, CorpusExample] = {}
        
        self._setup_ui()
        self._load_corpus()
    
    def _setup_ui(self):
        """Setup the corpus browser UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📚 Existential Graphs Corpus")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(header)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Category filter
        filter_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All", "peirce", "scholars", "canonical", "alpha", "beta"])
        self.category_filter.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.category_filter)
        
        # Pattern filter
        filter_layout.addWidget(QLabel("Pattern:"))
        self.pattern_filter = QComboBox()
        self.pattern_filter.addItems(["All", "implication", "quantification", "disjunction", "ligature"])
        self.pattern_filter.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.pattern_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Main content splitter - VERTICAL to put Examples above Example Details
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Top: Example tree
        tree_group = QGroupBox("Examples")
        tree_layout = QVBoxLayout(tree_group)
        
        self.example_tree = QTreeWidget()
        self.example_tree.setHeaderLabels(["Title", "Pattern", "Source"])
        self.example_tree.itemSelectionChanged.connect(self._on_selection_changed)
        tree_layout.addWidget(self.example_tree)
        
        splitter.addWidget(tree_group)
        
        # Bottom: Example details (consolidated EGIF panel)
        details_group = QGroupBox("Example Details")
        details_layout = QVBoxLayout(details_group)
        
        # Metadata display
        self.metadata_display = QTextEdit()
        self.metadata_display.setReadOnly(True)
        self.metadata_display.setMaximumHeight(120)
        details_layout.addWidget(self.metadata_display)
        
        # EGIF preview (consolidated - no separate EGIF Source panel needed)
        egif_label = QLabel("EGIF Source:")
        egif_label.setFont(QFont("Arial", 10, QFont.Bold))
        details_layout.addWidget(egif_label)
        
        self.egif_preview = QTextEdit()
        self.egif_preview.setReadOnly(True)
        self.egif_preview.setFont(QFont("Courier", 10))
        self.egif_preview.setMaximumHeight(100)
        details_layout.addWidget(self.egif_preview)
        
        splitter.addWidget(details_group)
        
        # Set splitter proportions - Examples on top, Details on bottom
        splitter.setSizes([300, 200])
    
    def _load_corpus(self):
        """Load corpus examples from the filesystem."""
        try:
            # Load corpus index if available
            index_path = self.corpus_path / "corpus_index.json"
            if index_path.exists():
                self._load_from_index(index_path)
            else:
                self._scan_corpus_directory()
            
            self._populate_tree()
            print(f"✓ Loaded {len(self.examples)} corpus examples")
            
        except Exception as e:
            print(f"❌ Failed to load corpus: {e}")
    
    def _load_from_index(self, index_path: Path):
        """Load examples from corpus index file."""
        with open(index_path, 'r') as f:
            index_data = json.load(f)
        
        for example_data in index_data.get('examples', []):
            example_id = example_data['id']
            
            # Find corresponding files
            egif_path = self._find_example_file(example_id, '.egif')
            json_path = self._find_example_file(example_id, '.json')
            
            if egif_path:
                # Handle source field - can be string or dict
                source_data = example_data.get('source', {})
                if isinstance(source_data, str):
                    source_data = {'reference': source_data}
                
                example = CorpusExample(
                    id=example_id,
                    title=example_data.get('title', example_id),
                    description=example_data.get('description', ''),
                    category=example_data.get('category', 'unknown'),
                    logical_pattern=example_data.get('logical_pattern', 'unknown'),
                    source=source_data,
                    egif_path=egif_path,
                    json_path=json_path
                )
                self.examples[example_id] = example
    
    def _scan_corpus_directory(self):
        """Scan corpus directory for examples."""
        for category_dir in self.corpus_path.iterdir():
            if category_dir.is_dir() and category_dir.name != '__pycache__':
                self._scan_category_directory(category_dir)
    
    def _scan_category_directory(self, category_dir: Path):
        """Scan a category directory for examples."""
        category = category_dir.name
        
        # Find all .egif files
        for egif_file in category_dir.glob('*.egif'):
            example_id = egif_file.stem
            json_file = egif_file.with_suffix('.json')
            
            # Load metadata if available
            metadata = {}
            if json_file.exists():
                try:
                    with open(json_file, 'r') as f:
                        metadata = json.load(f)
                except Exception as e:
                    print(f"⚠ Failed to load metadata for {example_id}: {e}")
            
            # Handle source field - can be string or dict
            source_data = metadata.get('source', {})
            if isinstance(source_data, str):
                source_data = {'reference': source_data}
            
            example = CorpusExample(
                id=example_id,
                title=metadata.get('title', example_id),
                description=metadata.get('description', ''),
                category=category,
                logical_pattern=metadata.get('logical_pattern', 'unknown'),
                source=source_data,
                egif_path=egif_file,
                json_path=json_file if json_file.exists() else None
            )
            self.examples[example_id] = example
    
    def _find_example_file(self, example_id: str, extension: str) -> Optional[Path]:
        """Find example file with given extension."""
        for category_dir in self.corpus_path.iterdir():
            if category_dir.is_dir():
                file_path = category_dir / f"{example_id}{extension}"
                if file_path.exists():
                    return file_path
        return None
    
    def _populate_tree(self):
        """Populate the example tree widget."""
        self.example_tree.clear()
        
        # Group by category
        category_items = {}
        
        for example in self.examples.values():
            # Get or create category item
            if example.category not in category_items:
                category_item = QTreeWidgetItem([example.category.title(), "", ""])
                category_item.setFont(0, QFont("Arial", 10, QFont.Bold))
                self.example_tree.addTopLevelItem(category_item)
                category_items[example.category] = category_item
            
            # Create example item
            source_text = ""
            if example.source:
                author = example.source.get('author', '')
                year = example.source.get('year', '')
                if author and year:
                    source_text = f"{author} ({year})"
                elif author:
                    source_text = author
            
            example_item = QTreeWidgetItem([
                example.title,
                example.logical_pattern,
                source_text
            ])
            example_item.setData(0, Qt.UserRole, example.id)
            category_items[example.category].addChild(example_item)
        
        # Expand all categories
        self.example_tree.expandAll()
    
    def _apply_filters(self):
        """Apply category and pattern filters."""
        category_filter = self.category_filter.currentText()
        pattern_filter = self.pattern_filter.currentText()
        
        # Hide/show items based on filters
        for i in range(self.example_tree.topLevelItemCount()):
            category_item = self.example_tree.topLevelItem(i)
            category_name = category_item.text(0).lower()
            
            # Check category filter
            category_visible = (category_filter == "All" or 
                              category_filter.lower() == category_name)
            
            # Check children for pattern filter
            children_visible = 0
            for j in range(category_item.childCount()):
                child_item = category_item.child(j)
                pattern = child_item.text(1)
                
                pattern_visible = (pattern_filter == "All" or 
                                 pattern_filter.lower() == pattern.lower())
                
                child_visible = category_visible and pattern_visible
                child_item.setHidden(not child_visible)
                
                if child_visible:
                    children_visible += 1
            
            # Hide category if no visible children
            category_item.setHidden(children_visible == 0)
    
    def _on_selection_changed(self):
        """Handle example selection change."""
        selected_items = self.example_tree.selectedItems()
        
        if selected_items:
            item = selected_items[0]
            example_id = item.data(0, Qt.UserRole)
            
            if example_id and example_id in self.examples:
                self._display_example_details(self.examples[example_id])

            else:
                self._clear_details()
    
    def _display_example_details(self, example: CorpusExample):
        """Display details for the selected example."""
        # Format metadata
        metadata_text = f"<h3>{example.title}</h3>\n"
        metadata_text += f"<b>Category:</b> {example.category}<br>\n"
        metadata_text += f"<b>Pattern:</b> {example.logical_pattern}<br>\n"
        
        if example.source:
            metadata_text += "<b>Source:</b> "
            source_parts = []
            if 'author' in example.source:
                source_parts.append(example.source['author'])
            if 'work' in example.source:
                source_parts.append(example.source['work'])
            if 'year' in example.source:
                source_parts.append(f"({example.source['year']})")
            metadata_text += " ".join(source_parts) + "<br>\n"
        
        metadata_text += f"<br><b>Description:</b><br>{example.description}"
        
        self.metadata_display.setHtml(metadata_text)
        
        # Load and display EGIF
        if example.egif_path and example.egif_path.exists():
            try:
                with open(example.egif_path, 'r') as f:
                    egif_content = f.read()
                self.egif_preview.setPlainText(egif_content)
                
                # CRITICAL FIX: Emit the example_selected signal for Browser canvas display
                print(f"📊 Corpus browser: Emitting example_selected signal for '{example.title}'")
                self.example_selected.emit(example.title, egif_content)
                
            except Exception as e:
                self.egif_preview.setPlainText(f"Error loading EGIF: {e}")
        else:
            self.egif_preview.setPlainText("EGIF file not found")
    
    def _clear_details(self):
        """Clear the details display."""
        self.metadata_display.clear()
        self.egif_preview.clear()
    
    def _load_selected_example(self):
        """Load the selected example into the canvas."""
        selected_items = self.example_tree.selectedItems()
        
        if selected_items:
            item = selected_items[0]
            example_id = item.data(0, Qt.UserRole)
            
            if example_id and example_id in self.examples:
                example = self.examples[example_id]
                
                if example.egif_path and example.egif_path.exists():
                    try:
                        with open(example.egif_path, 'r') as f:
                            egif_content = f.read()
                        
                        # Extract just the EGIF (skip comments)
                        egif_lines = []
                        for line in egif_content.split('\n'):
                            line = line.strip()
                            if line and not line.startswith('#'):
                                egif_lines.append(line)
                        
                        clean_egif = '\n'.join(egif_lines).strip()
                        
                        if clean_egif:
                            print(f"📊 Loading example: {example.title}")
                            print(f"   EGIF: {clean_egif}")
                            self.example_selected.emit(example.title, clean_egif)
                        else:
                            print(f"⚠ No EGIF content found in {example.egif_path}")
                    
                    except Exception as e:
                        print(f"❌ Failed to load example: {e}")


def create_corpus_browser(corpus_path: str = "corpus/corpus") -> CorpusBrowser:
    """Factory function to create a corpus browser."""
    return CorpusBrowser(corpus_path)


if __name__ == "__main__":
    # Test the corpus browser
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    browser = create_corpus_browser()
    browser.show()
    
    print("📚 Corpus Browser Test")
    print("Browser created and displayed")
    
    sys.exit(app.exec())
