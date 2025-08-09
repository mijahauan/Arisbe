#!/usr/bin/env python3
"""
Enhanced GUI Foundation - Integrated Professional EG Editor

Demonstrates the solidified GUI rendering, selection system, and transformation rules
with Dau-compliant visual quality and professional interaction patterns.
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Set, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Enhanced components
from src.enhanced_diagram_renderer import EnhancedDiagramRenderer, RenderingContext
from src.enhanced_selection_system import EnhancedSelectionSystem
from src.eg_transformation_engine import EGTransformationEngine, TransformationRule
from src.dau_rendering_theme import get_theme_manager, RenderingQuality

# Core pipeline components
from src.egif_parser_dau import EGIFParser
from src.egi_core_dau import RelationalGraphWithCuts
from src.graphviz_layout_engine_v2 import GraphvizLayoutEngine
from src.layout_engine_clean import SpatialPrimitive, LayoutResult
from src.corpus_loader import get_corpus_loader
from src.mode_aware_selection import Mode, ActionType

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTextEdit, QLabel, QSplitter, QFrame, QComboBox,
        QCheckBox, QGroupBox, QStatusBar, QMenuBar, QMenu, QAction,
        QToolBar, QButtonGroup, QRadioButton
    )
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QAction as QGuiAction
    from PySide6.QtCore import Qt, QPointF, QRectF, QTimer
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    print("PySide6 not available - install with: pip install PySide6")
    # Create dummy classes to prevent NameError - but PySide6 should be available
    class Qt:
        # These are just placeholders - PySide6 should be installed
        Horizontal = 1
        Vertical = 2
        LeftButton = 1
        RightButton = 2
        ControlModifier = 1
        AlignCenter = 1
        NoPen = 1
        NoBrush = 1
        SolidLine = 1
        DashLine = 1
        RoundCap = 1
        RoundJoin = 1
    
    # Dummy widget classes
    class QWidget: pass
    class QSplitter: 
        def setOrientation(self, orientation): pass
    class QApplication: pass


class EnhancedEGDiagramWidget(QWidget):
    """Enhanced diagram widget with professional rendering and interaction."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        # Enhanced components
        self.renderer = EnhancedDiagramRenderer()
        self.selection_system = EnhancedSelectionSystem()
        self.transformation_engine = EGTransformationEngine()
        
        # Core pipeline
        self.layout_engine = GraphvizLayoutEngine()
        self.egif_parser = EGIFParser()
        
        # State
        self.egi: Optional[RelationalGraphWithCuts] = None
        self.spatial_primitives: List[SpatialPrimitive] = []
        self.current_mode = Mode.WARMUP
        
        # Visual settings
        self.show_annotations = False
        self.show_argument_labels = False
        self.show_context_backgrounds = True
        
        # Setup interaction
        self.setMouseTracking(True)
        self._setup_action_callbacks()
    
    def _setup_action_callbacks(self):
        """Setup callbacks for transformation actions."""
        self.selection_system.register_action_callback(
            ActionType.ADD_VERTEX, self._add_vertex
        )
        self.selection_system.register_action_callback(
            ActionType.ADD_PREDICATE, self._add_predicate
        )
        self.selection_system.register_action_callback(
            ActionType.ADD_CUT, self._add_cut
        )
        self.selection_system.register_action_callback(
            ActionType.DELETE_ELEMENT, self._delete_element
        )
        self.selection_system.register_action_callback(
            ActionType.APPLY_ERASURE, self._apply_erasure
        )
        self.selection_system.register_action_callback(
            ActionType.APPLY_INSERTION, self._apply_insertion
        )
        self.selection_system.register_action_callback(
            ActionType.APPLY_ITERATION, self._apply_iteration
        )
        self.selection_system.register_action_callback(
            ActionType.APPLY_DOUBLE_CUT_ADDITION, self._apply_double_cut_addition
        )
        self.selection_system.register_action_callback(
            ActionType.APPLY_DOUBLE_CUT_REMOVAL, self._apply_double_cut_removal
        )
    
    def load_egi_from_egif(self, egif_text: str):
        """Load EGI from EGIF text using canonical pipeline."""
        try:
            # Parse EGIF to EGI
            self.egi = self.egif_parser.parse_to_graph(egif_text)
            
            # Update selection system
            self.selection_system.set_graph(self.egi)
            
            # Create layout
            layout_result = self.layout_engine.create_layout_from_graph(self.egi)
            self.spatial_primitives = list(layout_result.primitives.values())
            
            # Trigger repaint
            self.update()
            
            print(f"✓ Loaded EGI with {len(self.egi.V)} vertices, {len(self.egi.E)} edges, {len(self.egi.Cut)} cuts")
            
        except Exception as e:
            print(f"Error loading EGIF: {e}")
    
    def switch_mode(self, new_mode: Mode):
        """Switch between Warmup and Practice modes."""
        self.current_mode = new_mode
        self.selection_system.switch_mode(new_mode)
        self.update()
        print(f"Switched to {new_mode.value} mode")
    
    def set_rendering_theme(self, theme_name: str):
        """Set the rendering theme."""
        self.renderer.set_theme(theme_name)
        self.update()
        print(f"Set rendering theme: {theme_name}")
    
    def paintEvent(self, event):
        """Paint the diagram with enhanced rendering."""
        if not PYSIDE6_AVAILABLE:
            return
            
        painter = QPainter(self)
        
        if self.egi and self.spatial_primitives:
            # Create rendering context
            context = RenderingContext(
                egi=self.egi,
                spatial_primitives=self.spatial_primitives,
                selection_state=self.selection_system.get_selection_state(),
                current_mode=self.current_mode,
                show_annotations=self.show_annotations,
                show_argument_labels=self.show_argument_labels,
                show_context_backgrounds=self.show_context_backgrounds
            )
            
            # Render with enhanced renderer
            self.renderer.render_diagram(painter, context)
            
            # Render selection feedback
            self.selection_system.render_selection_feedback(painter, self.spatial_primitives)
        else:
            # Draw placeholder
            painter.setPen(QPen(QColor("#CCCCCC")))
            painter.drawText(self.rect(), Qt.AlignCenter, "Load an EGIF expression to begin")
    
    def mousePressEvent(self, event):
        """Handle mouse press with enhanced selection."""
        if not PYSIDE6_AVAILABLE:
            return
            
        pos = (event.position().x(), event.position().y())
        element_id = self._find_element_at_position(pos)
        modifiers = event.modifiers()
        
        if event.button() == Qt.LeftButton:
            self.selection_system.handle_mouse_press(pos, element_id, modifiers)
            self.update()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(pos, element_id)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move with enhanced interaction."""
        if not PYSIDE6_AVAILABLE:
            return
            
        pos = (event.position().x(), event.position().y())
        element_id = self._find_element_at_position(pos)
        
        if self.selection_system.handle_mouse_move(pos, element_id):
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if not PYSIDE6_AVAILABLE:
            return
            
        pos = (event.position().x(), event.position().y())
        
        if self.selection_system.handle_mouse_release(pos):
            self.update()
    
    def _find_element_at_position(self, pos: Tuple[float, float]) -> Optional[str]:
        """Find element at mouse position."""
        x, y = pos
        
        # Check each spatial primitive for hit testing
        for primitive in self.spatial_primitives:
            if self._point_in_primitive(x, y, primitive):
                return primitive.element_id
        
        return None
    
    def _point_in_primitive(self, x: float, y: float, primitive: SpatialPrimitive) -> bool:
        """Check if point is within primitive bounds."""
        if hasattr(primitive, 'bounds'):
            x1, y1, x2, y2 = primitive.bounds
            return x1 <= x <= x2 and y1 <= y <= y2
        elif hasattr(primitive, 'position'):
            px, py = primitive.position
            radius = 15  # Hit test radius
            return abs(x - px) <= radius and abs(y - py) <= radius
        
        return False
    
    def _show_context_menu(self, pos: Tuple[float, float], element_id: Optional[str]):
        """Show context menu for current selection."""
        menu = self.selection_system.handle_context_menu(self, pos, element_id)
        if menu:
            # Connect menu actions
            for action in menu.actions():
                if action.data():
                    action.triggered.connect(
                        lambda checked, a=action: self._execute_menu_action(a.data())
                    )
            
            # Show menu at cursor position
            global_pos = self.mapToGlobal(self.mapFromScene(pos[0], pos[1]))
            menu.exec(global_pos)
    
    def _execute_menu_action(self, action_type: ActionType):
        """Execute action from context menu."""
        success = self.selection_system.execute_action(action_type)
        if success:
            self.update()
            print(f"Executed action: {action_type.value}")
        else:
            print(f"Failed to execute action: {action_type.value}")
    
    # Action callback implementations
    def _add_vertex(self):
        """Add vertex action."""
        if self.egi:
            result = self.transformation_engine.apply_transformation(
                self.egi, TransformationRule.INSERTION,
                element_type="vertex"
            )
            if result.success:
                self._update_egi(result.new_egi)
    
    def _add_predicate(self):
        """Add predicate action."""
        if self.egi:
            result = self.transformation_engine.apply_transformation(
                self.egi, TransformationRule.INSERTION,
                element_type="predicate",
                predicate_name="NewPredicate"
            )
            if result.success:
                self._update_egi(result.new_egi)
    
    def _add_cut(self):
        """Add cut action."""
        if self.egi:
            result = self.transformation_engine.apply_transformation(
                self.egi, TransformationRule.INSERTION,
                element_type="cut"
            )
            if result.success:
                self._update_egi(result.new_egi)
    
    def _delete_element(self):
        """Delete element action."""
        selected = self.selection_system.get_selection_state().selected_elements
        if selected and self.egi:
            element_id = next(iter(selected))
            result = self.transformation_engine.apply_transformation(
                self.egi, TransformationRule.ERASURE,
                element_id=element_id
            )
            if result.success:
                self._update_egi(result.new_egi)
    
    def _apply_erasure(self):
        """Apply erasure transformation."""
        selected = self.selection_system.get_selection_state().selected_elements
        if selected and self.egi:
            element_id = next(iter(selected))
            result = self.transformation_engine.apply_transformation(
                self.egi, TransformationRule.ERASURE,
                element_id=element_id
            )
            if result.success:
                self._update_egi(result.new_egi)
            else:
                print(f"Erasure failed: {result.error_message}")
    
    def _apply_insertion(self):
        """Apply insertion transformation."""
        if self.egi:
            result = self.transformation_engine.apply_transformation(
                self.egi, TransformationRule.INSERTION,
                element_type="vertex"
            )
            if result.success:
                self._update_egi(result.new_egi)
    
    def _apply_iteration(self):
        """Apply iteration transformation."""
        selected = self.selection_system.get_selection_state().selected_elements
        if selected and self.egi:
            element_id = next(iter(selected))
            result = self.transformation_engine.apply_transformation(
                self.egi, TransformationRule.ITERATION,
                element_id=element_id,
                target_context="sheet"
            )
            if result.success:
                self._update_egi(result.new_egi)
    
    def _apply_double_cut_addition(self):
        """Apply double cut addition."""
        if self.egi:
            result = self.transformation_engine.apply_transformation(
                self.egi, TransformationRule.DOUBLE_CUT_ADDITION,
                target_area="sheet"
            )
            if result.success:
                self._update_egi(result.new_egi)
    
    def _apply_double_cut_removal(self):
        """Apply double cut removal."""
        # This would need proper cut selection logic
        print("Double cut removal requires selecting nested cuts")
    
    def _update_egi(self, new_egi: RelationalGraphWithCuts):
        """Update EGI and refresh display."""
        self.egi = new_egi
        self.selection_system.set_graph(new_egi)
        
        # Recreate layout
        layout_result = self.layout_engine.create_layout_from_graph(self.egi)
        self.spatial_primitives = list(layout_result.primitives.values())
        
        # Clear selection
        self.selection_system.mode_aware_selection.clear_selection()
        
        self.update()


class EnhancedGUIFoundation(QMainWindow):
    """Enhanced GUI foundation with professional features."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe Enhanced GUI Foundation - Professional EG Editor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize components
        self.theme_manager = get_theme_manager()
        self.corpus_loader = None
        
        # Load corpus
        try:
            self.corpus_loader = get_corpus_loader()
            print(f"✓ Corpus loaded with {len(self.corpus_loader.examples)} examples")
        except Exception as e:
            print(f"Warning: Could not load corpus: {e}")
        
        # Sample EGIF expressions
        self.sample_egifs = [
            '(Human "Socrates")',
            '(Human "Socrates") (Mortal "Socrates")',
            '*x (Human x) ~[ (Mortal x) ]',
            '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            '*x *y (Loves x y) ~[ (Happy x) ]',
            '*x ~[ ~[ (P x) ] ]',  # Double cut
        ]
        
        self.setup_ui()
        self.load_sample_diagram()
    
    def setup_ui(self):
        """Setup the enhanced user interface."""
        # Create menu bar
        self._create_menu_bar()
        
        # Create main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter
        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Controls
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Diagram
        self.diagram_widget = EnhancedEGDiagramWidget()
        splitter.addWidget(self.diagram_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        # Create toolbar after diagram widget is available
        self._create_toolbar()
        
        # Create status bar
        self.statusBar().showMessage("Enhanced GUI Foundation Ready")
    
    def _create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New", self._new_diagram)
        file_menu.addAction("Open", self._open_diagram)
        file_menu.addAction("Save", self._save_diagram)
        file_menu.addSeparator()
        file_menu.addAction("Export PNG", self._export_png)
        file_menu.addAction("Export SVG", self._export_svg)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Undo", self._undo)
        edit_menu.addAction("Redo", self._redo)
        edit_menu.addSeparator()
        edit_menu.addAction("Select All", self._select_all)
        edit_menu.addAction("Clear Selection", self._clear_selection)
        
        # View menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction("Zoom In", self._zoom_in)
        view_menu.addAction("Zoom Out", self._zoom_out)
        view_menu.addAction("Fit to Window", self._fit_to_window)
        
        # Mode menu
        mode_menu = menubar.addMenu("Mode")
        mode_menu.addAction("Warmup Mode", lambda: self._switch_mode(Mode.WARMUP))
        mode_menu.addAction("Practice Mode", lambda: self._switch_mode(Mode.PRACTICE))
    
    def _create_toolbar(self):
        """Create toolbar."""
        toolbar = self.addToolBar("Main")
        
        # Mode selection
        toolbar.addAction("Warmup", lambda: self._switch_mode(Mode.WARMUP))
        toolbar.addAction("Practice", lambda: self._switch_mode(Mode.PRACTICE))
        toolbar.addSeparator()
        
        # Theme selection
        theme_action = toolbar.addAction("Theme")
        # This would open a theme selection dialog
        
        toolbar.addSeparator()
        
        # Quick actions
        toolbar.addAction("Add Vertex", self.diagram_widget._add_vertex)
        toolbar.addAction("Add Cut", self.diagram_widget._add_cut)
    
    def _create_left_panel(self) -> QWidget:
        """Create left control panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setMaximumWidth(300)
        
        layout = QVBoxLayout(panel)
        
        # EGIF Input
        egif_group = QGroupBox("EGIF Input")
        egif_layout = QVBoxLayout(egif_group)
        
        self.egif_input = QTextEdit()
        self.egif_input.setMaximumHeight(100)
        self.egif_input.textChanged.connect(self._on_egif_changed)
        egif_layout.addWidget(self.egif_input)
        
        render_btn = QPushButton("Render Diagram")
        render_btn.clicked.connect(self._render_diagram)
        egif_layout.addWidget(render_btn)
        
        layout.addWidget(egif_group)
        
        # Mode Selection
        mode_group = QGroupBox("Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_buttons = QButtonGroup()
        warmup_radio = QRadioButton("Warmup (Composition)")
        practice_radio = QRadioButton("Practice (Transformation)")
        warmup_radio.setChecked(True)
        
        self.mode_buttons.addButton(warmup_radio, 0)
        self.mode_buttons.addButton(practice_radio, 1)
        self.mode_buttons.buttonClicked.connect(self._on_mode_changed)
        
        mode_layout.addWidget(warmup_radio)
        mode_layout.addWidget(practice_radio)
        
        layout.addWidget(mode_group)
        
        # Theme Selection
        theme_group = QGroupBox("Rendering Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_combo = QComboBox()
        themes = self.theme_manager.get_available_themes()
        for theme_id, theme_name in themes.items():
            self.theme_combo.addItem(theme_name, theme_id)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        
        theme_layout.addWidget(self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Visual Options
        visual_group = QGroupBox("Visual Options")
        visual_layout = QVBoxLayout(visual_group)
        
        self.annotations_check = QCheckBox("Show Annotations")
        self.annotations_check.toggled.connect(self._on_annotations_toggled)
        visual_layout.addWidget(self.annotations_check)
        
        self.labels_check = QCheckBox("Show Argument Labels")
        self.labels_check.toggled.connect(self._on_labels_toggled)
        visual_layout.addWidget(self.labels_check)
        
        self.context_check = QCheckBox("Show Context Backgrounds")
        self.context_check.setChecked(True)
        self.context_check.toggled.connect(self._on_context_toggled)
        visual_layout.addWidget(self.context_check)
        
        layout.addWidget(visual_group)
        
        # Corpus Examples
        if self.corpus_loader:
            corpus_group = QGroupBox("Corpus Examples")
            corpus_layout = QVBoxLayout(corpus_group)
            
            self.corpus_combo = QComboBox()
            self._populate_corpus_dropdown()
            corpus_layout.addWidget(self.corpus_combo)
            
            import_btn = QPushButton("Import Example")
            import_btn.clicked.connect(self._import_corpus_example)
            corpus_layout.addWidget(import_btn)
            
            layout.addWidget(corpus_group)
        
        # Sample Examples
        samples_group = QGroupBox("Sample Examples")
        samples_layout = QVBoxLayout(samples_group)
        
        for i, egif in enumerate(self.sample_egifs):
            btn = QPushButton(f"Example {i+1}")
            btn.clicked.connect(lambda checked, text=egif: self._load_sample(text))
            samples_layout.addWidget(btn)
        
        layout.addWidget(samples_group)
        
        layout.addStretch()
        
        return panel
    
    def _populate_corpus_dropdown(self):
        """Populate corpus dropdown."""
        if self.corpus_loader:
            self.corpus_combo.addItem("Select example...", None)
            for example in self.corpus_loader.examples:
                title = example.metadata.get('title', example.egif[:50])
                self.corpus_combo.addItem(title, example)
    
    def _on_egif_changed(self):
        """Handle EGIF input change."""
        # Auto-render could be added here
        pass
    
    def _render_diagram(self):
        """Render diagram from EGIF input."""
        egif_text = self.egif_input.toPlainText().strip()
        if egif_text:
            self.diagram_widget.load_egi_from_egif(egif_text)
    
    def _on_mode_changed(self, button):
        """Handle mode change."""
        mode = Mode.WARMUP if button.id() == 0 else Mode.PRACTICE
        self.diagram_widget.switch_mode(mode)
        self.statusBar().showMessage(f"Switched to {mode.value} mode")
    
    def _on_theme_changed(self, theme_name):
        """Handle theme change."""
        # Find theme ID by name
        themes = self.theme_manager.get_available_themes()
        theme_id = None
        for tid, tname in themes.items():
            if tname == theme_name:
                theme_id = tid
                break
        
        if theme_id:
            self.diagram_widget.set_rendering_theme(theme_id)
            self.statusBar().showMessage(f"Set theme: {theme_name}")
    
    def _on_annotations_toggled(self, checked):
        """Handle annotations toggle."""
        self.diagram_widget.show_annotations = checked
        self.diagram_widget.update()
    
    def _on_labels_toggled(self, checked):
        """Handle argument labels toggle."""
        self.diagram_widget.show_argument_labels = checked
        self.diagram_widget.update()
    
    def _on_context_toggled(self, checked):
        """Handle context backgrounds toggle."""
        self.diagram_widget.show_context_backgrounds = checked
        self.diagram_widget.update()
    
    def _import_corpus_example(self):
        """Import selected corpus example."""
        if self.corpus_loader:
            example = self.corpus_combo.currentData()
            if example:
                self.egif_input.setPlainText(example.egif)
                self._render_diagram()
    
    def _load_sample(self, egif_text):
        """Load sample EGIF."""
        self.egif_input.setPlainText(egif_text)
        self._render_diagram()
    
    def load_sample_diagram(self):
        """Load first sample on startup."""
        self._load_sample(self.sample_egifs[0])
    
    # Menu action implementations
    def _new_diagram(self): pass
    def _open_diagram(self): pass
    def _save_diagram(self): pass
    def _export_png(self): pass
    def _export_svg(self): pass
    def _undo(self): pass
    def _redo(self): pass
    def _select_all(self): pass
    def _clear_selection(self): 
        self.diagram_widget.selection_system.mode_aware_selection.clear_selection()
        self.diagram_widget.update()
    def _zoom_in(self): pass
    def _zoom_out(self): pass
    def _fit_to_window(self): pass
    def _switch_mode(self, mode): 
        self.diagram_widget.switch_mode(mode)


def main():
    """Run the enhanced GUI foundation."""
    if not PYSIDE6_AVAILABLE:
        print("PySide6 is required. Install with: pip install PySide6")
        return
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Arisbe Enhanced GUI Foundation")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Arisbe Project")
    
    # Create and show main window
    window = EnhancedGUIFoundation()
    window.show()
    
    print("=== Enhanced GUI Foundation Started ===")
    print("Features:")
    print("- Dau-compliant rendering with professional themes")
    print("- Enhanced selection system with visual feedback")
    print("- Formal transformation rules engine")
    print("- Mode-aware interaction (Warmup/Practice)")
    print("- Context menus and professional interaction patterns")
    print("- Canonical pipeline integration (EGIF→EGI→EGDF)")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
