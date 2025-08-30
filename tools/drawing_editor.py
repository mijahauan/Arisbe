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
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, QLineF
from PySide6.QtGui import QAction, QPen, QBrush, QColor, QKeySequence, QPainterPath
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
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
    QLabel,
)

## Ensure repository src/ is importable
try:
    REPO_ROOT = Path(__file__).resolve().parents[1]
    SRC_DIR = REPO_ROOT / "src"
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
except Exception:
    pass

# Optional: theming
try:
    import os
    from styling.style_manager import create_style_manager
except Exception:
    os = None  # type: ignore[assignment]
    create_style_manager = None  # type: ignore[assignment]

# EGDF adapter (platform-independent export)
try:
    from egdf_adapter import drawing_to_egdf_document
except Exception as _egdf_import_exc:  # log the reason for visibility
    try:
        import traceback
        print("[EGDF] Adapter import failed:")
        traceback.print_exc()
    except Exception:
        pass
    drawing_to_egdf_document = None  # type: ignore[assignment]

# EGDF parser (to load EGDF docs)
try:
    from egdf_parser import EGDFDocument
except Exception:
    EGDFDocument = None  # type: ignore[assignment]

# EGI/EGIF conversion utilities
try:
    from drawing_to_egi_adapter import drawing_to_relational_graph
    from egif_generator_dau import generate_egif
except Exception:
    drawing_to_relational_graph = None  # type: ignore[assignment]
    generate_egif = None  # type: ignore[assignment]

# Platform-agnostic constraint/validation controller
try:
    from controller import constraint_engine
except Exception:
    constraint_engine = None  # type: ignore[assignment]


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
    label: Optional[str] = None  # textual label
    label_kind: Optional[str] = None  # "constant" | "name"
    gfx_label: Optional[QGraphicsTextItem] = None


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
    predicate_outputs: Dict[str, str] = field(default_factory=dict)  # edge_id -> vertex_id

    def to_schema(self) -> Dict:
        return {
            "sheet_id": self.sheet_id,
            "cuts": [
                {"id": c.id, "parent_id": c.parent_id} for c in self.cuts.values()
            ],
            "vertices": [
                {
                    **{"id": v.id, "area_id": v.area_id},
                    **({"label": v.label} if v.label else {}),
                    **({"label_kind": v.label_kind} if v.label_kind else {}),
                }
                for v in self.vertices.values()
            ],
            "predicates": [
                {"id": p.id, "name": p.name, "area_id": p.area_id} for p in self.predicates.values()
            ],
            "ligatures": [
                {"edge_id": e, "vertex_ids": vids} for e, vids in self.ligatures.items()
            ],
            "predicate_outputs": self.predicate_outputs,
        }

    @classmethod
    def from_schema(cls, scene: QGraphicsScene, schema: Dict) -> "DrawingModel":
        model = cls(sheet_id=schema.get("sheet_id", "S"))
        # Cuts first
        for c in schema.get("cuts", []):
            rid = c["id"]
            # Place dummy rects; users can adjust later. For now, auto-grid.
            rect = QRectF(50 + 30 * len(model.cuts), 50 + 30 * len(model.cuts), 240, 160)
            gfx = CutRectItem(rect, editor=None)  # editor injected after editor constructed
            pen = QPen(QColor(0, 0, 0), 1)
            pen.setJoinStyle(Qt.RoundJoin)
            gfx.setPen(pen)
            gfx.setBrush(QBrush(QColor(240, 240, 240, 60)))
            gfx.setFlag(QGraphicsItem.ItemIsMovable, True)
            gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)
            scene.addItem(gfx)
            model.cuts[rid] = CutItem(id=rid, rect=rect, parent_id=c.get("parent_id"), gfx=gfx)
        # Vertices
        for v in schema.get("vertices", []):
            vid = v["id"]
            pos = QPointF(120 + 15 * len(model.vertices), 120)
            gfx = VertexGfxItem(-4, -4, 8, 8, editor=None)  # editor set after model/editor constructed
            gfx.setBrush(QBrush(QColor(0, 0, 0)))
            gfx.setPen(QPen(QColor(0, 0, 0), 2))
            gfx.setPos(pos)
            gfx.setFlag(QGraphicsItem.ItemIsMovable, True)
            gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)
            scene.addItem(gfx)
            vx = VertexItem(id=vid, pos=pos, area_id=v["area_id"], gfx=gfx)
            # Optional label rendering as child so it follows movement
            lbl = v.get("label")
            if lbl:
                vx.label = lbl
                vx.label_kind = v.get("label_kind")
                txt = QGraphicsTextItem(lbl)
                txt.setDefaultTextColor(QColor(20, 20, 20))
                txt.setPos(QPointF(6, -8))
                txt.setFlag(QGraphicsItem.ItemIsSelectable, False)
                txt.setFlag(QGraphicsItem.ItemIsMovable, False)
                txt.setParentItem(gfx)
                vx.gfx_label = txt
            model.vertices[vid] = vx
        # Predicates
        for p in schema.get("predicates", []):
            eid = p["id"]
            name = p.get("name", eid)
            pos = QPointF(200 + 20 * len(model.predicates), 120)
            text = QGraphicsTextItem(name)
            rect = text.boundingRect().adjusted(-4, -2, 4, 2)
            rect_item = PredicateRectItem(rect, editor=None)  # editor set after model/editor constructed
            # Transparent background and no border; ligatures will anchor to this rect's border
            rect_item.setBrush(Qt.NoBrush)
            rect_item.setPen(QPen(QColor(0, 0, 0, 0), 0))
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
        # Predicate outputs
        po = schema.get("predicate_outputs", {})
        if isinstance(po, dict):
            model.predicate_outputs = {str(k): str(v) for k, v in po.items()}
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
        self.resize(1200, 800)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 900, 600)
        self.view = QGraphicsView(self.scene)
        # Use a safer update mode to avoid residual trails during interactive resizes
        try:
            from PySide6.QtWidgets import QGraphicsView as _QV
            self.view.setViewportUpdateMode(_QV.BoundingRectViewportUpdate)
        except Exception:
            pass
        self.setCentralWidget(self.view)

        self.model = DrawingModel()
        # Visual ligature paths (single item per predicate-vertex link)
        self._ligature_items: List[QGraphicsPathItem] = []
        # Ligature drag state (vertex -> predicate)
        self._ligature_drag_from_vid: Optional[str] = None
        self._ligature_drag_path: Optional[QGraphicsPathItem] = None
        self._ligature_refresh_pending = False
        self._zorder_refresh_pending = False
        self._interaction_active = False
        # Debounce timer handle for auto-importing EGIF from the Corpus EGIF editor
        self._egif_autoload_pending: bool = False
        # Visual toggles and guards
        self._show_ligatures: bool = True
        self._suppress_scene_change: bool = False
        # Style/profile selection for deltas authoring and reader mode
        self.current_style_path: Optional[str] = None
        self.current_style_id: Optional[str] = None  # e.g., "dau-classic@1.0"
        # Theme manager (if available)
        self.styles = None
        try:
            if create_style_manager is not None:
                env_path = None
                if os is not None:
                    env_path = os.environ.get("ARISBE_THEME")
                self.styles = create_style_manager(env_path)
        except Exception:
            self.styles = None
        # Ergasterion app modes
        self.erg_mode: str = "composition"  # or "practice"
        self.semantic_guardrails: bool = False
        # EGI lock: when True, semantic guardrails apply (no area reassignment)
        self.egi_locked: bool = False
        # Puzzle Mode state: when arranging pieces to match a parsed EGI
        self.puzzle_mode_active: bool = False
        self._target_egi_meta: Optional[Dict[str, Any]] = None  # {'kind': 'egif_text'|'egi_inline', 'payload': ...}

        self.mode: str = Mode.SELECT
        self.active_parent_area: Optional[str] = None  # If a cut is selected before adding, that becomes parent/area

        # Temp vars for interactions
        self._drag_start: Optional[QPointF] = None
        self._cut_preview_item: Optional[QGraphicsRectItem] = None
        self._pending_predicate_name: Optional[str] = None
        self._ligature_edge: Optional[str] = None

        # Preview UI (dock)
        self._build_preview_dock()
        # Corpus guidance dock
        self._build_corpus_dock()
        # Toolbar
        self._build_toolbar()
        # Persistent status banner
        try:
            self.status_mode_label = QLabel()
            self.status_egi_label = QLabel()
            self.statusBar().addPermanentWidget(self.status_mode_label, 0)
            self.statusBar().addPermanentWidget(self.status_egi_label, 0)
            self._refresh_status_banner()
        except Exception:
            pass
        # Initial preview
        self._update_preview()
        # Keep visuals and z-order in sync with movements
        self.scene.changed.connect(self._on_scene_changed)
        # Selection visuals
        self.scene.selectionChanged.connect(self._on_selection_changed)
        # Inject editor backrefs into gfx subclasses now that editor exists
        self._inject_editor_backrefs_for_model()
        # Initial theme application (no-op if no items yet)
        try:
            self._apply_theme_styles()
        except Exception:
            pass

    # ----- Public mode API (for embedding shells) -----
    def set_composition_mode(self) -> None:
        """External toggle: set Composition Mode (unlocked)."""
        try:
            self._set_mode_composition()
        except Exception:
            # Fallback: ensure flags are consistent
            self.erg_mode = "composition"
            self.egi_locked = False
            try:
                self._refresh_status_banner()
            except Exception:
                pass

    def set_practice_mode(self) -> None:
        """External toggle: set Practice Mode (locked)."""
        try:
            self._set_mode_practice()
        except Exception:
            self.erg_mode = "practice"
            self.egi_locked = True
            try:
                self._refresh_status_banner()
            except Exception:
                pass

    # ----- Internal mode toggles -----
    def _set_mode_composition(self) -> None:
        """Switch to Composition (unlocked) and update UI state."""
        self.erg_mode = "composition"
        self.egi_locked = False
        try:
            # Sync toolbar checks if present
            if hasattr(self, 'act_mode_composition') and self.act_mode_composition is not None:
                self.act_mode_composition.setChecked(True)
            if hasattr(self, 'act_mode_practice') and self.act_mode_practice is not None:
                self.act_mode_practice.setChecked(False)
            if hasattr(self, 'act_egi_lock') and self.act_egi_lock is not None:
                self.act_egi_lock.setChecked(False)
        except Exception:
            pass
        self._set_mode(Mode.SELECT)
        self.statusBar().showMessage("Composition Mode (EGI unlocked)")
        self._refresh_status_banner()

    def _set_mode_practice(self) -> None:
        """Switch to Practice (locked) and update UI state."""
        self.erg_mode = "practice"
        self.egi_locked = True
        try:
            # Sync toolbar checks if present
            if hasattr(self, 'act_mode_composition') and self.act_mode_composition is not None:
                self.act_mode_composition.setChecked(False)
            if hasattr(self, 'act_mode_practice') and self.act_mode_practice is not None:
                self.act_mode_practice.setChecked(True)
            if hasattr(self, 'act_egi_lock') and self.act_egi_lock is not None:
                self.act_egi_lock.setChecked(True)
        except Exception:
            pass
        # Ensure items are guarded by constraint-enforcing gfx classes
        try:
            self._ensure_guarded_items()
        except Exception:
            pass
        self._set_mode(Mode.SELECT)
        self.statusBar().showMessage("Practice Mode (EGI locked)")
        self._refresh_status_banner()

    def _ensure_guarded_items(self) -> None:
        """Swap raw QGraphics* items to constraint-aware gfx items where needed.
        - Cuts -> CutRectItem
        - Vertices -> VertexGfxItem
        - Predicates -> PredicateRectItem
        Safe to call multiple times.
        """
        # Cuts
        try:
            self._rebuild_cuts_with_constraints_and_place()
        except Exception:
            pass
        # Vertices
        for vid, v in list(self.model.vertices.items()):
            if not isinstance(v.gfx, VertexGfxItem):
                pos = v.gfx.scenePos()
                try:
                    self.scene.removeItem(v.gfx)
                except Exception:
                    pass
                new_v = VertexGfxItem(-4, -4, 8, 8, self)
                new_v.setBrush(QBrush(QColor(0, 0, 0)))
                new_v.setPen(QPen(QColor(0, 0, 0), 2))
                new_v.setPos(pos)
                new_v.setFlag(QGraphicsItem.ItemIsMovable, True)
                new_v.setFlag(QGraphicsItem.ItemIsSelectable, True)
                self.scene.addItem(new_v)
                self.model.vertices[vid].gfx = new_v
        # Predicates
        for pid, p in list(self.model.predicates.items()):
            if not isinstance(p.gfx_rect, PredicateRectItem):
                # Compute rect in local and scene pos
                r = p.gfx_rect.rect()
                scene_pos = p.gfx_rect.scenePos()
                try:
                    self.scene.removeItem(p.gfx_rect)
                except Exception:
                    pass
                new_rect = PredicateRectItem(r, self)
                new_rect.setBrush(Qt.NoBrush)
                new_rect.setPen(QPen(QColor(0, 0, 0, 0), 0))
                new_rect.setPos(scene_pos)
                # Recreate text child
                label = QGraphicsTextItem(p.name)
                label.setParentItem(new_rect)
                label.setPos(4, 2)
                # Flags
                new_rect.setFlag(QGraphicsItem.ItemIsMovable, True)
                new_rect.setFlag(QGraphicsItem.ItemIsSelectable, True)
                label.setFlag(QGraphicsItem.ItemIsMovable, False)
                label.setFlag(QGraphicsItem.ItemIsSelectable, False)
                self.scene.addItem(new_rect)
                self.model.predicates[pid].gfx_rect = new_rect
                self.model.predicates[pid].gfx_text = label

    # ----- Utilities -----
    def _parse_qcolor(self, value: Any) -> QColor:
        """Convert common color encodings to QColor.
        Supports names, hex (#RRGGBB[AA]), and 'rgba(r,g,b,a)' with a in [0,1] or [0,255].
        Falls back to black fully transparent if invalid.
        """
        try:
            if isinstance(value, QColor):
                return value
            if isinstance(value, (tuple, list)) and len(value) in (3, 4):
                r, g, b = int(value[0]), int(value[1]), int(value[2])
                a = value[3] if len(value) == 4 else 255
                a = int(max(0, min(255, a if a > 1 else round(float(a) * 255))))
                return QColor(r, g, b, a)
            if isinstance(value, str):
                s = value.strip()
                if s.lower().startswith("rgba(") and s.endswith(")"):
                    inner = s[5:-1]
                    parts = [p.strip() for p in inner.split(",")]
                    if len(parts) == 4:
                        r = int(float(parts[0]))
                        g = int(float(parts[1]))
                        b = int(float(parts[2]))
                        raw_a = float(parts[3])
                        a = int(max(0, min(255, raw_a if raw_a > 1 else round(raw_a * 255))))
                        return QColor(r, g, b, a)
                # QColor can parse names and hex
                qc = QColor(s)
                if qc.isValid():
                    return qc
        except Exception:
            pass
        return QColor(0, 0, 0, 0)

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
        # Legacy add-mode actions are kept for internal use only but hidden from the toolbar UI.
        self.act_add_cut = make_action("Add Cut", True, lambda: self._set_mode(Mode.ADD_CUT))
        self.act_add_vertex = make_action("Add Vertex", True, lambda: self._set_mode(Mode.ADD_VERTEX))
        self.act_add_pred = make_action("Add Predicate", True, lambda: self._set_mode(Mode.ADD_PREDICATE))
        self.act_ligature = make_action("Ligature", True, lambda: self._set_mode(Mode.LIGATURE))
        # Hide these buttons to move to context-menu based insertion
        try:
            self.act_add_cut.setVisible(False)
            self.act_add_vertex.setVisible(False)
            self.act_add_pred.setVisible(False)
            self.act_ligature.setVisible(False)
        except Exception:
            pass

        tb.addSeparator()
        make_action("New", False, self.on_new)
        make_action("Save", False, self.on_save)
        make_action("Load", False, self.on_load)
        # Import EGIF text into the current scene (populate cuts/vertices/predicates)
        make_action("Import EGIF→Scene", False, self.on_import_egif_to_scene)
        make_action("Export EGI", False, self.on_export_egi)
        # Platform-independent EGDF export (logic + layout/styles/deltas)
        make_action("Export EGDF", False, self.on_export_egdf)

        tb.addSeparator()
        make_action("Select Style", False, self.on_select_style)
        make_action("Save Layout Deltas", False, self.on_save_layout_deltas)

        tb.addSeparator()
        # Ergasterion modes
        self.act_mode_composition = make_action("Composition Mode", True, self._set_mode_composition)
        self.act_mode_composition.setChecked(True)
        self.act_mode_practice = make_action("Practice Mode", True, self._set_mode_practice)
        self.act_mode_practice.setChecked(False)
        tb.addAction(self.act_mode_composition)
        tb.addAction(self.act_mode_practice)

        tb.addSeparator()
        # EGI lock toggle
        self.act_egi_lock = make_action("EGI Locked", True, self._toggle_egi_lock)
        self.act_egi_lock.setChecked(False)
        tb.addAction(self.act_egi_lock)

        # Validate & Lock (Puzzle Mode)
        self.act_validate_lock = make_action("Validate & Lock EGI", False, self._validate_and_lock_egi)
        tb.addAction(self.act_validate_lock)

        tb.addSeparator()
        self.act_preview = make_action("Preview", False, self._update_preview)
        self.act_auto = make_action("Auto Preview", True, None)
        # Default on so preview/selection sync works immediately
        self.act_auto.setChecked(True)
        tb.addAction(self.act_auto)

        # Toggle: Show Ligatures (visual only) — hidden now that we show by default
        self.act_show_ligs = make_action("Show Ligatures", True, self._toggle_show_ligatures)
        self.act_show_ligs.setChecked(True)
        try:
            self.act_show_ligs.setVisible(False)
        except Exception:
            pass
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
        # Internal mode setter; UI now uses context menus for add actions.
        try:
            for act in [self.act_select, self.act_add_cut, self.act_add_vertex, self.act_add_pred, self.act_ligature]:
                act.setChecked(False)
        except Exception:
            pass
        self.mode = mode
        try:
            mapping = {
                Mode.SELECT: self.act_select,
                Mode.ADD_CUT: self.act_add_cut,
                Mode.ADD_VERTEX: self.act_add_vertex,
                Mode.ADD_PREDICATE: self.act_add_pred,
                Mode.LIGATURE: self.act_ligature,
            }
            mapping[self.mode].setChecked(True)
        except Exception:
            pass
        self._refresh_status_banner()

    def _build_preview_dock(self) -> None:
        self.preview_dock = QDockWidget("Meaning (Current EGI)", self)
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
        # Note: Corpus dock is built in _build_corpus_dock()

    def _build_corpus_dock(self) -> None:
        self.corpus_dock = QDockWidget("Guide (Target EGI)", self)
        self.corpus_dock.setObjectName("corpusDock")
        # Tabs: show both the loaded corpus EGI JSON and its EGIF text
        corpus_tabs = QTabWidget(self.corpus_dock)
        self.txt_corpus_egi_json = QTextEdit()
        self.txt_corpus_egi_json.setReadOnly(True)
        self.txt_corpus_egif = QTextEdit()
        # Make editable so users can paste/type EGIF to initialize a scene
        try:
            self.txt_corpus_egif.setReadOnly(False)
            self.txt_corpus_egif.setPlaceholderText(
                "Paste or type EGIF here, then click 'Import EGIF→Scene' in the toolbar to build the diagram."
            )
        except Exception:
            # Fallback if placeholder not supported in environment
            self.txt_corpus_egif.setReadOnly(False)
        # Auto-parse on edit (debounced) to seed puzzle scene
        try:
            self.txt_corpus_egif.textChanged.connect(self._on_corpus_egif_changed)
        except Exception:
            pass
        corpus_tabs.addTab(self.txt_corpus_egi_json, "Corpus EGI (JSON)")
        corpus_tabs.addTab(self.txt_corpus_egif, "Corpus EGIF")
        self.corpus_dock.setWidget(corpus_tabs)
        self.addDockWidget(Qt.RightDockWidgetArea, self.corpus_dock)
        # Split vertically so both Preview and Guide are visible concurrently
        try:
            self.splitDockWidget(self.preview_dock, self.corpus_dock, Qt.Vertical)
        except Exception:
            pass

    def _schedule_preview(self) -> None:
        if self.act_auto.isChecked():
            # Debounce preview a bit to avoid thrashing during edits
            QTimer.singleShot(60, self._update_preview)

    def _update_preview(self) -> None:
        try:
            # Always gather and show current scene schema
            schema = self._gather_schema_from_scene()
            self.txt_egi.setPlainText(json.dumps(schema, indent=2))
            # Validate but do not clear previews on failure
            ok, msg = self._validate_syntactic_constraints()
            # Try EGIF generation regardless; generator will handle failures and return ""
            egif_text = self._schema_to_egif(schema)
            self.txt_egif.setPlainText(egif_text or "")
            if ok:
                self.statusBar().showMessage("Preview updated.")
            else:
                self.statusBar().showMessage(f"Syntactic validation failed: {msg} (preview shows current scene)")
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
        try:
            items = self.scene.selectedItems()
        except Exception:
            items = []
        for it in items:
            eid = self._id_for_item(it)
            if not eid:
                continue
            # Flash in current meaning (Preview)
            try:
                self._flash_in_editor(self.txt_egi, eid)
            except Exception:
                pass
            # Also try to flash in target corpus views (if present)
            try:
                if hasattr(self, 'txt_corpus_egi_json') and self.txt_corpus_egi_json is not None:
                    self._flash_in_editor(self.txt_corpus_egi_json, eid)
            except Exception:
                pass
    def _clear_ligature_visuals(self) -> None:
        for line in self._ligature_items:
            try:
                self.scene.removeItem(line)
            except Exception:
                pass
        self._ligature_items.clear()

    def _schedule_ligature_refresh(self) -> None:
        if not self._show_ligatures:
            # Keep visuals cleared when disabled
            if self._ligature_items:
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
        QTimer.singleShot(80, do_refresh)

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
        QTimer.singleShot(80, do_refresh)

    def _refresh_ligature_visuals(self) -> None:
        # Rebuild paths from predicates to vertices, honoring style-driven path mode
        self._suppress_scene_change = True
        try:
            self._clear_ligature_visuals()
            # Style-aware pens (fallback to legacy if style manager unavailable)
            if self.styles is not None:
                s = self.styles.resolve(type="edge", role="edge.identity")
                line_color = self._parse_qcolor(s.get("line_color", "#000000"))
                line_width = float(s.get("line_width", 3.5))
                base_pen = QPen(line_color, line_width)
                base_pen.setCosmetic(True)
                out_pen = QPen(QColor(40, 150, 60, 220), max(2.0, line_width))
                out_pen.setCosmetic(True)
                # Ligature path mode
                try:
                    s_path = self.styles.resolve(type="ligature", role="ligature.path")
                except Exception:
                    s_path = {}
            else:
                base_pen = QPen(QColor(80, 80, 200, 160), 1)
                base_pen.setCosmetic(True)
                out_pen = QPen(QColor(40, 150, 60, 220), 2)
                out_pen.setCosmetic(True)
                s_path = {}
            mode = str(s_path.get("mode", "straight")).lower()
            curvature = float(s_path.get("curvature", 0.35))
            ortho_bias = str(s_path.get("orthogonal_bias", "h_first")).lower()
            # Length of the trunk from the vertex to the first junction point for branching
            try:
                trunk_len = float(s_path.get("trunk_length", 24.0))
            except Exception:
                trunk_len = 24.0
            parent_map = self._compute_parent_map()
            # Build inverse map: vertex -> list[predicate_id]
            v_to_ps: Dict[str, List[str]] = {}
            for pid, vids in self.model.ligatures.items():
                for vid in vids:
                    v_to_ps.setdefault(vid, []).append(pid)

            for vid, pids in v_to_ps.items():
                v = self.model.vertices.get(vid)
                if v is None:
                    continue
                v_center = v.gfx.scenePos()
                # Determine z from vertex area
                v_area = self._resolve_area_position(v_center, parent_map)
                depth = self._area_depth(v_area, parent_map)

                # Collect predicate centers for this vertex
                p_centers: List[Tuple[str, QPointF]] = []
                for pid in pids:
                    p = self.model.predicates.get(pid)
                    if p is None:
                        continue
                    rect = p.gfx_rect.sceneBoundingRect()
                    p_centers.append((pid, rect.center()))
                if not p_centers:
                    continue

                # Single connection: simple segment from vertex to predicate border
                if len(p_centers) == 1:
                    pid, pc = p_centers[0]
                    # Anchor at predicate border in direction from vertex
                    p_rect = self.model.predicates[pid].gfx_rect.sceneBoundingRect()
                    pc = self._rect_border_anchor(p_rect, v_center)
                    path = QPainterPath(v_center)
                    if mode == "orthogonal":
                        self._build_orthogonal_path(path, v_center, pc, ortho_bias)
                    elif mode == "curved":
                        self._build_curved_path(path, v_center, pc, curvature)
                    else:
                        path.lineTo(pc)
                    item = QGraphicsPathItem(path)
                    try:
                        item.setData(0, pid)
                        item.setData(1, vid)
                    except Exception:
                        pass
                    item.setZValue(depth * 10.0)
                    if self.model.predicate_outputs.get(pid) == vid:
                        item.setPen(out_pen)
                    else:
                        item.setPen(base_pen)
                    self.scene.addItem(item)
                    self._ligature_items.append(item)
                    continue

                # Multiple connections: build a trunk to a junction, then branch to each predicate border
                # Junction heuristic: in direction of centroid of predicate centers, at length = trunk_len
                cx = sum(pc.x() for _, pc in p_centers) / float(len(p_centers))
                cy = sum(pc.y() for _, pc in p_centers) / float(len(p_centers))
                dirx = cx - v_center.x()
                diry = cy - v_center.y()
                dlen = (dirx * dirx + diry * diry) ** 0.5
                if dlen < 1e-6:
                    jx, jy = v_center.x(), v_center.y()
                else:
                    jx = v_center.x() + dirx / dlen * trunk_len
                    jy = v_center.y() + diry / dlen * trunk_len
                junction = QPointF(jx, jy)

                path = QPainterPath(v_center)
                # Trunk
                if mode == "orthogonal":
                    self._build_orthogonal_path(path, v_center, junction, ortho_bias)
                elif mode == "curved":
                    self._build_curved_path(path, v_center, junction, curvature)
                else:
                    path.lineTo(junction)
                # Branches from junction to each predicate
                for pid, pc in p_centers:
                    # Anchor at predicate border from junction
                    p_rect = self.model.predicates[pid].gfx_rect.sceneBoundingRect()
                    pc = self._rect_border_anchor(p_rect, junction)
                    path.moveTo(junction)
                    if mode == "orthogonal":
                        self._build_orthogonal_path(path, junction, pc, ortho_bias)
                    elif mode == "curved":
                        self._build_curved_path(path, junction, pc, curvature)
                    else:
                        path.lineTo(pc)

                item = QGraphicsPathItem(path)
                try:
                    # Store primary identifiers: vid on 1, and a comma-joined pid list on 0
                    item.setData(1, vid)
                    item.setData(0, ",".join(pids))
                except Exception:
                    pass
                item.setZValue(depth * 10.0)
                # If any predicate marks this vertex as output, highlight the whole ligature
                highlight = any(self.model.predicate_outputs.get(pid) == vid for pid in pids)
                item.setPen(out_pen if highlight else base_pen)
                self.scene.addItem(item)
                self._ligature_items.append(item)
        finally:
            self._suppress_scene_change = False

    def _build_orthogonal_path(self, path: QPainterPath, a: QPointF, b: QPointF, bias: str = "h_first") -> None:
        """Add an orthogonal elbow between a and b to the given path.
        bias: 'h_first' for horizontal-then-vertical, else vertical-then-horizontal.
        """
        if bias == "v_first":
            mid = QPointF(a.x(), b.y())
        else:
            mid = QPointF(b.x(), a.y())
        path.lineTo(mid)
        path.lineTo(b)

    def _rect_border_anchor(self, scene_rect: QRectF, from_point: QPointF) -> QPointF:
        """Return the intersection point of the line from from_point to the rect center with the rect border.
        If no intersection is found (degenerate), return the rect center.
        Inputs are in scene coordinates.
        """
        center = scene_rect.center()
        ray = QLineF(from_point, center)
        # Construct scene-space edges
        tl = scene_rect.topLeft()
        tr = scene_rect.topRight()
        bl = scene_rect.bottomLeft()
        br = scene_rect.bottomRight()
        edges = [
            QLineF(tl, tr),  # top
            QLineF(tr, br),  # right
            QLineF(br, bl),  # bottom
            QLineF(bl, tl),  # left
        ]
        best_pt: Optional[QPointF] = None
        for edge in edges:
            res = ray.intersects(edge)
            # PySide6 returns a tuple (IntersectionType, QPointF)
            try:
                itype, ipt = res
            except Exception:
                # Older bindings may require passing a QPointF by ref; fallback to center
                continue
            if itype == QLineF.IntersectionType.BoundedIntersection:
                best_pt = ipt
                break
        return best_pt if best_pt is not None else center

    def _build_curved_path(self, path: QPainterPath, a: QPointF, b: QPointF, curvature: float = 0.35) -> None:
        """Add a gentle quadratic Bezier curve from a to b. Curvature in [0..1]."""
        # Control point: offset perpendicular to the chord by curvature * chord_length * 0.5
        dx = b.x() - a.x()
        dy = b.y() - a.y()
        mx = (a.x() + b.x()) * 0.5
        my = (a.y() + b.y()) * 0.5
        # Perpendicular vector (normalized)
        length = max(1e-6, (dx*dx + dy*dy) ** 0.5)
        nx = -dy / length
        ny = dx / length
        offset = curvature * 0.5 * length
        cx = mx + nx * offset
        cy = my + ny * offset
        path.quadTo(QPointF(cx, cy), b)

    def _apply_theme_styles(self) -> None:
        """Apply basic style tokens to existing scene items.
        Minimal initial pass: cut borders/fill and predicate rect fill/border.
        Ligatures are styled in _refresh_ligature_visuals().
        """
        if self.styles is None:
            return
        # Scene background
        try:
            s_scene = self.styles.resolve(type="scene", role="scene.background")
            bg = self._parse_qcolor(s_scene.get("color", "#FFFFFF"))
            self.view.setBackgroundBrush(QBrush(bg))
        except Exception:
            pass
        # Cuts
        try:
            s_border = self.styles.resolve(type="cut", role="cut.border")
            s_fill_odd = self.styles.resolve(type="cut", role="cut.fill.odd")
        except Exception:
            s_border, s_fill_odd = {}, {}
        for cid, c in self.model.cuts.items():
            pen = c.gfx.pen()
            try:
                color = self._parse_qcolor(s_border.get("line_color", "#000000"))
                width = float(s_border.get("line_width", 1))
                pen.setColor(color)
                pen.setWidthF(width)
                c.gfx.setPen(pen)
            except Exception:
                pass
            try:
                fill = s_fill_odd.get("fill_color", "rgba(0,0,0,0)")
                c.gfx.setBrush(QBrush(self._parse_qcolor(fill)))
            except Exception:
                pass
        # Predicates (background only)
        try:
            s_edge_even = self.styles.resolve(type="edge", role="edge.fill.even")
        except Exception:
            s_edge_even = {}
        for pid, p in self.model.predicates.items():
            try:
                fill = s_edge_even.get("fill_color", "transparent")
                p.gfx_rect.setBrush(QBrush(self._parse_qcolor(fill)))
                pen = p.gfx_rect.pen()
                pen.setColor(self._parse_qcolor(s_edge_even.get("border_color", "transparent")))
                pen.setWidthF(float(s_edge_even.get("border_width", 0)))
                p.gfx_rect.setPen(pen)
            except Exception:
                pass
        # Rebuild ligature visuals with new pens
        self._schedule_ligature_refresh()

    # ----- Interaction throttle helpers -----
    def begin_interaction(self) -> None:
        self._interaction_active = True
        # Snapshot positions to allow snap-back in locked mode
        try:
            self._pre_interaction_positions = {
                "vertices": {vid: v.gfx.scenePos() for vid, v in self.model.vertices.items()},
                "predicates": {pid: p.gfx_rect.scenePos() for pid, p in self.model.predicates.items()},
                "cuts": {cid: c.gfx.sceneBoundingRect() for cid, c in self.model.cuts.items()},
            }
        except Exception:
            self._pre_interaction_positions = {"vertices": {}, "predicates": {}, "cuts": {}}

    def end_interaction(self) -> None:
        # End of a drag/manipulation: re-enable updates and do one refresh
        self._interaction_active = False
        self._schedule_ligature_refresh()
        self._schedule_zorder_refresh()
        # In unlocked mode, auto-reassign areas based on current positions
        try:
            if not self.egi_locked and constraint_engine is not None:
                changes = self._auto_reassign_areas_unlocked()
                # Surface a brief status message about reassignment
                if changes:
                    self.statusBar().showMessage("Reassigned: " + ", ".join(changes), 1500)
            elif self.egi_locked:
                # Locked mode: delegate move planning to controller (meaning-preserving)
                if constraint_engine is not None:
                    self._locked_mode_plan_and_apply_move()
                else:
                    # Fallback: Snap-back any items that violate their declared area
                    offenders_v, offenders_p = self._find_out_of_area_items()
                    if offenders_v or offenders_p:
                        for vid in offenders_v:
                            pos = self._pre_interaction_positions.get("vertices", {}).get(vid)
                            if pos is not None:
                                self.model.vertices[vid].gfx.setPos(pos)
                        for pid in offenders_p:
                            pos = self._pre_interaction_positions.get("predicates", {}).get(pid)
                            if pos is not None:
                                self.model.predicates[pid].gfx_rect.setPos(pos)
                        self.statusBar().showMessage("Locked: invalid drop outside declared area; snapped back.", 1500)
        except Exception:
            # Fail-open: do not block the UI if reassignment has issues
            pass
        # Also refresh the semantic preview (EGI/EGIF) after moves/resizes
        self._schedule_preview()

    def _locked_mode_plan_and_apply_move(self) -> None:
        """Detect a single-anchor move, delegate to controller.plan_move, apply or snap back."""
        try:
            # Detect anchor: exactly one of cut/vertex/predicate moved
            moved_cuts = []
            for cid, c in self.model.cuts.items():
                before = self._pre_interaction_positions.get("cuts", {}).get(cid)
                r = c.gfx.sceneBoundingRect()
                if before is not None and (abs(before.x() - r.x()) > 0.1 or abs(before.y() - r.y()) > 0.1):
                    moved_cuts.append((cid, before, r))
            moved_vertices = []
            for vid, v in self.model.vertices.items():
                before = self._pre_interaction_positions.get("vertices", {}).get(vid)
                now = v.gfx.scenePos()
                if before is not None and (abs(before.x() - now.x()) > 0.1 or abs(before.y() - now.y()) > 0.1):
                    moved_vertices.append((vid, before, now))
            moved_predicates = []
            for pid, p in self.model.predicates.items():
                before = self._pre_interaction_positions.get("predicates", {}).get(pid)
                now = p.gfx_rect.scenePos()
                if before is not None and (abs(before.x() - now.x()) > 0.1 or abs(before.y() - now.y()) > 0.1):
                    moved_predicates.append((pid, before, now))

            # Only handle simple case: exactly one anchor moved
            anchors = [("cut",) + t for t in moved_cuts] + [("vertex",) + t for t in moved_vertices] + [("predicate",) + t for t in moved_predicates]
            if len(anchors) != 1:
                # Defer to simple snap-back checks
                offenders_v, offenders_p = self._find_out_of_area_items()
                if offenders_v or offenders_p:
                    for vid in offenders_v:
                        pos = self._pre_interaction_positions.get("vertices", {}).get(vid)
                        if pos is not None:
                            self.model.vertices[vid].gfx.setPos(pos)
                    for pid in offenders_p:
                        pos = self._pre_interaction_positions.get("predicates", {}).get(pid)
                        if pos is not None:
                            self.model.predicates[pid].gfx_rect.setPos(pos)
                    self.statusBar().showMessage("Locked: invalid drop outside declared area; snapped back.", 1500)
                return

            kind, item_id, before, after = anchors[0]
            if kind == "cut":
                dx, dy = after.x() - before.x(), after.y() - before.y()
                selection = {"cuts": [item_id], "vertices": [], "predicates": []}
            elif kind == "vertex":
                dx, dy = after.x() - before.x(), after.y() - before.y()
                selection = {"cuts": [], "vertices": [item_id], "predicates": []}
            else:  # predicate
                dx, dy = after.x() - before.x(), after.y() - before.y()
                selection = {"cuts": [], "vertices": [], "predicates": [item_id]}

            # Build DTO and call controller
            dto = self._model_to_dto()
            subgraph = constraint_engine.select_subgraph(dto, selection)
            status, reason, changes = constraint_engine.plan_move(dto, subgraph, {"dx": float(dx), "dy": float(dy)}, locked=True)
            if status in ("ok", "adjusted") and changes:
                self._apply_layout_changes(changes)
                self.statusBar().showMessage("Locked: move applied (meaning-preserving).", 1200)
            else:
                # Revert anchor
                if kind == "cut":
                    c = self.model.cuts[item_id]
                    # Move back by -dx,-dy
                    c.gfx.moveBy(-dx, -dy)
                elif kind == "vertex":
                    self.model.vertices[item_id].gfx.setPos(before)
                else:
                    self.model.predicates[item_id].gfx_rect.setPos(before)
                self.statusBar().showMessage(f"Locked: move rejected ({reason}); snapped back.", 2000)
        except Exception as e:
            # Safety: do not block UI
            print(f"[LockedMove] error: {e}")
            pass

    def _apply_layout_changes(self, changes: Dict[str, Any]) -> None:
        """Apply controller-proposed geometry changes to scene items."""
        # Cuts
        for cid, upd in changes.items():
            if cid in self.model.cuts and "rect" in upd:
                x, y, w, h = upd["rect"]
                # Move by delta to preserve size without recomputing local rect
                cur = self.model.cuts[cid].gfx.sceneBoundingRect()
                self.model.cuts[cid].gfx.moveBy(x - cur.x(), y - cur.y())
        # Vertices
        for vid, upd in changes.items():
            if vid in self.model.vertices and "pos" in upd:
                px, py = upd["pos"]
                self.model.vertices[vid].gfx.setPos(px, py)
        # Predicates
        for pid, upd in changes.items():
            if pid in self.model.predicates and "rect" in upd:
                rx, ry, rw, rh = upd["rect"]
                # Move rect to (rx,ry)
                self.model.predicates[pid].gfx_rect.setPos(rx, ry)

    # ----- DTO adapter for controller -----
    def _model_to_dto(self) -> Dict[str, Any]:
        """Translate current scene/model to controller DTO (no Qt types)."""
        # Cuts: use scene-rects
        cuts: Dict[str, Dict[str, Any]] = {}
        for cid, c in self.model.cuts.items():
            r = c.gfx.rect()
            tl = c.gfx.mapToScene(r.topLeft())
            br = c.gfx.mapToScene(r.bottomRight())
            x, y = tl.x(), tl.y()
            w, h = (br.x() - tl.x()), (br.y() - tl.y())
            cuts[cid] = {"rect": (float(x), float(y), float(w), float(h)), "parent_id": c.parent_id}
        # Vertices: scenePos
        vertices: Dict[str, Dict[str, Any]] = {}
        for vid, v in self.model.vertices.items():
            sp = v.gfx.scenePos()
            vertices[vid] = {"pos": (float(sp.x()), float(sp.y())), "area_id": v.area_id}
        # Predicates: sceneBoundingRect
        predicates: Dict[str, Dict[str, Any]] = {}
        for pid, p in self.model.predicates.items():
            rb = p.gfx_rect.sceneBoundingRect()
            predicates[pid] = {"rect": (float(rb.x()), float(rb.y()), float(rb.width()), float(rb.height())), "area_id": p.area_id}
        # Ligatures: direct copy
        ligs: Dict[str, List[str]] = {str(e): [str(v) for v in vs] for e, vs in self.model.ligatures.items()}
        return {
            "sheet_id": self.model.sheet_id,
            "cuts": cuts,
            "vertices": vertices,
            "predicates": predicates,
            "ligatures": ligs,
        }

    def _auto_reassign_areas_unlocked(self) -> List[str]:
        """When composition (unlocked), update model area_ids based on positions.
        Uses controller.suggest_area_for_point() for deterministic assignment.
        """
        if constraint_engine is None:
            return []
        dto = self._model_to_dto()
        sheet_id = self.model.sheet_id
        changes: List[str] = []
        # Reassign vertices by scene position
        for vid, v in self.model.vertices.items():
            sp = v.gfx.scenePos()
            new_area = constraint_engine.suggest_area_for_point(dto, (float(sp.x()), float(sp.y())), sheet_id)
            if new_area and new_area != v.area_id:
                v.area_id = new_area
                changes.append(f"{vid}->{new_area}")
        # Reassign predicates by center of their rect
        for pid, p in self.model.predicates.items():
            rb = p.gfx_rect.sceneBoundingRect()
            cx, cy = float(rb.center().x()), float(rb.center().y())
            new_area = constraint_engine.suggest_area_for_point(dto, (cx, cy), sheet_id)
            if new_area and new_area != p.area_id:
                p.area_id = new_area
                changes.append(f"{pid}->{new_area}")
        return changes

    def _find_out_of_area_items(self) -> Tuple[List[str], List[str]]:
        """Return (vertex_ids, predicate_ids) currently outside their declared areas.
        GUI-only helper used for snap-back in locked mode.
        """
        # Build cut rects in scene coords
        rects: Dict[str, QRectF] = {}
        for cid, c in self.model.cuts.items():
            r = c.gfx.rect()
            tl = c.gfx.mapToScene(r.topLeft())
            br = c.gfx.mapToScene(r.bottomRight())
            rects[cid] = QRectF(tl, br).normalized()
        v_off: List[str] = []
        p_off: List[str] = []
        # Check vertices
        for vid, v in self.model.vertices.items():
            aid = v.area_id
            if aid and aid in rects:
                if not rects[aid].contains(v.gfx.scenePos()):
                    v_off.append(vid)
        # Check predicates by rect center
        for pid, p in self.model.predicates.items():
            aid = p.area_id
            if aid and aid in rects:
                center = p.gfx_rect.sceneBoundingRect().center()
                if not rects[aid].contains(center):
                    p_off.append(pid)
        return v_off, p_off

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
        # If exactly one element is selected, flash its id in the JSON preview
        try:
            selected_ids: List[str] = []
            for cid, c in self.model.cuts.items():
                if c.gfx.isSelected():
                    selected_ids.append(cid)
            for vid, v in self.model.vertices.items():
                if v.gfx.isSelected():
                    selected_ids.append(vid)
            for pid, p in self.model.predicates.items():
                if p.gfx_rect.isSelected():
                    selected_ids.append(pid)
            if len(selected_ids) == 1:
                self._flash_highlight_in_json(selected_ids[0])
        except Exception:
            pass

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
        # Cancel ligature drag with Esc
        if key == Qt.Key_Escape and self._ligature_drag_from_vid is not None:
            if self._ligature_drag_path is not None:
                try:
                    self.scene.removeItem(self._ligature_drag_path)
                except Exception:
                    pass
            self._ligature_drag_path = None
            self._ligature_drag_from_vid = None
            self.statusBar().showMessage("Ligature drag canceled")
            event.accept()
            return
        super().keyPressEvent(event)

    def _delete_selected_items(self) -> None:
        # Remove selected vertices/predicates/cuts; update model and ligatures
        if self.egi_locked:
            self.statusBar().showMessage("Practice/Locked: deletion is disabled.", 1500)
            return
        items = list(self.scene.selectedItems())
        if not items:
            return
        # Batch heavy updates during bulk delete
        self.begin_interaction()
        try:
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

            # Remove ligatures and predicate_outputs referencing removed items
            if remove_vertices or remove_predicates:
                # Ligatures
                new_ligs: Dict[str, List[str]] = {}
                for eid, vids in self.model.ligatures.items():
                    if eid in remove_predicates:
                        continue  # drop entire mapping
                    kept = [v for v in vids if v not in remove_vertices]
                    if kept:
                        new_ligs[eid] = kept
                self.model.ligatures = new_ligs
                # Predicate outputs
                new_outputs: Dict[str, str] = {}
                for eid, out_vid in self.model.predicate_outputs.items():
                    if eid in remove_predicates:
                        continue  # predicate itself removed
                    if out_vid in remove_vertices:
                        continue  # output vertex removed
                    new_outputs[eid] = out_vid
                self.model.predicate_outputs = new_outputs

            # Remove graphics and model entries
            for vid in remove_vertices:
                v = self.model.vertices.pop(vid, None)
                if v is not None:
                    if v.gfx_label is not None:
                        try:
                            v.gfx_label.setParentItem(None)
                            self.scene.removeItem(v.gfx_label)
                        except Exception:
                            pass
                        v.gfx_label = None
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
        finally:
            self.end_interaction()

    def _id_for_cut_item(self, item: QGraphicsRectItem) -> str:
        for cid, c in self.model.cuts.items():
            if c.gfx is item:
                return cid
        return "?"

    # ----- Z-order helpers -----
    def _compute_parent_map(self) -> Dict[str, Optional[str]]:
        # Map each cut to its parent cut or sheet using FULL RECT CONTAINMENT
        parent_map: Dict[str, Optional[str]] = {}
        # Ensure current rects are up to date
        for c in self.model.cuts.values():
            r = c.gfx.rect()
            tl = c.gfx.mapToScene(r.topLeft())
            br = c.gfx.mapToScene(r.bottomRight())
            c.rect = QRectF(tl, br).normalized()

        def rect_fully_inside(inner: QRectF, outer: QRectF, eps: float = 0.5) -> bool:
            return (
                outer.left() - eps <= inner.left() and
                outer.top() - eps <= inner.top() and
                outer.right() + eps >= inner.right() and
                outer.bottom() + eps >= inner.bottom()
            )

        # Choose the smallest fully containing cut as parent; otherwise sheet
        for cid, c in self.model.cuts.items():
            candidates: List[Tuple[float, str]] = []
            for oid, oc in self.model.cuts.items():
                if oid == cid:
                    continue
                if rect_fully_inside(c.rect, oc.rect):
                    candidates.append((oc.rect.width() * oc.rect.height(), oid))
            if candidates:
                candidates.sort()
                parent_map[cid] = candidates[0][1]
            else:
                parent_map[cid] = self.model.sheet_id

        # Defensive: break cycles by promoting to sheet
        for cid in list(parent_map.keys()):
            seen = set()
            pid = parent_map.get(cid)
            steps = 0
            while pid is not None and pid in self.model.cuts:
                if pid in seen or steps > 100:
                    parent_map[cid] = self.model.sheet_id
                    break
                seen.add(pid)
                pid = parent_map.get(pid)
                steps += 1

        return parent_map

    def _area_depth(self, area_id: Optional[str], parent_map: Dict[str, Optional[str]]) -> int:
        # Sheet has depth 0
        if area_id is None or area_id == self.model.sheet_id:
            return 0
        depth = 1
        pid = parent_map.get(area_id)
        seen = set()
        while pid is not None and pid in self.model.cuts:
            if pid in seen:
                # Cycle detected, break to avoid infinite loop
                break
            seen.add(pid)
            depth += 1
            pid = parent_map.get(pid)
            if depth > 100:
                # Defensive: break if depth is unreasonably high
                break
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
            # Also update ligature paths if present
            if self._ligature_items:
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

    # ----- Element placement guardrails -----
    def _parent_map_current(self) -> Dict[str, Optional[str]]:
        return self._compute_parent_map()

    def _cut_rect(self, cid: str) -> Optional[QRectF]:
        c = self.model.cuts.get(cid)
        if not c:
            return None
        r = c.gfx.rect()
        tl = c.gfx.mapToScene(r.topLeft())
        br = c.gfx.mapToScene(r.bottomRight())
        return QRectF(tl, br).normalized()

    def _descendants_of(self, cid: str, parent_map: Dict[str, Optional[str]]) -> List[str]:
        kids = {}
        for k, p in parent_map.items():
            kids.setdefault(p, []).append(k)
        out: List[str] = []
        stack = [cid]
        while stack:
            x = stack.pop()
            for ch in kids.get(x, []):
                out.append(ch)
                stack.append(ch)
        return out

    def _is_point_allowed_in_area(self, pt: QPointF, area_id: str, parent_map: Optional[Dict[str, Optional[str]]] = None) -> bool:
        pm = parent_map or self._parent_map_current()
        # Sheet: point must not be inside any cut
        if area_id == self.model.sheet_id:
            for cid in self.model.cuts.keys():
                cr = self._cut_rect(cid)
                if cr and cr.contains(pt):
                    return False
            return True
        # Within a cut: point must be inside that cut and not inside any of its descendants
        cr = self._cut_rect(area_id)
        if cr is None or not cr.contains(pt):
            return False
        for dcid in self._descendants_of(area_id, pm):
            dcr = self._cut_rect(dcid)
            if dcr and dcr.contains(pt):
                return False
        return True

    def _is_rect_allowed_in_area(self, rect: QRectF, area_id: str, parent_map: Optional[Dict[str, Optional[str]]] = None) -> bool:
        # Validate by testing rect corners and center
        pts = [rect.topLeft(), rect.topRight(), rect.bottomLeft(), rect.bottomRight(), rect.center()]
        return all(self._is_point_allowed_in_area(p, area_id, parent_map) for p in pts)

    def _element_area_id(self, item: QGraphicsItem) -> Optional[str]:
        # Return the assigned area_id for a vertex or predicate graphics item
        for v in self.model.vertices.values():
            if v.gfx is item:
                return v.area_id
        for p in self.model.predicates.values():
            if p.gfx_rect is item:
                return p.area_id
        return None

    def _generate_id(self, prefix: str) -> str:
        # Generate short unique IDs with a stable prefix
        return f"{prefix}_{uuid.uuid4().hex[:6]}"

    def _hit_cut(self, pos: QPointF) -> Optional[str]:
        """Return the topmost cut ID whose rect contains the scene position."""
        items = self.scene.items(pos)
        for it in items:
            for cid, c in self.model.cuts.items():
                if it is c.gfx:
                    try:
                        if c.gfx.contains(c.gfx.mapFromScene(pos)):
                            return cid
                    except Exception:
                        # Fallback to identity match if contains() not reliable
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

    def _hit_ligature_vertex(self, pos: QPointF) -> Optional[str]:
        # If right-clicking on a ligature line, treat as if clicking the vertex connected by that line
        items = self.scene.items(pos)
        for it in items:
            if isinstance(it, QGraphicsPathItem) and it in self._ligature_items:
                try:
                    vid = it.data(1)
                    if isinstance(vid, str):
                        return vid
                except Exception:
                    pass
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
                # Right-click context menus
                if event.button() == Qt.RightButton:
                    # Prefer vertex; else allow starting from existing ligature line
                    vid = self._hit_vertex(scene_pos) or self._hit_ligature_vertex(scene_pos)
                    if vid:
                        self._show_vertex_menu(scene_pos, vid)
                        return True
                    pid = self._hit_predicate(scene_pos)
                    if pid:
                        self._show_predicate_menu(scene_pos, pid)
                        return True
                    # Otherwise, show canvas-level menu for add actions
                    self._show_canvas_menu(scene_pos)
                    return True
                # If currently dragging a ligature, consume other presses to avoid conflicts
                if self._ligature_drag_from_vid is not None:
                    return True
                if self.mode == Mode.ADD_CUT:
                    # In locked mode, prevent starting a new cut
                    if self.egi_locked:
                        self._set_mode(Mode.SELECT)
                        self.statusBar().showMessage("Practice/Locked: adding cuts is disabled.", 1500)
                        return True
                    # Allow starting a nested cut inside an existing cut, but not when pressing on
                    # a vertex or predicate (to avoid moving them). Starting over a cut rect is OK.
                    hit_items = self.scene.items(scene_pos)
                    should_start = True
                    for it in hit_items:
                        # Block if clicking a vertex or predicate
                        for vid, v in self.model.vertices.items():
                            if it is v.gfx:
                                should_start = False
                                break
                        if not should_start:
                            break
                        for pid, p in self.model.predicates.items():
                            if it is p.gfx_rect or it is p.gfx_text:
                                should_start = False
                                break
                        if not should_start:
                            break
                    if should_start:
                        # When starting a cut, consume the press so existing cuts don't move
                        if self._drag_start is None:
                            # Suppress heavy scene-changed work during the drag of the preview rect
                            self.begin_interaction()
                            self._drag_start = scene_pos
                            # Create a lightweight dashed preview rect
                            try:
                                prev = QGraphicsRectItem(QRectF(scene_pos, scene_pos))
                                pen = QPen(QColor(50, 120, 220, 180), 1, Qt.DashLine)
                                pen.setCosmetic(True)
                                prev.setPen(pen)
                                prev.setBrush(QBrush(Qt.transparent))
                                prev.setZValue(9999)
                                self.scene.addItem(prev)
                                self._cut_preview_item = prev
                            except Exception:
                                self._cut_preview_item = None
                        return True
                    else:
                        # Let normal interaction proceed (e.g., selecting/moving items)
                        return False
                elif self.mode == Mode.ADD_VERTEX:
                    if self.egi_locked:
                        self._set_mode(Mode.SELECT)
                        self.statusBar().showMessage("Practice/Locked: adding vertices is disabled.", 1500)
                        return True
                    self._add_vertex(scene_pos)
                    self._schedule_preview()
                    # Return to baseline select mode after a single add
                    self._set_mode(Mode.SELECT)
                elif self.mode == Mode.ADD_PREDICATE:
                    if self.egi_locked:
                        self._set_mode(Mode.SELECT)
                        self.statusBar().showMessage("Practice/Locked: adding predicates is disabled.", 1500)
                        return True
                    self._add_predicate(scene_pos)
                    self._schedule_preview()
                    # Return to baseline select mode after a single add
                    self._set_mode(Mode.SELECT)
                return False
            elif event.type() == QEvent.MouseMove:
                # Update temporary ligature line during drag
                if self._ligature_drag_from_vid is not None and self._ligature_drag_path is not None:
                    scene_pos = self.view.mapToScene(event.position().toPoint())
                    v = self.model.vertices.get(self._ligature_drag_from_vid)
                    if v is not None:
                        p1 = v.gfx.scenePos()
                        p = QPainterPath(p1)
                        p.lineTo(scene_pos)
                        try:
                            self._ligature_drag_path.setPath(p)
                        except Exception:
                            pass
                    return True
                # Update cut preview rect while dragging
                if self.mode == Mode.ADD_CUT and self._drag_start is not None and self._cut_preview_item is not None:
                    scene_pos = self.view.mapToScene(event.position().toPoint())
                    rect = QRectF(self._drag_start, scene_pos).normalized()
                    try:
                        self._cut_preview_item.setRect(rect)
                    except Exception:
                        pass
                    return True
                return False
            elif event.type() == QEvent.MouseButtonRelease:
                scene_pos = self.view.mapToScene(event.position().toPoint())
                # Finish ligature drag on mouse release
                if self._ligature_drag_from_vid is not None:
                    try:
                        pid = self._hit_predicate(scene_pos)
                        if pid is not None:
                            # Commit ligature vid -> pid (edge maps to list of vids)
                            vids = self.model.ligatures.setdefault(pid, [])
                            if self._ligature_drag_from_vid not in vids:
                                vids.append(self._ligature_drag_from_vid)
                            self.statusBar().showMessage(f"Ligature added: {pid} <- {self._ligature_drag_from_vid}")
                            self._schedule_ligature_refresh()
                            self._schedule_preview()
                    finally:
                        # Cleanup temp line/state
                        if self._ligature_drag_path is not None:
                            try:
                                self.scene.removeItem(self._ligature_drag_path)
                            except Exception:
                                pass
                        self._ligature_drag_path = None
                        self._ligature_drag_from_vid = None
                    return True
                if self.mode == Mode.ADD_CUT and self._drag_start is not None:
                    scene_pos = self.view.mapToScene(event.position().toPoint())
                    self._finish_cut(self._drag_start, scene_pos)
                    self._drag_start = None
                    # Remove preview item
                    if self._cut_preview_item is not None:
                        try:
                            self.scene.removeItem(self._cut_preview_item)
                        except Exception:
                            pass
                        self._cut_preview_item = None
                    # Re-enable updates that were suppressed during the drag
                    self.end_interaction()
                    self._schedule_preview()
                    self._schedule_ligature_refresh()
                    # Return to baseline select mode after finishing the cut
                    self._set_mode(Mode.SELECT)
                return False
        return super().eventFilter(obj, event)

    # ----- Actions -----
    def _finish_cut(self, start: QPointF, end: QPointF) -> None:
        rect = QRectF(start, end).normalized()
        cid = self._generate_id("c")
        # Choose parent based on the final rect center, not the mouse-down point
        center = rect.center()
        try:
            parent_map = self._compute_parent_map()
            parent = self._resolve_area_position(center, parent_map)
        except Exception:
            # Fallback to start-based heuristic if anything goes wrong
            parent = self._current_area_for_add(start)
        # Validate syntactic constraint: no partial overlaps
        self._log(f"ADD_CUT attempt id={cid} rect={rect}")
        if not self._is_valid_cut_scene_rect(rect):
            self._log(f"ADD_CUT invalid id={cid} reason=partial_overlap")
            self.statusBar().showMessage("Invalid cut: cuts must be nested or disjoint (no partial overlaps).")
            return
        # Batch updates during add to avoid heavy recompute mid-operation
        self.begin_interaction()
        try:
            gfx = CutRectItem(rect, self)
            pen = QPen(QColor(0, 0, 0), 2)
            try:
                pen.setJoinStyle(Qt.RoundJoin)
            except Exception:
                pass
            gfx.setPen(pen)
            gfx.setBrush(QBrush(QColor(255, 255, 255, 0)))
            gfx.setFlag(QGraphicsItem.ItemIsMovable, True)
            gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self.scene.addItem(gfx)
            self.model.cuts[cid] = CutItem(id=cid, rect=rect, parent_id=parent, gfx=gfx)
            self._log(f"ADD_CUT ok id={cid} parent={parent}")
            # Schedule post-add refreshes
            self._schedule_zorder_refresh()
            self._schedule_ligature_refresh()
            self._schedule_preview()
        finally:
            self.end_interaction()

    def _add_vertex(self, pos: QPointF) -> None:
        vid = self._generate_id("v")
        area = self._current_area_for_add(pos)
        self._log(f"ADD_VERTEX id={vid} pos=({pos.x():.1f},{pos.y():.1f}) area={area}")
        gfx = VertexGfxItem(-4, -4, 8, 8, self)
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
        rect_item = PredicateRectItem(rect, self)
        rect_item.setBrush(Qt.NoBrush)
        rect_item.setPen(QPen(QColor(0, 0, 0, 0), 0))
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

    # ----- Context menus -----
    def _show_canvas_menu(self, scene_pos: QPointF) -> None:
        # In locked mode, block authoring operations
        if self.egi_locked:
            self.statusBar().showMessage("Practice/Locked: add operations are disabled.", 1500)
            return
        menu = QMenu(self)
        act_add_vertex = menu.addAction("Add Vertex here")
        act_add_pred = menu.addAction("Add Predicate here")
        act_add_cut = menu.addAction("Start Cut here (then drag)")
        chosen = menu.exec(self.view.mapToGlobal(self.view.mapFromScene(scene_pos)))
        if chosen is act_add_vertex:
            self._add_vertex(scene_pos)
            self._schedule_preview()
        elif chosen is act_add_pred:
            self._add_predicate(scene_pos)
            self._schedule_preview()
        elif chosen is act_add_cut:
            # Arm a cut starting at this position; user will drag to size and release to create
            self._set_mode(Mode.ADD_CUT)
            self._drag_start = scene_pos
            self.statusBar().showMessage("Cut armed: drag to define rectangle, release to create.")
    def _show_vertex_menu(self, scene_pos: QPointF, vid: str) -> None:
        menu = QMenu(self)
        # Edit name/label
        act_edit_name = menu.addAction("Edit vertex name…")
        # Start ligature drag
        act_drag = menu.addAction(f"Drag ligature from {vid}")
        # Delete vertex
        # Dynamic actions for existing connections
        connected_preds = [pid for pid, vids in self.model.ligatures.items() if vid in vids]
        if connected_preds:
            menu.addSeparator()
            # Remove ligature entries
            remove_actions = {}
            for pid in connected_preds:
                a = menu.addAction(f"Remove ligature to {pid}")
                remove_actions[a] = pid
            # Set output per predicate
            menu.addSeparator()
            setout_actions = {}
            for pid in connected_preds:
                label = f"Set as output of {pid}"
                a = menu.addAction(label)
                setout_actions[a] = pid
            # Clear output for any predicate where this vid is current output
            clearout_actions = {}
            for pid in connected_preds:
                if self.model.predicate_outputs.get(pid) == vid:
                    a = menu.addAction(f"Clear output of {pid}")
                    clearout_actions[a] = pid
        menu.addSeparator()
        act_del = menu.addAction("Delete vertex")
        chosen = menu.exec(self.view.mapToGlobal(self.view.mapFromScene(scene_pos)))
        if chosen is act_edit_name:
            v = self.model.vertices.get(vid)
            if v is None:
                return
            current = v.label or ""
            text, ok = QInputDialog.getText(self, "Edit Vertex Name", "Name (leave blank to clear):", text=current)
            if ok:
                new_label = text.strip()
                if not new_label:
                    # Clear label
                    v.label = None
                    v.label_kind = None
                    if v.gfx_label is not None:
                        try:
                            v.gfx_label.setParentItem(None)
                            self.scene.removeItem(v.gfx_label)
                        except Exception:
                            pass
                        v.gfx_label = None
                else:
                    v.label = new_label
                    # Treat user-provided vertex name as a constant identifier
                    v.label_kind = "constant"
                    if v.gfx_label is None:
                        txt = QGraphicsTextItem(new_label)
                        txt.setDefaultTextColor(QColor(20, 20, 20))
                        txt.setPos(QPointF(6, -8))
                        txt.setFlag(QGraphicsItem.ItemIsSelectable, False)
                        txt.setFlag(QGraphicsItem.ItemIsMovable, False)
                        txt.setParentItem(v.gfx)
                        v.gfx_label = txt
                    else:
                        v.gfx_label.setPlainText(new_label)
                self._schedule_preview()
                self._schedule_ligature_refresh()
        elif chosen is act_drag:
            # Start a temporary visual from this vertex to the cursor; finalize on release
            v = self.model.vertices.get(vid)
            if v is None:
                return
            tmp = QGraphicsPathItem()
            tmp.setPen(QPen(QColor(50, 120, 220, 180), 1, Qt.DashLine))
            p = v.gfx.scenePos()
            path = QPainterPath(p)
            path.lineTo(p)
            try:
                tmp.setPath(path)
            except Exception:
                pass
            tmp.setZValue(99999)
            self.scene.addItem(tmp)
            self._ligature_drag_from_vid = vid
            self._ligature_drag_path = tmp
            self.statusBar().showMessage("Drag to a predicate to add ligature; release to drop. Press Esc to cancel.")
        elif 'remove_actions' in locals() and chosen in remove_actions:
            pid = remove_actions[chosen]
            # Remove vid from pid's ligature list
            try:
                vids = self.model.ligatures.get(pid, [])
                self.model.ligatures[pid] = [x for x in vids if x != vid]
                self._schedule_ligature_refresh()
            except Exception:
                pass
            # If removed the output, clear it
            if self.model.predicate_outputs.get(pid) == vid:
                try:
                    del self.model.predicate_outputs[pid]
                except Exception:
                    pass
            self._schedule_ligature_refresh()
            self._schedule_preview()
        elif 'setout_actions' in locals() and chosen in setout_actions:
            pid = setout_actions[chosen]
            # Ensure the ligature exists
            vids = self.model.ligatures.setdefault(pid, [])
            if vid not in vids:
                vids.append(vid)
            self.model.predicate_outputs[pid] = vid
            self._schedule_ligature_refresh()
            self._schedule_preview()
        elif 'clearout_actions' in locals() and chosen in clearout_actions:
            pid = clearout_actions[chosen]
            try:
                del self.model.predicate_outputs[pid]
            except Exception:
                pass
            self._schedule_ligature_refresh()
            self._schedule_preview()
        elif chosen is act_del:
            # Select and delete via existing pipeline
            self.scene.clearSelection()
            v = self.model.vertices.get(vid)
            if v is not None:
                v.gfx.setSelected(True)
            self._delete_selected_items()

    def _show_predicate_menu(self, scene_pos: QPointF, pid: str) -> None:
        menu = QMenu(self)
        # Show ligature management for this predicate
        vids = list(self.model.ligatures.get(pid, []))
        remove_actions = {}
        setout_actions = {}
        clearout_action = None
        if vids:
            menu.addSection(f"Predicate {pid}")
            for vid in vids:
                a = menu.addAction(f"Remove ligature from {vid}")
                remove_actions[a] = vid
            menu.addSeparator()
            for vid in vids:
                a = menu.addAction(f"Set output to {vid}")
                setout_actions[a] = vid
            if self.model.predicate_outputs.get(pid):
                clearout_action = menu.addAction("Clear output")
            menu.addSeparator()
        act_del = menu.addAction("Delete predicate")
        chosen = menu.exec(self.view.mapToGlobal(self.view.mapFromScene(scene_pos)))
        if chosen in remove_actions:
            vid = remove_actions[chosen]
            self.model.ligatures[pid] = [v for v in self.model.ligatures.get(pid, []) if v != vid]
            if not self.model.ligatures[pid]:
                try:
                    del self.model.ligatures[pid]
                except Exception:
                    pass
            if self.model.predicate_outputs.get(pid) == vid:
                try:
                    del self.model.predicate_outputs[pid]
                except Exception:
                    pass
            self._schedule_ligature_refresh()
            self._schedule_preview()
        elif chosen in setout_actions:
            vid = setout_actions[chosen]
            vids = self.model.ligatures.setdefault(pid, [])
            if vid not in vids:
                vids.append(vid)
            self.model.predicate_outputs[pid] = vid
            self._schedule_ligature_refresh()
            self._schedule_preview()
        elif clearout_action is not None and chosen is clearout_action:
            try:
                del self.model.predicate_outputs[pid]
            except Exception:
                pass
            self._schedule_ligature_refresh()
            self._schedule_preview()
        elif chosen is act_del:
            self.scene.clearSelection()
            p = self.model.predicates.get(pid)
            if p is not None:
                p.gfx_rect.setSelected(True)
            self._delete_selected_items()

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
        # Allow loading drawing schema JSON, corpus JSON (with EGIF), or plain EGIF
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Drawing or EGIF",
            "",
            "JSON (*.json);;EGDF YAML (*.yaml *.yml);;EGIF (*.egif *.txt);;All Files (*)",
        )
        if not path:
            return
        p = Path(path)
        text = None
        data = None
        try:
            if p.suffix.lower() == ".json":
                data = json.loads(p.read_text())
            elif p.suffix.lower() in (".yaml", ".yml"):
                text = p.read_text()
            else:
                text = p.read_text().strip()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read file: {e}\nPath: {path}")
            return

        # Case 0: EGDF (JSON/YAML)
        if (isinstance(data, dict) and ("egdf" in data or "egi_ref" in data)) or (isinstance(text, str) and ("egdf:" in text or "egi_ref:" in text)):
            if EGDFDocument is None:
                QMessageBox.critical(self, "Unavailable", "EGDF parser not available (missing src.egdf_parser).")
                return
            try:
                if isinstance(data, dict):
                    doc = EGDFDocument.from_dict(data)
                else:
                    # YAML or JSON string
                    if p.suffix.lower() in (".yaml", ".yml"):
                        doc = EGDFDocument.from_yaml(text or "")
                    else:
                        doc = EGDFDocument.from_json(text or "")
            except Exception as e:
                QMessageBox.critical(self, "EGDF Error", f"Failed to parse EGDF: {e}")
                return

            # Build drawing schema from inline EGI and populate scene
            inline = doc.egi_ref.get("inline") if isinstance(doc.egi_ref, dict) else None
            if not inline:
                QMessageBox.critical(self, "EGDF Error", "EGDF missing inline EGI (egi_ref.inline)")
                return
            try:
                schema = self._schema_from_egi_inline(inline)  # type: ignore[arg-type]
            except Exception as e:
                QMessageBox.critical(self, "EGDF Error", f"Failed to convert EGI inline to scene schema: {e}")
                return

            self.begin_interaction()
            try:
                self.scene.clear()
                self.model = DrawingModel.from_schema(self.scene, schema)
                self._inject_editor_backrefs_for_model()
                self._rebuild_cuts_with_constraints_and_place()
                # Apply layout and then deltas to restore positions/sizes
                try:
                    self._apply_egdf_layout(doc.layout)
                except Exception as e:
                    print(f"[EGDF] layout apply warning: {e}")
                try:
                    self._apply_egdf_deltas(doc.deltas or [])
                except Exception as e:
                    print(f"[EGDF] deltas apply warning: {e}")
                self._schedule_zorder_refresh()
                self._schedule_ligature_refresh()
                if self.act_auto.isChecked():
                    self._update_preview()
            finally:
                self.end_interaction()

            # Populate Guide panels with target EGI (JSON and EGIF) for reference
            try:
                if hasattr(self, "txt_corpus_egi_json") and self.txt_corpus_egi_json is not None:
                    self.txt_corpus_egi_json.setPlainText(json.dumps(inline, indent=2))
                if hasattr(self, "txt_corpus_egif") and self.txt_corpus_egif is not None:
                    guide_egif = self._schema_to_egif(schema)
                    self.txt_corpus_egif.setPlainText(guide_egif or "")
            except Exception:
                pass

            QMessageBox.information(self, "Loaded EGDF", f"Loaded EGDF from {path}")
            # Treat EGDF load as puzzle target unlocked until user validates
            self.egi_locked = False
            self.puzzle_mode_active = True
            self._target_egi_meta = {"kind": "egi_inline", "payload": inline}
            if hasattr(self, 'act_egi_lock'):
                self.act_egi_lock.setChecked(False)
            self.statusBar().showMessage("Puzzle Mode: syntactic-only. Arrange to match EGI, then Validate & Lock.")
            self._refresh_status_banner()
            return

        # Case 1: Drawing schema JSON (our sandbox format)
        if isinstance(data, dict) and any(k in data for k in ("cuts", "vertices", "predicates", "ligatures")):
            self.scene.clear()
            self.model = DrawingModel.from_schema(self.scene, data)
            # Replace plain rect items with constrained ones and do hierarchical placement
            self._rebuild_cuts_with_constraints_and_place()
            QMessageBox.information(self, "Loaded", f"Loaded drawing from {path}")
            # Scratch drawing schema: unlock EGI
            self.egi_locked = False
            if hasattr(self, 'act_egi_lock'):
                self.act_egi_lock.setChecked(False)
            self.statusBar().showMessage("EGI unlocked (syntactic guardrails only).")
            self._refresh_status_banner()
            if self.act_auto.isChecked():
                self._update_preview()
            self._schedule_ligature_refresh()
            return

        # Case 2: Corpus JSON entry with EGIF content
        if isinstance(data, dict):
            egif_text = data.get("egif_content") or data.get("egif") or data.get("eg_graph")
            # Populate Corpus Guide JSON view with the raw corpus entry
            try:
                if hasattr(self, "txt_corpus_egi_json") and self.txt_corpus_egi_json is not None:
                    self.txt_corpus_egi_json.setPlainText(json.dumps(data, indent=2))
            except Exception:
                pass
            if egif_text:
                # Update Corpus Guide EGIF preview
                if hasattr(self, "txt_corpus_egif") and self.txt_corpus_egif is not None:
                    self.txt_corpus_egif.setPlainText(str(egif_text))
                else:
                    # Fallback if corpus dock not present
                    self.txt_egif.setPlainText(str(egif_text))
                # Parse EGIF and populate scene so Preview reflects current meaning
                try:
                    from egif_parser_dau import parse_egif
                    rgc = parse_egif(str(egif_text))
                except Exception as e:
                    QMessageBox.critical(self, "Parse Error", f"Failed to parse EGIF from corpus entry: {e}")
                    return
                try:
                    schema = self._schema_from_relational_graph(rgc)
                except Exception as e:
                    QMessageBox.critical(self, "Conversion Error", f"Failed to convert parsed EGIF to scene schema: {e}")
                    return
                self.begin_interaction()
                try:
                    self.scene.clear()
                    self.model = DrawingModel.from_schema(self.scene, schema)
                    self._inject_editor_backrefs_for_model()
                    self._rebuild_cuts_with_constraints_and_place()
                    self._schedule_zorder_refresh()
                    self._schedule_ligature_refresh()
                    if self.act_auto.isChecked():
                        self._update_preview()
                finally:
                    self.end_interaction()
                QMessageBox.information(self, "Loaded EGIF", f"Loaded EGIF from corpus entry: {data.get('id', p.name)}")
                # Puzzle Mode semantics on external load: syntactic-only until Validate & Lock
                self.egi_locked = False
                self.puzzle_mode_active = True
                self._target_egi_meta = {"kind": "egif_text", "payload": str(egif_text)}
                if hasattr(self, 'act_egi_lock'):
                    self.act_egi_lock.setChecked(False)
                self.statusBar().showMessage("Puzzle Mode: syntactic-only. Arrange to match EGI, then Validate & Lock.")
                self._refresh_status_banner()
                return

        # Case 3: EGI JSON (inline) => convert to drawing schema and place
        if isinstance(data, dict) and all(k in data for k in ("V", "E", "Cut", "area", "nu")):
            try:
                schema = self._schema_from_egi_inline(data)
            except Exception as e:
                QMessageBox.critical(self, "EGI JSON Error", f"Failed to interpret EGI JSON: {e}")
                return
            self.scene.clear()
            self.model = DrawingModel.from_schema(self.scene, schema)
            self._rebuild_cuts_with_constraints_and_place()
            QMessageBox.information(self, "Loaded", f"Loaded EGI and built scene from {path}")
            # Populate Guide panels with the target EGI (JSON and EGIF)
            try:
                if hasattr(self, "txt_corpus_egi_json") and self.txt_corpus_egi_json is not None:
                    self.txt_corpus_egi_json.setPlainText(json.dumps(data, indent=2))
                if hasattr(self, "txt_corpus_egif") and self.txt_corpus_egif is not None:
                    guide_egif = self._schema_to_egif(schema)
                    self.txt_corpus_egif.setPlainText(guide_egif or "")
            except Exception:
                pass
            # Inline EGI for Puzzle Mode: unlock and activate puzzle state
            self.egi_locked = False
            self.puzzle_mode_active = True
            self._target_egi_meta = {"kind": "egi_inline", "payload": data}
            if hasattr(self, 'act_egi_lock'):
                self.act_egi_lock.setChecked(False)
            self.statusBar().showMessage("Puzzle Mode: syntactic-only. Arrange to match EGI, then Validate & Lock.")
            self._refresh_status_banner()
            if self.act_auto.isChecked():
                self._update_preview()
            self._schedule_ligature_refresh()
            return

        # Case 4: Plain EGIF text file
        if isinstance(text, str) and text:
            # Populate Guide EGIF
            if hasattr(self, "txt_corpus_egif") and self.txt_corpus_egif is not None:
                self.txt_corpus_egif.setPlainText(text)
            else:
                self.txt_egif.setPlainText(text)
            # Parse EGIF and populate scene
            try:
                from egif_parser_dau import parse_egif
                rgc = parse_egif(text)
            except Exception as e:
                QMessageBox.critical(self, "Parse Error", f"Failed to parse EGIF text: {e}")
                return
            try:
                schema = self._schema_from_relational_graph(rgc)
            except Exception as e:
                QMessageBox.critical(self, "Conversion Error", f"Failed to convert parsed EGIF to scene schema: {e}")
                return
            self.begin_interaction()
            try:
                self.scene.clear()
                self.model = DrawingModel.from_schema(self.scene, schema)
                self._inject_editor_backrefs_for_model()
                self._rebuild_cuts_with_constraints_and_place()
                self._schedule_zorder_refresh()
                self._schedule_ligature_refresh()
                if self.act_auto.isChecked():
                    self._update_preview()
            finally:
                self.end_interaction()
            QMessageBox.information(self, "Loaded EGIF", f"Loaded EGIF text from {path}")
            # Puzzle Mode semantics
            self.egi_locked = False
            self.puzzle_mode_active = True
            self._target_egi_meta = {"kind": "egif_text", "payload": text}
            if hasattr(self, 'act_egi_lock'):
                self.act_egi_lock.setChecked(False)
            self.statusBar().showMessage("Puzzle Mode: syntactic-only. Arrange to match EGI, then Validate & Lock.")
            self._refresh_status_banner()
            return

        QMessageBox.warning(self, "Unrecognized File", "File did not match drawing schema or contain EGIF content.")

    def _apply_egdf_layout(self, layout: Dict[str, Any]) -> None:
        """Apply EGDF.layout positions/sizes to current scene items.
        Expects coordinates in scene units (px).
        """
        if not isinstance(layout, dict):
            return
        # Cuts
        for cid, r in layout.get("cuts", {}).items():
            c = self.model.cuts.get(cid)
            if not c:
                continue
            try:
                x = float(r.get("x", 0.0)); y = float(r.get("y", 0.0))
                w = float(r.get("w", c.gfx.rect().width()))
                h = float(r.get("h", c.gfx.rect().height()))
            except Exception:
                continue
            c.gfx.setRect(QRectF(x, y, w, h))
        # Vertices
        for vid, v in layout.get("vertices", {}).items():
            vx = self.model.vertices.get(vid)
            if not vx:
                continue
            try:
                x = float(v.get("x", vx.gfx.scenePos().x()))
                y = float(v.get("y", vx.gfx.scenePos().y()))
            except Exception:
                continue
            vx.gfx.setPos(QPointF(x, y))
            vx.pos = QPointF(x, y)
        # Predicates
        for pid, r in layout.get("predicates", {}).items():
            p = self.model.predicates.get(pid)
            if not p:
                continue
            try:
                x = float(r.get("x", p.gfx_rect.scenePos().x()))
                y = float(r.get("y", p.gfx_rect.scenePos().y()))
                w = float(r.get("w", p.gfx_rect.rect().width()))
                h = float(r.get("h", p.gfx_rect.rect().height()))
            except Exception:
                continue
            # Update text if provided
            try:
                txt = r.get("text")
                if isinstance(txt, str) and txt:
                    p.gfx_text.setPlainText(txt)
                    p.name = txt
            except Exception:
                pass
            p.gfx_rect.setRect(QRectF(0, 0, w, h))
            p.gfx_rect.setPos(QPointF(x, y))
            p.pos = QPointF(x, y)
        # Refresh visuals derived from geometry
        self._schedule_ligature_refresh()

    def _apply_egdf_deltas(self, deltas: List[Dict[str, Any]]) -> None:
        """Apply EGDF.deltas to the scene. Supports set_rect, set_position, translate.
        Unknown ops are ignored with a console note.
        """
        if not isinstance(deltas, list):
            return
        for d in deltas:
            if not isinstance(d, dict):
                continue
            op = d.get("op")
            if op == "set_rect":
                _id = d.get("id")
                if not isinstance(_id, str):
                    continue
                x = float(d.get("x", 0.0)); y = float(d.get("y", 0.0))
                w = float(d.get("w", 0.0)); h = float(d.get("h", 0.0))
                if _id in self.model.cuts:
                    self.model.cuts[_id].gfx.setRect(QRectF(x, y, w, h))
                elif _id in self.model.predicates:
                    pr = self.model.predicates[_id]
                    pr.gfx_rect.setRect(QRectF(0, 0, w, h))
                    pr.gfx_rect.setPos(QPointF(x, y))
                    pr.pos = QPointF(x, y)
            elif op == "set_position":
                _id = d.get("id")
                if not isinstance(_id, str):
                    continue
                x = float(d.get("x", 0.0)); y = float(d.get("y", 0.0))
                if _id in self.model.vertices:
                    self.model.vertices[_id].gfx.setPos(QPointF(x, y))
                    self.model.vertices[_id].pos = QPointF(x, y)
                elif _id in self.model.predicates:
                    pr = self.model.predicates[_id]
                    pr.gfx_rect.setPos(QPointF(x, y))
                    pr.pos = QPointF(x, y)
            elif op == "translate":
                # Move any known element by dx,dy
                _id = d.get("id") or d.get("edge_id")
                if not isinstance(_id, str):
                    continue
                dx = float(d.get("dx", 0.0)); dy = float(d.get("dy", 0.0))
                if _id in self.model.vertices:
                    item = self.model.vertices[_id]
                    cur = item.gfx.scenePos()
                    item.gfx.setPos(QPointF(cur.x() + dx, cur.y() + dy))
                    item.pos = item.gfx.scenePos()
                elif _id in self.model.predicates:
                    pr = self.model.predicates[_id]
                    cur = pr.gfx_rect.scenePos()
                    pr.gfx_rect.setPos(QPointF(cur.x() + dx, cur.y() + dy))
                    pr.pos = pr.gfx_rect.scenePos()
                elif _id in self.model.cuts:
                    c = self.model.cuts[_id]
                    r = c.gfx.rect()
                    c.gfx.setRect(QRectF(r.x() + dx, r.y() + dy, r.width(), r.height()))
            else:
                try:
                    print(f"[EGDF] Unknown delta op ignored: {op}")
                except Exception:
                    pass
        # Reflect changes in previews/visuals
        self._schedule_ligature_refresh()

    def on_import_egif_to_scene(self) -> None:
        """Import EGIF text and populate the scene (cuts/vertices/predicates/ligatures).
        Sources:
        - If Corpus Guide EGIF dock has content, default to that text (confirm overwrite).
        - Otherwise, prompt to open an EGIF text file.
        """
        # Prefer corpus guide text if present
        egif_text: Optional[str] = None
        if hasattr(self, "txt_corpus_egif") and self.txt_corpus_egif is not None:
            egif_text = self.txt_corpus_egif.toPlainText().strip() or None

        if not egif_text:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Import EGIF to Scene",
                "",
                "EGIF (*.egif *.txt);;All Files (*)",
            )
            if not path:
                return
            try:
                egif_text = Path(path).read_text().strip()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read EGIF: {e}")
                return

        if not egif_text:
            QMessageBox.warning(self, "No EGIF", "No EGIF text available to import.")
            return

        # Parse EGIF to RelationalGraphWithCuts
        try:
            from egif_parser_dau import parse_egif
            rgc = parse_egif(egif_text)
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Failed to parse EGIF: {e}")
            return

        # Convert graph to our drawing schema (area relationships only; positions auto)
        try:
            schema = self._schema_from_relational_graph(rgc)
        except Exception as e:
            QMessageBox.critical(self, "Conversion Error", f"Failed to convert graph: {e}")
            return

        # Populate scene with batching to prevent stalls
        self.begin_interaction()
        try:
            self.scene.clear()
            self.model = DrawingModel.from_schema(self.scene, schema)
            # Replace plain rects with constrained CutRectItem instances and place hierarchically
            self._rebuild_cuts_with_constraints_and_place()
            # Apply proposed layout from SpatialCorrespondenceEngine
            try:
                from egi_spatial_correspondence import SpatialCorrespondenceEngine
                from drawing_to_egi_adapter import drawing_to_relational_graph as _d2r
                rgc_layout = _d2r(schema)
                eng = SpatialCorrespondenceEngine(rgc_layout)
                layout = eng.generate_spatial_layout()
                self._apply_proposed_layout(layout)
            except Exception as _e:
                # Non-fatal: keep default auto positions
                try:
                    print(f"[EGI] Proposed layout unavailable: {_e}")
                except Exception:
                    pass
            self._schedule_zorder_refresh()
            self._schedule_ligature_refresh()
            self._schedule_preview()
        finally:
            self.end_interaction()

        # Enter Puzzle Mode semantics when importing EGIF
        try:
            self.egi_locked = False
            self.puzzle_mode_active = True
            self._target_egi_meta = {"kind": "egif_text", "payload": str(egif_text)}
            if hasattr(self, 'act_egi_lock'):
                self.act_egi_lock.setChecked(False)
            self.statusBar().showMessage("Puzzle Mode: syntactic-only. Arrange to match EGI, then Validate & Lock.")
            # Also show EGIF in the Guide tab
            if hasattr(self, "txt_corpus_egif") and self.txt_corpus_egif is not None:
                self.txt_corpus_egif.setPlainText(str(egif_text))
        except Exception:
            pass
        QMessageBox.information(self, "Imported", "EGIF imported into the scene.")

    def _apply_proposed_layout(self, layout: Dict[str, Any]) -> None:
        """Apply SpatialCorrespondenceEngine layout to current scene elements.
        Expects a dict of SpatialElement with element_type and spatial_bounds.
        """
        try:
            # Cuts: set rectangles to proposed bounds
            for cid, cut in self.model.cuts.items():
                le = layout.get(cid)
                if not le:
                    continue
                b = getattr(le, 'spatial_bounds', None)
                if not b:
                    continue
                rect = QRectF(float(b.x), float(b.y), float(b.width), float(b.height))
                try:
                    cut.gfx.setRect(rect)
                except Exception:
                    pass
                cut.rect = rect
            # Vertices: center points from bounds
            for vid, v in self.model.vertices.items():
                le = layout.get(vid)
                if not le:
                    continue
                b = getattr(le, 'spatial_bounds', None)
                if not b:
                    continue
                cx = float(b.x) + float(b.width) / 2.0
                cy = float(b.y) + float(b.height) / 2.0
                try:
                    v.gfx.setPos(QPointF(cx, cy))
                except Exception:
                    pass
                v.pos = QPointF(cx, cy)
            # Predicates: place rects by top-left bounds
            for eid, p in self.model.predicates.items():
                le = layout.get(eid)
                if not le:
                    continue
                b = getattr(le, 'spatial_bounds', None)
                if not b:
                    continue
                try:
                    p.gfx_rect.setPos(QPointF(float(b.x), float(b.y)))
                except Exception:
                    pass
                p.pos = QPointF(float(b.x), float(b.y))
        finally:
            # Ensure visuals (ligatures/z-order) refresh after placement
            self._schedule_ligature_refresh()
            self._schedule_zorder_refresh()

    def _on_corpus_egif_changed(self) -> None:
        """Debounce auto-import when EGIF text is edited in the Corpus dock."""
        if self._egif_autoload_pending:
            return
        self._egif_autoload_pending = True
        def do_autoload():
            try:
                self._maybe_autoload_corpus_egif()
            finally:
                self._egif_autoload_pending = False
        QTimer.singleShot(700, do_autoload)

    def _scene_is_nonempty(self) -> bool:
        try:
            return bool(self.model.vertices or self.model.predicates or self.model.cuts)
        except Exception:
            return False

    def _maybe_autoload_corpus_egif(self) -> None:
        """If there is valid EGIF text in the Corpus editor, parse and populate scene (Puzzle mode)."""
        try:
            if not hasattr(self, "txt_corpus_egif") or self.txt_corpus_egif is None:
                return
            egif_text = self.txt_corpus_egif.toPlainText().strip()
            if not egif_text or len(egif_text) < 6:
                return
            # Try to parse; if fails, do nothing (user may still be typing)
            try:
                from egif_parser_dau import parse_egif
                rgc = parse_egif(egif_text)
            except Exception:
                return
            # Confirm replacing non-empty scenes
            if self._scene_is_nonempty():
                try:
                    res = QMessageBox.question(self, "Replace Scene?", "Replace current scene with EGIF from Corpus tab?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if res != QMessageBox.Yes:
                        return
                except Exception:
                    pass
            # Convert and populate
            try:
                schema = self._schema_from_relational_graph(rgc)
            except Exception as e:
                QMessageBox.critical(self, "Conversion Error", f"Failed to convert EGIF: {e}")
                return
            self.begin_interaction()
            try:
                self.scene.clear()
                self.model = DrawingModel.from_schema(self.scene, schema)
                self._rebuild_cuts_with_constraints_and_place()
                # Proposed layout
                try:
                    from egi_spatial_correspondence import SpatialCorrespondenceEngine
                    eng = SpatialCorrespondenceEngine(rgc)
                    layout = eng.generate_spatial_layout()
                    self._apply_proposed_layout(layout)
                except Exception:
                    pass
                # Update Guide JSON from inline schema built from rgc to assist user
                try:
                    inline = self._egi_inline_from_schema(schema)
                    if hasattr(self, 'txt_corpus_egi_json') and self.txt_corpus_egi_json is not None:
                        self.txt_corpus_egi_json.setPlainText(json.dumps(inline, indent=2))
                except Exception:
                    pass
                # Enter Puzzle mode
                self.egi_locked = False
                self.puzzle_mode_active = True
                self._target_egi_meta = {"kind": "egif_text", "payload": str(egif_text)}
                if hasattr(self, 'act_egi_lock'):
                    self.act_egi_lock.setChecked(False)
                self.statusBar().showMessage("Puzzle Mode: syntactic-only. Arrange to match EGI, then Validate & Lock.")
                self._schedule_preview()
            finally:
                self.end_interaction()
        except Exception:
            pass

    def _schema_from_relational_graph(self, rgc) -> Dict:
        """Build a drawing schema dict from a RelationalGraphWithCuts (no positions).
        - Cuts: id and parent_id via rgc.get_context(cut.id) or sheet.
        - Vertices: id with area_id from rgc.get_context(vertex.id).
        - Predicates (edges): id, name (relation), area_id from rgc.get_context(edge.id).
        - Ligatures: from rgc.nu edge -> vertex sequence.
        """
        try:
            sheet_id = getattr(rgc, "sheet", "S")
        except Exception:
            sheet_id = "S"

        # Cuts
        cuts = []
        try:
            for cut in getattr(rgc, "Cut", []):
                cid = getattr(cut, "id", None)
                if not cid:
                    continue
                try:
                    parent = rgc.get_context(cid)
                except Exception:
                    parent = sheet_id
                cuts.append({"id": cid, "parent_id": parent or sheet_id})
        except Exception:
            cuts = []

        # Vertices
        vertices = []
        try:
            for v in getattr(rgc, "V", []):
                vid = getattr(v, "id", None)
                if not vid:
                    continue
                try:
                    area = rgc.get_context(vid)
                except Exception:
                    area = sheet_id
                vertices.append({"id": vid, "area_id": area or sheet_id})
        except Exception:
            vertices = []

        # Predicates (edges)
        predicates = []
        try:
            for e in getattr(rgc, "E", []):
                eid = getattr(e, "id", None)
                if not eid:
                    continue
                try:
                    name = rgc.get_relation_name(eid)
                except Exception:
                    name = eid
                try:
                    area = rgc.get_context(eid)
                except Exception:
                    area = sheet_id
                predicates.append({"id": eid, "name": name, "area_id": area or sheet_id})
        except Exception:
            predicates = []

        # Ligatures from nu mapping
        ligatures = []
        try:
            nu_map = getattr(rgc, "nu", {})
            for eid, vseq in nu_map.items():
                try:
                    vids = list(vseq)
                except Exception:
                    vids = [v for v in vseq]
                ligatures.append({"edge_id": eid, "vertex_ids": vids})
        except Exception:
            ligatures = []

        return {
            "sheet_id": sheet_id,
            "cuts": cuts,
            "vertices": vertices,
            "predicates": predicates,
            "ligatures": ligatures,
        }

    def _inject_editor_backrefs_for_model(self) -> None:
        """Ensure all gfx items carry a reference back to this editor after model (re)loads."""
        try:
            for v in self.model.vertices.values():
                if isinstance(v.gfx, VertexGfxItem):
                    v.gfx._editor = self
        except Exception:
            pass
        try:
            for p in self.model.predicates.values():
                if isinstance(p.gfx_rect, PredicateRectItem):
                    p.gfx_rect._editor = self
        except Exception:
            pass
        try:
            for c in self.model.cuts.values():
                # Some cut items may be specialized and accept _editor backref
                try:
                    setattr(c.gfx, "_editor", self)
                except Exception:
                    pass
        except Exception:
            pass

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

    # ----- Ergasterion Modes -----
    def _set_mode_composition(self) -> None:
        self.erg_mode = "composition"
        self.semantic_guardrails = False
        # Do not auto-lock; scratch composition typically starts unlocked
        self.act_mode_composition.setChecked(True)
        self.act_mode_practice.setChecked(False)
        self.statusBar().showMessage("Ergasterion: Composition Mode (semantic guardrails off)")
        self._refresh_status_banner()

    def _set_mode_practice(self) -> None:
        self.erg_mode = "practice"
        self.semantic_guardrails = True
        # Practice mode assumes meaning is fixed
        self.egi_locked = True
        self.act_egi_lock.setChecked(True)
        self.act_mode_composition.setChecked(False)
        self.act_mode_practice.setChecked(True)
        self.statusBar().showMessage("Ergasterion: Practice Mode (semantic guardrails on)")
        self._refresh_status_banner()

    def _toggle_egi_lock(self) -> None:
        self.egi_locked = not self.egi_locked
        self.act_egi_lock.setChecked(self.egi_locked)
        lock_state = "locked" if self.egi_locked else "unlocked"
        self.statusBar().showMessage(f"EGI {lock_state}: {'semantic guardrails on' if self.egi_locked else 'semantic guardrails off'}")
        self._refresh_status_banner()

    def _validate_and_lock_egi(self) -> None:
        # Basic structural validation stub; can be extended to full EGI comparison
        ok = True
        msg = "Locked EGI."
        try:
            if self._target_egi_meta:
                kind = self._target_egi_meta.get('kind')
                if kind == 'egi_inline':
                    target = self._target_egi_meta.get('payload') or {}
                    # Compare basic counts
                    schema = self._gather_schema_from_scene()
                    v_ok = len(schema.get('vertices', [])) == len(target.get('V', []))
                    p_ok = len(schema.get('predicates', [])) == len(target.get('E', []))  # E may represent predicates/edges depending on inline format
                    c_ok = len(schema.get('cuts', [])) == len(target.get('Cut', []))
                    ok = v_ok and c_ok  # predicates mapping may differ; keep minimal
                    if not ok:
                        msg = "Locked with warnings: counts differ from target EGI."
                else:
                    # For EGIF text, skip strict validation for now
                    msg = "Locked EGI (validation deferred for EGIF text)."
        except Exception as e:
            ok = False
            msg = f"Validation failed: {e}. You can still lock manually from the toggle."

        if ok or True:
            self.egi_locked = True
            self.act_egi_lock.setChecked(True)
            self.puzzle_mode_active = False
            self.statusBar().showMessage(msg)
            self._refresh_status_banner()

    def _refresh_status_banner(self) -> None:
        try:
            mode_str = f"Mode: {self.erg_mode}/{self.mode}"
            if hasattr(self, 'status_mode_label'):
                self.status_mode_label.setText(mode_str)
            if hasattr(self, 'status_egi_label'):
                if self.puzzle_mode_active and not self.egi_locked:
                    egi_str = "EGI: Puzzle (unlocked)"
                else:
                    egi_str = f"EGI: {'Locked' if self.egi_locked else 'Unlocked'}"
                self.status_egi_label.setText(egi_str)
        except Exception:
            pass

    def on_export_egdf(self) -> None:
        if drawing_to_egdf_document is None:
            QMessageBox.critical(self, "Unavailable", "EGDF adapter not available (missing src.egdf_adapter).")
            return
        # Choose output path/format
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export EGDF",
            "drawing.egdf.json",
            "EGDF JSON (*.json);;EGDF YAML (*.yaml *.yml)"
        )
        if not path:
            return
        try:
            # Gather platform-independent drawing schema and a neutral layout snapshot
            drawing_schema = self._gather_schema_from_scene()
            layout = self._gather_layout_from_scene()
            # Include current style snapshot if selected
            styles: Dict[str, Any] = {}
            if self.current_style_path:
                try:
                    styles[self.current_style_id or Path(self.current_style_path).stem] = json.loads(Path(self.current_style_path).read_text())
                except Exception as e:
                    print(f"[EGDF] Warning: failed reading style {self.current_style_path}: {e}")
            # Include current layout deltas
            deltas: List[Dict[str, Any]] = self._derive_deltas_from_layout(layout)
            # Minimal header metadata
            created = datetime.now().isoformat(timespec="seconds")
            doc = drawing_to_egdf_document(
                drawing=drawing_schema,
                layout=layout,
                styles=styles,
                deltas=deltas,
                version="0.1",
                generator="arisbe-drawing-editor",
                created=created,
            )
            p = Path(path)
            if p.suffix.lower() in (".yaml", ".yml"):
                p.write_text(doc.to_yaml())
            else:
                p.write_text(doc.to_json(indent=2))
            QMessageBox.information(self, "Exported", f"EGDF exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "EGDF Export Error", str(e))
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

        # Compute cut parent mapping using FULL RECTANGLE CONTAINMENT (not center-point)
        def rect_fully_inside(inner: QRectF, outer: QRectF, eps: float = 0.5) -> bool:
            # True if "inner" lies completely within "outer" (with a small tolerance)
            return (
                outer.left() - eps <= inner.left() and
                outer.top() - eps <= inner.top() and
                outer.right() + eps >= inner.right() and
                outer.bottom() + eps >= inner.bottom()
            )

        # For each cut, choose the SMALLEST fully containing cut as its parent; otherwise parent is sheet
        parent_map: Dict[str, Optional[str]] = {}
        for cid, c in self.model.cuts.items():
            candidates: List[Tuple[float, str]] = []  # (area, id)
            for oid, oc in self.model.cuts.items():
                if oid == cid:
                    continue
                if rect_fully_inside(c.rect, oc.rect):
                    candidates.append((oc.rect.width() * oc.rect.height(), oid))
            if candidates:
                candidates.sort()  # smallest area first
                parent_map[cid] = candidates[0][1]
            else:
                parent_map[cid] = self.model.sheet_id

        # Defensive: break any accidental cycles by promoting offending cuts to sheet
        for cid in list(parent_map.keys()):
            seen = set()
            pid = parent_map.get(cid)
            steps = 0
            while pid is not None and pid in self.model.cuts:
                if pid in seen or steps > 100:
                    # Cycle or unreasonable depth detected; promote to sheet
                    parent_map[cid] = self.model.sheet_id
                    break
                seen.add(pid)
                pid = parent_map.get(pid)
                steps += 1

        # Determine area for vertices/predicates by their position
        def resolve_area(pos: QPointF) -> str:
            inside: List[Tuple[int, str]] = []
            for cid, c in self.model.cuts.items():
                if point_in_rect(pos, c.rect):
                    # depth = distance to sheet via parent_map
                    depth = 1
                    pid = parent_map.get(cid)
                    seen = set()
                    while pid is not None and pid in self.model.cuts:
                        if pid in seen:
                            # Cycle detected, break to avoid infinite loop
                            break
                        seen.add(pid)
                        depth += 1
                        pid = parent_map.get(pid)
                        if depth > 100:
                            # Defensive: break if depth is unreasonably high
                            break
                    inside.append((depth, cid))
            if inside:
                inside.sort()
                return inside[-1][1]
            return self.model.sheet_id

        vertices = []
        for v in self.model.vertices.values():
            entry = {"id": v.id, "area_id": resolve_area(v.pos)}
            if v.label:
                entry["label"] = v.label
                if v.label_kind:
                    entry["label_kind"] = v.label_kind
            vertices.append(entry)
        predicates = []
        for p in self.model.predicates.values():
            predicates.append({"id": p.id, "name": p.name, "area_id": resolve_area(p.pos)})

        cuts = []
        for cid, c in self.model.cuts.items():
            cuts.append({"id": cid, "parent_id": parent_map.get(cid, self.model.sheet_id)})

        # Sanitize ligatures: drop references to missing edges/vertices
        ligatures = []
        existing_edges = set(self.model.predicates.keys())
        existing_vertices = set(self.model.vertices.keys())
        for e, vids in self.model.ligatures.items():
            if e not in existing_edges:
                continue
            clean_vids = [vid for vid in vids if vid in existing_vertices]
            ligatures.append({"edge_id": e, "vertex_ids": clean_vids})

        schema = {
            "sheet_id": self.model.sheet_id,
            "cuts": cuts,
            "vertices": vertices,
            "predicates": predicates,
            "ligatures": ligatures,
        }
        if self.model.predicate_outputs:
            schema["predicate_outputs"] = dict(self.model.predicate_outputs)
        return schema

    def _gather_layout_from_scene(self) -> Dict:
        """Produce a platform-neutral layout snapshot for EGDF.layout.
        Units are in scene pixels (px). Only geometry is captured — no Qt-specific fields.
        """
        # Ensure rect/pos caches are up-to-date
        for c in self.model.cuts.values():
            r = c.gfx.rect()
            tl = c.gfx.mapToScene(r.topLeft())
            br = c.gfx.mapToScene(r.bottomRight())
            c.rect = QRectF(tl, br).normalized()
        for v in self.model.vertices.values():
            v.pos = v.gfx.scenePos()
        for p in self.model.predicates.values():
            p.pos = p.gfx_rect.scenePos()

        cuts: Dict[str, Dict[str, float]] = {}
        for cid, c in self.model.cuts.items():
            rect = c.rect
            cuts[cid] = {"x": rect.x(), "y": rect.y(), "w": rect.width(), "h": rect.height()}

        vertices: Dict[str, Dict[str, float]] = {}
        for vid, v in self.model.vertices.items():
            vertices[vid] = {"x": v.pos.x(), "y": v.pos.y()}

        predicates: Dict[str, Dict[str, float]] = {}
        for pid, p in self.model.predicates.items():
            # Use the predicate rect's scene bounding box for width/height
            r = p.gfx_rect.sceneBoundingRect()
            predicates[pid] = {
                "text": p.gfx_text.toPlainText() or p.id,
                "x": r.x(),
                "y": r.y(),
                "w": r.width(),
                "h": r.height(),
            }

        # Ligature layout is optional; omit paths for now (renderers may route automatically)
        layout: Dict[str, Any] = {
            "units": "px",
            "cuts": cuts,
            "vertices": vertices,
            "predicates": predicates,
        }
        return layout

    # ----- Style selection and layout deltas -----
    def on_select_style(self) -> None:
        # Choose a style JSON file (e.g., docs/styles/dau-classic@1.0.json)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Style",
            "docs/styles",
            "Style JSON (*.json);;All Files (*)",
        )
        if not path:
            return
        self.current_style_path = path
        # Derive a human id from filename (without extension)
        try:
            self.current_style_id = Path(path).stem
        except Exception:
            self.current_style_id = path
        # Recreate style manager with selected path and apply to scene
        try:
            if create_style_manager is not None:
                self.styles = create_style_manager(self.current_style_path)
        except Exception:
            self.styles = None
        self._apply_theme_styles()
        self.statusBar().showMessage(f"Style selected: {self.current_style_id}")

    def on_save_layout_deltas(self) -> None:
        # Build deltas-only doc from current layout
        layout = self._gather_layout_from_scene()
        deltas = self._derive_deltas_from_layout(layout)
        style_id = self.current_style_id or "unknown-style@0"
        # Choose save path
        default_name = f"drawing.layout.{style_id}.json"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Layout Deltas",
            default_name,
            "JSON (*.json)"
        )
        if not path:
            return
        doc = {
            "egdf_deltas": {"version": "0.1", "generator": "arisbe"},
            "style_ref": {"id": style_id, **({"path": self.current_style_path} if self.current_style_path else {})},
            "deltas": deltas,
        }
        try:
            Path(path).write_text(json.dumps(doc, indent=2))
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save deltas: {e}")
            return
        QMessageBox.information(self, "Saved", f"Layout deltas saved to {path}")

    def _derive_deltas_from_layout(self, layout: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Convert a layout snapshot into a sequence of deltas ops.
        ops: List[Dict[str, Any]] = []
        for cid, r in layout.get("cuts", {}).items():
            ops.append({
                "op": "set_rect", "id": cid,
                "x": r.get("x", 0.0), "y": r.get("y", 0.0),
                "w": r.get("w", 0.0), "h": r.get("h", 0.0),
            })
        for vid, v in layout.get("vertices", {}).items():
            ops.append({
                "op": "set_position", "id": vid,
                "x": v.get("x", 0.0), "y": v.get("y", 0.0),
            })
        for pid, r in layout.get("predicates", {}).items():
            ops.append({
                "op": "set_rect", "id": pid,
                "x": r.get("x", 0.0), "y": r.get("y", 0.0),
                "w": r.get("w", 0.0), "h": r.get("h", 0.0),
            })
        # Ligature routing could be added later as route ops
        return ops

    # ----- Placement and conversions -----
    def _rebuild_cuts_with_constraints_and_place(self) -> None:
        """Swap raw cut rects to `CutRectItem`, set tooltips, and arrange:
        - Children are nested within parents with padding
        - Siblings are placed disjointly with simple tiling to avoid overlap
        Ensures initial scene respects syntactic constraints (nested or disjoint).
        """
        # Build parent map from model
        parent: Dict[str, Optional[str]] = {cid: c.parent_id for cid, c in self.model.cuts.items()}
        # Create CutRectItem for each cut and store mutable rect we will set
        cut_rects: Dict[str, QRectF] = {}
        for cid, c in list(self.model.cuts.items()):
            old_item = c.gfx
            rect = self._scene_rect_for_item(old_item)
            new_item = CutRectItem(rect, self)
            new_item.setPen(old_item.pen())
            new_item.setBrush(old_item.brush())
            new_item.setFlag(QGraphicsItem.ItemIsMovable, True)
            new_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
            new_item.setToolTip(f"Cut: {cid}")
            self.scene.addItem(new_item)
            try:
                self.scene.removeItem(old_item)
            except Exception:
                pass
            self.model.cuts[cid].gfx = new_item
            cut_rects[cid] = rect

        # Define base rects
        sheet_rect = QRectF(40, 40, 820, 520)
        # Place root-level cuts (parent == sheet or None) in non-overlapping grid
        roots = [cid for cid, pid in parent.items() if not pid or pid == self.model.sheet_id]
        x, y = 60.0, 60.0
        col_w, row_h = 260.0, 180.0
        for idx, cid in enumerate(roots):
            rx = x + (idx % 3) * col_w
            ry = y + (idx // 3) * row_h
            cut_rects[cid] = QRectF(rx, ry, 220.0, 140.0)

        # Recursively place children within parents with padding and tiling
        def place_children(pid: str, level: int = 0) -> None:
            children = [cid for cid, p in parent.items() if p == pid and cid != pid]
            if not children:
                return
            prect = cut_rects.get(pid, QRectF(60, 60, 240, 160))
            pad = 16.0
            inner = QRectF(prect.x() + pad, prect.y() + pad, max(40.0, prect.width() - 2 * pad), max(40.0, prect.height() - 2 * pad))
            cols = max(1, int(inner.width() // 120.0))
            cx, cy = inner.x(), inner.y()
            cw, ch = 180.0, 120.0
            for i, cid in enumerate(children):
                col = i % cols
                row = i // cols
                rx = cx + col * (cw + 8.0)
                ry = cy + row * (ch + 8.0)
                # Ensure it stays within parent bounds
                if rx + cw > inner.right():
                    rx = inner.right() - cw
                if ry + ch > inner.bottom():
                    ry = inner.bottom() - ch
                cut_rects[cid] = QRectF(rx, ry, cw, ch)
                place_children(cid, level + 1)

        for root in roots:
            place_children(root)

        # Apply rects back to graphics
        for cid, c in self.model.cuts.items():
            if cid in cut_rects:
                c.gfx.setRect(cut_rects[cid])
            c.gfx.setToolTip(f"Cut: {cid}")

        # Set tooltips for vertices and predicates
        for vid, v in self.model.vertices.items():
            v.gfx.setToolTip(f"Vertex: {vid}")
        for pid, p in self.model.predicates.items():
            p.gfx_rect.setToolTip(f"Predicate: {pid} [{p.name}]")

    def _schema_to_egif(self, schema: Dict) -> str:
        """Convert our drawing schema to EGIF text using Dau-compliant generator.
        Returns empty string on failure.
        """
        try:
            if drawing_to_relational_graph is None or generate_egif is None:
                self.statusBar().showMessage("EGIF generator unavailable (imports failed)")
                return ""
            graph = drawing_to_relational_graph(schema)
            return generate_egif(graph) or ""
        except Exception as e:
            # Surface error to user and console so issues after edits are diagnosable
            try:
                print("[EGIF] generation error:", e)
            except Exception:
                pass
            try:
                self.statusBar().showMessage(f"EGIF generation failed: {e}")
            except Exception:
                pass
            return ""

    def _schema_from_egi_inline(self, inline: Dict) -> Dict:
        """Convert an EGI inline JSON object to our drawing schema.
        - Cuts come from inline["Cut"] with hierarchy implied by inline["area"] entries that are cuts.
        - Vertices and predicates (edges) areas from inline["area"].
        """
        def _norm_id(x: Any) -> str:
            # Common shapes: "id" may be provided directly as string or wrapped in an object {"id": str}
            try:
                if isinstance(x, dict) and isinstance(x.get("id"), str):
                    return x["id"]
                if isinstance(x, str):
                    return x
            except Exception:
                pass
            # Fallback: stable stringification (should rarely be needed)
            return json.dumps(x, sort_keys=True)

        def _norm_id_list(xs: Any) -> List[str]:
            if not isinstance(xs, list):
                return []
            return [_norm_id(x) for x in xs]

        def _norm_area(a: Any) -> Dict[str, List[str]]:
            out: Dict[str, List[str]] = {}
            if isinstance(a, dict):
                for k, v in a.items():
                    out[_norm_id(k)] = _norm_id_list(v)
            return out

        def _norm_map_list(m: Any) -> Dict[str, List[str]]:
            out: Dict[str, List[str]] = {}
            if isinstance(m, dict):
                for k, v in m.items():
                    out[_norm_id(k)] = _norm_id_list(v)
            return out

        def _norm_map_str(m: Any) -> Dict[str, str]:
            out: Dict[str, str] = {}
            if isinstance(m, dict):
                for k, v in m.items():
                    out[_norm_id(k)] = _norm_id(v)
            return out

        sheet_id = _norm_id(inline.get("sheet", "S"))
        area: Dict[str, List[str]] = _norm_area(inline.get("area", {}))
        rel: Dict[str, str] = _norm_map_str(inline.get("rel", {}))
        nu: Dict[str, List[str]] = _norm_map_list(inline.get("nu", {}))
        cuts_ids = _norm_id_list(inline.get("Cut", []))
        cuts_set = set(cuts_ids)

        # Build parent map for cuts: for each cut, find which area lists it (parent)
        parent_map: Dict[str, Optional[str]] = {}
        for cut in cuts_set:
            parent = sheet_id
            for a, elems in area.items():
                if cut in elems:
                    parent = a
                    break
            parent_map[cut] = parent

        cuts = [{"id": c, "parent_id": parent_map.get(c, sheet_id)} for c in cuts_set]

        vertices = []
        for v in inline.get("V", []):
            vid = _norm_id(v)
            v_area = sheet_id
            for a, elems in area.items():
                if vid in elems:
                    v_area = a
                    break
            # Carry label information when available (EGI may provide is_generic/label)
            label_kind = None
            label_val = None
            try:
                if isinstance(v, dict):
                    is_generic = v.get("is_generic")
                    lbl = v.get("label")
                    if lbl is not None and is_generic is False:
                        label_kind = "constant"
                        label_val = lbl
            except Exception:
                pass
            v_entry = {"id": vid, "area_id": v_area}
            if label_kind is not None:
                v_entry["label_kind"] = label_kind
            if label_val is not None:
                v_entry["label"] = label_val
            vertices.append(v_entry)

        predicates = []
        for e in inline.get("E", []):
            eid = _norm_id(e)
            e_area = sheet_id
            for a, elems in area.items():
                if eid in elems:
                    e_area = a
                    break
            predicates.append({"id": eid, "name": rel.get(eid, eid), "area_id": e_area})

        ligatures = [{"edge_id": _norm_id(e), "vertex_ids": _norm_id_list(vs)} for e, vs in nu.items()]

        return {"sheet_id": sheet_id, "cuts": cuts, "vertices": vertices, "predicates": predicates, "ligatures": ligatures}

    # ----- Selection -> JSON preview highlight -----
    def _flash_highlight_in_json(self, element_id: str) -> None:
        """Find and temporarily highlight the first occurrence of element_id in `self.txt_egi` JSON."""
        try:
            edit = self.txt_egi
            text = edit.toPlainText()
            idx = text.find(element_id)
            if idx < 0:
                return
            cursor = edit.textCursor()
            cursor.setPosition(idx)
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, len(element_id))
            edit.setTextCursor(cursor)
            fmt = cursor.charFormat()
            fmt.setBackground(QColor(255, 240, 140))
            cursor.mergeCharFormat(fmt)
            # Clear highlight shortly after
            def clear():
                cursor2 = edit.textCursor()
                cursor2.setPosition(idx)
                cursor2.movePosition(cursor2.Right, cursor2.KeepAnchor, len(element_id))
                fmt2 = cursor2.charFormat()
                fmt2.setBackground(QColor(255, 255, 255))
                cursor2.mergeCharFormat(fmt2)
            QTimer.singleShot(900, clear)
        except Exception:
            pass

    def _flash_in_editor(self, edit: QTextEdit, element_id: str) -> None:
        try:
            text = edit.toPlainText()
            idx = text.find(element_id)
            if idx < 0:
                return
            cursor = edit.textCursor()
            cursor.setPosition(idx)
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, len(element_id))
            edit.setTextCursor(cursor)
            fmt = cursor.charFormat()
            fmt.setBackground(QColor(255, 240, 140))
            cursor.mergeCharFormat(fmt)
            def clear():
                cursor2 = edit.textCursor()
                cursor2.setPosition(idx)
                cursor2.movePosition(cursor2.Right, cursor2.KeepAnchor, len(element_id))
                fmt2 = cursor2.charFormat()
                fmt2.setBackground(QColor(255, 255, 255))
                cursor2.mergeCharFormat(fmt2)
            QTimer.singleShot(900, clear)
        except Exception:
            pass

    def _id_for_item(self, item: QGraphicsItem) -> Optional[str]:
        # Reverse lookup over model; small sizes expected
        for cid, c in self.model.cuts.items():
            if c.gfx is item:
                return cid
        for vid, v in self.model.vertices.items():
            if v.gfx is item:
                return vid
        for pid, p in self.model.predicates.items():
            if p.gfx_rect is item:
                return pid
        return None

    def _id_for_cut_item(self, item: QGraphicsItem) -> Optional[str]:
        for cid, c in self.model.cuts.items():
            if c.gfx is item:
                return cid
        return None

    def _parent_map_current(self) -> Dict[str, Optional[str]]:
        # Determine nesting by scene-rect containment
        rects: Dict[str, QRectF] = {}
        for cid, c in self.model.cuts.items():
            r = c.gfx.rect()
            tl = c.gfx.mapToScene(r.topLeft())
            br = c.gfx.mapToScene(r.bottomRight())
            rects[cid] = QRectF(tl, br).normalized()
        parent: Dict[str, Optional[str]] = {cid: None for cid in rects}
        for cid, r in rects.items():
            best: Optional[Tuple[str, float]] = None
            for other_id, orc in rects.items():
                if other_id == cid:
                    continue
                if orc.contains(r):
                    area = orc.width() * orc.height()
                    if best is None or area < best[1]:
                        best = (other_id, area)
            parent[cid] = best[0] if best else None
        return parent

    def _is_valid_cut_scene_rect(self, new_rect: QRectF, ignore_item: Optional[QGraphicsItem] = None) -> bool:
        # Check new_rect against other cuts: must be nested or disjoint
        for cid, c in self.model.cuts.items():
            if ignore_item is not None and c.gfx is ignore_item:
                continue
            r = c.gfx.rect()
            tl = c.gfx.mapToScene(r.topLeft())
            br = c.gfx.mapToScene(r.bottomRight())
            other = QRectF(tl, br).normalized()
            if new_rect.intersects(other):
                # allow if one contains the other (with small epsilon)
                def contains(a: QRectF, b: QRectF, eps: float = 0.5) -> bool:
                    return (a.left()-eps <= b.left() and a.top()-eps <= b.top() and a.right()+eps >= b.right() and a.bottom()+eps >= b.bottom())
                if not (contains(new_rect, other) or contains(other, new_rect)):
                    return False
        return True

    def _area_id_at_point(self, pos: QPointF) -> str:
        # deepest cut containing the point, else sheet
        best_id = self.model.sheet_id
        best_area = None
        for cid, c in self.model.cuts.items():
            r = c.gfx.rect()
            sb = c.gfx.mapToScene(r).boundingRect()
            if sb.contains(pos):
                area = sb.width() * sb.height()
                if best_area is None or area < best_area:
                    best_area = area
                    best_id = cid
        return best_id

    # (duplicate area guardrail methods removed; earlier robust implementations are authoritative)

    def _validate_syntactic_constraints(self) -> Tuple[bool, str]:
        """Delegate validation to the platform-agnostic controller."""
        try:
            if constraint_engine is None:
                # Fallback: treat as ok but flag missing controller
                return True, "controller unavailable"
            dto = self._model_to_dto()
            ok, msg, _info = constraint_engine.validate_syntax(dto, self.egi_locked)
            return ok, msg
        except Exception as e:
            return False, f"controller validation error: {e}"


class CutRectItem(QGraphicsRectItem):
    """Rect item that enforces EG cut constraints: nested or disjoint only."""
    def __init__(self, rect: QRectF, editor: "DrawingEditor") -> None:
        super().__init__(rect)
        self._editor = editor
        self._last_valid_scene_rect: QRectF = QRectF()
        self._press_pos: Optional[QPointF] = None
        # While a handle is dragging, we suppress movement of the cut itself
        self._resizing: bool = False
        self._resize_role: Optional[str] = None  # one of roles used by handles: nw,n,ne,e,se,s,sw,w
        self._resize_start_rect: Optional[QRectF] = None
        # Ensure child handles receive their own events (no parent pre-handling)
        try:
            self.setHandlesChildEvents(False)
        except Exception:
            pass
        try:
            self.setAcceptHoverEvents(True)
        except Exception:
            pass
        # Create resize handles (8 grips)
        self._handles: List["CutHandleItem"] = []
        self._create_handles()
        self._update_handles()

    def paint(self, painter, option, widget=None):
        # Draw rounded rectangle using style radius; clamp radius to half of width/height so
        # very small cuts appear circular per Dau style intent.
        r = self.rect()
        # Resolve radius from style; fallback to 8
        radius = 8.0
        try:
            if getattr(self, "_editor", None) and getattr(self._editor, "styles", None):
                s = self._editor.styles.resolve(type="cut", role="cut.border")
                radius = float(s.get("radius", radius))
        except Exception:
            pass
        # Clamp radius so corners meet smoothly even when tiny
        max_rx = max(0.0, min(radius, r.width() / 2.0))
        max_ry = max(0.0, min(radius, r.height() / 2.0))
        # Ensure nice joins
        pen = QPen(self.pen())
        try:
            pen.setJoinStyle(Qt.RoundJoin)
        except Exception:
            pass
        painter.setPen(pen)
        painter.setBrush(self.brush())
        painter.drawRoundedRect(r, max_rx, max_ry)

    def mousePressEvent(self, event):
        # Start of drag/manipulation; suppress heavy refresh work
        try:
            self._editor.begin_interaction()
        except Exception:
            pass
        # Hit-test for edge-based resize: if near an edge/corner, start resize mode
        try:
            local = event.pos()
            r = self.rect()
            m = 8.0  # margin for edge hit
            roles = {
                "nw": QRectF(r.left()-m, r.top()-m, 2*m, 2*m),
                "ne": QRectF(r.right()-m, r.top()-m, 2*m, 2*m),
                "sw": QRectF(r.left()-m, r.bottom()-m, 2*m, 2*m),
                "se": QRectF(r.right()-m, r.bottom()-m, 2*m, 2*m),
                "n": QRectF(r.left()+m, r.top()-m, max(0.0, r.width()-2*m), 2*m),
                "s": QRectF(r.left()+m, r.bottom()-m, max(0.0, r.width()-2*m), 2*m),
                "w": QRectF(r.left()-m, r.top()+m, 2*m, max(0.0, r.height()-2*m)),
                "e": QRectF(r.right()-m, r.top()+m, 2*m, max(0.0, r.height()-2*m)),
            }
            role_hit: Optional[str] = None
            # Prefer corners before edges
            for key in ("nw","ne","sw","se","n","s","w","e"):
                if roles[key].contains(local):
                    role_hit = key
                    break
            if role_hit is not None:
                self._resizing = True
                self._resize_role = role_hit
                self._resize_start_rect = QRectF(r)
                # Prevent movement while resizing
                self.setFlag(QGraphicsItem.ItemIsMovable, False)
                # Keep handles visible
                self.setSelected(True)
                self._update_handles()
                # Ensure all subsequent mouse moves are delivered here
                try:
                    self.grabMouse()
                except Exception:
                    pass
                event.accept()
                return
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
        # If we were in edge-resize mode, finalize resize first
        if getattr(self, "_resizing", False) and self._resize_role is not None:
            event.accept()
            # Validate as below after computing new scene rect
        else:
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
                    # Suppress scene change handlers during snap-back to avoid cascades
                    prev = getattr(self._editor, "_suppress_scene_change", False)
                    self._editor._suppress_scene_change = True
                    try:
                        self.setPos(self._press_pos)
                        # If resizing, also revert rect
                        if getattr(self, "_resize_start_rect", None) is not None:
                            self.setRect(self._resize_start_rect)
                            self._update_handles()
                    finally:
                        self._editor._suppress_scene_change = prev
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
        # Clear resize state, restore movability
        if getattr(self, "_resizing", False):
            self._resizing = False
            self._resize_role = None
            self._resize_start_rect = None
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            try:
                self.ungrabMouse()
            except Exception:
                pass

    def hoverMoveEvent(self, event):
        # Update cursor when near edges/corners for discoverability
        try:
            local = event.pos()
            r = self.rect()
            m = 8.0
            def near(p: QPointF, q: QPointF, eps: float) -> bool:
                return abs(p.x()-q.x()) <= eps and abs(p.y()-q.y()) <= eps
            # Build hit boxes like in press
            roles = {
                "nw": QRectF(r.left()-m, r.top()-m, 2*m, 2*m),
                "ne": QRectF(r.right()-m, r.top()-m, 2*m, 2*m),
                "sw": QRectF(r.left()-m, r.bottom()-m, 2*m, 2*m),
                "se": QRectF(r.right()-m, r.bottom()-m, 2*m, 2*m),
                "n": QRectF(r.left()+m, r.top()-m, max(0.0, r.width()-2*m), 2*m),
                "s": QRectF(r.left()+m, r.bottom()-m, max(0.0, r.width()-2*m), 2*m),
                "w": QRectF(r.left()-m, r.top()+m, 2*m, max(0.0, r.height()-2*m)),
                "e": QRectF(r.right()-m, r.top()+m, 2*m, max(0.0, r.height()-2*m)),
            }
            role_hit: Optional[str] = None
            for key in ("nw","ne","sw","se","n","s","w","e"):
                if roles[key].contains(local):
                    role_hit = key
                    break
            cursor_map = {
                "nw": Qt.SizeFDiagCursor,
                "se": Qt.SizeFDiagCursor,
                "ne": Qt.SizeBDiagCursor,
                "sw": Qt.SizeBDiagCursor,
                "n": Qt.SizeVerCursor,
                "s": Qt.SizeVerCursor,
                "e": Qt.SizeHorCursor,
                "w": Qt.SizeHorCursor,
            }
            if role_hit is not None:
                self.setCursor(cursor_map[role_hit])
            else:
                self.unsetCursor()
        except Exception:
            pass
        super().hoverMoveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # If currently resizing via a handle, veto position changes
            if getattr(self, "_resizing", False):
                return self.pos()
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
        elif change == QGraphicsItem.ItemSelectedHasChanged:
            # Toggle resize handle visibility based on selection state
            try:
                selected = bool(value)
            except Exception:
                selected = False
            # If a resize is in progress, keep handles visible regardless of selection flips
            force_visible = bool(getattr(self, "_resizing", False))
            for h in getattr(self, "_handles", []):
                try:
                    h.setVisible(selected or force_visible)
                except Exception:
                    pass
        return super().itemChange(change, value)

    def mouseMoveEvent(self, event):
        # Handle edge-based resize when active
        if getattr(self, "_resizing", False) and self._resize_role is not None:
            try:
                start_r = self._resize_start_rect or QRectF(self.rect())
                local_pt = event.pos()
                r = QRectF(start_r)
                min_w, min_h = 20.0, 20.0
                if self._resize_role in ("nw", "w", "sw"):
                    r.setLeft(local_pt.x())
                if self._resize_role in ("ne", "e", "se"):
                    r.setRight(local_pt.x())
                if self._resize_role in ("nw", "n", "ne"):
                    r.setTop(local_pt.y())
                if self._resize_role in ("sw", "s", "se"):
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
                self.setRect(r)
                self._update_handles()
                event.accept()
                return
            except Exception:
                pass
        # Otherwise, allow normal move behavior
        super().mouseMoveEvent(event)

    # ----- Resize handles helpers (for cuts) -----
    def _create_handles(self) -> None:
        roles = [
            "nw", "n", "ne",
            "e",
            "se", "s", "sw",
            "w",
        ]
        for role in roles:
            h = CutHandleItem(self, role)
            self._handles.append(h)
        # Start hidden; they will be shown when the cut is selected
        for h in self._handles:
            try:
                h.setVisible(False)
            except Exception:
                pass

    def _update_handles(self) -> None:
        if not self._handles:
            return
        r = self.rect()
        s = 12.0  # handle size (increased for easier hit-testing)
        half = s / 2.0
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
            # Place the handle at the corner point and use a small local rect centered at origin
            try:
                h.setPos(c)
            except Exception:
                pass
            h.setRect(QRectF(-half, -half, s, s))


class VertexGfxItem(QGraphicsEllipseItem):
    def __init__(self, x: float, y: float, w: float, h: float, editor: Optional["DrawingEditor"]) -> None:
        super().__init__(x, y, w, h)
        self._editor = editor
        self._press_pos: Optional[QPointF] = None
        # Ensure we receive ItemPositionChange during drags
        try:
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        except Exception:
            pass

    def mousePressEvent(self, event):
        try:
            self._editor.begin_interaction()
        except Exception:
            pass
        self._press_pos = self.scenePos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # If editor reference isn't injected yet, skip post-move validation gracefully
        if not getattr(self, "_editor", None):
            return
        try:
            pm = self._editor._parent_map_current()
            pos = self.scenePos()
            area_id = self._editor._element_area_id(self)
            if area_id is None:
                return
            allowed = self._editor._is_point_allowed_in_area(pos, area_id, pm)
            if not allowed:
                # If unlocked, allow area reassignment to the area at the drop point
                if not self._editor.egi_locked:
                    new_area = self._editor._area_id_at_point(pos)
                    if self._editor._is_point_allowed_in_area(pos, new_area, pm):
                        # Update model area_id
                        for vid, v in self._editor.model.vertices.items():
                            if v.gfx is self:
                                v.area_id = new_area
                                break
                        self._editor.statusBar().showMessage(f"Vertex moved to area '{new_area}'.")
                        return
                # Locked: snap back
                prev = getattr(self._editor, "_suppress_scene_change", False)
                self._editor._suppress_scene_change = True
                try:
                    if self._press_pos is not None:
                        self.setPos(self._press_pos)
                finally:
                    self._editor._suppress_scene_change = prev
                self._editor.statusBar().showMessage("Invalid move: point cannot enter forbidden areas.")
        finally:
            try:
                self._editor.end_interaction()
            except Exception:
                pass

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and getattr(self, "_editor", None):
            if self._editor.egi_locked:
                try:
                    delta = value - self.pos()
                except Exception:
                    delta = QPointF(0.0, 0.0)
                new_scene_pos = self.scenePos() + delta
                area_id = self._editor._element_area_id(self)
                if area_id is not None:
                    if not self._editor._is_point_allowed_in_area(new_scene_pos, area_id):
                        return self.pos()
        return super().itemChange(change, value)


class PredicateRectItem(QGraphicsRectItem):
    def __init__(self, rect: QRectF, editor: Optional["DrawingEditor"]) -> None:
        super().__init__(rect)
        self._editor = editor
        self._press_pos: Optional[QPointF] = None
        # Ensure we receive ItemPositionChange during drags
        try:
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        except Exception:
            pass

    def paint(self, painter, option, widget=None):
        """Do not draw any visible border or fill, even when selected.
        Keep hit-testing via shape() but suppress visuals to ensure
        predicate boundaries are invisible.
        """
        try:
            painter.save()
            painter.setPen(QPen(QColor(0, 0, 0, 0), 0))
            painter.setBrush(Qt.NoBrush)
            # Intentionally do not call super().paint to avoid selection outline
        finally:
            painter.restore()

    def mousePressEvent(self, event):
        try:
            self._editor.begin_interaction()
        except Exception:
            pass
        self._press_pos = self.scenePos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # If editor reference isn't injected yet, skip post-move validation gracefully
        if not getattr(self, "_editor", None):
            return
        try:
            pm = self._editor._parent_map_current()
            # Compute new rect in scene coords
            r = self.rect()
            tl = self.mapToScene(r.topLeft())
            br = self.mapToScene(r.bottomRight())
            new_rect = QRectF(tl, br).normalized()
            area_id = self._editor._element_area_id(self)
            if area_id is None:
                return
            allowed = self._editor._is_rect_allowed_in_area(new_rect, area_id, pm)
            if not allowed:
                # If unlocked, allow area reassignment to the area at rect center
                if not self._editor.egi_locked:
                    center = new_rect.center()
                    new_area = self._editor._area_id_at_point(center)
                    if self._editor._is_rect_allowed_in_area(new_rect, new_area, pm):
                        # Update model area_id
                        for pid, p in self._editor.model.predicates.items():
                            if p.gfx_rect is self:
                                p.area_id = new_area
                                break
                        self._editor.statusBar().showMessage(f"Predicate moved to area '{new_area}'.")
                        return
                # Locked: snap back
                prev = getattr(self._editor, "_suppress_scene_change", False)
                self._editor._suppress_scene_change = True
                try:
                    if self._press_pos is not None:
                        self.setPos(self._press_pos)
                finally:
                    self._editor._suppress_scene_change = prev
                self._editor.statusBar().showMessage("Invalid move: element cannot enter forbidden areas.")
        finally:
            try:
                self._editor.end_interaction()
            except Exception:
                pass

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and getattr(self, "_editor", None):
            if self._editor.egi_locked:
                new_pos = value
                r = self.rect()
                tl_scene = self.mapToScene(r.topLeft()) + (new_pos - self.pos())
                br_scene = self.mapToScene(r.bottomRight()) + (new_pos - self.pos())
                new_rect = QRectF(tl_scene, br_scene).normalized()
                area_id = self._editor._element_area_id(self)
                if area_id is not None:
                    if not self._editor._is_rect_allowed_in_area(new_rect, area_id):
                        return self.pos()
        return super().itemChange(change, value)


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
        self.setAcceptHoverEvents(True)
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
        # Ensure parent cut stays selected during resize so handles remain visible
        try:
            self._cut.setSelected(True)
            # Mark resizing state on the cut for visibility logic
            setattr(self._cut, "_resizing", True)
        except Exception:
            pass
        # Prevent parent cut from moving during resize
        try:
            self._prev_cut_movable = self._cut.flags() & QGraphicsItem.ItemIsMovable
            self._cut.setFlag(QGraphicsItem.ItemIsMovable, False)
        except Exception:
            pass
        self._start_rect = QRectF(self._cut.rect())
        try:
            cid = self._cut._editor._id_for_cut_item(self._cut)
            sp = self._cut.scenePos()
            self._cut._editor._log(f"CUT_RESIZE begin id={cid} pos=({sp.x():.1f},{sp.y():.1f}) rect={self._start_rect} handle={self.role}")
        except Exception:
            pass
        # Proactively grab mouse so all subsequent move events are delivered to this handle
        try:
            self.grabMouse()
        except Exception:
            pass
        # Consume to avoid propagating to parent (which would start a move)
        event.accept()

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
        event.accept()

    def mouseReleaseEvent(self, event):
        # Consume release, then validate and end interaction
        event.accept()
        # Release the grab so other items can receive events again
        try:
            self.ungrabMouse()
        except Exception:
            pass
        # Restore parent cut movability after resize
        try:
            want_movable = bool(getattr(self, "_prev_cut_movable", True))
            self._cut.setFlag(QGraphicsItem.ItemIsMovable, want_movable)
        except Exception:
            pass
        # Clear resizing state and ensure handles visibility updates follow selection
        try:
            setattr(self._cut, "_resizing", False)
            # Trigger a small handles refresh
            self._cut._update_handles()
        except Exception:
            pass
        # Validate final rect; revert if invalid
        try:
            r = self._cut.rect()
            tl = self._cut.mapToScene(r.topLeft())
            br = self._cut.mapToScene(r.bottomRight())
            new_scene_rect = QRectF(tl, br).normalized()
            if not self._cut._editor._is_valid_cut_scene_rect(new_scene_rect, ignore_item=self._cut):
                if self._start_rect is not None:
                    # Suppress scene change handlers during snap-back to avoid cascades
                    prev = getattr(self._cut._editor, "_suppress_scene_change", False)
                    self._cut._editor._suppress_scene_change = True
                    try:
                        self._cut.setRect(self._start_rect)
                        self._cut._update_handles()
                    finally:
                        self._cut._editor._suppress_scene_change = prev
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
            # End throttling
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
