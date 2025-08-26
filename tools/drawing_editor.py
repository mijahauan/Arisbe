#!/usr/bin/env python3
"""
Minimal drawing tool for constructing EGI drawings and exporting to JSON schema
compatible with drawing_to_egi_adapter.drawing_to_relational_graph().

Features:
- Add cuts (click-drag rectangles). Parent is selected cut or sheet by default.
- Add vertices (click).
- Add predicates (click; prompt for name).
- Create ligatures (click predicate, then vertex) to associate vertices to an edge.
- Save/Load drawing JSON.
- Optional: Export to EGI summary using SpatialCorrespondenceEngine (console).

This is intentionally minimal, focused on authoring the headless schema.
"""
from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QAction, QPen, QBrush, QColor, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QToolBar,
    QDockWidget,
    QTabWidget,
    QTextEdit,
    QWidget,
    QMenu,
)


# ---------- Data schema (in-memory) ----------
@dataclass
class CutItem:
    id: str
    rect: QRectF
    parent_id: Optional[str]  # sheet or another cut
    gfx: QGraphicsRectItem


@dataclass
class VertexItem:
    id: str
    pos: QPointF
    area_id: str
    gfx: QGraphicsEllipseItem


@dataclass
class PredicateItem:
    id: str
    name: str
    pos: QPointF
    area_id: str
    gfx_text: QGraphicsTextItem
    gfx_rect: QGraphicsRectItem


@dataclass
class DrawingModel:
    sheet_id: str = "S"
    cuts: Dict[str, CutItem] = field(default_factory=dict)
    vertices: Dict[str, VertexItem] = field(default_factory=dict)
    predicates: Dict[str, PredicateItem] = field(default_factory=dict)
    ligatures: Dict[str, List[str]] = field(default_factory=dict)  # edge_id -> [vertex_id]

    def to_schema(self) -> Dict:
        return {
            "sheet_id": self.sheet_id,
            "cuts": [
                {"id": c.id, "parent_id": c.parent_id} for c in self.cuts.values()
            ],
            "vertices": [
                {"id": v.id, "area_id": v.area_id} for v in self.vertices.values()
            ],
            "predicates": [
                {"id": p.id, "name": p.name, "area_id": p.area_id} for p in self.predicates.values()
            ],
            "ligatures": [
                {"edge_id": e, "vertex_ids": vids} for e, vids in self.ligatures.items()
            ],
        }

    @classmethod
    def from_schema(cls, scene: QGraphicsScene, schema: Dict) -> "DrawingModel":
        model = cls(sheet_id=schema.get("sheet_id", "S"))
        # Cuts first
        for c in schema.get("cuts", []):
            rid = c["id"]
            # Place dummy rects; users can adjust later. For now, auto-grid.
            rect = QRectF(50 + 30 * len(model.cuts), 50 + 30 * len(model.cuts), 240, 160)
            gfx = QGraphicsRectItem(rect)
            gfx.setPen(QPen(QColor(0, 0, 0), 1))
            gfx.setBrush(QBrush(QColor(240, 240, 240, 60)))
            gfx.setFlag(QGraphicsItem.ItemIsMovable, True)
            gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)
            scene.addItem(gfx)
            model.cuts[rid] = CutItem(id=rid, rect=rect, parent_id=c.get("parent_id"), gfx=gfx)
        # Vertices
        for v in schema.get("vertices", []):
            vid = v["id"]
            pos = QPointF(120 + 15 * len(model.vertices), 120)
            gfx = QGraphicsEllipseItem(-4, -4, 8, 8)
            gfx.setBrush(QBrush(QColor(0, 0, 0)))
            gfx.setPen(QPen(QColor(0, 0, 0), 2))
            gfx.setPos(pos)
            gfx.setFlag(QGraphicsItem.ItemIsMovable, True)
            gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)
            scene.addItem(gfx)
            model.vertices[vid] = VertexItem(id=vid, pos=pos, area_id=v["area_id"], gfx=gfx)
        # Predicates
        for p in schema.get("predicates", []):
            eid = p["id"]
            name = p.get("name", eid)
            pos = QPointF(200 + 20 * len(model.predicates), 120)
            text = QGraphicsTextItem(name)
            rect = text.boundingRect().adjusted(-4, -2, 4, 2)
            rect_item = QGraphicsRectItem(rect)
            rect_item.setBrush(QBrush(QColor(255, 255, 255)))
            rect_item.setPen(QPen(QColor(0, 0, 0, 60), 0))
            group_pos = pos
            rect_item.setPos(group_pos)
            # Parent text to rect so they move together
            text.setParentItem(rect_item)
            text.setPos(4, 2)
            rect_item.setFlag(QGraphicsItem.ItemIsMovable, True)
            rect_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
            # Text follows rect; do not allow independent movement
            text.setFlag(QGraphicsItem.ItemIsMovable, False)
            text.setFlag(QGraphicsItem.ItemIsSelectable, False)
            scene.addItem(rect_item)
            model.predicates[eid] = PredicateItem(
                id=eid, name=name, pos=pos, area_id=p["area_id"], gfx_text=text, gfx_rect=rect_item
            )
        # Ligatures
        lig_map: Dict[str, List[str]] = {}
        for lig in schema.get("ligatures", []):
            lig_map.setdefault(lig["edge_id"], []).extend(lig.get("vertex_ids", []))
        model.ligatures = lig_map
        return model


# ---------- Editor UI ----------
class Mode:
    SELECT = "select"
    ADD_CUT = "add_cut"
    ADD_VERTEX = "add_vertex"
    ADD_PREDICATE = "add_predicate"
    LIGATURE = "ligature"


class DrawingEditor(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Arisbe Drawing Tool (minimal)")
        self.resize(1000, 700)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 900, 600)
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.model = DrawingModel()
        # Visual ligature lines
        self._ligature_lines: List[QGraphicsLineItem] = []
        self._ligature_refresh_pending: bool = False
        self._suppress_scene_change: bool = False
        self._show_ligatures: bool = False
        # Z-order refresh debounce
        self._zorder_refresh_pending: bool = False
        # Interaction throttle: suppress heavy refresh during drag
        self._interaction_active: bool = False

        self.mode: str = Mode.SELECT
        self.active_parent_area: Optional[str] = None  # If a cut is selected before adding, that becomes parent/area

        # Temp vars for interactions
        self._drag_start: Optional[QPointF] = None
        self._pending_predicate_name: Optional[str] = None
        self._ligature_edge: Optional[str] = None

        # Preview UI (dock)
        self._build_preview_dock()
        # Toolbar
        self._build_toolbar()
        # Initial preview
        self._update_preview()
        # Keep visuals and z-order in sync with movements
        self.scene.changed.connect(self._on_scene_changed)
        # Selection visuals
        self.scene.selectionChanged.connect(self._on_selection_changed)

    # ----- Stdout logging -----
    def _log(self, msg: str) -> None:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] {msg}")
        except Exception:
            try:
                print(msg)
            except Exception:
                pass

    # ----- Toolbar and actions -----
    def _build_toolbar(self) -> None:
        tb = QToolBar("Tools")
        self.addToolBar(tb)

        def make_action(text: str, checkable=False, slot=None) -> QAction:
            a = QAction(text, self)
            a.setCheckable(checkable)
            if slot:
                a.triggered.connect(slot)
            tb.addAction(a)
            return a

        self.act_select = make_action("Select", True, lambda: self._set_mode(Mode.SELECT))
        self.act_add_cut = make_action("Add Cut", True, lambda: self._set_mode(Mode.ADD_CUT))
        self.act_add_vertex = make_action("Add Vertex", True, lambda: self._set_mode(Mode.ADD_VERTEX))
        self.act_add_pred = make_action("Add Predicate", True, lambda: self._set_mode(Mode.ADD_PREDICATE))
        self.act_ligature = make_action("Ligature", True, lambda: self._set_mode(Mode.LIGATURE))

        tb.addSeparator()
        make_action("New", False, self.on_new)
        make_action("Save", False, self.on_save)
        make_action("Load", False, self.on_load)
        make_action("Export EGI", False, self.on_export_egi)

        tb.addSeparator()
        self.act_preview = make_action("Preview", False, self._update_preview)
        self.act_auto = make_action("Auto Preview", True, None)
        # Default off to reduce startup load; you can enable it any time
        self.act_auto.setChecked(False)
        tb.addAction(self.act_auto)

        # Toggle: Show Ligatures (visual only)
        self.act_show_ligs = make_action("Show Ligatures", True, self._toggle_show_ligatures)
        self.act_show_ligs.setChecked(False)
        tb.addAction(self.act_show_ligs)

        # Quick access: Delete selected
        del_action = QAction("Delete", self)
        del_action.setShortcuts([QKeySequence.Delete, QKeySequence.Backspace])
        del_action.triggered.connect(self._delete_selected_items)
        tb.addAction(del_action)

        self.act_select.setChecked(True)

        self.view.setMouseTracking(True)
        self.view.viewport().installEventFilter(self)

    def _set_mode(self, mode: str) -> None:
        for act in [self.act_select, self.act_add_cut, self.act_add_vertex, self.act_add_pred, self.act_ligature]:
            act.setChecked(False)
        self.mode = mode
        mapping = {
            Mode.SELECT: self.act_select,
            Mode.ADD_CUT: self.act_add_cut,
            Mode.ADD_VERTEX: self.act_add_vertex,
            Mode.ADD_PREDICATE: self.act_add_pred,
            Mode.LIGATURE: self.act_ligature,
        }
        mapping[self.mode].setChecked(True)
        self.statusBar().showMessage(f"Mode: {self.mode}")

    def _build_preview_dock(self) -> None:
        self.preview_dock = QDockWidget("Preview", self)
        self.preview_dock.setObjectName("previewDock")
        tabs = QTabWidget(self.preview_dock)
        self.txt_egi = QTextEdit()
        self.txt_egi.setReadOnly(True)
        self.txt_egif = QTextEdit()
        self.txt_egif.setReadOnly(True)
        tabs.addTab(self.txt_egi, "EGI (JSON)")
        tabs.addTab(self.txt_egif, "EGIF")
        container = QWidget()
        # Directly set tabs as dock widget content
        self.preview_dock.setWidget(tabs)
        self.addDockWidget(Qt.RightDockWidgetArea, self.preview_dock)
        # Click-to-select from JSON: react to cursor changes
        self.txt_egi.cursorPositionChanged.connect(self._on_egi_cursor_moved)

    def _schedule_preview(self) -> None:
        if self.act_auto.isChecked():
            QTimer.singleShot(0, self._update_preview)

    def _update_preview(self) -> None:
        try:
            schema = self._gather_schema_from_scene()
            # Pretty JSON
            self.txt_egi.setPlainText(json.dumps(schema, indent=2))
            # Build EGIF via adapter + generator
            try:
                from drawing_to_egi_adapter import drawing_to_relational_graph
                from egif_generator_dau import generate_egif
                rgc = drawing_to_relational_graph(schema)
                egif = generate_egif(rgc)
            except Exception as e:
                egif = f"<EGIF generation error>\n{e}"
            self.txt_egif.setPlainText(egif)
        except Exception as e:
            self.txt_egi.setPlainText(f"<Preview error>\n{e}")
            self.txt_egif.setPlainText("")

    # ----- Helpers -----
    def _toggle_show_ligatures(self, checked: bool) -> None:
        self._show_ligatures = bool(checked)
        if not self._show_ligatures:
            # Clear quickly when turning off
            self._clear_ligature_visuals()
        else:
            self._schedule_ligature_refresh()
    def _on_scene_changed(self, *args) -> None:
        # Accepts the changed regions from the signal and schedules a refresh
        # Skip during active drag to avoid repeated heavy work per mouse move
        if self._interaction_active:
            return
        self._schedule_ligature_refresh()
        self._schedule_zorder_refresh()

    def _on_selection_changed(self) -> None:
        self._apply_selection_styles()
    def _clear_ligature_visuals(self) -> None:
        for line in self._ligature_lines:
            try:
                self.scene.removeItem(line)
            except Exception:
                pass
        self._ligature_lines.clear()

    def _schedule_ligature_refresh(self) -> None:
        if not self._show_ligatures:
            # Keep visuals cleared when disabled
            if self._ligature_lines:
                self._clear_ligature_visuals()
            return
        if self._suppress_scene_change:
            return
        if self._ligature_refresh_pending:
            return
        self._ligature_refresh_pending = True
        def do_refresh():
            try:
                self._refresh_ligature_visuals()
            finally:
                self._ligature_refresh_pending = False
        # Throttle slightly to coalesce bursts of scene changes
        QTimer.singleShot(30, do_refresh)

    def _schedule_zorder_refresh(self) -> None:
        if self._suppress_scene_change:
            return
        if self._zorder_refresh_pending:
            return
        self._zorder_refresh_pending = True
        def do_refresh():
            try:
                self._update_z_order()
            finally:
                self._zorder_refresh_pending = False
        QTimer.singleShot(30, do_refresh)

    def _refresh_ligature_visuals(self) -> None:
        # Rebuild simple straight lines from predicates to vertices
        self._suppress_scene_change = True
        try:
            self._clear_ligature_visuals()
            pen = QPen(QColor(80, 80, 200, 160), 1)
            pen.setCosmetic(True)
            parent_map = self._compute_parent_map()
            for edge_id, vids in self.model.ligatures.items():
                p = self.model.predicates.get(edge_id)
                if p is None:
                    continue
                # Anchor at center of predicate rect
                rect = p.gfx_rect.sceneBoundingRect()
                p_center = rect.center()
                # z baseline from area depth
                p_area = self._resolve_area_position(p_center, parent_map)
                depth = self._area_depth(p_area, parent_map)
                for vid in vids:
                    v = self.model.vertices.get(vid)
                    if v is None:
                        continue
                    v_center = v.gfx.scenePos()
                    line = QGraphicsLineItem(p_center.x(), p_center.y(), v_center.x(), v_center.y())
                    line.setZValue(depth * 10.0)  # behind predicate(+1) and vertex(+2)
                    line.setPen(pen)
                    self.scene.addItem(line)
                    self._ligature_lines.append(line)
        finally:
            self._suppress_scene_change = False

    # ----- Interaction throttle helpers -----
    def begin_interaction(self) -> None:
        self._interaction_active = True

    def end_interaction(self) -> None:
        # End of a drag/manipulation: re-enable updates and do one refresh
        self._interaction_active = False
        self._schedule_ligature_refresh()
        self._schedule_zorder_refresh()

    # ----- Selection visuals and JSON mapping -----
    def _apply_selection_styles(self) -> None:
        # Basic highlight: thicker/darker pen for selected
        for cid, c in self.model.cuts.items():
            sel = c.gfx.isSelected()
            pen = c.gfx.pen()
            pen.setWidthF(2.0 if sel else 1.0)
            pen.setColor(QColor(50, 120, 220) if sel else QColor(0, 0, 0))
            c.gfx.setPen(pen)
        for pid, p in self.model.predicates.items():
            sel = p.gfx_rect.isSelected()
            pen = p.gfx_rect.pen()
            pen.setWidthF(2.0 if sel else 0.0)
            pen.setColor(QColor(50, 120, 220) if sel else QColor(0, 0, 0, 60))
            p.gfx_rect.setPen(pen)
        for vid, v in self.model.vertices.items():
            sel = v.gfx.isSelected()
            pen = v.gfx.pen()
            pen.setWidthF(3.0 if sel else 2.0)
            pen.setColor(QColor(50, 120, 220) if sel else QColor(0, 0, 0))
            v.gfx.setPen(pen)

    def _on_egi_cursor_moved(self) -> None:
        # Get word under cursor and try to select corresponding item
        from PySide6.QtGui import QTextCursor
        cursor = self.txt_egi.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        token = cursor.selectedText()
        if not token:
            return
        self._select_by_id(token)

    def _select_by_id(self, element_id: str) -> None:
        # Clear old selection
        matched = False
        self.scene.blockSignals(True)
        try:
            self.scene.clearSelection()
            # Prefer exact ID match in our model dicts
            if element_id in self.model.cuts:
                self.model.cuts[element_id].gfx.setSelected(True)
                self.view.centerOn(self.model.cuts[element_id].gfx)
                matched = True
            elif element_id in self.model.vertices:
                self.model.vertices[element_id].gfx.setSelected(True)
                self.view.centerOn(self.model.vertices[element_id].gfx)
                matched = True
            elif element_id in self.model.predicates:
                self.model.predicates[element_id].gfx_rect.setSelected(True)
                self.view.centerOn(self.model.predicates[element_id].gfx_rect)
                matched = True
        finally:
            self.scene.blockSignals(False)
        if matched:
            self._apply_selection_styles()

    # ----- Key handling -----
    def keyPressEvent(self, event) -> None:
        from PySide6.QtGui import QKeySequence
        key = event.key()
        if key in (Qt.Key_Delete, Qt.Key_Backspace):
            self._delete_selected_items()
            event.accept()
            return
        super().keyPressEvent(event)

    def _delete_selected_items(self) -> None:
        # Remove selected vertices/predicates/cuts; update model and ligatures
        items = list(self.scene.selectedItems())
        if not items:
            return
        # Helper to find ids
        remove_vertices: List[str] = []
        remove_predicates: List[str] = []
        remove_cuts: List[str] = []
        for it in items:
            # Predicate rect
            for pid, p in self.model.predicates.items():
                if it is p.gfx_rect or it is p.gfx_text:
                    remove_predicates.append(pid)
                    break
            # Vertex
            for vid, v in self.model.vertices.items():
                if it is v.gfx:
                    remove_vertices.append(vid)
                    break
            # Cut
            for cid, c in self.model.cuts.items():
                if it is c.gfx:
                    remove_cuts.append(cid)
                    break

        # Deduplicate
        remove_vertices = list(dict.fromkeys(remove_vertices))
        remove_predicates = list(dict.fromkeys(remove_predicates))
        remove_cuts = list(dict.fromkeys(remove_cuts))

        # Remove ligatures referencing removed items
        if remove_vertices or remove_predicates:
            new_ligs: Dict[str, List[str]] = {}
            for eid, vids in self.model.ligatures.items():
                if eid in remove_predicates:
                    continue  # drop entire mapping
                kept = [v for v in vids if v not in remove_vertices]
                if kept:
                    new_ligs[eid] = kept
            self.model.ligatures = new_ligs

        # Remove graphics and model entries
        for vid in remove_vertices:
            v = self.model.vertices.pop(vid, None)
            if v is not None:
                self.scene.removeItem(v.gfx)
        for pid in remove_predicates:
            p = self.model.predicates.pop(pid, None)
            if p is not None:
                # Removing rect also removes child text
                self.scene.removeItem(p.gfx_rect)
        for cid in remove_cuts:
            c = self.model.cuts.pop(cid, None)
            if c is not None:
                self.scene.removeItem(c.gfx)

        # Refresh visuals and preview
        self._clear_ligature_visuals()
        self._schedule_ligature_refresh()
        self._schedule_zorder_refresh()
        self._schedule_preview()
        if remove_vertices or remove_predicates or remove_cuts:
            self._log(
                f"DELETE vertices={remove_vertices} predicates={remove_predicates} cuts={remove_cuts}"
            )

    # Helper to fetch cut id for a given graphics item
    def _id_for_cut_item(self, item: QGraphicsRectItem) -> str:
        for cid, c in self.model.cuts.items():
            if c.gfx is item:
                return cid
        return "?"

    # ----- Z-order helpers -----
    def _compute_parent_map(self) -> Dict[str, Optional[str]]:
        # Map each cut to its parent cut or sheet
        parent_map: Dict[str, Optional[str]] = {}
        # Ensure current rects are up to date
        for c in self.model.cuts.values():
            r = c.gfx.rect()
            tl = c.gfx.mapToScene(r.topLeft())
            br = c.gfx.mapToScene(r.bottomRight())
            c.rect = QRectF(tl, br).normalized()

        def point_in_rect(pt: QPointF, rect: QRectF) -> bool:
            eps = 0.1
            return (rect.x() - eps <= pt.x() <= rect.x() + rect.width() + eps and
                    rect.y() - eps <= pt.y() <= rect.y() + rect.height() + eps)

        for cid, c in self.model.cuts.items():
            center = c.rect.center()
            parent: Optional[str] = None
            best_depth = -1
            for oid, oc in self.model.cuts.items():
                if oid == cid:
                    continue
                if point_in_rect(center, oc.rect):
                    # approximate depth by chain length using current parent_map
                    depth = 1
                    pid = parent_map.get(oid)
                    while pid is not None:
                        depth += 1
                        pid = parent_map.get(pid)
                    if depth > best_depth:
                        best_depth = depth
                        parent = oid
            parent_map[cid] = parent if parent is not None else self.model.sheet_id
        return parent_map

    def _area_depth(self, area_id: Optional[str], parent_map: Dict[str, Optional[str]]) -> int:
        # Sheet has depth 0
        if area_id is None or area_id == self.model.sheet_id:
            return 0
        depth = 1
        pid = parent_map.get(area_id)
        while pid is not None and pid in self.model.cuts:
            depth += 1
            pid = parent_map.get(pid)
        return depth

    def _resolve_area_position(self, pos: QPointF, parent_map: Dict[str, Optional[str]]) -> str:
        inside: List[Tuple[int, str]] = []
        def point_in_rect(pt: QPointF, rect: QRectF) -> bool:
            eps = 0.1
            return (rect.x() - eps <= pt.x() <= rect.x() + rect.width() + eps and
                    rect.y() - eps <= pt.y() <= rect.y() + rect.height() + eps)
        for cid, c in self.model.cuts.items():
            if point_in_rect(pos, c.rect):
                # compute depth
                depth = self._area_depth(cid, parent_map)
                inside.append((depth, cid))
        if inside:
            inside.sort()
            return inside[-1][1]
        return self.model.sheet_id

    def _update_z_order(self) -> None:
        # Set z-values so that:
        # - sheet background (implicit) is lowest
        # - cuts increase with depth
        # - predicates above cuts
        # - vertices highest
        self._suppress_scene_change = True
        try:
            parent_map = self._compute_parent_map()
            for cid, c in self.model.cuts.items():
                depth = self._area_depth(cid, parent_map)
                c.gfx.setZValue(depth * 10.0)
            for pid, p in self.model.predicates.items():
                area = self._resolve_area_position(p.gfx_rect.scenePos(), parent_map)
                depth = self._area_depth(area, parent_map)
                p.gfx_rect.setZValue(depth * 10.0 + 1.0)
                # text inherits z from parent
            for vid, v in self.model.vertices.items():
                area = self._resolve_area_position(v.gfx.scenePos(), parent_map)
                depth = self._area_depth(area, parent_map)
                v.gfx.setZValue(depth * 10.0 + 2.0)
            # Also update ligature lines if present
            if self._ligature_lines:
                self._refresh_ligature_visuals()
        finally:
            self._suppress_scene_change = False
    def _scene_rect_for_item(self, item: QGraphicsRectItem) -> QRectF:
        r = item.rect()
        tl = item.mapToScene(r.topLeft())
        br = item.mapToScene(r.bottomRight())
        return QRectF(tl, br).normalized()

    def _rect_contains(self, outer: QRectF, inner: QRectF, eps: float = 0.1) -> bool:
        return (
            outer.left() - eps <= inner.left() and
            outer.top() - eps <= inner.top() and
            outer.right() + eps >= inner.right() and
            outer.bottom() + eps >= inner.bottom()
        )

    def _rects_intersect(self, a: QRectF, b: QRectF, eps: float = 0.0) -> bool:
        ar = QRectF(a)
        br = QRectF(b)
        ar.adjust(-eps, -eps, eps, eps)
        br.adjust(-eps, -eps, eps, eps)
        return ar.intersects(br)

    def _is_valid_cut_scene_rect(self, new_rect: QRectF, ignore_item: Optional[QGraphicsRectItem] = None) -> bool:
        # Valid if disjoint from every other cut OR fully contains OR fully contained by that cut.
        for cid, c in self.model.cuts.items():
            if ignore_item is not None and c.gfx is ignore_item:
                continue
            other = self._scene_rect_for_item(c.gfx)
            if not self._rects_intersect(new_rect, other):
                continue  # disjoint ok
            if self._rect_contains(new_rect, other) or self._rect_contains(other, new_rect):
                continue  # nesting ok
            return False  # partial overlap -> invalid
        return True
    def _generate_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:6]}"

    def _hit_cut(self, pos: QPointF) -> Optional[str]:
        # Return topmost cut id containing pos
        items = self.scene.items(pos)
        for it in items:
            for cid, c in self.model.cuts.items():
                if it is c.gfx and c.gfx.contains(c.gfx.mapFromScene(pos)):
                    return cid
        return None

    def _hit_predicate(self, pos: QPointF) -> Optional[str]:
        items = self.scene.items(pos)
        for it in items:
            for pid, p in self.model.predicates.items():
                if it in (p.gfx_rect, p.gfx_text):
                    return pid
        return None

    def _hit_vertex(self, pos: QPointF) -> Optional[str]:
        items = self.scene.items(pos)
        for it in items:
            for vid, v in self.model.vertices.items():
                if it is v.gfx or (isinstance(it, QGraphicsEllipseItem) and it == v.gfx):
                    return vid
        return None

    def _current_area_for_add(self, pos: QPointF) -> str:
        # If user clicked inside a cut, use that cut; else sheet
        cid = self._hit_cut(pos)
        return cid if cid else self.model.sheet_id

    # ----- Mouse interactions -----
    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent

        if obj == self.view.viewport():
            if event.type() == QEvent.MouseButtonPress:
                scene_pos = self.view.mapToScene(event.position().toPoint())
                if self.mode == Mode.ADD_CUT:
                    self._drag_start = scene_pos
                elif self.mode == Mode.ADD_VERTEX:
                    self._add_vertex(scene_pos)
                    self._schedule_preview()
                elif self.mode == Mode.ADD_PREDICATE:
                    self._add_predicate(scene_pos)
                    self._schedule_preview()
                elif self.mode == Mode.LIGATURE:
                    self._handle_ligature_click(scene_pos)
                    self._schedule_preview()
                    self._schedule_ligature_refresh()
                return False
            elif event.type() == QEvent.ContextMenu:
                # Show context menu with Delete when selection is non-empty
                if self.scene.selectedItems():
                    menu = QMenu(self)
                    act_del = menu.addAction("Delete")
                    act = menu.exec(event.globalPos())
                    if act is act_del:
                        self._delete_selected_items()
                        return True
                return False
            elif event.type() == QEvent.MouseMove:
                return False
            elif event.type() == QEvent.MouseButtonRelease:
                if self.mode == Mode.ADD_CUT and self._drag_start is not None:
                    scene_pos = self.view.mapToScene(event.position().toPoint())
                    self._finish_cut(self._drag_start, scene_pos)
                    self._drag_start = None
                    self._schedule_preview()
                    self._schedule_ligature_refresh()
                return False
        return super().eventFilter(obj, event)

    # ----- Actions -----
    def _finish_cut(self, start: QPointF, end: QPointF) -> None:
        rect = QRectF(start, end).normalized()
        cid = self._generate_id("c")
        parent = self._current_area_for_add(start)
        # Validate syntactic constraint: no partial overlaps
        self._log(f"ADD_CUT attempt id={cid} rect={rect}")
        if not self._is_valid_cut_scene_rect(rect):
            self._log(f"ADD_CUT invalid id={cid} reason=partial_overlap")
            self.statusBar().showMessage("Invalid cut: cuts must be nested or disjoint (no partial overlaps).")
            return
        gfx = CutRectItem(rect, self)
        gfx.setPen(QPen(QColor(0, 0, 0), 1))
        gfx.setBrush(QBrush(QColor(240, 240, 240, 60)))
        gfx.setFlag(QGraphicsItem.ItemIsMovable, True)
        gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.scene.addItem(gfx)
        self.model.cuts[cid] = CutItem(id=cid, rect=rect, parent_id=parent, gfx=gfx)
        self._log(f"ADD_CUT ok id={cid} parent={parent}")

    def _add_vertex(self, pos: QPointF) -> None:
        vid = self._generate_id("v")
        area = self._current_area_for_add(pos)
        self._log(f"ADD_VERTEX id={vid} pos=({pos.x():.1f},{pos.y():.1f}) area={area}")
        gfx = QGraphicsEllipseItem(-4, -4, 8, 8)
        gfx.setBrush(QBrush(QColor(0, 0, 0)))
        gfx.setPen(QPen(QColor(0, 0, 0), 2))
        gfx.setPos(pos)
        gfx.setFlag(QGraphicsItem.ItemIsMovable, True)
        gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.scene.addItem(gfx)
        self.model.vertices[vid] = VertexItem(id=vid, pos=pos, area_id=area, gfx=gfx)
        self._schedule_ligature_refresh()

    def _add_predicate(self, pos: QPointF) -> None:
        text, ok = QInputDialog.getText(self, "Predicate", "Name:")
        if not ok or not text:
            return
        eid = self._generate_id("e")
        area = self._current_area_for_add(pos)
        self._log(f"ADD_PREDICATE id={eid} name={text} pos=({pos.x():.1f},{pos.y():.1f}) area={area}")
        label = QGraphicsTextItem(text)
        rect = label.boundingRect().adjusted(-4, -2, 4, 2)
        rect_item = QGraphicsRectItem(rect)
        rect_item.setBrush(QBrush(QColor(255, 255, 255)))
        rect_item.setPen(QPen(QColor(0, 0, 0, 60), 0))
        rect_item.setPos(pos)
        # Parent text to rect so they move together
        label.setParentItem(rect_item)
        label.setPos(4, 2)
        rect_item.setFlag(QGraphicsItem.ItemIsMovable, True)
        rect_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        # Text follows rect; do not allow independent movement
        label.setFlag(QGraphicsItem.ItemIsMovable, False)
        label.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.scene.addItem(rect_item)
        self.model.predicates[eid] = PredicateItem(
            id=eid, name=text, pos=pos, area_id=area, gfx_text=label, gfx_rect=rect_item
        )
        self._schedule_ligature_refresh()

    def _handle_ligature_click(self, pos: QPointF) -> None:
        if self._ligature_edge is None:
            pid = self._hit_predicate(pos)
            if pid is None:
                self.statusBar().showMessage("Click a predicate first")
                return
            self._ligature_edge = pid
            self.statusBar().showMessage(f"Ligature: edge {pid} selected; now click a vertex")
            self._log(f"LIGATURE begin edge={pid}")
        else:
            vid = self._hit_vertex(pos)
            if vid is None:
                self.statusBar().showMessage("Click a vertex to connect; ESC to cancel")
                return
            self.model.ligatures.setdefault(self._ligature_edge, []).append(vid)
            self.statusBar().showMessage(f"Ligature added: {self._ligature_edge} -> {vid}")
            self._log(f"LIGATURE add edge={self._ligature_edge} vertex={vid}")
            self._ligature_edge = None
            self._schedule_ligature_refresh()

    # ----- Save/Load/Export -----
    def on_new(self) -> None:
        self.scene.clear()
        self.model = DrawingModel()
        self._clear_ligature_visuals()
        self._update_preview()

    def on_save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Drawing", "drawing.json", "JSON (*.json)")
        if not path:
            return
        schema = self._gather_schema_from_scene()
        Path(path).write_text(json.dumps(schema, indent=2))
        QMessageBox.information(self, "Saved", f"Saved drawing to {path}")
        if self.act_auto.isChecked():
            self._update_preview()

    def on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Drawing", "", "JSON (*.json)")
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read JSON: {e}")
            return
        # Clear scene and model
        self.scene.clear()
        self.model = DrawingModel.from_schema(self.scene, data)
        # Replace plain rect items with constrained ones for future moves
        for cid, c in list(self.model.cuts.items()):
            old_item = c.gfx
            rect = self._scene_rect_for_item(old_item)
            new_item = CutRectItem(rect, self)
            new_item.setPen(old_item.pen())
            new_item.setBrush(old_item.brush())
            new_item.setFlag(QGraphicsItem.ItemIsMovable, True)
            new_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self.scene.addItem(new_item)
            self.scene.removeItem(old_item)
            self.model.cuts[cid].gfx = new_item
        QMessageBox.information(self, "Loaded", f"Loaded drawing from {path}")
        if self.act_auto.isChecked():
            self._update_preview()
        self._schedule_ligature_refresh()

    def on_export_egi(self) -> None:
        try:
            schema = self._gather_schema_from_scene()
            from drawing_to_egi_adapter import drawing_to_relational_graph
            from egi_spatial_correspondence import SpatialCorrespondenceEngine

            rgc = drawing_to_relational_graph(schema)
            # Basic console summary
            print("[EGI] sheet:", rgc.sheet)
            print("[EGI] V:", [v.id for v in rgc.V])
            print("[EGI] E:", [e.id for e in rgc.E])
            print("[EGI] Cut:", [c.id for c in rgc.Cut])
            print("[EGI] rel:", dict(rgc.rel))
            print("[EGI] nu:", {k: list(v) for k, v in rgc.nu.items()})
            # Try layout (may fail on cross-area ligatures; that's acceptable)
            try:
                engine = SpatialCorrespondenceEngine(rgc)
                layout = engine.generate_spatial_layout()
                types = {}
                for k, v in layout.items():
                    types[v.element_type] = types.get(v.element_type, 0) + 1
                print("[EGI] Layout types:", types)
                QMessageBox.information(self, "Exported", "EGI built. See console for summary.")
            except AssertionError as e:
                print("[EGI] Layout assertion:", e)
                QMessageBox.information(self, "Exported", "EGI built. Layout assertion encountered (see console).")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")
        finally:
            if self.act_auto.isChecked():
                self._update_preview()

    # Gather schema reflecting current positions and nesting
    def _gather_schema_from_scene(self) -> Dict:
        # Update rects and positions from gfx items
        for c in self.model.cuts.values():
            # Map rect with item's transform
            r = c.gfx.rect()
            top_left = c.gfx.mapToScene(r.topLeft())
            bottom_right = c.gfx.mapToScene(r.bottomRight())
            c.rect = QRectF(top_left, bottom_right).normalized()
        for v in self.model.vertices.values():
            v.pos = v.gfx.scenePos()
        for p in self.model.predicates.values():
            # Use rect position (text follows)
            p.pos = p.gfx_rect.scenePos()
            p.name = p.gfx_text.toPlainText() or p.id

        # Determine containment by point-in-rect
        def point_in_rect(pt: QPointF, rect: QRectF) -> bool:
            eps = 0.1
            return (rect.x() - eps <= pt.x() <= rect.x() + rect.width() + eps and
                    rect.y() - eps <= pt.y() <= rect.y() + rect.height() + eps)

        # Compute cut nesting depths and parent mapping
        cut_ids = list(self.model.cuts.keys())
        parent_map: Dict[str, Optional[str]] = {}
        for cid, c in self.model.cuts.items():
            # Parent is the deepest other cut whose rect contains this rect's center; else sheet
            center = c.rect.center()
            parent: Optional[str] = None
            best_depth = -1
            for oid, oc in self.model.cuts.items():
                if oid == cid:
                    continue
                if point_in_rect(center, oc.rect):
                    # depth approximated by containment chain length via current parent_map
                    depth = 1
                    pid = parent_map.get(oid)
                    while pid is not None:
                        depth += 1
                        pid = parent_map.get(pid)
                    if depth > best_depth:
                        best_depth = depth
                        parent = oid
            parent_map[cid] = parent if parent is not None else self.model.sheet_id

        # Determine area for vertices/predicates by their position
        def resolve_area(pos: QPointF) -> str:
            inside: List[Tuple[int, str]] = []
            for cid, c in self.model.cuts.items():
                if point_in_rect(pos, c.rect):
                    # depth = distance to sheet via parent_map
                    depth = 1
                    pid = parent_map.get(cid)
                    while pid is not None and pid in self.model.cuts:
                        depth += 1
                        pid = parent_map.get(pid)
                    inside.append((depth, cid))
            if inside:
                inside.sort()
                return inside[-1][1]
            return self.model.sheet_id

        vertices = []
        for v in self.model.vertices.values():
            vertices.append({"id": v.id, "area_id": resolve_area(v.pos)})
        predicates = []
        for p in self.model.predicates.values():
            predicates.append({"id": p.id, "name": p.name, "area_id": resolve_area(p.pos)})

        cuts = []
        for cid, c in self.model.cuts.items():
            cuts.append({"id": cid, "parent_id": parent_map.get(cid, self.model.sheet_id)})

        ligatures = [{"edge_id": e, "vertex_ids": vids} for e, vids in self.model.ligatures.items()]

        return {
            "sheet_id": self.model.sheet_id,
            "cuts": cuts,
            "vertices": vertices,
            "predicates": predicates,
            "ligatures": ligatures,
        }


class CutRectItem(QGraphicsRectItem):
    """Rect item that enforces EG cut constraints: nested or disjoint only."""
    def __init__(self, rect: QRectF, editor: "DrawingEditor") -> None:
        super().__init__(rect)
        self._editor = editor
        self._last_valid_scene_rect: QRectF = QRectF()
        self._press_pos: Optional[QPointF] = None
        # Create resize handles (8 grips)
        self._handles: List["CutHandleItem"] = []
        self._create_handles()
        self._update_handles()

    def mousePressEvent(self, event):
        # Start of drag/manipulation; suppress heavy refresh work
        try:
            self._editor.begin_interaction()
        except Exception:
            pass
        # Record current valid rect and position
        r = self.rect()
        tl = self.mapToScene(r.topLeft())
        br = self.mapToScene(r.bottomRight())
        self._last_valid_scene_rect = QRectF(tl, br).normalized()
        self._press_pos = self.pos()
        try:
            cid = self._editor._id_for_cut_item(self)
            sp = self.scenePos()
            self._editor._log(f"CUT_DRAG begin id={cid} pos=({sp.x():.1f},{sp.y():.1f}) rect={self._last_valid_scene_rect}")
        except Exception:
            pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # End of drag/manipulation; do one consolidated refresh
        try:
            # Validate final position; if invalid, snap back
            r = self.rect()
            tl = self.mapToScene(r.topLeft())
            br = self.mapToScene(r.bottomRight())
            new_scene_rect = QRectF(tl, br).normalized()
            if not self._editor._is_valid_cut_scene_rect(new_scene_rect, ignore_item=self):
                # revert to previous valid pos
                if self._press_pos is not None:
                    self.setPos(self._press_pos)
                try:
                    cid = self._editor._id_for_cut_item(self)
                    self._editor._log(f"CUT_DRAG end id={cid} result=invalid snap_back=1")
                except Exception:
                    pass
                self._editor.statusBar().showMessage("Invalid move: cuts must be nested or disjoint.")
            else:
                self._last_valid_scene_rect = new_scene_rect
                try:
                    cid = self._editor._id_for_cut_item(self)
                    sp = self.scenePos()
                    self._editor._log(f"CUT_DRAG end id={cid} result=ok pos=({sp.x():.1f},{sp.y():.1f}) rect={new_scene_rect}")
                except Exception:
                    pass
            self._update_handles()
        finally:
            try:
                self._editor.end_interaction()
            except Exception:
                pass

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Proposed new top-left position (in parent coords). Compute scene rect at that pos.
            new_pos = value
            # Temporarily compute scene rect by translating current rect to new pos relative to parent
            r = self.rect()
            # Map new tl and br to scene using parent's mapping
            parent = self.parentItem()
            if parent is None:
                tl_scene = self.mapToScene(r.topLeft()) + (new_pos - self.pos())
                br_scene = self.mapToScene(r.bottomRight()) + (new_pos - self.pos())
            else:
                # When parented, new_pos is in parent's coords; map points accordingly
                tl_parent = r.topLeft() + (new_pos - self.pos())
                br_parent = r.bottomRight() + (new_pos - self.pos())
                tl_scene = parent.mapToScene(tl_parent)
                br_scene = parent.mapToScene(br_parent)
            new_scene_rect = QRectF(tl_scene, br_scene).normalized()
            # During active drag, skip heavy validation to avoid UI stalls
            if not self._editor._interaction_active:
                if not self._editor._is_valid_cut_scene_rect(new_scene_rect, ignore_item=self):
                    self._editor.statusBar().showMessage("Invalid move: cuts must be nested or disjoint.")
                    return self.pos()  # veto move when not dragging
                else:
                    self._last_valid_scene_rect = new_scene_rect
        return super().itemChange(change, value)

    # ----- Resize handles helpers -----
    def _create_handles(self) -> None:
        # Lazily import type to avoid forward ref issues in type checkers
        roles = [
            "nw", "n", "ne",
            "e",
            "se", "s", "sw",
            "w",
        ]
        for role in roles:
            h = CutHandleItem(self, role)
            self._handles.append(h)

    def _update_handles(self) -> None:
        if not self._handles:
            return
        r = self.rect()
        s = 8.0  # handle size
        half = s / 2.0
        # Corner/edge centers in local coords
        points = {
            "nw": QPointF(r.left(), r.top()),
            "n": QPointF(r.center().x(), r.top()),
            "ne": QPointF(r.right(), r.top()),
            "e": QPointF(r.right(), r.center().y()),
            "se": QPointF(r.right(), r.bottom()),
            "s": QPointF(r.center().x(), r.bottom()),
            "sw": QPointF(r.left(), r.bottom()),
            "w": QPointF(r.left(), r.center().y()),
        }
        for h in self._handles:
            c = points[h.role]
            h.setRect(QRectF(c.x() - half, c.y() - half, s, s))


class CutHandleItem(QGraphicsRectItem):
    """Small grip used to resize a CutRectItem."""
    def __init__(self, parent_cut: CutRectItem, role: str) -> None:
        super().__init__(parent_cut)
        self._cut = parent_cut
        self.role = role  # one of: nw, n, ne, e, se, s, sw, w
        self.setZValue(parent_cut.zValue() + 5.0)
        self.setBrush(QBrush(QColor(0, 120, 255, 180)))
        self.setPen(QPen(QColor(255, 255, 255), 0))
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        # Cursor shape
        cursors = {
            "nw": Qt.SizeFDiagCursor,
            "se": Qt.SizeFDiagCursor,
            "ne": Qt.SizeBDiagCursor,
            "sw": Qt.SizeBDiagCursor,
            "n": Qt.SizeVerCursor,
            "s": Qt.SizeVerCursor,
            "e": Qt.SizeHorCursor,
            "w": Qt.SizeHorCursor,
        }
        self.setCursor(cursors[self.role])
        self._start_rect: Optional[QRectF] = None

    def mousePressEvent(self, event):
        # Begin resize interaction
        try:
            self._cut._editor.begin_interaction()
        except Exception:
            pass
        self._start_rect = QRectF(self._cut.rect())
        try:
            cid = self._cut._editor._id_for_cut_item(self._cut)
            sp = self._cut.scenePos()
            self._cut._editor._log(f"CUT_RESIZE begin id={cid} pos=({sp.x():.1f},{sp.y():.1f}) rect={self._start_rect} handle={self.role}")
        except Exception:
            pass
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._start_rect is None:
            self._start_rect = QRectF(self._cut.rect())
        # Map current mouse scene pos into cut's local coordinates
        scene_pt = event.scenePos()
        local_pt = self._cut.mapFromScene(scene_pt)
        r = QRectF(self._start_rect)
        min_w = 20.0
        min_h = 20.0
        # Adjust rectangle according to handle role
        if self.role in ("nw", "w", "sw"):
            r.setLeft(local_pt.x())
        if self.role in ("ne", "e", "se"):
            r.setRight(local_pt.x())
        if self.role in ("nw", "n", "ne"):
            r.setTop(local_pt.y())
        if self.role in ("sw", "s", "se"):
            r.setBottom(local_pt.y())
        r = r.normalized()
        if r.width() < min_w:
            cx = r.center().x()
            r.setLeft(cx - min_w / 2.0)
            r.setRight(cx + min_w / 2.0)
        if r.height() < min_h:
            cy = r.center().y()
            r.setTop(cy - min_h / 2.0)
            r.setBottom(cy + min_h / 2.0)
        # Apply without validation during drag for performance
        self._cut.setRect(r)
        self._cut._update_handles()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # Validate final rect; revert if invalid
        try:
            r = self._cut.rect()
            tl = self._cut.mapToScene(r.topLeft())
            br = self._cut.mapToScene(r.bottomRight())
            new_scene_rect = QRectF(tl, br).normalized()
            if not self._cut._editor._is_valid_cut_scene_rect(new_scene_rect, ignore_item=self._cut):
                if self._start_rect is not None:
                    self._cut.setRect(self._start_rect)
                    self._cut._update_handles()
                try:
                    cid = self._cut._editor._id_for_cut_item(self._cut)
                    self._cut._editor._log(f"CUT_RESIZE end id={cid} result=invalid snap_back=1")
                except Exception:
                    pass
                self._cut._editor.statusBar().showMessage("Invalid resize: cuts must be nested or disjoint.")
            else:
                try:
                    cid = self._cut._editor._id_for_cut_item(self._cut)
                    sp = self._cut.scenePos()
                    self._cut._editor._log(f"CUT_RESIZE end id={cid} result=ok pos=({sp.x():.1f},{sp.y():.1f}) rect={new_scene_rect}")
                except Exception:
                    pass
        finally:
            try:
                self._cut._editor.end_interaction()
            except Exception:
                pass

def main() -> int:
    app = QApplication(sys.argv)
    w = DrawingEditor()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
