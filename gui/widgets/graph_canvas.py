"""
EG-HG Graph Canvas Widget

Interactive canvas for displaying and manipulating existential graphs
with support for CLIF-generated baseline layouts and constrained editing.
"""

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsLineItem,
    QGraphicsTextItem, QMenu, QGraphicsItemGroup
)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter
from PySide6.QtSvg import QSvgGenerator

# Import existing EG system
try:
    from graph import EGGraph
    from eg_types import Context, Node, Edge, Ligature
    EG_SYSTEM_AVAILABLE = True
except ImportError:
    EG_SYSTEM_AVAILABLE = False


class GraphicsContext(QGraphicsEllipseItem):
    """Graphics item representing an existential graph context (cut)"""
    
    def __init__(self, x, y, width, height, context_data=None):
        super().__init__(x, y, width, height)
        self.context_data = context_data
        
        # Visual styling
        self.setPen(QPen(QColor(200, 100, 100), 3))
        self.setBrush(QBrush(QColor(255, 200, 200, 50)))
        
        # Make movable but constrained
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
    def itemChange(self, change, value):
        """Handle item changes with logical constraints"""
        if change == QGraphicsItem.ItemPositionChange:
            # TODO: Implement logical constraints for context movement
            pass
        return super().itemChange(change, value)


class GraphicsNode(QGraphicsRectItem):
    """Graphics item representing a predicate node"""
    
    def __init__(self, x, y, width, height, node_data=None):
        super().__init__(x, y, width, height)
        self.node_data = node_data
        
        # Visual styling for predicates - rectangular with transparent border
        self.setPen(QPen(QColor(100, 150, 200), 1))  # Thin blue border
        self.setBrush(QBrush(QColor(150, 200, 255, 200)))  # Semi-transparent blue fill
        
        # Make movable with constraints
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Add text label
        if node_data and 'name' in node_data:
            self.label = QGraphicsTextItem(node_data['name'])
            self.label.setParentItem(self)
            
            # Center the text in the rectangle
            text_rect = self.label.boundingRect()
            self.label.setPos(
                (width - text_rect.width()) / 2,
                (height - text_rect.height()) / 2
            )
            
            self.label.setFont(QFont("Arial", 10))
            self.label.setDefaultTextColor(QColor(50, 50, 50))
            
    def itemChange(self, change, value):
        """Handle item changes with constraint validation"""
        if change == QGraphicsItem.ItemPositionChange:
            # Validate position change
            try:
                from gui.widgets.constraint_validator import EGConstraintValidator
                validator = EGConstraintValidator()
                
                if not validator.validate_node_move(self, value):
                    # Flash red to indicate invalid move
                    self.flash_invalid()
                    return self.pos()  # Return current position (don't move)
            except ImportError:
                pass
        return super().itemChange(change, value)
        
    def flash_invalid(self):
        """Flash red to indicate invalid move"""
        original_brush = self.brush()
        self.setBrush(QBrush(QColor(255, 100, 100, 150)))
        
        # Reset color after a short delay
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.singleShot(500, lambda: self.setBrush(original_brush))


class GraphicsLigature(QGraphicsLineItem):
    """Graphics item representing a line of identity"""
    
    def __init__(self, x1, y1, x2, y2, ligature_data=None):
        super().__init__(x1, y1, x2, y2)
        self.ligature_data = ligature_data
        self.variable_name = None
        self.hover_label = None
        
        # Visual styling for line of identity
        self.setPen(QPen(QColor(50, 50, 50), 4))  # Thick black line
        
        # Make selectable and movable
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setAcceptHoverEvents(True)
        
    def hoverEnterEvent(self, event):
        """Show variable name on hover"""
        if self.variable_name and hasattr(self, 'scene') and self.scene():
            # Create hover label
            self.hover_label = QGraphicsTextItem(f"Variable: {self.variable_name}")
            self.hover_label.setFont(QFont("Arial", 10))
            self.hover_label.setDefaultTextColor(QColor(100, 100, 100))
            
            # Position near the ligature
            line = self.line()
            mid_x = (line.x1() + line.x2()) / 2
            mid_y = (line.y1() + line.y2()) / 2
            self.hover_label.setPos(mid_x - 30, mid_y - 25)
            
            # Add to scene
            self.scene().addItem(self.hover_label)
            
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Hide variable name when hover ends"""
        if self.hover_label and hasattr(self, 'scene') and self.scene():
            self.scene().removeItem(self.hover_label)
            self.hover_label = None
            
        super().hoverLeaveEvent(event)


class GraphicsContext(QGraphicsEllipseItem):
    """Graphics item representing a context (cut)"""
    
    def __init__(self, x, y, width, height, context_data=None):
        super().__init__(x, y, width, height)
        self.context_data = context_data
        
        # Visual styling for cuts
        self.setPen(QPen(QColor(150, 100, 150), 2))
        self.setBrush(QBrush(QColor(200, 150, 200, 30)))
        
        # Make movable with constraints
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)


class GraphCanvas(QGraphicsView):
    """Main canvas for displaying and editing existential graphs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_canvas()
        self.current_graph = None
        self.graph_items = {}
        
    def setup_canvas(self):
        """Setup the graphics scene and view"""
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Configure view
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Set background
        self.setBackgroundBrush(QBrush(QColor(250, 250, 250)))
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def show_context_menu(self, position):
        """Show context menu for canvas operations"""
        # This method would be implemented to show the right-click menu
        pass
        
    def set_graph(self, graph):
        """Set the current graph and render it"""
        self.current_graph = graph
        self.clear_graph()
        if graph:
            self.render_graph()
            
    def clear_graph(self):
        """Clear all graph items from the scene"""
        self.scene.clear()
        self.graph_items.clear()
        
    def render_graph(self):
        """Render the current graph"""
        if not self.current_graph:
            return
            
        # This would render the graph using the corrected architecture
        # For now, just a placeholder
        pass
        
    def check_logical_constraints(self, new_pos, contexts):
        """Check if the new position violates logical constraints"""
        # For now, implement basic constraint: nodes must stay within their quantifier scope
        
        # If this node has variables, it must stay within contexts that bind those variables
        if self.node_data and isinstance(self.node_data, dict):
            node_vars = self.node_data.get('args', [])
            
            # Check if the new position is within at least one appropriate context
            for context in contexts:
                context_rect = context.boundingRect()
                context_pos = context.pos()
                
                # Transform to scene coordinates
                scene_rect = QRectF(
                    context_pos.x() + context_rect.x(),
                    context_pos.y() + context_rect.y(),
                    context_rect.width(),
                    context_rect.height()
                )
                
                # Check if new position is within this context
                node_rect = self.boundingRect()
                new_scene_pos = QPointF(new_pos.x() + node_rect.width()/2, 
                                       new_pos.y() + node_rect.height()/2)
                
                if scene_rect.contains(new_scene_pos):
                    # Position is within a context, check if it's appropriate
                    # For existential contexts, nodes with bound variables must stay inside
                    return True
                    
            # If we have variables but aren't in any context, that might be invalid
            if node_vars:
                # Show constraint violation feedback
                self.show_constraint_violation()
                return False
                
        return True  # Allow move if no specific constraints apply
        
    def show_constraint_violation(self):
        """Show visual feedback for constraint violation"""
        # Briefly change color to indicate constraint violation
        original_brush = self.brush()
        self.setBrush(QBrush(QColor(255, 100, 100)))  # Red
        
        # Reset color after a short delay (this is a simple approach)
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.singleShot(500, lambda: self.setBrush(original_brush))
class GraphicsLigature(QGraphicsLineItem):
    """Graphics item representing a line of identity"""
    
    def __init__(self, x1, y1, x2, y2, ligature_data=None):
        super().__init__(x1, y1, x2, y2)
        self.ligature_data = ligature_data
        self.variable_name = None
        self.hover_label = None
        
        # Visual styling for line of identity
        self.setPen(QPen(QColor(50, 50, 50), 4))  # Thick black line
        
        # Make selectable and movable
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setAcceptHoverEvents(True)
        
    def hoverEnterEvent(self, event):
        """Show variable name on hover"""
        if self.variable_name and hasattr(self, 'scene') and self.scene():
            # Create hover label
            self.hover_label = QGraphicsTextItem(f"Variable: {self.variable_name}")
            self.hover_label.setFont(QFont("Arial", 10))
            self.hover_label.setDefaultTextColor(QColor(100, 100, 100))
            
            # Position near the ligature
            line = self.line()
            mid_x = (line.x1() + line.x2()) / 2
            mid_y = (line.y1() + line.y2()) / 2
            self.hover_label.setPos(mid_x - 30, mid_y - 25)
            
            # Add to scene
            self.scene().addItem(self.hover_label)
            
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Hide variable name when hover ends"""
        if self.hover_label and hasattr(self, 'scene') and self.scene():
            self.scene().removeItem(self.hover_label)
            self.hover_label = None
            
        super().hoverLeaveEvent(event)


class GraphicsContext(QGraphicsEllipseItem):
    """Graphics item representing a context (cut)"""
    
    def __init__(self, x, y, width, height, context_data=None):
        super().__init__(x, y, width, height)
        self.context_data = context_data
        
        # Visual styling for cuts
        self.setPen(QPen(QColor(150, 100, 150), 2))
        self.setBrush(QBrush(QColor(200, 150, 200, 30)))
        
        # Make movable with constraints
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)


class GraphCanvas(QGraphicsView):
    """Interactive canvas for existential graph visualization and editing"""
    
    # Signals
    graph_changed = Signal(object)  # EGGraph
    selection_changed = Signal(list)  # List of selected items
    item_double_clicked = Signal(object)  # Graph item
    
    def __init__(self):
        super().__init__()
        
        # Create graphics scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Current graph and items
        self.current_graph = None
        self.graph_items = {}  # Map from graph objects to graphics items
        self.baseline_layout = None
        
        # Configure view
        self.setup_view()
        
        # Create initial sample
        self.create_sample_display()
        
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
        self.scene.setSceneRect(-600, -400, 1200, 800)
        
    def set_graph(self, graph):
        """Set the current graph and render it"""
        self.current_graph = graph
        self.render_graph()
        self.graph_changed.emit(graph)
        
    def clear_graph(self):
        """Clear the current graph completely"""
        self.scene.clear()
        self.graph_items.clear()
        self.current_graph = None
        self.baseline_layout = None
        
    def render_graph(self):
        """Render the current graph with baseline layout"""
        # Clear existing items first
        self.scene.clear()
        self.graph_items.clear()
        
        if not self.current_graph:
            self.create_sample_display()
            return
            
        if EG_SYSTEM_AVAILABLE:
            self._render_eg_graph()
        else:
            self._render_mock_graph()
            
    def _render_eg_graph(self):
        """Render actual EGGraph object"""
        # TODO: Implement rendering of actual EGGraph
        # This will use the real data structures from the existing system
        
        # Create baseline layout
        self.create_baseline_layout()
        
        # Render contexts (cuts)
        if hasattr(self.current_graph, 'contexts'):
            for i, context in enumerate(self.current_graph.contexts):
                self._render_context(context, i)
                
        # Render nodes
        if hasattr(self.current_graph, 'nodes'):
            for i, node in enumerate(self.current_graph.nodes):
                self._render_node(node, i)
                
        # Render ligatures
        if hasattr(self.current_graph, 'ligatures'):
            for i, ligature in enumerate(self.current_graph.ligatures):
                self._render_ligature(ligature, i)
                
    def _render_mock_graph(self):
        """Render mock graph for development"""
        if not self.current_graph:
            self.create_sample_display()
            return
            
        # Clear scene first
        self.scene.clear()
        self.graph_items.clear()
        
        # Sheet of Assertion background
        sheet_rect = QGraphicsRectItem(-350, -200, 700, 400)
        sheet_rect.setPen(QPen(QColor(100, 100, 100), 2))
        sheet_rect.setBrush(QBrush(QColor(250, 250, 250, 100)))
        self.scene.addItem(sheet_rect)
        
        # Sheet label
        sheet_label = QGraphicsTextItem("Sheet of Assertion")
        sheet_label.setPos(-80, -180)
        sheet_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.scene.addItem(sheet_label)
        
        # Render contexts (cuts)
        if hasattr(self.current_graph, 'contexts') and self.current_graph.contexts:
            for i, context in enumerate(self.current_graph.contexts):
                self._render_mock_context(context, i)
                
        # Render nodes (predicates)
        if hasattr(self.current_graph, 'nodes') and self.current_graph.nodes:
            for i, node in enumerate(self.current_graph.nodes):
                self._render_mock_node(node, i)
                
        # Render ligatures (lines of identity)
        if hasattr(self.current_graph, 'ligatures') and self.current_graph.ligatures:
            for i, ligature in enumerate(self.current_graph.ligatures):
                self._render_mock_ligature(ligature, i)
                
    def _render_mock_context(self, context, index):
        """Render a mock context"""
        if 'bounds' in context:
            bounds = context['bounds']
            x, y = bounds['x'], bounds['y']
            width, height = bounds['width'], bounds['height']
        else:
            x, y = -150 + (index * 100), -75
            width, height = 300, 150
            
        # Create context (cut) as ellipse
        graphics_context = QGraphicsEllipseItem(x, y, width, height)
        graphics_context.setPen(QPen(QColor(150, 100, 150), 2))
        graphics_context.setBrush(QBrush(QColor(200, 150, 200, 30)))
        self.scene.addItem(graphics_context)
        
        # Add context label
        if context.get('type') == 'existential':
            variables = context.get('variables', ['x'])
            label_text = f"scope of {', '.join(variables)}"
            context_label = QGraphicsTextItem(label_text)
            context_label.setPos(x + width/2 - 30, y + 10)
            context_label.setFont(QFont("Arial", 10, QFont.Italic))
            context_label.setDefaultTextColor(QColor(100, 50, 100))
            self.scene.addItem(context_label)
            
        self.graph_items[f"context_{index}"] = graphics_context
        
    def _render_mock_node(self, node, index):
        """Render a mock node (predicate)"""
        if 'position' in node:
            x, y = node['position']['x'], node['position']['y']
        else:
            x, y = -100 + (index * 80), 0
            
        # Create predicate node
        graphics_node = GraphicsNode(x, y, 80, 30, node)
        
        # Add predicate label
        predicate_name = node.get('name', f"Pred{index}")
        node_label = QGraphicsTextItem(predicate_name)
        node_label.setParentItem(graphics_node)
        node_label.setPos(x + 5, y + 5)
        node_label.setFont(QFont("Arial", 10))
        
        self.scene.addItem(graphics_node)
        self.graph_items[f"node_{index}"] = graphics_node
        
    def _render_mock_ligature(self, ligature, index):
        """Render a mock ligature (line of identity) with proper EG notation"""
        if 'start' in ligature and 'end' in ligature:
            start = ligature['start']
            end = ligature['end']
            x1, y1 = start['x'], start['y']
            x2, y2 = end['x'], end['y']
        else:
            x1, y1 = -50 + (index * 30), 15
            x2, y2 = x1 + 80, y1
            
        # Create line of identity with proper thickness
        graphics_ligature = GraphicsLigature(x1, y1, x2, y2, ligature)
        
        # Make ligature thick and prominent
        pen = QPen(QColor(50, 50, 50), 4)  # Thick black line
        graphics_ligature.setPen(pen)
        
        # Add hover capability for variable display
        graphics_ligature.setAcceptHoverEvents(True)
        
        # Store variable for hover display (but don't show by default)
        variable = ligature.get('variable', f'var_{index}')
        graphics_ligature.variable_name = variable
        
        self.scene.addItem(graphics_ligature)
        self.graph_items[f"ligature_{index}"] = graphics_ligature
        
    def create_baseline_layout(self):
        """Create baseline layout for CLIF-generated graph"""
        # TODO: Implement intelligent layout algorithm
        # This should position elements based on logical structure
        # For now, use simple grid layout
        
        self.baseline_layout = {
            'contexts': [],
            'nodes': [],
            'ligatures': []
        }
        
        # Calculate positions based on graph structure
        if hasattr(self.current_graph, 'nodes'):
            node_count = len(self.current_graph.nodes)
            for i in range(node_count):
                x = -200 + (i * 150)
                y = 0
                self.baseline_layout['nodes'].append((x, y))
                
    def _render_context(self, context, index):
        """Render a context from the EG system"""
        # Use baseline layout if available
        if self.baseline_layout and index < len(self.baseline_layout.get('contexts', [])):
            x, y = self.baseline_layout['contexts'][index]
        else:
            x, y = -100 + (index * 200), -50
            
        # Create graphics context
        graphics_context = GraphicsContext(x, y, 300, 150, context)
        self.scene.addItem(graphics_context)
        self.graph_items[context] = graphics_context
        
    def _render_node(self, node, index):
        """Render a node from the EG system"""
        # Use baseline layout if available
        if self.baseline_layout and index < len(self.baseline_layout.get('nodes', [])):
            x, y = self.baseline_layout['nodes'][index]
        else:
            x, y = -150 + (index * 100), 50
            
        # Create graphics node
        graphics_node = GraphicsNode(x, y, 80, 40, node)
        self.scene.addItem(graphics_node)
        self.graph_items[node] = graphics_node
        
    def _render_ligature(self, ligature, index):
        """Render a ligature from the EG system"""
        # TODO: Connect actual nodes based on ligature data
        # For now, create sample ligature
        x1, y1 = -100 + (index * 50), 70
        x2, y2 = x1 + 100, y1
        
        graphics_ligature = GraphicsLigature(x1, y1, x2, y2, ligature)
        self.scene.addItem(graphics_ligature)
        self.graph_items[ligature] = graphics_ligature
        
    def create_sample_display(self):
        """Create sample display when no graph is loaded"""
        # Sheet of Assertion
        sheet_rect = QGraphicsRectItem(-400, -250, 800, 500)
        sheet_rect.setPen(QPen(QColor(100, 100, 100), 2))
        sheet_rect.setBrush(QBrush(QColor(250, 250, 250, 100)))
        self.scene.addItem(sheet_rect)
        
        # Title
        title = QGraphicsTextItem("EG-HG Bullpen Tools")
        title.setPos(-100, -230)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        self.scene.addItem(title)
        
        # Instructions
        instructions = QGraphicsTextItem(
            "• Load CLIF examples from the Bullpen panel\n"
            "• Parse CLIF expressions to create interactive graphs\n"
            "• Use Graph Builder for manual construction\n"
            "• Explore Peirce's rhemas in the constructor\n"
            "• Move graph elements with logical constraints"
        )
        instructions.setPos(-350, -150)
        instructions.setFont(QFont("Arial", 12))
        self.scene.addItem(instructions)
        
    def create_clif_example_display(self):
        """Create display showing CLIF parsing result using proper EG notation"""
        # Clear and create example based on mock graph
        self.scene.clear()
        
        # Sheet of Assertion (the universe of discourse)
        sheet_rect = QGraphicsRectItem(-350, -200, 700, 400)
        sheet_rect.setPen(QPen(QColor(100, 100, 100), 2))
        sheet_rect.setBrush(QBrush(QColor(250, 250, 250, 100)))
        self.scene.addItem(sheet_rect)
        
        # Sheet label
        sheet_label = QGraphicsTextItem("Sheet of Assertion")
        sheet_label.setPos(-80, -180)
        sheet_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.scene.addItem(sheet_label)
        
        # Example: (exists (x) (and (Person x) (Mortal x)))
        # In EG notation: No explicit existential quantifier symbol
        # Variables are implicitly existentially quantified by their scope
        
        # Outer context represents the existential scope
        # In EG, this is just the area where the variable x has scope
        outer_context = QGraphicsEllipseItem(-200, -100, 400, 150)
        outer_context.setPen(QPen(QColor(150, 100, 150), 2))
        outer_context.setBrush(QBrush(QColor(200, 150, 200, 30)))
        self.scene.addItem(outer_context)
        
        # Context label (scope indicator, not logical symbol)
        scope_label = QGraphicsTextItem("scope of x")
        scope_label.setPos(-30, -85)
        scope_label.setFont(QFont("Arial", 10, QFont.Italic))
        scope_label.setDefaultTextColor(QColor(100, 50, 100))
        self.scene.addItem(scope_label)
        
        # Predicate nodes within the scope
        person_node = GraphicsNode(-120, -20, 80, 30)
        person_label = QGraphicsTextItem("Person")
        person_label.setParentItem(person_node)
        person_label.setPos(-115, -15)
        person_label.setFont(QFont("Arial", 10))
        self.scene.addItem(person_node)
        
        mortal_node = GraphicsNode(40, -20, 80, 30)
        mortal_label = QGraphicsTextItem("Mortal")
        mortal_label.setParentItem(mortal_node)
        mortal_label.setPos(45, -15)
        mortal_label.setFont(QFont("Arial", 10))
        self.scene.addItem(mortal_node)
        
        # Line of Identity connecting the predicates (this is crucial in EG)
        # This represents the same individual in both predicates
        ligature = GraphicsLigature(-80, -5, 40, -5)
        self.scene.addItem(ligature)
        
        # Variable label on the line of identity
        var_label = QGraphicsTextItem("x")
        var_label.setPos(-25, -30)
        var_label.setFont(QFont("Arial", 12, QFont.Bold))
        var_label.setDefaultTextColor(QColor(150, 100, 150))
        self.scene.addItem(var_label)
        
        # CLIF expression display
        clif_display = QGraphicsTextItem("CLIF: (exists (x) (and (Person x) (Mortal x)))")
        clif_display.setPos(-200, 120)
        clif_display.setFont(QFont("Consolas", 10))
        self.scene.addItem(clif_display)
        
        # EG interpretation
        eg_interpretation = QGraphicsTextItem("EG Interpretation: Something is both a person and mortal")
        eg_interpretation.setPos(-250, 140)
        eg_interpretation.setFont(QFont("Arial", 9, QFont.Italic))
        self.scene.addItem(eg_interpretation)
        
        # EG notation explanation
        notation_explanation = QGraphicsTextItem(
            "• No explicit ∃ symbol - existential quantification is implicit\n"
            "• Line of Identity (thick line) connects same individual\n"
            "• Scope boundary shows variable domain\n"
            "• Predicates are connected by shared variables"
        )
        notation_explanation.setPos(-300, 160)
        notation_explanation.setFont(QFont("Arial", 9))
        self.scene.addItem(notation_explanation)
        
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
        
    # Event handlers
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        if event.modifiers() & Qt.ControlModifier:
            zoom_factor = 1.15
            if event.angleDelta().y() < 0:
                zoom_factor = 1.0 / zoom_factor
            self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)
            
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.RightButton:
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
            if isinstance(item, GraphicsNode):
                menu.addAction("Edit Predicate", lambda: self.edit_predicate(item))
            elif isinstance(item, GraphicsContext):
                menu.addAction("Edit Context", lambda: self.edit_context(item))
            elif isinstance(item, GraphicsLigature):
                menu.addAction("Edit Ligature", lambda: self.edit_ligature(item))
                
            menu.addAction("Delete", lambda: self.delete_item(item))
            menu.addSeparator()
            
        # General actions
        menu.addAction("Add Context", lambda: self.add_context_at_pos(global_pos))
        menu.addAction("Add Predicate", lambda: self.add_predicate_at_pos(global_pos))
        menu.addAction("Add Ligature", lambda: self.add_ligature_at_pos(global_pos))
        menu.addSeparator()
        menu.addAction("Zoom In", self.zoom_in)
        menu.addAction("Zoom Out", self.zoom_out)
        menu.addAction("Fit to View", self.zoom_fit)
        
        menu.exec(global_pos)
        
    def edit_predicate(self, item):
        """Edit predicate properties"""
        # TODO: Open predicate editing dialog
        print(f"Edit predicate: {item}")
        
    def edit_context(self, item):
        """Edit context properties"""
        # TODO: Open context editing dialog
        print(f"Edit context: {item}")
        
    def edit_ligature(self, item):
        """Edit ligature properties"""
        # TODO: Open ligature editing dialog
        print(f"Edit ligature: {item}")
        
    def delete_item(self, item):
        """Delete a graph item with logical validation"""
        # TODO: Validate deletion doesn't break logical constraints
        self.scene.removeItem(item)
        
    def add_context_at_pos(self, global_pos):
        """Add context at specified position"""
        scene_pos = self.mapToScene(self.mapFromGlobal(global_pos))
        context = GraphicsContext(scene_pos.x() - 75, scene_pos.y() - 50, 150, 100)
        self.scene.addItem(context)
        
    def add_predicate_at_pos(self, global_pos):
        """Add predicate at specified position"""
        scene_pos = self.mapToScene(self.mapFromGlobal(global_pos))
        node = GraphicsNode(scene_pos.x() - 30, scene_pos.y() - 15, 60, 30)
        self.scene.addItem(node)
        
    def add_ligature_at_pos(self, global_pos):
        """Add ligature at specified position"""
        # TODO: Implement ligature creation tool
        print("Ligature creation tool - select two predicates to connect")
        
    # Export operations
    def export_svg(self, file_path):
        """Export the graph as SVG"""
        generator = QSvgGenerator()
        generator.setFileName(file_path)
        generator.setSize(self.scene.sceneRect().size().toSize())
        generator.setViewBox(self.scene.sceneRect())
        generator.setTitle("EG-HG Existential Graph")
        
        painter = QPainter()
        painter.begin(generator)
        self.scene.render(painter)
        painter.end()
        
    def export_png(self, file_path):
        """Export the graph as PNG"""
        from PySide6.QtGui import QPixmap
        
        rect = self.scene.itemsBoundingRect()
        pixmap = QPixmap(rect.size().toSize())
        pixmap.fill(Qt.white)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        self.scene.render(painter, QRectF(), rect)
        painter.end()
        
        pixmap.save(file_path, "PNG")

