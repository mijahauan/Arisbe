"""
EG-HG Graph Canvas Widget

Interactive canvas for displaying and manipulating existential graphs.
Integrates directly with the EG-HG system data structures.
"""

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsLineItem,
    QGraphicsTextItem, QMenu
)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter
from PySide6.QtSvg import QSvgGenerator

# Import existing EG-HG types
try:
    from eg_types import EGGraph, Context, Node, Edge, Ligature
    EG_SYSTEM_AVAILABLE = True
except ImportError:
    EG_SYSTEM_AVAILABLE = False


class GraphCanvas(QGraphicsView):
    """Interactive canvas for existential graph visualization"""
    
    # Signals
    graph_changed = Signal(object)  # EGGraph
    selection_changed = Signal(list)  # List of selected items
    item_double_clicked = Signal(object)  # Graph item
    context_menu_requested = Signal(QPointF, object)  # Position, item
    
    def __init__(self):
        super().__init__()
        
        # Create graphics scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Current graph
        self.current_graph = None
        self.graph_items = {}  # Map from graph objects to graphics items
        
        # Configure view
        self.setup_view()
        
        # Create sample graph for demonstration
        self.create_sample_graph()
        
    def setup_view(self):
        """Configure the graphics view"""
        # Enable drag mode for selection
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Enable antialiasing for smooth rendering
        self.setRenderHint(QPainter.Antialiasing)
        
        # Set background
        self.setBackgroundBrush(QBrush(QColor(248, 248, 248)))
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
        # Set scene rect
        self.scene.setSceneRect(-500, -400, 1000, 800)
        
    def set_graph(self, graph):
        """Set the current graph and render it"""
        self.current_graph = graph
        self.render_graph()
        self.graph_changed.emit(graph)
        
    def render_graph(self):
        """Render the current graph to graphics items"""
        # Clear existing items
        self.scene.clear()
        self.graph_items.clear()
        
        if not self.current_graph:
            return
            
        if EG_SYSTEM_AVAILABLE:
            self._render_eg_graph()
        else:
            self._render_sample_graph()
            
    def _render_eg_graph(self):
        """Render actual EGGraph object"""
        # TODO: Implement rendering of actual EGGraph
        # This will use the real data structures from your existing system
        
        # Render contexts (cuts)
        for context in self.current_graph.context_manager.contexts:
            self._render_context(context)
            
        # Render nodes
        for node in self.current_graph.nodes:
            self._render_node(node)
            
        # Render edges
        for edge in self.current_graph.edges:
            self._render_edge(edge)
            
        # Render ligatures
        for ligature in self.current_graph.ligatures:
            self._render_ligature(ligature)
            
    def _render_sample_graph(self):
        """Render sample graph for demonstration"""
        self.create_sample_graph()
        
    def create_sample_graph(self):
        """Create a sample existential graph for demonstration"""
        # Sheet of Assertion (root context)
        sheet_rect = QGraphicsRectItem(-300, -200, 600, 400)
        sheet_rect.setPen(QPen(QColor(100, 100, 100), 2))
        sheet_rect.setBrush(QBrush(QColor(250, 250, 250, 100)))
        self.scene.addItem(sheet_rect)
        
        # Sheet label
        sheet_label = QGraphicsTextItem("Sheet of Assertion")
        sheet_label.setPos(-80, -190)
        sheet_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.scene.addItem(sheet_label)
        
        # Context (cut) - represents negation
        context_ellipse = QGraphicsEllipseItem(-150, -100, 300, 150)
        context_ellipse.setPen(QPen(QColor(200, 100, 100), 3))
        context_ellipse.setBrush(QBrush(QColor(255, 200, 200, 50)))
        self.scene.addItem(context_ellipse)
        
        # Context label
        context_label = QGraphicsTextItem("¬")
        context_label.setPos(-10, -90)
        context_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.scene.addItem(context_label)
        
        # Nodes (predicates)
        node1 = QGraphicsEllipseItem(-120, -50, 60, 40)
        node1.setPen(QPen(QColor(100, 150, 200), 2))
        node1.setBrush(QBrush(QColor(150, 200, 255)))
        self.scene.addItem(node1)
        
        node1_label = QGraphicsTextItem("Person")
        node1_label.setPos(-110, -40)
        node1_label.setFont(QFont("Arial", 10))
        self.scene.addItem(node1_label)
        
        node2 = QGraphicsEllipseItem(60, -50, 60, 40)
        node2.setPen(QPen(QColor(100, 150, 200), 2))
        node2.setBrush(QBrush(QColor(150, 200, 255)))
        self.scene.addItem(node2)
        
        node2_label = QGraphicsTextItem("Mortal")
        node2_label.setPos(70, -40)
        node2_label.setFont(QFont("Arial", 10))
        self.scene.addItem(node2_label)
        
        # Ligature (line of identity)
        ligature = QGraphicsLineItem(-60, -30, 60, -30)
        ligature.setPen(QPen(QColor(150, 100, 150), 4))
        self.scene.addItem(ligature)
        
        # Variable label on ligature
        var_label = QGraphicsTextItem("x")
        var_label.setPos(-5, -45)
        var_label.setFont(QFont("Arial", 10, QFont.Italic))
        self.scene.addItem(var_label)
        
        # Add interpretation text
        interpretation = QGraphicsTextItem("Graph reads: ¬(Person(x) ∧ Mortal(x))")
        interpretation.setPos(-150, 120)
        interpretation.setFont(QFont("Arial", 10, QFont.Italic))
        self.scene.addItem(interpretation)
        
        meaning = QGraphicsTextItem("Meaning: It is not the case that something is both a person and mortal")
        meaning.setPos(-200, 140)
        meaning.setFont(QFont("Arial", 9))
        self.scene.addItem(meaning)
        
    def _render_context(self, context):
        """Render a context (cut) from the EG system"""
        # TODO: Implement actual context rendering
        # This will use the real Context object properties
        pass
        
    def _render_node(self, node):
        """Render a node from the EG system"""
        # TODO: Implement actual node rendering
        # This will use the real Node object properties
        pass
        
    def _render_edge(self, edge):
        """Render an edge from the EG system"""
        # TODO: Implement actual edge rendering
        # This will use the real Edge object properties
        pass
        
    def _render_ligature(self, ligature):
        """Render a ligature from the EG system"""
        # TODO: Implement actual ligature rendering
        # This will use the real Ligature object properties
        pass
        
    # View operations
    def zoom_in(self):
        """Zoom in on the graph"""
        self.scale(1.2, 1.2)
        
    def zoom_out(self):
        """Zoom out from the graph"""
        self.scale(0.8, 0.8)
        
    def zoom_fit(self):
        """Fit the graph to the view"""
        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.resetTransform()
        
    # Export operations
    def export_svg(self, file_path):
        """Export the graph as SVG"""
        generator = QSvgGenerator()
        generator.setFileName(file_path)
        generator.setSize(self.scene.sceneRect().size().toSize())
        generator.setViewBox(self.scene.sceneRect())
        generator.setTitle("EG-HG Existential Graph")
        generator.setDescription("Exported from EG-HG Desktop Application")
        
        painter = QPainter()
        painter.begin(generator)
        self.scene.render(painter)
        painter.end()
        
    def export_png(self, file_path):
        """Export the graph as PNG"""
        from PySide6.QtGui import QPixmap
        
        # Create pixmap
        rect = self.scene.itemsBoundingRect()
        pixmap = QPixmap(rect.size().toSize())
        pixmap.fill(Qt.white)
        
        # Render scene to pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        self.scene.render(painter, QRectF(), rect)
        painter.end()
        
        # Save pixmap
        pixmap.save(file_path, "PNG")
        
    # Event handlers
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        # Zoom with Ctrl+wheel
        if event.modifiers() & Qt.ControlModifier:
            zoom_factor = 1.15
            if event.angleDelta().y() < 0:
                zoom_factor = 1.0 / zoom_factor
            self.scale(zoom_factor, zoom_factor)
        else:
            # Default scroll behavior
            super().wheelEvent(event)
            
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.RightButton:
            # Right click - show context menu
            scene_pos = self.mapToScene(event.pos())
            item = self.scene.itemAt(scene_pos, self.transform())
            self.show_context_menu(event.globalPos(), item)
        else:
            super().mousePressEvent(event)
            
    def mouseDoubleClickEvent(self, event):
        """Handle double click events"""
        scene_pos = self.mapToScene(event.pos())
        item = self.scene.itemAt(scene_pos, self.transform())
        if item:
            self.item_double_clicked.emit(item)
        super().mouseDoubleClickEvent(event)
        
    def show_context_menu(self, global_pos, item):
        """Show context menu for graph operations"""
        menu = QMenu(self)
        
        if item:
            # Item-specific actions
            menu.addAction("Edit Properties", lambda: self.edit_item_properties(item))
            menu.addAction("Delete", lambda: self.delete_item(item))
            menu.addSeparator()
            
        # General actions
        menu.addAction("Add Context", lambda: self.add_context(global_pos))
        menu.addAction("Add Node", lambda: self.add_node(global_pos))
        menu.addSeparator()
        menu.addAction("Zoom In", self.zoom_in)
        menu.addAction("Zoom Out", self.zoom_out)
        menu.addAction("Fit to View", self.zoom_fit)
        
        menu.exec(global_pos)
        
    def edit_item_properties(self, item):
        """Edit properties of a graph item"""
        # TODO: Open properties dialog
        pass
        
    def delete_item(self, item):
        """Delete a graph item"""
        # TODO: Remove from graph and scene
        self.scene.removeItem(item)
        
    def add_context(self, global_pos):
        """Add a new context at the specified position"""
        # TODO: Add context to graph
        scene_pos = self.mapToScene(self.mapFromGlobal(global_pos))
        context = QGraphicsEllipseItem(scene_pos.x() - 50, scene_pos.y() - 25, 100, 50)
        context.setPen(QPen(QColor(200, 100, 100), 2))
        context.setBrush(QBrush(QColor(255, 200, 200, 50)))
        self.scene.addItem(context)
        
    def add_node(self, global_pos):
        """Add a new node at the specified position"""
        # TODO: Add node to graph
        scene_pos = self.mapToScene(self.mapFromGlobal(global_pos))
        node = QGraphicsEllipseItem(scene_pos.x() - 20, scene_pos.y() - 15, 40, 30)
        node.setPen(QPen(QColor(100, 150, 200), 2))
        node.setBrush(QBrush(QColor(150, 200, 255)))
        self.scene.addItem(node)

