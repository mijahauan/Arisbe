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
import math
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, Signal
from PySide6.QtGui import QPen, QColor, QBrush, QPainter, QPainterPath, QFont, QPixmap, QAction, QActionGroup
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsItem,
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
    QMenu,
    QLabel,
    QDockWidget,
    QTabWidget,
    QTextEdit,
    QWidget,
)

# Hand-drawn ligature system
try:
    from .hand_drawn_ligature import HandDrawnPath, LigaturePathPreview, ConnectionDetector
except ImportError:
    try:
        from hand_drawn_ligature import HandDrawnPath, LigaturePathPreview, ConnectionDetector
    except ImportError:
        # Fallback - disable hand-drawn ligature features
        HandDrawnPath = None
        LigaturePathPreview = None
        ConnectionDetector = None

class LigatureCompositionView(QGraphicsView):
    """Custom graphics view that supports predicate-initiated ligature creation with hand-drawn paths."""
    
    def __init__(self, scene: QGraphicsScene, editor: 'DrawingEditor'):
        super().__init__(scene)
        self.editor = editor
        self.current_path = None
        self.path_preview = None
        self.connection_detector = ConnectionDetector(editor) if ConnectionDetector else None
        self.drawing_ligature = False
    
    def mousePressEvent(self, event):
        """Handle mouse press for selection/movement (left) and hand-drawn ligature creation (right)."""
        scene_pos = self.mapToScene(event.pos())
        
        # Right-click: start hand-drawn ligature creation
        if event.button() == Qt.RightButton:
            if not self.drawing_ligature:
                # Start ligature creation if right-clicking on a predicate
                clicked_item = self.scene().itemAt(scene_pos, self.transform())
                if clicked_item:
                    predicate_id = self._find_predicate_id_for_item(clicked_item)
                    if predicate_id:
                        self._start_hand_drawn_ligature(predicate_id, scene_pos)
                        event.accept()
                        return
            
            event.accept()
            return
        
        # Left-click: normal selection and movement behavior
        if event.button() == Qt.LeftButton:
            # If drawing ligature, finish it
            if self.drawing_ligature:
                self._finish_hand_drawn_ligature(scene_pos)
                event.accept()
                return
        
        # Default behavior for other cases
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for hand-drawn ligature creation."""
        # Handle mouse move for hand-drawn ligature creation
        if self.drawing_ligature and self.current_path:
            scene_pos = self.mapToScene(event.pos())
            self.current_path.add_point(scene_pos)
            
            # Update preview
            if self.path_preview:
                smoothed_path = self.current_path.smooth_path()
                self.path_preview.update_path(smoothed_path)
        
        super().mouseMoveEvent(event)
    
    def keyPressEvent(self, event):
        """Handle escape to cancel ligature creation."""
        if event.key() == Qt.Key_Escape:
            if self.drawing_ligature:
                self._cleanup_ligature_drawing()
                event.accept()
                return
            elif self.editor._ligature_creation_active:
                self.editor._cancel_ligature_creation()
                event.accept()
                return
        super().keyPressEvent(event)
    
    def _start_hand_drawn_ligature(self, predicate_id: str, start_pos: QPointF):
        """Start hand-drawn ligature creation from a predicate."""
        if not HandDrawnPath or not LigaturePathPreview:
            return  # Hand-drawn ligature features not available
            
        self.drawing_ligature = True
        self.current_path = HandDrawnPath()
        self.current_path.add_point(start_pos)
        
        # Create preview item
        self.path_preview = LigaturePathPreview()
        self.scene().addItem(self.path_preview)
        
        # Store starting predicate
        self.ligature_start_predicate = predicate_id
    
    def _finish_hand_drawn_ligature(self, end_pos: QPointF):
        """Finish hand-drawn ligature creation and create the actual ligature."""
        if not self.drawing_ligature or not self.current_path:
            return
        
        # Add final point
        self.current_path.add_point(end_pos)
        
        # Find connection target
        if self.connection_detector:
            connection_type, target_id, connection_point = self.connection_detector.find_connection_target(end_pos)
        else:
            # Fallback to simple vertex detection
            target_vertex = self.editor._find_vertex_at_position(end_pos)
            if target_vertex:
                connection_type, target_id, connection_point = 'vertex', target_vertex, end_pos
            else:
                connection_type, target_id, connection_point = 'none', None, end_pos
        
        # Create the ligature based on connection type
        if connection_type == 'vertex' and target_id:
            self.editor._create_hand_drawn_ligature(
                self.ligature_start_predicate, 
                target_id, 
                self.current_path
            )
        elif connection_type == 'ligature' and target_id:
            # Handle branching to existing ligature
            self.editor._create_branching_ligature(
                self.ligature_start_predicate,
                target_id,
                connection_point,
                self.current_path
            )
        elif self.editor._composition_mode:
            # Create new vertex at end position
            new_vertex_id = self.editor._create_vertex_at_position(connection_point or end_pos)
            self.editor._create_hand_drawn_ligature(
                self.ligature_start_predicate,
                new_vertex_id,
                self.current_path
            )
        
        # Clean up
        self._cleanup_ligature_drawing()
    
    def _cleanup_ligature_drawing(self):
        """Clean up after ligature drawing is complete or cancelled."""
        self.drawing_ligature = False
        self.current_path = None
        
        if self.path_preview:
            self.scene().removeItem(self.path_preview)
            self.path_preview = None
        
        self.ligature_start_predicate = None
    
    def _find_predicate_id_for_item(self, item: QGraphicsItem) -> Optional[str]:
        """Find predicate ID associated with a graphics item."""
        # Check if item itself is a predicate
        for pid, pred in self.editor.model.predicates.items():
            if pred.gfx_rect == item:
                return pid
        
        # Check if item is a child of a predicate (e.g., text label)
        parent = item.parentItem()
        if parent:
            for pid, pred in self.editor.model.predicates.items():
                if pred.gfx_rect == parent:
                    return pid
        
        return None

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


    @classmethod
    def from_schema(cls, scene: QGraphicsScene, schema: Dict) -> "DrawingModel":
        print(f"[DEBUG] DrawingModel.from_schema called - THIS SHOULD NOT HAPPEN IN SIMPLIFIED MODE!")
        import traceback
        traceback.print_stack()
        
        model = cls(sheet_id=schema.get("sheet_id", "S"))
        # DON'T AUTO-PLACE ELEMENTS - return empty model for manual diagramming
        return model


# ---------- Editor UI ----------
class Mode:
    SELECT = "select"
    ADD_CUT = "add_cut"
    ADD_VERTEX = "add_vertex"
    ADD_PREDICATE = "add_predicate"
    LIGATURE = "ligature"


class DrawingEditor(QMainWindow):
    # Signal for Ergasterion→Organon return flow
    egi_created_from_diagram = Signal(dict)  # emits payload with EGIF for Organon to parse
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Arisbe Drawing Tool (minimal)")
        self.resize(1200, 800)

        self.model = DrawingModel()
        self.scene = QGraphicsScene()
        self.view = LigatureCompositionView(self.scene, self)
        self.setCentralWidget(self.view)
        
        # Hand-drawn ligature state
        self._ligature_items = []  
        
        try:
            from PySide6.QtWidgets import QGraphicsView as _QV
            self.view.setViewportUpdateMode(_QV.BoundingRectViewportUpdate)
        except Exception:
            pass
        
        self.scene.setSceneRect(0, 0, 900, 600)
        
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
        # Embedded mode (for unified app) — disables standalone load/save UI
        self.embedded_mode: bool = False
        # Visual toggles and guards
        self._show_ligatures: bool = True
        self._suppress_scene_change: bool = False
        # Ligature drawing modes and user control
        self._ligature_mode: str = "straight"  # "straight", "rectilinear", "curved"
        self._ligature_creation_active: bool = False
        self._connection_preview_item: Optional[QGraphicsPathItem] = None
        self._ligature_creation_from_predicate: Optional[str] = None  # predicate_id initiating connection
        self._smart_target_cache: Dict[str, QPointF] = {}  # Cache for smart target calculations
        self._composition_mode: bool = True  # Create new vertices when drawing to empty space
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
        # Persistent status banner with EGI Lock status
        try:
            self.status_mode_label = QLabel()
            self.status_egi_label = QLabel()
            self.status_lock_label = QLabel()
            self.statusBar().addPermanentWidget(self.status_mode_label, 0)
            self.statusBar().addPermanentWidget(self.status_egi_label, 0)
            self.statusBar().addPermanentWidget(self.status_lock_label, 0)
            self._refresh_status_banner()
        except Exception:
            pass
        # Initial preview
        self._update_preview()
        # Keep visuals and z-order in sync with movements        # Connect scene events
        self.scene.changed.connect(self._on_scene_changed)
        self.scene.changed.connect(self._auto_update_preview)
        self.scene.selectionChanged.connect(self._on_selection_changed)
        
        # Load EGDF if available (similar to Organon)
        print("[Ergasterion] About to call _load_current_egdf()")
        self._load_current_egdf()
        print("[Ergasterion] Finished _load_current_egdf() call")
        
        # Inject editor backrefs into gfx subclasses now that editor exists
        self._inject_editor_backrefs_for_model()
        # Initial theme application (no-op if no items yet)
        try:
            self._apply_theme_styles()
        except Exception:
            pass

    # ----- Engine-driven rendering helpers (Organon parity) -----
            
            # Make sure Corpus dock is visible and show the EGIF tab
            if hasattr(self, "corpus_dock"):
                self.corpus_dock.show()
                self.corpus_dock.raise_()
                # Switch to the EGIF tab to show the target
                if hasattr(self, "corpus_dock") and self.corpus_dock.widget():
                    tab_widget = self.corpus_dock.widget()
                    if hasattr(tab_widget, "setCurrentIndex"):
                        tab_widget.setCurrentIndex(1)  # Index 1 is "Corpus EGIF" tab
                
        except Exception as e:
            print(f"[Corpus] Failed to populate guidance: {e}")


    def export_result(self) -> Dict[str, Any]:
        """Export EGDF + components for Organon to persist. Returns a dict payload.
        Structure: { 'egdf': <dict>, 'inline': <dict>, 'styles': <dict>, 'deltas': <list>, 'layout': <dict> }
        """
        if drawing_to_egdf_document is None:
            return {}
        try:
            drawing_schema = self._gather_schema_from_scene()
            
            # Apply ID mapping if diagram matches target EGI structure
            drawing_schema = self._apply_target_id_mapping(drawing_schema)
            
            layout = self._gather_layout_from_scene()
            
            # Update layout with mapped IDs
            layout = self._update_layout_with_mapped_ids(layout, drawing_schema)
            
            styles: Dict[str, Any] = {}
            if self.current_style_path:
                try:
                    styles[self.current_style_id or Path(self.current_style_path).stem] = json.loads(Path(self.current_style_path).read_text())
                except Exception:
                    styles = {}
            deltas: List[Dict[str, Any]] = self._derive_deltas_from_layout(layout)
            created = datetime.now().isoformat(timespec="seconds")
            doc = drawing_to_egdf_document(
                drawing=drawing_schema,
                layout=layout,
                styles=styles or None,
                deltas=deltas or None,
                version="0.1",
                generator="arisbe-drawing-editor",
                created=created,
            )
            inline = {}
            if isinstance(doc.egi_ref, dict):
                inline = dict(doc.egi_ref.get("inline") or {})
            return {
                "egdf": doc.to_dict(),
                "inline": inline,
                "styles": styles,
                "deltas": deltas,
                "layout": layout,
            }
        except Exception:
            return {}

    
    
    def _update_layout_with_mapped_ids(self, layout: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Update layout data to use the mapped IDs from schema."""
        # For now, return layout as-is since the mapping happens at schema level
        # The layout structure will be rebuilt with correct IDs by the EGDF adapter
        return layout

    def _apply_theme_styles(self) -> None:
        """Apply current theme styles to all scene items."""
        pass

    # ----- Utilities -----

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

        # Essential selection mode
        self.act_select = make_action("Select", True, lambda: self._set_mode(Mode.SELECT))
        
        # Legacy add-mode actions kept for internal use but hidden
        self.act_add_cut = make_action("Add Cut", True, lambda: self._set_mode(Mode.ADD_CUT))
        self.act_add_vertex = make_action("Add Vertex", True, lambda: self._set_mode(Mode.ADD_VERTEX))
        self.act_add_pred = make_action("Add Predicate", True, lambda: self._set_mode(Mode.ADD_PREDICATE))
        self.act_ligature = make_action("Ligature", True, lambda: self._set_mode(Mode.LIGATURE))
        try:
            self.act_add_cut.setVisible(False)
            self.act_add_vertex.setVisible(False)
            self.act_add_pred.setVisible(False)
            self.act_ligature.setVisible(False)
        except Exception:
            pass

        tb.addSeparator()
        # Keep only essential actions
        make_action("Select Style", False, self.on_select_style)
        make_action("Return to Organon", False, self.on_return_to_organon)

        tb.addSeparator()
        # Exclusive mode toggle - Composition vs Practice
        self.mode_group = QActionGroup(self)
        self.act_mode_composition = make_action("Composition Mode", True, self._set_mode_composition)
        self.act_mode_practice = make_action("Practice Mode", True, self._set_mode_practice)
        self.act_mode_composition.setChecked(True)
        self.act_mode_practice.setChecked(False)
        self.mode_group.addAction(self.act_mode_composition)
        self.mode_group.addAction(self.act_mode_practice)

        tb.addSeparator()
        # Ligature assistant buttons
        self.ligature_mode_group = QActionGroup(self)
        self.act_straight = make_action("Straight Ligatures", True, lambda: self._set_ligature_mode("straight"))
        self.act_rectilinear = make_action("Rectilinear Ligatures", True, lambda: self._set_ligature_mode("rectilinear"))
        self.act_curved = make_action("Curved Ligatures", True, lambda: self._set_ligature_mode("curved"))
        
        self.act_straight.setChecked(True)  # Default mode
        self.ligature_mode_group.addAction(self.act_straight)
        self.ligature_mode_group.addAction(self.act_rectilinear)
        self.ligature_mode_group.addAction(self.act_curved)

        tb.addSeparator()
        # Annotation toggles - make them more prominent
        self.act_show_vertex_names = make_action("Vertex Names", True, self._toggle_vertex_annotations)
        self.act_show_predicate_arity = make_action("Arity", True, self._toggle_arity_annotations)
        self.act_show_vertex_names.setChecked(False)
        self.act_show_predicate_arity.setChecked(False)
        self.act_show_vertex_names.setToolTip("Show vertex variable names (*x, *y, etc.)")
        self.act_show_predicate_arity.setToolTip("Show predicate arity numbers (2), (3), etc.")

        tb.addSeparator()
        # Clear button instead of Delete
        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(self._clear_scene)
        tb.addAction(clear_action)
        
        # Return to Organon button
        return_action = QAction("Return to Organon", self)
        return_action.triggered.connect(self._return_to_organon)
        tb.addAction(return_action)

        self.act_select.setChecked(True)

        self.view.setMouseTracking(True)
        self.view.viewport().installEventFilter(self)

    def _clear_scene(self) -> None:
        """Clear the scene to restart diagramming process."""
        self.scene.clear()
        self.model = DrawingModel()
        self._clear_all_temporary_items()
        # Reset to composition mode and unlock EGI for new diagram
        self.egi_locked = False
        self._set_mode_composition()
        self.statusBar().showMessage("Scene cleared - ready for new diagram")
        self._update_preview()

    def _return_to_organon(self) -> None:
        """Return diagram to Organon with proper validation."""
        try:
            # Check if current diagram matches target (if in target mode)
            if self.puzzle_mode_active and self._target_egi_meta:
                # Target mode: only allow return if current matches target
                if not self._current_matches_target():
                    QMessageBox.warning(
                        self, 
                        "Target Not Matched",
                        "Current diagram does not match the target EGI.\n\n"
                        "Please complete the diagram to match the target before returning to Organon."
                    )
                    return
            
            # Generate current EGI from diagram
            current_egi = self._generate_current_egi()
            
            # Always confirm with user what the EGI means
            self._confirm_and_return_egi(current_egi)
                
        except Exception as e:
            QMessageBox.critical(self, "Return Error", f"Failed to return to Organon: {e}")

    def _current_matches_target(self) -> bool:
        """Check if current diagram matches the target EGI."""
        try:
            # Get target EGIF
            target_egif = ""
            kind = self._target_egi_meta.get("kind")
            if kind == "egif_text":
                target_egif = str(self._target_egi_meta.get("payload", ""))
            elif kind == "egi_inline":
                # Convert inline EGI to EGIF for comparison
                target_inline = self._target_egi_meta.get("payload", {})
                if isinstance(target_inline, dict):
                    try:
                        if drawing_to_relational_graph and generate_egif:
                            target_schema = self._schema_from_egi_inline(target_inline)
                            target_graph = drawing_to_relational_graph(target_schema)
                            target_egif = generate_egif(target_graph) or ""
                    except Exception:
                        return False
            
            # Get current EGIF
            current_schema = self._gather_schema_from_scene()
            current_egif = self._schema_to_egif(current_schema)
            
            # Compare normalized EGIF strings
            def normalize_egif(egif: str) -> str:
                return " ".join(egif.split())  # Normalize whitespace
            
            return normalize_egif(current_egif) == normalize_egif(target_egif)
        except Exception:
            return False

    def _confirm_and_return_egi(self, current_egi: str) -> None:
        """Confirm EGI meaning with user before returning to Organon."""
        # Generate EGIF for display
        try:
            schema = self._gather_schema_from_scene()
            egif_content = self._schema_to_egif(schema)
        except Exception:
            egif_content = "Error generating EGIF"
        
        reply = QMessageBox.question(
            self,
            "Confirm EGI Meaning", 
            f"Please confirm this EGI represents what you intended:\n\n"
            f"EGIF:\n{egif_content}\n\n"
            f"Return this diagram to Organon?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            diagram_type = "target_visualization" if self.puzzle_mode_active else "new_graph"
            self._send_to_organon(current_egi, diagram_type=diagram_type)

    def _generate_current_egi(self) -> str:
        """Generate EGI representation of current diagram."""
        try:
            # Use existing preview generation logic
            schema = self._gather_schema_from_scene()
            if drawing_to_relational_graph:
                egi = drawing_to_relational_graph(schema)
                return str(egi)
            else:
                # Fallback to EGIF format
                return self._generate_egif_from_scene()
        except Exception as e:
            return f"Error generating EGI: {e}"

    def _send_to_organon(self, egi: str, diagram_type: str) -> None:
        """Send completed diagram back to Organon."""
        try:
            # Generate EGIF for Organon to parse
            schema = self._gather_schema_from_scene()
            egif_content = self._schema_to_egif(schema)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to generate content: {e}")
            return
    def _clear_ligature_visuals(self) -> None:
        for line in self._ligature_items:
            try:
                self.scene.removeItem(line)
            except Exception:
                pass
        self._ligature_items.clear()

    def _clear_all_temporary_items(self) -> None:
        """Clear all temporary/preview items to ensure clean puzzle mode display."""
        # Clear ligature visuals
        self._clear_ligature_visuals()
        
        # Clear cut preview item
        if hasattr(self, '_cut_preview_item') and self._cut_preview_item is not None:
            try:
                self.scene.removeItem(self._cut_preview_item)
            except Exception:
                pass
            self._cut_preview_item = None
        
        # Clear ligature drag path
        if hasattr(self, '_ligature_drag_path') and self._ligature_drag_path is not None:
            try:
                self.scene.removeItem(self._ligature_drag_path)
            except Exception:
                pass
            self._ligature_drag_path = None
            self._ligature_drag_from_vid = None
        
        # Reset any pending refresh flags
        self._ligature_refresh_pending = False
        self._zorder_refresh_pending = False
        
        # Clear any selection to avoid artifacts
        try:
            self.scene.clearSelection()
        except Exception:
            pass

    def _schedule_ligature_refresh(self, force_immediate: bool = False) -> None:
        if not self._show_ligatures:
            # Keep visuals cleared when disabled
            if self._ligature_items:
                self._clear_ligature_visuals()
            return
        if self._suppress_scene_change and not force_immediate:
            return
        if self._ligature_refresh_pending and not force_immediate:
            return
        self._ligature_refresh_pending = True
        def do_refresh():
            try:
                self._refresh_ligature_visuals()
            finally:
                self._ligature_refresh_pending = False
        # For immediate updates (during dragging), use shorter delay
        delay = 20 if force_immediate else 80
        QTimer.singleShot(delay, do_refresh)

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
        # Rebuild paths from predicates to vertices using flexible user-controlled system
        self._suppress_scene_change = True
        try:
            self._clear_ligature_visuals()
            
            # Use new flexible ligature system instead of engine-driven rendering
            self._draw_flexible_ligatures()
            
        finally:
            self._suppress_scene_change = False
    
    def _draw_flexible_ligatures(self) -> None:
        """Draw ligatures using predicate-initiated system with consistent styling."""
        # Get centralized ligature styling
        base_pen, out_pen = self._get_ligature_style()
        
        # Draw individual ligature for each predicate -> vertex connection
        for predicate_id, vertex_ids in self.model.ligatures.items():
            pred = self.model.predicates.get(predicate_id)
            if not pred:
                continue
            
            pred_rect = pred.gfx_rect.sceneBoundingRect()
            
            for vertex_id in vertex_ids:
                vertex = self.model.vertices.get(vertex_id)
                if not vertex:
                    continue
                
                # Get proper anchor points
                target_point = vertex.gfx.scenePos()
                start_point = self._get_predicate_anchor_point(pred_rect, target_point)
                
                # Create straight path
                path = QPainterPath(start_point)
                path.lineTo(target_point)
                
                # Create graphics item
                item = QGraphicsPathItem(path)
                item.setData(0, predicate_id)
                item.setData(1, vertex_id)
                item.setZValue(1000.0)
                
                # Apply consistent styling
                if self.model.predicate_outputs.get(predicate_id) == vertex_id:
                    item.setPen(out_pen)
                else:
                    item.setPen(base_pen)
                
                self.scene.addItem(item)
                self._ligature_items.append(item)

    def _get_ligature_style(self) -> tuple:
        """Get consistent ligature styling from styles system or defaults."""
        if self.styles is not None:
            try:
                s = self.styles.resolve(type="edge", role="edge.identity")
                line_color = self._parse_qcolor(s.get("line_color", "#000000"))
                line_width = float(s.get("line_width", 3.5))
                base_pen = QPen(line_color, line_width)
                base_pen.setCosmetic(True)
                out_pen = QPen(QColor(40, 150, 60, 220), max(2.0, line_width))
                out_pen.setCosmetic(True)
                return base_pen, out_pen
            except Exception:
                pass
        
        # Fallback to defaults
        base_pen = QPen(QColor(80, 80, 200, 160), 3.5)
        base_pen.setCosmetic(True)
        out_pen = QPen(QColor(40, 150, 60, 220), 3.5)
        out_pen.setCosmetic(True)
        return base_pen, out_pen

    def _get_predicate_anchor_point(self, pred_rect: QRectF, target_point: QPointF) -> QPointF:
        """Get proper anchor point on predicate border toward target."""
        center = pred_rect.center()
        
        # Calculate direction vector from center to target
        dx = target_point.x() - center.x()
        dy = target_point.y() - center.y()
        
        # Normalize and find intersection with rectangle border
        if abs(dx) < 0.1 and abs(dy) < 0.1:
            return center  # Target is at center, use center
        
        # Find which edge the line intersects
        half_width = pred_rect.width() / 2
        half_height = pred_rect.height() / 2
        
        # Scale to rectangle boundary
        if abs(dx / half_width) > abs(dy / half_height):
            # Intersects left or right edge
            scale = half_width / abs(dx)
            anchor_x = center.x() + (half_width if dx > 0 else -half_width)
            anchor_y = center.y() + dy * scale
        else:
            # Intersects top or bottom edge
            scale = half_height / abs(dy)
            anchor_x = center.x() + dx * scale
            anchor_y = center.y() + (half_height if dy > 0 else -half_height)
        
        return QPointF(anchor_x, anchor_y)

    def _parse_qcolor(self, value: Any) -> QColor:
        """Convert common color encodings to QColor."""
        try:
            if isinstance(value, QColor):
                return value
            if isinstance(value, str):
                qc = QColor(value)
                if qc.isValid():
                    return qc
        except Exception:
            pass
        return QColor(0, 0, 0)


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



    def _find_vertex_at_position(self, pos: QPointF, tolerance: float = 15.0) -> Optional[str]:
        """Find vertex ID at the given scene position within tolerance."""
        for vid, vertex in self.model.vertices.items():
            v_pos = vertex.gfx.scenePos()
            distance = ((pos.x() - v_pos.x())**2 + (pos.y() - v_pos.y())**2)**0.5
            if distance <= tolerance:
                return vid
        return None
    

    def _complete_ligature_connection(self, target_vertex_id: Optional[str] = None, target_position: Optional[QPointF] = None) -> None:
        """Complete a ligature connection to a vertex or create new vertex in composition mode."""
        if not self._ligature_creation_active or not self._ligature_creation_from_predicate:
            return
        
        predicate_id = self._ligature_creation_from_predicate
        
        # Composition mode: create new vertex if no target vertex specified
        if target_vertex_id is None and target_position is not None and self._composition_mode:
            target_vertex_id = self._create_vertex_at_position(target_position)
            if target_vertex_id is None:
                self._cancel_ligature_creation()
                return
        
        if target_vertex_id is None:
            self._cancel_ligature_creation()
            return
        
        # Add to model ligatures
        if predicate_id not in self.model.ligatures:
            self.model.ligatures[predicate_id] = []
        if target_vertex_id not in self.model.ligatures[predicate_id]:
            self.model.ligatures[predicate_id].append(target_vertex_id)
        
        # Clear creation state
        self._ligature_creation_active = False
        self._ligature_creation_from_predicate = None
        if self._connection_preview_item:
            self.scene.removeItem(self._connection_preview_item)
            self._connection_preview_item = None
        
        # Refresh ligatures to show the new connection
        if self._show_ligatures:
            self._schedule_ligature_refresh()
    
    def _create_vertex_at_position(self, position: QPointF) -> Optional[str]:
        """Create a new vertex at the specified position in composition mode."""
        # Determine parent area for the new vertex
        parent_map = self._compute_parent_map()
        target_area = self._resolve_area_position(position, parent_map)
        
        # Generate unique vertex ID
        vertex_id = f"v_{uuid.uuid4().hex[:8]}"
        
        # Create vertex graphics item
        vertex_item = QGraphicsEllipseItem(-5, -5, 10, 10)
        vertex_item.setPos(position)
        vertex_item.setBrush(QBrush(QColor(100, 100, 255)))
        vertex_item.setPen(QPen(QColor(50, 50, 150), 2))
        
        # Add to model
        self.model.vertices[vertex_id] = VertexItem(
            id=vertex_id,
            pos=position,
            area_id=target_area,
            gfx=vertex_item
        )
        
        # Add to scene
        self.scene.addItem(vertex_item)
        
        # Update z-order
        depth = self._area_depth(target_area, parent_map)
        vertex_item.setZValue(depth * 10.0 + 1.0)
        
        return vertex_id
    
    def _resolve_area_position(self, position: QPointF, parent_map: Dict[str, str]) -> str:
        """Determine which area contains the given position."""
        # Check cuts in depth order (deepest first)
        cut_depths = []
        for cut_id, cut in self.model.cuts.items():
            depth = self._area_depth(cut_id, parent_map)
            cut_depths.append((depth, cut_id, cut))
        
        # Sort by depth (deepest first)
        cut_depths.sort(reverse=True)
        
        for depth, cut_id, cut in cut_depths:
            cut_rect = cut.gfx.sceneBoundingRect()
            if cut_rect.contains(position):
                return cut_id
        
        # Default to sheet area if not in any cut
        return "sheet"
    
    def _area_depth(self, area_id: str, parent_map: Dict[str, str]) -> int:
        """Calculate the depth of an area in the containment hierarchy."""
        if area_id == "sheet":
            return 0
        
        depth = 0
        current = area_id
        while current in parent_map and parent_map[current] != "sheet":
            depth += 1
            current = parent_map[current]
            if depth > 100:  # Prevent infinite loops
                break
        
        return depth + 1 if current != "sheet" else depth
    
    def _cancel_ligature_creation(self) -> None:
        """Cancel ongoing ligature creation."""
        self._ligature_creation_active = False
        self._ligature_creation_from_predicate = None
        if self._connection_preview_item:
            self.scene.removeItem(self._connection_preview_item)
            self._connection_preview_item = None
    
    
    def _start_ligature_creation(self, predicate_id: str) -> None:
        """Start ligature creation from a predicate."""
        self._ligature_creation_active = True
        self._ligature_creation_from_predicate = predicate_id
        self._smart_target_cache.clear()  # Clear cache for fresh calculations

    def _show_argument_order_dialog(self, predicate_id: str) -> None:
        """Show dialog to reorder predicate arguments."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel
        from PySide6.QtCore import Qt
        
        # Get current argument order
        connected_vertices = self.model.ligatures.get(predicate_id, [])
        if len(connected_vertices) < 2:
            return  # No need to reorder single or no arguments
        
        predicate_name = self.model.predicates[predicate_id].name
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Argument Order - {predicate_name}")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Instructions
        instructions = QLabel(f"Drag to reorder arguments for predicate '{predicate_name}'.\nLast position = output (by convention)")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # List widget for reordering
        list_widget = QListWidget()
        list_widget.setDragDropMode(QListWidget.InternalMove)
        
        # Add current vertices in order
        for i, vertex_id in enumerate(connected_vertices):
            vertex_name = self._get_vertex_display_name(vertex_id)
            position_label = "OUTPUT" if i == len(connected_vertices) - 1 else f"ARG {i+1}"
            item = QListWidgetItem(f"{vertex_name} [{position_label}]")
            item.setData(Qt.UserRole, vertex_id)
            list_widget.addItem(item)
        
        layout.addWidget(list_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        apply_btn = QPushButton("Apply")
        
        cancel_btn.clicked.connect(dialog.reject)
        apply_btn.clicked.connect(lambda: self._apply_argument_order(dialog, list_widget, predicate_id))
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(apply_btn)
        layout.addLayout(button_layout)
        
        dialog.exec_()

    def _get_vertex_display_name(self, vertex_id: str) -> str:
        """Get display name for vertex (variable name or constant)."""
        vertex = self.model.vertices.get(vertex_id)
        if vertex and hasattr(vertex, 'label') and vertex.label:
            # Named constant
            return f'"{vertex.label}"'
        
        # For generic vertices, use a simple alphabetic naming scheme
        # This matches what users expect to see
        vertex_index = list(self.model.vertices.keys()).index(vertex_id) if vertex_id in self.model.vertices else 0
        variable_name = chr(ord('x') + (vertex_index % 26))  # x, y, z, then wrap around
        return f"*{variable_name}"

    def _apply_argument_order(self, dialog, list_widget, predicate_id: str) -> None:
        """Apply the new argument order from the dialog."""
        # Extract new order from list widget
        new_order = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            vertex_id = item.data(Qt.UserRole)
            new_order.append(vertex_id)
        
        # Update the ligature order
        self.model.ligatures[predicate_id] = new_order
        
        # Refresh the display
        self._schedule_ligature_refresh()
        self._update_egif_preview()
        
        dialog.accept()

    def _toggle_vertex_annotations(self):
        """Toggle display of vertex variable names."""
        show_names = self.act_show_vertex_names.isChecked()
        for vertex_id, vertex in self.model.vertices.items():
            if vertex.gfx:
                self._update_vertex_annotation(vertex_id, show_names)

    def _toggle_arity_annotations(self):
        """Toggle display of predicate arity numbers."""
        show_arity = self.act_show_predicate_arity.isChecked()
        for predicate_id, predicate in self.model.predicates.items():
            if predicate.gfx_rect:
                self._update_predicate_annotation(predicate_id, show_arity)

    def _update_vertex_annotation(self, vertex_id: str, show_name: bool):
        """Update vertex annotation display."""
        vertex = self.model.vertices.get(vertex_id)
        if not vertex or not vertex.gfx:
            return
        
        # Remove existing annotation
        if hasattr(vertex, '_name_annotation') and vertex._name_annotation:
            self.scene.removeItem(vertex._name_annotation)
            vertex._name_annotation = None
        
        if show_name:
            from PySide6.QtWidgets import QGraphicsTextItem
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QFont, QColor
            
            # Create text annotation
            text_item = QGraphicsTextItem(self._get_vertex_display_name(vertex_id))
            text_item.setDefaultTextColor(QColor(0, 0, 200))
            text_item.setFont(QFont("Arial", 8))
            
            # Position below vertex
            vertex_pos = vertex.gfx.scenePos()
            text_item.setPos(vertex_pos.x() - 10, vertex_pos.y() + 15)
            
            self.scene.addItem(text_item)
            vertex._name_annotation = text_item

    def _update_predicate_annotation(self, predicate_id: str, show_arity: bool):
        """Update predicate arity annotation display."""
        predicate = self.model.predicates.get(predicate_id)
        if not predicate or not predicate.gfx_rect:
            return
        
        # Remove existing annotation
        if hasattr(predicate, '_arity_annotation') and predicate._arity_annotation:
            self.scene.removeItem(predicate._arity_annotation)
            predicate._arity_annotation = None
        
        if show_arity:
            from PySide6.QtWidgets import QGraphicsTextItem
            from PySide6.QtGui import QFont, QColor
            
            # Get arity from ligatures
            connected_vertices = self.model.ligatures.get(predicate_id, [])
            arity = len(connected_vertices)
            
            # Create arity annotation
            text_item = QGraphicsTextItem(f"({arity})")
            text_item.setDefaultTextColor(QColor(200, 0, 0))
            text_item.setFont(QFont("Arial", 8))
            
            # Position at top-right of predicate
            predicate_pos = predicate.gfx_rect.scenePos()
            text_item.setPos(predicate_pos.x() + 40, predicate_pos.y() - 5)
            
            self.scene.addItem(text_item)
            predicate._arity_annotation = text_item
    
    def _find_vertex_at_position(self, position: QPointF, tolerance: float = 10.0) -> Optional[str]:
        """Find vertex ID at the given position within tolerance."""
        for vertex_id, vertex in self.model.vertices.items():
            vertex_pos = vertex.gfx.scenePos()
            distance = ((vertex_pos.x() - position.x())**2 + (vertex_pos.y() - position.y())**2)**0.5
            if distance <= tolerance:
                return vertex_id
        return None
    
    def _update_connection_preview(self) -> None:
        """Update the visual preview of the ligature being created."""
        if not self._ligature_creation_active or not self._ligature_creation_from_predicate:
            return
        
        # Get current mouse position
        mouse_pos = self.view.mapToScene(self.view.mapFromGlobal(QCursor.pos()))
        
        # Get predicate position
        predicate = self.model.predicates.get(self._ligature_creation_from_predicate)
        if not predicate:
            return
        
        pred_rect = predicate.gfx_rect.sceneBoundingRect()
        pred_center = pred_rect.center()
        
        # Check if hovering over a vertex for smart targeting
        target_vertex = self._find_vertex_at_position(mouse_pos)
        if target_vertex:
            target_point = self._get_smart_connection_target(target_vertex, pred_center)
        else:
            target_point = mouse_pos
        
        # Calculate start point on predicate border
        start_point = self._rect_border_anchor(pred_rect, target_point)
        
        # Create preview path
        preview_path = self._create_path_by_mode(start_point, target_point)
        
        # Update or create preview item
        if self._connection_preview_item:
            self._connection_preview_item.setPath(preview_path)
        else:
            self._connection_preview_item = QGraphicsPathItem(preview_path)
            preview_pen = QPen(QColor(255, 100, 100), 2, Qt.DashLine)
            self._connection_preview_item.setPen(preview_pen)
            self._connection_preview_item.setZValue(1000)  # High z-value for visibility
            self.scene.addItem(self._connection_preview_item)
    
    def _get_flexible_branching_junction(self, vertex_id: str, predicate_ids: List[str]) -> QPointF:
        """Calculate optimal junction point for multi-predicate branching."""
        # Check if user has set a custom junction point
        if vertex_id in self._user_junction_points:
            return self._user_junction_points[vertex_id]
        
        # Calculate centroid-based junction (existing logic)
        vertex = self.model.vertices.get(vertex_id)
        if not vertex:
            return QPointF(0, 0)
        
        v_center = vertex.gfx.scenePos()
        
        # Collect predicate centers
        p_centers = []
        for pid in predicate_ids:
            pred = self.model.predicates.get(pid)
            if pred:
                rect = pred.gfx_rect.sceneBoundingRect()
                p_centers.append(rect.center())
        
        if not p_centers:
            return v_center
        
        # Calculate centroid direction
        cx = sum(pc.x() for pc in p_centers) / len(p_centers)
        cy = sum(pc.y() for pc in p_centers) / len(p_centers)
        
        # Junction at configurable distance from vertex toward centroid
        trunk_length = 24.0  # Can be made configurable
        dirx = cx - v_center.x()
        diry = cy - v_center.y()
        dlen = (dirx * dirx + diry * diry) ** 0.5
        
        if dlen < 1e-6:
            return v_center
        
        jx = v_center.x() + dirx / dlen * trunk_length
        jy = v_center.y() + diry / dlen * trunk_length
        return QPointF(jx, jy)

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
                # Locked mode: allow free movement for now
                pass
        except Exception:
            # Fail-open: do not block the UI if reassignment has issues
            pass
        
        # Check target match now that interaction is complete
        try:
            self._check_target_match_and_update_display()
        except Exception:
            pass
        
        # Also refresh the semantic preview (EGI/EGIF) after moves/resizes
        self._schedule_preview()


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
        # Old vertex-initiated ligature drag system disabled
        super().keyPressEvent(event)

    def _delete_selected_items(self) -> None:
        # Remove selected vertices/predicates/cuts; update model and ligatures
        if self.egi_locked:
            self.statusBar().showMessage("Practice/Locked: deletion would change logical structure.", 1500)
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
            
            # Remove items
            for vid in remove_vertices:
                self._remove_vertex(vid)
            for pid in remove_predicates:
                self._remove_predicate(pid)
            for cid in remove_cuts:
                self._remove_cut(cid)
        finally:
            self.end_interaction()

    def _remove_vertex(self, vid: str) -> None:
        """Remove vertex and clean up nu mappings in connected predicates."""
        if vid not in self.model.vertices:
            return
        
        vertex = self.model.vertices[vid]
        
        # Remove from nu mappings of all predicates
        for pid, predicate in self.model.predicates.items():
            # Check if this vertex is referenced in any nu mapping
            nu_map = getattr(predicate, 'nu', {})
            if nu_map:
                # Remove all references to this vertex
                keys_to_remove = [k for k, v in nu_map.items() if v == vid]
                for k in keys_to_remove:
                    del nu_map[k]
        
        # Remove graphics item from scene
        if vertex.gfx:
            self.scene.removeItem(vertex.gfx)
            if vertex.gfx_label:
                self.scene.removeItem(vertex.gfx_label)
        
        # Remove from model
        del self.model.vertices[vid]
        
        # Refresh ligatures since connections may have changed
        self._schedule_ligature_refresh()
        self._log(f"REMOVE_VERTEX ok id={vid}")

    def _remove_predicate(self, pid: str) -> None:
        """Remove predicate and its graphics items."""
        if pid not in self.model.predicates:
            return
        
        predicate = self.model.predicates[pid]
        
        # Remove graphics items from scene
        if predicate.gfx_rect:
            self.scene.removeItem(predicate.gfx_rect)
        if predicate.gfx_text:
            self.scene.removeItem(predicate.gfx_text)
        
        # Remove from model
        del self.model.predicates[pid]
        
        # Refresh ligatures since connections may have changed
        self._schedule_ligature_refresh()
        self._log(f"REMOVE_PREDICATE ok id={pid}")

    def _remove_cut(self, cid: str) -> None:
        """Remove cut and reassign contained elements to parent area."""
        if cid not in self.model.cuts:
            return
        
        cut = self.model.cuts[cid]
        parent_area = cut.parent_id or self.model.sheet_id
        
        # Reassign vertices in this cut to parent area
        for vid, vertex in self.model.vertices.items():
            if vertex.area_id == cid:
                vertex.area_id = parent_area
        
        # Reassign predicates in this cut to parent area
        for pid, predicate in self.model.predicates.items():
            if predicate.area_id == cid:
                predicate.area_id = parent_area
        
        # Reassign child cuts to parent area
        for child_cid, child_cut in self.model.cuts.items():
            if child_cut.parent_id == cid:
                child_cut.parent_id = parent_area
        
        # Remove graphics item from scene
        if cut.gfx:
            self.scene.removeItem(cut.gfx)
        
        # Remove from model
        del self.model.cuts[cid]
        
        # Refresh ligatures and update display
        self._schedule_ligature_refresh()
        self._log(f"REMOVE_CUT ok id={cid}")

    def _identify_double_negatives(self) -> List[str]:
        """Identify cuts that are double negatives using transformation rules module."""
        try:
            from transformation_rules import identify_double_negatives
        except ImportError:
            return []  # Fallback if transformation_rules unavailable
        
        # Build DTO from current model state
        dto = self._build_dto_from_model()
        
        # Use transformation_rules for platform-independent detection
        return identify_double_negatives(dto, self.model.sheet_id)

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
        # Set z-values according to EGI semantics:
        # - sheet background (implicit) is lowest (z=0)
        # - cuts increase with depth (z = depth * 10)
        # - predicates/vertices at the same level as their containing area (z = area_depth * 10)
        # - ligatures highest as they transcend all cuts (z = 1000)
        self._suppress_scene_change = True
        try:
            parent_map = self._compute_parent_map()
            
            # Set cut z-values by depth
            for cid, c in self.model.cuts.items():
                depth = self._area_depth(cid, parent_map)
                c.gfx.setZValue(depth * 10.0)
            
            # Set predicate z-values ABOVE their containing area for selectability
            for pid, p in self.model.predicates.items():
                # Use center of predicate for area detection
                pred_rect = p.gfx_rect.sceneBoundingRect()
                pred_center = pred_rect.center()
                area = self._resolve_area_position(pred_center, parent_map)
                depth = self._area_depth(area, parent_map)
                # Predicates above their containing area for selectability
                p.gfx_rect.setZValue(depth * 10.0 + 2.0)
                # Ensure text is slightly above rectangle for readability
                if hasattr(p, 'gfx_text') and p.gfx_text:
                    p.gfx_text.setZValue(depth * 10.0 + 2.1)
            
            # Set vertex z-values ABOVE their containing area for selectability
            for vid, v in self.model.vertices.items():
                # Use center of vertex for area detection
                vertex_rect = v.gfx.sceneBoundingRect()
                vertex_center = vertex_rect.center()
                area = self._resolve_area_position(vertex_center, parent_map)
                depth = self._area_depth(area, parent_map)
                # Vertices above their containing area for selectability
                v.gfx.setZValue(depth * 10.0 + 1.0)
            
            # Ligatures transcend all cuts - highest z-order
            for item in self._ligature_items:
                item.setZValue(1000.0)
                
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
    
    def _get_or_generate_id(self, prefix: str, element_type: str) -> str:
        """Get existing ID from original EGI if available, otherwise generate new ID.
        
        Args:
            prefix: ID prefix (e.g., 'v', 'e', 'c')
            element_type: Type of element ('vertices', 'predicates', 'cuts')
        """
        # Check if we have original EGI IDs to preserve
        if hasattr(self, '_original_egi_ids') and self._original_egi_ids:
            original_ids = self._original_egi_ids.get(element_type, set())
            
            # Find an unused original ID with matching prefix
            for original_id in original_ids:
                if original_id.startswith(f"{prefix}_"):
                    # Check if this ID is already used in current model
                    if element_type == 'vertices' and original_id not in self.model.vertices:
                        return original_id
                    elif element_type == 'predicates' and original_id not in self.model.predicates:
                        return original_id
                    elif element_type == 'cuts' and original_id not in self.model.cuts:
                        return original_id
        
        # Fallback: generate new ID if no original ID available
        return self._generate_id(prefix)

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
                # Old vertex-initiated ligature system disabled
                if self.mode == Mode.ADD_CUT:
                    # In locked mode, prevent adding cuts (changes logical structure)
                    if self.egi_locked:
                        self._set_mode(Mode.SELECT)
                        self.statusBar().showMessage("Practice/Locked: adding cuts would change logical structure.", 1500)
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
                        self.statusBar().showMessage("Practice/Locked: adding vertices would change logical structure.", 1500)
                        return True
                    self._add_vertex(scene_pos)
                    self._schedule_preview()
                    # Return to baseline select mode after a single add
                    self._set_mode(Mode.SELECT)
                elif self.mode == Mode.ADD_PREDICATE:
                    if self.egi_locked:
                        self._set_mode(Mode.SELECT)
                        self.statusBar().showMessage("Practice/Locked: adding predicates would change logical structure.", 1500)
                        return True
                    self._add_predicate(scene_pos)
                    self._schedule_preview()
                    # Return to baseline select mode after a single add
                    self._set_mode(Mode.SELECT)
                return False
            elif event.type() == QEvent.MouseMove:
                # Old vertex-initiated ligature drag system disabled
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
                # Old vertex-initiated ligature drag system disabled
                if self.mode == Mode.ADD_CUT and self._drag_start is not None:
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
        cid = self._get_or_generate_id("c", "cuts")
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
        vid = self._get_or_generate_id("v", "vertices")
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

    def _find_non_overlapping_position(self, desired_pos: QPointF, item_rect: QRectF) -> QPointF:
        """Find a position near desired_pos where item_rect won't overlap with existing elements."""
        test_rect = QRectF(item_rect)
        test_rect.moveTopLeft(desired_pos)
        
        # Check for overlaps with existing predicates
        for p in self.model.predicates.values():
            if p.gfx_rect and p.gfx_rect.scene():
                existing_rect = p.gfx_rect.sceneBoundingRect()
                if test_rect.intersects(existing_rect):
                    # Move to the right of the existing predicate
                    test_rect.moveLeft(existing_rect.right() + 5)
        
        # Check for overlaps with vertices
        for v in self.model.vertices.values():
            if v.gfx and v.gfx.scene():
                existing_rect = v.gfx.sceneBoundingRect()
                if test_rect.intersects(existing_rect):
                    # Move to the right of the existing vertex
                    test_rect.moveLeft(existing_rect.right() + 5)
        
        return test_rect.topLeft()

    def _add_predicate(self, pos: QPointF) -> None:
        text, ok = QInputDialog.getText(self, "Predicate", "Name:")
        if not ok or not text:
            return
        eid = self._get_or_generate_id("e", "predicates")
        area = self._current_area_for_add(pos)
        
        # Check for collisions and adjust position if needed
        label = QGraphicsTextItem(text)
        rect = label.boundingRect().adjusted(-2, -1, 2, 1)
        adjusted_pos = self._find_non_overlapping_position(pos, rect)
        
        self._log(f"ADD_PREDICATE id={eid} name={text} pos=({adjusted_pos.x():.1f},{adjusted_pos.y():.1f}) area={area}")
        rect_item = PredicateRectItem(rect, self)
        rect_item.setBrush(Qt.NoBrush)
        rect_item.setPen(QPen(QColor(0, 0, 0, 0), 0))
        rect_item.setPos(adjusted_pos)
        # Parent text to rect so they move together
        label.setParentItem(rect_item)
        label.setPos(2, 1)
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
        # In locked mode, block authoring operations that change logical structure
        if self.egi_locked:
            self.statusBar().showMessage("Practice/Locked: add operations would change logical structure.", 1500)
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
        # Note: Ligature creation is now predicate-initiated (right-click on predicates)
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
        # Old vertex-initiated ligature system disabled - use predicate-initiated instead
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
        
        # Add ligature creation option at the top
        act_create_ligature = menu.addAction("Create ligature...")
        menu.addSeparator()
        
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
        elif chosen is act_create_ligature:
            # Start ligature creation from this predicate
            self._start_ligature_creation(pid)
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
        if self.embedded_mode:
            try:
                QMessageBox.information(self, "Embedded", "Save is managed by Organon in embedded mode.")
            except Exception:
                pass
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Drawing", "drawing.json", "JSON (*.json)")
        if not path:
            return
        schema = self._gather_schema_from_scene()
        Path(path).write_text(json.dumps(schema, indent=2))
        QMessageBox.information(self, "Saved", f"Saved drawing to {path}")
        if self.act_auto.isChecked():
            self._update_preview()

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
        # Skip ligature refresh during EGDF layout application to prevent element clearing
        # self._schedule_ligature_refresh()

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
            # Skip autoload if we already have positioned elements from EGDF
            if hasattr(self, 'model') and self.model and len(self.model.vertices) > 0:
                return
                
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
            # Skip confirmation prompt when loading from Organon handoff
            # Only prompt for manual corpus loading, not programmatic handoffs
            # Convert and populate
            try:
                schema = self._schema_from_relational_graph(rgc)
            except Exception as e:
                QMessageBox.critical(self, "Conversion Error", f"Failed to convert EGIF: {e}")
                return
            self.begin_interaction()
            try:
                self.scene.clear()
                self._initialize_clean_model_from_schema(schema)
                # Skip auto-placement - manual diagramming mode
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
            self._update_preview()

    # ----- Ergasterion Modes -----
    def _set_mode_composition(self) -> None:
        self.erg_mode = "composition"
        self.semantic_guardrails = False
        # Composition mode allows meaning changes - unlock EGI
        self.egi_locked = False
        self.act_mode_composition.setChecked(True)
        self.act_mode_practice.setChecked(False)
        self.statusBar().showMessage("Ergasterion: Composition Mode (semantic guardrails off)")
        self._refresh_status_banner()

    def _set_mode_practice(self) -> None:
        self.erg_mode = "practice"
        self.semantic_guardrails = True
        # Practice mode assumes meaning is fixed - lock EGI
        self.egi_locked = True
        self.act_mode_composition.setChecked(False)
        self.act_mode_practice.setChecked(True)
        self.statusBar().showMessage("Ergasterion: Practice Mode (semantic guardrails on)")
        self._refresh_status_banner()

    def _toggle_egi_lock(self) -> None:
        """Internal method to toggle EGI lock state - now controlled by mode changes."""
        if not self.egi_locked:
            # Trying to lock - validate against target if it exists
            if hasattr(self, '_target_egi_meta') and self._target_egi_meta:
                if not self._validate_egi_matches_target():
                    return  # Validation failed, don't lock
        
        self.egi_locked = not self.egi_locked
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
    
    def _validate_egi_matches_target(self) -> bool:
        """Validate that current EGI matches target EGI before allowing lock."""
        try:
            if not hasattr(self, '_target_egi_meta') or not self._target_egi_meta:
                return True  # No target, allow lock
            
            target = self._target_egi_meta.get('payload', {})
            current_schema = self._gather_schema_from_scene()
            
            # Compare structure counts
            target_vertices = len(target.get('V', []))
            target_predicates = len(target.get('E', []))
            target_cuts = len(target.get('Cut', []))
            
            current_vertices = len(current_schema.get('vertices', []))
            current_predicates = len(current_schema.get('predicates', []))
            current_cuts = len(current_schema.get('cuts', []))
            
            if (target_vertices != current_vertices or 
                target_predicates != current_predicates or 
                target_cuts != current_cuts):
                
                self.statusBar().showMessage(
                    f"Cannot lock: Current diagram structure ({current_vertices}V, {current_predicates}P, {current_cuts}C) "
                    f"does not match target ({target_vertices}V, {target_predicates}P, {target_cuts}C)"
                )
                return False
            
            # TODO: Add deeper semantic comparison (predicate names, connections, etc.)
            self.statusBar().showMessage("EGI structure matches target - ready to lock!")
            return True
            
        except Exception as e:
            self.statusBar().showMessage(f"Validation error: {e}")
            return False

    def _refresh_status_banner(self) -> None:
        try:
            mode_str = f"Mode: {self.erg_mode}/{self.mode}"
            if hasattr(self, 'status_mode_label'):
                self.status_mode_label.setText(mode_str)
            if hasattr(self, 'status_egi_label'):
                if self.puzzle_mode_active and not self.egi_locked:
                    egi_str = "EGI: Puzzle (unlocked)"
                else:
                    egi_str = f"EGI: {'locked' if self.egi_locked else 'unlocked'}"
                self.status_egi_label.setText(egi_str)
            # EGI Lock status indicator
            if hasattr(self, 'status_lock_label'):
                if self.egi_locked:
                    lock_str = "EGI Locked"
                    self.status_lock_label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    lock_str = "EGI Unlocked"
                    self.status_lock_label.setStyleSheet("color: orange; font-weight: bold;")
                self.status_lock_label.setText(lock_str)
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
            deltas = self._gather_layout_deltas()
            
            return {
                "egi": drawing_schema,
                "layout": layout,
                "styles": styles,
                "deltas": deltas,
            }
        except Exception:
            return {}

    def on_export_egdf(self) -> None:
        """Export EGDF (EGI + layout + style + deltas)."""
        try:
            egdf_payload = self.export_result()
            egdf_doc = egdf_payload.get("egdf", {})
            if not egdf_doc:
                QMessageBox.warning(self, "Export", "No EGDF to export.")
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export EGDF", "", "EGDF Files (*.egdf.json);;All Files (*)"
            )
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(egdf_doc, f, indent=2)
                QMessageBox.information(self, "Export", f"EGDF exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export EGDF: {e}")

    def on_return_to_organon(self) -> None:
        """Return to Organon with complete EGDF (EGI + layout + style + deltas)."""
        try:
            # Generate EGI from current diagram
            egi = self._build_egi()
            if not egi:
                QMessageBox.warning(self, "Return", "No valid EGI to return. Create a diagram first.")
                return
            
            # Use the complete EGDF workflow
            self._send_to_organon(egi, "manual_diagram")
            
        except Exception as e:
            QMessageBox.critical(self, "Return Error", f"Failed to return diagram: {e}")

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
        """Swap raw cut rects to `CutRectItem` and set tooltips.
        Enforces syntactic constraints and enables proper editing functionality.
        """
        # Upgrade graphics items to constraint-aware versions with proper editing support
        for cid, c in list(self.model.cuts.items()):
            if not isinstance(c.gfx, CutRectItem):
                old_item = c.gfx
                rect = self._scene_rect_for_item(old_item)
                new_item = CutRectItem(rect, self)
                new_item.setPen(old_item.pen())
                new_item.setBrush(old_item.brush())
                new_item.setFlag(QGraphicsItem.ItemIsMovable, True)
                new_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
                new_item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
                new_item.setToolTip(f"Cut: {cid}")
                self.scene.addItem(new_item)
                try:
                    self.scene.removeItem(old_item)
                except Exception:
                    pass
                self.model.cuts[cid].gfx = new_item

        # Enable editing for vertices and predicates
        for vid, v in self.model.vertices.items():
            v.gfx.setFlag(QGraphicsItem.ItemIsMovable, True)
            v.gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)
            v.gfx.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
            v.gfx.setToolTip(f"Vertex: {vid}")
            
        # Upgrade predicates to PredicateRectItem if needed
        for pid, p in list(self.model.predicates.items()):
            if not isinstance(p.gfx_rect, PredicateRectItem):
                print(f"[DEBUG] Converting predicate {pid} from {type(p.gfx_rect)} to PredicateRectItem")
                # Convert generic QGraphicsRectItem to PredicateRectItem
                old_rect = p.gfx_rect
                rect = old_rect.rect()
                scene_pos = old_rect.scenePos()
                try:
                    self.scene.removeItem(old_rect)
                except Exception:
                    pass
                new_rect = PredicateRectItem(rect, self)
                new_rect.setBrush(Qt.NoBrush)
                new_rect.setPen(QPen(QColor(0, 0, 0, 0), 0))
                new_rect.setPos(scene_pos)
                # Recreate text child with tight bounds
                label = QGraphicsTextItem(p.name)
                text_rect = label.boundingRect()
                
                # Resize rectangle to fit text tightly
                padding = 4
                tight_width = text_rect.width() + padding
                tight_height = text_rect.height() + padding
                new_rect.setRect(QRectF(0, 0, tight_width, tight_height))
                
                label.setParentItem(new_rect)
                label.setPos(padding/2, padding/2)  # Center with minimal padding
                label.setFlag(QGraphicsItem.ItemIsMovable, False)
                label.setFlag(QGraphicsItem.ItemIsSelectable, False)
                self.scene.addItem(new_rect)
                # Don't add label to scene - it's automatically added as child of new_rect
                self.model.predicates[pid].gfx_rect = new_rect
                self.model.predicates[pid].gfx_text = label
            else:
                print(f"[DEBUG] Predicate {pid} already is PredicateRectItem")
            
            # Enable editing flags
            p.gfx_rect.setFlag(QGraphicsItem.ItemIsMovable, True)
            p.gfx_rect.setFlag(QGraphicsItem.ItemIsSelectable, True)
            p.gfx_rect.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
            p.gfx_rect.setToolTip(f"Predicate: {pid} [{p.name}]")
            # Ensure text is properly parented and disable independent movement
            if hasattr(p, 'gfx_text') and p.gfx_text:
                # Make sure text is child of rectangle
                if p.gfx_text.parentItem() != p.gfx_rect:
                    p.gfx_text.setParentItem(p.gfx_rect)
                p.gfx_text.setFlag(QGraphicsItem.ItemIsMovable, False)
                p.gfx_text.setFlag(QGraphicsItem.ItemIsSelectable, False)
        
        # Apply syntactic constraints to prevent overlapping cuts
        self._enforce_cut_containment_constraints()
        
        # Set proper z-ordering
        self._schedule_zorder_refresh()

    def _enforce_cut_containment_constraints(self) -> None:
        """Enforce syntactic constraints to prevent overlapping cuts and maintain proper containment."""
        parent_map = self._compute_parent_map()
        
        # Separate cuts by depth level
        cuts_by_depth = {}
        for cut_id, cut in self.model.cuts.items():
            depth = self._area_depth(cut_id, parent_map)
            if depth not in cuts_by_depth:
                cuts_by_depth[depth] = []
            cuts_by_depth[depth].append((cut_id, cut))
        
        # Process cuts from outermost to innermost, ensuring no overlaps
        for depth in sorted(cuts_by_depth.keys()):
            self._arrange_cuts_at_depth(cuts_by_depth[depth], parent_map)
    
    def _arrange_cuts_at_depth(self, cuts_at_depth: List[Tuple[str, 'DrawingModel.Cut']], parent_map: Dict[str, str]) -> None:
        """Arrange cuts at the same depth to avoid overlaps while maintaining containment."""
        if not cuts_at_depth:
            return
        
        # Group cuts by their parent area
        cuts_by_parent = {}
        for cut_id, cut in cuts_at_depth:
            parent_area = parent_map.get(cut_id, "sheet")
            if parent_area not in cuts_by_parent:
                cuts_by_parent[parent_area] = []
            cuts_by_parent[parent_area].append((cut_id, cut))
        
        # Arrange cuts within each parent area
        for parent_area, sibling_cuts in cuts_by_parent.items():
            if len(sibling_cuts) <= 1:
                continue
            
            # Get parent bounds
            if parent_area == "sheet":
                # Use scene bounds for sheet
                parent_bounds = QRectF(0, 0, 800, 600)
            else:
                parent_cut = self.model.cuts.get(parent_area)
                if parent_cut:
                    parent_bounds = parent_cut.gfx.sceneBoundingRect().adjusted(20, 20, -20, -20)
                else:
                    continue
            
            # Arrange sibling cuts in a non-overlapping grid
            self._arrange_cuts_in_grid(sibling_cuts, parent_bounds)
    
    def _arrange_cuts_in_grid(self, cuts: List[Tuple[str, 'DrawingModel.Cut']], bounds: QRectF) -> None:
        """Arrange cuts in a non-overlapping grid within the given bounds."""
        if not cuts:
            return
        
        # Calculate grid dimensions
        num_cuts = len(cuts)
        cols = int(math.ceil(math.sqrt(num_cuts)))
        rows = int(math.ceil(num_cuts / cols))
        
        # Calculate cell size
        cell_width = bounds.width() / cols
        cell_height = bounds.height() / rows
        
        # Position each cut in its grid cell
        for i, (cut_id, cut) in enumerate(cuts):
            row = i // cols
            col = i % cols
            
            # Calculate position within cell (centered)
            cut_rect = cut.gfx.sceneBoundingRect()
            cell_x = bounds.left() + col * cell_width
            cell_y = bounds.top() + row * cell_height
            
            # Center cut within cell
            new_x = cell_x + (cell_width - cut_rect.width()) / 2
            new_y = cell_y + (cell_height - cut_rect.height()) / 2
            
            # Ensure cut fits within cell bounds
            new_x = max(cell_x + 10, min(new_x, cell_x + cell_width - cut_rect.width() - 10))
            new_y = max(cell_y + 10, min(new_y, cell_y + cell_height - cut_rect.height() - 10))
            
            cut.gfx.setPos(new_x, new_y)

    def _initialize_clean_model_from_schema(self, schema: Dict[str, Any]) -> None:
        """Initialize clean model structure from schema for manual diagramming.
        
        Two paths:
        1. EGI-target: Schema has existing structure, user diagrams to represent it
        2. Evolving-EGI: Schema is empty/minimal, user builds from scratch
        """
        
        # Initialize empty model
        self.model = DrawingModel()
        
        # Extract elements from schema to understand target structure
        cuts_data = schema.get('cuts', [])
        vertices_data = schema.get('vertices', [])
        predicates_data = schema.get('predicates', [])
        
        # Store target structure for reference but don't place elements
        # User will manually diagram the structure
        self._target_structure = {
            'cuts': cuts_data,
            'vertices': vertices_data, 
            'predicates': predicates_data,
            'ligatures': schema.get('ligatures', [])
        }
        
        # Store original EGI IDs to preserve them during editing
        self._original_egi_ids = {
            'vertices': {v.get('id') for v in vertices_data if v.get('id')},
            'predicates': {p.get('id') for p in predicates_data if p.get('id')},
            'cuts': {c.get('id') for c in cuts_data if c.get('id')}
        }
        
        # Create model elements from schema - create graphics items too
        from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsRectItem
        
        for vertex_data in schema.get("vertices", []):
            vertex_id = vertex_data.get("id")
            area_id = vertex_data.get("area_id", "sheet")
            if vertex_id:
                # Create proper VertexGfxItem from start to avoid replacement
                gfx_item = VertexGfxItem(-5, -5, 10, 10, self)
                # Position will be set from schema data below
                gfx_item.setPen(QPen(QColor(0, 0, 255), 2))
                gfx_item.setBrush(QBrush(QColor(0, 0, 255)))
                gfx_item.setFlag(QGraphicsItem.ItemIsMovable, True)
                gfx_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
                gfx_item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
                self.scene.addItem(gfx_item)
                
                vertex = VertexItem(
                    id=vertex_id,
                    pos=vertex_data.get("pos", QPointF(0, 0)),
                    area_id=area_id,
                    gfx=gfx_item
                )
                # Set graphics item position from vertex position
                gfx_item.setPos(vertex.pos)
                self.model.vertices[vertex_id] = vertex
        
        for predicate_data in schema.get("predicates", []):
            predicate_id = predicate_data.get("id")
            predicate_name = predicate_data.get("name", predicate_id)
            area_id = predicate_data.get("area_id", "sheet")
            if predicate_id:
                # Create proper PredicateRectItem from start to avoid replacement
                gfx_text = QGraphicsTextItem(predicate_name)
                text_rect = gfx_text.boundingRect()
                padding = 4
                rect_width = text_rect.width() + padding
                rect_height = text_rect.height() + padding
                
                gfx_rect = PredicateRectItem(QRectF(0, 0, rect_width, rect_height), self)
                # Position will be set from schema data below
                gfx_rect.setBrush(Qt.NoBrush)
                gfx_rect.setPen(QPen(QColor(0, 0, 0, 0), 0))
                gfx_rect.setFlag(QGraphicsItem.ItemIsMovable, True)
                gfx_rect.setFlag(QGraphicsItem.ItemIsSelectable, True)
                gfx_rect.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
                self.scene.addItem(gfx_rect)
                
                # Parent text to rectangle
                gfx_text.setParentItem(gfx_rect)
                gfx_text.setPos(padding/2, padding/2)
                gfx_text.setFlag(QGraphicsItem.ItemIsMovable, False)
                gfx_text.setFlag(QGraphicsItem.ItemIsSelectable, False)
                
                predicate = PredicateItem(
                    id=predicate_id,
                    name=predicate_name,
                    pos=predicate_data.get("pos", QPointF(0, 0)),
                    area_id=area_id,
                    gfx_text=gfx_text,
                    gfx_rect=gfx_rect
                )
                # Set graphics item position from predicate position
                gfx_rect.setPos(predicate.pos)
                self.model.predicates[predicate_id] = predicate
        
        for cut_data in schema.get("cuts", []):
            cut_id = cut_data.get("id")
            parent_id = cut_data.get("parent_id")
            if cut_id:
                # Create proper CutRectItem from start to avoid replacement
                gfx_item = CutRectItem(QRectF(0, 0, 100, 100), self)
                gfx_item.setPen(QPen(QColor(0, 0, 0), 2))
                gfx_item.setBrush(QBrush(QColor(255, 255, 255, 0)))
                gfx_item.setFlag(QGraphicsItem.ItemIsMovable, True)
                gfx_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
                gfx_item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
                self.scene.addItem(gfx_item)
                
                cut = CutItem(
                    id=cut_id,
                    rect=QRectF(0, 0, 100, 100),
                    parent_id=parent_id,
                    gfx=gfx_item
                )
                self.model.cuts[cut_id] = cut
        
        # Load ligature connections from schema
        for ligature_data in schema.get("ligatures", []):
            edge_id = ligature_data.get("edge_id")
            vertex_ids = ligature_data.get("vertex_ids", [])
            if edge_id and vertex_ids:
                self.model.ligatures[edge_id] = vertex_ids
        
        # Determine diagramming mode
        has_existing_structure = bool(cuts_data or vertices_data or predicates_data)
        self._diagramming_mode = "egi_target" if has_existing_structure else "evolving_egi"
        
        # Update status to guide user
        if self._diagramming_mode == "egi_target":
            self.statusBar().showMessage(f"EGI Target Mode: Diagram the provided structure ({len(cuts_data)} cuts, {len(vertices_data)} vertices, {len(predicates_data)} predicates)")
        else:
            self.statusBar().showMessage("Evolving EGI Mode: Create diagram from scratch")

    def _create_graphics_from_target_structure(self) -> None:
        """Create graphics items from target structure for existing diagrams."""
        if not hasattr(self, '_target_structure'):
            return
            
        structure = self._target_structure
        
        # Create cuts
        for cut_data in structure.get('cuts', []):
            cut_id = cut_data.get('id', '')
            if not cut_id:
                continue
            rect = QRectF(0, 0, 100, 100)  # Default size, will be positioned by layout
            self._add_cut_at_position(cut_id, rect)
        
        # Create vertices  
        for vertex_data in structure.get('vertices', []):
            vertex_id = vertex_data.get('id', '')
            if not vertex_id:
                continue
            pos = QPointF(0, 0)  # Default position, will be positioned by layout
            self._add_vertex_at_position(vertex_id, pos)
        
        # Create predicates
        for pred_data in structure.get('predicates', []):
            pred_id = pred_data.get('id', '')
            name = pred_data.get('name', pred_id)
            if not pred_id:
                continue
            pos = QPointF(0, 0)  # Default position, will be positioned by layout
            self._add_predicate_at_position(pred_id, name, pos)

    def _add_cut_at_position(self, cut_id: str, rect: QRectF) -> None:
        """Add a cut at the specified position, simulating user action."""
        cut_item = CutRectItem(rect, self)
        cut_item.setPen(QPen(QColor(0, 0, 0), 2))
        cut_item.setBrush(QBrush(QColor(255, 255, 255, 0)))
        cut_item.setFlag(QGraphicsItem.ItemIsMovable, True)
        cut_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        cut_item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.scene.addItem(cut_item)
        
        cut = CutItem(id=cut_id, rect=rect, parent_id=None, gfx=cut_item)
        self.model.cuts[cut_id] = cut

    def _add_vertex_at_position(self, vertex_id: str, pos: QPointF) -> None:
        """Add a vertex at the specified position, simulating user action."""
        vertex_item = VertexGfxItem(-5, -5, 10, 10, self)
        vertex_item.setPos(pos)
        vertex_item.setPen(QPen(QColor(0, 0, 255), 2))
        vertex_item.setBrush(QBrush(QColor(0, 0, 255)))
        vertex_item.setFlag(QGraphicsItem.ItemIsMovable, True)
        vertex_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        vertex_item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.scene.addItem(vertex_item)
        
        vertex = VertexItem(id=vertex_id, pos=pos, area_id="sheet", gfx=vertex_item)
        self.model.vertices[vertex_id] = vertex

    def _add_predicate_at_position(self, predicate_id: str, name: str, pos: QPointF) -> None:
        """Add a predicate at the specified position, simulating user action."""
        # Create predicate text first to measure its size
        pred_text = QGraphicsTextItem(name)
        text_rect = pred_text.boundingRect()
        
        # Create predicate rectangle sized to fit text with minimal padding
        padding = 2  # 1px padding on each side
        rect_width = text_rect.width() + padding
        rect_height = text_rect.height() + padding
        pred_rect = PredicateRectItem(QRectF(0, 0, rect_width, rect_height), self)
        pred_rect.setPos(pos)
        # Make predicate rectangle visible with red border for debugging
        pred_rect.setPen(QPen(QColor(255, 0, 0), 2))
        pred_rect.setBrush(QBrush(QColor(255, 255, 255, 50)))  # Semi-transparent white fill
        self.scene.addItem(pred_rect)
        
        # Parent text to rectangle and center it
        pred_text.setParentItem(pred_rect)  # Parent to rectangle, not scene
        pred_text.setPos(1, 1)  # Center with minimal padding
        pred_text.setFlag(QGraphicsItem.ItemIsMovable, False)
        pred_text.setFlag(QGraphicsItem.ItemIsSelectable, False)
        
        predicate = PredicateItem(
            id=predicate_id,
            name=name,
            pos=pos,
            area_id="sheet",
            gfx_text=pred_text,
            gfx_rect=pred_rect
        )
        self.model.predicates[predicate_id] = predicate

    def _create_ligature_between(self, predicate_id: str, vertex_id: str) -> None:
        """Create a ligature between predicate and vertex, simulating user action."""
        if predicate_id not in self.model.predicates or vertex_id not in self.model.vertices:
            return
        
        # Add to ligatures mapping (edge_id -> [vertex_id])
        if predicate_id not in self.model.ligatures:
            self.model.ligatures[predicate_id] = []
        
        if vertex_id not in self.model.ligatures[predicate_id]:
            self.model.ligatures[predicate_id].append(vertex_id)
        
        # The ligature visual will be created by the ligature refresh system
    
    def _create_hand_drawn_ligature(self, predicate_id: str, vertex_id: str, path) -> None:
        """Create a ligature using a hand-drawn path."""
        if predicate_id not in self.model.predicates or vertex_id not in self.model.vertices:
            return
        
        # Add to ligatures mapping
        if predicate_id not in self.model.ligatures:
            self.model.ligatures[predicate_id] = []
        
        if vertex_id not in self.model.ligatures[predicate_id]:
            self.model.ligatures[predicate_id].append(vertex_id)
        
        # Create visual representation using the hand-drawn path
        if path and HandDrawnPath:
            self._create_ligature_visual_from_path(predicate_id, vertex_id, path)
        else:
            # Fallback to regular ligature creation
            self._create_ligature_between(predicate_id, vertex_id)
    
    def _create_branching_ligature(self, predicate_id: str, target_edge_id: str, branch_point: QPointF, path) -> None:
        """Create a ligature that branches off an existing ligature."""
        # For now, create a simple connection - branching logic can be enhanced later
        # This would require more complex ligature data structures to track branch points
        pass
    
    def _create_vertex_at_position(self, pos: QPointF) -> str:
        """Create a new vertex at the specified position."""
        vertex_id = f"v_{uuid.uuid4().hex[:8]}"
        self._create_vertex(vertex_id, "•", pos)
        return vertex_id
    
    def _create_vertex(self, vertex_id: str, name: str, pos: QPointF) -> None:
        """Create a vertex with the given ID, name, and position."""
        # Create vertex visual
        vertex_item = QGraphicsEllipseItem(-5, -5, 10, 10)
        vertex_item.setPos(pos)
        vertex_item.setPen(QPen(QColor(0, 0, 255), 2))
        vertex_item.setBrush(QBrush(QColor(0, 0, 255)))
        vertex_item.setFlag(QGraphicsItem.ItemIsMovable, True)
        vertex_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        vertex_item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.scene.addItem(vertex_item)
        
        vertex = VertexItem(id=vertex_id, pos=pos, area_id="sheet", gfx=vertex_item)
        self.model.vertices[vertex_id] = vertex
    
    def _add_sample_content(self) -> None:
        """Add sample content to match the Cat-On-Mat diagram structure from Organon."""
        # Create the Cat-On-Mat structure: Cat -> On <- Mat
        self._add_predicate_at_position("pred_cat", "Cat", QPointF(100, 150))
        self._add_predicate_at_position("pred_on", "On", QPointF(250, 150))
        self._add_predicate_at_position("pred_mat", "Mat", QPointF(400, 150))
        
        # Add vertices for connections
        self._create_vertex("v1", "•", QPointF(175, 150))  # Between Cat and On
        self._create_vertex("v2", "•", QPointF(325, 150))  # Between On and Mat
        
        # Create ligatures: Cat -> v1 -> On -> v2 -> Mat
        self._create_ligature_between("pred_cat", "v1")
        self._create_ligature_between("pred_on", "v1")
        self._create_ligature_between("pred_on", "v2")
        self._create_ligature_between("pred_mat", "v2")
        
        # Schedule ligature refresh to show connections
        self._schedule_ligature_refresh()
    
    def _load_current_egdf(self) -> None:
        """Load the current EGDF file, similar to how Organon does it."""
        try:
            # Look for the sowa_cat_on_mat EGDF that Organon is using
            egdf_path = Path("corpus/graphs/sowa_cat_on_mat/EGDF/diagram_20250902_202811.egdf.json")
            print(f"[Ergasterion] Attempting to load EGDF from: {egdf_path}")
            print(f"[Ergasterion] File exists: {egdf_path.exists()}")
            if egdf_path.exists():
                self._load_egdf_file(egdf_path)
            else:
                print(f"[Ergasterion] EGDF file not found: {egdf_path}")
        except Exception as e:
            print(f"[Ergasterion] Failed to load EGDF: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_egdf_file(self, path: Path) -> None:
        """Load an EGDF file and render its contents."""
        try:
            # Import EGDF document class
            try:
                from egdf_parser import EGDFDocument
            except ImportError:
                print("EGDF document class not available")
                return
            
            # Read and parse EGDF
            print(f"[Ergasterion] Reading EGDF file...")
            text = path.read_text(encoding="utf-8")
            print(f"[Ergasterion] File content length: {len(text)} chars")
            
            doc = EGDFDocument.from_json(text)
            print(f"[Ergasterion] Successfully parsed EGDF document")
            
            # Clear existing content
            print(f"[Ergasterion] Clearing scene and resetting model...")
            self.scene.clear()
            self.model = DrawingModel()
            
            # Render EGDF content
            print(f"[Ergasterion] Rendering EGDF document...")
            self._render_egdf_document(doc)
            
            print(f"[Ergasterion] Successfully loaded EGDF from {path}")
            
        except Exception as e:
            print(f"Failed to load EGDF file {path}: {e}")
    
    def _render_egdf_document(self, doc) -> None:
        """Render an EGDF document to the scene."""
        try:
            # Get layout data from EGDF
            layout = doc.layout if hasattr(doc, 'layout') else {}
            print(f"[Ergasterion] Layout keys: {list(layout.keys())}")
            
            # Render predicates from layout.predicates
            predicates = layout.get('predicates', {})
            print(f"[Ergasterion] Found {len(predicates)} predicates: {list(predicates.keys())}")
            for pred_id, pred_data in predicates.items():
                text = pred_data.get('text', pred_id)
                x = pred_data.get('x', 100)
                y = pred_data.get('y', 100)
                pos = QPointF(x, y)
                print(f"[Ergasterion] Creating predicate {pred_id} '{text}' at ({x}, {y})")
                self._add_predicate_at_position(pred_id, text, pos)
            
            # Render vertices from layout.vertices
            vertices = layout.get('vertices', {})
            print(f"[Ergasterion] Found {len(vertices)} vertices: {list(vertices.keys())}")
            for vertex_id, vertex_data in vertices.items():
                x = vertex_data.get('x', 150)
                y = vertex_data.get('y', 150)
                pos = QPointF(x, y)
                print(f"[Ergasterion] Creating vertex {vertex_id} at ({x}, {y})")
                self._create_vertex(vertex_id, "•", pos)
            
            # Create ligatures from EGI nu (predicate -> vertex connections)
            egi_ref = doc.egi_ref if hasattr(doc, 'egi_ref') else {}
            inline = egi_ref.get('inline', {}) if isinstance(egi_ref, dict) else {}
            nu = inline.get('nu', {})
            print(f"[Ergasterion] Found nu connections: {nu}")
            
            for pred_id, vertex_list in nu.items():
                if isinstance(vertex_list, list):
                    for vertex_id in vertex_list:
                        if pred_id in self.model.predicates and vertex_id in self.model.vertices:
                            print(f"[Ergasterion] Creating ligature between {pred_id} and {vertex_id}")
                            self._create_ligature_between(pred_id, vertex_id)
            
            # Schedule refresh
            self._schedule_ligature_refresh()
            print(f"[Ergasterion] Finished rendering EGDF document")
            
        except Exception as e:
            print(f"[Ergasterion] Failed to render EGDF document: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_ligature_visual_from_path(self, predicate_id: str, vertex_id: str, path) -> None:
        """Create the visual representation of a ligature from a hand-drawn path."""
        if predicate_id not in self.model.predicates or vertex_id not in self.model.vertices:
            return
        
        predicate = self.model.predicates[predicate_id]
        vertex = self.model.vertices[vertex_id]
        
        # Get anchor points
        pred_center = predicate.gfx_rect.sceneBoundingRect().center()
        vertex_pos = vertex.gfx.scenePos()
        
        # Use the smoothed path from the hand-drawn input
        smoothed_path = path.smooth_path()
        
        # Adjust path to connect properly to predicate and vertex
        adjusted_path = self._adjust_path_endpoints(smoothed_path, pred_center, vertex_pos)
        
        # Create graphics item
        ligature_item = QGraphicsPathItem(adjusted_path)
        
        # Apply styling
        if hasattr(self, '_styles') and self._styles:
            edge_style = self._styles.get("edge", {})
            pen_color = QColor(edge_style.get("color", "black"))
            pen_width = edge_style.get("width", 2)
            ligature_item.setPen(QPen(pen_color, pen_width))
        else:
            ligature_item.setPen(QPen(QColor(0, 0, 0), 2))
        
        ligature_item.setZValue(-1)  # Behind other items
        self.scene.addItem(ligature_item)
        self._ligature_items.append(ligature_item)
    
    def _adjust_path_endpoints(self, path: QPainterPath, start_point: QPointF, end_point: QPointF) -> QPainterPath:
        """Adjust a path to properly connect start and end points."""
        if path.elementCount() == 0:
            # Empty path - create simple line
            adjusted = QPainterPath()
            adjusted.moveTo(start_point)
            adjusted.lineTo(end_point)
            return adjusted
        
        # Create new path with adjusted endpoints
        adjusted = QPainterPath()
        adjusted.moveTo(start_point)
        
        # Add intermediate points from original path (skip first and last)
        for i in range(1, path.elementCount() - 1):
            element = path.elementAt(i)
            if element.type == QPainterPath.MoveToElement:
                adjusted.moveTo(element.x, element.y)
            elif element.type == QPainterPath.LineToElement:
                adjusted.lineTo(element.x, element.y)
            elif element.type == QPainterPath.CurveToElement:
                # Handle curve elements (would need next two control points)
                adjusted.lineTo(element.x, element.y)
        
        # End at vertex position
        adjusted.lineTo(end_point)
        return adjusted
    
    def _build_preview_dock(self) -> None:
        """Build the preview dock with EGI/EGIF tabs."""
        self.preview_dock = QDockWidget("Preview", self)
        self.preview_dock.setObjectName("previewDock")
        tabs = QTabWidget(self.preview_dock)
        self.txt_egi = QTextEdit()
        self.txt_egi.setReadOnly(True)
        self.txt_egif = QTextEdit()
        self.txt_egif.setReadOnly(True)
        tabs.addTab(self.txt_egi, "EGI (JSON)")
        tabs.addTab(self.txt_egif, "EGIF")
        self.preview_dock.setWidget(tabs)
        self.addDockWidget(Qt.RightDockWidgetArea, self.preview_dock)
        
        # Click-to-select from JSON: react to cursor changes
        self.txt_egi.cursorPositionChanged.connect(self._on_egi_cursor_moved)
    
    def _build_corpus_dock(self) -> None:
        """Build the corpus guidance dock."""
        self.corpus_dock = QDockWidget("Corpus Guide", self)
        self.corpus_dock.setObjectName("corpusDock")
        corpus_tabs = QTabWidget(self.corpus_dock)
        self.txt_corpus_egi_json = QTextEdit()
        self.txt_corpus_egi_json.setReadOnly(True)
        self.txt_corpus_egif = QTextEdit()
        self.txt_corpus_egif.setReadOnly(True)
        corpus_tabs.addTab(self.txt_corpus_egi_json, "Corpus EGI (JSON)")
        corpus_tabs.addTab(self.txt_corpus_egif, "Corpus EGIF")
        self.corpus_dock.setWidget(corpus_tabs)
        self.addDockWidget(Qt.RightDockWidgetArea, self.corpus_dock)
        
        # Tabify with the preview dock
        try:
            self.tabifyDockWidget(self.preview_dock, self.corpus_dock)
        except Exception:
            pass
    
    def _on_egi_cursor_moved(self) -> None:
        """Handle cursor movement in EGI text for selection."""
        # Placeholder for EGI cursor handling
        pass
    
    def _schedule_preview(self) -> None:
        """Schedule preview update."""
        if hasattr(self, 'act_auto') and self.act_auto.isChecked():
            QTimer.singleShot(60, self._update_preview)
    
    def _update_preview(self) -> None:
        """Update the preview panes with current diagram state."""
        try:
            schema = self._gather_schema_from_scene()
            # Pretty JSON
            self.txt_egi.setPlainText(json.dumps(schema, indent=2))
            # Build EGIF via adapter + generator
            try:
                if drawing_to_relational_graph and generate_egif:
                    rgc = drawing_to_relational_graph(schema)
                    egif = generate_egif(rgc)
                else:
                    egif = "<EGIF generation not available>"
            except Exception as e:
                egif = f"<EGIF generation error>\n{e}"
            self.txt_egif.setPlainText(egif)
        except Exception as e:
            self.txt_egi.setPlainText(f"<Preview error>\n{e}")
            self.txt_egif.setPlainText("")
    
    def _gather_schema_from_scene(self) -> Dict[str, Any]:
        """Gather the current diagram state as a schema."""
        # Convert current model to schema format
        cuts = {}
        for cid, c in self.model.cuts.items():
            br = c.gfx.sceneBoundingRect()
            tl = br.topLeft()
            x, y = float(tl.x()), float(tl.y())
            w, h = float(br.width()), float(br.height())
            cuts[cid] = {"rect": (x, y, w, h), "parent_id": c.parent_id}
        
        vertices = {}
        for vid, v in self.model.vertices.items():
            sp = v.gfx.scenePos()
            vertices[vid] = {"pos": (float(sp.x()), float(sp.y())), "area_id": v.area_id}
        
        predicates = {}
        for pid, p in self.model.predicates.items():
            rb = p.gfx_rect.sceneBoundingRect()
            predicates[pid] = {
                "rect": (float(rb.x()), float(rb.y()), float(rb.width()), float(rb.height())), 
                "area_id": p.area_id
            }
        
        ligatures = {str(e): [str(v) for v in vs] for e, vs in self.model.ligatures.items()}
        
        return {
            "sheet_id": self.model.sheet_id,
            "cuts": cuts,
            "vertices": vertices,
            "predicates": predicates,
            "ligatures": ligatures,
        }
    
    def _on_scene_changed(self, *args) -> None:
        """Handle scene changes and schedule refreshes."""
        # Skip during active drag to avoid repeated heavy work per mouse move
        if hasattr(self, '_interaction_active') and self._interaction_active:
            return
        self._schedule_ligature_refresh()
        self._schedule_zorder_refresh()
    
    def _on_selection_changed(self) -> None:
        """Handle selection changes and apply styles."""
        self._apply_selection_styles()
        
        # Notify practice mode about selection changes
        if hasattr(self, 'practice_mode') and self.practice_mode:
            try:
                selected_items = self.scene.selectedItems()
                selected_ids = []
                for item in selected_items:
                    # Try to get ID from different item types
                    if hasattr(item, 'id'):
                        selected_ids.append(item.id)
                    elif hasattr(item, '_id'):
                        selected_ids.append(item._id)
                
                self.practice_mode.update_selection(selected_ids)
            except Exception as e:
                print(f"Warning: Failed to update practice mode selection: {e}")
    
    def _auto_update_preview(self, *args) -> None:
        """Auto-update preview when scene changes."""
        self._schedule_preview()

    def _check_target_match_and_update_display(self) -> None:
        """Check if current EGIF matches target, provide visual feedback, and auto-enable lock when matched."""
        if not self.puzzle_mode_active or not self._target_egi_meta:
            # Reset to default styling when not in puzzle mode
            self._set_egif_display_style(matched=None)
            return
        
        try:
            # Get target EGIF
            target_egif = ""
            kind = self._target_egi_meta.get("kind")
            if kind == "egif_text":
                target_egif = str(self._target_egi_meta.get("payload", ""))
            elif kind == "egi_inline":
                # Convert inline EGI to EGIF for comparison
                target_inline = self._target_egi_meta.get("payload", {})
                if isinstance(target_inline, dict):
                    try:
                        if drawing_to_relational_graph and generate_egif:
                            target_schema = self._schema_from_egi_inline(target_inline)
                            target_graph = drawing_to_relational_graph(target_schema)
                            target_egif = generate_egif(target_graph) or ""
                    except Exception:
                        self._set_egif_display_style(matched=False)
                        return
            
            # Get current EGIF
            current_schema = self._gather_schema_from_scene()
            current_egif = self._schema_to_egif(current_schema)
            
            # Compare normalized EGIF strings
            def normalize_egif(egif: str) -> str:
                return " ".join(egif.split())  # Normalize whitespace
            
            if normalize_egif(current_egif) == normalize_egif(target_egif):
                # Match found - show green but DON'T auto-lock to allow corrections
                self._set_egif_display_style(matched=True)
                # Show success message but keep unlocked for position corrections
                self.statusBar().showMessage("✓ Target matched! You can now validate & lock, or continue adjusting positions.")
            else:
                # No match - show red
                self._set_egif_display_style(matched=False)
        except Exception:
            self._set_egif_display_style(matched=False)

    def _set_egif_display_style(self, matched: Optional[bool]) -> None:
        """Set the visual style of the current EGIF display based on target match status."""
        if not hasattr(self, 'txt_egi'):
            return
        
        if matched is True:
            # Green for matched
            self.txt_egi.setStyleSheet("QTextEdit { color: green; }")
        elif matched is False:
            # Red for unmatched
            self.txt_egi.setStyleSheet("QTextEdit { color: red; }")
        else:
            # Default styling when not in puzzle mode
            self.txt_egi.setStyleSheet("")

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

    def _is_valid_cut_scene_rect(self, new_rect: QRectF, ignore_item: Optional[QGraphicsItem] = None) -> bool:
        # Use centralized constraint engine for validation
        if constraint_engine is None:
            return True  # Fallback if constraint engine unavailable
        
        # Build DTO with current cuts plus the proposed new rect
        dto = {"cuts": {}}
        
        # Add existing cuts
        for cid, c in self.model.cuts.items():
            if ignore_item is not None and c.gfx is ignore_item:
                continue
            r = c.gfx.rect()
            tl = c.gfx.mapToScene(r.topLeft())
            br = c.gfx.mapToScene(r.bottomRight())
            scene_rect = QRectF(tl, br).normalized()
            dto["cuts"][cid] = {"rect": (scene_rect.x(), scene_rect.y(), scene_rect.width(), scene_rect.height())}
        
        # Add the proposed new rect
        dto["cuts"]["_temp"] = {"rect": (new_rect.x(), new_rect.y(), new_rect.width(), new_rect.height())}
        
        # Validate using constraint engine
        ok, msg, info = constraint_engine.validate_syntax(dto, egi_locked=False)
        return ok

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
        
        # Show selection highlight when selected
        if self.isSelected():
            # Draw selection highlight with thicker blue border
            selection_pen = QPen(QColor(100, 150, 255), 3)
            selection_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(selection_pen)
            painter.setBrush(QBrush(QColor(100, 150, 255, 30)))  # Light blue fill
            painter.drawRoundedRect(r, max_rx, max_ry)
        else:
            # Normal appearance
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
        
        # Handle right-click for cut deletion
        if event.button() == Qt.RightButton:
            from PySide6.QtWidgets import QMenu
            menu = QMenu()
            delete_action = menu.addAction("Delete Cut")
            action = menu.exec_(event.screenPos())
            if action == delete_action:
                # Find the cut ID for this graphics item
                cut_id = None
                for cid, c in self._editor.model.cuts.items():
                    if c.gfx is self:
                        cut_id = cid
                        break
                if cut_id:
                    self._editor._remove_cut(cut_id)
                event.accept()
                return
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
            # Check if editor is available before validation
            if self._editor and not self._editor._is_valid_cut_scene_rect(new_scene_rect, ignore_item=self):
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
                    if self._editor:
                        cid = self._editor._id_for_cut_item(self)
                        self._editor._log(f"CUT_DRAG end id={cid} result=invalid snap_back=1")
                except Exception:
                    pass
                if self._editor:
                    self._editor.statusBar().showMessage("Invalid move: cuts must be nested or disjoint.")
            else:
                self._last_valid_scene_rect = new_scene_rect
                try:
                    if self._editor:
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
            
            # Always validate cut movements to enforce syntactic constraints
            if not self._editor._is_valid_cut_scene_rect(new_scene_rect, ignore_item=self):
                self._editor.statusBar().showMessage("Invalid move: cuts must be nested or disjoint.")
                return self.pos()  # snap back to valid position
            
            # In locked mode, check if cut stays within its parent area
            if self._editor.egi_locked:
                # Find this cut's ID and parent area
                cut_id = None
                for cid, c in self._editor.model.cuts.items():
                    if c.gfx is self:
                        cut_id = cid
                        break
                
                if cut_id:
                    cut_data = self._editor.model.cuts[cut_id]
                    parent_area = cut_data.parent_id or self._editor.model.sheet_id
                    
                    # Check if new position keeps cut within parent area
                    new_area = self._editor._area_id_at_point(new_scene_rect.center())
                    if new_area != parent_area:
                        self._editor.statusBar().showMessage("Practice/Locked: cut cannot change areas.")
                        return self.pos()
            
            self._last_valid_scene_rect = new_scene_rect
        elif change == QGraphicsItem.ItemPositionHasChanged:
            # When cut moves, move its contents and connected ligatures with it
            if self._editor.egi_locked:
                self._move_cut_context_with_cut()
        elif change == QGraphicsItem.ItemSelectedHasChanged:
            # Handle visibility is now managed centrally in _on_selection_changed
            # Only keep handles visible during active resize operations
            if getattr(self, "_resizing", False):
                for h in getattr(self, "_handles", []):
                    try:
                        h.setVisible(True)
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
        elif change == QGraphicsItem.ItemPositionHasChanged and getattr(self, "_editor", None):
            # Update model position and ligatures when vertex position changes
            try:
                # Find vertex in model and update its position
                for vertex_id, vertex in self._editor.model.vertices.items():
                    if vertex.gfx == self:
                        vertex.pos = self.pos()
                        break
                self._editor._schedule_ligature_refresh(force_immediate=True)
            except Exception:
                pass
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
        """Draw a clear selection outline when selected, subtle boundary always visible."""
        try:
            painter.save()
            if self.isSelected():
                # Draw clear selection outline
                painter.setPen(QPen(QColor(0, 120, 255), 2))
                painter.setBrush(QBrush(QColor(0, 120, 255, 30)))
                painter.drawRect(self.rect())
            else:
                # Always show subtle boundary for spatial awareness
                painter.setPen(QPen(QColor(200, 200, 200, 80), 1))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(self.rect())
        finally:
            painter.restore()

    def mousePressEvent(self, event):
        try:
            self._editor.begin_interaction()
        except Exception:
            pass
        
        # Handle right-click for context menu
        if event.button() == Qt.RightButton and self._editor:
            # Find the predicate ID for this graphics item
            predicate_id = None
            for pid, p in self._editor.model.predicates.items():
                if p.gfx_rect is self:
                    predicate_id = pid
                    break
            
            if predicate_id:
                self._show_predicate_context_menu(event.screenPos(), predicate_id)
                event.accept()
                return
        
        self._press_pos = self.scenePos()
        super().mousePressEvent(event)

    def _show_predicate_context_menu(self, screen_pos, predicate_id):
        """Show context menu for predicate with ligature creation and argument ordering options."""
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu()
        
        # Add ligature creation option
        create_ligature_action = menu.addAction("Create Ligature")
        create_ligature_action.triggered.connect(lambda: self._editor._start_ligature_creation(predicate_id))
        
        # Add argument ordering option if predicate has multiple arguments
        connected_vertices = self._editor.model.ligatures.get(predicate_id, [])
        if len(connected_vertices) > 1:
            menu.addSeparator()
            edit_order_action = menu.addAction("Edit Argument Order...")
            edit_order_action.triggered.connect(lambda: self._editor._show_argument_order_dialog(predicate_id))
        
        menu.exec_(screen_pos)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and getattr(self, "_editor", None):
            if self._editor.egi_locked:
                try:
                    return self.pos()  # Prevent movement when locked
                except Exception:
                    pass
        elif change == QGraphicsItem.ItemPositionHasChanged and getattr(self, "_editor", None):
            # Update model position and ligatures when predicate position changes
            try:
                # Find predicate in model and update its position
                for pred_id, pred in self._editor.model.predicates.items():
                    if pred.gfx_rect is self:
                        pred.pos = self.pos()
                        break
                self._editor._schedule_ligature_refresh(force_immediate=True)
            except Exception:
                pass
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if not getattr(self, "_editor", None):
            return
        try:
            self._editor.end_interaction()
        except Exception:
            pass


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
