"""
Interactive EGI Viewer

Integration example showing how the viewport-based renderer works with
existing GUI components to provide a complete interactive EGI experience.
"""

from typing import Optional, List
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QWheelEvent, QMouseEvent, QKeyEvent, QPainter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,
    QPushButton, QComboBox, QLabel, QSlider, QCheckBox, QGroupBox,
    QSplitter, QTextEdit
)

from egi_core_dau import RelationalGraphWithCuts
from chapter21_diagram_engine import UniversalEGIEngine, InteractionMode
from gui.viewport_renderer import ViewportRenderer, ViewportState, RenderingLevel
from gui.style_manager import STYLE_MANAGER, get_current_style
from gui.interaction_layer import InteractionManager, SelectionMode, InteractionState
from formal_transformation_rules import TransformationResult


class InteractiveGraphicsView(QGraphicsView):
    """
    Custom graphics view that integrates with viewport renderer for
    seamless zooming, panning, and interaction.
    """
    
    # Signals
    viewport_changed = Signal(QPointF, float, QRectF)  # center, zoom, visible_rect
    mouse_pressed = Signal(QPointF, Qt.KeyboardModifiers)
    mouse_dragged = Signal(QPointF, QPointF)  # start, current
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configure view
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Interaction state
        self.last_mouse_pos = QPointF()
        self.is_dragging = False
        
    def wheelEvent(self, event: QWheelEvent):
        """Handle zoom with mouse wheel with zoom limits."""
        # Calculate zoom factor
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        # Get current transform
        current_scale = self.transform().m11()  # Get current scale factor
        
        # Set zoom limits
        min_scale = 0.1   # Don't zoom out beyond 10%
        max_scale = 10.0  # Don't zoom in beyond 1000%
        
        # Set zoom factor based on wheel direction
        if event.angleDelta().y() > 0:
            # Zoom in - check max limit
            if current_scale * zoom_in_factor <= max_scale:
                zoom_factor = zoom_in_factor
            else:
                zoom_factor = 1.0  # No zoom if at limit
        else:
            # Zoom out - check min limit
            if current_scale * zoom_out_factor >= min_scale:
                zoom_factor = zoom_out_factor
            else:
                zoom_factor = 1.0  # No zoom if at limit
            
        # Apply zoom only if not at limit
        if zoom_factor != 1.0:
            self.scale(zoom_factor, zoom_factor)
            
            # Emit viewport change
            self._emit_viewport_change()
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for selection and interaction."""
        scene_pos = self.mapToScene(event.pos())
        self.last_mouse_pos = scene_pos
        
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed.emit(scene_pos, event.modifiers())
            
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse movement for dragging operations."""
        scene_pos = self.mapToScene(event.pos())
        
        if event.buttons() & Qt.MouseButton.LeftButton:
            if not self.is_dragging:
                self.is_dragging = True
                
            self.mouse_dragged.emit(self.last_mouse_pos, scene_pos)
            
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        self.is_dragging = False
        super().mouseReleaseEvent(event)
        
    def resizeEvent(self, event):
        """Handle view resize."""
        super().resizeEvent(event)
        self._emit_viewport_change()
        
    def _emit_viewport_change(self):
        """Emit viewport change signal with current parameters."""
        # Get current view parameters
        scene_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        center = scene_rect.center()
        zoom = self.transform().m11()  # Get current zoom level
        
        self.viewport_changed.emit(center, zoom, scene_rect)


class InteractiveEGIViewer(QWidget):
    """
    Complete interactive EGI viewer integrating viewport renderer
    with existing GUI patterns and transformation capabilities.
    """
    
    # Signals
    egi_loaded = Signal(RelationalGraphWithCuts)
    selection_changed = Signal(list)  # List of selected element IDs
    transformation_applied = Signal(str, TransformationResult)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Core components
        self.engine = UniversalEGIEngine()
        self.viewport_renderer = ViewportRenderer(self.engine)
        
        # Current state
        self.current_egi: Optional[RelationalGraphWithCuts] = None
        self.current_mode = InteractionMode.ORGANON
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left panel - Controls
        control_panel = self._create_control_panel()
        main_splitter.addWidget(control_panel)
        
        # Center - Graphics view
        self.scene = QGraphicsScene()
        # Set reasonable initial scene bounds to prevent extreme bounding rectangles
        self.scene.setSceneRect(-500, -500, 1000, 1000)
        self.graphics_view = InteractiveGraphicsView(self.scene)
        main_splitter.addWidget(self.graphics_view)
        
        # Right panel - Information
        info_panel = self._create_info_panel()
        main_splitter.addWidget(info_panel)
        
        # Set splitter proportions - give much more space to the canvas
        main_splitter.setSizes([250, 800, 300])  # More reasonable proportions
        
        # Make splitter resizable and set minimum sizes
        main_splitter.setChildrenCollapsible(False)
        control_panel.setMinimumWidth(200)
        control_panel.setMaximumWidth(300)
        info_panel.setMinimumWidth(250)
        info_panel.setMaximumWidth(400)
        
    def _create_control_panel(self) -> QWidget:
        """Create control panel with style and interaction options."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Style selection
        style_group = QGroupBox("Visual Style")
        style_layout = QVBoxLayout(style_group)
        
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "Dau Compliant",
            "Peirce Authentic", 
            "Peirce LaTeX-Inspired",
            "Peirce Handwritten"
        ])
        style_layout.addWidget(self.style_combo)
        
        layout.addWidget(style_group)
        
        # Interaction mode
        mode_group = QGroupBox("Interaction Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Organon", "Ergasterion", "Agon"])
        mode_layout.addWidget(self.mode_combo)
        
        layout.addWidget(mode_group)
        
        # Rendering options
        render_group = QGroupBox("Rendering")
        render_layout = QVBoxLayout(render_group)
        
        self.show_debug = QCheckBox("Show Debug Info")
        render_layout.addWidget(self.show_debug)
        
        self.auto_fit = QCheckBox("Auto Fit View")
        self.auto_fit.setChecked(False)  # Disable by default for better manual control
        render_layout.addWidget(self.auto_fit)
        
        # Detail level slider
        detail_label = QLabel("Detail Level:")
        render_layout.addWidget(detail_label)
        
        self.detail_slider = QSlider(Qt.Orientation.Horizontal)
        self.detail_slider.setRange(0, 3)
        self.detail_slider.setValue(1)  # Medium detail
        self.detail_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        render_layout.addWidget(self.detail_slider)
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        self.zoom_reset_btn = QPushButton("Reset Zoom")
        self.fit_view_btn = QPushButton("Fit to View")
        zoom_layout.addWidget(self.zoom_reset_btn)
        zoom_layout.addWidget(self.fit_view_btn)
        render_layout.addLayout(zoom_layout)
        
        layout.addWidget(render_group)
        
        # Corpus selection - make it more compact
        corpus_label = QLabel("Corpus Examples:")
        layout.addWidget(corpus_label)
        
        self.corpus_combo = QComboBox()
        self.corpus_combo.addItem("Select from corpus...", "")
        layout.addWidget(self.corpus_combo)
        
        # Load corpus examples
        self._populate_corpus_examples()
        
        # Load buttons
        button_layout = QHBoxLayout()
        
        self.load_simple_btn = QPushButton("Load Simple Example")
        self.load_complex_btn = QPushButton("Load Complex Example")
        self.load_peirce_btn = QPushButton("Load Peirce Example")
        self.test_styles_btn = QPushButton("Test All Styles")
        
        button_layout.addWidget(self.load_simple_btn)
        button_layout.addWidget(self.load_complex_btn)
        button_layout.addWidget(self.load_peirce_btn)
        button_layout.addWidget(self.test_styles_btn)
        
        layout.addLayout(button_layout)
        
        # Transformation controls
        transform_group = QGroupBox("Transformations")
        transform_layout = QVBoxLayout(transform_group)
        
        self.available_transforms = QComboBox()
        self.available_transforms.setEnabled(False)
        transform_layout.addWidget(self.available_transforms)
        
        self.apply_transform_btn = QPushButton("Apply Transformation")
        self.apply_transform_btn.setEnabled(False)
        transform_layout.addWidget(self.apply_transform_btn)
        
        layout.addWidget(transform_group)
        
        # Export controls
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        
        self.export_svg_btn = QPushButton("Export as SVG")
        export_layout.addWidget(self.export_svg_btn)
        
        self.export_png_btn = QPushButton("Export as PNG")
        export_layout.addWidget(self.export_png_btn)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        return panel
        
    def _create_info_panel(self) -> QWidget:
        """Create information panel showing selection and validation details."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # EGI information
        egi_group = QGroupBox("EGI Information")
        egi_layout = QVBoxLayout(egi_group)
        
        self.egi_info_label = QLabel("No EGI loaded")
        egi_layout.addWidget(self.egi_info_label)
        
        layout.addWidget(egi_group)
        
        # Linear forms display - Enhanced Organon display
        linear_group = QGroupBox("Linear Forms (EGIF, CGIF, CLIF, FOPL)")
        linear_layout = QVBoxLayout(linear_group)
        
        # Format selector
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["All Formats", "EGIF", "CGIF", "CLIF", "FOPL"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        linear_layout.addLayout(format_layout)
        
        self.linear_form_text = QTextEdit()
        self.linear_form_text.setReadOnly(True)
        self.linear_form_text.setMaximumHeight(300)  # Increased for all formats
        self.linear_form_text.setPlainText("No EGI loaded")
        self.linear_form_text.setFont(self.linear_form_text.font())  # Use monospace
        linear_layout.addWidget(self.linear_form_text)
        
        layout.addWidget(linear_group)
        
        # Selection information
        selection_group = QGroupBox("Current Selection")
        selection_layout = QVBoxLayout(selection_group)
        
        self.selection_info = QTextEdit()
        self.selection_info.setMaximumHeight(100)
        self.selection_info.setReadOnly(True)
        selection_layout.addWidget(self.selection_info)
        
        layout.addWidget(selection_group)
        
        # Validation messages
        validation_group = QGroupBox("Validation")
        validation_layout = QVBoxLayout(validation_group)
        
        self.validation_info = QTextEdit()
        self.validation_info.setMaximumHeight(100)
        self.validation_info.setReadOnly(True)
        validation_layout.addWidget(self.validation_info)
        
        layout.addWidget(validation_group)
        
        layout.addStretch()
        return panel
        
    def _connect_signals(self):
        """Connect widget signals."""
        # Style changes
        self.style_combo.currentTextChanged.connect(self._on_style_changed)
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        # Format changes
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        
        # Rendering options
        self.show_debug.toggled.connect(self._on_debug_toggled)
        self.detail_slider.valueChanged.connect(self._on_detail_changed)
        
        # Zoom controls
        self.zoom_reset_btn.clicked.connect(self._on_zoom_reset)
        self.fit_view_btn.clicked.connect(self._on_fit_to_view)
        
        # Corpus selection
        self.corpus_combo.currentTextChanged.connect(self._on_corpus_selection)
        
        # Graphics view
        self.graphics_view.viewport_changed.connect(self._on_viewport_changed)
        self.graphics_view.mouse_pressed.connect(self._on_mouse_pressed)
        self.graphics_view.mouse_dragged.connect(self._on_mouse_dragged)
        
        # Viewport renderer
        self.viewport_renderer.element_selected.connect(self._on_element_selected)
        self.viewport_renderer.interaction_state_changed.connect(self._on_interaction_changed)
        
        # Transformation
        self.apply_transform_btn.clicked.connect(self._on_apply_transformation)
        
        # Export
        self.export_svg_btn.clicked.connect(lambda: self._export_viewport("svg"))
        self.export_png_btn.clicked.connect(lambda: self._export_viewport("png"))
        
    def load_egi(self, egi: RelationalGraphWithCuts):
        """Load an EGI for interactive viewing."""
        self.current_egi = egi
        
        # Get current style
        style_name = self.style_combo.currentText()
        style = self._get_style_by_name(style_name)
        
        # Set up viewport renderer
        self.viewport_renderer.set_egi(egi, style)
        
        # Initial render
        self._refresh_view()
        
        # Update info panel
        self._update_egi_info()
        
        # Auto-fit if enabled
        if self.auto_fit.isChecked():
            self.graphics_view.fitInView(
                self.scene.itemsBoundingRect(),
                Qt.AspectRatioMode.KeepAspectRatio
            )
            
        self.egi_loaded.emit(egi)
        
    def _refresh_view(self):
        """Refresh the current view."""
        if self.current_egi:
            self.viewport_renderer.render_to_scene(self.scene)
            
            # Ensure scene has proper bounds and fit view
            if self.scene.items():
                scene_rect = self.scene.itemsBoundingRect()
                if not scene_rect.isEmpty():
                    # Add some padding around the items
                    padding = 50
                    scene_rect = scene_rect.adjusted(-padding, -padding, padding, padding)
                    
                    # Ensure reasonable bounds (prevent extreme rectangles)
                    max_size = 5000  # Maximum scene dimension
                    if scene_rect.width() > max_size or scene_rect.height() > max_size:
                        # Clamp to reasonable size
                        center = scene_rect.center()
                        clamped_rect = QRectF(
                            center.x() - max_size/2, center.y() - max_size/2,
                            max_size, max_size
                        )
                        self.scene.setSceneRect(clamped_rect)
                        print(f"DEBUG: Clamped scene rect from {scene_rect} to {clamped_rect}")
                    else:
                        self.scene.setSceneRect(scene_rect)
                    
                    # Auto-fit if enabled
                    if self.auto_fit.isChecked():
                        self.graphics_view.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)
                else:
                    # No items or empty bounds - set a default scene
                    self.scene.setSceneRect(-200, -200, 400, 400)
            else:
                # No items - set a default scene
                self.scene.setSceneRect(-200, -200, 400, 400)
            
    def _get_style_by_name(self, name: str):
        """Get style instance by name."""
        style_map = {
            "Dau Compliant": "dau_compliant",
            "Peirce Authentic": "peirce_authentic", 
            "Peirce LaTeX-Inspired": "peirce_latex_inspired",
            "Peirce Handwritten": "peirce_handwritten"
        }
        
        style_id = style_map.get(name, "dau_compliant")
        print(f"DEBUG: Getting style for name='{name}', style_id='{style_id}'")
        
        style = STYLE_MANAGER.get_style(style_id)
        print(f"DEBUG: Style manager returned: {style is not None}")
        
        if style is None:
            print(f"DEBUG: Available styles: {list(STYLE_MANAGER.available_styles.keys())}")
            # Fallback to simple style system
            from gui.simple_style_system import get_simple_style
            style = get_simple_style("default")
            print(f"DEBUG: Using fallback simple style: {style is not None}")
        
        return style
        
    def _on_style_changed(self, style_name: str):
        """Handle style change."""
        if self.current_egi:
            style = self._get_style_by_name(style_name)
            self.viewport_renderer.set_egi(self.current_egi, style)
            self._refresh_view()
            
    def _on_mode_changed(self, mode_name: str):
        """Handle interaction mode change."""
        mode_map = {
            "Organon": InteractionMode.ORGANON,
            "Ergasterion": InteractionMode.ERGASTERION,
            "Agon": InteractionMode.AGON
        }
        self.current_mode = mode_map.get(mode_name, InteractionMode.ORGANON)
        
    def _on_debug_toggled(self, enabled: bool):
        """Handle debug mode toggle."""
        # Update rendering to show/hide debug information
        self._refresh_view()
        
    def _on_detail_changed(self, level: int):
        """Handle detail level change."""
        detail_levels = [
            RenderingLevel.OVERVIEW,
            RenderingLevel.MEDIUM,
            RenderingLevel.DETAILED,
            RenderingLevel.MICROSCOPIC
        ]
        
        # Update viewport renderer detail level
        # This would require extending the viewport renderer API
        self._refresh_view()
        
    def _on_viewport_changed(self, center: QPointF, zoom: float, visible_rect: QRectF):
        """Handle viewport change from graphics view."""
        self.viewport_renderer.set_viewport(center, zoom, visible_rect)
        self._refresh_view()
        
    def _on_mouse_pressed(self, position: QPointF, modifiers: Qt.KeyboardModifiers):
        """Handle mouse press in graphics view."""
        self.viewport_renderer.handle_mouse_event("press", position, modifiers)
        
    def _on_mouse_dragged(self, start: QPointF, current: QPointF):
        """Handle mouse drag in graphics view."""
        self.viewport_renderer.handle_mouse_event("drag", current, Qt.KeyboardModifier.NoModifier)
        
    def _on_element_selected(self, element_id: str):
        """Handle element selection."""
        # Update available transformations
        available = self.viewport_renderer.get_available_transformations()
        
        self.available_transforms.clear()
        self.available_transforms.addItems(available)
        self.available_transforms.setEnabled(len(available) > 0)
        self.apply_transform_btn.setEnabled(len(available) > 0)
        
        # Update selection info
        self._update_selection_info([element_id])
        
    def _on_interaction_changed(self, state: str):
        """Handle interaction state change."""
        # Update UI based on interaction state
        pass
        
    def _on_apply_transformation(self):
        """Apply selected transformation."""
        rule_name = self.available_transforms.currentText()
        if rule_name:
            self.viewport_renderer.apply_transformation(rule_name)
            
    def _export_viewport(self, format: str):
        """Export current viewport."""
        # Implementation would use viewport_renderer.export_viewport()
        pass
        
    def _update_egi_info(self):
        """Update EGI information display."""
        if self.current_egi:
            vertex_count = len(self.current_egi.V)
            edge_count = len(self.current_egi.E)
            cut_count = len(self.current_egi.Cut)
            
            info_text = f"""
            Vertices: {vertex_count}
            Edges: {edge_count}
            Cuts: {cut_count}
            Mode: {self.current_mode.value}
            """
            
            self.egi_info_label.setText(info_text.strip())
            
            # Update linear form display
            self._update_linear_form()
        else:
            # No items - set a default scene
            self.scene.setSceneRect(-200, -200, 400, 400)
            
    def _get_style_by_name(self, name: str):
        """Get style instance by name."""
        style_map = {
            "Dau Compliant": "dau_compliant",
            "Peirce Authentic": "peirce_authentic", 
            "Peirce LaTeX-Inspired": "peirce_latex_inspired",
            "Peirce Handwritten": "peirce_handwritten"
        }
            
        style_id = style_map.get(name, "dau_compliant")
        print(f"DEBUG: Getting style for name='{name}', style_id='{style_id}'")
            
        style = STYLE_MANAGER.get_style(style_id)
        print(f"DEBUG: Style manager returned: {style is not None}")
            
        if style is None:
            print(f"DEBUG: Available styles: {list(STYLE_MANAGER.available_styles.keys())}")
            # Fallback to simple style system
            from gui.simple_style_system import get_simple_style
            style = get_simple_style("default")
            print(f"DEBUG: Using fallback simple style: {style is not None}")
            
        return style
        
    def _update_egi_info(self):
        """Update EGI information display."""
        if self.current_egi:
            vertex_count = len(self.current_egi.V)
            edge_count = len(self.current_egi.E)
            cut_count = len(self.current_egi.Cut)
                
            info_text = f"""
            Vertices: {vertex_count}
            Edges: {edge_count}
            Cuts: {cut_count}
            Mode: {self.current_mode.value}
            """
                
            self.egi_info_label.setText(info_text.strip())
                
            # Update linear form display
            self._update_linear_form()
        else:
            self.egi_info_label.setText("No EGI loaded")
            self.linear_form_text.setPlainText("No EGI loaded")
    
    def _update_linear_form(self):
        """Update linear form display with all formats (EGIF, CGIF, CLIF, FOPL)."""
        if self.current_egi:
            try:
                # Get the selected format
                selected_format = self.format_combo.currentText()
                    
                if selected_format == "All Formats" or not selected_format:
                    # Generate all formats
                    egif_text = self.viewport_renderer.engine._egi_to_egif(self.current_egi)
                    cgif_text = self.viewport_renderer.engine._egi_to_cgif(self.current_egi)
                    clif_text = self.viewport_renderer.engine._egi_to_clif(self.current_egi)
                    fopl_text = self.viewport_renderer.engine._egi_to_fopl(self.current_egi)
                        
                    combined_text = f"""═══════════════════════════════════════════════════════════════
EGIF (Existential Graph Interchange Format)
═══════════════════════════════════════════════════════════════
{egif_text}

═══════════════════════════════════════════════════════════════
CGIF (Conceptual Graph Interchange Format)
═══════════════════════════════════════════════════════════════
{cgif_text}

═══════════════════════════════════════════════════════════════
CLIF (Common Logic Interchange Format)
═══════════════════════════════════════════════════════════════
{clif_text}

═══════════════════════════════════════════════════════════════
FOPL (First-Order Predicate Logic)
═══════════════════════════════════════════════════════════════
{fopl_text}"""
                    self.linear_form_text.setPlainText(combined_text)
                        
                elif selected_format == "EGIF":
                    egif_text = self.viewport_renderer.engine._egi_to_egif(self.current_egi)
                    self.linear_form_text.setPlainText(egif_text)
                        
                elif selected_format == "CGIF":
                    cgif_text = self.viewport_renderer.engine._egi_to_cgif(self.current_egi)
                    self.linear_form_text.setPlainText(cgif_text)
                        
                elif selected_format == "CLIF":
                    clif_text = self.viewport_renderer.engine._egi_to_clif(self.current_egi)
                    self.linear_form_text.setPlainText(clif_text)
                        
                elif selected_format == "FOPL":
                    fopl_text = self.viewport_renderer.engine._egi_to_fopl(self.current_egi)
                    self.linear_form_text.setPlainText(fopl_text)
                        
            except Exception as e:
                self.linear_form_text.setPlainText(f"Error generating linear form: {e}")
        else:
            self.linear_form_text.setPlainText("No EGI loaded")
    
    def _on_format_changed(self, format_name: str):
        """Handle format selection change."""
        self._update_linear_form()
    
    def _on_zoom_reset(self):
        """Reset zoom to 100%."""
        self.graphics_view.resetTransform()
        self.graphics_view._emit_viewport_change()
    
    def _on_fit_to_view(self):
        """Fit the entire diagram to the view."""
        if self.scene.items():
            # Get the bounding rect of all items
            scene_rect = self.scene.itemsBoundingRect()
            if not scene_rect.isEmpty():
                # Add generous margin for better visibility
                margin = 100
                scene_rect = scene_rect.adjusted(-margin, -margin, margin, margin)
                
                # Update scene rect to match content
                self.scene.setSceneRect(scene_rect)
                
                # Fit the view to this rect
                self.graphics_view.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)
                self.graphics_view._emit_viewport_change()
                
                print(f"DEBUG: Fit to view - scene rect: {scene_rect}")
        else:
            # No items - fit to default scene
            default_rect = QRectF(-200, -200, 400, 400)
            self.scene.setSceneRect(default_rect)
            self.graphics_view.fitInView(default_rect, Qt.AspectRatioMode.KeepAspectRatio)
            print("DEBUG: Fit to view - using default rect")
    
    def _populate_corpus_examples(self):
        """Populate the corpus selection dropdown with available examples."""
        import os
        corpus_path = "corpus/graphs"
        
        if os.path.exists(corpus_path):
            try:
                # Get all directories in the corpus
                examples = []
                for item in os.listdir(corpus_path):
                    item_path = os.path.join(corpus_path, item)
                    if os.path.isdir(item_path):
                        # Look for .egi.json file
                        egi_file = os.path.join(item_path, f"{item}.egi.json")
                        if os.path.exists(egi_file):
                            # Create a nice display name
                            display_name = item.replace('_', ' ').title()
                            examples.append((display_name, egi_file))
                
                # Sort examples by display name
                examples.sort(key=lambda x: x[0])
                
                # Add to combo box
                for display_name, file_path in examples:
                    self.corpus_combo.addItem(display_name, file_path)
                    
            except Exception as e:
                print(f"Error loading corpus examples: {e}")
    
    def _on_corpus_selection(self, display_name: str):
        """Handle corpus example selection."""
        if display_name and display_name != "Select from corpus...":
            file_path = self.corpus_combo.currentData()
            if file_path:
                try:
                    from egi_loader import load_egi_from_json
                    egi = load_egi_from_json(file_path)
                    self.load_egi(egi)
                    
                    # Update status
                    import os
                    example_name = os.path.basename(os.path.dirname(file_path))
                    self.status_label.setText(f"{example_name} loaded from corpus")
                    
                except Exception as e:
                    self.status_label.setText(f"Error loading {display_name}: {e}")
                    print(f"Error loading corpus example: {e}")
            
    def _update_selection_info(self, selected_elements: List[str]):
        """Update selection information display."""
        if selected_elements:
            info_text = f"Selected: {len(selected_elements)} elements\n"
            info_text += "\n".join(selected_elements[:5])  # Show first 5
            if len(selected_elements) > 5:
                info_text += f"\n... and {len(selected_elements) - 5} more"
        else:
            info_text = "No elements selected"
            
        self.selection_info.setText(info_text)
        self.selection_changed.emit(selected_elements)
