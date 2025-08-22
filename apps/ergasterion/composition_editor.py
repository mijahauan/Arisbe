#!/usr/bin/env python3
"""
Composition Editor - Interactive composition interface for Existential Graphs

Provides tools for composing and editing Existential Graphs with
visual feedback and validation.
"""

import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

try:
    from PySide6.QtCore import Qt, Signal, QObject
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    # Dummy classes
    class QWidget: pass
    class QObject: pass
    class Signal: pass

try:
    from egi_types import EGI, Vertex, Edge, Cut
except ImportError:
    # Create basic classes if not available
    class EGI:
        def __init__(self):
            self.V = []
            self.E = []
            self.Cut = []
    
    class Vertex:
        def __init__(self, id, label=""):
            self.id = id
            self.label = label
    
    class Edge:
        def __init__(self, id, predicate=""):
            self.id = id
            self.predicate = predicate
    
    class Cut:
        def __init__(self, id, enclosed_elements=None):
            self.id = id
            self.enclosed_elements = enclosed_elements or []

class CompositionEditor(QWidget):
    """
    Interactive editor for composing Existential Graphs.
    
    Provides tools for creating vertices, edges, and cuts with
    real-time validation and visual feedback.
    """
    
    # Signals
    graph_changed = Signal(object)
    element_added = Signal(str, object)
    element_removed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_egi = EGI()
        self.current_egi.V = []
        self.current_egi.E = []
        self.current_egi.Cut = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the composition editor interface."""
        if not PYSIDE6_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # Tool buttons
        tools_layout = QHBoxLayout()
        
        self.add_vertex_btn = QPushButton("Add Vertex")
        self.add_vertex_btn.clicked.connect(self._add_vertex)
        tools_layout.addWidget(self.add_vertex_btn)
        
        self.add_edge_btn = QPushButton("Add Edge")
        self.add_edge_btn.clicked.connect(self._add_edge)
        tools_layout.addWidget(self.add_edge_btn)
        
        self.add_cut_btn = QPushButton("Add Cut")
        self.add_cut_btn.clicked.connect(self._add_cut)
        tools_layout.addWidget(self.add_cut_btn)
        
        layout.addLayout(tools_layout)
        
        # Composition area
        self.composition_area = QTextEdit()
        self.composition_area.setPlaceholderText("Composition area - elements will appear here")
        layout.addWidget(self.composition_area)
    
    def _add_vertex(self):
        """Add a new vertex to the composition."""
        vertex_id = f"v{len(self.current_egi.V) + 1}"
        vertex = Vertex(id=vertex_id, label="new_vertex")
        
        self.current_egi.V.append(vertex)
        self._update_display()
        self.element_added.emit("vertex", vertex)
    
    def _add_edge(self):
        """Add a new edge to the composition."""
        edge_id = f"e{len(self.current_egi.E) + 1}"
        edge = Edge(id=edge_id, predicate="relates")
        
        self.current_egi.E.append(edge)
        self._update_display()
        self.element_added.emit("edge", edge)
    
    def _add_cut(self):
        """Add a new cut to the composition."""
        cut_id = f"c{len(self.current_egi.Cut) + 1}"
        cut = Cut(id=cut_id, enclosed_elements=[])
        
        self.current_egi.Cut.append(cut)
        self._update_display()
        self.element_added.emit("cut", cut)
    
    def _update_display(self):
        """Update the composition display."""
        if not hasattr(self, 'composition_area'):
            return
            
        display_text = "Current Composition:\n\n"
        
        display_text += "Vertices:\n"
        for vertex in self.current_egi.V:
            label = getattr(vertex, 'label', 'unlabeled')
            display_text += f"  {vertex.id}: {label}\n"
        
        display_text += "\nEdges:\n"
        for edge in self.current_egi.E:
            predicate = getattr(edge, 'predicate', 'relates')
            display_text += f"  {edge.id}: {predicate}\n"
        
        display_text += "\nCuts:\n"
        for cut in self.current_egi.Cut:
            enclosed = getattr(cut, 'enclosed_elements', [])
            display_text += f"  {cut.id}: encloses {len(enclosed)} elements\n"
        
        self.composition_area.setPlainText(display_text)
        self.graph_changed.emit(self.current_egi)
    
    def load_egi(self, egi: EGI):
        """Load an existing EGI for editing."""
        self.current_egi = egi
        self._update_display()
    
    def get_egi(self) -> EGI:
        """Get the current EGI being composed."""
        return self.current_egi
    
    def clear_composition(self):
        """Clear the current composition."""
        self.current_egi = EGI()
        self.current_egi.V = []
        self.current_egi.E = []
        self.current_egi.Cut = []
        self._update_display()
    
    def remove_element(self, element_id: str):
        """Remove an element from the composition."""
        # Remove from vertices
        self.current_egi.V = [v for v in self.current_egi.V if v.id != element_id]
        
        # Remove from edges
        self.current_egi.E = [e for e in self.current_egi.E if e.id != element_id]
        
        # Remove from cuts
        self.current_egi.Cut = [c for c in self.current_egi.Cut if c.id != element_id]
        
        # Remove from cut enclosures
        for cut in self.current_egi.Cut:
            if hasattr(cut, 'enclosed_elements'):
                cut.enclosed_elements = [e for e in cut.enclosed_elements if e != element_id]
        
        self._update_display()
        self.element_removed.emit(element_id)
    
    def validate_composition(self) -> bool:
        """Validate the current composition."""
        try:
            # Basic validation
            if not hasattr(self.current_egi, 'V') or not hasattr(self.current_egi, 'E'):
                return False
            
            # Check for duplicate IDs
            all_ids = []
            for vertex in self.current_egi.V:
                if vertex.id in all_ids:
                    return False
                all_ids.append(vertex.id)
            
            for edge in self.current_egi.E:
                if edge.id in all_ids:
                    return False
                all_ids.append(edge.id)
            
            for cut in self.current_egi.Cut:
                if cut.id in all_ids:
                    return False
                all_ids.append(cut.id)
            
            return True
            
        except Exception:
            return False
