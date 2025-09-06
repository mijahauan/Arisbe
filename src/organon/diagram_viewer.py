from __future__ import annotations

from pathlib import Path
from typing import Optional, Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, QMessageBox, QGraphicsTextItem, QToolBar, QPushButton
from PySide6.QtGui import QPen, QBrush, QColor, QAction
from PySide6.QtCore import QLineF

from egdf_parser import EGDFDocument
from shared_diagram_renderer import SharedDiagramRenderer


class DiagramViewer(QWidget):
    """
    Simple EGDF diagram viewer that renders layout data directly.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._current_doc: Optional[EGDFDocument] = None

        v = QVBoxLayout(self)
        
        # Add annotation toolbar
        self._create_annotation_toolbar(v)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        
        # Make Organon view read-only - disable all interactions
        self.view.setDragMode(QGraphicsView.NoDrag)
        self.view.setInteractive(False)
        
        v.addWidget(self.view)
        
        # Use shared renderer with unified style system
        from styling.style_manager import StyleManager
        style_manager = StyleManager()
        self.renderer = SharedDiagramRenderer(self.scene, style_manager)
    
    def _create_annotation_toolbar(self, layout: QVBoxLayout) -> None:
        """Create annotation controls for Organon."""
        toolbar_layout = QHBoxLayout()
        
        # Double cut annotation toggle
        self.double_cut_btn = QPushButton("Double Cuts")
        self.double_cut_btn.setCheckable(True)
        self.double_cut_btn.setToolTip("Highlight double cuts in red")
        self.double_cut_btn.clicked.connect(lambda checked: self._toggle_annotation('double_cuts', checked))
        toolbar_layout.addWidget(self.double_cut_btn)
        
        # Predicate arity annotation toggle
        self.arity_btn = QPushButton("Arity")
        self.arity_btn.setCheckable(True)
        self.arity_btn.setToolTip("Show predicate arity numbers")
        self.arity_btn.clicked.connect(lambda checked: self._toggle_annotation('predicate_arity', checked))
        toolbar_layout.addWidget(self.arity_btn)
        
        # Vertex variable annotation toggle
        self.variables_btn = QPushButton("Names")
        self.variables_btn.setCheckable(True)
        self.variables_btn.setToolTip("Show vertex names")
        self.variables_btn.clicked.connect(lambda checked: self._toggle_annotation('vertex_variables', checked))
        toolbar_layout.addWidget(self.variables_btn)
        
        toolbar_layout.addStretch()  # Push buttons to left
        layout.addLayout(toolbar_layout)
    
    def _toggle_annotation(self, annotation_type: str, enabled: bool) -> None:
        """Toggle annotation display in Organon."""
        if hasattr(self, 'renderer') and self.renderer:
            self.renderer.toggle_annotation(annotation_type, enabled)

    # Public API
    def clear(self) -> None:
        self._current_doc = None
        self.scene.clear()

    def load_egdf_path(self, path: Path) -> None:
        doc = self._read_doc(path)
        self._set_doc(doc)

    def set_egdf_text(self, text: str, is_yaml: bool = False) -> None:
        doc = EGDFDocument.from_yaml(text) if is_yaml else EGDFDocument.from_json(text)
        self._set_doc(doc)

    def get_current_doc(self) -> Optional[EGDFDocument]:
        return self._current_doc

    # Internals
    def _read_doc(self, path: Path) -> EGDFDocument:
        text = path.read_text(encoding="utf-8")
        if str(path).endswith(('.yaml', '.yml')):
            return EGDFDocument.from_yaml(text)
        return EGDFDocument.from_json(text)

    def _set_doc(self, doc: EGDFDocument) -> None:
        # Store document and render directly from EGDF layout data
        self._current_doc = doc
        self._render_exact()

    def _replace_egi_from_inline(self, inline: dict) -> None:
        sheet: str = inline.get("sheet") or "sheet"
        # Vertices from list of IDs; labels via rho if present
        V = []
        rho_map = inline.get("rho") or {}
        for vid in inline.get("V", []):
            label = rho_map.get(vid)
            is_generic = True if label is None else False
            V.append(Vertex(id=vid, label=label, is_generic=is_generic))
        E = [Edge(id=eid) for eid in inline.get("E", [])]
        CutSet = [Cut(id=cid) for cid in inline.get("Cut", [])]
        nu = frozendict({k: tuple(v) for k, v in (inline.get("nu") or {}).items()})
        rel = frozendict(dict(inline.get("rel") or {}))
        area = frozendict({k: frozenset(v) for k, v in (inline.get("area") or {}).items()})
        rho = frozendict(dict(rho_map))
        alph_data = inline.get("alphabet") or {}
        alph = AlphabetDAU(
            C=frozenset(alph_data.get("C") or []),
            F=frozenset(alph_data.get("F") or []),
            R=frozenset(alph_data.get("R") or []),
            ar=frozendict(alph_data.get("ar") or {}),
        ).with_defaults()
        graph = RelationalGraphWithCuts(
            V=frozenset(V),
            E=frozenset(E),
            nu=nu,
            sheet=sheet,
            Cut=frozenset(CutSet),
            area=area,
            rel=rel,
            alphabet=alph,
            rho=rho,
        )
        self._egi_system.replace_egi(graph)

    def _render_exact(self) -> None:
        """Render EGDF using shared renderer for consistent ligature anchoring."""
        if not self._current_doc:
            return
        # Pass interactive=True to enable constraint validation in Organon view
        self.renderer.render_egdf(self._current_doc, interactive=True)
        
        # Ensure vertex names are rendered in Organon
        self.renderer._render_vertex_names()
