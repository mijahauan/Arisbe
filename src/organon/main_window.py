from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDockWidget, QMessageBox, QToolBar, QGraphicsItem, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem
)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor

from egi_core_dau import (
    RelationalGraphWithCuts, Vertex, Edge, Cut, AlphabetDAU
)
from egi_system import create_egi_system
from egdf_parser import EGDFDocument
import corpus_index as cidx

from .corpus_panel import CorpusPanel
from .info_panel import InfoPanel
from .linear_forms_panel import LinearFormsPanel
from .diagram_viewer import DiagramViewer

# Prefer the working renderer from tools/drawing_editor in embedded mode
try:
    # Ensure tools/ is on sys.path for DrawingEditor import
    import sys
    import os
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    tools_dir = os.path.join(repo_root, "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    
    from drawing_editor import DrawingEditor
except Exception:
    DrawingEditor = None  # type: ignore


@dataclass
class Current:
    graph_dir: Optional[Path] = None
    graph: Optional[RelationalGraphWithCuts] = None
    latest_egdf_path: Optional[Path] = None


class OrganonMainWindow(QMainWindow):
    """
    Clean Organon implementation meeting the spec:
    1) Corpus panel for search/select/new
    2) Read-only diagram preview from EGDF (if present); otherwise offer handoff
    3) Editable graph metadata (id/title/category/tags)
    4) Generated linear forms (EGIF/CGIF/CLIF) from the EGI source of truth
    """

    # Handoff signal: emit Ergasterion payload
    edit_in_ergasterion = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Arisbe – Organon")
        self.resize(1200, 800)

        # EGI system for conversions (kept for linear forms generation)
        self._egi_system = create_egi_system()

        self._cur = Current()

        # Central wrapper
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Viewer header (status + handoff)
        header = QHBoxLayout()
        self.lbl_status = QLabel("No graph loaded")
        header.addWidget(self.lbl_status)
        header.addStretch(1)
        self.btn_open_erg = QPushButton("Open in Ergasterion")
        self.btn_open_erg.clicked.connect(self._on_open_in_ergasterion)
        header.addWidget(self.btn_open_erg)
        root.addLayout(header)

        # Create diagram viewer using same rendering as Ergasterion
        self.diagram_viewer = DiagramViewer()
        root.addWidget(self.diagram_viewer, 1)

        # Docks
        self._init_corpus_dock()
        self._init_info_dock()
        self._init_linear_forms_dock()

        # Load corpus on startup but without heavy processing
        self._corpus_loaded = False
        self._refresh_corpus()
        self._update_handoff_visibility()

    # --- Docks ---
    def _init_corpus_dock(self) -> None:
        self.corpus_dock = QDockWidget("Corpus", self)
        self.corpus_panel = CorpusPanel(self)
        self.corpus_panel.entry_selected.connect(self._on_entry_selected)
        self.corpus_panel.refresh_requested.connect(self._refresh_corpus)
        self.corpus_panel.new_requested.connect(self._on_new_graph)
        self.corpus_dock.setWidget(self.corpus_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.corpus_dock)
        try:
            self.resizeDocks([self.corpus_dock], [280], Qt.Horizontal)
        except Exception:
            pass

    def _init_info_dock(self) -> None:
        self.info_dock = QDockWidget("Graph Info", self)
        self.info_panel = InfoPanel(self)
        self.info_panel.saved.connect(lambda _info: self._refresh_corpus())
        self.info_dock.setWidget(self.info_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.info_dock)

    def _init_linear_forms_dock(self) -> None:
        self.forms_dock = QDockWidget("Linear Forms", self)
        self.forms_panel = LinearFormsPanel(self)
        self.forms_dock.setWidget(self.forms_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.forms_dock)

    # --- Corpus operations ---
    def _refresh_corpus(self) -> None:
        """Refresh corpus display."""
        self.corpus_panel.refresh_corpus()

    def refresh_current_graph(self) -> None:
        """Refresh the current graph display after external changes."""
        if self._cur.graph_dir:
            # Reload the current graph directory to pick up new files
            self._load_graph_dir(self._cur.graph_dir)
            self._refresh_corpus()

    def _on_new_graph(self) -> None:
        """Create new graph and launch Ergasterion for de novo diagram creation."""
        from PySide6.QtWidgets import QInputDialog
        
        # Get graph title from user
        title, ok = QInputDialog.getText(
            self, 
            "New Graph", 
            "Enter a title for the new graph:",
            text="New Existential Graph"
        )
        
        if not ok or not title.strip():
            return
            
        # Create unique graph ID from title
        import re
        base_id = re.sub(r'[^a-zA-Z0-9_]', '_', title.strip().lower())
        base_id = re.sub(r'_+', '_', base_id).strip('_')
        if not base_id:
            base_id = "new_graph"
            
        # Find unique ID
        i = 1
        while True:
            gid = f"{base_id}_{i}" if i > 1 else base_id
            gdir = cidx.REPO_ROOT / "corpus" / "graphs" / gid
            if not gdir.exists():
                break
            i += 1
        
        try:
            # Create graph directory structure
            gdir.mkdir(parents=True, exist_ok=True)
            (gdir / "EGDF").mkdir(exist_ok=True)
            (gdir / "EXPORTS").mkdir(exist_ok=True)
            
            # Create initial metadata file
            import json
            from datetime import datetime
            
            metadata = {
                "id": gid,
                "title": title.strip(),
                "category": None,
                "tags": [],
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "status": "draft",
                "links": {
                    "egi": f"{gid}.egi.json",
                    "egdf_dir": "EGDF/",
                    "exports_dir": "EXPORTS/"
                },
                "linear_forms": {}
            }
            
            metadata_path = gdir / f"{gid}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update corpus index
            relative_path = f"corpus/graphs/{gid}"
            self.corpus_panel.add_graph_to_index(gid, title.strip(), relative_path)
            
            # Update current state
            self._cur.graph_dir = gdir
            self._cur.graph = None  # No EGI yet
            self._cur.latest_egdf_path = None
            
            # Refresh corpus and UI
            self._refresh_corpus()
            
            # Automatically launch Ergasterion for diagram creation
            self._on_open_in_ergasterion()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create new graph: {e}")

    def _on_entry_selected(self, entry: Dict[str, Any]) -> None:
        rel = entry.get("path")
        gdir = (cidx.REPO_ROOT / rel) if rel else None
        if not gdir or not gdir.exists():
            try:
                QMessageBox.warning(self, "Corpus", "Selected entry directory missing.")
            except Exception:
                pass
            return
        self._load_graph_dir(gdir)

    # --- Loading ---
    def _load_graph_dir(self, gdir: Path) -> None:
        """Load graph directory with EGI-first logic."""
        self._cur = Current(graph_dir=gdir, graph=None, latest_egdf_path=None)
        
        # EGI-first loading: check for <graph>.egi.json
        egi_path = cidx.graph_paths(gdir)["egi"]
        egi_exists = egi_path.exists() and egi_path.stat().st_size > 0
        
        if egi_exists:
            # EGI exists: load it and derive linear forms
            self._cur.graph = self._read_egi_json(gdir)
            if self._cur.graph is not None:
                self.forms_panel.set_graph(self._cur.graph)  # Switch to display mode
            else:
                self.forms_panel.clear()  # Switch to input mode on load failure
        else:
            # No EGI: prepare for creation via linear form input or Ergasterion
            self._cur.graph = None
            self.forms_panel.clear()  # Switch to input mode
        
        # Load info panel (will detect EGI state and set read-only accordingly)
        self.info_panel.load_graph_dir(gdir)
        
        # Load diagram if EGDF exists
        latest = self._find_latest_egdf(gdir)
        self._cur.latest_egdf_path = latest
        
        if latest and latest.exists():
            # Load and display the diagram using proper DiagramViewer
            try:
                self.diagram_viewer.load_egdf_path(latest)
            except Exception as e:
                print(f"Warning: Failed to load EGDF: {e}")
                # If loading fails, clear the viewer
                self.diagram_viewer.clear()
        else:
            # No EGDF exists - clear the viewer (empty state)
            self.diagram_viewer.clear()
        
        # Update status & handoff visibility
        self._update_status()
        self._update_handoff_visibility()

    def _update_status(self) -> None:
        if not self._cur.graph_dir:
            self.lbl_status.setText("No graph loaded")
            return
        has_egdf = bool(self._cur.latest_egdf_path)
        self.lbl_status.setText(
            f"{self._cur.graph_dir.name}  |  EGDF: {'yes' if has_egdf else 'no'}"
        )

    def _update_handoff_visibility(self) -> None:
        # Always allow Ergasterion access when a graph is loaded (for creation or editing)
        self.btn_open_erg.setEnabled(self._cur.graph_dir is not None)


    # --- Helpers ---
    def _read_egi_json(self, gdir: Path) -> Optional[RelationalGraphWithCuts]:
        try:
            egi_path = cidx.graph_paths(gdir)["egi"]
            data = None
            if egi_path.exists():
                import json
                data = json.loads(egi_path.read_text(encoding="utf-8"))
            if not data:
                return None
            # Build graph from inline dict
            sheet: str = data.get("sheet") or "sheet"
            V = []
            rho_map = data.get("rho") or {}
            
            # Handle V as list of objects with id, label, is_generic
            for v_obj in data.get("V", []):
                if isinstance(v_obj, dict):
                    vid = v_obj.get("id")
                    label = v_obj.get("label") or rho_map.get(vid)
                    is_generic = v_obj.get("is_generic", True if label is None else False)
                else:
                    vid = v_obj
                    label = rho_map.get(vid)
                    is_generic = True if label is None else False
                V.append(Vertex(id=vid, label=label, is_generic=is_generic))
            
            # Handle E as list of objects with id
            E = []
            for e_obj in data.get("E", []):
                if isinstance(e_obj, dict):
                    E.append(Edge(id=e_obj.get("id")))
                else:
                    E.append(Edge(id=e_obj))
            
            # Handle Cut as list of objects with id
            CutSet = []
            for c_obj in data.get("Cut", []):
                if isinstance(c_obj, dict):
                    CutSet.append(Cut(id=c_obj.get("id")))
                else:
                    CutSet.append(Cut(id=c_obj))
            from frozendict import frozendict
            nu = frozendict({k: tuple(v) for k, v in (data.get("nu") or {}).items()})
            rel = frozendict(dict(data.get("rel") or {}))
            area = frozendict({k: frozenset(v) for k, v in (data.get("area") or {}).items()})
            rho = frozendict(dict(rho_map))
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
            return graph
        except Exception:
            return None

    def _find_latest_egdf(self, gdir: Path) -> Optional[Path]:
        """Find EGDF to display. Shows selection dialog if multiple exist."""
        egdf_dir = cidx.graph_paths(gdir)["egdf_dir"]
        if not egdf_dir.exists():
            return None
        try:
            candidates: List[Path] = [p for p in egdf_dir.iterdir() if p.name.lower().endswith(".json")]
        except Exception:
            candidates = []
        if not candidates:
            return None
        
        # If only one EGDF, return it
        if len(candidates) == 1:
            return candidates[0]
        
        # Multiple EGDFs - show selection dialog
        return self._select_egdf_dialog(candidates)
    
    def _select_egdf_dialog(self, candidates: List[Path]) -> Optional[Path]:
        """Show dialog to select which EGDF to display when multiple exist."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Diagram")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Multiple diagrams found. Select one to display:"))
        
        # List of EGDF files with readable names
        list_widget = QListWidget()
        for path in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
            # Extract style info from filename if available
            name = path.stem
            if '@' in name:
                # Format: style@author@version
                parts = name.split('@')
                display_name = f"{parts[0]} (by {parts[1]}, v{parts[2]})" if len(parts) >= 3 else name
            else:
                display_name = name
            
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, path)
            list_widget.addItem(item)
        
        # Select first item by default
        if list_widget.count() > 0:
            list_widget.setCurrentRow(0)
        
        layout.addWidget(list_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("Select")
        cancel_btn = QPushButton("Cancel")
        
        def on_ok():
            dialog.accept()
        
        def on_cancel():
            dialog.reject()
        
        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(on_cancel)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Show dialog and return selection
        if dialog.exec() == QDialog.Accepted:
            current_item = list_widget.currentItem()
            if current_item:
                return current_item.data(Qt.UserRole)
        
        return None

    # --- Handoff ---
    def _on_open_in_ergasterion(self) -> None:
        if not self._cur.graph_dir:
            try:
                QMessageBox.information(self, "Ergasterion", "No graph loaded.")
            except Exception:
                pass
            return
        payload = self._build_ergasterion_payload()
        self.edit_in_ergasterion.emit(payload)

    def _build_ergasterion_payload(self) -> Dict[str, Any]:
        style_id = "default"
        egdf_doc = None
        inline: Dict[str, Any] = {}
        
        print(f"[Organon] Building payload - graph_dir: {self._cur.graph_dir}, graph: {self._cur.graph is not None}")
        
        # Load EGDF first to check for inline EGI
        if self._cur.latest_egdf_path and self._cur.latest_egdf_path.exists():
            try:
                egdf_content = self._cur.latest_egdf_path.read_text(encoding="utf-8")
                egdf_doc = EGDFDocument.from_json(egdf_content).to_dict()
                
                # Use EGDF's inline EGI if available (ensures ID consistency)
                egdf_inline = egdf_doc.get("egi_ref", {}).get("inline")
                if egdf_inline:
                    inline = egdf_inline
                    print(f"[Organon] Using EGDF inline EGI for ID consistency")
                else:
                    print(f"[Organon] EGDF missing inline EGI, falling back to graph EGI")
                    
                print(f"[Organon] Successfully loaded EGDF from {self._cur.latest_egdf_path}")
            except Exception as e:
                print(f"[Organon] Failed to load EGDF from {self._cur.latest_egdf_path}: {e}")
                egdf_doc = None
        else:
            print(f"[Organon] No EGDF path found: latest_egdf_path={self._cur.latest_egdf_path}")
        
        # Fallback: compose inline EGI dict from current graph if no EGDF inline
        if not inline and self._cur.graph:
            g = self._cur.graph
            inline = {
                "sheet": g.sheet,
                "V": [{"id": v.id, "label": v.label, "is_generic": v.is_generic} for v in g.V],
                "E": [{"id": e.id} for e in g.E],
                "Cut": [{"id": c.id} for c in g.Cut],
                "nu": {eid: list(g.nu.get(eid, ())) for eid in (e.id for e in g.E)},
                "rel": dict(g.rel),
                "area": {k: list(v) for k, v in g.area.items()},
                "alphabet": {
                    "C": list(g.alphabet.C),
                    "F": list(g.alphabet.F),
                    "R": list(g.alphabet.R),
                    "ar": dict(g.alphabet.ar),
                },
                "rho": dict(g.rho),
            }
            print(f"[Organon] Using graph EGI as fallback")
        else:
            print(f"[Organon] No EGI data available - inline: {bool(inline)}, graph: {self._cur.graph is not None}")
        
        payload = {
            "source_path": str(self._cur.graph_dir) if self._cur.graph_dir else "",
            "graph_dir": str(self._cur.graph_dir) if self._cur.graph_dir else "",
            "egi": inline,
            "egdf": egdf_doc,
            "style_id": style_id,
        }
        print(f"[Organon] Payload created with {len(inline)} EGI entries, EGDF: {egdf_doc is not None}")
        return payload

    def _on_egi_created(self, egi: RelationalGraphWithCuts) -> None:
        """Handle new EGI created from linear form input."""
        if not self._cur.graph_dir:
            return
        
        try:
            # Save EGI to <graph_id>.egi.json
            egi_path = cidx.graph_paths(self._cur.graph_dir)["egi"]
            egi_data = self._egi_to_json_dict(egi)
            import json
            egi_path.write_text(json.dumps(egi_data, indent=2), encoding="utf-8")
            
            # Update current state
            self._cur.graph = egi
            
            # Update metadata with generated linear forms
            try:
                from egif_generator_dau import generate_egif
                from cgif_generator_dau import generate_cgif
                from clif_generator_dau import generate_clif
                
                linear_forms = {
                    "egif": {"content": generate_egif(egi), "source": "generated"},
                    "cgif": {"content": generate_cgif(egi), "source": "generated"},
                    "clif": {"content": generate_clif(egi), "source": "generated"},
                }
                
                # Update graph metadata
                info = cidx.read_info(self._cur.graph_dir)
                info["linear_forms"] = linear_forms
                cidx.write_info(self._cur.graph_dir, info)
                
            except Exception:
                pass  # Continue even if linear form generation fails
            
            # Refresh all panels
            self.info_panel.load_graph_dir(self._cur.graph_dir)
            self.forms_panel.set_graph(egi)
            self._refresh_corpus()
            
            # Update status
            self._update_status()
            
        except Exception as e:
            try:
                QMessageBox.critical(self, "Save Error", f"Failed to save EGI: {e}")
            except Exception:
                pass

    def _egi_to_json_dict(self, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Convert EGI to JSON-serializable dict for <graph_id>.egi.json."""
        return {
            "sheet": egi.sheet,
            "V": [v.id for v in egi.V],
            "E": [e.id for e in egi.E],
            "Cut": [c.id for c in egi.Cut],
            "nu": {eid: list(egi.nu.get(eid, ())) for eid in (e.id for e in egi.E)},
            "rel": dict(egi.rel),
            "area": {k: list(v) for k, v in egi.area.items()},
            "alphabet": {
                "C": list(egi.alphabet.C),
                "F": list(egi.alphabet.F),
                "R": list(egi.alphabet.R),
                "ar": dict(egi.alphabet.ar),
            },
            "rho": dict(egi.rho),
        }

    def process_egi_from_ergasterion(self, payload: dict) -> None:
        """Handle diagram from Ergasterion - add EGDF replica to existing graph or create new."""
        try:
            egdf_content = payload.get("egdf", {})
            if not egdf_content:
                QMessageBox.warning(self, "Import Error", "No EGDF content in Ergasterion payload.")
                return
            
            if self._cur.graph_dir:
                # Existing graph: add EGDF replica without modifying EGI
                self._add_egdf_replica(egdf_content)
            else:
                # New graph: create from EGIF
                egif_content = payload.get("egif", "")
                if not egif_content:
                    QMessageBox.warning(self, "Import Error", "No EGIF content for new graph.")
                    return
                
                from egif_parser_dau import EGIFParser
                parser = EGIFParser(egif_content)
                egi = parser.parse()
                
                # Create new graph directory
                import time
                graph_id = f"ergasterion_graph_{int(time.time())}"
                graph_dir = cidx.CORPUS_GRAPHS_DIR / graph_id
                graph_dir.mkdir(exist_ok=True)
                self._cur.graph_dir = graph_dir
                
                # Create initial metadata
                info = {
                    "id": graph_id,
                    "title": f"Graph from Ergasterion",
                    "category": "ergasterion",
                    "tags": ["created-in-ergasterion"],
                    "status": "draft",
                }
                cidx.write_info(graph_dir, info)
                
                # Save EGDF for new graph
                try:
                    import json
                    egdf_path = cidx.graph_paths(self._cur.graph_dir)["egdf"]
                    egdf_path.write_text(json.dumps(egdf_content, indent=2), encoding="utf-8")
                except Exception as e:
                    print(f"Warning: Failed to save EGDF: {e}")
                
                # Process as if created via linear form input
                self._on_egi_created(egi)
                
                # Refresh the viewer to show the new diagram
                self._load_graph_dir(self._cur.graph_dir)
        
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to process diagram from Ergasterion: {e}")
            import traceback
            traceback.print_exc()

    def _add_egdf_replica(self, egdf_content: dict) -> None:
        """Add EGDF diagram replica to existing graph without modifying EGI."""
        try:
            import json
            from datetime import datetime
            
            # Ensure EGDF subdirectory exists
            egdf_dir = self._cur.graph_dir / "EGDF"
            egdf_dir.mkdir(exist_ok=True)
            
            # Generate unique EGDF filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            egdf_filename = f"diagram_{timestamp}.egdf.json"
            egdf_path = egdf_dir / egdf_filename
            
            # Save EGDF file in proper subdirectory
            with open(egdf_path, 'w', encoding='utf-8') as f:
                json.dump(egdf_content, f, indent=2)
            
            # Refresh the diagram viewer to show new EGDF
            self._load_graph_dir(self._cur.graph_dir)
            
            QMessageBox.information(
                self, 
                "Diagram Added", 
                f"Diagram replica saved as EGDF/{egdf_filename}\nExisting EGI preserved."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save diagram replica: {e}")
