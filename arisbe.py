#!/usr/bin/env python3
"""
Arisbe - Home for Existential Graph Inquiry

Named after Charles Sanders Peirce's home in northeast New Jersey,
Arisbe serves as the intellectual workspace for Existential Graph inquiry.

Entry point: Integrated doorway interface
Users enter through the home screen and navigate to Organon/Ergasterion/Agon.

Architecture:
- Home: Central doorway interface with component selection
- Organon: Browser for corpus management and graph navigation
- Ergasterion: Workshop for diagram creation and editing
- Agon: Competition arena for logical evaluation and games
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

# Import the new integrated home interface
from arisbe_home import IntegratedArisbeWindow


def main():
    """Main entry point for Arisbe with integrated home interface."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Arisbe")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Arisbe Project")
    
    # Create and show integrated home window
    main_window = IntegratedArisbeWindow()
    main_window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
    
    def _setup_ui(self):
        """Set up main UI with Organon browser as central widget."""
        self._setup_central_widget()
    
    def _setup_central_widget(self):
        """Set up central widget with proper three-panel Organon."""
        # Import and use the existing OrganonMainWindow with three panels
        from organon.main_window import OrganonMainWindow
        self.organon = OrganonMainWindow()
        
        # Connect Organon's handoff signal to our Ergasterion launcher
        self.organon.edit_in_ergasterion.connect(self._handle_organon_ergasterion_handoff)
        
        # Embed Organon as central widget
        self.setCentralWidget(self.organon)
    
    def _connect_organon_signals(self):
        """Connect Organon signals for launching Ergasterion."""
        # In a full implementation, Organon would emit signals for:
        # - New graph creation
        # - Edit existing graph  
        # - Practice with graph
        
        # For now, we'll add methods that Organon can call
        if hasattr(self.organon, 'set_ergasterion_launcher'):
            self.organon.set_ergasterion_launcher(self.launch_ergasterion_with_handoff)
    
    def _setup_menu_bar(self):
        """Set up menu bar with triad navigation."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_graph_action = QAction("New Graph → Ergasterion", self)
        new_graph_action.triggered.connect(self._new_graph_to_ergasterion)
        file_menu.addAction(new_graph_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit Arisbe", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Workshop menu
        workshop_menu = menubar.addMenu("Workshop")
        
        ergasterion_action = QAction("Launch Ergasterion", self)
        ergasterion_action.triggered.connect(self._launch_ergasterion_standalone)
        workshop_menu.addAction(ergasterion_action)
        
        workshop_menu.addSeparator()
        
        agon_action = QAction("Launch Agon (Stub)", self)
        agon_action.triggered.connect(self._show_agon_stub)
        agon_action.setEnabled(False)
        workshop_menu.addAction(agon_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About Arisbe", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Set up toolbar with quick actions."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Quick actions for common workflows
        new_graph_action = QAction("New Graph", self)
        new_graph_action.triggered.connect(self._new_graph_to_ergasterion)
        toolbar.addAction(new_graph_action)
        
        toolbar.addSeparator()
        
        ergasterion_action = QAction("Ergasterion", self)
        ergasterion_action.triggered.connect(self._launch_ergasterion_standalone)
        toolbar.addAction(ergasterion_action)
        
        # Future: Agon action when implemented
    
    def _setup_status_bar(self):
        """Set up status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Arisbe ready - Organon browser active")
    
    def _setup_communication_dock(self):
        """Set up dock for component communication logging."""
        comm_dock = QDockWidget("Activity Log", self)
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(150)
        comm_dock.setWidget(self.activity_log)
        self.addDockWidget(Qt.BottomDockWidgetArea, comm_dock)
        
        self._log_activity("Arisbe initialized - Organon browser ready for corpus browsing")
    
    # --- Ergasterion Integration ---
    
    def launch_ergasterion_with_handoff(self, package: GraphHandoffPackage) -> bool:
        """Launch Ergasterion with handoff package from Organon."""
        try:
            # Create new Ergasterion instance
            ergasterion = RefactoredDrawingEditor()
            success = ergasterion.launch_with_handoff(package)
            
            if not success:
                QMessageBox.warning(self, "Handoff Error", 
                                  f"Failed to initialize Ergasterion with {package.graph_id}")
                return False
            
            # Show Ergasterion window
            ergasterion.show()
            self.ergasterion_instances.append(ergasterion)
            
            # Log the handoff
            workflow_names = {
                GraphHandoffType.BRAND_NEW: "New Graph Creation",
                GraphHandoffType.EGI_ONLY: "Diagram Matching", 
                GraphHandoffType.EGI_PLUS_EGDF: "Practice/Adjustment"
            }
            
            workflow_name = workflow_names.get(package.handoff_type, "Unknown")
            self._log_activity(f"Ergasterion launched: {workflow_name} - {package.graph_id}")
            self.status_bar.showMessage(f"Ergasterion active - {package.graph_id}")
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to launch Ergasterion: {e}")
            return False
    
    def _launch_ergasterion_standalone(self):
        """Launch Ergasterion in standalone mode."""
        try:
            ergasterion = RefactoredDrawingEditor()
            ergasterion.show()
            self.ergasterion_instances.append(ergasterion)
            
            self._log_activity("Ergasterion launched (standalone mode)")
            self.status_bar.showMessage("Ergasterion active (standalone)")
            
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to launch Ergasterion: {e}")
    
    def _handle_organon_ergasterion_handoff(self, payload: dict):
        """Handle handoff from Organon to Ergasterion."""
        try:
            # Convert Organon payload to GraphHandoffPackage
            from organon_ergasterion_protocol import GraphHandoffPackage, GraphHandoffType
            
            # Determine handoff type based on payload content
            has_egi = bool(payload.get("egi"))
            has_egdf = bool(payload.get("egdf"))
            
            if has_egi and has_egdf:
                handoff_type = GraphHandoffType.EGI_PLUS_EGDF
            elif has_egi:
                handoff_type = GraphHandoffType.EGI_ONLY
            else:
                handoff_type = GraphHandoffType.BRAND_NEW
            
            # Extract graph ID from source path
            source_path = payload.get("source_path", "")
            graph_id = Path(source_path).name if source_path else "unknown"
            
            # Convert EGI dict to RelationalGraphWithCuts if present
            egi_object = None
            egi_data = payload.get("egi")
            if egi_data:
                try:
                    from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, AlphabetDAU
                    from frozendict import frozendict
                    
                    # Build graph from inline dict
                    sheet = egi_data.get("sheet", "sheet")
                    V = []
                    rho_map = egi_data.get("rho", {})
                    
                    # Handle V as list of objects or strings
                    for v_obj in egi_data.get("V", []):
                        if isinstance(v_obj, dict):
                            vid = v_obj.get("id")
                            label = v_obj.get("label") or rho_map.get(vid)
                            is_generic = v_obj.get("is_generic", True if label is None else False)
                        else:
                            vid = v_obj
                            label = rho_map.get(vid)
                            is_generic = True if label is None else False
                        V.append(Vertex(id=vid, label=label, is_generic=is_generic))
                    
                    # Handle E as list of objects or strings
                    E = []
                    for e_obj in egi_data.get("E", []):
                        if isinstance(e_obj, dict):
                            E.append(Edge(id=e_obj.get("id")))
                        else:
                            E.append(Edge(id=e_obj))
                    
                    # Handle Cut as list of objects or strings
                    CutSet = []
                    for c_obj in egi_data.get("Cut", []):
                        if isinstance(c_obj, dict):
                            CutSet.append(Cut(id=c_obj.get("id")))
                        else:
                            CutSet.append(Cut(id=c_obj))
                    
                    nu = frozendict({k: tuple(v) for k, v in (egi_data.get("nu") or {}).items()})
                    rel = frozendict(dict(egi_data.get("rel") or {}))
                    area = frozendict({k: frozenset(v) for k, v in (egi_data.get("area") or {}).items()})
                    rho = frozendict(dict(rho_map))
                    
                    alph_data = egi_data.get("alphabet") or {}
                    alph = AlphabetDAU(
                        C=frozenset(alph_data.get("C") or []),
                        F=frozenset(alph_data.get("F") or []),
                        R=frozenset(alph_data.get("R") or []),
                        ar=frozendict(alph_data.get("ar") or {}),
                    ).with_defaults()
                    
                    egi_object = RelationalGraphWithCuts(
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
                    
                except Exception as e:
                    self._log_activity(f"Warning: Failed to convert EGI data: {e}")
                    egi_object = None
            
            # Create proper handoff package
            package = GraphHandoffPackage(
                handoff_type=handoff_type,
                graph_id=graph_id,
                metadata={"source_path": source_path, "style_id": payload.get("style_id", "default")},
                egi=egi_object,
                egdf=payload.get("egdf")
            )
            
            # Create Ergasterion instance and launch with handoff
            ergasterion = RefactoredDrawingEditor()
            success = ergasterion.launch_with_handoff(package)
            
            if not success:
                QMessageBox.warning(self, "Handoff Error", 
                                  "Failed to initialize Ergasterion with graph data")
                return
            
            # Show Ergasterion window
            ergasterion.show()
            self.ergasterion_instances.append(ergasterion)
            
            # Log the handoff
            self._log_activity(f"Ergasterion launched: {handoff_type.value} - {graph_id}")
            self.status_bar.showMessage(f"Ergasterion active - {graph_id}")
            
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to launch Ergasterion: {e}")
            import traceback
            traceback.print_exc()
    
    def _new_graph_to_ergasterion(self):
        """Create new graph and launch Ergasterion."""
        package = OrganonErgasterionBridge.create_handoff_package("new_graph")
        
        self.launch_ergasterion_with_handoff(package)
    
    # --- Organon Integration Points ---
    
    def handle_organon_graph_request(self, graph_data: Dict[str, Any], action: str):
        """Handle graph requests from Organon."""
        graph_id = graph_data.get("id", "unknown")
        
        if action == "create_new":
            # Case 1: Brand new graph
            package = OrganonErgasterionBridge.create_handoff_package(
                graph_id=graph_id,
                metadata=graph_data.get("metadata", {})
            )
            
        elif action == "draw_diagram":
            # Case 2: EGI exists, need diagram
            egi = graph_data.get("egi")
            package = OrganonErgasterionBridge.create_handoff_package(
                graph_id=graph_id,
                metadata=graph_data.get("metadata", {}),
                egi=egi
            )
            
        elif action == "edit_diagram":
            # Case 3: Both EGI and EGDF exist
            egi = graph_data.get("egi")
            egdf = graph_data.get("egdf")
            package = OrganonErgasterionBridge.create_handoff_package(
                graph_id=graph_id,
                metadata=graph_data.get("metadata", {}),
                egi=egi,
                egdf=egdf
            )
            
        else:
            self._log_activity(f"Unknown action from Organon: {action}")
            return
        
        self.launch_ergasterion_with_handoff(package)
    
    def receive_ergasterion_return(self, return_package):
        """Receive completed work back from Ergasterion with dual routing."""
        destination = return_package.return_destination
        
        if destination in ["organon", "both"]:
            # Forward to Organon for storage
            if hasattr(self.organon, 'receive_graph_return'):
                self.organon.receive_graph_return(return_package)
            self._log_activity(f"Graph returned to Organon: {return_package.graph_id}")
        
        if destination in ["agon", "both"]:
            # Forward to Agon as new proposal for Endoporeutic Game
            self._send_proposal_to_agon(return_package)
            self._log_activity(f"Graph sent to Agon as proposal: {return_package.graph_id}")
    
    def _send_proposal_to_agon(self, return_package):
        """Send completed diagram to Agon as new proposal for evaluation."""
        # Agon stub - just log the action
        self._log_activity(f"Agon stub: Would process proposal {return_package.graph_id}")
    
    # --- UI Actions ---
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """
        <h2>Arisbe</h2>
        <p><b>Home for Existential Graph Inquiry</b></p>
        
        <p>Named after Charles Sanders Peirce's home in northeast New Jersey, 
        Arisbe serves as your intellectual workspace for Existential Graph inquiry.</p>
        
        <p>Arisbe provides integrated access to three specialized components:</p>
        
        <ul>
        <li><b>Organon</b>: Browser for corpus navigation and graph management</li>
        <li><b>Ergasterion</b>: Workshop for diagram creation and editing</li>
        <li><b>Agon</b>: Competition arena for logical evaluation and games</li>
        </ul>
        
        <p>Enter through Organon browser to explore your knowledge corpus, then launch Ergasterion workshop for diagram work.</p>
        """
        
        QMessageBox.about(self, "About Arisbe", about_text)
    
    def _show_agon_stub(self):
        """Show Agon stub message."""
        self._log_activity("Agon stub: Menu item clicked")
    
    def _log_activity(self, message: str):
        """Log activity to the communication dock."""
        current_text = self.activity_log.toPlainText()
        new_text = f"{current_text}\n• {message}" if current_text else f"• {message}"
        self.activity_log.setPlainText(new_text)
        
        # Auto-scroll to bottom
        cursor = self.activity_log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.activity_log.setTextCursor(cursor)


def main():
    """Main entry point for Arisbe."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Arisbe")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Arisbe Project")
    
    # Create and show main window
    main_window = ArisbeMainWindow()
    main_window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
