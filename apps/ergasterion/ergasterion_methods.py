#!/usr/bin/env python3
"""
Additional methods for Ergasterion Workshop
"""

def _on_egif_input(self):
    """Handle EGIF text input and parse it."""
    egif_text = self.canvas_widget.toPlainText().strip()
    if egif_text:
        try:
            # Parse EGIF
            egi = self.egif_parser.parse(egif_text)
            self.current_egi = egi
            
            # Update displays
            self._update_graph_display()
            self.status_bar.showMessage(f"Parsed EGIF: {len(egi.V)} vertices, {len(egi.E)} edges")
            
        except Exception as e:
            self.status_bar.showMessage(f"EGIF parse error: {e}")

def _load_sample_egif(self):
    """Load a sample EGIF for testing."""
    sample_egif = """[Socrates: Man]
[Man: Mortal]
[Socrates: Mortal]"""
    
    if hasattr(self.canvas_widget, 'setPlainText'):
        self.canvas_widget.setPlainText(sample_egif)
        self._on_egif_input()

def _update_graph_display(self):
    """Update the graph display after parsing."""
    if self.current_egi is None:
        return
        
    try:
        # Generate layout
        layout_result = self.pipeline.generate_layout(self.current_egi)
        
        # If we have a proper canvas widget, render there
        if hasattr(self.canvas_widget, 'update_graph'):
            self.canvas_widget.update_graph(self.current_egi, layout_result)
        else:
            # For text widget, show structure info
            structure_info = f"""

--- Parsed Structure ---
Vertices: {len(self.current_egi.V)}
Edges: {len(self.current_egi.E)}
Cuts: {len(getattr(self.current_egi, 'Cut', []))}

Vertices:
"""
            for v in self.current_egi.V:
                structure_info += f"  {v.id}: {getattr(v, 'label', 'unlabeled')}\n"
            
            structure_info += "\nEdges:\n"
            for e in self.current_egi.E:
                structure_info += f"  {e.id}: {getattr(e, 'predicate', 'no predicate')}\n"
            
            current_text = self.canvas_widget.toPlainText().split('--- Parsed Structure ---')[0]
            self.canvas_widget.setPlainText(current_text + structure_info)
            
    except Exception as e:
        self.status_bar.showMessage(f"Display error: {e}")

def load_from_browser(self, egi_data):
    """Load graph data from the browser component."""
    try:
        self.current_egi = egi_data
        
        # Convert to EGIF text representation
        egif_text = self._egi_to_egif_string(egi_data)
        
        if hasattr(self.canvas_widget, 'setPlainText'):
            self.canvas_widget.setPlainText(egif_text)
        
        self._update_graph_display()
        self.status_bar.showMessage("Graph loaded from browser")
        
    except Exception as e:
        self.status_bar.showMessage(f"Error loading from browser: {e}")

def _egi_to_egif_string(self, egi):
    """Convert EGI back to EGIF string representation."""
    if egi is None:
        return ""
        
    egif_lines = []
    
    # Add vertices as propositions
    for vertex in getattr(egi, 'V', []):
        label = getattr(vertex, 'label', 'unlabeled')
        egif_lines.append(f"[{vertex.id}: {label}]")
    
    # Add edges as relations
    for edge in getattr(egi, 'E', []):
        predicate = getattr(edge, 'predicate', 'relates')
        # Simple representation - could be enhanced
        egif_lines.append(f"[{edge.id}: {predicate}]")
    
    return "\n".join(egif_lines)
