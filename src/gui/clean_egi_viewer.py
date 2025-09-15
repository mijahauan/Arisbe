"""
Clean EGI Viewer Widget

Pure PySide6 widget for viewing EGI diagrams using only:
- egi_core_dau.py (Dau's 6+1 formalism)
- dau_diagram_correspondence.py (clean EGI ↔ diagram mapping)
- clean_diagram_renderer.py (pure Qt rendering)

No legacy code dependencies. Suitable for both Organon (read-only)
and Ergasterion (interactive) use cases.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from egi_core_dau import RelationalGraphWithCuts
from gui.clean_diagram_renderer import CleanDiagramRenderer


class CleanEGIViewer(QWidget):
    """
    Clean EGI viewer widget using pure Dau formalism.

    Features:
    - Load and display EGI using clean renderer
    - Optional annotation toggles (vertex labels, edge numbers, etc.)
    - Element selection and highlighting
    - Read-only or interactive modes
    """

    # Signals
    element_selected = Signal(str, str)  # element_id, element_type
    element_double_clicked = Signal(str, str)  # element_id, element_type

    def __init__(self, read_only: bool = True, parent=None):
        super().__init__(parent)
        self.read_only = read_only
        self.current_egi = None
        self.renderer = CleanDiagramRenderer()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("EGI Diagram Viewer" if self.read_only else "EGI Diagram Editor")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Annotation toggles
        self.show_vertex_labels = QCheckBox("Vertex Labels")
        self.show_vertex_labels.setChecked(True)
        header_layout.addWidget(self.show_vertex_labels)

        self.show_edge_numbers = QCheckBox("Edge Numbers")
        self.show_edge_numbers.setChecked(True)
        header_layout.addWidget(self.show_edge_numbers)

        self.show_cut_areas = QCheckBox("Cut Areas")
        self.show_cut_areas.setChecked(True)
        header_layout.addWidget(self.show_cut_areas)

        layout.addLayout(header_layout)

        # Graphics view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        from PySide6.QtGui import QPainter

        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(
            QGraphicsView.DragMode.RubberBandDrag
            if not self.read_only
            else QGraphicsView.DragMode.NoDrag
        )

        layout.addWidget(self.view)

        # Status bar
        status_layout = QHBoxLayout()

        self.status_label = QLabel("No EGI loaded")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        if not self.read_only:
            # Interactive mode buttons
            self.clear_selection_btn = QPushButton("Clear Selection")
            status_layout.addWidget(self.clear_selection_btn)

        layout.addLayout(status_layout)

    def _connect_signals(self):
        """Connect widget signals."""
        self.show_vertex_labels.toggled.connect(self._refresh_display)
        self.show_edge_numbers.toggled.connect(self._refresh_display)
        self.show_cut_areas.toggled.connect(self._refresh_display)

        if not self.read_only:
            self.clear_selection_btn.clicked.connect(self._clear_selection)
            self.scene.selectionChanged.connect(self._on_selection_changed)

    def load_egi(self, egi: RelationalGraphWithCuts) -> None:
        """
        Load and display EGI using clean renderer.

        Args:
            egi: The EGI to display
        """
        self.current_egi = egi

        try:
            # Render using clean renderer
            self.renderer.render_egi_to_scene(egi, self.scene)

            # Update status
            vertex_count = len(egi.V)
            edge_count = len(egi.E)
            cut_count = len(egi.Cut)

            self.status_label.setText(
                f"EGI loaded: {vertex_count} vertices, {edge_count} edges, {cut_count} cuts"
            )

            # Fit view to contents
            self.view.fitInView(
                self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio
            )

            print(
                f"[CleanEGIViewer] Loaded EGI with {vertex_count} vertices, "
                f"{edge_count} edges, {cut_count} cuts"
            )

        except Exception as e:
            self.status_label.setText(f"Error loading EGI: {e}")
            print(f"[CleanEGIViewer] Error loading EGI: {e}")
            import traceback

            traceback.print_exc()

    def _refresh_display(self):
        """Refresh the display with current annotation settings."""
        if self.current_egi is None:
            return

        # Re-render with current settings
        # Note: In a full implementation, this would selectively show/hide elements
        # For now, just re-render everything
        self.load_egi(self.current_egi)

    def _clear_selection(self):
        """Clear all selections."""
        self.scene.clearSelection()

    def _on_selection_changed(self):
        """Handle selection changes."""
        selected_items = self.scene.selectedItems()

        if selected_items:
            # Get first selected item
            item = selected_items[0]
            element_id = item.data(0)
            element_type = item.data(1)

            if element_id and element_type:
                self.element_selected.emit(element_id, element_type)
                print(f"[CleanEGIViewer] Selected {element_type}: {element_id}")

    def highlight_element(self, element_id: str, highlight: bool = True):
        """Highlight element in the display."""
        self.renderer.highlight_element(element_id, highlight)

    def get_current_egi(self) -> Optional[RelationalGraphWithCuts]:
        """Get the currently loaded EGI."""
        return self.current_egi

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        super().mousePressEvent(event)

        if not self.read_only:
            # Convert to scene coordinates
            scene_pos = self.view.mapToScene(event.pos())

            # Get element at position
            element_info = self.renderer.get_element_at_position(scene_pos)

            if element_info:
                element_id, element_type = element_info

                if event.button() == Qt.MouseButton.LeftButton:
                    self.element_selected.emit(element_id, element_type)
                elif (
                    event.button() == Qt.MouseButton.LeftButton
                    and event.type() == event.Type.MouseButtonDblClick
                ):
                    self.element_double_clicked.emit(element_id, element_type)


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    from egi_core_dau import create_cut, create_edge, create_empty_graph, create_vertex

    print("=== Testing Clean EGI Viewer ===")

    app = QApplication(sys.argv)

    # Create test EGI
    graph = create_empty_graph()

    # Add vertices
    v1 = create_vertex(label=None, is_generic=True)
    v2 = create_vertex(label="Socrates", is_generic=False)
    graph = graph.with_vertex(v1).with_vertex(v2)

    # Add relation
    edge = create_edge()
    graph = graph.with_edge(edge, (v1.id, v2.id), "loves")

    # Add cut with vertex inside
    cut = create_cut()
    graph = graph.with_cut(cut)
    v3 = create_vertex(label="Plato", is_generic=False)
    graph = graph.with_vertex_in_context(v3, cut.id)

    print(
        f"✓ Created test EGI: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts"
    )

    # Test viewer
    viewer = CleanEGIViewer(read_only=False)
    viewer.load_egi(graph)
    viewer.show()

    print("✓ Clean EGI Viewer launched")

    sys.exit(app.exec())
