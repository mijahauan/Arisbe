#!/usr/bin/env python3
"""
Arisbe Existential Graph Works - Clean Implementation

A from-scratch GUI implementation that integrates:
1. Clean EGDF canvas renderer (no more black ovals!)
2. Corpus browser for educational examples
3. Working canonical EGDF pipeline
4. Proper Dau-compliant rendering

This replaces the problematic existing GUI with a clean, working implementation.
"""

import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QTabWidget, QTextEdit, QPushButton, QLabel, QListWidget, 
    QListWidgetItem, QSplitter, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QFont, QAction

# Import our clean components
from canonical import get_canonical_pipeline
from egdf_canvas_renderer import EGDFCanvasRenderer
from eg_graphics_scene_renderer import EGGraphicsSceneRenderer  # NEW: Qt Graphics Framework
from corpus_browser import CorpusBrowser
from egdf_dau_canonical import create_dau_compliant_egdf_generator
from graphviz_layout_engine_v2 import GraphvizLayoutEngine


class GraphPreparationArea(QWidget):
    """
    Graph Preparation area with Composition and Practice modes.
    
    Composition Mode: Free graph composition with syntactic constraints only
    Practice Mode: Locked EGI model with semantic constraints enforced
    """
    
    def __init__(self, pipeline):
        super().__init__()
        self.pipeline = pipeline
        self.current_mode = "composition"  # Start in composition mode
        
        self._setup_ui()
        print("📝 Graph Preparation area initialized")
    
    def _setup_ui(self):
        """Setup Graph Preparation UI with Composition/Practice sub-tabs."""
        layout = QVBoxLayout(self)
        
        # Sub-tabs for Composition/Practice modes
        self.mode_tabs = QTabWidget()
        self.mode_tabs.setTabPosition(QTabWidget.North)
        self.mode_tabs.currentChanged.connect(self._on_mode_changed)
        
        # Composition mode tab
        self.composition_widget = CompositionModeWidget(self.pipeline)
        self.mode_tabs.addTab(self.composition_widget, "🎨 Composition")
        
        # Practice mode tab
        self.practice_widget = PracticeModeWidget(self.pipeline)
        self.mode_tabs.addTab(self.practice_widget, "🎯 Practice")
        
        layout.addWidget(self.mode_tabs)
    
    def _on_mode_changed(self, index):
        """Handle mode changes between Composition and Practice."""
        modes = ["composition", "practice"]
        if 0 <= index < len(modes):
            old_mode = self.current_mode
            self.current_mode = modes[index]
            
            print(f"🔄 Mode switch: {old_mode} → {self.current_mode}")
            
            if self.current_mode == "practice":
                print("🔒 Semantic constraints ENABLED")
                self._enable_semantic_constraints()
            else:
                print("🔓 Semantic constraints DISABLED")
                self._disable_semantic_constraints()
    
    def _enable_semantic_constraints(self):
        """Enable semantic constraints for Practice mode."""
        # TODO: Implement semantic constraint enforcement
        # This will lock the diagram to a specific EGI model
        self.practice_widget.enable_semantic_mode()
    
    def _disable_semantic_constraints(self):
        """Disable semantic constraints for Composition mode."""
        # TODO: Implement free composition mode
        # This allows free graph composition with syntactic constraints only
        self.composition_widget.enable_composition_mode()
    
    def load_egif_from_browser(self, egif_content, example_name):
        """Load EGIF content from Browser into both Composition and Practice modes."""
        print(f"📝 Loading '{example_name}' into Preparation area")
        
        # Load into both mode widgets
        self.composition_widget.load_egif(egif_content, example_name)
        self.practice_widget.load_egif(egif_content, example_name)
        
        print(f"✅ '{example_name}' loaded into both Composition and Practice modes")


class CompositionModeWidget(QWidget):
    """
    Composition mode: Free graph composition with syntactic constraints only.
    Users can add/move elements freely to compose new graphs.
    """
    
    def __init__(self, pipeline):
        super().__init__()
        self.pipeline = pipeline
        self.semantic_constraints_enabled = False  # Always off in composition
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup Composition mode UI."""
        layout = QVBoxLayout(self)
        
        # Mode indicator
        mode_label = QLabel("🎨 Composition Mode - Free graph composition (syntactic constraints only)")
        mode_label.setStyleSheet("font-weight: bold; color: #2E8B57; padding: 8px; background: #F0FFF0; border-radius: 4px;")
        layout.addWidget(mode_label)
        
        # Use the existing CleanBullpenApp functionality
        self.bullpen_content = CleanBullpenApp(self.pipeline)
        layout.addWidget(self.bullpen_content)
    
    def enable_composition_mode(self):
        """Enable composition mode with syntactic constraints only."""
        print("🎨 Composition mode: Syntactic constraints only")
        # TODO: Configure canvas for free composition
    
    def load_egif(self, egif_content, example_name):
        """Load EGIF content into Composition mode."""
        print(f"🎨 Loading '{example_name}' into Composition mode")
        self.bullpen_content.load_egif_content(egif_content, example_name)


class PracticeModeWidget(QWidget):
    """
    Practice mode: Locked EGI model with semantic constraints enforced.
    Modifications must preserve meaning and follow transformation rules.
    """
    
    def __init__(self, pipeline):
        super().__init__()
        self.pipeline = pipeline
        self.semantic_constraints_enabled = True  # Always on in practice
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup Practice mode UI."""
        layout = QVBoxLayout(self)
        
        # Mode indicator
        mode_label = QLabel("🎯 Practice Mode - Locked EGI model (semantic constraints enforced)")
        mode_label.setStyleSheet("font-weight: bold; color: #8B0000; padding: 8px; background: #FFF0F0; border-radius: 4px;")
        layout.addWidget(mode_label)
        
        # Use the existing CleanBullpenApp functionality
        self.bullpen_content = CleanBullpenApp(self.pipeline)
        layout.addWidget(self.bullpen_content)
    
    def enable_semantic_mode(self):
        """Enable semantic mode with full constraint enforcement."""
        print("🎯 Practice mode: Syntactic + Semantic constraints")
        # TODO: Configure canvas for semantic constraint enforcement
    
    def load_egif(self, egif_content, example_name):
        """Load EGIF content into Practice mode."""
        print(f"🎯 Loading '{example_name}' into Practice mode")
        self.bullpen_content.load_egif_content(egif_content, example_name)


class BrowserArea(QWidget):
    """
    Browser area for exploring corpus and workspace content.
    Users can browse examples and copy them to Preparation area.
    """
    
    # Signal for copying graphs to Preparation
    copy_to_preparation = Signal(str, str)  # (egif_content, example_name)
    
    def __init__(self, pipeline=None):
        super().__init__()
        
        # Initialize pipeline for rendering previews (same as Preparation area)
        from egdf_dau_canonical import create_dau_compliant_egdf_generator
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        # Use provided pipeline or create default
        self.pipeline = pipeline
        self.egdf_generator = create_dau_compliant_egdf_generator()
        self.layout_engine = GraphvizLayoutEngine()
        
        self._setup_ui()
        print("🗂️ Browser area initialized with corpus functionality and visual preview")
    
    def _setup_ui(self):
        """Setup Browser area UI with corpus browser."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🗂️ Browser - Corpus & Workspace Explorer")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px; background: #F5F5F5; border-radius: 4px;")
        layout.addWidget(header)
        
        # Main content area - left column controls, large canvas
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        
        # Left column: All corpus controls stacked vertically
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_panel.setMinimumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)
        
        # Corpus browser (compact) - Examples above Example Details as requested
        self.corpus_browser = CorpusBrowser()
        self.corpus_browser.example_selected.connect(self._on_example_selected)
        left_layout.addWidget(self.corpus_browser)
        
        # Action buttons (stacked)
        self.copy_button = QPushButton("📋 Copy to Preparation")
        self.copy_button.clicked.connect(self._copy_to_preparation)
        self.copy_button.setEnabled(False)
        self.copy_button.setStyleSheet("font-weight: bold; padding: 10px; background: #28a745; color: white; border-radius: 4px; margin: 4px 0;")
        left_layout.addWidget(self.copy_button)
        
        # Annotation toggles (for analysis)
        annotations_label = QLabel("🔍 Display Annotations")
        annotations_label.setStyleSheet("font-weight: bold; margin-top: 8px; margin-bottom: 4px;")
        left_layout.addWidget(annotations_label)
        
        self.arity_checkbox = QCheckBox("Show Arity Numbers")
        self.arity_checkbox.setToolTip("Display argument position numbers (1,2,3...) for predicate analysis")
        self.arity_checkbox.stateChanged.connect(self._on_annotation_changed)
        left_layout.addWidget(self.arity_checkbox)
        
        self.identity_checkbox = QCheckBox("Show Identity Markers")
        self.identity_checkbox.setToolTip("Display '=' symbols on ligatures to clarify identity semantics")
        self.identity_checkbox.stateChanged.connect(self._on_annotation_changed)
        left_layout.addWidget(self.identity_checkbox)
        
        self.view_button = QPushButton("👁 View Details")
        self.view_button.clicked.connect(self._view_details)
        self.view_button.setEnabled(False)
        self.view_button.setStyleSheet("padding: 8px; background: #6c757d; color: white; border-radius: 4px; margin: 4px 0;")
        left_layout.addWidget(self.view_button)
        
        # Add stretch to push everything up
        left_layout.addStretch()
        
        content_layout.addWidget(left_panel)
        
        # Right side: Large canvas
        canvas_panel = QWidget()
        canvas_layout = QVBoxLayout(canvas_panel)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        
        # Interactive canvas using same EGGraphicsSceneRenderer as Preparation (fully manipulatable)
        from eg_graphics_scene_renderer import EGGraphicsSceneRenderer
        
        self.browser_canvas = EGGraphicsSceneRenderer()
        self.browser_canvas.setMinimumSize(600, 400)
        self.browser_canvas.setStyleSheet("border: 2px solid #DDD; border-radius: 4px; background: white;")
        
        canvas_layout.addWidget(self.browser_canvas)
        
        content_layout.addWidget(canvas_panel)
        
        layout.addLayout(content_layout)
        
        # Status
        self.status_label = QLabel("Ready - Select a corpus example to browse")
        self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 4px;")
        layout.addWidget(self.status_label)
        
        # Store current selection
        self.current_egif = ""
        self.current_example_name = ""
    
    def _on_example_selected(self, example_name, egif_content):
        """Handle corpus example selection."""
        self.current_egif = egif_content
        self.current_example_name = example_name
        
        # EGIF content is now handled directly by corpus browser (no separate preview needed)
        
        # Enable action buttons
        self.copy_button.setEnabled(True)
        self.view_button.setEnabled(True)
        self.status_label.setText(f"📋 Selected: {example_name}")
        print(f"🗂️ Browser: Selected {example_name}")
        
        # Automatically load and display the selected example
        self._load_and_display()
    
    def _on_annotation_changed(self):
        """Handle annotation toggle changes and refresh display."""
        if not self.current_egif:
            return
            
        # Update EGDF generator with new annotation settings
        show_arity = self.arity_checkbox.isChecked()
        show_identity = self.identity_checkbox.isChecked()
        
        # Recreate EGDF generator with new settings
        from egdf_dau_canonical import create_dau_compliant_egdf_generator
        self.egdf_generator = create_dau_compliant_egdf_generator(
            show_arity_annotations=show_arity,
            show_identity_annotations=show_identity
        )
        
        # Refresh the display
        self._load_and_display()
        
        # Provide user feedback
        annotations = []
        if show_arity:
            annotations.append("arity numbers")
        if show_identity:
            annotations.append("identity markers")
            
        if annotations:
            print(f"🔍 Annotations enabled: {', '.join(annotations)}")
        else:
            print("🔍 All annotations disabled")
    
    def _load_and_display(self):
        """Load and display selected example in Browser canvas using EXACT same process as Preparation tab."""
        if not self.current_egif:
            return
            
        try:
            print(f"🖼️ Rendering Browser canvas for '{self.current_example_name}'")
            
            # EXACT SAME PROCESS AS PREPARATION TAB:
            
            # Step 1: Parse EGIF using pipeline (same as Preparation)
            egi = self.pipeline.parse_egif(self.current_egif)
            print(f"✓ EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
            
            # Step 2: Generate Layout using working Graphviz engine (same as Preparation)
            layout_result = self.layout_engine.create_layout_from_graph(egi)
            print(f"✓ Layout: {len(layout_result.primitives)} primitives")
            
            # Step 3: Generate canonical Dau-compliant EGDF (same as Preparation)
            egdf_primitives = self.egdf_generator.generate_egdf_from_layout(egi, layout_result)
            print(f"✓ EGDF: {len(egdf_primitives)} Dau-compliant primitives")
            
            # Step 4: Convert EGDF primitives to dictionary format for compatibility (same as Preparation)
            spatial_primitives = []
            for primitive in egdf_primitives:
                spatial_primitive = {
                    'element_id': primitive.element_id,
                    'element_type': primitive.element_type,
                    'position': primitive.position,
                    'bounds': primitive.bounds,
                    'z_index': primitive.z_index
                }
                
                # Add display name for predicate names and vertex labels
                if hasattr(primitive, 'display_name') and primitive.display_name:
                    spatial_primitive['display_name'] = primitive.display_name
                
                # Add curve points for ligatures
                if hasattr(primitive, 'curve_points') and primitive.curve_points:
                    spatial_primitive['curve_points'] = primitive.curve_points
                
                spatial_primitives.append(spatial_primitive)
            
            # Step 5: Load into Qt Graphics Scene (same as Preparation)
            self.browser_canvas.load_from_egdf_primitives(spatial_primitives, egi)
            print(f"✅ Browser canvas rendered: {len(spatial_primitives)} primitives (fully interactive)")
            
        except Exception as e:
            print(f"❌ Failed to render Browser canvas for '{self.current_example_name}': {e}")
            print(f"🔍 DEBUG: Full traceback:")
            import traceback
            traceback.print_exc()
            
            # Clear canvas on error
            self.browser_canvas.scene.clear()
            
            # Show error in status
            self.status_label.setText(f"❌ Preview error: {self.current_example_name}")
    
    def _copy_to_preparation(self):
        """Copy current example to Preparation area."""
        if self.current_egif and self.current_example_name:
            self.copy_to_preparation.emit(self.current_egif, self.current_example_name)
            self.status_label.setText(f"📝 Copied '{self.current_example_name}' to Preparation")
            print(f"📝 Copied '{self.current_example_name}' to Preparation area")
            
            # Show confirmation
            QMessageBox.information(self, "Copied to Preparation", 
                                  f"'{self.current_example_name}' has been copied to the Preparation area.\n\nSwitch to the Graph Preparation tab to work with it.")
    

    
    def _view_details(self):
        """Show detailed view of current example."""
        if self.current_egif and self.current_example_name:
            # Create detailed view dialog
            dialog = QMessageBox(self)
            dialog.setWindowTitle(f"Details: {self.current_example_name}")
            dialog.setText(f"Example: {self.current_example_name}")
            dialog.setDetailedText(self.current_egif)
            dialog.setStandardButtons(QMessageBox.Ok)
            dialog.exec()


class EndoporeuticGameArea(QWidget):
    """
    Endoporeutic Game area for formal game interface.
    (Stub implementation for now)
    """
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        print("🎮 Endoporeutic Game area initialized (stub)")
    
    def _setup_ui(self):
        """Setup Endoporeutic Game area UI."""
        layout = QVBoxLayout(self)
        
        # Placeholder content
        placeholder = QLabel("🎮 Endoporeutic Game Area\n\nComing Soon:\n• Game position management\n• Move validation\n• Game history\n• Rule enforcement")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("font-size: 16px; color: #666; padding: 40px;")
        layout.addWidget(placeholder)


class CleanBullpenApp(QWidget):
    """
    Clean Bullpen application with interactive EGDF canvas.
    
    Features:
    - Interactive EGDF canvas with selection system
    - Graph rearrangement and manipulation
    - Canonical EGDF pipeline integration
    - Constraint-aware editing (Composition/Practice modes)
    """
    
    def __init__(self, pipeline):
        super().__init__()
        
        self.pipeline = pipeline
        self.current_egi = None
        self.current_egdf = None
        
        # Initialize canonical EGDF components (revert to working generator)
        self.egdf_generator = create_dau_compliant_egdf_generator()  # Use proven canonical generator
        self.layout_engine = GraphvizLayoutEngine()
        
        # Add area management as post-processing constraint layer
        from shapely_area_manager import ShapelyAreaManager
        canvas_bounds = (0, 0, 800, 600)  # Default canvas bounds
        self.area_manager = ShapelyAreaManager(canvas_bounds)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the clean Bullpen UI for graph preparation."""
        layout = QVBoxLayout(self)
        
        # Header for current graph
        self.graph_header = QLabel("📊 Graph Preparation - Ready for Browser input")
        self.graph_header.setFont(QFont("Arial", 14, QFont.Bold))
        self.graph_header.setStyleSheet("padding: 8px; background: #F8F9FA; border-radius: 4px; margin-bottom: 8px;")
        layout.addWidget(self.graph_header)
        
        # EGIF input area
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("EGIF:"))
        
        self.egif_input = QTextEdit()
        self.egif_input.setMaximumHeight(80)
        self.egif_input.setPlaceholderText("Load graphs from Browser or enter EGIF directly...")
        input_layout.addWidget(self.egif_input)
        
        self.load_button = QPushButton("Load")
        self.load_button.clicked.connect(self._load_egif)
        input_layout.addWidget(self.load_button)
        
        self.clear_button = QPushButton("Clear Canvas")
        self.clear_button.clicked.connect(self._clear_canvas)
        self.clear_button.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold;")
        input_layout.addWidget(self.clear_button)
        
        layout.addLayout(input_layout)
        
        # Create Qt Graphics Scene renderer (replaces all custom hit detection)
        self.canvas = EGGraphicsSceneRenderer()
        self.canvas.setMinimumSize(800, 600)
        
        # Connect Qt Graphics Framework signals
        self.canvas.element_moved.connect(self._on_element_moved)
        self.canvas.element_selected.connect(self._on_element_selected)
        
        layout.addWidget(self.canvas)
        
        # Live EGIF Chiron - shows current graph in linear form
        chiron_label = QLabel("📜 Current Graph (EGIF)")
        chiron_label.setStyleSheet("font-weight: bold; margin-top: 8px; margin-bottom: 4px;")
        layout.addWidget(chiron_label)
        
        self.egif_chiron = QTextEdit()
        self.egif_chiron.setMaximumHeight(60)
        self.egif_chiron.setReadOnly(True)
        self.egif_chiron.setPlaceholderText("Graph will appear here in EGIF format...")
        self.egif_chiron.setStyleSheet("""
            font-family: 'Courier New', monospace; 
            font-size: 11px; 
            background: #F8F9FA; 
            border: 1px solid #DDD; 
            border-radius: 4px;
            padding: 4px;
        """)
        layout.addWidget(self.egif_chiron)
        
        # Status
        self.status_label = QLabel("Ready - Load graphs from Browser or enter EGIF")
        self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 4px;")
        layout.addWidget(self.status_label)
    
    def _connect_signals(self):
        """Connect UI signals."""
        # No corpus browser signals needed - that's now in Browser area
        pass
    
    def load_egif_content(self, egif_content: str, example_name: str):
        """Load EGIF content from Browser area."""
        print(f"📝 Loading '{example_name}' into Preparation canvas")
        
        # Update header
        self.graph_header.setText(f"📊 Graph Preparation - {example_name}")
        
        # Load into input field
        self.egif_input.setPlainText(egif_content)
        
        # Automatically load and render
        self._load_egif()
        
        # Update status
        self.status_label.setText(f"✅ Loaded '{example_name}' - Ready for rearrangement")
    
    def _clear_canvas(self):
        """Clear the canvas and reset the preparation area."""
        try:
            # Clear the Qt Graphics Scene
            self.canvas.clear_scene()
            
            # Clear the EGIF input
            self.egif_input.clear()
            
            # Reset header and chiron
            self.graph_header.setText("📊 Graph Preparation - Ready for Browser input")
            self.egif_chiron.clear()
            
            print("🧹 Canvas cleared successfully")
            
        except Exception as e:
            print(f"❌ Error clearing canvas: {e}")
    
    def _load_egif(self):
        """Load EGIF from text input and render in canvas."""
        egif_text = self.egif_input.toPlainText().strip()
        
        if not egif_text:
            print("❌ No EGIF text provided")
            return
        
        try:
            # Step 1: Parse EGIF to EGI
            print("📝 Parsing EGIF...")
            egi = self.pipeline.parse_egif(egif_text)
            print(f"✓ EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.C)} cuts")
            
            # Step 2: Generate Graphviz layout
            print("📝 Generating layout...")
            layout_result = self.layout_engine.create_layout_from_graph(egi)
            print(f"✓ Layout: {len(layout_result.primitives)} primitives")
            
            # Step 3: Generate canonical Dau-compliant EGDF
            print("📝 Converting to canonical EGDF...")
            egdf_primitives = self.egdf_generator.generate_egdf_from_layout(egi, layout_result)
            print(f"✓ EGDF: {len(egdf_primitives)} Dau-compliant primitives")
            
            # Step 4: Convert EGDF primitives to dictionary format for compatibility
            spatial_primitives = []
            for primitive in egdf_primitives:
                spatial_primitive = {
                    'element_id': primitive.element_id,
                    'element_type': primitive.element_type,
                    'position': primitive.position,
                    'bounds': primitive.bounds,
                    'z_index': primitive.z_index
                }
                
                # Add display name for predicate names and vertex labels
                if hasattr(primitive, 'display_name') and primitive.display_name:
                    spatial_primitive['display_name'] = primitive.display_name
                
                # Add curve points for ligatures
                if hasattr(primitive, 'curve_points') and primitive.curve_points:
                    spatial_primitive['curve_points'] = primitive.curve_points
                
                spatial_primitives.append(spatial_primitive)
            
            # Load into Qt Graphics Scene - handles all hit detection automatically!
            self.canvas.load_from_egdf_primitives(spatial_primitives, egi)
            
            # Update header and chiron
            self.graph_header.setText(f"📊 Graph Preparation - Loaded from EGIF")
            self._update_egif_chiron(egi)
            
            print("✅ EGIF loaded and rendered successfully")
            
        except Exception as e:
            print(f"❌ Error loading EGIF: {e}")
            import traceback
            traceback.print_exc()

# ... (rest of the code remains the same)
            print(error_msg)
    
    def _on_element_selected(self, element_id):
        """Handle element selection in Qt Graphics Framework."""
        print(f"🎯 Qt Graphics: Element selected: {element_id}")
        self.status_label.setText(f"🎯 Selected: {element_id}")
        
        # Get all currently selected elements
        selected_elements = self.canvas.get_selected_elements()
        if len(selected_elements) > 1:
            element_list = ", ".join(selected_elements)
            self.status_label.setText(f"🎯 Selected: {element_list}")
    
    def _on_element_moved(self, element_id, delta_x, delta_y):
        """Handle element movement in Qt Graphics Framework."""
        print(f"🚚 Qt Graphics: Element moved: {element_id} by ({delta_x:.1f}, {delta_y:.1f})")
        self.status_label.setText(f"🚚 Moved: {element_id} by ({delta_x:.1f}, {delta_y:.1f})")
        
        # Update live EGIF chiron after movement
        self._update_egif_chiron_from_current_state()
    
    # Legacy signal handlers (will be removed once Qt Graphics Framework is fully integrated)
    def _on_selection_changed(self, selected_elements):
        """Handle selection changes in the interactive canvas (LEGACY)."""
        if selected_elements:
            element_list = ", ".join(selected_elements)
            self.status_label.setText(f"🎯 Selected: {element_list}")
            print(f"🎯 Selection changed: {selected_elements}")
        else:
            self.status_label.setText("Ready - Select elements or enter EGIF")
    
    def _on_element_double_clicked(self, element_id):
        """Handle double-click on elements (LEGACY)."""
        print(f"🖱️ Double-clicked element: {element_id}")
        self.status_label.setText(f"🖱️ Double-clicked: {element_id}")
        
        # TODO: Implement element-specific double-click actions
        # For now, just show info
        QMessageBox.information(self, "Element Info", f"Double-clicked element: {element_id}")
    
    def _on_context_action(self, action, element_id):
        """Handle context menu actions (LEGACY)."""
        print(f"🎬 Context action: {action} on {element_id}")
        self.status_label.setText(f"🎬 Action: {action} on {element_id}")
        
        # TODO: Implement actual context actions
        # For now, just show what would happen
        if action == "add_vertex":
            QMessageBox.information(self, "Add Vertex", "Would add a new vertex at cursor position")
        elif action == "add_predicate":
            QMessageBox.information(self, "Add Predicate", "Would add a new predicate at cursor position")
        elif action == "add_cut":
            QMessageBox.information(self, "Add Cut", "Would add a new cut around selected elements")
        elif action.startswith("edit_"):
            QMessageBox.information(self, "Edit Element", f"Would edit {element_id}")
        elif action.startswith("delete_"):
            QMessageBox.information(self, "Delete Element", f"Would delete {element_id}")
        else:
            QMessageBox.information(self, "Context Action", f"Action: {action}\nElement: {element_id}")
    
    def _on_drag_completed(self, element_ids, delta):
        """Handle completed drag operations with syntactic constraint preservation."""
        print(f"🚚 Drag completed: {element_ids} moved by {delta}")
        
        if not element_ids:
            print("❌ No element IDs provided for drag")
            return
            
        if not self.canvas.spatial_primitives:
            print("❌ No spatial primitives on canvas")
            return
        
        # Expand selection to include syntactically dependent elements
        expanded_element_ids = self._expand_selection_for_syntactic_constraints(element_ids)
        print(f"🔗 Expanded selection for constraints: {element_ids} → {expanded_element_ids}")
        
        # Actually move the expanded selection (including dependent elements)
        moved_count = 0
        for primitive in self.canvas.spatial_primitives:
            if not isinstance(primitive, dict):
                continue
                
            element_id = primitive.get('element_id')
            if element_id in expanded_element_ids:
                # Update position
                if 'position' in primitive:
                    old_pos = primitive['position']
                    new_pos = (old_pos[0] + delta.x(), old_pos[1] + delta.y())
                    primitive['position'] = new_pos
                    print(f"  📍 Moved {element_id}: {old_pos} → {new_pos}")
                
                # Update bounds
                if 'bounds' in primitive:
                    old_bounds = primitive['bounds']
                    new_bounds = (
                        old_bounds[0] + delta.x(),  # left
                        old_bounds[1] + delta.y(),  # top
                        old_bounds[2] + delta.x(),  # right
                        old_bounds[3] + delta.y()   # bottom
                    )
                    primitive['bounds'] = new_bounds
                
                # Update curve points for identity lines
                if 'curve_points' in primitive and primitive['curve_points']:
                    new_curve_points = []
                    for point in primitive['curve_points']:
                        new_point = (point[0] + delta.x(), point[1] + delta.y())
                        new_curve_points.append(new_point)
                    primitive['curve_points'] = new_curve_points
                
                moved_count += 1
        
        # Recalculate logical bounds and refresh canvas
        self.canvas._calculate_logical_bounds()
        self.canvas.update()
        
        # Update live EGIF chiron after movement
        if hasattr(self, 'current_egi') and self.current_egi:
            self._update_egif_chiron_from_current_state()
        
        # Update status
        self.status_label.setText(f"✅ Successfully moved {moved_count} elements")
        print(f"✅ Successfully moved {moved_count} elements")
    
    def _get_predicate_name_from_egi(self, egi, element_id):
        """Get predicate name from EGI graph."""
        try:
            # Look for the element in EGI edges (relations)
            for edge in egi.E:
                if edge.id == element_id:
                    return edge.relation_name
            return element_id  # Fallback to element ID
        except Exception as e:
            print(f"⚠ Could not get predicate name for {element_id}: {e}")
            return element_id
    
    def _expand_selection_for_syntactic_constraints(self, element_ids):
        """Expand selection to include syntactically dependent elements."""
        expanded = set(element_ids)
        
        for element_id in element_ids:
            # Find the element type
            element_type = self._get_element_type(element_id)
            
            if element_type == 'vertex':
                # When moving a vertex, include all connected identity lines
                connected_lines = self._find_connected_identity_lines(element_id)
                expanded.update(connected_lines)
                print(f"  🔗 Vertex {element_id} → adding connected lines: {connected_lines}")
                
            elif element_type == 'predicate':
                # When moving a predicate, include all connected identity lines
                connected_lines = self._find_connected_identity_lines(element_id)
                expanded.update(connected_lines)
                print(f"  🔗 Predicate {element_id} → adding connected lines: {connected_lines}")
                
            elif element_type == 'cut':
                # When moving a cut, include all contained elements
                contained_elements = self._find_elements_in_cut(element_id)
                expanded.update(contained_elements)
                print(f"  🔗 Cut {element_id} → adding contained elements: {contained_elements}")
        
        return list(expanded)
    
    def _get_element_type(self, element_id):
        """Get the type of an element from spatial primitives."""
        for primitive in self.canvas.spatial_primitives:
            if isinstance(primitive, dict) and primitive.get('element_id') == element_id:
                return primitive.get('element_type')
        return None
    
    def _find_connected_identity_lines(self, element_id):
        """Find all identity lines connected to a vertex or predicate."""
        connected_lines = []
        
        for primitive in self.canvas.spatial_primitives:
            if not isinstance(primitive, dict):
                continue
                
            if primitive.get('element_type') == 'identity_line':
                line_id = primitive.get('element_id')
                
                # Identity line IDs follow pattern: ligature_vertex_predicate or similar
                # Check if this identity line connects to our element
                if element_id in line_id:
                    connected_lines.append(line_id)
                    print(f"    🔗 Found connected line: {line_id}")
                    
        print(f"  🔍 Found {len(connected_lines)} connected lines for {element_id}")
        return connected_lines
    
    def _find_elements_in_cut(self, cut_id):
        """Find all elements contained within a cut's area."""
        contained_elements = []
        
        # Get cut bounds
        cut_bounds = None
        for primitive in self.canvas.spatial_primitives:
            if (isinstance(primitive, dict) and 
                primitive.get('element_id') == cut_id and 
                primitive.get('element_type') == 'cut'):
                cut_bounds = primitive.get('bounds')
                break
        
        if not cut_bounds:
            return contained_elements
            
        cut_left, cut_top, cut_right, cut_bottom = cut_bounds
        
        # Check which elements are inside the cut
        for primitive in self.canvas.spatial_primitives:
            if not isinstance(primitive, dict):
                continue
                
            element_id = primitive.get('element_id')
            element_type = primitive.get('element_type')
            
            # Skip the cut itself
            if element_id == cut_id:
                continue
                
            # Check if element is inside cut bounds
            position = primitive.get('position')
            if position:
                x, y = position
                if cut_left < x < cut_right and cut_top < y < cut_bottom:
                    contained_elements.append(element_id)
                    
        return contained_elements
    
    def _update_egif_chiron(self, egi):
        """Update the live EGIF chiron with the current EGI."""
        print(f"🔍 DEBUG: _update_egif_chiron called with EGI: {egi}")
        print(f"🔍 DEBUG: self.egif_chiron exists: {hasattr(self, 'egif_chiron')}")
        
        if not hasattr(self, 'egif_chiron'):
            print("❌ ERROR: egif_chiron widget not found!")
            return
            
        try:
            from src.egif_generator_dau import EGIFGenerator
            
            # Convert EGI back to EGIF format
            egif_generator = EGIFGenerator(egi)
            egif_text = egif_generator.generate()
            
            print(f"🔍 DEBUG: Generated EGIF text: '{egif_text}'")
            
            # Update the chiron display
            self.egif_chiron.setPlainText(egif_text)
            self.egif_chiron.update()  # Force UI update
            print(f"📜 CHIRON UPDATED: {egif_text[:50]}...")
            
        except Exception as e:
            # Fallback to basic representation if EGIF generation fails
            fallback_text = f"EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts"
            print(f"🔍 DEBUG: Exception occurred: {e}")
            print(f"🔍 DEBUG: Using fallback text: '{fallback_text}'")
            self.egif_chiron.setPlainText(fallback_text)
            self.egif_chiron.update()  # Force UI update
            print(f"⚠ CHIRON FALLBACK: {fallback_text}")
    
    def _update_egif_chiron_from_current_state(self):
        """Update chiron from current canvas state (after drag operations)."""
        try:
            # For now, use the stored EGI since we haven't implemented 
            # reverse conversion from spatial primitives back to EGI yet
            if hasattr(self, 'current_egi') and self.current_egi:
                # TODO: In the future, we should reconstruct EGI from current spatial primitives
                # to reflect any structural changes made through dragging
                self._update_egif_chiron(self.current_egi)
                print("📜 Chiron updated from stored EGI (drag operations preserve structure)")
        except Exception as e:
            print(f"⚠ Could not update chiron from current state: {e}")


class ArisbeEGClean(QMainWindow):
    """
    Clean Arisbe EG Works main window with three-area architecture.
    
    Three main areas:
    - Graph Preparation (Composition/Practice modes)
    - Browser (corpus and workspace exploration)
    - Endoporeutic Game (formal game interface)
    """
    
    def __init__(self):
        super().__init__()
        
        # Application metadata
        self.app_name = "Arisbe EG Works"
        self.version = "3.0.0"
        
        # Initialize canonical pipeline
        self.pipeline = get_canonical_pipeline()
        
        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        
        print(f"🚀 {self.app_name} v{self.version} - Three-Area Architecture initialized")
    
    def _setup_ui(self):
        """Setup main UI with three-area tab architecture."""
        # Central widget with main tab container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Main application tabs (three areas)
        self.main_tabs = QTabWidget()
        self.main_tabs.setTabPosition(QTabWidget.North)
        self.main_tabs.currentChanged.connect(self._on_main_tab_changed)
        
        # 1. Browser (with corpus functionality) - DEFAULT TAB
        self.browser_widget = BrowserArea(self.pipeline)
        self.browser_widget.copy_to_preparation.connect(self._on_copy_to_preparation)
        self.main_tabs.addTab(self.browser_widget, "🗂️ Browser")
        
        # 2. Graph Preparation (with Composition/Practice sub-tabs)
        self.preparation_widget = GraphPreparationArea(self.pipeline)
        self.main_tabs.addTab(self.preparation_widget, "📝 Graph Preparation")
        
        # 3. Endoporeutic Game (stub for now)
        self.epg_widget = EndoporeuticGameArea()
        self.main_tabs.addTab(self.epg_widget, "🎮 Endoporeutic Game")
        
        layout.addWidget(self.main_tabs)
        
        # Set window properties
        self.setWindowTitle(f"{self.app_name} v{self.version}")
        self.setGeometry(100, 100, 1400, 900)
        self.show()
    
    def _on_main_tab_changed(self, index):
        """Handle main tab changes between the three areas."""
        tab_names = ["Browser", "Graph Preparation", "Endoporeutic Game"]
        if 0 <= index < len(tab_names):
            print(f"🔄 Switched to {tab_names[index]} area")
            self.statusBar().showMessage(f"Active: {tab_names[index]}", 2000)
    
    def _on_copy_to_preparation(self, egif_content, example_name):
        """Handle copying graph from Browser to Preparation area."""
        print(f"📝 Copying '{example_name}' from Browser to Preparation")
        
        # Load the EGIF into the Preparation area
        self.preparation_widget.load_egif_from_browser(egif_content, example_name)
        
        # Keep user on current tab - let them decide when to switch
        # self.main_tabs.setCurrentIndex(1)  # Removed automatic switching
        
        # Show status
        self.statusBar().showMessage(f"Copied '{example_name}' to Preparation area", 3000)
    
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Export action
        export_action = QAction("&Export SVG...", self)
        export_action.triggered.connect(self._export_svg)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage(f"{self.app_name} ready")
    
    def _export_svg(self):
        """Export current diagram to SVG."""
        if hasattr(self.bullpen_app, 'current_egi') and self.bullpen_app.current_egi:
            try:
                # Use the same working SVG export as our sanity check
                from renderer_minimal_dau import render_layout_to_svg
                from graphviz_layout_engine_v2 import GraphvizLayoutEngine
                
                layout_engine = GraphvizLayoutEngine()
                layout = layout_engine.create_layout_from_graph(self.bullpen_app.current_egi)
                
                # Save to file
                svg_path = "exported_diagram.svg"
                render_layout_to_svg(
                    layout,
                    svg_path,
                    canvas_px=(800, 600),
                    graph=self.bullpen_app.current_egi,
                    background_color="white",
                    cut_corner_radius=12.0,
                    pred_font_size=14,
                    pred_char_width=8,
                    pred_pad_x=6,
                    pred_pad_y=4,
                )
                
                self.status_bar.showMessage(f"✓ Exported to {svg_path}")
                QMessageBox.information(self, "Export Success", f"Diagram exported to {svg_path}")
                
            except Exception as e:
                QMessageBox.warning(self, "Export Error", f"Failed to export: {e}")
        else:
            QMessageBox.information(self, "No Diagram", "No diagram loaded to export")
    
    def _show_about(self):
        """Show about dialog."""
        about_text = f"""
        <h2>{self.app_name}</h2>
        <p>Version {self.version}</p>
        <p>A clean, working implementation of Existential Graph editing with:</p>
        <ul>
        <li>✅ Working EGDF canvas renderer</li>
        <li>✅ Corpus browser integration</li>
        <li>✅ Canonical Dau-compliant pipeline</li>
        <li>✅ Educational EG examples</li>
        </ul>
        <p>Built on the proven canonical EGIF ↔ EGI ↔ EGDF pipeline.</p>
        """
        
        QMessageBox.about(self, "About", about_text)


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Arisbe EG Works (Clean)")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Arisbe Project")
    
    # Create and show main window
    window = ArisbeEGClean()
    window.show()
    
    print("🎨 Clean GUI launched successfully!")
    print("📚 Browse corpus examples or enter EGIF directly")
    print("🖼️ Canvas uses proven EGDF rendering pipeline")
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
