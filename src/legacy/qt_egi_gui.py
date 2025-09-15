#!/usr/bin/env python3
"""
Arisbe Qt GUI - Organon Mode (minimal scaffold)

Defines required classes for tests:
- BranchingPointItem, LigatureItem, PredicateItem, CutItem
- EGIGraphicsView, EGIControlPanel, EGIMainWindow

Integrates with EGISystem and QtCorrespondenceIntegration to generate a scene.
"""
from __future__ import annotations

import hashlib
import json

# Enforce PySide6 and block PyQt6 before any Qt import to avoid mixed bindings
import os as _os
import sys
import sys as _sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Optional

_os.environ.setdefault("QT_API", "pyside6")
if "PyQt6" in _sys.modules:
    _sys.modules["PyQt6"] = None  # type: ignore[assignment]

from time import monotonic

from PySide6.QtCore import QLineF, QPointF, QRectF, QSizeF, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QFormLayout,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


# --- Module-level helpers ----------------------------------------------------
def _egi_loader_dispatch(main: "EGIMainWindow", path: Path) -> None:
    """Dispatch to an available EGI JSON loader on the given main window.
    Preference order: _safe_load_egi_json → load_egi_json → _load_egi_json.
    """
    # Prefer canonical safe loader if present
    fn = getattr(main, "_safe_load_egi_json", None)
    if callable(fn):
        return fn(path)
    # Next, public API
    fn = getattr(main, "load_egi_json", None)
    if callable(fn):
        return fn(path)
    # Legacy alias
    fn = getattr(main, "_load_egi_json", None)
    if callable(fn):
        return fn(path)
    # As a last resort, perform a minimal inline load here to ensure UX continuity
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        sheet: str = data.get("sheet") or "sheet"
        V = [
            Vertex(
                id=v.get("id"),
                label=v.get("label"),
                is_generic=bool(v.get("is_generic", True)),
            )
            for v in (data.get("V") or [])
            if v.get("id")
        ]
        E = [Edge(id=e.get("id")) for e in (data.get("E") or []) if e.get("id")]
        CutSet = [Cut(id=c.get("id")) for c in (data.get("Cut") or []) if c.get("id")]
        nu = frozendict({k: tuple(v) for k, v in (data.get("nu") or {}).items()})
        rel = frozendict(dict(data.get("rel") or {}))
        area = frozendict(
            {k: frozenset(v) for k, v in (data.get("area") or {}).items()}
        )
        rho = frozendict(dict(data.get("rho") or {}))
        alph_data = data.get("alphabet") or {}
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
        main.egi_system.replace_egi(graph)
        return None
    except Exception:
        # Nothing found: emit clearer diagnostics
        available = [
            name
            for name in ("_safe_load_egi_json", "load_egi_json", "_load_egi_json")
            if hasattr(main, name)
        ]
        raise AttributeError(
            f"No EGI JSON loader available on this EGIMainWindow instance (checked: {', '.join(available) or 'none'})"
        )


from egdf_parser import EGDFDocument
from frozendict import frozendict
from PySide6.QtGui import QBrush, QColor, QFont, QPainterPath, QPen
from qt_correspondence_integration import create_qt_correspondence_integration

import corpus_index as cidx
from egi_core_dau import AlphabetDAU, Cut, Edge, RelationalGraphWithCuts, Vertex
from egi_system import EGISystem, create_egi_system
from export.tikz_exporter import generate_tikz
from styling.style_manager import create_style_manager

# Optional: embed the known-good DrawingEditor as a preview
try:
    from drawing_editor import DrawingEditor as _DrawingEditor  # type: ignore
except Exception:
    _DrawingEditor = None  # type: ignore


# --- Utilities ---
def _qcolor(value) -> QColor:
    """Parse color tokens flexibly, supporting:
    - "transparent"
    - "#RRGGBB" or named colors
    - "rgba(r,g,b,a)" with a in 0..1 or 0..255
    - [r,g,b,a] list/tuple with floats 0..1 or ints 0..255
    """
    try:
        if value is None:
            return QColor(0, 0, 0, 0)
        if isinstance(value, QColor):
            return value
        if isinstance(value, str):
            s = value.strip()
            if s.lower() == "transparent":
                return QColor(0, 0, 0, 0)
            if s.lower().startswith("rgba(") and s.endswith(")"):
                parts = [p.strip() for p in s[5:-1].split(",")]
                if len(parts) == 4:
                    r, g, b, a = parts
                    r = float(r)
                    g = float(g)
                    b = float(b)
                    a = float(a)
                    # If any component > 1, assume 0..255 range; else 0..1
                    if max(r, g, b, a) > 1.0:
                        return QColor(int(r), int(g), int(b), int(a))
                    return QColor.fromRgbF(r, g, b, a)
            # Fallback to named/hex
            qc = QColor(s)
            if not qc.isValid():
                return QColor(0, 0, 0, 0)
            return qc
        if isinstance(value, (list, tuple)) and len(value) >= 4:
            r, g, b, a = value[:4]
            # Detect 0..255 vs 0..1
            if max(r, g, b, a) > 1.0:
                return QColor(int(r), int(g), int(b), int(a))
            return QColor.fromRgbF(float(r), float(g), float(b), float(a))
    except Exception:
        pass
    return QColor(0, 0, 0, 0)


# --- Minimal graphics items ---
class BranchingPointItem(QGraphicsEllipseItem):
    def __init__(self, x: float, y: float, r: float = 6.0):
        super().__init__(x - r / 2, y - r / 2, r, r)
        self.setBrush(QBrush(QColor(0, 0, 0)))
        self.setPen(QPen(QColor(0, 0, 0), 1))


class LigatureItem(QGraphicsLineItem):
    pass


class PredicateItem(QGraphicsTextItem):
    def __init__(self, label: str, x: float, y: float):
        super().__init__(label)
        self.setFont(QFont("Arial", 10))
        rect = self.boundingRect()
        self.setPos(x - rect.width() / 2, y - rect.height() / 2)


class CutItem(QGraphicsRectItem):
    def __init__(self, x: float, y: float, w: float, h: float):
        super().__init__(x, y, w, h)
        pen = QPen(QColor(0, 0, 0), 1)
        self.setPen(pen)
        self.setBrush(QBrush(QColor(240, 240, 240, 60)))


# --- View and control panel ---
class EGIGraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, main_window: "EGIMainWindow"):
        super().__init__(scene)
        self.main_window = main_window
        self.setRenderHints(self.renderHints())
        self.setMouseTracking(True)
        # Hover throttle state
        self._hover_throttle_ms: float = 60.0
        self._last_hover_time: float = 0.0
        self._last_hover_id: str | None = None

    def mousePressEvent(self, event):
        # Handle right-click context menus
        if event.button() == event.MouseButton.RightButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            items = self.scene().items(scene_pos)

            # Find the best item under cursor
            precedence = {"vertex": 0, "edge": 1, "ligature": 2, "cut": 3}
            best = None
            best_rank = 999
            best_item = None

            for it in items:
                try:
                    etype = it.data(1)
                    eid = it.data(0)
                except Exception:
                    etype, eid = None, None
                if not eid or not etype:
                    continue
                rank = precedence.get(str(etype), 100)
                if rank < best_rank:
                    best_rank = rank
                    best = (str(eid), str(etype))
                    best_item = it

            if best:
                self._show_context_menu(
                    event.globalPosition().toPoint(), best[0], best[1], best_item
                )
            else:
                self._show_canvas_context_menu(
                    event.globalPosition().toPoint(), scene_pos
                )
            return

        # Handle left-click selection
        scene_pos = self.mapToScene(event.position().toPoint())
        items = self.scene().items(scene_pos)

        # Precedence: vertex > edge > ligature > cut
        precedence = {"vertex": 0, "edge": 1, "ligature": 2, "cut": 3}

        best = None
        best_rank = 999
        for it in items:
            try:
                etype = it.data(1)
                eid = it.data(0)
            except Exception:
                etype, eid = None, None
            if not eid or not etype:
                continue
            rank = precedence.get(str(etype), 100)
            if rank < best_rank:
                best_rank = rank
                best = (str(eid), str(etype))

        if best:
            self.main_window.select_element(best[0])

        # Continue default behavior
        super().mousePressEvent(event)

    def _show_context_menu(self, global_pos, element_id, element_type, item):
        """Show context menu for diagram elements."""
        from PySide6.QtWidgets import QMenu

        menu = QMenu()

        if element_type == "vertex":
            menu.addAction("Edit Vertex Name", lambda: self._edit_vertex(element_id))
            menu.addAction("Delete Vertex", lambda: self._delete_vertex(element_id))
            menu.addAction(
                "Extend Ligature from Vertex",
                lambda: self._start_ligature_from_vertex(element_id),
            )
        elif element_type == "edge":
            menu.addAction(
                "Edit Predicate Text", lambda: self._edit_predicate(element_id)
            )
            menu.addAction(
                "Delete Predicate", lambda: self._delete_predicate(element_id)
            )
            menu.addAction(
                "Draw Ligature to Vertex",
                lambda: self._start_ligature_from_predicate(element_id),
            )
        elif element_type == "cut":
            menu.addAction("Delete Cut", lambda: self._delete_cut(element_id))
            menu.addAction("Resize Cut", lambda: self._resize_cut(element_id))

        menu.exec(global_pos)

    def _show_canvas_context_menu(self, global_pos, scene_pos):
        """Show context menu for empty canvas."""
        from PySide6.QtWidgets import QMenu

        menu = QMenu()
        menu.addAction("Add Vertex", lambda: self._add_vertex_at_position(scene_pos))
        menu.addAction(
            "Add Predicate", lambda: self._add_predicate_at_position(scene_pos)
        )
        menu.addAction("Add Cut", lambda: self._add_cut_at_position(scene_pos))

        menu.exec(global_pos)

    def _edit_vertex(self, vertex_id):
        """Edit vertex name."""
        from PySide6.QtWidgets import QInputDialog

        current_name = ""
        # Get current name from main window if available
        if hasattr(self.main_window, "get_vertex_name"):
            current_name = self.main_window.get_vertex_name(vertex_id) or ""

        name, ok = QInputDialog.getText(
            self,
            "Edit Vertex",
            f"Enter name for vertex {vertex_id}:",
            text=current_name,
        )
        if ok:
            if hasattr(self.main_window, "update_vertex_name"):
                self.main_window.update_vertex_name(vertex_id, name)

    def _delete_vertex(self, vertex_id):
        """Delete vertex."""
        if hasattr(self.main_window, "delete_vertex"):
            self.main_window.delete_vertex(vertex_id)

    def _edit_predicate(self, predicate_id):
        """Edit predicate text."""
        from PySide6.QtWidgets import QInputDialog

        current_text = ""
        if hasattr(self.main_window, "get_predicate_text"):
            current_text = self.main_window.get_predicate_text(predicate_id) or ""

        text, ok = QInputDialog.getText(
            self,
            "Edit Predicate",
            f"Enter text for predicate {predicate_id}:",
            text=current_text,
        )
        if ok:
            if hasattr(self.main_window, "update_predicate_text"):
                self.main_window.update_predicate_text(predicate_id, text)

    def _delete_predicate(self, predicate_id):
        """Delete predicate."""
        if hasattr(self.main_window, "delete_predicate"):
            self.main_window.delete_predicate(predicate_id)

    def _delete_cut(self, cut_id):
        """Delete cut."""
        if hasattr(self.main_window, "delete_cut"):
            self.main_window.delete_cut(cut_id)

    def _resize_cut(self, cut_id):
        """Resize cut."""
        from PySide6.QtWidgets import QInputDialog

        width, ok1 = QInputDialog.getDouble(
            self, "Resize Cut", "Enter new width:", 150, 10, 1000, 1
        )
        if not ok1:
            return

        height, ok2 = QInputDialog.getDouble(
            self, "Resize Cut", "Enter new height:", 100, 10, 1000, 1
        )
        if not ok2:
            return

        if hasattr(self.main_window, "resize_cut"):
            self.main_window.resize_cut(cut_id, width, height)

    def _add_vertex_at_position(self, scene_pos):
        """Add vertex at position."""
        if hasattr(self.main_window, "add_vertex_at_position"):
            self.main_window.add_vertex_at_position(scene_pos.x(), scene_pos.y())

    def _add_predicate_at_position(self, scene_pos):
        """Add predicate at position."""
        from PySide6.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(self, "Add Predicate", "Enter predicate text:")
        if ok and text:
            if hasattr(self.main_window, "add_predicate_at_position"):
                self.main_window.add_predicate_at_position(
                    scene_pos.x(), scene_pos.y(), text
                )

    def _add_cut_at_position(self, scene_pos):
        """Add cut at position."""
        if hasattr(self.main_window, "add_cut_at_position"):
            self.main_window.add_cut_at_position(scene_pos.x(), scene_pos.y())

    def _start_ligature_from_vertex(self, vertex_id):
        """Start ligature drawing from vertex."""
        # For now, show info message - full implementation would require ligature drawing mode
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Ligature Drawing",
            f"Ligature drawing from vertex {vertex_id} - feature in development",
        )

    def _start_ligature_from_predicate(self, predicate_id):
        """Start ligature drawing from predicate."""
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Ligature Drawing",
            f"Ligature drawing from predicate {predicate_id} - feature in development",
        )

    def mouseMoveEvent(self, event):
        # Basic throttle to prevent excessive processing on tiny/continuous movements
        now = monotonic() * 1000.0
        if now - self._last_hover_time < self._hover_throttle_ms:
            return super().mouseMoveEvent(event)
        # Hover highlight with same precedence
        scene_pos = self.mapToScene(event.position().toPoint())
        items = self.scene().items(scene_pos)
        precedence = {"vertex": 0, "edge": 1, "ligature": 2, "cut": 3}
        best = None
        best_rank = 999
        for it in items:
            try:
                etype = it.data(1)
                eid = it.data(0)
            except Exception:
                etype, eid = None, None
            if not eid or not etype:
                continue
            rank = precedence.get(str(etype), 100)
            if rank < best_rank:
                best_rank = rank
                best = (str(eid), str(etype))

        if best:
            best_id = best[0]
            if best_id != self._last_hover_id:
                try:
                    self.main_window.hover_element(best_id)
                except Exception:
                    pass
                self._last_hover_id = best_id
        else:
            if self._last_hover_id is not None:
                try:
                    if hasattr(self.main_window, "clear_hover"):
                        self.main_window.clear_hover()
                except Exception:
                    pass
                self._last_hover_id = None

        self._last_hover_time = now

        super().mouseMoveEvent(event)


class EGIControlPanel(QWidget):
    def __init__(self, main_window: "EGIMainWindow"):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        # Placeholder for future Corpus Index browser
        note = QLabel("Corpus Index: Manage graphs via the left Corpus dock.")
        note.setWordWrap(True)
        layout.addWidget(note)
        # Toggles row
        self.chk_show_vars = QCheckBox("Show variable labels (*x → x)")
        self.chk_show_vars.setChecked(False)
        self.chk_show_vars.stateChanged.connect(
            lambda _: self.main_window.set_show_variable_labels(
                self.chk_show_vars.isChecked()
            )
        )
        layout.addWidget(self.chk_show_vars)

        self.chk_show_arity = QCheckBox("Show relation arity (R → R/n)")
        self.chk_show_arity.setChecked(False)
        self.chk_show_arity.stateChanged.connect(
            lambda _: self.main_window.set_show_arity(self.chk_show_arity.isChecked())
        )
        layout.addWidget(self.chk_show_arity)
        # No Corpus quick actions here; avoid duplicates with left Corpus dock
        layout.addStretch()


# --- Main window ---
class EGIMainWindow(QMainWindow):
    # In-app handoff signal: emit payload dict for Ergasterion
    edit_in_ergasterion = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe – Organon")
        self.resize(1000, 700)

        # Core systems
        self.egi_system: EGISystem = create_egi_system()
        self.qt_integration = create_qt_correspondence_integration(self.egi_system)
        self.style = create_style_manager()
        # Layout tokens (for potential styling of chiron widget)
        ltoks = self.style.resolve(type="layout")
        self._chiron_height = float(ltoks.get("chiron_height", 120.0))

        # Registries and state
        self._items_by_element: DefaultDict[str, List[Any]] = DefaultDict(list)
        self._selected_id: str | None = None
        self._selected_ids: set[str] = set()
        self._hover_id: str | None = None
        # Annotation toggles and caches
        self._show_variable_labels: bool = False
        self._show_arity: bool = False
        self._vertex_var_labels: dict[str, str] = {}
        # File tracking
        self._current_source_path: Optional[Path] = None
        self._last_saved_egdf_path: Optional[Path] = None
        self._current_egdf_doc: Optional[EGDFDocument] = None
        # Corpus tracking
        self._current_graph_dir: Optional[Path] = None

        # Central layout
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Minimal runtime banner to help diagnose import/source mismatches
        try:
            import inspect

            mod_file = inspect.getsourcefile(type(self)) or "(unknown)"
            print(f"[Organon] EGIMainWindow from: {mod_file}")
        except Exception:
            pass

        # Scene and view
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 600)
        self.graphics_view = EGIGraphicsView(self.scene, self)

        # Control panel
        self.control_panel = EGIControlPanel(self)

        root.addWidget(self.graphics_view, 1)
        root.addWidget(self.control_panel)

        # Menu bar: File menu (corpus-first workflow)
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        act_open_corpus = file_menu.addAction("Open Selected (Corpus)…")
        act_open_corpus.triggered.connect(
            lambda: (
                getattr(
                    self,
                    "_open_selected_corpus_action",
                    self._inline_open_selected_corpus,
                )()
            )
        )
        act_reload = file_menu.addAction("Reload")
        act_reload.triggered.connect(
            lambda: (
                getattr(
                    self,
                    "reload_current_source",
                    lambda: QMessageBox.information(
                        self, "No Source", "No source file to reload."
                    ),
                )()
            )
        )
        file_menu.addSeparator()
        act_save_egdf = file_menu.addAction("Save EGDF beside source…")
        act_save_egdf.triggered.connect(
            lambda: (
                getattr(self, "save_egdf_to_sibling", self._inline_save_egdf_beside)()
            )
        )

        # Graph menu (Corpus-aware operations)
        graph_menu = menubar.addMenu("Graph")
        act_new = graph_menu.addAction("New…")
        act_new.triggered.connect(
            lambda: (getattr(self, "on_corpus_new", self._inline_corpus_new)())
        )
        act_open_sel = graph_menu.addAction("Open Selected")
        act_open_sel.triggered.connect(
            lambda: (
                getattr(
                    self,
                    "_open_selected_corpus_action",
                    self._inline_open_selected_corpus,
                )()
            )
        )
        graph_menu.addSeparator()
        act_save_corpus = graph_menu.addAction("Save to Corpus")
        act_save_corpus.triggered.connect(
            lambda: (
                getattr(
                    self,
                    "graph_save_to_corpus",
                    lambda: QMessageBox.information(
                        self, "Corpus", "Save to Corpus not available."
                    ),
                )()
            )
        )
        act_save_egdf_corpus = graph_menu.addAction("Save EGDF to Corpus")
        act_save_egdf_corpus.triggered.connect(
            lambda: (
                getattr(
                    self,
                    "graph_save_egdf_to_corpus",
                    lambda: QMessageBox.information(
                        self, "Corpus", "Save EGDF to Corpus not available."
                    ),
                )()
            )
        )
        act_export_tikz_corpus = graph_menu.addAction("Export TikZ to Corpus")
        act_export_tikz_corpus.triggered.connect(
            lambda: (
                getattr(
                    self,
                    "graph_export_tikz_to_corpus",
                    lambda: QMessageBox.information(
                        self, "Corpus", "Export TikZ to Corpus not available."
                    ),
                )()
            )
        )

        # Graph Info dock
        self.graph_info_dock = GraphInfoDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.graph_info_dock)

        # Optional: Preview dock powered by DrawingEditor (read-only/embedded)
        if "_DrawingEditor" in globals() and _DrawingEditor is not None:
            try:
                self.preview_dock = PreviewDock(self)
                self.addDockWidget(Qt.RightDockWidgetArea, self.preview_dock)
            except Exception:
                pass

        # Corpus dock (left)
        try:
            self._init_corpus_dock()
            # Ensure it is visible
            try:
                self.corpus_dock.show()
            except Exception:
                pass
        except Exception as e:
            # Do not swallow: surface errors to help diagnose why Corpus dock is missing
            import traceback

            tb = traceback.format_exc()
            try:
                QMessageBox.warning(
                    self, "Organon", f"Failed to initialize Corpus dock: {e}\n{tb}"
                )
            except Exception:
                print(f"Failed to initialize Corpus dock: {e}\n{tb}")

        # No default graph on startup; wait for user to open from corpus
        # Track last loaded linear form text for chiron
        try:
            self._last_linear_text: str | None = self.egi_system.to_egif()
        except Exception:
            self._last_linear_text = None
        # Initialize dockable chiron panel
        try:
            self._init_chiron_dock()
        except AttributeError:
            # In case method not available in this build variant, continue without Chiron
            pass
        # Ensure an emitter exists even in legacy builds to prevent crashes
        if not hasattr(self, "_emit_command"):

            def _no_emit_command(cmd):
                return

            try:
                # attach as bound method
                setattr(self, "_emit_command", _no_emit_command)
            except Exception:
                pass

        # --- Minimal core methods to guarantee availability during init ---
        def _clear_scene_min():
            try:
                if hasattr(self, "scene"):
                    self.scene.clear()
                self._items_by_element.clear()
                self._selected_id = None
            except Exception:
                pass

        if not hasattr(self, "clear_scene"):
            setattr(self, "clear_scene", _clear_scene_min)

        def _update_graph_info_min():
            try:
                egi = self.egi_system.get_egi()
                v_count = len(egi.V)
                e_count = len(egi.E)
                c_count = len(egi.Cut)
            except Exception:
                v_count = e_count = c_count = 0
            src = (
                str(self._current_source_path)
                if getattr(self, "_current_source_path", None)
                else "(none)"
            )
            egdf = getattr(self, "_current_egdf_doc", None)
            has_layout = bool(getattr(egdf, "layout", None)) if egdf else False
            has_styles = bool(getattr(egdf, "styles", None)) if egdf else False
            has_deltas = bool(getattr(egdf, "deltas", None)) if egdf else False
            try:
                self.graph_info_dock.update_info(
                    v_count,
                    e_count,
                    c_count,
                    src,
                    bool(egdf),
                    has_layout,
                    has_styles,
                    has_deltas,
                )
            except Exception:
                pass
            # Update preview if present
            try:
                if hasattr(self, "_update_preview"):
                    self._update_preview()
            except Exception:
                pass

        if not hasattr(self, "_update_graph_info"):
            setattr(self, "_update_graph_info", _update_graph_info_min)

        def _refresh_scene_min():
            try:
                self.clear_scene()
            except Exception:
                pass
            try:
                self._update_graph_info()
            except Exception:
                pass

        if not hasattr(self, "refresh_scene"):
            setattr(self, "refresh_scene", _refresh_scene_min)
        # Initial paint and info using minimal stubs (real implementations defined later in class)
        self.refresh_scene()
        self._update_graph_info()

    # --- Toggle handlers (wired from EGIControlPanel) ---
    def set_show_variable_labels(self, on: bool):
        self._show_variable_labels = bool(on)
        try:
            self.refresh_scene()
        except Exception:
            pass

    def set_show_arity(self, on: bool):
        self._show_arity = bool(on)
        try:
            self.refresh_scene()
        except Exception:
            pass

    # --- Corpus Dock and actions (EGIMainWindow methods) ---
    def _init_corpus_dock(self):
        self.corpus_dock = CorpusDock(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.corpus_dock)
        try:
            self.resizeDocks([self.corpus_dock], [260], Qt.Horizontal)
        except Exception:
            pass
        self._refresh_corpus_list()

    def _refresh_corpus_list(self):
        try:
            entries = cidx.list_entries()
        except Exception:
            entries = []
        try:
            self.corpus_dock.populate(entries)
        except Exception:
            pass

    def on_corpus_new(self):
        gid, ok = QInputDialog.getText(self, "New Graph", "Graph ID:")
        if not ok or not gid.strip():
            return
        title, ok2 = QInputDialog.getText(self, "New Graph", "Title:", text=gid.strip())
        if not ok2:
            return
        try:
            gdir = cidx.create_graph_dir(gid.strip(), title=title.strip())
            egi_path = cidx.graph_paths(gdir)["egi"]
            try:
                self._load_egdf_clear()
            except AttributeError:
                self._current_egdf_doc = None
            _egi_loader_dispatch(self, egi_path)
            self._current_source_path = egi_path
            self._current_graph_dir = gdir
            self.refresh_scene()
            self._refresh_corpus_list()
        except Exception as e:
            try:
                QMessageBox.critical(
                    self, "Corpus Error", f"Failed to create graph directory:\n{e}"
                )
            except Exception:
                pass

    def _open_selected_corpus_action(self):
        try:
            if hasattr(self, "on_corpus_open_selected") and callable(
                getattr(self, "on_corpus_open_selected")
            ):
                return self.on_corpus_open_selected()
        except Exception:
            pass
        return self._inline_open_selected_corpus()

    def _inline_open_selected_corpus(self):
        try:
            entry = None
            if hasattr(self, "corpus_dock") and hasattr(
                self.corpus_dock, "current_entry"
            ):
                entry = self.corpus_dock.current_entry()
            if not entry:
                QMessageBox.information(
                    self, "Corpus", "Select a graph in the Corpus list."
                )
                return
            gdir = (cidx.REPO_ROOT / entry.get("path")).resolve()
            egi_path = cidx.graph_paths(gdir)["egi"]
            if not egi_path.exists():
                raise FileNotFoundError(str(egi_path))
            try:
                self._load_egdf_clear()
            except AttributeError:
                self._current_egdf_doc = None
            _egi_loader_dispatch(self, egi_path)
            self._current_source_path = egi_path
            self._current_graph_dir = gdir
            self.refresh_scene()
        except Exception as e:
            try:
                QMessageBox.critical(
                    self, "Open Error", f"Failed to open selected graph:\n{e}"
                )
            except Exception:
                pass

    def _inline_corpus_new(self):
        # Fallback for creating new graph when on_corpus_new is unavailable
        return self.on_corpus_new()


class CorpusDock(QDockWidget):
    """Dock listing corpus graphs from index.json."""

    def __init__(self, main: "EGIMainWindow"):
        super().__init__("Corpus")
        self._main = main
        self._entries: list[dict] = []
        w = QWidget()
        self.setWidget(w)
        v = QVBoxLayout(w)
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(
            lambda _: (
                getattr(self._main, "_open_selected_corpus_action", (lambda: None))()
            )
        )
        v.addWidget(self.list)
        # minimal footer actions
        btns = QHBoxLayout()
        btn_refresh = QPushButton("Refresh")
        btn_new = QPushButton("New…")
        btn_open = QPushButton("Open Selected")
        btn_refresh.clicked.connect(
            lambda: (getattr(self._main, "_refresh_corpus_list", (lambda: None))())
        )
        btn_new.clicked.connect(
            lambda: (getattr(self._main, "on_corpus_new", (lambda: None))())
        )
        btn_open.clicked.connect(
            lambda: (
                getattr(self._main, "_open_selected_corpus_action", (lambda: None))()
            )
        )
        btns.addWidget(btn_refresh)
        btns.addWidget(btn_new)
        btns.addWidget(btn_open)
        v.addLayout(btns)
        # Make sure the dock has a reasonable initial size
        self.setMinimumWidth(220)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

    def populate(self, entries: list[dict]):
        self._entries = list(entries)
        self.list.clear()
        for e in self._entries:
            title = e.get("title") or e.get("id") or "(untitled)"
            item = QListWidgetItem(title)
            # store index in item for retrieval
            item.setData(Qt.UserRole, e)
            self.list.addItem(item)

    def current_entry(self) -> dict | None:
        it = self.list.currentItem()
        if not it:
            return None
        return it.data(Qt.UserRole)

    # --- Corpus Dock and actions ---
    def _init_corpus_dock(self):
        self.corpus_dock = CorpusDock(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.corpus_dock)
        try:
            # Allocate initial width so it doesn't collapse
            self.resizeDocks([self.corpus_dock], [260], Qt.Horizontal)
        except Exception:
            pass
        self._refresh_corpus_list()

    def _refresh_corpus_list(self):
        try:
            entries = cidx.list_entries()
            self.corpus_dock.populate(entries)
        except Exception:
            self.corpus_dock.populate([])

    def on_corpus_new(self):
        gid, ok = QInputDialog.getText(self, "New Graph", "Graph ID:")
        if not ok or not gid.strip():
            return
        title, ok2 = QInputDialog.getText(self, "New Graph", "Title:", text=gid.strip())
        if not ok2:
            return
        try:
            gdir = cidx.create_graph_dir(gid.strip(), title=title.strip())
            # Load fresh graph
            egi_path = cidx.graph_paths(gdir)["egi"]
            try:
                self._load_egdf_clear()
            except AttributeError:
                self._current_egdf_doc = None
            _egi_loader_dispatch(self, egi_path)
            self._current_source_path = egi_path
            self._current_graph_dir = gdir
            self.refresh_scene()
            self._refresh_corpus_list()
        except Exception as e:
            QMessageBox.critical(
                self, "Corpus Error", f"Failed to create graph directory:\n{e}"
            )

    def on_corpus_open_selected(self):
        entry = self.corpus_dock.current_entry()
        if not entry:
            QMessageBox.information(
                self, "Corpus", "Select a graph in the Corpus list."
            )
            return
        try:
            gdir = (cidx.REPO_ROOT / entry.get("path")).resolve()
            egi_path = cidx.graph_paths(gdir)["egi"]
            if not egi_path.exists():
                raise FileNotFoundError(str(egi_path))
            try:
                self._load_egdf_clear()
            except AttributeError:
                self._current_egdf_doc = None
            _egi_loader_dispatch(self, egi_path)
            self._current_source_path = egi_path
            self._current_graph_dir = gdir
            self.refresh_scene()
        except Exception as e:
            QMessageBox.critical(
                self, "Open Error", f"Failed to open selected graph:\n{e}"
            )

    def _inline_corpus_new(self):
        """Inline fallback for creating a new corpus graph directory and loading it."""
        gid, ok = QInputDialog.getText(self, "New Graph", "Graph ID:")
        if not ok or not gid.strip():
            return
        title, ok2 = QInputDialog.getText(self, "New Graph", "Title:", text=gid.strip())
        if not ok2:
            return
        try:
            gdir = cidx.create_graph_dir(gid.strip(), title=title.strip())
            egi_path = cidx.graph_paths(gdir)["egi"]
            try:
                self._load_egdf_clear()
            except AttributeError:
                self._current_egdf_doc = None
            _egi_loader_dispatch(self, egi_path)
            self._current_source_path = egi_path
            self._current_graph_dir = gdir
            self.refresh_scene()
            self._refresh_corpus_list()
        except Exception as e:
            QMessageBox.critical(
                self, "Corpus Error", f"Failed to create graph directory:\n{e}"
            )

    def _inline_save_egdf_beside(self):
        """Inline fallback for saving EGDF next to the current source file."""
        base: Optional[Path] = self._current_source_path
        if not base:
            QMessageBox.information(
                self,
                "No Source",
                "No source file tracked yet. Open a linear form or EGI JSON first.",
            )
            return
        name = base.name
        if name.endswith(".egi.json"):
            out = base.with_name(name[:-9] + ".egdf.json")
        else:
            out = base.with_name(base.stem + ".egdf.json")
        try:
            doc = self.egi_system.to_egdf()
            # Ensure header integrity similar to corpus save
            egi_norm = self._normalized_egi_dict()
            egi_json = json.dumps(egi_norm, sort_keys=True, separators=(",", ":"))
            egi_checksum = hashlib.sha256(egi_json.encode("utf-8")).hexdigest()
            now_iso = datetime.now(timezone.utc).isoformat()
            header = {
                "version": "0.1",
                "generator": "arisbe",
                "updated": now_iso,
                "egi_checksum": egi_checksum,
            }
            if isinstance(doc, dict):
                if "header" in doc and isinstance(doc["header"], dict):
                    doc["header"].update(header)
                else:
                    doc["header"] = header
            out.write_text(json.dumps(doc, indent=2, sort_keys=False), encoding="utf-8")
            self._last_saved_egdf_path = out
            QMessageBox.information(
                self, "Saved", f"EGDF saved beside source at:\n{out}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save EGDF:\n{e}")

    def _open_selected_corpus_action(self):
        """Dispatcher-safe action for opening the selected corpus entry.
        Falls back to inline logic if on_corpus_open_selected is unavailable.
        """
        try:
            if hasattr(self, "on_corpus_open_selected") and callable(
                getattr(self, "on_corpus_open_selected")
            ):
                return self.on_corpus_open_selected()
            # Fallback behavior
            entry = None
            if hasattr(self, "corpus_dock") and hasattr(
                self.corpus_dock, "current_entry"
            ):
                entry = self.corpus_dock.current_entry()
            if not entry:
                QMessageBox.information(
                    self, "Corpus", "Select a graph in the Corpus list."
                )
                return
            gdir = (cidx.REPO_ROOT / entry.get("path")).resolve()
            egi_path = cidx.graph_paths(gdir)["egi"]
            if not egi_path.exists():
                raise FileNotFoundError(str(egi_path))
            try:
                self._load_egdf_clear()
            except AttributeError:
                self._current_egdf_doc = None
            self._safe_load_egi_json(egi_path)
            self._current_source_path = egi_path
            self._current_graph_dir = gdir
            self.refresh_scene()
        except Exception as e:
            QMessageBox.critical(
                self, "Open Error", f"Failed to open selected graph:\n{e}"
            )

    def _inline_open_selected_corpus(self):
        """Inline fallback used by menu/dock lambdas to open selected corpus entry."""
        try:
            entry = None
            if hasattr(self, "corpus_dock") and hasattr(
                self.corpus_dock, "current_entry"
            ):
                entry = self.corpus_dock.current_entry()
            if not entry:
                QMessageBox.information(
                    self, "Corpus", "Select a graph in the Corpus list."
                )
                return
            gdir = (cidx.REPO_ROOT / entry.get("path")).resolve()
            egi_path = cidx.graph_paths(gdir)["egi"]
            if not egi_path.exists():
                raise FileNotFoundError(str(egi_path))
            try:
                self._load_egdf_clear()
            except AttributeError:
                self._current_egdf_doc = None
            self._safe_load_egi_json(egi_path)
            self._current_source_path = egi_path
            self._current_graph_dir = gdir
            self.refresh_scene()
        except Exception as e:
            QMessageBox.critical(
                self, "Open Error", f"Failed to open selected graph:\n{e}"
            )

    def graph_save_to_corpus(self):
        if not self._current_graph_dir:
            QMessageBox.information(
                self,
                "Corpus",
                "No active corpus graph. Use Graph → New or Open Selected.",
            )
            return
        try:
            egi_norm = self._normalized_egi_dict()
            egi_path = cidx.graph_paths(self._current_graph_dir)["egi"]
            egi_path.write_text(json.dumps(egi_norm, indent=2), encoding="utf-8")
            # update info.json and index timestamp
            info = cidx.read_info(self._current_graph_dir)
            info["title"] = info.get("title") or info.get("id")
            cidx.write_info(self._current_graph_dir, info)
            entry = {
                "id": info.get("id"),
                "title": info.get("title"),
                "category": info.get("category"),
                "tags": info.get("tags", []),
                "path": str(self._current_graph_dir.relative_to(cidx.REPO_ROOT)),
                "updated": datetime.now(timezone.utc).isoformat(),
            }
            cidx.upsert_entry(entry)
            self._current_source_path = egi_path
            self._refresh_corpus_list()
            QMessageBox.information(
                self, "Saved", f"EGI saved to corpus at:\n{egi_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save to corpus:\n{e}")

    def graph_export_tikz_to_corpus(self):
        if not self._current_graph_dir:
            QMessageBox.information(
                self,
                "Corpus",
                "No active corpus graph. Use Graph → New or Open Selected.",
            )
            return
        try:
            scene_data = self.qt_integration.generate_qt_scene()
            cmds = scene_data.get("render_commands", [])
            if not cmds:
                QMessageBox.information(self, "Export", "No render commands to export.")
                return
            tikz_text = generate_tikz(cmds, standalone=True)
            out = cidx.export_path(self._current_graph_dir, "tikz", ext="tex")
            out.write_text(tikz_text, encoding="utf-8")
            QMessageBox.information(
                self, "Export", f"TikZ exported to corpus at:\n{out}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Export Error", f"Failed to export TikZ to corpus:\n{e}"
            )

    def graph_save_egdf_to_corpus(self):
        if not self._current_graph_dir:
            QMessageBox.information(
                self,
                "Corpus",
                "No active corpus graph. Use Graph → New or Open Selected.",
            )
            return
        try:
            doc = self.egi_system.to_egdf()
            # Determine style_id for filename
            style_path = getattr(self.style, "theme_path", "")
            style_id = Path(style_path).stem if style_path else "default"
            out = cidx.egdf_path(self._current_graph_dir, style_id=style_id)
            # Ensure header integrity as in save_egdf_to_sibling
            egi_norm = self._normalized_egi_dict()
            egi_json = json.dumps(egi_norm, sort_keys=True, separators=(",", ":"))
            egi_checksum = hashlib.sha256(egi_json.encode("utf-8")).hexdigest()
            now_iso = datetime.now(timezone.utc).isoformat()
            header = {
                "version": "0.1",
                "generator": "arisbe",
                "updated": now_iso,
                "egi_checksum": egi_checksum,
                "style_id": style_id,
            }
            if isinstance(doc, dict):
                if "header" in doc and isinstance(doc["header"], dict):
                    doc["header"].update(header)
                else:
                    doc["header"] = header
            out.write_text(json.dumps(doc, indent=2, sort_keys=False), encoding="utf-8")
            QMessageBox.information(self, "Saved", f"EGDF saved to corpus at:\n{out}")
        except Exception as e:
            QMessageBox.critical(
                self, "Save Error", f"Failed to save EGDF to corpus:\n{e}"
            )

    def _load_linear_and_refresh(self, text: str, format_hint: str | None = None):
        try:
            self.egi_system.load_linear(text, format_hint)
            self._last_linear_text = text
            self.refresh_scene()
            self._safe_update_chiron_contents()
        except Exception as e:
            QMessageBox.critical(
                self, "Import Error", f"Failed to load linear form: {e}"
            )

    def open_linear_form_file(self):
        """Open a file containing EGIF/CGIF and display it."""
        # Note: both .egif and .cgif supported; also allow any text file
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Open Linear Form",
            "",
            "Linear Forms (*.egif *.cgif *.txt);;All Files (*)",
        )
        if not fname:
            return
        try:
            with open(fname, "r", encoding="utf-8") as f:
                text = f.read()
            # Hint by extension if available
            ext = fname.split(".")[-1].lower() if "." in fname else None
            fmt_hint = "egif" if ext == "egif" else ("cgif" if ext == "cgif" else None)
            self._load_linear_and_refresh(text, fmt_hint)
            # Track source path for sibling saves (base without forcing EGDF name)
            self._current_source_path = Path(fname)
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Failed to read file:\n{e}")

    def open_graph_file(self):
        """Open EGDF (.egdf.json/.egdf.yaml) or EGI (.egi.json) and display it."""
        filt = "EGDF/EGI (*.egdf.json *.egdf.yaml *.egi.json);;All Files (*)"
        fname, _ = QFileDialog.getOpenFileName(self, "Open Graph", "", filt)
        if not fname:
            return
        path = Path(fname)
        try:
            if fname.endswith(".egi.json"):
                try:
                    self._load_egdf_clear()
                except AttributeError:
                    self._current_egdf_doc = None
                _egi_loader_dispatch(self, path)
                self._current_source_path = path
            elif fname.endswith(".egdf.json") or fname.endswith(".egdf.yaml"):
                self._load_egdf_file(path)
                self._current_source_path = path
            else:
                # Fallback: try EGDF JSON first then EGI JSON
                try:
                    self._load_egdf_file(path)
                    self._current_source_path = path
                except Exception:
                    try:
                        self._load_egdf_clear()
                    except AttributeError:
                        self._current_egdf_doc = None
                    _egi_loader_dispatch(self, path)
                    self._current_source_path = path
            self.refresh_scene()
            self._update_chiron_contents()
            self._update_graph_info()
        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Failed to open graph file:\n{e}")

    def reload_current_source(self):
        """Reload last opened EGDF/EGI source from disk (basic)."""
        if not self._current_source_path:
            QMessageBox.information(self, "No Source", "No source file to reload.")
            return
        try:
            path = self._current_source_path
            if str(path).endswith(".egi.json"):
                try:
                    self._load_egdf_clear()
                except AttributeError:
                    self._current_egdf_doc = None
                _egi_loader_dispatch(self, path)
            elif str(path).endswith(".egdf.json") or str(path).endswith(".egdf.yaml"):
                self._load_egdf_file(path)
            else:
                # Try EGDF first then EGI
                try:
                    self._load_egdf_file(path)
                except Exception:
                    try:
                        self._load_egdf_clear()
                    except AttributeError:
                        self._current_egdf_doc = None
                    _egi_loader_dispatch(self, path)
            self.refresh_scene()
            self._update_chiron_contents()
            self._update_graph_info()
        except Exception as e:
            QMessageBox.critical(self, "Reload Error", f"Failed to reload:\n{e}")

    def _on_file_open_menu(self):
        """Robust dispatcher for File→Open to accommodate build variants."""
        try:
            if hasattr(self, "open_graph_file") and callable(
                getattr(self, "open_graph_file")
            ):
                return self.open_graph_file()
            # Fallbacks present in older builds
            if hasattr(self, "open_egi_file") and callable(
                getattr(self, "open_egi_file")
            ):
                return self.open_egi_file()
            if hasattr(self, "open_linear_form_file") and callable(
                getattr(self, "open_linear_form_file")
            ):
                return self.open_linear_form_file()
            QMessageBox.information(
                self, "Open", "No compatible open dialog available in this build."
            )
        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Failed to open:\n{e}")

    def open_egi_file(self):
        """Open an EGI JSON file (<name>.egi.json) and display it."""
        fname, _ = QFileDialog.getOpenFileName(
            self, "Open EGI JSON", "", "EGI JSON (*.egi.json);;All Files (*)"
        )
        if not fname:
            return
        try:
            _egi_loader_dispatch(self, Path(fname))
            self._current_source_path = Path(fname)
            self.refresh_scene()
            self._safe_update_chiron_contents()
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Failed to load EGI JSON:\n{e}")

    def _safe_load_egi_json(self, path: Path) -> None:
        """Load EGI JSON from path. Canonical loader used across call paths."""
        data = json.loads(path.read_text(encoding="utf-8"))
        sheet: str = data.get("sheet") or "sheet"
        V = []
        for v in data.get("V", []):
            vid = v.get("id")
            if not vid:
                continue
            V.append(
                Vertex(
                    id=vid,
                    label=v.get("label"),
                    is_generic=bool(v.get("is_generic", True)),
                )
            )
        E = [Edge(id=e.get("id")) for e in data.get("E", []) if e.get("id")]
        CutSet = [Cut(id=c.get("id")) for c in data.get("Cut", []) if c.get("id")]
        nu = frozendict({k: tuple(v) for k, v in (data.get("nu") or {}).items()})
        rel = frozendict(dict(data.get("rel") or {}))
        area = frozendict(
            {k: frozenset(v) for k, v in (data.get("area") or {}).items()}
        )
        rho = frozendict(dict(data.get("rho") or {}))
        alph_data = data.get("alphabet")
        if alph_data:
            alph = AlphabetDAU(
                C=frozenset(alph_data.get("C") or []),
                F=frozenset(alph_data.get("F") or []),
                R=frozenset(alph_data.get("R") or []),
                ar=frozendict(alph_data.get("ar") or {}),
            ).with_defaults()
        else:
            alph = AlphabetDAU().with_defaults()
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
        self.egi_system.replace_egi(graph)

    def _load_egi_json(self, path: Path) -> None:
        """Legacy alias. Delegates to the canonical loader."""
        return self._safe_load_egi_json(path)

    def load_egi_json(self, path: Path) -> None:
        """Public API: Load EGI JSON from a file path."""
        return self._safe_load_egi_json(path)

    def _load_egi_dispatch(self, path: Path) -> None:
        """Dispatch to whichever EGI JSON loader exists on this build.
        Tries public API then safe/legacy names for maximum compatibility.
        """
        for name in ("load_egi_json", "_safe_load_egi_json", "_load_egi_json"):
            fn = getattr(self, name, None)
            if callable(fn):
                return fn(path)
        raise AttributeError(
            "No EGI JSON loader available on this EGIMainWindow instance"
        )

    def _load_egi_inline_dict(self, inline: Dict[str, Any]) -> None:
        """Load an EGI object from an EGDF egi_ref.inline dict."""
        # Map inline schema to RelationalGraphWithCuts
        sheet: str = inline.get("sheet") or "sheet"
        V = []
        for vid in inline.get("V", []):
            # Inline schema uses list of vertex IDs; labels and generics are in rho if needed
            # We assume constants are labeled via rho and non-generic via rho != None
            label = inline.get("rho", {}).get(vid)
            # If label is None, treat as generic variable
            is_generic = True if label is None else False
            V.append(Vertex(id=vid, label=label, is_generic=is_generic))
        E = [Edge(id=eid) for eid in inline.get("E", [])]
        CutSet = [Cut(id=cid) for cid in inline.get("Cut", [])]
        nu = frozendict({k: tuple(v) for k, v in (inline.get("nu") or {}).items()})
        rel = frozendict(dict(inline.get("rel") or {}))
        area = frozendict(
            {k: frozenset(v) for k, v in (inline.get("area") or {}).items()}
        )
        rho = frozendict(dict(inline.get("rho") or {}))
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
        self.egi_system.replace_egi(graph)

    def _load_egdf_clear(self) -> None:
        """Clear current EGDF document state (but keep EGI)."""
        self._current_egdf_doc = None

    def _load_egdf_file(self, path: Path) -> None:
        """Parse EGDF (JSON or YAML) and load its inline EGI into the system, keeping doc in memory."""
        text = path.read_text(encoding="utf-8")
        if str(path).endswith(".yaml") or str(path).endswith(".yml"):
            doc = EGDFDocument.from_yaml(text)
        else:
            doc = EGDFDocument.from_json(text)
        # Prefer inline EGI for deterministic loading
        egi_ref = doc.egi_ref
        inline = egi_ref.get("inline") if isinstance(egi_ref, dict) else None
        if not inline:
            raise ValueError(
                "EGDF egi_ref.inline missing; external uri not supported here"
            )
        # Load graph and retain EGDF
        self._load_egi_inline_dict(inline)
        self._current_egdf_doc = doc
        self._update_graph_info()

    def save_egdf_to_sibling(self):
        """Save current EGI's EGDF document as <basename>.egdf.json next to current source."""
        base: Optional[Path] = self._current_source_path
        if not base:
            QMessageBox.information(
                self,
                "No Source",
                "No source file tracked yet. Open a linear form or EGI JSON first.",
            )
            return
        # Compute sibling path: if source endswith .egi.json, replace with .egdf.json; else append .egdf.json
        name = base.name
        if name.endswith(".egi.json"):
            out = base.with_name(name[:-9] + ".egdf.json")
        else:
            stem = base.stem
            out = base.with_name(stem + ".egdf.json")
        try:
            doc = self.egi_system.to_egdf()
            # Compose header with integrity and reproducibility
            egi_norm = self._normalized_egi_dict()
            egi_json = json.dumps(egi_norm, sort_keys=True, separators=(",", ":"))
            egi_checksum = hashlib.sha256(egi_json.encode("utf-8")).hexdigest()
            style_path = getattr(self.style, "theme_path", "")
            style_id = Path(style_path).stem if style_path else "default"
            now_iso = datetime.now(timezone.utc).isoformat()
            header = {
                "version": "0.1",
                "generator": "arisbe",
                "updated": now_iso,
                "egi_checksum": egi_checksum,
                "style_id": style_id,
            }
            # Inject or update header
            if isinstance(doc, dict):
                if "header" in doc and isinstance(doc["header"], dict):
                    doc["header"].update(header)
                else:
                    doc["header"] = header
            out.write_text(json.dumps(doc, indent=2, sort_keys=False), encoding="utf-8")
            self._last_saved_egdf_path = out
            QMessageBox.information(self, "Saved", f"EGDF saved to:\n{out}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save EGDF:\n{e}")

    def _normalized_egi_dict(self) -> Dict[str, Any]:
        """Produce a stable JSON-able dict of current EGI for checksumming.
        Mirrors tools/migrate_corpus_to_egi.py::egi_to_dict ordering.
        """
        egi = self.egi_system.get_egi()

        def _sorted_set(iterable):
            return sorted(list(iterable))

        payload: Dict[str, Any] = {
            "sheet": egi.sheet,
            "V": [
                {"id": v.id, "label": v.label, "is_generic": v.is_generic}
                for v in sorted(egi.V, key=lambda x: x.id)
            ],
            "E": [{"id": e.id} for e in sorted(egi.E, key=lambda x: x.id)],
            "Cut": [{"id": c.id} for c in sorted(egi.Cut, key=lambda x: x.id)],
            "nu": {k: list(v) for k, v in sorted(egi.nu.items())},
            "rel": dict(sorted(egi.rel.items())),
            "area": {k: _sorted_set(v) for k, v in sorted(egi.area.items())},
            "alphabet": (
                None
                if egi.alphabet is None
                else {
                    "C": _sorted_set(egi.alphabet.C),
                    "F": _sorted_set(egi.alphabet.F),
                    "R": _sorted_set(egi.alphabet.R),
                    "ar": dict(egi.alphabet.ar),
                }
            ),
            "rho": {k: v for k, v in sorted(egi.rho.items())},
        }
        return payload

    def paste_linear_form(self):
        """Paste EGIF/CGIF text and display it."""
        text, ok = QInputDialog.getMultiLineText(
            self, "Paste Linear Form", "Enter EGIF or CGIF:"
        )
        if not ok or not text.strip():
            return
        self._load_linear_and_refresh(text, None)

    def igi_seed(self) -> EGISystem:
        """Return EGI system for integration (helper for decoupled construction)."""
        return self.egi_system

    def seed_demo_graph(self):
        """Populate a small demo graph: Person(Tom), Happy(Tom), and a cut."""
        self.egi_system.insert_vertex("Tom")
        self.egi_system.insert_edge("e1", "Person", ["Tom"])
        self.egi_system.insert_edge("e2", "Happy", ["Tom"])
        self.egi_system.insert_cut("cut_1")

    def clear_scene(self):
        self.scene.clear()
        self._items_by_element.clear()
        self._selected_id = None

    def refresh_scene(self):
        self.clear_scene()
        # Regenerate integration each refresh to reflect current EGI
        self.qt_integration = create_qt_correspondence_integration(self.egi_system)
        scene_data = self.qt_integration.generate_qt_scene()
        # If showing variable labels, compute EGIF variable label mapping for current EGI
        self._vertex_var_labels = {}
        if self._show_variable_labels:
            try:
                from egif_generator_dau import EGIFGenerator

                gen = EGIFGenerator(self.egi_system.get_egi())
                # generate() assigns labels internally
                _ = gen.generate()
                self._vertex_var_labels = dict(gen.vertex_labels)
            except Exception:
                self._vertex_var_labels = {}
        # Emit items if emitter is available; avoid crash in legacy builds
        emitter = getattr(self, "_emit_command", None)
        if callable(emitter):
            for cmd in scene_data.get("render_commands", []):
                emitter(cmd)
        else:
            # No emitter available; draw directly into the QGraphicsScene (minimal fallback)
            cmds = scene_data.get("render_commands", [])

            def _register(it, eid: str, etype: str):
                try:
                    it.setData(0, eid)
                    it.setData(1, etype)
                except Exception:
                    pass
                try:
                    self._items_by_element[eid].append(it)
                except Exception:
                    pass
                try:
                    self.scene.addItem(it)
                except Exception:
                    pass

            for cmd in cmds:
                etype = str(cmd.get("type", ""))
                eid = str(cmd.get("element_id", ""))
                b = cmd.get("bounds", {}) or {}
                x = float(b.get("x", 0.0))
                y = float(b.get("y", 0.0))
                w = float(b.get("width", 0.0))
                h = float(b.get("height", 0.0))
                try:
                    if etype == "vertex":
                        # Draw a dot for the vertex
                        r = max(4.0, min(w, h, 8.0))
                        cx, cy = x + w / 2.0, y + h / 2.0
                        dot = BranchingPointItem(cx, cy, r)
                        _register(dot, eid, "vertex")
                        # Optional superscript label for variable name
                        if self._show_variable_labels:
                            label = self._vertex_var_labels.get(eid)
                            if label:
                                sup = cmd.get("vertex_sup_bounds") or {}
                                sx = float(sup.get("x", cx + 8.0))
                                sy = float(sup.get("y", cy - 8.0))
                                txt = QGraphicsTextItem(label)
                                txt.setDefaultTextColor(QColor(80, 80, 80))
                                txt.setPos(sx, sy)
                                _register(txt, eid, "vertex_label")
                    elif etype == "edge":
                        # Draw relation label box as text centered in bounds
                        rel = cmd.get("relation_name") or "?"
                        cx, cy = x + w / 2.0, y + h / 2.0
                        lbl = PredicateItem(str(rel), cx, cy)
                        _register(lbl, eid, "edge")
                        # Optional arity superscript
                        if self._show_arity and "edge_sup_bounds" in cmd:
                            sup = cmd.get("edge_sup_bounds") or {}
                            sx = float(sup.get("x", cx + 8.0))
                            sy = float(sup.get("y", cy - 8.0))
                            arity = None
                            try:
                                arity = self.egi_system.get_egi().alphabet.ar.get(rel)
                            except Exception:
                                arity = None
                            if arity is not None:
                                txt = QGraphicsTextItem(f"/{arity}")
                                txt.setDefaultTextColor(QColor(80, 80, 80))
                                txt.setPos(sx, sy)
                                _register(txt, eid, "edge_arity")
                    elif etype == "cut":
                        rect = CutItem(x, y, max(1.0, w), max(1.0, h))
                        # Shade parity=1 areas lightly
                        if int(cmd.get("area_parity", 0)) % 2 == 1:
                            rect.setBrush(QBrush(QColor(240, 240, 240, 60)))
                        else:
                            rect.setBrush(QBrush(QColor(255, 255, 255, 0)))
                        _register(rect, eid, "cut")
                    elif etype == "ligature":
                        pts = cmd.get("path_points") or []
                        if isinstance(pts, list) and len(pts) >= 2:
                            for i in range(len(pts) - 1):
                                (x1, y1) = pts[i]
                                (x2, y2) = pts[i + 1]
                                line = QGraphicsLineItem(
                                    QLineF(float(x1), float(y1), float(x2), float(y2))
                                )
                                line.setPen(QPen(QColor(0, 0, 0), 1))
                                _register(line, eid, "ligature")
                        # else: ignore empty path
                except Exception:
                    # Keep going on per-item failures
                    continue
        # Keep graph info synced
        self._update_graph_info()

    def _safe_update_chiron_contents(self):
        """Safely update Chiron dock contents if the dock has been initialized."""
        try:
            # Ensure attributes exist before calling
            if hasattr(self, "_update_chiron_contents") and hasattr(
                self, "chiron_left"
            ):
                self._update_chiron_contents()
        except Exception:
            pass

    def export_tikz(self):
        """Export current scene render commands to a TikZ .tex file."""
        try:
            scene_data = self.qt_integration.generate_qt_scene()
            cmds = scene_data.get("render_commands", [])
            if not cmds:
                QMessageBox.information(self, "Export", "No render commands to export.")
                return
            tikz_text = generate_tikz(cmds, standalone=True)

            # Propose default path next to current source
            default_name = "diagram.tex"
            if self._current_source_path:
                stem = self._current_source_path.stem
                # If source like name.egi.json or name.egdf.json, normalize to name
                if stem.endswith(".egi"):
                    stem = stem[:-4]
                elif stem.endswith(".egdf"):
                    stem = stem[:-5]
                default_name = str(self._current_source_path.with_name(f"{stem}.tex"))

            fname, _ = QFileDialog.getSaveFileName(
                self, "Export TikZ", default_name, "LaTeX (*.tex);;All Files (*)"
            )
            if not fname:
                return
            Path(fname).write_text(tikz_text, encoding="utf-8")
            QMessageBox.information(self, "Export", f"TikZ exported to:\n{fname}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export TikZ:\n{e}")

    # --- Graph Info ---
    def _update_graph_info(self):
        try:
            egi = self.egi_system.get_egi()
            v_count = len(egi.V)
            e_count = len(egi.E)
            c_count = len(egi.Cut)
        except Exception:
            v_count = e_count = c_count = 0
        src = str(self._current_source_path) if self._current_source_path else "(none)"
        egdf = self._current_egdf_doc
        has_layout = bool(getattr(egdf, "layout", None)) if egdf else False
        has_styles = bool(getattr(egdf, "styles", None)) if egdf else False
        has_deltas = bool(getattr(egdf, "deltas", None)) if egdf else False
        self.graph_info_dock.update_info(
            v_count,
            e_count,
            c_count,
            src,
            bool(egdf),
            has_layout,
            has_styles,
            has_deltas,
        )

    def on_open_in_ergasterion(self):
        """In-app handoff: emit payload and let unified app switch to Ergasterion tab."""
        try:
            payload = self._build_ergasterion_payload()
            self.edit_in_ergasterion.emit(payload)
        except Exception as e:
            QMessageBox.critical(
                self, "Handoff Error", f"Failed to prepare Ergasterion payload:\n{e}"
            )

    def _build_ergasterion_payload(self) -> Dict[str, Any]:
        """Compose a stable payload for Ergasterion and the Organon preview."""
        # Build EGI payload (normalized inline dict)
        egi_inline = self._normalized_egi_dict()
        # If we have an EGDF document in memory, include its dict form
        egdf_doc = None
        if self._current_egdf_doc is not None:
            try:
                egdf_doc = self._current_egdf_doc.to_dict()
            except Exception:
                egdf_doc = None
        # Determine mode
        mode = "locked" if egdf_doc else "puzzle"
        # Style identifier if available
        style_path = getattr(self.style, "theme_path", "")
        style_id = Path(style_path).stem if style_path else "default"
        payload: Dict[str, Any] = {
            "source_path": (
                str(self._current_source_path) if self._current_source_path else ""
            ),
            "egi": egi_inline,
            "egdf": egdf_doc,
            "mode": mode,
            "style_id": style_id,
        }
        return payload

    def _update_preview(self) -> None:
        """Push current payload into embedded preview if available."""
        try:
            if (
                hasattr(self, "preview_dock")
                and getattr(self, "preview_dock", None) is not None
            ):
                try:
                    self.preview_dock.load_from_main()
                except Exception:
                    pass
        except Exception:
            pass


class GraphInfoDock(QDockWidget):
    """Dock showing graph metadata, source, EGDF flags, and quick actions."""

    def __init__(self, main: "EGIMainWindow"):
        super().__init__("Graph Info")
        self._main = main
        w = QWidget()
        self.setWidget(w)
        v = QVBoxLayout(w)

        form = QFormLayout()
        self.lbl_counts = QLabel("V: 0  E: 0  Cut: 0")
        self.lbl_source = QLabel("(none)")
        self.lbl_flags = QLabel("EGDF: no | layout: no | styles: no | deltas: no")
        form.addRow("Counts:", self.lbl_counts)
        form.addRow("Source:", self.lbl_source)
        form.addRow("Flags:", self.lbl_flags)
        # Diagnostics: show whether handoff hooks are present on main
        try:
            has_handoff = hasattr(self._main, "on_open_in_ergasterion")
            has_signal = hasattr(self._main, "edit_in_ergasterion")
            self.lbl_diag = QLabel(
                f"handoff: {'yes' if has_handoff else 'no'} | signal: {'yes' if has_signal else 'no'}"
            )
            form.addRow("Diag:", self.lbl_diag)
        except Exception:
            pass
        v.addLayout(form)

        # Actions row
        btns = QHBoxLayout()
        btn_open = QPushButton("Open in Ergasterion")
        # Route through a small helper to emit debug to stdout if unavailable
        btn_open.clicked.connect(self._on_open_clicked)
        btn_reload = QPushButton("Reload")
        btn_reload.clicked.connect(
            lambda: (
                getattr(
                    self._main,
                    "reload_current_source",
                    lambda: QMessageBox.information(
                        self._main, "No Source", "No source file to reload."
                    ),
                )()
            )
        )
        btn_save = QPushButton("Save As EGDF…")
        btn_save.clicked.connect(
            lambda: (
                getattr(
                    self._main,
                    "save_egdf_to_sibling",
                    lambda: QMessageBox.information(
                        self._main, "Save", "Save EGDF beside source not available."
                    ),
                )()
            )
        )
        btns.addWidget(btn_open)
        btns.addWidget(btn_reload)
        btns.addWidget(btn_save)
        v.addLayout(btns)
        v.addStretch()

    def _on_open_clicked(self):
        try:
            has_handoff = hasattr(self._main, "on_open_in_ergasterion")
            has_signal = hasattr(self._main, "edit_in_ergasterion")
            try:
                print(
                    f"[GraphInfoDock] Open clicked | handoff:{has_handoff} signal:{has_signal} main_cls:{type(self._main).__name__}"
                )
            except Exception:
                pass
            if has_handoff:
                return self._main.on_open_in_ergasterion()
            else:
                QMessageBox.information(
                    self._main, "Ergasterion", "Handoff not available."
                )
        except Exception as e:
            try:
                QMessageBox.critical(self._main, "Ergasterion", f"Open failed: {e}")
            except Exception:
                pass

    def update_info(
        self,
        v_count: int,
        e_count: int,
        c_count: int,
        source: str,
        has_egdf: bool,
        has_layout: bool,
        has_styles: bool,
        has_deltas: bool,
    ):
        try:
            self.lbl_counts.setText(f"V: {v_count}  E: {e_count}  Cut: {c_count}")
            self.lbl_source.setText(source)
            self.lbl_flags.setText(
                f"EGDF: {'yes' if has_egdf else 'no'} | layout: {'yes' if has_layout else 'no'} | styles: {'yes' if has_styles else 'no'} | deltas: {'yes' if has_deltas else 'no'}"
            )
        except Exception:
            pass

    # (toggle handlers belong to EGIMainWindow; moved there)

    def _register_item(self, element_id: str, element_type: str, item: Any):
        try:
            item.setData(0, element_id)
            item.setData(1, element_type)
        except Exception:
            pass
        self._items_by_element[element_id].append(item)

    def _set_item_highlight(self, item: Any, element_type: str, on: bool):
        # Apply style tokens from StyleManager using selected/normal states
        from PySide6.QtGui import QBrush, QColor, QPen

        try:
            role_map = {
                "vertex": "vertex.dot",
                "edge": "edge.label_box",
                "ligature": "ligature.arm",
                "cut": "cut.border",
            }
            role = role_map.get(element_type, element_type)
            tokens = self.style.resolve(
                type=element_type, role=role, state=("selected" if on else None)
            )

            # Pens
            pen_color = QColor(
                tokens.get("line_color", tokens.get("border_color", "#000000"))
            )
            pen_w = float(tokens.get("line_width", tokens.get("border_width", 1)))
            if hasattr(item, "setPen"):
                item.setPen(QPen(pen_color, pen_w))

            # Brushes (do not change cut fill on selection; spec says border emphasis only)
            if element_type != "cut" and hasattr(item, "setBrush"):
                brush_color = tokens.get("fill_color")
                if brush_color:
                    item.setBrush(QBrush(QColor(brush_color)))
        except Exception:
            pass

    def clear_highlight(self):
        if not self._selected_ids:
            return
        # Turn off highlight for all previously selected element IDs
        for sid in list(self._selected_ids):
            for it in self._items_by_element.get(sid, []):
                etype = it.data(1) if hasattr(it, "data") else None
                if etype:
                    self._set_item_highlight(it, str(etype), False)
        self._selected_ids.clear()
        self._selected_id = None

    def select_element(self, element_id: str):
        # If clicking same seed element again, no-op
        if element_id == self._selected_id:
            return
        # Clear any existing selection highlights
        self.clear_highlight()

        # Compute connected subgraph IDs and apply highlight to all
        connected_ids = self._compute_connected_ids(element_id)
        for sid in connected_ids:
            for it in self._items_by_element.get(sid, []):
                etype = it.data(1) if hasattr(it, "data") else None
                if etype:
                    self._set_item_highlight(it, str(etype), True)
        # Track selection state
        self._selected_ids = connected_ids
        self._selected_id = element_id

    def clear_hover(self):
        if not self._hover_id:
            return
        for it in self._items_by_element.get(self._hover_id, []):
            etype = it.data(1) if hasattr(it, "data") else None
            if etype:
                # turn off hover by reapplying selected state if selected, else normal
                is_selected = self._selected_id == self._hover_id
                self._set_item_highlight(it, str(etype), is_selected)
        self._hover_id = None

    def hover_element(self, element_id: str):
        if element_id == self._hover_id:
            return
        # clear prior hover
        self.clear_hover()
        # apply hover style only if not selected (selected takes precedence)
        for it in self._items_by_element.get(element_id, []):
            etype = it.data(1) if hasattr(it, "data") else None
            if not etype:
                continue
            if self._selected_id == element_id or element_id in self._selected_ids:
                # keep selected styling
                self._set_item_highlight(it, str(etype), True)
            else:
                # apply hover tokens
                self._apply_item_state(it, str(etype), state="hover")
        self._hover_id = element_id

    def _apply_item_state(self, item: Any, element_type: str, state: str | None):
        from PySide6.QtGui import QBrush, QColor, QPen

        role_map = {
            "vertex": "vertex.dot",
            "edge": "edge.label_box",
            "ligature": "ligature.arm",
            "cut": "cut.border",
        }
        role = role_map.get(element_type, element_type)
        tokens = self.style.resolve(type=element_type, role=role, state=state)
        pen_color = QColor(
            tokens.get("line_color", tokens.get("border_color", "#000000"))
        )
        pen_w = float(tokens.get("line_width", tokens.get("border_width", 1)))
        if hasattr(item, "setPen"):
            item.setPen(QPen(pen_color, pen_w))
        if element_type != "cut" and hasattr(item, "setBrush"):
            brush_color = tokens.get("fill_color")
            if brush_color:
                item.setBrush(QBrush(QColor(brush_color)))

    def _compute_connected_ids(self, element_id: str) -> set[str]:
        """Compute the connected subgraph per Dau formalism.
        - If seed is a cut: include the cut and all elements in its full context (recursive area).
        - If seed is an edge: include edge + all incident vertices, then expand via incident edges of those vertices (bipartite walk), staying within same context.
        - If seed is a vertex: symmetric to edge case.
        """
        egi = self.egi_system.get_egi()
        connected: set[str] = set()

        # Identify type of seed
        v_ids = {v.id for v in egi.V}
        e_ids = {e.id for e in egi.E}
        c_ids = {c.id for c in egi.Cut}

        # Cut: take full context contents plus the cut itself
        if element_id in c_ids:
            connected.update(egi.get_full_context(element_id))
            connected.add(element_id)
            return connected

        # Build reverse adjacency: vertex -> incident edges
        vertex_to_edges: dict[str, list[str]] = {}
        for edge_id, vseq in egi.nu.items():
            for vid in vseq:
                vertex_to_edges.setdefault(vid, []).append(edge_id)

        # Determine starting frontier
        frontier: list[str] = [element_id]
        seed_ctx = None
        try:
            seed_ctx = egi.get_context(element_id)
        except Exception:
            pass

        while frontier:
            eid = frontier.pop()
            if eid in connected:
                continue
            connected.add(eid)

            # Keep traversal within the same direct context when available
            def same_ctx(xid: str) -> bool:
                if seed_ctx is None:
                    return True
                try:
                    return egi.get_context(xid) == seed_ctx
                except Exception:
                    return True

            if eid in v_ids:
                # From vertex to its incident edges
                for neigh_e in vertex_to_edges.get(eid, []):
                    if neigh_e not in connected and same_ctx(neigh_e):
                        frontier.append(neigh_e)
            elif eid in e_ids:
                # From edge to its incident vertices
                for neigh_v in egi.nu.get(eid, ()):  # tuple of vertex IDs
                    if neigh_v not in connected and same_ctx(neigh_v):
                        frontier.append(neigh_v)

        return connected

    def _emit_command(self, cmd: Dict[str, Any]):
        typ = cmd.get("type")
        role = cmd.get("role")
        b = cmd.get("bounds", {})
        x, y, w, h = (
            b.get("x", 0.0),
            b.get("y", 0.0),
            b.get("width", 0.0),
            b.get("height", 0.0),
        )

        if typ == "vertex":
            # Draw small spot and label
            s = self.style.resolve(type="vertex", role=role)
            radius = float(s.get("radius", 3))
            fill = _qcolor(s.get("fill_color", "#000000"))
            border_color = _qcolor(s.get("border_color", "#000000"))
            border_w = float(s.get("border_width", 1))
            vid = cmd.get("element_id", "")
            v_center_x, v_center_y = x + w / 2, y + h / 2

            # Determine constant rendering mode
            vobj = None
            try:
                vobj = self.egi_system.get_egi().get_vertex(vid)
            except Exception:
                vobj = None
            constant_mode = "spot_label"
            if vobj is not None and not getattr(vobj, "is_generic", True):
                vconst = self.style.resolve(type="vertex", role="vertex.constant")
                constant_mode = str(vconst.get("mode", "spot_label")).lower()

            drew_spot = False
            if not (
                vobj is not None
                and not getattr(vobj, "is_generic", True)
                and constant_mode == "label_only"
            ):
                # Draw spot for generic or constant in spot_label mode
                spot = QGraphicsEllipseItem(
                    v_center_x - radius, v_center_y - radius, 2 * radius, 2 * radius
                )
                spot.setBrush(QBrush(fill))
                spot.setPen(QPen(border_color, border_w))
                self.scene.addItem(spot)
                spot.setZValue(10)
                self._register_item(vid, "vertex", spot)
                try:
                    spot.setData(2, "vertex.dot")
                except Exception:
                    pass
                drew_spot = True
            # Optional vertex label rendering (variable superscript or constant label)
            try:
                label_text: str | None = None
                if vobj.is_generic:
                    if self._show_variable_labels:
                        label_text = self._vertex_var_labels.get(vid)
                else:
                    # Constant vertex: always show its name
                    label_text = vobj.label or None
                if label_text:
                    # For generic variable labels, prefer superscript styling and bounds from engine
                    sup_b = cmd.get("vertex_sup_bounds") if vobj.is_generic else None
                    role_for_style = (
                        "vertex.superscript_text"
                        if vobj.is_generic
                        else "vertex.label_text"
                    )
                    tstyle = self.style.resolve(type="vertex", role=role_for_style)
                    font_family = tstyle.get("font_family", "Arial")
                    base_sz = int(
                        tstyle.get("font_size", tstyle.get("estimate_height", 12))
                    )
                    font_size = base_sz
                    vtext = QGraphicsTextItem(str(label_text))
                    vtext.setFont(QFont(font_family, font_size))
                    # Apply text color if provided
                    try:
                        color = tstyle.get("color")
                        if color:
                            from PySide6.QtGui import QColor as _QColor

                            vtext.setDefaultTextColor(_QColor(color))
                    except Exception:
                        pass
                    if sup_b and isinstance(sup_b, dict):
                        # Engine provided collision-avoided placement
                        sx, sy = float(sup_b.get("x", x)), float(sup_b.get("y", y))
                        vtext.setPos(sx, sy)
                    else:
                        # Fallback offset near the dot
                        tx_off, ty_off = 0.0, 0.0
                        try:
                            off = tstyle.get("offset", [-18, -16])
                            tx_off, ty_off = float(off[0]), float(off[1])
                        except Exception:
                            pass
                        cx, cy = x + w / 2, y + h / 2
                        vtext.setPos(cx + tx_off, cy + ty_off)
                    # Position text: for constant label_only, center on vertex; else offset from spot
                    if (
                        vobj is not None
                        and not getattr(vobj, "is_generic", True)
                        and constant_mode == "label_only"
                    ):
                        # Center text on the vertex center
                        rect = vtext.boundingRect()
                        vtext.setPos(
                            v_center_x - rect.width() / 2,
                            v_center_y - rect.height() / 2,
                        )
                    self.scene.addItem(vtext)
                    vtext.setZValue(11)
                    self._register_item(vid, "vertex", vtext)
                    try:
                        vtext.setData(2, "vertex.label")
                    except Exception:
                        pass
            except Exception:
                pass
        elif typ == "edge":
            # Draw predicate background exactly matching engine-provided bounds with thin border
            ap = int(cmd.get("area_parity", 0))
            parity_role = "edge.fill.odd" if ap == 1 else "edge.fill.even"
            s = self.style.resolve(type="edge", role=parity_role)
            border_color = _qcolor(s.get("border_color", "transparent"))
            border_w = float(s.get("border_width", 0))
            fill_color = _qcolor(s.get("fill_color", "transparent"))
            bg = QGraphicsRectItem(x, y, w, h)
            bg.setPen(QPen(border_color, border_w))
            bg.setBrush(QBrush(fill_color))
            self.scene.addItem(bg)
            bg.setZValue(6)
            self._register_item(cmd.get("element_id", ""), "edge", bg)

            # Center predicate name within the rectangle (no arity appended)
            label_txt = cmd.get("relation_name", "")
            text = QGraphicsTextItem(label_txt)
            g = self.style.resolve(type="edge", role="edge.label_text")
            text.setFont(
                QFont(g.get("font_family", "Arial"), int(g.get("font_size", 10)))
            )
            rect = text.boundingRect()
            tx = x + (w - rect.width()) / 2
            ty = y + (h - rect.height()) / 2
            text.setPos(tx, ty)
            self.scene.addItem(text)
            text.setZValue(7)
            self._register_item(cmd.get("element_id", ""), "edge", text)

            # Optional arity superscript as a small separate text near top-right
            if self._show_arity:
                try:
                    sup_b = cmd.get("edge_sup_bounds")
                    if sup_b and isinstance(sup_b, dict):
                        egi = self.egi_system.get_egi()
                        arity = len(
                            egi.get_incident_vertices(cmd.get("element_id", ""))
                        )
                        sup_txt = f"/{arity}"
                        sstyle = self.style.resolve(
                            type="edge", role="edge.superscript_text"
                        )
                        sfam = sstyle.get("font_family", g.get("font_family", "Arial"))
                        ss = int(
                            sstyle.get(
                                "font_size", max(8, int(g.get("font_size", 10)) - 2)
                            )
                        )
                        sup_item = QGraphicsTextItem(sup_txt)
                        sup_item.setFont(QFont(sfam, ss))
                        # Apply text color if provided
                        try:
                            color = sstyle.get("color")
                            if color:
                                from PySide6.QtGui import QColor as _QColor

                                sup_item.setDefaultTextColor(_QColor(color))
                        except Exception:
                            pass
                        sup_item.setPos(
                            float(sup_b.get("x", x + w)), float(sup_b.get("y", y))
                        )
                        self.scene.addItem(sup_item)
                        sup_item.setZValue(8)
                        self._register_item(cmd.get("element_id", ""), "edge", sup_item)
                except Exception:
                    pass
        elif typ == "cut":
            # Rounded rectangle cut
            s_border = self.style.resolve(type="cut", role=role)
            ap = int(cmd.get("area_parity", 0))
            s_fill = self.style.resolve(
                type="cut", role=("cut.fill.odd" if ap == 1 else "cut.fill.even")
            )
            line_color = _qcolor(s_border.get("line_color", "#000000"))
            line_w = float(s_border.get("line_width", 1))
            radius = float(s_border.get("radius", 10))
            fill_color = _qcolor(s_fill.get("fill_color", "transparent"))
            path = QPainterPath()
            path.addRoundedRect(QRectF(x, y, w, h), radius, radius)
            path_item = self.scene.addPath(
                path, QPen(line_color, line_w), QBrush(fill_color)
            )
            path_item.setZValue(-1)
            self._register_item(cmd.get("element_id", ""), "cut", path_item)
        elif typ == "ligature":
            pts = cmd.get("path_points", []) or []
            if len(pts) >= 2:
                # Resolve style (edge.identity fallback -> ligature.arm)
                s = self.style.resolve(
                    type="edge", role="edge.identity"
                ) or self.style.resolve(type="ligature", role=role)
                line_color = _qcolor(s.get("line_color", "#000000"))
                line_w = float(s.get("line_width", 3))

                # Ensure thicker than cuts
                s_cut = self.style.resolve(type="cut", role="cut.border") or {}
                cut_w = float(s_cut.get("line_width", 1))
                if line_w <= cut_w:
                    line_w = cut_w + 1.0

                # Pen config
                pen = QPen(line_color, line_w)
                try:
                    from PySide6.QtCore import Qt as QtCoreQt

                    # Cap from command override or style
                    cap_val = (cmd.get("cap") or s.get("cap", "round")).lower()
                    if cap_val == "round":
                        pen.setCapStyle(QtCoreQt.PenCapStyle.RoundCap)
                    elif cap_val == "square":
                        pen.setCapStyle(QtCoreQt.PenCapStyle.SquareCap)
                    else:
                        pen.setCapStyle(QtCoreQt.PenCapStyle.FlatCap)
                    join_val = (cmd.get("join") or s.get("join", "round")).lower()
                    if join_val == "round":
                        pen.setJoinStyle(QtCoreQt.PenJoinStyle.RoundJoin)
                    elif join_val == "miter":
                        pen.setJoinStyle(QtCoreQt.PenJoinStyle.MiterJoin)
                    else:
                        pen.setJoinStyle(QtCoreQt.PenJoinStyle.BevelJoin)
                    # Dash from stroke or style
                    stroke = (cmd.get("stroke") or s.get("stroke", "solid")).lower()
                    if stroke == "dashed":
                        dash = s.get("dash") or [6, 3]
                        pen.setDashPattern([float(d) for d in dash])
                except Exception:
                    pass

                # Build path based on style
                path_style = (
                    cmd.get("path_style") or s.get("path_style", "straight")
                ).lower()
                smooth_r = float(
                    cmd.get("smooth_radius", s.get("smooth_radius", 0)) or 0
                )
                zig_amp = cmd.get("zigzag_amp", s.get("zigzag_amp"))
                zig_per = cmd.get("zigzag_period", s.get("zigzag_period"))

                def _polyline_to_path(points):
                    # Build a continuous path, skipping consecutive duplicate points
                    p = QPainterPath()
                    if not points:
                        return p
                    lx, ly = points[0]
                    p.moveTo(lx, ly)
                    for x1, y1 in points[1:]:
                        if (x1, y1) == (lx, ly):
                            # skip zero-length segment; keep path continuous
                            continue
                        p.lineTo(x1, y1)
                        lx, ly = x1, y1
                    return p

                def _rounded_path(points, radius):
                    if radius <= 0 or len(points) <= 2:
                        return _polyline_to_path(points)
                    p = QPainterPath()
                    p.moveTo(*points[0])
                    for i in range(1, len(points) - 1):
                        x0, y0 = points[i - 1]
                        x1, y1 = points[i]
                        x2, y2 = points[i + 1]
                        # Vectors
                        from math import hypot

                        v1x, v1y = x1 - x0, y1 - y0
                        v2x, v2y = x2 - x1, y2 - y1
                        len1 = hypot(v1x, v1y) or 1.0
                        len2 = hypot(v2x, v2y) or 1.0
                        r = min(radius, len1 / 2, len2 / 2)
                        # Points near the corner
                        p1x, p1y = x1 - v1x / len1 * r, y1 - v1y / len1 * r
                        p2x, p2y = x1 + v2x / len2 * r, y1 + v2y / len2 * r
                        p.lineTo(p1x, p1y)
                        # Use quadratic curve through the corner point
                        p.quadTo(x1, y1, p2x, p2y)
                    p.lineTo(*points[-1])
                    return p

                def _zigzag_points(points, amp, period):
                    # Generate a zigzag polyline along the original segments
                    if not amp or not period or period <= 0:
                        return points
                    from math import hypot

                    out = [points[0]]
                    phase = 1.0
                    for a, b in zip(points, points[1:]):
                        ax, ay = a
                        bx, by = b
                        dx, dy = bx - ax, by - ay
                        seg_len = hypot(dx, dy)
                        if seg_len == 0:
                            continue
                        nx, ny = -dy / seg_len, dx / seg_len  # left normal
                        t = 0.0
                        while t + period < seg_len:
                            t += period
                            px = ax + dx * (t / seg_len)
                            py = ay + dy * (t / seg_len)
                            out.append((px + phase * amp * nx, py + phase * amp * ny))
                            phase *= -1.0
                        out.append((bx, by))
                    return out

                if path_style == "curved":
                    path = _rounded_path(pts, smooth_r if smooth_r > 0 else 8.0)
                elif path_style == "zigzag":
                    zpts = _zigzag_points(
                        pts, float(zig_amp or 6.0), float(zig_per or 12.0)
                    )
                    path = _polyline_to_path(zpts)
                else:
                    path = _polyline_to_path(pts)

                path_item = self.scene.addPath(path, pen)
                path_item.setZValue(5)
                self._register_item(cmd.get("element_id", ""), "ligature", path_item)
                try:
                    path_item.setData(2, "edge.identity")
                except Exception:
                    pass

                # Bridges: draw small gaps/overpass indicators at provided coordinates (underpass ligature)
                bridges = cmd.get("bridges") or []
                if bridges:
                    # Use a small circle filled with background to punch a gap
                    gap_r = max(2.0, line_w * 0.6)
                    bg = QColor(255, 255, 255)
                    for bx, by in bridges:
                        hole = QGraphicsEllipseItem(
                            bx - gap_r / 2, by - gap_r / 2, gap_r, gap_r
                        )
                        hole.setBrush(QBrush(bg))
                        hole.setPen(QPen(bg, 0))
                        hole.setZValue(6)  # above the ligature to appear as a gap
                        self.scene.addItem(hole)

                # Optional: debug hook markers
                import os

                if os.environ.get("ARISBE_DEBUG_HOOKS") == "1":
                    base_pt = pts[0]
                    for i, (hx, hy) in enumerate(pts[1:], start=1):
                        is_base = (hx, hy) == base_pt
                        next_is_base = (i + 1 < len(pts)) and (pts[i + 1] == base_pt)
                        if not is_base and next_is_base:
                            marker = QGraphicsEllipseItem(hx - 2, hy - 2, 4, 4)
                            marker.setBrush(QBrush(QColor(220, 0, 0)))
                            marker.setPen(QPen(QColor(220, 0, 0), 0))
                            self.scene.addItem(marker)

    # --- Chiron dock panel ---
    def _init_chiron_dock(self):
        # Create dock
        self.chiron_dock = QDockWidget("Chiron", self)
        self.chiron_dock.setObjectName("ChironDock")
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.chiron_dock)

        # Container widget
        container = QWidget(self.chiron_dock)
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)

        # Controls row
        controls = QHBoxLayout()
        controls.setContentsMargins(8, 6, 8, 0)
        self.chiron_format = QComboBox()
        self.chiron_format.addItems(["EGIF", "CGIF", "CLIF"])  # right pane format
        self.chiron_format.currentIndexChanged.connect(self._update_chiron_contents)

        copy_left = QToolButton()
        copy_left.setText("Copy Left")
        copy_left.clicked.connect(lambda: self._copy_text(self.chiron_left))
        copy_right = QToolButton()
        copy_right.setText("Copy Right")
        copy_right.clicked.connect(lambda: self._copy_text(self.chiron_right))

        controls.addWidget(self.chiron_format)
        controls.addStretch(1)
        controls.addWidget(copy_left)
        controls.addWidget(copy_right)
        v.addLayout(controls)

        # Two-pane text area
        body = QHBoxLayout()
        body.setContentsMargins(8, 4, 8, 8)
        self.chiron_left = QPlainTextEdit()
        self.chiron_left.setReadOnly(True)
        self.chiron_right = QPlainTextEdit()
        self.chiron_right.setReadOnly(True)
        body.addWidget(self.chiron_left, 1)
        body.addWidget(self.chiron_right, 1)
        v.addLayout(body)

        # Style fonts/colors from style tokens
        t_title = self.style.resolve(type="chiron", role="chiron.title")
        t_text = self.style.resolve(type="chiron", role="chiron.text")
        font_family = t_text.get("font_family", t_title.get("font_family", "Arial"))
        font_size = int(t_text.get("font_size", 10))
        f = QFont(font_family, font_size)
        self.chiron_left.setFont(f)
        self.chiron_right.setFont(f)

        self.chiron_dock.setWidget(container)
        self._update_chiron_contents()

    def _copy_text(self, widget: QPlainTextEdit):
        try:
            clipboard = QApplication.instance().clipboard()
            clipboard.setText(widget.toPlainText())
        except Exception:
            pass

    def _update_chiron_contents(self):
        # Left: last loaded linear form (as-is)
        self.chiron_left.setPlainText(self._last_linear_text or "(none)")
        # Right: current EGI projection by selection
        choice = (self.chiron_format.currentText() or "EGIF").upper()
        try:
            if choice == "CGIF":
                txt = self.egi_system.to_cgif()
            elif choice == "CLIF":
                txt = self.egi_system.to_clif()
            else:
                txt = self.egi_system.to_egif()
        except Exception:
            txt = "(unavailable)"
        self.chiron_right.setPlainText(txt)

    def export_tikz(self):
        # Generate TikZ from current scene via correspondence integration
        try:
            from export.tikz_exporter import generate_tikz
        except Exception:
            # Fallback import path if module-style import fails
            from .export.tikz_exporter import generate_tikz  # type: ignore

        # Ensure we use the freshest commands
        self.qt_integration = create_qt_correspondence_integration(self.egi_system)
        scene_data = self.qt_integration.generate_qt_scene()
        render_commands = scene_data.get("render_commands", [])

        tikz_doc = generate_tikz(render_commands, standalone=True)

        # Write to project-local file
        import os

        out_path = os.path.join(os.getcwd(), "arisbe_export.tex")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(tikz_doc)
            print(f"[TikZ Export] Wrote {len(tikz_doc)} chars to {out_path}")
        except Exception as e:
            print(f"[TikZ Export] Failed to write TikZ: {e}")


def main():
    import sys

    app = QApplication(sys.argv)
    win = EGIMainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
