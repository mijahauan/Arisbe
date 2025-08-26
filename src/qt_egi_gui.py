#!/usr/bin/env python3
"""
Arisbe Qt GUI - Organon Mode (minimal scaffold)

Defines required classes for tests:
- BranchingPointItem, LigatureItem, PredicateItem, CutItem
- EGIGraphicsView, EGIControlPanel, EGIMainWindow

Integrates with EGISystem and QtCorrespondenceIntegration to generate a scene.
"""
from __future__ import annotations

from typing import Any, Dict, List, DefaultDict

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QDockWidget,
    QComboBox,
    QPlainTextEdit,
    QToolButton,
    QCheckBox,
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath

from egi_system import create_egi_system, EGISystem
from qt_correspondence_integration import create_qt_correspondence_integration
from styling.style_manager import create_style_manager


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
    def __init__(self, scene: QGraphicsScene, main_window: 'EGIMainWindow'):
        super().__init__(scene)
        self.main_window = main_window
        self.setRenderHints(self.renderHints())
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        # Map to scene and collect items under cursor
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

    def mouseMoveEvent(self, event):
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
            self.main_window.hover_element(best[0])
        else:
            self.main_window.clear_hover()

        super().mouseMoveEvent(event)


class EGIControlPanel(QWidget):
    def __init__(self, main_window: 'EGIMainWindow'):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        refresh_btn = QPushButton("Refresh Scene")
        refresh_btn.clicked.connect(self.main_window.refresh_scene)
        layout.addWidget(refresh_btn)
        export_btn = QPushButton("Export TikZ (stub)")
        export_btn.clicked.connect(self.main_window.export_tikz)
        layout.addWidget(export_btn)
        open_btn = QPushButton("Open Linear Form…")
        open_btn.clicked.connect(self.main_window.open_linear_form_file)
        layout.addWidget(open_btn)
        paste_btn = QPushButton("Paste Linear Form…")
        paste_btn.clicked.connect(self.main_window.paste_linear_form)
        layout.addWidget(paste_btn)
        # Toggles row
        self.chk_show_vars = QCheckBox("Show variable labels (*x → x)")
        self.chk_show_vars.setChecked(False)
        self.chk_show_vars.stateChanged.connect(lambda _: self.main_window.set_show_variable_labels(self.chk_show_vars.isChecked()))
        layout.addWidget(self.chk_show_vars)

        self.chk_show_arity = QCheckBox("Show relation arity (R → R/n)")
        self.chk_show_arity.setChecked(False)
        self.chk_show_arity.stateChanged.connect(lambda _: self.main_window.set_show_arity(self.chk_show_arity.isChecked()))
        layout.addWidget(self.chk_show_arity)
        layout.addStretch()


# --- Main window ---
class EGIMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe – Organon")
        self.resize(1000, 700)

        # Core systems
        self.egi_system: EGISystem = create_egi_system()
        self.qt_integration = create_qt_correspondence_integration(self.igi_seed())
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

        # Central layout
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # Scene and view
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 600)
        self.graphics_view = EGIGraphicsView(self.scene, self)

        # Control panel
        self.control_panel = EGIControlPanel(self)

        root.addWidget(self.graphics_view, 1)
        root.addWidget(self.control_panel)

        # Seed demo content and render
        self.seed_demo_graph()
        # Track last loaded linear form text for chiron
        try:
            self._last_linear_text: str | None = self.egi_system.to_egif()
        except Exception:
            self._last_linear_text = None
        # Initialize dockable chiron panel
        self._init_chiron_dock()
        self.refresh_scene()

    def _load_linear_and_refresh(self, text: str, format_hint: str | None = None):
        try:
            self.egi_system.load_linear(text, format_hint)
            self._last_linear_text = text
            self.refresh_scene()
            self._update_chiron_contents()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to load linear form: {e}")

    def open_linear_form_file(self):
        """Open a file containing EGIF/CGIF and display it."""
        # Note: both .egif and .cgif supported; also allow any text file
        fname, _ = QFileDialog.getOpenFileName(self, "Open Linear Form", "", "Linear Forms (*.egif *.cgif *.txt);;All Files (*)")
        if not fname:
            return
        try:
            with open(fname, 'r', encoding='utf-8') as f:
                text = f.read()
            # Hint by extension if available
            ext = fname.split('.')[-1].lower() if '.' in fname else None
            fmt_hint = 'egif' if ext == 'egif' else ('cgif' if ext == 'cgif' else None)
            self._load_linear_and_refresh(text, fmt_hint)
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Failed to read file:\n{e}")

    def paste_linear_form(self):
        """Paste EGIF/CGIF text and display it."""
        text, ok = QInputDialog.getMultiLineText(self, "Paste Linear Form", "Enter EGIF or CGIF:")
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
        for cmd in scene_data.get("render_commands", []):
            self._emit_command(cmd)

    # --- Toggle handlers ---
    def set_show_variable_labels(self, on: bool):
        self._show_variable_labels = bool(on)
        self.refresh_scene()

    def set_show_arity(self, on: bool):
        self._show_arity = bool(on)
        self.refresh_scene()

    def _register_item(self, element_id: str, element_type: str, item: Any):
        try:
            item.setData(0, element_id)
            item.setData(1, element_type)
        except Exception:
            pass
        self._items_by_element[element_id].append(item)

    def _set_item_highlight(self, item: Any, element_type: str, on: bool):
        # Apply style tokens from StyleManager using selected/normal states
        from PySide6.QtGui import QPen, QBrush, QColor
        try:
            role_map = {
                "vertex": "vertex.dot",
                "edge": "edge.label_box",
                "ligature": "ligature.arm",
                "cut": "cut.border",
            }
            role = role_map.get(element_type, element_type)
            tokens = self.style.resolve(type=element_type, role=role, state=("selected" if on else None))

            # Pens
            pen_color = QColor(tokens.get("line_color", tokens.get("border_color", "#000000")))
            pen_w = float(tokens.get("line_width", tokens.get("border_width", 1)))
            if hasattr(item, 'setPen'):
                item.setPen(QPen(pen_color, pen_w))

            # Brushes (do not change cut fill on selection; spec says border emphasis only)
            if element_type != "cut" and hasattr(item, 'setBrush'):
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
                etype = it.data(1) if hasattr(it, 'data') else None
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
                etype = it.data(1) if hasattr(it, 'data') else None
                if etype:
                    self._set_item_highlight(it, str(etype), True)
        # Track selection state
        self._selected_ids = connected_ids
        self._selected_id = element_id

    def clear_hover(self):
        if not self._hover_id:
            return
        for it in self._items_by_element.get(self._hover_id, []):
            etype = it.data(1) if hasattr(it, 'data') else None
            if etype:
                # turn off hover by reapplying selected state if selected, else normal
                is_selected = (self._selected_id == self._hover_id)
                self._set_item_highlight(it, str(etype), is_selected)
        self._hover_id = None

    def hover_element(self, element_id: str):
        if element_id == self._hover_id:
            return
        # clear prior hover
        self.clear_hover()
        # apply hover style only if not selected (selected takes precedence)
        for it in self._items_by_element.get(element_id, []):
            etype = it.data(1) if hasattr(it, 'data') else None
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
        from PySide6.QtGui import QPen, QBrush, QColor
        role_map = {
            "vertex": "vertex.dot",
            "edge": "edge.label_box",
            "ligature": "ligature.arm",
            "cut": "cut.border",
        }
        role = role_map.get(element_type, element_type)
        tokens = self.style.resolve(type=element_type, role=role, state=state)
        pen_color = QColor(tokens.get("line_color", tokens.get("border_color", "#000000")))
        pen_w = float(tokens.get("line_width", tokens.get("border_width", 1)))
        if hasattr(item, 'setPen'):
            item.setPen(QPen(pen_color, pen_w))
        if element_type != "cut" and hasattr(item, 'setBrush'):
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
        x, y, w, h = b.get("x", 0.0), b.get("y", 0.0), b.get("width", 0.0), b.get("height", 0.0)

        if typ == "vertex":
            # Draw small spot and label
            s = self.style.resolve(type="vertex", role=role)
            radius = float(s.get("radius", 3))
            fill = _qcolor(s.get("fill_color", "#000000"))
            border_color = _qcolor(s.get("border_color", "#000000"))
            border_w = float(s.get("border_width", 1))
            spot = QGraphicsEllipseItem(x + w / 2 - radius, y + h / 2 - radius, 2 * radius, 2 * radius)
            spot.setBrush(QBrush(fill))
            spot.setPen(QPen(border_color, border_w))
            self.scene.addItem(spot)
            spot.setZValue(10)
            self._register_item(cmd.get("element_id", ""), "vertex", spot)
            # Optional vertex label rendering (variable superscript or constant label)
            try:
                vid = cmd.get("element_id", "")
                vobj = self.egi_system.get_egi().get_vertex(vid)
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
                    role_for_style = "vertex.superscript_text" if vobj.is_generic else "vertex.label_text"
                    tstyle = self.style.resolve(type="vertex", role=role_for_style)
                    font_family = tstyle.get("font_family", "Arial")
                    base_sz = int(tstyle.get("font_size", tstyle.get("estimate_height", 12)))
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
                    self.scene.addItem(vtext)
                    vtext.setZValue(11)
                    self._register_item(vid, "vertex", vtext)
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
            text.setFont(QFont(g.get("font_family", "Arial"), int(g.get("font_size", 10))))
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
                        arity = len(egi.get_incident_vertices(cmd.get("element_id", "")))
                        sup_txt = f"/{arity}"
                        sstyle = self.style.resolve(type="edge", role="edge.superscript_text")
                        sfam = sstyle.get("font_family", g.get("font_family", "Arial"))
                        ss = int(sstyle.get("font_size", max(8, int(g.get("font_size", 10)) - 2)))
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
                        sup_item.setPos(float(sup_b.get("x", x + w)), float(sup_b.get("y", y)))
                        self.scene.addItem(sup_item)
                        sup_item.setZValue(8)
                        self._register_item(cmd.get("element_id", ""), "edge", sup_item)
                except Exception:
                    pass
        elif typ == "cut":
            # Rounded rectangle cut
            s_border = self.style.resolve(type="cut", role=role)
            ap = int(cmd.get("area_parity", 0))
            s_fill = self.style.resolve(type="cut", role=("cut.fill.odd" if ap == 1 else "cut.fill.even"))
            line_color = _qcolor(s_border.get("line_color", "#000000"))
            line_w = float(s_border.get("line_width", 1))
            radius = float(s_border.get("radius", 10))
            fill_color = _qcolor(s_fill.get("fill_color", "transparent"))
            path = QPainterPath()
            path.addRoundedRect(QRectF(x, y, w, h), radius, radius)
            path_item = self.scene.addPath(path, QPen(line_color, line_w), QBrush(fill_color))
            path_item.setZValue(-1)
            self._register_item(cmd.get("element_id", ""), "cut", path_item)
        elif typ == "ligature":
            pts = cmd.get("path_points", []) or []
            if len(pts) >= 2:
                path = QPainterPath()
                # Draw as multiple subpaths: whenever the polyline returns to base,
                # start a new subpath instead of drawing a return segment. This makes
                # each ligature arm a separate stroke, preventing loop-like bends.
                base_x, base_y = pts[0]
                path.moveTo(base_x, base_y)
                for (x1, y1) in pts[1:]:
                    if (x1, y1) == (base_x, base_y):
                        path.moveTo(base_x, base_y)
                    else:
                        path.lineTo(x1, y1)
                s = self.style.resolve(type="ligature", role=role)
                pen = QPen(_qcolor(s.get("line_color", "#000000")), float(s.get("line_width", 3)))
                try:
                    from PySide6.QtCore import Qt as QtCoreQt
                    cap = str(s.get("cap", "round")).lower()
                    if cap == "round":
                        pen.setCapStyle(QtCoreQt.PenCapStyle.RoundCap)
                    elif cap == "square":
                        pen.setCapStyle(QtCoreQt.PenCapStyle.SquareCap)
                    else:
                        pen.setCapStyle(QtCoreQt.PenCapStyle.FlatCap)
                except Exception:
                    pass
                path_item = self.scene.addPath(path, pen)
                path_item.setZValue(5)
                self._register_item(cmd.get("element_id", ""), "ligature", path_item)

                # Optional: draw small markers at hook endpoints to aid debugging visibility
                import os
                if os.environ.get('ARISBE_DEBUG_HOOKS') == '1':
                    base_pt = pts[0]
                    for i, (hx, hy) in enumerate(pts[1:], start=1):
                        # Consider a hook point if followed by base or if it's not equal to base
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
    
