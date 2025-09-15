from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QLineF, Qt
from PySide6.QtGui import QAction, QBrush, QColor, QPen
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from egi_dto import EGIStateDTO
from gui.clean_egi_viewer import CleanEGIViewer


class DiagramViewer(QWidget):
    """
    Clean EGI diagram viewer for Organon using pure Dau formalism.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Use clean EGI viewer in read-only mode
        layout = QVBoxLayout(self)
        self.clean_viewer = CleanEGIViewer(read_only=True, parent=self)
        layout.addWidget(self.clean_viewer)

    # Public API
    def clear(self) -> None:
        """Clear the diagram display."""
        # Delegate to clean viewer
        if hasattr(self.clean_viewer, "scene"):
            self.clean_viewer.scene.clear()

    def load_egdf_path(self, path: Path) -> None:
        """EGDF loading disabled - use EGI DTO system instead."""
        print(f"[DiagramViewer] EGDF rendering disabled for {path}")
        self.clear()

    def load_egi_dto_readonly(self, egi_dto: EGIStateDTO) -> None:
        """Load EGI DTO for read-only display in Organon using clean renderer."""
        print(
            f"[DiagramViewer] Loading EGI DTO with clean renderer: {len(egi_dto.vertices)} vertices, {len(egi_dto.edges)} edges, {len(egi_dto.cuts)} cuts"
        )

        # Convert EGI DTO to RelationalGraphWithCuts
        egi = self._convert_dto_to_egi(egi_dto)

        # Load using clean viewer
        self.clean_viewer.load_egi(egi)

        print("[DiagramViewer] EGI DTO loaded using clean renderer")

    def _convert_dto_to_egi(self, egi_dto: EGIStateDTO):
        """Convert EGI DTO to RelationalGraphWithCuts for clean rendering."""
        from frozendict import frozendict

        from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex

        # Convert vertices
        vertices = frozenset(
            Vertex(
                id=vertex_id,
                label=vertex_dto.label,
                is_generic=(vertex_dto.label is None),
            )
            for vertex_id, vertex_dto in egi_dto.vertices.items()
        )

        # Convert edges
        edges = frozenset(Edge(id=edge_id) for edge_id in egi_dto.edges.keys())

        # Convert cuts
        cuts = frozenset(Cut(id=cut_id) for cut_id in egi_dto.cuts.keys())

        # Build nu mapping (edge -> vertex sequence)
        nu_mapping = {}
        for edge_id, edge_dto in egi_dto.edges.items():
            if hasattr(edge_dto, "incident_vertices") and edge_dto.incident_vertices:
                nu_mapping[edge_id] = tuple(edge_dto.incident_vertices)
            else:
                nu_mapping[edge_id] = tuple()

        # Build relation mapping
        rel_mapping = {}
        for edge_id, edge_dto in egi_dto.edges.items():
            if hasattr(edge_dto, "relation_name") and edge_dto.relation_name:
                rel_mapping[edge_id] = edge_dto.relation_name
            else:
                rel_mapping[edge_id] = f"rel_{edge_id[:8]}"

        # Build area mapping - all elements on sheet for now
        sheet_id = "sheet"
        all_element_ids = (
            set(egi_dto.vertices.keys())
            | set(egi_dto.edges.keys())
            | set(egi_dto.cuts.keys())
        )
        area_mapping = {sheet_id: frozenset(all_element_ids)}

        # Add empty areas for cuts
        for cut_id in egi_dto.cuts.keys():
            area_mapping[cut_id] = frozenset()

        return RelationalGraphWithCuts(
            V=vertices,
            E=edges,
            nu=frozendict(nu_mapping),
            sheet=sheet_id,
            Cut=cuts,
            area=frozendict(area_mapping),
            rel=frozendict(rel_mapping),
        )
